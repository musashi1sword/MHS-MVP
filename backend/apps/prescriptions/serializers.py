from rest_framework import serializers

from .models import DrugInteraction, Medication, Prescription, PrescriptionItem


class MedicationSerializer(serializers.ModelSerializer):
    label = serializers.CharField(read_only=True)

    class Meta:
        model = Medication
        fields = (
            "id",
            "name",
            "form",
            "strength",
            "drug_class",
            "allergen_groups",
            "rxnorm_code",
            "is_controlled",
            "label",
        )


class DrugInteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DrugInteraction
        fields = "__all__"


class PrescriptionItemSerializer(serializers.ModelSerializer):
    medication_detail = MedicationSerializer(source="medication", read_only=True)
    summary = serializers.CharField(read_only=True)

    class Meta:
        model = PrescriptionItem
        fields = (
            "id",
            "medication",
            "medication_detail",
            "dose",
            "frequency",
            "duration",
            "notes",
            "summary",
        )


class PrescriptionSerializer(serializers.ModelSerializer):
    items = PrescriptionItemSerializer(many=True)
    patient_name = serializers.CharField(source="patient.get_full_name", read_only=True)
    prescriber_name = serializers.CharField(source="prescriber.get_full_name", read_only=True, default=None)
    pharmacy_name = serializers.CharField(source="pharmacy.name", read_only=True, default=None)
    medication_list = serializers.ListField(read_only=True)

    class Meta:
        model = Prescription
        fields = (
            "id",
            "consultation",
            "prescriber",
            "prescriber_name",
            "patient",
            "patient_name",
            "pharmacy",
            "pharmacy_name",
            "status",
            "fulfilment",
            "allergen_alert_triggered",
            "safety_report",
            "override_reason",
            "medication_list",
            "items",
            "created_at",
            "sent_to_pharmacy_at",
            "ready_at",
            "dispensed_at",
        )
        read_only_fields = (
            "prescriber",
            "patient",
            "status",
            "allergen_alert_triggered",
            "safety_report",
            "override_reason",
            "sent_to_pharmacy_at",
            "ready_at",
            "dispensed_at",
        )

    def create(self, validated_data):
        items = validated_data.pop("items")
        rx = Prescription.objects.create(**validated_data)
        for item in items:
            PrescriptionItem.objects.create(prescription=rx, **item)
        return rx


class CheckAllergySerializer(serializers.Serializer):
    """Ad-hoc safety check without persisting a prescription."""

    patient = serializers.IntegerField(required=False, allow_null=True)
    patient_allergies = serializers.ListField(
        child=serializers.CharField(), required=False, allow_null=True
    )
    medications = serializers.ListField(child=serializers.IntegerField())
    concurrent_medications = serializers.ListField(
        child=serializers.CharField(), required=False, allow_null=True
    )


class OverrideSerializer(serializers.Serializer):
    reason = serializers.CharField()
