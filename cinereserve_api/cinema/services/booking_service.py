from django.db import transaction
from cinema.models import SeatSession
from booking.models import Booking, Ticket
from rest_framework.exceptions import ValidationError, NotFound
from django.utils import timezone
from datetime import timedelta
import uuid

class BookingService:
    @staticmethod
    @transaction.atomic
    def cancel_booking(booking, payment=None):
        tickets = (
            booking.tickets
            .select_related("seat_session")
            .filter(booking=booking)
        )

        for ticket in tickets:
            seat_session = ticket.seat_session
            seat_session.status = "Available"
            seat_session.reserved_until = None
            seat_session.reserved_by = None
            seat_session.save(
                update_fields=[
                    "status",
                    "reserved_until",
                    "reserved_by"
                ]
            )

        tickets.delete()

        booking.status = "cancelled"
        booking.save(update_fields=["status"])

        if payment:
            payment.status = "failed"
            payment.save(update_fields=["status"])

    @staticmethod
    @transaction.atomic
    def create_booking(user, session, seat_ids):
        from cinema.tasks import cancel_booking_after_timeout
        
        now = timezone.now()
        today = now.date()
        current_time = now.time()

        if not (
            session.date > today or
            (
                session.date == today and
                session.showtime > current_time
            )
        ):
            raise ValidationError(
                "The session has already passed."
            )

        seat_sessions = list(
            SeatSession.objects
            .select_for_update()
            .filter(
                id__in=seat_ids,
                session=session
            )
        )

        if len(seat_sessions) != len(seat_ids):
            raise NotFound(
                "One or more seats not found."
            )

        invalid_seats = []

        for seat in seat_sessions:
            if (
                seat.status == "Reserved" and
                seat.reserved_by != user
            ):
                if (
                    seat.reserved_until and
                    seat.reserved_until < now
                ):

                    seat.status = "Available"
                    seat.reserved_until = None
                    seat.reserved_by = None

                    seat.save(update_fields=[
                        "status",
                        "reserved_until",
                        "reserved_by"
                    ])

                else:
                    invalid_seats.append(seat)
            elif seat.status == "Sold":
                invalid_seats.append(seat)

        if invalid_seats:
            invalid_labels = [
                f"{seat.seat.row}{seat.seat.number}"
                for seat in invalid_seats
            ]
            raise ValidationError(
                f"Seats unavailable: {', '.join(invalid_labels)}"
            )

        expires_at = now + timedelta(minutes=5)

        booking = Booking.objects.create(
            user=user,
            session=session,
            status="pending",
            expires_at=expires_at
        )

        for seat in seat_sessions:
            seat.status = "Reserved"
            seat.reserved_by = user
            seat.reserved_until = expires_at

            seat.save(update_fields=[
                "status",
                "reserved_by",
                "reserved_until"
            ])

            Ticket.objects.create(
                user=user,
                booking=booking,
                seat_session=seat,
                code=str(uuid.uuid4()),
                price=session.ticket_price
            )

        cancel_booking_after_timeout.apply_async(
            args=[booking.id],
            countdown=300
        )

        return booking