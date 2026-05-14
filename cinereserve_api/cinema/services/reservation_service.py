from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from django.utils.timezone import localtime
from rest_framework.exceptions import ValidationError, NotFound
from cinema.models import SeatSession

class ReservationService:
    @staticmethod
    @transaction.atomic
    def reserve_seats(user, session, seat_ids):
        from cinema.tasks import update_seat_status_after_timeout_on_reserve
        now = timezone.now()
        seat_sessions = list(
            SeatSession.objects.select_for_update().filter(
                id__in=seat_ids,
                session=session
            )
        )

        if len(seat_sessions) != len(seat_ids):
            raise NotFound("One or more seats not found.")

        invalid_seats = []

        for seat in seat_sessions:

            if seat.status == "Reserved":

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

        reserved_seats = []

        for seat in seat_sessions:

            seat.status = "Reserved"
            seat.reserved_until = now + timedelta(minutes=5)
            seat.reserved_by = user

            seat.save(update_fields=[
                "status",
                "reserved_until",
                "reserved_by"
            ])

            update_seat_status_after_timeout_on_reserve.apply_async(
                args=[seat.id],
                countdown=300
            )

            reserved_seats.append({
                "seat": f"{seat.seat.row}{seat.seat.number}",
                "status": seat.status,
                "expires_at": localtime(
                    seat.reserved_until
                ).strftime("%d/%m/%Y - %H:%M:%S")
            })

        return reserved_seats