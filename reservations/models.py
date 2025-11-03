from django.db import models
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

class RoomType(models.Model):
    name = models.CharField(max_length=50)      # Single, Double, Suite
    capacity = models.IntegerField()            # How many people fit
    price_per_night = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Room(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('maintenance', 'Maintenance'),
        ('cleaning', 'Cleaning'),
        ('occupied', 'Occupied'),
    ]

    room_number = models.CharField(max_length=10)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='available'
    )

    def __str__(self):
        return f"{self.room_number} - {self.room_type.name} ({self.status})"


class Guest(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Reservation(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    guest = models.ForeignKey(Guest, on_delete=models.CASCADE)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE)
    check_in = models.DateField()
    check_out = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    def __str__(self):
        return f"{self.guest} - {self.room_type.name} ({self.check_in} to {self.check_out})"

from django.db import models

class Stay(models.Model):
    STATUS_CHOICES = [
        ('checked_in', 'Checked In'),
        ('checked_out', 'Checked Out'),
        ('no_show', 'No Show'),
    ]

    reservation = models.ForeignKey('Reservation', on_delete=models.CASCADE)
    room = models.ForeignKey('Room', on_delete=models.CASCADE)
    check_in_actual = models.DateTimeField()
    check_out_actual = models.DateTimeField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='no_show'
    )

    def __str__(self):
        return f"{self.reservation.guest} - Room {self.room.room_number} ({self.status})"

    def save(self, *args, **kwargs):
    # Ensure primary key exists for related queries
        if not self.pk:
            super().save(*args, **kwargs)

        # Calculate nights
        nights = 1
        if self.check_out_actual and self.check_in_actual:
            delta = (self.check_out_actual.date() - self.check_in_actual.date()).days
            nights = delta if delta > 0 else 1

        # Base room price
        room_price = self.room.room_type.price_per_night * nights

        # Total for all services
        service_total = sum(s.total_cost for s in self.serviceusage_set.all()) if self.pk else 0

        # Update total_amount
        self.total_amount = room_price + service_total

        # Save final
        super().save(*args, **kwargs)

    # 🧮 ---- Computed properties go here ----
    @property
    def total_paid(self):
        return sum(p.amount for p in self.payment_set.filter(payment_type='stay'))

    @property
    def remaining_balance(self):
        return self.total_amount - self.total_paid

class Service(models.Model):
    name = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return self.name

class ServiceUsage(models.Model):
    stay = models.ForeignKey(Stay, on_delete=models.CASCADE)
    service = models.ForeignKey('Service', on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.total_cost = self.quantity * self.service.price
        super().save(*args, **kwargs)

# reservations/models.py
from django.db import models

class Payment(models.Model):
    PAYMENT_TYPE_CHOICES = [
        ('stay', 'Stay'),
        ('service', 'Service'),
    ]

    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPE_CHOICES)
    stay = models.ForeignKey('Stay', null=True, blank=True, on_delete=models.CASCADE)
    service_usage = models.ForeignKey('ServiceUsage', null=True, blank=True, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=50, default='cash')
    payment_date = models.DateTimeField(default=timezone.now)
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        if self.payment_type == 'stay' and self.stay:
            return f"Stay Payment: {self.stay} - {self.amount}"
        elif self.payment_type == 'service' and self.service_usage:
            return f"Service Payment: {self.service_usage.service.name} - {self.amount}"
        return f"Payment {self.id} - {self.amount}"

    def clean(self):

        if self.payment_type == 'stay' and not self.stay:
            raise ValidationError("Stay payment must be linked to a Stay.")
        if self.payment_type == 'service' and not self.service_usage:
            raise ValidationError("Service payment must be linked to a Service Usage.")


class Kassa(models.Model):
    name = models.CharField(max_length=50, default="Main Cash Register")
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.name} — Balance: {self.balance} ₸"


class KassaTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('in', 'Cash In'),
        ('out', 'Cash Out'),
    ]

    kassa = models.ForeignKey(Kassa, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=3, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    date = models.DateTimeField(default=timezone.now)

    payment = models.ForeignKey('Payment', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.transaction_type.upper()} {self.amount}₸ — {self.date.strftime('%Y-%m-%d')}"