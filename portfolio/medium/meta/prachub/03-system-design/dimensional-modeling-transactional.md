# Design a Scalable Dimensional Model for Near Real-Time Transactional Analytics

## 1. Simple way to think

- Imagine a giant retail company with thousands of stores. Every second, customers swipe cards, return items, and earn loyalty points. Leadership wants a live dashboard showing "revenue by region, by product, by hour" — not yesterday's report.
- The naive approach is to keep scanning the giant transactional database. That works for 10 stores but breaks at 10,000 — the operational DB is busy serving checkouts.
- The fix is a **star schema**: one fat table in the middle (the *fact*) holding measurable events like sales, surrounded by thin tables (the *dimensions*) holding descriptive context like store, product, customer, date.
- Think of it like a hub-and-spoke: every sale is a spoke, and the hub is the fact table. Dimensions are little cheat sheets you can join to give the spoke meaning.
- For "near real-time", we don't wait until midnight. We stream inserts into the fact table as transactions happen, using micro-batches every 1–5 minutes. The dashboard looks live, but the warehouse isn't being hammered.
- Why star (not snowflake)? Because dashboards do lots of group-bys, and a denormalized wide table is way faster to scan. Snowflake normalization looks pretty but kills query speed.
- Slowly Changing Dimensions (SCD Type 2) preserve history — if a product moves from "Electronics" to "Clearance", we keep both rows so old reports still make sense.
- A concrete example: a rideshare company modeling trip completions. Fact = `fct_trips` (one row per ride), dimensions = `dim_driver`, `dim_rider`, `dim_city`, `dim_date`, `dim_time_of_day`.

## 2. Interview write-up (how to solve it)

**Requirements clarification.** "Before I dive in — when you say near real-time, what's the freshness target? Seconds, one minute, or five? And are we optimizing for ad-hoc analyst queries, or fixed executive dashboards? Latency vs. cost trade-off lives there. For this answer I'll assume a 5-minute freshness SLA and Snowflake/BigQuery/Redshift as the warehouse."

**Concrete example — rideshare trips.** Let's model one trip completion as our grain: one row in the fact table per trip. Dimensions: driver, rider, city, date, time-of-day, payment method, surge tier, device platform.

```
              dim_driver
                  |
dim_rider -- dim_city -- fct_trips -- dim_date
                  |           |
            dim_payment   dim_surge
```

**Data model.**

```sql
CREATE TABLE fct_trips (
  trip_id          BIGINT,
  driver_key       BIGINT,    -- FK
  rider_key        BIGINT,    -- FK
  city_key         INT,
  date_key         INT,       -- YYYYMMDD
  time_key         INT,       -- HHMM
  payment_key      INT,
  surge_key        INT,
  fare_amount      DECIMAL(10,2),
  tip_amount       DECIMAL(10,2),
  distance_miles   DECIMAL(8,2),
  trip_duration_s  INT,
  rating           TINYINT,
  event_timestamp  TIMESTAMP
) PARTITION BY (date_key);

CREATE TABLE dim_driver (
  driver_key       BIGINT,
  driver_id        VARCHAR,
  full_name        VARCHAR,
  vehicle_type     VARCHAR,
  signup_date      DATE,
  rating_avg       DECIMAL(3,2),
  -- SCD2 columns
  effective_from   TIMESTAMP,
  effective_to     TIMESTAMP,
  is_current       BOOLEAN
);
```

**Ingestion flow.** Trip service writes to Kafka topic `trips.completed.v1`. A streaming job (Flink / Spark Structured Streaming) consumes, enriches with dimension lookups (driver's current rating, city's timezone), and micro-batches into the warehouse every 2 minutes via `MERGE`. Late-arriving trips are handled with a watermark of 15 minutes.

**API/data design.** Analysts query through Tableau / Mode. Heavy users get pre-aggregated rollup tables (`agg_trips_by_city_hour`). Materialized views handle common patterns.

**Key trade-offs.** Streaming adds complexity and cost vs. a nightly batch. We accept ~3 min of staleness for ~10x lower cost than second-by-second streaming. Snowflake dimensions would save storage but slow queries 5–10x.

**Failure modes.** Late events: handled by watermark + late-arriving zone in staging. Dimension updates: idempotent MERGE keyed on natural ID. Backfill: replay Kafka from offset.

## 3. Best optimized solution

**Refined architecture.**

```
[App] -> Kafka (trips.completed) -> Flink (enrich + dedupe)
                                      |
                                      v
                              Staging (Iceberg/Hudi on S3)
                                      |
                              MERGE every 2 min
                                      v
                              Fact table (partitioned, clustered)
                                      |
                              v
                              Rollup tables (hourly, daily, monthly)
                                      |
                              v
                              BI tools / ML features
```

**Storage & partitioning.** Use **Apache Iceberg** on Parquet in S3. Partition fact by `date_key` (one partition per day). Within partition, **cluster (Z-order)** on `city_key, driver_key` for locality on common joins. This makes a query like "revenue by city last week" scan ~7 partitions and within them only relevant clusters.

**Storage format.** Parquet (columnar, predicate pushdown, ~10x compression vs. CSV). Avoid Avro for analytical fact tables — row-based, slower scans. Avro is fine for the Kafka schema, Parquet for the warehouse.

**Cost considerations.** Auto-suspend warehouse clusters. Use smallest cluster that meets the 2-min SLA. Rollup tables are 100x cheaper to scan for fixed dashboards. Compress dimension updates using MERGE-on-cursor. Archive partitions older than 90 days to cheaper storage tier.

**Monitoring & SLOs.** Freshness SLO: 95th-percentile lag < 5 min. Track via a heartbeat table populated by the streaming job. Alert on: (a) lag > 10 min, (b) duplicate rate > 0.1%, (c) dimension coverage < 99.9% (orphan keys).

**Why it's optimal.**
- Iceberg gives ACID, schema evolution, and **hidden partitioning** — analysts don't write partition predicates.
- Z-order clustering beats simple sort by 5–10x on multi-column filters.
- Micro-batch MERGE is 5x cheaper than continuous streaming and meets the 5-min SLA comfortably.
- SCD2 dimensions cost 2x storage but enable accurate historical reporting — non-negotiable for finance.

**What the interviewer is really testing:** They want to see that you understand the *separation* of operational and analytical workloads, that you can choose between batch/streaming/micro-batch with eyes open, and that you know star schemas beat normalized ones for analytics. Bonus points: warehouse-specific optimization (clustering, partitioning, file format) and late-arrival handling.
