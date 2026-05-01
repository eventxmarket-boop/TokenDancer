#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:${PATH:-}"
NODE_BIN="$(command -v node || true)"
unset XPC_SERVICE_NAME

if [ -z "${NODE_BIN}" ]; then
  echo "node is not available on PATH" >&2
  exit 1
fi

cd "${ROOT_DIR}"

trap 'echo "[monitor-wrapper] stop signal received"; exit 0' INT TERM

while true; do
  set +e
  "${NODE_BIN}" --input-type=module -e "await import('./monitor.js')"
  exit_code=$?
  set -e
  echo "[monitor-wrapper] monitor.js exited with ${exit_code}; restarting in 5s" >&2
  sleep 5
done
