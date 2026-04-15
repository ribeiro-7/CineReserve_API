from api.models import Seat, SeatSession
from .session_mixins import SessionMixin
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

class SeatMixin(SessionMixin):
    def create_seats(self, rows=5, number=10):
        session = self.create_session()
        seat_sessions = []
        for row in ['A', 'B', 'C', 'D', 'E']:
            for number in range(1, 11):
                seat, _ = Seat.objects.get_or_create(
                    row=row,
                    number=number
                )
                seat_session = SeatSession.objects.create(
                    session=session,
                    seat=seat,
                    status='Available'
                )
                seat_sessions.append(seat_session)
        return {
            'session': session,
            'seat_sessions': seat_sessions
        }
    
    def create_available_seat(self, row='A', number='1'):
        session = self.create_session()
        seat = Seat.objects.create(
            row=row,
            number=number
        )
        seat_session = SeatSession.objects.create(
            session=session,
            seat=seat,
            status='Available'
        )
        
        return seat_session
    
    def create_expired_seat(self, row='A', number='1'):
        session = self.create_session()
        seat = Seat.objects.create(
            row=row,
            number=number
        )
        seat_session = SeatSession.objects.create(
            session=session,
            seat=seat,
            status='Available'
        )
        now = timezone.localtime()
        session.date = now.date() - timedelta(days=1)
        session.showtime = (now - timedelta(hours=2)).time()
        session.save()
        return seat_session

    def reserve_seat(self, session_id, seat_id, access_token):
        api_url = reverse('sessions-reserve', args=[session_id])
        data = {
            'seat_id': seat_id
        }
        response = self.client.post(api_url, data=data, HTTP_AUTHORIZATION=f'Bearer {access_token}')
        return response
    
    def buy_seat(self, session_id, seat_id, access_token=None):
        api_url = reverse('sessions-buy', args=[session_id])
        data = {
            'seat_id': seat_id
        }
        response = self.client.post(api_url, data=data, HTTP_AUTHORIZATION=f'Bearer {access_token}')
        return response