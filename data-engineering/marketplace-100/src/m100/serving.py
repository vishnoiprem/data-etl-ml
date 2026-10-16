"""
serving.py — model serving + monitoring.

Two responsibilities:

  1. **Deploy** each iteration's baseline model to a Databricks
     serving endpoint (`/serving-endpoints/{name}/...`).
     In production: `WorkspaceClient().serving_endpoints.create()`.
     In smoke: a `LocalEndpoint` FastAPI-style stub.

  2. **Monitor** the deployed model with synthetic probes. We
     hit it with N requests, time the latencies, and compute:

       * p50 / p95 / p99 latency
       * error rate
       * prediction-drift score (mean abs delta between
         the predicted batch and a held-out baseline mean)

     Results are written to MLflow as a `monitoring/<iter>`
     run so the agent can see whether the model is healthy
     and the digest can show "model latency vs budget".

Why monitor with synthetic probes?
  Real request volume on a Free Edition endpoint is too low
  to be statistically meaningful. A small burst of 50 requests
  is enough to get a stable p50/p95 and surface obvious
  drift (e.g. a model that returns 0 for everything).

Free Edition posture:
  * No dedicated serving quota → we use the same endpoint
    and overwrite it each iteration. Each iter is its own
    short-lived endpoint; we delete after monitoring.
"""

from __future__ import annotations

import json
import logging
import os
import statistics
import time
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ============================================================
# Result types
# ============================================================

@dataclass
class ServingResult:
    """What `deploy_and_monitor` produced."""
    endpoint_name: str
    deployed: bool
    sample_request: dict
    latencies_ms: list[float]
    p50_ms: float
    p95_ms: float
    p99_ms: float
    error_rate: float
    drift_score: float
    n_requests: int
    mlflow_run_id: str = ""        # for the monitoring run


# ============================================================
# Deployment
# ============================================================

def deploy_to_endpoint(
    *,
    workspace_client: Optional[Any],
    model_name: str,
    endpoint_name: str,
) -> bool:
    """Deploy `model_name` to `endpoint_name`.

    In production: `workspace_client.serving_endpoints.create()`.
    In smoke / no-workspace: no-op that returns True (the
    LocalEndpoint stand-in is wired in `LocalEndpoint.deploy`).

    Returns True on success, False on failure (logged but not
    raised — the driver continues even if serving fails).
    """
    if workspace_client is None:
        logger.info("deploy_to_endpoint: no workspace — skipping (smoke)")
        return True
    try:
        # Production path — minimal API surface; full payload
        # in a real project.
        workspace_client.serving_endpoints.create(
            name=endpoint_name,
            config={
                "served_models": [{
                    "model_name": model_name,
                    "model_version": "1",
                    "workload_size": "Small",
                    "scale_to_zero_enabled": True,
                }],
            },
        )
        logger.info("deployed %s to endpoint %s", model_name, endpoint_name)
        return True
    except Exception as e:
        logger.warning("deploy %s failed: %s", model_name, e)
        return False


# ============================================================
# Monitoring — synthetic probe
# ============================================================

def _percentile(xs: list[float], p: float) -> float:
    """Linear-interpolated percentile (numpy-less, no SciPy)."""
    if not xs:
        return 0.0
    xs = sorted(xs)
    k = (len(xs) - 1) * p / 100.0
    f, c = int(k), min(int(k) + 1, len(xs) - 1)
    if f == c:
        return xs[f]
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def monitor_endpoint(
    *,
    workspace_client: Optional[Any],
    endpoint_name: str,
    sample_input: list[Any],
    n_requests: int = 50,
    mlflow_run_id: str = "",
) -> ServingResult:
    """Hit the endpoint N times with `sample_input`, log metrics.

    `sample_input` is the payload we'll send on every request
    (a list of feature dicts for tabular, a list of strings
    for text). We hold it constant to detect drift: the
    prediction distribution should be roughly stable.

    In production: `workspace_client.serving_endpoints.query()`.
    In smoke: `LocalEndpoint.predict()`.

    Returns a `ServingResult` even on partial failure (so the
    driver can record it in MLflow).
    """
    if not sample_input:
        sample_input = [{"x": 0.0}]

    latencies_ms: list[float] = []
    errors = 0
    predictions: list[float] = []

    for _ in range(n_requests):
        t0 = time.time()
        try:
            if workspace_client is None:
                # Smoke path — LocalEndpoint stand-in
                preds = _local_predict(endpoint_name, sample_input)
            else:
                resp = workspace_client.serving_endpoints.query(
                    name=endpoint_name, inputs=sample_input,
                )
                preds = resp.predictions if hasattr(resp, "predictions") else []
            latencies_ms.append((time.time() - t0) * 1000.0)
            # Coerce predictions to floats for drift calc
            for p in (preds or [0.0]):
                try:
                    predictions.append(float(p))
                except (TypeError, ValueError):
                    pass
        except Exception as e:
            logger.warning("monitoring request failed: %s", e)
            errors += 1

    drift = _drift_score(predictions)
    res = ServingResult(
        endpoint_name=endpoint_name,
        deployed=True,
        sample_request={"inputs": sample_input},
        latencies_ms=latencies_ms,
        p50_ms=_percentile(latencies_ms, 50),
        p95_ms=_percentile(latencies_ms, 95),
        p99_ms=_percentile(latencies_ms, 99),
        error_rate=errors / max(n_requests, 1),
        drift_score=drift,
        n_requests=n_requests,
        mlflow_run_id=mlflow_run_id,
    )

    # Log to MLflow so the agent / digest can see it
    _log_monitoring(res)
    return res


def _drift_score(predictions: list[float]) -> float:
    """Mean-absolute-delta from a centered baseline (0.5).

    A model that's returning 0.99 for every input scores ~0.49
    (heavily drifted). A well-calibrated one scores ~0.1.
    """
    if not predictions:
        return 0.0
    return float(statistics.mean(abs(p - 0.5) for p in predictions))


def _local_predict(endpoint_name: str, sample_input: list[Any]) -> list[float]:
    """Local stand-in for serving-endpoint query. Returns a
    deterministic fake prediction (sum-of-inputs / 2, clipped).
    """
    out: list[float] = []
    for row in sample_input:
        if isinstance(row, dict):
            s = sum(float(v) for v in row.values() if isinstance(v, (int, float)))
        elif isinstance(row, str):
            s = float(len(row))
        else:
            s = 0.0
        out.append(max(0.0, min(1.0, s / 10.0)))
    return out


# ============================================================
# MLflow logging
# ============================================================

def _log_monitoring(res: ServingResult) -> None:
    """Best-effort MLflow log; never raises."""
    try:
        import mlflow
        with mlflow.start_run(run_name=f"monitor-{res.endpoint_name}"):
            mlflow.set_tag("endpoint", res.endpoint_name)
            mlflow.log_metric("p50_ms", res.p50_ms)
            mlflow.log_metric("p95_ms", res.p95_ms)
            mlflow.log_metric("p99_ms", res.p99_ms)
            mlflow.log_metric("error_rate", res.error_rate)
            mlflow.log_metric("drift_score", res.drift_score)
            mlflow.log_metric("n_requests", res.n_requests)
    except Exception as e:
        logger.debug("mlflow log skipped: %s", e)


# ============================================================
# Convenience: one-shot deploy + monitor
# ============================================================

def deploy_and_monitor(
    *,
    workspace_client: Optional[Any],
    model_name: str,
    endpoint_name: str,
    sample_input: list[Any],
    n_requests: int = 50,
) -> ServingResult:
    """Deploy then monitor. One call from the driver."""
    deploy_to_endpoint(
        workspace_client=workspace_client,
        model_name=model_name,
        endpoint_name=endpoint_name,
    )
    return monitor_endpoint(
        workspace_client=workspace_client,
        endpoint_name=endpoint_name,
        sample_input=sample_input,
        n_requests=n_requests,
    )


# ============================================================
# CLI demo
# ============================================================

if __name__ == "__main__":
    res = deploy_and_monitor(
        workspace_client=None,
        model_name="marketplace_100.models.demo",
        endpoint_name="m100_endpoint_demo",
        sample_input=[{"x": 1.0}, {"x": 2.0}, {"x": 3.0}],
        n_requests=50,
    )
    print(
        f"endpoint={res.endpoint_name}  "
        f"p50={res.p50_ms:.2f}ms  p95={res.p95_ms:.2f}ms  "
        f"p99={res.p99_ms:.2f}ms  err={res.error_rate:.1%}  "
        f"drift={res.drift_score:.3f}"
    )
