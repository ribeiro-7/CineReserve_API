from rest_framework import test
from cinema.tests.mixins import seat_mixins
from django.urls import reverse
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from accounts.tests.mixins import jwt_mixins

class BookingTest(test.APITestCase, jwt_mixins.JWTMixin, seat_mixins.SeatMixin):
    def test_booking_history_list_returns_all_bookings_200_ok(self):
        token = self.get_user_access_token()
        create_seats = self.create_seats()
        session_id = create_seats['session'].id
        seat1_id = create_seats['seat_sessions'][0].id
        seat2_id = create_seats['seat_sessions'][1].id

        self.buy_seats(
            session_id=session_id,
            seat_ids=[seat1_id, seat2_id],
            access_token=token
        )

        api_url = reverse('bookings-list')
        response = self.client.get(api_url, HTTP_AUTHORIZATION=f'Bearer {token}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        booking = response.data[0]

        self.assertEqual(booking['status'], 'completed')
        self.assertEqual(len(booking['tickets']), 2)

    def test_booking_upcoming_list_returns_only_future_sessions(self):
        user_access_token = self.get_user_access_token()

        seat = self.create_available_seat()

        buy = self.buy_seats(
            session_id=seat.session.id,
            seat_ids=[seat.id],
            access_token=user_access_token
        )

        api_url = reverse('bookings-list') + '?type=upcoming'
        response = self.client.get(api_url, HTTP_AUTHORIZATION=f'Bearer {user_access_token}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], buy.data.get('booking_id'))

    def test_booking_past_list_returns_only_past_sessions(self):
        user_access_token = self.get_user_access_token()

        seat = self.create_available_seat()

        buy = self.buy_seats(
            session_id=seat.session.id,
            seat_ids=[seat.id],
            access_token=user_access_token
        )

        session = seat.session
        session.date = timezone.now().date() - timedelta(days=1)
        session.showtime = (timezone.now() - timedelta(hours=2)).time()
        session.save()

        api_url = reverse('bookings-list') + '?type=past'
        response = self.client.get(api_url, HTTP_AUTHORIZATION=f'Bearer {user_access_token}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], buy.data.get('booking_id'))

    def test_multiple_bookings_are_listed(self):
        token = self.get_user_access_token()

        seat1 = self.create_available_seat()
        seat2 = self.create_available_seat(number='2')

        self.buy_seats(
            session_id=seat1.session.id,
            seat_ids=[seat1.id],
            access_token=token
        )

        self.buy_seats(
            session_id=seat2.session.id,
            seat_ids=[seat2.id],
            access_token=token
        )

        api_url = reverse('bookings-list')
        response = self.client.get(api_url, HTTP_AUTHORIZATION=f'Bearer {token}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_booking_contains_correct_ticket_codes(self):
        token = self.get_user_access_token()

        seat = self.create_available_seat()

        buy = self.buy_seats(
            session_id=seat.session.id,
            seat_ids=[seat.id],
            access_token=token
        )

        ticket_code = buy.data['tickets'][0]['ticket_code']

        api_url = reverse('bookings-list')
        response = self.client.get(api_url, HTTP_AUTHORIZATION=f'Bearer {token}')

        booking = response.data[0]
        returned_codes = [t['code'] for t in booking['tickets']]

        self.assertIn(ticket_code, returned_codes)

    def test_user_cannot_see_other_users_bookings(self):
        user1 = self.get_user_access_token()
        user2 = self.get_admin_access_token()

        seat = self.create_available_seat()

        self.buy_seats(
            session_id=seat.session.id,
            seat_ids=[seat.id],
            access_token=user1
        )

        api_url = reverse('bookings-list')
        response = self.client.get(api_url, HTTP_AUTHORIZATION=f'Bearer {user2}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    