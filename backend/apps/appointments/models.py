from django.conf import settings
from django.db import models
from django.utils import timezone


class ProviderSlot(models.Model):
    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="slots"
    )
    clinic = models.ForeignKey("clinics.Clinic", on_delete=models.CASCADE, related_name="slots")
    start = models.DateTimeField()
    end = models.DateTimeField()
    is_booked = models.BooleanField(default=False)

    class Meta:
        ordering = ["start"]

    def __str__(self):
        return f"{self.provider} @ {self.start:%Y-%m-%d %H:%M}"


class AppointmentStatus(models.TextChoices):
    REQUESTED = "requested", "Requested"
    CONFIRMED = "confirmed", "Confirmed"
    IN_QUEUE = "in_queue", "In queue"
    IN_PROGRESS = "in_progress", "In progress"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
    NO_SHOW = "no_show", "No-show"


class Appointment(models.Model):
    MODE_CHOICES = [("video", "Video"), ("audio", "Audio"), ("in_person", "In person")]

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="appointments_as_patient"
    )
    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="appointments_as_provider",
    )
    clinic = models.ForeignKey("clinics.Clinic", on_delete=models.SET_NULL, null=True)
    slot = models.OneToOneField(
        ProviderSlot, on_delete=models.SET_NULL, null=True, blank=True, related_name="appointment"
    )
    scheduled_start = models.DateTimeField()
    mode = models.CharField(max_length=12, choices=MODE_CHOICES, default="video")
    status = models.CharField(
        max_length=16, choices=AppointmentStatus.choices, default=AppointmentStatus.REQUESTED
    )

    symptom_note = models.TextField(blank=True)
    intake = models.JSONField(default=dict, blank=True)
    triage = models.JSONField(default=dict, blank=True)  # populated by mock AI triage

    # Timestamps used by the metrics funnel.
    created_at = models.DateTimeField(default=timezone.now)
    queued_at = models.DateTimeField(null=True, blank=True)
    seen_at = models.DateTimeField(null=True, blank=True)  # provider joined the visit
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["scheduled_start"]

    def __str__(self):
        return f"Appt<{self.patient} / {self.get_status_display()}>"

    @property
    def wait_seconds(self):
        if self.queued_at and self.seen_at:
            return (self.seen_at - self.queued_at).total_seconds()
        return None
