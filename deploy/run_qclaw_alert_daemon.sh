#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NODE_BIN="$(command -v node || true)"

if [ -z "${NODE_BIN}" ]; then
  echo "node is not available on PATH" >&2
  exit 1
fi

cd "${ROOT_DIR}"
exec "${NODE_BIN}" "${ROOT_DIR}/calendar_alert_daemon.js"
