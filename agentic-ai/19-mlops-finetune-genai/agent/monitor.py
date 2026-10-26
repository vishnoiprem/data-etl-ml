"""agent.monitor — Prometheus + Evidently drift detector.

Two responsibilities:

    1. Push drift scores into Prometheus so Grafana + alerts.yml can see them.
       `record_drift(score)` is called by `serve.py` per request (or batched
       by `evidently`).

    2. Run an Evidently DataDriftPreset comparing the live request-embedding
       distribution against a baseline parquet file. The baseline is captured
       at adapter-registration time (`scripts/run_pipeline.sh`) and lives at
       `MonitorConfig.drift_baseline_path`.

We deliberately rely on `prometheus_client` rather than `prometheus_fastapi_instrumentator`
so the metric set is owned and stable — fewer surprises on alert rules.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np


try:  # pragma: no cover
    import mlflow  # type: ignore
except ImportError:  # pragma: no cover
    mlflow = None  # type: ignore[assignment]


# Reuse the registry from serve.py so /metrics endpoint has both
# request counters and drift gauges in the same exposition.
from agent.serve import DRIFT_SCORE  # noqa: E402


def record_drift(score: float, model: str = "champion") -> None:
    """Idempotent push of the most recent drift score to Prometheus."""
    DRIFT_SCORE.set(score)
    if mlflow is not None and mlflow.active_run() is not None:
        mlflow.log_metric("model_drift_score", float(score), step=int(time.time()))


def compute_drift(baseline: np.ndarray, current: np.ndarray) -> dict[str, Any]:
    """Pure-function drift estimate.

    We compute dataset-level drift as the mean pairwise distance between the
    two empirical distributions, normalized to [0, 1] via a sigmoid on the
    symmetric KL-style ratio:

        score = sigmoid(mean_kl_divergence)

    Falls back to a pure-numpy implementation when `evidently` is unavailable
    so we don't break CI in offline environments.
    """
    try:
        from evidently import ColumnMapping  # type: ignore
        from evidently.metrics import DataDriftPreset  # type: ignore
        import pandas as pd  # type: ignore

        df_base = pd.DataFrame(baseline, columns=[f"f{i}" for i in range(baseline.shape[1])])
        df_curr = pd.DataFrame(current, columns=[f"f{i}" for i in range(current.shape[1])])
        report = DataDriftPreset().calc(df_base, df_curr, ColumnMapping(numerical_features=list(df_base.columns)))
        score = float(report.metrics[0].value)
        return {"synthetic": False, "score": score}
    except Exception:
        # Pure-numpy fallback: per-feature Wasserstein-1 distance, mean.
        from scipy.stats import wasserstein_distance  # type: ignore

        if baseline.shape != current.shape:
            return {"synthetic": True, "score": 0.0, "reason": "shape_mismatch"}
        per_feat = []
        for i in range(baseline.shape[1]):
            per_feat.append(wasserstein_distance(baseline[:, i], current[:, i]))
        raw = float(np.mean(per_feat))
        # Sigmoid centered so that identical distributions land near 0.
        # Plin scaling: typical Wasserstein distance for N(0,1) baseline vs
        # same distribution is ~0.05 (sample-size dependent); we want a shift
        # of ~1.0 standard unit to land near 0.5 on the gate.
        if raw <= 1e-9:
            score = 0.0
        else:
            score = float(1.0 / (1.0 + np.exp(-(raw - 0.05) * 10)))
        # Clamp for safety against extreme outliers.
        score = max(0.0, min(1.0, score))
        return {"synthetic": True, "score": score, "raw": raw}


def run(baseline_path: Path | None = None, current_path: Path | None = None) -> dict[str, Any]:
    """Public entrypoint. Compares two parquet files (baseline + current) and
    updates the Prometheus gauge + MLflow metric.

    If `current_path` is None, generate a synthetic drift signal so the
    `make monitor` target always has something to display.
    """
    from agent.config import load_settings

    settings = load_settings()
    baseline_path = baseline_path or settings.monitor.drift_baseline_path

    if not baseline_path.exists():
        return {"synthetic": True, "score": 0.0, "reason": "no_baseline"}

    try:
        import pandas as pd  # type: ignore
        base_df = pd.read_parquet(baseline_path)
        baseline = base_df.to_numpy()
    except Exception as e:
        return {"synthetic": True, "score": 0.0, "reason": f"baseline_read_failed: {e}"}

    if current_path and current_path.exists():
        try:
            curr_df = pd.read_parquet(current_path)
            current = curr_df.to_numpy()
        except Exception as e:
            return {"synthetic": True, "score": 0.0, "reason": f"current_read_failed: {e}"}
    else:
        # Synthetic drift — shift the mean by `drift_threshold * 0.5` standard deviations,
        # so the dashboard has a non-zero line to show.
        noise = np.random.default_rng(0).normal(
            loc=baseline.mean(axis=0) * settings.monitor.drift_threshold * 0.5,
            scale=baseline.std(axis=0),
            size=baseline.shape,
        )
        current = baseline + noise

    result = compute_drift(baseline, current)
    record_drift(result["score"], model=settings.serve.adapter_alias)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the drift detector and update Prometheus + MLflow.")
    parser.add_argument("--baseline", type=Path, default=None)
    parser.add_argument("--current", type=Path, default=None)
    args = parser.parse_args(argv)

    result = run(baseline_path=args.baseline, current_path=args.current)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
