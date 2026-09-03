# Investor Demo Runbook (7 minutes)

**Pre-flight**
- `./scripts/dev.sh` running; <http://localhost:5173> open.
- Two browser windows: **A** signed in as `jane.doe@example.com` (patient),
  **B** signed in as `dr.mwangi@example.com` (clinician).
- Click **Seed demo data** once on the login screen if the DB is fresh.
- Have the pre-recorded screen capture ready as the network-failure fallback.

| Time | Screen | Action |
|---|---|---|
| 0:00–0:30 | Metrics (B) | "This is a live product, not a mockup." Show the dashboard is served from the real API. |
| 0:30–2:00 | Book & Intake (A) | Patient logs a symptom ("sore throat, fever"), picks a same-day slot, books, completes the quick intake → **joins the queue**. Point out the mock AI triage tag. |
| 2:00–4:00 | Provider Console (B) → Visit | Patient appears in the queue. Provider clicks **Open**, then **Open video visit** — both windows connect. Brief scripted exchange. Provider writes the SOAP note and **Save note**. |
| 4:00–5:00 | Provider Console (B) | Provider adds **Amoxicillin** to the prescription. The **safety layer fires**: penicillin-allergy alert, blocking. Try **Create prescription** → **Send** → blocked (409). Enter an override reason *or* swap to a safe drug (Metformin) and send. |
| 5:00–6:00 | Pharmacy Board (open a 3rd window as `pharm@example.com`) | The prescription appears instantly (WebSocket). Auto-routed to **Africanna Health Center – Westlands Pharmacy** (nearest to Jane's address). Pharmacist clicks **Mark ready for pickup** → patient-facing status updates in real time. |
| 6:00–7:00 | Metrics (B) | Provider clicks **Complete visit**. Cut to the Metrics dashboard — funnel, speed, unit economics, retention, market wedge. Transition into the pitch. |

## Edge-case script (safety layer)

> Provider tries to prescribe a drug the patient is allergic to. The system
> flashes a blocking warning and refuses to route the prescription to the
> pharmacy until the provider records an explicit override reason.

Trigger: prescribe **Amoxicillin** (penicillin) or **Ibuprofen** (interacts with
Jane's warfarin) for `jane.doe@example.com`.

## Exit criteria

**Pass:** demo completes in ≤ 7 min · ≥ 70% of eligible consultations complete ·
provider NPS ≥ 7 · one viable paying/funded segment shown.

**Fail:** allergy alert doesn't fire · pharmacy status doesn't update in real time
· network failure crashes the demo with no fallback.
