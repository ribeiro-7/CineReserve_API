from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from cinema.models import Movie, Seat, SeatSession, Session
from cinema.services.reservation_service import ReservationService

User = get_user_model()


class ReservationServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='reserve_user',
            password='Password123#',
        )
        self.other_user = User.objects.create_user(
            username='other_user',
            password='Password123#',
        )
        movie = Movie.objects.create(
            title='Test Movie',
            description='Desc',
            duration=120,
            age_rating='L',
            genre='Ação',
            release_date='2025-01-01',
        )
        self.session = Session.objects.create(
            date=timezone.now().date() + timedelta(days=1),
            showtime='18:00',
            theater='Sala 1',
            movie=movie,
            ticket_price=20,
        )
        seat = Seat.objects.create(row='A', number=1)
        self.seat_session = SeatSession.objects.create(
            session=self.session,
            seat=seat,
            status='Available',
        )

    @patch('cinema.tasks.update_seat_status_after_timeout_on_reserve.apply_async')
    def test_reserve_seats_success(self, mock_task):
        result = ReservationService.reserve_seats(
            user=self.user,
            session=self.session,
            seat_ids=[self.seat_session.id],
        )

        self.seat_session.refresh_from_db()
        self.assertEqual(self.seat_session.status, 'Reserved')
        self.assertEqual(self.seat_session.reserved_by, self.user)
        self.assertEqual(len(result), 1)
        mock_task.assert_called_once()

    def test_reserve_seats_session_passed(self):
        past = timezone.now() - timedelta(days=1)
        self.session.date = past.date()
        self.session.showtime = past.time()
        self.session.save()

        with self.assertRaises(ValidationError) as ctx:
            ReservationService.reserve_seats(
                user=self.user,
                session=self.session,
                seat_ids=[self.seat_session.id],
            )

        self.assertIn('already passed', str(ctx.exception))

    def test_reserve_seats_not_found(self):
        with self.assertRaises(NotFound):
            ReservationService.reserve_seats(
                user=self.user,
                session=self.session,
                seat_ids=[99999],
            )

    def test_reserve_seats_unavailable_when_reserved_by_other(self):
        self.seat_session.status = 'Reserved'
        self.seat_session.reserved_by = self.other_user
        self.seat_session.reserved_until = timezone.now() + timedelta(minutes=5)
        self.seat_session.save()

        with self.assertRaises(ValidationError) as ctx:
            ReservationService.reserve_seats(
                user=self.user,
                session=self.session,
                seat_ids=[self.seat_session.id],
            )

        self.assertIn('Seats unavailable', str(ctx.exception))

    def test_reserve_seats_unavailable_when_sold(self):
        self.seat_session.status = 'Sold'
        self.seat_session.save()

        with self.assertRaises(ValidationError):
            ReservationService.reserve_seats(
                user=self.user,
                session=self.session,
                seat_ids=[self.seat_session.id],
            )

    @patch('cinema.tasks.update_seat_status_after_timeout_on_reserve.apply_async')
    def test_reserve_releases_expired_hold(self, mock_task):
        self.seat_session.status = 'Reserved'
        self.seat_session.reserved_by = self.other_user
        self.seat_session.reserved_until = timezone.now() - timedelta(minutes=1)
        self.seat_session.save()

        ReservationService.reserve_seats(
            user=self.user,
            session=self.session,
            seat_ids=[self.seat_session.id],
        )

        self.seat_session.refresh_from_db()
        self.assertEqual(self.seat_session.reserved_by, self.user)
        mock_task.assert_called_once()
