# Lesson 1 — Pipeline Code Generation

> **Type:** Article · Module 3 · AI for Pipeline Development
> Generating ingestion pipelines that handle edge cases, not just happy paths.

---

## The 80/20 of pipelines

Pipelines are **80% boilerplate** (extractor skeleton, retries, logging, DAG, tests) and **20% the part you actually have to think about** (business validation, idempotency, edge cases). AI handles the 80% almost perfectly. The 20% is yours.

```
   Pipeline tasks                              AI handles?
   ─────────────                               ──────────
   Source connector boilerplate                ✅ 100%
   Pagination logic                            ✅ 90% (verify edge cases)
   Retry + backoff                             ✅ 100%
   Schema validation (Pydantic)                ✅ 90%
   Loader (warehouse upsert)                  ✅ 80% (verify MERGE logic)
   DAG scaffold                                ✅ 100%
   Logging                                     ✅ 100%
   Tests (happy path)                          ✅ 100%
   Tests (edge cases)                          ⚠️ must specify
   Business validation rules                   ❌ on you
   Idempotency strategy                        ❌ on you
   Backfill plan                               ❌ on you
   On-call runbook                             ❌ on you
```

---

## The happy-path trap

AI loves the happy path. It generates beautiful extraction code that handles the case where the API returns clean data on the first try. If you don't ask for edge cases, **it won't write that code**.

The failure mode in production is exactly the failure mode you did not specify.

```
   Happy path only (default)                    With explicit edge cases
   ────────────────────                         ────────────────────────
   ✅ API returns 200                           ✅ API returns 200
   ✅ all pages return                          ✅ handles 429 (backoff)
   ✅ schema unchanged                          ✅ handles 5xx (retry)
   ✅ no duplicates                             ✅ handles partial pages
   ✅ correct data                              ✅ handles new field tomorrow
   → SILENT FAILURES IN PROD                    ✅ handles duplicate row
                                                 → production-ready
```

---

## The pipeline-generation prompt

```text
ROLE: senior data platform engineer. Pipeline stack: Airflow 2.9 + Python 3.11 + Snowflake.

CONTEXT:
- Source: Stripe payments endpoint, paginated, Bearer-token auth.
- Destination: raw.stripe.payments_v2 Snowflake table, partitioned by ingest_date.
- Idempotency: re-running for the same ingest_date must upsert on payment_id.
- Schedule: @daily, 06:00 UTC.
- Retries: 3 with exponential backoff (60s, 300s, 900s).
- Alerting: Slack channel #data-alerts on failure.

TASK: Generate these files:
1. dags/stripe_payments.py — Airflow DAG from templates/dag_template.py
2. stripe_payments/extract.py — paginated extractor
3. stripe_payments/validate.py — Pydantic v2 schema
4. stripe_payments/load.py — Snowflake MERGE upsert
5. stripe_payments/test_extract.py — pytest stubs

CONSTRAINTS — DO NOT GENERATE HAPPY-PATH ONLY CODE. You MUST explicitly handle:
- 429 rate-limited response → exponential backoff + jitter
- 5xx server error → retry up to 3 times
- partial page (e.g. last page has 5 items) → still write what you got
- new field appears in API response → log warning, accept, surface
- duplicate payment_id in same page → de-dupe before load
- malformed JSON in a record → skip + log row, do NOT fail whole extract
- secret rotation failure (401) → fail loudly, alert, do NOT silently use stale token

Additional:
- use uv-managed env, structlog JSON output, type hints everywhere
- idempotent end-to-end: re-running for same ingest_date == no new rows
- tests: include edge cases listed above

FORMAT: one file per ```python block, file path comment at top.

VERIFICATION: list 5 unit tests + 1 integration test I should run before deploy.
```

**This single instruction in the constraints block is the difference between demo code and production code.**

---

## The "split into components" workflow

Never generate a whole pipeline in one shot. Break it apart:

```
   ┌────────────────────────────────────────────────┐
   │  STEP 1 — Source connector                     │
   │  "Generate the paginated Stripe API client    │
   │   with explicit backoff for 429 and 5xx."     │
   └─────────────┬──────────────────────────────────┘
                 ▼
   ┌────────────────────────────────────────────────┐
   │  STEP 2 — Extractor                            │
   │  "Generate the extractor that pages through   │
   │   all results, dedupes by payment_id, logs    │
   │   partial pages and unknown fields."          │
   └─────────────┬──────────────────────────────────┘
                 ▼
   ┌────────────────────────────────────────────────┐
   │  STEP 3 — Validator                            │
   │  "Generate the Pydantic v2 schema with        │
   │   strict types. Mark unknown fields.          │
   │   Reject malformed records."                  │
   └─────────────┬──────────────────────────────────┘
                 ▼
   ┌────────────────────────────────────────────────┐
   │  STEP 4 — Loader                               │
   │  "Generate the Snowflake MERGE upsert.       │
   │   Idempotent on (payment_id, ingest_date)."   │
   └─────────────┬──────────────────────────────────┘
                 ▼
   ┌────────────────────────────────────────────────┐
   │  STEP 5 — Orchestrator                         │
   │  "Generate the Airflow DAG using             │
   │   templates/dag_template.py. Schedule         │
   │   @daily, 06:00 UTC, retries 3."             │
   └─────────────┬──────────────────────────────────┘
                 ▼
   ┌────────────────────────────────────────────────┐
   │  STEP 6 — Tests                                │
   │  "Generate pytest tests covering every edge   │
   │   case in the constraints list."              │
   └────────────────────────────────────────────────┘
```

Each step runs at ~80% quality on first try. The whole pipeline assembled from these steps is **production-grade on day one**, not after a week of debugging.

---

## The "what AI gets wrong about pipelines" honesty

### 1. State management in streaming
AI defaults to batch pipeline patterns. Stateful streaming (exactly-once, watermarking, late-arrival handling) needs explicit spec.

### 2. Backfill behaviour
What happens when the source has 6 months of historical data and you want to load it? AI won't write the backfill DAG unless you ask.

### 3. Resource sizing
AI doesn't know your cluster size, executor memory, or shuffle partitions. Tell it.

### 4. Compliance / ACLs
AI doesn't know which rows are PII. Tell it which columns to mask.

### 5. Operational concerns
On-call runbook, alert routing, escalation — these are yours.

---

## The pipeline deliverable (what to ship)

After the workflow above, you have:

```
   dags/stripe_payments.py          (DAG)
   stripe_payments/                 (package)
       __init__.py
       extract.py                  (API client + extractor)
       validate.py                 (Pydantic schema)
       load.py                     (Snowflake MERGE)
       models.py                   (dataclasses)
   tests/
       test_extract.py             (edge cases)
       test_validate.py
       test_load.py
       fixtures/
           stripe_page1.json
           stripe_429.json
           stripe_partial.json
   README.md                       (runbook)
```

Each file went through the review (Lesson 5 of Module 1). Each test covers an edge case from the constraints block. The DAG extends your team's canonical template. README documents the runbook: "if you get an alert at 3 a.m., here's what to check."

---

## The 3-a.m. test

> Before shipping, ask: *"If this pipeline fails at 3 a.m., can someone who has never seen this code debug it in 30 minutes?"*

If the answer is no:
- The README is too thin.
- The tests don't cover the failure mode.
- The error messages are too generic.
- The alerting doesn't point to the next action.

Fix those before shipping. AI can draft all four. You review and own them.

---

## What Comes Next

> Lesson 2 — **AI for Spark** — generating PySpark code that's correct on your cluster config, your data shape, and your AQE settings.
