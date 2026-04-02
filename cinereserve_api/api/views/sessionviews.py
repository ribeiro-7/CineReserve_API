from api.models import Session, SeatSession
from tickets.models import Ticket
from api.serializers.sessionserializers import SeatSessionSerializer, SessionDetailSerializer, SessionSerializer
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser, AllowAny, IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from api.tasks import update_seat_status_after_timeout, send_ticket_email
from rest_framework import status
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
import uuid
from api.throttles import SeatsRateThrottle, ReserveRateThrottle, BuyRateThrottle
from django.utils.timezone import localtime


class SessionPagination(PageNumberPagination):
    page_size = 5


@method_decorator(cache_page(30), name='list')
@method_decorator(cache_page(30), name='retrieve')
class SessionViewSet(ModelViewSet):
    queryset = Session.objects.filter(date__gte=timezone.now().date()).order_by('date', 'showtime').prefetch_related('movie', Prefetch(
        'seats', 
        queryset=SeatSession.objects.select_related('seat').order_by('seat__row', 'seat__number')
    ))
    
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
        seat_id = request.data.get('seat_id')

        if not seat_id:
            return Response({'error': 'seat_id invalid.'}, status=status.HTTP_400_BAD_REQUEST)
        
        seat_session = get_object_or_404(
            SeatSession.objects.select_for_update(),
            id=seat_id,
            session=session
        )

        if seat_session.status == 'Reserved' and seat_session.reserved_until:
            if seat_session.reserved_until <= timezone.now():
                seat_session.status = 'Available'
                seat_session.reserved_until = None
                seat_session.reserved_by = None
                seat_session.save(update_fields=['status', 'reserved_until', 'reserved_by'])

        if seat_session.status == 'Available':
            seat_session.status = 'Reserved'
            seat_session.reserved_until = timezone.now() + timedelta(minutes=5)
            expires_at = seat_session.reserved_until
            seat_session.reserved_by = request.user
            seat_session.save(update_fields=['status', 'reserved_until', 'reserved_by'])
            update_seat_status_after_timeout.apply_async(
            args=[seat_session.id],
            countdown=300
            )
            return Response({
                'seat': f'{seat_session.seat.row}{seat_session.seat.number}',
                'status': seat_session.status,
                'expires_at': localtime(expires_at).strftime("%d/%m/%Y - %H:%M:%S")
            }, status=status.HTTP_200_OK)
        
        return Response({'error': f'This seat is already {seat_session.status}'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], throttle_classes=[BuyRateThrottle])
    @transaction.atomic
    def buy(self, request, pk=None):
        session = self.get_object()
        seat_id = request.data.get('seat_id')

        if not seat_id:
            return Response({'error': 'seat_id invalid'}, status=status.HTTP_400_BAD_REQUEST)

        seat_session = get_object_or_404(
            SeatSession.objects.select_for_update(),
            id=seat_id,
            session=session
        )
        
        if seat_session.status == 'Reserved':
            if seat_session.reserved_until and seat_session.reserved_until < timezone.now():
                seat_session.status = 'Available'
                seat_session.reserved_until = None
                seat_session.reserved_by = None
                seat_session.save(update_fields=['status', 'reserved_until', 'reserved_by'])

        elif seat_session.status == 'Reserved' and seat_session.reserved_by != request.user:
            return Response({'error': 'This seat is reserved'}, status=status.HTTP_400_BAD_REQUEST)

        if seat_session.status == 'Available' or (seat_session.status == 'Reserved' and seat_session.reserved_by == request.user):
            seat_session.status = 'Sold'
            seat_session.reserved_until = None
            seat_session.reserved_by = None
            seat_session.save(update_fields=['status', 'reserved_until', 'reserved_by'])

            ticket = Ticket.objects.create(
                user=request.user,
                seat_session=seat_session,
                code=str(uuid.uuid4())
            )

            send_ticket_email.delay(
                request.user.email,
                seat_session.session.movie.title,
                f"{seat_session.seat.row}{seat_session.seat.number}",
                ticket.code
            )

            return Response({
                'movie': f'{seat_session.session.movie.title}',
                'seat': f"{seat_session.seat.row}{seat_session.seat.number}",
                'ticket-code': ticket.code,
            }, status=status.HTTP_201_CREATED)
        
        return Response({'error': f'This seat is already {seat_session.status}'}, status=status.HTTP_400_BAD_REQUEST)


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