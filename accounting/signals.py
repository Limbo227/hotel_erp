from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from reservations.models import Payment
from .models import Kassa, KassaTransaction
from decimal import Decimal

@receiver(post_save, sender=Payment)
def handle_payment_created(sender, instance, created, **kwargs):
    """When a Payment is created, update Kassa if cash."""
    if not created or instance.method != 'cash':
        return

    kassa, _ = Kassa.objects.get_or_create(name="Main Cash Register")

    # Ensure Decimal arithmetic
    amount = Decimal(instance.amount)
    kassa.balance = Decimal(kassa.balance) + amount
    kassa.save()

    KassaTransaction.objects.create(
        kassa=kassa,
        transaction_type='in',
        amount=amount,
        description=f"Payment ({instance.payment_type}) for guest",
        related_payment=instance
    )

@receiver(post_delete, sender=Payment)
def handle_payment_deleted(sender, instance, **kwargs):
    """When a Payment is deleted, reverse the Kassa transaction."""
    if instance.method != 'cash':
        return

    try:
        kassa = Kassa.objects.get(name="Main Cash Register")
    except Kassa.DoesNotExist:
        return

    amount = Decimal(instance.amount)
    kassa.balance = Decimal(kassa.balance) - amount
    if kassa.balance < 0:
        kassa.balance = Decimal('0.00')  # safety check
    kassa.save()

    # Log reversal
    KassaTransaction.objects.create(
        kassa=kassa,
        transaction_type='out',
        amount=amount,
        description=f"Deleted payment ({instance.payment_type}) — reversed cash inflow",
        related_payment=None
    )
