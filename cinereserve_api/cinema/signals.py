from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Session, Seat, SeatSession

#Signal para criar mapa de assentos automaticamente para uma nova sessão criada
@receiver(post_save, sender=Session)
def create_seats_for_new_session(sender, instance, created, **kwargs):
    if created:
        seats = Seat.objects.all()

        bulk = [
            SeatSession(session=instance, seat=seat)
            for seat in seats
        ]

        SeatSession.objects.bulk_create(bulk, ignore_conflicts=True)