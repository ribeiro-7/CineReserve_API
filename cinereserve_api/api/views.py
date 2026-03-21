from .models import Movie, Session
from .serializers import MovieListSerializer, MovieDetailWithSessionSerializer, SessionSerializer, RegisterUserSerializer, SessionDetailSerializer
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.pagination import PageNumberPagination


class MoviePagination(PageNumberPagination):
    page_size = 5

class SessionPagination(PageNumberPagination):
    page_size = 5


class MovieViewSet(ModelViewSet):
    queryset = Movie.objects.all().prefetch_related('sessions')
    pagination_class = MoviePagination

    #Todos os filmes/filme específico com sessões disponiveis
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MovieDetailWithSessionSerializer
        return MovieListSerializer
    
    #Os outros metodos somente Admin pode alterar, criar, ou deletar filmes
    def get_permissions(self):
        if self.action in ['create', 'partial_update', 'update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]
    
class SessionViewSet(ModelViewSet):
    queryset = Session.objects.all().prefetch_related('movie')
    pagination_class = SessionPagination

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SessionDetailSerializer
        return SessionSerializer

    def get_permissions(self):
        if self.action in ['create', 'partial_update', 'update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]



class RegisterUserView(APIView):
    
    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)