#!/usr/bin/env bash
# stop_all.sh — stop the stack but keep volumes (data preserved).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> docker compose down (volumes preserved)"
docker compose down

echo
echo "Stopped. Volumes are intact — restart with: bash scripts/1_start_containers.sh"
