"""Idempotent synthetic-data seeder for the investor demo. No real PHI."""
from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import PatientProfile, ProviderProfile
from apps.appointments.models import Appointment, AppointmentStatus, ProviderSlot
from apps.clinics.models import Clinic, Pharmacy
from apps.payments.models import Wallet
from apps.prescriptions.models import DrugInteraction, Medication

User = get_user_model()

DEMO_PASSWORD = "demo1234"

CLINICS = [
    {"name": "Africanna Health Center - Westlands", "holding_company": "africanna", "city": "Nairobi",
     "address": "Woodvale Grove, Westlands, Nairobi", "latitude": -1.2686, "longitude": 36.8100},
    {"name": "Mwafrika Clinic - Kibera", "holding_company": "africanna", "city": "Nairobi",
     "address": "Olympic Estate, Kibera, Nairobi", "latitude": -1.3130, "longitude": 36.7890},
    {"name": "The Clinician Clinic - Kisumu", "holding_company": "clinician", "city": "Kisumu",
     "address": "Oginga Odinga Street, Kisumu", "latitude": -0.0917, "longitude": 34.7680},
]

# 3-5 sample drugs; amoxicillin trips the penicillin allergy, warfarin+ibuprofen interact.
FORMULARY = [
    {"name": "Amoxicillin", "form": "capsule", "strength": "500mg", "drug_class": "penicillin",
     "allergen_groups": ["penicillin", "beta-lactam"], "rxnorm_code": "723"},
    {"name": "Amlodipine", "form": "tablet", "strength": "5mg", "drug_class": "calcium channel blocker",
     "allergen_groups": [], "rxnorm_code": "17767"},
    {"name": "Metformin", "form": "tablet", "strength": "500mg", "drug_class": "biguanide",
     "allergen_groups": [], "rxnorm_code": "6809"},
    {"name": "Ibuprofen", "form": "tablet", "strength": "400mg", "drug_class": "nsaid",
     "allergen_groups": [], "rxnorm_code": "5640"},
    {"name": "Warfarin", "form": "tablet", "strength": "5mg", "drug_class": "anticoagulant",
     "allergen_groups": [], "rxnorm_code": "11289", "is_controlled": False},
]

INTERACTIONS = [
    {"left": "anticoagulant", "right": "nsaid", "severity": "major",
     "description": "NSAIDs increase bleeding risk with anticoagulants (warfarin). Avoid combination."},
    {"left": "warfarin", "right": "ibuprofen", "severity": "major",
     "description": "Concurrent warfarin + ibuprofen markedly raises GI bleeding risk."},
]


def _user(email, first, last, role, phone=""):
    user, created = User.objects.get_or_create(
        email=email,
        defaults={"username": email, "first_name": first, "last_name": last, "role": role, "phone": phone},
    )
    if created:
        user.set_password(DEMO_PASSWORD)
        user.save()
    Wallet.objects.get_or_create(user=user)
    return user


@transaction.atomic
def seed_demo() -> dict:
    now = timezone.now()

    clinics = {c["name"]: Clinic.objects.get_or_create(name=c["name"], defaults=c)[0] for c in CLINICS}

    pharmacies = {}
    for c in CLINICS:
        clinic = clinics[c["name"]]
        pharm, _ = Pharmacy.objects.get_or_create(
            name=f"{c['name']} Pharmacy",
            defaults={
                "clinic": clinic, "city": c["city"], "address": c["address"],
                "latitude": c["latitude"], "longitude": c["longitude"],
                "is_mhs_affiliated": True, "supports_delivery": True,
            },
        )
        pharmacies[c["name"]] = pharm

    for m in FORMULARY:
        Medication.objects.get_or_create(
            name=m["name"], strength=m["strength"], form=m["form"], defaults=m
        )
    for i in INTERACTIONS:
        DrugInteraction.objects.get_or_create(left=i["left"], right=i["right"], defaults=i)

    # People.
    westlands = clinics["Africanna Health Center - Westlands"]
    patient = _user("jane.doe@example.com", "Jane", "Doe", "patient", "+254700000001")
    provider = _user("dr.mwangi@example.com", "John", "Mwangi", "clinician", "+254700000002")
    provider.clinic = westlands
    provider.save(update_fields=["clinic"])
    pharmacist = _user("pharm@example.com", "Aisha", "Otieno", "pharmacist", "+254700000003")
    pharmacist.clinic = westlands
    pharmacist.save(update_fields=["clinic"])
    chw = _user("chw@example.com", "Peter", "Kamau", "chw", "+254700000004")

    admin = _user("admin@example.com", "MHS", "Admin", "admin")
    if not admin.is_staff:
        admin.is_staff = admin.is_superuser = True
        admin.save(update_fields=["is_staff", "is_superuser"])

    PatientProfile.objects.update_or_create(
        user=patient,
        defaults={
            "date_of_birth": "1989-04-12",
            "address": "Parklands Road, Westlands, Nairobi",
            "latitude": -1.2630, "longitude": 36.8180,
            "allergies": ["penicillin"],
            "insurance_provider": "Jubilee Health (TEST)",
            "insurance_member_id": "TEST-JD-00417",
            "medication_history": ["Amlodipine 5mg", "Warfarin 5mg"],
        },
    )
    ProviderProfile.objects.update_or_create(
        user=provider,
        defaults={"specialty": "Internal Medicine", "license_number": "KMPDC-TEST-4821", "is_overseas_ic": False},
    )

    # Open same-day slots for Dr. Mwangi.
    ProviderSlot.objects.filter(provider=provider, start__gte=now).delete()
    base = now.replace(minute=0, second=0, microsecond=0)
    slots = []
    for offset in (1, 2, 3, 4):
        start = base + timedelta(hours=offset)
        slots.append(
            ProviderSlot.objects.create(
                provider=provider, clinic=westlands, start=start, end=start + timedelta(minutes=20)
            )
        )

    # Historical completed appointments so the funnel/speed metrics have live rows.
    made = 0
    for d in range(1, 8):
        when = now - timedelta(days=d, hours=2)
        appt = Appointment.objects.create(
            patient=patient, provider=provider, clinic=westlands,
            scheduled_start=when, mode="video", status=AppointmentStatus.COMPLETED,
            symptom_note="Follow-up on blood pressure control.",
            created_at=when - timedelta(minutes=20),
            queued_at=when - timedelta(minutes=12),
            seen_at=when, completed_at=when + timedelta(minutes=14),
        )
        made += 1
        _ = appt

    return {
        "status": "seeded",
        "password_for_all_demo_users": DEMO_PASSWORD,
        "accounts": {
            "patient": patient.email,
            "clinician": provider.email,
            "pharmacist": pharmacist.email,
            "chw": chw.email,
            "admin": admin.email,
        },
        "clinics": [c.name for c in clinics.values()],
        "pharmacies": [p.name for p in pharmacies.values()],
        "formulary": [m["name"] for m in FORMULARY],
        "open_slots": [s.start.isoformat() for s in slots],
        "historical_appointments": made,
    }
