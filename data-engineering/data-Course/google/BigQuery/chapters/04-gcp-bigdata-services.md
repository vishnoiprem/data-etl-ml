# 1.4 — Big Data Services in GCP

> **Section 1 · Introduction to Google Cloud Platform · Lecture 1.4 · 3:56**

## 🎯 What you will learn

- The five big data services and how they fit together
- Which service owns which problem in a pipeline
- The decision matrix for Batch vs Streaming vs SQL

---

## 🧠 Concept

GCP's data platform has five core services. Each one owns a distinct problem:

| Service | Problem it solves | Managed for you | Core abstraction |
|---------|-------------------|-----------------|------------------|
| **BigQuery** | Ad-hoc + batch analytical SQL | Fully (serverless) | Table / SQL |
| **Dataflow** | Complex ETL & streaming pipelines | Partially (cluster optional) | Beam pipeline |
| **Pub/Sub** | Decoupled event ingestion | Fully | Topic / Subscription |
| **Composer** | Scheduling & orchestration | Fully (Airflow as a service) | DAG |
| **Dataproc** | Spark/Hadoop without cluster ops | Partially | Cluster / job |

### The mental model

```
                 ┌──────────────┐
  producers ───▶ │   Pub/Sub    │ ◀─── decoupled, buffering, at-least-once
                 └──────┬───────┘
                        │ streaming
                        ▼
                 ┌──────────────┐
                 │   Dataflow   │ ──── Beam: transforms, windows, joins
                 └──────┬───────┘
                        │ writes
                        ▼
   ┌───────────┐   ┌──────────────┐   ┌──────────────┐
   │Cloud      │   │   BigQuery   │   │  Cloud       │
   │Storage    │◀──│  (warehouse) │──▶│  Composer    │
   │(lake)     │   └──────────────┘   │  (schedule)  │
   └───────────┘                       └──────────────┘
```

### Batch vs Streaming vs SQL — the real decision

**Use BigQuery SQL when you can.** It is the cheapest, simplest, and most maintainable option. BigQuery
elephants are still a thing, but they are much rarer than engineers expect.

**Use Dataflow when:**
- The transformation requires stateful, windowed aggregation over an unbounded stream
- You need to join a stream against a slowly-changing dimension
- You must parse semi-structured or unstructured data at scale
- You need exactly-once semantics with checkpointing
- The logic is genuinely too complex for SQL — e.g., sessionization, sophisticated deduplication

**Use Pub/Sub when:**
- Producers should not be coupled to consumers
- You need buffering for bursty traffic
- You need multiple independent consumers of the same stream
- You want replay capability

**Use Dataproc when** your team already runs Spark and the migration cost of moving to Beam is not
justified. Dataproc is "Spark without the cluster admin"; Dataflow is "a different programming model
that runs Spark under the hood on Batch and Flink-like streaming on Streaming."

**Use Composer when** you need:
- Dependencies between tasks (DAG semantics)
- Backfills and parameterized runs
- A managed Airflow with no ops burden

---

## 🛠️ Hands-On: A Pipeline in Five Commands

```bash
# 1. Create the topic
gcloud pubsub topics create raw-events

# 2. Create the BigQuery dataset
bq --location=US mk --dataset analytics

# 3. Create the staging table with partitioning
bq mk --table \
  --time_partitioning_type=DAY \
  --time_partitioning_field=event_date \
  --description="Raw events landing table" \
  YOUR_PROJECT_ID:analytics.raw_events \
  event_id:STRING,user_id:STRING,event_type:STRING,event_ts:TIMESTAMP,event_date:DATE

# 4. Submit a Dataflow job (template example)
gcloud dataflow jobs run raw-events-to-bq \
    --template=gs://dataflow-templates-us-central1/streaming/dataflow/python3/dataflow/python3-streaming-bigquery.json \
    --region=us-central1 \
    --parameters="topic=projects/YOUR_PROJECT_ID/topics/raw-events,outputTable=YOUR_PROJECT_ID:analytics.raw_events,bigQueryDataset=analytics"

# 5. Verify the load
bq query --use_legacy_sql=false \
  'SELECT event_type, COUNT(*) AS n FROM `YOUR_PROJECT_ID.analytics.raw_events` GROUP BY 1 ORDER BY n DESC'
```

### Pure BigQuery alternative (no Dataflow)

```sql
-- If Pub/Sub messages are landing in a GCS bucket (Pub/Sub → GCS sink),
-- BigQuery can ingest them with a scheduled query and zero infrastructure.
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.analytics.raw_events`
PARTITION BY DATE(event_ts)
CLUSTER BY event_type
AS
SELECT
    JSON_VALUE(data, '$.event_id')  AS event_id,
    JSON_VALUE(data, '$.user_id')   AS user_id,
    JSON_VALUE(data, '$.event_type') AS event_type,
    TIMESTAMP_MILLIS(CAST(JSON_VALUE(data, '$.ts_ms') AS INT64)) AS event_ts,
    DATE(TIMESTAMP_MILLIS(CAST(JSON_VALUE(data, '$.ts_ms') AS INT64))) AS event_date
FROM `YOUR_PROJECT_ID.raw_pubsub_landing.events_*`
WHERE DATE(publication_timestamp) = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY);
```

💡 This "GCS landing zone + BigQuery SQL" pattern eliminates Dataflow entirely for a large class of
workloads. It is less powerful than Beam, but far cheaper to operate.

---

## 💡 Production Notes

- **Dataflow Streaming (Flink-like) is a different runtime from Dataflow Batch.** The same Beam
  code mostly runs on both, but state management, windowing, and checkpointing semantics differ.
- **Composer is managed Airflow.** You get the Airflow UI and DAG files without managing a cluster.
  It costs ~$340/month minimum for a 3-node environment — this is *not* free.
- **Dataproc clusters bill while idle.** Use `dataproc clusters start` / `stop` for scheduled Spark,
  or auto-stop with `--idle-timeout`.
- **Pub/Sub is at-least-once by default.** Duplicate delivery is expected. Your pipeline must be
  idempotent — use a deduplication key (e.g. `event_id`) and BigQuery `MERGE` rather than blind
  `INSERT`.

---

## 🔑 Key Takeaways

- Five services, five problems: query (BigQuery), transform (Dataflow), ingest (Pub/Sub),
  schedule (Composer), Spark (Dataproc).
- **Prefer BigQuery SQL over Dataflow** whenever it can express the logic — it is cheaper and simpler.
- The GCS-landing-zone pattern removes DataFlow from many pipelines entirely.
- Pub/Sub delivers **at least once** — design for idempotency.
- Composer has a meaningful fixed cost; don't use it for a two-task schedule.

---

## 📚 Practice Exercises

1. **Service selection.** Choose the minimal service set for each:
   - (a) Hourly aggregation of a 2 TB MySQL replica
   - (b) Real-time fraud scoring on clickstream with 50k events/s
   - (c) Monthly regulatory report from 40 TB of S3 data
   - (d) A daily ETL that reads from BigQuery and writes to a Postgres CRM

2. **Idempotency.** Pub/Sub may deliver a message twice. Design a BigQuery ingestion query that is
   safe to re-run. (Hint: `MERGE` on a unique key.)

3. **Cost of simplicity.** A team runs a Dataflow job that could be a 20-line BigQuery SQL query.
   The job costs $800/month in Dataflow worker time. Quantify the savings of the SQL rewrite,
   including BigQuery's own query cost.

4. **Composer sizing.** An Airflow DAG runs 4 tiny tasks at 03:00 daily and nothing else all day.
   Is Composer the right choice? What would you use instead?

---

## 📖 Further Reading

- BigQuery overview — https://cloud.google.com/bigquery/docs/introduction
- Dataflow overview — https://cloud.google.com/dataflow/docs/overview
- Pub/Sub overview — https://cloud.google.com/pubsub/docs/overview
- Cloud Composer overview — https://cloud.google.com/composer/docs/overview
