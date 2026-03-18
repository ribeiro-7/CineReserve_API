from rest_framework import serializers
from .models import Movie, Session


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ['date', 'showtime', 'theater']

class MovieSerializer(serializers.ModelSerializer):
    sessions = SessionSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = ['title', 'description', 'duration', 'age_rating', 'genre', 'release_date', 'sessions']