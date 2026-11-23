#!/usr/bin/env bash
# run.sh — thin wrapper over the canonical leads pipeline.
#
# Everything here calls projects/leads-pipeline/draft-cron/. The repo-root
# leads-pipeline/ directory is a stale untracked copy and is never touched.
#
#   ./run.sh doctor          check the environment (DB, deps, creds presence)
#   ./run.sh preview         dry run: show what would be queued and sent
#   ./run.sh discover        client prospects + more leads (no send)
#   ./run.sh status          pipeline state as JSON
#   ./run.sh report          daily + full reports
#   ./run.sh bounces         sync bounces from Gmail, update deny list
#   ./run.sh reply <query>   mark a lead as replied
#   ./run.sh send <mode> <n> SEND approved emails (mode: pitch_pod|apply_personal)
#
# The `send` subcommand is the only one that sends. Everything else is safe.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PIPE="$ROOT/projects/leads-pipeline/draft-cron"
SELF="$ROOT/projects/data-ai-outreach/run.sh"

if [[ ! -d "$PIPE" ]]; then
  echo "error: canonical pipeline not found at $PIPE" >&2
  exit 1
fi

cd "$PIPE"

if [[ -x ".venv/bin/python" ]]; then
  PY=".venv/bin/python"
else
  PY="python3"
fi

case "${1:-doctor}" in
  doctor)
    echo "pipeline:  $PIPE"
    echo "python:    $($PY -V 2>&1)"
    if "$PY" -c "import psycopg2" 2>/dev/null; then
      echo "psycopg2:  ok"
    else
      echo "psycopg2:  MISSING (make install)"
    fi
    if [[ -f .env ]]; then
      echo ".env:      present"
    else
      echo ".env:      MISSING (see SETUP_GMAIL_SMTP.md)"
    fi
    if nc -z "${AVILX_DB_HOST:-localhost}" "${AVILX_DB_PORT:-5433}" 2>/dev/null; then
      echo "postgres:  up on ${AVILX_DB_HOST:-localhost}:${AVILX_DB_PORT:-5433}"
    else
      echo "postgres:  DOWN on ${AVILX_DB_HOST:-localhost}:${AVILX_DB_PORT:-5433} — docker compose up -d"
      echo "           (cron_lock fails closed, so sends will refuse to run)"
    fi
    ;;
  preview)
    exec "$PY" autopilot.py --dry "${@:2}"
    ;;
  discover)
    exec "$PY" find_clients.py "${@:2}"
    ;;
  status)
    exec "$PY" dashboard.py --json "${@:2}"
    ;;
  report)
    "$PY" daily_report.py "${@:2}"
    exec "$PY" full_report.py
    ;;
  bounces)
    exec "$PY" check_bounces.py --since "${2:-14}"
    ;;
  reply)
    shift
    exec "$PY" bin/mark_reply.py "$@"
    ;;
  send)
    mode="${2:-pitch_pod}"
    count="${3:-1}"
    if [[ "${4:-}" != "SEND" ]]; then
      echo "refusing to send without confirmation." >&2
      echo "usage: $0 send <pitch_pod|apply_personal> <count> SEND" >&2
      echo "Drafts must be approved before this runs." >&2
      exit 2
    fi
    exec "$PY" autopilot.py --email --mode "$mode" --max-emails "$count"
    ;;
  *)
    sed -n '3,17p' "$SELF" | sed 's/^# \{0,1\}//'
    ;;
esac
