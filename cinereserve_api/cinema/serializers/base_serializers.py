from rest_framework import serializers
from cinema.models import Movie, Session


class BaseMovieSerializer(serializers.ModelSerializer):
    duration_display = serializers.SerializerMethodField(read_only=True)
    age_rating_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Movie
        fields = ['id', 'title', 'description', 'duration', 'duration_display', 
                  'age_rating', 'age_rating_display', 'genre', 'release_date']
        extra_kwargs = {
            'duration': {'write_only': True},
            'age_rating': {'write_only': True}
        }

    def get_duration_display(self, obj):
        return f"{obj.duration} min"
    
    def get_age_rating_display(self, obj):
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