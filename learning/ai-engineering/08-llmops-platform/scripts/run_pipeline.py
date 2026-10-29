"""End-to-end LLMOps pipeline demo.

Runs three scenarios so you can see all branches:
  A) Healthy candidate → ships
  B) Regression       → blocked at eval
  C) Bad rollout      → rolled back at promote
And computes drift on a final synthetic prod stream.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.drift import length_drift, quality_drift_cusum, topic_drift
from src.event_bus import EventBus
from src.orchestrator import run_pipeline
from src.stages import Artifact, promote_canary

console = Console()


def main():
    random.seed(11)
    bus = EventBus()

    # Subscribe a tiny "Slack notifier" to drift alarms
    notifications: list[str] = []
    bus.subscribe("pipeline.drift.alarm",
                  lambda e: notifications.append(f"[ALARM] {e.detail}"))
    bus.subscribe("pipeline.run.rolled_back",
                  lambda e: notifications.append(f"[ROLLBACK] {e.detail}"))

    # Healthy promote: deterministic clean canary so scenario A actually ships
    def healthy_promote(artifact, b):
        from src.stages import StageResult
        rollout = []
        for pct in (5, 25, 100):
            b.emit("pipeline.promote.step", percent=pct, error_rate=0.002, p95_ms=950)
            rollout.append({"percent": pct, "error_rate": 0.002, "p95_ms": 950})
        b.emit("pipeline.promote.completed", final_pct=100)
        return StageResult(name="promote", success=True, output={"rollout": rollout})

    runs = []
    runs.append(("A. healthy",   run_pipeline(
        Artifact("ticket.summarize", "v3", "anthropic.claude-3-5-sonnet-v2"),
        bus, candidate_score=0.86, promote_fn=healthy_promote,
    )))
    # Force a clean regression (delta = -0.05, well below threshold of -0.02)
    runs.append(("B. regression", run_pipeline(
        Artifact("rag.answer", "v9", "anthropic.claude-3-haiku-v1"),
        bus, candidate_score=0.75,   # baseline is 0.80
    )))
    # Force a bad rollout: the canary will see error_rate spike
    def bad_promote(artifact, b):
        random.seed(0)  # deterministic bad telemetry on first step
        return promote_canary(artifact, b)
    runs.append(("C. bad rollout", run_pipeline(
        Artifact("agent.kyc", "v2", "anthropic.claude-3-5-sonnet-v2"),
        bus, candidate_score=0.84,
        promote_fn=bad_promote,
    )))

    table = Table(title="Pipeline runs")
    table.add_column("Scenario", style="cyan")
    table.add_column("Use case")
    table.add_column("Final status", style="bold")
    table.add_column("Stages", style="dim")
    for label, run in runs:
        stages = ", ".join(f"{r.name}={'ok' if r.success else 'fail'}" for r in run.results)
        color = {"shipped": "green", "blocked_eval": "yellow", "rolled_back": "red"}.get(run.final_status, "white")
        table.add_row(label, run.artifact.use_case,
                      f"[{color}]{run.final_status}[/{color}]", stages)
    console.print(table)

    # ── Drift detection on synthetic prod stream ─────────────────────────────
    baseline = {"pricing": 0.4, "billing": 0.3, "feature": 0.2, "other": 0.1}
    current  = {"pricing": 0.2, "billing": 0.2, "feature": 0.3, "other": 0.3}
    td = topic_drift(baseline, current)

    rng = random.Random(2)
    base_lens = [int(rng.gauss(180, 30)) for _ in range(200)]
    curr_lens = [int(rng.gauss(260, 60)) for _ in range(200)]
    ld = length_drift(base_lens, curr_lens)

    quality_history = [0.86] * 30 + [0.78] * 30   # quality dropped halfway
    qd = quality_drift_cusum(quality_history)

    drift = Table(title="Production drift report")
    drift.add_column("Signal", style="cyan")
    drift.add_column("Value", style="bold")
    drift.add_column("Threshold")
    drift.add_column("Alarm", style="bold")
    for r in (td, ld, qd):
        flag = "[red]YES[/red]" if r.alarm else "[green]no[/green]"
        drift.add_row(r.metric, f"{r.value:.3f}", f"{r.threshold:.3f}", flag)
    console.print(drift)

    # Notifications sent
    if notifications:
        console.print(Panel("\n".join(notifications), title="Notifications fired"))

    # Event-bus stats
    by_name: dict[str, int] = {}
    for e in bus.events:
        by_name[e.name] = by_name.get(e.name, 0) + 1
    counts = Table(title=f"Event bus — {len(bus.events)} events")
    counts.add_column("Event")
    counts.add_column("Count", style="bold")
    for k in sorted(by_name):
        counts.add_row(k, str(by_name[k]))
    console.print(counts)


if __name__ == "__main__":
    main()
