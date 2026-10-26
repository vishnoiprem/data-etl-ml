# System Design Sub-Lesson 6 — Batch Processing and Data Pipelines (the canonical Pattern 6 walkthrough)

> **Batch processing and data pipelines are the sixth most common system design pattern.** 10-15% of system design questions involve batch jobs (daily aggregation, ML training, log analysis, ETL). The FDE signal: a candidate who names the scheduler AND the worker pool size AND the failure handling AND the data quality checks — is showing they can own a data pipeline. **This sub-lesson walks through the canonical batch processing design.**

---

## Why batch processing is the FDE signal

The 4 things the interviewer is testing:

1. **Can you read the requirements?** Batch = process a large dataset in a scheduled job. The requirement drives the design (daily vs hourly, batch vs streaming, full vs incremental).
2. **Can you pick the right scheduler?** Cron for simple scheduling; Airflow for DAGs + dependencies; AWS Step Functions for managed service.
3. **Can you handle the worker failure?** The worker dies (OOM, hardware failure). The candidate who names the checkpoint + restart is showing they understand the failure mode.
4. **Can you handle the data quality?** Bad data (nulls, duplicates, schema drift). The candidate who names the quarantine table is showing they understand the operational boundary.

**The FDE pattern:** clarify → decompose → design → tradeoffs. Same as the other patterns, but the design is data-focused.

---

## The canonical batch processing design (worked example)

### The prompt

> "Design a batch processing system: a daily aggregation pipeline for an analytics platform. The pipeline ingests 100M events/day, aggregates them by user_id and date, and writes the results to a Postgres table. The pipeline runs once per day at 02:00 UTC. The customer wants the results by 06:00 UTC."

### Step 1: Clarify (5-7 minutes)

**The 5 questions:**

1. **What's the user?** Analytics team (internal) reading the aggregated data; data scientists (internal) using the data for ML.
2. **What's the scale?** 100M events/day; 1M unique users; 10GB raw data; 4-hour SLA.
3. **What's the constraint?** SLA < 4 hours; cost < $500/month; idempotent (re-runnable without duplicates).
4. **What's the failure mode?** Worker dies mid-job; bad data (nulls, duplicates); schema drift.
5. **What's the timeline?** MVP in 2 weeks; full scale in 4 weeks.

### Step 2: Decompose (10-12 minutes)

**The 3 lists:**

**Entities:**
- RawEvent (id, user_id, event_type, event_data, timestamp) [S3]
- AggregatedEvent (user_id, date, event_count, unique_events, total_value) [Postgres]
- QuarantinedEvent (id, reason, raw_data) [S3]
- PipelineRun (id, started_at, completed_at, status, row_count) [Postgres]

**Services:**
- EventIngestion (writes raw events to S3)
- BatchAggregator (reads from S3, aggregates, writes to Postgres)
- DataQualityChecker (validates before writing to Postgres)
- PipelineScheduler (triggers the daily job)

**Flows:**
- EventIngestion writes raw events to S3 (partitioned by date)
- PipelineScheduler triggers BatchAggregator at 02:00 UTC
- BatchAggregator reads from S3, aggregates by user_id + date, writes to Postgres
- DataQualityChecker validates the aggregated data (no nulls, no duplicates)
- PipelineRun records the run metadata (started_at, completed_at, row_count)

### Step 3: Design (15-20 minutes)

**The API contracts (3-5 endpoints):**

```
GET /aggregated?date=2026-10-10&user_id=U12345
  → 200 OK
  → {"user_id": "U12345", "date": "2026-10-10", "event_count": 100, "unique_events": 5, "total_value": 1000.00}

GET /admin/pipeline-runs?date=2026-10-10
  → 200 OK
  → [{"run_id": "RUN-12345", "started_at": "2026-10-10T02:00:00Z", "completed_at": "2026-10-10T03:30:00Z", "status": "completed", "row_count": 1000000}]

POST /admin/pipeline-runs/replay?date=2026-10-10
  → 200 OK
  → {"run_id": "RUN-12346", "status": "queued"}
```

**The data model (3-5 tables):**

```
aggregated_events (
  user_id BIGINT NOT NULL,
  date DATE NOT NULL,
  event_count INT NOT NULL,
  unique_events INT NOT NULL,
  total_value DECIMAL(10, 2) NOT NULL,
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, date)
)

quarantined_events (
  id BIGSERIAL PRIMARY KEY,
  reason VARCHAR(255) NOT NULL,
  raw_data JSONB,
  quarantined_at TIMESTAMP NOT NULL DEFAULT NOW()
)

pipeline_runs (
  id BIGSERIAL PRIMARY KEY,
  started_at TIMESTAMP NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMP,
  status VARCHAR(20) NOT NULL DEFAULT 'running',  -- running, completed, failed
  row_count INT,
  error_message TEXT
)
```

**The S3 layout:**

```
s3://events-bucket/
  raw/
    year=2026/
      month=10/
        day=10/
          hour=00/
            event-12345.json
            event-12346.json
          hour=01/
            ...
```

**The scale model:**

- **Volume:** 100M events/day; 10GB raw; 1M aggregated rows
- **Compute:** 1 worker (16 CPU, 64GB RAM) for 1.5 hours
- **Storage:** S3 $50/month + Postgres $100/month
- **Cost:** $500/month (S3 $50 + Postgres $100 + worker VM $200 + Airflow $50 + CloudWatch $100)

### Step 4: Tradeoffs (5-7 minutes)

**The 3 tradeoffs:**

1. **Full reprocessing vs incremental.** Full is simpler but slow; incremental is faster but complex. Pick full for 100M events/day (1.5 hours); pick incremental for 1B events/day.
2. **Spark vs Dask vs Python script.** Spark is distributed and featureful; Dask is Pythonic; Python script is simplest. Pick Spark for 1B+ events; pick Dask for 100M events; pick Python script for 10M events.
3. **Airflow vs Step Functions vs cron.** Airflow is the de facto standard; Step Functions is managed; cron is simplest. Pick Airflow for DAGs + dependencies; pick Step Functions for managed; pick cron for single-job scheduling.

**The closing line:** "For 100M events/day with a 4-hour SLA, I'd use S3 for raw storage, a Python worker with pandas to aggregate, Postgres for the aggregated data, and Airflow for scheduling. The cost is $500/month, under the $500/month ceiling. The failure mode is worker death; the fallback is checkpoint + restart. The data quality is checked before writing to Postgres (nulls, duplicates, schema drift)."

---

## The 5 most common batch processing questions

The 5 questions that cover 90% of batch processing system design:

1. **"Design a daily aggregation pipeline"** — covered by the canonical example above.
2. **"Design an ML training pipeline"** — same pattern, with feature engineering + model training + evaluation.
3. **"Design a log analysis pipeline"** — same pattern, with log parsing + aggregation + alerting.
4. **"Design an ETL pipeline"** — same pattern, with extract + transform + load.
5. **"Design a data warehouse loading pipeline"** — same pattern, with staging + dimension + fact tables.

**The pattern:** batch processing = S3 for raw + worker (Spark/Dask/Python) + Postgres for aggregated + scheduler (Airflow/cron) + data quality checks. The variations are the volume (100M vs 1B), the latency (4 hours vs 24 hours), and the failure mode (worker death vs bad data).

---

## The 5 anti-patterns for batch processing

1. **Naming a technology in the first 5 minutes.** The framework says: clarify, decompose, design, tradeoffs. The technology comes in step 3.
2. **Skipping the idempotency story.** The candidate who doesn't mention re-runnability is signaling they don't understand batch systems.
3. **Skipping the data quality checks.** The candidate who doesn't mention nulls, duplicates, schema drift is signaling they don't operate the system.
4. **Skipping the checkpoint + restart.** The candidate who doesn't mention checkpointing is signaling they don't think about long-running jobs.
5. **Skipping the cost calculation.** "It would cost $X/month" without the math is hand-waving. The cost model is the FDE signal.

---

## The 3 most common follow-up questions

| Question | The FDE answer |
|---|---|
| 1. "What if the worker dies mid-job?" | "Checkpoint the aggregated data every 10 minutes. On restart, resume from the last checkpoint. Idempotency prevents duplicates." |
| 2. "What if the data has nulls or duplicates?" | "Quarantine the bad rows to a separate table. Alert the data engineering team. The pipeline continues with the good rows." |
| 3. "How do you handle schema drift?" | "Schema validation before processing. If the schema changes, alert the data engineering team. Use a schema registry (e.g., Confluent Schema Registry)." |

---

## The cross-reference: how this maps to Phase 6

| Phase | The FDE skill it proves |
|---|---|
| `../decomposition/README.md` | The 4-step framework (clarify → decompose → design → tradeoffs) |
| `../take-home/02-pipeline.md` | The data-pipeline take-home variant |
| `../system-design/README.md` | The 9 patterns cheat sheet (Pattern 6: batch processing) |

---

## The thesis

**Batch processing is the sixth most common system design pattern.** The candidate who names the scheduler AND the worker pool size AND the failure handling AND the data quality checks — is showing they can own a data pipeline.

**The 4-step framework (clarify → decompose → design → tradeoffs) is the muscle memory.** The 5 worked examples (daily aggregation, ML training, log analysis, ETL, data warehouse loading) are the patterns. Practice them out loud, time yourself at 60 minutes per question, and rehearse with an AI assistant.

**General prep gets you past the resume screen. System design prep gets you past the centerpiece round at Anthropic, OpenAI, AWS FDE, Databricks, and Scale AI.**