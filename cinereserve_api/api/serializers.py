from rest_framework import serializers
from .models import Movie, Session
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .validators import password_validator

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