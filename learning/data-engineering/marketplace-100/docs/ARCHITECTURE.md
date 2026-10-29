# Architecture — Marketplace 100

This document captures the moving parts of the system and
the design decisions behind them. Read it before changing
anything structural.

## The 100-iteration loop, layer by layer

```
        ┌─────────────────────────────────────────────────────┐
        │           Databricks Job (m100_driver_job)          │
        │   serverless · quartz 03:00 UTC · max_concurrent=1  │
        └────────────────────┬────────────────────────────────┘
                             │
                             ▼
        ┌─────────────────────────────────────────────────────┐
        │                    driver.py                        │
        │  for i in range(resume_from, max_iterations):       │
        │      1. pick category                               │
        │      2. search marketplace                          │
        │      3. install listing                             │
        │      4. ingest → bronze                             │
        │      5. DLT promote → silver + gold                 │
        │      6. MLOps → MLflow + UC                         │
        │      7. agent.evaluate() → score + next_category    │
        │      8. persist → Delta + Lakebase                  │
        │      sleep(stagger_seconds)                         │
        └────────────────────┬────────────────────────────────┘
                             │
                             ▼ each of (4)-(7) is a separate module
                             │
       ┌─────────────┬───────┴─────────┬─────────────┬─────────┐
       ▼             ▼                 ▼             ▼         ▼
   ingest.py    dlt_pipeline.py    mlops.py    agent.py   lakebase.py
   COPY INTO /  bronze→silver→gold LightGBM /  M100Agent  psycopg v3 /
   Auto Loader  + expectations     ST embed    + FM API   Delta fallback
       │             │                 │             │         │
       └─────────────┴──── marketplace_client.py ─────┴─────────┘
                             (REST API wrapper)
```

## State of the world

Three persistent stores, one canonical truth per concern:

| Concern                | Primary store                                | Secondary / fallback                       |
|------------------------|----------------------------------------------|--------------------------------------------|
| Iteration state        | `marketplace_100.agents.iterations` (Delta)  | `lakebase.iterations` (Postgres)           |
| Per-call agent log     | `lakebase.agent_log` (Postgres)              | `marketplace_100.agents.lakebase_fallback` |
| Listing data (bronze)  | `marketplace_100.bronze.<id>_<hash>` (Delta) | n/a                                        |
| Model registry         | Unity Catalog `<catalog>.models.m100_*`      | n/a                                        |
| MLflow runs            | MLflow Experiment `/Users/prem/m100/...`     | n/a                                        |
| Skipped listings       | `lakebase.skip_log` (Postgres)               | n/a                                        |

The Delta `iterations` table is the source of truth. Lakebase
is a fast read cache for the driver boot path. If Lakebase
is down, the driver still runs — every write goes to the
Delta fallback. The next time Lakebase is back, the driver
catches up.

## Why this stack (and not the obvious alternatives)

| Decision                       | What we picked                | What we didn't pick                  | Why                                                                                             |
|--------------------------------|-------------------------------|-------------------------------------|-------------------------------------------------------------------------------------------------|
| Orchestrator                   | Databricks Jobs               | Airflow, Prefect, Dagster           | One fewer system. Free Edition already gives us a Job. The 100-iter loop fits in one task.        |
| Ingest                         | COPY INTO + Auto Loader       | Kafka, Pulsar                       | Marketplace deliveries are batch drops; COPY INTO is the canonical batch ingest on Databricks.  |
| Transform                      | Lakeflow Declarative Pipeline | dbt, Spark raw                      | DLT gives us expectations + lineage for free; dbt would be a 2nd transform engine.               |
| Model training                 | LightGBM + sentence-transformers | XGBoost, custom NN                | Both are pip-installable, run in <30s, cover 95% of marketplace shapes.                          |
| Agent framework                | Mosaic AI Agent + FM API      | LangChain, custom                   | Mosaic AI is the native Databricks path; FM API pay-per-token bypasses the serving quota.        |
| State / ops log                | Lakebase (Postgres)           | Redis, plain Delta                  | Lakebase is serverless + Postgres-compatible + UC-governed. Delta fallback if not available.      |
| Dashboard                      | Databricks App (Streamlit)    | Tableau, Looker                     | App is a single DAB resource; deploys in `databricks bundle deploy` with no separate infra.     |

## Concurrency model

- **One driver run at a time.** The Job has
  `max_concurrent_runs: 1`. If two start, the second
  blocks on the first — the Lakebase `iterations`
  table has a unique constraint on `iter_no`.
- **Per-iteration, single-task.** No fan-out within
  an iteration. The 100-iter loop is 100 task
  executions, but in *one* Job run.
- **No concurrent ingest.** A listing install is
  serialised by the Marketplace API (each `POST
  /installations` is an async job that completes
  in 5-60s).
- **Stagger, not parallelism.** Free Edition has
  no "parallel tasks" budget worth using for
  this; staggering 60s between iterations is the
  cheapest way to stay under throttle.

## Failure modes

| Failure                                     | What we do                                                                |
|---------------------------------------------|---------------------------------------------------------------------------|
| Marketplace API 429                          | Tenacity retries with exponential backoff (2-120s, 6 attempts)            |
| Listing needs personalization                | Catch `PersonalizationRequired`, log, skip, move to next category         |
| Ingest produces 0 rows                       | Driver logs `bronze_row_count=0`, agent scores 0.0, retries up to N times |
| DLT expectation fail-rate > 50%             | Driver logs expectation_pass_rate, agent scores low, retries              |
| MLOps: only 1 unique value in target         | Skip the train step, log zero-metric run, agent scores 0.0, retries       |
| Agent response malformed                    | Fall back to `quality_score=0.5, retry=false` and continue                 |
| FM API quota exhausted                       | Same fallback (we don't have a way to detect quota — for v1, fail loud)    |
| Lakebase unreachable                         | `connect()` yields None, every write goes to Delta fallback               |
| Driver crash mid-iteration                  | Next boot reads `MAX(iter_no)` and resumes; `running` rows > 1h get retried|
| Free Edition throttle (1-day cooldown)      | Stagger across days; daily Job schedule at 03:00 UTC lets the budget reset |

## Cost analysis (30-day, Free Edition)

| Component              | Quantity     | Unit cost         | Subtotal |
|------------------------|--------------|-------------------|----------|
| Serverless Jobs        | 30 × 1 run   | free              | $0       |
| Lakeflow pipeline_task | 30 × 100 = 3000 task-runs | serverless DLT  | ~$1      |
| Foundation Model API   | 30 × 100 × ~5k tokens = 15M | $1/M input, $5/M output | ~$5 |
| Lakebase               | 1 project, scale-to-zero | free up to 1 CU | $0 |
| SQL warehouse (digest) | 1 × 2X-Small | free              | $0       |
| **Total**              |              |                   | **~$6/mo** |

The Foundation Model API spend is the only material line.
If we ran 100 iterations in a single day, we'd see ~$3-4
for LLM tokens alone. Staggering across 30 days lets us
fit under the Free Edition "fair use" compute cap.

## What changes when you leave Free Edition

The biggest cost jump is **all-purpose clusters** — if
someone wants to swap in a dedicated DLT cluster, the
`m100_lakeflow` resource needs `cluster: { ... }` and
the Job's `tasks[0].python_wheel_task` needs a cluster
spec. Everything else is already serverless.

The second jump is **dedicated serving endpoints** — if
the agent gets called often enough that pay-per-token
becomes more expensive than a provisioned endpoint, we
swap `_call_fm_api` to `WorkspaceClient.serving_endpoints
.get_open_ai_client()` and add a `serving_endpoint` DAB
resource. Same tool schemas, same prompt.
