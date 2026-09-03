#!/usr/bin/env bash
# One-time setup: Python venv + backend deps, Node toolchain + frontend deps.
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"

echo "==> Python virtualenv (.venv)"
python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r backend/requirements.txt

echo "==> Backend: migrate + seed demo data"
(cd backend && "$ROOT/.venv/bin/python" manage.py migrate)
(cd backend && "$ROOT/.venv/bin/python" manage.py seed_demo)

echo "==> Node toolchain"
if command -v node >/dev/null 2>&1; then
  NPM=npm
else
  echo "   node not found on PATH — bootstrapping a local copy via nodeenv"
  .venv/bin/pip install -q nodeenv
  .venv/bin/nodeenv --node=lts .nodeenv
  export PATH="$ROOT/.nodeenv/bin:$PATH"
  NPM="$ROOT/.nodeenv/bin/npm"
fi

echo "==> Frontend deps"
(cd frontend && "$NPM" install --no-audit --no-fund)

cat <<'DONE'

Setup complete. Start the app with:

    ./scripts/dev.sh

Demo users (password: demo1234)
    jane.doe@example.com    patient
    dr.mwangi@example.com   clinician
    pharm@example.com       pharmacist
    admin@example.com       admin  (also Django /admin)
DONE
