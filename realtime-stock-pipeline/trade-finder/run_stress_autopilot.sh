#!/usr/bin/env bash
# run_stress_autopilot.sh — keep stress-testing the trade finder 24/7.
#
# Each "run" is N_CYCLES (default 1000) back-to-back iterations of the
# trade finder. After each run, log a verdict (PASS/FAIL), and if the
# pass-rate < 95%, log a WARN. This is the "autopilot mode" the user
# asked for: every N minutes, the system re-tests itself and reports
# whether the AI loop is still healthy.
#
# Set RUN_EVERY_MIN=10 (or whatever) in the environment to control how
# often a fresh 1000-cycle test starts. The default of 10 min means the
# test re-runs ~144 times/day.

set -u
cd "$(dirname "$0")" || exit 1

N_CYCLES="${N_CYCLES:-1000}"
RUN_EVERY_MIN="${RUN_EVERY_MIN:-10}"
LOG_DIR="$(pwd)/logs"
STATE_DIR="$LOG_DIR/state"
PID_FILE="$LOG_DIR/stress.pid"
MERGED="$LOG_DIR/stress_autopilot.log"
mkdir -p "$LOG_DIR" "$STATE_DIR"

MAX_RESTARTS=5
WINDOW_SEC=1200
COOLDOWN=15

read_count() {
  local f="$STATE_DIR/restart.count"
  local t="$STATE_DIR/restart.ts"
  local now last
  now=$(date +%s)
  last=$(cat "$t" 2>/dev/null || echo 0)
  if [ $((now - last)) -gt "$WINDOW_SEC" ]; then
    echo 0 > "$f"; echo "$now" > "$t"
  fi
  cat "$f" 2>/dev/null || echo 0
}

bump_count() {
  local f="$STATE_DIR/restart.count"
  local t="$STATE_DIR/restart.ts"
  local now last
  now=$(date +%s)
  last=$(cat "$t" 2>/dev/null || echo 0)
  if [ $((now - last)) -gt "$WINDOW_SEC" ]; then
    echo 0 > "$f"
  fi
  local c
  c=$(cat "$f" 2>/dev/null || echo 0)
  c=$((c + 1))
  echo "$c" > "$f"
  echo "$now" > "$t"
}

cleanup() {
  echo "[$(date '+%H:%M:%S')] stress autopilot: caught signal, stopping" >> "$MERGED"
  [ -f "$PID_FILE" ] && { pid=$(cat "$PID_FILE"); kill "$pid" 2>/dev/null; rm -f "$PID_FILE"; }
  exit 0
}
trap cleanup INT TERM

echo "=== stress autopilot started $(date) ===" > "$MERGED"
echo "    n_cycles per run: $N_CYCLES" >> "$MERGED"
echo "    re-run every:     $RUN_EVERY_MIN min" >> "$MERGED"

cycle=0
while true; do
  rc=$(read_count)
  if [ "$rc" -ge "$MAX_RESTARTS" ]; then
    echo "[$(date '+%H:%M:%S')] hit $MAX_RESTARTS restarts — giving up" >> "$MERGED"
    exit 1
  fi
  cycle=$((cycle + 1))
  echo "" >> "$MERGED"
  echo "[$(date '+%H:%M:%S')] ==== RUN $cycle start (n=$N_CYCLES, restart=$rc) ====" >> "$MERGED"

  # Force N_CYCLES into the env so stress_test.py can pick it up
  N_CYCLES="$N_CYCLES" python3 stress_test.py >> "$MERGED" 2>&1 &
  PID=$!
  echo "$PID" > "$PID_FILE"
  wait "$PID" 2>/dev/null
  code=$?
  rm -f "$PID_FILE"

  bump_count
  echo "[$(date '+%H:%M:%S')] RUN $cycle done (exit=$code). Next run in ${RUN_EVERY_MIN}m." >> "$MERGED"

  # Quick verdict grep on the merged log
  last_verdict=$(grep -E "^  PASS|^  FAIL|^  WARN" "$MERGED" | tail -1)
  if [ -n "$last_verdict" ]; then
    echo "[$(date '+%H:%M:%S')] last verdict: $last_verdict" >> "$MERGED"
  fi

  sleep $((RUN_EVERY_MIN * 60))
done
