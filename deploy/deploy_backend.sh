#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
SERVICE_NAME="${SERVICE_NAME:-tokendancer-persona-api}"

cd "${BACKEND_DIR}"

python3 -m pip install -r requirements.txt

if [ -f alembic.ini ]; then
  alembic upgrade head
fi

if command -v systemctl >/dev/null 2>&1; then
  systemctl restart "${SERVICE_NAME}"
else
  echo "systemctl is unavailable; restart ${SERVICE_NAME} manually."
fi
