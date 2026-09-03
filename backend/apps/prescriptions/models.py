from django.conf import settings
from django.db import models


class Medication(models.Model):
    """Formulary entry. `allergen_groups` and `drug_class` drive safety checks."""

    name = models.CharField(max_length=120)
    form = models.CharField(max_length=40, default="tablet")
    strength = models.CharField(max_length=40, blank=True)
    drug_class = models.CharField(max_length=80, blank=True)
    # Cross-reactive allergy groups this drug belongs to, e.g. ["penicillin", "beta-lactam"].
    allergen_groups = models.JSONField(default=list, blank=True)
    rxnorm_code = models.CharField(max_length=20, blank=True)
    is_controlled = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]
        unique_together = ("name", "strength", "form")

    def __str__(self):
        return f"{self.name} {self.strength}".strip()

    @property
    def label(self):
        return f"{self.name} {self.strength} {self.form}".strip()


class DrugInteraction(models.Model):
    SEVERITY = [("minor", "Minor"), ("moderate", "Moderate"), ("major", "Major"), ("contraindicated", "Contraindicated")]

    # Matched by drug_class OR medication name (case-insensitive) on either side.
    left = models.CharField(max_length=80)
    right = models.CharField(max_length=80)
    severity = models.CharField(max_length=20, choices=SEVERITY, default="moderate")
    description = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.left} x {self.right} ({self.severity})"


class PrescriptionStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PENDING = "pending", "Pending"  # sent to pharmacy, not yet picked
    READY = "ready", "Ready for pickup"
    OUT_FOR_DELIVERY = "out_for_delivery", "Out for delivery"
    DISPENSED = "dispensed", "Dispensed"
    CANCELLED = "cancelled", "Cancelled"


class Prescription(models.Model):
    consultation = models.ForeignKey(
        "consultations.Consultation", on_delete=models.CASCADE, related_name="prescriptions"
    )
    prescriber = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="prescriptions"
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="prescriptions_received"
    )
    pharmacy = models.ForeignKey(
        "clinics.Pharmacy", on_delete=models.SET_NULL, null=True, blank=True, related_name="prescriptions"
    )
    status = models.CharField(
        max_length=20, choices=PrescriptionStatus.choices, default=PrescriptionStatus.DRAFT
    )
    fulfilment = models.CharField(
        max_length=10, choices=[("pickup", "Pickup"), ("delivery", "Delivery")], default="pickup"
    )

    allergen_alert_triggered = models.BooleanField(default=False)
    safety_report = models.JSONField(default=dict, blank=True)  # full check output
    override_reason = models.TextField(blank=True)
    overridden_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prescription_overrides",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    sent_to_pharmacy_at = models.DateTimeField(null=True, blank=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    dispensed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Rx<{self.id} {self.get_status_display()}>"

    @property
    def medication_list(self):
        return [item.summary for item in self.items.all()]


class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name="items")
    medication = models.ForeignKey(Medication, on_delete=models.PROTECT)
    dose = models.CharField(max_length=60, blank=True)
    frequency = models.CharField(max_length=60, blank=True)
    duration = models.CharField(max_length=60, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    @property
    def summary(self):
        bits = [self.medication.label, self.dose, self.frequency, self.duration]
        return " · ".join(b for b in bits if b)
