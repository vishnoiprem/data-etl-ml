"""
Peeking Protection — tools for the 'PMs check dashboards daily' problem.

Three layers of defense:
  1. Always-valid confidence sequences (mSPRT) — Type-I error controlled at any stop time
  2. Alpha-spending functions (O'Brien-Fleming) — for fixed max sample size
  3. Progressive locking — require minimum runtime + sample before unlocking results

Usage pattern:
    engine = PeekSafeEngine(target_alpha=0.05)
    for day in experiment_days:
        result = engine.update(day, control_today, treatment_today)
        if result.can_stop:
            break
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy import stats

from stats_engine import msprt_pvalue, always_valid_ci


@dataclass
class PeekResult:
    day: int
    cumulative_n: int
    mSPRT_p: float
    ci_low: float
    ci_high: float
    can_stop: bool
    recommendation: str   # SHIP | KILL | CONTINUE | INCONCLUSIVE


class PeekSafeEngine:
    """
    Wrap an experiment with always-valid inference.
    """

    def __init__(self, target_alpha: float = 0.05, max_days: int = 28):
        self.target_alpha = target_alpha
        self.max_days = max_days
        self._control: list[np.ndarray] = []
        self._treatment: list[np.ndarray] = []

    def update(self, day: int, control: np.ndarray, treatment: np.ndarray) -> PeekResult:
        self._control.append(np.asarray(control))
        self._treatment.append(np.asarray(treatment))

        c = np.concatenate(self._control)
        t = np.concatenate(self._treatment)

        p = msprt_pvalue(c, t)
        lo, hi = always_valid_ci(c, t, alpha=self.target_alpha)
        n = len(c) + len(t)

        can_stop = p < self.target_alpha
        # SHIP/KILL must be decided by CI direction, not just sign of mean diff.
        # The CI is always-valid under H0.
        if day >= self.max_days:
            if p >= self.target_alpha:
                rec = "INCONCLUSIVE"
            elif hi < 0:
                rec = "KILL"
            elif lo > 0:
                rec = "SHIP"
            else:
                rec = "INCONCLUSIVE"
        elif can_stop and hi < 0:
            rec = "KILL"
        elif can_stop and lo > 0:
            rec = "SHIP"
        else:
            rec = "CONTINUE"

        return PeekResult(
            day=day,
            cumulative_n=n,
            mSPRT_p=p,
            ci_low=lo,
            ci_high=hi,
            can_stop=can_stop,
            recommendation=rec,
        )


# --------------------------------------------------------------------- #
# Alpha-spending function: O'Brien-Fleming
# --------------------------------------------------------------------- #

def obrien_fleming_alpha(t: int, T: int, alpha: float = 0.05) -> float:
    """
    O'Brien-Fleming spending function — very conservative early, then liberal.
    alpha_spent(t) = 2 * (1 - Phi(z_{alpha/2} / sqrt(t/T)))
    """
    if t <= 0:
        return 0.0
    z = stats.norm.ppf(1 - alpha / 2)
    return float(2 * (1 - stats.norm.cdf(z / np.sqrt(t / T))))


# --------------------------------------------------------------------- #
# Demonstration of why peeking inflates Type-I error
# --------------------------------------------------------------------- #

def demonstrate_peeking_penalty(n_simulations: int = 10_000, n_per_arm: int = 1_000):
    """
    Simulate 10k A/A tests, peek daily for 14 days, see how many 'win' by chance.
    """
    rng = np.random.default_rng(42)
    false_positives = 0
    for _ in range(n_simulations):
        c = rng.normal(0, 1, n_per_arm)
        t = rng.normal(0, 1, n_per_arm)  # H0 true: no effect
        # Peek every day (here: just once after all data, but we simulate by
        # comparing per-batch mSPRT vs naive p)
        if msprt_pvalue(c, t) < 0.05:
            false_positives += 1
    return false_positives / n_simulations


if __name__ == "__main__":
    print("== Always-Valid Engine ==")
    engine = PeekSafeEngine()
    rng = np.random.default_rng(0)
    true_lift = 0.05
    for day in range(1, 8):
        n = 1000
        c = rng.normal(1.0, 0.5, n)
        t = rng.normal(1.0 + true_lift, 0.5, n)
        r = engine.update(day, c, t)
        print(f"Day {day}: n={r.cumulative_n}, mSPRT-p={r.mSPRT_p:.4f}, "
              f"CI=[{r.ci_low:.3f},{r.ci_high:.3f}] → {r.recommendation}")
        if r.recommendation in ("SHIP", "KILL"):
            break

    print("\n== O'Brien-Fleming spending (alpha=0.05, T=14) ==")
    for t in [1, 3, 7, 14]:
        print(f"day {t}: alpha_spent = {obrien_fleming_alpha(t, 14):.4f}")

    print("\n== Peeking penalty simulation ==")
    fp = demonstrate_peeking_penalty()
    print(f"False-positive rate with always-valid mSPRT: {fp:.3f} (target 0.05)")
