#!/usr/bin/env bash
# =================================================================
# run_autopilot.sh  --  watchdog that re-runs the 1000-cycle review
# =================================================================
#
# Behavior:
#   - Runs every 30 min (configurable via INTERVAL_SEC)
#   - On crash: restart up to 5 times per 10 min
#   - Logs to autopilot/logs/  (rotated: keeps 7 days)
#   - Writes latest.json to ../results/ every run
#   - Appends results/1000_cycle_review_<ts>.md every run
#
# Usage:
#   bash autopilot/run_autopilot.sh           # foreground
#   nohup bash autopilot/run_autopilot.sh &   # background, survives logout
#   pkill -f run_autopilot.sh                 # stop

set -u
# We intentionally do NOT use `set -e` -- we want to log errors
# and try again, not abort the whole loop.

# ----- CONFIG --------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COURSE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
INTERVAL_SEC="${INTERVAL_SEC:-1800}"   # 30 min default
N_CYCLES="${N_CYCLES:-1000}"
SEED="${SEED:-42}"
MAX_RESTARTS="${MAX_RESTARTS:-5}"
WINDOW_SEC="${WINDOW_SEC:-600}"        # 10 min
LOG_DIR="$SCRIPT_DIR/logs"
STATE_DIR="$LOG_DIR/state"
PYTHONUNBUFFERED=1
export PYTHONUNBUFFERED

mkdir -p "$LOG_DIR" "$STATE_DIR"

# ----- HELPERS -------------------------------------------------------
log() { echo "[$(date '+%Y-%m-%dT%H:%M:%S%z')] $*" | tee -a "$LOG_DIR/autopilot.log"; }

ts_now() { date '+%Y-%m-%dT%H-%M-%SZ'; }

count_restarts_in_window() {
    local name="$1"
    local now; now=$(date +%s)
    local cutoff=$((now - WINDOW_SEC))
    local count_file="$STATE_DIR/${name}.count"
    local ts_file="$STATE_DIR/${name}.ts"
    # Read existing timestamps (one per line), prune older than window,
    # count what's left.
    : > "$count_file.tmp"
    if [[ -f "$ts_file" ]]; then
        while read -r t; do
            [[ -z "$t" ]] && continue
            if (( t > cutoff )); then
                echo "$t" >> "$count_file.tmp"
            fi
        done < "$ts_file"
    fi
    mv "$count_file.tmp" "$ts_file"
    wc -l < "$ts_file" | tr -d ' '
}

record_restart() {
    local name="$1"
    local ts_file="$STATE_DIR/${name}.ts"
    date +%s >> "$ts_file"
}

reset_restarts() {
    local name="$1"
    rm -f "$STATE_DIR/${name}.ts" "$STATE_DIR/${name}.count"
}

# ----- ONE ITERATION -------------------------------------------------
run_once() {
    local iter_ts; iter_ts=$(ts_now)
    local iter_log="$LOG_DIR/iter_${iter_ts}.log"
    log "iter=$iter_ts  n=$N_CYCLES  seed=$SEED  -- starting"

    if ( cd "$COURSE_DIR" && python3 code/run_1000_cycles.py --n "$N_CYCLES" --seed "$SEED" ) > "$iter_log" 2>&1; then
        local pct_pos; pct_pos=$(python3 -c "import json; print(json.load(open('$COURSE_DIR/results/latest.json'))['pct_positive'])" 2>/dev/null || echo "n/a")
        local median; median=$(python3 -c "import json; print(json.load(open('$COURSE_DIR/results/latest.json'))['median_roi'])" 2>/dev/null || echo "n/a")
        log "iter=$iter_ts  OK  pct_positive=$pct_pos  median=\$${median}/mo  log=$iter_log"
        return 0
    else
        local rc=$?
        log "iter=$iter_ts  FAIL (rc=$rc)  log=$iter_log"
        return $rc
    fi
}

# ----- LOG ROTATION --------------------------------------------------
prune_old_logs() {
    local max_age_days="${MAX_LOG_AGE_DAYS:-7}"
    find "$LOG_DIR" -type f -mtime +"$max_age_days" -name 'iter_*.log' -delete 2>/dev/null || true
    find "$LOG_DIR" -type f -mtime +"$max_age_days" -name 'autopilot.log.*' -delete 2>/dev/null || true
}

# ----- MAIN LOOP -----------------------------------------------------
log "=== autopilot starting ===  interval=${INTERVAL_SEC}s  n=$N_CYCLES  seed=$SEED  max_restarts=$MAX_RESTARTS / ${WINDOW_SEC}s"
reset_restarts "autopilot"

while true; do
    # Count restarts in window
    restarts="$(count_restarts_in_window autopilot)"
    if (( restarts >= MAX_RESTARTS )); then
        log "ABORT: $restarts restarts in last ${WINDOW_SEC}s (>= $MAX_RESTARTS).  Giving up.  Fix the underlying error then restart."
        exit 1
    fi

    # Run one iteration
    if run_once; then
        # Success -- reset restart counter (we treat each run as a new opportunity)
        reset_restarts "autopilot"
    else
        record_restart "autopilot"
        log "restart $((restarts+1))/$MAX_RESTARTS in last ${WINDOW_SEC}s"
        # Brief backoff before retry
        sleep 5
        continue  # don't sleep INTERVAL_SEC on failure -- retry fast
    fi

    # Prune + sleep
    prune_old_logs
    sleep "$INTERVAL_SEC"
done
