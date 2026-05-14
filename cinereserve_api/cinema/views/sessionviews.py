from cinema.models import Session, SeatSession
from cinema.serializers.sessionserializers import SeatSessionSerializer, SessionDetailSerializer, SessionSerializer
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser, AllowAny, IsAuthenticated
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.db.models import Q, Prefetch
from cinema.throttles import SeatsRateThrottle, ReserveRateThrottle, BuyRateThrottle, SessionReadRateThrottle
from payments.services import PaymentService
from cinema.services.booking_service import BookingService
from cinema.services.reservation_service import ReservationService
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework import status


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
    def reserve(self, request, pk=None):
        session = self.get_object()
        seat_ids = request.data.get("seat_ids")

        try:
            reserved_seats = ReservationService.reserve_seats(
                user=request.user,
                session=session,
                seat_ids=seat_ids
            )

            return Response({
                "reserved_seats": reserved_seats
            })

        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        except NotFound as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'], throttle_classes=[BuyRateThrottle])
    def buy(self, request, pk=None):
        session = self.get_object()
        seat_ids = request.data.get("seat_ids")

        try:
            booking = BookingService.create_booking(
                user=request.user,
                session=session,
                seat_ids=seat_ids
            )

            payment_link = PaymentService.create_payment_for_booking(booking)

            tickets = []

            for ticket in booking.tickets.select_related("seat_session__seat"):
                seat = ticket.seat_session
                tickets.append({
                    "seat": f"{seat.seat.row}{seat.seat.number}",
                    "ticket_code": ticket.code,
                    "price": ticket.price,
                    "date": session.date,
                    "time": session.showtime
                })

            return Response({
                "booking_id": booking.id,
                "movie": session.movie.title,
                "tickets": tickets,
                "amount": booking.amount,
                "payment_link": payment_link,
                "message": (
                    "Complete payment to confirm your booking..."
                )
            }, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        except NotFound as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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