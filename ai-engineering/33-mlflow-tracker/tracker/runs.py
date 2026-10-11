"""Weights & Biases-style experiment tracker: every run, every metric, queryable.

The "I forgot what hyperparameters I used 3 weeks ago" problem goes
away. Toy in pure stdlib captures the schema: Run -> Config + Metrics
+ Artifacts. Persist to disk; query by metric / config / run id.
"""
from __future__ import annotations
import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional


@dataclass
class Run:
    run_id: str
    project: str
    config: dict = field(default_factory=dict)
    metrics: dict = field(default_factory=dict)
    artifacts: list[str] = field(default_factory=list)   # paths to files
    status: str = "running"        # running | finished | failed
    started_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None


class Tracker:
    def __init__(self, storage_dir: str = "./runs"):
        self.storage = Path(storage_dir)
        self.storage.mkdir(parents=True, exist_ok=True)
        self._runs: dict[str, Run] = {}

    def start_run(self, project: str, run_id: Optional[str] = None, config: Optional[dict] = None) -> Run:
        rid = run_id or f"{project}-{int(time.time() * 1000)}"
        run = Run(run_id=rid, project=project, config=config or {})
        self._runs[rid] = run
        self._persist(run)
        return run

    def log(self, run_id: str, metrics: dict) -> None:
        r = self._runs[run_id]
        # last-write-wins on scalar keys; lists appended
        for k, v in metrics.items():
            if k in r.metrics and isinstance(r.metrics[k], list) and not isinstance(v, list):
                r.metrics[k].append(v)
            else:
                r.metrics[k] = v
        self._persist(r)

    def log_artifact(self, run_id: str, path: str) -> None:
        self._runs[run_id].artifacts.append(path)
        self._persist(self._runs[run_id])

    def finish(self, run_id: str, status: str = "finished") -> None:
        r = self._runs[run_id]
        r.status = status
        r.finished_at = time.time()
        self._persist(r)

    def query(self, **filters) -> list[Run]:
        out = list(self._runs.values())
        for k, v in filters.items():
            out = [r for r in out if r.config.get(k) == v]
        return out

    def best(self, project: str, metric: str, mode: str = "max") -> Optional[Run]:
        runs = [r for r in self._runs.values() if r.project == project and metric in r.metrics]
        if not runs:
            return None
        return sorted(runs, key=lambda r: r.metrics[metric], reverse=(mode == "max"))[0]

    def _persist(self, run: Run) -> None:
        path = self.storage / f"{run.run_id}.json"
        path.write_text(json.dumps(asdict(run), indent=2, default=str))


if __name__ == "__main__":
    import shutil
    storage = "./_tracker_demo"
    if Path(storage).exists():
        shutil.rmtree(storage)
    tr = Tracker(storage_dir=storage)

    # 3 hyperparam sweeps
    for lr in [1e-3, 1e-4, 1e-5]:
        for batch in [16, 64]:
            run = tr.start_run(project="rag-eval", config={"lr": lr, "batch": batch, "model": "llama-3-8b"})
            # simulate 3 epochs
            for epoch in range(3):
                tr.log(run.run_id, {"epoch": epoch, "loss": 2.0 / (1 + epoch) - lr * 10, "recall@10": 0.5 + epoch * 0.1 + lr * 5})
            tr.log_artifact(run.run_id, f"./models/{run.run_id}.pt")
            tr.finish(run.run_id)

    # Find the best run by recall@10
    best = tr.best("rag-eval", "recall@10", mode="max")
    print(f"best run: {best.run_id}, config={best.config}, recall@10={best.metrics['recall@10']:.3f}")

    # Query: all runs with lr=1e-4
    matches = tr.query(lr=1e-4)
    print(f"runs with lr=1e-4: {len(matches)}")

    shutil.rmtree(storage)
