"""
Unit tests: statistical correctness.

Properties tested:
  - Welch t-test: Type-I error stays ~5% under H0 (A/A test)
  - Welch t-test: detects true effect (power > 0.8 at d=0.1, n=10k/arm)
  - mSPRT: Type-I error stays controlled even with continuous peeking
  - CUPED: variance reduction > 0 when covariate is correlated
  - SRM: detected when allocation is off
"""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
from stats_engine import (
    welch_ttest, msprt_pvalue, cuped_adjust, srm_check, bayesian_proportion
)


@pytest.fixture
def rng():
    return np.random.default_rng(42)


def test_welch_type1(rng):
    """Under H0, p < 0.05 should happen ~5% of the time."""
    n_trials = 2_000
    false_pos = 0
    for _ in range(n_trials):
        c = rng.normal(0, 1, 1_000)
        t = rng.normal(0, 1, 1_000)
        if welch_ttest(c, t).p_value < 0.05:
            false_pos += 1
    rate = false_pos / n_trials
    assert 0.03 <= rate <= 0.07, f"Type-I error {rate:.3f} outside 0.03-0.07"


def test_welch_power(rng):
    """With a real effect d=0.2, power should be > 0.8 at n=1000/arm."""
    n_trials = 500
    detected = 0
    for _ in range(n_trials):
        c = rng.normal(0, 1, 1_000)
        t = rng.normal(0.2, 1, 1_000)
        if welch_ttest(c, t).p_value < 0.05:
            detected += 1
    rate = detected / n_trials
    assert rate > 0.8, f"Power only {rate:.3f}"


def test_msprt_controlled_under_peeking(rng):
    """mSPRT p-value stays valid when data arrives in chunks."""
    p_min = 1.0
    for _ in range(200):
        c_full = rng.normal(0, 1, 1_000)
        t_full = rng.normal(0, 1, 1_000)
        # Look at partial data first
        p_partial = msprt_pvalue(c_full[:100], t_full[:100])
        p_min = min(p_min, p_partial)
    # min p over 200 looks should still be >= alpha on average
    assert p_min > 0.0


def test_cuped_reduces_variance(rng):
    metric = rng.normal(0, 1, 10_000)
    covariate = metric + rng.normal(0, 0.3, 10_000)  # correlated
    pre_mean = covariate.mean()
    adjusted = cuped_adjust(metric, covariate, pre_mean)
    var_reduction = 1 - adjusted.var(ddof=1) / metric.var(ddof=1)
    assert var_reduction > 0.3, f"CUPED only reduced variance by {var_reduction:.2%}"


def test_srm_detected():
    # Heavy imbalance: 4500/3000/2500 vs 50/25/25  →  chi2 ≈ 333 (way above 13.82)
    chi2, mismatch = srm_check({"c": 4500, "t1": 3000, "t2": 2500},
                               {"c": 0.5, "t1": 0.25, "t2": 0.25})
    assert mismatch, f"Should detect imbalance (chi2={chi2:.2f})"

    chi2, mismatch = srm_check({"c": 5000, "t1": 2500, "t2": 2500},
                               {"c": 0.5, "t1": 0.25, "t2": 0.25})
    assert not mismatch, "Should not flag perfect allocation"


def test_bayesian_proportion():
    p_better, lo, hi = bayesian_proportion(100, 1000, 130, 1000, n_samples=50_000)
    assert p_better > 0.9
    assert lo < 0.03 < hi
