"""
test_dqx.py — tests for the Databricks DQX wrapper.

Covers:

  * WARN / DROP / QUARANTINE tier routing
  * default_rules_for_silver picks sensible rules from
    column names (amount/price/count → non-negative; *_id → unique)
  * DQResult.quality_score formula
  * Engine handles empty input
  * Engine handles rows that throw in a rule (treated as fail)
  * The CLI demo runs without error
"""

from __future__ import annotations

import pytest

from m100.dqx import (
    DQEngine, DQResult, DQRule, Tier,
    default_rules_for_silver, rule_not_null, rule_in_range, rule_unique,
)


# ============================================================
# Rule construction
# ============================================================

def test_rule_not_null_passes_for_value():
    assert rule_not_null("x").evaluate({"x": "a"})
    assert rule_not_null("x").evaluate({"x": 0})


def test_rule_not_null_fails_for_none_and_empty():
    assert not rule_not_null("x").evaluate({"x": None})
    assert not rule_not_null("x").evaluate({"x": ""})
    assert not rule_not_null("x").evaluate({"x": "   "})


def test_rule_in_range_passes_inside_bounds():
    r = rule_in_range("x", 0, 100)
    assert r.evaluate({"x": 50})
    assert r.evaluate({"x": 0})
    assert r.evaluate({"x": 100})


def test_rule_in_range_fails_outside():
    r = rule_in_range("x", 0, 100)
    assert not r.evaluate({"x": -1})
    assert not r.evaluate({"x": 101})


def test_rule_in_range_handles_none_and_bad_types():
    r = rule_in_range("x", 0, 100)
    # None passes (rule_not_null handles nulls separately)
    assert r.evaluate({"x": None})
    # Non-numeric → fails
    assert not r.evaluate({"x": "not a number"})


def test_rule_throwing_is_treated_as_fail():
    def check(row):
        raise RuntimeError("boom")
    r = DQRule(name="thrower", check=check)
    assert not r.evaluate({})


# ============================================================
# Engine
# ============================================================

def test_engine_empty_input():
    eng = DQEngine(rules=[])
    res = eng.evaluate([], listing_id="x")
    assert res.rows_in == 0
    assert res.rows_kept == 0
    assert res.drop_rate == 0.0
    assert res.quality_score == 1.0


def test_engine_warn_only_keeps_everything():
    rules = [rule_not_null("name", tier=Tier.WARN)]
    eng = DQEngine(rules)
    rows = [{"name": "a"}, {"name": None}, {"name": ""}]
    res = eng.evaluate(rows)
    assert res.rows_in == 3
    assert res.rows_kept == 3  # WARN doesn't drop
    assert res.rows_warn == 2


def test_engine_drop_filters_matching_rows():
    rules = [rule_not_null("name", tier=Tier.DROP)]
    eng = DQEngine(rules)
    rows = [{"name": "a"}, {"name": None}, {"name": "c"}]
    res = eng.evaluate(rows)
    assert res.rows_in == 3
    assert res.rows_kept == 2
    assert res.rows_drop == 1
    assert {r["name"] for r in res.kept} == {"a", "c"}


def test_engine_quarantine_routes_to_side_path():
    rules = [rule_not_null("name", tier=Tier.QUARANTINE)]
    eng = DQEngine(rules)
    rows = [{"name": "a"}, {"name": None}, {"name": "c"}]
    res = eng.evaluate(rows)
    assert res.rows_in == 3
    assert res.rows_kept == 2
    assert res.rows_quarantine == 1
    assert res.quarantine[0][0] == {"name": None}


def test_engine_drop_takes_precedence_over_quarantine():
    """If a row fails both DROP and QUARANTINE, it's dropped, not quarantined."""
    rules = [
        rule_not_null("name", tier=Tier.DROP),
        rule_in_range("amount", 0, 100, tier=Tier.QUARANTINE),
    ]
    eng = DQEngine(rules)
    rows = [
        {"name": "a", "amount": 50},     # kept
        {"name": None, "amount": 50},    # dropped (name null)
        {"name": "b", "amount": 999},    # quarantined (amount OOR)
    ]
    res = eng.evaluate(rows)
    assert res.rows_kept == 1
    assert res.rows_drop == 1
    assert res.rows_quarantine == 1


def test_engine_reasons_are_counted():
    rules = [rule_not_null("x", tier=Tier.DROP)]
    eng = DQEngine(rules)
    rows = [{"x": None}, {"x": None}, {"x": "v"}]
    res = eng.evaluate(rows)
    # The reasons dict on DQResult tracks warn; drop reasons
    # are not separately tracked (every drop is a row gone).
    # WARN is the only place we accumulate reasons.
    assert res.warn_reasons == {}


# ============================================================
# Quality score
# ============================================================

def test_quality_score_no_drops_scores_one():
    rules = []
    eng = DQEngine(rules)
    res = eng.evaluate([{"x": 1}, {"x": 2}])
    assert res.quality_score == 1.0


def test_quality_score_full_drop_scores_zero():
    rules = [rule_not_null("x", tier=Tier.DROP)]
    eng = DQEngine(rules)
    res = eng.evaluate([{"x": None}, {"x": None}])
    assert res.quality_score == 0.0


def test_quality_score_quarantine_costs_half():
    """Quarantine is half as costly as drop — quarantined rows are
    saved (auditable), just not in the kept set."""
    rules = [rule_in_range("x", 0, 100, tier=Tier.QUARANTINE)]
    eng = DQEngine(rules)
    res = eng.evaluate([{"x": 50}, {"x": 200}])  # 1 kept, 1 quarantined
    assert res.quarantine_rate == 0.5
    assert res.quality_score == 0.75  # 1.0 - 0.5*0.5


def test_quality_score_mixed_drops_and_quarantine():
    rules = [
        rule_not_null("a", tier=Tier.DROP),
        rule_in_range("b", 0, 100, tier=Tier.QUARANTINE),
    ]
    eng = DQEngine(rules)
    rows = [
        {"a": 1, "b": 50},   # kept
        {"a": None, "b": 50},  # drop (a null)
        {"a": 2, "b": 999},  # quarantine (b OOR)
    ]
    res = eng.evaluate(rows)
    assert res.rows_in == 3
    assert res.rows_kept == 1
    assert res.rows_drop == 1
    assert res.rows_quarantine == 1
    # drop=1/3, quarantine=1/3, score = 1 - 1/3 - 0.5*1/3 = 1 - 0.5 = 0.5
    assert abs(res.quality_score - 0.5) < 1e-9


# ============================================================
# default_rules_for_silver
# ============================================================

def test_default_rules_picks_not_null_for_every_column():
    rules = default_rules_for_silver(["a", "b", "c"])
    nn = [r for r in rules if r.name.endswith("_not_null")]
    assert len(nn) == 3
    assert {r.name for r in nn} == {"a_not_null", "b_not_null", "c_not_null"}


def test_default_rules_picks_non_negative_for_amount_columns():
    rules = default_rules_for_silver(["id", "amount", "price", "count", "name"])
    non_neg = [r for r in rules if "in_range" in r.name]
    assert len(non_neg) == 3
    assert all("0" in r.name for r in non_neg)


def test_default_rules_picks_unique_for_id_columns():
    rules = default_rules_for_silver(["id", "user_id", "amount"])
    unique = [r for r in rules if r.name.startswith("unique")]
    assert len(unique) == 2
    assert all(r.tier == Tier.QUARANTINE for r in unique)


# ============================================================
# CLI demo
# ============================================================

def test_cli_demo_runs(capsys):
    """The __main__ block should run without raising and print the summary.

    We invoke the demo via subprocess so the package import doesn't
    see the module as already-loaded (which would emit a noisy
    RuntimeWarning about top-level side effects).
    """
    import subprocess
    import sys
    result = subprocess.run(
        [sys.executable, "-m", "m100.dqx"],
        capture_output=True, text=True, env={"PYTHONPATH": "src"},
    )
    assert result.returncode == 0, f"stderr={result.stderr}"
    assert "DQ " in result.stdout
    assert "score=" in result.stdout
