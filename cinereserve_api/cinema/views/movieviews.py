from cinema.models import Movie
from cinema.throttles import MovieRateThrottle
from cinema.serializers.movieserializers import MovieListSerializer, MovieDetailWithSessionSerializer
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser, AllowAny
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

class MoviePagination(PageNumberPagination):
    page_size = 5

@method_decorator(cache_page(60 * 5), name='list')
@method_decorator(cache_page(60 * 5), name='retrieve')
class MovieViewSet(ModelViewSet):
    queryset = Movie.objects.all().order_by('-id').prefetch_related('sessions')
    pagination_class = MoviePagination

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MovieDetailWithSessionSerializer
        return MovieListSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'partial_update', 'update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]

    def get_throttles(self):
        if self.action in ['list', 'retrieve']:
            return [MovieRateThrottle()]
        return super().get_throttles()