from .models import Movie, Session
from .serializers.movieserializers import MovieListSerializer, MovieDetailWithSessionSerializer
from .serializers.sessionserializers import SessionSerializer, SessionDetailSerializer, SeatSessionSerializer
from .serializers.registerserializer import RegisterUserSerializer
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta



class MoviePagination(PageNumberPagination):
    page_size = 5

class SessionPagination(PageNumberPagination):
    page_size = 5


class MovieViewSet(ModelViewSet):
    queryset = Movie.objects.all().prefetch_related('sessions')
    pagination_class = MoviePagination

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MovieDetailWithSessionSerializer
        return MovieListSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'partial_update', 'update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]
    
class SessionViewSet(ModelViewSet):
    queryset = Session.objects.all().order_by('date', 'showtime').prefetch_related('movie')
    pagination_class = SessionPagination

    @action(detail=True, methods=['get'])
    def seats(self, request, pk=None):
        session = self.get_object()
        seats = session.seats.all()
        serializer = SeatSessionSerializer(seats, many=True)
        return Response(serializer.data)
    
    
    @action(detail=True, methods=['post'])
    def reserve(self, request, pk=None):
        session = self.get_object()
        seat_id = request.data.get('seat_id')

        if not seat_id:
            return Response({'error': 'seat_id invalid'}, status=status.HTTP_400_BAD_REQUEST)

        seat_session = get_object_or_404(session.seats, id=seat_id)

        if seat_session.status == 'Reserved' and seat_session.reserved_until:
            if seat_session.reserved_until < timezone.now():
                seat_session.status = 'Available'
                seat_session.reserved_until = None
                seat_session.save()

        if seat_session.status == 'Available':
            seat_session.status = 'Reserved'
            seat_session.reserved_until = timezone.now() + timedelta(minutes=10)
            seat_session.save()
            return Response({'message': 'Seat reserved for 10 minutes'}, status=status.HTTP_200_OK)

        
        return Response({'error': f'This seat is {seat_session.status}'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def buy(self, request, pk=None):
        session = self.get_object()
        seat_id = request.data.get('seat_id')

        if not seat_id:
            return Response({'error': 'seat_id invalid'}, status=status.HTTP_400_BAD_REQUEST)
        
        seat_session = get_object_or_404(session.seats, id=seat_id)

        if seat_session.status == 'Reserved':
            if seat_session.reserved_until and seat_session.reserved_until < timezone.now():
                seat_session.status = 'Available'
                seat_session.reserved_until = None
                seat_session.save()

        if seat_session.status == 'Available':
            seat_session.status = 'Sold'
            seat_session.reserved_until = None
            seat_session.save()
            return Response({'message': f'You bought a ticket for: "{seat_session.session.movie.title}", your seat is: "{seat_session.seat.row}{seat_session.seat.number}"'})
        
        return Response({'error': f'This seat is already {seat_session.status}'}, status=status.HTTP_400_BAD_REQUEST)


    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SessionDetailSerializer
        return SessionSerializer

    def get_permissions(self):
        if self.action in ['create', 'partial_update', 'update', 'destroy']:
            return [IsAdminUser()]
        elif self.action in ['reserve', 'buy']:
            return [IsAuthenticated()]
        return [AllowAny()]


class RegisterUserView(APIView):
    
    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)