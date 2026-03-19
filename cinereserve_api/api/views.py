from .models import Movie
from .serializers import MovieListSerializer, MovieDetailSerializer
from rest_framework.viewsets import ModelViewSet


class MovieViewSet(ModelViewSet):
    queryset = Movie.objects.all().prefetch_related('sessions')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MovieDetailSerializer
        return MovieListSerializer
