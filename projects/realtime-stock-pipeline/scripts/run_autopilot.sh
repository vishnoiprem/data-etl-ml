#!/usr/bin/env bash
# run_autopilot.sh — auto-restart the live signal dashboards.
#
# - Rule-based (script 7) on 15s refresh.
# - AI predictor (script 8) on 60s refresh, retrain every 3 polls.
# - Watchdog: if either dies, wait 10s and relaunch (max 5 restarts in
#   10 minutes before giving up).
# - Tail merged output to logs/autopilot.log so the user can `tail -f`.
#
# State is persisted to plain files (logs/state/<name>.count + .ts) so
# this script works under any POSIX shell (bash, zsh, dash).

set -u
cd "$(dirname "$0")/.." || exit 1

TICKERS="SOXL,SOXS,NVDA,AMD,INTC,MU,ARM,MSFT,AVGO,MRVL,AMAT,LRCX,QCOM,TQQQ,SQQQ,SPY,QQQ"
LOG_DIR="$(pwd)/logs"
STATE_DIR="$LOG_DIR/state"
PID_DIR="$LOG_DIR/pids"
mkdir -p "$LOG_DIR" "$STATE_DIR" "$PID_DIR"

RULE_LOG="$LOG_DIR/rule.log"
AI_LOG="$LOG_DIR/ai.log"
MERGED="$LOG_DIR/autopilot.log"

MAX_RESTARTS=5
WINDOW_SEC=600   # 10 minutes
COOLDOWN=10

# Read & reset the restart counter if we're outside the 10-min window.
read_count() {
  local key="$1"
  local count_file="$STATE_DIR/${key}.count"
  local ts_file="$STATE_DIR/${key}.ts"
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
  local key="$1"
  local count_file="$STATE_DIR/${key}.count"
  local ts_file="$STATE_DIR/${key}.ts"
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

run_loop() {
  local name="$1"
  local cmd="$2"
  local log="$3"
  local pidfile="$PID_DIR/${name}.pid"
  while true; do
    local rc
    rc=$(read_count "$name")
    if [ "$rc" -ge "$MAX_RESTARTS" ]; then
      echo "[$(date '+%H:%M:%S')] $name hit $MAX_RESTARTS restarts in ${WINDOW_SEC}s — giving up" >> "$MERGED"
      return 1
    fi
    echo "[$(date '+%H:%M:%S')] $name: starting (restart $rc)" >> "$MERGED"
    # shellcheck disable=SC2086
    python3 $cmd >> "$log" 2>&1 &
    local pid=$!
    echo "$pid" > "$pidfile"
    wait "$pid" 2>/dev/null
    local code=$?
    rm -f "$pidfile"
    bump_count "$name"
    echo "[$(date '+%H:%M:%S')] $name: exited code=$code, restarting in ${COOLDOWN}s" >> "$MERGED"
    sleep "$COOLDOWN"
  done
}

cleanup() {
  echo "[$(date '+%H:%M:%S')] autopilot: caught signal, stopping children" >> "$MERGED"
  for pf in "$PID_DIR"/*.pid; do
    [ -f "$pf" ] || continue
    pid=$(cat "$pf" 2>/dev/null) || continue
    [ -n "$pid" ] && kill "$pid" 2>/dev/null
    rm -f "$pf"
  done
  exit 0
}
trap cleanup INT TERM

echo "=== autopilot started $(date) ===" > "$MERGED"
echo "TICKERS=$TICKERS" >> "$MERGED"
echo "LOGS: $RULE_LOG  $AI_LOG" >> "$MERGED"

(
  run_loop "rule" "scripts/7_live_buy_signals.py --tickers $TICKERS --poll-seconds 15" "$RULE_LOG"
) &
RULE_WRAPPER_PID=$!

(
  run_loop "ai" "scripts/8_ai_predict_signals.py --tickers $TICKERS --poll-seconds 60 --retrain-every 3" "$AI_LOG"
) &
AI_WRAPPER_PID=$!

# Poll for any wrapper exit (portable across bash/zsh/dash)
while kill -0 "$RULE_WRAPPER_PID" 2>/dev/null && kill -0 "$AI_WRAPPER_PID" 2>/dev/null; do
  sleep 5
done
echo "[$(date '+%H:%M:%S')] autopilot: a wrapper exited, shutting down the other" >> "$MERGED"
kill "$RULE_WRAPPER_PID" "$AI_WRAPPER_PID" 2>/dev/null
wait 2>/dev/null
exit 0
