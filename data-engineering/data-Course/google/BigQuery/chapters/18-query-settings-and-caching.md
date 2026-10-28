# 3.1 — Query Settings & Caching

> **Section 3 · Running Queries with Various Query Settings · Lectures 3.1–3.2 · 5:18 + 3:41**

## 🎯 What you will learn

- The four query settings that matter and how to set each
- How BigQuery's result cache works, and when it does **not** apply
- Maximum bytes billed as your cost circuit breaker
- Dry runs as a free planning tool

---

## 🧠 Concept

Every BigQuery query runs with a set of settings. Some are cosmetic; three of them have direct
financial impact.

### The settings that matter

| Setting | Default | Effect | Where to set |
|---------|---------|--------|--------------|
| **Maximum bytes billed** | Unlimited (on-demand) | **Hard cap — query fails if exceeded** | Job config, CLI flag, UI |
| **Use legacy SQL** | `false` (GoogleSQL) | Switches dialect | UI, CLI, SDK |
| **Maximum rows / bytes** | unlimited | Truncates result | Job config |
| **Timeout** | 6 hours | Query is cancelled | Job config |
| **Destination table** | none | Writes results to a table | UI, SDK |
| **Use query cache** | `true` | Reuses identical recent results | UI, SDK |
| **Random shuffle** | `false` | Randomizes row order | Job config |
| **Flatten results** | `true` | Repeats rows for nested data | Job config |

---

## 🧠 Maximum Bytes Billed

This is the single most important setting in BigQuery.

```sql
-- Set a cap on a single query
SELECT
    job_id,
    error_result.reason AS error_reason,
    error_result.message AS error_message
FROM `region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE job_type = 'QUERY'
  AND error_result.reason LIKE '%exceeded%'
ORDER BY creation_time DESC;
```

```bash
# CLI: cap a query at 1 GB
bq query --use_legacy_sql=false --max_bytes_billed=1000000000 \
  'SELECT COUNT(*) FROM `YOUR_PROJECT_ID.analytics.orders`'
```

```python
# Python: cap every query
from google.cloud import bigquery

config = bigquery.QueryJobConfig()
config.maximum_bytes_billed = 1_000_000_000   # 1 GB

job = client.query(sql, job_config=config)
try:
    result = job.result()
except Exception as exc:
    print(f"Query aborted: {exc}")
```

💡 **Set this as your personal default during development.** A cartesian join between two 10 TB
tables would scan ~100 TB and cost ~$625. With a 1 GB cap, it fails in seconds at zero cost.

⚠️ **Important distinction:** `maximum_bytes_billed` causes the query to **fail** — it does not
truncate results. It is a circuit breaker, not a limit. A failing query returns an error and
charges only for the bytes already processed.

---

## 🧠 The Query Cache

BigQuery caches query results to make repeated identical queries free and instant.

### How it works

```
Query arrives
    │
    ├─ Compute a cache key from:
    │    • the query text (normalized)
    │    • the referenced tables' versions
    │    • the query job's settings
    │
    ├─ Cache HIT?  → return cached results, $0, near-instant
    │
    └─ Cache MISS → execute normally, pay normally, store result
```

### Cache entry lifetime

- Results are cached for **24 hours** by default
- The cache is **per-user** — your cache hit does not benefit your colleague
- The cache is invalidated if any referenced table changes

### What is NOT cached

| Situation | Cached? | Why |
|-----------|---------|-----|
| Query with a `current_timestamp()` or non-deterministic function | ❌ | Results would be stale |
| Query against a streaming buffer table | ❌ | Data is still arriving |
| Query with `INFORMATION_SCHEMA` | ❌ | Changes constantly |
| Query with a random shuffle | ❌ | Non-deterministic |
| Query with a `TABLESAMPLE` clause | ❌ | Non-deterministic |
| Any query where a referenced table was modified | ❌ | Cache invalidated |
| Ordinary deterministic SELECT | ✅ | Eligible |
| DDL (CREATE, ALTER, DROP) | ❌ | Not a result to cache |
| DML (INSERT, UPDATE, DELETE, MERGE) | ❌ | Not a result to cache |

💡 **The cache makes ad-hoc exploration nearly free** — as long as you do not modify the tables
in between. This is why a dashboard that hits the same query repeatedly costs almost nothing, but
one that adds `NOW()` or a varying filter does.

⚠️ **The cache does not help a query with `WHERE event_date = CURRENT_DATE()`** if the table is
being written to, because the cache invalidates on every write.

### Caching in practice

```sql
-- Run this twice — the second is a cache hit
SELECT customer_id, SUM(total_amount) AS ltv
FROM `YOUR_PROJECT_ID.curated.orders`
GROUP BY customer_id;
```

```sql
-- Verify the cache hit in the job details:
SELECT
    job_id,
    creation_time,
    total_bytes_processed,      -- 0 on a cache hit
    total_bytes_billed,         -- 0 on a cache hit
    cache_hit,                  -- TRUE on a hit
    query_id
FROM `region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE job_type = 'QUERY'
ORDER BY creation_time DESC
LIMIT 10;
```

💡 **`total_bytes_billed = 0` is your cache-hit indicator.** The `cache_hit` column was added
later; `total_bytes_billed` is the more widely available signal.

---

## 🛠️ Hands-On

### 1. Set a byte cap and prove it works

```sql
-- This WILL fail — it would scan far more than 1 MB
SELECT o.order_id, c.name, o.total_amount
FROM `YOUR_PROJECT_ID.curated.orders` o
CROSS JOIN `YOUR_PROJECT_ID.curated.customers` c
LIMIT 10;
```

The error:
```
Resources exceeded during query execution. The query exceeded the maximum bytes
billed for this query. Set maximum_bytes_billed to a value larger than the
current query's estimated cost.
```

### 2. Dry run — free estimation

```bash
bq query --dry_run --use_legacy_sql=false '
  SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders`'
```

Output:
```
Job ID: ...dry-run
Bytes processed: 14827157552
```

💡 **Dry runs cost nothing and tell you the exact byte count.** Use them before every
non-trivial query. This is the most useful habit in BigQuery.

### 3. Compare cached vs uncached cost

```sql
-- Run 1
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders`;  -- billable

-- Run 2 (identical)  → cache hit, $0
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders`;

-- Run 3 (different, breaks the cache) → billable
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders` WHERE TRUE;
```

### 4. Legacy SQL vs GoogleSQL

```bash
# Legacy SQL (the old Hive-like dialect) — deprecated features
bq query --use_legacy_sql=true \
  'SELECT COUNT(*) FROM [bigquery-public-data:samples.shakespeare]'

# GoogleSQL (standard SQL) — the current dialect
bq query --use_legacy_sql=false \
  'SELECT COUNT(*) FROM `bigquery-public-data.samples.shakespeare`'
```

| Feature | Legacy SQL | GoogleSQL |
|---------|-----------|------------|
| Table reference | `[project:dataset.table]` | `` `project.dataset.table` `` |
| Joins | Not supported | Full support |
| Window functions | No | Yes |
| `WITH` CTEs | No | Yes |
| Arrays / structs | Limited | Full support |
| UDFs | No | JavaScript, Python |
| Default | `false` since 2023 | ✅ **Default** |

💡 **Never use legacy SQL in new code.** It was fully retired as of June 2023. If you inherit a
legacy SQL codebase, migrate it — the dialect differences are significant enough that a
mechanical translation will not work.

### 5. Set a project-wide default byte cap

```bash
# Create a .bqrc file in your home directory to set CLI defaults
cat > ~/.bqrc <<'EOF'
--max_bytes_billed=10000000000
EOF
```

---

## 💡 Production Notes

- **The cache is per-user.** A shared dashboard where 20 users each run the same query 20 times
  does *not* get 20× the savings from one cache entry — each user's first run is a miss.
- **DML is not cached.** A pipeline that runs `MERGE` then immediately `SELECT`s the result pays
  twice.
- **Set `maximum_bytes_billed` on scheduled queries too.** A scheduled job with a bad parameter
  value can run 400 times a day.
- **`INFORMATION_SCHEMA` queries are never cached** and scan the metadata store — they are cheap
  but not free.

---

## 🔑 Key Takeaways

- **`maximum_bytes_billed` is the circuit breaker** — the query *fails* rather than over-spending.
- The **query cache** makes repeated identical deterministic queries free for 24 hours, per user.
- Cache is invalidated by any table write, and never applies to DDL, DML, or
  non-deterministic functions.
- **Dry runs are free and exact** — use them before every non-trivial query.
- Legacy SQL is retired; use GoogleSQL.

---

## 📚 Practice Exercises

1. **Cache experiment.** Design an experiment that empirically determines the cache lifetime.
   Write the exact queries and the timing table you would record.

2. **Cost guardrail.** Write a Composer DAG task that runs a user-supplied query with a byte cap,
   catches the failure, and routes an alert. Write both the SQL and the Python.

3. **Legacy migration.** Convert these legacy SQL statements to GoogleSQL:
   - `SELECT COUNT(*) FROM [project:dataset.table]`
   - `SELECT a.*, b.* FROM [p:d.a] a JOIN [p:d.b] b ON a.id = b.id`
   - `SELECT * FROM [bigquery-public-data:samples.shakespeare] WHERE word = 'hamlet'`

4. **Cache invalidation design.** A dashboard needs "revenue last 30 days" refreshed hourly. The
   `WHERE order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)` filter defeats the cache.
   Design an alternative that keeps caching working while staying fresh.

---

## 📖 Further Reading

- Query parameters and settings — https://cloud.google.com/bigquery/docs/parameters
- Maximum bytes billed — https://cloud.google.com/bigquery/docs/queries#maximum_bytes_billed
- Cached query results — https://cloud.google.com/bigquery/docs/caching
