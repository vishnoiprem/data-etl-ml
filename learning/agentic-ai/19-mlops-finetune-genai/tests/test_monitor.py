"""Tests for `agent.monitor`.

Two things to verify:
  1. The drift score is bounded to [0, 1] (Prometheus exposes a Gauge — values
     outside this range are user errors).
  2. The Prometheus registry is module-shared with `agent.serve` so the
     /metrics endpoint reports both sets.
"""

from __future__ import annotations

import importlib
import sys

import numpy as np
import pytest

from tests.conftest import requires_scipy


class TestComputeDrift:
    @requires_scipy
    def test_identical_distributions_drift_near_zero(self):
        from agent.monitor import compute_drift

        rng = np.random.default_rng(0)
        baseline = rng.normal(size=(128, 8))
        result = compute_drift(baseline, baseline.copy())
        assert result["score"] == pytest.approx(0.0, abs=0.05)

    @requires_scipy
    def test_shifted_distributions_drift_near_one(self):
        from agent.monitor import compute_drift

        rng = np.random.default_rng(0)
        baseline = rng.normal(size=(256, 8))
        # Big shift + bigger spread
        current = baseline + rng.normal(scale=4.0, size=baseline.shape) + 5.0
        result = compute_drift(baseline, current)
        assert 0.0 <= result["score"] <= 1.0
        assert result["score"] > 0.5

    @requires_scipy
    def test_score_bounded_0_to_1(self):
        """Whatever the inputs, the score must be a probability."""
        from agent.monitor import compute_drift

        rng = np.random.default_rng(1)
        baseline = rng.normal(size=(64, 4))
        # Pathological input — far-apart means.
        current = baseline + 100.0
        result = compute_drift(baseline, current)
        assert 0.0 <= result["score"] <= 1.0

    def test_returns_dict(self):
        from agent.monitor import compute_drift

        rng = np.random.default_rng(0)
        baseline = rng.normal(size=(32, 4))
        # numpy fallback path if scipy isn't present should still return a dict
        result = compute_drift(baseline, baseline + rng.normal(scale=0.1, size=baseline.shape))
        assert isinstance(result, dict)
        assert "score" in result


class TestRecordDrift:
    def test_pushes_to_gauge(self):
        """`record_drift` updates the Prometheus gauge that `serve.py` re-exports."""
        from agent import monitor as monitor_module
        from agent.serve import DRIFT_SCORE

        monitor_module.record_drift(0.42, model="unit-test")
        # Prometheus collectors don't expose a "current value" without a server,
        # but we can at least confirm the gauge object is shared.
        assert DRIFT_SCORE is monitor_module.DRIFT_SCORE


class TestRun:
    def test_no_baseline_returns_synthetic(self, tmp_path):
        """The run() entrypoint must not crash when the baseline file is absent —
        otherwise the Grafana dashboard can't be wired on a fresh install."""
        from agent.config import load_settings
        from agent.monitor import run

        load_settings.cache_clear()
        result = run(baseline_path=tmp_path / "nonexistent.parquet")
        assert result["synthetic"] is True
        assert "no_baseline" in result["reason"]

    def test_synthetic_drift_signal_when_baseline_present(self, tmp_path):
        from agent.config import load_settings
        from agent.monitor import run
        import pandas as pd
        import numpy as np

        rng = np.random.default_rng(0)
        df = pd.DataFrame(rng.normal(size=(64, 4)), columns=[f"f{i}" for i in range(4)])
        baseline = tmp_path / "baseline.parquet"
        df.to_parquet(baseline)

        load_settings.cache_clear()
        result = run(baseline_path=baseline)
        assert "score" in result
        assert 0.0 <= result["score"] <= 1.0


class TestRegistrySharing:
    def test_monitor_uses_serve_registry(self):
        """If the registries split, Grafana would silently drop drift_score."""
        import agent.monitor
        import agent.serve
        assert agent.monitor.DRIFT_SCORE is agent.serve.DRIFT_SCORE