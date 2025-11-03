from django.contrib import admin
from .models import RoomType, Room, Guest, Reservation, Stay, Service, ServiceUsage, Payment

# Register simple models
admin.site.register(RoomType)
admin.site.register(Room)
admin.site.register(Guest)
admin.site.register(Service)
admin.site.register(ServiceUsage)

# 🧾 Reservation Admin
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('guest', 'check_in', 'check_out', 'status')
    list_filter = ('status', 'check_in', 'check_out')
    search_fields = ('guest__name', 'room__room_number')


# 🏨 Stay Admin
@admin.register(Stay)
class StayAdmin(admin.ModelAdmin):
    list_display = ('reservation', 'room', 'status', 'check_in_actual', 'check_out_actual', 'total_amount', 'total_paid', 'remaining_balance')
    readonly_fields = ('total_paid', 'remaining_balance')
    list_filter = ('status',)
    search_fields = ('reservation__guest__name', 'room__room_number')


# 💰 Payment Admin
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_type', 'amount', 'method', 'payment_date', 'stay', 'service_usage')
    list_filter = ('payment_type', 'method')
    search_fields = ('stay__reservation__guest__name', 'service_usage__service__name')

