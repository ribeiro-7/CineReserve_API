from rest_framework import serializers
from booking.models import Booking
from .TicketSerializer import TicketSerializer

class BookingSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=True)
    session_date = serializers.DateField(source='session.date', format="%d/%m/%Y", read_only=True)
    session_time = serializers.TimeField(source='session.showtime', format="%H:%M:%S", read_only=True)
    movie_title = serializers.CharField(source='session.movie.title', read_only=True)
    class Meta:
        model = Booking
        fields = [
            'id',
            'movie_title',
            'session_date',
            'session_time',
            'status',
            'created_at',
            'tickets'
        ]