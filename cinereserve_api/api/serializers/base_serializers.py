from rest_framework import serializers
from api.models import Movie, Session


class BaseMovieSerializer(serializers.ModelSerializer):
    duration = serializers.SerializerMethodField()
    age_rating = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = ['id', 'title', 'description', 'duration', 'age_rating', 'genre', 'release_date']

    def get_duration(self, obj):
        return f"{obj.duration} min"
    
    def get_age_rating(self, obj):
        return {
            "code": obj.age_rating,
            "label": obj.get_age_rating_display()
        }
    
class SessionSerializer(serializers.ModelSerializer):
    showtime = serializers.TimeField(format="%H:%M")
    date = serializers.DateField(format="%d/%m/%Y")

    class Meta:
        model = Session
        fields = ['id', 'date', 'showtime', 'theater', 'movie']
        extra_kwargs = {
            'movie': {'write_only': True}
        }