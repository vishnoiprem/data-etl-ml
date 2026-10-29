#!/usr/bin/env bash
# run_autopilot.sh — keep the trade-finder running 24/7.
#
# Re-runs find_opportunities.py every --interval-min minutes. If it
# dies, restarts up to MAX_RESTARTS times per WINDOW_SEC before giving
# up. All output goes to logs/. Stale emails older than 7 days are
# cleaned up on each cycle so the reports/ dir doesn't bloat.

set -u
cd "$(dirname "$0")" || exit 1

INTERVAL_MIN="${INTERVAL_MIN:-5}"   # 5 min default — fast enough to demo the loop
LOG_DIR="$(pwd)/logs"
STATE_DIR="$LOG_DIR/state"
PID_FILE="$LOG_DIR/trade-finder.pid"
MERGED="$LOG_DIR/autopilot.log"
mkdir -p "$LOG_DIR" "$STATE_DIR"

MAX_RESTARTS=5
WINDOW_SEC=600
COOLDOWN=10

read_count() {
  local count_file="$STATE_DIR/restart.count"
  local ts_file="$STATE_DIR/restart.ts"
  local now last
  now=$(date +%s)
  last=$(cat "$ts_file" 2>/dev/null || echo 0)
  if [ $((now - last)) -gt "$WINDOW_SEC" ]; then
    echo 0 > "$count_file"
    echo "$now" > "$ts_file"
  fi
  cat "$count_file" 2>/dev/null || echo 0
}

bump_count() {
  local count_file="$STATE_DIR/restart.count"
  local ts_file="$STATE_DIR/restart.ts"
  local now last
  now=$(date +%s)
  last=$(cat "$ts_file" 2>/dev/null || echo 0)
  if [ $((now - last)) -gt "$WINDOW_SEC" ]; then
    echo 0 > "$count_file"
  fi
  local c
  c=$(cat "$count_file" 2>/dev/null || echo 0)
  c=$((c + 1))
  echo "$c" > "$count_file"
  echo "$now" > "$ts_file"
}

cleanup_old() {
  # Delete email drafts older than 7 days
  find reports/ -name "email_*.txt" -mtime +7 -delete 2>/dev/null || true
  # Keep the most recent 14 markdown reports
  ls -1t reports/*.md 2>/dev/null | tail -n +15 | xargs -r rm --
}

cleanup() {
  echo "[$(date '+%H:%M:%S')] autopilot: caught signal, stopping" >> "$MERGED"
  if [ -f "$PID_FILE" ]; then
    pid=$(cat "$PID_FILE" 2>/dev/null) || true
    [ -n "$pid" ] && kill "$pid" 2>/dev/null
    rm -f "$PID_FILE"
  fi
  exit 0
}
trap cleanup INT TERM

echo "=== trade-finder autopilot started $(date) ===" > "$MERGED"
echo "    interval: ${INTERVAL_MIN} min" >> "$MERGED"
echo "    log:      $MERGED" >> "$MERGED"

while true; do
  rc=$(read_count)
  if [ "$rc" -ge "$MAX_RESTARTS" ]; then
    echo "[$(date '+%H:%M:%S')] hit $MAX_RESTARTS restarts in ${WINDOW_SEC}s — giving up" >> "$MERGED"
    exit 1
  fi

  echo "[$(date '+%H:%M:%S')] cycle start (restart $rc)" >> "$MERGED"
  python3 find_opportunities.py --loop --interval-min "$INTERVAL_MIN" --quiet >> "$MERGED" 2>&1 &
  PID=$!
  echo "$PID" > "$PID_FILE"
  echo "[$(date '+%H:%M:%S')] pid=$PID" >> "$MERGED"

  wait "$PID" 2>/dev/null
  code=$?
  rm -f "$PID_FILE"
  bump_count
  echo "[$(date '+%H:%M:%S')] cycle exited code=$code, restarting in ${COOLDOWN}s" >> "$MERGED"

  cleanup_old
  sleep "$COOLDOWN"
done
