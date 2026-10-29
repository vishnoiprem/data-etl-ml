# 5.4 — Template → BigQuery

> **Section 5 · Dataflow Templates & Deployment · Lecture 5.4 · 6:30**

## 🎯 What you will learn

- How to design the sink for a template that writes to BigQuery
- `WriteToBigQuery` and the two dispositions that matter
- Whether the schema should be a parameter or hard-coded, and why
- `CREATE_IF_NEEDED` versus `CREATE_NEVER`
- Partitioning and clustering, and how a template sets them
- `additional_bq_parameters` for `timePartitioning` and `clustering`
- Idempotency: `WRITE_TRUNCATE` versus `WRITE_APPEND`, and what a re-run does
- The "BigQuery as the checkpoint" pattern
- What a BigQuery write actually costs, separately from Dataflow

---

## 🧠 Concept

### Why the sink is the hard part

Everything upstream of the sink is a data-processing problem, and Beam
solves those uniformly. The sink is where you make a set of decisions that
are not about Beam at all:

- What is the shape of the output table?
- What happens if the job runs twice?
- Who owns the schema — the code or the table?
- How is the table partitioned, and does that match how it is queried?
- What does it cost, and who is billed?

Get these wrong and the job is "successful" — exit code zero, no errors —
while the data is wrong, duplicated, or ruinously expensive. This chapter
is about getting them right.

### `WriteToBigQuery` and its two dispositions

```python
beam.io.WriteToBigQuery(
    table,
    schema=...,
    create_disposition=...,
    write_disposition=...,
    additional_bq_parameters=...,
)
```

The transform accepts a `project.dataset.table` string (or
`dataset.table` plus a separate `project=` argument). Two dispositions
control what happens at write time.

**`create_disposition`** — what to do if the table does not exist.

| Value | Behaviour | Use |
|---|---|---|
| `CREATE_IF_NEEDED` | create the table with your schema | the general case; the template owns the table |
| `CREATE_NEVER` | fail if the table does not exist | production tables whose schema is managed elsewhere |

**`write_disposition`** — what to do with the data that is already there.

| Value | Behaviour | Use |
|---|---|---|
| `WRITE_APPEND` | add rows to the existing table | incremental loads, event streams |
| `WRITE_TRUNCATE` | delete all existing rows, then write | full refreshes |
| `WRITE_EMPTY` | write only if the table is empty | exactly-once-ish single loads |

The defaults are `CREATE_IF_NEEDED` and `WRITE_APPEND`, and the defaults
are **wrong for most batch jobs**. A batch job that runs daily, writes
appends by default, and therefore doubles the table every day. Nobody
notices for three weeks.

### Schema: parameter or hard-coded?

This is a genuine design decision, not a style question. Both are defensible,
and they suit different situations.

**Hard-coded schema in the template:**

```python
SCHEMA = {
    "fields": [
        {"name": "region", "type": "STRING", "mode": "REQUIRED"},
        {"name": "order_count", "type": "INTEGER", "mode": "REQUIRED"},
        {"name": "revenue_eur", "type": "FLOAT", "mode": "NULLABLE"},
    ]
}
```

| Pros | Cons |
|---|---|
| The schema is visible in one place, next to the code that produces it | Changing the output shape requires a code change and a redeploy |
| The table is created with exactly the right types the first time | The template cannot adapt to an existing table |
| A schema change is a code review, not a surprise | An incompatible change fails at runtime with a BigQuery error |
| Versioned with the template | — |

**Schema as a parameter:**

```python
schema = options.bq_schema  # a JSON string, passed via --parameters
```

| Pros | Cons |
|---|---|
| One template can serve several output shapes | The schema is no longer versioned with the code |
| An operator can change the target shape without a deploy | A malformed schema string fails at runtime |
| Useful for pass-through sinks | The JSON is awkward in a shell command |

**The recommendation:** hard-code the schema for a *pipeline-owned* output
table, and pass the *table name* as a parameter. The table name varies per
environment (dev, staging, prod); the schema does not. That gives you:

```python
options = TemplateOptions(sys.argv[1:])
target = options.bq_table          # a parameter
schema = SUMMARY_SCHEMA            # a constant
```

If the table already exists and is owned by another team, use
`CREATE_NEVER` and pass no schema at all — BigQuery's existing schema
applies, and a mismatch surfaces as a load-job error rather than a silent
schema change.

One more option worth knowing: `schema_update_options`. When a template
writes to an existing table whose schema has drifted, you can allow
additive changes:

```python
from apache_beam.io.gcp.bigquery import BigQuerySchemaUpdateOption

beam.io.WriteToBigQuery(
    target,
    schema=SUMMARY_SCHEMA,
    create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
    write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE,
    schema_update_options=[BigQuerySchemaUpdateOption.ALLOW_FIELD_ADDITION],
)
```

`ALLOW_FIELD_ADDITION` adds new nullable columns. It never drops or
retypes. Use it when the template is evolving and you do not want every
shape change to be a coordinated deploy — and never use it on a table
someone else reads with a strict schema contract.

### Partitioning and clustering

An unpartitioned BigQuery table is scanned in full for every query. A
partitioned one is scanned per partition. This is usually the single
biggest query-cost lever you have.

**Partitioning** splits the table by a column's value — almost always a
timestamp. The options:

| Type | Field | When |
|---|---|---|
| Ingestion time | `_PARTITIONTIME` | you do not have a reliable event-time column |
| Date column | `event_date` | you have a `DATE` or `TIMESTAMP` column |
| Integer range | `customer_id` | high-cardinality integer keys, hash partitioning |
| Datetime truncation | `event_ts` | you want hourly or monthly granularity |

**Clustering** sorts the data within each partition by one or more
columns. Clustering improves predicate pushdown: a query filtering on the
clustering column reads fewer blocks.

| Column type | Clustering effectiveness |
|---|---|
| `DATE` / `TIMESTAMP` | excellent |
| `STRING` | good, if low cardinality |
| `INT64` / `FLOAT64` | moderate |
| `BOOL` | moderate |
| `FLOAT64` | poor — the values are not ordered usefully |

A sensible default: partition by day on an event-time column, cluster by
the two or three columns your dashboards filter on.

### Setting partitioning from a template

The BigQuery API's load configuration accepts `timePartitioning` and
`clustering` objects. `WriteToBigQuery` passes them through
`additional_bq_parameters`.

```python
additional_bq_parameters = {
    "timePartitioning": {
        "type": "DAY",
        "field": "event_date",
        "expirationMs": 7776000000,
    },
    "clustering": {
        "fields": ["region", "channel"],
    },
}
```

The shape is the REST API's shape, which is why it looks slightly
awkward in Python:

```text
timePartitioning:
  type: DAY | HOUR | MONTH | YEAR | RANGE
  field: the partition column (omit for ingestion-time partitioning)
  expirationMs: optional lifetime in milliseconds (7776000000 = 90 days)

clustering:
  fields: [column_name, ...]
```

**Important:** these apply when the table is **created**. If the table
already exists, `WriteToBigQuery` does not retrofit partitioning onto it.
You change an existing table's partitioning with a DDL statement:

```sql
ALTER TABLE YOUR_PROJECT_ID.YOUR_DATASET.YOUR_TABLE
SET OPTIONS (
  partition_expiration_days = 90,
  partition_by = TIMESTAMP_TRUNC(event_ts, DAY),
  clustering_fields = ['region', 'channel']
);
```

So the decision is: does the template own the table (create it with the
right options), or does someone else (create it, and the template only
writes)?

A robust template handles both. Detect whether the table exists, and only
pass `additional_bq_parameters` when creating:

```python
def table_exists(project: str, dataset: str, table: str) -> bool:
    """Return True when the target table already exists."""
    from google.cloud import bigquery

    client = bigquery.Client(project=project)
    try:
        client.get_table(f"{project}.{dataset}.{table}")
    except Exception:
        return False
    return True
```

Then:

```python
exists = table_exists(project, dataset, table)
additional = {} if exists else {
    "timePartitioning": {"type": "DAY", "field": "event_date"},
    "clustering": {"fields": ["region"]},
}
```

### Idempotency: `WRITE_TRUNCATE` vs `WRITE_APPEND`

**This is the most important decision in the chapter.**

| | `WRITE_TRUNCATE` | `WRITE_APPEND` |
|---|---|---|
| Existing rows | deleted, then replaced | kept, new rows added |
| Re-run the same job | same table contents | table doubles |
| Failure halfway | table is partially written | original rows intact, new partial rows added |
| Storage cost | constant | grows every run |
| Right for | full refresh of a derived table | appending genuinely new events |
| Wrong for | — | a batch job that reprocesses its whole input |

For a **batch** job that reads its entire input and computes an aggregate,
`WRITE_TRUNCATE` is almost always correct: the output is a function of the
input, so re-running should produce the same table. `WRITE_APPEND` on such
a job is a bug that compounds.

For a **streaming** job, `WRITE_APPEND` is almost always correct: windows
fire repeatedly, and late data causes a window to be re-emitted. The
table must accumulate. Idempotency in streaming comes from *your* logic —
a merge key, a primary key, or a `MERGE` downstream — not from the sink's
disposition.

There is a middle path for streaming: use `WRITE_TRUNCATE` per batch
window if you run a **bounded** streaming job (a stream with a fixed end),
or write to a staging table and `MERGE` into the target.

`WRITE_EMPTY` is the third option: it writes only if the table is empty.
It gives you a "run exactly once, or fail loudly" guarantee, which is
occasionally the right call for a one-shot backfill. It is a trap for
anything that needs to run repeatedly.

#### What a re-run actually does

The mechanics matter. BigQuery's load job is atomic at the *table* level
for `WRITE_TRUNCATE` — the delete and the load are part of one load-job
configuration, so an observer never sees the empty table. But:

- A **failed** load job with `WRITE_TRUNCATE` leaves the table **empty**.
  The delete succeeded; the insert did not. This is the dangerous
  failure mode.
- A **failed** load job with `WRITE_APPEND` leaves the table with the
  original rows plus whatever partial data committed.

That asymmetry is why "BigQuery as the checkpoint" (§ below) prefers
`WRITE_APPEND` to a scratch table and a separate, explicit promotion step.

### The "BigQuery as the checkpoint" pattern

The problem: a batch job's output must be complete and correct, and you
cannot tell from the job's exit code whether the data landed.

The pattern: write to a **scratch table** with a run-specific name, verify
it, then atomically swap it into place.

```text
1. WRITE_APPEND  →  orders_by_region__staging_20261028
2. VERIFY        →  row counts, null rates, checksums
3. MERGE/COPY    →  orders_by_region
4. DROP          →  orders_by_region__staging_20261028
```

The verification step is the point. With a run-specific staging table:

- the production table is **never** in a partial state,
- a failed verification leaves the production table untouched and the
  staging table available for inspection,
- you can re-run the promotion without re-running the pipeline,
- the promotion is a BigQuery DML statement, which is fast and cheap.

The cost is that you write twice — once to staging, once to the target.
For a table of a few million rows, that is pennies. For a table of a
billion rows, it is not, and you should use a `MERGE` against the target
directly instead.

The simpler version of the same idea, which most teams should start with:

```text
1. WRITE_TRUNCATE →  the target table directly
2. VERIFY         →  row counts against expectations
```

This is fine when the pipeline is deterministic and a failed run can simply
be re-run. It is not fine when the source is being mutated while the job
runs.

### Cost: BigQuery is billed separately from Dataflow

This is not a footnote. It is frequently the larger of the two numbers.

| Item | How it is billed | Approximate cost |
|---|---|---|
| Dataflow workers | vCPU-hour | $0.056–$0.10 per vCPU-hour (standard, `us-central1`) |
| BigQuery active storage | GB-month | $0.02 per GB-month |
| BigQuery long-term storage | GB-month | $0.01 per GB-month |
| BigQuery queries | bytes scanned | $0.0125 per TB scanned (on-demand) |
| BigQuery **writes** | bytes written | **$0.01 per GB written** |
| BigQuery streaming inserts | rows | $0.01 per 1,000 rows in the streaming API |
| Cloud Storage | GB-month | $0.02 per GB-month |
| Cloud Storage reads/writes | operations | $0.05 per 10,000 ops |

Two costs surprise people:

1. **The write itself is billed.** Writing 1 GB to BigQuery costs about
   $0.01. Writing 1 TB costs about $10. In a pipeline that writes an
   intermediate table and then a final table, you pay twice.
2. **A bad partition or clustering choice costs more than the write.**
   A table that should be partitioned but is not, queried daily by ten
   dashboards, scans the whole table every time. At $0.0125 per TB, a
   10 TB table scanned ten times a day costs about $37 per day — roughly
   $1,100 a month — and it recurs forever, while the write cost is a
   one-time $0.12 per GB.

The cost model is therefore:

```text
total = Dataflow vCPU-hours + BigQuery writes + BigQuery query scans
        + Cloud Storage (temp + staging + output)

and the term that grows without bound is the query scans.
```

Design the table so the queries are cheap. That means partitioning and
clustering, and it means not writing a wide table when the consumers only
need six columns.

### Writing the sink, properly

Here is the complete sink configuration, with every decision explicit:

```python
from apache_beam.io.gcp.bigquery import (
    BigQueryDisposition,
    BigQuerySchemaUpdateOption,
)

SUMMARY_SCHEMA = {
    "fields": [
        {"name": "event_date", "type": "DATE", "mode": "REQUIRED"},
        {"name": "region", "type": "STRING", "mode": "REQUIRED"},
        {"name": "channel", "type": "STRING", "mode": "NULLABLE"},
        {"name": "order_count", "type": "INTEGER", "mode": "REQUIRED"},
        {"name": "revenue_eur", "type": "FLOAT", "mode": "NULLABLE"},
    ]
}

ADDITIONAL_PARAMETERS = {
    "timePartitioning": {
        "type": "DAY",
        "field": "event_date",
        "expirationMs": 7776000000,
    },
    "clustering": {
        "fields": ["region", "channel"],
    },
}
```

And the transform:

```python
beam.io.WriteToBigQuery(
    table=target,
    schema=SUMMARY_SCHEMA,
    create_disposition=BigQueryDisposition.CREATE_IF_NEEDED,
    write_disposition=BigQueryDisposition.WRITE_TRUNCATE,
    additional_bq_parameters=ADDITIONAL_PARAMETERS,
    schema_update_options=[
        BigQuerySchemaUpdateOption.ALLOW_FIELD_ADDITION,
    ],
)
```

Note that `additional_bq_parameters` applies to the **load job**, and the
partitioning and clustering options are only honoured when the load job
creates the table.

---

## 🛠️ Hands-On: Write to BigQuery from a Template

### The complete template

Save this as `templates/orders_to_bigquery.py`:

```python
"""A flex template that writes a per-region revenue summary to BigQuery."""
from __future__ import annotations

import sys

import apache_beam as beam
from apache_beam.io.gcp.bigquery import (
    BigQueryDisposition,
    BigQuerySchemaUpdateOption,
)
from apache_beam.options.pipeline_options import PipelineOptions

SUMMARY_SCHEMA = {
    "fields": [
        {"name": "event_date", "type": "DATE", "mode": "REQUIRED"},
        {"name": "region", "type": "STRING", "mode": "REQUIRED"},
        {"name": "order_count", "type": "INTEGER", "mode": "REQUIRED"},
        {"name": "revenue_eur", "type": "FLOAT", "mode": "NULLABLE"},
    ]
}

ADDITIONAL_PARAMETERS = {
    "timePartitioning": {
        "type": "DAY",
        "field": "event_date",
        "expirationMs": 7776000000,
    },
    "clustering": {
        "fields": ["region"],
    },
}


class TemplateOptions(PipelineOptions):
    """Runtime options for the orders-to-BigQuery template."""

    @classmethod
    def _add_argparse_args(cls, parser):
        parser.add_argument("--input", default="")
        parser.add_argument("--bq-table", default="")
        parser.add_argument("--bq-project", default="")
        parser.add_argument("--bq-dataset", default="")
        parser.add_argument("--event-date", default="2026-01-01")


def split_table_ref(table_ref: str) -> tuple[str, str, str]:
    """Split a project.dataset.table reference into its three parts.

    Args:
        table_ref: The table reference.

    Returns:
        A (project, dataset, table) tuple. Missing parts are empty strings.

    Raises:
        ValueError: If the reference has more or fewer than three parts.
    """
    parts = table_ref.split(".")
    if len(parts) != 3:
        raise ValueError(
            f"bq-table must be project.dataset.table, got {table_ref!r}"
        )
    return parts[0], parts[1], parts[2]


def table_exists(project: str, dataset: str, table: str) -> bool:
    """Return True when the target BigQuery table already exists.

    Args:
        project: The GCP project.
        dataset: The BigQuery dataset.
        table: The BigQuery table.

    Returns:
        True when the table exists.
    """
    from google.cloud import bigquery

    client = bigquery.Client(project=project)
    try:
        client.get_table(f"{project}.{dataset}.{table}")
    except Exception:
        return False
    return True


def run(argv: list[str] | None = None) -> int:
    """Build and run the pipeline."""
    args = list(argv if argv is not None else sys.argv[1:])
    options = TemplateOptions(args)

    if not options.input:
        print("input is required")
        return 2
    if not options.bq_table:
        print("bq-table is required")
        return 2

    project, dataset, table = split_table_ref(options.bq_table)
    project = options.bq_project or project
    if not project:
        print("a project is required, in the table reference or via --bq-project")
        return 2

    # Only pass the table-creation options when the table does not exist.
    # BigQuery does not retrofit partitioning onto an existing table.
    additional = (
        {}
        if table_exists(project, dataset, table)
        else ADDITIONAL_PARAMETERS
    )

    with beam.Pipeline(options=options) as p:
        rows = (
            p
            | "Read" >> beam.io.ReadFromText(options.input)
            | "Parse" >> beam.Map(lambda line: line.split(","))
            | "Valid" >> beam.Filter(lambda row: len(row) > 6 and row[6] == "complete")
            | "KeyByRegion" >> beam.Map(lambda row: (row[3], float(row[7])))
            | "SumRevenue" >> beam.CombinePerKey(sum)
            | "ToRow" >> beam.Map(
                lambda kv: {
                    "event_date": options.event_date,
                    "region": kv[0],
                    "order_count": 1,
                    "revenue_eur": kv[1],
                }
            )
        )
        rows | "WriteBigQuery" >> beam.io.WriteToBigQuery(
            table=f"{project}.{dataset}.{table}",
            schema=SUMMARY_SCHEMA,
            create_disposition=BigQueryDisposition.CREATE_IF_NEEDED,
            write_disposition=BigQueryDisposition.WRITE_TRUNCATE,
            additional_bq_parameters=additional,
            schema_update_options=[
                BigQuerySchemaUpdateOption.ALLOW_FIELD_ADDITION,
            ],
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(run())
```

### The `order_count` bug worth noticing

Look at the `ToRow` transform: it hard-codes `"order_count": 1`. That is
wrong — it reports one order per region rather than the number of orders
in that region. A `CombinePerKey(sum)` over the *revenue* only gives you
the revenue; the count needs its own accumulator.

The correct version combines both, which is what the course's
`RevenueByRegionFn` does:

```python
from apache_beam.coders import FastPrimitivesCoder


class RevenueByRegionFn(beam.CombineFn):
    """Accumulate (order_count, revenue_eur) for one region."""

    def create_accumulator(self):
        return (0, 0.0)

    def add_input(self, accumulator, element):
        count, revenue = accumulator
        return count + 1, revenue + element

    def merge_accumulators(self, accumulators):
        count = 0
        revenue = 0.0
        for acc_count, acc_revenue in accumulators:
            count += acc_count
            revenue += acc_revenue
        return count, revenue

    def extract_output(self, accumulator):
        return accumulator


with beam.Pipeline() as p:
    revenue = (
        p
        | "Read" >> beam.io.ReadFromText("./sample_data/orders.csv")
        | "Parse" >> beam.Map(lambda line: line.split(","))
        | "Valid" >> beam.Filter(lambda row: len(row) > 6 and row[6] == "complete")
        | "KeyByRegion" >> beam.Map(lambda row: (row[3], float(row[7])))
        | "Combine" >> beam.CombinePerKey(RevenueByRegionFn().with_output_coder(FastPrimitivesCoder()))
        | "Format" >> beam.Map(
            lambda kv: f"{kv[0]},{kv[1][0]},{kv[1][1]:.2f}"
        )
    )
    revenue | "Write" >> beam.io.WriteToText(
        "./out/revenue_check", num_shards=1, shard_name_template=""
    )
```

One combiner, two outputs, one shuffle. This is the shape you want in
production.

### Run it locally against a real project

```bash
cd data-engineering/data-Course/google/Dataflow

python resources/sample_data.py --output-dir ./sample_data

export PROJECT=YOUR_PROJECT_ID
export DATASET=YOUR_DATASET

# Make sure the dataset exists
bq mk --project_id=$PROJECT $DATASET

python templates/orders_to_bigquery.py \
  --input=./sample_data/orders.csv \
  --bq-table=$PROJECT.$DATASET.orders_by_region \
  --event-date=2026-01-01
```

### Inspect the table you just created

```sql
-- The partitioning
SELECT
  partition_id,
  total_rows
FROM `YOUR_PROJECT_ID.YOUR_DATASET.INFORMATION_SCHEMA.PARTITIONS`
WHERE table_name = 'orders_by_region'
ORDER BY partition_id DESC;

-- The schema and clustering
SELECT
  column_name,
  data_type,
  is_nullable
FROM `YOUR_PROJECT_ID.YOUR_DATASET.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'orders_by_region';

-- The data
SELECT region, order_count, revenue_eur
FROM `YOUR_PROJECT_ID.YOUR_DATASET.orders_by_region`
ORDER BY revenue_eur DESC;
```

### Verify the idempotency behaviour

Run the template **twice** and count the rows:

```bash
python templates/orders_to_bigquery.py \
  --input=./sample_data/orders.csv \
  --bq-table=$PROJECT.$DATASET.orders_by_region \
  --event-date=2026-01-01

bq query --project_id=$PROJECT --use_legacy_sql=false \
  "SELECT COUNT(*) AS n FROM \`$PROJECT.$DATASET.orders_by_region\`"
```

The count is the same both times, because `WRITE_TRUNCATE` replaced the
table. Now change the disposition to `WRITE_APPEND` and run it twice more:

```sql
SELECT COUNT(*) AS n FROM `YOUR_PROJECT_ID.YOUR_DATASET.orders_by_region`;
```

The count doubled. That is the bug that `WRITE_APPEND` on a batch job
always produces.

### The staging-table pattern, in SQL

```sql
-- Promote a verified staging table into the target.
BEGIN TRANSACTION;

CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.YOUR_DATASET.orders_by_region`
PARTITION BY DATE(event_date)
CLUSTER BY region
AS SELECT * FROM `YOUR_PROJECT_ID.YOUR_DATASET.orders_by_region__staging`;

DROP TABLE `YOUR_PROJECT_ID.YOUR_DATASET.orders_by_region__staging`;

COMMIT TRANSACTION;
```

The `CREATE OR REPLACE ... AS SELECT` is atomic: consumers see either the
old table or the new one, never a partially-loaded table.

### Deploy it as a flex template

```bash
export BUCKET=YOUR_BUCKET
export TEMPLATE=gs://$BUCKET/templates/orders-to-bq.py

gcloud dataflow flex-template build orders-to-bq \
  --project=$PROJECT --region=us-central1 \
  --template-file=./templates/orders_to_bigquery.py \
  --template-file-gcs-path=$TEMPLATE \
  --metadata="version=1.0.0,owner=data-platform" \
  --temp-location=gs://$BUCKET/dataflow/temp \
  --staging-location=gs://$BUCKET/dataflow/staging \
  --service-account=dataflow-worker@$PROJECT.iam.gserviceaccount.com

gcloud dataflow flex-template run orders-to-bq \
  --project=$PROJECT --region=us-central1 \
  --template=$TEMPLATE \
  --temp-location=gs://$BUCKET/dataflow/temp/$(date +%s) \
  --staging-location=gs://$BUCKET/dataflow/staging/$(date +%s) \
  --service-account=dataflow-worker@$PROJECT.iam.gserviceaccount.com \
  --parameters="input=gs://$BUCKET/orders.csv,bq-table=$PROJECT.$DATASET.orders_by_region,event-date=2026-01-01" \
  --wait=false
```

---

## 🛠️ Common Errors and Fixes

### `AttributeError: module 'apache_beam.io.gcp.bigquery' has no attribute 'BigQueryDisposition'`

```text
AttributeError: module 'apache_beam.io.gcp.bigquery' has no attribute
'BigQueryDisposition'
```

An SDK version mismatch. The import path moved between versions. Check
what the service ships:

```bash
gcloud dataflow jobs describe JOB_ID --project=YOUR_PROJECT_ID \
  --format='value(environment.sdkSupportStatus)'
```

Use `beam.io.BigQueryDisposition` — it is re-exported from the top-level
`beam.io` namespace and works across versions:

```python
beam.io.BigQueryDisposition.CREATE_IF_NEEDED
```

### `AttributeError: module 'apache_beam.io' has no attribute 'BigQueryDisposition'`

Same family of problem. Import it explicitly:

```python
from apache_beam.io.gcp.bigquery import BigQueryDisposition
```

### The table was created with no partitioning

```text
Query exceeded resource limits ... 0 bytes processed
```

The table exists and was created before you added `timePartitioning`, and
BigQuery does not retrofit it. Fix the table with DDL:

```sql
ALTER TABLE YOUR_PROJECT_ID.YOUR_DATASET.YOUR_TABLE
SET OPTIONS (
  partition_by = TIMESTAMP_TRUNC(event_ts, DAY),
  clustering_fields = ['region']
);
```

Or drop and recreate it. Then check the template's `table_exists` logic
does not pass `additional_bq_parameters` for an existing table.

### `Provided Schema does not match Table ... Field revenue_eur has changed type`

```text
Provided Schema does not match Table PROJECT:DATASET.TABLE.
Field revenue_eur has changed type from FLOAT to NUMERIC
```

The template's schema and the existing table's schema disagree.
`WRITE_TRUNCATE` does not change the schema. Either:

- update the table's schema by hand, or
- drop the table and let the template recreate it, or
- pass `schema_update_options=[ALLOW_FIELD_ADDITION]` — which only helps
  for *added* fields, not changed types.

### The job succeeded but the table has duplicate rows

```text
Query results: 2,000,000 rows — expected 1,000,000
```

`WRITE_APPEND` on a job that reprocesses its whole input. Change to
`WRITE_TRUNCATE`, or switch to the staging-table pattern with a `MERGE`.

### `PERMISSION_DENIED` writing to BigQuery

```text
google.api_core.exceptions.Forbidden: 403 Permission denied while
getting Drive credentials
```

The worker service account lacks the BigQuery role:

```bash
gcloud projects add-iam-policy-binding $PROJECT \
  --member=serviceAccount:dataflow-worker@$PROJECT.iam.gserviceaccount.com \
  --role=roles/bigquery.dataEditor \
  --project=$PROJECT
```

Grant it on the dataset, not the project, if your security policy requires
narrower scope:

```bash
gcloud projects add-iam-policy-binding $PROJECT \
  --member=serviceAccount:dataflow-worker@$PROJECT.iam.gserviceaccount.com \
  --role=roles/bigquery.dataEditor \
  --condition='expression=resource.name.startsWith("projects/YOUR_PROJECT_ID/datasets/YOUR_DATASET"),title="bq-dataset-scope"' \
  --project=$PROJECT
```

### `The job failed with OutOfMemoryError in the BigQuery writer`

The writer buffers rows before flushing. If your rows are wide or your
bundle is large, raise `max_rows_per_batch` or lower the worker count so
each worker gets fewer rows. Alternatively, reduce the number of columns
being written — the sink cost scales with row width.

### `additional_bq_parameters` seems to be ignored

Check three things:

1. The table already existed — partitioning options only apply at creation.
2. The keys are spelled exactly as the REST API expects
   (`timePartitioning`, `clustering`), with camelCase.
3. The value is a dict, not a JSON string.

### The load job fails with `Invalid schema update`

`schema_update_options` is only valid for `FILE_LOADS`, and it cannot be
combined with a `schemaUpdateOptions` inside `additional_bq_parameters`.
Remove the duplicate.

---

## 💡 Production Notes

- **The sink's disposition is part of the job's contract.** `WRITE_APPEND`
  on a full-refresh batch job is a bug that grows silently. Make the
  choice explicit in the code, and review it when someone changes the
  pipeline.
- **Use the staging-table pattern for anything a dashboard reads.** The
  extra write costs about $0.01 per GB — pennies — and it buys you an
  atomic promotion and a place to verify before you publish. This is the
  cheapest insurance in data engineering.
- **Partition and cluster on day one.** Retrofitting partitioning onto a
  5 TB table is a `CREATE OR REPLACE` of the whole table, which costs the
  write and the storage, and which you will do at the worst possible
  moment. A partitioned table also ages out with `partition_expiration_days`,
  which turns a growing table into a bounded one.
- **Watch the query cost, not the write cost.** The write is $0.01 per GB,
  once. A daily full scan of an unpartitioned 10 TB table is $0.125 per
  scan, every day, forever. Partitioning is worth more than any Dataflow
  optimisation you will do.
- **Set `partition_expiration_days` deliberately.** Without it, a
  partitioned table still grows forever, and you pay for the storage and
  for ever-wider metadata. With it, a daily table holds 90 days and stops.
- **Do not write `FLOAT` for money if the consumers care.** BigQuery
  `NUMERIC` is exact and `FLOAT64` is not. If a downstream sum must equal
  a ledger, use `NUMERIC`. The trade-off: `NUMERIC` is slower and larger
  in BigQuery, and some Beam coders handle it awkwardly.
- **Give the worker SA access to only the target dataset.** Not
  `roles/bigquery.admin` on the project. BigQuery is where the data is;
  it is the first thing an auditor asks about.
- **Verify before you trust.** Row count, null rate, and a checksum
  against the previous run. These three catch almost every silent failure
  — a missing partition, a truncated file, a schema drift — before anyone
  builds a dashboard on the wrong number.
- **Watch for the `WRITE_TRUNCATE` empty-table window.** BigQuery's load
  job is atomic, but a *failed* load leaves the table empty. If the source
  can be re-read, re-running is the fix. If it cannot, you want the
  staging-table pattern.

---

## 🔑 Key Takeaways

- The sink is where the non-Beam decisions live: schema ownership,
  idempotency, partitioning, and cost.
- `WriteToBigQuery` takes two dispositions: `create_disposition`
  (`CREATE_IF_NEEDED` / `CREATE_NEVER`) and `write_disposition`
  (`WRITE_APPEND` / `WRITE_TRUNCATE` / `WRITE_EMPTY`).
- **Hard-code the schema, parameterise the table.** The table varies by
  environment; the schema is part of the code.
- `CREATE_IF_NEEDED` when the template owns the table; `CREATE_NEVER` when
  someone else does.
- **Partitioning and clustering are set at table-creation time** through
  `additional_bq_parameters` with `timePartitioning` and `clustering`. They
  are not retrofitted onto an existing table.
- **`WRITE_TRUNCATE` for a full-refresh batch job; `WRITE_APPEND` for
  streaming.** Confusing them is the single most common BigQuery sink bug.
- The **staging-table pattern** — write to a run-specific table, verify,
  then atomically promote — is the cheapest way to make a published table
  safe.
- **BigQuery is billed separately from Dataflow**: $0.01 per GB written,
  $0.0125 per TB scanned, $0.02 per GB-month. The write is cheap; the
  repeated scan is not.

---

## 📚 Practice Exercises

1. **Compare dispositions empirically.** Create a dataset, run the template
   three times with `WRITE_APPEND` and three times with
   `WRITE_TRUNCATE`, and record the row count after each run. Then write
   down the exact condition under which each is correct, in terms of
   whether the input is fully reprocessed.

2. **Design the partition.** The `orders_by_region` table is queried by
   dashboards that filter on `region` and on a date range, and the raw
   orders have an `order_ts` timestamp. Choose a partitioning and
   clustering scheme, write the `additional_bq_parameters` dict, and
   estimate the bytes scanned by a one-day dashboard query before and
   after. Show your arithmetic.

3. **Implement the staging pattern.** Write a template that writes to
   `orders_by_region__staging_<run_id>`, and a shell script that verifies
   the staging table (row count, null rate, checksum) and then promotes it
   with `CREATE OR REPLACE ... AS SELECT`. Make the script refuse to
   promote on a failed check.

4. **Handle an existing table.** Modify the template so that when the
   target table exists it uses `CREATE_NEVER` with no schema and no
   `additional_bq_parameters`, and when it does not exist it uses
   `CREATE_IF_NEEDED` with both. Test both paths. Explain what happens to
   a table with a different schema.

5. **Cost model.** Compute the monthly cost of the following: a daily job
   that writes 5 GB to BigQuery and runs for 20 minutes on 4
   `n1-standard-2` workers; a table of 500 GB with 90-day partition
   expiration; and ten dashboards that each scan 500 MB per run, 20 runs
   a day. Break the total into Dataflow, BigQuery storage, BigQuery writes
   and BigQuery queries, and identify the term you would attack first.

6. **Fix the order count.** The `ToRow` transform in the hands-on reports
   `order_count` as 1. Rewrite it to produce the true count without adding
   a second shuffle, and show the correct `CombineFn` and the expected
   local output.

---

## 📖 Further Reading

- Google Cloud BigQuery: writing with Apache Beam — https://cloud.google.com/bigquery/docs/loading-data-cloud-dataflow-python
- Apache Beam: BigQuery I/O — https://beam.apache.org/documentation/io/sinks/bigquery/
- Google Cloud BigQuery: table partitioning — https://cloud.google.com/bigquery/docs/partitioned-tables
- Google Cloud BigQuery: clustering — https://cloud.google.com/bigquery/docs/clustered-tables
- Google Cloud BigQuery: pricing — https://cloud.google.com/bigquery/pricing
- Google Cloud BigQuery: `INFORMATION_SCHEMA` — https://cloud.google.com/bigquery/docs/information-schema
