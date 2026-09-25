#!/usr/bin/env bash
# 1_start_containers.sh — pull images, start the stack, wait for healthchecks.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker not found on PATH"; exit 1
fi

if [[ "${SKIP_PULL:-0}" = "1" ]]; then
  echo "==> SKIP_PULL=1 — skipping 'docker compose pull'"
else
  echo "==> docker compose pull"
  docker compose pull || echo "pull failed (continuing with local images)"
fi

echo "==> docker compose up -d"
docker compose up -d

echo "==> Waiting for services to become healthy (timeout 180s)..."
REQUIRED=(kafka timescaledb flink-jobmanager flink-taskmanager grafana stock-producer)
TIMEOUT=180
START=$SECONDS

while (( SECONDS - START < TIMEOUT )); do
  all_ok=1
  for svc in "${REQUIRED[@]}"; do
    state=$(docker inspect --format '{{.State.Status}}' "$svc" 2>/dev/null || echo "missing")
    health=$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$svc" 2>/dev/null || echo "missing")
    if [[ "$state" != "running" ]]; then
      all_ok=0
      break
    fi
    # Treat "none" (no healthcheck defined) as ok if running; otherwise require healthy.
    if [[ "$health" != "healthy" && "$health" != "none" ]]; then
      all_ok=0
      break
    fi
  done
  if (( all_ok )); then break; fi
  sleep 3
done

echo
echo "==> Container status"
docker compose ps --format 'table {{.Name}}\t{{.State}}\t{{.Status}}\t{{.Ports}}'

echo
cat <<EOF
URLs:
  Grafana        http://localhost:3000   (admin / admin)
  Flink UI       http://localhost:8081
  TimescaleDB    localhost:5432          (user/pass from .env)
  Kafka          localhost:9092
EOF
