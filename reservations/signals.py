from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ServiceUsage, Stay

@receiver(post_save, sender=ServiceUsage)
def update_stay_total(sender, instance, **kwargs):
    stay = instance.stay

    # Only update if Stay exists in DB
    if not stay.pk:
        return

    # Calculate number of nights
    if stay.check_out_actual:
        nights = (stay.check_out_actual.date() - stay.check_in_actual.date()).days
        if nights <= 0:
            nights = 1
    else:
        nights = 1

    # Room price
    room_price = stay.room.room_type.price_per_night * nights

    # Services total
    service_total = sum(s.total_cost for s in stay.serviceusage_set.all())

    # Update total_amount
    stay.total_amount = room_price + service_total
    stay.save()

@receiver(post_save, sender=Stay)
def update_room_status_on_stay(sender, instance, **kwargs):
    room = instance.room

    if instance.status == 'checked_in':
        room.status = 'occupied'
    elif instance.status == 'checked_out':
        room.status = 'cleaning'
    elif instance.status == 'no_show':
        room.status = 'available'

    room.save()