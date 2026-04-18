from accounts.serializers.registerserializer import RegisterUserSerializer
from rest_framework.permissions import AllowAny
from rest_framework.generics import CreateAPIView

class RegisterUserView(CreateAPIView):
    serializer_class = RegisterUserSerializer
    permission_classes = [AllowAny]