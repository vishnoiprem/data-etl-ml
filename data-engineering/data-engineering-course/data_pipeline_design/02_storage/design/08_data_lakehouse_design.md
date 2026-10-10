# 08 — Data Lakehouse Design

> **Lesson 8 of 30 — Storage**

A 30-minute lesson on designing a data lakehouse from scratch: when
to use it, when not to use it, and what the tradeoffs actually look
like at the whiteboard. This is the lesson that bridges "lakehouse
in 30 seconds" (Lesson 7) and "lakehouse as an architecture" (the
mock interview). Read Lesson 7 first if you haven't.

---

## 1. What a lakehouse actually is

A lakehouse is Parquet on S3 (or GCS / ADLS / Azure Blob) with **three
extra guarantees** the raw lake doesn't have:

1. **ACID transactions** — multi-writer safety, no partial reads.
2. **Schema enforcement** — bad data is rejected at write time, not
   at query time.
3. **Time travel** — read the table as it was at timestamp T-7.

In 2026, the three implementations are roughly equivalent on
capability and diverge on ecosystem:

| | Delta Lake | Apache Iceberg | Apache Hudi |
|---|---|---|---|
| Backed by | Databricks / Linux Foundation | Apple, Netflix, Tabular | Uber |
| Strengths | Spark-native, mature, governance | Hidden partitioning, Hive-compatible | Record-level updates, CDC |
| Weakness | Spark coupling | Less Spark-native | Smaller ecosystem |
| When default | Databricks stack | AWS-native / multi-engine | CDC-heavy, upsert-heavy |

In an interview you don't get points for picking one. You get
points for knowing what they all share and naming the differences
when pushed.

---

## 2. The Medallion architecture (bronze → silver → gold)

The Medallion architecture is the single most common answer for
"where do I put my data?" It maps cleanly to the three guarantees
above:

```
                    ┌─────────────────────────────────────────────┐
   raw ingest       │  Bronze (raw)                              │
   ────────────────►│   - append-only, schema-on-read           │
                    │   - all source columns + metadata         │
                    │   - Idempotency key = event_id            │
                    └──────────────────┬──────────────────────────┘
                                       │ transform (Spark / dbt)
                                       ▼
                    ┌─────────────────────────────────────────────┐
   cleaned          │  Silver (typed)                            │
                    │   - ACID, schema-enforced                  │
                    │   - de-duped on event_id                   │
                    │   - typed (string → int / timestamp)        │
                    │   - PII tokenized                         │
                    └──────────────────┬──────────────────────────┘
                                       │ aggregate (dbt / Spark)
                                       ▼
                    ┌─────────────────────────────────────────────┐
   curated          │  Gold (curated)                            │
                    │   - business-logic joins                   │
                    │   - aggregated for BI / ML                 │
                    │   - materialized in warehouse or served    │
                    └─────────────────────────────────────────────┘
```

### Worked example: `orders` flowing through the three layers

Imagine an e-commerce source system pushes a JSON event to Kafka
on every `order_placed`. The flow through the layers:

**Bronze (parquet-on-S3 with Delta / Iceberg / Hudi):**

```
s3://lake/bronze/orders/
  year=2026/month=10/day=10/hour=14/
    part-0001.parquet
    _delta_log/0000001.json   ← transaction log
```

Each row is the raw JSON, plus pipeline metadata:

```json
{
  "raw_payload": "{\"order_id\":1234,\"customer_id\":777,\"total\":42.50}",
  "ingestion_ts": "2026-10-10T14:23:11Z",
  "source_system": "shopify",
  "event_id": "uuid-v4"
}
```

**Silver (typed, deduped, partitioned):**

```
s3://lake/silver/orders/
  order_date=2026-10-10/
    part-0001.parquet
```

```sql
-- dbt or Spark SQL that produces silver from bronze:
SELECT
  CAST(raw_payload:order_id AS BIGINT)    AS order_id,
  CAST(raw_payload:customer_id AS BIGINT) AS customer_id,
  CAST(raw_payload:total AS DECIMAL(10,2)) AS total_usd,
  raw_payload:currency                      AS currency,
  DATE(ingestion_ts)                        AS order_date,
  ingestion_ts                              AS loaded_at,
  event_id                                  AS idempotency_key
FROM bronze.orders
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY event_id
  ORDER BY ingestion_ts DESC
) = 1;
```

The `QUALIFY ... = 1` is the dedup. Schema is enforced on write.

**Gold (curated, BI-shaped):**

```sql
-- dbt model for the daily revenue fact:
SELECT
  order_date,
  customer_id,
  COUNT(*)            AS order_count,
  SUM(total_usd)      AS gross_revenue_usd
FROM silver.orders
WHERE order_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY 1, 2;
```

The gold table is what dashboards and ML pipelines read from.
Bronze is the replay; silver is the truth; gold is the answer.

---

## 3. Schema evolution: adding a column without breaking downstream

This is the most-asked lakehouse question because it tests
whether you understand **what was hard about Hive**.

### The naive approach (and why it breaks)

In Hive, a `CREATE TABLE` defines the schema and a write writes
data. To add a column, you ran `ALTER TABLE ADD COLUMN new_col
STRING`. The next read needed a `SERDEPROPERTIES` update or
readers crashed with a schema mismatch. Across hundreds of tables
this became unmaintainable. Hive tables were either completely
mutable (and broken) or completely frozen (and painful to evolve).

### The lakehouse approach

Delta / Iceberg / Hudi all store the schema *inside* the
transaction log. Every write carries the schema. The protocol for
adding a column is:

1. **Producer side.** The pipeline reads bronze, adds the column
   with a default, writes silver. The new schema is appended to
   the transaction log.

2. **Reader side.** A reader that was compiled against the old
   schema does not need to be re-deployed. It uses *schema
   evolution on read* — the reader fetches the schema, sees the
   new column, and either fills it from defaults or ignores it.

3. **Backward-compatible changes** (add nullable column, widen
   int to bigint, add a partition column) are automatic. The
   transaction log accepts them.

4. **Backward-incompatible changes** (rename column, narrow
   type, drop column) are *rejected at registration time*. The
   log uses a JSON schema with backwards-compatibility checks.

```python
# Spark + Delta — adding a column safely:
delta_table = DeltaTable.forPath(spark, "s3://lake/silver/orders")
delta_table.addColumn("discount_code", "string")  # nullable

# Widening int → bigint:
delta_table.alterColumnTypes([("qty", "BIGINT")])
```

The senior move: name the **compatibility matrix** that you commit
to. "We guarantee backward-compatible evolution: add nullable
column is fine; rename is a deployment."

### The advanced scenario: partitions and hidden partitioning

Iceberg's killer feature is *hidden partitioning*. The partition
transform (`days(loaded_at)`, `bucket(8, customer_id)`) is stored
in the metadata, not the column list. A reader can query
`WHERE loaded_at BETWEEN '2026-10-01' AND '2026-10-10'` and the
query engine computes the partition predicate. No
`partition_filter` clause needed in the query.

This is what the senior answer for "how do you handle time-based
queries efficiently?" looks like in 2026.

---

## 4. Cross-region replication: active-passive vs active-active

### Active-passive (the default)

- One region is primary. Writes go there.
- A second region holds a read-only replica (S3 cross-region
  replication, or Delta Lake's `clone` for shadow tables).
- DR: in failover, you promote the secondary. RPO = replication
  lag (seconds to minutes). RTO = manual cutover time
  (minutes to hours).

```
us-east-1 (primary)              eu-west-1 (passive)
   ┌──────────────┐                  ┌──────────────┐
   │ writers       │──── replicate ──►│ readers       │
   │ bronze/silver │                  │ DR / EU reads │
   └──────────────┘                  └──────────────┘
```

### Active-active (rare)

- Both regions accept writes. Each region has its own
  transaction log.
- Conflict resolution is via timestamps or vector clocks.
- Reads need union across regions with conflict resolution.

```
us-east-1                 eu-west-1
   writers  ─┐         ┌─  writers
             ├─ union ─┤
   readers   ┘         └─ readers
```

In practice, active-active is rarely worth the complexity. The
costs:

- Every write has to be globally ordered, which means every
  write pays a cross-region round-trip. Latency goes from
  5 ms to 80 ms.
- Conflict resolution (last-write-wins, vector clocks,
  CRDT) is a non-trivial engineering effort. Most teams
  under-estimate it by 3x.
- Cost: cross-region egress is $0.02/GB.

### Senior answer

> **"Active-passive with S3 cross-region replication, with RPO =
> 5 minutes and RTO = 1 hour. Active-active is reserved for cases
> where the regulatory requirement is single-region unavailability
> tolerance — for example, EU data residency forcing EU writes to
> stay in EU."**

This is what 90% of companies end up with. Name the RPO / RTO
explicitly.

---

## 5. The cost story (what the interviewer wants)

The four numbers to memorize:

| Layer | Storage $ / TB / month | Compute $ per scan |
|---|---|---|
| S3 standard | $23 | $0 |
| S3 Glacier Instant | $4 | + retrieval cost |
| Delta / Iceberg on S3 | $23 + small metadata overhead | $5-10 per Athena query / Spark job |
| Snowflake | $40 (after compression) | $2-5 per credit, ~$0.0002 / row scanned |

**Worked example.** A 100 TB lakehouse:

- 100 TB raw on S3 standard = $2,300 / month
- 30 TB hot (last 30 days, often queried) on S3 = $690 / month
- 70 TB cold (archive) on S3 Glacier = $280 / month
- Snowflake for gold = $40 × 30 TB compressed = $1,200 / month
- Spark cluster for silver transformations = $5K-15K / month

**Total:** ~$10K-20K / month for a 100 TB lakehouse.

### The cost vs warehouse tradeoff

- **Lakehouse is cheaper on storage.** S3 at $23/TB is 5-10× cheaper
  than a warehouse's compressed-but-also-paying-for-compute cost.
- **Warehouse is cheaper on ad-hoc queries.** Snowflake runs a
  full scan in seconds with no setup; a Spark query against raw
  Parquet needs a cluster, ~60-second startup, and a data engineer
  to write it.
- **The bridge.** Most 2026 architectures use S3 + Iceberg as the
  source of truth and Snowflake / BigQuery as the query engine,
  via external tables. The query engine pays per-scan, and the
  storage is cheap.

---

## 6. The lakehouse vs warehouse decision matrix

| If you need... | Use a warehouse | Use a lakehouse |
|---|---|---|
| Sub-second SQL on structured data | ✅ | ❌ |
| Cheap storage of raw, semi-structured data | ❌ | ✅ |
| ML training (Spark, GPUs) | ❌ | ✅ |
| BI dashboards (Looker, Tableau) | ✅ | ⚠️ (with external table) |
| ACID across many writers | ⚠️ | ✅ |
| Time travel / audit | ❌ | ✅ |
| 99% of financial reporting | ✅ | ⚠️ |
| Streaming ingest with low latency | ❌ | ✅ (with auto-loader) |

The senior answer is *rarely* "lakehouse for everything." It's
"lakehouse for the source of truth (bronze / silver), warehouse
for the curated gold."

---

## 7. When NOT to use a lakehouse

Three cases where a lakehouse is the wrong answer:

1. **Small data (< 10 TB total).** A Postgres + dbt setup gives you
   the medallion pattern at 1/10th the operational cost. The
   lakehouse wins because of cheap storage at scale; below 10 TB
   the savings are negligible and the operational complexity is
   real.

2. **No semi-structured data.** If every row is a tabular,
   fully-typed record (financial trades, line items), a warehouse
   wins on query ergonomics and is competitive on cost. The
   lakehouse earns its keep when you also have JSON, images,
   embeddings, clickstream, and other shapes.

3. **Single team, single workload.** A lakehouse needs Spark
   expertise, an S3 / GCS account, schema governance, and an
   understanding of the transaction log. A Snowflake account is
   one click. If your team is 5 analysts and 0 engineers, the
   lakehouse is a tax they can't afford.

> **In the interview, you would say:** "The default 2026 answer is
> lakehouse — but only because we have at least one of: large
> volume, semi-structured data, or ML workloads. If none of those
> apply, I'd start with a warehouse and migrate to a lakehouse
> when the cost or scale makes it worth the operational overhead."

---

## 8. The architectural patterns (cheat sheet)

```
Small team, small data:     Postgres + dbt → Snowflake
Single team, large data:    Snowflake (or BigQuery) end-to-end
Multi-team, mixed data:     S3 + Iceberg (silver) → Snowflake / BigQuery (gold)
ML-heavy, large data:       S3 + Delta / Iceberg → Spark / Ray / Dask
Real-time + analytics:      Kafka + Flink + Iceberg + Snowflake
```

The senior answer is "lakehouse + warehouse" — Iceberg on S3 as
the source of truth, Snowflake or BigQuery for the curated query
layer. The medallion pattern spans both. That's the architecture
for the 2026 interview.

---

## 9. Common mistakes (and how to avoid them)

1. **Putting everything in the lakehouse.** "We have a lake, so all
   data goes into the lake" — and then the BI team needs to set up
   Spark for every dashboard. The lakehouse is the *source of
   truth*, not the *only* destination.

2. **Confusing bronze with archive.** Bronze is *raw and replayable*,
   not *cold and forgotten*. The transactional log lets you
   re-derive silver from bronze. If you delete bronze after 30
   days, you lose the ability to fix schema bugs in silver.

3. **Treating Delta and Iceberg as interchangeable without
   understanding the tradeoffs.** They are similar but not
   compatible. Pick one and document the choice.

4. **Skipping schema enforcement on bronze.** If you let any JSON
   land in bronze without a schema, the bronze layer degenerates
   into a data swamp. Schema enforcement is the *whole point* of
   the lakehouse.

---

## Try it

Pick a real table from a pipeline you've worked on. Sketch the
medallion flow: what's in bronze, what's in silver, what's in
gold. What columns would you add to each layer? What's the
schema evolution story when a column is added next quarter?

If you can't answer the schema evolution question, that's the
weakest part of your answer — practice it.

---

*Author: Prem Vishnoi <prem.vishnoi@example.com>*
