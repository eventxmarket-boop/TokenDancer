#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPLOY_DIR="${ROOT_DIR}/deploy"
SYSTEMD_DIR="/etc/systemd/system"
BASE_DIR_DEFAULT="/home/ubuntu/.qclaw/workspace-agent-be2ecf0c"
BASE_DIR="${Z_CHAIN_BASE_DIR:-${BASE_DIR_DEFAULT}}"
TARGET_IDS=("1" "2" "3" "5" "6" "7")

if [[ "${INCLUDE_CHAIN_4:-false}" == "true" ]]; then
  TARGET_IDS=("1" "2" "3" "4" "5" "6" "7")
fi

if [[ ! -f "${ROOT_DIR}/.env" ]]; then
  echo "[install_z_chain_instances] missing .env in ${ROOT_DIR}" >&2
  exit 1
fi

load_target_value() {
  local key="$1"
  local value
  value="$(grep -E "^${key}=" "${ROOT_DIR}/.env" | tail -n 1 | cut -d= -f2- || true)"
  value="${value%$'\r'}"
  printf '%s' "${value}"
}

require_sudo() {
  if [[ "${EUID}" -eq 0 ]]; then
    return 0
  fi

  if ! sudo -n true 2>/dev/null; then
    sudo -v
  fi
}

require_sudo

mkdir -p "${DEPLOY_DIR}"

for target_id in "${TARGET_IDS[@]}"; do
  target_name="$(load_target_value "TARGET_${target_id}_NAME")"
  target_url="$(load_target_value "TARGET_${target_id}_URL")"

  if [[ -z "${target_name}" || -z "${target_url}" ]]; then
    echo "[install_z_chain_instances] skip ${target_id}: missing target config" >&2
    continue
  fi

  instance_id="mescladis-${target_id}"
  profile_csv_name="z_chain_profiles_${target_id}.csv"
  profile_csv_path="${ROOT_DIR}/${profile_csv_name}"
  env_file="${DEPLOY_DIR}/tokendancer-z-chain-${target_id}.env"
  monitor_unit="${SYSTEMD_DIR}/tokendancer-z-chain-${target_id}.service"
  executor_unit="${SYSTEMD_DIR}/tokendancer-z-chain-${target_id}-executor.service"

  if [[ ! -f "${profile_csv_path}" && -f "${ROOT_DIR}/z_chain_profiles_template.csv" ]]; then
    cp "${ROOT_DIR}/z_chain_profiles_template.csv" "${profile_csv_path}"
  fi

  cat >"${env_file}" <<EOF
Z_CHAIN_INSTANCE_ID=${instance_id}
Z_CHAIN_TARGET_NAME=${target_name}
Z_CHAIN_TARGET_URL=${target_url}
Z_CHAIN_PROFILES_CSV_PATH=${profile_csv_name}
Z_CHAIN_BASE_DIR=${BASE_DIR}
EOF

  sudo tee "${monitor_unit}" >/dev/null <<EOF
[Unit]
Description=Tokendancer Z Chain ${target_id} Autofill Monitor
After=network.target

[Service]
User=ubuntu
WorkingDirectory=${ROOT_DIR}
EnvironmentFile=${env_file}
Environment=NODE_ENV=production
Environment=PLAYWRIGHT_BROWSERS_PATH=/home/ubuntu/.cache/ms-playwright
ExecStart=${ROOT_DIR}/deploy/run_z_chain.sh
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

  sudo tee "${executor_unit}" >/dev/null <<EOF
[Unit]
Description=Tokendancer Z Chain ${target_id} Executor
After=network.target

[Service]
User=ubuntu
WorkingDirectory=${ROOT_DIR}
EnvironmentFile=${env_file}
Environment=NODE_ENV=production
Environment=PLAYWRIGHT_BROWSERS_PATH=/home/ubuntu/.cache/ms-playwright
ExecStart=${ROOT_DIR}/deploy/run_z_chain_executor.sh
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

  echo "[install_z_chain_instances] installed ${monitor_unit} and ${executor_unit}"
done

sudo systemctl daemon-reload
for target_id in "${TARGET_IDS[@]}"; do
  sudo systemctl enable --now "tokendancer-z-chain-${target_id}.service" "tokendancer-z-chain-${target_id}-executor.service" || true
done

echo "[install_z_chain_instances] completed"
