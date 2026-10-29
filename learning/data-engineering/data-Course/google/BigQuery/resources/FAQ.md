# BigQuery FAQ

> The questions students actually ask.

---

## Getting started

### Do I need a GCP project to follow the course?

Yes. BigQuery is a Google Cloud service. The free tier includes 1 TiB of query processing per month and 10 GB of storage, so you can complete every exercise at no cost. You do need billing enabled on the project, but you will not be charged inside the free tier.

### Which region should I use?

`US` if you have no reason to choose otherwise — it has the largest feature availability and the most public sample data. If your organisation has data-residency requirements, pick the matching region from the start: **a dataset's location is immutable**.

### How do I get free sample data?

```sql
SELECT * FROM `bigquery-public-data.utility_us.country_code_iso`
LIMIT 10;
```

Other useful public datasets: `bigquery-public-data.samples.github_nested`, `bigquery-public-data.world_bank.world_bank_indicators`, `bigquery-public-data.crypto_bitcoin.transactions`.

### Is there a free BigQuery sandbox?

No. BigQuery has no separate sandbox tier, but the free tier is generous enough for the whole course. If you want a hard guarantee of zero cost, add a billing budget alert at $1.

---

## Cost

### How do I know what a query will cost before running it?

```bash
bq query --use_legacy_sql=false --dry_run 'SELECT ...'
```

The dry run is free and reports the exact byte count. In Python, use `job_config=bigquery.QueryJobConfig(dry_run=True)` and read `job.total_bytes_processed`.

### Why did a tiny query cost $5?

Three usual reasons:

1. **No partition filter** — the query scanned the whole table.
2. **`SELECT *` in a subquery** — column pruning stopped at the subquery boundary.
3. **A join that exploded** — a many-to-many join multiplied the bytes.

Check the "Execution details" tab in the console for the actual bytes processed and the stages involved.

### Is the streaming buffer expensive?

Yes. Streaming-buffer data is billed at the **active** storage rate ($0.02/GiB/month) and is never query-cached. If you stream heavily and query it often, you will pay both the storage premium and the scan cost on every query.

### When should I switch to capacity (slot) pricing?

When your on-demand bill is **stable and above roughly 500–1,000 slot-hours per month**. Before that, capacity pricing wins only if your usage is genuinely predictable. Capacity is a commitment — you pay for reserved slots even when they are idle.

### Do free-tier amounts reset?

- Storage: 10 GB per month
- Query bytes: 1 TiB per month
- Streaming inserts: 1 GB per **day**, per **table**

The free tier is per **billing account**, not per project. If you have several projects in one account, they share the same allowance.

### Does compression reduce query cost?

**No.** BigQuery bills the *uncompressed logical* bytes scanned. Compression reduces storage and network transfer, not query dollars.

---

## Performance

### Why is my query slow when the table is small?

- **Slot queueing** — your project is waiting for capacity. Check `waitingForSlotsMs` in the execution details.
- **Cold cache** — the first read after a while must fetch from storage.
- **Overly complex SQL** — a bad join or a window function over a large range.
- **The streaming buffer** — recent data is always read fresh, never cached.

### What is the 10,000-partition limit and how do I avoid it?

A table can have at most 10,000 partitions. Daily partitioning gives you ~27 years. Hourly partitioning gives you ~1.1 years — and then you hit the limit. If you need hourly granularity at scale, use **daily partitions plus a clustered hour column**.

### Does `SELECT *` really cost more?

Yes. BigQuery stores data column-by-column, so it only reads the columns you reference — but only if your projection is explicit. A `SELECT *` in a view or subquery forces every column to be read.

### Is a materialized view always faster?

For the query it was built for, yes. For anything else, no — an MV has one base table and one specific shape. If the query does not match the MV's predicate and columns, BigQuery will not use it.

### Should I partition or cluster?

Usually **both**:

- **Partition** by date when you filter by time and want automatic expiration.
- **Cluster** by the 2–4 columns you filter on most often.

Clustering order matters more than cardinality. Put your most frequently filtered column first.

---

## Schema and DDL

### Can I change a column's type?

Not directly. `ALTER TABLE ... ALTER COLUMN ... SET DATA TYPE` is not supported. The workarounds:

1. `ALTER TABLE ... ALTER COLUMN ... DROP NOT NULL` to relax a mode.
2. Create a new table with `CAST` and swap.
3. Use `schema_update_options = ALLOW_FIELD_RELAXATION` on load (e.g. `INT64` → `FLOAT64`).

### How do I add a column without a table rewrite?

`ALTER TABLE ... ADD COLUMN` is metadata-only and fast. It is only expensive for `SET OPTIONS` operations that rewrite data. For a large table, prefer CTAS with the new column.

### What is the difference between `REQUIRED` and `NULLABLE`?

`REQUIRED` means every row must have a value; loading a null fails the job. `NULLABLE` (the default) permits nulls. `REPEATED` means the column holds an array.

### Does `autodetect` hurt query cost?

No, but it hurts correctness. Auto-detection reads the first 100 rows and fixes the schema — one malformed row can permanently change a column's type. In production, always use `--schema_file`.

### What is flexible column names?

BigQuery can interpret JSON-like data with flexible column names, where the source keys become columns. Useful for ingesting semi-structured data without a strict schema.

---

## Partitioning and clustering

### Why isn't my partition filter pruning?

Common causes:

1. The filter is on a **function** of the partition column (`DATE(order_date) = ...`). Use the column directly.
2. The filter is inside an `OR`.
3. The filter is on a different column.
4. The query is reading the whole table via `SELECT *` from a view that has no filter.

### Can I change a table's partitioning after creation?

**No.** Partitioning is fixed at creation. To change it, create a new table and copy the data. (You *can* change the expiration, and you can add or drop individual partitions.)

### Can I change clustering after creation?

**Yes.** `ALTER TABLE ... SET OPTIONS (clustering_fields = [...])`. Re-clustering happens in the background over roughly the last 10 GB, so it is not instant.

### Does clustering cost more storage?

Yes, 5–20%. BigQuery stores additional sort keys for each block.

---

## Views and materialized views

### When should I use a view vs a materialized view?

| | View | Materialized view |
|---|---|---|
| Cost | No storage | Storage + refresh cost |
| Freshness | Always current | Up to `max_staleness` |
| Query cost | Same as the base table | Much cheaper |
| Use for | Joins, RLS, reusable logic | Dashboards, repeated aggregations |

### Why does my materialized view creation fail with "cannot be based on multiple tables"?

An MV supports exactly **one** base table. If you need a join, use the **MV + view pattern**: create a view that does the join, then materialize the view.

### What is `max_staleness`?

The maximum time an MV's data can lag behind its base table. Set it to `INTERVAL 1 HOUR` for a dashboard that can be slightly behind. Set `enable_refresh = TRUE` for automatic background refreshes.

### Does a materialized view cost anything to query?

The query is cheap (you read pre-aggregated rows), but the MV itself incurs storage cost and each refresh is billed.

---

## Python client

### Why does my load job "finish" but no data arrives?

`load_table_from_file` is **asynchronous**. You must call `job.result()` to block until the load completes. Without it, the script can exit and the load is cancelled.

### Why is `insert_rows_json` slow?

It is one HTTP request per batch of rows, capped at 1,000 rows and 10 MB. For bulk data, use a load job or the Dataflow BigQuery sink.

### How do I pass a list of values into a query?

```python
bigquery.ArrayQueryParameter("statuses", "STRING", ["active", "complete"])
```

### How do I avoid creating duplicate clients?

The client manages an internal connection pool. Reuse one instance per process:

```python
_client = None

def get_client():
    global _client
    if _client is None:
        _client = bigquery.Client()
    return _client
```

### What is the difference between `update_fields` and `update_full`?

`update_fields` applies only the fields you set. `update_full` replaces the entire object — anything you omit is reset to its default. Use `update_fields` unless you intend a full replacement.

---

## Streaming

### Is Pub/Sub exactly-once?

Pub/Sub supports exactly-once delivery, which deduplicates redeliveries of the same message. It does **not** make your BigQuery write idempotent — deduplicate on your event ID anyway.

### Should I use Pub/Sub push-to-BigQuery or a Dataflow pipeline?

| | Push to BigQuery | Dataflow |
|---|---|---|
| Code | None | Beam pipeline |
| Joins / state | ❌ | ✅ |
| Transformation | ❌ | ✅ |
| Cost | Lower | Higher |
| Setup | Minutes | Hours |

Start with push-to-BigQuery. Move to Dataflow when you need state, windowing, or joins.

### Why do my streamed rows appear twice?

Pub/Sub is at-least-once. Deduplicate on the event ID:

```sql
SELECT * EXCEPT(rn) FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY ingested_at DESC) AS rn
  FROM `raw.events`
) WHERE rn = 1;
```

### How do I query data that is still in the streaming buffer?

Normally — just query the table. The buffer is queryable; it is only *cached* data that is skipped. The tradeoff is that queries touching the buffer are never cached and are billed for the bytes read.

---

## Airflow and Composer

### Why does my backfill produce the wrong data?

The task is reading `CURRENT_DATE()` instead of a parameterised date. **Every task in a backfillable DAG must take the target date as a parameter.**

### Why is my sensor holding a worker slot?

In `poke` mode. Use `mode="reschedule"` so the slot is released while waiting.

### Can I pass a large DataFrame between Airflow tasks?

**No.** XComs are stored in the metadata database and are meant for small values — counts, dates, flags. Pass large data through Cloud Storage or BigQuery.

### `execution_date` vs `data_interval_start`?

In Airflow 2, `data_interval_start` and `data_interval_end` are the modern names. `execution_date` is deprecated. A `@daily` DAG starting at 01:30 has a `data_interval_start` of the previous day's 01:30.

---

## Troubleshooting

### "Not found: Table" but the table exists

Two likely causes:

1. **Wrong region.** `bq query` defaults to `US`. Pass `--location` for other regions.
2. **No default dataset.** Use a fully qualified name: `` `project.dataset.table` ``.

### "Resources exceeded" during a query

Either the byte cap or a slot quota. Add a partition filter first; only then raise the cap.

### "Exceeded maximum bytes billed"

Working as intended. The query would have processed more than `maximum_bytes_billed`. Add a partition filter or raise the cap deliberately.

### "AttributeError: module 'google.cloud' has no attribute 'bigquery'"

```bash
pip install google-cloud-bigquery
```

Then restart the Jupyter kernel.

### "DefaultCredentialsError"

```bash
gcloud auth application-default login
```

### How do I find a query's job ID?

`job.query_id` in Python. In the CLI, the job ID is printed in the job summary. Search the console's job history, or query `INFORMATION_SCHEMA.JOBS_BY_PROJECT`.

---

## Best practices

### What is the single most important cost habit?

**Set `maximum_bytes_billed` on every job** and **dry run before every non-trivial query**. A query that fails is free; a query that runs without a cap is not.

### What is the single most important schema habit?

**Store schemas in version control as JSON files** and load them with `--schema_file` / `SchemaField`. One source of truth, reused by the CLI, the Python client, and your tests.

### What is the single most important design habit?

**Make everything idempotent.** Use `exists_ok=True`, deterministic job IDs, partition-scoped writes, and `MERGE` instead of `INSERT`. Then a retry is free.

### What is the single most important pipeline habit?

**Never use `CURRENT_DATE()` in a scheduled transform.** Take the date as a parameter so backfills work.

---

## Further reading

- BigQuery documentation — https://cloud.google.com/bigquery/docs
- Best practices — https://cloud.google.com/bigquery/docs/best-practices
- Pricing — https://cloud.google.com/bigquery/pricing
- Quotas — https://cloud.google.com/bigquery/quotas
- Python client reference — https://cloud.google.com/python/docs/reference/bigquery/latest/index
