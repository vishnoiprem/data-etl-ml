# Design Batch and Streaming ETL Architecture

## 1. Simple way to think

- Imagine a restaurant that needs to know two things: what was yesterday's total revenue (needs the full day's data, doesn't need to be instant), and how many burgers are being sold *right now* (needs a fast number, can be a bit approximate).
- Those are two different jobs, and they have different tools. Trying to do both with one system is like using a sledgehammer to crack a nut.
- **Batch ETL** = the dishwasher at the end of the night. You pile everything in, run it once, and you get a clean result. Cheap, simple, thorough. Used for: nightly revenue, weekly cohort reports, ML training sets.
- **Streaming ETL** = the line cook during dinner. They see orders as they come in and update the "available" board in real time. More expensive, more complex, but freshness is the whole point. Used for: fraud detection, live counters, recommendation refreshes.
- Most companies do **80% batch, 20% streaming**. Don't stream what can wait 24 hours.
- The shared foundation is a **log** (Kafka). Producers write events, consumers read at their own pace. Batch jobs read from the log, streaming jobs subscribe live.
- Lambda architecture = batch + speed layer running in parallel. Kappa architecture = one streaming pipeline that also serves batch use cases. Modern shops lean Kappa.
- A concrete example: a payment processor. Batch = nightly reconciliation against bank statements. Streaming = real-time fraud scoring on each transaction.

## 2. Interview write-up (how to solve it)

**Requirements clarification.** "Couple of questions before I start: what's the volume — thousands or millions of events per second? What's the freshness target — seconds, minutes, or hours? What are the source systems — APIs, databases, event streams? And is this a greenfield design or fitting into an existing warehouse?"

**Scale assumptions.** Let's say **2M events/sec** at peak, 30+ source systems (Postgres, MySQL, MongoDB, Kafka, REST APIs, S3 logs), 200 downstream consumers (dashboards, ML models, reverse ETL to Salesforce). Warehouse: Snowflake or Databricks. Orchestrator: Airflow or Dagster. Stream processor: Flink or Spark Structured Streaming.

**High-level architecture.**

```
Sources                              |   Serving
-------                              |   -------
OLTP DBs (CDC) ──┐                   |  ┌─> BI dashboards
Kafka topics ────┼──> Ingestion ──>  |  ├─> ML feature store
REST APIs ───────┤   (Kafka)          |  ├─> Reverse ETL
Logs (S3) ───────┘                   |  └─> Real-time APIs
                                     v
                              [Bronze layer]
                              (raw, immutable)
                                     |
                              [Silver layer]
                              (cleaned, deduped, joined)
                                     |
                              [Gold layer]
                              (aggregated, business-ready)
```

The **medallion** (Bronze/Silver/Gold) pattern. Storage = Delta Lake or Iceberg.

**Data flow specifics.**
- **Batch**: Airflow triggers a Spark job at 2am. Reads yesterday's S3 logs, joins with daily snapshots from Postgres via CDC, writes to Silver. Then a second job computes Gold aggregates.
- **Streaming**: Flink consumes from Kafka topic `payments.events.v1`, enriches with dimension data from a key-value store, writes to Iceberg Bronze via streaming sink. Another Flink job maintains a 5-minute tumbling-window aggregate in Gold.

**API/data design.** Bronze: append-only Parquet, one table per source. Silver: typed, schema-enforced, deduplicated. Gold: wide, denormalized, pre-aggregated for known query patterns.

**Key trade-offs.**
- Batch is 5x cheaper per byte but 24h stale. Streaming is fresh but expensive and operationally heavy.
- Kappa (stream-only) is elegant but requires **replayable logs** and careful state management.
- We choose **lambda for now** — keep nightly batch as ground truth, stream for live signals, reconcile daily.

**Failure modes.** Schema drift: schema registry + auto-evolve with alerts. Duplicate events: idempotent writes keyed on event_id. Late events: watermark + dead-letter queue. Job failure: Airflow retries with backoff; idempotent so re-runs are safe. Backpressure: Kafka acts as shock absorber; Flink checkpointing to S3.

## 3. Best optimized solution

**Refined architecture.**

```
[CDC: Debezium] ─┐
[Kafka native] ──┼──> Kafka (Schema Registry) ──> Flink ──> Bronze (Iceberg)
[REST poll] ─────┤                                          │
[Log shippers] ──┘                                          v
                                                        Silver (Iceberg, MERGE)
                                                          │
                                              ┌───────────┼───────────┐
                                              v           v           v
                                         Gold rollups   ML features  Reverse ETL
                                              │           │
                                              v           v
                                          Snowflake    Feast store
```

**Storage choices.** Iceberg on Parquet for all lake layers (ACID, time-travel, schema evolution). Compression = ZSTD. File size target = 128–256 MB. Compact small files with a daily Spark job.

**Partitioning/clustering.** Bronze: partition by `ingest_date`, cluster by `source_system`. Silver: partition by `event_date`, Z-order on `entity_id, event_type` for join locality. Gold: partition by `date`, cluster by `metric_name` for dashboard patterns.

**Orchestration.** Airflow for batch DAGs. Flink for stream jobs. Use **Argo Events** or **Dagster** for hybrid workflows. Treat every job as code, version-controlled, with CI tests on sample data.

**Cost considerations.** Spot instances for batch. Auto-scale Flink based on Kafka consumer lag. Right-size Iceberg files to avoid "small file problem" (the #1 lake cost killer). Archive Silver to Glacier after 90 days. Use **auto-suspend** warehouses.

**Monitoring & SLOs.**
- **Freshness SLO**: 99% of streaming events in Silver within 2 min of production.
- **Completeness SLO**: row count from source vs. Bronze within 0.1% daily.
- **Latency SLO**: batch DAG completes by 4am with 99% reliability.
- **Alerts**: consumer lag, schema violations, data quality checks (Great Expectations), cost anomalies.

**Why it's optimal.**
- The medallion layers decouple raw preservation from business logic — you can rebuild Gold without re-ingesting sources.
- Iceberg's hidden partitioning + Z-order gives Snowflake-like performance on open storage at 1/4 the cost.
- CDC + stream-first ingestion means you never lose data even if downstream is down — Kafka + Iceberg is your replayable source of truth.
- Lambda over Kappa is pragmatic: 99% of teams don't have the operational maturity for pure stream-replay-of-batch, and the dual-write reconciliation is cheap insurance.

**What the interviewer is really testing:** They want to see you don't fall into the trap of "everything is streaming" or "everything is batch". They want batch *and* streaming justified, a layered lakehouse with clear contracts, and operational thinking (failure modes, SLOs, cost). Bonus: real tools (Flink, Iceberg, Debezium) over hand-wavy boxes.
