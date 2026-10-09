# 22 — Partitioning Strategies in the Warehouse

> **Lesson 22 of 30 — Loading**

The single biggest performance lever in a warehouse. A
well-partitioned table scans 1% of the data for a typical query;
a poorly-partitioned one scans 100%. This lesson is the three
partitioning strategies and when to use each.

---

## 1. What partitioning is

A *partition* is a physical subdivision of a table. Each
partition stores a subset of the rows, identified by a partition
key. Queries that filter on the partition key read only the
relevant partitions.

```
Table "events" partitioned by DATE(event_time):

  events/2024-01-01/  ← partition
  events/2024-01-02/
  events/2024-01-03/
  ...
  events/2024-12-31/
```

A query `WHERE DATE(event_time) = '2024-01-15'` reads only the
`events/2024-01-15/` partition. The other 364 partitions are
skipped.

---

## 2. The three strategies

| Strategy | Partition key | Best for |
|---|---|---|
| **Date** | `DATE(event_time)` or `DATE(updated_at)` | Time-series, append-only |
| **Key** | `user_id` or other high-cardinality key | Multi-tenant, per-user queries |
| **Bucket** | `HASH(user_id) % N` | Skew-resistant, high-cardinality |

The senior move: "I'd default to date partitioning for
time-series data. For multi-tenant data I'd bucket by tenant
id to avoid hot partitions. For user-level data I'd use a
combination: date coarse, user_id fine."

---

## 3. Date partitioning

The most common pattern. Each day (or hour) is a partition:

```sql
-- Snowflake
CREATE TABLE events (
  event_id BIGINT,
  event_time TIMESTAMP,
  user_id BIGINT,
  payload VARIANT
)
PARTITION BY (DATE(event_time));

-- BigQuery
CREATE TABLE events
PARTITION BY DATE(event_time)
AS SELECT ...;
```

The benefits:
- Time-range queries are O(1) — only the relevant partitions
  are scanned.
- Old partitions can be dropped cheaply (just delete the files).
- Maintenance is per-partition (vacuum, optimize, statistics).

The pitfall: a partition per day × 5 years = 1825 partitions.
Most warehouses handle this fine; some (older Hive) struggle
beyond a few thousand.

---

## 4. Key partitioning

Partition by a high-cardinality key like `user_id`:

```sql
-- Postgres (declarative partitioning)
CREATE TABLE events_by_user (
  user_id BIGINT,
  event_time TIMESTAMP,
  payload JSONB
) PARTITION BY HASH (user_id);

CREATE TABLE events_by_user_0 PARTITION OF events_by_user
  FOR VALUES WITH (MODULUS 4, REMAINDER 0);
-- ... and 3 more
```

The benefit: per-user queries are fast. The pitfall: skew.
If one user has 50% of the events, one partition is huge.

The senior move: "Key partitioning is great for multi-tenant
data when tenants are roughly the same size. If one tenant
dominates, I'd bucket by hash and accept the skew, or I'd
add a sub-partition."

---

## 5. Bucket partitioning

Hash partitioning distributes rows evenly:

```sql
-- BigQuery
CREATE TABLE events
PARTITION BY DATE(event_time)
CLUSTER BY user_id;
```

The `CLUSTER BY` is BigQuery's term for *bucket partitioning*
within a date partition. Each date partition has N buckets
based on `HASH(user_id)`.

The benefit: combines the time-range pruning of date
partitioning with the user-pruning of key partitioning. The
pitfall: needs to be re-clustered periodically as data
distorts.

---

## 6. The partition pruning

The performance win comes from *partition pruning*: the
planner skips partitions that don't match the query.

```sql
-- This query prunes 364 of 365 partitions:
SELECT COUNT(*)
FROM events
WHERE event_time >= '2024-01-15' AND event_time < '2024-01-16';

-- This query prunes ZERO partitions (no filter on the key):
SELECT COUNT(*)
FROM events;  -- full scan, all 365 partitions
```

The senior move: "I'd always filter on the partition key. A
query that doesn't is a full scan, no matter how many
partitions."

---

## 7. The partition lifecycle

Partitions aren't immortal. The lifecycle:

```
  ┌──────────────┐
  │ active       │  ← written, read, optimized
  └──────┬───────┘
         │ (30 days)
         ▼
  ┌──────────────┐
  │ cold         │  ← read-only, not optimized
  └──────┬───────┘
         │ (1 year)
         ▼
  ┌──────────────┐
  │ archived     │  ← moved to S3 Glacier / equivalent
  └──────┬───────┘
         │ (compliance window)
         ▼
  ┌──────────────┐
  │ dropped      │  ← files deleted
  └──────────────┘
```

The senior move: "I'd set a 30-day cold window and a 1-year
archive window. After the compliance window, the partition
is dropped. This keeps the table small and the cost down."

---

## 8. The compaction problem

Bulk-loaded files (Parquet, ORC) accumulate as small files
inside a partition. A partition with 10,000 small files is
*slower* than one with 10 large files.

The mitigation: periodic *compaction*. A Spark / dbt job
reads the small files, writes one large file, and replaces.

```python
# The compaction pattern (Spark)
df = spark.read.parquet("s3://data/events/2024/01/15/")
df.repartition(1).write.mode("overwrite").parquet(
    "s3://data/events_compacted/2024/01/15/"
)
```

The senior move: "I'd run compaction on a schedule, say
nightly for hot partitions, weekly for cold ones."

---

## 9. The interview answer

> "I default to date partitioning for time-series data, with
> optional bucket clustering for high-cardinality keys. The
> partition key is the most common filter in queries. A
> well-partitioned table scans 1% of the data; a poorly
> partitioned one scans 100%. I'd set up a partition
> lifecycle: hot (active), cold (read-only, not optimized),
> archived (S3 Glacier), dropped (after compliance). I'd
> run compaction on a schedule to avoid the small-files
> problem."

That single paragraph covers: default strategy, partition
pruning, lifecycle, compaction. Senior answer in 30 seconds.

---

## Try it

Look at the most recent warehouse table you've worked on.
What's the partition key? Is the partition key the most
common filter? Is there a lifecycle policy? Is compaction
running? If any is "no," the table is either under-optimized
or will be in 6 months.
