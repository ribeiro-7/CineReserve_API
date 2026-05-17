from django.urls import reverse
from django.test import TestCase


class PaymentCallbackTest(TestCase):
    def test_payment_callback_returns_ok(self):
        response = self.client.get(reverse('payment_callback'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')
