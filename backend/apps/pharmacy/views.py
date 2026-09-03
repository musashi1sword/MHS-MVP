from rest_framework import decorators, permissions, response, status, views

from apps.prescriptions.models import Prescription, PrescriptionStatus
from apps.prescriptions.serializers import PrescriptionSerializer

from .services import InvalidTransition, advance_prescription


class PharmacyQueueView(views.APIView):
    """The pharmacy board: everything sent to a pharmacy and not yet closed out."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = (
            Prescription.objects.select_related("patient", "pharmacy", "prescriber")
            .prefetch_related("items__medication")
            .exclude(status__in=[PrescriptionStatus.DRAFT])
            .order_by("sent_to_pharmacy_at")
        )
        pharmacy_id = request.query_params.get("pharmacy")
        if pharmacy_id:
            qs = qs.filter(pharmacy_id=pharmacy_id)
        active = request.query_params.get("active")
        if active != "false":
            qs = qs.exclude(status__in=[PrescriptionStatus.DISPENSED, PrescriptionStatus.CANCELLED])
        return response.Response(PrescriptionSerializer(qs, many=True).data)


class PrescriptionStatusView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        rx = Prescription.objects.get(pk=pk)
        to_status = request.data.get("status")
        try:
            advance_prescription(rx, to_status, actor=request.user, note=request.data.get("note", ""))
        except InvalidTransition as exc:
            return response.Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return response.Response(PrescriptionSerializer(rx).data)
