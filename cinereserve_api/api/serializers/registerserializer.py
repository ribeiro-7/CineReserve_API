from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from api.validators import password_validator

class RegisterUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['email', 'username', 'password']
        #a senha não é retornada
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate_password(self, value):
        password_validator(value)
        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user