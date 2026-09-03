from django.conf import settings
from django.db import models


class DispenseEvent(models.Model):
    """Audit trail of a prescription moving through the pharmacy."""

    prescription = models.ForeignKey(
        "prescriptions.Prescription", on_delete=models.CASCADE, related_name="dispense_events"
    )
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
