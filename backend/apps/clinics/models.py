from django.db import models


class Clinic(models.Model):
    HOLDING_COMPANIES = [("africanna", "Africanna"), ("clinician", "Clinician")]

    name = models.CharField(max_length=160, unique=True)
    holding_company = models.CharField(max_length=20, choices=HOLDING_COMPANIES, default="africanna")
    city = models.CharField(max_length=80)
    address = models.CharField(max_length=255, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.name


class Pharmacy(models.Model):
    name = models.CharField(max_length=160, unique=True)
    clinic = models.ForeignKey(
        Clinic, null=True, blank=True, on_delete=models.SET_NULL, related_name="pharmacies"
    )
    city = models.CharField(max_length=80)
    address = models.CharField(max_length=255, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    is_mhs_affiliated = models.BooleanField(default=True)
    supports_delivery = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "pharmacies"

    def __str__(self):
        return self.name
