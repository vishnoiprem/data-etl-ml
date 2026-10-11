"""MLflow-style experiment tracker: experiments, runs, params, metrics, model registry.

The shape every ML team has to build at some point: experiments group runs,
runs carry params + metrics + artifacts, models go through a registry with
stage transitions (None -> Staging -> Production -> Archived). This toy
implementation in pure stdlib mirrors the MLflow API.

Meaningful workload:
- 3+ experiments, 30+ runs, each with 3+ params and 5+ metrics.
- Query runs by experiment; compare runs to find the best by loss.
- Register a model; transition through None -> Staging -> Production; verify
  the history is recorded in order.
- Assert invariants: run counts, best-by-loss correctness, stage ordering,
  retrievability of params and metrics.
"""
from __future__ import annotations
import json
import shutil
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

VALID_STAGES = ("None", "Staging", "Production", "Archived")


@dataclass
class Run:
    run_id: str
    experiment_id: str
    project: str
    config: dict = field(default_factory=dict)        # parameters
    metrics: dict = field(default_factory=dict)        # final or last-write scalar metrics
    metric_history: dict = field(default_factory=dict) # metric_name -> list[float]
    artifacts: list[str] = field(default_factory=list)
    status: str = "running"                            # running | finished | failed
    started_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None


@dataclass
class Experiment:
    experiment_id: str
    name: str
    created_at: float = field(default_factory=time.time)
    tags: dict = field(default_factory=dict)


@dataclass
class ModelVersion:
    name: str
    version: int
    run_id: str
    stage: str = "None"
    stage_history: list = field(default_factory=list)  # list[(stage, timestamp)]
    created_at: float = field(default_factory=time.time)


# ---------------------------------------------------------------------------
# Tracker
# ---------------------------------------------------------------------------

class Tracker:
    def __init__(self, storage_dir: str = "./runs"):
        self.storage = Path(storage_dir)
        self.storage.mkdir(parents=True, exist_ok=True)
        self._experiments: dict[str, Experiment] = {}
        self._experiments_by_name: dict[str, str] = {}
        self._runs: dict[str, Run] = {}
        self._models: dict[str, dict[int, ModelVersion]] = {}  # name -> {version: ModelVersion}

    # -- experiments --------------------------------------------------------

    def create_experiment(self, name: str, tags: Optional[dict] = None) -> Experiment:
        if name in self._experiments_by_name:
            return self._experiments[self._experiments_by_name[name]]
        eid = f"exp-{uuid.uuid4().hex[:8]}"
        exp = Experiment(experiment_id=eid, name=name, tags=tags or {})
        self._experiments[eid] = exp
        self._experiments_by_name[name] = eid
        return exp

    def get_experiment(self, name: str) -> Optional[Experiment]:
        eid = self._experiments_by_name.get(name)
        return self._experiments.get(eid) if eid else None

    def list_experiments(self) -> list[Experiment]:
        return list(self._experiments.values())

    # -- runs ---------------------------------------------------------------

    def start_run(
        self,
        experiment_name: str,
        run_id: Optional[str] = None,
        config: Optional[dict] = None,
    ) -> Run:
        exp = self.get_experiment(experiment_name)
        if exp is None:
            exp = self.create_experiment(experiment_name)
        rid = run_id or f"{experiment_name}-{uuid.uuid4().hex[:10]}"
        run = Run(run_id=rid, experiment_id=exp.experiment_id,
                  project=experiment_name, config=config or {})
        self._runs[rid] = run
        self._persist_run(run)
        return run

    def log_params(self, run_id: str, params: dict) -> None:
        r = self._runs[run_id]
        r.config.update(params)
        self._persist_run(r)

    def log(self, run_id: str, metrics: dict, step: Optional[int] = None) -> None:
        r = self._runs[run_id]
        for k, v in metrics.items():
            r.metric_history.setdefault(k, []).append(v)
            r.metrics[k] = v  # last-write-wins scalar
        self._persist_run(r)

    def log_artifact(self, run_id: str, path: str) -> None:
        self._runs[run_id].artifacts.append(path)
        self._persist_run(self._runs[run_id])

    def finish(self, run_id: str, status: str = "finished") -> None:
        r = self._runs[run_id]
        r.status = status
        r.finished_at = time.time()
        self._persist_run(r)

    def get_run(self, run_id: str) -> Optional[Run]:
        return self._runs.get(run_id)

    def query(self, experiment_name: Optional[str] = None, **filters) -> list[Run]:
        out = list(self._runs.values())
        if experiment_name is not None:
            out = [r for r in out if r.project == experiment_name]
        for k, v in filters.items():
            out = [r for r in out if r.config.get(k) == v]
        return out

    def best(self, experiment_name: str, metric: str, mode: str = "min") -> Optional[Run]:
        runs = [r for r in self._runs.values()
                if r.project == experiment_name and metric in r.metrics]
        if not runs:
            return None
        return sorted(runs, key=lambda r: r.metrics[metric], reverse=(mode == "max"))[0]

    def runs_by_experiment(self) -> dict[str, list[Run]]:
        out: dict[str, list[Run]] = {}
        for r in self._runs.values():
            out.setdefault(r.project, []).append(r)
        return out

    # -- model registry -----------------------------------------------------

    def register_model(self, name: str, run_id: str) -> ModelVersion:
        if run_id not in self._runs:
            raise KeyError(f"unknown run_id: {run_id}")
        versions = self._models.setdefault(name, {})
        version = max(versions.keys(), default=0) + 1
        mv = ModelVersion(name=name, version=version, run_id=run_id)
        versions[version] = mv
        return mv

    def transition_model_stage(self, name: str, version: int, stage: str) -> ModelVersion:
        if stage not in VALID_STAGES:
            raise ValueError(f"invalid stage {stage!r}; must be one of {VALID_STAGES}")
        mv = self._models[name][version]
        if stage == mv.stage:
            return mv
        mv.stage_history.append((mv.stage, time.time()))
        mv.stage = stage
        return mv

    def get_model_version(self, name: str, version: int) -> Optional[ModelVersion]:
        return self._models.get(name, {}).get(version)

    def list_model_versions(self, name: str) -> list[ModelVersion]:
        return sorted(self._models.get(name, {}).values(), key=lambda mv: mv.version)

    # -- persistence --------------------------------------------------------

    def _persist_run(self, run: Run) -> None:
        path = self.storage / "runs" / f"{run.run_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(run), indent=2, default=str))


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

def _simulate_training(tr: Tracker, run: Run, epochs: int, base_loss: float) -> None:
    """Simulate a training run that logs 3+ params and 5+ metrics per epoch."""
    lr = run.config["lr"]
    bs = run.config["batch_size"]
    # extra parameters (beyond lr / batch_size) so each run has >= 3 params
    tr.log_params(run.run_id, {
        "optimizer": run.config["optimizer"],
        "weight_decay": run.config["weight_decay"],
        "seed": run.config["seed"],
    })
    last_loss = base_loss
    for epoch in range(epochs):
        # toy dynamics: loss decays; lr too high -> diverges
        decay = (1.0 - 0.1 * epoch) if lr < 5e-3 else (1.0 + 0.2 * epoch)
        last_loss = base_loss * decay
        acc = min(0.99, 0.3 + 0.07 * epoch + (1e-3 / lr))
        precision = acc * 0.95
        recall = acc * 0.93
        f1 = 2 * precision * recall / max(precision + recall, 1e-9)
        tr.log(run.run_id, {
            "loss": last_loss,
            "accuracy": acc,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        })
    tr.log_artifact(run.run_id, f"./models/{run.run_id}.pt")
    tr.finish(run.run_id)


def main() -> int:
    storage = "./_tracker_smoke"
    if Path(storage).exists():
        shutil.rmtree(storage)
    tr = Tracker(storage_dir=storage)

    # ---- Scenario A: create experiments, start runs, log params/metrics ----
    experiment_names = ["rag-eval", "text-classifier", "forecast-lstm"]
    for name in experiment_names:
        tr.create_experiment(name, tags={"team": "ml-platform"})

    # rag-eval: 4 LRs x 3 batch sizes = 12 runs
    rag_count = 0
    for lr in [1e-2, 1e-3, 1e-4, 5e-5]:
        for bs in [16, 32, 64]:
            run = tr.start_run(
                "rag-eval",
                config={"lr": lr, "batch_size": bs, "optimizer": "adamw",
                        "weight_decay": 0.01, "seed": 42},
            )
            _simulate_training(tr, run, epochs=5, base_loss=2.5)
            rag_count += 1

    # text-classifier: 5 runs (mixed optimizers)
    tc_count = 0
    for opt, lr in [("adam", 1e-3), ("sgd", 1e-2), ("adamw", 5e-4),
                    ("rmsprop", 1e-3), ("adam", 3e-4)]:
        run = tr.start_run(
            "text-classifier",
            config={"lr": lr, "batch_size": 32, "optimizer": opt,
                    "weight_decay": 0.001, "seed": 7},
        )
        _simulate_training(tr, run, epochs=5, base_loss=1.8)
        tc_count += 1

    # forecast-lstm: 13 runs (lr sweep)
    fc_count = 0
    for lr in [1e-2, 5e-3, 1e-3, 5e-4, 1e-4]:
        for bs in [16, 32, 64]:
            if fc_count >= 13:
                break
            run = tr.start_run(
                "forecast-lstm",
                config={"lr": lr, "batch_size": bs, "optimizer": "adam",
                        "weight_decay": 0.0, "seed": 1},
            )
            _simulate_training(tr, run, epochs=5, base_loss=3.2)
            fc_count += 1
        if fc_count >= 13:
            break

    total_runs = rag_count + tc_count + fc_count
    runs_by_exp = tr.runs_by_experiment()
    print(f"experiments created: {len(tr.list_experiments())}")
    for name in experiment_names:
        print(f"  {name}: {len(runs_by_exp.get(name, []))} runs")
    print(f"total runs: {total_runs}")

    # ---- Scenario B: query runs by experiment ------------------------------
    rag_runs = tr.query(experiment_name="rag-eval")
    tc_runs = tr.query(experiment_name="text-classifier")
    fc_runs = tr.query(experiment_name="forecast-lstm")
    print(f"query rag-eval: {len(rag_runs)} runs")
    print(f"query text-classifier: {len(tc_runs)} runs")
    print(f"query forecast-lstm: {len(fc_runs)} runs")

    # ---- Scenario C: compare runs, find best by loss ----------------------
    best_per_exp = {}
    for name in experiment_names:
        b = tr.best(name, "loss", mode="min")
        if b is not None:
            best_per_exp[name] = b
            # verify by exhaustive search
            candidate = min(runs_by_exp[name],
                            key=lambda r: r.metrics["loss"])
            assert b.run_id == candidate.run_id, "best() disagreement"
            print(f"best {name}: {b.run_id} loss={b.metrics['loss']:.4f} "
                  f"acc={b.metrics['accuracy']:.3f} config={b.config}")

    # ---- Scenario D: register model, transition stages --------------------
    # pick the best rag-eval run
    prod_candidate = best_per_exp["rag-eval"]
    mv1 = tr.register_model("rag-retriever", prod_candidate.run_id)
    print(f"registered rag-retriever v{mv1.version} (stage={mv1.stage})")

    tr.transition_model_stage("rag-retriever", mv1.version, "Staging")
    tr.transition_model_stage("rag-retriever", mv1.version, "Production")
    # also register a second version from a different run
    second_run = [r for r in rag_runs if r.run_id != prod_candidate.run_id][0]
    mv2 = tr.register_model("rag-retriever", second_run.run_id)
    tr.transition_model_stage("rag-retriever", mv2.version, "Staging")
    tr.transition_model_stage("rag-retriever", mv2.version, "Production")
    tr.transition_model_stage("rag-retriever", mv2.version, "Archived")

    versions = tr.list_model_versions("rag-retriever")
    print(f"model rag-retriever: {len(versions)} versions")
    for v in versions:
        print(f"  v{v.version}: stage={v.stage} transitions={len(v.stage_history)}")

    # ---- Assertions -------------------------------------------------------
    assert len(tr.list_experiments()) == 3, "expected 3 experiments"
    assert total_runs >= 30, f"expected >=30 runs, got {total_runs}"
    assert len(rag_runs) == rag_count, "rag run count mismatch"
    assert len(tc_runs) == tc_count, "tc run count mismatch"
    assert len(fc_runs) == fc_count, "fc run count mismatch"
    # all runs queryable
    assert len(tr.query()) == total_runs, "global query lost runs"
    # each run has >= 3 params and >= 5 metrics
    for r in tr.query():
        assert len(r.config) >= 3, f"{r.run_id} has <3 params"
        assert len(r.metrics) >= 5, f"{r.run_id} has <5 metrics"
    # best by loss is correct (lowest)
    for name in experiment_names:
        b = best_per_exp[name]
        for r in runs_by_exp[name]:
            assert r.metrics["loss"] >= b.metrics["loss"], \
                f"{name}: found a run with lower loss than best"
    # model stage transitions are recorded in order
    prod_v1 = tr.get_model_version("rag-retriever", 1)
    stages_in_order = [start for start, _ in prod_v1.stage_history]
    assert stages_in_order == ["None", "Staging"], \
        f"v1 stage history wrong: {stages_in_order}"
    assert prod_v1.stage == "Production", "v1 should be in Production"
    prod_v2 = tr.get_model_version("rag-retriever", 2)
    stages_v2 = [start for start, _ in prod_v2.stage_history]
    assert stages_v2 == ["None", "Staging", "Production"], \
        f"v2 stage history wrong: {stages_v2}"
    assert prod_v2.stage == "Archived", "v2 should be in Archived"
    # params and metrics retrievable
    sample = tr.query(experiment_name="rag-eval", lr=1e-3)
    assert len(sample) == 3, f"expected 3 runs at lr=1e-3, got {len(sample)}"
    for r in sample:
        assert "accuracy" in r.metrics
        assert "loss" in r.metrics
        assert "optimizer" in r.config

    print("metrics per run: >=5, params per run: >=3")
    print(f"best runs by loss: {[(n, b.run_id, round(b.metrics['loss'], 4)) for n, b in best_per_exp.items()]}")
    print("all model stage transitions: "
          f"v1 {stages_in_order}->Production, v2 {stages_v2}->Archived")
    print("✓ all invariants pass")

    shutil.rmtree(storage)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
