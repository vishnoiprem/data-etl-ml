"""Build the practice notebooks.

Run from the `practice/` directory:  python notebooks/_build_notebooks.py

The generated notebooks use the same cell conventions as the course's own
notebooks: `#` title, then `##` numbered sections, and a setup cell that puts
the course's pure core modules on the path.
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

METADATA = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    },
    "language_info": {"name": "python", "version": "3.11"},
}


def md(source: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": source.strip("\n") + "\n"}


def code(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.strip("\n") + "\n",
    }


def notebook(cells: list[dict]) -> dict:
    return {
        "cells": cells,
        "metadata": METADATA,
        "nbformat": 4,
        "nbformat_minor": 5,
    }


SETUP = """
import sys
from pathlib import Path

# The course's pure core modules. No installation and no cloud SDK — that is
# the whole point of the split.
COURSE_ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd().parent
sys.path.insert(0, str(COURSE_ROOT / "project" / "core"))

from cost_model import (
    BIGQUERY_ONDEMAND_PER_TB,
    BIGQUERY_SLOT_HOUR,
    compare_architectures,
    estimate,
    format_comparison,
    monthly_runway,
)
from pipeline_logic import (
    aggregate_events,
    bucket_by_window,
    dedup_key,
    deduplicate,
    estimated_scan_bytes,
    partition_for_date,
    partition_for_event,
)

print("core modules on the path:", (COURSE_ROOT / "project" / "core").exists())
"""


# ---------------------------------------------------------------------------
# 01 — Storage and partitioning
# ---------------------------------------------------------------------------

NB1 = notebook([
    md("""
# Storage and partitioning

The half of BigQuery you can model on your laptop.

BigQuery organises data into **datasets**, and datasets hold **tables** and **views**. The
tables live in **Colossus**, Google’s distributed storage system, in **Capacitor** — a
compressed columnar format — and **Dremel** executes your SQL across **slots**.

The memory trick for the whole architecture:

```text
S → C → C → D → S
Serverless → Colossus → Capacitor → Dremel → Slots
```

Everything in this notebook follows from one idea: **BigQuery bills for bytes scanned**, so
every layout decision is a cost decision.
"""),

    md("""
## 0. Setup

Put the course’s pure core modules on the path. No installation and no cloud SDK.
"""),
    code(SETUP),

    md("""
## 1. Partition decorators

BigQuery partitions a table by a date column, and names each partition with a **decorator** —
the date with the dashes removed. The course’s helper produces the same convention.
"""),
    code("""
print("logical date ->", partition_for_date("2026-01-15"))
print("event time  ->", partition_for_event("2026-01-15T09:30:00+00:00"))
print("decorator   ->", partition_for_date("2026-01-15"))
"""),

    md("""
## 2. How much does a table actually weigh?

BigQuery is **columnar**: it stores data in columns, in blocks. A query that reads two columns
reads two columns’ worth of bytes — the rest are never opened. That is the mechanism behind
every cost optimisation BigQuery has.
"""),
    code("""
rows = [
    {
        "event_id": f"e{i:08d}",
        "user_id": f"u{i:06d}",
        "event_dt": "2026-01-15",
        "region": ("AMER", "EMEA", "APAC", "LATAM")[i % 4],
        "event_type": ("order", "refund", "page_view", "signup")[i % 4],
        "amount_eur": 10.0 + (i % 97),
    }
    for i in range(4800)
]

full = estimated_scan_bytes(rows, partitioned=False)
pruned = estimated_scan_bytes(rows, partitioned=True, partition_prune_ratio=0.01)

print(f"rows:            {len(rows):,}")
print(f"unpartitioned:   {full:,} bytes")
print(f"pruned to 1%:    {pruned:,} bytes")
print(f"reduction:       {full / pruned:.0f}x")
"""),

    md("""
## 3. The number to remember

A 10 TB table, scanned whole versus pruned to one partition. **$62.50 versus $0.63** — and the
saving came from the *table layout*, not from rewriting the query.
"""),
    code("""
whole = estimate("bigquery", scanned_tb=10.0, apply_free_tier=False).total
pruned = estimate("bigquery", scanned_tb=0.1, apply_free_tier=False).total

print(f"unpartitioned: ${whole:.2f}")
print(f"partitioned:   ${pruned:.2f}")
print(f"saving:        ${whole - pruned:.2f}  ({whole / pruned:.0f}x)")
"""),

    md("""
## 4. The free tier trap

`estimate()` applies the monthly free tier by default — 1 TB of scanned bytes. A 1 TB scan
therefore prices at $0.00, which is true and also completely misleading as a price list.

**Always pass `apply_free_tier=False` when you want the price list rather than the bill.**
"""),
    code("""
print("1 TB, free tier ON :", estimate("bigquery", scanned_tb=1.0).total)
print("1 TB, free tier OFF:", estimate("bigquery", scanned_tb=1.0, apply_free_tier=False).total)
print()
print("per-TB price:", BIGQUERY_ONDEMAND_PER_TB)
print("slot-hour price:", BIGQUERY_SLOT_HOUR)
"""),

    md("""
## 5. Clustering only pays when you filter

Clustering sorts data within a partition so that a **filter** on the clustered column can skip
blocks. A query that aggregates over *every* value of that column gets nothing from it.

This is the most commonly misunderstood point in BigQuery performance work, and it is worth
being able to explain in one sentence.
"""),
    code("""
# A table clustered by region.
by_region = {"AMER": 0, "EMEA": 0, "APAC": 0, "LATAM": 0}
for row in rows:
    by_region[row["region"]] += 1

print("rows per region:", by_region)
print()
print("Clustering helps when the query says: WHERE region = 'AMER'")
print("Clustering does NOT help when the query says: GROUP BY region")
print()
print("Query 1 (selective filter) reads the AMER blocks only.")
print("Query 2 (aggregate all) reads every block in the partition either way.")
"""),

    md("""
## 6. Idempotency keys, derived from data

A retry must produce the **same** identity, so the duplicate collapses. If the key included a
load timestamp, the retry would produce a *different* key and both rows would survive.

This is the same lesson as Pub/Sub at-least-once delivery, and it is the reason
`dedup_key` takes an event id and a partition — not a clock reading.
"""),
    code("""
batch = [
    {"event_id": "evt-0001", "event_dt": "2026-01-15", "amount_eur": 10.0},
    {"event_id": "evt-0002", "event_dt": "2026-01-15", "amount_eur": 20.0},
    {"event_id": "evt-0001", "event_dt": "2026-01-15", "amount_eur": 10.0},
]

print("idempotency key:", dedup_key("evt-0001", "20260115"))
print(f"in:  {len(batch)} rows")
print(f"out: {len(deduplicate(batch, partition='20260115'))} rows")
"""),

    md("""
## 7. Windows and aggregation

Windowing derives the bucket from the **event timestamp**, never from arrival time. Get that
wrong and every event collapses into one window — and the totals stay right, which is exactly
why the bug is easy to miss.

Note which field the windowing reads: `event_dt`, and it must be a **full timestamp**. A date
alone puts every event in the same window, because there is no hour to separate them.
"""),
    code("""
# A day of events, one timestamp per hour.
windowed = [
    {**row, "event_dt": f"2026-01-15T{(i % 24):02d}:00:00+00:00"}
    for i, row in enumerate(rows)
]

buckets = bucket_by_window(windowed)
print(f"hourly windows: {len(buckets)}")
print(f"first window:   {min(buckets)}")
print(f"last window:    {max(buckets)}")
print()
summary = aggregate_events(rows)
for region in sorted(summary):
    stats = summary[region]
    print(f"{region:<6} {int(stats['event_count']):>5} events  ${stats['revenue_eur']:>12,.2f}")
"""),

    md("""
## What you should be able to say now

Without notes:

1. The five-component chain, and the memory trick.
2. Why a 10 TB table costs **$62.50** to scan and **$0.63** when partitioned.
3. Why clustering helps some queries and not others.
4. Why an idempotency key must come from the data.
5. Why `apply_free_tier=False` when you are quoting a price.
"""),
])


# ---------------------------------------------------------------------------
# 02 — Query cost lab
# ---------------------------------------------------------------------------

NB2 = notebook([
    md("""
# Query cost lab

Four architectures, one workload, priced side by side.

This is the module that turns "BigQuery is expensive" into something you can defend. Every
number here comes from the course's own price list, so it is reproducible without an account.
"""),

    md("""
## 0. Setup
"""),
    code(SETUP),

    md("""
## 1. The four architectures

`compare_architectures()` prices the same workload four ways and returns them **cheapest
first**.

Read the output carefully: two rows are `$0.0000`, because the default `streaming_hours=0.0`
means no streaming was configured. **Never read a `$0.00` streaming row as free.**
"""),
    code("""
print(format_comparison(compare_architectures()))
"""),

    md("""
## 2. Give the streaming rows a real number

Now the comparison means something. Note that Dataproc is cheaper per vCPU-hour than Dataflow —
and that does not make Dataproc the right answer.
"""),
    code("""
options = compare_architectures(streaming_hours=24, batch_runs=30)
print(format_comparison(options))
print()
for name, cost in options:
    print(f"{name:<38} ${cost:>10.4f}")
"""),

    md("""
## 3. The 100× partitioning multiplier

The single biggest lever in BigQuery cost, and it costs nothing to apply.

Partitioning is a **range** operation on a date column. A query with a date predicate skips
whole partitions at the metadata level — they are never opened.
"""),
    code("""
print(f"{'prune ratio':>12} {'TB scanned':>12} {'cost':>12}")
print("-" * 38)
for ratio in (1.0, 0.1, 0.01, 0.001):
    tb = 10.0 * ratio
    cost = estimate("bigquery", scanned_tb=tb, apply_free_tier=False).total
    print(f"{ratio:>12} {tb:>12.2f} {cost:>12.4f}")
"""),

    md("""
## 4. On-demand versus flat-rate

Two different units, and the crossover is a real number you can compute.

- **On-demand**: $6.25 per TB scanned. You pay for what you read.
- **Flat-rate**: $0.06 per slot-hour. You pay for capacity, whether or not it is busy.

The crossover: at what scan volume does 1000 slot-hours cost the same as the on-demand scan?
"""),
    code("""
flat = estimate("bigquery", slot_hours=1000, apply_free_tier=False).total
print(f"flat-rate, 1000 slot-hours: ${flat:.2f}")
print()
print(f"on-demand equivalent:       ${flat:.2f}")
print(f"= {flat / BIGQUERY_ONDEMAND_PER_TB:.1f} TB scanned")
print()
print("Below that volume, on-demand wins.")
print("Above it, flat-rate wins — provided the slots are actually busy.")
print("Reserve for the average and you queue at the peaks.")
"""),

    md("""
## 5. The three billing units

The one that surprises people is storage, because it is metered separately from everything
else — and it is what makes a materialized view a trade rather than a free win.
"""),
    code("""
print("=== SCAN: on-demand bytes ===")
print(f"10 TB scan: ${estimate('bigquery', scanned_tb=10.0, apply_free_tier=False).total:.2f}")
print()
print("=== SLOTS: compute capacity ===")
print(f"1000 slot-hours: ${estimate('bigquery', slot_hours=1000, apply_free_tier=False).total:.2f}")
print()
print("=== STORAGE: data at rest ===")
for gb in (100, 1024, 10240):
    cost = estimate("bigquery", storage_gb=gb, apply_free_tier=False).total
    print(f"{gb:>6,} GB-month: ${cost:>10.2f}")
print()
print(f"Dataflow monthly runway: ${monthly_runway('dataflow'):.2f}")
print(f"Compute Engine monthly runway: ${monthly_runway('compute-engine'):.2f}")
"""),

    md("""
## 6. A dashboard, priced both ways

The materialized-view argument, in numbers. The read frequency is what decides it.
"""),
    code("""
SCAN_TB, READS, DAYS = 2.0, 200, 30

logical = estimate("bigquery", scanned_tb=SCAN_TB * READS * DAYS,
                   apply_free_tier=False).total
materialized = estimate("bigquery", scanned_tb=SCAN_TB * DAYS, storage_gb=50,
                        apply_free_tier=False).total

print(f"logical view:      ${logical:>12,.2f}")
print(f"materialized view: ${materialized:>12,.2f}")
print(f"difference:        ${logical - materialized:>12,.2f}")
print()
print(f"break-even at about {materialized / (SCAN_TB * BIGQUERY_ONDEMAND_PER_TB):.0f} reads per month.")
"""),

    md("""
## 7. Guardrails

`maximumBytesBilled` turns a budget incident into a failed job. The cost of the failure is a
retry; the cost of the success is unbounded.
"""),
    code("""
MAX_BYTES = 10_000_000_000
MAX_TB = MAX_BYTES / 1024**4

print(f"maximumBytesBilled: {MAX_BYTES:,} bytes")
print(f"that is {MAX_TB:.4f} TB")
print(f"priced at $6.25/TB: ${MAX_TB * BIGQUERY_ONDEMAND_PER_TB:.2f}")
print()
print("Above that, the job FAILS. Which is the correct behaviour at 3am.")
"""),

    md("""
## What you should be able to say now

1. Why two rows in the architecture comparison are `$0.0000`.
2. The 100× partitioning win, in dollars.
3. Where the on-demand and flat-rate lines cross.
4. Why storage is a separate billing unit and what it makes expensive.
5. What `maximumBytesBilled` does and why it belongs on every job.
"""),
])


# ---------------------------------------------------------------------------
# 03 — bq CLI lab
# ---------------------------------------------------------------------------

NB3 = notebook([
    md("""
# The `bq` command line and scripting

`bq` is BigQuery’s Python-based command-line interface. It wraps the same REST API the
console and the client libraries use.

> ⚠️ **These `bq` commands are documented, not executed here.** `bq` and `gcloud` are not
> installed in the environment where this notebook was written. The syntax and flags come from
> the official
> [BigQuery CLI reference](https://docs.cloud.google.com/bigquery/docs/reference/bq-cli-reference).
> Run them yourself and compare the output.

Everything marked **Runs locally** below executes here, with no account.
"""),

    md("""
## 0. Setup
"""),
    code(SETUP),

    md("""
## 1. The command set

```text
bq mk       create a dataset, table, view, materialized view, connection, reservation
bq load     load data into a table
bq query    run a query
bq ls       list datasets, tables, jobs, models, routines
bq show     show details of a dataset, table, or job
bq rm       remove a dataset, table, or job
bq cp       copy a table
```

`bq mk` needs a **resource-type flag** to know what to create.
"""),

    md("""
## 2. Everyday commands

```bash
# Set the project once, so every later command inherits it.
gcloud config set project YOUR_PROJECT_ID

# Create a dataset.
bq mk --dataset --location=YOUR_REGION YOUR_DATASET

# List what exists.
bq ls --datasets=true --format=pretty
bq ls --format=pretty YOUR_DATASET
bq show --format=pretty YOUR_DATASET.sales

# Run a query, CSV out.
bq query --use_legacy_sql=false --format=csv '
SELECT store_id, SUM(sales_amount) AS revenue
FROM `YOUR_PROJECT_ID.YOUR_DATASET.sales`
WHERE sale_date = "2026-11-13"
GROUP BY store_id
ORDER BY revenue DESC
'
```

**`--use_legacy_sql=false` should be in `.bigqueryrc`, not typed every time.**
"""),

    md("""
## 3. `.bigqueryrc`

```ini
[query]
--use_legacy_sql=false
--max_rows=100
--maximum_bytes_billed=10000000

[load]
--skip_leading_rows=1
--autodetect=true
```

The default should be safe. Safety should not require remembering a flag.
"""),

    md("""
## 4. The flags that matter

### `bq query`

| Flag | Purpose |
|---|---|
| `--use_legacy_sql=false` | Use GoogleSQL. Always pass this. |
| `--dry_run` | Validate and estimate bytes without executing. |
| `--maximum_bytes_billed=N` | Fail the query if it would exceed N bytes. |
| `--use_query_cache=false` | Bypass the result cache. |
| `--destination_table=...` | Write the result to a table. |
| `--parameter=...` | Bind a query parameter. |
| `--format=...` | `json`, `prettyjson`, `csv`, `pretty`, `none`, `text`. |

### `bq load`

| Flag | Purpose |
|---|---|
| `--source_format=FORMAT` | `CSV`, `NEWLINE_DELIMITED_JSON`, `AVRO`, `PARQUET`, `ORC` |
| `--schema={SCHEMA_FILE\\|SCHEMA}` | Inline schema, or a file path |
| `--skip_leading_rows=N` | Skip the header |
| `--autodetect={true\\|false}` | Infer the schema from the data |
| `--replace={true\\|false}` | Erase existing data **and schema** first |
| `--field_delimiter=DELIMITER` | Or `-F=DELIMITER` |
| `--null_marker=STRING` | The string that means NULL |
| `--allow_jagged_rows={true\\|false}` | Tolerate rows with trailing missing fields |
| `--max_bad_records=MAX` | Tolerate N bad rows before failing |
"""),

    md("""
## 5. Dry run — a query you have never run before

```bash
bq query --use_legacy_sql=false --dry_run --format=pretty '
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.YOUR_DATASET.sales`
'
```

This validates the query and returns the bytes it would scan, **without executing it**. A dry
run on a badly written query over a 40 TB table costs nothing and tells you it would have cost
$250.

**Runs locally** — the same habit, against the course’s cost model:
"""),
    code("""
# A dry run, expressed as a number the pipeline can act on.
DRY_RUN_TB = 40.0
dry_run_bytes = int(DRY_RUN_TB * 1024**4)
dry_run_cost = estimate("bigquery", scanned_tb=DRY_RUN_TB, apply_free_tier=False).total

print(f"dry run: {dry_run_bytes:,} bytes would be scanned")
print(f"dry run: ${dry_run_cost:.2f}")
print()
print("execute?", "NO - too expensive" if dry_run_cost > 250 else "yes")
"""),

    md("""
## 6. The idempotent creation script

```bash
#!/usr/bin/env bash
set -euo pipefail

PROJECT="YOUR_PROJECT_ID"
DATASET="YOUR_DATASET"
LOCATION="YOUR_REGION"

if ! bq mk --dataset --location="${LOCATION}" "${PROJECT}:${DATASET}" 2>/dev/null; then
  echo "Dataset ${DATASET} already exists — continuing."
fi

bq rm --table --recursive=true "${PROJECT}:${DATASET}.sales" 2>/dev/null || true

bq mk --table \\
  --location="${LOCATION}" \\
  --schema=transaction_id:STRING,store_id:STRING,sale_date:DATE,customer_id:STRING,sales_amount:NUMERIC \\
  --time_partitioning=sale_date \\
  --clustering_fields=store_id \\
  "${PROJECT}:${DATASET}.sales"
```

**Runs locally** — the same three properties, without BigQuery:
"""),
    code("""
# Idempotency, modelled: the same input always produces the same output.
batch = [
    {"event_id": "evt-0001", "event_dt": "2026-01-15", "amount_eur": 10.0},
    {"event_id": "evt-0002", "event_dt": "2026-01-15", "amount_eur": 20.0},
    {"event_id": "evt-0001", "event_dt": "2026-01-15", "amount_eur": 10.0},
]

def load_once(rows):
    \"\"\"Stand-in for `bq load --replace=true`: a deterministic starting point.\"\"\"
    return deduplicate(rows, partition="20260115")

first = load_once(batch)
second = load_once(batch)

print(f"run 1: {len(first)} rows")
print(f"run 2: {len(second)} rows")
print(f"identical: {first == second}")
"""),

    md("""
## 7. Load, verify, assert

Never finish a load job with "the command exited 0". The pattern is: load, verify the
invariants, then fail loudly if they do not hold.

```bash
read -r ROWS DISTINCT <<<"$(bq query --use_legacy_sql=false --format=csv '
  SELECT COUNT(*), COUNT(DISTINCT transaction_id)
  FROM `YOUR_PROJECT_ID.YOUR_DATASET.sales`
  WHERE sale_date = "2026-11-13"
' | tail -n 1 | tr ',' ' ')"

if [ "${ROWS}" -ne "${DISTINCT}" ]; then
  echo "FAIL: duplicate transaction ids" >&2
  exit 1
fi
```

**Runs locally** — the assertion itself:
"""),
    code("""
def verify(rows, partition):
    \"\"\"The invariant: distinct keys must equal rows once deduplicated.

    This is the check that catches a non-idempotent load or a double-delivered
    stream. If the loader is idempotent, the deduplicated set has no repeats.
    \"\"\"
    unique = deduplicate(rows, partition=partition)
    rows_n = len(unique)
    distinct_n = len({dedup_key(r["event_id"], partition) for r in unique})
    return rows_n, distinct_n, rows_n == distinct_n

# A clean batch: one row per transaction.
clean = [
    {"event_id": "evt-0001", "event_dt": "2026-01-15", "amount_eur": 10.0},
    {"event_id": "evt-0002", "event_dt": "2026-01-15", "amount_eur": 20.0},
]
rows_n, distinct_n, ok = verify(clean, "20260115")
print(f"clean batch  -> rows={rows_n} distinct={distinct_n} ok={ok}")
assert ok, "duplicate transaction ids — failing the job"
print("assertion passed")
"""),

    md("""
## 8. The Python client library, when to switch

Reach for Python rather than shelling out when the logic has loops, conditionals or retries;
when you need the Storage Write API with a write stream ID for exactly-once delivery; when you
want typed parameters instead of string interpolation; or when you want
`job.total_bytes_billed` programmatically, for a cost assertion.

```python
from google.cloud import bigquery

client = bigquery.Client()
job = client.query(
    \"\"\"
    SELECT store_id, SUM(sales_amount) AS revenue
    FROM `retail.analytics.sales`
    WHERE sale_date = @sale_date
    GROUP BY store_id
    \"\"\",
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

**Never build SQL by string-interpolating a user value.** Query parameters are correct by
construction.
"""),

    md("""
## What you should be able to say now

1. The `bq` command set, and why `bq mk` needs a resource-type flag.
2. Why `--use_legacy_sql=false` belongs in `.bigqueryrc`.
3. What `--dry_run` gives you, and why it is free.
4. Why `maximumBytesBilled` belongs on every job.
5. The three properties that make a script production-grade: idempotent, bounded, verifying.
6. Why query parameters, not string interpolation.
"""),
])


def main() -> None:
    targets = {
        "01-storage-and-partitioning.ipynb": NB1,
        "02-query-cost-lab.ipynb": NB2,
        "03-bq-cli-lab.ipynb": NB3,
    }
    for name, nb in targets.items():
        path = HERE / name
        path.write_text(json.dumps(nb, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {name}")


if __name__ == "__main__":
    main()
