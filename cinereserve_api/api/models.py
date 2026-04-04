from django.db import models
from django.contrib.auth.models import User

class Movie(models.Model):

    AGE_RATINGS = [
        ('L', "Livre"),
        ('10', "Não recomendado para menores de 10 anos"),
        ('12', "Não recomendado para menores de 12 anos"),
        ('14', "Não recomendado para menores de 14 anos"),
        ('16', "Não recomendado para menores de 16 anos"),
        ('18', "Não recomendado para menores de 18 anos")
    ]

    GENRES = [
        ("Ação", "Ação"),
        ("Aventura", "Aventura"),
        ("Comédia", "Comédia"),
        ("Drama", "Drama"),
        ("Ficção Científica", "Ficção Científica"),
        ("Terror", "Terror"),
        ("Suspense", "Suspense"),
        ("Romance", "Romance"),
        ("Fantasia", "Fantasia"),
        ("Musical", "Musical"),
        ("Documentário", "Documentário"),
    ]

    title = models.CharField(max_length=100)
    description = models.TextField()
    duration = models.PositiveIntegerField() #duração em minutos - ex: 120min
    age_rating = models.CharField(max_length=2,choices=AGE_RATINGS) 
    genre = models.CharField(max_length=50, choices=GENRES)
    release_date = models.DateField()

class Session(models.Model):
    date = models.DateField()
    showtime = models.TimeField()
    theater = models.CharField(max_length=50)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="sessions")


class Seat(models.Model):
    row = models.CharField(max_length=5)
    number = models.IntegerField()

class SeatSession(models.Model):

    STATUS_CHOICE = [
        ('Available', 'Available'),
        ('Reserved', 'Reserved'),
        ('Sold', 'Sold')
    ]

    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='seats')
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICE, default='Available')
    reserved_until = models.DateTimeField(null=True, blank=True)
    reserved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ['session', 'seat']