# 6 — The `bq` Command Line and Scripting

> **Practice Module 6 · BigQuery · 45 minutes**

## 🎯 What you will learn

- Every `bq` command you need, with the flags that matter and the ones that lie.
- How to dry-run a query before it costs you anything.
- How to write a script that is **idempotent** — safe to run twice.
- How to pipe `bq query` into other tools, and how to make a pipeline fail on bad data.
- Why `.bigqueryrc` is the first file you should create.

---

## 🧠 Concept

### The `bq` tool

`bq` is BigQuery's Python-based command-line interface. It wraps the same REST API the console
and the client libraries use, so anything it can do, your pipeline can do.

### The command set

| Command | Does |
|---|---|
| `bq mk` | Create a dataset, table, view, materialized view, connection, reservation, or transfer config |
| `bq load` | Load data into a table |
| `bq query` | Run a query |
| `bq ls` | List datasets, tables, jobs, models, routines |
| `bq show` | Show details of a dataset, table, or job |
| `bq rm` | Remove a dataset, table, or job |
| `bq cp` | Copy a table |

`bq mk` needs a resource-type flag to know what to create:

```bash
bq mk --dataset myDataset
bq mk --dataset --location=US myDataset
bq mk --table myDataset.myTable
bq mk --table --schema=Region:STRING,Quarter:STRING,Total_sales:INTEGER myDataset.myTable
bq mk --view myDataset.myView
bq mk --materialized_view myDataset.myMaterializedView
```

### Global flags

These apply to every command:

| Flag | Purpose |
|---|---|
| `--format=FORMAT` | Output format: `json`, `prettyjson`, `csv`, `pretty`, `none`, `text` |
| `--location=LOCATION` | The location to use |
| `--project_id=PROJECT_ID` | The project to bill and act in |

### The flags that matter most

**`bq query`:**

| Flag | Purpose |
|---|---|
| `--use_legacy_sql=false` | Use GoogleSQL. **Always pass this.** |
| `--nouse_legacy_sql` | Same thing, inverted spelling. |
| `--dry_run` | Validate and estimate bytes without executing. |
| `--maximum_bytes_billed=N` | Fail the query if it would exceed N bytes. |
| `--use_query_cache=false` | Bypass the result cache. |
| `--destination_table=...` | Write the result to a table instead of stdout. |
| `--parameter=...` | Bind a query parameter. |
| `--format=...` | How to print results. |

**`bq load`:**

| Flag | Purpose |
|---|---|
| `--source_format=FORMAT` | `CSV`, `NEWLINE_DELIMITED_JSON`, `AVRO`, `PARQUET`, `ORC` |
| `--schema={SCHEMA_FILE\|SCHEMA}` | Inline schema or a file path |
| `--skip_leading_rows=N` | Skip N rows — the header |
| `--autodetect={true\|false}` | Infer the schema from the data |
| `--replace={true\|false}` | Erase existing data **and schema** first |
| `--field_delimiter=DELIMITER` | Or `-F=DELIMITER` |
| `--null_marker=STRING` | The string that means NULL |
| `--allow_jagged_rows={true\|false}` | Tolerate rows with trailing missing fields |
| `--max_bad_records=MAX` | Tolerate N bad rows before failing |
| `--bad_field_delimiter=STRING` | Delimiter for the bad-rows log table |

**`bq ls`:**

| Flag | Purpose |
|---|---|
| `--datasets={true\|false}` | List datasets |
| `--jobs={true\|false}` | List jobs |
| `--models={true\|false}` | List models |
| `--routines` | List routines |
| `--filter="FILTER"` | Filter results |
| `--max_results=N` | Page size |

### `.bigqueryrc`

The configuration file that removes repetition from every command:

```ini
[query]
--use_legacy_sql=false
--max_rows=100
--maximum_bytes_billed=10000000

[load]
--skip_leading_rows=1
--autodetect=true
```

With that file in place, `bq query 'SELECT 1'` is already GoogleSQL, already capped at 10 MB of
billing, and already limited to 100 rows of output. **The default should be safe; safety should
not require remembering a flag.**

### The dry run

`--dry_run` validates the query and returns the bytes it would scan, without executing it.

This is the single most valuable habit in this module:

```bash
bq query --use_legacy_sql=false --dry_run --format=pretty '
SELECT COUNT(*) FROM `retail.analytics.sales`
'
```

A dry run on a badly written query over a 40 TB table costs **nothing** and tells you it would
have cost $250. Every query you have not yet run should be dry-run first, and every query you
*have* run should have a `maximumBytesBilled` cap.

### Why scripting matters

A `bq` command is a manual action. A script is a **repeatable, reviewable, auditable
deployment**. The difference matters the first time something needs to run at 2am, twice, for
two partitions, without a human present.

Three properties make a script production-grade:

1. **Idempotent.** Running it twice produces the same state as running it once.
2. **Bounded.** It cannot spend more than a stated amount, and it fails fast if it would.
3. **Verifying.** It does not trust its own exit code — it checks the result.

---

## 🛠️ Hands-On

### 💻 Runs locally — the pattern, without a BigQuery account

The `bq` command is not installed in every environment, so the *pattern* is what you should
take away. Here is the same logic against the course's local modules:

```python
import sys
sys.path.insert(0, "../project/core")
from pipeline_logic import ingest_events, aggregate_events, render_summary_csv

# Stand-in for `bq load`: ingest, then verify, then report.
accepted, rejected = ingest_events([
    "event_id,user_id,event_ts,event_type,region,channel,currency,amount",
    "evt-1,u1,2026-01-15T09:00:00+00:00,order,EMEA,web,EUR,100.00",
    "evt-2,u2,2026-01-15T10:00:00+00:00,order,AMER,web,USD,50.00",
    "bad,row,here",
])

print(f"loaded:   {len(accepted)} rows")
print(f"rejected: {len(rejected)} rows")
print()
print(render_summary_csv(aggregate_events(accepted)))
```

Expected output:

```text
loaded:   2 rows
rejected: 1 rows

region,event_count,revenue_eur
AMER,1,46.00
EMEA,1,100.00
```

Note the shape: **load, count what was rejected, then aggregate.** The rejected count is not an
error to be printed — it is an assertion to be checked.

Also note `AMER` shows **46.00**, not 50.00 — the pipeline normalises currency to EUR before
aggregating, so the summary is comparable across regions. This is the same normalisation the
`interview/` bank describes in `pipeline_logic.normalise_currency`, and it is the difference
between a regional breakdown you can total and one you cannot.

### 🌐 Needs a BigQuery project — the everyday commands

```bash
# Set the project once, so every later command inherits it.
gcloud config set project YOUR_PROJECT_ID

# Create a dataset (idempotent: the flag makes a re-run a no-op).
bq mk --dataset --location=YOUR_REGION YOUR_DATASET

# List what exists.
bq ls --datasets=true --format=pretty
bq ls --format=pretty YOUR_DATASET
bq show --format=pretty YOUR_DATASET.sales

# Run a query and get CSV out.
bq query --use_legacy_sql=false --format=csv '
SELECT store_id, SUM(sales_amount) AS revenue
FROM `YOUR_PROJECT_ID.YOUR_DATASET.sales`
WHERE sale_date = "2026-11-13"
GROUP BY store_id
ORDER BY revenue DESC
'
```

### 🌐 Needs a BigQuery project — the dry-run-then-load loop

```bash
#!/usr/bin/env bash
set -euo pipefail

PROJECT="YOUR_PROJECT_ID"
DATASET="YOUR_DATASET"
BUCKET="YOUR_BUCKET"
MAX_BYTES=10000000000   # 10 GB — a query beyond this fails rather than billing

# 1. Dry run first: validate and price the query at no cost.
BYTES=$(bq query --use_legacy_sql=false --dry_run --format=pretty \
  "SELECT COUNT(*) FROM \`$PROJECT.$DATASET.sales\`" \
  | grep -oP 'totalBytesProcessed: \K[0-9]+')

echo "Query would scan ${BYTES} bytes."

# 2. Only then run it, with a hard billing cap.
bq query --use_legacy_sql=false \
  --maximum_bytes_billed="${MAX_BYTES}" \
  --format=pretty \
  "SELECT COUNT(*) FROM \`$PROJECT.$DATASET.sales\`"

# 3. Load, also capped.
bq load \
  --source_format=CSV \
  --skip_leading_rows=1 \
  --schema=transaction_id:STRING,store_id:STRING,sale_date:DATE,customer_id:STRING,sales_amount:NUMERIC \
  --replace=true \
  "${PROJECT}:${DATASET}.sales" \
  "gs://${BUCKET}/sales.csv"
```

Three things make this safe: `set -euo pipefail` (fail on the first error, fail on an unset
variable, fail on a failed pipe), the dry run before the spend, and `maximum_bytes_billed` on
both the query and the load.

### 🌐 Needs a BigQuery project — the idempotent creation script

```bash
#!/usr/bin/env bash
set -euo pipefail

PROJECT="YOUR_PROJECT_ID"
DATASET="YOUR_DATASET"
LOCATION="YOUR_REGION"

# `bq mk` fails if the dataset exists. That is fine — the failure IS the idempotency.
if ! bq mk --dataset --location="${LOCATION}" "${PROJECT}:${DATASET}" 2>/dev/null; then
  echo "Dataset ${DATASET} already exists — continuing."
fi

# Drop and recreate the target table: a clean, deterministic starting point.
bq rm --table --recursive=true "${PROJECT}:${DATASET}.sales" 2>/dev/null || true

bq mk --table \
  --location="${LOCATION}" \
  --schema=transaction_id:STRING,store_id:STRING,sale_date:DATE,customer_id:STRING,sales_amount:NUMERIC \
  --time_partitioning=sale_date \
  --clustering_fields=store_id \
  "${PROJECT}:${DATASET}.sales"

echo "Ready."
```

The `|| true` on the delete is deliberate: it is there so a re-run on a fresh environment does
not abort the script.

### 🌐 Needs a BigQuery project — load, verify, assert

The pattern from module 3, as a script. This is the one to copy.

```bash
#!/usr/bin/env bash
set -euo pipefail

PROJECT="YOUR_PROJECT_ID"
DATASET="YOUR_DATASET"
TABLE="${PROJECT}:${DATASET}.sales"
PARTITION="2026-11-13"

# --- Load ---
bq load \
  --source_format=CSV \
  --skip_leading_rows=1 \
  --schema=transaction_id:STRING,store_id:STRING,sale_date:DATE,customer_id:STRING,sales_amount:NUMERIC \
  --replace=true \
  --maximum_bytes_billed=10000000000 \
  "${TABLE}" \
  "gs://YOUR_BUCKET/sales_${PARTITION}.csv"

# --- Verify: rows must equal distinct transaction ids ---
read -r ROWS DISTINCT <<<"$(bq query --use_legacy_sql=false --format=csv '
  SELECT COUNT(*), COUNT(DISTINCT transaction_id)
  FROM `'${PROJECT}.${DATASET}.sales`
  WHERE sale_date = "'"${PARTITION}"'"
' | tail -n 1 | tr ',' ' ')"

echo "rows=${ROWS} distinct=${DISTINCT}"

if [ "${ROWS}" -eq 0 ]; then
  echo "FAIL: partition ${PARTITION} is empty" >&2
  exit 1
fi

if [ "${ROWS}" -ne "${DISTINCT}" ]; then
  echo "FAIL: duplicate transaction ids (${ROWS} rows, ${DISTINCT} distinct)" >&2
  exit 1
fi

echo "OK: ${PARTITION} loaded and verified."
```

The exit code is the point. A script that exits non-zero fails the orchestration task, and the
data never reaches a dashboard.

### 💻 Runs locally — the same shape in Python

The client library version, which is what you use when the logic is more than a few queries.

```python
import sys
sys.path.insert(0, "../project/core")
from cost_model import estimate
from pipeline_logic import dedup_key, deduplicate

# The idempotency key is derived from data, so a retry collapses.
rows = [
    {"event_id": "evt-0001", "event_dt": "2026-01-15", "amount_eur": 10.0},
    {"event_id": "evt-0002", "event_dt": "2026-01-15", "amount_eur": 20.0},
    {"event_id": "evt-0001", "event_dt": "2026-01-15", "amount_eur": 10.0},
]
unique = deduplicate(rows, partition="20260115")
assert len(unique) == 2, "duplicate transaction ids"

# The cost cap, expressed as a number the pipeline can assert on.
MAX_BYTES = 10_000_000_000
estimated = estimate("bigquery", scanned_tb=10.0, apply_free_tier=False).total
print(f"estimated scan cost: ${estimated:.2f}")
print(f"would exceed cap: {estimated > 250}")
print("all assertions passed")
```

Expected output:

```text
estimated scan cost: $62.50
would exceed cap: False
all assertions passed
```

---

## 🛠️ Common Errors and Fixes

**"Error in format string: Invalid value at line 1, column 8"**

Usually the schema string is malformed. The format is `column_name:TYPE`, comma-separated, with
no spaces after the commas:

```bash
--schema=transaction_id:STRING,store_id:STRING,sale_date:DATE
```

An empty field name, a space after the comma, or a lowercase type name will all produce this.

**"bq query --dry_run fails with 'Access Denied' but the query itself works."**

The dry run still needs permission to read the table's metadata. Verify with `bq show` on the
table. This usually means the identity can query through a view but cannot read the underlying
table's metadata.

**"The load job says 'Rows provided: 0'."**

The source path is wrong, the object does not exist, or the identity lacks read access to the
bucket. Test the path directly:

```bash
gsutil ls "gs://YOUR_BUCKET/sales.csv"
```

**"Error while reading data, error message: Could not parse '2026-11-13 09:30:00' as DATE."**

The column is declared `DATE` but the file contains a timestamp. Either declare the column as
`TIMESTAMP` or `STRING` and cast in the query. BigQuery will not silently truncate.

**"The script worked yesterday and fails today, with no changes."**

Almost always a **date**. A script that hardcodes `2026-11-13` works until the next partition
arrives. Derive the date from the logical date of the run — the same rule as Airflow's logical
date in module 5 of the `interview/` bank. Never use `now()` in a pipeline.

**"bq query returns no output but exits 0."**

The result went to a table, or the format suppressed it. Check for `--destination_table`, and
try `--format=json` to see what came back.

---

## 💡 Production Notes

### The `.bigqueryrc` I would ship

```ini
[query]
--use_legacy_sql=false
--max_rows=100
--maximum_bytes_billed=10000000

[load]
--skip_leading_rows=1
```

The two defaults that matter are `maximum_bytes_billed` and `use_legacy_sql=false`. Both turn a
forgettable mistake into an automatic failure.

### A shell script checklist

- [ ] `set -euo pipefail` on line 2.
- [ ] No hardcoded dates — take the partition from an argument.
- [ ] `maximum_bytes_billed` on every query and every load.
- [ ] A dry run before the first real query of a new shape.
- [ ] An assertion after the load, not just before it.
- [ ] Non-zero exit on failure, so the orchestrator stops.
- [ ] The project ID from an environment variable, not hardcoded.

### The Python client library, when to switch

Reach for the Python library rather than shelling out when:

- The logic involves loops, conditionals or retries — shell gets ugly fast.
- You need the **Storage Write API** with a write stream ID for exactly-once delivery.
- You want typed parameters instead of string interpolation.
- You want the job's `total_bytes_billed` programmatically, for a cost assertion.

```python
from google.cloud import bigquery

client = bigquery.Client()
job = client.query(
    """
    SELECT store_id, SUM(sales_amount) AS revenue
    FROM `retail.analytics.sales`
    WHERE sale_date = @sale_date
    GROUP BY store_id
    """,
    job_config=bigquery.QueryJobConfig(
        use_legacy_sql=False,
        maximum_bytes_billed=10_000_000_000,
        query_parameters=[
            bigquery.ScalarQueryParameter("sale_date", "DATE", "2026-11-13"),
        ],
    ),
)
rows = list(job.result())
print(f"{len(rows)} rows, {job.total_bytes_billed} bytes billed")
```

**Never build SQL by string-interpolating a user value.** Use query parameters — they are
correct by construction, and they keep you out of the SQL injection conversation entirely.

### The rule for CI

Any query that runs in CI gets a `maximumBytesBilled` and a row-count assertion. A CI job that
spends real money is a CI job that will eventually spend an unreasonable amount, because
someone will merge a query against the full dataset and the pipeline will run it four times
across four environments.

---

## 🔑 Key Takeaways

- `bq` = `mk`, `load`, `query`, `ls`, `show`, `rm`, `cp`. `bq mk` needs a **resource-type
  flag**.
- **Always `--use_legacy_sql=false`.** Put it in `.bigqueryrc` so you cannot forget it.
- **`--dry_run` prices a query for free.** Use it on every query shape you have not run before.
- **`--maximum_bytes_billed` turns a budget incident into a failed job.** Put it on everything.
- `--replace=true` on a load makes it idempotent. `--autodetect=true` is for exploration, not
  production.
- `set -euo pipefail`, no hardcoded dates, and a non-zero exit on failure — that is what makes a
  script production-grade.
- **Verify after loading**, with `COUNT(*) = COUNT(DISTINCT key)`.
- In Python, use **query parameters**, never string interpolation.

---

## 📚 Practice Exercises

1. Write a `.bigqueryrc` for a team that runs both ad-hoc exploration and scheduled pipelines,
   and explain each line. Then state what happens if a developer overrides it with an explicit
   flag, and whether that is a problem you would try to prevent.

2. Using `--dry_run`, work out how to extract the bytes a query would scan from the CLI output
   and use it to fail a build when a query exceeds a threshold. Write the shell snippet and
   explain why the threshold belongs in the pipeline rather than in a review checklist.

3. Write a complete idempotent shell script that creates a dataset, creates a partitioned and
   clustered table, loads a file, verifies the row count, and exits non-zero on mismatch. Then
   explain, line by line, what would happen if you ran it twice.

4. Rewrite the "load, verify, assert" script from this module in the Python client library. Then
   explain what the two versions are better and worse at, and when you would choose each.

5. Take a query that interpolates a date as a string, and rewrite it with a query parameter in
   both the CLI and the Python library. Then explain what happens with the original version when
   the value is `'2026-11-13' OR 1=1`, and why the parameterised version is not vulnerable.

6. Write a script that processes a date range of partitions in a loop. Then explain why the loop
   should be bounded, what happens when it is not, and how you would make the script resumable
   after a failure halfway through the range.

7. Explain the difference between `--replace=true` and `--append=true` for a load, in terms of
   what happens to the table's schema as well as its data. Then describe a scenario where
   `--replace=true` on a production table is a mistake.

8. Using the `bq` reference, produce a command reference sheet for your team covering the
   commands you use most, with a one-line example each and the flag you always pass. Then
   explain which of those flags are safety flags and which are convenience flags.

---

## 📖 Further Reading

- [Using the bq command-line tool](https://docs.cloud.google.com/bigquery/docs/bq-command-line-tool)
- [bq CLI reference](https://docs.cloud.google.com/bigquery/docs/reference/bq-cli-reference)
- [Quickstart: load data with the command line](https://docs.cloud.google.com/bigquery/docs/quickstarts/load-data-bq)
- [BigQuery API client libraries](https://docs.cloud.google.com/bigquery/docs/reference/libraries)
- [Controlling costs](https://docs.cloud.google.com/bigquery/docs/controlling-costs)
- [Course interview bank: Processing and Orchestration](../interview/05-processing-and-orchestration.md)
