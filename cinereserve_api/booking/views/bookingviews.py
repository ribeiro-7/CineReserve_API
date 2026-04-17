from rest_framework.viewsets import ModelViewSet
from booking.models import Booking
from booking.serializers.BookingSerializer import BookingSerializer
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from cinema.throttles import BookingRateThrottle
from django.db.models import Q

class BookingViewSet(ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']
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