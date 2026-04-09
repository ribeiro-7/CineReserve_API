from api.models import Session, Movie
from .movie_mixins import MovieMixin
import random
from faker import Faker
from datetime import datetime, timedelta, time
from django.utils import timezone

fake = Faker('pt_BR')

class SessionMixin(MovieMixin):
    def create_sessions(self, movies_number, sessions_number):
        def generate_future_date(max_days_ahead=30):
            today = datetime.now().date()
            days_ahead = random.randint(1, max_days_ahead)
            return today + timedelta(days=days_ahead)

        GENRES = [
            "Ação",
            "Aventura",
            "Comédia",
            "Drama",
            "Ficção Científica",
            "Terror",
            "Suspense",
            "Romance",
            "Fantasia",
            "Musical",
            "Documentário",
        ]
        movies = []
        for _ in range(movies_number):
            movie = Movie.objects.create(
                title=fake.catch_phrase(),
                description=fake.text(max_nb_chars=200),
                duration=random.randint(80, 180),
                age_rating=random.choice(['L', '10', '12', '14', '16', '18']),
                genre=random.choice(GENRES),
                release_date=fake.date_between(start_date='-10y', end_date='today')
            )
            movies.append(movie)

        SHOWTIMES = [14, 16, 18, 20, 22]

        sessions = []
        for movie in movies:
            for _ in range(sessions_number):
                session_date = generate_future_date()

                session = Session.objects.create(
                    date=session_date,
                    showtime=time(random.choice(SHOWTIMES), 0),
                    theater=f"Sala {random.randint(1,7)}",
                    movie=movie
                )
                sessions.append(session)
        
        return sessions

    def create_session(self):
        movie = self.create_movie()
        session = Session.objects.create(
            date=timezone.now().date() + timedelta(days=1),
            showtime='14:00',
            theater='Sala 2',
            movie=movie
        )
        return session
    
    def format_date(self, session_data):
        expected_date = datetime.strptime(
            session_data, "%Y-%m-%d").strftime("%d/%m/%Y")
        return expected_date