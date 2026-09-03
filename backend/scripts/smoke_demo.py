"""End-to-end smoke test of the investor demo flow, via the DRF test client.

    python manage.py shell < scripts/smoke_demo.py
or  ../.venv/bin/python scripts/smoke_demo.py
"""
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ["DJANGO_ALLOWED_HOSTS"] = "testserver,localhost,127.0.0.1"
django.setup()

from rest_framework.test import APIClient  # noqa: E402

from apps.demo.seed import seed_demo  # noqa: E402

BASE = "/api/v1"
ok = 0


def step(label, cond, extra=""):
    global ok
    mark = "PASS" if cond else "FAIL"
    if cond:
        ok += 1
    print(f"  [{mark}] {label} {extra}")
    assert cond, label


seed = seed_demo()
print("Seeded demo data.")

c = APIClient()


def login(email):
    r = c.post(f"{BASE}/auth/login", {"email": email, "password": "demo1234"}, format="json")
    assert r.status_code == 200, r.content
    return r.data["access"]


# --- 1. Patient books + completes intake -------------------------------------
patient_token = login("jane.doe@example.com")
c.credentials(HTTP_AUTHORIZATION=f"Bearer {patient_token}")

slots = c.get(f"{BASE}/slots").data
step("open slots available", len(slots) > 0, f"({len(slots)})")

book = c.post(
    f"{BASE}/appointments",
    {"slot": slots[0]["id"], "symptom_note": "Sore throat and mild fever for 2 days.",
     "mode": "video", "intake": {"temperature_c": 37.9}},
    format="json",
)
step("booking created", book.status_code == 201, book.content[:200])
appt_id = book.data["id"]
step("triage ran", book.data["triage"].get("acuity") in {"routine", "urgent", "emergency"},
     book.data["triage"].get("acuity"))

intake = c.post(f"{BASE}/appointments/{appt_id}/intake", {"intake": {"duration_days": 2}}, format="json")
step("intake accepted -> in_queue", intake.data["status"] == "in_queue", intake.data["status"])

# --- 2. Provider joins the visit and writes a note --------------------------
prov_token = login("dr.mwangi@example.com")
c.credentials(HTTP_AUTHORIZATION=f"Bearer {prov_token}")

queue = c.get(f"{BASE}/appointments/queue").data
step("appt in provider queue", any(a["id"] == appt_id for a in queue), f"({len(queue)})")

start = c.post(
    f"{BASE}/consultations/start",
    {"appointment": appt_id, "mode": "video", "video_provider": "webrtc"},
    format="json",
)
step("consultation started", start.status_code in (200, 201), start.content[:200])
consult_id = start.data["consultation"]["id"]
join = start.data["join"]
step("webrtc join info", join["provider"] == "webrtc" and "iceServers" in join, str(list(join))[:120])
step("signal url present", join.get("signalUrl", "").startswith("/ws/consultations/"), join.get("signalUrl"))

# managed mode also works from the same interface
start_m = c.post(
    f"{BASE}/consultations/start",
    {"appointment": appt_id, "mode": "video", "video_provider": "managed"},
    format="json",
)
step("managed join info", start_m.data["join"]["provider"] == "managed" and "token" in start_m.data["join"],
     start_m.data["join"].get("vendor"))

note = c.patch(
    f"{BASE}/consultations/{consult_id}/note",
    {"subjective": "2d sore throat, low-grade fever", "assessment": "Acute pharyngitis, likely bacterial",
     "plan": "Antibiotics, fluids, review in 3 days"},
    format="json",
)
step("clinical note saved", note.status_code == 200 and "pharyngitis" in note.data["assessment"], "")

# --- 3. E-prescription with the allergy check firing ------------------------
formulary = {m["name"]: m["id"] for m in c.get(f"{BASE}/formulary").data}

check = c.post(
    f"{BASE}/prescriptions/check-allergy",
    {"patient": None, "medications": [formulary["Amoxicillin"]], "patient_allergies": ["penicillin"]},
    format="json",
)
step("allergy check flags amoxicillin", check.data["blocking"] is True,
     [a["type"] for a in check.data["alerts"]])

rx = c.post(
    f"{BASE}/prescriptions",
    {"consultation": consult_id, "fulfilment": "pickup",
     "items": [{"medication": formulary["Amoxicillin"], "dose": "500mg", "frequency": "TDS", "duration": "5 days"}]},
    format="json",
)
step("prescription created (draft)", rx.status_code == 201, rx.content[:200])
rx_id = rx.data["id"]
step("allergen alert triggered on Rx", rx.data["allergen_alert_triggered"] is True, "")

blocked = c.post(f"{BASE}/prescriptions/{rx_id}/send", {}, format="json")
step("send blocked by safety layer (409)", blocked.status_code == 409, blocked.status_code)

# Edge-case script: provider overrides with a reason.
ovr = c.post(f"{BASE}/prescriptions/{rx_id}/override", {"reason": "Patient tolerated amoxicillin last year; benefit outweighs risk."}, format="json")
step("override recorded", ovr.status_code == 200, "")

# Safe alternative path: swap to a non-allergen drug and send.
rx2 = c.post(
    f"{BASE}/prescriptions",
    {"consultation": consult_id, "fulfilment": "pickup",
     "items": [{"medication": formulary["Metformin"], "dose": "500mg", "frequency": "BD", "duration": "30 days"}]},
    format="json",
)
rx2_id = rx2.data["id"]
sent = c.post(f"{BASE}/prescriptions/{rx2_id}/send", {}, format="json")
step("safe prescription routed to pharmacy", sent.status_code == 200 and sent.data["status"] == "pending", sent.data.get("pharmacy_name"))
step("auto-routed to nearest MHS pharmacy", sent.data["pharmacy_name"] is not None, sent.data["pharmacy_name"])

# --- 4. Pharmacy handoff + status updates ----------------------------------
pharm_token = login("pharm@example.com")
c.credentials(HTTP_AUTHORIZATION=f"Bearer {pharm_token}")

pq = c.get(f"{BASE}/pharmacy/queue").data
step("prescription on pharmacy board", any(p["id"] == rx2_id for p in pq), f"({len(pq)})")

to_ready = c.post(f"{BASE}/pharmacy/prescriptions/{rx2_id}/status", {"status": "ready"}, format="json")
step("status -> Ready for pickup", to_ready.data["status"] == "ready", "")
to_disp = c.post(f"{BASE}/pharmacy/prescriptions/{rx2_id}/status", {"status": "dispensed"}, format="json")
step("status -> Dispensed", to_disp.data["status"] == "dispensed", "")

bad = c.post(f"{BASE}/pharmacy/prescriptions/{rx2_id}/status", {"status": "pending"}, format="json")
step("invalid transition rejected", bad.status_code == 400, bad.status_code)

# --- 5. Provider completes the visit; metrics slide ------------------------
c.credentials(HTTP_AUTHORIZATION=f"Bearer {prov_token}")
done = c.post(f"{BASE}/appointments/{appt_id}/complete", {}, format="json")
step("visit completed", done.data["status"] == "completed", "")

c.credentials()
metrics = c.get(f"{BASE}/dashboard/metrics")
step("metrics endpoint (no auth)", metrics.status_code == 200, "")
f = metrics.data["funnel"]
step("funnel has conversion rates", "booking_to_filled_pct" in f["conversion"], f["conversion"])
step("speed metrics present", "avg_booking_to_provider_min" in metrics.data["speed"], metrics.data["speed"])

print(f"\n{ok} checks passed. Demo flow is wired end to end.")
