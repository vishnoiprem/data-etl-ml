#!/usr/bin/env bash
# 4_start_producer.sh — restart the producer and tail logs briefly.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker not found"; exit 1
fi

echo "==> docker compose restart stock-producer"
docker compose restart stock-producer

echo "==> Tailing logs for 10 seconds..."
timeout 10s docker compose logs -f stock-producer || true

echo
echo "Producer running. Tail logs with: docker compose logs -f stock-producer"
