# Data Warehousing — CTO / Principal Study Plan

**Source course:** Data Vidhya — *Data Warehousing* by Darshil Parmar.
**Course URL:** https://datavidhya.com/learn/data-warehouse/
**Coverage:** 4 modules • 24 lessons
**Audience:** Data engineers targeting **Staff → Principal → Director →
VP/CTO** track with deep data-warehouse architecture, internals, and
loading-pattern expertise.

> **How to use this file.** Each lesson has four lenses:
>
> 1. **Theory** — mental model and the warehouse primitive.
> 2. **Practical Example** — concrete code, configs, decisions.
> 3. **AI Use Case** — where GenAI / ML slots in or on top of this lesson.
> 4. **CTO / Principal Motivation** — career reason; what decisions
>    you're trusted with at senior levels.
>
> This is the **architecture & internals** course that complements
> Snowflake Hands-On (the vendor-specific deep dive) and the DE
> Foundations track. Module 1 grounds the warehouse in the DE
> lifecycle and the Kimball vs Inmon debate. Module 2 covers the
> layered-warehouse architecture. Module 3 covers internals
> (columnar storage, MPP, partitioning). Module 4 covers loading
> patterns (full vs incremental, CDC, idempotent loads, dim/fact
> loading).
>
> The Principal-level warehouse engineer can whiteboard a
> layered warehouse with Kimball marts, defend columnar vs row
> storage trade-offs, design an idempotent CDC load pattern, and
> explain to a CTO why we're spending $X/year on a particular
> warehouse.

---

# Module 1 · DW Foundations (11 lessons)

## Lesson 1 — Data Engineering Lifecycle — Where Does the Data Warehouse Fit? (Video)

### Theory

The DE lifecycle is the **canonical flow from source to value**.
Mental model:

```
Sources → Ingestion → Storage → Transformation → Warehouse → Serving → Consumption
   │         │            │            │              │           │           │
 OLTP     Kafka       Data Lake     dbt/Spark       Snowflake   OLAP      BI/ML
 SaaS     AppFlow      Iceberg       Airflow        Redshift    Druid     Apps
```

The **warehouse** sits at the *serving* layer: the system of record
for analytics. It's where the business trusts the data.

### Practical Example

In a 5-person data team:

- Data engineer 1 — ingestion (Kafka, CDC).
- Data engineer 2 — transformation (dbt, Spark).
- Data engineer 3 — **warehouse** (schema, performance, SLAs).
- Data scientist — ML on warehouse features.
- Analyst — SQL on warehouse marts.

The warehouse owner is the **hub** — every team's work funnels into
or out of their system.

### AI Use Case

**AI-curated warehouse documentation.** AI watches the warehouse
schema and query patterns, generates living documentation. The
Principal's edge: zero-touch docs.

### CTO / Principal Motivation

Understanding where the warehouse sits in the lifecycle is **the
CTO's strategic clarity**. "We can't build a real-time feature
without first having a batch warehouse" — this kind of dependency
mapping is board-level thinking.

---

## Lesson 2 — Data Engineering Lifecycle (Article)

### Theory

The lifecycle in detail. Mental model — the seven stages with
typical tools:

| Stage | Purpose | Common tools |
|-------|---------|--------------|
| **Sources** | Where data originates | OLTP, SaaS APIs, IoT, logs |
| **Ingestion** | Move data from sources | Kafka, Fivetran, Airbyte, DMS |
| **Storage** | Raw durable store | S3, ADLS, GCS (Parquet, Iceberg) |
| **Transformation** | Clean, enrich, conform | dbt, Spark, Airflow |
| **Serving** | System of record for analytics | Snowflake, Redshift, BigQuery, Iceberg |
| **Consumption** | Where humans/ML read | BI (Looker, Tableau), notebooks, apps |
| **Orchestration** | Glue between stages | Airflow, Step Functions, Dagster |

The 2026 trend: **lakehouse convergence** — Iceberg/Delta tables
collapse storage + serving into one layer, blurring the line
between data lake and warehouse.

### Practical Example

A modern lifecycle on AWS:

```
RDS Postgres → DMS CDC → Kinesis → Firehose → S3 (Parquet)
                                       ↓
                                  Glue (Spark) → S3 Iceberg
                                       ↓
                                  dbt → Snowflake (gold)
                                       ↓
                                  QuickSight / SageMaker
```

### AI Use Case

**AI-augmented lifecycle design.** "For a fintech with 5 OLTP
sources and 50 analysts, design the lifecycle" → AI generates
the architecture with cost estimates. The Principal's edge:
faster greenfield design.

### CTO / Principal Motivation

The lifecycle is the **lingua franca** of data engineering
reviews. Every architecture review at Staff+ level follows this
flow. CTOs who think in lifecycle terms communicate with the
board at the right altitude.

---

## Lesson 3 — What is a Data Warehouse and Why Do We Need It? (Video)

### Theory

A **data warehouse** is a centralized, integrated, time-variant,
non-volatile collection of data used for analytical reporting.
Mental model:

- **Subject-oriented** — organized by business subject (sales,
  customers, products).
- **Integrated** — consistent naming, units, types across sources.
- **Time-variant** — tracks history (timestamps on every row).
- **Non-volatile** — append-only; no in-place updates from source.

Why we need it:

1. **Single source of truth** for analytics.
2. **Decouples BI** from production OLTP.
3. **Historical analysis** — query 5 years of data without hurting
   production.
4. **Performance** — columnar + MPP for sub-second dashboards.

### Practical Example

Without a warehouse: 50 analysts run 50 ad-hoc SQL queries against
the production database → load on prod increases → checkout latency
spikes → customers complain. With a warehouse: 50 analysts query
the warehouse → production is isolated → no impact.

### AI Use Case

**AI-generated warehouse pitch.** "Write a 1-page exec summary
explaining why we need a warehouse" → AI generates with cost
comparisons. The Principal's edge: faster budget approval.

### CTO / Principal Motivation

The "why warehouse" pitch is the **first architecture decision** a
new DE org makes. The Principal delivers the pitch in 5 minutes
with ROI numbers. CTOs approve it because the alternative is
uncontrolled analytics on production databases.

---

## Lesson 4 — What is a Data Warehouse (Article)

### Theory

The full article. Mental model — the warehouse has five
characteristics (Inmon's definition):

| Characteristic | What it means |
|----------------|---------------|
| **Subject-oriented** | Organized by business subject, not application |
| **Integrated** | Consistent data definitions across sources |
| **Time-variant** | All data has a timestamp; history preserved |
| **Non-volatile** | Data is loaded, not updated in place |
| **Used for decision-making** | Optimized for OLAP, not OLTP |

Plus the modern view: a warehouse is **decoupled storage +
compute** — that's why Snowflake, BigQuery, Redshift Serverless
all look similar architecturally.

### Practical Example

Compare:

| | OLTP | OLAP (Warehouse) |
|---|------|------------------|
| Workload | Transactions | Analytics |
| Operations | INSERT/UPDATE/DELETE | SELECT (bulk) |
| Schema | Normalized | Denormalized/star |
| Storage | Row | Columnar |
| Latency | Sub-second | Seconds-minutes |
| Volume | GB-TB | TB-PB |

### AI Use Case

**AI-generated warehouse schema.** Given an OLTP schema, AI
generates the corresponding star schema. The Principal's edge:
faster dimensional modeling.

### CTO / Principal Motivation

Defining what a warehouse **is** is the **starting gun** for every
data architecture conversation. CTOs who internalize the
subject-oriented / integrated / time-variant / non-volatile
framework win arguments because they have the vocabulary.

---

## Lesson 5 — Kimball's Approach to Data Warehousing (Video)

### Theory

Kimball's approach is **bottom-up dimensional modeling**. Mental
model:

- **Star schema** — fact tables (events/measures) at the center,
  surrounded by dimension tables (entities).
- **Bus matrix** — identifies conformed dimensions shared across
  marts (date, customer, product).
- **Conformed dimensions** — same definition across marts.
- **Slowly Changing Dimensions (SCD)** — Type 1 (overwrite),
  Type 2 (history), Type 3 (previous value).

The Kimball lifecycle:

```
Project planning → Requirements → Dimensional modeling → Physical design → ETL → BI apps
```

### Practical Example

A retail star schema:

```
fact_sales (date_id, customer_id, product_id, store_id, qty, revenue)
dim_date (date_id, date, day_of_week, month, quarter, holiday)
dim_customer (customer_id, name, segment, country, join_date)
dim_product (product_id, sku, name, category, brand)
dim_store (store_id, name, region, format)
```

Conformed `dim_date` is shared across `fact_sales`, `fact_inventory`,
`fact_returns`. **Single source of truth for time.**

### AI Use Case

**AI-generated star schemas.** "Design a star schema for a
streaming service" → AI proposes fact + dim tables with SCD type
recommendations. The Principal's edge: faster modeling.

### CTO / Principal Motivation

Kimball vs Inmon is the **classical warehouse debate** (covered
next lesson). The Principal picks a side based on the team's
strengths. CTOs approve the choice based on time-to-value (Kimball
wins here — usually 3-6 months to first mart vs 12-18 for Inmon).

---

## Lesson 6 — Kimball's DW Approach (Article)

### Theory

The full Kimball lifecycle. Mental model — the **four tracks**:

| Track | Output |
|-------|--------|
| **Technology** | Infrastructure, tools, performance |
| **Data** | Staging → conformed → marts |
| **Applications** | BI dashboards, analytics apps |
| **Adoption** | Training, rollout, support |

The **dimensional modeling** step is the heart. The four-step
process:

1. **Select the business process** (e.g., sales, inventory).
2. **Declare the grain** (one row per...).
3. **Identify the dimensions** (who, what, when, where, why).
4. **Identify the facts** (numeric measures).

### Practical Example

A "sales analytics" marts build:

1. Process: retail sales.
2. Grain: one row per line item per sale.
3. Dimensions: date, customer, product, store, promotion.
4. Facts: quantity, gross_revenue, net_revenue, discount, cost.

### AI Use Case

**AI-augmented dimensional modeling.** AI watches query patterns,
suggests new facts and dimensions. The Principal's edge:
self-healing marts.

### CTO / Principal Motivation

Kimball's approach is the **default methodology** for analytical
warehouses in 2026. The Principal who runs it well ships marts
3× faster than teams without methodology. CTOs see this as
**time-to-value** for analytics investments.

---

## Lesson 7 — OLAP vs OLTP (Video)

### Theory

The fundamental split. Mental model:

| | OLTP | OLAP |
|---|------|------|
| **Purpose** | Run the business | Analyze the business |
| **Workload** | Many small transactions | Few large queries |
| **Schema** | Normalized (3NF) | Star/snowflake |
| **Storage** | Row-oriented | Columnar |
| **Indexes** | Many B-tree | Few bitmap/zone |
| **Latency** | Sub-100 ms | Seconds-minutes |
| **Volume** | GB-TB | TB-PB |
| **Examples** | MySQL, Postgres, Oracle | Snowflake, Redshift, BigQuery |

### Practical Example

OLTP query:

```sql
SELECT * FROM orders WHERE order_id = 12345;  -- 1 row, fast lookup
```

OLAP query:

```sql
SELECT date_trunc('month', order_date) AS month,
       sum(revenue) AS total
FROM orders
WHERE order_date >= '2025-01-01'
GROUP BY 1;  -- 100M rows, aggregates
```

The OLTP query is fast because of the primary-key index; the OLAP
query is fast because of columnar + partitioning + MPP.

### AI Use Case

**AI-powered workload classifier.** AI classifies queries as OLTP
or OLAP based on patterns, routes accordingly. The Principal's
edge: prevents OLAP queries from hitting OLTP systems.

### CTO / Principal Motivation

The OLTP/OLAP distinction is the **first mental model every DE
learns**. CTOs use it daily to explain why the team needs a
separate analytical system. "We can't run analytics on the
production database" is the conversation starter.

---

## Lesson 8 — OLAP vs OLTP (Guide) (Article)

### Theory

The full guide. Mental model — extended comparison with
operational metrics:

| Metric | OLTP | OLAP |
|--------|------|------|
| **Concurrent users** | 1000s | 10s-100s |
| **Query type** | Predefined | Ad-hoc |
| **Data scope** | Current | Historical |
| **Update pattern** | Frequent writes | Bulk loads |
| **Backup** | Critical | Less critical |
| **Performance goal** | Transaction throughput | Query throughput |

The "why they need to be separate" reason is the **use-case
collision**: OLTP optimizes for fast single-row reads + writes;
OLAP optimizes for bulk aggregations. Running OLAP on OLTP
destroys OLTP performance.

### Practical Example

The "anti-pattern":

```
Analyst: "Can I run this report on the production DB?"
Engineer: "Sure..."
SELECT customer_id, sum(amount) FROM orders GROUP BY customer_id;
-- 10-minute table scan
-- → Production checkout: latency 200ms → 8 seconds
-- → Customers: complain → revenue drops
```

The right pattern: ETL from OLTP to OLAP nightly; analyst queries
the OLAP.

### AI Use Case

**AI-driven traffic shaping.** AI classifies queries by latency
sensitivity, routes to OLTP or OLAP. The Principal's edge: zero
incidents from rogue analytical queries.

### CTO / Principal Motivation

The OLTP/OLAP separation is **the most important architectural
decision** in early-stage data platforms. Get it right and you
sleep well. Get it wrong and you have monthly outages. The
Principal owns the **routing policy**; the CTO owns the
**incident narrative**.

---

## Lesson 9 — Data Warehouse vs Data Lake (Video)

### Theory

The classic debate. Mental model:

| | Data Warehouse | Data Lake |
|---|---------------|-----------|
| **Data type** | Structured | Structured + semi + unstructured |
| **Schema** | Schema-on-write | Schema-on-read |
| **Users** | Analysts, BI | Data scientists, ML |
| **Storage cost** | $$$ | $ |
| **Query performance** | Excellent | Variable |
| **Governance** | Strong | Weak (historically) |

The 2026 reality: **lakehouse convergence** (Iceberg, Delta)
blurs the line. Iceberg in Snowflake vs Parquet in S3 is now a
config choice, not an architecture decision.

### Practical Example

Cost comparison for 100 TB:

| System | Storage / month | Query cost |
|--------|-----------------|------------|
| Snowflake (always-on) | $2,000 + compute | $5/TB scanned |
| Athena (serverless) | $2,000 (S3) | $5/TB scanned |
| Redshift (ra3) | $20/TB + compute | bundled |
| BigQuery (logical) | $20/TB + slot | bundled |

The "cheapest" depends on query volume.

### AI Use Case

**AI-driven lake-vs-warehouse advisor.** AI analyzes access
patterns and recommends the right tool per workload. The
Principal's edge: optimal cost-performance.

### CTO / Principal Motivation

The lake-vs-warehouse decision is **the CTO's strategic call**. The
2026 default: lakehouse (Iceberg) for new builds. The Principal
owns the **migration plan from old warehouse to lakehouse**.

---

## Lesson 10 — DW vs Data Lake (Article)

### Theory

The full comparison. Mental model — the decision tree:

```
What data types? → All structured → Warehouse
                → Mixed → Lake or Lakehouse

Who uses it?    → Analysts → Warehouse
              → Data scientists → Lake

Governance?     → Strict → Warehouse
              → Loose → Lake

Query SLA?      → Sub-second → Warehouse
              → Seconds-minutes → Lake/Lakehouse

Cost priority?  → Predictable → Warehouse (with reservations)
              → Pay-per-use → Lake
```

### Practical Example

A company with both needs:

```
Source → Lake (Iceberg on S3) → Warehouse (Snowflake) for BI
                              → Notebook (Athena) for DS
                              → ML (SageMaker) for features
```

The lake is the **single source of truth**; the warehouse is the
**curated analytics layer**.

### AI Use Case

**AI-driven lake-warehouse integration.** AI bridges data
catalogs across lake and warehouse. The Principal's edge:
unified governance.

### CTO / Principal Motivation

The lake/warehouse strategy is **the CTO's data platform
narrative**. The Principal delivers the **architecture diagram**;
the CTO delivers the **cost + governance story**.

---

## Lesson 11 — Quiz: DW Foundations

### Theory

Validate: lifecycle placement, Kimball methodology, OLAP/OLTP
distinction, lake-vs-warehouse trade-offs.

### Practical Example

The 10-question drill:

1. Why is a warehouse time-variant?
2. Kimball vs Inmon — when to use which?
3. OLAP indexing strategy?
4. Why can't we run OLAP on OLTP?
5. Lakehouse vs warehouse in 2026?

### AI Use Case

AI-generated flashcards.

### CTO / Principal Motivation

The foundations quiz is the **prerequisite for the architecture
and loading-pattern modules**.

---

# Module 2 · Warehouse Architecture (4 lessons)

## Lesson 1 — Layered Architecture

### Theory

The canonical **layered warehouse architecture**. Mental model:

```
Bronze  → Silver → Gold → Marts
(raw)    (cleaned) (curated) (BI-ready)
```

- **Bronze** — raw ingest, append-only, schema-on-read.
- **Silver** — cleaned, deduplicated, conformed.
- **Gold** — business logic, aggregations, joined.
- **Marts** — BI-friendly dimensional models.

Each layer has a different audience and SLA. Bronze for engineers
(replay); Silver for data scientists (analysis); Gold for analysts
(reporting); Marts for BI tools.

### Practical Example

```sql
-- Bronze: raw CDC
CREATE TABLE bronze.orders AS
SELECT * FROM kafka_orders;

-- Silver: cleaned + deduped
CREATE TABLE silver.orders AS
SELECT *,
       row_number() OVER (PARTITION BY order_id ORDER BY _ingested_at DESC) AS rn
FROM bronze.orders
QUALIFY rn = 1;

-- Gold: business logic
CREATE TABLE gold.daily_revenue AS
SELECT order_date, sum(amount) AS revenue
FROM silver.orders
GROUP BY 1;

-- Mart: BI star schema
CREATE TABLE mart.fact_sales AS
SELECT order_id, date_id, customer_id, product_id, amount
FROM gold.daily_revenue
JOIN silver.orders USING (order_date);
```

### AI Use Case

**AI-curated gold layer.** AI watches analyst queries, recommends
new gold tables to materialize. The Principal's edge: lower
analyst query latency.

### CTO / Principal Motivation

The layered architecture is **the 2026 default**. The Principal
owns the **layer definitions**; the CTO owns the **governance
narrative** (bronze is collected, gold is trusted).

---

## Lesson 2 — Kimball vs Inmon

### Theory

The classical debate. Mental model:

| | Kimball | Inmon |
|---|---------|-------|
| **Approach** | Bottom-up (marts first) | Top-down (warehouse first) |
| **Schema** | Star | Normalized (3NF) |
| **Time-to-value** | 3-6 months | 12-18 months |
| **Conformed dims** | Critical | Not needed |
| **Skill required** | Dimensional modeling | Enterprise-wide data modeling |
| **Best for** | BI-driven org | Data-quality-driven org |

**2026 consensus:** Kimball wins for BI; Inmon-style normalized
warehouse is rare. Most modern orgs use a hybrid: lake (Inmon-like
integrated data) + Kimball marts (BI).

### Practical Example

A 50-engineer fintech:
- Lakehouse (Iceberg) for integrated source-of-truth data.
- Snowflake gold + marts for BI.
- Kimball-style marts for finance + ops dashboards.
- Inmon-style normalized for regulatory reporting.

### AI Use Case

**AI-driven methodology selection.** AI analyzes the org's data
maturity and recommends Kimball, Inmon, or hybrid. The
Principal's edge: faster architectural decisions.

### CTO / Principal Motivation

Kimball vs Inmon is a **CTO-level decision** that compounds.
Pick Kimball for fast iteration; Inmon for data-quality-first
industries (banking, healthcare). The Principal owns the
**methodology standard**.

---

## Lesson 3 — Marts & Semantic Layer

### Theory

**Marts** are BI-ready datasets. **Semantic layer** is the
abstraction that hides physical tables behind business concepts.
Mental model:

- **Mart** — physical implementation (table/view).
- **Semantic layer** — logical model (`dbt semantic models`,
  Cube, LookML).
- **Metric layer** — definitions of business metrics
  (active_user = unique users with event in last 30 days).

The trend in 2026: **metric layer + semantic layer as a product**
(tools: dbt Semantic Layer, Cube, Lightdash, MetricFlow).

### Practical Example

A semantic layer:

```yaml
# metrics/active_users.yml
- name: active_users
  type: simple
  type_params:
    measure: count_distinct_user_id
  entity: user
  description: "Unique users with at least one event in the last 30 days"
  filter: |
    {{ Dimension('event_time') }} >= dateadd(day, -30, current_date)
```

```sql
-- Generated query (auto)
SELECT count(DISTINCT user_id) AS active_users
FROM silver.events
WHERE event_time >= dateadd(day, -30, current_date)
```

### AI Use Case

**AI-augmented semantic layer.** AI suggests metric definitions,
flags inconsistencies across dashboards. The Principal's edge:
unified metric definitions.

### CTO / Principal Motivation

The semantic layer is the **CTO's metric consistency tool**.
"Every dashboard uses the same definition of revenue" is a
board-level claim. The Principal owns the **metric library**; the
CTO owns the **trust narrative**.

---

## Lesson 4 — Quiz: Warehouse Architecture

### Theory

Validate: layered architecture decisions, Kimball vs Inmon choice,
semantic layer pattern.

### Practical Example

The 5-question drill:

1. Why layer the warehouse?
2. When pick Kimball vs Inmon?
3. What does a semantic layer solve?
4. Where do marts sit in the layered architecture?

### AI Use Case

AI-generated architecture quizzes.

### CTO / Principal Motivation

Architecture decisions compound. The Principal's standards
chart saves 6 months of mid-stream course-correction.

---

# Module 3 · How Warehouses Work (4 lessons)

## Lesson 1 — Columnar Storage

### Theory

The fundamental storage layout. Mental model:

- **Row storage** — each row is contiguous. Fast for full-row
  reads (OLTP).
- **Columnar storage** — each column is contiguous. Fast for
  analytical queries that read few columns (OLAP).
- **Compression** — columns have repeating values, so they
  compress well (10-50× compression with RLE/dict encoding).
- **Vectorized execution** — columnar format enables SIMD-style
  processing.

The math:

```
Row:  100 columns × 8 bytes = 800 bytes per row
      Query needs 3 columns → reads 800 bytes

Columnar: 100 columns × 8 bytes × N rows
          Query needs 3 columns → reads 24 bytes per row × N
          → 30× less I/O
```

### Practical Example

A columnar table:

```
Block layout:
[user_id block][amount block][date block][country block]

Query: SELECT sum(amount) FROM t WHERE country = 'US';
→ Reads only country block (filter) + amount block (sum)
→ Skips user_id, date blocks
```

This is why Snowflake / Redshift / BigQuery are fast.

### AI Use Case

**AI-optimized column ordering.** AI analyzes query patterns and
recommends column storage order. The Principal's edge: 2-5×
faster queries.

### CTO / Principal Motivation

Columnar storage is **the reason columnar warehouses cost less
than row databases for analytics**. The Principal owns the
**table design standard**; the CTO sees the **query performance
and cost metrics**.

---

## Lesson 2 — MPP & Compute/Storage

### Theory

**Massively Parallel Processing** — multiple nodes working on the
same query. Mental model:

- **Leader node** — query planner, coordinator.
- **Compute nodes** — execute query in parallel.
- **Storage** — local (each node has data) or shared (S3 + cache).
- **Decoupled compute/storage** — Snowflake, BigQuery, Athena;
  scale compute independently from storage.

The scaling math:

```
Query time = (data_per_node × processing_speed) / num_nodes
           = (1 TB / node × 10 sec/GB) / N nodes

For 1 TB total data, 1 node = 10000 sec = 2.8 hours
For 1 TB total data, 10 nodes = 1000 sec = 17 min
For 1 TB total data, 100 nodes = 100 sec = 1.7 min
```

### Practical Example

A 100-node Redshift cluster vs a 10-node one: 10× faster query,
10× cost. The trade-off: only run 100 nodes when you actually
need 10× speed.

### AI Use Case

**AI-driven warehouse sizing.** AI watches query patterns and
recommends cluster size, warehouse type. The Principal's edge:
2× cost reduction from automated sizing.

### CTO / Principal Motivation

The MPP sizing decision is **the largest cost variable in a
warehouse**. A 10× oversized warehouse burns $500k/year. The
Principal owns the **sizing standard**; the CTO owns the
**warehouse cost narrative**.

---

## Lesson 3 — Partitioning & Pruning

### Theory

Partitioning = physical data organization by a column. Pruning =
skipping irrelevant partitions at query time. Mental model:

- **Partition by date** — most common; query 1 day = read 1/30
  of monthly data.
- **Partition by tenant** — multi-tenant SaaS; query 1 tenant =
  read 1/N.
- **Partition by composite** — date + tenant (be careful of
  cardinality).

The trade-off:

```
Too few partitions → no pruning benefit
Too many partitions → metadata overhead, small-file problem
Sweet spot: 1000s of partitions, not millions
```

### Practical Example

```sql
-- 30 TB / 365 days = ~80 GB/day
-- Query: last 7 days → ~560 GB scanned (vs 30 TB)
-- 50× query cost reduction

SELECT * FROM events WHERE event_date >= current_date - 7;
-- Without partition pruning: scans 30 TB
-- With partition pruning: scans 560 GB
```

### AI Use Case

**AI-driven partition advisor.** AI watches query patterns and
recommends partition key + clustering. The Principal's edge:
50-100× cost reduction on common queries.

### CTO / Principal Motivation

Partitioning is **the single biggest performance lever**. The
Principal's deliverable: a **partitioning standard** enforced
by code review. CTOs see this as **query cost reduction**.

---

## Lesson 4 — Quiz: How Warehouses Work

### Theory

Validate: columnar vs row trade-offs, MPP scaling math,
partitioning strategies.

### Practical Example

The 5-question drill:

1. Why is columnar faster for analytics?
2. Compute/storage decoupling benefit?
3. Ideal partition cardinality?
4. Cluster sizing trade-off?

### AI Use Case

AI-generated optimization drills.

### CTO / Principal Motivation

Internal knowledge is the **prerequisite for vendor selection**
(Snowflake vs Redshift vs BigQuery).

---

# Module 4 · Loading the Warehouse (5 lessons)

## Lesson 1 — Full vs Incremental

### Theory

Two loading strategies. Mental model:

| | Full load | Incremental load |
|---|-----------|------------------|
| **What** | Replace all data | Append new/updated |
| **Cost** | High (re-process everything) | Low (process delta only) |
| **Complexity** | Low | High (track delta) |
| **Latency** | High (full re-process) | Low (sub-minute possible) |
| **Idempotency** | Trivial | Requires merge logic |
| **Use when** | Small dims (<10M rows) | Large facts (>100M rows) |

The hybrid: **incremental merge with full refresh fallback**.

### Practical Example

A fact table load:

```sql
-- Incremental: append new partitions
INSERT INTO fact_sales
SELECT * FROM staging.sales
WHERE order_date > (SELECT max(order_date) FROM fact_sales);

-- Or MERGE for upsert
MERGE INTO fact_sales t
USING staging.sales s
ON t.order_id = s.order_id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;
```

### AI Use Case

**AI-driven load-strategy advisor.** AI watches table growth
rates and recommends full vs incremental. The Principal's edge:
lower load cost automatically.

### CTO / Principal Motivation

The full vs incremental decision is **the largest cost
variable in loading**. The Principal's deliverable: a **load
pattern standard**. CTOs see this as **load cost reduction**.

---

## Lesson 2 — Change Data Capture

### Theory

CDC = capture database changes and replicate them downstream.
Mental model:

- **Log-based CDC** — Debezium reads WAL/binlog. Full fidelity.
- **Trigger-based CDC** — database triggers write change rows.
- **Query-based CDC** — periodic SELECT with timestamp filter.
- **Snapshot + streaming** — initial full read, then changes.

The 2026 standard: **Debezium for OLTP CDC** (open, free,
production-proven).

### Practical Example

Debezium to Snowflake:

```
Postgres WAL → Debezium → Kafka (CDC topic)
                                    ↓
                              Kafka Connect Snowflake Sink
                                    ↓
                              Snowflake bronze.events
```

### AI Use Case

**AI-driven CDC schema evolution.** AI watches Debezium schema
changes and auto-updates downstream tables. The Principal's
edge: zero-downtime schema evolution.

### CTO / Principal Motivation

CDC is **the foundation for replication and real-time
analytics**. The Principal owns the **CDC platform**; the CTO
owns the **data freshness narrative**.

---

## Lesson 3 — Idempotent Loads

### Theory

An idempotent load = **running it twice produces the same result
as running it once**. Mental model:

- **INSERT-only loads** — run twice → duplicates (NOT idempotent).
- **MERGE-based loads** — run twice → same result (idempotent).
- **DELETE + INSERT** — run twice → same result (idempotent).
- **TRUNCATE + INSERT** — run twice → same result (idempotent).

### Practical Example

```sql
-- NOT idempotent
INSERT INTO target SELECT * FROM source;

-- Idempotent (MERGE)
MERGE INTO target t USING source s ON t.id = s.id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;

-- Idempotent (truncate + insert)
TRUNCATE target;
INSERT INTO target SELECT * FROM source;
```

### AI Use Case

**AI-driven idempotency audit.** AI scans ETL code, flags
non-idempotent operations. The Principal's edge: zero duplicate
data.

### CTO / Principal Motivation

Idempotency is **the foundation of data correctness**. The
Principal owns the **load pattern standard**; the CTO sees the
**MTTR + correctness dashboards**.

---

## Lesson 4 — Loading Dims & Facts

### Theory

**Dimensions** (slowly changing, referential integrity) load
**before facts** (volumetric, append-mostly). Mental model:

- **Dim load order**: date → reference data → customer → product.
- **Fact load order**: per fact source, MERGE into the fact.
- **SCD Type 2** — close old version, insert new.

The pattern:

```
Stage raw data → Load dims (SCD2) → Load facts (MERGE) → Run DQ tests → Promote to gold
```

### Practical Example

A daily load:

```sql
-- 1. Stage
CREATE OR REPLACE TABLE staging.sales_daily AS
SELECT * FROM raw_sales WHERE sale_date = current_date;

-- 2. SCD2 dim
MERGE INTO dim_customer t USING staging.customers s
ON t.customer_id = s.customer_id
WHEN MATCHED AND t.email <> s.email THEN
  UPDATE SET effective_to = current_timestamp, is_current = false;

INSERT INTO dim_customer
SELECT customer_id, ..., current_timestamp, NULL, true
FROM staging.customers s
WHERE NOT EXISTS (SELECT 1 FROM dim_customer WHERE customer_id = s.customer_id);

-- 3. Load fact
INSERT INTO fact_sales
SELECT s.sale_id, d.date_id, c.customer_id, p.product_id, s.amount
FROM staging.sales_daily s
JOIN dim_date d ON s.sale_date = d.date
JOIN dim_customer c ON s.customer_id = c.customer_id AND c.is_current
JOIN dim_product p ON s.product_id = p.product_id AND p.is_current;

-- 4. DQ
ASSERT (SELECT count(*) FROM fact_sales WHERE sale_date = current_date) > 0;
```

### AI Use Case

**AI-driven dim/fact generation.** AI generates dim and fact
DDL + load patterns from source schema. The Principal's edge:
faster modeling.

### CTO / Principal Motivation

The dim/fact load pattern is **the most-replicated data
engineering code in the org**. The Principal's deliverable:
a **reusable load framework**. CTOs see this as **time-to-value
for new sources**.

---

## Lesson 5 — Quiz: Loading the Warehouse

### Theory

Validate: full vs incremental trade-offs, CDC mechanics,
idempotent load patterns, dim/fact sequencing.

### Practical Example

The 5-question drill:

1. Why is MERGE idempotent but INSERT not?
2. CDC latency by method?
3. Why load dims before facts?
4. SCD2 column requirements?

### AI Use Case

AI-generated load-pattern drills.

### CTO / Principal Motivation

Loading mastery is **the prerequisite for production-grade
warehouses**.

---

# Closing Notes

## The Promotion Path from this Course

| Level        | Skill unlocked by this course | Compensation signal |
|--------------|-------------------------------|---------------------|
| Senior DE    | Loads dims and facts; writes MERGE statements | $150-200k |
| Staff DE     | Designs layered warehouse architecture; tunes for cost/performance | $200-280k |
| Principal DE | Sets org-wide warehouse standards; leads warehouse vendor selection | $280-400k |
| Director / VP | Owns warehouse platform budget; signs off on lakehouse migration | $350-500k+ |
| CTO          | Decides Snowflake vs BigQuery vs Databricks vs lakehouse strategy | $400-700k+ |

## The Warehouse Principal's Strategic Toolkit

Six decisions a Principal owns:

1. **Kimball vs Inmon** — default Kimball for BI; hybrid for
   regulated industries.
2. **Lakehouse vs warehouse** — default lakehouse (Iceberg) for
   new builds; Snowflake/Redshift for BI performance.
3. **Columnar vs row** — columnar always for analytics.
4. **MPP sizing** — right-size based on query latency SLA; not
   over-provision.
5. **Partition strategy** — partition by date + tenant for SaaS;
   date only for B2C.
6. **Idempotent loads** — MERGE always; INSERT banned for
   production loads.

## The Two CTO Pillars (Warehousing flavor)

This course is the **technical pillar** for warehouse-platform
CTOs. The **other pillar** is the **TCO narrative** — "$0.005/GB
scanned with our partitioning + columnar design" beats
"$X/year on Snowflake." CTOs who have both pillars close deals
5× faster.

## Cross-References

- **DE Foundations** — `01_de_foundations_track.md`.
- **Snowflake Hands-On full-detail** — `snowflake_full_detail.md`
  (vendor-specific deep dive).
- **AWS DE CTO plan** — `aws_de_cto_learning_plan.md` (Redshift vs
  Athena decision tree).
- **DE System Design CTO plan** — `de_system_design_cto_learning_plan.md`
  (warehouse in architecture patterns).
