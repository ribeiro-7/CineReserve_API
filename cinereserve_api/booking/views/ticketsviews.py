from rest_framework.viewsets import ModelViewSet
from booking.models import Ticket
from booking.serializers.TicketSerializer import TicketSerializer
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from cinema.throttles import TicketRateThrottle
from django.db.models import Q

class TicketViewSet(ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']
    throttle_classes = [TicketRateThrottle]
    
    def get_queryset(self):
        queryset = Ticket.objects.filter(user=self.request.user).select_related(
            'seat_session__session__movie',
            'seat_session__seat'
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