#!/bin/bash
# run_12h_cycle.sh — Drive autopilot.py for 12 hours with mixed pod/solo sends.
#
# Cadence: every ~15min, alternate between pod and solo batches.
# Per-batch: 2-4 emails to keep under per-send throttling and avoid SMTP spikes.
# Total budget: 60-80 emails over 12h (well under Gmail 500/day cap).
#
# Usage: nohup ./run_12h_cycle.sh > /tmp/cycle_12h.log 2>&1 &
#
# Stop early:  pkill -f run_12h_cycle.sh
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-python3}"
LOG="/tmp/cycle_12h.log"

# 12h = 720 minutes. With 15min sleeps we get ~48 cycles.
# 2-4 emails per cycle × 48 cycles ≈ 96-192. Cap max_emails=2 to stay safe.
HOURS=12
SLEEP_MIN=15
PER_BATCH=2

END_TS=$(( $(date +%s) + HOURS * 3600 ))
CYCLE=0

echo "=== 12h send cycle started $(date) — ends ~$(date -r $END_TS 2>/dev/null || date) ===" | tee -a "$LOG"
echo "    cadence: every ${SLEEP_MIN}min, $PER_BATCH emails per batch" | tee -a "$LOG"
echo "    modes:   even cycles = pitch_pod (Avilx), odd = apply_personal (Prem)" | tee -a "$LOG"

while [[ $(date +%s) -lt $END_TS ]]; do
    CYCLE=$((CYCLE + 1))
    # Alternate: even cycles = pitch_pod, odd = apply_personal. Keeps both
    # queues draining so neither mode starves while the other dominates.
    if (( CYCLE % 2 == 0 )); then
        MODE="pitch_pod"
    else
        MODE="apply_personal"
    fi
    echo "" | tee -a "$LOG"
    echo "[cycle $CYCLE / ~$((HOURS * 60 / SLEEP_MIN))] $(date) — mode=$MODE, batch=$PER_BATCH" | tee -a "$LOG"
    if ! "$PY" "$HERE/autopilot.py" --email --mode "$MODE" --max-emails "$PER_BATCH" --no-bounce-sync 2>&1 | tee -a "$LOG"; then
        echo "  (autopilot failed or lock held, continuing)" | tee -a "$LOG"
    fi
    sleep "${SLEEP_MIN}m"
done

echo "" | tee -a "$LOG"
echo "=== 12h cycle complete $(date) — $CYCLE cycles, ~$((CYCLE * PER_BATCH)) emails ===" | tee -a "$LOG"
