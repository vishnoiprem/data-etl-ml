# Marketplace 100 — autonomous Databricks agent over Marketplace

> **100 marketplace datasets. 1 self-driving agent. Zero
> Airflow.** An end-to-end Databricks-native pipeline that
> pulls a fresh asset from the Databricks Marketplace every
> iteration, ingests it via Auto Loader / COPY INTO,
> transforms it with a Lakeflow Declarative Pipeline, runs a
> baseline ML experiment with MLflow, lets a Mosaic AI
> agent score the result and pick the next category, and
> writes the ops log to **Lakebase** — the Postgres-
> compatible lakehouse database. 100 iterations, 30 days,
> Free Edition, fully agentic.

The portfolio piece: a live Databricks App that shows the
running digest, a per-iteration Delta table, and an MLflow
experiment list. The point isn't the numbers — it's
proving that the **whole loop runs without a human in the
seat**.

---

## What I built

- `src/m100/marketplace_client.py` — wraps the
  `/api/2.1/marketplace-consumer` REST API. Search,
  detail, install, fulfillments. Handles PAT auth,
  pagination, and rate-limit backoff.
- `src/m100/ingest.py` — `COPY INTO` for static
  fulfillment files, **Auto Loader** (`cloudFiles`) for
  streaming sources. Every Delta table registers in
  Unity Catalog under `marketplace_100.bronze.<id>`.
- `src/m100/dlt_pipeline.py` — Lakeflow Declarative
  Pipeline definitions: bronze → silver → gold with
  expectations (DQ rules) and a per-table quality
  score.
- `src/m100/mlops.py` — baseline ML (LightGBM
  classifier for tabular, sentence-transformer retrieval
  for text). Logs params / metrics / artifacts to
  MLflow, registers the model in Unity Catalog with a
  `@Champion` alias.
- `src/m100/agent.py` — **Mosaic AI Agent Framework**
  `ChatAgent` subclass. Calls the Foundation Model API
  (`databricks-meta-llama-3.3-70b-instruct`) with a
  tool-use schema. The agent introspects its own MLflow
  metrics, returns a JSON `{summary, quality_score,
  next_category, retry?}`. Four registered tools:
  `profile_table`, `get_mlflow_metrics`,
  `inspect_dlt_expectations`, **`query_history`** (the
  last one does semantic search over its own prior
  iterations via Vector Search in production, a local
  numpy index in dev).
- `src/m100/bandit.py` — **UCB1 multi-armed bandit**
  (Auer, Cesa-Bianchi, Fischer 2002) over the 10
  marketplace categories. The agent's `next_category`
  override is blended in with a 3-iter cooldown so the
  driver doesn't flip-flop. State persists to Lakebase
  so we don't reset to zero on every boot.
- `src/m100/dqx.py` — **Databricks DQX**-style data
  quality with three tiers (`WARN` / `DROP` /
  `QUARANTINE`) and a per-table quality score
  `1 - (drop_rate + 0.5 * quarantine_rate)`. Side
  outputs go to `silver_quarantine` and `silver_warn`
  Delta tables.
- `src/m100/history_search.py` — **Vector Search**
  index over the agent's iteration summaries.
  Production: Databricks Vector Search endpoint
  (`m100_history_endpoint`) with
  `sentence-transformers/all-MiniLM-L6-v2` embeddings.
  Dev: a local numpy index in `.m100_history/`.
- `src/m100/serving.py` — **Model serving + monitoring**.
  Deploys each iteration's baseline to a (short-lived)
  serving endpoint, then runs a 50-request synthetic
  probe to capture p50 / p95 / p99 latency, error rate,
  and a 0.5-centered drift score. Results land in
  MLflow as a `monitor-<endpoint>` run.
- `src/m100/cost.py` — **Cost telemetry + budget guard**.
  Every FM API call is priced (per-token, 5 models in
  the table) and recorded to a `CostLedger`. The
  `BudgetGuard` raises `BudgetExceeded` if the driver
  burns past the daily / hourly / DBU caps (Free
  Edition defaults: $5/day, 200k tokens/window, 5
  DBU/day). Catches a runaway loop before the workspace
  does.
- `src/m100/benchmark.py` — end-to-end benchmark
  runner. Hits every component (bandit, DQX, agent,
  history, cost, serving) on canned but realistic
  data, emits a JSON of measured numbers. `make bench`.
- `src/m100/lakebase.py` — Postgres-compatible Lakebase
  connection. Persists per-iteration state, ops log,
  bandit pulls, and DQX quarantine counts. Falls back
  to a Delta table if Lakebase is not available in the
  region.
- `src/m100/driver.py` — the 100-iteration driver.
  Resumes from Delta on crash, self-evaluates on
  `quality_score < 0.4`, configurable inter-iteration
  sleep, calls `BudgetGuard.check()` at the top of
  every iter.
- `databricks.yml` — Databricks Asset Bundle. Defines
  the driver Job, the Lakeflow pipeline, the Lakebase
  instance, and the digest Databricks App.
- `dashboards/digest_app/` — Streamlit app that reads
  the iterations Delta table + Lakebase ops log and
  shows the digest.

---

## The agent loop, in one diagram

```
   ┌────────────── Marketplace API (search-listings) ──────────────┐
   │                                                               │
   │  filter by category, sort by downloads DESC                    │
   └─────────────────────────────┬─────────────────────────────────┘
                                 │ pick listing_id
                                 ▼
   ┌─────────────── POST /listings/{id}/installations ──────────────┐
   │                                                               │
   │  Unity Catalog: marketplace_100.bronze.<id>                    │
   └─────────────────────────────┬─────────────────────────────────┘
                                 │ fulfillment paths
                                 ▼
   ┌─────────────────── COPY INTO / Auto Loader ───────────────────┐
   │                                                               │
   │  bronze Delta tables in marketplace_100.bronze                 │
   └─────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
   ┌───────────────── Lakeflow Declarative Pipeline ───────────────┐
   │                                                               │
   │  bronze → silver (typed) → gold (aggregated)                  │
   │  + expectations (DQ rules) + per-table quality_score           │
   └─────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
   ┌────────────── MLflow / Unity Catalog (MLOps) ─────────────────┐
   │                                                               │
   │  LightGBM / sentence-transformer baseline                      │
   │  log params / metrics / model → UC @Champion alias             │
   └─────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
   ┌────────────────── Mosaic AI Agent (tool-use) ─────────────────┐
   │                                                               │
   │  foundation-model-api → FM API → 70B                          │
   │  tools: [profile_table, get_mlflow_metrics,                   │
   │         inspect_dlt_expectations]                             │
   │  returns {summary, quality_score, next_category, retry?}      │
   └─────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
   ┌────────────── Lakebase ops log + Delta digest ────────────────┐
   │                                                               │
   │  marketplace_100.agents.iterations (Delta)                    │
   │  marketplace_100_lakebase.agent_log (Postgres)                │
   └───────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
                       next iteration (0..99)
```

---

## Why this matters

The whole "agentic AI" conversation is currently being
held in notebooks. Notebook-with-LLM is not a system.
A system has **state that survives a crash, retries
that don't double-bill, an evaluator that decides
"this is good enough" or "go again", and a UI that
shows a human what's been done.**

That is what this project is.

- **State** lives in Delta (`iterations` table) +
  Lakebase (ops log). Crash mid-iteration → resume
  from `MAX(iter_no) WHERE status='ok'`.
- **Retries** are bounded by `MAX_RETRIES` (default 2)
  and gated by `quality_score >= 0.4`. A bad
  iteration doesn't burn DBUs indefinitely.
- **Evaluator** is the Mosaic AI agent itself, with
  Foundation Model API as the judge. The judge reads
  MLflow metrics, DLT expectations, and the table
  profile, and decides whether to keep the result.
- **UI** is a Databricks App. Deploy via DAB, share
  the URL with whoever needs to see what 100
  autonomous iterations produced.

---

## Cost ceiling

Target: **Free Edition, $0–$20/mo.** Free Edition is
serverless-only. The stack is serverless:

- Jobs: serverless compute, 5 concurrent tasks (we
  use 1).
- DLT: 1 active pipeline per type — we re-deploy
  per iteration via `pipeline_task`, so no long-lived
  pipeline.
- Model serving: short-lived per-iteration endpoint,
  scale-to-zero. Probe traffic only.
- Lakebase: 1 project, scale-to-zero, free.
- SQL warehouse: 1 × 2X-Small, free.

### Measured numbers (benchmark, 25 iters, 17s wall)

```
quality:    min=0.40 max=0.95 avg=0.82 p50=0.95
cost:       $0.022  (8,000 prompt + 2,750 completion tokens)
per-iter:   $0.0009 / 320 prompt + 110 completion
stage avg:  ingest=10ms  dlt=6ms  serving=261ms
            agent<1ms  history_add=662ms (one-time embed)
bandit:     all 10 arms pulled at least once in 25 iters
```

So 100 iterations ≈ **$0.09 FM API** + the cost of
~5 GB of marketplace data storage (negligible).
Total monthly: **$1–$3** if you stay in the free
tier, even before the budget guard's $5/day cap.

If Free Edition throttles the "all 100 in one day"
case, **stagger 3–4 iterations/day over 30 days** —
the bandit state and history index are durable, so
the loop resumes from where it stopped.

---

## How to run

### Local smoke (no Databricks creds needed)

```bash
cd marketplace-100
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make smoke
```

`make smoke` runs 1 iteration against a sandbox
fixture. It exercises the driver, the agent (with
the FM API call mocked), the DLT stub, and the
Lakebase stub. No network. ~30 seconds.

### Real run (Databricks workspace required)

```bash
# 1. Configure your PAT
export DATABRICKS_HOST="https://<your-workspace>.cloud.databricks.com"
export DATABRICKS_TOKEN="<your-PAT>"

# 2. Validate the DAB
databricks bundle validate

# 3. Deploy to dev (creates Job, Lakeflow pipeline, Lakebase, App)
databricks bundle deploy --target dev

# 4. Trigger the 100-iteration driver
databricks bundle run m100_driver_job

# 5. Open the digest App
databricks bundle open m100_digest_app
```

The Job's parameter is `max_iterations` (default
100). The driver writes every iteration's row to
`marketplace_100.agents.iterations` (Delta) and
`marketplace_100_lakebase.agent_log` (Postgres).
Resumable: kill the Job, run it again, it picks up
where it left off.

---

## Tests

```bash
make test
```

127 tests across 9 modules. No network, no Databricks
creds, no GPU.

- `tests/test_marketplace_client.py` — mocked HTTP,
  covers search / detail / install / fulfillments,
  pagination, rate-limit backoff.
- `tests/test_agent.py` — mocked FM API, covers
  4-tool schema, quality-score threshold,
  retry decision, multiple response shapes.
- `tests/test_bandit.py` — UCB1 math, Lakebase
  persistence, agent-override cooldown.
- `tests/test_dqx.py` — 3 tiers (WARN / DROP /
  QUARANTINE), quality-score formula, side outputs.
- `tests/test_history_search.py` — 384-dim
  embeddings, cosine similarity, write-through
  persistence, fallback to hash embeddings.
- `tests/test_serving.py` — percentile math, drift
  score, local predict, error capture.
- `tests/test_cost.py` — pricing for all 5 models,
  ledger accumulation, each budget cap, DBU reader.
- `tests/test_benchmark.py` — end-to-end invariants
  (cost aggregates, bandit exploration, JSON shape).
- `tests/test_smoke.py` — full iteration lifecycle
  with every external dep mocked.

## Benchmark

```bash
make bench
```

Runs `python -m m100.benchmark --iterations 25` and
prints a JSON summary (numbers above) and writes
`/tmp/m100_bench.json`. Exercises every component
end-to-end (bandit, DQX, agent, history, cost,
serving) on canned but realistic data. ~17s.

---

## What this is NOT

- **Not an orchestrator.** There's no Airflow, no
  Prefect, no Dagster. The 100-iteration Job IS
  the orchestrator.
- **Not a streaming platform.** A single iteration
  is a batch job. If you want continuous ingestion,
  replace the per-iteration `pipeline_task` with a
  long-lived Auto Loader + DLT pipeline (and
  accept the Free Edition 1-pipeline quota).
- **Not a model-training framework.** The ML
  baseline is intentionally simple (LightGBM /
  sentence-transformer). The point is to **register
  one model in Unity Catalog per iteration**, not
  to win Kaggle.
- **Not a generic agent framework.** The Mosaic AI
  Agent is a `ChatAgent` subclass tied to the
  Marketplace iteration shape. It is not a
  re-usable autonomous-research agent.

---

## Related directories

- [`../Banking-AML-Data/`](../Banking-AML-Data/) —
  the regulated-industry project; the same Unity
  Catalog patterns apply.
- [`../e-commerce-end-2end/`](../e-commerce-end-2end/) —
  the original "100% Databricks" reference; this
  project is its agentic successor.
- [`../keystone-iceberg-ops/`](../keystone-iceberg-ops/) —
  the table-ops layer that keeps the lake alive;
  Marketplace 100 produces the data this would
  compact.
- [`../realtime-stock-pipeline/`](../realtime-stock-pipeline/) —
  the streaming reference; Marketplace 100 is the
  batch counterpart.

---

**Last updated:** 2026-10-14
**License:** MIT — use freely in your own courses,
prototypes, and products.
