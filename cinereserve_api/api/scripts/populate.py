import random
from faker import Faker
from datetime import time
from api.models import Movie, Session, Seat

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

    for movie in movies:
        for _ in range(3): 
            Session.objects.create(
                date=fake.date_this_month(),
                showtime=time(random.choice([14, 16, 18, 20, 22]), 0),
                theater=f"Sala {random.randint(1,7)}",
                movie=movie
            )

    print("Banco populado com sucesso!")