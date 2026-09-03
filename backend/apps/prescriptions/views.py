from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import decorators, permissions, response, status, viewsets
from rest_framework.exceptions import ValidationError

from apps.clinics.models import Pharmacy
from apps.communications.broadcast import push_pharmacy_status
from apps.pharmacy.routing import nearest_pharmacy

from .models import Medication, Prescription, PrescriptionStatus
from .safety import check_prescription_safety
from .serializers import (
    CheckAllergySerializer,
    MedicationSerializer,
    OverrideSerializer,
    PrescriptionSerializer,
)


def _patient_allergies(patient):
    profile = getattr(patient, "patient_profile", None)
    return list(getattr(profile, "allergies", []) or [])


def _concurrent_meds(patient):
    profile = getattr(patient, "patient_profile", None)
    return list(getattr(profile, "medication_history", []) or [])


def _run_safety_for_prescription(rx: Prescription) -> dict:
    meds = [item.medication for item in rx.items.select_related("medication")]
    report = check_prescription_safety(
        meds, _patient_allergies(rx.patient), _concurrent_meds(rx.patient)
    )
    rx.safety_report = report
    rx.allergen_alert_triggered = any(a["type"] == "allergy" for a in report["alerts"])
    rx.save(update_fields=["safety_report", "allergen_alert_triggered"])
    return report


class MedicationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Medication.objects.all()
    serializer_class = MedicationSerializer
    permission_classes = [permissions.IsAuthenticated]


class PrescriptionViewSet(viewsets.ModelViewSet):
    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Prescription.objects.select_related(
            "patient", "prescriber", "pharmacy"
        ).prefetch_related("items__medication")
        if user.role == "patient":
            return qs.filter(patient=user)
        if user.role == "pharmacist":
            visible = qs.exclude(status=PrescriptionStatus.DRAFT)
            return visible.filter(pharmacy=user.clinic.pharmacies.first()) if user.clinic else visible
        if user.role in {"clinician", "chw"}:
            return qs.filter(prescriber=user)
        return qs

    def perform_create(self, serializer):
        rx = serializer.save(prescriber=self.request.user, patient_id=self._patient_id())
        _run_safety_for_prescription(rx)

    def _patient_id(self):
        # patient is derived from the consultation to avoid spoofing.
        from apps.consultations.models import Consultation

        consultation = get_object_or_404(
            Consultation, pk=self.request.data.get("consultation")
        )
        return consultation.patient_id

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        rx = serializer.instance
        return response.Response(PrescriptionSerializer(rx).data, status=status.HTTP_201_CREATED)

    @decorators.action(detail=False, methods=["post"], url_path="check-allergy")
    def check_allergy(self, request):
        serializer = CheckAllergySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        meds = list(Medication.objects.filter(id__in=data["medications"]))
        if len(meds) != len(set(data["medications"])):
            raise ValidationError("One or more medication ids are unknown.")

        allergies = data.get("patient_allergies")
        concurrent = data.get("concurrent_medications")
        if data.get("patient"):
            from django.contrib.auth import get_user_model

            patient = get_object_or_404(get_user_model(), pk=data["patient"])
            allergies = allergies or _patient_allergies(patient)
            concurrent = concurrent or _concurrent_meds(patient)

        report = check_prescription_safety(meds, allergies or [], concurrent or [])
        return response.Response(report)

    @decorators.action(detail=True, methods=["post"])
    def override(self, request, pk=None):
        rx = self.get_object()
        serializer = OverrideSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rx.override_reason = serializer.validated_data["reason"]
        rx.overridden_by = request.user
        rx.save(update_fields=["override_reason", "overridden_by"])
        return response.Response(PrescriptionSerializer(rx).data)

    @decorators.action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        """Route to the nearest MHS pharmacy. Blocked by unresolved safety alerts."""
        rx = self.get_object()
        report = _run_safety_for_prescription(rx)
        if report["blocking"] and not rx.override_reason:
            return response.Response(
                {
                    "detail": "Prescription blocked by safety check. Resolve or override.",
                    "safety_report": report,
                },
                status=status.HTTP_409_CONFLICT,
            )

        pharmacy_id = request.data.get("pharmacy")
        if pharmacy_id:
            rx.pharmacy = get_object_or_404(Pharmacy, pk=pharmacy_id)
        else:
            rx.pharmacy = nearest_pharmacy(getattr(rx.patient, "patient_profile", None))

        rx.fulfilment = request.data.get("fulfilment", rx.fulfilment)
        rx.status = PrescriptionStatus.PENDING
        rx.sent_to_pharmacy_at = timezone.now()
        rx.save(update_fields=["pharmacy", "fulfilment", "status", "sent_to_pharmacy_at"])

        push_pharmacy_status(
            {
                "event": "prescription.sent",
                "prescription": rx.id,
                "patient": rx.patient.get_full_name(),
                "pharmacy": rx.pharmacy.name if rx.pharmacy else None,
                "status": rx.status,
                "medications": rx.medication_list,
            }
        )
        return response.Response(PrescriptionSerializer(rx).data)
