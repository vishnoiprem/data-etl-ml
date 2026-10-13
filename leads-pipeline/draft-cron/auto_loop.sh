#!/bin/bash
# auto_loop.sh — runs autopilot up to N times (default 100), re-finds leads
# in between, never asks for confirmation. Auto mode = on.
#
# Usage:
#   ./auto_loop.sh                 # 100 iterations
#   ./auto_loop.sh 50              # 50 iterations
#   LOOP_MAX=10 ./auto_loop.sh     # 10 iterations via env
#   LOOP_SLEEP=60 ./auto_loop.sh   # 60s between iterations
#   REFINE_ONLY=1 ./auto_loop.sh   # no email sends (Gmail cooldown)
#   ./auto_loop.sh stop            # stop the running loop

set -eo pipefail
cd "$(dirname "$0")"
HERE="$(pwd)"

# Python interpreter — prefer the project venv, fall back to PATH.
PY="${AVILX_PY:-${HERE}/../.venv/bin/python}"
if [[ ! -x "$PY" ]]; then
    PY="$(command -v python3)"
fi

# Allow PY override from the environment.
PY="${AVILX_PY_OVERRIDE:-$PY}"

LOOP_MAX="${1:-${LOOP_MAX:-100}}"
LOOP_SLEEP="${LOOP_SLEEP:-90}"
LOG="${AVILX_LOOP_LOG:-/tmp/auto_loop.log}"
PIDFILE="${AVILX_LOOP_PIDFILE:-/tmp/auto_loop.pid}"
CHILDREN_DIR="${AVILX_LOOP_CHILDREN:-/tmp/auto_loop.children}"

mkdir -p "$CHILDREN_DIR"

# Track every child we spawn so `stop` only kills our descendants.
spawn() {
    "$@" &
    echo $! > "$CHILDREN_DIR/$$.$!"
    wait $!
    rm -f "$CHILDREN_DIR/$$.$!"
}

stop_loop() {
    if [[ -f "$PIDFILE" ]]; then
        pid=$(cat "$PIDFILE")
        kill "$pid" 2>/dev/null || true
        rm -f "$PIDFILE"
        echo "stopped loop PID $pid"
    fi
    # Kill only the children we tracked — not any interactive dev session.
    if [[ -d "$CHILDREN_DIR" ]]; then
        for f in "$CHILDREN_DIR"/*; do
            [[ -f "$f" ]] || continue
            cpid=$(cat "$f" 2>/dev/null)
            if [[ -n "$cpid" ]]; then
                kill "$cpid" 2>/dev/null || true
            fi
            rm -f "$f"
        done
        echo "killed tracked child processes"
    fi
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
trap 'rm -f "$PIDFILE"; stop_loop' EXIT INT TERM HUP

echo "=== AUTO LOOP STARTED $(date) — up to $LOOP_MAX iterations, ${LOOP_SLEEP}s sleep ===" | tee -a "$LOG"
echo "    PY=$PY" | tee -a "$LOG"

for i in $(seq 1 "$LOOP_MAX"); do
    echo "" | tee -a "$LOG"
    echo "[$i/$LOOP_MAX] === $(date) — run autopilot (email phase) ===" | tee -a "$LOG"

    # 1. Refresh leads in background (don't block email phase)
    if (( i % 5 == 1 )); then
        echo "[$i/$LOOP_MAX] refreshing lead list (job boards)..." | tee -a "$LOG"
        if ! spawn "$PY" "$HERE/find_more_leads.py" >> "$LOG" 2>&1; then
            echo "  (find_more_leads failed, continuing)" | tee -a "$LOG"
        fi
        echo "[$i/$LOOP_MAX] refreshing lead list (clients + AI-native)..." | tee -a "$LOG"
        if ! spawn "$PY" "$HERE/find_clients.py" >> "$LOG" 2>&1; then
            echo "  (find_clients failed, continuing)" | tee -a "$LOG"
        fi
    fi

    # 2. Sync bounces
    if ! "$PY" "$HERE/bin/loop_bounce_sync.py" 2>&1 | tee -a "$LOG"; then
        echo "  (bounce-sync error, continuing)" | tee -a "$LOG"
    fi

    # 3. Run autopilot — email phase, up to 10 emails
    # Skip if REFINE_ONLY=1 (Gmail cooldown, etc.)
    if [[ "${REFINE_ONLY:-0}" == "1" ]]; then
        echo "[$i/$LOOP_MAX] REFINE_ONLY=1 → skipping email sends" | tee -a "$LOG"
    else
        if ! "$PY" "$HERE/autopilot.py" --email --max-emails 10 --no-bounce-sync >> "$LOG" 2>&1; then
            echo "  (autopilot exited with non-zero, continuing)" | tee -a "$LOG"
        fi
    fi

    # 3b. Refine pipeline — enriches pending leads (resume + cover + better email)
    if ! "$PY" "$HERE/refine_pipeline.py" --enrich-only >> "$LOG" 2>&1; then
        echo "  (refine_pipeline exited with non-zero, continuing)" | tee -a "$LOG"
    fi

    # 3c. Backfill emails — derive careers@X for any pending leads still missing an email
    if ! "$PY" "$HERE/backfill_emails.py" >> "$LOG" 2>&1; then
        echo "  (backfill_emails exited with non-zero, continuing)" | tee -a "$LOG"
    fi

    # 4. Report status — single Python invocation, four counts
    sleep 2
    if ! counts="$("$PY" "$HERE/bin/loop_status.py" 2>/dev/null)"; then
        counts="? ? ? ?"
    fi
    read -r pending_total pending_email pending_enriched bounce_pct <<< "$counts"
    echo "[$i/$LOOP_MAX] pending=$pending_total  w/email=$pending_email  enriched=$pending_enriched  bounce_rate=${bounce_pct}%" | tee -a "$LOG"

    # 4b. Print full report every 10 iterations
    if (( i % 10 == 0 )); then
        echo "" | tee -a "$LOG"
        "$PY" "$HERE/full_report.py" 2>&1 | head -50 | tee -a "$LOG" || true
    fi

    if [[ "$pending_email" == "0" ]]; then
        echo "[$i/$LOOP_MAX] queue empty, will refresh in next iteration" | tee -a "$LOG"
    fi

    sleep "$LOOP_SLEEP"
done

echo "=== AUTO LOOP FINISHED $(date) ===" | tee -a "$LOG"
