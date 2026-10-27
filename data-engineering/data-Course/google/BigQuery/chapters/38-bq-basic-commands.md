# 6.2 — `bq` Basic Commands

> **Section 6 · Command Line Interface · Lecture 6.2 · 6:36**

## 🎯 What you will learn

- The `bq ls`, `show`, `rm`, `mk`, and `cp` commands in depth
- The output formats and how to pipe them into `jq`
- The flags that matter for each command
- Scripts that use `bq` safely

---

## 🧠 Concept

The `bq` command follows a consistent pattern:

```
bq <command> [subcommand] [flags] [arguments]
```

The commands you will use most are `ls`, `show`, `mk`, `rm`, `cp`, `query`, `load`, `extract`, and
`insert`.

---

## 🧠 `bq ls` — list resources

```bash
# List datasets
bq ls --project_id=YOUR_PROJECT_ID

# List tables in a dataset
bq ls --project_id=YOUR_PROJECT_ID --dataset_id=curated

# List with details
bq ls --project_id=YOUR_PROJECT_ID --dataset_id=curated --max_results=20

# Machine-readable output — essential for scripts
bq ls --project_id=YOUR_PROJECT_ID --dataset_id=curated --format=json
bq ls --project_id=YOUR_PROJECT_ID --dataset_id=curated --format=csv
bq ls --project_id=YOUR_PROJECT_ID --dataset_id=curated --format="value(tableId)"

# Only tables (exclude views and MVs)
bq ls --project_id=YOUR_PROJECT_ID --dataset_id=curated --filter="type:TABLE"

# Include views
bq ls --project_id=YOUR_PROJECT_ID --dataset_id=curated --filter="type:VIEW"

# List jobs
bq ls --project_id=YOUR_PROJECT_ID --jobs --max_results=10
bq ls --project_id=YOUR_PROJECT_ID --jobs --format=json --state=RUNNING

# List scheduled queries
bq ls --project_id=YOUR_PROJECT_ID --schedule

# List transfer configurations
bq ls --project_id=YOUR_PROJECT_ID --transfers
```

💡 **`--format="value(tableId)"` is the key to scripting.** It gives you a clean, one-item-per-line
list with no headers or brackets — perfect for piping into a `while read` loop.

```bash
# The classic script pattern
bq ls --project_id=YOUR_PROJECT_ID --dataset_id=curated \
    --format="value(tableId)" | while read -r table; do
    echo "Processing $table"
    bq query --use_legacy_sql=false \
      "SELECT COUNT(*) FROM \`YOUR_PROJECT_ID.curated.$table\`"
done
```

### Output formats

| Format | Output | Use for |
|--------|--------|---------|
| `pretty` | Human-readable tables | Interactive use |
| `prettyjson` | Pretty JSON | Interactive scripting |
| `json` | Compact JSON | `jq` pipelines |
| `csv` | Comma-separated | Spreadsheets |
| `tsv` | Tab-separated | Shell processing |
| `value(field)` | Just that field's value | Scripting |
| `none` | No output | Suppressing output |

---

## 🧠 `bq show` — inspect resources

```bash
# Show a table's schema
bq show --project_id=YOUR_PROJECT_ID --schema --format=prettyjson YOUR_PROJECT_ID:curated.orders

# Show only the schema fields
bq show --schema --format=csv YOUR_PROJECT_ID:curated.orders

# Show table metadata
bq show --format=prettyjson YOUR_PROJECT_ID:curated.orders

# Show a dataset
bq show --format=prettyjson YOUR_PROJECT_ID:curated

# Show a view definition
bq show --format=prettyjson YOUR_PROJECT_ID:curated.v_orders

# Show a job's details
bq show --format=prettyjson --job_id=bquxjob_abc123
```

```bash
# Extract just the column names
bq show --schema --format=csv YOUR_PROJECT_ID:curated.orders | cut -d, -f1

# Get the row count
bq show --format=json YOUR_PROJECT_ID:curated.orders | jq -r '.numRows'
```

💡 **`bq show --schema --format=csv` is the fastest way to inspect a table's schema** and to
generate a schema file for a load job.

---

## 🧠 `bq mk` — create resources

```bash
# Create a dataset
bq mk --dataset --location=US YOUR_PROJECT_ID:curated

# Create a dataset with a description and labels
bq mk --dataset \
    --location=US \
    --description="Curated analytics models" \
    --labels=env=prod,tier=curated \
    YOUR_PROJECT_ID:curated

# Create a table from a schema
bq mk --table \
    --description="Orders" \
    --time_partitioning_type=DAY \
    --time_partitioning_field=order_date \
    --require_partition_filter \
    YOUR_PROJECT_ID:curated.orders \
    order_id:STRING,order_date:DATE,total_amount:NUMERIC,status:STRING

# Create a clustered table
bq mk --table \
    --time_partitioning_type=DAY \
    --time_partitioning_field=order_date \
    --clustering_fields=customer_id,status \
    YOUR_PROJECT_ID:curated.orders_clustered \
    order_id:STRING,customer_id:STRING,order_date:DATE,total_amount:NUMERIC

# Create an external table
bq mk --table \
    --source_format=PARQUET \
    --source_uris=gs://YOUR_PROJECT_ID-bq-course/raw/events_*.parquet \
    YOUR_PROJECT_ID:raw.events_external

# Create a view
bq mk --use_legacy_sql=false \
    YOUR_PROJECT_ID:curated.v_active_orders \
    "SELECT * FROM \`YOUR_PROJECT_ID.curated.orders\` WHERE status='active'"

# Create a materialized view
bq mk --use_legacy_sql=false \
    --time_partitioning_type=DAY \
    --time_partitioning_field=order_date \
    YOUR_PROJECT_ID:mart.mv_daily_revenue \
    "SELECT order_date, customer_id, SUM(total_amount) AS revenue \
     FROM \`YOUR_PROJECT_ID.curated.orders\` GROUP BY 1,2"
```

⚠️ **`bq mk` for DDL has limits.** Complex DDL (nested schemas, policy tags, `DEFAULT` values) is
easier via a `bq query` with a DDL statement:

```bash
bq query --use_legacy_sql=false '
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders` (
  order_id STRING NOT NULL,
  order_date DATE NOT NULL,
  line_items ARRAY<STRUCT<product_id STRING, qty INT64>>
) PARTITION BY order_date
OPTIONS (require_partition_filter = TRUE)'
```

💡 **Use `bq query` for anything non-trivial DDL.** It supports the full syntax.

---

## 🧠 `bq rm` — delete resources

```bash
# Delete a table
bq rm --table YOUR_PROJECT_ID:curated.orders

# Delete a dataset (and everything in it)
bq rm --dataset --delete_contents YOUR_PROJECT_ID:curated

# Delete without prompting
bq rm --table --force YOUR_PROJECT_ID:curated.orders

# Delete a partition
bq rm --partition_filter=order_date=20260101 YOUR_PROJECT_ID:curated.orders

# Undelete a dropped table
bq undelete YOUR_PROJECT_ID:curated.orders_dropped_20261027
```

⚠️ **`bq rm --dataset --delete_contents` is destructive.** It deletes every table in the dataset.
There is no `--dry_run` for it. Always verify the dataset name first.

💡 **Recovery:** dropped tables can be recovered with `bq undelete` for 30 days. Deleted *files*
inside a table cannot.

---

## 🧠 `bq cp` — copy resources

```bash
# Copy a table
bq cp YOUR_PROJECT_ID:curated.orders YOUR_PROJECT_ID:backup.orders_backup

# Copy with a new expiration
bq cp \
    --destination_table_expiration_timestamp=2027-01-01T00:00:00Z \
    YOUR_PROJECT_ID:curated.orders \
    YOUR_PROJECT_ID:backup.orders_backup

# Copy a single partition
bq cp 'YOUR_PROJECT_ID:curated.orders$20260115' YOUR_PROJECT_ID:backup.orders_20260115

# Copy a wildcard of tables
bq cp --ignore_existing YOUR_PROJECT_ID:curated.events_* YOUR_PROJECT_ID:backup.events_*

# Copy a dataset to another project
bq cp -r YOUR_PROJECT_ID:curated OTHER_PROJECT_ID:curated_backup
```

---

## 🧠 `bq head` — preview data

```bash
# Preview rows
bq head YOUR_PROJECT_ID:curated.orders

# Preview with a specific number of rows
bq head --max_rows=5 YOUR_PROJECT_ID:curated.orders

# Preview as JSON
bq head --format=json YOUR_PROJECT_ID:curated.orders
```

💡 **`bq head` is faster than a full query for a quick look.** It reads a small sample rather
than executing the full scan.

---

## 🛠️ Hands-On: A Shell Script Using bq

```bash
#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-YOUR_PROJECT_ID}"
DATASET="curated"
BYTES_CAP="10000000000"

echo "=== Tables in ${PROJECT_ID}:${DATASET} ==="
bq ls --project_id="$PROJECT_ID" --dataset_id="$DATASET" \
    --format="value(tableId)"

echo ""
echo "=== Row counts ==="
bq ls --project_id="$PROJECT_ID" --dataset_id="$DATASET" \
    --format="value(tableId)" | while read -r table; do
    rows=$(bq query --quiet --use_legacy_sql=false --max_bytes_billed="$BYTES_CAP" \
        "SELECT COUNT(*) FROM \`${PROJECT_ID}.${DATASET}.${table}\`" \
        --format="value(f0_)")
    printf "%-40s %s\n" "$table" "$rows"
done

echo ""
echo "=== Total size ==="
bq show --format=json --project_id="$PROJECT_ID" --dataset_id="$DATASET" | \
    jq -r '[.tables[]? | .numRows // 0] | add // 0'
```

---

## 💡 Production Notes

- **Always use `--format=json` or `--format=csv` in scripts** — the `pretty` format is not
  machine-parseable.
- **`--quiet` suppresses the job summary**, which keeps logs readable.
- **`--max_bytes_billed` on every `bq query`** in a script.
- **Use `set -euo pipefail`** in every shell script that touches BigQuery.
- **Dry run before destructive operations** — `bq query --dry_run` on a `CREATE OR REPLACE` shows
  the cost of the operation without running it.

---

## 🔑 Key Takeaways

- `bq ls`, `show`, `mk`, `rm`, `cp`, `head` cover resource management.
- **Output formats are the key to scripting** — `--format="value(tableId)"` and `json`/`csv`.
- Use `bq query` for complex DDL rather than `bq mk`.
- `bq undelete` recovers dropped tables within 30 days.
- Always pair scripts with `set -euo pipefail`, `--max_bytes_billed`, and `--quiet`.

---

## 📚 Practice Exercises

1. **Inventory script.** Write a script that lists every table in every dataset of a project with
   its row count, size, partition count, and clustering. Output as CSV.

2. **Safe deletion.** Write a script that deletes tables older than N days in a dataset, with a
   dry-run mode, a confirmation prompt, and a log file.

3. **Schema capture.** Write a script that dumps every table's schema to a JSON file per table,
   for use as load-job schema files.

4. **Format exploration.** Using `bq show --schema`, explore the different output formats for
   nested schemas, and document which format preserves what information.

5. **Command reference sheet.** Build a one-page cheat sheet of the `bq` commands used in this
   course, with a working example for each.

---

## 📖 Further Reading

- `bq` CLI reference — https://cloud.google.com/bigquery/docs/reference/bq-cli-reference
- `bq ls` — https://cloud.google.com/bigquery/docs/reference/bq-cli-reference#bq_ls
- `bq show` — https://cloud.google.com/bigquery/docs/reference/bq-cli-reference#bq_show
