import json
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.urls import reverse

from payments.models import Payment


class PaymentMixin:
    def start_flutterwave_mocks(self, verify_amount=None):
        self._verify_amount = verify_amount
        self.flw_post_patcher = patch('payments.services.requests.post')
        self.flw_get_patcher = patch('payments.services.requests.get')
        self.mock_flw_post = self.flw_post_patcher.start()
        self.mock_flw_get = self.flw_get_patcher.start()
        self._configure_flutterwave_create_mock()
        self._configure_flutterwave_verify_mock(verify_amount)

    def stop_flutterwave_mocks(self):
        self.flw_post_patcher.stop()
        self.flw_get_patcher.stop()

    def _configure_flutterwave_create_mock(self):
        create_response = MagicMock()
        create_response.status_code = 200
        create_response.json.return_value = {
            'data': {'link': 'https://pay.test/link'}
        }
        self.mock_flw_post.return_value = create_response

    def _configure_flutterwave_verify_mock(self, amount=None, currency='USD', status='successful'):
        verify_response = MagicMock()
        verify_response.status_code = 200
        verify_response.json.return_value = {
            'data': {
                'amount': amount if amount is not None else 10.0,
                'currency': currency,
                'status': status,
            }
        }
        self.mock_flw_get.return_value = verify_response

    def complete_payment_via_webhook(self, booking_id, amount=None):
        payment = Payment.objects.get(booking_id=booking_id)
        if amount is None:
            amount = float(payment.amount)
        self._configure_flutterwave_verify_mock(amount)
        payload = {'txRef': payment.tx_ref, 'id': '12345'}
        return self.client.post(
            reverse('flutterwave_webhook'),
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_VERIF_HASH=settings.FLW_SECRET_HASH,
        )

    def buy_and_complete_seats(self, session_id, seat_ids, access_token):
        response = self.buy_seats(
            session_id=session_id,
            seat_ids=seat_ids,
            access_token=access_token,
        )
        if response.status_code == 201:
            amount = float(response.data['amount'])
            webhook_response = self.complete_payment_via_webhook(
                response.data['booking_id'],
                amount=amount,
            )
            self.assertEqual(webhook_response.status_code, 200)
        return response
