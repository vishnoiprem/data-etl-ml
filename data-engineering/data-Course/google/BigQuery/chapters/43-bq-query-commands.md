# 6.3 — `bq` Querying Commands

> **Section 6 · Command Line Interface · Lecture 6.3 · 8:02**

## 🎯 What you will learn

- The full `bq query` command with all the flags that matter
- Dry runs, job management, and output control
- Interactive vs scripted usage patterns
- Debugging failed queries

---

## 🧠 Concept

`bq query` runs a query and returns results. It is the workhorse of the CLI.

### The full syntax

```bash
bq query [flags] 'QUERY'
```

### The flags that matter

| Flag | Purpose |
|------|---------|
| `--use_legacy_sql=false` | Use GoogleSQL (the default now) |
| `--dry_run` | Validate + estimate bytes, no execution, no cost |
| `--max_bytes_billed` | **Cost cap — the query fails if exceeded** |
| `--destination_table` | Write results to a table |
| `--destination_format` | Output format for results (`CSV`, `NEWLINE_DELIMITED_JSON`, `AVRO`, `PARQUET`) |
| `--use_legacy_sql` | Legacy dialect (deprecated) |
| `--max_results` | Max rows to return |
| `--timeout_ms` | Client-side timeout |
| `--parameter` | Named query parameter |
| `--quiet` | Suppress the job summary |
| `--format` | Output format (`pretty`, `json`, `csv`, `none`) |
| `--job_id` | Use a specific job ID (for exactly-once semantics) |
| `--job_retry` | Retry on transient errors |

---

## 🧠 Dry runs — the most important flag

```bash
bq query --dry_run --use_legacy_sql=false \
  'SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders`'
```

Output:
```
Job ID: your-project.bquxjob_1234
Bytes processed: 10737418240
```

💡 **A dry run costs nothing, takes one second, and tells you the exact byte count.** Make it
your first action on every non-trivial query.

```bash
# The habit
bq query --dry_run --use_legacy_sql=false "$QUERY" | grep "Bytes processed"
```

### Dry run with a byte cap — catch problems before execution

```bash
# If the dry run exceeds the cap, it reports the failure without running
bq query --dry_run --max_bytes_billed=1000000000 --use_legacy_sql=false \
  'SELECT o.*, c.* FROM `YOUR_PROJECT_ID.curated.orders` o
   CROSS JOIN `YOUR_PROJECT_ID.curated.customers` c'
```

---

## 🧠 Output control

```bash
# Default: a formatted table
bq query --use_legacy_sql=false 'SELECT 1 AS n, "hello" AS greeting'

# JSON — for scripts
bq query --use_legacy_sql=false --format=json 'SELECT * FROM `p.d.t` LIMIT 10'

# CSV — for spreadsheets
bq query --use_legacy_sql=false --format=csv 'SELECT * FROM `p.d.t` LIMIT 10'

# Just one value
bq query --use_legacy_sql=false --format="value(total)" \
  'SELECT COUNT(*) AS total FROM `p.d.t`'

# No output (for DDL and DML)
bq query --use_legacy_sql=false --quiet \
  'DELETE FROM `p.d.t` WHERE order_date = DATE "2026-01-01"'
```

💡 **`--format="value(column_name)"` is the workhorse for shell scripting.** It returns the raw
value with no quotes, so it can be used directly in a command substitution.

---

## 🧠 Writing results to a table

```bash
# Write to a table
bq query --use_legacy_sql=false --quiet \
  --destination_table=YOUR_PROJECT_ID:curated.orders_summary \
  --destination_format=PARQUET \
  'SELECT order_date, customer_id, SUM(total_amount) AS revenue
   FROM `YOUR_PROJECT_ID.curated.orders`
   GROUP BY 1, 2'

# Append to a table
bq query --use_legacy_sql=false --quiet \
  --destination_table=YOUR_PROJECT_ID:curated.orders_summary \
  --destination_format=PARQUET \
  "INSERT INTO \`YOUR_PROJECT_ID:curated.orders_summary\` SELECT * FROM \`p.d.t\`"
```

💡 **Writing to a Parquet destination in Cloud Storage** is the cheapest way to materialize
results:

```bash
bq query --use_legacy_sql=false --quiet \
  --destination_table=gs://YOUR_PROJECT_ID-bq-course/exports/orders_*.parquet \
  --destination_format=PARQUET \
  'SELECT * FROM `YOUR_PROJECT_ID.curated.orders`'
```

---

## 🧠 Query parameters

```bash
bq query --use_legacy_sql=false \
  --parameter=start_date:2026-01-01 \
  --parameter=end_date:2026-02-01 \
  'SELECT COUNT(*)
   FROM `YOUR_PROJECT_ID.curated.orders`
   WHERE order_date BETWEEN @start_date AND @end_date'
```

💡 **Always use parameters instead of string interpolation.** It prevents SQL injection, and it
makes the query reusable. Parameters are typed, so `DATE` and `TIMESTAMP` parameters are
correctly compared against `DATE` columns — no implicit casting.

```bash
# ❌ Never do this
bq query --use_legacy_sql=false "SELECT * FROM t WHERE name = '$USER_INPUT'"
```

---

## 🧠 Job management

```bash
# Specify a job ID — enables exactly-once semantics
bq query --use_legacy_sql=false --job_id=nightly_orders_20260115 \
  'SELECT * FROM `p.d.t`'

# With a deterministic job ID, re-running is safe:
# BigQuery refuses to create a duplicate job with the same ID
bq query --use_legacy_sql=false --job_id=nightly_orders_20260115 \
  'SELECT * FROM `p.d.t`'
# → Error: Already Exists
```

💡 **Deterministic job IDs are a genuinely useful pattern.** It gives you exactly-once semantics
for free: a retried script will not double-insert.

```bash
# Retry on transient errors
bq query --use_legacy_sql=false --job_retry \
  'SELECT * FROM `p.d.t`'

# Client-side timeout
bq query --use_legacy_sql=false --timeout_ms=30000 'SELECT * FROM `p.d.t`'
```

### Finding and cancelling jobs

```bash
# List recent jobs
bq ls --project_id=YOUR_PROJECT_ID --jobs --max_results=20 \
    --format="table(jobId,state,creationTime,destinationTable)"

# Get a job's details
bq show --format=prettyjson --job_id=bquxjob_abc123

# Cancel a running job
bq cancel --job_id=bquxjob_abc123
```

---

## 🧠 Interactive vs scripted usage

### Interactive

```bash
# Open a REPL
bq shell
```

```sql
-- Inside the shell
SELECT 1 AS x;
.help
.quit
```

### Scripted

```bash
#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="YOUR_PROJECT_ID"
QUERY='SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders`'

# 1. Dry run — fail fast if too expensive
BYTES=$(bq query --dry_run --use_legacy_sql=false "$QUERY" 2>&1 | \
         grep -oP 'Bytes processed: \K[0-9]+')

if [ "$BYTES" -gt 10000000000 ]; then
    echo "ABORT: query would process ${BYTES} bytes" >&2
    exit 1
fi

# 2. Execute
bq query --use_legacy_sql=false --quiet --format="value(f0_)" "$QUERY"
```

💡 **Always dry run before a destructive or expensive statement in a script.** The pattern above
is a good template for CI.

---

## 🛠️ Hands-On: Debugging a Failed Query

### 1. Read the error carefully

```bash
bq query --use_legacy_sql=false 'SELECT * FROM `YOUR_PROJECT_ID.does_not_exist`'
```
```
Error in query string: Table name "does_not_exist" missing dataset while no default dataset is set in the request.
```

### 2. Check the job's error details

```bash
bq show --format=prettyjson --job_id=JOB_ID_HERE
```

```json
{
  "status": {
    "errorResult": {
      "reason": "invalid",
      "message": "Syntax error: Unexpected keyword at [1:8]"
    },
    "errors": [
      {
        "reason": "invalidQuery",
        "message": "Syntax error: Unexpected keyword at [1:8]"
      }
    ]
  }
}
```

💡 **The `reason` field categorises the failure:**

| Reason | Meaning | Fix |
|--------|---------|-----|
| `invalidQuery` | Syntax error | Check the SQL |
| `notFound` | Table/dataset missing | Check the name and region |
| `accessDenied` | IAM | Grant the role |
| `resourcesExceeded` | Quota or byte cap | Lower the scan or raise the cap |
| `stopped` | Cancelled | — |
| `backendError` | Transient | Retry |

### 3. Common errors and fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `Syntax error: Unexpected keyword` | Legacy SQL syntax in GoogleSQL | Use backticks, not `[project:ds.table]` |
| `Table name missing dataset` | No default dataset | Use fully qualified `` `project.dataset.table` `` |
| `Resources exceeded` | Byte cap or quota | Add a partition filter; check slot quota |
| `Access Denied` | IAM | `gcloud projects add-iam-policy-binding` |
| `Not found: Table` | Wrong region or deleted | Check the dataset location |
| `Query exceeded resource limits` | Too much data | Add filters; use a partitioned table |

### 4. The region gotcha

```bash
# If a table exists but "not found", check the dataset's region
bq show --format=prettyjson YOUR_PROJECT_ID:curated | jq -r '.location'

# Then query it in the right location
bq query --use_legacy_sql=false --location=EU \
  'SELECT COUNT(*) FROM `YOUR_PROJECT_ID.eu_curated.orders`'
```

⚠️ **`bq query` defaults to the `US` region.** Tables in `europe-west2` or `asia-south1` need an
explicit `--location` flag, or the query fails with "Not found" even though the table exists.

---

## 💡 Production Notes

- **Set `--max_bytes_billed` in `.bqrc`**, not just in individual commands.
- **Use `--destination_format=PARQUET` when writing results** — smaller and faster to re-read.
- **`--job_id` for idempotency** in pipelines and backfills.
- **Always specify `--location`** for non-US datasets.
- **Use `--format="value(...)"` in scripts** — never parse the `pretty` output.
- **`--quiet` keeps logs clean** when you are capturing output.

---

## 🔑 Key Takeaways

- `bq query` flags: `--dry_run`, `--max_bytes_billed`, `--destination_table`, `--format`,
  `--parameter`, `--job_id`.
- **Dry run first, always** — it is free and exact.
- **Parameters over string interpolation** — typed and injection-safe.
- **Deterministic `--job_id` gives exactly-once semantics** for retried scripts.
- `--location` matters for non-US datasets; `bq query` defaults to `US`.
- Read errors via `bq show --job_id=...` and categorize by `reason`.

---

## 📚 Practice Exercises

1. **CLI script suite.** Write four scripts: (a) a dry-run-and-execute wrapper with a byte cap,
   (b) an export to Parquet, (c) a table-inventory exporter, (d) a job-failure reporter.

2. **Error catalogue.** Deliberately trigger each of the six common errors and record the exact
   message and fix. Package it as a troubleshooting document.

3. **Idempotent pipeline.** Write a script that uses a deterministic `--job_id` to load a daily
   partition, and prove that re-running it does not duplicate data.

4. **Parameterize.** Convert a set of queries with hard-coded dates into parameterized versions,
   and show how typed parameters avoid implicit casts.

5. **Output formats.** Produce the same query result in all six output formats. Document which
   format is best for each downstream consumer (shell, jq, spreadsheet, log file, BI tool).

---

## 📖 Further Reading

- `bq query` reference — https://cloud.google.com/bigquery/docs/reference/bq-cli-reference#bq_query
- Query parameters — https://cloud.google.com/bigquery/docs/parameters
- Job IDs and exactly-once — https://cloud.google.com/bigquery/docs/managing-job-identifiers
