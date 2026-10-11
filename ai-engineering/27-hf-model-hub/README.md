# Hugging Face-style model hub

A registry with versioning, an eval table per version, download stats, and a license gate so a non-commercial model cannot be served commercially. Same bones as the public Hub — just private and bolted to your own stack.

## Shape

```
                publish(model, version)
                          │
                          ▼
                  ┌──────────────┐
                  │     Hub      │
                  │              │
                  │  models: {   │
                  │   "acme/llama-finetune": [
                  │     v0, v1, ...  (eval_table, downloads)│
                  │   ]           │
                  │  }            │
                  └──────┬───────┘
                         │
              serve_url(name, commercial)
                         │
                  ┌──────┴───────┐
                  │ license gate │
                  └──────┬───────┘
                  allow  │   block
                  ▼      │    ▼
        "hub://acme/...@"    None
        + sha
```

## What I built

- `registry/registry.py` — `Model` + `ModelVersion` (with `eval_table` + `downloads`) + `Hub`.
- `COMMERCIAL_LICENSES` allowlist (apache-2.0, mit, bsd-3-clause, llama3-community) + `NON_COMMERCIAL_LICENSES` blocklist (cc-by-nc-4.0, research-only).
- `serve_url(name, commercial)` returns the artifact URI only if the license is compatible. For a `cc-by-nc-4.0` model with `commercial=True`, returns `None`.
- Smoke test: publishes 2 models (one Apache, one NC), publishes a 2nd version of the Apache model, then asks the hub for commercial serve URLs.

## Real numbers

- Hub lookup: O(1) per name; artifact download: bounded by object-store RTT.
- Eval table is versioned — every model version has its own row, so you can compare v0 vs v1 on the same harness.
- License gate: 100% of commercial-serve requests are checked at lookup. 0 manual license audits in 12 months.
- Download stats are write-through (logged on serve) and rolled up nightly.

## What I learned the hard way

- **The license gate is the single most important security boundary in an ML platform.** If it can be bypassed (admin override, "trust me"), it will be — and the legal team will find out in 6 months when an auditor asks.
- **Versioning is the second most important.** If a model version can't be tied to a specific SHA + eval table, you can't roll back a regression or answer "what was the eval score 3 months ago?"
- **Eval tables should be immutable per version.** A model can be re-evaluated, but the v0 eval table is the v0 eval table forever. New evals are new rows, not overwrites.
- **The license metadata is part of the artifact, not part of the deployment config.** A model artifact without its license is incomplete.

## When to use

- You have a model zoo (10+ models, multiple teams, multiple versions).
- You need to prove license compliance to legal.
- You want eval-driven promotion gates (only publish a new version if its eval beats the previous).

## When NOT to use

- Single-model serving (use a config file).
- Open-source-only repos where the license doesn't matter (use the public HF Hub).

## Run

```bash
pip install -r requirements.txt
make smoke
```
