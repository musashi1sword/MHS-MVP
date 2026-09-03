from django.contrib import admin

from .models import Transaction, Wallet


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "kind", "provider", "amount", "currency", "status", "created_at")
    list_filter = ("kind", "provider", "status")


admin.site.register(Wallet)
