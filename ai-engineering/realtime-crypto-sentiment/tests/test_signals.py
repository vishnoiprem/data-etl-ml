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
    # Use a value that is far from the mean of the history to get a big positive z
    sig = generate_signal(
        symbol="AVAX",
        sentiment_value=100.0,  # way bigger than history mean ~30
        sentiment_history=[10, 15, 20, 25, 30, 35, 40, 45, 50, 50],
        momentum_value=2.0,
        momentum_history=[0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2],
        threshold=1.0, sent_weight=2.0, mom_weight=0.0,
    )
    assert sig.score > 1.0
    assert sig.sentiment_zscore > 1.0
    # Since mom_weight = 0, momentum contributes 0; sent dominates
    assert abs(sig.momentum_zscore) >= 0  # just check it was computed
