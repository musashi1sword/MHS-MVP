from django.utils import timezone

from apps.communications.broadcast import push_pharmacy_status
from apps.prescriptions.models import Prescription, PrescriptionStatus

from .models import DispenseEvent

# Allowed forward transitions on the pharmacy board.
TRANSITIONS = {
    PrescriptionStatus.PENDING: {PrescriptionStatus.READY, PrescriptionStatus.OUT_FOR_DELIVERY, PrescriptionStatus.CANCELLED},
    PrescriptionStatus.READY: {PrescriptionStatus.DISPENSED, PrescriptionStatus.CANCELLED},
    PrescriptionStatus.OUT_FOR_DELIVERY: {PrescriptionStatus.DISPENSED, PrescriptionStatus.CANCELLED},
}


class InvalidTransition(Exception):
    pass


def advance_prescription(rx: Prescription, to_status: str, actor=None, note: str = "") -> Prescription:
    allowed = TRANSITIONS.get(rx.status, set())
    if to_status not in allowed:
        raise InvalidTransition(f"Cannot move {rx.status} -> {to_status}")

    from_status = rx.status
    rx.status = to_status
    fields = ["status"]
    if to_status == PrescriptionStatus.READY:
        rx.ready_at = timezone.now()
        fields.append("ready_at")
    if to_status == PrescriptionStatus.DISPENSED:
        rx.dispensed_at = timezone.now()
        fields.append("dispensed_at")
    rx.save(update_fields=fields)

    DispenseEvent.objects.create(
        prescription=rx, from_status=from_status, to_status=to_status, actor=actor, note=note
    )
    push_pharmacy_status(
        {
            "event": "prescription.status",
            "prescription": rx.id,
            "patient": rx.patient.get_full_name(),
            "pharmacy": rx.pharmacy.name if rx.pharmacy else None,
            "status": rx.status,
            "status_display": rx.get_status_display(),
        }
    )
    return rx
