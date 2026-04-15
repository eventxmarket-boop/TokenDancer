#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
SERVICE_NAME="${SERVICE_NAME:-tokendancer-backend.service}"
SERVICE_UNIT_SRC="${ROOT_DIR}/deploy/${SERVICE_NAME}"
SERVICE_UNIT_DST="/etc/systemd/system/${SERVICE_NAME}"
VENV_DIR="${VENV_DIR:-${BACKEND_DIR}/.venv}"
PYTHON_BIN="${PYTHON_BIN:-${VENV_DIR}/bin/python}"

cd "${BACKEND_DIR}"

if [ ! -x "${PYTHON_BIN}" ]; then
  python3 -m venv "${VENV_DIR}"
fi

"${PYTHON_BIN}" -m pip install -r requirements.txt

if [ "${RUN_MIGRATIONS:-0}" = "1" ] && [ -f alembic.ini ]; then
  "${PYTHON_BIN}" -m alembic upgrade head
fi

if [ -f "${SERVICE_UNIT_SRC}" ]; then
  install -m 644 "${SERVICE_UNIT_SRC}" "${SERVICE_UNIT_DST}"
  systemctl daemon-reload
fi

if command -v systemctl >/dev/null 2>&1; then
  systemctl restart "${SERVICE_NAME}"
else
  echo "systemctl is unavailable; restart ${SERVICE_NAME} manually."
fi
