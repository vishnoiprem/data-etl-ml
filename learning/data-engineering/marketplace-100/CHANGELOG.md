# Changelog — marketplace-100

All notable changes to this project will be documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] — 2026-10-14

### Added

- **Project skeleton** — `databricks.yml` (DAB), `pyproject.toml`,
  `Makefile`, `.gitignore`, `README.md`, `CHANGELOG.md`.
- **`marketplace_client.py`** — wraps the
  `/api/2.1/marketplace-consumer` REST API: search-listings,
  get-listing, install-listing, list-fulfillments. Handles
  PAT auth, pagination, exponential backoff on 429/5xx,
  and `PersonalizationRequired` for listings that need
  a use-case form.
- **`ingest.py`** — `COPY INTO` for batch files, Auto Loader
  (`cloudFiles`) for streaming sources, native Delta
  passthrough. Every bronze table registers in Unity
  Catalog.
- **`dlt_pipeline.py`** — Lakeflow Declarative Pipeline
  definitions: bronze → silver → gold, with expectations
  and a per-table profile. Includes a local fallback
  (in-process promote) for the smoke test.
- **`mlops.py`** — LightGBM classifier (tabular) and
  sentence-transformers retrieval (text) baselines.
  Logs to MLflow, registers in Unity Catalog with the
  `@Champion` alias.
- **`agent.py`** — Mosaic AI Agent (`M100Agent`) with
  three tool schemas: `profile_table`, `get_mlflow_metrics`,
  `inspect_dlt_expectations`. Calls the Foundation Model
  API (`databricks-meta-llama-3.3-70b-instruct`). Returns
  `{summary, quality_score, next_category, retry}`.
  Mock mode for the smoke test.
- **`lakebase.py`** — Postgres-compatible Lakebase
  connection (`psycopg` v3). Persists `agent_log`,
  `iterations`, `skip_log`. Falls back to a Delta
  table if Lakebase is not available or `psycopg`
  is not installed.
- **`driver.py`** — the 100-iteration controller.
  Resumes from `MAX(iter_no)` on crash, self-evaluates
  via the agent, retries up to `MAX_RETRIES` times
  per iteration, persists to Delta + Lakebase.
- **`smoke.py`** — local end-to-end smoke test, runs
  N iterations with all externals mocked.
- **`dashboards/digest_app/app.py`** — Streamlit
  dashboard for the running digest (5 KPI cards, quality
  timeline, category mix, agent log). Deployable as a
  Databricks App via `databricks_app.yml`.
- **Tests** — 28 passing. `test_marketplace_client.py`
  (14), `test_agent.py` (9), `test_smoke.py` (5).
  Covers pagination, error mapping, agent response
  parsing, smoke lifecycle, Lakebase fallback path.

### Operational notes

- **Free Edition posture.** Serverless Jobs, no all-
  purpose clusters. Lakeflow `pipeline_task` per
  iteration (1-active-pipeline quota). Foundation
  Model API (not dedicated serving). Lakebase
  scale-to-zero. Estimated cost: $3-5/month for
  100 iterations.
- **Stagger strategy.** Job runs once per day at
  03:00 UTC; driver sleeps `STAGGER_SECONDS`
  (default 60) between iterations. With 100 iters
  and a 60s sleep, the Job takes ~100 min of
  wall-clock time, well under Free Edition's
  per-Job timeout.
- **Crash recovery.** Lakebase `iterations` table
  is read on driver boot; if `MAX(iter_no) = 42`,
  the next run starts at iter 43. A `running`
  row older than 1 hour is treated as a stale
  crash and the iteration is retried.
