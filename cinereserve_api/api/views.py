from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Movie, Session
from .serializers import MovieSerializer, SessionSerializer


@api_view()
def movie_list(request):
    movies = Movie.objects.all().prefetch_related('sessions')
    serializer = MovieSerializer(movies, many=True)
    return Response(serializer.data)

@api_view()
def session_list(request):
    session = Session.objects.all()
    serializer = SessionSerializer(session, many=True)
    return Response(serializer.data)