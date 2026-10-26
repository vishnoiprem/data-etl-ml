"""
================================================================
RUN_1000_CYCLES  --  the headline proof for the AI Agents course.
================================================================

Run:    python3 code/run_1000_cycles.py [--n 1000] [--seed 42]
Keys:   none

Samples N random SMB scenarios from agent_roi.RANGES, runs each
through run_trial, aggregates with review(), and writes:

  ../results/1000_cycle_review_<timestamp>.md   (human report)
  ../results/latest.json                       (machine report)

The 1000-cycle review is the "world 1%" bar: if the median ROI is
positive in >= 95% of trials, the formula is robust.  If the P05
downside is not catastrophic (<= 1 month of agent cost), the
formula is safe.  The autopilot re-runs this on a timer and
appends a new markdown report each time.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Make sibling imports work when run as a script
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from agent_roi import RANGES, Trial, run_trial, review, ReviewStats


# =================================================================
# CONFIG
# =================================================================

LESSON_NUMBER = "run_1000_cycles.py"
DEFAULT_N = 1000
DEFAULT_SEED = 42
RESULTS_DIR = HERE.parent / "results"


# =================================================================
# SAMPLER  --  uniform within each range
# =================================================================

def sample_inputs(rng: random.Random) -> dict[str, float]:
    """Draw one random scenario from the SMB ranges."""
    return {
        "hours_saved_per_week": rng.uniform(*RANGES["hours_saved_per_week"]),
        "hourly_rate_usd":      rng.uniform(*RANGES["hourly_rate_usd"]),
        "volume_factor":        rng.uniform(*RANGES["volume_factor"]),
        "adoption_rate":        rng.uniform(*RANGES["adoption_rate"]),
        "success_rate":         rng.uniform(*RANGES["success_rate"]),
        "agent_cost_usd":       rng.uniform(*RANGES["agent_cost_usd"]),
    }


def run_cycles(n: int, seed: int) -> tuple[list[Trial], ReviewStats, float]:
    """Run n cycles.  Returns (trials, stats, wall_seconds)."""
    rng = random.Random(seed)
    t0 = time.time()
    trials: list[Trial] = []
    for _ in range(n):
        inp = sample_inputs(rng)
        trials.append(run_trial(**inp))
    elapsed = time.time() - t0
    stats = review(trials)
    return trials, stats, elapsed


# =================================================================
# WRITERS
# =================================================================

def write_markdown_report(stats: ReviewStats, n: int, seed: int, elapsed: float, ts: str) -> Path:
    """Write a human-readable markdown report."""
    path = RESULTS_DIR / f"1000_cycle_review_{ts}.md"
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# 1000-Cycle ROI Review",
        f"",
        f"_Generated: {ts}  ·  cycles: {n}  ·  seed: {seed}  ·  wall: {elapsed:.2f}s_",
        f"",
        f"## Headline numbers",
        f"",
        f"| Metric | Value |",
        f"|---|---:|",
        f"| Trials | {stats.n:,} |",
        f"| Mean monthly ROI | **${stats.mean_roi:+,.0f}** |",
        f"| Median (P50) monthly ROI | **${stats.median_roi:+,.0f}** |",
        f"| P05 (downside) | ${stats.p05_roi:+,.0f} |",
        f"| P25 | ${stats.p25_roi:+,.0f} |",
        f"| P75 | ${stats.p75_roi:+,.0f} |",
        f"| P95 (upside) | ${stats.p95_roi:+,.0f} |",
        f"| Stddev | ${stats.stddev_roi:,.0f} |",
        f"| **% positive** | **{stats.pct_positive:.1%}** |",
        f"| **% >= 3x payback** | **{stats.pct_3x:.1%}** |",
        f"",
        f"## Best trial",
        f"",
        f"  {stats.best.summary()}",
        f"",
        f"## Worst trial",
        f"",
        f"  {stats.worst.summary()}",
        f"",
        f"## Verdict",
        f"",
    ]

    # Pass / fail against the "world 1%" bar
    pct_pos = stats.pct_positive
    p05 = stats.p05_roi
    median = stats.median_roi

    if pct_pos >= 0.95 and p05 > -100 and median > 0:
        verdict = "**PASS** -- the formula is robust. Median ROI is positive in 95%+ of trials and the P05 downside is not catastrophic."
    elif pct_pos >= 0.85 and median > 0:
        verdict = "**MARGINAL** -- the formula is positive in most trials but the tail is wide. Tighten the inputs before deploying at scale."
    else:
        verdict = "**FAIL** -- the formula is not robust under the current input ranges. Lower the cost or raise the success rate."

    lines.append(f"  {verdict}")
    lines.append("")
    lines.append("## How to read this")
    lines.append("")
    lines.append("- **Mean / P50**: typical monthly ROI across 1000 random SMB scenarios")
    lines.append("- **P05**: worst-case 5% of scenarios (downside). If this is > -1 month of agent cost, you're safe.")
    lines.append("- **P95**: best-case 5% (upside). This is the headline number for marketing.")
    lines.append("- **% positive**: fraction of scenarios where the agent nets positive ROI")
    lines.append("- **% >= 3x payback**: fraction of scenarios where the agent returns >= 3x its cost (the 'good deal' threshold)")
    lines.append("")
    lines.append("## Reproduce")
    lines.append("")
    lines.append("```bash")
    lines.append(f"python3 code/run_1000_cycles.py --n {n} --seed {seed}")
    lines.append("```")
    lines.append("")

    path.write_text("\n".join(lines))
    return path


def write_latest_json(stats: ReviewStats, n: int, seed: int, elapsed: float, ts: str) -> Path:
    """Write a machine-readable snapshot for diffing over time."""
    path = RESULTS_DIR / "latest.json"
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "ts": ts,
        "n": n,
        "seed": seed,
        "wall_seconds": round(elapsed, 3),
        "n_cycles_per_sec": round(n / elapsed, 1) if elapsed > 0 else None,
        "mean_roi": round(stats.mean_roi, 2),
        "median_roi": round(stats.median_roi, 2),
        "p05_roi": round(stats.p05_roi, 2),
        "p25_roi": round(stats.p25_roi, 2),
        "p75_roi": round(stats.p75_roi, 2),
        "p95_roi": round(stats.p95_roi, 2),
        "stddev_roi": round(stats.stddev_roi, 2),
        "pct_positive": round(stats.pct_positive, 4),
        "pct_3x": round(stats.pct_3x, 4),
        "best": {
            "hours_saved_per_week": stats.best.hours_saved_per_week,
            "hourly_rate_usd": stats.best.hourly_rate_usd,
            "volume_factor": stats.best.volume_factor,
            "adoption_rate": stats.best.adoption_rate,
            "success_rate": stats.best.success_rate,
            "agent_cost_usd": stats.best.agent_cost_usd,
            "roi_usd": round(stats.best.roi_usd, 2),
            "roi_multiple": round(stats.best.roi_multiple, 2),
        },
        "worst": {
            "hours_saved_per_week": stats.worst.hours_saved_per_week,
            "hourly_rate_usd": stats.worst.hourly_rate_usd,
            "volume_factor": stats.worst.volume_factor,
            "adoption_rate": stats.worst.adoption_rate,
            "success_rate": stats.worst.success_rate,
            "agent_cost_usd": stats.worst.agent_cost_usd,
            "roi_usd": round(stats.worst.roi_usd, 2),
            "roi_multiple": round(stats.worst.roi_multiple, 2),
        },
    }
    path.write_text(json.dumps(payload, indent=2))
    return path


# =================================================================
# PRUNE OLD REPORTS  --  keep 7 days
# =================================================================

def prune_old_reports(max_age_days: int = 7) -> int:
    """Delete markdown reports older than max_age_days.  Returns count deleted."""
    if not RESULTS_DIR.exists():
        return 0
    cutoff = time.time() - max_age_days * 86400
    deleted = 0
    for f in RESULTS_DIR.glob("1000_cycle_review_*.md"):
        if f.stat().st_mtime < cutoff:
            f.unlink()
            deleted += 1
    return deleted


# =================================================================
# ENTRY
# =================================================================

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=DEFAULT_N, help="number of cycles")
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED, help="RNG seed for reproducibility")
    args = ap.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    trials, stats, elapsed = run_cycles(args.n, args.seed)

    md_path = write_markdown_report(stats, args.n, args.seed, elapsed, ts)
    json_path = write_latest_json(stats, args.n, args.seed, elapsed, ts)
    pruned = prune_old_reports()

    print("=" * 60)
    print(f"  {LESSON_NUMBER}  --  {args.n} cycles in {elapsed:.2f}s ({args.n/elapsed:,.0f}/s)")
    print("=" * 60)
    print(stats.report())
    print(f"  Markdown  -> {md_path}")
    print(f"  JSON      -> {json_path}")
    if pruned:
        print(f"  Pruned    : {pruned} old report(s)")
    print("=" * 60)

    # Exit 0 on PASS, 1 otherwise (used by the autopilot)
    if stats.pct_positive >= 0.95 and stats.p05_roi > -100 and stats.median_roi > 0:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
