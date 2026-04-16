from django.db import models
from django.contrib.auth.models import User
from cinema.models import SeatSession

class Ticket(models.Model):
    code = models.CharField(max_length=100, unique=True)
    purchased_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    seat_session = models.OneToOneField(SeatSession, on_delete=models.CASCADE)