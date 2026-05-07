"""Orchestrator that runs ingest → evaluate → promote → observe.

Embeds simple business rules:
  - On evaluate failure: stop (don't attempt to promote).
  - On promote failure: roll back; mark deployment failed.
  - On observe drift: emit alarm; deployment is still considered shipped.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from src.event_bus import EventBus
from src.stages import (
    Artifact, StageResult, evaluate, ingest, observe, promote_canary,
)


@dataclass
class PipelineRun:
    artifact: Artifact
    results: list[StageResult] = field(default_factory=list)
    final_status: str = "pending"

    @property
    def success(self) -> bool:
        return self.final_status == "shipped"


def run_pipeline(
    artifact: Artifact,
    bus: EventBus,
    candidate_score: float | None = None,
    drift_signal: bool = False,
    promote_fn: Callable | None = None,
) -> PipelineRun:
    promote_fn = promote_fn or promote_canary
    run = PipelineRun(artifact=artifact)
    bus.emit("pipeline.run.started", use_case=artifact.use_case)

    # 1. ingest
    r = ingest(artifact, bus); run.results.append(r)
    if not r.success:
        run.final_status = "failed_ingest"
        bus.emit("pipeline.run.failed", stage="ingest", reason=r.error)
        return run

    # 2. evaluate
    r = evaluate(artifact, bus, candidate_score=candidate_score)
    run.results.append(r)
    if not r.success:
        run.final_status = "blocked_eval"
        bus.emit("pipeline.run.blocked", stage="evaluate",
                 reason=r.error, output=r.output)
        return run

    # 3. promote
    r = promote_fn(artifact, bus); run.results.append(r)
    if not r.success:
        run.final_status = "rolled_back"
        bus.emit("pipeline.run.rolled_back", stage="promote", reason=r.error)
        return run

    # 4. observe
    r = observe(artifact, bus, drift_signal=drift_signal); run.results.append(r)
    run.final_status = "shipped"
    bus.emit("pipeline.run.shipped", use_case=artifact.use_case,
             drift_alarm=r.output.get("drift_alarm", False))
    return run
