from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.drift import kl_divergence, length_drift, quality_drift_cusum, topic_drift
from src.event_bus import EventBus
from src.orchestrator import run_pipeline
from src.stages import Artifact


def test_event_bus_subscribers_called():
    bus = EventBus()
    seen: list[str] = []
    bus.subscribe("foo", lambda e: seen.append(e.detail["x"]))
    bus.emit("foo", x="hello")
    assert seen == ["hello"]
    assert len(bus.events) == 1


def test_kl_zero_for_equal_distributions():
    p = {"a": 0.5, "b": 0.5}
    assert abs(kl_divergence(p, p)) < 1e-6


def test_topic_drift_alarms_when_distributions_diverge():
    baseline = {"x": 0.9, "y": 0.1}
    current  = {"x": 0.1, "y": 0.9}
    r = topic_drift(baseline, current, threshold=0.2)
    assert r.alarm is True


def test_quality_cusum_alarms_on_decline():
    scores = [0.9] * 5 + [0.6] * 30
    r = quality_drift_cusum(scores)
    assert r.alarm is True


def test_pipeline_blocks_eval_regression():
    bus = EventBus()
    art = Artifact("uc", "v1", "m")
    run = run_pipeline(art, bus, candidate_score=0.50)
    assert run.final_status == "blocked_eval"
    assert any(e.name == "pipeline.run.blocked" for e in bus.events)


def test_pipeline_ships_healthy_candidate():
    bus = EventBus()
    # We use a deterministic promote stub that doesn't trigger rollback
    from src.stages import StageResult, Artifact
    def fake_promote(art, b):
        b.emit("pipeline.promote.completed", final_pct=100)
        return StageResult(name="promote", success=True, output={})
    art = Artifact("uc", "v1", "m")
    run = run_pipeline(art, bus, candidate_score=0.90, promote_fn=fake_promote)
    assert run.final_status == "shipped"
