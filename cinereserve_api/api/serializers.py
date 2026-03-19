from rest_framework import serializers
from .models import Movie, Session

class MovieListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ['title', 'description', 'duration', 'age_rating', 'genre', 'release_date']

class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ['date', 'showtime', 'theater']

class MovieDetailSerializer(serializers.ModelSerializer):
    sessions = SessionSerializer(many=True, read_only=True)
    class Meta:
        model = Movie
        fields = ['title', 'description', 'duration', 'age_rating', 'genre', 'release_date', 'sessions']