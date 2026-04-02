from api.serializers.registerserializer import RegisterUserSerializer
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response



class RegisterUserView(APIView):
    
    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)