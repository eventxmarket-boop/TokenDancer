#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

"${ROOT_DIR}/deploy/build_frontend.sh"
"${ROOT_DIR}/deploy/deploy_backend.sh"
