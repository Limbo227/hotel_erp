from django.contrib import admin
from .models import Kassa, KassaTransaction

@admin.register(Kassa)
class KassaAdmin(admin.ModelAdmin):
    list_display = ('name', 'balance')

@admin.register(KassaTransaction)
class KassaTransactionAdmin(admin.ModelAdmin):
    list_display = ('kassa', 'amount', 'transaction_type', 'description', 'related_payment', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('description', 'related_payment__id')
