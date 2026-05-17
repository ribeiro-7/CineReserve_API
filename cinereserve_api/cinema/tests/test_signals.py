from django.test import TestCase

from cinema.models import Movie, Seat, SeatSession, Session


class SessionSignalTest(TestCase):
    def test_create_session_auto_creates_seat_sessions(self):
        Seat.objects.create(row='Z', number=9)
        Seat.objects.create(row='Z', number=10)
        movie = Movie.objects.create(
            title='Signal Movie',
            description='Desc',
            duration=95,
            age_rating='L',
            genre='Ação',
            release_date='2025-01-01',
        )

        session = Session.objects.create(
            date='2026-06-01',
            showtime='15:00',
            theater='Sala 9',
            movie=movie,
        )

        self.assertEqual(SeatSession.objects.filter(session=session).count(), 2)
