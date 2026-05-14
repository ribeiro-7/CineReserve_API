from django.utils import timezone
from celery import shared_task
from cinema.models import SeatSession
from booking.models import Booking, Ticket
from django.core.mail import send_mail
from django.db import transaction
import logging
from .services.booking_service import BookingService

logger = logging.getLogger(__name__)

@shared_task
def update_seat_status_after_timeout_on_reserve(seat_session_id):
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

        seat_session.status = 'Available'
        seat_session.reserved_until = None
        seat_session.reserved_by = None
        seat_session.save(update_fields=['status', 'reserved_until', 'reserved_by'])
        logger.info(f"SeatSession {seat_session_id} released after reservation timeout.")

@shared_task
def cancel_booking_after_timeout(booking_id):
    with transaction.atomic():
        booking = (
            Booking.objects
            .select_for_update()
            .filter(id=booking_id)
            .first()
        )

        if not booking:
            logger.info(f"Booking {booking_id} not found.")
            return
        
        if booking.status != "pending":
            logger.info(
                f"Booking {booking.id} is already {booking.status}."
            )
            return
        
        tickets = (
            Ticket.objects
            .select_related("seat_session")
            .select_for_update()
            .filter(booking=booking)
        )

        if not tickets.exists():
            logger.info(
                f"Booking {booking.id} has no tickets."
            )
            return
        
        now = timezone.now()
        
        expired = all(
            ticket.seat_session.reserved_until and
            ticket.seat_session.reserved_until < now
            for ticket in tickets
        )

        if not expired:
            logger.info(
                f"Booking {booking.id} has not expired yet."
            )
            return

        BookingService.cancel_booking(booking)

        logger.info(
            f"Booking {booking.id} cancelled due to timeout."
        )

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