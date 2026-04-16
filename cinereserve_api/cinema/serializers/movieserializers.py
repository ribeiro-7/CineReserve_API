from .base_serializers import BaseMovieSerializer, SessionSerializer


class MovieListSerializer(BaseMovieSerializer):
        pass

class MovieDetailWithSessionSerializer(BaseMovieSerializer):
    sessions = SessionSerializer(many=True, read_only=True)

    class Meta(BaseMovieSerializer.Meta):
        fields = BaseMovieSerializer.Meta.fields + ['sessions']

class MovieDetailWithoutSession(BaseMovieSerializer):
    pass