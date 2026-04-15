#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="${ROOT_DIR}/frontend"
DEPLOY_DIR="${DEPLOY_DIR:-/var/www/tokendancer/persona}"

cd "${FRONTEND_DIR}"

if [ ! -d node_modules ]; then
  if [ -f package-lock.json ]; then
    npm ci
  else
    npm install
  fi
fi

npm run build

mkdir -p "${DEPLOY_DIR}"
cp -R dist/. "${DEPLOY_DIR}/"
