# 2.2 — What is BigQuery

> **Section 2 · BigQuery Fundamentals · Lecture 2.2 · 3:38**

## 🎯 What you will learn

- A precise one-sentence definition of BigQuery
- The three resource models in BigQuery (slots, jobs, tables)
- The three pricing models and when each applies
- What BigQuery is explicitly *not*

---

## 🧠 Concept

### Definition

> **BigQuery is a fully managed, serverless, columnar data warehouse that separates storage from
> compute, and bills you for the bytes your queries scan rather than for the machines they run on.**

Every word in that sentence is load-bearing. Let's take them one at a time.

| Word | What it means |
|------|---------------|
| **Fully managed** | Google operates the storage, the compute, the catalog, the patching, the failover. You never touch a server. |
| **Serverless** | There is no cluster. When a query arrives, BigQuery provisions slots for it and releases them when it finishes. |
| **Columnar** | Data is stored column-by-column, compressed, and typed. Only the columns your query references are read. |
| **Separated storage from compute** | Storage is a durable service (Colossus); compute is ephemeral (Dremel). Neither is sized by the other. |
| **Billed on bytes scanned** | The unit of cost is data read, not cluster time. Idle clusters cost nothing because no cluster exists. |

### The three resource models

**1. Slots.** A slot is a unit of compute — roughly one vCPU with 4 GB of memory. BigQuery allocates
slots to a query based on the work it needs, up to your project's maximum.

```sql
-- Check your project's slot capacity
SELECT * FROM `region-us.INFORMATION_SCHEMA.SLOTS`
LIMIT 10;
```

A query using 1,000 slots for 30 seconds = 1,000 slot-seconds. This is the "CPU time" that pricing
for **capacity editions** is based on.

**2. Jobs.** Every operation in BigQuery is a job: a query, a load, an extract, a copy. Jobs have
state (`PENDING`, `RUNNING`, `DONE`), can be cancelled, and appear in the console and in
`INFORMATION_SCHEMA.JOBS`.

```sql
-- See recent jobs and their cost
SELECT
    job_id,
    job_type,
    state,
    creation_time,
    total_bytes_processed,
    ROUND((total_bytes_processed / POW(1024, 4)) * 6.25, 2) AS est_cost_usd,
    error_result
FROM `region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
ORDER BY total_bytes_processed DESC
LIMIT 20;
```

**3. Tables.** The unit of storage and schema. BigQuery offers several table types, and choosing
correctly is one of the highest-leverage decisions in the platform.

| Table type | What it is | Storage cost | Query cost | Use when |
|------------|-----------|--------------|-----------|----------|
| **Managed** | BigQuery owns storage | Yes | Scans stored bytes | The default. Data loaded into BigQuery. |
| **External** | Points at GCS/S3 files | No (GCS bills) | Scans files | Data stays in the lake; query it in place. |
| **Materialized view** | Pre-computed query result | Yes | Cheaper scans | Repeated expensive aggregations. |
| **Logical view** | Stored SQL, no data | No | Scans the base table | Reusable query logic, access control. |
| **Snapshot** | Point-in-time copy | Yes (billed as storage) | Scans snapshot | Time-travel analysis, safe table swaps. |
| **Streaming buffer** | Recent streaming inserts | Yes | Special pricing | Low-latency insert path. |
| **Capacity-optimized** | Managed, reorg-optimized | Yes | Cheapest scans | Large append-only tables. |
| **Storage-optimized** | Managed, columnar-optimized | Yes | Cheapest scans | Read-mostly, columnar workloads. |

💡 **Table type is a bigger lever than most people realize.** A table created as
`STORAGE_OPTIMIZED` can be **up to 70% cheaper to scan** than a standard managed table of identical
data, and `CAPACITY_OPTIMIZED` similarly reduces storage for large append-only data. This is often a
larger win than adding clustering.

```sql
-- Create a storage-optimized table
CREATE TABLE `YOUR_PROJECT_ID.analytics.events_archive`
OPTIONS (
  storage_billing_model = 'STORAGE_OPTIMIZED'
) AS
SELECT * FROM `YOUR_PROJECT_ID.analytics.events`;
```

---

## 💡 The three pricing models

| Model | How you pay | Commitment | Best for |
|-------|-------------|-------------|----------|
| **On-demand** | Per TiB scanned ($6.25) | None | Spiky, unpredictable, low-volume |
| **Capacity (slot)** | Per slot-hour (~$0.06) | 1yr/3yr optional | Steady, predictable, heavy usage |
| **Enterprise** | Contracted spend, custom rate | Annual | Large enterprises, custom support |

**Capacity editions** let you purchase slot capacity in the regions you use, which can cut costs
30–70% versus on-demand for steady workloads.

```sql
-- Create a capacity reservation (requires the right IAM role)
CREATE RESERVATION `YOUR_PROJECT_ID.analytics_slots`
AS
SELECT
  TIMESTAMP '2026-01-01 00:00:00' AS start_time,
  TIMESTAMP '2027-01-01 00:00:00' AS end_time,
  TRUE AS use_global_reservation,
  'US' AS location,
  100 AS slot_count;
```

---

## 🧠 What BigQuery is NOT

- **Not a database for OLTP.** No sub-10ms single-row writes, no secondary indexes, no transactions
  across rows.
- **Not a real-time serving store.** Streaming inserts are visible within a few seconds, but there is
  no millisecond-read serving tier. Use Bigtable.
- **Not free.** The free tier is generous for learning (1 TiB queries/month, 10 GB storage) and
  trivial for production.
- **Not infinitely fast.** A single query over 10 TB takes minutes regardless of pricing model.
- **Not schema-free.** Auto-detection helps, but it guesses. Production schemas are designed.

---

## 🛠️ Hands-On: Your First BigQuery Job

```sql
-- 1. The simplest possible query — BigQuery provides public datasets
SELECT
    country_name,
    country_code,
    continent_name,
    population
FROM `bigquery-public-data.world_bank.country_population`
WHERE year = 2020
ORDER BY population DESC
LIMIT 10;
```

```sql
-- 2. Check what it cost
SELECT
    total_bytes_processed,
    ROUND((total_bytes_processed / POW(1024, 4)) * 6.25, 4) AS cost_usd,
    total_slot_ms
FROM `region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE job_type = 'QUERY'
ORDER BY creation_time DESC
LIMIT 5;
```

💡 Notice `total_bytes_processed` is 0 for the public dataset query — Google does not charge for
bytes scanned on public datasets.

---

## 🔑 Key Takeaways

- BigQuery = fully managed + serverless + columnar + separated storage/compute + pay-per-scan.
- Three resource models: **slots** (compute), **jobs** (operations), **tables** (storage).
- **Table type is a first-class cost lever** — `STORAGE_OPTIMIZED` can cut scan cost by up to 70%.
- Three pricing models: on-demand, capacity (slot commitments), enterprise.
- BigQuery is an OLAP engine, not a database, not a serving store, and not free.

---

## 📚 Practice Exercises

1. **Resource model.** Write a query that shows, for your project, the total slot-seconds and total
   bytes processed in the last 7 days, grouped by job type.

2. **Table type selection.** For each, choose the table type and justify:
   - (a) A 90 PB immutable log archive, queried twice a year
   - (b) A daily fact table, 2 TB, queried by dashboards 50×/day
   - (c) A 5 GB lookup table updated hourly
   - (d) A frequently re-run aggregation over a 30 TB events table

3. **Pricing model.** A startup's monthly scanned volume is 3 TiB in month 1, 40 TiB in month 2, and
   stable at 40 TiB thereafter. On-demand costs are 40 × $6.25 = $250/month. Model the capacity
   edition cost assuming $0.06/slot-hour and 20 slots continuously reserved. At what volume does
   capacity win?

4. **Service boundary.** A product needs sub-20ms reads of the last 5 minutes of user session state.
   Why is BigQuery the wrong tool? What would you use, and how would BigQuery still be involved?

---

## 📖 Further Reading

- BigQuery overview — https://cloud.google.com/bigquery/docs/introduction
- BigQuery pricing — https://cloud.google.com/bigquery/pricing
- BigQuery reservations — https://cloud.google.com/bigquery/docs/reservations-intro
