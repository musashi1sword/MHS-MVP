# MHS-MVP — Mwafrika Health Services

Investor-ready MVP for a digitally enabled healthcare operating network for East
Africa: digital access, video visits, e-prescribing with a clinical safety layer,
affiliated-pharmacy routing, payments, and a metrics dashboard — one ecosystem,
built to execute a **7-minute investor demo**:

> Book → Intake → Video → Rx → Pharmacy → Metrics

## Quick start

```bash
./scripts/setup.sh     # venv + deps + migrate + seed (one time)
./scripts/dev.sh        # backend :8000 + frontend :5173
```

Open <http://localhost:5173>. On the login screen, **Seed demo data** then use a
quick sign-in. All demo users share the password `demo1234`.

| User | Role | Use for |
|---|---|---|
| `jane.doe@example.com` | patient | booking, intake, waiting room, patient side of the video visit |
| `dr.mwangi@example.com` | clinician | provider console: queue, video, note, e-prescribe |
| `pharm@example.com` | pharmacist | pharmacy board (live status) |
| `admin@example.com` | admin | metrics + Django `/admin` |

Jane Doe is seeded with a **penicillin allergy** and concurrent **warfarin**, so
prescribing amoxicillin (or ibuprofen) trips the safety layer on cue.

### Running the 2-party video visit locally

Open two browsers (or a normal + incognito window): sign in as the patient in one
and the clinician in the other, both navigating to the same visit. WebRTC mode
does a real peer connection over the Channels signalling socket; managed mode
issues a vendor-style room token and shows the local preview.

## Stack

- **Backend** — Django 5 + DRF, Django Channels (ASGI/WebSockets), Celery.
  PostgreSQL + Redis on the spec stack; **SQLite + in-memory channel layer +
  eager Celery** by default so the demo needs zero external services.
- **Frontend** — React + TypeScript (Vite).
- **Video** — dual-mode: custom WebRTC (COTURN/STUN + Channels signalling) and a
  managed API adapter (Twilio/Chime), both behind one `VideoProvider` interface.
- **Payments** — M-Pesa Daraja, Airtel Money, Stripe (IC payouts) adapters, all
  with a `mock` mode (the default).

To run on PostgreSQL + Redis: `docker compose up -d`, then set `DATABASE_URL` and
`REDIS_URL` (see `backend/.env.example`).

## Layout

```
backend/            Django project (config/) + apps/
  apps/accounts        custom user, roles, patient/provider profiles, JWT auth
  apps/clinics         clinics + pharmacies
  apps/appointments    slots, booking, queue, mock AI triage
  apps/consultations   visit lifecycle, SOAP note, /consultations/start
  apps/prescriptions   formulary, e-Rx, allergy/interaction safety layer
  apps/pharmacy        dispense routing + status board + transitions
  apps/payments        wallet, transactions, gateway adapters
  apps/communications  VideoProvider (webrtc|managed), signalling consumers
  apps/metrics         investor dashboard endpoint
  apps/demo            POST /api/v1/demo/seed + seed_demo management command
  scripts/             smoke_demo.py (full flow), smoke_ws.py (signalling)
frontend/           React app (src/pages, src/video, src/api)
docs/               ARCHITECTURE.md, DEMO_RUNBOOK.md, API.md
```

## Tests / smoke checks

```bash
cd backend
../.venv/bin/python manage.py test                 # unit tests (safety layer)
../.venv/bin/python scripts/smoke_demo.py           # full Book→Metrics flow
../.venv/bin/python scripts/smoke_ws.py             # WebRTC signalling relay
```

## Notes

- All seeded data is clearly synthetic — **no real PHI**.
- `DJANGO_SECRET_KEY` and gateway keys are dev placeholders; set real values in
  `backend/.env` for anything beyond a local demo.
