#!/usr/bin/env bash
# Run backend (Daphne/ASGI on :8000) and frontend (Vite on :5173) together.
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"

[ -d .nodeenv ] && export PATH="$ROOT/.nodeenv/bin:$PATH"
NPM="$(command -v npm || echo "$ROOT/.nodeenv/bin/npm")"

export DJANGO_ALLOWED_HOSTS="${DJANGO_ALLOWED_HOSTS:-localhost,127.0.0.1}"

echo "==> Backend  http://localhost:8000   (API /api/v1, docs /api/docs, admin /admin)"
(cd backend && exec "$ROOT/.venv/bin/daphne" -b 0.0.0.0 -p 8000 config.asgi:application) &
BACK=$!

echo "==> Frontend http://localhost:5173"
(cd frontend && exec "$NPM" run dev) &
FRONT=$!

trap 'kill $BACK $FRONT 2>/dev/null || true' EXIT INT TERM
wait
