#!/bin/bash
# auto_loop.sh — runs autopilot up to N times (default 100), re-finds leads
# in between, never asks for confirmation. Auto mode = on.
#
# Usage:
#   ./auto_loop.sh                 # 100 iterations
#   ./auto_loop.sh 50              # 50 iterations
#   LOOP_MAX=10 ./auto_loop.sh     # 10 iterations via env
#   LOOP_SLEEP=60 ./auto_loop.sh   # 60s between iterations
#   ./auto_loop.sh stop            # stop the running loop

set -e
cd "$(dirname "$0")"
HERE="$(pwd)"
LOOP_MAX="${1:-${LOOP_MAX:-100}}"
LOOP_SLEEP="${LOOP_SLEEP:-90}"
LOG="/tmp/auto_loop.log"
PIDFILE="/tmp/auto_loop.pid"

stop_loop() {
    if [[ -f "$PIDFILE" ]]; then
        pid=$(cat "$PIDFILE")
        kill "$pid" 2>/dev/null || true
        rm -f "$PIDFILE"
        echo "stopped loop PID $pid"
    fi
    # Also kill any child autopilot processes
    pkill -f "autopilot.py" 2>/dev/null || true
    echo "killed any child autopilot processes"
}

if [[ "${1:-}" == "stop" ]]; then
    stop_loop
    exit 0
fi

# Don't start if already running
if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    echo "auto_loop already running (PID $(cat "$PIDFILE")) — see $LOG"
    exit 0
fi

echo $$ > "$PIDFILE"
trap 'rm -f "$PIDFILE"' EXIT

echo "=== AUTO LOOP STARTED $(date) — up to $LOOP_MAX iterations, ${LOOP_SLEEP}s sleep ===" | tee -a "$LOG"

for i in $(seq 1 "$LOOP_MAX"); do
    echo "" | tee -a "$LOG"
    echo "[$i/$LOOP_MAX] === $(date) — run autopilot (email phase) ===" | tee -a "$LOG"

    # 1. Refresh leads in background (don't block email phase)
    if (( i % 5 == 1 )); then
        echo "[$i/$LOOP_MAX] refreshing lead list..." | tee -a "$LOG"
        /Users/vishnoiprem/PycharmProjects/data-etl-ml/.venv/bin/python find_more_leads.py >> "$LOG" 2>&1 || echo "  (lead refresh failed, continuing)"
    fi

    # 2. Sync bounces
    /Users/vishnoiprem/PycharmProjects/data-etl-ml/.venv/bin/python -c "
import sys
sys.path.insert(0, '$HERE')
try:
    from check_bounces import scan_bounces, mark_bounced
    bm, _ = scan_bounces(since_days=7)
    if bm:
        mark_bounced(bm, dry=False)
        print(f'  marked {len(bm)} new bounces')
    else:
        print('  no new bounces')
except Exception as e:
    print(f'  bounce-sync error: {e}')
" 2>&1 | tee -a "$LOG"

    # 3. Run autopilot — email phase, up to 10 emails
    /Users/vishnoiprem/PycharmProjects/data-etl-ml/.venv/bin/python autopilot.py --email --max-emails 10 --no-bounce-sync >> "$LOG" 2>&1 || {
        echo "  (autopilot exited with non-zero, continuing)" | tee -a "$LOG"
    }

    # 4. Report status
    pending=$(/Users/vishnoiprem/PycharmProjects/data-etl-ml/.venv/bin/python -c "
import sys
sys.path.insert(0, '$HERE')
from db.lead_store import get_cursor
with get_cursor() as cur:
    cur.execute(\"SELECT COUNT(*) FROM leads WHERE contact_email IS NOT NULL AND contact_email != '' AND status NOT IN ('sent_email','bounced','replied','unsubscribed','failed')\")
    print(cur.fetchone()[0])
" 2>/dev/null || echo "?")
    echo "[$i/$LOOP_MAX] pending w/ email after run: $pending" | tee -a "$LOG"

    if [[ "$pending" == "0" ]]; then
        echo "[$i/$LOOP_MAX] queue empty, will refresh in next iteration" | tee -a "$LOG"
    fi

    sleep "$LOOP_SLEEP"
done

echo "=== AUTO LOOP FINISHED $(date) ===" | tee -a "$LOG"
