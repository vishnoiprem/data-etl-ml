"""
================================================================
AGENT_ROI  --  The AI agent ROI formula, in code.
================================================================

Run:    python3 code/agent_roi.py
Keys:   none (pure math, deterministic)

The formula (L1 of the course):

    monthly_value = hours_saved_per_week * hourly_rate
                    * weeks_per_month
                    * volume_factor
                    * adoption_rate
                    * success_rate

    monthly_roi   = monthly_value - agent_cost

The 5 inputs (hours, rate, volume, adoption, success) and 1 cost
are the 6 knobs every SMB owner must estimate before deploying an
agent.  The 1000-cycle notebook samples each knob from a realistic
range and reports the distribution.

This file is intentionally minimal: no LLM, no tools, no I/O.
The notebook in ../notebook.ipynb imports this and runs 1000 trials.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass


# =================================================================
# CONFIG  --  All magic numbers live here
# =================================================================

LESSON_NUMBER = "agent_roi.py"
WEEKS_PER_MONTH = 4.33  # 52 / 12

# Realistic Asian SMB ranges (used by the 1000-cycle sampler)
RANGES = {
    "hours_saved_per_week": (1.0, 5.0),     # hours the agent saves per week
    "hourly_rate_usd":      (25.0, 150.0),  # what the SMB owner's time is worth
    "volume_factor":        (10.0, 100.0),  # number of tasks/wk the agent handles
    "adoption_rate":        (0.5, 1.0),     # fraction of tasks the agent actually does
    "success_rate":         (0.7, 1.0),     # fraction of agent tasks done correctly
    "agent_cost_usd":       (10.0, 100.0),  # monthly LLM + infra cost
}


# =================================================================
# THE FORMULA
# =================================================================

def monthly_value(
    hours_saved_per_week: float,
    hourly_rate_usd: float,
    volume_factor: float,
    adoption_rate: float,
    success_rate: float,
) -> float:
    """USD per month the agent is worth, before subtracting cost.

    hours_saved_per_week * hourly_rate    = $ saved per week
    * WEEKS_PER_MONTH                     = $ saved per month (one task)
    * volume_factor / 100.0               = scale to N tasks/wk
    * adoption_rate                       = fraction actually used
    * success_rate                        = fraction done correctly
    """
    per_task_per_month = hours_saved_per_week * hourly_rate_usd * WEEKS_PER_MONTH
    scale = volume_factor / 100.0
    return per_task_per_month * scale * adoption_rate * success_rate


def monthly_roi(
    hours_saved_per_week: float,
    hourly_rate_usd: float,
    volume_factor: float,
    adoption_rate: float,
    success_rate: float,
    agent_cost_usd: float,
) -> float:
    """USD per month the agent nets, after cost."""
    return monthly_value(
        hours_saved_per_week,
        hourly_rate_usd,
        volume_factor,
        adoption_rate,
        success_rate,
    ) - agent_cost_usd


# =================================================================
# ONE TRIAL  --  one cycle of the 1000-cycle review
# =================================================================

@dataclass
class Trial:
    """One randomized scenario + the resulting ROI."""
    hours_saved_per_week: float
    hourly_rate_usd: float
    volume_factor: float
    adoption_rate: float
    success_rate: float
    agent_cost_usd: float
    value_usd: float
    cost_usd: float
    roi_usd: float
    roi_multiple: float  # roi / cost  ("paid back Nx")

    def summary(self) -> str:
        return (
            f"hrs={self.hours_saved_per_week:.1f}/wk  "
            f"rate=${self.hourly_rate_usd:.0f}/hr  "
            f"vol={self.volume_factor:.0f}  "
            f"adopt={self.adoption_rate:.0%}  "
            f"succ={self.success_rate:.0%}  "
            f"cost=${self.agent_cost_usd:.0f}/mo  ->  "
            f"ROI ${self.roi_usd:+,.0f}/mo ({self.roi_multiple:.1f}x)"
        )


def run_trial(
    hours_saved_per_week: float,
    hourly_rate_usd: float,
    volume_factor: float,
    adoption_rate: float,
    success_rate: float,
    agent_cost_usd: float,
) -> Trial:
    """Run one trial.  Pure function: same inputs -> same output."""
    value = monthly_value(
        hours_saved_per_week, hourly_rate_usd,
        volume_factor, adoption_rate, success_rate,
    )
    roi = value - agent_cost_usd
    multiple = roi / agent_cost_usd if agent_cost_usd > 0 else 0.0
    return Trial(
        hours_saved_per_week=hours_saved_per_week,
        hourly_rate_usd=hourly_rate_usd,
        volume_factor=volume_factor,
        adoption_rate=adoption_rate,
        success_rate=success_rate,
        agent_cost_usd=agent_cost_usd,
        value_usd=value,
        cost_usd=agent_cost_usd,
        roi_usd=roi,
        roi_multiple=multiple,
    )


# =================================================================
# STATISTICS OVER MANY TRIALS
# =================================================================

@dataclass
class ReviewStats:
    """Aggregate stats from N trials."""
    n: int
    mean_roi: float
    median_roi: float
    p05_roi: float        # 5th percentile (downside)
    p25_roi: float
    p75_roi: float
    p95_roi: float
    stddev_roi: float
    pct_positive: float   # 0.0 - 1.0
    pct_3x: float         # fraction of trials that paid back >= 3x
    best: Trial
    worst: Trial

    def report(self) -> str:
        return (
            f"  N            : {self.n}\n"
            f"  Mean ROI     : ${self.mean_roi:+,.0f}/mo\n"
            f"  Median (P50) : ${self.median_roi:+,.0f}/mo\n"
            f"  P05 (down)   : ${self.p05_roi:+,.0f}/mo\n"
            f"  P25          : ${self.p25_roi:+,.0f}/mo\n"
            f"  P75          : ${self.p75_roi:+,.0f}/mo\n"
            f"  P95 (up)     : ${self.p95_roi:+,.0f}/mo\n"
            f"  Stddev       : ${self.stddev_roi:,.0f}\n"
            f"  % positive   : {self.pct_positive:.1%}\n"
            f"  % >= 3x pay  : {self.pct_3x:.1%}\n"
            f"  Best trial   : {self.best.summary()}\n"
            f"  Worst trial  : {self.worst.summary()}\n"
        )


def percentile(sorted_values: list[float], pct: float) -> float:
    """Linear-interpolation percentile.  pct in [0, 100]."""
    if not sorted_values:
        return 0.0
    k = (len(sorted_values) - 1) * (pct / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    if f == c:
        return sorted_values[f]
    return sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f)


def review(trials: list[Trial]) -> ReviewStats:
    """Aggregate one set of trials into a ReviewStats report."""
    rois = sorted([t.roi_usd for t in trials])
    if not rois:
        raise ValueError("no trials to review")

    return ReviewStats(
        n=len(trials),
        mean_roi=statistics.fmean(rois),
        median_roi=percentile(rois, 50),
        p05_roi=percentile(rois, 5),
        p25_roi=percentile(rois, 25),
        p75_roi=percentile(rois, 75),
        p95_roi=percentile(rois, 95),
        stddev_roi=statistics.pstdev(rois) if len(rois) > 1 else 0.0,
        pct_positive=sum(1 for r in rois if r > 0) / len(rois),
        pct_3x=sum(1 for t in trials if t.roi_multiple >= 3.0) / len(trials),
        best=max(trials, key=lambda t: t.roi_usd),
        worst=min(trials, key=lambda t: t.roi_usd),
    )


# =================================================================
# DEMO  --  3 worked examples
# =================================================================

def demo() -> None:
    """Three worked examples from the lesson doc."""
    print("=" * 60)
    print(f"  {LESSON_NUMBER}  --  ROI formula demo (3 examples)")
    print("=" * 60)

    # Example 1: SMB owner triages customer emails with an agent
    #   saves 2 hr/wk, time is worth $50/hr, 80 tasks/wk, 80% adopted, 85% success
    #   agent costs $30/mo
    t1 = run_trial(2.0, 50.0, 80.0, 0.8, 0.85, 30.0)
    print(f"\n  Example 1: SMB email triage")
    print(f"    {t1.summary()}")
    print(f"    Annualized: ${t1.roi_usd * 12:+,.0f}/yr")

    # Example 2: Solo trader does pre-market research
    #   saves 3 hr/wk, time worth $100/hr, 30 tasks/wk, 90% adopted, 90% success
    #   agent costs $50/mo
    t2 = run_trial(3.0, 100.0, 30.0, 0.9, 0.9, 50.0)
    print(f"\n  Example 2: Solo trader research")
    print(f"    {t2.summary()}")
    print(f"    Annualized: ${t2.roi_usd * 12:+,.0f}/yr")

    # Example 3: Tiny e-commerce shop, agent does listing photos + descriptions
    #   saves 1 hr/wk, time worth $25/hr, 100 tasks/wk, 60% adopted, 70% success
    #   agent costs $80/mo
    t3 = run_trial(1.0, 25.0, 100.0, 0.6, 0.7, 80.0)
    print(f"\n  Example 3: E-commerce listings")
    print(f"    {t3.summary()}")
    print(f"    Annualized: ${t3.roi_usd * 12:+,.0f}/yr")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    demo()
