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

CHAIN_INSTANCE_ID="${Z_CHAIN_INSTANCE_ID:-${Z_CHAIN_TARGET_NAME:-z-chain}}"
CHAIN_INSTANCE_ID="$(printf '%s' "${CHAIN_INSTANCE_ID}" | tr '[:upper:]' '[:lower:]' | sed -E 's#[ /]+#-#g; s#[^a-z0-9_-]+##g; s#-+#-#g; s#^-+|-+$##g')"
CHAIN_INSTANCE_ID="${CHAIN_INSTANCE_ID:-z-chain}"
CHAIN_BASE_DIR="${Z_CHAIN_BASE_DIR:-${HOME:-/Users/chanzi}/.qclaw/workspace-agent-be2ecf0c}"

export Z_CHAIN_INSTANCE_ID="${CHAIN_INSTANCE_ID}"
export Z_CHAIN_ALERT_FILE_PATH="${Z_CHAIN_ALERT_FILE_PATH:-${CHAIN_BASE_DIR}/${CHAIN_INSTANCE_ID}_alert.txt}"
export Z_CHAIN_SIGNAL_FILE_PATH="${Z_CHAIN_SIGNAL_FILE_PATH:-${Z_CHAIN_ALERT_FILE_PATH}}"
export Z_CHAIN_STATE_FILE="${Z_CHAIN_STATE_FILE:-${CHAIN_BASE_DIR}/${CHAIN_INSTANCE_ID}_bridge_state.json}"
export Z_CHAIN_HEARTBEAT_FILE_PATH="${Z_CHAIN_HEARTBEAT_FILE_PATH:-${CHAIN_BASE_DIR}/${CHAIN_INSTANCE_ID}_bridge_heartbeat.json}"
export Z_CHAIN_EXECUTION_ONLY="${Z_CHAIN_EXECUTION_ONLY:-true}"
export Z_CHAIN_TELEGRAM_DISABLED="${Z_CHAIN_TELEGRAM_DISABLED:-true}"
export Z_CHAIN_SUPPRESS_STATUS_EVENTS="${Z_CHAIN_SUPPRESS_STATUS_EVENTS:-false}"

trap 'echo "[z-chain-wrapper] stop signal received"; exit 0' INT TERM

while true; do
  set +e
  "${NODE_BIN}" --input-type=module -e "await import('./z_chain_monitor.js')"
  exit_code=$?
  set -e
  echo "[z-chain-wrapper] z_chain_monitor.js exited with ${exit_code}; restarting in 5s" >&2
  sleep 5
done
