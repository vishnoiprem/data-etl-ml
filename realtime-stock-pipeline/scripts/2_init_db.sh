#!/usr/bin/env bash
# 2_init_db.sh — wait for TimescaleDB and apply views SQL.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

CONTAINER="${TIMESCALEDB_CONTAINER:-timescaledb}"
PG_USER="${POSTGRES_USER:-stocks}"
PG_DB="${POSTGRES_DB:-stocks}"
VIEWS_FILE="${VIEWS_FILE:-db/02_views.sql}"

echo "==> Waiting for TimescaleDB ($CONTAINER) to accept connections..."
for i in {1..60}; do
  if docker exec "$CONTAINER" pg_isready -U "$PG_USER" -d "$PG_DB" >/dev/null 2>&1; then
    echo "TimescaleDB ready."
    break
  fi
  sleep 2
  if (( i == 60 )); then
    echo "Timed out waiting for TimescaleDB"; exit 1
  fi
done

if [[ ! -f "$VIEWS_FILE" ]]; then
  echo "WARNING: $VIEWS_FILE not found — skipping. (Other agent may not have created it yet.)"
  echo "Database initialized (no-op)."
  exit 0
fi

echo "==> Applying $VIEWS_FILE"
docker exec -i "$CONTAINER" psql -U "$PG_USER" -d "$PG_DB" -v ON_ERROR_STOP=0 < "$VIEWS_FILE"

# Sanity check that the TimescaleDB extension is loaded (init.sql already did this,
# but if a user runs against a pre-existing volume we want to confirm).
echo "==> Verifying TimescaleDB extension..."
docker exec "$CONTAINER" psql -U "$PG_USER" -d "$PG_DB" -tAc \
  "SELECT extname FROM pg_extension WHERE extname='timescaledb';"

echo "Database initialized."
