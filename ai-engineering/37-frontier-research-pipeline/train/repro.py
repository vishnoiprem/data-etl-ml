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


def deterministic_train(config: RunConfig) -> dict:
    """Mock trainer. Bit-exact reproducible: same config -> same metrics.

    The 'loss' is derived from a small closed-form function of the
    hyperparameters so the surface is realistic (lower lr + bigger batch
    tends to land in a flatter minimum here), and any time we call this
    with the same config we get the same number.
    """
    lr_term = abs(config.lr - 5e-4) * 1000          # optimal at lr=5e-4
    bs_term = abs(config.batch_size - 64) / 64       # optimal at batch=64
    seed_term = (config.seed % 7) * 0.001            # small seed-dependent jitter
    epoch_term = max(0.0, (3 - config.epochs) * 0.05)
    loss = round(2.0 + lr_term + bs_term + seed_term + epoch_term, 4)
    accuracy = round(max(0.0, min(1.0, 0.85 - (loss - 2.0) * 0.1)), 4)
    return {"loss": loss, "accuracy": accuracy, "lr": config.lr,
            "batch_size": config.batch_size, "epochs": config.epochs}


def find_best(runs: list[RunRecord], metric: str = "loss",
              mode: str = "min") -> RunRecord:
    """Return the best run by metric. mode='min' for loss, 'max' for accuracy."""
    if not runs:
        raise ValueError("no runs to compare")
    if mode == "min":
        return min(runs, key=lambda r: r.metrics[metric])
    return max(runs, key=lambda r: r.metrics[metric])


if __name__ == "__main__":
    print("═══ frontier-research-pipeline: reproducible sweep ═══")
    base = RunConfig(model="llama-3-8b", dataset="c4", dataset_version="2024-09",
                     lr=1e-4, batch_size=32, epochs=3, seed=42)

    data_sha = sha("c4-2024-09-shard-0001")
    code_sha = sha("git-rev-abc123")

    # === Scenario A: 3 ablation sweeps, ≥5 config axes, ≥30 runs ===
    sweep_specs = [
        # LR × batch × seed sweep (3×2×2 = 12 runs)
        {"lr": [1e-3, 5e-4, 1e-4], "batch_size": [16, 64], "seed": [42, 7]},
        # LR × epoch × seed sweep (3×2×2 = 12 runs)
        {"lr": [1e-3, 5e-4, 1e-4], "epochs": [2, 4], "seed": [42, 7]},
        # batch × epoch × seed × lr sweep (2×2×2×2 = 16 runs)
        {"batch_size": [16, 64], "epochs": [3, 5], "seed": [42, 7],
         "lr": [5e-4, 1e-4]},
    ]
    all_configs: list[RunConfig] = []
    for spec in sweep_specs:
        sweep = AblationSweep(base)
        cfgs = sweep.sweep(spec)
        all_configs.extend(cfgs)
        # invariant: sweep size == product of axis sizes
        expected = 1
        for v in spec.values():
            expected *= len(v)
        assert len(cfgs) == expected, (
            f"sweep size {len(cfgs)} != product {expected} for spec {spec}"
        )
        print(f"  sweep {list(spec.keys())}: {len(cfgs)} runs "
              f"(expected {expected})")
    print(f"total runs across {len(sweep_specs)} sweeps: {len(all_configs)}")
    assert len(all_configs) >= 30, f"need ≥30 runs, got {len(all_configs)}"

    # === Run all configs and collect RunRecords ===
    runs: list[RunRecord] = []
    for cfg in all_configs:
        rec = RunRecord.make(cfg, data_sha, code_sha)
        rec.metrics = deterministic_train(cfg)
        rec.status = "completed"
        runs.append(rec)
    assert len(runs) == len(all_configs), "run count must equal config count"

    # === Scenario B: run_id determinism ===
    cfg_a = RunConfig(model="m", dataset="d", dataset_version="v1",
                      lr=1e-4, batch_size=32, epochs=3, seed=42)
    cfg_b = RunConfig(model="m", dataset="d", dataset_version="v1",
                      lr=1e-4, batch_size=32, epochs=3, seed=42)
    rec_a = RunRecord.make(cfg_a, data_sha, code_sha)
    rec_b = RunRecord.make(cfg_b, data_sha, code_sha)
    assert rec_a.run_id == rec_b.run_id, (
        f"identical (config, data, code) must yield identical run_id; "
        f"got {rec_a.run_id} != {rec_b.run_id}"
    )
    assert rec_a.config_sha == rec_b.config_sha
    print(f"\n✓ determinism: identical triple → run_id={rec_a.run_id}")

    # SHA uniqueness: within each sweep, no two configs collide (the
    # cartesian-product guarantee). Across sweeps, the same (config,
    # data, code) triple yields the same run_id — which is the whole
    # point of the scheme — so we count unique triples instead of
    # forcing all run_ids to differ.
    run_ids = [r.run_id for r in runs]
    triples = [(r.config_sha, r.data_sha, r.code_sha) for r in runs]
    n_unique_triples = len(set(triples))
    print(f"✓ SHA uniqueness: {n_unique_triples} unique "
          f"(config, data, code) triples across {len(runs)} runs")
    # Per-sweep uniqueness (no two configs in the same sweep share a triple)
    offset = 0
    for spec, cfgs in zip(sweep_specs, [
        AblationSweep(base).sweep(s) for s in sweep_specs
    ]):
        sweep_run_ids = [r.run_id for r in runs[offset:offset + len(cfgs)]]
        assert len(set(sweep_run_ids)) == len(sweep_run_ids), (
            f"within-sweep duplicate run_id in spec {spec}"
        )
        offset += len(cfgs)

    # === Scenario C: find best run by loss ===
    best_by_loss = find_best(runs, metric="loss", mode="min")
    best_by_acc = find_best(runs, metric="accuracy", mode="max")
    # verify: no other run has a strictly lower loss than best_by_loss
    for r in runs:
        assert r.metrics["loss"] >= best_by_loss.metrics["loss"], (
            f"run {r.run_id} has loss {r.metrics['loss']} < "
            f"best {best_by_loss.metrics['loss']}"
        )
    print(f"\n✓ best by loss: run_id={best_by_loss.run_id} "
          f"loss={best_by_loss.metrics['loss']} "
          f"(lr={best_by_loss.config.lr}, batch={best_by_loss.config.batch_size}, "
          f"epochs={best_by_loss.config.epochs}, seed={best_by_loss.config.seed})")
    print(f"✓ best by accuracy: run_id={best_by_acc.run_id} "
          f"acc={best_by_acc.metrics['accuracy']}")

    # === Scenario D: reproducibility — re-run a config, get same metrics ===
    target_cfg = all_configs[0]
    rec1 = RunRecord.make(target_cfg, data_sha, code_sha)
    rec1.metrics = deterministic_train(target_cfg)
    rec2 = RunRecord.make(target_cfg, data_sha, code_sha)
    rec2.metrics = deterministic_train(target_cfg)
    assert rec1.run_id == rec2.run_id, "re-run should yield same run_id"
    assert rec1.metrics == rec2.metrics, (
        f"re-run metrics differ: {rec1.metrics} != {rec2.metrics}"
    )
    print(f"\n✓ reproducibility: re-run of {rec1.run_id} → "
          f"identical metrics {rec1.metrics}")

    # Cross-check determinism on a handful of random runs
    for r in runs[::5]:
        again = RunRecord.make(r.config, data_sha, code_sha)
        again.metrics = deterministic_train(r.config)
        assert again.run_id == r.run_id, f"run_id changed for {r.run_id}"
        assert again.metrics == r.metrics, f"metrics changed for {r.run_id}"
    print(f"✓ reproducibility spot-check: {len(runs[::5])} re-runs identical")

    # === Summary metrics ===
    losses = [r.metrics["loss"] for r in runs]
    print(f"\n═══ summary ═══")
    print(f"  sweeps:           {len(sweep_specs)}")
    print(f"  total runs:       {len(runs)}")
    print(f"  unique run_ids:   {len(set(run_ids))}")
    print(f"  loss min/avg/max: {min(losses):.4f} / "
          f"{sum(losses)/len(losses):.4f} / {max(losses):.4f}")
    print(f"  best run loss:    {best_by_loss.metrics['loss']:.4f}")
    print(f"\n✓ all invariants pass")
