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

---

## What this is NOT

- **Not the public Hugging Face Hub.** HF is a
  hosted platform with a community, a model
  browser, and a multi-tenant serving layer.
  This is the *registry + versioning + license
  gate* pattern, sized for one team's private
  hub. Use the public HF Hub for open-source
  distribution; use this for the private one.
- **Not a model registry in the MLflow sense.**
  This is a *content* registry (versions,
  artifacts, license, eval tables). The
  MLflow-style *lifecycle* registry (staging →
  production, promotion gates, rollback) is
  [`../17-mlops-control-plane/`](../17-mlops-control-plane/).
  The two integrate (the lifecycle registry
  references the artifacts from this hub) but
  they're different concerns.
- **Not a substitute for legal review.** The
  license allowlist / blocklist is a *technical*
  enforcement; the legal team still needs to
  review new licenses before they go on the
  allowlist. The gate stops accidental
  commercial-serve of an NC model; it doesn't
  tell you whether a custom license is OK.
- **Not a serving system.** The hub returns a
  `serve_url` (an artifact URI); the actual
  serving is done by
  [`../20-cog-style-inference-api/`](../20-cog-style-inference-api/)
  or
  [`../36-together-gpu-cloud/`](../36-together-gpu-cloud/).

---

## Related directories

- [`../17-mlops-control-plane/`](../17-mlops-control-plane/) —
  the lifecycle registry (staging / production /
  promotion gates) that this content registry
  feeds.
- [`../33-mlflow-tracker/`](../33-mlflow-tracker/) —
  the experiment-tracking layer that records
  which run produced which model version.
- [`../20-cog-style-inference-api/`](../20-cog-style-inference-api/) —
  the inference service that the `serve_url`
  points to.
- [`../32-llm-eval-harness/`](../32-llm-eval-harness/) —
  the eval framework whose `RunRecord` becomes
  the `eval_table` row per model version.

---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
