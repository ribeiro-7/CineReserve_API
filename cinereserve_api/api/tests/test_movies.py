from rest_framework import test
from django.urls import reverse
from .mixins import jwt_mixins, movie_mixins

class MovieTest(test.APITestCase, jwt_mixins.JWTMixin, movie_mixins.MovieMixin):     
    def test_movie_list_returns_status_code_200(self):
        api_url = reverse('movies-list')
        response = self.client.get(api_url)
        self.assertEqual(
            response.status_code,
            200
        )

    def test_movie_list_loads_correct_number_of_movies(self):
        movies_number = 5
        self.create_movies(movies_number)
        response = self.client.get(reverse('movies-list'))

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(len(response.data.get('results')), movies_number)
    
    def test_movie_retrieve_return_correct_movie(self):
        movie = self.create_movie()
        api_url = reverse('movies-detail', args=[movie.id])
        response = self.client.get(api_url)

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            response.data.get('id'),
            movie.id
        )

        self.assertEqual(
            response.data.get('title'),
            movie.title
        )

        self.assertEqual(
            response.data.get('description'),
            movie.description
        )

        self.assertEqual(
            response.data.get('duration_display').split()[0],
            str(movie.duration)
        )

        self.assertEqual(
            response.data.get('age_rating_display').get('code'),
            movie.age_rating
        )

        self.assertEqual(
            response.data.get('genre'),
            movie.genre
        )

        self.assertEqual(
            response.data.get('release_date'),
            movie.release_date
        )

    def test_movie_dont_create_new_movie_without_permission_and_returns_error_403_forbidden(self):
        access_token = self.get_normal_user_jwt_access_token(username='usertest', password='Password123#')
        api_url = reverse('movies-list')
        data = {
            "title": "O Mundo Depois de Nós",
            "description": "Amanda e Clay alugam uma casa de luxo para passar alguns dias tranquilos longe da cidade grande com seus filhos. Mas uma catástrofe misteriosa vira o país de ponta cabeça. G.H. e Ruth batem à sua porta afirmando que são os donos originais da mansão e pedem abrigo no lugar. Desconfiados e em meio ao caos do mundo, os estranhos são obrigados a morar juntos, mas não conseguem confiar uns nos outros.",
            "duration": 140,
            "age_rating": "16",
            "genre": "Ficção Científica",
            "release_date": "2023-11-22"
        }
        response = self.client.post(api_url, data=data, HTTP_AUTHORIZATION=f'Bearer {access_token}')
        self.assertEqual(
            response.status_code,
            403
        )

    def test_movie_create_new_movie_being_an_admin_and_returns_correct_data_and_code_201_created(self):
        access_token = self.get_admin_user_jwt_access_token(username='admin', password='Admin123#')
        api_url = reverse('movies-list')
        data = {
            'id': 1,
            "title": "O Mundo Depois de Nós",
            "description": "Amanda e Clay alugam uma casa de luxo para passar alguns dias tranquilos longe da cidade grande com seus filhos. Mas uma catástrofe misteriosa vira o país de ponta cabeça. G.H. e Ruth batem à sua porta afirmando que são os donos originais da mansão e pedem abrigo no lugar. Desconfiados e em meio ao caos do mundo, os estranhos são obrigados a morar juntos, mas não conseguem confiar uns nos outros.",
            "duration": 140,
            "age_rating": "16",
            "genre": "Ficção Científica",
            "release_date": "2023-11-22"
        }
        response = self.client.post(api_url, data=data, HTTP_AUTHORIZATION=f'Bearer {access_token}')
        self.assertEqual(
            response.status_code,
            201
        )

        self.assertEqual(
            response.data.get('id'),
            data.get('id')
        )

        self.assertEqual(
            response.data.get('title'),
            data.get('title')
        )

        self.assertEqual(
            response.data.get('description'),
            data.get('description')
        )

        self.assertEqual(
            response.data.get('duration_display').split()[0],
            str(data.get('duration'))
        )

        self.assertEqual(
            response.data.get('age_rating_display').get('code'),
            data.get('age_rating')
        )

        self.assertEqual(
            response.data.get('genre'),
            data.get('genre')
        )

        self.assertEqual(
            response.data.get('release_date'),
            data.get('release_date')
        )

    def test_movie_dont_update_a_movie_without_permission_and_returns_error_403_forbidden(self):
        access_token = self.get_normal_user_jwt_access_token(username='usertest', password='Password123#')
        data = {
            'id': 1,
            "title": "O Mundo Depois de Nós [ALTERAÇÃO]",
            "description": "Amanda e Clay alugam uma casa de luxo para passar alguns dias tranquilos longe da cidade grande com seus filhos. Mas uma catástrofe misteriosa vira o país de ponta cabeça. G.H. e Ruth batem à sua porta afirmando que são os donos originais da mansão e pedem abrigo no lugar. Desconfiados e em meio ao caos do mundo, os estranhos são obrigados a morar juntos, mas não conseguem confiar uns nos outros.",
            "duration": 140,
            "age_rating": "16",
            "genre": "Ficção Científica",
            "release_date": "2023-11-22"
        }
        api_url = reverse('movies-detail', args=[data.get('id')])
        response = self.client.put(api_url, data=data, HTTP_AUTHORIZATION=f'Bearer {access_token}')
        self.assertEqual(
            response.status_code,
            403
        )

    def test_movie_update_a_movie_being_an_admin_and_returns_correct_data_and_code_200_ok(self):
        access_token = self.get_admin_user_jwt_access_token(username='admin', password='Admin123#')
        movie = self.create_movie()
        update_data = {
            "title": "O Mundo Depois de Nós [ALTERAÇÃO]",
            "description": "Amanda e Clay alugam uma casa de luxo para passar alguns dias tranquilos longe da cidade grande com seus filhos. Mas uma catástrofe misteriosa vira o país de ponta cabeça. G.H. e Ruth batem à sua porta afirmando que são os donos originais da mansão e pedem abrigo no lugar. Desconfiados e em meio ao caos do mundo, os estranhos são obrigados a morar juntos, mas não conseguem confiar uns nos outros.",
            "duration": 140,
            "age_rating": "16",
            "genre": "Ficção Científica",
            "release_date": "2023-11-22"
        }
        update_url = reverse('movies-detail', args=[movie.id])
        response = self.client.put(update_url, data=update_data, HTTP_AUTHORIZATION=f'Bearer {access_token}')
        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            response.data.get('id'),
            movie.id
        )

        self.assertEqual(
            response.data.get('title'),
            update_data.get('title')
        )

        self.assertEqual(
            response.data.get('description'),
            update_data.get('description')
        )

        self.assertEqual(
            response.data.get('duration_display').split()[0],
            str(update_data.get('duration'))
        )

        self.assertEqual(
            response.data.get('age_rating_display').get('code'),
            update_data.get('age_rating')
        )

        self.assertEqual(
            response.data.get('genre'),
            update_data.get('genre')
        )

        self.assertEqual(
            response.data.get('release_date'),
            update_data.get('release_date')
        )

    def test_movie_dont_delete_a_movie_without_permission_and_returns_error_403_forbidden(self):
        access_token = self.get_normal_user_jwt_access_token(username='usertest', password='Password123#')
        movie = self.create_movie()
        api_url = reverse('movies-detail', args=[movie.id])
        response = self.client.delete(api_url, HTTP_AUTHORIZATION=f'Bearer {access_token}')
        self.assertEqual(
            response.status_code,
            403
        )

    def test_movie_delete_a_movie_being_an_admin_and_returns_code_204_no_content(self):
        access_token = self.get_admin_user_jwt_access_token(username='admin', password='Admin123#')
        movie = self.create_movie()
        api_url = reverse('movies-detail', args=[movie.id])
        response = self.client.delete(api_url, HTTP_AUTHORIZATION=f'Bearer {access_token}')
        self.assertEqual(
            response.status_code,
            204
        )


    



