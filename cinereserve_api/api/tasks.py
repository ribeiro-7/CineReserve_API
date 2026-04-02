from django.utils import timezone
from celery import shared_task
from api.models import SeatSession
from django.core.mail import send_mail
from django.db import transaction

@shared_task
def update_seat_status_after_timeout(seat_session_id):

    try:
        with transaction.atomic():
            seat_session = SeatSession.objects.select_for_update().get(id=seat_session_id)
            if seat_session.status == 'Reserved':
                    seat_session.status = 'Available'
                    seat_session.reserved_until = None
                    seat_session.reserved_by = None
                    seat_session.save(update_fields=['status', 'reserved_until', 'reserved_by'])
    except SeatSession.DoesNotExist:
        pass

@shared_task
def send_ticket_email(user_email, movie, seat, code):
    subject = "Your Ticket Confirmation!"

    message = f"""
        Your purchase was successful!

        Movie: {movie}
        Seat: {seat}
        Ticket Code: {code}

        Enjoy your movie 🍿
        """
    
    send_mail(
        subject,
        message,
        'noreply@cinereserve.com',
        [user_email],
        fail_silently=False
    )