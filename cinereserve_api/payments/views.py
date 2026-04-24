import uuid
import requests
from django.conf import settings
from .models import Payment
from django.http import JsonResponse, HttpResponse
import json
from django.views.decorators.csrf import csrf_exempt
from booking.models import Booking
from django.shortcuts import get_object_or_404
from cinema.tasks import send_ticket_email
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

#While tickets dont have price
TICKET_PRICE = 10

def payment_callback(request):
    return JsonResponse({
        "status": "ok",
        "message": "You were redirected after payment"
    })

def create_payment_for_booking(booking):
    now = timezone.now()
    expires_at = now + timedelta(minutes=5)

    booking.expires_at = expires_at
    booking.save(update_fields=['expires_at'])

    tx_ref = f"booking-{booking.id}-{uuid.uuid4()}"
    amount = booking.tickets.count() * TICKET_PRICE

    Payment.objects.create(
        booking=booking,
        tx_ref=tx_ref,
        amount=amount
    )

    url = "https://api.flutterwave.com/v3/payments"

    headers = {
        "Authorization": f"Bearer {settings.FLW_SECRET_KEY}",
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

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Flutterwave error: {response.text}")

    data = response.json()
    return data["data"]["link"]


@csrf_exempt
def flutterwave_webhook(request):
    now = timezone.now()
    secret_hash = settings.FLW_SECRET_HASH
    signature = request.headers.get("verif-hash")

    if signature != secret_hash:
        return HttpResponse(status=401)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    tx_ref = payload.get("txRef")
    flw_id = payload.get("id")

    if not tx_ref or not flw_id:
        return HttpResponse(status=400)

    with transaction.atomic():
        payment = (
            Payment.objects
            .select_for_update()
            .select_related("booking")
            .filter(tx_ref=tx_ref)
            .first()
        )

        if not payment:
            return HttpResponse(status=400)

        if payment.status == "successful":
            return HttpResponse(status=200)

        booking = payment.booking

        if booking.expires_at and booking.expires_at < now:
            booking.status = "cancelled"
            booking.save(update_fields=["status"])

            payment.status = "failed"
            payment.save(update_fields=["status"])

            return HttpResponse(status=200)

        if booking.status == "cancelled":
            return HttpResponse(status=200)

        verify_url = f"https://api.flutterwave.com/v3/transactions/{flw_id}/verify"

        headers = {
            "Authorization": f"Bearer {settings.FLW_SECRET_KEY}"
        }

        response = requests.get(verify_url, headers=headers)

        if response.status_code != 200:
            print("VERIFY ERROR:", response.text)
            return HttpResponse(status=500)

        data = response.json().get("data")

        if not data:
            return HttpResponse(status=500)

        amount_ok = abs(float(data.get("amount")) - float(payment.amount)) < 0.01
        currency_ok = data.get("currency") == "USD"
        status_ok = data.get("status") == "successful"

        if status_ok and amount_ok and currency_ok:
            payment.status = "successful"
            payment.flutterwave_id = flw_id
            payment.save(update_fields=["status", "flutterwave_id"])

            if booking.status == "pending":
                booking.status = "completed"
                booking.save(update_fields=["status"])

            tickets_data = []

            for ticket in booking.tickets.select_related("seat_session__seat"):
                seat = ticket.seat_session

                if seat.status == "Reserved":
                    seat.status = "Sold"
                    seat.reserved_until = None
                    seat.reserved_by = None
                    seat.save(update_fields=["status", "reserved_until", "reserved_by"])

                tickets_data.append({
                    "seat": f"{seat.seat.row}{seat.seat.number}",
                    "ticket_code": ticket.code,
                    "date": booking.session.date,
                    "time": booking.session.showtime
                })

            if not getattr(payment, "email_sent", False):
                send_ticket_email.delay(
                    booking.user.email,
                    booking.session.movie.title,
                    tickets_data
                )

                payment.email_sent = True
                payment.save(update_fields=["email_sent"])

        else:
            payment.status = "failed"
            payment.save(update_fields=["status"])

    return HttpResponse(status=200)