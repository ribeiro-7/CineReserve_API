from cinema.models import Movie

class MovieMixin:
    def create_movies(self, movies_number):

        for i in range(movies_number):
            Movie.objects.create(
                title = f'Movie {i}',
                description = f'Description of Movie {i}',
                duration = 120,
                age_rating = 'L',
                genre = 'Ação',
                release_date = '2025-04-04'
            )

    def create_movie(self):

        movie = Movie.objects.create(
            title = f'Movie 1',
            description = f'Description of Movie 1',
            duration = 120,
            age_rating = 'L',
            genre = 'Ação',
            release_date = '2025-04-04'
        )

        return movie