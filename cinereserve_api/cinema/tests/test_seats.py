from rest_framework import test
from django.urls import reverse
from accounts.tests.mixins import jwt_mixins
from .mixins import seat_mixins
from django.utils import timezone
from datetime import timedelta
from cinema.tasks import update_seat_status_after_timeout
from django.core.cache import cache
from unittest.mock import patch
import threading
from django.db import connections


class SeatTest(test.APITestCase, seat_mixins.SeatMixin, jwt_mixins.JWTMixin):
    def setUp(self):
        cache.clear()
        
    def test_seat_list_returns_status_code_200_ok(self):
        session = self.create_session()
        api_url = reverse('sessions-seats', args=[session.id])
        response = self.client.get(api_url)
        self.assertEqual(
            response.status_code,
            200
        )

    def test_seat_list_returns_all_seats_from_session_and_code_200_ok(self):
        data = self.create_seats()
        session = data.get('session')
        seat_sessions = data.get('seat_sessions')
        api_url = reverse('sessions-seats', args=[session.id])
        response = self.client.get(api_url)
        
        expected = {
            seat.id: {
                'seat_label': f"{seat.seat.row}{seat.seat.number}",
                'status': seat.status
            }
            for seat in seat_sessions
        }

        self.assertEqual(
            response.status_code,
            200
        )

        for item in response.data:
            self.assertIn(item['id'], expected)
            self.assertEqual(item['seat_label'], expected[item['id']]['seat_label'])
            self.assertEqual(item['status'], expected[item['id']]['status'])

    def test_seat_reserve_dont_work_with_unauthenticated_user_and_code_401_unauthorized(self):
        create_seat = self.create_available_seat()
        seat_id = create_seat.seat.id
        session_id = create_seat.session.id
        response = self.reserve_seats(session_id=session_id, seat_ids=[seat_id], access_token=None)
        self.assertEqual(
            response.status_code,
            401
        )

    def test_seat_reserve_change_status_to_reserve_and_code_200_ok(self):
        user_access_token = self.get_user_access_token()
        create_seat = self.create_available_seat()
        seat_id = create_seat.seat.id
        session_id = create_seat.session.id
        reserve_response = self.reserve_seats(session_id=session_id, seat_ids=[seat_id], access_token=user_access_token)
        reserved_seats = reserve_response.data.get('reserved_seats')
        self.assertEqual(reserve_response.status_code, 200)
        self.assertEqual(
            reserved_seats[0].get('status'),
            'Reserved'
        )

    def test_seat_trying_to_reserve_a_seat_thats_already_reserved_by_other_person_code_400(self):
        user_access_token = self.get_user_access_token()
        admin_access_token = self.get_admin_access_token()
        create_seat = self.create_available_seat()
        seat = create_seat.seat
        seat_id = create_seat.seat.id
        session_id = create_seat.session.id
        reserving_seat_with_admin_user = self.reserve_seats(session_id=session_id, seat_ids=[seat_id], access_token=admin_access_token)
        reserved_seats = reserving_seat_with_admin_user.data.get('reserved_seats')
        self.assertEqual(reserving_seat_with_admin_user.status_code, 200)
        self.assertEqual(
            reserved_seats[0].get('status'),
            'Reserved'
        )
        trying_to_reserve_with_different_user = self.reserve_seats(session_id=session_id, seat_ids=[seat_id], access_token=user_access_token)
        self.assertEqual(trying_to_reserve_with_different_user.status_code, 400)
        self.assertEqual(
            trying_to_reserve_with_different_user.data.get('error'),
                f"Seats unavailable: {seat.row}{seat.number}"
        )

    def test_seat_trying_to_reserve_a_seat_thats_already_sold_returns_code_400(self):
        user_access_token = self.get_user_access_token()
        admin_access_token = self.get_admin_access_token()
        create_seat = self.create_available_seat()
        seat = create_seat.seat
        seat_id = create_seat.seat.id
        session_id = create_seat.session.id
        buying_seat = self.buy_seats(session_id=session_id, seat_ids=[seat_id], access_token=admin_access_token)
        self.assertEqual(buying_seat.status_code, 201)
        trying_to_reserve_sold_seat = self.reserve_seats(session_id=session_id, seat_ids=[seat.id], access_token=user_access_token)
        self.assertEqual(trying_to_reserve_sold_seat.status_code, 400)
        self.assertEqual(
            trying_to_reserve_sold_seat.data.get('error'),
            f"Seats unavailable: {seat.row}{seat.number}"
        )

    def test_seat_buy_available_seat_return_ticket_and_code_201(self):
        user_access_token = self.get_user_access_token()
        create_seat = self.create_available_seat()
        seat = create_seat.seat
        seat_id = create_seat.seat.id
        session_id = create_seat.session.id
        buying_seat = self.buy_seats(session_id=session_id, seat_ids=[seat_id], access_token=user_access_token)
        tickets = buying_seat.data.get('tickets')[0]
        self.assertEqual(buying_seat.status_code, 201)
        self.assertEqual(
            buying_seat.data.get('movie'),
            create_seat.session.movie.title
        )
        self.assertEqual(
            tickets.get('seat'),
            f"{seat.row}{seat.number}"
        )
        self.assertIsNotNone(
            tickets.get('ticket_code'),
        )
        
    def test_seat_buy_dont_work_with_unauthenticated_user_and_code_401_unauthorized(self):
        create_seat = self.create_available_seat()
        seat_id = create_seat.seat.id
        session_id = create_seat.session.id
        response = self.buy_seats(session_id=session_id, seat_ids=[seat_id])
        self.assertEqual(
            response.status_code,
            401
        )

    def test_seat_buy_change_status_to_sold_and_code_201_ok(self):
        user_access_token = self.get_user_access_token()
        create_seat = self.create_available_seat()
        seat_id = create_seat.seat.id
        session_id = create_seat.session.id
        response = self.buy_seats(session_id=session_id, seat_ids=[seat_id], access_token=user_access_token)
        create_seat.refresh_from_db()
        self.assertEqual(
            response.status_code,
            201
        )
        self.assertEqual(
            create_seat.status,
            'Sold'
        )

    def test_buying_a_seat_that_has_already_been_purchased(self):
        admin_access_token = self.get_admin_access_token()
        user_access_token = self.get_user_access_token()
        create_seat = self.create_available_seat()
        seat = create_seat.seat
        seat_id = create_seat.seat.id
        session_id = create_seat.session.id
        admin_buy = self.buy_seats(session_id=session_id, seat_ids=[seat_id], access_token=admin_access_token)
        self.assertEqual(
            admin_buy.status_code,
            201
        )
        create_seat.refresh_from_db()
        self.assertEqual(
            create_seat.status,
            'Sold'
        )
        user_try_to_buy_same_seat = self.buy_seats(session_id=session_id, seat_ids=[seat_id], access_token=user_access_token)
        self.assertEqual(
            user_try_to_buy_same_seat.status_code,
            400
        )
        self.assertEqual(
            user_try_to_buy_same_seat.data.get('error'),
            f"Seats unavailable: {seat.row}{seat.number}"
        )

    def test_seat_buying_a_seat_that_has_already_been_reserved_by_other_user(self):
        admin_access_token = self.get_admin_access_token()
        user_access_token = self.get_user_access_token()
        create_seat = self.create_available_seat()
        seat = create_seat.seat
        seat_id = create_seat.seat.id
        session_id = create_seat.session.id
        admin_reserve = self.reserve_seats(session_id=session_id, seat_ids=[seat_id], access_token=admin_access_token)
        reserved_seats = admin_reserve.data.get('reserved_seats')[0]
        self.assertEqual(admin_reserve.status_code, 
            200
        )
        self.assertEqual(
            reserved_seats.get('status'),
            'Reserved'
        )
        user_try_to_buy = self.buy_seats(session_id=session_id, seat_ids=[seat_id], access_token=user_access_token)
        self.assertEqual(
            user_try_to_buy.status_code, 
            400
        )
        self.assertEqual(
            user_try_to_buy.data.get('error'),
            f"Seats unavailable: {seat.row}{seat.number}"
        )

    def test_buy_a_seat_that_the_user_reserved_himself(self):
        user_access_token = self.get_user_access_token()
        create_seat = self.create_available_seat()
        seat = create_seat.seat
        session = create_seat.session
        seat_id = create_seat.seat.id
        session_id = create_seat.session.id
        reserve_response = self.reserve_seats(session_id=session_id, seat_ids=[seat_id], access_token=user_access_token)
        self.assertEqual(
            reserve_response.status_code,
            200
        )
        buy_response = self.buy_seats(session_id=session_id, seat_ids=[seat_id], access_token=user_access_token)
        ticket = buy_response.data['tickets'][0]
        self.assertEqual(
            buy_response.status_code,
            201
        )
        self.assertEqual(
            buy_response.data.get('movie'),
            session.movie.title
        )
        self.assertEqual(
            ticket.get('seat'),
            f"{seat.row}{seat.number}"
        )
        self.assertIsNotNone(ticket.get('ticket_code'))

    def test_celery_task_releases_seat_after_timeout(self):
        create_seat = self.create_available_seat()
        seat_id = create_seat.seat.id
        session_id = create_seat.session.id
        self.reserve_seats(
            session_id=session_id,
            seat_ids=[seat_id],
            access_token=self.get_user_access_token()
        )
        create_seat.refresh_from_db()
        create_seat.reserved_until = timezone.now() - timedelta(minutes=1)
        create_seat.save()
        update_seat_status_after_timeout(create_seat.id)
        create_seat.refresh_from_db()
        self.assertEqual(create_seat.status, 'Available')
        self.assertIsNone(create_seat.reserved_until)

    def test_celery_task_when_if_not_seat_session(self):
        logger_name = 'cinema.tasks'
        with self.assertLogs(logger_name, level='INFO') as log:
            update_seat_status_after_timeout(seat_session_id=999)
        self.assertIn(
            "SeatSession 999 not found",
            log.output[0]
        )

    @patch('cinema.views.sessionviews.send_ticket_email.delay')
    def test_celery_task_send_email_after_purchase(self, mock_send_email):
        user, user_access_token = self.get_user_and_access_token()
        create_seat = self.create_available_seat()
        seat_id = create_seat.seat.id
        session_id = create_seat.session.id
        response = self.buy_seats(
            session_id=session_id,
            seat_ids=[seat_id],
            access_token=user_access_token
        )
        ticket = response.data.get('tickets')
        self.assertEqual(response.status_code, 201)
        mock_send_email.assert_called_once_with(
            user.email,
            response.data.get('movie'),
            ticket
        )

    def test_seat_reserve_with_invalid_seat_id_return_code_400(self):
        seat = self.create_available_seat()
        seat_id = ["abc"]
        response = self.reserve_seats(
            session_id=seat.session.id,
            seat_ids=seat_id,
            access_token=self.get_user_access_token()
        )
        self.assertEqual(
            response.status_code,
            400
        )
        self.assertEqual(
            response.data.get('error'),
            f'Invalid seat_id: {seat_id[0]}'
        )

    def test_seat_reserve_verify_status_and_expire_time_and_reset_to_available(self):
        user_access_token = self.get_user_access_token()
        admin_access_token = self.get_admin_access_token()
        create_seat = self.create_available_seat()
        seat_id = create_seat.seat.id
        session_id = create_seat.session.id
        self.reserve_seats(
            session_id=session_id,
            seat_ids=[seat_id],
            access_token=admin_access_token
        )
        create_seat.status = 'Reserved'
        create_seat.reserved_until = timezone.now() - timedelta(minutes=2)
        create_seat.save()
        create_seat.refresh_from_db()
        response = self.reserve_seats(       
            session_id=session_id,
            seat_ids=[seat_id],
            access_token=user_access_token
        )
        self.assertEqual(
            response.status_code,
            200
        )
    
    def test_seat_reserve_trying_to_reserve_a_seat_already_reserved_for_another_user(self):
        user_access_token = self.get_user_access_token()
        admin_access_token = self.get_admin_access_token()
        create_seat = self.create_available_seat()
        seat = create_seat.seat
        seat_id = create_seat.seat.id
        session_id = create_seat.session.id
        self.reserve_seats(
            session_id=session_id,
            seat_ids=[seat_id],
            access_token=admin_access_token
        )
        response = self.reserve_seats(
            session_id=session_id,
            seat_ids=[seat_id],
            access_token=user_access_token
        )
        self.assertEqual(
            response.status_code,
            400
        )
        self.assertEqual(
            response.data.get('error'),
            f'Seats unavailable: {seat.row}{seat.number}'
        )

    def test_seat_buy_verify_status_and_expire_time_and_reset_to_available(self):
        user_access_token = self.get_user_access_token()
        create_seat = self.create_available_seat()
        session_id = create_seat.session.id
        seat_id = create_seat.seat.id
        create_seat.status = 'Reserved'
        create_seat.reserved_until = timezone.now() - timedelta(minutes=2)
        create_seat.save()
        response = self.buy_seats(
            session_id=session_id,
            seat_ids=[seat_id],
            access_token=user_access_token
        )
        self.assertEqual(
            response.status_code, 
            201
        )

    def test_seat_buy_with_invalid_seat_id_return_code_400(self):
        seat = self.create_available_seat()
        seat_id = ["abc"]
        response = self.buy_seats(
            session_id=seat.session.id,
            seat_ids=seat_id,
            access_token=self.get_user_access_token()
        )
        self.assertEqual(
            response.status_code,
            400
        )
        self.assertEqual(
            response.data.get('error'),
            f'Invalid seat_id: {seat_id[0]}'
        )
    
    def test_rate_limiting_in_non_user_seat_retrieve(self):
        session = self.create_session()
        api_url = reverse('sessions-seats', args=[session.id])
        responses = []
        for s in range(16):
            response = self.client.get(api_url)
            responses.append(response.status_code)
        self.assertIn(
            429,
            responses
        )
    
    def test_rate_limiting_in_user_seat_retrieve(self):
        user_access_token = self.get_user_access_token()
        session = self.create_session()
        api_url = reverse('sessions-seats', args=[session.id])
        responses = []
        for s in range(31):
            response = self.client.get(api_url, HTTP_AUTHORIZATION=f'Bearer {user_access_token}')
            responses.append(response.status_code)
        self.assertIn(
            429,
            responses
        )

    def test_rate_limiting_in_seat_reserve(self):
        user_access_token = self.get_user_access_token()
        create_seat = self.create_available_seat()
        session_id = create_seat.session.id
        seat_id = create_seat.seat.id
        responses = []
        for s in range(11):
            response = self.reserve_seats(
            session_id=session_id,
            seat_ids=[seat_id],
            access_token=user_access_token
        )
            responses.append(response.status_code)
        self.assertIn(
            429,
            responses
        )

    def test_rate_limiting_in_seat_buy(self):
        user_access_token = self.get_user_access_token()
        create_seat = self.create_available_seat()
        session_id = create_seat.session.id
        seat_id = create_seat.seat.id
        responses = []
        for s in range(11):
            response = self.buy_seats(
            session_id=session_id,
            seat_ids=[seat_id],
            access_token=user_access_token
        )
            responses.append(response.status_code)
        self.assertIn(
            429,
            responses
        )

    def test_trying_to_reserve_seat_thats_already_passed_error_400(self):
        user_access_token = self.get_user_access_token()
        create_expired_seat = self.create_expired_seat()
        session_id = create_expired_seat.session.id
        expired_seat_id = create_expired_seat.seat.id
        response = self.reserve_seats(
            session_id=session_id,
            seat_ids=[expired_seat_id],
            access_token=user_access_token
        )
        self.assertEqual(
            response.status_code,
            400
        )
        self.assertEqual(
            response.data.get('error'),
            'The session has already passed.'
        )

    def test_trying_to_buy_seat_thats_session_already_passed_error_400(self):
        user_access_token = self.get_user_access_token()
        create_expired_seat = self.create_expired_seat()
        session_id = create_expired_seat.session.id
        expired_seat_id = create_expired_seat.seat.id
        response = self.buy_seats(
            session_id=session_id,
            seat_ids=[expired_seat_id],
            access_token=user_access_token
        )
        self.assertEqual(
            response.status_code,
            400
        )
        self.assertEqual(
            response.data.get('error'),
            'The session has already passed.'
        )

    def test_reserve_seat_ids_request_isnt_a_list_instance(self):
        user_access_token = self.get_user_access_token()
        create_seat = self.create_available_seat()
        session_id = create_seat.session.id
        seat_id = create_seat.seat.id
        response = self.reserve_seats(
            session_id=session_id,
            seat_ids=seat_id,
            access_token=user_access_token
        )
        self.assertEqual(
            response.status_code,
            400
        )
        self.assertEqual(
            response.data.get('error'),
            'seat_ids must be a non-empty list.'
        )
    
    def test_buy_seat_ids_request_isnt_a_list_instance(self):
        user_access_token = self.get_user_access_token()
        create_seat = self.create_available_seat()
        session_id = create_seat.session.id
        seat_id = create_seat.seat.id
        response = self.buy_seats(
            session_id=session_id,
            seat_ids=seat_id,
            access_token=user_access_token
        )
        self.assertEqual(
            response.status_code,
            400
        )
        self.assertEqual(
            response.data.get('error'),
            'seat_ids must be a non-empty list.'
        )

    def test_if_reserve_seat_ids_request_is_empty(self):
        user_access_token = self.get_user_access_token()
        create_seat = self.create_available_seat()
        session_id = create_seat.session.id
        response = self.reserve_seats(
            session_id=session_id,
            seat_ids=[],
            access_token=user_access_token
        )
        self.assertEqual(
            response.status_code,
            400
        )
        self.assertEqual(
            response.data.get('error'),
            'seat_ids must be a non-empty list.'
        )

    def test_if_buy_seat_ids_request_is_empty(self):
        user_access_token = self.get_user_access_token()
        create_seat = self.create_available_seat()
        session_id = create_seat.session.id
        response = self.buy_seats(
            session_id=session_id,
            seat_ids=[],
            access_token=user_access_token
        )
        self.assertEqual(
            response.status_code,
            400
        )
        self.assertEqual(
            response.data.get('error'),
            'seat_ids must be a non-empty list.'
        )

    def test_if_reserve_seat_ids_request_lenght_is_different_than_seat_sessions_lenght(self):
        user = self.get_user_access_token()
        seat = self.create_available_seat()
        session_id = seat.session.id

        valid_id = seat.id
        invalid_id = 99999

        response = self.reserve_seats(
            session_id=session_id,
            seat_ids=[valid_id, invalid_id],
            access_token=user
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.data.get('error'),
            "One or more seats not found."
        )

    def test_if_buy_seat_ids_request_lenght_is_different_than_seat_sessions_lenght(self):
        user = self.get_user_access_token()
        seat = self.create_available_seat()
        session_id = seat.session.id

        valid_id = seat.id
        invalid_id = 99999

        response = self.buy_seats(
            session_id=session_id,
            seat_ids=[valid_id, invalid_id],
            access_token=user
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.data.get('error'),
            "One or more seats not found."
        )

class SeatConcurrencyTest(test.APITransactionTestCase, jwt_mixins.JWTMixin, seat_mixins.SeatMixin):
    def test_concurrent_reserve_same_seat(self):
        user1 = self.get_user_access_token()
        user2 = self.get_admin_access_token()
        create_seat = self.create_available_seat()
        session_id = create_seat.session.id
        seat_id = create_seat.id
        data = {
            'seat_ids': [seat_id]
        }
        responses = []
        def reserve(user):
            client = test.APIClient()
            client.credentials(HTTP_AUTHORIZATION=f'Bearer {user}')
            response = client.post(
                reverse('sessions-reserve', args=[session_id]),
                data,
                format='json'
            )
            responses.append(response.status_code)
            connections.close_all()

        t1 = threading.Thread(target=reserve, args=(user1,))
        t2 = threading.Thread(target=reserve, args=(user2,))

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        self.assertIn(
            200,
            responses
        )
        self.assertIn(
            400,
            responses
        )

    def test_concurrent_buy_same_seat(self):
        user1 = self.get_user_access_token()
        user2 = self.get_admin_access_token()
        create_seat = self.create_available_seat()
        session_id = create_seat.session.id
        seat_id = create_seat.id
        data = {
            'seat_ids': [seat_id]
        }
        responses = []
        def buy(user):
            client = test.APIClient()
            client.credentials(HTTP_AUTHORIZATION=f'Bearer {user}')
            response = client.post(
                reverse('sessions-buy', args=[session_id]),
                data,
                format='json'
            )
            responses.append(response.status_code)
            connections.close_all()

        t1 = threading.Thread(target=buy, args=(user1,))
        t2 = threading.Thread(target=buy, args=(user2,))

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        self.assertIn(
            201,
            responses
        )
        self.assertIn(
            400,
            responses
        )