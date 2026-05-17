from unittest.mock import patch

from django.urls import reverse
from rest_framework import test

from accounts.tests.mixins import jwt_mixins
from cinema.tests.mixins.payment_mixins import PaymentMixin
from cinema.tests.mixins.seat_mixins import SeatMixin
from payments.models import Payment


class WebhookIntegrationTest(test.APITestCase, jwt_mixins.JWTMixin, SeatMixin, PaymentMixin,):
    def setUp(self):
        self.start_flutterwave_mocks()

    def tearDown(self):
        self.stop_flutterwave_mocks()

    @patch('payments.services.send_ticket_email.delay')
    def test_buy_then_webhook_completes_booking(self, mock_email):
        token = self.get_user_access_token()
        seat = self.create_available_seat()

        buy_response = self.buy_seats(
            session_id=seat.session.id,
            seat_ids=[seat.id],
            access_token=token,
        )
        self.assertEqual(buy_response.status_code, 201)
        seat.refresh_from_db()
        self.assertEqual(seat.status, 'Reserved')

        webhook_response = self.complete_payment_via_webhook(
            buy_response.data['booking_id'],
            amount=float(buy_response.data['amount']),
        )
        self.assertEqual(webhook_response.status_code, 200)

        seat.refresh_from_db()
        payment = Payment.objects.get(booking_id=buy_response.data['booking_id'])

        self.assertEqual(seat.status, 'Sold')
        self.assertEqual(payment.status, 'successful')
        self.assertTrue(payment.email_sent)
        mock_email.assert_called_once()

    def test_tickets_empty_before_webhook(self):
        token = self.get_user_access_token()
        seat = self.create_available_seat()

        self.buy_seats(
            session_id=seat.session.id,
            seat_ids=[seat.id],
            access_token=token,
        )

        tickets_url = reverse('tickets-list')
        response = self.client.get(
            tickets_url,
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)
