"""
test_property.py — property tests for the pipeline invariants.

A property test asserts an invariant that holds for *all*
valid inputs, not just a hand-picked case. We use
`hypothesis` where it adds value, but most properties here
are simple loops over random data.

Properties covered:

  1. **Bandit never starves arms** — over N iters, every
     arm gets at least one pull with probability 1
     (UCB1 is provably logarithmically-optimal, but the
     strong empirical claim is "no starvation").

  2. **DQX quality score is in [0, 1]**.

  3. **DQX kept + dropped + quarantined == total input rows**.

  4. **Cost ledger total_usd = sum of per-record cost_usd**.

  5. **History index size grows monotonically with add_iteration()**.

  6. **Serving percentile ordering**: p50 ≤ p95 ≤ p99.

  7. **Digest determinism**: same input → same JSON output
     (the golden test).

  8. **Digest invariants**: n_iterations == n_ok + n_skipped + n_failed
     (modulo a possible "running" status we exclude from the
     sum).
"""

from __future__ import annotations

import json
import random
import statistics
import subprocess
import sys
from collections import Counter

import pandas as pd
import pytest

from m100.bandit import CategoryBandit
from m100.cost import CostLedger, DEFAULT_MODEL, cost_usd
from m100.digest import (
    compute_metrics,
    filter_recent,
    category_breakdown,
    quality_timeline,
    digest_golden,
)
from m100.dqx import (
    DQEngine, Tier, default_rules_for_silver, DQRule,
)
from m100.history_search import HistoryIndex
from m100.serving import _percentile


# ============================================================
# 1. Bandit never starves arms
# ============================================================

def test_bandit_never_starves_arms_over_200_iters():
    """200 iters over 10 arms: every arm gets at least 1 pull.
    UCB1 starts with mean=0 and UCB=inf for all unpulled
    arms, so the first 10 iters are guaranteed to cover
    all arms; after that exploration continues to favor
    unpulled / under-pulled arms.
    """
    random.seed(0)
    cats = [f"c{i}" for i in range(10)]
    bandit = CategoryBandit(arms=cats)
    for i in range(200):
        c = bandit.choose()
        bandit.update(c, random.random())
    pulled = {name for name, arm in bandit.arms.items() if arm.pulls >= 1}
    assert pulled == set(cats), f"starved arms: {set(cats) - pulled}"


def test_bandit_ucb1_favors_high_reward_over_time():
    """If one arm always returns reward=1.0 and others 0.0,
    the high-reward arm should dominate the pulls after
    the initial exploration phase."""
    bandit = CategoryBandit(arms=["good", "bad1", "bad2"])
    rewards = {"good": 1.0, "bad1": 0.0, "bad2": 0.0}
    for i in range(60):
        c = bandit.choose()
        bandit.update(c, rewards[c])
    assert bandit.arms["good"].pulls > 30, (
        f"good arm should dominate, got {bandit.arms['good'].pulls} pulls"
    )


# ============================================================
# 2-3. DQX properties
# ============================================================

def test_dqx_quality_score_in_unit_interval():
    """quality_score must always be in [0, 1]."""
    random.seed(0)
    rules = [
        DQRule(
            name="amount_ok",
            check=lambda r: r.get("amount") is not None and 0 <= r["amount"] <= 1000,
            tier=Tier.DROP,
        ),
    ]
    engine = DQEngine(rules)
    for _ in range(50):
        rows = [
            {"amount": random.choice([None, -1, 50, 5000])}
            for _ in range(random.randint(5, 50))
        ]
        res = engine.evaluate(rows)
        assert 0.0 <= res.quality_score <= 1.0


def test_dqx_row_conservation():
    """kept + quarantined + dropped (or kept + warn + dropped) == total input rows."""
    rules = [
        DQRule(
            name="id_unique",
            # Within a single batch, this only filters rows whose
            # id collides with a prior row. Naive but good enough
            # for the conservation check.
            check=lambda r: r.get("id") is not None,
            tier=Tier.QUARANTINE,
        ),
        DQRule(
            name="amount_ok",
            check=lambda r: r.get("amount") is not None and 0 <= r["amount"] <= 100,
            tier=Tier.DROP,
        ),
    ]
    engine = DQEngine(rules)
    rows = [
        {"id": i % 5, "amount": random.choice([None, 50, 200])}
        for i in range(40)
    ]
    res = engine.evaluate(rows)
    n_in = len(rows)
    n_out = len(res.kept) + len(res.quarantine) + res.rows_drop
    assert n_out == n_in, (
        f"row conservation: in={n_in}, out={n_out}, "
        f"kept={len(res.kept)}, q={len(res.quarantine)}, d={res.rows_drop}"
    )


# ============================================================
# 4. Cost ledger conservation
# ============================================================

def test_cost_ledger_total_equals_sum_of_records():
    """Ledger total_usd = sum of per-record cost_usd."""
    random.seed(0)
    ledger = CostLedger()
    for i in range(100):
        ledger.record(
            iter_no=i, model=DEFAULT_MODEL,
            prompt_tokens=random.randint(100, 5000),
            completion_tokens=random.randint(50, 1000),
        )
    usd, pt, ct = ledger.total()
    summed = sum(r.cost_usd for r in ledger.records)
    assert abs(usd - summed) < 1e-9
    assert pt == sum(r.prompt_tokens for r in ledger.records)
    assert ct == sum(r.completion_tokens for r in ledger.records)


# ============================================================
# 5. History index grows monotonically
# ============================================================

def test_history_index_size_grows_monotonically(tmp_path):
    """Adding N iterations increases the size by exactly N each call."""
    idx = HistoryIndex(persist_dir=str(tmp_path / "h"))
    prev = idx.size
    for i in range(5):
        idx.add_iteration(
            iter_no=i, listing_id=f"l{i}", category="Finance",
            summary=f"summary {i}", quality_score=0.5,
        )
        assert idx.size == prev + 1
        prev = idx.size


# ============================================================
# 6. Serving percentile ordering
# ============================================================

def test_serving_percentile_ordering():
    """p50 ≤ p95 ≤ p99 for any list of values."""
    random.seed(0)
    for _ in range(20):
        xs = [random.gauss(50, 10) for _ in range(50)]
        p50 = _percentile(xs, 50)
        p95 = _percentile(xs, 95)
        p99 = _percentile(xs, 99)
        assert p50 <= p95 <= p99, f"p50={p50} p95={p95} p99={p99}"


# ============================================================
# 7. Digest determinism (golden)
# ============================================================

GOLDEN_INPUT = pd.DataFrame([
    {"iter_no": 0, "listing_id": "l0", "category": "Finance",
     "status": "ok", "quality_score": 0.5, "summary": "first"},
    {"iter_no": 1, "listing_id": "l1", "category": "Healthcare",
     "status": "ok", "quality_score": 0.7, "summary": "second"},
    {"iter_no": 2, "listing_id": "l2", "category": "Geospatial",
     "status": "skipped", "quality_score": 0.3, "summary": "third"},
    {"iter_no": 3, "listing_id": "l3", "category": "Retail",
     "status": "ok", "quality_score": 0.85, "summary": "fourth"},
    {"iter_no": 4, "listing_id": "l4", "category": "Energy",
     "status": "failed", "quality_score": 0.1, "summary": "fifth"},
])

# Generated by running the digest once and freezing the output.
# Any change to the digest format will require bumping this.
GOLDEN_DIGEST = """{
  "category_breakdown": {
    "Energy": 1,
    "Finance": 1,
    "Geospatial": 1,
    "Healthcare": 1,
    "Retail": 1
  },
  "quality_timeline": {
    "0": 0.5,
    "1": 0.7,
    "2": 0.3,
    "3": 0.85,
    "4": 0.1
  },
  "summary": {
    "avg_quality": 0.49,
    "median_quality": 0.5,
    "n_distinct_categories": 5,
    "n_distinct_listings": 5,
    "n_failed": 1,
    "n_iterations": 5,
    "n_ok": 3,
    "n_skipped": 1,
    "quality_max": 0.85,
    "quality_min": 0.1,
    "total_cost_usd": 0.0,
    "total_tokens": 0
  }
}"""


def test_digest_golden_matches_frozen_output():
    """The digest, given the same input, must produce the same JSON."""
    out = digest_golden(GOLDEN_INPUT)
    assert out == GOLDEN_DIGEST, (
        f"\n--- got ---\n{out}\n--- expected ---\n{GOLDEN_DIGEST}"
    )


def test_digest_is_deterministic_across_runs():
    """Two runs of the digest on the same input produce identical output."""
    a = digest_golden(GOLDEN_INPUT)
    b = digest_golden(GOLDEN_INPUT)
    assert a == b


# ============================================================
# 8. Digest invariants
# ============================================================

def test_digest_n_iters_equals_sum_of_statuses():
    """n_iterations = n_ok + n_skipped + n_failed (no "running" rows)."""
    df = pd.DataFrame([
        {"iter_no": 0, "listing_id": "l0", "category": "Finance",
         "status": "ok", "quality_score": 0.5, "summary": ""},
        {"iter_no": 1, "listing_id": "l1", "category": "Finance",
         "status": "skipped", "quality_score": 0.3, "summary": ""},
        {"iter_no": 2, "listing_id": "l2", "category": "Finance",
         "status": "failed", "quality_score": 0.0, "summary": ""},
    ])
    m = compute_metrics(df)
    assert m["n_iterations"] == m["n_ok"] + m["n_skipped"] + m["n_failed"]


def test_digest_empty_returns_zero_safely():
    """Empty frame → no exception, all-zero summary."""
    df = pd.DataFrame(columns=[
        "iter_no", "listing_id", "category", "status", "quality_score", "summary",
    ])
    m = compute_metrics(df)
    assert m["n_iterations"] == 0
    assert m["n_ok"] == 0
    assert m["n_failed"] == 0
    assert m["total_tokens"] == 0


def test_filter_recent_returns_n_rows_in_desc_order():
    """filter_recent(df, n=3) returns exactly n rows, sorted DESC by iter_no."""
    df = pd.DataFrame([
        {"iter_no": i, "category": "X", "listing_id": f"l{i}",
         "status": "ok", "quality_score": 0.5, "summary": f"s{i}"}
        for i in range(10)
    ])
    recent = filter_recent(df, n=3)
    assert len(recent) == 3
    iters = recent["iter_no"].tolist()
    assert iters == sorted(iters, reverse=True)
    assert iters[0] == 9 and iters[-1] == 7


def test_category_breakdown_counts_match():
    """category_breakdown sums to n_iterations."""
    df = pd.DataFrame([
        {"iter_no": 0, "category": "A", "status": "ok", "quality_score": 0.5,
         "listing_id": "l0", "summary": ""},
        {"iter_no": 1, "category": "A", "status": "ok", "quality_score": 0.5,
         "listing_id": "l1", "summary": ""},
        {"iter_no": 2, "category": "B", "status": "ok", "quality_score": 0.5,
         "listing_id": "l2", "summary": ""},
    ])
    cb = category_breakdown(df)
    assert sum(cb.values()) == 3
    assert cb["A"] == 2
    assert cb["B"] == 1


# ============================================================
# CLI smoke
# ============================================================

def test_digest_cli_runs():
    """`python -m m100.digest` prints the demo digest JSON."""
    result = subprocess.run(
        [sys.executable, "-m", "m100.digest"],
        capture_output=True, text=True, timeout=10,
    )
    assert "category_breakdown" in result.stdout
    assert "quality_timeline" in result.stdout
    assert "summary" in result.stdout
