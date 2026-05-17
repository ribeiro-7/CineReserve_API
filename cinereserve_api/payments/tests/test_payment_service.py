import json
from datetime import timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.utils import timezone

from booking.models import Booking, Ticket
from cinema.models import Movie, Seat, SeatSession, Session
from payments.models import Payment
from payments.services import PaymentService

User = get_user_model()


class PaymentServiceTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='pay_user',
            email='pay@test.com',
            password='Password123#',
        )
        movie = Movie.objects.create(
            title='Pay Movie',
            description='Desc',
            duration=110,
            age_rating='L',
            genre='Ação',
            release_date='2025-01-01',
        )
        self.session = Session.objects.create(
            date=timezone.now().date() + timedelta(days=1),
            showtime='21:00',
            theater='Sala 4',
            movie=movie,
            ticket_price=Decimal('30.00'),
        )
        seat = Seat.objects.create(row='D', number=4)
        self.seat_session = SeatSession.objects.create(
            session=self.session,
            seat=seat,
            status='Reserved',
            reserved_by=self.user,
            reserved_until=timezone.now() + timedelta(minutes=5),
        )
        self.booking = Booking.objects.create(
            user=self.user,
            session=self.session,
            status='pending',
        )
        self.ticket = Ticket.objects.create(
            user=self.user,
            booking=self.booking,
            seat_session=self.seat_session,
            code='pay-ticket-code',
            price=Decimal('30.00'),
        )

    @patch('payments.services.requests.post')
    def test_create_payment_for_booking(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {'link': 'https://pay.test/checkout'}
        }
        mock_post.return_value = mock_response

        link = PaymentService.create_payment_for_booking(self.booking)

        self.assertEqual(link, 'https://pay.test/checkout')
        payment = Payment.objects.get(booking=self.booking)
        self.assertEqual(payment.amount, Decimal('30.00'))
        self.booking.refresh_from_db()
        self.assertIsNotNone(self.booking.expires_at)

    @patch('payments.services.requests.post')
    def test_create_payment_flutterwave_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = 'error'
        mock_post.return_value = mock_response

        with self.assertRaises(Exception) as ctx:
            PaymentService.create_payment_for_booking(self.booking)

        self.assertIn('Flutterwave error', str(ctx.exception))

    @patch('payments.services.requests.get')
    def test_verify_flutterwave_transaction(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'amount': 30.0,
                'currency': 'USD',
                'status': 'successful',
            }
        }
        mock_get.return_value = mock_response

        data = PaymentService.verify_flutterwave_transaction('flw-123')
        self.assertEqual(data['status'], 'successful')

    @patch('payments.services.requests.get')
    def test_verify_flutterwave_transaction_empty_data(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': None}
        mock_get.return_value = mock_response

        with self.assertRaises(Exception) as ctx:
            PaymentService.verify_flutterwave_transaction('flw-123')

        self.assertIn('empty', str(ctx.exception))

    @patch('payments.services.requests.get')
    def test_verify_flutterwave_transaction_http_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'server error'
        mock_get.return_value = mock_response

        with self.assertRaises(Exception) as ctx:
            PaymentService.verify_flutterwave_transaction('flw-123')

        self.assertIn('Flutterwave verify error', str(ctx.exception))

    @patch('payments.services.send_ticket_email.delay')
    def test_finalize_successful_payment(self, mock_email):
        payment = Payment.objects.create(
            booking=self.booking,
            tx_ref='booking-test-ref',
            amount=Decimal('30.00'),
        )

        PaymentService.finalize_successful_payment(
            payment,
            self.booking,
            'flw-success-id',
        )

        payment.refresh_from_db()
        self.booking.refresh_from_db()
        self.seat_session.refresh_from_db()

        self.assertEqual(payment.status, 'successful')
        self.assertEqual(self.booking.status, 'completed')
        self.assertEqual(self.seat_session.status, 'Sold')
        self.assertTrue(payment.email_sent)
        mock_email.assert_called_once()

    def test_fail_payment(self):
        payment = Payment.objects.create(
            booking=self.booking,
            tx_ref='booking-fail-ref',
            amount=Decimal('30.00'),
        )

        PaymentService.fail_payment(payment)

        payment.refresh_from_db()
        self.assertEqual(payment.status, 'failed')

    def test_process_webhook_invalid_hash(self):
        request = self.factory.post(
            '/payments/webhook/',
            data=json.dumps({'txRef': 'x', 'id': 1}),
            content_type='application/json',
            HTTP_VERIF_HASH='wrong-hash',
        )

        response = PaymentService.process_flutterwave_webhook(request)
        self.assertEqual(response.status_code, 401)

    def test_process_webhook_invalid_json(self):
        from django.conf import settings

        request = self.factory.post(
            '/payments/webhook/',
            data='not-json',
            content_type='application/json',
            HTTP_VERIF_HASH=settings.FLW_SECRET_HASH,
        )

        response = PaymentService.process_flutterwave_webhook(request)
        self.assertEqual(response.status_code, 400)

    def test_process_webhook_missing_tx_ref(self):
        from django.conf import settings

        request = self.factory.post(
            '/payments/webhook/',
            data=json.dumps({'id': 1}),
            content_type='application/json',
            HTTP_VERIF_HASH=settings.FLW_SECRET_HASH,
        )

        response = PaymentService.process_flutterwave_webhook(request)
        self.assertEqual(response.status_code, 400)

    @patch('payments.services.PaymentService.verify_flutterwave_transaction')
    def test_process_webhook_success(self, mock_verify):
        from django.conf import settings

        payment = Payment.objects.create(
            booking=self.booking,
            tx_ref='booking-webhook-ref',
            amount=Decimal('30.00'),
        )
        mock_verify.return_value = {
            'amount': 30.0,
            'currency': 'USD',
            'status': 'successful',
        }

        request = self.factory.post(
            '/payments/webhook/',
            data=json.dumps({'txRef': payment.tx_ref, 'id': '999'}),
            content_type='application/json',
            HTTP_VERIF_HASH=settings.FLW_SECRET_HASH,
        )

        with patch('payments.services.send_ticket_email.delay'):
            response = PaymentService.process_flutterwave_webhook(request)

        self.assertEqual(response.status_code, 200)
        payment.refresh_from_db()
        self.booking.refresh_from_db()
        self.assertEqual(payment.status, 'successful')
        self.assertEqual(self.booking.status, 'completed')

    @patch('payments.services.PaymentService.verify_flutterwave_transaction')
    def test_process_webhook_idempotent_when_already_successful(self, mock_verify):
        from django.conf import settings

        payment = Payment.objects.create(
            booking=self.booking,
            tx_ref='booking-idempotent-ref',
            amount=Decimal('30.00'),
            status='successful',
        )

        request = self.factory.post(
            '/payments/webhook/',
            data=json.dumps({'txRef': payment.tx_ref, 'id': '999'}),
            content_type='application/json',
            HTTP_VERIF_HASH=settings.FLW_SECRET_HASH,
        )

        response = PaymentService.process_flutterwave_webhook(request)

        self.assertEqual(response.status_code, 200)
        mock_verify.assert_not_called()

    @patch('payments.services.PaymentService.verify_flutterwave_transaction')
    def test_process_webhook_fails_on_amount_mismatch(self, mock_verify):
        from django.conf import settings

        payment = Payment.objects.create(
            booking=self.booking,
            tx_ref='booking-mismatch-ref',
            amount=Decimal('30.00'),
        )
        mock_verify.return_value = {
            'amount': 5.0,
            'currency': 'USD',
            'status': 'successful',
        }

        request = self.factory.post(
            '/payments/webhook/',
            data=json.dumps({'txRef': payment.tx_ref, 'id': '999'}),
            content_type='application/json',
            HTTP_VERIF_HASH=settings.FLW_SECRET_HASH,
        )

        response = PaymentService.process_flutterwave_webhook(request)

        self.assertEqual(response.status_code, 200)
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'failed')

    @patch('payments.services.PaymentService.verify_flutterwave_transaction')
    def test_process_webhook_expired_booking(self, mock_verify):
        from django.conf import settings

        self.booking.expires_at = timezone.now() - timedelta(minutes=1)
        self.booking.save()
        payment = Payment.objects.create(
            booking=self.booking,
            tx_ref='booking-expired-ref',
            amount=Decimal('30.00'),
        )

        request = self.factory.post(
            '/payments/webhook/',
            data=json.dumps({'txRef': payment.tx_ref, 'id': '999'}),
            content_type='application/json',
            HTTP_VERIF_HASH=settings.FLW_SECRET_HASH,
        )

        response = PaymentService.process_flutterwave_webhook(request)

        self.assertEqual(response.status_code, 200)
        mock_verify.assert_not_called()
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'cancelled')

    def test_process_webhook_payment_not_found(self):
        from django.conf import settings

        request = self.factory.post(
            '/payments/webhook/',
            data=json.dumps({'txRef': 'missing-ref', 'id': '999'}),
            content_type='application/json',
            HTTP_VERIF_HASH=settings.FLW_SECRET_HASH,
        )

        response = PaymentService.process_flutterwave_webhook(request)
        self.assertEqual(response.status_code, 400)

    @patch('payments.services.PaymentService.verify_flutterwave_transaction')
    def test_process_webhook_cancelled_booking(self, mock_verify):
        from django.conf import settings

        self.booking.status = 'cancelled'
        self.booking.save()
        payment = Payment.objects.create(
            booking=self.booking,
            tx_ref='booking-cancelled-ref',
            amount=Decimal('30.00'),
        )

        request = self.factory.post(
            '/payments/webhook/',
            data=json.dumps({'txRef': payment.tx_ref, 'id': '999'}),
            content_type='application/json',
            HTTP_VERIF_HASH=settings.FLW_SECRET_HASH,
        )

        response = PaymentService.process_flutterwave_webhook(request)

        self.assertEqual(response.status_code, 200)
        mock_verify.assert_not_called()

    @patch('payments.services.PaymentService.verify_flutterwave_transaction')
    def test_process_webhook_verify_error_returns_500(self, mock_verify):
        from django.conf import settings

        payment = Payment.objects.create(
            booking=self.booking,
            tx_ref='booking-verify-error-ref',
            amount=Decimal('30.00'),
        )
        mock_verify.side_effect = Exception('verify failed')

        request = self.factory.post(
            '/payments/webhook/',
            data=json.dumps({'txRef': payment.tx_ref, 'id': '999'}),
            content_type='application/json',
            HTTP_VERIF_HASH=settings.FLW_SECRET_HASH,
        )

        response = PaymentService.process_flutterwave_webhook(request)
        self.assertEqual(response.status_code, 500)
