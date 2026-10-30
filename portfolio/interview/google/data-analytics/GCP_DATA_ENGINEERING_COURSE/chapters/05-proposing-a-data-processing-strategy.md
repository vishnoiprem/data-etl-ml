# 1.5 — Proposing a Data Processing Strategy

> **Section 1 · GCP Fundamentals · Lecture 1.5 · 8:00**

## 🎯 What you will learn
- What a data engineer is actually accountable for, and what data engineering is *not*
- The three data types — structured, semi-structured, unstructured — and how each one changes the tool choice
- Batch versus streaming: the trade-off that is not really about latency
- What a data pipeline is, mechanically, and why every pipeline has the same seven stages
- ETL versus ELT, and why the industry moved
- The families of ETL tooling and where each one fits
- How to propose a strategy to a client: the decision framework that sets up the whole course
- How to write the proposal document that wins the work

---

## 🧠 Concept

### What data engineering is

Data engineering is the discipline of building the systems that move data from where it is produced to where it is needed, and of making that movement reliable, observable and cheap enough to run every day.

That definition contains four words that do the work: **reliable, observable, cheap, every day**. A pipeline that processes a terabyte beautifully once is a demo. A pipeline that processes two gigabytes, badly, every day for three years is infrastructure.

The distinction worth stating explicitly, because clients constantly confuse it: **data engineering is not analytics**. Analytics asks questions of data. Data engineering builds the system that makes the questions answerable. The output of a data engineer is a *pipeline*, a *schema*, a *contract*, a *cost model* — not a chart. When you find yourself building a dashboard for a client, you have crossed into a different discipline (and should probably be billing for it differently).

Nor is data engineering the same as data science. Data science produces models and insights; data engineering produces the platform those models run on — the feature store, the training pipeline, the serving infrastructure, the reproducibility.

### The three data types

The type of data determines the tool, and it determines it more strongly than almost any other factor.

**Structured data** has a schema — a known set of fields with known types. Tables in Cloud SQL, tables in BigQuery, a Parquet file with a fixed schema, a Google Ads export. Structured data can be queried relationally: filter, join, aggregate.

**Semi-structured data** has a schema in practice but not in the type system. JSON, Avro, Protobuf, YAML. Every record has the same general shape, but fields appear and disappear, and nesting varies. This is the dominant format for event data — the kind a Pub/Sub topic carries, the kind an API returns, the kind a CDC connector emits.

Semi-structured data is where the most interesting engineering decisions live. You have three options:

1. **Keep it semi-structured and query it as-is.** BigQuery can query JSON columns directly with `JSON_VALUE` and `JSON_QUERY_ARRAY`, and with `CREATE TABLE ... EXTRACT PARTITION FROM JSON` you can promote selected fields into typed, partitioned columns. This is often the right answer: it preserves fidelity and avoids a transformation layer that may need reworking when the schema evolves.
2. **Normalise it into typed columns at ingestion.** Faster to query, explicit schema, better compression, partition-friendly. Costs a transformation step and freezes a schema decision.
3. **Store it as-is in object storage and let a schema-on-read engine handle it.** BigLake with Iceberg or Parquet gives you open table formats with schema evolution.

My recommendation, and it is a strong one: **promote the fields you filter and partition on; leave the rest as JSON.** The fields you partition by and filter by are the ones whose query cost and correctness matter. Everything else can be queried lazily. This is exactly what the course's own pipeline does — it normalises `amount` to a number and `event_ts` to a timestamp because those are the fields that get aggregated and windowed, while the rest of the record is not touched.

**Unstructured data** has no schema at all: images, audio, video, PDF, free text, sensor readings. This is where the platform's ML services come in — Vision, Natural Language, Speech-to-Text, Video Intelligence, Document AI. The engineering problem changes shape: instead of "map fields to types", it becomes "extract structure from unstructured input, then process that". The pipeline still needs to be batch or streaming, idempotent and observable; only the processing step is different.

The uncomfortable truth: **most real data is a mixture.** A clickstream is semi-structured events plus unstructured content (page text, images), joined against structured dimension tables. A good strategy names which type dominates and where the boundary is.

### Batch versus streaming

The framing "batch is slow, streaming is fast" is wrong, and believing it produces bad architectures.

The real distinction is **when the results become visible and how much state you must hold**:

- **Batch** processes a bounded set of data. The job knows when it starts and when it is done. It can use all the data it has for a window, recompute freely, and checkpoint. There is no notion of "behind" because there is a defined end.
- **Streaming** processes an unbounded stream. The job never finishes. It must produce results continuously, and because events arrive late, out of order and duplicated, it must hold **state** (windows, deduplication keys, session state) across the entire lifetime of the stream.

That state requirement is the real cost of streaming. It brings:

- **Windowing semantics** — how do you aggregate an event stream where an event can arrive at 14:59 for a window that closed at 14:00? Tumbling (fixed, non-overlapping), sliding (overlapping), and session (activity-based) windows each make different trade-offs.
- **Exactly-once delivery** — which, in practice, means "at-least-once delivery plus idempotent processing", because you cannot make the network transactional with the sink.
- **Watermarks and late data** — the mechanism for deciding when a window is closed and what happens to events that arrive afterwards.
- **State growth** — a stream that runs for a year has a year of state, and state that must be checkpointed, replicated and restored.

The decision framework:

| Requirement | Choose | Reason |
|---|---|---|
| The answer is needed "eventually" (minutes to hours is fine) | Batch | Far simpler, cheaper, easier to test |
| The answer drives a real-time action (fraud, recommendations, alerting) | Streaming | Latency is the product |
| Data arrives in files, on a schedule, in bulk | Batch | Streaming would be a downgrade |
| Data arrives continuously from many producers | Streaming | Batch means constant re-reads |
| The transformation needs global state (all-time aggregates, joins to large tables) | Batch, or streaming with external state | Streaming joins are expensive |
| Regulated, must be reproducible | Batch | Batch runs are deterministic and re-runnable |
| Team is small and has no streaming expertise | Batch | The operational cost of streaming is real |

**The pragmatic middle ground: micro-batching.** Run a streaming engine on a schedule — every five minutes, every hour — with a bounded window. You get near-real-time freshness with batch-like simplicity and far less state. Many production pipelines are exactly this, and it is the right answer far more often than people admit.

**The honest cost comparison.** Streaming pipelines reserve workers for the lifetime of the stream, so a stream that is quiet at 3 a.m. still bills. A batch job that runs for 20 minutes bills 20 minutes. On the other hand, a streaming pipeline does not need a scheduler to re-trigger it, does not need to re-scan yesterday's data, and gives incremental results. Neither is "better"; they are different cost shapes.

### What a data pipeline is, mechanically

A pipeline is a directed, mostly-acyclic graph of transformations over data that arrives from sources and terminates at sinks. Strip away the vendor nouns and every pipeline has the same seven stages:

```text
1. EXTRACT    get data out of the source system
2. INGEST     land it somewhere durable, unchanged
3. VALIDATE   check it is well-formed, in range, and timely
4. TRANSFORM  reshape it into the target schema
5. ENRICH     join reference data
6. AGGREGATE  roll it up to the grain the consumer wants
7. LOAD       write it to the sink, idempotently
```

Three properties distinguish a *good* pipeline from a script that happens to work:

**Idempotency.** Running the same input twice produces the same final state. This is the single most important property of a data pipeline, because it means retry is safe, backfill is safe, and a late-arriving correction can be applied by re-running a window.

The mechanism is a **deterministic key** that identifies the logical record. The course's pipeline uses `dedup_key()`, which combines the event ID with the event timestamp — so re-delivering the same event is recognised and dropped. The `--run` output shows this working:

```text
dedup: 4800 -> 4800 rows (0 duplicates removed)
```

Re-run the same input twice and you still get 4800 rows. In a system without idempotency, you would get 9600 — and you would be writing a reconciliation script to remove the duplicates later.

**Observability.** You must be able to answer, at any moment: how many records came in, how many were rejected and why, how many made it to the sink, and how much did it cost. The course pipeline carries all of this: 4800 in, 4800 accepted, 0 rejected, 4 regions aggregated, 4800 published, 4800 loaded, with a monthly cost estimate attached.

**Bounded failure.** When something fails, it fails in a way that is detectable, attributable and recoverable — not silently. The rejected-row path is the example: 12 malformed rows produce 10 distinct reason codes, each counted, each routable to a dead-letter topic, each alertable if a new code appears.

### ETL versus ELT

**ETL** — Extract, Transform, Load. Data is transformed *before* it lands. The transformed shape is what is stored.

**ELT** — Extract, Load, Transform. Data lands raw, and transformations happen inside the target platform.

The industry's movement from ETL to ELT was not fashion. Three mechanisms drove it:

1. **Storage became cheap enough to keep everything.** Cloud Storage at $0.020/GB-month makes a raw landing zone essentially free. Storing raw data is now an insurance policy, not a cost.
2. **The target platform became faster than the transform.** BigQuery queries a petabyte in seconds; Dataflow transforms a stream in parallel. Writing a bespoke transformation engine outside the platform was reinventing a worse version of it.
3. **Requirements change.** In ETL, a schema change means changing the extract pipeline and reprocessing. In ELT, the raw data is already there; you write a new transformation and re-run it. The raw data is the source of truth for every future question.

The modern pattern, and the one I recommend:

```text
Raw landing (Cloud Storage, immutable, partitioned by date)
    -> validated, schema-promoted table (BigQuery, partitioned, clustered)
        -> business marts (BigQuery views, materialised views)
```

The raw layer is write-once and never transformed in place. The curated layer is derived and rebuildable. The mart layer is shaped for consumption.

Where ELT is the wrong choice:

- **The source data is too large to land raw** — e.g. multi-petabyte CDC with heavy transformation. Transform on the way in (Dataflow streaming).
- **The landing target costs more than the transformation** — rare on GCP, but true when landing into a database rather than object storage.
- **You must not store the raw data at all** — regulatory constraints where the raw data cannot be persisted (use streaming transformation in memory, or Sensitive Data Protection de-identification on the way in).
- **The transformation is expensive and deterministic** — e.g. parsing terabytes of proprietary binary. Do it once, on the way in, and store the result.

### The families of ETL tooling

On Google Cloud, the tooling families are:

**Managed SQL transformation** — BigQuery scheduled queries and [Dataform](24-dataform-and-the-transformation-layer.md). SQL logic in version control, dependency graph, tests, incremental models. This is the default for warehouse transformation.

**Managed streaming/batch engines** — [Dataflow](22-apache-beam-and-dataflow.md) for Beam pipelines (batch and streaming, one API) and [Dataproc](21-apache-spark-and-dataproc.md) for Spark. Dataflow for new work; Dataproc when the team already speaks Spark or the job needs a specific Spark library.

**No-code / low-code integration** — Data Fusion for visual pipeline design and Dataprep for interactive data preparation. Both are genuinely productive for short, ad-hoc jobs; neither is where you want a business-critical nightly pipeline.

**Orchestration** — [Composer](23-airflow-composer-and-workflows.md) for Airflow DAGs, and Workflows for simple HTTP-and-service-call sequences. Orchestration is not transformation: Composer schedules and wires; Dataform and Dataflow transform.

**Ingestion services** — Storage Transfer Service, BigQuery Data Transfer Service, Database Migration Service, Datastream for CDC. These are the "Extract" half.

**In-house frameworks** — dbt on BigQuery, Airflow on Composer, Spark on Dataproc. Often the right answer, because they are the tools the team already knows.

The honest ranking of my preferences for a new GCP data platform in 2026:

1. **Dataform + BigQuery** for warehouse transformation. Lowest operational burden, best testing story, SQLX is readable by analysts.
2. **Composer** for orchestration when dependencies get complex and retries and backfills matter.
3. **Dataflow** for streaming ingestion and transformation.
4. **Dataproc** only when the team has a genuine Spark requirement.
5. **Data Fusion / Dataprep** for exploration and one-off jobs, not for the critical path.

### The decision framework

This is the framework the rest of the course hangs on. Six questions, asked in order. Each narrows the space.

**Question 1 — What is the shape of the data and where does it originate?**

- Transactional database (Cloud SQL, Cloud Spanner) → batch extraction, or **Datastream** for CDC if you need change capture.
- SaaS API (CRM, payments) → API extraction into a landing bucket.
- Files dropped by partners (SFTP, Cloud Storage) → Storage Transfer Service.
- Applications emitting events → **Pub/Sub**.
- On-device or clickstream → Pub/Sub with a streaming pipeline.
- Unstructured (images, documents) → storage + an ML service.

**Question 2 — What latency does the consumer need?**

- Daily or weekly reporting → **batch**, no debate. Scheduled query, Dataform, Composer.
- "Within an hour" → micro-batched or streaming.
- "Within seconds" → streaming, and now you have accepted windows, watermarks, state and idempotency.

**Question 3 — What volume and shape of processing?**

- Under ~1 TB and simple → BigQuery SQL. Full stop.
- Multi-TB transformations with shuffles → Dataflow or Dataproc.
- Streaming with complex state → Dataflow (Beam's stateful processing is the strongest in the platform).

**Question 4 — What are the non-functional requirements?**

- **Residency** → region choices and product-specific location settings.
- **Compliance** → VPC Service Controls, CMEK, audit logging, DLP for de-identification.
- **Availability** → multi-region for storage, regional clusters for compute.
- **Cost ceiling** → flat-rate BigQuery reservations versus on-demand; Spot VMs; storage lifecycle policies.

**Question 5 — What team and skills exist?**

This is the question clients consistently under-weight. A perfectly designed Beam streaming pipeline delivered to a team of SQL analysts will not run. A Dataform + BigQuery platform delivered to a Spark team will be resented. **Design for the team that will operate it**, and treat a training plan as part of the proposal.

**Question 6 — What does success look like, and how will you know?**

Define the SLIs before the design: freshness (how old is the newest record?), correctness (does the daily total reconcile with the source?), completeness (how many records were rejected, and is that number stable?), and cost (per month, per stage). A pipeline without SLIs is a pipeline whose health is discovered by a client complaint.

### Writing the proposal

A proposal that wins has a specific shape. Six sections, in this order:

**1. The problem, in the client's words.** Not "we need a modern data platform" but "the nightly finance report arrives at 09:00 and the European business has already closed." Quote the client. If you cannot write this section in the client's language, you do not understand the problem yet.

**2. The data inventory.** What sources, what shapes, what volumes, what growth rate, what quality. Include the things nobody wants to talk about: the missing `user_id` in 3% of events, the legacy system with no API, the partner still sending CSV via email.

**3. The proposed architecture, with the alternatives.** One diagram of the recommended architecture. Then a table of the two or three serious alternatives with the reason each was not chosen. A proposal without alternatives is a sales pitch, not an engineering proposal.

**4. The trade-offs, stated honestly.** This is the section that builds trust. Every architecture has costs: BigQuery on-demand pricing scales with query volume; a streaming pipeline adds operational complexity; a single region is a single failure domain; Dataform requires the team to learn SQLX. A proposal that admits its costs is read as competent; one that claims there are none is read as inexperienced.

**5. The cost model.** A monthly estimate broken down by line item, with the assumptions stated. Use the course's `cost_model` as the shape — line items with quantities, unit prices and a note explaining the assumption. State what happens as volume grows: which costs scale linearly, which are fixed, and where the free tier stops applying.

**6. The delivery plan.** Phases, each independently valuable, with a named acceptance criterion. The first phase should deliver something in production within weeks, because the point of a phase is to reduce uncertainty.

### Applying the framework to the course project

The course's pipeline is a complete, if small, example of the framework:

```text
Source:      sample_data/events.csv (4800 rows, semi-structured CSV, one day)
Extract:     read the file
Ingest:      landing bucket, partitioned by date
Validate:   10 reason codes, 12 malformed rows caught
Transform:   currency to EUR, timestamp normalisation, region upper-casing
Enrich:      region reference (50 rows)
Aggregate:   per-region event count and revenue
Load:        BigQuery partition 20260115, 4800 rows, idempotent via dedup_key
```

Latency: batch, on a schedule. Volume: small enough for BigQuery SQL, and the design scales because the partitioning and the dedup key are already right. Non-functional: residency in `us-central1`, a landing bucket that is write-once. Team: SQL skills are sufficient. Success: 4800 in, 4800 out, 0 unexplained rejects, a stable daily revenue figure.

That is what a proposal looks like when it is grounded in a working pipeline rather than a slide.

---

## 🛠️ Hands-On

### Exercise A — Run the pipeline and read every number

```bash
cd path/to/gcp-de   # the course root
python project/local_runner.py --run
```

Expected output:

```text
organization: acme.example.com
└── folder: engineering
    └── project: GCP Data Engineering Course (gcp-de-course)
        ├── dataset: curated_us-central1  [BigQuery]
        ├── topic: events-us-central1  [Pub/Sub]
        ├── bucket: raw-events-us-central1  [Cloud Storage]
        └── serviceAccount: pipeline-sa@gcp-de-course.iam.gserviceaccount.com

▶ Running pipeline

  ingest: 4800 accepted, 0 rejected
  aggregate: 4 regions, 4800 events
  publish: 4800 messages to events-normalised
  load: partition 20260115, 4800 rows
  dedup: 4800 -> 4800 rows (0 duplicates removed)

region,event_count,revenue_eur
AMER,1238,464848.02
APAC,1159,421049.85
EMEA,1176,432544.17
LATAM,1227,445554.36

Dead-letter path
----------------
  malformed rows rejected: 12
    bad_amount               1
    bad_timestamp            1
    missing_event_id         1
    missing_user_id          1
    negative_amount          1
    unknown_channel          1
    unknown_currency         1
    unknown_event_type       1
    unknown_region           2
    wrong_field_count        2
```

Every one of those numbers maps to a stage in the seven-stage model. The `dedup` line is the idempotency guarantee. The dead-letter breakdown is the observability guarantee — **every reason code appears at least once**, so the failure taxonomy is testable rather than a hope.

Note that the clean run rejects nothing, and that is correct: `events.csv` has no bad rows. The `--run` command then merges in `sample_data/malformed_events.csv` so the dead-letter path is visible. A pipeline that can reject bad input must have bad input to reject.

### Exercise B — Feed the pipeline malformed data

```bash
python project/local_runner.py --run 2>&1 | tail -20
```

That gives you the dead-letter breakdown: 12 malformed rows rejected, with every reason code shown.

Then run the malformed dataset through the same code path to see the validation stage work:

```python
"""Run both datasets through the pipeline's validation stage."""
import sys
from pathlib import Path

sys.path.insert(0, "project/core")

from pipeline_logic import (
    aggregate_events,
    ingest_events,
    reject_counts,
    render_summary_csv,
)

SAMPLE = Path("sample_data")


def run(name: str, filename: str) -> None:
    lines = (SAMPLE / filename).read_text(encoding="utf-8").splitlines()
    accepted, rejected = ingest_events(lines)
    print(f"--- {name}")
    print(f"  accepted={len(accepted)} rejected={len(rejected)}")
    if rejected:
        print(f"  reject counts: {reject_counts(rejected)}")
    if accepted:
        print(render_summary_csv(aggregate_events(accepted)))


def main() -> None:
    run("clean", "events.csv")
    run("malformed", "malformed_events.csv")


if __name__ == "__main__":
    main()
```

Expected results:

```text
--- clean
  accepted=4800 rejected=0
region,event_count,revenue_eur
AMER,1238,464848.02
APAC,1159,421049.85
EMEA,1176,432544.17
LATAM,1227,445554.36

--- malformed
  accepted=0 rejected=12
  reject counts: {'wrong_field_count': 2, 'bad_amount': 1, 'unknown_region': 2,
                  'unknown_channel': 1, 'unknown_currency': 1,
                  'unknown_event_type': 1, 'missing_event_id': 1,
                  'missing_user_id': 1, 'negative_amount': 1, 'bad_timestamp': 1}
```

The malformed dataset has 12 rows and 10 distinct reason codes. This is the dead-letter path working, and it is why reason codes must be stable and low-cardinality — each one becomes a metric label and a dashboard dimension.

### Exercise C — Prove idempotency

```python
"""Re-running the same input must not duplicate rows."""
import sys
from pathlib import Path

sys.path.insert(0, "project/core")

from pipeline_logic import deduplicate, dedup_key, ingest_events, partition_for_date

SAMPLE = Path("sample_data")


def main() -> None:
    lines = (SAMPLE / "events.csv").read_text(encoding="utf-8").splitlines()
    accepted, _ = ingest_events(lines)

    partition = partition_for_date("2026-01-15")
    keys = [dedup_key(str(row["event_id"]), partition) for row in accepted]
    print(f"input rows:            {len(accepted)}")
    print(f"distinct dedup keys:   {len(set(keys))}")

    doubled = accepted + accepted
    unique = deduplicate(doubled, partition=partition)
    print(f"\nafter feeding the batch twice:")
    print(f"  input rows:          {len(doubled)}")
    print(f"  rows after dedup:    {len(unique)}")
    print(f"  idempotent:          {len(unique) == len(accepted)}")

    # The key itself is deterministic and explainable
    print(f"\npartition:  {partition}")
    print(f"sample dedup key: {keys[0]}")


if __name__ == "__main__":
    main()
```

This is the property that makes retries, backfills and at-least-once delivery safe. Without it, a Pub/Sub redelivery silently doubles revenue.

### Exercise D — Examine the windowing model

```python
"""Inspect the hourly windowing used by the streaming path."""
import sys
from pathlib import Path

sys.path.insert(0, "project/core")

from pipeline_logic import (
    WINDOW_BUCKET_SECONDS,
    aggregate_events,
    bucket_by_window,
    ingest_events,
)

SAMPLE = Path("sample_data")


def main() -> None:
    lines = (SAMPLE / "events.csv").read_text(encoding="utf-8").splitlines()
    accepted, _ = ingest_events(lines)

    windows = bucket_by_window(accepted)
    print(f"window size: {WINDOW_BUCKET_SECONDS} seconds")
    print(f"number of windows: {len(windows)}")

    counts = [len(rows) for rows in windows.values()]
    print(f"events per window: min={min(counts)} max={max(counts)} mean={sum(counts)//len(counts)}")

    keys = sorted(windows)
    print(f"first window: {keys[0]}")
    print(f"last window:  {keys[-1]}")

    summary = aggregate_events(accepted)
    print(f"\naggregated regions: {len(summary)}")
    total = sum(v["event_count"] for v in summary.values())
    print(f"total events aggregated: {total}")


if __name__ == "__main__":
    main()
```

The dataset spans **24 hourly windows over 24 hours**. That is a tumbling window — fixed size, non-overlapping, each event assigned to exactly one window. In a real streaming system you would also have to decide what happens to an event that arrives after its window closed; that is what watermarks and a dead-letter path are for.

### Exercise E — Build a cost model for a proposal

```python
"""Produce a proposal-shaped cost estimate."""
import sys
from pathlib import Path

sys.path.insert(0, "project/core")

from cost_model import (
    BIGQUERY_ONDEMAND_PER_TB,
    FREE_TIER,
    NETWORK_EGRESS_PER_GB,
    estimate,
)


def main() -> None:
    # Assumptions, stated explicitly, as a proposal must.
    daily_tb_scanned = 0.5
    working_days = 22
    egress_gb = 20

    query = estimate("bigquery", scanned_tb=daily_tb_scanned * working_days)
    storage = estimate("cloud-storage", storage_gb=1024 * 100)
    egress = egress_gb * NETWORK_EGRESS_PER_GB * working_days

    print("Assumptions")
    print(f"  daily scan:        {daily_tb_scanned} TB")
    print(f"  working days:      {working_days}")
    print(f"  stored:            100 GB")
    print(f"  egress/day:        {egress_gb} GB")
    print()
    print(query)
    print(storage)
    print(f"egress: {egress_gb} GB x {working_days} days x ${NETWORK_EGRESS_PER_GB}/GB = ${egress:.4f}")
    print()
    print(f"monthly total: ${query.total + storage.total + egress:.4f}")
    print()
    print("Free-tier sensitivity")
    free_tb = FREE_TIER["bigquery_query_tb"]
    used_tb = daily_tb_scanned * working_days
    print(f"  BigQuery free allowance: {free_tb} TB/month")
    print(f"  our usage:               {used_tb} TB/month")
    print(f"  within free tier:        {used_tb <= free_tb}")
    print(f"  over by:                 {max(0.0, used_tb - free_tb):.2f} TB")
    print(f"  at ${BIGQUERY_ONDEMAND_PER_TB}/TB: ${max(0.0, used_tb - free_tb) * BIGQUERY_ONDEMAND_PER_TB:.4f}")


if __name__ == "__main__":
    main()
```

A proposal's cost section must state the assumptions, because every number above is conditional on them. "BigQuery will cost $X" is a useless sentence; "BigQuery will cost $X assuming 0.5 TB scanned per working day, with the first 1 TB per month free" is a usable one.

### Exercise F — Map the proposal to GCP services

```python
"""Turn the decision framework into a service list."""
import sys
from pathlib import Path

sys.path.insert(0, "project/core")

from service_catalog import SERVICES, get_service

PROPOSAL = {
    "extract": ["cloud-storage", "pubsub", "datastream"],
    "ingest": ["cloud-storage", "pubsub", "bigquery-transfer"],
    "transform": ["dataflow", "dataproc", "bigquery", "dataform"],
    "orchestrate": ["composer", "workflows"],
    "store": ["cloud-storage", "bigquery", "bigtable"],
    "govern": ["data-catalog", "dataplex", "sensitive-data-protection"],
}


def main() -> None:
    for stage, service_ids in PROPOSAL.items():
        print(f"\n{stage.upper()}")
        for service_id in service_ids:
            service = get_service(service_id)
            deep = f"  -> {service.deep_dive}" if service.deep_dive else ""
            print(f"  {service.name:<26} {service.summary}{deep}")

    total = sum(len(v) for v in PROPOSAL.values())
    print(f"\n{total} service references across {len(PROPOSAL)} stages")


if __name__ == "__main__":
    main()
```

Every stage has more than one candidate. A proposal that names only one service per stage is not a decision — it is a preference.

### Exercise G — Write the proposal

Write a two-page proposal for this scenario, using the six-section structure from this chapter:

> A European omnichannel retailer generates approximately 15 million events per day from its web, mobile and store applications, plus order data from Cloud SQL. The finance team needs daily revenue by region by 07:00 CET. The marketing team wants to react to cart-abandonment within 5 minutes. Three source systems currently produce CSV files delivered by email.

Your proposal must include: the problem in the client's words, the data inventory, a recommended architecture plus two rejected alternatives, the honest trade-offs, a monthly cost model with assumptions, and a phased delivery plan. Then run `python project/local_runner.py --cost` and reconcile your estimate with the course model's output.

---

## 🛠️ Common Errors and Fixes

### Error 1 — `ERROR: (gcloud.bigquery.jobs.insert) Resources exceeded during query execution. Your table exceeds the maximum size allowed for a free external table.`

**When:** You query a large external table (Parquet or CSV in Cloud Storage) on the free tier.

**Why:** BigQuery's free tier applies a 10 GB per-query limit on external tables, and a 1 TB/month processing limit overall. Reading a 100 GB Parquet file from Cloud Storage exceeds the per-query external table limit.

**Fix:** Either use a standard table (load the data with `bq load` so it counts as storage, not query-time processing), or upgrade to a billing account with on-demand pricing.

```bash
bq load --source_format=PARQUET \
  PROJECT_ID:raw_events.raw_events_20260115 \
  gs://BUCKET/events/2026-01-15/*.parquet
```

### Error 2 — `PERMISSION_DENIED: Permission 'bigquery.tables.getData' denied on resource 'projects/PROJECT_ID/datasets/DATASET/tables/TABLE'`

**When:** A service account that can create tables cannot read them.

**Why:** The role you granted — probably `roles/bigquery.jobUser` — grants the ability to *run* queries without the ability to *read the results*. This is a deliberate, well-designed pair: `jobUser` lets a user run a query without seeing the data. `roles/bigquery.dataViewer` adds `bigquery.tables.getData`.

**Fix:** Add the data role. If the identity genuinely must not read the data, do not add it — instead grant the specific writer role it needs and accept that it cannot read back what it wrote.

```bash
gcloud bigquery datasets add-iam-policy-binding PROJECT_ID:DATASET \
  --member="serviceAccount:dp-transform@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"
```

### Error 3 — Duplicated rows after a re-run or a backfill

**When:** Your nightly load appends and the table now has double the rows.

**Why:** The load is not idempotent. An `INSERT` or an append-mode load has no natural key, so re-processing the same window inserts it again. This is the most common data-quality bug in production pipelines and it is invisible until a reconciliation report runs.

**Fix:** Make the load idempotent, in one of three ways:

1. **Partition overwrite.** Load into a partition and overwrite it rather than appending. The course pipeline writes to partition `20260115` — re-running replaces that partition's contents.
2. **MERGE on a deterministic key.** `MERGE` on the dedup key upserts rather than inserts.
3. **Delete-then-insert.** Delete the rows for the key, then insert the new set.

```sql
MERGE curated.events AS target
USING staging.events AS source
ON target.event_id = source.event_id AND target.event_ts = source.event_ts
WHEN MATCHED THEN UPDATE SET amount = source.amount
WHEN NOT MATCHED THEN INSERT (event_id, event_ts, amount, region) VALUES (source.event_id, source.event_ts, source.amount, source.region);
```

### Error 4 — `ERROR: (gcloud.storage.cp) The bucket ... is a requester pays bucket but no user project was specified.`

**When:** You copy a file from a requester-pays bucket.

**Why:** Requester-pays buckets charge the *reader*, not the bucket owner. The client must supply a project to bill. It is a legitimate pattern for sharing large public datasets without the owner paying.

**Fix:** Pass `--requester-pays` and a billing project.

```bash
gcloud storage cp --requester-pays --project=BILLING_PROJECT \
  gs://public-bucket/data.csv ./data.csv
```

### Error 5 — Pub/Sub subscription backlog growing without bound

**When:** The pipeline keeps falling behind and the subscription's age grows.

**Why:** The consumer's throughput is lower than the publish rate. Common causes: the sink is rate-limited (BigQuery load quota), the consumer is not parallelised enough, or one poison message is blocking a single-threaded pull.

**Fix:** Diagnose before scaling. Check the subscription's oldest-unacked-age, then scale the consumer (Dataflow worker count, Cloud Run max instances) and confirm the sink's quota headroom. For poison messages, use a dead-letter topic so one bad record cannot stall the pipeline.

```bash
gcloud pubsub subscriptions describe SUB_ID --format="value(ackDeadlineSeconds, messageRetentionDuration)"
gcloud logging read 'resource.type="pubsub_subscription" AND severity>=ERROR' --limit=20
```

### Error 6 — The pipeline is correct in development but produces different totals in production

**When:** Local sample data reconciles exactly; production data does not.

**Why:** Usually one of four things: timezone handling (local code assumes UTC, production events carry offsets); floating-point rounding differences in the currency conversion; a different set of valid enum values (your `VALID_REGIONS` set is a snapshot, and production has a region you have not seen); or a missing filter that the sample data happens to satisfy.

**Fix:** Treat the validation allow-lists as data, not code. Move them to a reference table that the pipeline joins against, so adding a region is a data change and not a deployment. The course's pipeline already has a `region_reference.ndjson` file with 50 reference rows — that is the right shape.

You will also hit `ERROR: (gcloud.projects.get-iam-policy) The project is not in ACTIVE state` when you try to read IAM on a project that is being created or deleted. Project state transitions are asynchronous, and a project spends time in `DELETE_REQUESTED` or `DELETE_IN_PROGRESS`. Wait, and check the state explicitly with `gcloud projects describe PROJECT_ID --format="value(state)"`.

---

## 💡 Production Notes

- **Define the SLIs before designing the pipeline.** Freshness, completeness, correctness and cost. A pipeline without an agreed definition of "correct" will be judged correct by whoever complains loudest.
- **Make the dedup key explicit and version it.** It is part of your data contract. Changing it invalidates every historical row that was written with the old one. Partition by ingestion date for the landing zone and by event date for the fact table — they answer different questions, "what arrived today" versus "what happened today", and backfills need both.
- **Write rejects to a dead-letter location with a stable reason code.** Never drop a row silently. Never put a raw payload in a reason code; reason codes become metric labels and will blow up your cardinality.
- **Reconcile counts at every stage boundary.** In → accepted, accepted → published, published → loaded. The course pipeline prints all of them. A pipeline that only checks the final count tells you *that* something is wrong but not *where*.
- **Version the transformation logic in Git, always.** Dataform, a SQL directory, a Beam pipeline — whatever it is, it belongs in a repository with review, CI and a rollback.
- **Alert on reject-rate change, not only on reject count.** A jump from 0 to 12 matters more than 12 rejections on a day when you expect zero. Baseline against the previous day or the same day last week.
- **Budget for the failure path, not just the happy path.** Backfills cost money at on-demand rates. A 10 TB backfill is a deliberate, budgeted operation, not something to discover during an incident. Keep the raw layer immutable and the curated layer rebuildable: if you cannot rebuild the curated layer from raw, your pipeline has state in the wrong place.
- **Design for the team that will operate it.** The best architecture for a team that cannot run it is a bad architecture, and no amount of engineering elegance compensates for an unmaintained pipeline.

---

## 🔑 Key Takeaways

- Data engineering is accountable for **reliable, observable, cheap, daily** movement of data — not for analysis.
- **Structured, semi-structured and unstructured data** drive different tool choices. Promote the fields you filter and partition on; leave the rest as JSON.
- **Batch vs streaming is not really about latency.** It is about whether the result is bounded, whether you must hold state, and what happens to late and duplicated events.
- Every pipeline has the same **seven stages**: extract, ingest, validate, transform, enrich, aggregate, load.
- **Idempotency, observability and bounded failure** are the properties that separate a pipeline from a script.
- **ETL vs ELT**: land raw, transform in the warehouse, because storage is cheap, the platform is fast, and requirements change.
- The **six-question decision framework**: data shape, latency, volume, non-functional requirements, team skills, success criteria.
- A proposal has **six sections**: problem, data inventory, architecture plus alternatives, honest trade-offs, cost model with assumptions, phased delivery plan.
- **Design for the team that will operate it.** The best architecture for a team that cannot run it is a bad architecture.

---

## 📚 Practice Exercises

1. Run `python project/local_runner.py --run` and annotate the output with the seven pipeline stages. Which line of output proves each of the three properties — idempotency, observability, bounded failure? Which stage does the `dedup` line belong to, and why is it not in the extract stage?
2. Run the malformed dataset through the pipeline and list all ten reason codes with the count for each. Then explain why `wrong_field_count` has a count of 2 while `bad_amount` has 1. Design an alerting rule that would page a human for each reason code.
3. Write a script that feeds the clean dataset twice through `deduplicate` and asserts the row count is unchanged. Then add a third duplicate with a *different* event ID but the same user and timestamp, and explain why the dedup key does not catch it — and what additional constraint would.
4. Use `bucket_by_window` to compute the events per hourly window, then compute the same aggregation with a 15-minute window. Write down what changes about the output and which one you would use for a dashboard that refreshes every 15 minutes.
5. Take the six questions of the decision framework and apply them to a client scenario you invent: a hospital network with 2 million IoT readings per day from 40 sites, a regulatory requirement that data never leaves the country, and a team of three Python developers with no Spark experience. Produce the one-page recommendation.
6. Write two competing cost models for the same workload: (a) a Dataflow streaming pipeline running continuously, and (b) a Dataflow batch job scheduled hourly. Using the course's cost model, show the crossover point in events per hour at which streaming becomes cheaper. State every assumption.
7. Write a proposal for the course project itself, following the six-section structure. Use the exact verified numbers — 4800 events, 12 malformed rows, 50 reference rows, target date 2026-01-15, and the four-region summary — and include a cost model from `cost_model.py`.
8. Argue the opposite of this chapter's recommendation in one case: name a scenario where **ETL** is clearly the right choice on GCP and a cloud-native ELT design would be a mistake. Then explain what would have to be true for the ELT design to become correct.

---

## 📖 Further Reading
- [Dataflow Documentation](https://cloud.google.com/dataflow/docs)
- [Dataproc Documentation](https://cloud.google.com/dataproc/docs)
- [Dataform Documentation](https://cloud.google.com/dataform/docs)
- [Composer Documentation](https://cloud.google.com/composer/docs)
- [Pub/Sub Documentation](https://cloud.google.com/pubsub/docs)
- [Datastream Documentation](https://cloud.google.com/datastream/docs)
- [Data Engineering on Google Cloud (architecture guidance)](https://cloud.google.com/architecture/data-engineering)
