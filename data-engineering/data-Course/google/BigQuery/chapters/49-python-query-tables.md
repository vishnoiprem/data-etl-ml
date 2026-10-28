# 7.4 — Python: Query Tables

> **Section 7 · Python Client Library · Lecture 7.4 · 5:42**

## 🎯 What you will learn

- `client.query()` and the job lifecycle
- Returning results as DataFrames, lists, and generators
- Parameters, job configs, and the query cache
- Introspecting a job: bytes processed, cost, timings, and errors
- Streaming inserts and the DML round trip

---

## 🧠 Concept

`client.query()` is asynchronous. It returns a `QueryJob` immediately; the work happens in
BigQuery's backend. You get results when you call `.result()`.

```
client.query(sql)        → QueryJob   (submitted)
job.result()             → RowIterator (results, blocks until done)
```

---

## 🛠️ Hands-On

### 1. The simplest query

```python
from google.cloud import bigquery

client = bigquery.Client(project="YOUR_PROJECT_ID")

sql = """
    SELECT order_date, COUNT(*) AS order_count, SUM(total_amount) AS revenue
    FROM `YOUR_PROJECT_ID.curated.orders`
    GROUP BY order_date
    ORDER BY order_date
"""

rows = client.query(sql).result()

for row in rows:
    print(row.order_date, row.order_count, row.revenue)
```

### 2. Return results as a DataFrame

```python
df = client.query(sql).to_dataframe(
    max_results=10_000,          # API limit per call
    progress_bar_type=None,      # quiet in notebooks/CI
    create_bqstorage_client=False,
)
print(df.head())
print(df.dtypes)
```

| Parameter | Effect |
|-----------|--------|
| `max_results` | Max rows per API page (default 10,000) |
| `progress_bar_type` | `None`, `tqdm`, `tqdm_notebook` |
| `create_bqstorage_client` | Use the Storage Read API — faster, needs extra IAM |
| `dtypes` | Force a dtype mapping |
| `geography_as_object` | Keep GEOGRAPHY as a WKT string instead of GeoSeries |

💡 **`to_dataframe()` materializes everything in memory.** For results over a few million rows,
paginate with `.result()` and write each page out instead.

### 3. Paginate without loading it all

```python
def iter_rows(sql: str, page_size: int = 50_000):
    job = client.query(sql)
    rows = job.result()
    while True:
        page = rows.fetchmany(page_size)
        if not page:
            break
        yield from page

for row in iter_rows(sql):
    process(row)
```

### 4. Parameters — always, no exceptions

```python
job_config = bigquery.QueryJobConfig(
    query_parameters=[
        bigquery.ScalarQueryParameter("start_date", "DATE", "2026-01-01"),
        bigquery.ScalarQueryParameter("end_date", "DATE", "2026-01-31"),
        bigquery.ScalarQueryParameter("min_amount", "NUMERIC", 100),
        bigquery.ArrayQueryParameter("statuses", "STRING", ["active", "complete"]),
    ],
)

rows = client.query(sql, job_config=job_config).result()
```

💡 **Always use `ScalarQueryParameter` with an explicit type.** Guessing the type from the Python
value produces surprises — a `datetime.date` becomes `DATE`, but a `str` stays `STRING` even
when you meant `DATE`.

### 5. Dry run — check the cost first

```python
job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
job = client.query(sql, job_config=job_config)

bytes_processed = job.total_bytes_processed or 0
print(f"{bytes_processed / 1024**4:.4f} TiB → ${bytes_processed / 1024**4 * 6.25:.4f}")
```

### 6. Enforce a byte cap on every query

```python
job_config = bigquery.QueryJobConfig(maximum_bytes_billed=1_000_000_000)  # 1 GB

try:
    rows = client.query(sql, job_config=job_config).result()
except Exception as exc:
    if "Exceeded maximum bytes" in str(exc):
        print("Query too expensive — add a partition filter")
    raise
```

### 7. Introspect the job

```python
job = client.query(sql)
rows = job.result()

print(job.job_id)
print(job.created, job.started, job.ended)
print(job.total_bytes_processed)
print(job.total_bytes_billed)
print(job.cache_hit)               # True if served from cache
print(job.num_dml_affected_rows)
print(job.location)
print(job.query_id)                # use this for the audit log
```

```python
# Detailed timings
print("Queue time:", job.query_plan[0].get("waitingForSlotsMs", "n/a"))
for step in job.query_plan:
    print(step.get("name"), step.get("status"), step.get("parallelInputs"))
```

### 8. Stream rows without loading the whole result

```python
import pandas as pd

frames = []
for page in client.query(sql).result().pages:
    frames.append(page.to_dataframe())

df = pd.concat(frames, ignore_index=True)
```

### 9. DML — the same API, different verbs

```python
# INSERT
job = client.query(
    """
    INSERT INTO `YOUR_PROJECT_ID.curated.orders` (order_id, customer_id, order_date, total_amount, status)
    VALUES ('o999', 'c001', DATE '2026-01-15', 99.99, 'active')
    """
)
job.result()
print(job.num_dml_affected_rows)   # 1

# UPDATE
client.query(
    """
    UPDATE `YOUR_PROJECT_ID.curated.orders`
    SET status = 'cancelled'
    WHERE order_id = 'o999'
    """
).result()

# DELETE
client.query(
    """
    DELETE FROM `YOUR_PROJECT_ID.curated.orders`
    WHERE order_date = DATE '2026-01-15'
    """
).result()

# MERGE
client.query(
    """
    MERGE `YOUR_PROJECT_ID.curated.customers` AS t
    USING `YOUR_PROJECT_ID.raw.customers` AS s
    ON t.customer_id = s.customer_id
    WHEN MATCHED THEN UPDATE SET t.name = s.name, t.updated_at = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN INSERT (customer_id, name) VALUES (s.customer_id, s.name)
    """
).result()
```

💡 **DML in BigQuery is a full table or partition rewrite** under the hood. `UPDATE` on a
million-row table is expensive and slow. Prefer `MERGE` into a new partition, or recompute
the affected partition and replace it.

### 10. Streaming inserts

```python
table = client.dataset("raw").table("events")

rows = [
    {"event_id": f"e{i:06d}", "user_id": "u001", "event_type": "click",
     "event_ts": "2026-01-01T10:00:00Z"}
    for i in range(1000)
]

errors = client.insert_rows_json(table, rows)
if errors:
    for err in errors:
        print("Failed row:", err["index"], err["errors"])
else:
    print(f"Streamed {len(rows)} rows")
```

💡 **Streaming inserts are synchronous and free up to 1 GB/day per table.** After that they cost
$0.01 per 200 MB. They are not cached and are billed at active storage rates.

### 11. Write query results to a table

```python
job_config = bigquery.QueryJobConfig(
    destination="YOUR_PROJECT_ID.mart.daily_revenue",
    write_disposition="WRITE_TRUNCATE",
)

job = client.query(sql, job_config=job_config)
job.result()
```

### 12. Export results to Parquet in GCS

```python
job_config = bigquery.ExtractJobConfig(
    destination="gs://YOUR_PROJECT_ID-bq-course/exports/orders_*.parquet",
    destination_format="PARQUET",
    use_avro_logical_types=True,
)

job = client.query(sql, job_config=job_config)
job.result()
```

---

## 🛠️ Building a reusable query helper

```python
"""
bq_query.py — a thin, safe wrapper over client.query().
"""
from __future__ import annotations

import logging
from typing import Any

from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError

log = logging.getLogger(__name__)

_client: bigquery.Client | None = None


def get_client() -> bigquery.Client:
    global _client
    if _client is None:
        _client = bigquery.Client()
    return _client


def run(
    sql: str,
    params: dict[str, Any] | None = None,
    max_bytes_billed: int = 10 * 1024**4,
    dry_run: bool = False,
) -> list[bigquery.Row]:
    """Run a query and return a list of rows. Raises on error."""
    client = get_client()

    job_config = bigquery.QueryJobConfig(
        maximum_bytes_billed=max_bytes_billed,
        use_query_cache=not dry_run,
        use_legacy_sql=False,
        dry_run=dry_run,
    )
    if params:
        job_config.query_parameters = [
            bigquery.ScalarQueryParameter(name, _sql_type(value), value)
            for name, value in params.items()
        ]

    try:
        job = client.query(sql, job_config=job_config)
        if dry_run:
            log.info("Dry run: %s bytes", job.total_bytes_processed)
            return []
        return list(job.result())
    except GoogleCloudError as exc:
        log.error("Query failed (%s): %s", exc.code, exc)
        raise


def _sql_type(value: Any) -> str:
    """Map a Python value to an explicit BigQuery SQL type."""
    import datetime
    if isinstance(value, bool):
        return "BOOL"
    if isinstance(value, int):
        return "INT64"
    if isinstance(value, float):
        return "FLOAT64"
    if isinstance(value, datetime.datetime):
        return "TIMESTAMP"
    if isinstance(value, datetime.date):
        return "DATE"
    return "STRING"
```

---

## 🛠️ Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `job.result()` hangs | Query is queued waiting for slots | Wait, or check `job.query_plan` for `waitingForSlotsMs` |
| `AttributeError: 'RowIterator' object has no attribute ...` | Used the job where you meant the rows | Call `.result()` first |
| `ValueError: Could not determine type of 'x'` | Parameter type mismatch | Give the parameter an explicit type |
| `Exceeded maximum bytes billed` | Byte cap hit | Add a partition filter, or raise the cap deliberately |
| `Not found: Table` | Wrong project or region | Use a fully qualified name and check the dataset location |
| `google.api_core.exceptions.BadRequest: Name already exists` | `CREATE TABLE` without `IF NOT EXISTS` | Use `exists_ok=True` or `IF NOT EXISTS` |
| `insert_rows_json` returns errors | Row does not match the table schema | Print `err["errors"]` and fix the row shape |
| `403 Permission denied` | Missing `roles/bigquery.jobUser` | Grant the role |
| `404 Not found: Dataset` | Client project differs from the table's project | Pass `project=` explicitly |

---

## 💡 Production Notes

- **Dry run before every non-trivial query.** It is free and exact.
- **Set `maximum_bytes_billed` on every job.** A runaway query should fail fast, not run for $500.
- **Wrap queries in a helper.** Never scatter `client.query()` calls across a codebase.
- **Use `to_dataframe()` for exploration and pagination for pipelines.**
- **Do not use `insert_rows_json` for bulk.** Use load jobs.
- **Always log `job.query_id`** — it is the key to finding the job in the console's job history.
- **`job.result()` blocks.** Use `client.query()` + `.result()` in a thread pool if you need
  concurrency.

---

## 🔑 Key Takeaways

- `client.query()` returns a `QueryJob`; `.result()` blocks and returns the rows.
- `.to_dataframe()` for convenience, `.pages` / `.fetchmany()` for large results.
- **Parameters always, with explicit types** — `ScalarQueryParameter`, `ArrayQueryParameter`.
- `dry_run=True` + `total_bytes_processed` is the pre-flight cost check.
- `maximum_bytes_billed` turns a cost accident into a failed job.
- `job.query_id` and `job.cache_hit` are your two best debugging fields.
- DML rewrites whole tables/partitions — prefer `MERGE` or partition replace for bulk changes.

---

## 📚 Practice Exercises

1. **Query toolkit.** Write a module with `run(sql)`, `run_df(sql)`, `run_to_dataframe(sql, path)`,
   `count(sql)`, and `dry_run_cost(sql)`. Every function takes optional parameters and a byte cap.

2. **Parameterized report.** Build a daily revenue report that takes `start_date` and `end_date`
   as typed parameters and returns a DataFrame. Prove the same SQL works for any range.

3. **Job telemetry.** Write a wrapper that logs `query_id`, bytes processed, bytes billed,
   cache hit, and duration for every query into a BigQuery audit table. Add a daily summary view.

4. **Streaming vs loading benchmark.** Stream 100k rows and load the same 100k rows as Parquet.
   Compare latency, cost, and the query experience (cache hits, latency on the streaming buffer).

5. **Retry with backoff.** Wrap `run()` so that it retries only on transient reasons
   (`backendError`, `rateLimitExceeded`) with exponential backoff and jitter. Log every retry.

---

## 📖 Further Reading

- `Client.query` — https://cloud.google.com/python/docs/reference/bigquery/latest/bigquery.client.Client.query
- `QueryJob` — https://cloud.google.com/python/docs/reference/bigquery/latest/bigquery.job.query.QueryJob
- Query parameters — https://cloud.google.com/bigquery/docs/parameters
