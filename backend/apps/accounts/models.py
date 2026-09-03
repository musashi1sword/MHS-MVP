from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    PATIENT = "patient", "Patient"
    CLINICIAN = "clinician", "Clinician"
    CHW = "chw", "Community Health Worker"
    PHARMACIST = "pharmacist", "Pharmacist"
    ADMIN = "admin", "Administrator"


class User(AbstractUser):
    """Custom user. Auth is by email; username mirrors email for admin compatibility."""

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.PATIENT)
    phone = models.CharField(max_length=20, blank=True)
    clinic = models.ForeignKey(
        "clinics.Clinic", null=True, blank=True, on_delete=models.SET_NULL, related_name="staff"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_full_name() or self.email} ({self.role})"


class PatientProfile(models.Model):
    """Synthetic clinical context for a patient — no real PHI."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="patient_profile")
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    # Simple, demo-friendly representations.
    allergies = models.JSONField(default=list, blank=True)  # e.g. ["penicillin", "sulfa"]
    insurance_provider = models.CharField(max_length=120, blank=True)
    insurance_member_id = models.CharField(max_length=60, blank=True)
    medication_history = models.JSONField(default=list, blank=True)  # e.g. ["amlodipine 5mg"]

    def __str__(self):
        return f"PatientProfile<{self.user.email}>"


class ProviderProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="provider_profile")
    specialty = models.CharField(max_length=120, blank=True, default="General Practice")
    license_number = models.CharField(max_length=60, blank=True)
    is_overseas_ic = models.BooleanField(default=False)  # non-US Independent Contractor

    def __str__(self):
        return f"ProviderProfile<{self.user.email}>"
