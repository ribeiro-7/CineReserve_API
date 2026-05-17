from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from booking.models import Booking, Ticket
from cinema.models import Movie, Seat, SeatSession, Session
from cinema.services.booking_service import BookingService

User = get_user_model()


class BookingServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='booking_user',
            password='Password123#',
        )
        self.other_user = User.objects.create_user(
            username='booking_other',
            password='Password123#',
        )
        movie = Movie.objects.create(
            title='Booking Movie',
            description='Desc',
            duration=90,
            age_rating='L',
            genre='Drama',
            release_date='2025-01-01',
        )
        self.session = Session.objects.create(
            date=timezone.now().date() + timedelta(days=2),
            showtime='20:00',
            theater='Sala 2',
            movie=movie,
            ticket_price=25,
        )
        seat = Seat.objects.create(row='B', number=2)
        self.seat_session = SeatSession.objects.create(
            session=self.session,
            seat=seat,
            status='Available',
        )

    @patch('cinema.tasks.cancel_booking_after_timeout.apply_async')
    def test_create_booking_success(self, mock_timeout):
        booking = BookingService.create_booking(
            user=self.user,
            session=self.session,
            seat_ids=[self.seat_session.id],
        )

        self.seat_session.refresh_from_db()
        self.assertEqual(booking.status, 'pending')
        self.assertEqual(self.seat_session.status, 'Reserved')
        self.assertEqual(self.seat_session.reserved_by, self.user)
        self.assertEqual(booking.tickets.count(), 1)
        mock_timeout.assert_called_once()

    def test_create_booking_session_passed(self):
        past = timezone.now() - timedelta(days=1)
        self.session.date = past.date()
        self.session.showtime = past.time()
        self.session.save()

        with self.assertRaises(ValidationError) as ctx:
            BookingService.create_booking(
                user=self.user,
                session=self.session,
                seat_ids=[self.seat_session.id],
            )

        self.assertIn('already passed', str(ctx.exception))

    def test_create_booking_seat_not_found(self):
        with self.assertRaises(NotFound):
            BookingService.create_booking(
                user=self.user,
                session=self.session,
                seat_ids=[99999],
            )

    def test_create_booking_seat_unavailable(self):
        self.seat_session.status = 'Sold'
        self.seat_session.save()

        with self.assertRaises(ValidationError) as ctx:
            BookingService.create_booking(
                user=self.user,
                session=self.session,
                seat_ids=[self.seat_session.id],
            )

        self.assertIn('Seats unavailable', str(ctx.exception))

    def test_cancel_booking_releases_seats(self):
        booking = Booking.objects.create(
            user=self.user,
            session=self.session,
            status='pending',
        )
        self.seat_session.status = 'Reserved'
        self.seat_session.reserved_by = self.user
        self.seat_session.reserved_until = timezone.now() + timedelta(minutes=5)
        self.seat_session.save()
        Ticket.objects.create(
            user=self.user,
            booking=booking,
            seat_session=self.seat_session,
            code='ticket-code-1',
            price=25,
        )

        BookingService.cancel_booking(booking)

        booking.refresh_from_db()
        self.seat_session.refresh_from_db()
        self.assertEqual(booking.status, 'cancelled')
        self.assertEqual(self.seat_session.status, 'Available')
        self.assertIsNone(self.seat_session.reserved_by)
        self.assertEqual(booking.tickets.count(), 0)
