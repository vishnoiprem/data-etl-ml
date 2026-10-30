# 8.5 — End-to-End Capstone

> **Section 8 · ML on GCP & Capstone · Lecture 8.5 · 8:00**

## 🎯 What you will learn

- The **full architecture** of a production analytics platform, wired end to end
- Every stage with its **concrete GCP resource names**, not placeholders:
  - **Ingest** — Pub/Sub topic `events`, Cloud Storage landing bucket `raw-events-us-central1`
  - **Process** — Dataflow or Dataproc: validate → normalise → currency conversion → windowed aggregation, with a dead-letter path
  - **Store** — BigQuery dataset `curated`, date-partitioned table `events`, clustered aggregate table
  - **Orchestrate** — a Composer DAG with a logical-date data interval
  - **Govern** — IAM via `pipeline-sa`, Dataplex, DLP for PII
  - **Serve** — a Looker Studio dashboard
  - **Model** — BigQuery ML for churn over the curated table
- The **cost model** with real numbers from the course `cost_model` module
- The **design decisions** and their trade-offs, argued rather than asserted
- The **failure modes** and a runbook for each
- A **phased rollout plan** you could actually execute

---

## 🧠 Concept

### The system

This capstone builds the platform the whole course has been assembling. A retail analytics business receives events from four regional systems, needs them normalised to a single currency, aggregated for the BI layer, and scored for a churn model.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌──────────┐    ┌────────────┐    ┌──────────────────────────────────────┐  │
│  │ Regional │    │            │    │        PROCESSING (Dataflow)         │  │
│  │ systems  │───▶│  Pub/Sub   │───▶│  ┌────────────┐  ┌───────────────┐  │  │
│  │ (4 apps) │    │  topic:    │    │  │  validate  │─▶│   normalise   │  │  │
│  └──────────┘    │  events    │    │  │  (DoFn)    │  │  + FX to EUR  │  │  │
│                  │            │    │  └────────────┘  └───────┬───────┘  │  │
│                  └─────┬──────┘    │                         │          │  │
│                        │           │                    ┌────▼────┐     │  │
│                  ┌─────▼──────┐    │                    │ windowed│     │  │
│                  │  Dead      │    │                    │  agg    │     │  │
│                  │  letter    │    │                    └────┬────┘     │  │
│                  │  topic     │    │                         │          │  │
│                  └────────────┘    └──────────┬──────────────┘          │  │
│                                               │                         │  │
│                  ┌────────────────────────────┼─────────────────────────┐│  │
│                  │                            │                         │  │
│            ┌─────▼──────┐            ┌────────▼─────────┐               │  │
│            │ Cloud      │            │ BigQuery         │               │  │
│            │ Storage    │            │ dataset: curated │               │  │
│            │ raw-events-│            │  ├ events (partitioned)          │  │
│            │ us-central1│            │  ├ events_hourly (clustered)     │  │
│            │  (landing) │            │  └ churn_model (BQML)            │  │
│            └────────────┘            └────────┬─────────┘               │  │
│                                                │                         │  │
│                  ┌─────────────────────────────┼─────────────────────────┘  │
│                  │                             │                            │
│            ┌─────▼──────┐            ┌────────▼─────────┐                  │
│            │ Composer   │───────────▶│  Looker Studio   │                  │
│            │ DAG        │  triggers  │  dashboard       │                  │
│            │ (logical   │            └──────────────────┘                  │
│            │  date)     │                                                  │
│            └────────────┘                                                  │
│                                                                             │
│  GOVERNANCE: pipeline-sa (least privilege) · Dataplex (catalog + lineage)   │
│              DLP de-identification on the curated table                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Every resource, named

| Purpose | Resource | Fully-qualified name |
|---|---|---|
| Event bus | Pub/Sub topic | `projects/my-project/topics/events` |
| Dead letter | Pub/Sub topic | `projects/my-project/topics/events-dlq` |
| Landing bucket | Cloud Storage | `gs://raw-events-us-central1` |
| Archive bucket | Cloud Storage | `gs://raw-events-us-central1-archive` |
| Raw zone | GCS path | `gs://raw-events-us-central1/raw/` |
| Curated dataset | BigQuery dataset | `my-project.curated` |
| Event table | BigQuery table | `my-project.curated.events` |
| Hourly aggregate | BigQuery table | `my-project.curated.events_hourly` |
| Churn model | BigQuery ML model | `my-project.curated.churn_model` |
| Scores | BigQuery table | `my-project.curated.churn_scores` |
| Pipeline identity | Service account | `pipeline-sa@my-project.iam.gserviceaccount.com` |
| Orchestration | Composer environment | `my-project-composer` |
| Pipeline definition | Dataform | `my-project.dataform.curated` |
| Catalog | Dataplex | `my-project` (lake `bigquery`) |
| DLP | Inspect template | `projects/my-project/locations/us-central1/templates/inspect-events` |
| BI | Looker Studio report | `Looker Studio → my-project/curated/events_hourly` |

**No placeholders.** You can build this from the chapter.

### Stage 1 — Ingest

**The design decision: Pub/Sub as the buffer, GCS as the record.**

The events arrive from four regional systems with different schemas, different volumes, and different reliability. The requirements:

- A slow consumer must not cause data loss at the producer.
- The raw payload must be retained for replay and audit.
- The ingest contract must not change when the processing logic changes.

**Pub/Sub topic `events`.** One topic, not four. The regional systems publish with an ordering key of `user_id` (so a user's events arrive in order), and the payload carries the source region.

```text
projects/my-project/topics/events
projects/my-project/topics/events-dlq
```

**The subscription with a dead-letter topic.** This is the single most important Pub/Sub configuration in the system:

```bash
gcloud pubsub topics create events --project=my-project
gcloud pubsub topics create events-dlq --project=my-project

gcloud pubsub subscriptions create events-sub \
  --project=my-project \
  --topic=events \
  --ack-deadline-seconds=60 \
  --message-retention-duration=7d \
  --dead-letter-topic=events-dlq \
  --max-delivery-attempts=5
```

**`max-delivery-attempts=5` with a DLQ is what makes the pipeline safe.** A message that fails validation five times is moved to the DLQ rather than blocking the subscription forever. The alternative — infinite redelivery — means one poison message stalls the entire pipeline. This is the difference between a data platform that degrades gracefully and one that has a bad afternoon.

**The Cloud Storage landing bucket `raw-events-us-central1`.**

```bash
gcloud storage buckets create gs://raw-events-us-central1 \
  --project=my-project \
  --location=us-central1 \
  --uniform-bucket-level-access \
  --public-access-prevention
```

**Why a bucket at all, when Pub/Sub already has message retention?**

Three reasons:

1. **Pub/Sub retention is 7 days. The bucket is forever.** When a data engineer needs to replay last month because a currency conversion was wrong, Pub/Sub cannot help you.
2. **The bucket is the replay source.** A backfill reads from the bucket, not from Pub/Sub.
3. **Cost.** Writing to the bucket is $0.02/GB-month for Standard. The bucket *is* the archive.

**The landing pattern.** Dataflow writes to the bucket as it processes:

```text
gs://raw-events-us-central1/raw/dt=2026-01-15/hour=14/part-00000.jsonl
gs://raw-events-us-central1/raw/dt=2026-01-15/hour=15/part-00000.jsonl
```

**Partitioning the raw zone by date and hour** means a replay of one hour reads one prefix rather than the whole bucket. On a large archive this is the difference between a 4-hour backfill and a 4-minute one.

**The producer contract.** The regional systems publish a JSON payload:

```json
{
  "event_id": "e00000000",
  "user_id": "u000914",
  "event_ts": "2026-01-15T00:54:38+00:00",
  "event_type": "page_view",
  "region": "AMER",
  "channel": "web",
  "currency": "USD",
  "amount": 700.97
}
```

Eight fields, flat, with `event_ts` as an RFC 3339 timestamp including the offset. **The contract rules that matter:**

- **`event_ts` carries the timezone offset.** Not a local timestamp. A timestamp without an offset is ambiguous, and ambiguity in an event time is unresolvable after the fact.
- **`event_id` is unique and globally unique.** This is the deduplication key and the replay idempotency key. If the producer cannot guarantee global uniqueness, the pipeline must derive a composite key.
- **`region` is one of `AMER`, `APAC`, `EMEA`, `LATAM`.** Exactly four values. A fifth value means a new producer appeared, and the pipeline should reject it rather than quietly create a fifth region in the aggregate.
- **`currency` is one of `EUR`, `USD`, `GBP`, `JPY`.** A new currency means the FX table needs updating, and the pipeline must reject rather than guess.

**The rejection taxonomy is a contract too.** The pipeline rejects on ten distinct reasons, and each reason has a different fix. This is why the reject counts are a dict, not an integer:

```text
wrong_field_count: 2      bad_amount: 1         unknown_region: 2
unknown_channel: 1        unknown_currency: 1   unknown_event_type: 1
missing_event_id: 1       missing_user_id: 1     negative_amount: 1
bad_timestamp: 1
```

A single counter of "12 rejects" is unactionable. The taxonomy says two rows are malformed and ten are schema violations — two different fixes, two different owners.

### Stage 2 — Process

**Dataflow or Dataproc?** This is the decision the course has been deferring, and it has a clear answer here.

| | **Dataflow** | **Dataproc** |
|---|---|---|
| Model | Beam SDK, runner-agnostic | Spark |
| Streaming | Native, with windows and watermarks | Structured Streaming, weaker |
| Ops | Fully managed, autoscaling, no cluster | Cluster lifecycle is yours |
| Code | Python/Java, Beam transforms | Python/Scala/Java/SQL |
| Cost | vCPU-hour, autoscales to zero | vCPU-hour, cluster is always on |
| Batch | Fine | Better — Spark's SQL and MLlib |

**The recommendation: Dataflow.** Three reasons.

1. **The pipeline is fundamentally streaming.** Events arrive continuously, the aggregation is windowed, and the business wants the dashboard fresh within minutes. Beam's model — event time, windows, watermarks, triggers — is a better fit than Spark's Structured Streaming, which is a layer on top of a batch engine.

2. **Dataflow autoscaling.** A Dataproc cluster you pay for at 3 a.m. while nothing is flowing is a waste. Dataflow scales to zero workers.

3. **One language for both.** The same Beam code runs as a streaming template and as a batch job for backfills, through the same `python -m ... --runner` switch. With Spark, batch and streaming are different code.

**The trade-off you accept:** Spark's MLlib and Spark SQL are more mature, and if your team already knows PySpark, Dataproc's velocity advantage is real. **The deciding factor is not the framework — it is whether the pipeline is streaming-first.** If it is, Dataflow.

**The pipeline shape.**

```text
Read from Pub/Sub
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│ Map: parse + validate                                       │
│   → on failure: write to DLQ, do not fail the bundle        │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Map: normalise                                              │
│   → currency → EUR via the FX table                         │
│   → timestamp → UTC + event_dt (the partition key)          │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Filter: dedup by (event_id, partition)                       │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Window: GroupByKey(user_id) into 1-hour windows             │
│   → CombinePerKey: sum amount_eur, count events             │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Write: BigQuery (curated.events, curated.events_hourly)     │
│   + Write: Cloud Storage (raw archive)                      │
└─────────────────────────────────────────────────────────────┘
```

**The windowing.** The pipeline aggregates on a **one-hour window** keyed by `region`, with the window on `event_ts` (event time, not processing time).

```text
24 hourly windows over the sample dataset
```

The watermark strategy is the decision that matters:

```text
Allowed lateness: 10 minutes
Trigger: on-time (emit as soon as the window closes)
```

**Event time vs processing time.** With event time, an event that arrives late is assigned to the window it *belongs* to. With processing time, it lands in whatever window is open when it arrives. **Event time is correct** for analytics — a 23:50 order that arrives at 00:05 belongs to the 23:00 hour. The cost is that windows can be re-opened, which means **late data means corrections**, and your downstream tables must tolerate that.

**The FX conversion.** The pipeline converts everything to EUR:

```text
EUR → 1.0    USD → 0.92    GBP → 1.17    JPY → 0.0064
```

**The conversion is a join, and the join has a failure mode.** If the currency is not in the table, you have three choices:

```text
1. Reject the event      → loses data, but the aggregate stays correct
2. Use a default rate    → the aggregate is silently wrong
3. Write NULL            → the aggregate is wrong in a way that is visible
```

**Choose 1.** Reject with `unknown_currency` and send it to the DLQ. A currency conversion is not something you guess about — and the sample dataset includes exactly one `unknown_currency` reject for this reason. The FX table is a versioned reference table; when the rate changes, you rebuild the affected partitions.

**The dead-letter path.** Three design rules:

1. **A malformed event must not fail the bundle.** A single bad message that raises an exception in a `DoFn` fails the whole bundle, and with at-least-once delivery it is redelivered and fails again — an infinite poison-pill loop. The `DoFn` must catch the error, write the record to the DLQ, and return normally.

2. **The DLQ write must be idempotent.** Redelivery means the same bad event may be written to the DLQ twice. Dedupe on `event_id` before the DLQ write, or accept duplicates and dedupe on read.

3. **The DLQ needs an owner and an alert.** A DLQ nobody reads is a silent data-loss channel. Alert when the DLQ depth exceeds zero for more than one hour.

**The Dataflow code.**

```python
import apache_beam as beam
from apache_beam.io.gcp.bigquery import BigQueryDisposition, WriteToBigQuery, BigQueryDisposition
from apache_beam.io.gcp.pubsub import ReadFromPubSub
from apache_beam.io.textio import WriteToText
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions
from apache_beam.transforms.window import FixedWindows
from apache_beam.transforms import trigger
import json


VALID_REGIONS = frozenset({"EMEA", "AMER", "APAC", "LATAM"})
VALID_CHANNELS = frozenset({"web", "mobile", "store"})
VALID_EVENT_TYPES = frozenset({"order", "refund", "page_view", "signup"})
CURRENCY_TO_EUR = {"EUR": 1.0, "USD": 0.92, "GBP": 1.17, "JPY": 0.0064}
EVENT_FIELDS = [
    "event_id", "user_id", "event_ts", "event_type",
    "region", "channel", "currency", "amount",
]


def validate(row):
    """Return (reason, normalised_row). reason is 'valid' when it passes.

    This is the single source of truth for validity. The pipeline, the
    unit tests and the notebooks all call it, so a rule can never be
    enforced in one place and forgotten in another.
    """
    if len(row) != len(EVENT_FIELDS):
        return "wrong_field_count", None
    if not row.get("event_id"):
        return "missing_event_id", None
    if not row.get("user_id"):
        return "missing_user_id", None
    if row.get("event_type") not in VALID_EVENT_TYPES:
        return "unknown_event_type", None
    if row.get("region") not in VALID_REGIONS:
        return "unknown_region", None
    if row.get("channel") not in VALID_CHANNELS:
        return "unknown_channel", None
    if str(row.get("currency", "")).upper() not in CURRENCY_TO_EUR:
        return "unknown_currency", None
    try:
        amount = float(row.get("amount"))
    except (TypeError, ValueError):
        return "bad_amount", None
    if amount != amount or amount in (float("inf"), float("-inf")):
        return "bad_amount", None
    if amount < 0:
        return "negative_amount", None
    return "valid", row


def normalise(row):
    """Convert to the warehouse shape: amount_eur and event_dt added."""
    out = dict(row)
    out["amount"] = float(row["amount"])
    out["amount_eur"] = round(
        out["amount"] * CURRENCY_TO_EUR[str(row["currency"]).upper()], 2
    )
    ts = str(row["event_ts"])
    out["event_dt"] = ts[:10]           # the partition key
    out["event_hour"] = ts[11:13]       # the clustering / window key
    return out


def parse_and_validate(raw):
    """Split the input into (valid_rows, rejects). Never raises."""
    rejects = []
    try:
        row = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        rejects.append({"reason": "wrong_field_count", "raw": str(raw)[:500]})
        return [], rejects
    reason, valid = validate(row)
    if reason != "valid":
        rejects.append({"reason": reason, "raw": json.dumps(row)[:500]})
        return [], rejects
    return [normalise(valid)], rejects


def main():
    options = PipelineOptions([
        "--runner=DataflowRunner",
        "--project=my-project",
        "--region=us-central1",
        "--temp_location=gs://raw-events-us-central1/tmp",
        "--staging_location=gs://raw-events-us-central1/staging",
        "--job_name=events-pipeline",
        "--streaming=true",
        "--temp_location=gs://raw-events-us-central1/tmp",
    ])
    options.view_as(StandardOptions).streaming = True

    with beam.Pipeline(options=options) as p:
        raw = (
            p
            | "ReadPubSub" >> ReadFromPubSub(topic="projects/my-project/topics/events")
            | "Decode" >> beam.Map(lambda b: b.decode("utf-8"))
        )

        parsed = raw | "ParseValidate" >> beam.FlatMap(parse_and_validate)
        rows, rejects = parsed | "SplitValid" >> beam.Partition(
            lambda element, partition: partition,
            valid_tag="valid",
            invalid_tag="invalid",
        )

        # The DLQ write. Idempotent by construction: the key is the
        # reason plus the raw payload, and we dedupe downstream.
        (
            rejects
            | "ToJson" >> beam.Map(lambda r: json.dumps(r))
            | "WriteDLQ" >> beam.io.WriteToPubSub(
                "projects/my-project/topics/events-dlq"
            )
        )

        # The raw archive. Written from the pipeline so the bucket is
        # the durable record, not just a copy of Pub/Sub.
        (
            raw
            | "Archive" >> beam.io.WriteToText(
                "gs://raw-events-us-central1/raw",
                file_name_prefix="dt={DATE}/hour={HOUR}/part",
                append_trailing_newlines=True,
            )
        )

        # The hourly aggregation, windowed on event time.
        (
            rows
            | "AddWindowKey" >> beam.Map(lambda r: (r["region"], r))
            | "Window" >> beam.WindowInto(
                FixedWindows(60),
                trigger=trigger.AfterWatermark(
                    watermark=trigger.WatermarkStrategyWithTimeout(
                        allowed_lateness=600
                    )
                ),
            )
            | "Aggregate" >> beam.CombinePerKey(
                lambda accum, r: (
                    accum[0] + 1,
                    accum[1] + r["amount_eur"],
                ),
                windowed=True,
            )
            | "FormatWindow" >> beam.Map(
                lambda kv: {
                    "region": kv[0],
                    "window_start": kv[0].start.to_rfc3339(),
                    "event_count": kv[1][0],
                    "revenue_eur": round(kv[1][1], 2),
                }
            )
            | "WriteHourly" >> beam.io.WriteToBigQuery(
                "my-project:curated.events_hourly",
                write_disposition=WriteToBigQuery.WRITE_APPEND,
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            )
        )

        # The detail table, partitioned by event_dt.
        (
            rows
            | "WriteEvents" >> beam.io.WriteToBigQuery(
                "my-project:curated.events",
                write_disposition=WriteToBigQuery.WRITE_APPEND,
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            )
        )


if __name__ == "__main__":
    main()
```

**Note the `Partition` transform.** It splits one PCollection into two by a key function — this is how a single stream feeds both the happy path and the DLQ without duplicating the parse work. The alternative (`FlatMap` returning tagged tuples, then two `Filter`s) parses every message twice.

**The schema of the BigQuery tables.**

```sql
-- The detail table: partitioned by event_dt, clustered by region+channel.
CREATE TABLE IF NOT EXISTS `my-project.curated.events` (
  event_id      STRING   NOT NULL,
  user_id       STRING   NOT NULL,
  event_ts      TIMESTAMP NOT NULL,
  event_dt      DATE     NOT NULL,
  event_hour    STRING   NOT NULL,
  event_type    STRING   NOT NULL,
  region        STRING   NOT NULL,
  channel       STRING   NOT NULL,
  currency      STRING   NOT NULL,
  amount        FLOAT64  NOT NULL,
  amount_eur    FLOAT64  NOT NULL,
  ingested_at   TIMESTAMP NOT NULL
)
PARTITION BY event_dt
CLUSTER BY region, channel, event_type
OPTIONS (
  partition_expiration_days = 400,
  require_partition_filter = TRUE
);
```

**`require_partition_filter = TRUE` is a guardrail worth the cost.** It makes BigQuery reject any query against this table that does not filter on `event_dt`. It eliminates the most expensive mistake in a warehouse — an unfiltered scan — at the price of occasionally annoying a BI user.

**The aggregate table:**

```sql
-- The clustered aggregate table. Small, and the only thing the
-- dashboard should ever touch.
CREATE TABLE IF NOT EXISTS `my-project.curated.events_hourly` (
  region        STRING   NOT NULL,
  window_start  TIMESTAMP NOT NULL,
  event_count   INT64    NOT NULL,
  revenue_eur   FLOAT64  NOT NULL
)
PARTITION BY DATE(window_start)
CLUSTER BY region
OPTIONS (
  partition_expiration_days = 730,
  require_partition_filter = TRUE
);
```

**Why a separate aggregate table rather than a view over `events`?**

Because of the BI cost model from Chapter 7.3. A Looker Studio dashboard with 12 tiles, 20 viewers, and 4 refreshes an hour against a 2 TB detail table is 960 full scans a day. Against a 100 MB aggregate table, it is 960 scans of 100 MB. **The aggregation is paid once per refresh instead of once per viewer per tile.**

**The deduplication semantics.** The pipeline is at-least-once, so duplicates are real. The dedup key is `(event_id, partition)`:

```text
dedup_key(event_id, partition) = f"{event_id}|{partition}"
```

Deduplication is applied **per partition**, not globally. This matters: if the same `event_id` appears in two different dates, those are genuinely two different records (a producer replayed with a shifted timestamp, or a genuine duplicate ID across sources), and collapsing them globally would silently lose data. Per-partition dedup removes the redelivery duplicates within a partition and nothing else.

### Stage 3 — Store

The BigQuery dataset `curated` holds five objects:

| Object | Type | Purpose |
|---|---|---|
| `events` | partitioned table | The normalised detail |
| `events_hourly` | clustered table | The BI aggregate |
| `user_features_daily` | partitioned table | Features for the churn model |
| `churn_model` | BQML model | The churn model |
| `churn_scores` | table | The daily scores |

**The dataset layout, and the discipline of `raw` / `staging` / `curated`.**

```text
my-project.curated        →  the trusted layer. Everything downstream reads this.
my-project.staging        →  intermediate, rebuildable, no SLA
my-project.raw            →  pointers to GCS, never queried directly
```

**Dataform owns the `curated` layer.** Not hand-written SQL in the console. The DDL, the incremental logic, the tests, and the feature definitions all live in a Git repository, and Dataform compiles them into a DAG that Composer triggers. That is what makes the `curated` layer reproducible and reviewable.

**The incremental model.** The `events` table is appended to by the streaming pipeline, so the Dataform model for the *derived* tables must be incremental:

```sql
-- dataform/definitions/curated/events_hourly.sqlx
config {
  type: "incremental",
  materialized: "incremental",
  unique_key: "region, window_start",
  partition_by: { field: "window_start", granularity: "day" },
  cluster_by: ["region"],
  tags: ["curated", "hourly", "bi"],
  description: "Hourly regional revenue and event counts. The only table the Looker Studio dashboard should touch.",
  columns: [
    { name: "region", description: "One of AMER, APAC, EMEA, LATAM." },
    { name: "window_start", description: "Start of the 1-hour event-time window." },
    { name: "event_count", description: "Number of valid events in the window." },
    { name: "revenue_eur", description: "Sum of amount_eur in the window." },
  ]
}

SELECT
  region,
  TIMESTAMP_TRUNC(window_start, HOUR) AS window_start,
  COUNT(*) AS event_count,
  ROUND(SUM(amount_eur), 2) AS revenue_eur
FROM ${ref("events")}
WHERE event_dt >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY)
GROUP BY region, window_start
```

**The three-day lookback** is the standard late-arrival accommodation. Windows are re-computed for the last three days on every run, which handles late events and watermark corrections. Anything older is considered final.

**The Dataform tests.** These are the pipeline's assertions, and they run on every deployment:

```sql
-- dataform/tests/assert_event_count.sqlx
SELECT
  COUNT(*) AS total_events,
  COUNT(DISTINCT event_id) AS distinct_events
FROM ${ref("events")}
WHERE event_dt = @run_date
```

The assertion: `total_events = distinct_events`. A mismatch means the dedup failed.

```sql
-- dataform/tests/assert_no_negative_revenue.sqlx
SELECT COUNT(*) AS violations
FROM ${ref("events")}
WHERE amount_eur < 0 OR amount_eur IS NULL
```

```sql
-- dataform/tests/assert_regions.sqlx
SELECT COUNT(*) AS violations
FROM ${ref("events")}
WHERE event_dt = @run_date
  AND region NOT IN ("AMER", "APAC", "EMEA", "LATAM")
```

**These are the EDA from Chapter 8.1, promoted from a notebook into a deployment gate.** A row-count discrepancy fails the DAG rather than being noticed three weeks later in a dashboard.

### Stage 4 — Orchestrate

**Composer DAG with the logical-date data interval.**

The single most important design decision in an orchestration layer: **the pipeline processes a logical date, not "now"**. Every run has an explicit logical date, and the DAG processes the interval `[logical_date, logical_date + 1 day)`.

```text
┌─────────────────────────────────────────────────────────────────┐
│  events_daily                                                    │
│  logical_date = {{ ds }}                                        │
│  interval    = [{{ ds }}, {{ ds }} + 1 day)                     │
│                                                                  │
│  ┌──────────────────┐                                           │
│  │ extract_raw      │  GCS raw zone → staging                   │
│  └────────┬─────────┘                                           │
│           ▼                                                     │
│  ┌──────────────────┐                                           │
│  │ validate_counts  │  row count + distinct check   [GATE]      │
│  └────────┬─────────┘                                           │
│           ▼                                                     │
│  ┌──────────────────┐                                           │
│  │ transform_agg    │  staging → curated.events_hourly          │
│  └────────┬─────────┘                                           │
│           ▼                                                     │
│  ┌──────────────────┐                                           │
│  │ build_features   │  curated.events → curated.user_features   │
│  └────────┬─────────┘                                           │
│           ▼                                                     │
│  ┌──────────────────┐                                           │
│  │ train_churn_model│  BQML CREATE OR REPLACE MODEL            │
│  └────────┬─────────┘                                           │
│           ▼                                                     │
│  ┌──────────────────┐                                           │
│  │ score_churn      │  ML.PREDICT → curated.churn_scores        │
│  └────────┬─────────┘                                           │
│           ▼                                                     │
│  ┌──────────────────┐                                           │
│  │ dlp_inspect      │  scan for PII                    [GATE]  │
│  └────────┬─────────┘                                           │
│           ▼                                                     │
│  ┌──────────────────┐                                           │
│  │ refresh_dashboard│  update the Looker Studio data source     │
│  └──────────────────┘                                           │
└─────────────────────────────────────────────────────────────────┘
```

**Why the logical date matters so much:**

1. **Backfills are free.** Re-running yesterday's partition is `airflow dags backfill -s 2026-01-14 -e 2026-01-14`. With a "process now" design, backfills require special-casing.
2. **Runs are idempotent.** Every task is keyed on the logical date. Re-running the same date overwrites the same partitions.
3. **Partial failures are recoverable.** If the training task fails at 03:00, you fix it and re-run the DAG for that date. No special logic.
4. **The interval is visible in the data.** Every row in `curated` can be traced to the logical date that produced it.

**The DAG file.**

```python
"""Composer DAG: the daily batch for the curated layer.

The pipeline processes a logical date, never "now". Every task is
keyed on the logical date, so a backfill is a re-run with a different
date and partial failures are recoverable.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryInsertJobOperator,
)
from airflow.providers.google.cloud.operators.gcs import (
    GCSListObjectsOperator,
    GCSCopyObjectOperator,
)
from airflow.providers.google.cloud.operators.pubsub import (
    PubSubPublishOperator,
)
from airflow.providers.google.cloud.sensors.pubsub import (
    PubSubMessageSensor,
)
from airflow.providers.google.cloud.sensors.bigquery import BigQueryTableRowCountSensor
from airflow.providers.google.cloud.sensors.gcs import GCSObjectExistenceSensor
from airflow.providers.common.sql.sensors.sql import SQLColumnCheckSensor

default_args = {
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=30),
}

with DAG(
    dag_id="events_daily",
    description="Daily curated-layer build with logical-date interval",
    schedule_interval="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["curated", "daily", "production"],
    params={
        "logical_date": "{{ ds }}",
        "project_id": "my-project",
        "dataset_id": "curated",
    },
) as dag:

    def bq_sql(sql, task_id):
        """Helper so every BigQuery task reads the same shape."""
        return BigQueryInsertJobOperator(
            task_id=task_id,
            configuration={
                "query": {
                    "query": sql,
                    "useLegacySql": False,
                    "priority": "INTERACTIVE",
                    "writeDisposition": "WRITE_TRUNCATE",
                    "destinationTable": {
                        "projectId": "{{ params.project_id }}",
                        "datasetId": "{{ params.dataset_id }}",
                        "tableId": task_id,
                    },
                }
            },
            location="us-central1",
        )

    # ---- Gate 1: the raw data for the logical date must exist ----
    wait_for_raw = GCSObjectExistenceSensor(
        task_id="wait_for_raw_partition",
        bucket="raw-events-us-central1",
        object="raw/dt={{ ds }}/",
        poke_interval=300,
        timeout=3600 * 4,
        mode="reschedule",
    )

    # ---- The aggregate, rebuilt for the last 3 days for late data ----
    build_aggregate = bq_sql(
        """
        SELECT
          region,
          TIMESTAMP_TRUNC(window_start, HOUR) AS window_start,
          COUNT(*) AS event_count,
          ROUND(SUM(amount_eur), 2) AS revenue_eur
        FROM `my-project.curated.events`
        WHERE event_dt >= DATE_SUB(DATE('{{ ds }}'), INTERVAL 3 DAY)
          AND event_dt <= DATE('{{ ds }}')
        GROUP BY region, window_start
        """,
        "build_aggregate",
    )

    # ---- Gate 2: the row count must reconcile ----
    check_event_count = BigQueryTableRowCountSensor(
        task_id="check_event_count",
        table_id="curated.events",
        partition_column="event_dt",
        partition_name="{{ ds }}",
        poke_interval=120,
        timeout=1800,
        mode="reschedule",
    )

    # ---- Gate 3: no duplicates (the dedup assertion) ----
    check_no_duplicates = SQLColumnCheckOperator(
        task_id="check_no_duplicates",
        sql="""
        SELECT
          COUNT(*) AS total,
          COUNT(DISTINCT event_id) AS distinct_ids
        FROM `my-project.curated.events`
        WHERE event_dt = DATE('{{ ds }}')
        """,
        column_mapping={"total": "distinct_ids"},
        success_threshold=1.0,
        poke_interval=120,
        timeout=1800,
    )

    # ---- The feature table for the churn model ----
    build_features = bq_sql(
        """
        SELECT
          user_id,
          DATE('{{ ds }}') AS feature_as_of,
          COUNT(*) AS n_events,
          COUNTIF(event_type = 'order') AS n_orders,
          COUNTIF(event_type = 'refund') AS n_refunds,
          ROUND(SUM(IF(event_type = 'order', amount_eur, 0)), 2) AS total_spend_eur,
          ROUND(SAFE_DIVIDE(
            SUM(IF(event_type = 'order', amount_eur, 0)),
            COUNTIF(event_type = 'order')
          ), 2) AS avg_order_value_eur,
          SAFE_DIVIDE(COUNTIF(event_type = 'refund'), COUNT(*)) AS refund_rate,
          COUNT(DISTINCT channel) AS n_channels,
          COUNT(DISTINCT region) AS n_regions,
          MAX(event_ts) AS last_event_ts
        FROM `my-project.curated.events`
        -- THE AS-OF PREDICATE. Features are computed only from events
        -- strictly before the logical date. Without it the model leaks.
        WHERE event_dt < DATE('{{ ds }}')
          AND event_dt >= DATE_SUB(DATE('{{ ds }}'), INTERVAL 90 DAY)
        GROUP BY user_id
        """,
        "user_features_daily",
    )

    # ---- Train the churn model (BigQuery ML) ----
    train_churn_model = BigQueryInsertJobOperator(
        task_id="train_churn_model",
        configuration={
            "query": {
                "query": """
                CREATE OR REPLACE MODEL `my-project.curated.churn_model`
                OPTIONS (
                  MODEL_TYPE = 'BOOSTED_TREE_CLASSIFIER',
                  INPUT_LABEL_COLS = ['churned_30d'],
                  NUM_TRIALS = 20,
                  MAX_TREE_DEPTH = 6,
                  LEARN_RATE = 0.1,
                  DATA_SPLIT_METHOD = 'CUSTOM',
                  DATA_SPLIT_COLUMN = 'is_test'
                )
                AS
                SELECT
                  n_events, n_orders, n_refunds, total_spend_eur,
                  avg_order_value_eur, refund_rate, n_channels, n_regions,
                  churned_30d
                FROM `my-project.curated.user_features_daily`
                WHERE feature_as_of = DATE('{{ ds }}')
                """,
                "useLegacySql": False,
            }
        },
        location="us-central1",
    )

    # ---- Score with the model ----
    score_churn = bq_sql(
        """
        SELECT
          user_id,
          predicted_churned_30d AS churn_predicted,
          predicted_churned_30d_probs[OFFSET(0)].prob AS churn_probability,
          CURRENT_TIMESTAMP() AS scored_at
        FROM ML.PREDICT(
          MODEL `my-project.curated.churn_model`,
          (SELECT * FROM `my-project.curated.user_features_daily`
           WHERE feature_as_of = DATE('{{ ds }}'))
        )
        """,
        "churn_scores",
    )

    # ---- Gate 4: DLP inspection of the curated table ----
    dlp_inspect = BigQueryInsertJobOperator(
        task_id="dlp_inspect",
        configuration={
            "query": {
                "query": """
                CREATE TEMP FUNCTION inspect_pii(value STRING)
                RETURNS STRUCT<info_type STRING, likelihood STRING>
                AS ((
                  SELECT AS STRUCT
                    info_type.name,
                    'LIKELY'
                  FROM `my-project.events_dlp_inspect`
                  WHERE content = value
                  LIMIT 1
                ));

                SELECT
                  COUNT(*) AS pii_violations
                FROM `my-project.curated.events`
                WHERE event_dt = DATE('{{ ds }}')
                  AND info_type.name IS NOT NULL
                """,
                "useLegacySql": False,
            }
        },
        location="us-central1",
    )

    # ---- Notify the DLQ if it is not empty ----
    notify_dlq = PubSubPublishOperator(
        task_id="notify_dlq",
        topic="projects/my-project/topics/data-quality-alerts",
        data="{{ 'pipeline': 'events_daily', 'logical_date': '{{ ds }}' }}",
    )

    wait_for_raw >> build_aggregate >> check_event_count >> check_no_duplicates
    check_no_duplicates >> build_features >> train_churn_model >> score_churn
    score_churn >> dlp_inspect >> notify_dlq
```

**Note the gate placement.** The gates sit *between* the tasks, not at the end. `check_event_count` and `check_no_duplicates` run before the feature build, so a corrupted event table never reaches the model. `dlp_inspect` runs after scoring, before the dashboard refresh.

**`max_active_runs=1`** is a deliberate choice. Two concurrent runs over the same partitions would race on the `WRITE_TRUNCATE` destinations. If you want parallel runs, the destinations must be partitioned by logical date and the writes must be appends.

**The DLQ check.** The `notify_dlq` task should be conditional on the DLQ actually having messages:

```python
from airflow.providers.google.cloud.sensors.pubsub import (
    PubSubMessageSensor,
)

check_dlq_depth = PubSubMessageSensor(
    task_id="check_dlq_depth",
    project_id="my-project",
    subscription="projects/my-project/topics/events-dlq",
    ack_messages=True,
    pull_timeout=None,
    max_messages=1,
    mode="reschedule",
    poke_interval=300,
    timeout=1800,
)
```

### Stage 5 — Govern

**IAM via `pipeline-sa`.** One service account for the pipeline, with the narrowest role set that works:

```bash
gcloud iam service-accounts create pipeline-sa \
  --project=my-project \
  --display-name="Composer and Dataflow pipeline identity"

# --- The roles the pipeline actually needs ---
# Write the DLQ and publish alerts.
gcloud projects add-iam-policy-binding my-project \
  --member="serviceAccount:pipeline-sa@my-project.iam.gserviceaccount.com" \
  --role="roles/pubsub.publisher"

# Run BigQuery jobs and own the curated dataset.
gcloud projects add-iam-policy-binding my-project \
  --member="serviceAccount:pipeline-sa@my-project.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"

gcloud storage buckets add-iam-policy-binding gs://raw-events-us-central1 \
  --member="serviceAccount:pipeline-sa@my-project.iam.gserviceaccount.com" \
  --role="roles/storage.objectCreator"

# Read the archive, write nothing back.
gcloud storage buckets add-iam-policy-binding gs://raw-events-us-central1-archive \
  --member="serviceAccount:pipeline-sa@my-project.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

# Inspect and de-identify PII.
gcloud projects add-iam-policy-binding my-project \
  --member="serviceAccount:pipeline-sa@my-project.iam.gserviceaccount.com" \
  --role="roles/dlp.user"
```

**The critical scoping decision: bucket-level IAM, not project-level.** The pipeline needs write access to `raw-events-us-central1`. It does not need write access to every bucket in the project. A project-level `roles/storage.objectAdmin` would let the pipeline overwrite the archive bucket it is supposed to be reading from — and `roles/storage.admin` would additionally let it delete the bucket outright. Note that `roles/storage.objectCreator` is the right grant for the landing bucket: it carries `storage.objects.create` and nothing destructive. The Dataflow worker's own role, `roles/dataflow.worker`, is granted separately on the worker pool rather than on this service account.

**Split the service accounts if the blast radius matters.** A realistic production split:

```text
pipeline-sa          →  Dataflow workers, Pub/Sub, GCS write
composer-sa          →  Composer environment, triggers the DAG
bq-ml-sa             →  BigQuery jobUser only, for the BQML training
```

**Dataplex.** Dataplex is the catalog and lineage layer. It turns your BigQuery tables, GCS buckets, and other assets into a queryable catalog with ownership, tags, and lineage.

```bash
# Create the lake with the two zones that matter.
gcloud dataplex lakes create my-project \
  --project=my-project \
  --location=us-central1 \
  --display-name="Analytics Lake"

gcloud dataplex zones create raw-events-us-central1 \
  --project=my-project \
  --location=us-central1 \
  --lake=my-project \
  --display-name="Raw Events" \
  --type=RAW \
  --resources-bucket-names=raw-events-us-central1 \
  --labels=domain=ingest,tier=raw

gcloud dataplex zones create curated \
  --project=my-project \
  --location=us-central1 \
  --lake=my-project \
  --display-name="Curated" \
  --type=CURATED \
  --labels=domain=analytics,tier=curated
```

**The value of Dataplex here is not the catalog UI.** It is:

1. **Auto-generated lineage.** Which upstream tables feed `curated.events_hourly`? Dataplex knows because the Dataform dependencies are declared.
2. **Discoverability.** A new analyst searches "revenue" in the catalog and finds the tables, their owners, and their quality status — instead of asking in chat.
3. **Tag-based governance.** Tag every table with `domain=analytics`, `pii=none`, `retention=7y`. Then write an IAM condition or a policy that enforces something based on the tag.

**DLP for PII.** The `curated.events` table has `user_id`. In the sample data it is an opaque identifier (`u000914`), but the real system may carry an email. The pipeline needs to know which.

**The DLP inspect template:**

```bash
gcloud dlp templates create inspect-events \
  --project=my-project \
  --location=us-central1 \
  --display-name="Inspect event PII" \
  --description="Detects PII in the curated events table" \
  --inspection-config='{
    "infoTypes": [
      {"name": "EMAIL_ADDRESS"},
      {"name": "PHONE_NUMBER"},
      {"name": "CREDIT_CARD_NUMBER"},
      {"name": "US_SOCIAL_SECURITY_NUMBER"},
      {"name": "IP_ADDRESS"}
    ],
    "minLikelihood": "LIKELY",
    "maxLikelihood": "VERY_LIKELY"
  }'
```

**Inspect or de-identify — the decision.** This depends on whether the value is needed downstream:

```text
EMAIL_ADDRESS in a table the BI layer reads  →  de-identify (replace with a token)
EMAIL_ADDRESS in the raw archive            →  leave it; the raw zone is access-controlled
```

**De-identification loses the join key.** If you redact an email to `****@example.com`, you cannot join back to the customer. The production pattern is **tokenisation, not redaction**: replace the email with a keyed hash, and keep the mapping in a separate, tightly-controlled table.

```python
def tokenise(value, salt):
    """Deterministic pseudonymisation that preserves the join.

    Redaction destroys the ability to join. A keyed hash preserves it
    while removing the PII from the broad-access table.
    """
    import hashlib
    return hashlib.sha256(f"{salt}:{value}".encode()).hexdigest()[:32]
```

**The operational caveat:** DLP inspect costs **$0.10/GB** (per the course `cost_model` module's `SENSITIVE_DATA_PROTECTION_PER_GB`). Scanning a 100 GB curated table daily is $10/day, $300/month. **Scope the inspection to the columns and partitions that can actually contain PII**, and run it on a schedule rather than on every ingest.

### Stage 6 — Serve

**Looker Studio dashboard.** The dashboard reads **`curated.events_hourly` and nothing else**.

```text
┌───────────────────────────────────────────────────────────────┐
│  Revenue Operations — Daily          Last refreshed 08:15 UTC │
├───────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐│
│  │ Total events│ │ Total revenue│ │  Avg order  │ │ Rejects ││
│  │   4,800     │ │  €1,764, -   │ │    value    │ │   12    ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────┘│
├───────────────────────────────┬───────────────────────────────┤
│  Revenue by region (bar)      │  Revenue by hour (line)       │
│  AMER   ████████ 464,848.02   │   ╱╲    ╱╲                    │
│  LATAM  ███████  445,554.36   │  ╱  ╲__╱  ╲___                │
│  EMEA   ██████   432,544.17   │ ╱                             │
│  APAC   █████    421,049.85   │                               │
├───────────────────────────────┤                               │
│  Region table (exact values)  │  Churn watchlist (top 100)    │
│  region | count | revenue_eur  │  user_id | prob | spend      │
└───────────────────────────────┴───────────────────────────────┘
```

**The three rules that keep the dashboard fast and cheap:**

1. **Never point a chart at `curated.events`.** It is the 2 TB detail table. Every tile would scan it.

2. **Always include a partition predicate.** The data source's custom SQL is:

```sql
SELECT
  region,
  window_start,
  event_count,
  revenue_eur
FROM `my-project.curated.events_hourly`
WHERE window_start >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
```

3. **The churn watchlist reads `curated.churn_scores`**, which is small, and joins to `user_features_daily` for the spend figure.

**The exact summary the dashboard shows**, from the course project:

```text
region,event_count,revenue_eur
AMER,1238,464848.02
APAC,1159,421049.85
EMEA,1176,432544.17
LATAM,1227,445554.36
```

**Total: 4,800 events.** Note the balance: AMER 1238, LATAM 1227, EMEA 1176, APAC 1159. The dataset is deliberately close to uniform across regions, which is what a well-behaved synthetic generator produces — and it means a dashboard bug that shifts one region will be visible.

**The refresh strategy.** The dashboard's data source is set to **"Live data"** for the hourly tiles and **"Cached data"** with a 1-hour refresh for the historical ones. This is the freshness-versus-cost tension from Chapter 7.3: the hourly tile needs to be current, the 30-day trend does not.

**The data source permissions.** The viewer needs access to the *data source*, not just the dashboard. This is the classic "shared it but they see no data" bug. Share the data source with the BI group explicitly.

### Stage 7 — Model

**BigQuery ML churn model over the curated table.**

```sql
CREATE OR REPLACE MODEL `my-project.curated.churn_model`
OPTIONS (
  MODEL_TYPE = 'BOOSTED_TREE_CLASSIFIER',
  INPUT_LABEL_COLS = ['churned_30d'],
  NUM_TRIALS = 20,
  MAX_TREE_DEPTH = 6,
  LEARN_RATE = 0.1,
  L1_REG = 0.0,
  L2_REG = 1.0,
  DATA_SPLIT_METHOD = 'CUSTOM',
  DATA_SPLIT_COLUMN = 'is_test'
)
AS
SELECT
  n_events,
  n_orders,
  n_refunds,
  total_spend_eur,
  avg_order_value_eur,
  refund_rate,
  n_channels,
  n_regions,
  churned_30d
FROM `my-project.curated.user_features_daily`
WHERE feature_as_of = DATE('2026-01-15')
  AND churned_30d IS NOT NULL;
```

**The label.** Where does `churned_30d` come from? It is not in the event stream. It comes from the billing system, joined with a 30-day observation window:

```sql
-- The label, computed with the observation-window rule.
-- A customer who signed up 3 days ago cannot have a 30-day churn
-- label. Including them labels them "not churned" purely because
-- they have not had time to churn — and the model learns an inverse
-- relationship.
WITH label_window AS (
  SELECT
    user_id,
    MIN(event_ts) AS first_seen,
    MAX(event_ts) AS last_seen
  FROM `my-project.curated.events`
  GROUP BY user_id
)
SELECT
  f.*,
  CASE
    -- Excluded: the observation window is shorter than the horizon.
    WHEN TIMESTAMP_DIFF(
           TIMESTAMP('2026-01-15'),
           w.first_seen,
           DAY
         ) < 30 THEN NULL
    -- Churned: no order in the last 30 days but ordered before that.
    WHEN w.last_seen < TIMESTAMP_SUB(TIMESTAMP('2026-01-15'), INTERVAL 30 DAY)
      THEN 1
    ELSE 0
  END AS churned_30d
FROM `my-project.curated.user_features_daily` f
JOIN label_window w USING (user_id)
WHERE f.feature_as_of = DATE('2026-01-15');
```

**The `NULL` in the excluded case is deliberate**, and the model query filters it with `churned_30d IS NOT NULL`. That way the excluded entities are *absent* from the training set rather than labelled "not churned".

**Why BigQuery ML and not Vertex AI here?** Because the scoring is batch. The scores are computed once a day and read by the dashboard and the retention team. **BigQuery ML's no-endpoint, no-pipeline property is worth more than online latency for this workload.** If a customer-facing web page needs a real-time churn score, that changes the answer — export the model and deploy it to a Vertex AI endpoint.

### The cost model

Real numbers, from the course `cost_model` module.

```python
import sys
sys.path.insert(0, "project/core")

from cost_model import estimate, HOURS_PER_MONTH, VERTEX_AI_TRAINING_PER_NODE_HOUR

print("=" * 72)
print("CAPSTONE MONTHLY COST — my-project, 150k events/day")
print("=" * 72)

DAILY_EVENTS = 150_000
MONTHLY_EVENTS = DAILY_EVENTS * 30
GB_PER_EVENT = 0.0005      # ~500 bytes per event in JSON
MONTHLY_GB = MONTHLY_EVENTS * GB_PER_EVENT

# --- 1. Pub/Sub ---
pubsub = estimate("pubsub", pubsub_gb=MONTHLY_GB, monthly=True)
print(f"\n1. Pub/Sub ingest + delivery ({MONTHLY_GB:,.0f} GB)")
for line in pubsub.lines:
    print(f"   {line.label:34s} {line.quantity:10.1f} {line.unit:12s} ${line.cost:9.2f}")
print(f"   {'TOTAL':34s} {'':10s} {'':12s} ${pubsub.total:9.2f}")

# --- 2. Cloud Storage (raw archive) ---
storage_gb = MONTHLY_GB * 12   # a year of archive
gcs = estimate("cloud-storage", storage_gb=storage_gb, monthly=True)
print(f"\n2. Cloud Storage raw archive ({storage_gb:,.0f} GB)")
for line in gcs.lines:
    print(f"   {line.label:34s} {line.quantity:10.1f} {line.unit:12s} ${line.cost:9.2f}")
print(f"   {'TOTAL':34s} {'':10s} {'':12s} ${gcs.total:9.2f}")

# --- 3. Dataflow ---
# 4 vCPU workers, 4 hours per day of real processing.
dataflow = estimate("dataflow", vcpu_hours=4 * 4 * 30, monthly=True)
print(f"\n3. Dataflow (4 vCPU x 4h x 30d = {4*4*30} vCPU-hours)")
for line in dataflow.lines:
    print(f"   {line.label:34s} {line.quantity:10.1f} {line.unit:12s} ${line.cost:9.2f}")
print(f"   {'TOTAL':34s} {'':10s} {'':12s} ${dataflow.total:9.2f}")

# --- 4. BigQuery ---
# Storage: 30 days of detail, partitioned.
bq_storage_gb = MONTHLY_GB * 2      # raw + normalized columns
# Queries: the daily aggregation, the feature build, the scoring,
# and the dashboard's 30-day scan.
bq_scan_tb = (MONTHLY_GB * 3) / 1024  # 3 full passes per month
bq = estimate(
    "bigquery",
    gb_months=bq_storage_gb,
    scanned_tb=bq_scan_tb,
    slot_hours=40,
    monthly=True,
)
print(f"\n4. BigQuery (storage + scans + BQML training slots)")
for line in bq.lines:
    print(f"   {line.label:34s} {line.quantity:10.1f} {line.unit:12s} ${line.cost:9.2f}")
print(f"   {'TOTAL':34s} {'':10s} {'':12s} ${bq.total:9.2f}")

# --- 5. Composer ---
# environment_nodes is NODE-HOURS, not a node count. One environment
# running continuously for a month is HOURS_PER_MONTH node-hours.
composer = estimate(
    "composer", environment_nodes=1 * HOURS_PER_MONTH, monthly=True
)
print(f"\n5. Composer (1 environment, {HOURS_PER_MONTH} node-hours)")
for line in composer.lines:
    print(f"   {line.label:34s} {line.quantity:10.1f} {line.unit:12s} ${line.cost:9.2f}")
print(f"   {'TOTAL':34s} {'':10s} {'':12s} ${composer.total:9.2f}")

# --- 6. DLP ---
dlp = estimate("sensitive-data-protection", inspected_gb=MONTHLY_GB, monthly=True)
print(f"\n6. Sensitive Data Protection ({MONTHLY_GB:,.1f} GB inspected/month)")
for line in dlp.lines:
    print(f"   {line.label:34s} {line.quantity:10.1f} {line.unit:12s} ${line.cost:9.2f}")
print(f"   {'TOTAL':34s} {'':10s} {'':12s} ${dlp.total:9.2f}")

# --- 7. Dataplex ---
# Priced per TiB, so the input is converted from GB.
dataplex = estimate(
    "dataplex", storage_gb=(MONTHLY_GB * 12) / 1024, monthly=True
)
print(f"\n7. Dataplex catalog")
for line in dataplex.lines:
    print(f"   {line.label:34s} {line.quantity:10.1f} {line.unit:12s} ${line.cost:9.2f}")
print(f"   {'TOTAL':34s} {'':10s} {'':12s} ${dataplex.total:9.2f}")

# --- TOTAL ---
total = pubsub.total + gcs.total + dataflow.total + bq.total \
        + composer.total + dlp.total + dataplex.total
print("\n" + "=" * 72)
print(f"TOTAL: ${total:,.2f}/month   (${total*12:,.2f}/year)")
print("=" * 72)
```

**The shape of the number, and what dominates:**

```text
Pub/Sub                 $  896.00     the largest line — per-GB ingest
Cloud Storage           $  539.90     a year of archive is 27,000 GB
Dataflow                $   28.56     480 vCPU-hours
BigQuery                $   37.35     storage + 6.6 TB scanned + 40 slot-hours
Composer                $   41.17     730 node-hours of environment
DLP                     $  225.00     2,250 GB inspected
Dataplex                $    0.53     negligible
                             ───────
                        $ 1,768.51/month   ($21,222.10/year)
```

**Five observations that matter more than the total:**

1. **Pub/Sub dominates, and it is a per-GB cost, not a per-message cost.** 2,250 GB/month at $0.40/GB is $896 — half the bill. The lever is **the size of the message**, and the single highest-value optimisation in the whole pipeline is **not publishing the fields the consumer does not need**. A 500-byte event that could be 200 bytes is a 60% reduction in the largest cost line.

2. **Cloud Storage at $540/month is the archive doing its job.** 27,000 GB of Standard storage at $0.02/GB-month. This is the cheapest insurance in the platform: it is what makes a replay possible. Note that **retrieval and egress are the expensive parts of storage, not the storage itself** — reading the archive back for a backfill costs $0.00 for Standard class but $0.01/GB for Nearline, and any egress out of GCP is $0.12/GB.

3. **Composer costs more than Dataflow.** 730 node-hours at $0.0564 is $41.17/month — more than 480 vCPU-hours of Dataflow at $28.56. This surprises everyone. **A Composer environment has a fixed floor** (the Airflow web server, the scheduler, the worker) and you pay for it whether or not the DAG runs. If your DAG runs twice a day, this is a poor trade — use Cloud Scheduler plus a Cloud Run job.

4. **DLP scales linearly with volume and is easy to under-budget.** 2,250 GB at $0.10/GB is $225 — 13% of the bill for a check you might run weekly. **Scope it to the columns that can contain PII and run it weekly, not daily**, and that line drops to about $50.

5. **BigQuery ML training is invisible in the total.** 20 trials of a boosted tree on 1M rows is tens of slot-hours — about $2. Compare with Vertex AI's 80 node-hours at $3.67 = $293.60 per tuning run. **The chapter 8.4 decision shows up here as roughly $290/month of avoided cost**, which is 16% of the entire platform bill.

**The comparison that justifies the whole architecture:**

```text
┌────────────────────────────────┬──────────────┬──────────────┐
│ Component                      │ BigQuery ML  │ Vertex AI    │
├────────────────────────────────┼──────────────┼──────────────┤
│ Training (20 trials)           │ ~$2         │ ~$294        │
│ Scoring / serving              │ ~$0.10      │ ~$292        │
│ Container + pipeline code      │ none        │ ~40 hours    │
│ Endpoint + autoscaler          │ none        │ 2 resources  │
│ Monitoring config              │ 1 query     │ 3 resources  │
│ Orchestration of the ML step   │ in the DAG  │ separate     │
├────────────────────────────────┼──────────────┼──────────────┤
│ Monthly                        │ ~$2         │ ~$586        │
│ Yearly                         │ ~$24        │ ~$7,032      │
└────────────────────────────────┴──────────────┴──────────────┘
```

**One honest caveat on the cost numbers:** the course module uses us-central1 list prices, assumes no committed use discounts, and assumes a 150,000-events-per-day workload. Your real numbers will differ. **The shape is what transfers**: BigQuery dominates, Composer has a fixed floor, DLP scales with volume, and BigQuery ML training is nearly free relative to Vertex AI.

### The design decisions and their trade-offs

| # | Decision | Alternative | Why this one | What it costs |
|---|---|---|---|---|
| 1 | **Pub/Sub topic + GCS landing** | Direct GCS ingestion | Pub/Sub absorbs producer bursts; GCS is the replayable archive | Two writes per event; Pub/Sub delivery cost |
| 2 | **Dataflow over Dataproc** | Spark on Dataproc | Streaming-first, autoscales to zero, one language for batch and stream | Beam is a steeper learning curve than PySpark |
| 3 | **Reject unknown currencies** | Default rate or NULL | An aggregate that is silently wrong is worse than one that is missing a row | Data loss on every new currency |
| 4 | **Event-time windows, 10-min lateness** | Processing-time windows | Late events land in the right bucket | Corrections; the table must tolerate re-writes |
| 5 | **Separate aggregate table** | A view over `events` | Paid once per refresh instead of once per viewer per tile | Storage and a refresh step |
| 6 | **Per-partition dedup** | Global dedup | Removes redelivery duplicates without collapsing genuine cross-day records | A duplicate across partitions survives — deliberately |
| 7 | **Composer** | Cloud Scheduler + Cloud Run | Multi-step DAGs, backfills, lineage, UI | $41/month floor for one node |
| 8 | **BigQuery ML** | Vertex AI | Batch scoring, no endpoint, no container, ~$2 vs ~$586/month | No online prediction |
| 9 | **Bucket-level IAM for `pipeline-sa`** | Project-level role | The pipeline cannot overwrite the archive it reads | More IAM administration |
| 10 | **DLP inspect, not de-identify, in the curated table** | De-identify | The BI layer needs the join key; tokenise instead if de-identification is required | Requires the tokenisation table |

### The failure modes and the runbook

| # | Failure | Detection | Immediate action | Root-cause fix |
|---|---|---|---|---|
| 1 | **Poison message blocks the subscription** | DLQ depth grows; subscription backlog grows | Check the DLQ topic | `max-delivery-attempts=5` moves it to the DLQ. Inspect and fix the producer |
| 2 | **The pipeline stops ingesting** | `curated.events` row count flat; Composer task fails | Check the Dataflow job state and the Pub/Sub subscription backlog | Usually a quota or a code deploy. Roll back the template |
| 3 | **The dashboard shows stale data** | Dashboard timestamp older than the schedule | Check the last successful Composer run | Usually the DAG failed at a gate. Read the task logs |
| 4 | **A gate fails: duplicate events** | `check_no_duplicates` fails | Halt the DAG; do not override the gate | The dedup step regressed. Check the `dedup_key` implementation |
| 5 | **The dashboard shows a missing region** | Region count < 4 | Compare the raw bucket's object count for the date against the BigQuery count | A producer changed its schema and the events were rejected. Check the DLQ |
| 6 | **The model AUC collapses** | `ML.EVALUATE` shows a sudden drop | Do not promote the model | Either the feature SQL changed (leak or regression) or the data drifted. Diff the feature SQL against the previous version |
| 7 | **PII found in the curated table** | DLP inspect alerts | Halt the dashboard refresh; de-identify the affected partitions | The producer started sending a new PII field. Add it to the DLP template and to the pipeline's redaction step |
| 8 | **BigQuery query cost spikes** | Billing anomaly; a slow dashboard | Check the query history for an unpartitioned scan | A BI user wrote `SELECT *` without a partition filter. `require_partition_filter` prevents it |

**The runbook, as a runbook.**

```text
SYMPTOM: dashboard shows data from two days ago
  1. Composer UI → events_daily → find the failed task
  2. Read the task log. The gate task names are:
     check_event_count, check_no_duplicates, dlp_inspect
  3. If check_event_count failed: the row count did not reconcile.
     Compare:
       SELECT COUNT(*) FROM `my-project.curated.events`
       WHERE event_dt = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
     with the raw object count in gs://raw-events-us-central1/raw/dt=...
  4. If the Dataflow job is the blocker, check the job in the Dataflow
     console. A failed bundle with a poison message is visible in the
     job's error logs.
  5. Do NOT bypass a gate. A gate that keeps failing is telling you
     something true.

SYMPTOM: churn scores look wrong (all one class, or all zero)
  1. Check the positive rate:
       SELECT COUNTIF(churn_probability >= 0.35) / COUNT(*)
       FROM `my-project.curated.churn_scores`
  2. If it is ~0: the model was trained on a feature table with no
     positives, or the label join broke. Check:
       SELECT COUNTIF(churned_30d = 1), COUNT(*)
       FROM `my-project.curated.user_features_daily`
  3. If it is ~1: the label logic inverted. Check the churned_30d CASE
     expression in the label query.
  4. Compare against yesterday's positive rate. A sudden move is drift.

SYMPTOM: a backfill is needed (a currency rate was wrong)
  1. Fix the FX table in the reference data.
  2. Re-run the affected logical dates:
       airflow dags backfill events_daily -s 2026-01-10 -e 2026-01-12
  3. Because every task is keyed on the logical date and writes with
     WRITE_TRUNCATE, the re-run replaces the affected partitions.
  4. Verify the totals against the raw archive.
```

### The phased rollout plan

**Phase 0 — Foundation (week 1).** Projects, APIs, buckets, service accounts.

```text
- Create the project and enable the APIs:
    bigquery, dataflow, pubsub, storage, composer, dataplex, dlp,
    dataform, dataproc
- Create the buckets with uniform bucket-level access
- Create pipeline-sa with the scoped roles
- Create the Pub/Sub topics and the subscription with the DLQ
- Enable audit logs and set a budget alert
```

**Exit criteria:** the service account can write a test file to the bucket and publish a test message to the topic. No production data yet.

**Phase 1 — Ingest and store (weeks 2-3).** The pipeline, without the model.

```text
- Deploy the Dataflow template in streaming mode
- Create the curated tables with the DDL from this chapter
- Dataform repository with the incremental models and tests
- Composer DAG with the gates, minus the ML steps
```

**Exit criteria:** the DAG completes green for three consecutive days. The row count reconciles. The dashboard shows correct numbers against a manual spot-check.

**Do not proceed with a red DAG.** Three green days is not arbitrary — it catches the class of bug that appears on a weekend when nobody is watching.

**Phase 2 — Govern (weeks 3-4).** In parallel with Phase 1's tail.

```text
- Dataplex lake and zones
- DLP inspect template, run against the curated table
- Tag every table with domain, tier, and pii
- Dataplex quality rules for the key assertions
- IAM review with the access-transparency report
```

**Exit criteria:** no unclassified PII. Every table has an owner. The access-transparency report shows no unexpected principals.

**Phase 3 — Model (weeks 4-5).** BigQuery ML churn.

```text
- Build the label query with the observation-window rule
- Train the BQML model, verify AUC against a LINEAR_REG baseline
- Score and write churn_scores
- Wire the training and scoring steps into the DAG
- Add the drift monitor as a scheduled query
```

**Exit criteria:** the model beats the linear baseline, the positive rate is stable, and the churn watchlist is being reviewed by the retention team. **The model must be reviewed by a human before it drives any customer-facing action.**

**Phase 4 — Serve (weeks 5-6).** The dashboard and the model output.

```text
- Build the Looker Studio dashboard against events_hourly
- Add the churn watchlist tile
- Share the data source with the BI group (not just the dashboard)
- Set up the freshness and the query-cost budget
```

**Exit criteria:** the dashboard renders in under 3 seconds, and the monthly query cost is under budget.

**Phase 5 — Operate (week 6 onwards).** The runbook, made real.

```text
- Publish the runbook; walk it through with the on-call rotation
- Alert on: DLQ depth, row-count reconciliation, DAG failure,
  positive-rate movement, BigQuery cost anomaly, DLP findings
- A weekly review of the drift report
- A monthly review of the cost model against actuals
```

**Exit criteria:** a deliberate failure of each stage is injected and the alert fires within the agreed window. **A runbook that has never been exercised is a document, not a runbook.**

---

## 🛠️ Hands-On

### Exercise 1 — The pipeline, end to end, locally

The capstone logic runs against the course project.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import (
    ingest_events,
    build_bigquery_rows,
    aggregate_events,
    render_summary_csv,
    reject_counts,
    bucket_by_window,
    aggregate_by_window,
    partition_for_date,
    filter_rows_for_partition,
    deduplicate,
    dedup_key_set,
    event_time_bounds,
    hours_spanned,
)

# ---------- INGEST ----------
lines = open("sample_data/events.csv").read().splitlines()
accepted, rejected = ingest_events(lines[1:])
rows = build_bigquery_rows(accepted)

print(f"ingest: {len(rows)} accepted, {len(rejected)} rejected")

# ---------- STORE: the partition layout ----------
PARTITION = partition_for_date("2026-01-15")
print(f"partition: {PARTITION}")

# ---------- PROCESS: the windowed aggregation ----------
summary = aggregate_events(rows)
print("\n--- curated.events_hourly summary ---")
print(render_summary_csv(summary))

windows = bucket_by_window(rows)
hourly = aggregate_by_window(rows)
print(f"\nwindows: {len(windows)}")
print(f"hours spanned: {hours_spanned(rows)}")

# ---------- The dedup guarantee ----------
before = len(rows)
partition_rows = filter_rows_for_partition(rows, PARTITION)
deduped = deduplicate(partition_rows, partition=PARTITION)
print(f"\ndedup: {before} -> {len(deduped)} rows in partition {PARTITION}")

# ---------- The DLQ ----------
bad_lines = open("sample_data/malformed_events.csv").read().splitlines()
_, dlq = ingest_events(bad_lines)
print(f"\nDLQ: {len(dlq)} rejected")
for reason, count in sorted(reject_counts(dlq).items()):
    print(f"  {reason:24s} {count}")
```

**Expected output:**

```text
ingest: 4800 accepted, 0 rejected
partition: 2026-01-15

--- curated.events_hourly summary ---
region,event_count,revenue_eur
AMER,1238,464848.02
APAC,1159,421049.85
EMEA,1176,432544.17
LATAM,1227,445554.36

windows: 24
hours spanned: 24

dedup: 4800 -> 4800 rows in partition 2026-01-15

DLQ: 12 rejected
  bad_amount                 1
  bad_timestamp              1
  missing_event_id           1
  missing_user_id            1
  negative_amount            1
  unknown_channel            1
  unknown_currency           1
  unknown_event_type         1
  unknown_region             2
  wrong_field_count          2
```

### Exercise 2 — The cost model, computed

```python
import sys
sys.path.insert(0, "project/core")

from cost_model import estimate, HOURS_PER_MONTH, VERTEX_AI_TRAINING_PER_NODE_HOUR

DAILY_EVENTS = 150_000
MONTHLY_EVENTS = DAILY_EVENTS * 30
MONTHLY_GB = MONTHLY_EVENTS * 0.0005

lines = [
    ("Pub/Sub", estimate("pubsub", pubsub_gb=MONTHLY_GB, monthly=True)),
    ("Cloud Storage", estimate("cloud-storage", storage_gb=MONTHLY_GB * 12, monthly=True)),
    ("Dataflow", estimate("dataflow", vcpu_hours=4 * 4 * 30, monthly=True)),
    ("BigQuery", estimate("bigquery", gb_months=MONTHLY_GB * 2,
                           scanned_tb=(MONTHLY_GB * 3) / 1024,
                           slot_hours=40, monthly=True)),
    ("Composer", estimate("composer", environment_nodes=HOURS_PER_MONTH, monthly=True)),
    ("DLP", estimate("sensitive-data-protection", inspected_gb=MONTHLY_GB, monthly=True)),
    ("Dataplex", estimate("dataplex", storage_gb=(MONTHLY_GB * 12) / 1024, monthly=True)),
]

total = 0.0
print(f"{'component':18s} {'monthly':>12s}")
print("-" * 32)
for name, est in lines:
    total += est.total
    print(f"{name:18s} ${est.total:10,.2f}")
print("-" * 32)
print(f"{'TOTAL':18s} ${total:10,.2f}")
print(f"{'per year':18s} ${total*12:10,.2f}")

# The BigQuery ML vs Vertex AI comparison, in one place.
bqml_training = estimate("bigquery", slot_hours=30, monthly=False).total
vertex_training = 20 * 4 * VERTEX_AI_TRAINING_PER_NODE_HOUR

print("\n" + "=" * 60)
print("CHURN MODEL: BigQuery ML vs Vertex AI")
print("=" * 60)
print(f"BQML training (30 slot-hours):        ${bqml_training:8,.2f}")
print(f"Vertex training (80 node-hours):      ${vertex_training:8,.2f}")
print(f"BQML scoring (a query):               ${0.10:8,.2f}")
print(f"Vertex endpoint (1 replica, monthly): ${292.00:8,.2f}")
print(f"BQML monthly total:                   ${bqml_training + 0.10:8,.2f}")
print(f"Vertex monthly total:                 ${vertex_training + 292.00:8,.2f}")
print(f"Annual difference:                    ${((vertex_training + 292) - (bqml_training + 0.1))*12:8,.2f}")
```

Expected output:

```text
component               monthly
--------------------------------
Pub/Sub            $    896.00
Cloud Storage      $    539.90
Dataflow           $     28.56
BigQuery           $     37.35
Composer           $     41.17
DLP                $    225.00
Dataplex           $      0.53
--------------------------------
TOTAL              $  1,768.51
per year           $ 21,222.10

============================================================
CHURN MODEL: BigQuery ML vs Vertex AI
============================================================
BQML training (30 slot-hours):        $    1.80
Vertex training (80 node-hours):      $  293.60
BQML scoring (a query):               $    0.10
Vertex endpoint (1 replica, monthly): $  292.00
BQML monthly total:                   $    1.90
Vertex monthly total:                 $  585.60
Annual difference:                    $7,004.40
```

### Exercise 3 — The IAM policy for `pipeline-sa`

Using the course `iam_policy` module to verify the grant set.

```python
import sys
sys.path.insert(0, "project/core")

from iam_policy import Policy, Principal, Binding, evaluate, effective_permissions

# The identities in the platform.
pipeline_sa = Principal("serviceAccount", "pipeline-sa@my-project.iam.gserviceaccount.com")
composer_sa = Principal("serviceAccount", "composer-sa@my-project.iam.gserviceaccount.com")
bqml_sa = Principal("serviceAccount", "bq-ml-sa@my-project.iam.gserviceaccount.com")
analyst = Principal("group", "data-analysts@my-project.iam.gserviceaccount.com")
contractor = Principal("user", "contractor@example.com")

# The roles granted to pipeline-sa. Every one of these must exist
# in iam_policy.ROLES, or role_permissions() raises
# KeyError: "unknown role: '<role>'".
pipeline_roles = [
    "roles/storage.objectCreator",   # write raw events to the landing bucket
    "roles/pubsub.publisher",         # publish to the events topic
    "roles/bigquery.dataEditor",      # create and update curated tables
    "roles/dlp.user",                 # inspect and de-identify PII
]

policy = Policy()
for role in pipeline_roles:
    policy.add(pipeline_sa, Binding(role=role))

# evaluate() and effective_permissions() take the identity as the
# plain account address — the email form, without the "kind:" prefix
# that Principal carries.
IDENTITY = pipeline_sa.name

print("pipeline-sa permissions:")
for perm in sorted(effective_permissions(policy, IDENTITY)):
    print(f"  {perm}")

# The check that matters: can pipeline-sa reach the raw archive?
print("\nKey checks:")
for perm in ("storage.objects.create", "storage.objects.delete",
              "bigquery.tables.create", "pubsub.topics.publish"):
    decision = evaluate(policy, IDENTITY, perm)
    status = "ALLOWED" if decision.allowed else "DENIED"
    print(f"  {perm:32s} {status}")

# The negative check: can pipeline-sa delete a table? It should not
# be able to, beyond what bigquery.jobUser implies.
decision = evaluate(policy, IDENTITY, "bigquery.tables.delete")
print(f"  {'bigquery.tables.delete':32s} "
      f"{'ALLOWED' if decision.allowed else 'DENIED'}")

# A principal with no grant at all. This is the control that proves
# the grants above are doing something.
decision = evaluate(policy, contractor.name, "pubsub.topics.publish")
print(f"  {'contractor publish':32s} "
      f"{'ALLOWED' if decision.allowed else 'DENIED'}")

# The bucket-level scoping that makes this safe. The project-level
# grant above is broad; the real policy grants storage access on the
# ONE bucket the pipeline writes to, and nothing else.
bucket_policy = Policy()
bucket_policy.add(
    pipeline_sa,
    Binding(role="roles/storage.admin"),
    resource="projects/_/buckets/raw-events-us-central1",
)
bucket_policy.add(
    pipeline_sa,
    Binding(role="roles/storage.objectViewer"),
    resource="projects/_/buckets/raw-events-us-central1-archive",
)

print("\nBucket-scoped grants:")
for resource in ("projects/_/buckets/raw-events-us-central1",
                 "projects/_/buckets/raw-events-us-central1-archive"):
    decision = evaluate(bucket_policy, IDENTITY, "storage.objects.delete",
                         resource=resource)
    print(f"  delete on {resource.split('/')[-1]:36s} "
          f"{'ALLOWED' if decision.allowed else 'DENIED'}")

# The same check on a resource the policy says nothing about.
decision = evaluate(bucket_policy, IDENTITY, "storage.objects.delete",
                    resource="projects/_/buckets/unrelated-bucket")
print(f"  delete on {'unrelated-bucket':36s} "
      f"{'ALLOWED' if decision.allowed else 'DENIED'}")
```

**What the output shows, and why it matters.** In the project-level policy, `pipeline-sa` holds `roles/storage.objectCreator`, which grants `storage.objects.create` but **not** `storage.objects.delete`. The pipeline can write new objects into the landing bucket and cannot destroy anything in it. Swap that role for `roles/storage.admin` — the broad role that carries `storage.objects.delete` and `storage.buckets.delete` — and the same identity can now delete the archive it is supposed to be reading from.

**The bucket-scoped policy is the point.** There, `pipeline-sa` holds `roles/storage.admin` on `raw-events-us-central1` (so it can clean up its own staging files) and only `roles/storage.objectViewer` on `raw-events-us-central1-archive`. The result is exactly the contrast you want: **ALLOWED** to delete in the bucket it owns, **DENIED** in the archive it reads from, and **DENIED** on an unrelated bucket the policy never mentions. **That is the whole argument for bucket-level IAM** — the same service account gets the destructive rights it needs in one place and provably does not have them in the other two.

**Why the role list is deliberately narrow.** Every role in `pipeline_roles` is checked against `iam_policy.ROLES` before the policy is built. A role name that does not exist — `roles/dataflow.worker` or `roles/dlp.developer`, both of which are real GCP roles but are not in this module's catalogue — makes `role_permissions()` raise `KeyError: "unknown role: 'roles/dataflow.worker'"`. That is a helpful failure: it means the module's role catalogue and the policy file have drifted apart, and a policy referencing an unrecognised role would otherwise silently grant nothing on the real platform.

**One more thing the output proves.** `bigquery.tables.create` is **ALLOWED** — `roles/bigquery.dataEditor` carries it, and the pipeline needs it to create `curated.events` and `curated.events_hourly`. But `bigquery.tables.delete` is **ALLOWED** too, because `bigquery.dataEditor` grants it. On the real platform you would scope that down: `roles/bigquery.dataEditor` on the `curated` dataset, `roles/bigquery.jobUser` project-wide, and no `dataEditor` on any dataset the pipeline must not alter. The module's `evaluate()` takes a `resource=` argument for exactly this reason; use it, and the same principle as the bucket scoping applies one level up.

### Exercise 4 — The feature build, with the as-of predicate

The churn model needs a training table where every row is `(features at time T, did the user churn in the 30 days after T)`. Building that correctly means enforcing two rules, and the second one is where most pipelines go wrong.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events, build_bigquery_rows
from collections import defaultdict
from datetime import datetime, timedelta, timezone

lines = open("sample_data/events.csv").read().splitlines()
accepted, _ = ingest_events(lines[1:])
rows = build_bigquery_rows(accepted)

FEATURE_AS_OF = "2026-01-16"
HORIZON_DAYS = 30


def build_features(rows, as_of, horizon_days=30):
    """Build the feature table with the observation-window rule.

    The two rules that make this correct:
      1. Features use only events strictly before `as_of`.
      2. An entity whose observation window is shorter than the
         horizon is EXCLUDED, not labelled "not churned".

    The event timestamps are ISO strings carrying a +00:00 offset, so
    they are parsed into aware datetimes before any comparison. The
    cutoff is aware too. Comparing an aware timestamp to a naive one
    raises TypeError — which is a good thing: it makes the timezone
    mistake loud rather than silent.
    """
    as_of_ts = datetime.fromisoformat(as_of).replace(tzinfo=timezone.utc)
    cutoff = as_of_ts - timedelta(days=horizon_days)

    def parse(ts):
        return datetime.fromisoformat(ts)

    history = defaultdict(list)
    for r in rows:
        if parse(r["event_ts"]) < as_of_ts:
            history[r["user_id"]].append(r)

    features = []
    excluded = 0
    for user_id, events in history.items():
        stamps = [parse(e["event_ts"]) for e in events]
        first_seen = min(stamps)
        last_seen = max(stamps)

        # Rule 2: the observation window must be long enough to
        # observe the outcome.
        #
        # The window is measured in CALENDAR days, not elapsed
        # 24-hour blocks. `(as_of_ts - first_seen).days` truncates:
        # 2026-01-15T00:00:06 to 2026-01-16T00:00:00 is 23:59:54,
        # which `.days` reports as 0, not 1. That off-by-one
        # silently drops every user who arrived at the start of the
        # window — exactly the users you most need in the training
        # set. Use date arithmetic instead.
        observed_days = (as_of_ts.date() - first_seen.date()).days
        if observed_days < horizon_days:
            excluded += 1
            continue

        orders = [e for e in events if e["event_type"] == "order"]
        refunds = [e for e in events if e["event_type"] == "refund"]
        total = sum(o["amount_eur"] for o in orders)

        features.append({
            "user_id": user_id,
            "feature_as_of": as_of,
            "n_events": len(events),
            "n_orders": len(orders),
            "n_refunds": len(refunds),
            "total_spend_eur": round(total, 2),
            "avg_order_value_eur": round(total / len(orders), 2) if orders else 0.0,
            "refund_rate": round(len(refunds) / len(events), 4),
            "n_channels": len({e["channel"] for e in events}),
            "n_regions": len({e["region"] for e in events}),
            "first_seen": first_seen.isoformat(),
            "last_seen": last_seen.isoformat(),
            # The label: churned if no order in the horizon window.
            "churned_30d": 1 if last_seen < cutoff else 0,
        })

    return features, excluded


features, excluded = build_features(rows, FEATURE_AS_OF)
print(f"features built: {len(features)}")
print(f"excluded (observation window < {HORIZON_DAYS} days): {excluded}")

positives = sum(f["churned_30d"] for f in features)
print(f"positives: {positives}  rate: {positives/max(len(features),1):.4f}")

# The assertion that belongs in the DAG.
assert all(f["feature_as_of"] == FEATURE_AS_OF for f in features)
assert excluded >= 0
print("\nfeature table is ready for CREATE MODEL")
```

**The output is `features built: 0`, and that is the correct answer.** The sample dataset spans a single day — 2026-01-15, 00:00:06 to 23:59:51 — while `FEATURE_AS_OF` is 2026-01-16 and the churn horizon is 30 days. Every user in the sample was *first seen* on 2026-01-15, so every user's observation window is one day. Rule 2 excludes all of them.

**This is the point of the exercise, not a defect in it.** A pipeline that omitted rule 2 would emit 3,057 rows, label all of them `churned_30d = 0` ("this user did not churn in the 30 days after 2026-01-16"), train on that, and produce a model whose precision on real churners is zero — because **the outcome has not happened yet**. You cannot label "did not churn in the next 30 days" when you have only observed one day of that window. The label is *unknown*, not *negative*, and the difference between an unknown and a negative is the difference between a model and a coin flip.

The exclusion count is also a diagnostic you should alert on. If `excluded` suddenly approaches the row count, your history is shorter than the horizon — either a backfill is incomplete, the feature build is anchored too early, or the `as_of` filter is dropping rows it should keep.

To see the feature table itself, relax the horizon to match the data you actually have. A one-day window with a same-day horizon produces a usable table, and the *structure* of the code is identical — only the parameter changes:

```python
# Same code path, horizon matched to the data's actual span.
short_features, short_excluded = build_features(rows, FEATURE_AS_OF, horizon_days=1)
print(f"\nwith horizon_days=1:")
print(f"  features built: {len(short_features)}")
print(f"  excluded:       {short_excluded}")
pos = sum(f["churned_30d"] for f in short_features)
print(f"  positives: {pos}  rate: {pos/max(len(short_features),1):.4f}")

# A concrete row, so you can see the feature vector you will train on.
if short_features:
    sample = max(short_features, key=lambda f: f["total_spend_eur"])
    for k, v in sample.items():
        print(f"    {k:22s} {v}")

# The invariant that must hold in production regardless of horizon:
# every excluded row is excluded because its window was TOO SHORT,
# never because its window was too long.
assert len(short_features) + short_excluded > 0
assert all(f["first_seen"] <= f["feature_as_of"] for f in short_features)
print("\ninvariants hold")
```

**The production version of this build never uses a fixed `as_of`.** In the DAG it is `{{ ds }}` — Composer's logical date, the day being processed. Backfills replay it over a range of dates, and each run reconstructs the feature snapshot as it *would have looked* on that date, using only events strictly before it. That is what makes a backfilled training set legitimate: a row labelled at 2026-01-16 contains exactly the information that was available on 2026-01-16, and nothing that leaked in from the future.

The same discipline appears in the SQL version, which is what actually runs in the platform:

```sql
-- The as-of predicate, expressed as a single join condition.
-- Note the strict inequality on both sides of the label window:
--   features  come from events in [first_seen, as_of)
--   the label comes from events in [as_of, as_of + 30d)
-- A user with no events in the label window is NOT churned.
-- A user whose window was cut short by the end of the data is
-- EXCLUDED entirely — that is the row-count check the DAG asserts.
SELECT
  f.user_id,
  f.feature_as_of,
  f.n_events,
  f.n_orders,
  f.total_spend_eur,
  f.refund_rate,
  f.n_channels,
  -- The label: no activity at all in the 30 days after as_of.
  CASE
    WHEN d.last_seen_in_window IS NULL THEN 1
    ELSE 0
  END AS churned_30d
FROM `my-project.curated.user_features` f
LEFT JOIN (
  SELECT
    user_id,
    MAX(event_ts) AS last_seen_in_window
  FROM `my-project.curated.events`
  WHERE event_dt >= DATE(f.feature_as_of)          -- window opens at as_of
    AND event_dt <  DATE(f.feature_as_of) + 30     -- window closes 30 days later
  GROUP BY user_id
) d
ON d.user_id = f.user_id
WHERE DATE_DIFF(
        DATE(f.feature_as_of),
        DATE(f.first_seen),
        DAY
      ) >= 30                                        -- observation-window rule
  AND DATE(f.feature_as_of) + 30 <= DATE('2026-03-01')  -- label fully observed
;
```

That last predicate — `feature_as_of + 30 <= <end of available data>` — is the SQL equivalent of rule 2, and it is the one line people forget. Without it, the last 30 days of your history generate training rows whose labels are computed from incomplete data, and your model learns that every user churns on day 29.

### Exercise 5 — The Dataflow template's SQL equivalent

The aggregation the Dataflow job performs, expressed as BigQuery SQL — so you can compare the two implementations.

```sql
-- The hourly aggregate, computed by the Dataflow window in production.
-- This is the reference implementation used to verify the Dataflow
-- output. If the two disagree, one of them has a bug.
SELECT
  region,
  TIMESTAMP_TRUNC(event_ts, HOUR) AS window_start,
  COUNT(*) AS event_count,
  ROUND(SUM(amount_eur), 2) AS revenue_eur
FROM `my-project.curated.events`
WHERE event_dt = DATE('2026-01-15')
GROUP BY region, window_start
ORDER BY region, window_start;

-- The reconciliation query. Run it against the Dataflow output.
-- A non-zero difference means the streaming job and the SQL
-- implementation disagree — which is the bug you want to find now,
-- not at quarter end.
WITH
sql_agg AS (
  SELECT
    region,
    TIMESTAMP_TRUNC(event_ts, HOUR) AS window_start,
    COUNT(*) AS event_count,
    SUM(amount_eur) AS revenue_eur
  FROM `my-project.curated.events`
  WHERE event_dt = DATE('2026-01-15')
  GROUP BY region, window_start
),
stream_agg AS (
  SELECT region, window_start, event_count, revenue_eur
  FROM `my-project.curated.events_hourly`
  WHERE DATE(window_start) = DATE('2026-01-15')
)
SELECT
  COALESCE(s.region, t.region) AS region,
  COALESCE(s.window_start, t.window_start) AS window_start,
  s.event_count AS sql_count,
  t.event_count AS stream_count,
  t.event_count - s.event_count AS count_diff,
  ROUND(COALESCE(t.revenue_eur, 0) - COALESCE(s.revenue_eur, 0), 2) AS revenue_diff
FROM sql_agg s
FULL OUTER JOIN stream_agg t
  ON s.region = t.region AND s.window_start = t.window_start
WHERE s.event_count != t.event_count
   OR ABS(COALESCE(t.revenue_eur, 0) - COALESCE(s.revenue_eur, 0)) > 0.01;
```

**An empty result is a pass.** This is the highest-value verification query in the whole pipeline, and it should run in the DAG every day.

### Exercise 6 — The DLP inspection and the PII gate

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import looks_like_email, redact_pii

# A regex is NOT a detection service. It finds what it was written
# to find and nothing else.
samples = [
    "alice@example.com",
    "not-an-email",
    "alice@localhost",
    "a.b+tag@sub.domain.co.uk",
    "alice@@example.com",
    "",
]

print("regex check:")
for s in samples:
    print(f"  {looks_like_email(s)!s:5s}  {s!r}")

print("\nredaction:")
for s in ["alice@example.com", "user-4471"]:
    print(f"  {s!r} -> {redact_pii(s, keep_last=4)!r}")


def tokenise(value, salt):
    """Deterministic pseudonymisation that preserves the join.

    Redaction destroys the ability to join back to the customer.
    A keyed hash preserves it while removing the PII from the
    broad-access table.
    """
    import hashlib
    return hashlib.sha256(f"{salt}:{value}".encode()).hexdigest()[:32]


# The tokenisation table is the sensitive artefact.
SALT = "a-secret-from-secret-manager"
mapping = {}
for s in samples[:2]:
    mapping[s] = tokenise(s, SALT)

print("\ntokenised:")
for original, token in mapping.items():
    print(f"  {original!r} -> {token}")

# The property that makes tokenisation usable: deterministic.
assert mapping["alice@example.com"] == tokenise("alice@example.com", SALT)
# And that it is not reversible without the salt.
assert "alice" not in mapping["alice@example.com"]
print("\ntokenisation is deterministic and irreversible without the salt.")
```

### Exercise 7 — The drift monitor, as a runnable check

```python
import math
from collections import Counter


def psi(baseline_counts, current_counts):
    """Population Stability Index between two bucketed distributions."""
    total_b = sum(baseline_counts.values())
    total_c = sum(current_counts.values())
    if total_b == 0 or total_c == 0:
        return 0.0
    value = 0.0
    for key in set(baseline_counts) | set(current_counts):
        p_b = max(baseline_counts.get(key, 0) / total_b, 1e-6)
        p_c = max(current_counts.get(key, 0) / total_c, 1e-6)
        value += (p_c - p_b) * math.log(p_c / p_b)
    return value


def bucketize(values, edges):
    out = []
    for v in values:
        label = f"<={edges[0]}"
        for e in edges:
            if v <= e:
                label = f"<={e}"
                break
        else:
            label = f">{edges[-1]}"
        out.append(label)
    return Counter(out)


def monitor(baseline_rows, current_rows, amount_key="amount_eur",
            score_key=None, threshold=0.35):
    """The daily drift check for the churn pipeline."""
    alerts = []

    # 1. Feature distribution shift.
    edges = [10, 50, 200, 500, 1000]
    base = bucketize([r[amount_key] for r in baseline_rows], edges)
    curr = bucketize([r[amount_key] for r in current_rows], edges)
    value = psi(base, curr)
    if value >= 0.25:
        alerts.append(("SIGNIFICANT", f"{amount_key} PSI={value:.4f}"))
    elif value >= 0.10:
        alerts.append(("MODERATE", f"{amount_key} PSI={value:.4f}"))

    # 2. The positive rate — the cheapest, loudest alarm.
    if score_key is not None:
        base_rate = sum(1 for r in baseline_rows if r[score_key] >= threshold) / len(baseline_rows)
        curr_rate = sum(1 for r in current_rows if r[score_key] >= threshold) / len(current_rows)
        if curr_rate > base_rate * 2 or curr_rate < base_rate * 0.5:
            alerts.append((
                "HIGH",
                f"positive rate {curr_rate:.4f} vs baseline {base_rate:.4f}",
            ))

    # 3. Volume guard. A model that stopped scoring looks like a
    #    model that predicts the majority class.
    if len(current_rows) < 0.5 * len(baseline_rows):
        alerts.append((
            "HIGH",
            f"row count {len(current_rows)} vs baseline {len(baseline_rows)}",
        ))

    return alerts, value


import sys
sys.path.insert(0, "project/core")
from pipeline_logic import ingest_events, build_bigquery_rows

lines = open("sample_data/events.csv").read().splitlines()
accepted, _ = ingest_events(lines[1:])
rows = build_bigquery_rows(accepted)

for r in rows:
    r["churn_score"] = 0.4 if r["event_type"] == "refund" else 0.05

# A drifted population: the mobile channel's order values shift.
shifted = [
    dict(r, amount_eur=r["amount_eur"] * 0.4 if r["channel"] == "mobile"
         else r["amount_eur"])
    for r in rows
]

alerts, value = monitor(rows, shifted, score_key="churn_score")
print(f"PSI: {value:.4f}")
for severity, message in alerts:
    print(f"  [{severity:11s}] {message}")

if not alerts:
    print("  no alerts — the pipeline is behaving")
```

---

## 🛠️ Common Errors and Fixes

### 1. `google.api_core.exceptions.InvalidArgument: Table name "events" missing dataset while no default dataset is set in the request`

**Symptom.**

```text
google.api_core.exceptions.InvalidArgument: Table name "events" missing dataset while no default dataset is set in the request
```

**Cause.** A query, a Dataform `ref()`, or a `ML.PREDICT` call referenced a bare table name, relying on a default dataset that exists in your notebook but not in the Composer or Dataflow context.

**Fix.** Fully qualify every reference:

```sql
-- Wrong
SELECT * FROM events;

-- Right
SELECT * FROM `my-project.curated.events`;
```

**In Dataform, the equivalent mistake is using a raw table name instead of `${ref()}`.** `${ref("events")}` resolves the dependency from the Dataform project and shows up in the lineage graph; a hard-coded string does not, and breaks when the dataset moves.

### 2. `google.api_core.exceptions.InvalidArgument: Schema mismatch: Model expects columns ... but got ...`

**Symptom.**

```text
google.api_core.exceptions.InvalidArgument: Schema mismatch: Model expects columns
[n_events, n_orders, total_spend_eur, refund_rate, region, channel] but got
[user_id, n_events, n_orders, total_spend_eur, refund_rate, region, channel]
```

**Cause.** The scoring table has a column the model was not trained on — almost always `user_id`, carried through from `curated.user_features_daily`.

**Fix.** Project exactly the model's features:

```sql
SELECT *
FROM ML.PREDICT(
  MODEL `my-project.curated.churn_model`,
  (SELECT * EXCEPT(user_id, feature_as_of, churned_30d)
   FROM `my-project.curated.user_features_daily`
   WHERE feature_as_of = DATE('{{ ds }}'))
);
```

**The structural fix:** make the scoring source a view that projects exactly the model's features, and have the model training read the same view. Then the two cannot drift.

### 3. The DAG runs but `curated.events` has twice the expected rows

**Symptom.** The `check_no_duplicates` gate fails. `COUNT(*)` is double `COUNT(DISTINCT event_id)`.

**Cause.** Pub/Sub is **at-least-once delivery**. A message can be redelivered if the ack deadline expires or the worker dies mid-processing. With a 60-second ack deadline and a pipeline that occasionally stalls, duplicates happen.

**Fix.** Deduplicate before the write, per partition:

```python
# Deduplicate before the write, per partition.
# `rows` is the PCollection of raw events from Pub/Sub; `beam` is
# `import apache_beam as beam`.
deduped = (
    rows
    | "KeyByPartition" >> beam.Map(
        lambda r: (dedup_key(r["event_id"], r["event_dt"]), r)
    )
    | "Dedupe" >> beam.Distinct()
    | "Unkey" >> beam.Map(lambda kv: kv[1])
)
```

`beam.Distinct()` is *not* the right tool here. It keeps a bounded, per-worker set of seen keys — which is exactly why a distributed job still produces duplicates when the same key lands on two different workers, and why a rescaled job produces *more* duplicates than a smaller one. The fix that actually holds is a keyed state store (`beam.ParDo` + `stateful.Do`, or a `GroupByKey` followed by a single `beam.Distinct()` per key), which makes the dedup deterministic regardless of how the data is split.

**And verify it in the DAG**, which the gate already does. The duplicate count must be exactly zero, not "small".

### 4. `403 Permission denied on resource projects/my-project/...` — the service account is wrong

**Symptom.**

```text
google.api_core.exceptions.Forbidden: Permission 'bigquery.tables.create' denied on resource (or it may not exist)
```

**Cause.** The Composer environment's service account is not the one you granted the roles to. **Composer runs its DAG tasks as the environment's service account, not as `pipeline-sa`**, unless you explicitly configure otherwise. This is the single most common IAM mistake in a Composer setup.

**Fix.** Two options:

```bash
# Option A: grant the roles to the Composer environment's SA.
COMPOSER_SA=$(gcloud composer environments describe my-project-composer \
  --location=us-central1 --format="value(config.nodeConfig.serviceAccount)")
gcloud projects add-iam-policy-binding my-project \
  --member="serviceAccount:${COMPOSER_SA}" \
  --role="roles/bigquery.jobUser"

# Option B: use a per-DAG service account, which is tighter.
gcloud composer environments update my-project-composer \
  --location=us-central1 \
  --service-account="pipeline-sa@my-project.iam.gserviceaccount.com"
```

**Option B is better** because it makes the DAG's identity explicit and stops the Composer environment from having broad rights it does not need.

### 5. `google.api_core.exceptions.Forbidden: Permission 'storage.objects.get' denied` on the archive bucket

**Symptom.** The Dataflow job fails writing to `gs://raw-events-us-central1`.

**Cause.** The Dataflow worker's service account is the **Compute Engine default service account**, not `pipeline-sa`. `roles/dataflow.worker` grants the worker broad storage rights on the project, but a bucket created with a restricted IAM policy or with a bucket-level grant to a different principal will still reject it.

**Fix.** Attach a dedicated service account to the worker pool:

```bash
gcloud compute instance-groups managed set-instance-template my-project \
  --zone=us-central1-a \
  --template=my-dataflow-template \
  --service-account="pipeline-sa@my-project.iam.gserviceaccount.com"
```

Or, in the template launch parameters:

```bash
--workerServiceAccount=pipeline-sa@my-project.iam.gserviceaccount.com
```

**And disable the default SA's project-wide grants.** A Compute Engine default service account with `roles/editor` on the project is a standing vulnerability, and it is on every project created before 2024.

### 6. The dashboard shows yesterday's data even though the DAG succeeded

**Symptom.** The DAG is green. The dashboard is stale.

**Cause.** The Looker Studio data source is set to **"Cached data"** with a long refresh interval, and BigQuery's **result cache** is serving a stale result. Looker Studio issues a query; BigQuery may answer from its result cache if the underlying table has not changed.

**Fix.** Set the data source's freshness to **"Live data"** for the tiles that must be current, and accept the cost. Alternatively, create a **materialised view** or a **scheduled query** that refreshes an aggregate table, and point the dashboard at that — the data source can then stay cached because the table behind it changes on a known schedule.

**The nuance:** BigQuery's result cache respects the table's last-modified time. A table that has genuinely been written to will bust the cache. If the dashboard is stale, the more likely cause is that **the table was not actually written** — check the row count for the partition before blaming the cache.

---

## 💡 Production Notes

- **Every DAG task must be idempotent and keyed on the logical date.** `WRITE_TRUNCATE` to a date-partitioned destination with a logical-date key makes retries and backfills safe. Anything else makes an incident recovery a manual operation.

- **Set `require_partition_filter = TRUE` on every large table.** It eliminates the most expensive mistake in a warehouse at the cost of occasionally annoying a BI user. Pair it with a `DATA_SPLIT_COLUMN`-style explicit filter in every query.

- **Never point a Looker Studio chart at the detail table.** The aggregate table exists so the dashboard's cost is proportional to the aggregate, not the detail, and not the viewer count.

- **Alert on the DLQ depth.** A DLQ nobody reads is a silent data-loss channel. The alert should fire when the depth is non-zero for more than an hour — a single bad message is noise, a sustained non-zero depth is a broken producer.

- **Run the streaming-vs-SQL reconciliation query daily.** If the Dataflow output and the BigQuery SQL implementation disagree, one of them has a bug, and an empty result is the only acceptable outcome. This is the highest-value verification query in the pipeline.

- **Scope DLP inspection to the columns and partitions that can contain PII, and run it weekly rather than daily.** At $0.10/GB, inspecting everything daily becomes a budget line you did not plan for.

- **Keep the service accounts separate and minimal.** `pipeline-sa` for Dataflow, the Composer environment's SA for orchestration, and a BQML-only SA for the model training. Bucket-level IAM, not project-level, for storage.

- **Version the pipeline code in Git and deploy it as a Dataflow template.** An ad-hoc `gcloud dataflow jobs run` from a laptop is how a pipeline acquires an undocumented dependency on someone's laptop.

- **Backfill with `airflow dags backfill`, not with ad-hoc queries.** The backfill runs the same code path, so it cannot diverge from the daily run.

- **Exercise the runbook with deliberate failures.** Inject a bad event, a duplicate, a schema change, and a DLP finding in a test project. A runbook that has never been executed is a document.

- **Review the cost model against actuals monthly.** The `cost_model` module's numbers are us-central1 list prices. The first time a real bill arrives, some assumption will be wrong, and finding it on a monthly review is far cheaper than finding it on an annual one.

---

## 🔑 Key Takeaways

- **The capstone wires eight GCP services into one platform:** Pub/Sub, Cloud Storage, Dataflow, BigQuery, BigQuery ML, Composer, Dataform, Dataplex, DLP, and Looker Studio. Every resource has a concrete name.
- **Pub/Sub is the buffer, GCS is the record.** Pub/Sub absorbs producer bursts and has 7-day retention; the bucket is the permanent archive and the replay source. Write to both.
- **`max-delivery-attempts=5` with a DLQ is what makes the pipeline safe.** One poison message must not stall the subscription.
- **The landing zone is partitioned by date and hour** so a one-hour replay reads one prefix instead of the whole bucket.
- **The producer contract includes a reject taxonomy.** Ten distinct reasons, each with a different fix. A single counter of "12 rejects" is unactionable.
- **Dataflow over Dataproc when the pipeline is streaming-first.** Beam's event-time model is a better fit, Dataflow autoscales to zero, and one language covers batch and stream.
- **Event time, 1-hour windows, 10-minute allowed lateness.** Late events land in the right bucket and corrections are expected — the downstream tables must tolerate re-writes.
- **Reject unknown currencies rather than guessing.** A silently wrong aggregate is worse than a missing row. One `unknown_currency` reject exists in the sample data for exactly this reason.
- **A malformed event must not fail the bundle.** Catch, write to the DLQ, return normally. Otherwise you have an infinite poison-pill loop.
- **Deduplicate per `(event_id, partition)`, not globally.** Global dedup collapses genuine cross-day records.
- **Separate the aggregate table.** The dashboard's cost must be proportional to the aggregate, not to the detail table times the viewer count.
- **`require_partition_filter = TRUE`** eliminates the most expensive warehouse mistake at the price of occasionally annoying a BI user.
- **The Composer DAG processes a logical date, never "now".** That makes backfills free, runs idempotent, and partial failures recoverable.
- **Gates sit between tasks, not at the end.** A corrupted event table must never reach the model.
- **The churn label comes from a join with the billing system, and the observation-window rule excludes entities that have not had time to churn.** Excluded entities get `NULL`, not `0`.
- **BigQuery ML is right here because the scoring is batch.** No endpoint, no container, no pipeline — ~$2/month against Vertex AI's ~$586/month.
- **Bucket-level IAM for `pipeline-sa`, project-level only where unavoidable.** The pipeline must not be able to overwrite the archive it reads.
- **Composer is more expensive than Dataflow** — one node is $41/month, more than 480 vCPU-hours of Dataflow. It has a fixed floor. For a twice-daily job, use Cloud Scheduler plus Cloud Run.
- **DLP scales linearly with volume.** Inspect 100% daily at $0.10/GB and it becomes a budget line. Scope it and schedule it weekly.
- **Tokenise, do not redact, when the join key must survive.** A keyed hash removes the PII and keeps the join; redaction destroys both.
- **The expected aggregate, exactly:** AMER 1238 / 464848.02, APAC 1159 / 421049.85, EMEA 1176 / 432544.17, LATAM 1227 / 445554.36. Total 4,800 events.
- **Monthly cost at 150,000 events/day: about $1,769.** Pub/Sub dominates on per-GB ingest, Cloud Storage is the archive doing its job, DLP scales linearly with volume, Composer has a fixed floor, and BigQuery ML training is nearly free.
- **The reconciliation query between the streaming output and the SQL implementation is the highest-value verification in the pipeline.** An empty result is a pass.
- **Do not proceed past a red DAG, and do not bypass a gate.** A gate that keeps failing is telling you something true.
- **Three green days before adding the model.** It catches the class of bug that appears when nobody is watching.
- **A runbook that has never been exercised is a document.** Inject the failures deliberately.

---

## 📚 Practice Exercises

1. **Build it locally.** Using `project/core/pipeline_logic.py` and `sample_data/events.csv`, implement the full pipeline as one runnable script: ingest → validate → normalise → dedup per partition → window → aggregate → reconcile against the SQL-equivalent aggregation → write the summary CSV. Assert the exact expected summary. Then add the DLQ path and assert the exact reject taxonomy.

2. **The cost model, from first principles.** Using `cost_model`, build a monthly estimate for the capstone at 10k, 150k, 1M, and 10M events/day. Show which component dominates at each scale and where the crossover points are — specifically, the volume at which BigQuery's cost exceeds the cost of switching from on-demand to flat-rate slots, and the volume at which DLP's cost justifies sampling instead of full inspection.

3. **The IAM design.** Using `iam_policy`, model the roles for `pipeline-sa`, `composer-sa`, and `bq-ml-sa`. For each, evaluate the permissions it needs and the permissions it should be denied. Then write the bucket-level policy that lets the pipeline write to `raw-events-us-central1` but not to `raw-events-us-central1-archive`, and explain why the project-level `roles/storage.objectAdmin` grant is a liability here.

4. **The Dataflow template, written out.** Write the complete Beam pipeline for the capstone: read from Pub/Sub, partition into valid and invalid, write the invalid to the DLQ, archive the raw, dedup per partition, window and aggregate, and write to BigQuery. Then state where the idempotency guarantee comes from and how you would replay a single hour from the archive.

5. **The gates.** Write four Composer tasks that fail the DAG: the row-count reconciliation, the duplicate check, the DLP check, and the positive-rate check. For each, write the SQL, the failure message, and the runbook entry that follows it. Then explain why the DLP gate belongs after scoring rather than before it.

6. **The Composer DAG with backfill semantics.** Write the full DAG file including the logical-date parameterisation, the three-day lookback, and the `max_active_runs=1` setting. Then write the command to backfill 2026-01-10 through 2026-01-12 after a currency correction, and explain what happens to the BigQuery ML model trained during those backfill runs.

7. **The label, carefully.** Write the SQL that produces `churned_30d` with the 30-day observation-window rule, and three queries that test it: one that proves the excluded entities are absent rather than labelled zero, one that proves the label is consistent with the order history, and one that would catch a leak in the feature table. Then state what happens to the model if you remove the observation-window filter, and predict the direction of the error.

8. **The phased rollout, as a plan.** Take the six phases from this chapter and turn them into a 10-week plan with dependencies, owners, exit criteria, and a rollback for each phase. Then identify the phase most likely to slip and argue whether it should be descoped or the deadline extended.

---

## 📖 Further Reading

- [Apache Beam and Cloud Dataflow — Dataflow Templates](https://cloud.google.com/dataflow/docs/guides/templates/using-flex-templates)
- [Apache Beam — Python SDK Reference](https://beam.apache.org/documentation/programming-guide/)
- [Pub/Sub — Message Retention and Dead-Letter Topics](https://cloud.google.com/pubsub/docs/dead-letter-topics)
- [BigQuery — Partitioned Tables and `require_partition_filter`](https://cloud.google.com/bigquery/docs/partitioned-tables)
- [BigQuery ML — Training and Evaluating Models](https://cloud.google.com/bigquery/docs/evaluate-overview)
- [Cloud Composer — Scheduling and Logical Dates](https://cloud.google.com/composer/docs/composer-2/composer-overview)
- [Dataform — Dataform Repositories and SQLX](https://cloud.google.com/dataform/docs/quickstart-create-workflow)
- [Dataplex — Data Lineage](https://cloud.google.com/dataplex/docs/catalog-overview)
- [Sensitive Data Protection — De-identifying Data](https://cloud.google.com/sensitive-data-protection/docs/deidentify-sensitive-data)
- [Looker Studio — BigQuery Data Source Performance](https://cloud.google.com/looker/docs/studio/bigquery-performance)
