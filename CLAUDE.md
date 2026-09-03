# CLAUDE.md

Guidance for working in this repo.

## What this is

MHS-MVP — investor-demo MVP for Mwafrika Health Services. The whole product is
built around one 7-minute flow: **Book → Intake → Video → Rx → Pharmacy →
Metrics**. When in doubt, optimise for that demo being fast and unbreakable.
See `docs/DEMO_RUNBOOK.md` and `docs/ARCHITECTURE.md`.

## Commands

```bash
./scripts/setup.sh          # one-time: venv, deps, migrate, seed
./scripts/dev.sh             # run backend :8000 + frontend :5173

cd backend
../.venv/bin/python manage.py migrate
../.venv/bin/python manage.py seed_demo             # idempotent synthetic data
../.venv/bin/python manage.py test                  # unit tests
../.venv/bin/python scripts/smoke_demo.py           # full-flow smoke test
../.venv/bin/python scripts/smoke_ws.py             # websocket signalling smoke test

cd frontend
<node>/npm run build        # tsc -b + vite build  (also the typecheck)
<node>/npm run dev
```

Local Node lives in `.nodeenv/bin` (bootstrapped by `setup.sh` when system Node
is absent); prefix npm calls with that path or add it to `PATH`.

## Conventions

- **Backend**: Django 5 + DRF. One app per domain under `backend/apps/`. Business
  logic goes in `services.py` / `safety.py` / `triage.py` / provider classes —
  keep views thin. API paths are **slash-free** (`APPEND_SLASH = False`,
  `DefaultRouter(trailing_slash=False)`).
- **Runtime**: must run with no external services (SQLite, in-memory channels,
  eager Celery, mock gateways). Every prod dependency is opt-in via a
  `backend/.env` variable — never make one mandatory.
- **Video**: all video code goes through the `VideoProvider` interface
  (`apps/communications/providers/`) and the `useVideoRoom` hook. Don't call a
  vendor SDK directly from a view or page.
- **Safety layer is load-bearing for the demo** (`apps/prescriptions/safety.py`).
  Changes there need a test in `apps/prescriptions/tests.py` and a green
  `smoke_demo.py`.
- **Frontend**: React + TS, `strict` on, `noUnusedLocals`. Fetch through
  `src/api/client.ts`; types in `src/api/types.ts`. No component libraries —
  plain CSS in `src/styles.css`.
- Seed data is synthetic only. Never add anything resembling real PHI.

## After changing models

```bash
cd backend && ../.venv/bin/python manage.py makemigrations && ../.venv/bin/python manage.py migrate
```
Commit the migration files.
