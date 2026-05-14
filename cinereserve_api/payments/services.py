import uuid
import json
import requests
from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from cinema.tasks import send_ticket_email
from cinema.services.booking_service import BookingService
from .models import Payment
from rest_framework import status

class PaymentService:
    @staticmethod
    def create_payment_for_booking(booking):
        now = timezone.now()
        expires_at = now + timedelta(minutes=5)

        booking.expires_at = expires_at
        booking.save(update_fields=["expires_at"])

        tx_ref = f"booking-{booking.id}-{uuid.uuid4()}"
        amount = booking.amount

        Payment.objects.create(
            booking=booking,
            tx_ref=tx_ref,
            amount=amount
        )

        url = "https://api.flutterwave.com/v3/payments"

        headers = {
            "Authorization": (
                f"Bearer {settings.FLW_SECRET_KEY}"
            ),
            "Content-Type": "application/json"
        }

        payload = {
            "tx_ref": tx_ref,
            "amount": str(amount),
            "currency": "USD",
            "redirect_url": settings.FLW_REDIRECT_URL,
            "customer": {
                "email": booking.user.email
            }
        }

        response = requests.post(
            url,
            json=payload,
            headers=headers
        )

        if response.status_code != 200:
            raise Exception(
                f"Flutterwave error: {response.text}"
            )

        data = response.json()

        return data["data"]["link"]

    @staticmethod
    def verify_flutterwave_transaction(flw_id):
        verify_url = (
            f"https://api.flutterwave.com/v3/transactions/{flw_id}/verify"
        )

        headers = {
            "Authorization": (
                f"Bearer {settings.FLW_SECRET_KEY}"
            )
        }

        response = requests.get(
            verify_url,
            headers=headers
        )

        if response.status_code != 200:
            raise Exception(
                f"Flutterwave verify error: "
                f"{response.text}"
            )

        data = response.json().get("data")

        if not data:
            raise Exception(
                "Flutterwave returned empty "
                "verification data."
            )

        return data

    @staticmethod
    def finalize_successful_payment(payment,booking,flw_id):
        payment.status = "successful"
        payment.flutterwave_id = flw_id
        payment.save(update_fields=["status","flutterwave_id"])

        if booking.status == "pending":
            booking.status = "completed"
            booking.save(update_fields=["status"])

        tickets_data = []

        for ticket in booking.tickets.select_related("seat_session__seat"):
            seat_session = ticket.seat_session
            if seat_session.status == "Reserved":
                seat_session.status = "Sold"
                seat_session.reserved_until = None
                seat_session.reserved_by = None
                seat_session.save(update_fields=["status","reserved_until","reserved_by"])

            tickets_data.append({
                "seat": (
                    f"{seat_session.seat.row}"
                    f"{seat_session.seat.number}"
                ),
                "ticket_code": ticket.code,
                "price": ticket.price,
                "date": booking.session.date,
                "time": booking.session.showtime
            })

        if not payment.email_sent:

            send_ticket_email.delay(
                booking.user.email,
                booking.session.movie.title,
                tickets_data
            )

            payment.email_sent = True

            payment.save(update_fields=["email_sent"])

    @staticmethod
    def fail_payment(payment):
        payment.status = "failed"
        payment.save(update_fields=["status"])

    @staticmethod
    def process_flutterwave_webhook(request):
        now = timezone.now()
        secret_hash = settings.FLW_SECRET_HASH
        signature = request.headers.get(
            "verif-hash"
        )

        if signature != secret_hash:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)

        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

        tx_ref = payload.get("txRef")

        flw_id = payload.get("id")

        if not tx_ref or not flw_id:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            payment = (
                Payment.objects
                .select_for_update()
                .select_related("booking")
                .filter(tx_ref=tx_ref)
                .first()
            )

            if not payment:
                return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

            if payment.status == "successful":
                return HttpResponse(status=status.HTTP_200_OK)

            booking = payment.booking

            if (
                booking.expires_at and
                booking.expires_at < now
            ):
                BookingService.cancel_booking(booking, payment)
                return HttpResponse(status=status.HTTP_200_OK)

            if booking.status == "cancelled":
                return HttpResponse(status=status.HTTP_200_OK)

            try:
                data = (PaymentService.verify_flutterwave_transaction(flw_id))
            except Exception as e:
                print("VERIFY ERROR:",str(e))
                return HttpResponse(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            amount_ok = (
                abs(
                    float(data.get("amount")) -
                    float(payment.amount)
                ) < 0.01
            )

            currency_ok = (
                data.get("currency") == "USD"
            )

            status_ok = (
                data.get("status") == "successful"
            )

            if (
                status_ok and
                amount_ok and
                currency_ok
            ):
                PaymentService.finalize_successful_payment(payment, booking, flw_id)

            else:
                PaymentService.fail_payment(payment)

        return HttpResponse(status=status.HTTP_200_OK)