from rest_framework.viewsets import ReadOnlyModelViewSet
from booking.models import Ticket
from booking.serializers.TicketSerializer import TicketSerializer
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from booking.throttles import TicketRateThrottle
from django.db.models import Q
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes,
)

@extend_schema_view(
    list=extend_schema(
        summary="List user tickets",
        description=(
            "Returns authenticated user tickets. "
            "Can filter by upcoming or past sessions."
        ),
        parameters=[
            OpenApiParameter(
                name='type',
                description=(
                    "Filter tickets by type. "
                    "Use 'upcoming', 'past', or omit for all tickets."
                ),
                required=False,
                type=OpenApiTypes.STR,
                enum=['upcoming', 'past'],
            )
        ],
        tags=['Tickets'],
    ),

    retrieve=extend_schema(
        summary="Retrieve ticket",
        description="Returns a specific ticket by ID.",
        tags=['Tickets'],
    )
)
class TicketViewSet(ReadOnlyModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [TicketRateThrottle]
    
    def get_queryset(self):
        queryset = Ticket.objects.filter(user=self.request.user, booking__status='completed').select_related(
            'seat_session__session__movie',
            'seat_session__seat',
            'booking'
        )

        ticket_type = self.request.query_params.get('type')
        now = timezone.now()
        today = now.date()
        current_time = now.time()

        if ticket_type == 'upcoming':
            return queryset.filter(
                Q(seat_session__session__date__gt=today) |
                Q(
                    seat_session__session__date=today,
                    seat_session__session__showtime__gte=current_time
                )
            )

        elif ticket_type == 'past':
            return queryset.filter(
                Q(seat_session__session__date__lt=today) |
                Q(
                    seat_session__session__date=today,
                    seat_session__session__showtime__lt=current_time
                )
            )

        return queryset