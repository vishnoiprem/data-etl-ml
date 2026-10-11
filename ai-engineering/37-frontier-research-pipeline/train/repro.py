"""DeepMind-style frontier research pipeline: reproducible runs from config.

Reproducible ML research: dataset versioning, training infra that
actually scales, an eval harness I can re-run on last week's commit,
and ablation sweeps in config, not in a notebook. The pipeline is
the artifact; the model weights are downstream.

The toy captures the run record: every run is keyed by (config_sha,
data_sha, code_sha) so any past run is reproducible.
"""
from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Any


def sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:12]


@dataclass
class RunConfig:
    model: str
    dataset: str
    dataset_version: str
    lr: float
    batch_size: int
    epochs: int
    seed: int
    extra: dict = field(default_factory=dict)

    def canonical_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, default=str)

    def sha(self) -> str:
        return sha(self.canonical_json())


@dataclass
class RunRecord:
    run_id: str                 # sha of all 3 SHAs
    config: RunConfig
    config_sha: str
    data_sha: str               # sha of the dataset version
    code_sha: str               # sha of the training code (git commit)
    metrics: dict = field(default_factory=dict)
    status: str = "pending"
    started_at: float = 0.0
    finished_at: float = 0.0

    @staticmethod
    def make(config: RunConfig, data_sha: str, code_sha: str) -> "RunRecord":
        cfg_sha = config.sha()
        run_id = sha(f"{cfg_sha}|{data_sha}|{code_sha}")
        return RunRecord(run_id=run_id, config=config, config_sha=cfg_sha,
                         data_sha=data_sha, code_sha=code_sha)

    def complete(self, metrics: dict) -> None:
        self.metrics = metrics
        self.status = "completed"


class AblationSweep:
    """Generates config variants from a base config + a sweep spec."""

    def __init__(self, base: RunConfig):
        self.base = base

    def sweep(self, axes: dict[str, list[Any]]) -> list[RunConfig]:
        """axes = {"lr": [1e-3, 1e-4, 1e-5], "batch_size": [16, 64]}. Returns 6 configs."""
        from itertools import product
        keys = list(axes.keys())
        out = []
        for combo in product(*[axes[k] for k in keys]):
            overrides = dict(zip(keys, combo))
            d = asdict(self.base)
            d.update(overrides)
            # Separate "extra" from the known fields so we can pass it as a single kwarg
            known = {"model", "dataset", "dataset_version", "lr", "batch_size", "epochs", "seed", "extra"}
            extra = {k: v for k, v in d.items() if k not in known}
            known_fields = {k: v for k, v in d.items() if k in known and k != "extra"}
            out.append(RunConfig(**known_fields, extra=extra))
        return out


if __name__ == "__main__":
    base = RunConfig(model="llama-3-8b", dataset="c4", dataset_version="2024-09",
                     lr=1e-4, batch_size=32, epochs=3, seed=42)
    sweep = AblationSweep(base)
    configs = sweep.sweep({"lr": [1e-3, 1e-4, 1e-5], "batch_size": [16, 64]})
    print(f"sweep generated {len(configs)} runs")
    data_sha = sha("c4-2024-09-shard-0001")
    code_sha = sha("git-rev-abc123")
    for c in configs:
        rec = RunRecord.make(c, data_sha, code_sha)
        rec.complete({"loss": 2.5, "accuracy": 0.62})
        print(f"  run_id={rec.run_id} lr={c.lr} batch={c.batch_size} cfg_sha={rec.config_sha[:6]}")
