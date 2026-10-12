# DeepMind-style frontier research pipeline (reproducibility)

Reproducible ML research: dataset versioning, training infra that actually scales, an eval harness I can re-run on last week's commit, and ablation sweeps in config, not in a notebook. The pipeline is the artifact; the model weights are downstream.

## Shape

```
      base config
           │
           ▼
    AblationSweep.sweep(axes={lr: [...], batch: [...]})
           │
           ▼
   list[RunConfig]   ──►   for each:
                              RunRecord.make(config, data_sha, code_sha)
                                         │
                                         ▼
                                 run_id = sha(config | data | code)
                                         │
                                         ▼
                                  run + log metrics
                                         │
                                         ▼
                                  later: re-run from run_id
```

## What I built

- `train/repro.py` — `RunConfig` (with `sha()` over canonical JSON) + `RunRecord.make()` + `AblationSweep`.
- A run is keyed by `(config_sha, data_sha, code_sha)`. Same three SHAs → same `run_id` → reproducible.
- `AblationSweep.sweep(axes)` generates the cartesian product of overrides. `sweep({"lr": [1e-3, 1e-4], "batch_size": [16, 64]})` → 4 runs.
- Smoke test: base config + 3 LR × 2 batch size = 6 runs, each with a unique `run_id`.

## Real numbers

- Reproducibility: identical SHAs → identical run. Verified by re-running on the same data and code.
- Sweep sizes: a 4-axis sweep with 3 values each = 81 runs. Plan for 5-10 minutes per run on a small model; 4-12 hours on a 7B.
- The "three SHAs" pattern is the same as W&B / MLflow / Neptune, with the key difference: this is in your code, not a vendor's service.
- Common pitfall: floating-point non-determinism. Even with `torch.manual_seed(42)`, GPU reductions are non-deterministic. Use `torch.use_deterministic_algorithms(True)` + a deterministic mode.

## What I learned the hard way

- **Config in code, not in notebooks.** A sweep spec in a YAML / Python file is reviewable, version-controlled, and reproducible. A sweep in a notebook is not.
- **The data SHA is the easy one to forget.** You change the dataset, retrain, get better numbers, and you have no idea why. Hash the dataset version.
- **The code SHA is the git commit.** Pin it in the run record. "What code was running?" is the most-asked question 3 months later.
- **Floating-point non-determinism is a real reproducibility killer.** A run that gives loss=2.51 one day and loss=2.53 the next is technically different but practically the same. Decide up-front which metrics need bit-exact reproducibility and which need statistical.

## When to use

- Frontier research where you need to defend your numbers 6 months later.
- Hyperparam sweeps with > 20 runs.
- Cross-team collaboration where reviewers need to re-run your results.

## When NOT to use

- One-off training runs in a notebook.
- Inference (no training, no sweep).

## Run

```bash
pip install -r requirements.txt
make smoke
```
---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
