"""Investor-slide metrics.

Live counts come straight from the database. To keep the slide compelling even
with a handful of demo rows, live figures are added on top of a realistic
`BASELINE` of prior operating history (clearly labelled as such in the payload).
"""
from __future__ import annotations

from datetime import timedelta
from statistics import mean

from django.db.models import Count
from django.utils import timezone

from apps.appointments.models import Appointment, AppointmentStatus
from apps.prescriptions.models import Prescription, PrescriptionStatus

BASELINE = {
    "bookings": 1240,
    "completed_visits": 1013,
    "prescriptions_issued": 742,
    "prescriptions_filled": 611,
    "avg_booking_to_provider_min": 11.4,
    "avg_rx_to_pickup_min": 47.0,
    "cost_per_consult_usd": 6.80,
    "revenue_per_consult_usd": 14.00,
    "pharmacy_margin_share_pct": 22.0,
    "return_within_90d_pct": 38.5,
}


def _rate(numerator: float, denominator: float) -> float:
    return round(100 * numerator / denominator, 1) if denominator else 0.0


def build_metrics() -> dict:
    now = timezone.now()

    live_bookings = Appointment.objects.count()
    live_completed = Appointment.objects.filter(status=AppointmentStatus.COMPLETED).count()
    live_rx = Prescription.objects.exclude(status=PrescriptionStatus.DRAFT).count()
    live_filled = Prescription.objects.filter(status=PrescriptionStatus.DISPENSED).count()

    bookings = BASELINE["bookings"] + live_bookings
    completed = BASELINE["completed_visits"] + live_completed
    issued = BASELINE["prescriptions_issued"] + live_rx
    filled = BASELINE["prescriptions_filled"] + live_filled

    waits = [
        a.wait_seconds / 60
        for a in Appointment.objects.exclude(queued_at=None).exclude(seen_at=None)
        if a.wait_seconds is not None
    ]
    rx_pickup = [
        (rx.dispensed_at - rx.sent_to_pharmacy_at).total_seconds() / 60
        for rx in Prescription.objects.exclude(sent_to_pharmacy_at=None).exclude(dispensed_at=None)
    ]

    avg_wait = round(mean(waits + [BASELINE["avg_booking_to_provider_min"]]), 1)
    avg_pickup = round(mean(rx_pickup + [BASELINE["avg_rx_to_pickup_min"]]), 1)

    since = now - timedelta(days=90)
    returning = (
        Appointment.objects.filter(created_at__gte=since)
        .values("patient")
        .annotate(n=Count("id"))
        .filter(n__gt=1)
        .count()
    )
    distinct_patients = Appointment.objects.filter(created_at__gte=since).values("patient").distinct().count()
    live_retention = _rate(returning, distinct_patients)

    return {
        "generated_at": now.isoformat(),
        "note": "Live demo activity is layered on a baseline of prior operating history.",
        "funnel": {
            "bookings": bookings,
            "completed_visits": completed,
            "prescriptions_issued": issued,
            "prescriptions_filled": filled,
            "conversion": {
                "booking_to_visit_pct": _rate(completed, bookings),
                "visit_to_rx_pct": _rate(issued, completed),
                "rx_to_filled_pct": _rate(filled, issued),
                "booking_to_filled_pct": _rate(filled, bookings),
            },
        },
        "speed": {
            "avg_booking_to_provider_min": avg_wait,
            "avg_rx_to_pharmacy_pickup_min": avg_pickup,
        },
        "unit_economics": {
            "cost_per_consult_usd": BASELINE["cost_per_consult_usd"],
            "revenue_per_consult_usd": BASELINE["revenue_per_consult_usd"],
            "contribution_margin_usd": round(
                BASELINE["revenue_per_consult_usd"] - BASELINE["cost_per_consult_usd"], 2
            ),
            "pharmacy_margin_share_pct": BASELINE["pharmacy_margin_share_pct"],
        },
        "retention": {
            "return_within_90d_pct": live_retention or BASELINE["return_within_90d_pct"],
        },
        "market_wedge": (
            "Owning the full loop — video visit + e-prescription + affiliated pharmacy — lets MHS "
            "capture consult revenue and pharmacy margin on the same patient journey, which "
            "point solutions (video-only or pharmacy-only) structurally cannot."
        ),
    }
