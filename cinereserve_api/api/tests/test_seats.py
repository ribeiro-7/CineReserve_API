from rest_framework import test
from django.urls import reverse
from .mixins import seat_mixins, jwt_mixins
from django.utils import timezone
from datetime import timedelta
from api.tasks import update_seat_status_after_timeout

class SeatTest(test.APITestCase, seat_mixins.SeatMixin, jwt_mixins.JWTMixin):
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
        seat = self.create_available_seat()
        api_url = reverse('sessions-reserve', args=[seat.session.id])
        data = {
            'seat_id': seat.id
        }
        response = self.client.post(api_url, data=data)
        self.assertEqual(
            response.status_code,
            401
        )

    def test_seat_reserve_change_status_after_reserve_and_code_200_ok(self):
        user_access_token = self.get_user_access_token()
        seat = self.create_available_seat()
        self.assertEqual(
            seat.status,
            'Available'
        )
        reserving_seat = self.reserve_seat(session_id=seat.session.id, seat_id=seat.id, access_token=user_access_token)
        self.assertEqual(reserving_seat.status_code, 200)
        self.assertEqual(
            reserving_seat.data.get('status'),
            'Reserved'
        )

    def test_seat_trying_to_reserve_a_seat_thats_already_reserved_by_other_person_code_400(self):
        user_access_token = self.get_user_access_token()
        admin_access_token = self.get_admin_access_token()
        seat = self.create_available_seat()
        reserving_seat_with_admin_user = self.reserve_seat(session_id=seat.session.id, seat_id=seat.id, access_token=admin_access_token)
        self.assertEqual(reserving_seat_with_admin_user.status_code, 200)
        self.assertEqual(
            reserving_seat_with_admin_user.data.get('status'),
            'Reserved'
        )
        trying_to_reserve_with_different_user = self.reserve_seat(session_id=seat.session.id, seat_id=seat.id, access_token=user_access_token)
        self.assertEqual(trying_to_reserve_with_different_user.status_code, 400)
        self.assertEqual(
            trying_to_reserve_with_different_user.data.get('error'),
            "This seat is already Reserved"
        )

    def test_seat_trying_to_reserve_a_seat_thats_already_sold_returns_code_400(self):
        user_access_token = self.get_user_access_token()
        admin_access_token = self.get_admin_access_token()
        seat = self.create_available_seat()
        buying_seat = self.buy_seat(session_id=seat.session.id, seat_id=seat.id, access_token=admin_access_token)
        self.assertEqual(buying_seat.status_code, 201)
        trying_to_reserve_sold_seat = self.reserve_seat(session_id=seat.session.id, seat_id=seat.id, access_token=user_access_token)
        self.assertEqual(trying_to_reserve_sold_seat.status_code, 400)
        self.assertEqual(
            trying_to_reserve_sold_seat.data.get('error'),
            "This seat is already Sold"
        )

    def test_seat_buy_available_seat_return_ticket_and_code_201(self):
        user_access_token = self.get_user_access_token()
        seat = self.create_available_seat()
        buying_seat = self.buy_seat(session_id=seat.session.id, seat_id=seat.id, access_token=user_access_token)
        self.assertEqual(buying_seat.status_code, 201)
        self.assertEqual(
            buying_seat.data.get('movie'),
            seat.session.movie.title
        )
        self.assertEqual(
            buying_seat.data.get('movie'),
            seat.session.movie.title
        )
        self.assertEqual(
            buying_seat.data.get('seat'),
            f'{seat.seat.row}{seat.seat.number}'
        )
        self.assertIsNotNone(
            buying_seat.data.get('ticket-code'),
        )
        
    def test_seat_buy_dont_work_with_unauthenticated_user_and_code_401_unauthorized(self):
        seat = self.create_available_seat()
        response = self.buy_seat(session_id=seat.session.id, seat_id=seat.id)
        self.assertEqual(
            response.status_code,
            401
        )

    def test_seat_buy_change_status_after_buy_and_code_201_ok(self):
        user_access_token = self.get_user_access_token()
        seat = self.create_available_seat()
        response = self.buy_seat(session_id=seat.session.id, seat_id=seat.id, access_token=user_access_token)
        self.assertEqual(
            response.status_code,
            201
        )
        seat.refresh_from_db()
        self.assertEqual(
            seat.status,
            'Sold'
        )

    def test_seat_buying_a_seat_that_has_already_been_purchased(self):
        admin_access_token = self.get_admin_access_token()
        user_access_token = self.get_user_access_token()
        seat = self.create_available_seat()
        admin_buy = self.buy_seat(session_id=seat.session.id, seat_id=seat.id, access_token=admin_access_token)
        self.assertEqual(
            admin_buy.status_code,
            201
        )
        seat.refresh_from_db()
        self.assertEqual(
            seat.status,
            'Sold'
        )
        user_try_to_buy_same_seat = self.buy_seat(session_id=seat.session.id, seat_id=seat.id, access_token=user_access_token)
        self.assertEqual(
            user_try_to_buy_same_seat.status_code,
            400
        )
        self.assertEqual(
            user_try_to_buy_same_seat.data.get('error'),
            "This seat is already Sold"
        )

    def test_seat_buying_a_seat_that_has_already_been_reserved_by_other_user(self):
        admin_access_token = self.get_admin_access_token()
        user_access_token = self.get_user_access_token()
        seat = self.create_available_seat()
        admin_reserve = self.reserve_seat(session_id=seat.session.id, seat_id=seat.id, access_token=admin_access_token)
        self.assertEqual(admin_reserve.status_code, 200)
        self.assertEqual(
            admin_reserve.data.get('status'),
            'Reserved'
        )
        user_try_to_buy = self.buy_seat(session_id=seat.session.id, seat_id=seat.id, access_token=user_access_token)
        self.assertEqual(user_try_to_buy.status_code, 400)
        self.assertEqual(
            user_try_to_buy.data.get('error'),
            "This seat is already Reserved"
        )

    def test_buy_a_seat_that_the_user_reserved_himself(self):
        user_access_token = self.get_user_access_token()
        seat = self.create_available_seat()
        user_reserving = self.reserve_seat(session_id=seat.session.id, seat_id=seat.id, access_token=user_access_token)
        self.assertEqual(user_reserving.status_code, 200)
        self.assertEqual(
            user_reserving.data.get('status'),
            'Reserved'
        )
        user_buying = self.buy_seat(session_id=seat.session.id, seat_id=seat.id, access_token=user_access_token)
        self.assertEqual(user_buying.status_code, 201)
        self.assertEqual(
            user_buying.data.get('movie'),
            seat.session.movie.title
        )
        self.assertEqual(
            user_buying.data.get('movie'),
            seat.session.movie.title
        )
        self.assertEqual(
            user_buying.data.get('seat'),
            f'{seat.seat.row}{seat.seat.number}'
        )
        self.assertIsNotNone(
            user_buying.data.get('ticket-code'),
        )

def test_celery_task_releases_seat_after_timeout(self):
    seat = self.create_available_seat()
    self.reserve_seat(
        session_id=seat.session.id,
        seat_id=seat.id,
        access_token=self.get_user_access_token()
    )
    seat.refresh_from_db()
    seat.reserved_until = timezone.now() - timedelta(minutes=1)
    seat.save()
    update_seat_status_after_timeout(seat.id)
    seat.refresh_from_db()
    self.assertEqual(seat.status, 'Available')
    self.assertIsNone(seat.reserved_until)