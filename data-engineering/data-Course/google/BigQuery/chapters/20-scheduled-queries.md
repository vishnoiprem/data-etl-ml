# 3.3 — Schedule, Save & Share Queries

> **Section 3 · Running Queries with Various Query Settings · Lecture 3.5 · 9:16**

## 🎯 What you will learn

- Scheduled queries: syntax, parameters, destination tables, and cost control
- Saved queries: what they are and when they beat a scheduled query
- Sharing queries and datasets with other users
- The difference between a scheduled query and a Composer DAG

---

## 🧠 Concept

Three related features, three different jobs:

| Feature | What it is | Runs | Stores results |
|---------|-----------|------|----------------|
| **Saved query** | Named SQL text | Never | No |
| **Scheduled query** | Named SQL that runs on a schedule | Yes | Optionally, to a table |
| **Composer DAG** | Orchestrated multi-task workflow | Yes | Via the tasks |

### Saved queries

A saved query is just named SQL. It is a convenience for reuse and sharing.

```sql
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.analytics.saved_queries` (
    id            STRING,
    name          STRING,
    description   STRING,
    query         STRING,
    created_by    STRING,
    created_at    TIMESTAMP,
    labels        ARRAY<STRUCT<key STRING, value STRING>>
);
```

```sql
-- Save a query from the UI: query editor → Save → name it
-- Or from the CLI:
bq query --use_legacy_sql=false \
  --destination_table YOUR_PROJECT_ID:analytics.query_results \
  'SELECT * FROM `YOUR_PROJECT_ID.curated.orders` LIMIT 100'
```

💡 **Saved queries live in the UI, not in the catalog** (unless you use the
`INFORMATION_SCHEMA.JOBS` approach below). To track them programmatically, log them yourself into
a registry table.

```sql
-- Build your own saved-query registry from job history
SELECT
    job_id,
    user_email,
    creation_time,
    query,
    destination_table
FROM `region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE job_type = 'QUERY'
  AND creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  AND destination_table IS NOT NULL
ORDER BY creation_time DESC;
```

---

## 🧠 Scheduled Queries

A scheduled query runs on a schedule, optionally writing results to a destination table.

### The two forms

**Form 1 — scheduled queries UI (legacy form)**
Created in the console under *Scheduled queries*. Basic, limited, and increasingly rare.

**Form 2 — `CREATE SCHEDULED QUERY` DDL (current form)**

```sql
CREATE SCHEDULED QUERY `YOUR_PROJECT_ID.analytics.refresh_daily_summary`
OPTIONS (
  schedule = "0 2 * * *",              -- 02:00 daily (UTC)
  time_zone = "America/New_York",     -- interpret the schedule in this TZ
  description = "Refresh the daily order summary",
  destination_table = "YOUR_PROJECT_ID.curated.daily_order_summary",
  write_disposition = "WRITE_TRUNCATE",
  create_disposition = "CREATE_IF_NEEDED",
  parallelism = 1,
  labels = [('env', 'prod'), ('owner', 'data-eng')]
)
AS
SELECT
    order_date,
    customer_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue
FROM `YOUR_PROJECT_ID.raw.orders`
WHERE order_date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
GROUP BY order_date, customer_id;
```

### Schedule syntax

The schedule uses **cron syntax**, in UTC unless `time_zone` is specified.

```
 ┌───── minute (0-59)
 │ ┌───── hour (0-23)
 │ │ ┌───── day of month (1-31)
 │ │ │ ┌───── month (1-12)
 │ │ │ │ ┌───── day of week (0-6, 0=Sunday)
 │ │ │ │ │
 * * * * *
```

| Schedule | Meaning |
|----------|---------|
| `0 2 * * *` | Every day at 02:00 |
| `30 3 * * 0` | Every Sunday at 03:30 |
| `0 */6 * * *` | Every 6 hours |
| `0 0 1 * *` | 1st of each month at midnight |
| `0 9-17 * * 1-5` | Every hour, 09:00–17:00, weekdays only |

⚠️ **Scheduled queries run at least every 24 hours, and Google may run them within a 4-hour
window around the scheduled time.** For precise timing, use Cloud Scheduler + a service account
that triggers the query, or Composer.

### Key options

| Option | Purpose |
|--------|---------|
| `schedule` | Cron expression |
| `time_zone` | IANA timezone for the schedule |
| `destination_table` | Where to write results (omit for a no-op query) |
| `write_disposition` | `WRITE_TRUNCATE` (replace), `WRITE_APPEND` (add), `WRITE_EMPTY` |
| `create_disposition` | `CREATE_IF_NEEDED`, `CREATE_NEVER` |
| `maximum_bytes_billed` | **Cost cap — set it** |
| `transactional_updates` | Only write if the query succeeds completely |
| `parallelism` | Concurrent query slots to use |
| `labels` | Governance tags |

### 💡 `WRITE_TRUNCATE` vs `WRITE_APPEND` — get this right

```sql
-- ✅ Correct for a full-refresh daily snapshot
write_disposition = "WRITE_TRUNCATE"

-- ✅ Correct for incremental accumulation
write_disposition = "WRITE_APPEND"
```

⚠️ **`WRITE_TRUNCATE` deletes and recreates the table.** Any grants, labels, partitioning, and
clustering on the destination table are **lost**. If the destination table is partitioned and
clustered, the scheduled query's replacement table will not have them.

💡 **The safe pattern: create the destination as a view over the scheduled query's output, or
use a `MERGE` into a stable table instead of `WRITE_TRUNCATE`.**

```sql
-- ✅ Better: MERGE into a table whose schema/grants/partitioning you control
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.customer_ltv` (
    customer_id STRING NOT NULL,
    ltv         NUMERIC(12,2),
    updated_at  TIMESTAMP
)
PARTITION BY DATE(updated_at)
CLUSTER BY customer_id;

-- Then the scheduled query does:
MERGE `YOUR_PROJECT_ID.curated.customer_ltv` t
USING (
    SELECT customer_id, SUM(total_amount) AS ltv
    FROM `YOUR_PROJECT_ID.raw.orders`
    GROUP BY customer_id
) s
ON t.customer_id = s.customer_id
WHEN MATCHED THEN UPDATE SET ltv = s.ltv, updated_at = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN INSERT (customer_id, ltv, updated_at)
VALUES (s.customer_id, s.ltv, CURRENT_TIMESTAMP());
```

### Parameterized scheduled queries

```sql
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.analytics.parameters` (
    name        STRING,
    type        STRING,
    value       STRING,
    description STRING
);

-- Named parameter definitions
CREATE OR REPLACE PROCEDURE `YOUR_PROJECT_ID.analytics.run_daily_report`(
    report_date DATE,
    max_bytes   INT64
)
BEGIN
    DECLARE query_text STRING;
    SET query_text = FORMAT(
        "SELECT * FROM `YOUR_PROJECT_ID.curated.orders` WHERE order_date = @report_date"
    );
    EXECUTE IMMEDIATE query_text USING report_date;
END;
```

💡 **Scheduled queries do not directly support parameters** in the DDL form. For parameterized
scheduling, the standard approach is a **Composer DAG** with `{{ ds }}` (Airflow's date macro) or a
Cloud Scheduler job that calls the API with a substituted date.

### Managing scheduled queries

```bash
# List
bq ls --schedule --project_id=YOUR_PROJECT_ID --max_results=100

# Update — you must drop and recreate; there is no ALTER
bq query --use_legacy_sql=false --dry_run \
  'SELECT * FROM `YOUR_PROJECT_ID.curated.daily_order_summary`'
```

```sql
-- Pause
ALTER SCHEDULED QUERY `YOUR_PROJECT_ID.analytics.refresh_daily_summary`
SET OPTIONS (state = "PAUSED");

-- Resume
ALTER SCHEDULED QUERY `YOUR_PROJECT_ID.analytics.refresh_daily_summary`
SET OPTIONS (state = "ACTIVE");

-- Drop
DROP SCHEDULED QUERY `YOUR_PROJECT_ID.analytics.refresh_daily_summary`;
```

```python
# Update the schedule via the Python client
from google.cloud import bigquery

client = bigquery.Client()
sq = client.get_scheduled_query("analytics.refresh_daily_summary")
sq.schedule = "0 4 * * *"
sq.maximum_bytes_billed = 5_000_000_000
sq.update()
print(f"Updated: {sq.schedule}")
```

---

## 🧠 Sharing

### Sharing a query

In the console: **Share → Get link**. The link gives the recipient read access to the query text.
They can run it only if they have `roles/bigquery.jobUser` on the project.

### Sharing a dataset

```bash
# Share a dataset with a group, read-only
bq add-iam-policy-binding \
  --member="group:analysts@yourcompany.com" \
  --role="roles/bigquery.dataViewer" \
  YOUR_PROJECT_ID:analytics
```

### Authorized views — the safest way to share

An **authorized view** grants access to a view *without* granting access to the underlying table.
This is the correct way to share sensitive data.

```sql
-- Create an authorized view
CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.curated.v_customer_ltv`
OPTIONS (
  description = "Customer LTV, authorized for the analytics team",
  labels = [('access', 'authorized')]
) AS
SELECT
    customer_id,
    SUM(total_amount) AS ltv,
    COUNT(*) AS order_count
FROM `YOUR_PROJECT_ID.curated.orders`
GROUP BY customer_id;
```

```bash
# Bind an authorized user or group
bq add-iam-policy-binding \
  --member="group:analytics@yourcompany.com" \
  --role="roles/bigquery.dataViewer" \
  YOUR_PROJECT_ID:curated.v_customer_ltv
```

💡 **The critical distinction:**
- **View with a `dataViewer` grant on the view** → the recipient can read the view, but if they
  *also* have base-table access, they bypass the filter.
- **Authorized view** → access is bound to the view object. Even with base-table access, the view
  filters cannot be bypassed. **Always use authorized views for row-level security.**

---

## 💡 Production Notes

- **Scheduled query timing is not precise.** Google may run it anywhere within a 4-hour window. For
  SLAs, use Cloud Scheduler → a service account → the BigQuery API.
- **Every scheduled query should have `maximum_bytes_billed`.** A schedule that runs 400×/day with
  an unfiltered scan is a common cause of surprise bills.
- **A failed scheduled query fails silently unless you alert on it.** Monitor
  `INFORMATION_SCHEMA.JOBS` for `state = 'ERROR'` on scheduled queries.
- **Composer is the right tool** once you need dependencies, backfills, or parameterized runs.

---

## 🔑 Key Takeaways

- Saved query = named SQL, never runs. Scheduled query = named SQL that runs on a cron schedule.
- `CREATE SCHEDULED QUERY` is the current DDL form; the console form is legacy.
- **`WRITE_TRUNCATE` loses grants, labels, partitioning, and clustering** on the destination.
  Prefer `MERGE` into a stable table.
- Always set `maximum_bytes_billed` on a scheduled query.
- **Authorized views are the correct mechanism for row-level security** — plain views can be
  bypassed by users with base-table access.
- Scheduled query timing has a 4-hour window; use Cloud Scheduler or Composer for precision.

---

## 📚 Practice Exercises

1. **Scheduled query design.** Design a scheduled query that refreshes a 5 TB fact table daily at
   03:00. Cover: schedule syntax, timezone, write disposition, byte cap, and what happens on
   failure.

2. **WRITE_TRUNCATE trap.** A scheduled query writes to a partitioned, clustered table with grants
   to 30 analysts. Describe exactly what breaks after the first run, and design the fix.

3. **Authorized view.** Create a setup where a user has `dataViewer` on the base table and on an
   authorized view. Prove that the view's filter cannot be bypassed. Write the test queries.

4. **Scheduling decision.** Compare scheduled queries vs Composer vs Cloud Scheduler for these:
   (a) A nightly full refresh, (b) A pipeline with 5 dependent steps and backfill support,
   (c) A 15-minute incremental load.

5. **Monitoring.** Write a query that finds failed scheduled queries in the last 24 hours, with
   the error message, so you can build an alert on it.

---

## 📖 Further Reading

- Scheduled queries — https://cloud.google.com/bigquery/docs/scheduled-queries
- Authorized views — https://cloud.google.com/bigquery/docs/authorized-views
- Sharing datasets — https://cloud.google.com/bigquery/docs/dataset-sharing
