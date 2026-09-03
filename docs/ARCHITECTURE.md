# Architecture

## Shape

Modular monolith (Django), split into domain apps that talk through services and
serializers rather than reaching into each other's models. Deployable as one
ASGI process now; each app is a candidate to peel into its own service later
(the spec's "microservices (modular monolith)").

```
React (Vite) ──/api──▶ DRF views ──▶ app services ──▶ models ──▶ Postgres/SQLite
      │                    │
      └──/ws──▶ Channels consumers ──▶ channel layer (Redis / in-memory)
```

## Runtime posture: demo-first, scale-ready

Everything defaults to zero-dependency so the investor demo can't be broken by an
external service:

| Concern | Demo default | Spec / production |
|---|---|---|
| Database | SQLite | PostgreSQL (`DATABASE_URL`) |
| Channel layer | in-memory | Redis (`REDIS_URL`) |
| Celery | eager (in-process) | Redis broker + workers |
| Video | WebRTC w/ public STUN, or mock managed token | COTURN + Twilio/Chime creds |
| Payments | `mock` adapters | Daraja / Airtel / Stripe keys |

All switches are environment variables (`backend/.env`).

## Dual-mode video (`apps/communications`)

One interface, two implementations, chosen per request or by
`settings.VIDEO_PROVIDER`:

```
VideoProvider (ABC)
├── WebRTCVideoProvider   create_session → mint room; join_info → ICE servers + Channels signal URL
└── ManagedVideoProvider  create_session → vendor room; join_info → HS256 room token (vendor JWT shape)
```

`get_provider(name)` returns the implementation; callers (`/consultations/start`,
`/video-sessions/{id}/join`) only touch `JoinInfo`. The React `useVideoRoom` hook
mirrors this: WebRTC runs a real `RTCPeerConnection` with perfect-negotiation
over the `ConsultationSignalConsumer` relay; managed hands `join.token` to the
vendor SDK (stubbed to local-preview for the demo).

## Clinical safety layer (`apps/prescriptions/safety.py`)

`check_prescription_safety(medications, patient_allergies, concurrent_meds)`
returns a structured report with a `blocking` flag. Two checks:

1. **Allergy** — patient allergy terms matched against each drug's `name`,
   `drug_class`, and `allergen_groups` (cross-reactivity, e.g. penicillin →
   amoxicillin). Any hit is blocking.
2. **Interaction** — pairwise over new + concurrent meds against `DrugInteraction`
   rules (matched by name or class). `major` / `contraindicated` are blocking.

`POST /prescriptions/{id}/send` re-runs the check and returns **409** unless the
prescription carries an `override_reason`. The override, its author, and the full
`safety_report` are persisted on the prescription for audit.

## Realtime (`Channels`)

- `ConsultationSignalConsumer` — per-room group; relays `offer`/`answer`/
  `candidate`/`bye`/`chat` between the two peers, never inspecting media.
- `PharmacyStatusConsumer` — single `pharmacy.status` group; `broadcast.py`
  fans out prescription routing and status transitions to every open board.
- WS auth: `?token=<JWT>` via `JWTAuthMiddleware` (`apps/communications/middleware.py`).

## Metrics (`apps/metrics/service.py`)

Live DB counts (bookings, completed visits, Rx issued/filled, wait times,
90-day return rate) layered on a labelled `BASELINE` of prior operating history
so the slide is compelling with only demo rows present.

## Data model (core)

```
User ─┬─ PatientProfile (allergies, insurance, med history, geo)
      └─ ProviderProfile (specialty, licence, is_overseas_ic)
Clinic ─< Pharmacy
ProviderSlot ─1:1─ Appointment ─1:1─ Consultation ─< Prescription ─< PrescriptionItem >─ Medication
                                          │                  └─ Pharmacy, DispenseEvent
                                          └─< VideoSession, StoreAndForwardMessage
Medication ── DrugInteraction (by name/class)
Wallet, Transaction (appointment-linked)
```

## Not in the MVP

Specialist / CME network (spec: Phase 2). USSD is a mock adapter. Live gateway
integrations are stubbed behind `mock` modes.
