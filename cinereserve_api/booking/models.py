from django.db import models
from django.contrib.auth.models import User
from cinema.models import Session, SeatSession

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled')
        ],
        default='pending'
    )
    expires_at = models.DateTimeField(null=True, blank=True)

class Ticket(models.Model):
    code = models.CharField(max_length=100, unique=True)
    purchased_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    seat_session = models.OneToOneField(SeatSession, on_delete=models.CASCADE)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='tickets')