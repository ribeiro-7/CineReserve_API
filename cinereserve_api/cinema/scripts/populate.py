import random
from faker import Faker
from datetime import datetime, timedelta, time
from cinema.models import Movie, Session, Seat

fake = Faker('pt_BR')

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

# 🔥 gera datas do presente até X dias no futuro
def generate_future_date(max_days_ahead=30):
    today = datetime.now().date()
    days_ahead = random.randint(0, max_days_ahead)
    return today + timedelta(days=days_ahead)


def run():
    print("Limpando banco...")
    Session.objects.all().delete()
    Movie.objects.all().delete()

    if not Seat.objects.exists():
        print("💺 Criando assentos...")

        for row in ['A', 'B', 'C', 'D', 'E']:
            for num in range(1, 11):
                Seat.objects.create(row=row, number=num)

        print("Assentos criados!")
    else:
        print("Assentos já existem.")

    print("Criando filmes...")

    movies = []

    for _ in range(35):
        movie = Movie.objects.create(
            title=fake.catch_phrase(),
            description=fake.text(max_nb_chars=200),
            duration=random.randint(80, 180),
            age_rating=random.choice(['L', '10', '12', '14', '16', '18']),
            genre=random.choice(GENRES),
            release_date=fake.date_between(start_date='-10y', end_date='today')
        )
        movies.append(movie)

    print("Criando sessões...")

    SHOWTIMES = [14, 16, 18, 20, 22]

    for movie in movies:
        for _ in range(3):
            session_date = generate_future_date()

            Session.objects.create(
                date=session_date,
                showtime=time(random.choice(SHOWTIMES), 0),
                theater=f"Sala {random.randint(1,7)}",
                movie=movie
            )

    print("Banco populado com sucesso!")