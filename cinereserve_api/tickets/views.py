from rest_framework.viewsets import ModelViewSet
from tickets.models import Ticket
from tickets.serializers import TicketSerializer
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from api.throttles import TicketRateThrottle


class TicketViewSet(ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']
    throttle_classes = [TicketRateThrottle]
    
    def get_queryset(self):
        queryset = Ticket.objects.filter(user=self.request.user)

        ticket_type = self.request.query_params.get('type')

        if ticket_type == 'upcoming':
            return queryset.filter(
                seat_session__session__date__gte=timezone.now().date()
            )
        
        elif ticket_type == 'past':
            return queryset.filter(
                seat_session__session__date__lt=timezone.now().date()
            )

        return queryset