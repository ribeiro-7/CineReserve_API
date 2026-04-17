from cinema.models import Session, SeatSession
from booking.models import Ticket, Booking
from cinema.serializers.sessionserializers import SeatSessionSerializer, SessionDetailSerializer, SessionSerializer
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser, AllowAny, IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from cinema.tasks import update_seat_status_after_timeout, send_ticket_email
from rest_framework import status
from django.db import transaction
from django.db.models import Q, Prefetch
import uuid
from cinema.throttles import SeatsRateThrottle, ReserveRateThrottle, BuyRateThrottle, SessionReadRateThrottle
from django.utils.timezone import localtime


class SessionPagination(PageNumberPagination):
    page_size = 5

@method_decorator(cache_page(60), name='list')
class SessionViewSet(ModelViewSet):

    pagination_class = SessionPagination

    @action(detail=True, methods=['get'], throttle_classes=[SeatsRateThrottle])
    def seats(self, request, pk=None):
        session = self.get_object()
        seats = session.seats.select_related('seat').order_by('seat__row', 'seat__number')
        serializer = SeatSessionSerializer(seats, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], throttle_classes=[ReserveRateThrottle])
    @transaction.atomic
    def reserve(self, request, pk=None):
        session = self.get_object()
        seat_ids = request.data.get('seat_ids')
        
        if not isinstance(seat_ids, list) or not seat_ids:
            return Response({'error': 'seat_ids must be a non-empty list.'}, status=status.HTTP_400_BAD_REQUEST)
        
        now = timezone.now()
        today = now.date()
        current_time = now.time()

        if not (session.date > today or (session.date == today and session.showtime > current_time)):
            return Response({'error': 'The session has already passed.'}, status=status.HTTP_400_BAD_REQUEST)

        seat_sessions = list(
            SeatSession.objects.select_for_update().filter(
                id__in=seat_ids,
                session=session
            )
        )

        if len(seat_sessions) != len(seat_ids):
            return Response({'error': 'One or more seats not found.'}, status=status.HTTP_404_NOT_FOUND)
                
        invalid_seats = []

        for seat in seat_sessions:
            if seat.status == 'Reserved':
                if seat.reserved_until and seat.reserved_until < now:
                    seat.status = 'Available'
                    seat.reserved_until = None
                    seat.reserved_by = None
                    seat.save(update_fields=['status', 'reserved_until', 'reserved_by'])
                else:
                    invalid_seats.append(seat)
            elif seat.status == 'Sold':
                invalid_seats.append(seat)

        if invalid_seats:
            invalid_seats_label = [
                f'{seat.seat.row}{seat.seat.number}'
                for seat in invalid_seats
            ]
            return Response(
                {'error': f"Seats unavailable: {', '.join(invalid_seats_label)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reserved_seats = []

        for seat in seat_sessions:
            seat.status = 'Reserved'
            seat.reserved_until = now + timedelta(minutes=5)
            expires_at = seat.reserved_until
            seat.reserved_by = request.user
            seat.save(update_fields=['status', 'reserved_until', 'reserved_by'])
            update_seat_status_after_timeout.apply_async(
            args=[seat.id],
            countdown=300
            )
            reserved_seats.append({
                'seat': f'{seat.seat.row}{seat.seat.number}',
                'status': seat.status,
                'expires_at': localtime(expires_at).strftime("%d/%m/%Y - %H:%M:%S")
            })
        return Response({
            'reserved_seats': reserved_seats
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], throttle_classes=[BuyRateThrottle])
    @transaction.atomic
    def buy(self, request, pk=None):
        session = self.get_object()
        seat_ids = request.data.get('seat_ids')

        if not isinstance(seat_ids, list) or not seat_ids:
            return Response({'error': 'seat_ids must be a non-empty list.'}, status=status.HTTP_400_BAD_REQUEST )
        
        now = timezone.now()
        today = now.date()
        current_time = now.time()
        
        if not (session.date > today or (session.date == today and session.showtime > current_time)):
            return Response({'error': 'The session has already passed.'})

        seat_sessions = list(
            SeatSession.objects.select_for_update().filter(
                id__in=seat_ids,
                session=session
            )
        )

        if len(seat_sessions) != len(seat_ids):
            return Response({'error': 'One or more seats not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        invalid_seats = []

        for seat in seat_sessions:
            if seat.status == 'Reserved' and seat.reserved_by != request.user:
                if seat.reserved_until and seat.reserved_until < now:
                    seat.status = 'Available'
                    seat.reserved_until = None
                    seat.reserved_by = None
                    seat.save(update_fields=['status', 'reserved_until', 'reserved_by'])
                else:
                    invalid_seats.append(seat)
            elif seat.status == 'Sold':
                invalid_seats.append(seat)

        if invalid_seats:
            invalid_seats_label = [
                f'{seat.seat.row}{seat.seat.number}'
                for seat in invalid_seats
            ]
            return Response(
                {'error': f"Seats unavailable: {', '.join(invalid_seats_label)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        booking = Booking.objects.create(
            user=request.user,
            session=session,
            status='completed'
        )

        tickets = []

        for seat in seat_sessions:
            seat.status = 'Sold'
            seat.reserved_until = None
            seat.reserved_by = None
            seat.save(update_fields=['status', 'reserved_until', 'reserved_by'])
            ticket = Ticket.objects.create(
                user=request.user,
                seat_session=seat,
                booking=booking,
                code=str(uuid.uuid4())
            )
            tickets.append({
                'seat': f"{seat.seat.row}{seat.seat.number}",
                'ticket_code': ticket.code,
                'date': session.date,
                'time': session.showtime}
            )
        
        send_ticket_email.delay(
            request.user.email,
            session.movie.title,
            tickets
        )

        return Response({
            'booking_id': booking.id,
            'movie': f'{session.movie.title}',
            'tickets': tickets
        }, status=status.HTTP_201_CREATED)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SessionDetailSerializer
        return SessionSerializer

    def get_permissions(self):
        if self.action in ['create', 'partial_update', 'update', 'destroy']:
            return [IsAdminUser()]
        elif self.action in ['reserve', 'buy']:
            return [IsAuthenticated()]
        return [AllowAny()]
    
    def get_throttles(self):
        if self.action in ['list', 'retrieve']:
            return [SessionReadRateThrottle()]
        return super().get_throttles()
    
    def get_queryset(self):
        now = timezone.now()
        base_queryset = Session.objects.all().order_by('date', 'showtime').prefetch_related(
            'movie',
            Prefetch(
                'seats',
                queryset=SeatSession.objects.select_related('seat').order_by('seat__row', 'seat__number')
            )
        )

        if self.action == 'list':
            return base_queryset.filter(
                Q(date__gt=now.date()) |
                Q(date=now.date(), showtime__gte=now.time())
            )
        
        return base_queryset