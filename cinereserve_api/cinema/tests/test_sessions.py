from rest_framework import test
from django.urls import reverse
from .mixins import jwt_mixins, session_mixins
from django.core.cache import cache

class SessionTest(test.APITestCase, jwt_mixins.JWTMixin, session_mixins.SessionMixin):
    def setUp(self):
        cache.clear()

    def test_session_list_returns_status_code_200_ok(self):
        self.create_session()
        api_url = reverse('sessions-list')
        response = self.client.get(api_url)
        self.assertEqual(
            response.status_code,
            200
        )

    def test_session_list_returns_all_sessions_and_code_200_ok(self):
        sessions = self.create_sessions(movies_number=5, sessions_number=3)
        api_url = reverse('sessions-list')
        response = self.client.get(api_url)
        self.assertEqual(
            response.status_code,
            200
        )
        self.assertEqual(
            response.data.get('count'),
            len(sessions)
        )

    def test_session_list_loads_correct_number_of_sessions_defined_on_pagination(self):
        self.create_sessions(movies_number=5, sessions_number=3)
        pagination = 5
        api_url = reverse('sessions-list')
        response = self.client.get(api_url)
        self.assertEqual(
            response.status_code,
            200
        )
        self.assertEqual(
            len(response.data.get('results')),
            pagination
        )

    def test_session_retrieve_return_correct_session_and_code_200_ok(self):
        session = self.create_session()
        api_url = reverse('sessions-detail', args=[session.id])
        response = self.client.get(api_url)
        self.assertEqual(
            response.status_code,
            200
        )
        self.assertEqual(
            response.data.get('id'),
            session.id
        )
        self.assertEqual(
            response.data.get('showtime'),
            session.showtime
        )
        self.assertEqual(
            response.data.get('theater'),
            session.theater
        )
        self.assertEqual(
            response.data.get('movie').get('id'),
            session.movie.id
        )

    def test_session_dont_create_new_session_without_permission_and_returns_error_403_forbidden(self):
        access_token = self.get_user_access_token()
        api_url = reverse('sessions-list')
        movie = self.create_movie()
        data = {
            "date": "2026-03-25",
            "showtime": "17:40:00",
            "theater": "Sala 7",
            "movie": movie.id
        }
        response = self.client.post(api_url, data=data, HTTP_AUTHORIZATION=f'Bearer {access_token}')
        self.assertEqual(
            response.status_code,
            403
        )

    def test_session_create_new_session_being_an_admin_and_returns_correct_data_and_code_201_created(self):
        access_token = self.get_admin_access_token()
        api_url = reverse('sessions-list')
        movie = self.create_movie()
        session_data = {
            "date": "2026-03-25",
            "showtime": "17:40",
            "theater": "Sala 7",
            "movie": movie.id
        }
        response = self.client.post(api_url, data=session_data, HTTP_AUTHORIZATION=f'Bearer {access_token}')
        self.assertEqual(
            response.status_code,
            201
        )
        self.assertIsNotNone(response.data.get('id'))
        self.assertEqual(
            response.data.get('date'),
            self.format_date(session_data.get('date'))
        )
        self.assertEqual(
            response.data.get('showtime'),
            session_data.get('showtime')
        )

        self.assertEqual(
            response.data.get('theater'),
            session_data.get('theater')
        )

    def test_session_dont_update_a_session_without_permission_and_returns_error_403_forbidden(self):
        access_token = self.get_user_access_token()
        session = self.create_session()
        api_url = reverse('sessions-detail', args=[session.id])
        update_data = {
            "date": "2026-03-25",
            "showtime": "17:40",
            "theater": "Sala 7",
            "movie": session.movie.id
        }
        response = self.client.put(api_url, data=update_data, HTTP_AUTHORIZATION=f'Bearer {access_token}')
        self.assertEqual(
            response.status_code,
            403
        )

    def test_session_update_a_session_being_an_admin_and_returns_correct_data_and_code_200_ok(self):
        access_token = self.get_admin_access_token()
        session = self.create_session()
        api_url = reverse('sessions-detail', args=[session.id])
        update_data = {
            "date": "2026-03-25",
            "showtime": "17:40",
            "theater": "Sala 7",
            "movie": session.movie.id
        }
        response = self.client.put(api_url, data=update_data, HTTP_AUTHORIZATION=f'Bearer {access_token}')
        self.assertEqual(
            response.status_code,
            200
        )
        self.assertIsNotNone(
            response.data.get('id'))
        self.assertEqual(
            response.data.get('date'),
            '25/03/2026'
        )
        self.assertEqual(
            response.data.get('showtime'),
            update_data.get('showtime')
        )

        self.assertEqual(
            response.data.get('theater'),
            update_data.get('theater')
        )
    
    def test_session_dont_partial_update_a_session_without_permission_and_returns_error_403_forbidden(self):
        access_token = self.get_user_access_token()
        session = self.create_session()
        api_url = reverse('sessions-detail', args=[session.id])
        update_data = {
            "showtime": "17:50",
        }
        response = self.client.patch(api_url, data=update_data, HTTP_AUTHORIZATION=f'Bearer {access_token}')
        self.assertEqual(
            response.status_code,
            403
        )

    def test_session_partial_update_a_session_being_an_admin_and_returns_correct_data_and_code_200_ok(self):
        access_token = self.get_admin_access_token()
        session = self.create_session()
        api_url = reverse('sessions-detail', args=[session.id])
        update_data = {
            "showtime": "17:50",
        }
        response = self.client.patch(api_url, data=update_data, HTTP_AUTHORIZATION=f'Bearer {access_token}')
        self.assertEqual(
            response.status_code,
            200
        )
        self.assertIsNotNone(response.data.get('id'))
        self.assertEqual(
            response.data.get('date'),
            self.format_date(str(session.date))
        )
        self.assertEqual(
            response.data.get('showtime'),
            update_data.get('showtime')
        )

        self.assertEqual(
            response.data.get('theater'),
            session.theater
        )

    def test_session_dont_delete_a_session_without_permission_and_returns_error_403_forbidden(self):
        access_token = self.get_user_access_token()
        session = self.create_session()
        api_url = reverse('sessions-detail', args=[session.id])
        response = self.client.delete(api_url, HTTP_AUTHORIZATION=f'Bearer {access_token}')
        self.assertEqual(
            response.status_code,
            403
        )

    def test_session_delete_a_session_being_an_admin_and_returns_code_204_no_content(self):
        access_token = self.get_admin_access_token()
        session = self.create_session()
        api_url = reverse('sessions-detail', args=[session.id])
        response = self.client.delete(api_url, HTTP_AUTHORIZATION=f'Bearer {access_token}')
        self.assertEqual(
            response.status_code,
            204
        )
    
    def test_if_action_retrieve_returns_session_detail_serializer(self):
        session = self.create_session()
        api_url = reverse('sessions-detail', args=[session.id])
        response = self.client.get(api_url)
        self.assertEqual(
            response.status_code,
            200
        )
        self.assertIsNotNone(
            response.data.get('movie')
        )
    
    def test_if_action_list_returns_session_serializer(self):
        self.create_session()
        api_url = reverse('sessions-list')
        response = self.client.get(api_url)
        self.assertEqual(
            response.status_code,
            200
        )
        self.assertIsNone(
            response.data.get('movie')
        )

    #rate limiting tests
    def test_rate_limiting_non_user_in_session_list(self):
        self.create_sessions(movies_number=5, sessions_number=3)
        api_url = reverse('sessions-list')
        responses = []
        for i in range(20):
            response = self.client.get(api_url)
            responses.append(response.status_code)
        self.assertIn(
            429,
            responses
        )

    def test_rate_limiting_user_in_session_list(self):
        user_access_token = self.get_user_access_token()
        self.create_sessions(movies_number=5, sessions_number=3)
        api_url = reverse('sessions-list')
        responses = []
        for i in range(31):
            response = self.client.get(api_url, HTTP_AUTHORIZATION=f'Bearer {user_access_token}')
            responses.append(response.status_code)
        self.assertIn(
            429,
            responses
        )
    
    def test_rate_limiting_in_non_user_session_retrieve(self):
        session = self.create_session()
        api_url = reverse('sessions-detail', args=[session.id])
        responses = []
        for i in range(20):
            response = self.client.get(api_url)
            responses.append(response.status_code)
        self.assertIn(
            429,
            responses
        )

    def test_rate_limiting_user_in_session_retrieve(self):
        user_access_token = self.get_user_access_token()
        session = self.create_session()
        api_url = reverse('sessions-detail', args=[session.id])
        responses = []
        for i in range(31):
            response = self.client.get(api_url, HTTP_AUTHORIZATION=f'Bearer {user_access_token}')
            responses.append(response.status_code)
        self.assertIn(
            429,
            responses
        )