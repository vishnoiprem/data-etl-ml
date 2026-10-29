#!/usr/bin/env bash
# 3_register_flink_jobs.sh — submit every SQL file in flink/jobs/ to sql-client.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

JOBMANAGER="${FLINK_JOBMANAGER:-flink-jobmanager}"
JOBS_DIR="${JOBS_DIR:-flink/jobs}"

echo "==> Waiting for Flink JobManager ($JOBMANAGER) at http://localhost:8081/overview..."
for i in {1..60}; do
  if curl -sf http://localhost:8081/overview >/dev/null 2>&1; then
    echo "JobManager ready."; break
  fi
  sleep 2
  if (( i == 60 )); then
    echo "Timed out waiting for Flink JobManager"; exit 1
  fi
done

if [[ ! -d "$JOBS_DIR" ]]; then
  echo "WARNING: $JOBS_DIR does not exist — nothing to register."
  exit 0
fi

shopt -s nullglob
sql_files=( "$JOBS_DIR"/*.sql )
if (( ${#sql_files[@]} == 0 )); then
  echo "No SQL files found in $JOBS_DIR — nothing to register."
  exit 0
fi

IFS=$'\n' sql_files_sorted=( $(printf '%s\n' "${sql_files[@]}" | sort) )
unset IFS

for f in "${sql_files_sorted[@]}"; do
  name=$(basename "$f" .sql)
  echo "==> Submitting $name"
  # Copy the file into the container and execute via sql-client
  docker cp "$f" "$JOBMANAGER:/tmp/$(basename "$f")" >/dev/null
  timeout 60s docker exec -i "$JOBMANAGER" /opt/flink/bin/sql-client.sh -f "/tmp/$(basename "$f")" \
    || echo "WARNING: $name submission failed/timed-out (continuing)"
done

echo "==> Polling /jobs overview for ~30s..."
end=$(( SECONDS + 30 ))
while (( SECONDS < end )); do
  if curl -sf http://localhost:8081/jobs >/dev/null 2>&1; then
    break
  fi
  sleep 3
done

echo
echo "==> Running Flink jobs:"
curl -s http://localhost:8081/jobs | python3 -c "
import json, sys
try:
    d=json.load(sys.stdin)
    jobs=d.get('jobs',[])
    if not jobs:
        print('  (none yet — check Flink UI)')
    for j in jobs:
        print(f\"  - {j.get('id')} {j.get('status')} {j.get('name')}\")
except Exception as e:
    print('  could not parse /jobs:', e)
"

echo "Flink jobs registration done."
