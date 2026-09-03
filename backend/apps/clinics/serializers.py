from rest_framework import serializers

from .models import Clinic, Pharmacy


class ClinicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clinic
        fields = "__all__"


class PharmacySerializer(serializers.ModelSerializer):
    clinic_name = serializers.CharField(source="clinic.name", read_only=True, default=None)

    class Meta:
        model = Pharmacy
        fields = "__all__"
