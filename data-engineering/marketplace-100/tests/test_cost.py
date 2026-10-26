"""
test_cost.py — tests for the cost telemetry + budget guard.

Covers:

  * `cost_usd()` math for every model in the PRICING table
  * `cost_usd()` falls back to DEFAULT_MODEL on unknown names
  * `CostLedger.record()` accumulates and `total()` sums correctly
  * `CostLedger.since()` filters by iter_no
  * `BudgetGuard.check()` raises on each cap (daily USD,
    hourly tokens, daily DBU)
  * `BudgetGuard.check()` is silent when under every cap
  * `read_dbu_for_iteration()` returns 0.0 on no-Spark /
    exception paths
  * CLI demo is runnable (smoke)

The DBU path is exercised with a MagicMock so we don't need a
real SparkSession.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
from unittest.mock import MagicMock

import pytest

from m100.cost import (
    PRICING,
    DEFAULT_MODEL,
    cost_usd,
    CostRecord,
    CostLedger,
    BudgetExceeded,
    BudgetGuard,
    read_dbu_for_iteration,
)


# ============================================================
# Pricing math
# ============================================================

@pytest.mark.parametrize("model,prices", list(PRICING.items()))
def test_pricing_math_for_each_model(model, prices):
    """For each known model, a 1M-prompt + 1M-completion call
    costs exactly input_price + output_price USD."""
    in_price, out_price = prices
    cost = cost_usd(model, prompt_tokens=1_000_000, completion_tokens=1_000_000)
    assert math.isclose(cost, in_price + out_price, rel_tol=1e-9)


def test_pricing_zero_tokens_is_free():
    """0 input + 0 output = $0.00, no division-by-zero weirdness."""
    for model in PRICING:
        assert cost_usd(model, 0, 0) == 0.0


def test_pricing_unknown_model_falls_back_to_default():
    """An unknown model name should use DEFAULT_MODEL's prices
    (not raise). This protects against typos and new models
    that haven't been added to the PRICING table yet."""
    unknown = "databricks-gpt-9000-instruct"
    in_p_def, out_p_def = PRICING[DEFAULT_MODEL]
    cost = cost_usd(unknown, prompt_tokens=1_000_000, completion_tokens=1_000_000)
    expected = in_p_def + out_p_def
    assert math.isclose(cost, expected, rel_tol=1e-9)


def test_pricing_known_model_in_table():
    """DEFAULT_MODEL must itself be in the PRICING dict (so the
    fallback in cost_usd always works)."""
    assert DEFAULT_MODEL in PRICING


# ============================================================
# CostRecord
# ============================================================

def test_cost_record_to_dict_rounds_cost():
    """to_dict() rounds cost_usd to 6 decimal places (sub-cent)."""
    rec = CostRecord(
        iter_no=1, model=DEFAULT_MODEL,
        prompt_tokens=123, completion_tokens=45,
        cost_usd=0.000123456789, dbu=0.0,
    )
    d = rec.to_dict()
    assert d["iter_no"] == 1
    assert d["prompt_tokens"] == 123
    assert d["completion_tokens"] == 45
    # Rounded to 6dp
    assert d["cost_usd"] == 0.000123


# ============================================================
# CostLedger
# ============================================================

def test_ledger_record_computes_cost():
    """record() auto-computes cost_usd from tokens + model."""
    ledger = CostLedger()
    cr = ledger.record(
        iter_no=0, model=DEFAULT_MODEL,
        prompt_tokens=1_000_000, completion_tokens=1_000_000,
    )
    in_p, out_p = PRICING[DEFAULT_MODEL]
    assert math.isclose(cr.cost_usd, in_p + out_p, rel_tol=1e-9)


def test_ledger_total_sums_all_records():
    """total() returns the sum across the whole ledger."""
    ledger = CostLedger()
    ledger.record(iter_no=0, model=DEFAULT_MODEL,
                  prompt_tokens=1_000, completion_tokens=200)
    ledger.record(iter_no=1, model=DEFAULT_MODEL,
                  prompt_tokens=2_000, completion_tokens=400)
    ledger.record(iter_no=2, model=DEFAULT_MODEL,
                  prompt_tokens=3_000, completion_tokens=600)
    usd, pt, ct = ledger.total()
    assert pt == 6_000
    assert ct == 1_200
    assert usd > 0


def test_ledger_since_filters_by_iter_no():
    """since(iter) returns only records with iter_no >= iter."""
    ledger = CostLedger()
    for i in range(5):
        ledger.record(iter_no=i, model=DEFAULT_MODEL,
                      prompt_tokens=100, completion_tokens=50)
    # since 3 → iter_no 3, 4
    usd, pt, ct = ledger.since(3)
    assert pt == 200  # 100 + 100
    assert ct == 100  # 50 + 50
    # since 0 → all 5
    usd_all, pt_all, ct_all = ledger.since(0)
    assert pt_all == 500
    assert ct_all == 250


def test_ledger_empty_total_is_zero():
    """An empty ledger totals to (0.0, 0, 0)."""
    ledger = CostLedger()
    usd, pt, ct = ledger.total()
    assert usd == 0.0
    assert pt == 0
    assert ct == 0


# ============================================================
# BudgetGuard — happy path
# ============================================================

def test_guard_silent_when_under_all_caps():
    """A small spend + no DBU should not raise."""
    ledger = CostLedger()
    ledger.record(iter_no=0, model=DEFAULT_MODEL,
                  prompt_tokens=500, completion_tokens=200, dbu=0.1)
    guard = BudgetGuard()  # defaults: $5/day, 200k tokens, 5 DBU
    # Should not raise
    guard.check(ledger, current_iter=0)


# ============================================================
# BudgetGuard — each cap triggers
# ============================================================

def test_guard_raises_on_daily_usd_cap():
    """Hit the daily-USD cap → BudgetExceeded."""
    ledger = CostLedger()
    # 1M prompt + 1M completion = in_p + out_p USD, which exceeds $5
    ledger.record(
        iter_no=0, model=DEFAULT_MODEL,
        prompt_tokens=1_000_000, completion_tokens=1_000_000,
    )
    guard = BudgetGuard(max_daily_usd=1.0)  # tight cap
    with pytest.raises(BudgetExceeded) as exc:
        guard.check(ledger, current_iter=0)
    assert "daily FM-API cost" in str(exc.value)


def test_guard_raises_on_hourly_token_cap():
    """Hit the per-window token cap (last 10 iters) → BudgetExceeded."""
    ledger = CostLedger()
    # Stuff 11 iters of 50k tokens each into the last-10 window
    for i in range(11):
        ledger.record(
            iter_no=i, model=DEFAULT_MODEL,
            prompt_tokens=25_000, completion_tokens=25_000,  # 50k each
        )
    guard = BudgetGuard(
        max_daily_usd=1_000.0,  # generous so this isn't the trigger
        max_hourly_tokens=200_000,  # 10 iters × 50k = 500k > 200k
    )
    with pytest.raises(BudgetExceeded) as exc:
        guard.check(ledger, current_iter=10)
    assert "token spend" in str(exc.value)


def test_guard_raises_on_daily_dbu_cap():
    """Hit the daily-DBU cap → BudgetExceeded."""
    ledger = CostLedger()
    ledger.record(
        iter_no=0, model=DEFAULT_MODEL,
        prompt_tokens=100, completion_tokens=50, dbu=10.0,
    )
    guard = BudgetGuard(
        max_daily_usd=1_000.0,
        max_hourly_tokens=10_000_000,
        max_daily_dbu=5.0,
    )
    with pytest.raises(BudgetExceeded) as exc:
        guard.check(ledger, current_iter=0)
    assert "DBU consumption" in str(exc.value)


def test_guard_hourly_window_uses_last_10_iters():
    """The hourly cap is scoped to the last 10 iterations, not all."""
    ledger = CostLedger()
    # Iter 0: heavy (5M tokens) — but it's outside the last-10 window
    # when current_iter=20, so it should NOT trip the hourly cap.
    ledger.record(iter_no=0, model=DEFAULT_MODEL,
                  prompt_tokens=2_500_000, completion_tokens=2_500_000)
    # Iter 11-20: tiny spend, inside the window
    for i in range(11, 21):
        ledger.record(iter_no=i, model=DEFAULT_MODEL,
                      prompt_tokens=10, completion_tokens=10)
    guard = BudgetGuard(
        max_daily_usd=1_000_000.0,  # generous
        max_hourly_tokens=200_000,
    )
    # current_iter=20 → since(10) → only iters 11..20
    guard.check(ledger, current_iter=20)  # must NOT raise


# ============================================================
# read_dbu_for_iteration
# ============================================================

def test_read_dbu_returns_zero_on_no_spark():
    """If `spark.sql` raises (no real workspace), return 0.0."""
    spark = MagicMock()
    spark.sql.side_effect = RuntimeError("no spark here")
    dbu = read_dbu_for_iteration(spark, iter_no=1)
    assert dbu == 0.0


def test_read_dbu_returns_zero_on_empty_result():
    """If the query returns no rows, return 0.0 (no .first())."""
    spark = MagicMock()
    spark.sql.return_value.first.return_value = None
    dbu = read_dbu_for_iteration(spark, iter_no=1)
    assert dbu == 0.0


def test_read_dbu_sums_query_result():
    """If the query returns {dbu: 12.5}, return 12.5."""
    spark = MagicMock()
    spark.sql.return_value.first.return_value = {"dbu": 12.5}
    dbu = read_dbu_for_iteration(spark, iter_no=1)
    assert dbu == 12.5


def test_read_dbu_handles_null_dbu_value():
    """If the result row has dbu=None, return 0.0 (not None)."""
    spark = MagicMock()
    spark.sql.return_value.first.return_value = {"dbu": None}
    dbu = read_dbu_for_iteration(spark, iter_no=1)
    assert dbu == 0.0


# ============================================================
# CLI smoke
# ============================================================

def test_cli_demo_runs():
    """The `python -m m100.cost` CLI should run without error."""
    result = subprocess.run(
        [sys.executable, "-m", "m100.cost"],
        capture_output=True, text=True, timeout=10,
    )
    # The demo triggers BudgetExceeded on purpose; exit code
    # is still 0 (the script catches it).
    assert "Total:" in result.stdout
    assert "budget hit" in result.stdout
