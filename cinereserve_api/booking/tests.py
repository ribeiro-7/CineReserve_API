from rest_framework import test
from cinema.tests.mixins import jwt_mixins, seat_mixins
from django.urls import reverse
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

class TicketTest(test.APITestCase, jwt_mixins.JWTMixin, seat_mixins.SeatMixin):
    def setUp(self):
        cache.clear()
        
    def test_ticket_history_list_returns_all_tickets_200_ok(self):
        user_access_token = self.get_user_access_token()
        seat1 = self.create_available_seat()
        seat2 = self.create_available_seat(number='2')
        buy1 = self.buy_seat(
            session_id=seat1.session.id,
            seat_id=seat1.id,
            access_token=user_access_token
        )
        buy2 = self.buy_seat(
            session_id=seat2.session.id,
            seat_id=seat2.id,
            access_token=user_access_token
        )
        api_url = reverse('tickets-list')
        response = self.client.get(api_url, HTTP_AUTHORIZATION=f'Bearer {user_access_token}')
        self.assertEqual(
            response.status_code,
            200
        )
        self.assertEqual(
            response.data[0].get('code'),
            buy1.data.get('ticket-code')
        )
        self.assertEqual(
            response.data[1].get('code'),
            buy2.data.get('ticket-code')
        )

    def test_ticket_upcoming_list_returns_all_tickets_200_ok(self):
        user_access_token = self.get_user_access_token()
        seat1 = self.create_available_seat()
        seat2 = self.create_available_seat(number='2')
        buy1 = self.buy_seat(
            session_id=seat1.session.id,
            seat_id=seat1.id,
            access_token=user_access_token
        )
        buy2 = self.buy_seat(
            session_id=seat2.session.id,
            seat_id=seat2.id,
            access_token=user_access_token
        )
        api_url = reverse('tickets-list') + '?type=upcoming'
        response = self.client.get(api_url, HTTP_AUTHORIZATION=f'Bearer {user_access_token}')
        self.assertEqual(
            response.status_code,
            200
        )
        self.assertEqual(
            response.data[0].get('code'),
            buy1.data.get('ticket-code')
        )
        self.assertEqual(
            response.data[1].get('code'),
            buy2.data.get('ticket-code')
        )

    def test_ticket_past_list_returns_all_tickets_200_ok(self):
        user_access_token = self.get_user_access_token()
        seat = self.create_available_seat()
        buy = self.buy_seat(
            session_id=seat.session.id,
            seat_id=seat.id,
            access_token=user_access_token
        )
        session = seat.session
        session.date = timezone.now().date() - timedelta(days=1)
        session.showtime = (timezone.now() - timedelta(hours=2)).time()
        session.save()
        api_url = reverse('tickets-list') + '?type=past'
        response = self.client.get(api_url, HTTP_AUTHORIZATION=f'Bearer {user_access_token}')
        self.assertEqual(
            response.status_code,
            200
        )
        self.assertEqual(
            response.data[0].get('code'),
            buy.data.get('ticket-code')
        )