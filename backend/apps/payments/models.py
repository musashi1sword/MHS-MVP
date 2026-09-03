from django.conf import settings
from django.db import models


class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="KES")

    def __str__(self):
        return f"Wallet<{self.user.email}: {self.balance} {self.currency}>"


class Transaction(models.Model):
    TYPES = [
        ("consult_fee", "Consultation fee"),
        ("wallet_topup", "Wallet top-up"),
        ("pharmacy", "Pharmacy charge"),
        ("ic_payout", "Independent contractor payout"),
        ("refund", "Refund"),
    ]
    PROVIDERS = [("mpesa", "M-Pesa"), ("airtel", "Airtel Money"), ("stripe", "Stripe"), ("wallet", "Wallet")]
    STATUS = [("pending", "Pending"), ("success", "Success"), ("failed", "Failed")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions")
    kind = models.CharField(max_length=20, choices=TYPES)
    provider = models.CharField(max_length=10, choices=PROVIDERS)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="KES")
    status = models.CharField(max_length=10, choices=STATUS, default="pending")
    reference = models.CharField(max_length=64, blank=True)
    appointment = models.ForeignKey(
        "appointments.Appointment", null=True, blank=True, on_delete=models.SET_NULL
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Txn<{self.kind} {self.amount} {self.currency} {self.status}>"
