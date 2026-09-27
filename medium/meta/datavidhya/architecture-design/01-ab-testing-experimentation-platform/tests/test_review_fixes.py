"""Regression tests for review findings (Problem 1)."""

import sys
import numpy as np
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from stats_engine import welch_ttest
from peeking_protection import PeekSafeEngine


def test_welch_returns_no_nan_on_constant_metric():
    """Both arms are constant (e.g. metric=0). SE=0 must not produce NaN."""
    c = np.zeros(100)
    t = np.zeros(100)
    res = welch_ttest(c, t)
    assert not np.isnan(res.p_value)
    assert res.p_value == 1.0          # no signal → no significance
    assert res.ci_low == res.ci_high == 0.0


def test_peek_uses_ci_direction_not_just_mean_sign():
    """Recommendation should depend on CI bounds, not sign of mean diff.

    A small mean diff with wide CI should be INCONCLUSIVE.
    """
    engine = PeekSafeEngine(target_alpha=0.05, max_days=3)
    rng = np.random.default_rng(0)
    # Both arms same distribution → mean ~0, CI should bracket 0
    c = rng.normal(0, 1, 50)
    t = rng.normal(0.001, 1, 50)       # tiny effect
    r = engine.update(3, c, t)
    assert r.recommendation == "INCONCLUSIVE"


def test_peek_kill_when_ci_upper_below_zero():
    """With a clear negative effect, KILL should fire."""
    engine = PeekSafeEngine(target_alpha=0.05, max_days=3)
    rng = np.random.default_rng(1)
    c = rng.normal(0.5, 0.05, 1000)     # control high
    t = rng.normal(-0.5, 0.05, 1000)    # treatment crashed
    r = engine.update(3, c, t)
    assert r.recommendation == "KILL"


def test_peek_ship_when_ci_lower_above_zero():
    """With a clear positive effect, SHIP should fire."""
    engine = PeekSafeEngine(target_alpha=0.05, max_days=3)
    rng = np.random.default_rng(2)
    c = rng.normal(0.5, 0.05, 1000)
    t = rng.normal(1.0, 0.05, 1000)     # big positive effect
    r = engine.update(3, c, t)
    assert r.recommendation == "SHIP"
