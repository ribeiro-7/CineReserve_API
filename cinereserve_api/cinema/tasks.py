from django.utils import timezone
from celery import shared_task
from cinema.models import SeatSession
from booking.models import Ticket
from django.core.mail import send_mail
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

@shared_task
def update_seat_status_after_timeout(seat_session_id):
    with transaction.atomic():
        seat_session = (
            SeatSession.objects
            .select_for_update()
            .filter(id=seat_session_id)
            .first()
        )

        if not seat_session:
            logger.info(f"SeatSession {seat_session_id} not found.")
            return 

        if not (
            seat_session.status == 'Reserved' and
            seat_session.reserved_until and
            seat_session.reserved_until < timezone.now()
        ):
            return

        ticket = (
            Ticket.objects
            .select_related("booking")
            .filter(seat_session=seat_session)
            .first()
        )

        if ticket:
            booking = ticket.booking

            if booking.status == "pending":
                booking.status = "cancelled"
                booking.save(update_fields=["status"])

                logger.info(f"Booking {booking.id} cancelled due to timeout")

        seat_session.status = 'Available'
        seat_session.reserved_until = None
        seat_session.reserved_by = None
        seat_session.save(update_fields=['status', 'reserved_until', 'reserved_by'])

@shared_task
def send_ticket_email(user_email, movie, tickets):
    subject = "Your Tickets Confirmation!"

    seats_info = "\n".join(
        [f"Seat: {t['seat']} | Code: {t['ticket_code']}" for t in tickets]
    )

    message = f"""
        Your purchase to - "{movie}" - was successful!

        {seats_info}

        Enjoy your movie!!!
        """
    
    send_mail(
        subject,
        message,
        'noreply@cinereserve.com',
        [user_email],
        fail_silently=False
    )