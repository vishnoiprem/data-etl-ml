---
l_id: L58
title: "Maximize Caching"
duration: "7:00"
prereqs:
  - L57 (Caching - Theory)
---

# L58 — Maximize Caching

> **Section:** 7 — Performance optimization
> **Duration:** 7:00

## Prereqs

- L57 — Caching — Theory

## Key terms

- **`USE_CACHED_RESULT`** — session parameter. `TRUE` (default)
  means the result cache can satisfy the query. `FALSE` forces
  a fresh execution.
- **Parameterised SQL** — same SQL text, different bind
  variables. Snowflake can serve the **same result cache entry**
  to many users if the SQL text matches exactly.
- **Cache invalidation** — anything that modifies the underlying
  micro-partitions (insert, delete, `TRUNCATE`, `MERGE`)
  invalidates the result cache for the affected tables.
- **Clustering key** — covered in section 8; the right
  clustering key dramatically improves query history cache
  pruning.

## Lecture

Knowing the three caches from L57 is the theory. This lecture
is the **practice**: how to write your SQL and structure your
workload so the caches hit as often as possible.

### Tip 1 — keep the SQL text byte-for-byte identical

The result cache is keyed on the **exact** SQL text. Whitespace
differences break it:

```sql
-- Two different cache entries
SELECT COUNT(*) FROM orders;
SELECT count(*) FROM orders;
```

For dashboards, build the query as a **parameterised
template**:

```sql
-- Same SQL, different bind values → same result cache entry
SELECT * FROM orders WHERE customer_id = ? AND order_ts >= ?;
```

Most BI tools (Tableau, Power BI, Streamlit) do this
automatically — they reuse the same prepared statement with
new bind values. The result cache is hit even though the
results differ per user.

### Tip 2 — don't modify data unnecessarily

Every `INSERT` / `DELETE` / `TRUNCATE` / `MERGE` invalidates
the result cache for the affected tables. Two patterns:

- **Batch your loads** — one `COPY INTO` at 2 AM beats 100
  small loads at 2 PM. Fewer invalidations.
- **Use `CREATE OR REPLACE TABLE` only when you must** — the
  table swap invalidates **all** result cache entries that
  referenced the old table.

### Tip 3 — pin queries to a specific warehouse

The local disk cache is per-warehouse. Run "the same dashboard"
on the same warehouse, not whatever is the current default:

```sql
USE WAREHOUSE bi_wh;
-- dashboards run here, every time
```

A Snowflake account without warehouse pinning wastes the local
disk cache: the same query on `bi_wh` and on `bi_wh2` reads
from S3 twice.

### Tip 4 — set `USE_CACHED_RESULT` deliberately

```sql
ALTER SESSION SET USE_CACHED_RESULT = FALSE;
-- run a query that must reflect the latest data
ALTER SESSION SET USE_CACHED_RESULT = TRUE;
-- back to default
```

`FALSE` is what you set when an analyst asks "is this up to
date?" — the result cache is 24 hours stale, so for a brand-new
row you want to bypass it.

### Tip 5 — measure cache hit rate

The Query History has a `bytes_spilled_to_local_storage`,
`partitions_scanned`, and `partitions_total` per query. The
**cache hit ratio** for the result cache is visible in
`QUERY_HISTORY` indirectly:

```sql
SELECT
    COUNT(*)                                                    AS n_queries,
    SUM(CASE WHEN total_elapsed_time < 1000 THEN 1 ELSE 0 END)  AS sub_second_queries,
    sub_second_queries / n_queries                              AS hit_ratio
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY(
    DATE_RANGE_START => DATEADD('day', -1, CURRENT_TIMESTAMP())
))
WHERE query_type = 'SELECT';
```

A hit ratio above 50% means the result cache is doing real
work. Below 20% means your queries are too unique (parameter
storm) or the data is too volatile.

### Tip 6 — design for the query history cache

The query history cache prunes micro-partitions. Two ways to
help it:

- **Cluster on the right key** — covered in section 8.
- **Filter on a column Snowflake knows about** — avoid
  `WHERE FUNCTION(col) = ...` (it disables pruning); prefer
  `WHERE col BETWEEN …` (pruning-friendly).

```sql
-- Bad: prevents partition pruning
SELECT * FROM orders WHERE YEAR(order_ts) = 2026;

-- Good: pruning-friendly
SELECT * FROM orders WHERE order_ts >= '2026-01-01'
                         AND order_ts <  '2027-01-01';
```

### Tip 7 — result cache vs `MATERIALIZED VIEW`

When a result cache is **almost free** but you want it to
**persist beyond 24 hours**, use a `MATERIALIZED VIEW`
(covered later in the course). It's the durable form of
"precomputed result".

### Cache-conscious dashboard pattern

```text
1. User opens dashboard.
2. Tool sends parameterised SQL with bind values.
3. Snowflake checks result cache → instant, free.
4. New data is loaded at 2 AM → result cache invalidated.
5. First user at 9 AM triggers a fresh scan → ~5 s.
6. Local disk cache is now warm → subsequent users are fast.
7. Result cache builds up again as users repeat queries.
```

That's the **steady state** of a well-cached dashboard.

### What caching does **not** fix

- **Long, I/O-bound scans** — caching speeds up the
  *next* scan; the *first* one is still a scan.
- **A query that aggregates 5 TB** — caches don't help;
  clustering and a bigger warehouse do.
- **Volatile data** — if you `INSERT` every 10 s, the result
  cache is invalidated every 10 s.

## Hands-on

Run the `USE_CACHED_RESULT = FALSE` test from tip 4, then run
the same query with `TRUE`. Compare the `total_elapsed_time`
in the Query History — the first should be a real scan; the
second should be milliseconds.

## Quiz prep

- What does `USE_CACHED_RESULT = FALSE` do?
- Why is the local disk cache per-warehouse?
- How can parameterised SQL improve the result cache hit
  ratio?

## Key takeaways

- Keep SQL text **byte-for-byte identical** for result cache
  hits.
- **Pin queries to specific warehouses** for local disk cache
  hits.
- Filter on **pruning-friendly** predicates for query history
  cache hits.
- Use `USE_CACHED_RESULT = FALSE` to bypass the result cache
  when fresh data is required.

## What's next

In **Section 8 — Loading from AWS** we'll switch from internal
stages to **S3**: clustering (theory + practice), creating an
S3 bucket, IAM policy, and the storage integration object that
links it all to Snowflake.