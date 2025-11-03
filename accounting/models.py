from django.db import models
from django.utils import timezone
from decimal import Decimal

class Kassa(models.Model):
    name = models.CharField(max_length=100, default="Main Cash Register")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.name} — Balance: {self.balance}"


class KassaTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('in', 'Cash In'),
        ('out', 'Cash Out'),
    )

    kassa = models.ForeignKey(Kassa, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=3, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255, blank=True, null=True)
    related_payment = models.ForeignKey(
        'reservations.Payment',  # Reference the Payment model
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='kassa_transactions'
    )
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.get_transaction_type_display()} — {self.amount}"

    def save(self, *args, **kwargs):
        """Auto-adjust Kassa balance when a transaction is created or updated."""
        is_new = self._state.adding
        super().save(*args, **kwargs)

        if is_new:
            if self.transaction_type == 'in':
                self.kassa.balance = Decimal(self.kassa.balance) + Decimal(self.amount)
            else:
                self.kassa.balance = Decimal(self.kassa.balance) - Decimal(self.amount)
            self.kassa.save()

    def delete(self, *args, **kwargs):
        """Revert balance when transaction is deleted."""
        if self.transaction_type == 'in':
            self.kassa.balance = Decimal(self.kassa.balance) - Decimal(self.amount)
        else:
            self.kassa.balance = Decimal(self.kassa.balance) + Decimal(self.amount)
        self.kassa.save()
        super().delete(*args, **kwargs)
