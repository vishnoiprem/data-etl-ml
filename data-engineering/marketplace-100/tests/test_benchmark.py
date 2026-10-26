"""
test_benchmark.py — tests for the end-to-end benchmark.

We don't time the benchmark (that's the bench's job); we
just assert structural invariants:

  * `run()` returns a BenchmarkResult
  * n_iterations matches what was requested
  * Every iteration has the expected fields populated
  * Quality scores are in [0, 1]
  * Cost is non-negative
  * Token counts are non-negative
  * Bandit arms get pulled (no arm starvation after 10 iters
    when there are 10 categories)
  * Stage timings are non-negative
  * `main_cli()` runs without error and emits a JSON summary
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile

import pytest

from m100.benchmark import (
    run,
    BenchmarkResult,
    IterationMetrics,
    StageTiming,
    CATEGORIES,
)


def test_benchmark_runs_with_3_iterations():
    """A short bench is enough to validate the wiring."""
    res = run(n_iterations=3, seed=42)
    assert isinstance(res, BenchmarkResult)
    assert res.n_iterations == 3
    assert len(res.iterations) == 3


def test_benchmark_iterations_have_fields():
    """Each iteration has the expected metrics populated."""
    res = run(n_iterations=3, seed=42)
    for it in res.iterations:
        assert 0.0 <= it.quality_score <= 1.0
        assert it.prompt_tokens >= 0
        assert it.completion_tokens >= 0
        assert it.cost_usd >= 0
        assert it.endpoint_p95_ms >= 0
        assert 0.0 <= it.endpoint_drift <= 0.5
        assert it.status in ("ok", "skipped")
        # stages should be populated
        assert it.stages
        stage_names = {s.name for s in it.stages}
        assert "agent" in stage_names
        assert "serving" in stage_names
        for s in it.stages:
            assert s.duration_ms >= 0


def test_benchmark_cost_aggregates_match_iteration_sum():
    """total_cost_usd == sum of per-iter cost_usd."""
    res = run(n_iterations=5, seed=42)
    summed = sum(it.cost_usd for it in res.iterations)
    assert abs(res.total_cost_usd - summed) < 1e-6


def test_benchmark_token_aggregates_match_iteration_sum():
    """total_prompt_tokens == sum across iters."""
    res = run(n_iterations=5, seed=42)
    assert res.total_prompt_tokens == sum(it.prompt_tokens for it in res.iterations)
    assert res.total_completion_tokens == sum(it.completion_tokens for it in res.iterations)


def test_benchmark_bandit_pulls_all_arms_with_enough_iterations():
    """10 iters across 10 categories: each arm should get at least
    1 pull (no starvation when n_iterations == n_arms)."""
    res = run(n_iterations=len(CATEGORIES), seed=42)
    arms_with_pulls = {
        cat for cat, stats in res.bandit_summary.items()
        if stats.get("pulls", 0) >= 1
    }
    # All 10 categories should have been tried at least once.
    assert arms_with_pulls == set(CATEGORIES)


def test_benchmark_quality_min_max_avg_consistent():
    """quality_min <= avg <= quality_max."""
    res = run(n_iterations=5, seed=42)
    assert res.quality_min <= res.quality_avg <= res.quality_max


def test_benchmark_history_index_grows_with_iterations():
    """history_index_size should match n_iterations after a fresh run."""
    res = run(n_iterations=4, seed=42)
    assert res.history_index_size == 4


def test_benchmark_json_round_trip():
    """asdict() should produce JSON-serializable output."""
    res = run(n_iterations=2, seed=42)
    blob = json.dumps(res.__dict__, indent=2, default=str)
    loaded = json.loads(blob)
    assert loaded["n_iterations"] == 2
    assert len(loaded["iterations"]) == 2


def test_benchmark_cli_runs():
    """`python -m m100.benchmark` should print a summary line."""
    result = subprocess.run(
        [sys.executable, "-m", "m100.benchmark",
         "--iterations", "2", "--seed", "1"],
        capture_output=True, text=True, timeout=60,
    )
    assert "M100 BENCHMARK" in result.stdout
    assert "n_iterations" in result.stdout
    assert "total_usd" in result.stdout
    assert "quality" in result.stdout
