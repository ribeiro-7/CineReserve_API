from rest_framework import serializers
from api.models import SeatSession
from .base_serializers import SessionSerializer
from .movieserializers import MovieDetailWithoutSession


class SeatSessionSerializer(serializers.ModelSerializer):
    seat_label = serializers.SerializerMethodField()

    class Meta:
        model = SeatSession
        fields = ['id', 'seat_label', 'status']
    
    def get_seat_label(self, obj):
        return f"{obj.seat.row}{obj.seat.number}"


class SessionDetailSerializer(SessionSerializer):
    movie = MovieDetailWithoutSession(read_only=True)
    seats = SeatSessionSerializer(many=True, read_only=True)

    class Meta(SessionSerializer.Meta):
        fields = SessionSerializer.Meta.fields + ['movie'] + ['seats']