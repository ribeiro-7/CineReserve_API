from rest_framework import serializers
from .models import Movie, Session
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .validators import password_validator

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


class MovieListSerializer(BaseMovieSerializer):
        pass

    
class SessionSerializer(serializers.ModelSerializer):
    showtime = serializers.TimeField(format="%H:%M")
    date = serializers.DateField(format="%d/%m/%Y")

    class Meta:
        model = Session
        fields = ['id', 'date', 'showtime', 'theater', 'movie']
        extra_kwargs = {
            'movie': {'write_only': True}
        }

class MovieDetailWithSessionSerializer(BaseMovieSerializer):
    sessions = SessionSerializer(many=True, read_only=True)

    class Meta(BaseMovieSerializer.Meta):
        fields = BaseMovieSerializer.Meta.fields + ['sessions']

class MovieDetailWithoutSession(BaseMovieSerializer):
    pass


class SessionDetailSerializer(SessionSerializer):
    movie = MovieDetailWithoutSession(read_only=True)
    class Meta(SessionSerializer.Meta):
        fields = SessionSerializer.Meta.fields + ['movie']

class RegisterUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['email', 'username', 'password']
        #a senha não é retornada
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate_password(self, value):
        validate_password(value)
        password_validator(value)
        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user