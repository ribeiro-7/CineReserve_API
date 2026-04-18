from rest_framework import serializers
from django.contrib.auth import get_user_model
from accounts.validators import password_validator, email_validator

User = get_user_model()

class RegisterUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['email', 'username', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate_email(self, email):
        email_validator(email)
        return email

    def validate_password(self, password):
        password_validator(password)
        return password

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)