# Weights & Biases-style experiment tracker (toy)

Every run, every hyperparameter, every metric, every artifact — queryable. The "I forgot what hyperparameters I used 3 weeks ago" problem goes away. Toy in stdlib captures the schema: Run -> Config + Metrics + Artifacts. Persist to disk; query by metric / config / run id.

## Shape

```
        start_run(project, config)
                  │
                  ▼
            Run(run_id, project, config={})
                  │
            log(metrics)   ◄──── epoch 0, 1, 2, ...
                  │
            log_artifact(path)  ◄──── model.pt, plot.png
                  │
            finish(status)
                  │
                  ▼
            _persist() → ./runs/{run_id}.json

        ───────────────────────────────

        query(**filters)        best(project, metric, mode)
        (filter by config)      (top run by metric)
```

## What I built

- `tracker/runs.py` — `Run` (config + metrics + artifacts + status) + `Tracker` (start_run / log / log_artifact / finish / query / best).
- `_persist()` writes one JSON per run to a configurable storage dir. Production replaces this with Postgres or S3.
- `query()` filters by config keys; `best()` returns the top run by metric.
- Smoke test: 3 learning rates × 2 batch sizes = 6 runs, 3 epochs each, then queries for `lr=1e-4` and finds the best `recall@10`.

## Real numbers

- 1K runs/project is normal; 10K+ is fine. Postgres handles this trivially; S3 is the bottleneck only if you log a lot of large artifacts.
- Query latency: 10ms on 1K runs with config filter; 100ms on 100K runs (Postgres index needed).
- Schema: `(run_id, project, config jsonb, metrics jsonb, artifacts text[], status, started_at, finished_at)`. Index on `(project, started_at)` and a GIN index on `config` for filter queries.
- W&B production: ~5-10 metrics logged per step × 10K steps × 100 runs/project = 10M rows. ClickHouse handles this; Postgres with care.

## What I learned the hard way

- **The schema is the API.** Once the run schema is set, every dashboard / notebook / report depends on it. Don't change it without a migration.
- **Group runs by project, not by user.** Project-level permissions, project-level quotas, project-level cost attribution.
- **Persist on every log.** Not at the end. A 2-hour run that crashes 1 hour in should still have its first hour of metrics.
- **Artifacts are paths, not blobs.** The tracker stores paths to S3 or local fs. The model weights live somewhere else; the tracker just knows where.
- **Best-run is the most-used query.** Index it: `(project, metric_name, metric_value DESC)`.

## When to use

- You run more than 5 experiments/week and need to compare them.
- Multiple people share experiments and need a single source of truth.
- You need to reproduce a result 6 months later.

## When NOT to use

- Single-experiment, single-user setups (a notebook is enough).
- You need real-time dashboards (use a separate metrics store; this is for query, not push).

## Run

```bash
pip install -r requirements.txt
make smoke
```

---

## What this is NOT

- **Not W&B / MLflow / Neptune.** Those are hosted
  experiment-tracking platforms with a UI, team
  features, and a managed ClickHouse. This is the
  *schema* (Run → Config + Metrics + Artifacts) in
  pure stdlib, so you can see what those platforms
  are doing. Use them in production.
- **Not a real-time metrics store.** The tracker is
  for *query* ("which run had the best recall?"),
  not *push* ("alert me when loss spikes"). For
  real-time, use Prometheus + Grafana.
- **Not a model registry.** The tracker stores
  *artifact paths*; the model registry holds the
  model *metadata + promotion state*. The two
  integrate (the registry points to the artifact
  in S3, the tracker records which run produced
  it), but they're different concerns.
- **Not a substitute for discipline.** The
  "persist on every log" rule is the only thing
  standing between a 2-hour run and a 1-hour
  crash. The schema doesn't enforce it; the
  developer does.

---

## Related directories

- [`../32-llm-eval-harness/`](../32-llm-eval-harness/) —
  the eval framework whose `RunRecord` is the
  per-run row the tracker persists.
- [`../37-frontier-research-pipeline/`](../37-frontier-research-pipeline/) —
  the research pipeline that produces the runs
  the tracker queries.
- [`../17-mlops-control-plane/`](../17-mlops-control-plane/) —
  the deployment + canary + rollback patterns
  that consume the tracker's `best()` query.
- [`../28-rlhf-dpo-train/`](../28-rlhf-dpo-train/) —
  the alignment training whose ablation sweeps
  land as many runs in the tracker.

---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
