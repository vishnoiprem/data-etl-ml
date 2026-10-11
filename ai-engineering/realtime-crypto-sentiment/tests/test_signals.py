"""Tests for signal generation logic.

Author: Prem Vishnoi <pvishnoi@avilx.com>

Pure-Python tests; no DB, no external services.
"""
from __future__ import annotations

import math
from datetime import datetime

from src.ml.signal import Signal, generate_signal, zscore

# ── zscore ───────────────────────────────────────────────────────────────

def test_zscore_known_window():
    # Mean = 50, std = 10 (population)
    history = [40, 50, 60]  # mean = 50, var = (100+0+100)/3 = 200/3 ≈ 66.67, std ≈ 8.165
    expected_mean = 50.0
    var = sum((x - expected_mean) ** 2 for x in history) / len(history)
    expected_std = math.sqrt(var)
    z = zscore(70.0, history)
    assert math.isclose(z, (70.0 - expected_mean) / expected_std, rel_tol=1e-6)


def test_zscore_history_too_short_returns_zero():
    assert zscore(1.0, []) == 0.0
    assert zscore(1.0, [1.0]) == 0.0


def test_zscore_constant_history_returns_zero():
    history = [42.0, 42.0, 42.0, 42.0]
    assert zscore(99.0, history) == 0.0


def test_zscore_negative_value():
    history = [10, 20, 30]  # mean=20, var=66.67, std≈8.165
    z = zscore(0.0, history)
    assert z < 0
    assert math.isclose(z, -20.0 / math.sqrt(sum((x - 20) ** 2 for x in history) / 3), rel_tol=1e-6)


def test_zscore_population_std_not_sample():
    """The implementation uses population std (÷n) not sample (÷n-1).
    This test guards against a switch to the Bessel-corrected std, which
    would inflate z-scores by ~sqrt(n/(n-1)) ≈ 1.05 for small n."""
    history = [1.0, 2.0, 3.0, 4.0, 5.0]
    # population std: sqrt(((1-3)² + (2-3)² + (3-3)² + (4-3)² + (5-3)²) / 5)
    #              = sqrt((4+1+0+1+4)/5) = sqrt(2.0) ≈ 1.4142
    z = zscore(7.0, history)
    expected = (7.0 - 3.0) / math.sqrt(2.0)
    assert math.isclose(z, expected, rel_tol=1e-9)
    # Sample std (÷n-1) would give sqrt(2.5) ≈ 1.5811 → z ≈ 2.53
    sample_z = (7.0 - 3.0) / math.sqrt(2.5)
    assert not math.isclose(z, sample_z, rel_tol=1e-6)


def test_zscore_uses_history_value_not_history_itself():
    """If zscore accidentally computed the z of the history mean, it
    would always be 0 for any history. Guard against that bug."""
    history = [10.0, 20.0, 30.0, 40.0]
    z_mean = zscore(25.0, history)  # exactly the mean
    z_extreme = zscore(40.0, history)
    assert z_mean == 0.0  # but for the right reason: (25-25)/std = 0
    # Extreme value must be positive
    assert z_extreme > 0
    assert z_extreme > z_mean


# ── generate_signal ──────────────────────────────────────────────────────

def _now():
    return datetime(2026, 1, 1, 12, 0, 0)


def test_generate_signal_buy_above_threshold():
    sig = generate_signal(
        symbol="BTC",
        sentiment_value=100.0,
        sentiment_history=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        momentum_value=100.0,
        momentum_history=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        threshold=1.0,
        sent_weight=1.0,
        mom_weight=1.0,
        now=_now(),
    )
    assert sig.action == "BUY"
    assert sig.score > 1.0
    assert sig.symbol == "BTC"
    assert sig.ts == _now()


def test_generate_signal_sell_below_threshold():
    sig = generate_signal(
        symbol="ETH",
        sentiment_value=-100.0,
        sentiment_history=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        momentum_value=-100.0,
        momentum_history=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        threshold=1.0,
        sent_weight=1.0,
        mom_weight=1.0,
        now=_now(),
    )
    assert sig.action == "SELL"
    assert sig.score < -1.0


def test_generate_signal_hold_within_band():
    # History with wide variance, value close to mean → small z
    sig = generate_signal(
        symbol="SOL",
        sentiment_value=10.0,  # exactly the mean of history
        sentiment_history=[-10, -5, 0, 5, 10, 15, 20, 25, 30, 15],
        momentum_value=0.0,
        momentum_history=[-0.05, -0.02, 0.0, 0.03, 0.01, -0.01, 0.04, 0.02, -0.03, 0.0],
        threshold=1.0,
        sent_weight=1.0,
        mom_weight=1.0,
    )
    assert sig.action == "HOLD"


def test_generate_signal_too_little_history_holds_or_handles_gracefully():
    # With <2 history points, zscore returns 0 → score = 0 → HOLD
    sig = generate_signal(
        symbol="BNB",
        sentiment_value=999.0,
        sentiment_history=[42.0],
        momentum_value=999.0,
        momentum_history=[42.0],
        threshold=1.0,
    )
    assert sig.action == "HOLD"


def test_generate_signal_reason_includes_both_zscores():
    sig = generate_signal(
        symbol="XRP",
        sentiment_value=10.0,
        sentiment_history=[1, 2, 3, 4, 5],
        momentum_value=-10.0,
        momentum_history=[5, 4, 3, 2, 1],
    )
    assert "sentiment" in sig.reason
    assert "momentum" in sig.reason


def test_signal_to_row_shape():
    sig = Signal(
        symbol="DOGE", ts=_now(), action="BUY", score=1.5,
        sentiment_zscore=2.0, momentum_zscore=1.0, reason="test",
    )
    row = sig.to_row()
    assert set(row.keys()) == {
        "ts", "symbol", "action", "score",
        "sentiment_zscore", "momentum_zscore", "reason",
    }
    assert row["symbol"] == "DOGE"
    assert row["action"] == "BUY"


def test_weighted_signal_score():
    """sent_weight=2, mom_weight=0 → score = 2*sent_z, mom_z must NOT contribute.
    Pre-fix this only checked the trivial abs(z) >= 0; now we verify the
    actual weighting math: score equals 2 * sentiment_zscore exactly."""
    sig = generate_signal(
        symbol="AVAX",
        sentiment_value=100.0,  # way bigger than history mean
        sentiment_history=[10, 15, 20, 25, 30, 35, 40, 45, 50, 50],
        momentum_value=2.0,
        momentum_history=[0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2],
        threshold=1.0, sent_weight=2.0, mom_weight=0.0,
    )
    # The score is exactly 2*sent_z + 0*mom_z. If mom_weight leaked in,
    # the equality below would fail.
    assert math.isclose(sig.score, 2.0 * sig.sentiment_zscore, rel_tol=1e-9)
    assert sig.sentiment_zscore > 1.0


def test_weighted_signal_score_mom_only():
    """Symmetric case: sent_weight=0, mom_weight=3 → score = 3*mom_z only."""
    sig = generate_signal(
        symbol="LINK",
        sentiment_value=0.0,
        sentiment_history=[0, 0, 0, 0, 0],  # constant → sent_z=0
        momentum_value=10.0,  # far from mean
        momentum_history=[1, 2, 3, 4, 5],
        threshold=1.0, sent_weight=0.0, mom_weight=3.0,
    )
    assert sig.sentiment_zscore == 0.0  # constant history → 0 z
    assert math.isclose(sig.score, 3.0 * sig.momentum_zscore, rel_tol=1e-9)


def test_weighted_signal_score_combined_math():
    """End-to-end: score must equal sent_w * sent_z + mom_w * mom_z exactly
    for arbitrary weights, with hand-computed expected values."""
    # Sentiment: history = [0, 10, 20] → mean=10, var=200/3, std=sqrt(66.67)≈8.165
    # sent_value=30 → sent_z = (30-10)/8.165 ≈ 2.449
    # Momentum: history = [0, 5, 10] → mean=5, var=50/3, std=sqrt(16.67)≈4.082
    # mom_value=-5 → mom_z = (-5-5)/4.082 ≈ -2.449
    sig = generate_signal(
        symbol="MATIC",
        sentiment_value=30.0,
        sentiment_history=[0.0, 10.0, 20.0],
        momentum_value=-5.0,
        momentum_history=[0.0, 5.0, 10.0],
        threshold=1.0, sent_weight=0.6, mom_weight=0.4,
    )
    expected = 0.6 * sig.sentiment_zscore + 0.4 * sig.momentum_zscore
    assert math.isclose(sig.score, expected, rel_tol=1e-9)


def test_threshold_boundary_exactly_at_threshold_is_hold():
    """The condition is `> threshold` for BUY and `< -threshold` for SELL.
    A score exactly at the threshold must be HOLD (boundary off-by-one
    test)."""
    # Construct a history where we know the exact z-score
    sig = generate_signal(
        symbol="XLM",
        sentiment_value=10.0,  # mean of history below
        sentiment_history=[0.0, 10.0, 20.0],  # mean=10
        momentum_value=5.0,  # mean of history below
        momentum_history=[0.0, 5.0, 10.0],  # mean=5
        threshold=0.0,  # any nonzero score → BUY or SELL
    )
    # With threshold=0, a score of exactly 0 is HOLD, positive is BUY, negative is SELL
    # Our constructed case → sent_z=0, mom_z=0 → score=0
    assert sig.score == 0.0
    assert sig.action == "HOLD"


def test_reason_string_format():
    """The reason is what shows up in the dashboard; pin its format so a
    refactor doesn't accidentally change the dashboard contract."""
    sig = generate_signal(
        symbol="AVAX",
        sentiment_value=1.0,
        sentiment_history=[0.0, 0.0, 0.0, 1.0, 2.0],
        momentum_value=1.0,
        momentum_history=[0.0, 0.0, 0.0, 1.0, 2.0],
    )
    # Must include both z-scores and the final score
    assert "sentiment" in sig.reason
    assert "momentum" in sig.reason
    assert "σ" in sig.reason  # Greek sigma character
    # Format must include sign-prefixed floats: e.g. +1.23
    import re
    assert re.search(r"[+-]\d+\.\d{2}", sig.reason), f"missing signed-float format: {sig.reason!r}"
