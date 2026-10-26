"""
test_serving.py — tests for model serving + monitoring.

Covers:

  * Percentile math (p50 / p95 / p99) on a known dataset
  * Empty-list / single-element edge cases
  * Drift score: 0.5-centered predictions are low-drift
  * Drift score: extreme predictions are high-drift
  * `monitor_endpoint()` with no workspace returns valid latencies
  * `monitor_endpoint()` reports errors when the workspace raises
  * `deploy_to_endpoint()` is a no-op when no workspace (smoke)
  * End-to-end `deploy_and_monitor()` returns a ServingResult
  * CLI demo runs

The MLflow logging path is best-effort and never raises; we
don't test it directly.
"""

from __future__ import annotations

import math
import statistics
import subprocess
import sys
from unittest.mock import MagicMock

import pytest

from m100.serving import (
    ServingResult,
    _percentile,
    _drift_score,
    _local_predict,
    monitor_endpoint,
    deploy_to_endpoint,
    deploy_and_monitor,
)


# ============================================================
# Percentile
# ============================================================

def test_percentile_known_dataset():
    """p50 of [1..10] = 5.5 (interpolated), p95 ≈ 9.55."""
    xs = list(range(1, 11))
    assert _percentile(xs, 50) == 5.5
    # p95: 1 + (10-1)*0.95 = 9.55
    assert math.isclose(_percentile(xs, 95), 9.55, abs_tol=1e-9)


def test_percentile_single_element():
    """Single element → returns that element for any p."""
    assert _percentile([42.0], 50) == 42.0
    assert _percentile([42.0], 99) == 42.0


def test_percentile_empty_list():
    """Empty list → 0.0 (not an exception)."""
    assert _percentile([], 50) == 0.0
    assert _percentile([], 99) == 0.0


def test_percentile_extremes():
    """p0 = min, p100 = max."""
    xs = [3.0, 1.0, 4.0, 1.0, 5.0, 9.0, 2.0, 6.0]
    assert _percentile(xs, 0) == min(xs)
    assert _percentile(xs, 100) == max(xs)


# ============================================================
# Drift score
# ============================================================

def test_drift_centered_predictions_low():
    """Predictions all near 0.5 → low drift score."""
    preds = [0.5] * 10
    score = _drift_score(preds)
    assert score == 0.0  # exactly 0.5 → abs delta 0


def test_drift_extreme_predictions_high():
    """Predictions all near 0 or 1 → high drift score."""
    preds = [0.0] * 10 + [1.0] * 10
    score = _drift_score(preds)
    # mean abs(p - 0.5) for p in {0, 1} is 0.5
    assert math.isclose(score, 0.5, rel_tol=1e-9)


def test_drift_empty_returns_zero():
    """No predictions → drift = 0.0 (no signal)."""
    assert _drift_score([]) == 0.0


def test_drift_mixed_predictions():
    """A 50/50 mix of 0.3 and 0.7 → drift = 0.2."""
    preds = [0.3] * 5 + [0.7] * 5
    score = _drift_score(preds)
    assert math.isclose(score, 0.2, rel_tol=1e-9)


# ============================================================
# Local predict
# ============================================================

def test_local_predict_dict_input():
    """Dict rows: predict on sum-of-values / 10, clipped to [0,1]."""
    out = _local_predict("e", [{"x": 5.0, "y": 5.0}])
    assert out == [1.0]  # 10/10 = 1.0
    out2 = _local_predict("e", [{"x": 1.0}])
    assert out2 == [0.1]  # 1/10 = 0.1


def test_local_predict_string_input():
    """String rows: predict on len / 10."""
    out = _local_predict("e", ["hello"])
    assert out == [0.5]  # len 5 / 10


def test_local_predict_clamps_to_unit_interval():
    """Negative or huge values are clipped to [0, 1]."""
    out = _local_predict("e", [{"x": -100.0}])
    assert out == [0.0]
    out2 = _local_predict("e", [{"x": 999.0}])
    assert out2 == [1.0]


# ============================================================
# monitor_endpoint (no workspace)
# ============================================================

def test_monitor_endpoint_no_workspace_runs():
    """With no workspace_client, we fall through to local predict."""
    res = monitor_endpoint(
        workspace_client=None,
        endpoint_name="ep",
        sample_input=[{"x": 1.0}, {"x": 2.0}],
        n_requests=20,
    )
    assert isinstance(res, ServingResult)
    assert res.n_requests == 20
    assert len(res.latencies_ms) == 20
    assert res.error_rate == 0.0  # local predict never raises
    assert 0.0 <= res.drift_score <= 0.5


def test_monitor_endpoint_uses_default_input_when_empty():
    """If sample_input is empty, we substitute a placeholder."""
    res = monitor_endpoint(
        workspace_client=None,
        endpoint_name="ep",
        sample_input=[],
        n_requests=5,
    )
    assert res.n_requests == 5
    assert res.error_rate == 0.0


def test_monitor_endpoint_records_errors_when_workspace_raises():
    """If workspace_client.serving_endpoints.query raises, the
    error is counted (not propagated)."""
    ws = MagicMock()
    ws.serving_endpoints.query.side_effect = RuntimeError("boom")
    res = monitor_endpoint(
        workspace_client=ws,
        endpoint_name="ep",
        sample_input=[{"x": 1.0}],
        n_requests=10,
    )
    assert res.n_requests == 10
    assert res.error_rate == 1.0  # every request failed
    assert res.latencies_ms == []  # none succeeded


# ============================================================
# deploy_to_endpoint
# ============================================================

def test_deploy_to_endpoint_no_workspace_returns_true():
    """No workspace → no-op success."""
    assert deploy_to_endpoint(
        workspace_client=None,
        model_name="m",
        endpoint_name="ep",
    ) is True


def test_deploy_to_endpoint_failure_returns_false():
    """A raising workspace_client yields False (not raised)."""
    ws = MagicMock()
    ws.serving_endpoints.create.side_effect = RuntimeError("quota")
    ok = deploy_to_endpoint(
        workspace_client=ws,
        model_name="m",
        endpoint_name="ep",
    )
    assert ok is False


# ============================================================
# deploy_and_monitor (one-shot)
# ============================================================

def test_deploy_and_monitor_returns_result():
    """End-to-end smoke (no workspace) returns a ServingResult."""
    res = deploy_and_monitor(
        workspace_client=None,
        model_name="m100.models.demo",
        endpoint_name="m100_endpoint_demo",
        sample_input=[{"x": 1.0}],
        n_requests=10,
    )
    assert res.endpoint_name == "m100_endpoint_demo"
    assert res.n_requests == 10
    assert res.p50_ms >= 0.0
    assert res.p95_ms >= res.p50_ms


# ============================================================
# CLI demo
# ============================================================

def test_cli_demo_runs():
    """`python -m m100.serving` should print the metrics line."""
    result = subprocess.run(
        [sys.executable, "-m", "m100.serving"],
        capture_output=True, text=True, timeout=15,
    )
    assert "endpoint=" in result.stdout
    assert "p50=" in result.stdout
    assert "p95=" in result.stdout
    assert "drift=" in result.stdout
