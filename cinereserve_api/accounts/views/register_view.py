from accounts.serializers.registerserializer import RegisterUserSerializer
from rest_framework.permissions import AllowAny
from rest_framework.generics import CreateAPIView
from drf_spectacular.utils import extend_schema

@extend_schema(
    summary="Register user",
    description="Creates a new user account.",
    tags=["Register"],
)
class RegisterUserView(CreateAPIView):
    serializer_class = RegisterUserSerializer
    permission_classes = [AllowAny]