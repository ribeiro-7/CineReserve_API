from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from booking.models import Booking, Ticket
from cinema.models import Movie, Seat, SeatSession, Session
from cinema.tasks import (
    cancel_booking_after_timeout,
    send_ticket_email,
    update_seat_status_after_timeout_on_reserve,
)

User = get_user_model()


class CinemaTasksTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='task_user',
            email='task@test.com',
            password='Password123#',
        )
        movie = Movie.objects.create(
            title='Task Movie',
            description='Desc',
            duration=100,
            age_rating='L',
            genre='Ação',
            release_date='2025-01-01',
        )
        self.session = Session.objects.create(
            date=timezone.now().date() + timedelta(days=1),
            showtime='19:00',
            theater='Sala 3',
            movie=movie,
            ticket_price=15,
        )
        seat = Seat.objects.create(row='C', number=3)
        self.seat_session = SeatSession.objects.create(
            session=self.session,
            seat=seat,
            status='Reserved',
            reserved_by=self.user,
            reserved_until=timezone.now() - timedelta(minutes=1),
        )

    def test_update_seat_status_releases_expired_reservation(self):
        update_seat_status_after_timeout_on_reserve(self.seat_session.id)
        self.seat_session.refresh_from_db()
        self.assertEqual(self.seat_session.status, 'Available')
        self.assertIsNone(self.seat_session.reserved_until)
        self.assertIsNone(self.seat_session.reserved_by)

    def test_update_seat_status_ignores_non_expired_reservation(self):
        self.seat_session.reserved_until = timezone.now() + timedelta(minutes=5)
        self.seat_session.save()

        update_seat_status_after_timeout_on_reserve(self.seat_session.id)
        self.seat_session.refresh_from_db()
        self.assertEqual(self.seat_session.status, 'Reserved')

    def test_update_seat_status_when_seat_session_missing(self):
        with self.assertLogs('cinema.tasks', level='INFO') as logs:
            update_seat_status_after_timeout_on_reserve(99999)
        self.assertIn('SeatSession 99999 not found', logs.output[0])

    def test_cancel_booking_after_timeout_cancels_expired_pending(self):
        booking = Booking.objects.create(
            user=self.user,
            session=self.session,
            status='pending',
        )
        Ticket.objects.create(
            user=self.user,
            booking=booking,
            seat_session=self.seat_session,
            code='cancel-code',
            price=15,
        )

        cancel_booking_after_timeout(booking.id)

        booking.refresh_from_db()
        self.seat_session.refresh_from_db()
        self.assertEqual(booking.status, 'cancelled')
        self.assertEqual(self.seat_session.status, 'Available')

    def test_cancel_booking_after_timeout_ignores_completed(self):
        booking = Booking.objects.create(
            user=self.user,
            session=self.session,
            status='completed',
        )

        cancel_booking_after_timeout(booking.id)

        booking.refresh_from_db()
        self.assertEqual(booking.status, 'completed')

    @patch('cinema.tasks.send_mail')
    def test_send_ticket_email(self, mock_send_mail):
        tickets = [
            {'seat': 'A1', 'ticket_code': 'code-123'},
        ]
        send_ticket_email('user@test.com', 'Task Movie', tickets)
        mock_send_mail.assert_called_once()
        self.assertIn('user@test.com', mock_send_mail.call_args[0][3])
