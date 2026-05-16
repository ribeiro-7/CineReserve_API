from rest_framework.viewsets import ReadOnlyModelViewSet
from booking.models import Booking
from booking.serializers.BookingSerializer import BookingSerializer
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from booking.throttles import BookingRateThrottle
from django.db.models import Q
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes,
)

@extend_schema_view(
    list=extend_schema(
        summary="List user bookings",
        description=(
            "Returns authenticated user bookings. "
            "Can filter by upcoming or past sessions."
        ),
        parameters=[
            OpenApiParameter(
                name='type',
                description=(
                    "Filter bookings by type. "
                    "Use 'upcoming', 'past', or omit for all tickets."
                ),
                required=False,
                type=OpenApiTypes.STR,
                enum=['upcoming', 'past'],
            )
        ],
        tags=['Booking'],
    ),

    retrieve=extend_schema(
        summary="Retrieve booking",
        description="Returns a specific booking by ID.",
        tags=['Booking'],
    )
)
class BookingViewSet(ReadOnlyModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [BookingRateThrottle]
    
    def get_queryset(self):
        queryset = Booking.objects.filter(user=self.request.user).prefetch_related(
            'tickets__seat_session__seat',
            'tickets__seat_session__session__movie'
        )

        booking_type = self.request.query_params.get('type')
        now = timezone.now()
        today = now.date()
        current_time = now.time()

        if booking_type == 'upcoming':
            return queryset.filter(
                Q(session__date__gt=today) |
                Q(session__date=today, session__showtime__gte=current_time)
            )
        
        elif booking_type == 'past':
            return queryset.filter(
                Q(session__date__lt=today) |
                Q(session__date=today, session__showtime__lt=current_time)
            )

        return queryset