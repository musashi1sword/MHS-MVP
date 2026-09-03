from django.utils import timezone
from rest_framework import serializers

from .models import Appointment, AppointmentStatus, ProviderSlot
from .triage import run_triage


class ProviderSlotSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source="provider.get_full_name", read_only=True)
    clinic_name = serializers.CharField(source="clinic.name", read_only=True)

    class Meta:
        model = ProviderSlot
        fields = ("id", "provider", "provider_name", "clinic", "clinic_name", "start", "end", "is_booked")


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.get_full_name", read_only=True)
    provider_name = serializers.CharField(source="provider.get_full_name", read_only=True, default=None)
    clinic_name = serializers.CharField(source="clinic.name", read_only=True, default=None)
    wait_seconds = serializers.FloatField(read_only=True)

    class Meta:
        model = Appointment
        fields = (
            "id",
            "patient",
            "patient_name",
            "provider",
            "provider_name",
            "clinic",
            "clinic_name",
            "slot",
            "scheduled_start",
            "mode",
            "status",
            "symptom_note",
            "intake",
            "triage",
            "created_at",
            "queued_at",
            "seen_at",
            "completed_at",
            "wait_seconds",
        )
        read_only_fields = ("triage", "queued_at", "seen_at", "completed_at", "status", "provider", "clinic")


class BookingSerializer(serializers.Serializer):
    """Patient booking: pick a slot, log a symptom. Intake can follow via PATCH."""

    slot = serializers.PrimaryKeyRelatedField(queryset=ProviderSlot.objects.filter(is_booked=False))
    symptom_note = serializers.CharField()
    mode = serializers.ChoiceField(choices=Appointment.MODE_CHOICES, default="video")
    intake = serializers.JSONField(required=False, default=dict)

    def create(self, validated_data):
        slot = validated_data["slot"]
        request = self.context["request"]
        appt = Appointment.objects.create(
            patient=request.user,
            provider=slot.provider,
            clinic=slot.clinic,
            slot=slot,
            scheduled_start=slot.start,
            mode=validated_data["mode"],
            symptom_note=validated_data["symptom_note"],
            intake=validated_data.get("intake") or {},
            status=AppointmentStatus.CONFIRMED,
        )
        appt.triage = run_triage(appt.symptom_note, appt.intake)
        appt.save(update_fields=["triage"])
        slot.is_booked = True
        slot.save(update_fields=["is_booked"])
        return appt


class IntakeSerializer(serializers.Serializer):
    intake = serializers.JSONField()

    def update(self, instance, validated_data):
        instance.intake = {**(instance.intake or {}), **validated_data["intake"]}
        instance.triage = run_triage(instance.symptom_note, instance.intake)
        instance.status = AppointmentStatus.IN_QUEUE
        instance.queued_at = instance.queued_at or timezone.now()
        instance.save(update_fields=["intake", "triage", "status", "queued_at"])
        return instance
