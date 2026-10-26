# Autopilot — World 1% Watchdog

The autopilot re-runs the 1000-cycle ROI review forever and survives crashes. Every 30 min (configurable) it:
1. Runs `code/run_1000_cycles.py --n 1000 --seed 42`
2. Writes a new `results/1000_cycle_review_<ts>.md`
3. Overwrites `results/latest.json`
4. Logs to `autopilot/logs/`
5. Prunes logs older than 7 days

If the runner crashes, it restarts. If it crashes 5 times in 10 min, it gives up (so a hung process doesn't spin).

## Quick start

```bash
# Foreground (Ctrl-C to stop)
bash autopilot/run_autopilot.sh

# Background, survives logout
nohup bash autopilot/run_autopilot.sh > autopilot/logs/nohup.log 2>&1 &

# Stop
pkill -f run_autopilot.sh
```

## Config (env vars)

| Var | Default | What it does |
|---|---|---|
| `INTERVAL_SEC` | 1800 (30 min) | Seconds between runs |
| `N_CYCLES` | 1000 | Cycles per run |
| `SEED` | 42 | RNG seed (for reproducibility) |
| `MAX_RESTARTS` | 5 | Restart limit |
| `WINDOW_SEC` | 600 (10 min) | Window for restart counting |
| `MAX_LOG_AGE_DAYS` | 7 | Log retention |

Example — run every 5 min, 5000 cycles, custom seed:
```bash
INTERVAL_SEC=300 N_CYCLES=5000 SEED=2024 bash autopilot/run_autopilot.sh
```

## Where to look

| What | Where |
|---|---|
| Latest run summary (machine) | `../results/latest.json` |
| Latest run summary (human) | `../results/1000_cycle_review_*.md` (newest) |
| Per-iteration log | `autopilot/logs/iter_<ts>.log` |
| Watchdog events | `autopilot/logs/autopilot.log` |
| State (restart count) | `autopilot/logs/state/autopilot.ts` |

## How to know it's healthy

```bash
# One-liner: latest P50 ROI
cat ../results/latest.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'P50=\${d[\"median_roi\"]:+.0f}/mo  P05=\${d[\"p05_roi\"]:+.0f}/mo  %pos={d[\"pct_positive\"]:.1%}  ({d[\"ts\"]})')"
```

## Why this is "world 1%"

1. **Zero manual intervention.** Runs forever until you kill it.
2. **Every run is comparable.** Same seed, same inputs, same script -> diff `latest.json` over time to spot regression.
3. **Survives crashes.** State-file restart counting (portable across `/bin/zsh` and `/bin/bash`).
4. **Honest reporting.** Exits 0 on PASS, 1 on FAIL. Wire to PagerDuty / Slack / a cron monitor and you have CI for ROI.
5. **Reproducible.** 1000 cycles at 285K/s = 4 ms. You can re-run 100x and the P50 won't move.

## When NOT to use this

- If you change the input ranges (e.g. for a new SMB vertical), update `RANGES` in `code/agent_roi.py` and commit. Don't let the autopilot drift on stale assumptions.
- If you change the formula, also change the 4 use case criteria in `lessons/01-roi-formula.py`. The notebook and the autopilot will keep running with the new numbers — but the lesson doc will lie.
- If `pct_positive` drops below 90%, the formula is no longer robust under the current ranges. Stop the autopilot, re-fit, restart.

## Smoke test (one iteration, then stop)

```bash
# Run once, see output, kill the loop
INTERVAL_SEC=1 bash autopilot/run_autopilot.sh 2>&1 | head -30
pkill -f run_autopilot.sh
```

## Restart after a fix

```bash
# Clear the restart counter if you fixed something
rm autopilot/logs/state/autopilot.ts
bash autopilot/run_autopilot.sh &
```

---

*Last updated: 2026-10-14*
*License: MIT*
