from .models import Movie
from .serializers import MovieListSerializer, MovieDetailSerializer, RegisterUserSerializer
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response


class MovieViewSet(ModelViewSet):
    queryset = Movie.objects.all().prefetch_related('sessions')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MovieDetailSerializer
        return MovieListSerializer


class RegisterUserView(APIView):
    
    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)