from rest_framework import test
from cinema.tests.mixins import seat_mixins
from django.urls import reverse
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from accounts.tests.mixins import jwt_mixins

class TicketTest(test.APITestCase, jwt_mixins.JWTMixin, seat_mixins.SeatMixin):
    def setUp(self):
        cache.clear()

    def test_ticket_history_list_returns_all_tickets_200_ok(self):
        token = self.get_user_access_token()
        seat1 = self.create_available_seat()
        seat2 = self.create_available_seat(number='2')
        buy1 = self.buy_seats(
            session_id=seat1.session.id,
            seat_ids=[seat1.id],
            access_token=token
        )
        buy2 = self.buy_seats(
            session_id=seat2.session.id,
            seat_ids=[seat2.id],
            access_token=token
        )

        api_url = reverse('tickets-list')
        response = self.client.get(api_url, HTTP_AUTHORIZATION=f'Bearer {token}')

        self.assertEqual(response.status_code, 200)

        returned_codes = [ticket['code'] for ticket in response.data]

        self.assertIn(buy1.data['tickets'][0]['ticket_code'], returned_codes)
        self.assertIn(buy2.data['tickets'][0]['ticket_code'], returned_codes)

    def test_ticket_upcoming_list_returns_all_tickets_200_ok(self):
        token = self.get_user_access_token()
        seat1 = self.create_available_seat()
        seat2 = self.create_available_seat(number='2')

        buy1 = self.buy_seats(
            session_id=seat1.session.id,
            seat_ids=[seat1.id],
            access_token=token
        )
        buy2 = self.buy_seats(
            session_id=seat2.session.id,
            seat_ids=[seat2.id],
            access_token=token
        )

        api_url = reverse('tickets-list') + '?type=upcoming'
        response = self.client.get(api_url, HTTP_AUTHORIZATION=f'Bearer {token}')

        self.assertEqual(response.status_code, 200)

        returned_codes = [ticket['code'] for ticket in response.data]

        self.assertIn(buy1.data['tickets'][0]['ticket_code'], returned_codes)
        self.assertIn(buy2.data['tickets'][0]['ticket_code'], returned_codes)

    def test_ticket_past_list_returns_all_tickets_200_ok(self):
        token = self.get_user_access_token()
        seat = self.create_available_seat()

        buy = self.buy_seats(
            session_id=seat.session.id,
            seat_ids=[seat.id],
            access_token=token
        )

        session = seat.session
        past = timezone.now() - timedelta(days=1)
        session.date = past.date()
        session.showtime = past.time()
        session.save()

        api_url = reverse('tickets-list') + '?type=past'
        response = self.client.get(api_url, HTTP_AUTHORIZATION=f'Bearer {token}')

        self.assertEqual(response.status_code, 200)

        returned_codes = [ticket['code'] for ticket in response.data]

        self.assertIn(buy.data['tickets'][0]['ticket_code'], returned_codes)