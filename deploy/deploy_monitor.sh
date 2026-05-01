#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_NAME="${SERVICE_NAME:-tokendancer-monitor.service}"
SERVICE_UNIT_SRC="${ROOT_DIR}/deploy/${SERVICE_NAME}"
SERVICE_UNIT_DST="/etc/systemd/system/${SERVICE_NAME}"

cd "${ROOT_DIR}"

if [ "$(id -u)" -eq 0 ]; then
  npx playwright install-deps chromium
else
  sudo npx playwright install-deps chromium
fi

if [ ! -d node_modules ]; then
  if [ -f package-lock.json ]; then
    npm ci
  else
    npm install
  fi
fi

if [ "$(id -u)" -eq 0 ]; then
  runuser -u ubuntu -- bash -lc "cd '${ROOT_DIR}' && npx playwright install chromium"
else
  sudo -u ubuntu -H bash -lc "cd '${ROOT_DIR}' && npx playwright install chromium"
fi

if [ -f "${SERVICE_UNIT_SRC}" ]; then
  install -m 644 "${SERVICE_UNIT_SRC}" "${SERVICE_UNIT_DST}"
  systemctl daemon-reload
fi

if command -v systemctl >/dev/null 2>&1; then
  systemctl enable "${SERVICE_NAME}"
  systemctl restart "${SERVICE_NAME}"
else
  echo "systemctl is unavailable; restart ${SERVICE_NAME} manually."
fi
