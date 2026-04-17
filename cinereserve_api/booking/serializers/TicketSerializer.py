from rest_framework import serializers
from booking.models import Ticket

class TicketSerializer(serializers.ModelSerializer):
    purchased_at = serializers.DateTimeField(format="%d/%m/%Y - %H:%M:%S", read_only=True)
    movie_title = serializers.CharField(source='seat_session.session.movie.title', read_only=True)
    showtime = serializers.TimeField(source='seat_session.session.showtime', format="%H:%M:%S", read_only=True)
    date = serializers.DateField(source='seat_session.session.date', format="%d/%m/%Y", read_only=True)
    theater = serializers.CharField(source='seat_session.session.theater', read_only=True)
    seat = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = ['code', 'purchased_at', 'movie_title', 'showtime', 'date', 'theater', 'seat']
        read_only_fields = ['code', 'purchased_at']

    def get_seat(self, obj):
        return f'{obj.seat_session.seat.row}{obj.seat_session.seat.number}'