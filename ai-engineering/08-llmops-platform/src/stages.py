"""Pipeline stages: ingest → evaluate → promote → observe.

Designed to be composable. Each stage:
  - takes an artifact
  - emits structured events
  - returns a stage result with success/failure

Failure short-circuits the pipeline; the orchestrator decides whether to
auto-rollback.
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Any

from src.event_bus import EventBus


@dataclass
class StageResult:
    name: str
    success: bool
    output: dict = field(default_factory=dict)
    error: str | None = None
    duration_ms: int = 0


@dataclass
class Artifact:
    """A unit moving through the pipeline."""
    use_case: str
    prompt_version: str
    model_id: str
    metadata: dict = field(default_factory=dict)


# ─────────────────────────── Stage 1: ingest ─────────────────────────────────

def ingest(artifact: Artifact, bus: EventBus) -> StageResult:
    t0 = time.time()
    bus.emit("pipeline.ingest.started", use_case=artifact.use_case,
             prompt_version=artifact.prompt_version, model_id=artifact.model_id)
    # In production: write to prompt registry, S3 manifest, version metadata
    artifact.metadata["registered_at"] = time.time()
    bus.emit("pipeline.ingest.completed", use_case=artifact.use_case)
    return StageResult(name="ingest", success=True, output={"registered": True},
                       duration_ms=int((time.time() - t0) * 1000))


# ─────────────────────────── Stage 2: evaluate ───────────────────────────────

def evaluate(artifact: Artifact, bus: EventBus,
             baseline_score: float = 0.80, candidate_score: float | None = None,
             threshold: float = 0.02) -> StageResult:
    """Stand-in eval. In production this calls the Project-4 harness on
    SageMaker Pipelines and returns metrics+verdicts.
    """
    t0 = time.time()
    bus.emit("pipeline.evaluate.started", use_case=artifact.use_case)
    if candidate_score is None:
        # Simulate: lift between -3pp and +6pp
        candidate_score = baseline_score + random.uniform(-0.03, 0.06)
    delta = candidate_score - baseline_score
    regression = delta < -threshold

    bus.emit("pipeline.evaluate.completed",
             baseline=baseline_score, candidate=candidate_score, delta=delta,
             regression=regression)

    return StageResult(
        name="evaluate", success=not regression,
        output={"baseline": baseline_score, "candidate": candidate_score, "delta": delta},
        error=("regression" if regression else None),
        duration_ms=int((time.time() - t0) * 1000),
    )


# ─────────────────────────── Stage 3: promote ────────────────────────────────

def promote_canary(artifact: Artifact, bus: EventBus,
                   stages: tuple[int, ...] = (5, 25, 100)) -> StageResult:
    """Multi-stage canary. At each step we sample synthetic telemetry; if
    error-rate spikes beyond a threshold, auto-rollback.
    """
    t0 = time.time()
    bus.emit("pipeline.promote.started", use_case=artifact.use_case, stages=stages)

    rollout: list[dict] = []
    rolled_back = False
    for pct in stages:
        # Synthetic telemetry: error_rate and p95
        error_rate = random.uniform(0.001, 0.012)
        p95_ms = random.randint(900, 1900)
        bus.emit("pipeline.promote.step",
                 percent=pct, error_rate=error_rate, p95_ms=p95_ms)
        rollout.append({"percent": pct, "error_rate": error_rate, "p95_ms": p95_ms})
        if error_rate > 0.01 or p95_ms > 1800:
            bus.emit("pipeline.promote.rollback",
                     percent=pct, reason=f"error_rate={error_rate:.3f} p95={p95_ms}ms")
            rolled_back = True
            break

    if rolled_back:
        return StageResult(name="promote", success=False, output={"rollout": rollout},
                           error="auto-rollback triggered",
                           duration_ms=int((time.time() - t0) * 1000))
    bus.emit("pipeline.promote.completed", final_pct=stages[-1])
    return StageResult(name="promote", success=True, output={"rollout": rollout},
                       duration_ms=int((time.time() - t0) * 1000))


# ─────────────────────────── Stage 4: observe ────────────────────────────────

def observe(artifact: Artifact, bus: EventBus, drift_signal: bool = False) -> StageResult:
    """Wire up production observers and run an initial drift check."""
    t0 = time.time()
    bus.emit("pipeline.observe.started", use_case=artifact.use_case)
    if drift_signal:
        bus.emit("pipeline.drift.alarm",
                 use_case=artifact.use_case,
                 kind="topic_drift",
                 details={"kl_divergence": 0.31, "threshold": 0.20})
    bus.emit("pipeline.observe.completed", drift_alarm=drift_signal)
    return StageResult(name="observe", success=True,
                       output={"drift_alarm": drift_signal},
                       duration_ms=int((time.time() - t0) * 1000))
