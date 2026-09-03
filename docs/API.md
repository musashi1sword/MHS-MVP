# API reference (v1)

Base path `/api/v1`. JSON only. Auth: `Authorization: Bearer <access>` from
`POST /auth/login`. Interactive schema at `/api/docs` (OpenAPI at `/api/schema`).

Paths are **slash-free** (`APPEND_SLASH = False`).

## Auth — `apps/accounts`
| Method | Path | Notes |
|---|---|---|
| POST | `/auth/login` | `{email, password}` → `{access, refresh, user}` |
| POST | `/auth/refresh` | `{refresh}` → `{access}` |
| POST | `/auth/register` | `{email, password, role, ...}` |
| GET | `/auth/me` | current user + profile |

## Clinics — `apps/clinics`
`GET /clinics`, `GET /clinics/{id}`, `GET /pharmacies`, `GET /pharmacies/{id}`

## Appointments — `apps/appointments`
| Method | Path | Notes |
|---|---|---|
| GET | `/slots` | open provider slots (`?provider=`, `?available=false`) |
| GET/POST | `/appointments` | POST body `{slot, symptom_note, mode, intake}` — books + runs triage |
| GET | `/appointments/{id}` | |
| POST | `/appointments/{id}/intake` | `{intake:{...}}` → moves to `in_queue` |
| GET | `/appointments/queue` | provider queue, triage-ordered |
| POST | `/appointments/{id}/complete` | provider marks visit completed |

## Consultations — `apps/consultations`
| Method | Path | Notes |
|---|---|---|
| POST | `/consultations/start` | `{appointment, mode, video_provider?}` → `{consultation, session_id, join}` (initiates the dual-mode video session) |
| GET | `/consultations/{id}` | includes `video_sessions` |
| PUT/PATCH | `/consultations/{id}/note` | SOAP fields |
| POST | `/consultations/{id}/end` | ends consultation + video sessions |

## Video — `apps/communications`
| Method | Path | Notes |
|---|---|---|
| POST | `/video-sessions/{id}/join` | provider-agnostic join info |
| POST | `/video-sessions/{id}/end` | |
| GET/POST | `/messages` | store-and-forward messaging (`?consultation=`) |
| WS | `/ws/consultations/{room}/signal?token=` | WebRTC SDP/ICE relay |
| WS | `/ws/pharmacy/status?token=` | live prescription/pharmacy status |

## Prescriptions — `apps/prescriptions`
| Method | Path | Notes |
|---|---|---|
| GET | `/formulary` | sample drugs |
| GET/POST | `/prescriptions` | POST `{consultation, fulfilment, items:[{medication,dose,frequency,duration}]}` — runs safety check on create |
| POST | `/prescriptions/check-allergy` | `{medications:[id], patient? , patient_allergies?, concurrent_medications?}` → safety report |
| POST | `/prescriptions/{id}/override` | `{reason}` |
| POST | `/prescriptions/{id}/send` | routes to nearest MHS pharmacy; **409** if blocked by an unresolved safety alert |

## Pharmacy — `apps/pharmacy`
| Method | Path | Notes |
|---|---|---|
| GET | `/pharmacy/queue` | routed prescriptions (`?pharmacy=`, `?active=false`) |
| POST | `/pharmacy/prescriptions/{id}/status` | `{status}` — `pending→ready/out_for_delivery→dispensed`; broadcasts on the status WS |

## Payments — `apps/payments`
`GET /payments/wallet` · `POST /payments/charge` `{provider, amount, kind}` ·
`POST /payments/payout` `{provider_user, amount, destination}` (admin) ·
`GET /transactions`

## Metrics — `apps/metrics`
`GET /dashboard/metrics` — funnel / speed / unit economics / retention / wedge (no auth).

## Demo — `apps/demo`
`POST /demo/seed` — idempotent synthetic data. Also `manage.py seed_demo`.
