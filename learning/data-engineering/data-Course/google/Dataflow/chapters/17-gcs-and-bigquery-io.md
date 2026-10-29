# 3.4 — GCS & BigQuery I/O

> **Section 3 · I/O & Multi-Source Pipelines · Lecture 3.4 · 6:30**

## 🎯 What you will learn

- `gs://` paths everywhere: one file transform per format, the path selects the file system
- What Beam actually needs for GCS, and the two different errors a bad `gs://` path produces
- Reading a GCS directory with `ReadFromText` and a wildcard
- GCS file naming, and the **shard explosion** problem: what happens when you write 10,000 tiny files, and how to fix it
- `WriteToBigQuery` in depth: `schema`, `write_disposition`, `create_disposition`, and the table-reference syntax
- The `additional_bq_parameters` parameter — the correct name, and what it is for
- `beam.io.ReadFromBigQuery`, and the `EXPORT` vs `DIRECT_READ` methods
- Why a BigQuery *source* in Beam is usually the wrong choice, and when writing to BigQuery from Beam is exactly right
- **The `with_sharding` misconception**: there is no such parameter, and sharding splits on **file size**, not row count

---

## 🧠 Concept

### There is no "GCS transform"

The single most important idea in this chapter is one that chapter 3.1
introduced and this chapter makes concrete:

> **Beam has one file transform per *format*. The *path* selects the
> file system.**

There is no `ReadFromGCS`. There is no `WriteToGCS`. You write
`beam.io.ReadFromText("gs://bucket/orders.csv")` and you are reading
from Cloud Storage, because the path says so. The format transform and
the file system are orthogonal.

| Scheme | Backend | Extra needed |
|---|---|---|
| `gs://bucket/path` | Cloud Storage | none — `google-cloud-storage` ships with `apache-beam` |
| `s3://bucket/path` | Amazon S3 | `s3fs` (in `[filesystem]`) |
| `hdfs://namenode/path` | HDFS | `hadoopfilesystem` |
| `./local/path` | Local disk | none |
| `file:///abs/path` | Local disk | none |

This design has a consequence that is worth internalising before you
write a single line: **your pipeline code does not change when you
move from local to GCS.** Only the path prefix changes.

The course's `project/batch_pipeline.py` is built around exactly this.
Its docstring says so:

```text
The **same code** runs locally on the Direct Runner and on Dataflow. The only
difference between a local run and a cloud run is the path prefix and the
--runner flag:

    # Local, no credentials, no bill
    python project/batch_pipeline.py --runner DirectRunner \
        --input ./sample_data/orders.csv --output ./out/summary

    # Cloud
    python project/batch_pipeline.py --runner DataflowRunner \
        --project my-project --region us-central1 \
        --input gs://my-bucket/orders.csv --output gs://my-bucket/summary \
        --staging_location gs://my-bucket/staging \
        --temp_location gs://my-bucket/temp
```

That is the property that makes a Beam pipeline worth the trouble. You
develop against a local directory, you deploy against a bucket, and the
business logic never changes.

### What Beam actually needs for GCS

Beam does not implement the GCS API itself. It ships a thin adapter —
`apache_beam.io.gcp.gcsfilesystem.GCSFileSystem` — over the official
`google-cloud-storage` client. The base `apache-beam` install already
carries that client, so **`gs://` works out of the box**:

```bash
pip show apache-beam | grep Requires
# ... google-cloud-storage ...
```

> **A correction you will see in older tutorials.** A lot of material
> on the web says Beam needs `gcsfs` (the `fsspec`-based file system)
> and that you must install `apache-beam[gcp]` or
> `apache-beam[filesystem]` before `gs://` paths work. That was true
> years ago. In Beam 2.77 the `gs` scheme is registered by the base
> package:
>
> ```text
> >>> from apache_beam.io.filesystem import FileSystem
> >>> sorted(fs.scheme() for fs in FileSystem.get_all_subclasses()
> ...        if fs.scheme())
> ['azfs', 'gs', 'hdfs', 's3']
> ```
>
> The `filesystem` extra is still worth installing for `s3fs` and the
> Hadoop file system, and `gcp` is worth installing for the other GCP
> extras. But `gs://` is not gated behind them.

### What a missing file system looks like

The scheme resolution happens in `FileSystems.get_filesystem(path)`,
which scans the registered subclasses for one whose `scheme()` matches
the path's prefix. When nothing matches, you get:

```text
ValueError: Unable to get filesystem from specified path, please use the
correct path or ensure the required dependency is installed, e.g., pip
install apache-beam[gcp]. Path specified: gs://YOUR_BUCKET/orders.csv
```

Note this is a `ValueError`, not an `ImportError` and not a
`BeamIOError` — the failure happens at *resolution* time, before any
network call.

But that is the error for an **unknown scheme**. A *known* scheme with
a bad path fails later, at request time, and the message is different:

```text
apache_beam.io.filesystem.BeamIOError: Match operation failed with
exceptions {'gs://YOUR_BUCKET/orders.csv': BadRequest("GET
https://storage.googleapis.com/storage/v1/b/YOUR_BUCKET/o/orders.csv?fields=name&prettyPrint=false:
Invalid bucket name: 'YOUR_BUCKET'")}
```

Two different errors for two different mistakes, and the second one
also fires when the bucket is real but you have no credentials:

```text
apache_beam.io.filesystem.BeamIOError: Match operation failed with
exceptions {'gs://my-real-bucket/orders.csv': Forbidden("GET
https://storage.googleapis.com/storage/v1/b/my-real-bucket/o/orders.csv?fields=name&prettyPrint=false:
my-user@my-project.iam.gserviceaccount.com does not have storage.objects.list access to the Google Cloud Storage bucket.")}
```

Read the error before you reach for the SDK docs. `Invalid bucket
name` means your *path* is wrong. `does not have ... access` means your
*path* is right and your *credentials* are wrong. Those need different
fixes, and no amount of re-reading the docs will tell you which one you
have.

### Reading from GCS with a wildcard

The idiomatic GCS read uses a **glob**, because a GCS "directory" is
just a prefix:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    orders = p | "ReadOrders" >> beam.io.ReadFromText(
        "gs://YOUR_BUCKET/orders/orders-*.csv"
    )
```

The wildcards that matter:

| Pattern | Matches |
|---|---|
| `gs://bucket/path/*` | every object directly under `path/` |
| `gs://bucket/path/**` | every object under `path/`, recursively |
| `gs://bucket/path/file-*.csv` | objects matching the prefix and suffix |
| `gs://bucket/path/?.csv` | single-character wildcards |

Two practical notes.

**The wildcard is evaluated by the file system, not by Beam.** Beam
hands the pattern to the file system, which lists the prefix and filters. On a
bucket with 100,000 objects under the prefix, that listing is the
dominant cost of the read — it can take seconds and generate many
listings. **Keep the prefix narrow.** `gs://bucket/orders/orders-*` is
fine; `gs://bucket/**` will hurt.

**A pattern that matches nothing fails loudly**, which is what you
want:

```text
OSError: No files found based on the file pattern
```

unless you pass `validate=False`, in which case the failure moves to
run time:

```python
with beam.Pipeline() as p:
    orders = p | "ReadOrders" >> beam.io.ReadFromText(
        "gs://YOUR_BUCKET/orders/orders-*.csv",
        validate=False,
    )
```

`validate=False` is for the case where the files are produced by an
earlier step *in the same pipeline*. Everywhere else, leave validation
on — it turns a silent empty read into an immediate, obvious error.

---

## 🧠 GCS file naming and the shard explosion

### How Beam names output files

When you write to a path, Beam writes a set of *shards* under that
path. The naming is controlled by `shard_name_template`, which defaults
to `"-SSSSS-of-NNNNN"`.

```python
with beam.Pipeline() as p:
    orders | "Write" >> beam.io.WriteToText(
        "gs://YOUR_BUCKET/orders/orders",
        num_shards=10,
    )
```

produces:

```text
gs://YOUR_BUCKET/orders/orders-00000-of-00010
gs://YOUR_BUCKET/orders/orders-00001-of-00010
...
gs://YOUR_BUCKET/orders/orders-00009-of-00010
```

The `of-NNNNN` suffix is not decoration. It is what makes the write
**idempotent under retry**: if a worker dies and the runner retries the
bundle, the shard numbering is deterministic, so the retry writes the
same files rather than creating a second set.

If you set `shard_name_template=""`, you get a single file with the
exact name you asked for — which is what the course's local scripts do
so that `cat out/summary` works.

### The shard explosion

Here is the failure mode, and it is one of the most common ways a
pipeline that works locally becomes a problem in production.

**The scenario.** You run a pipeline daily, over a small amount of
data, and you write each day's output to a path derived from the date:

```python
with beam.Pipeline() as p:
    orders | "Write" >> beam.io.WriteToText(
        f"gs://YOUR_BUCKET/orders/{date_string}",
        num_shards=1,
    )
```

After a year, the bucket has 365 objects. Fine.

Now you change the pipeline to write **per region**, or per customer
tier, or per hour. Say twelve shards per run:

```text
gs://YOUR_BUCKET/orders/2026-01-15/region-EMEA-00000-of-00001
gs://YOUR_BUCKET/orders/2026-01-15/region-AMER-00000-of-00001
...
```

Still fine. Now scale it up: 200 regions × 12 shards × 365 days =
**876,000 objects**. And now scale *that* up — a pipeline that runs
every hour, over 50,000 customers:

```text
50,000 customers × 24 hours × 365 days = 438,000,000 objects
```

**438 million objects in one bucket prefix.** This is the shard
explosion, and it is a well-known failure mode of object stores.

### Why it hurts

**1. Listing cost.** Every read of that prefix has to enumerate the
objects. GCS list operations are priced per 1,000 objects returned and
take time proportional to the number of objects. A pipeline that reads
one day of output pays to enumerate 438 million objects.

**2. Metadata cost.** GCS charges for object metadata storage. At 438
million objects with even a small amount of metadata each, this is a
line item you will find in the bill and not in the forecast.

**3. Per-object latency.** Every object is a separate HTTP request.
There is a per-request cost, so 438 million objects means 438 million
requests even if each one is fast.

**4. The performance cliff.** GCS performance for a single object
degrades as the number of objects in a prefix grows. The empirical
rule is that you should keep prefixes under about 10,000 objects; beyond
that, listing operations slow down noticeably.

**5. Your own tooling slows down.** `gsutil ls gs://bucket/orders/**`
takes minutes. So does a `gcloud storage ls` in a runbook.

### The fix: partition properly, and shard deliberately

There are two separate decisions here, and people conflate them.

**Decision A: how many objects per run.** This is `num_shards`, and
the rule is simple:

> **Aim for 64–256 MB per output object.** Not 10,000 files of 4 KB.
> Not one file of 400 GB.

The reasoning is about parallelism. If you write one file, you have one
task doing all the writing, and it is a bottleneck — no matter how many
workers the pipeline has. If you write 10,000 files, you have 10,000
tasks that each do almost nothing, and the scheduling overhead exceeds
the work.

The way to pick `num_shards` is from the data volume:

```python
# Rough rule of thumb: one shard per ~100 MB of *compressed* output.
NUM_SHARDS = max(1, estimated_output_bytes // (100 * 1024 * 1024))
```

Or let Beam decide, by not specifying it:

```python
with beam.Pipeline() as p:
    orders | "Write" >> beam.io.WriteToText("gs://YOUR_BUCKET/orders/orders")
```

Beam then picks a shard count based on the input size and the
parallelism available. **This is usually the right answer**, and
setting `num_shards` by hand is a decision you should make only when
you have a specific reason.

**Decision B: how the objects are laid out in the bucket.** This is the
one that prevents the explosion. The rule:

> **Partition by a key, not by a value that is unique per record.**

Good partitions:

```text
gs://bucket/orders/dt=2026-01-15/region=EMEA/part-00000-of-00004
```

The prefix `dt=2026-01-15/region=EMEA/` has a bounded number of
objects — 4 shards, per region, per day. You can list it cheaply, read
it cheaply, and delete it cheaply.

Bad partitions:

```text
gs://bucket/orders/customer=c000914/order-00000000.csv
```

One object per customer per order. Unbounded.

### The Hive-style convention

The `key=value/` convention is the Hive partition layout, and it is
worth adopting even outside Hive, because:

- **BigQuery external tables understand it directly.** A BigQuery
  external table over `gs://bucket/orders/*` with
  `source_uris` and hive partitioning enabled will infer `dt` and
  `region` as partition columns and prune them automatically.
- **It is self-describing.** Anyone looking at the bucket can see the
  layout without a README.
- **It makes deletion trivial.** `gsutil -m rm -r
  gs://bucket/orders/dt=2026-01-15/` removes exactly one day's data.

The course's `batch_pipeline.py` does not write to GCS directly, but
the pattern it teaches — one output path per logical dataset — is the
same discipline.

### A concrete before-and-after

The bad version:

```python
with beam.Pipeline() as p:
    orders | "Write" >> beam.io.WriteToText(
        "gs://YOUR_BUCKET/orders/",
        num_shards=1,
    )
```

Every run writes into the same prefix. After 365 runs you have 365
files with names like `orders-00000-of-00001`, and the second run
**overwrites** the first — or, if the shard count differs, leaves a
mess of partially-overlapping files. This is not a shard explosion; it
is a data-loss bug, and it is arguably worse.

The good version:

```python
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.utils.timestamp import Timestamp
import apache_beam as beam

options = PipelineOptions()
date_string = options.view_as(StandardOptions).get_all_options().get("job_name", "run")

with beam.Pipeline(options=options) as p:
    orders = (
        p
        | "ReadOrders" >> beam.io.ReadFromText("gs://YOUR_BUCKET/orders/orders-*.csv")
        | "ParseOrders" >> beam.Map(parse_order)
    )

    orders | "WriteOrders" >> beam.io.WriteToText(
        "gs://YOUR_BUCKET/curated/orders/dt=2026-01-15/",
        num_shards=4,
        shard_name_template="part-SSSSS-of-NNNNN",
    )
```

Each run writes a bounded, dated, partitioned prefix. Re-running
overwrites the same four files, because the shard naming is
deterministic. Downstream consumers read `gs://YOUR_BUCKET/curated/orders/dt=*/`.

---

## 🧠 BigQuery as a sink

### `WriteToBigQuery` in one screen

```python
import apache_beam as beam

SUMMARY_SCHEMA = {
    "fields": [
        {"name": "region", "type": "STRING", "mode": "NULLABLE"},
        {"name": "order_count", "type": "INTEGER", "mode": "NULLABLE"},
        {"name": "revenue_eur", "type": "FLOAT", "mode": "NULLABLE"},
    ],
}

with beam.Pipeline() as p:
    summary = (
        p
        | "Read" >> beam.io.ReadFromText("./sample_data/orders.csv")
        | "Parse" >> beam.Map(parse_order)
        | "Filter" >> beam.Filter(lambda o: o["status"] == "complete")
        | "Key" >> beam.Map(lambda o: (o["region"], o))
        | "Aggregate" >> beam.CombinePerKey(sum)
        | "Flatten" >> beam.Map(lambda kv: {"region": kv[0], "order_count": kv[1]})
    )

    summary | "WriteBigQuery" >> beam.io.WriteToBigQuery(
        "YOUR_PROJECT_ID:YOUR_DATASET.orders_by_region",
        schema=SUMMARY_SCHEMA,
        create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
        write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
    )
```

The course's own `batch_pipeline.py` does the same thing, and it is
worth reading because it shows the parameter set that actually matters:

```python
if bigquery_table:
    rows | "WriteSummaryBigQuery" >> beam.io.WriteToBigQuery(
        bigquery_table,
        write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
        create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
    )
```

Note that `schema` is not passed there. That is correct for that
pipeline: the table is expected to exist already, and the rows are
dicts whose keys match the table's columns. If the table does not
exist, `CREATE_IF_NEEDED` will try to create it — with no schema, it
infers one from the data, which is usually not what you want. **Pass
`schema` explicitly whenever you allow the table to be created.**

### The table reference syntax

`WriteToBigQuery` accepts the table in several forms:

| Form | Meaning |
|---|---|
| `"project.dataset.table"` | fully qualified, dot-separated |
| `"project:dataset.table"` | fully qualified, colon between project and dataset |
| `"dataset.table"` | dataset in the current project |
| `("dataset", "table")` via `dataset=` and `table=` | explicit |

The colon form — `project:dataset.table` — is the BigQuery CLI
convention and it is what the Beam SDK's own documentation uses:

```text
table='project_name1:dataset_2.query_events_table'
```

It is also the form to use with **date-partitioned tables**, where the
partition suffix is appended with a `$`:

```text
YOUR_PROJECT_ID:YOUR_DATASET.orders$20260115
```

Beam's table parser accepts this. The relevant source is
`apache_beam.io.gcp.bigquery_tools.parse_table_reference`, whose
docstring says:

```text
The ID must contain only letters (a-z, A-Z), numbers (0-9), connectors
(-_). If dataset argument is None then the table argument must contain
the entire table reference: 'DATASET.TABLE' or 'PROJECT:DATASET.TABLE'.
... Additionally, for date partitioned tables, appending '$YYYYmmdd' to
the table name is supported, e.g. 'DATASET.TABLE$YYYYmmdd'.
```

Verified behaviour:

```text
'proj:ds.tbl'               -> proj ds tbl
'ds.tbl'                    -> None ds tbl
'proj:ds.tbl$20260115'      -> proj ds tbl$20260115
'ds.tbl$20260115'           -> None ds tbl$20260115
'proj:ds.tbl$shard_1'       -> proj ds tbl$shard_1
```

> **The project ID must be lower-case.** The parser's project pattern
> is `([a-z0-9.-]+:)?[a-z][a-z0-9-]*[a-z0-9]` — lower-case only,
> because that is what GCP actually issues. An upper-case placeholder
> does not parse:
>
> ```text
> ValueError: Expected a table reference (PROJECT:DATASET.TABLE or
> DATASET.TABLE) instead of YOUR_PROJECT_ID:YOUR_DATASET.orders.
> ```
>
> The dataset and table names are case-*sensitive* in the pattern
> (`\w` and a Unicode class), so `MyDataset.Orders` is fine — it is
> specifically the project segment that is lower-cased.
```

The `$` suffix is part of the *table name* as far as Beam is concerned.
BigQuery interprets it as a **date partition decorator**, and you can
also use the decorator form for ingestion-time partitioning:

```text
YOUR_PROJECT_ID:YOUR_DATASET.orders$20260115
```

This routes rows into the `20260115` partition of an ingestion-time
partitioned table. It is a useful trick for a backfill: you write one
run per partition date, and each run's data lands in the right place.

Note the distinction from `additional_bq_parameters`, which is how you
declare the partitioning *on the table itself* when creating it.

### `schema`

The `schema` parameter has four accepted forms:

```python
# 1. A dictionary, in the BigQuery TableSchema shape.
schema = {
    "fields": [
        {"name": "region", "type": "STRING", "mode": "NULLABLE"},
        {"name": "order_count", "type": "INTEGER", "mode": "NULLABLE"},
    ],
}

# 2. A JSON string of the same thing.
schema = '{"fields": [{"name": "region", "type": "STRING", "mode": "NULLABLE"}]}'

# 3. A compact comma-separated string. Simple types only.
schema = "region:STRING,order_count:INTEGER,revenue_eur:FLOAT"

# 4. A callable, evaluated per element at run time.
schema = lambda table: SCHEMA_FOR_TABLE[table]
```

Form 3 is the quickest to write and the easiest to get subtly wrong,
because it does not support nested fields, repeated fields, or an
explicit mode. **Use form 1 for anything you will maintain.**

The schema is only used when the table has to be **created**. If the
table already exists, BigQuery's own schema is used and your `schema`
argument is ignored for that purpose — the rows must match the
*existing* table's columns.

### `write_disposition`

What to do when the table already has data.

| Value | Behaviour | Use when |
|---|---|---|
| `WRITE_APPEND` | add the new rows to the existing rows | **the default**, and usually right |
| `WRITE_TRUNCATE` | delete everything, then write | a full refresh of a derived table |
| `WRITE_EMPTY` | write only if the table is empty; otherwise fail | a "seed once, never overwrite" table |

```python
from apache_beam.io.gcp.bigquery import BigQueryDisposition

beam.io.WriteToBigQuery(
    "YOUR_PROJECT_ID:YOUR_DATASET.orders_by_region",
    write_disposition=BigQueryDisposition.WRITE_APPEND,
)
```

`WRITE_APPEND` is the default, and it is the correct default for an
incremental pipeline. But it is worth being deliberate about it,
because **`WRITE_APPEND` is how you double-count a re-run.** If your
pipeline reads a date range and someone re-runs it for the same range,
`WRITE_APPEND` adds the same rows again.

There are three ways to handle that, in increasing order of
sophistication:

1. **Partitioned table + partition decorator.** Write to
   `dataset.orders$20260115` with `WRITE_APPEND`. Re-running the same
   date appends to the same partition — still a duplicate. Not a fix.
2. **`WRITE_TRUNCATE` on a partitioned table.** This truncates only the
   partition the write targets. **This is the correct idempotent
   pattern** for a derived, partitioned table: re-running the same
   partition replaces it wholesale.
3. **`ignore_insert_ids=True`** with a deterministic insert ID derived
   from the row's identity. BigQuery then de-duplicates. This is what
   you want for at-least-once streaming sources.

The rule of thumb:

> **`WRITE_TRUNCATE` on a partitioned table is idempotent.
> `WRITE_APPEND` is not. If your pipeline can be re-run for the same
> partition, use `WRITE_TRUNCATE` and partition the table.**

There is one important restriction: **`WRITE_TRUNCATE` cannot be used
in a streaming pipeline.** The Beam source says so explicitly:

```text
For streaming pipelines WriteTruncate can not be used.
```

### `create_disposition`

What to do when the table does not exist.

| Value | Behaviour |
|---|---|
| `CREATE_IF_NEEDED` | create the table if it is missing (the default) |
| `CREATE_NEVER` | fail if the table is missing |

```python
beam.io.WriteToBigQuery(
    "YOUR_PROJECT_ID:YOUR_DATASET.orders_by_region",
    create_disposition=beam.io.BigQueryDisposition.CREATE_NEVER,
)
```

`CREATE_IF_NEEDED` is the default and is convenient. It has two sharp
edges:

**It needs a schema.** With no `schema` argument, Beam infers one from
the data, which means a table created by an automated run may have
different column types from what you intended. Always pass `schema` if
you allow creation.

**It needs the right IAM.** Creating a table needs
`bigquery.tables.create` on the dataset, which is a different
permission from `bigquery.tables.updateData`. A service account with
only the data-write permission will fail at table creation with
something like:

```text
google.api_core.exceptions.Forbidden: 403 Permission denied while
getting Drive credentials.
```

or, more precisely:

```text
Access Denied: Table YOUR_PROJECT_ID:YOUR_DATASET.orders_by_region:
 User does not have permission to create table.
```

`CREATE_NEVER` is the right choice in production when the table is
managed by a schema-migration tool (terraform, a dbt project, a
BigLake managed table). In that setup, the pipeline should fail loudly
if the table is missing, because the schema is owned elsewhere.

### `additional_bq_parameters`

This is the parameter name, and it is worth stating precisely because
the wrong name is a common copy-paste error:

> **`additional_bq_parameters`**. Not `additional_configuration`. Not
> `additional_bq_config`. The parameter does not exist under any other
> name in Beam 2.77.

The full signature is:

```python
WriteToBigQuery(
    table,
    dataset=None,
    project=None,
    schema=None,
    create_disposition='CREATE_IF_NEEDED',
    write_disposition='WRITE_APPEND',
    kms_key=None,
    batch_size=None,
    max_file_size=None,
    max_partition_size=None,
    max_files_per_bundle=None,
    test_client=None,
    custom_gcs_temp_location=None,
    method=None,
    insert_retry_strategy=None,
    additional_bq_parameters=None,
    table_side_inputs=None,
    schema_side_inputs=None,
    triggering_frequency=None,
    use_at_least_once=False,
    validate=True,
    temp_file_format=None,
    ignore_insert_ids=False,
    with_auto_sharding=False,
    num_storage_api_streams=0,
    ignore_unknown_columns=False,
    load_job_project_id=None,
    max_retries=10000,
    max_insert_payload_size=9437184,
    num_streaming_keys=500,
    use_cdc_writes=False,
    primary_key=None,
    expansion_service=None,
    big_lake_configuration=None,
    type_overrides=None,
    schema_update_options=None,
)
```

`additional_bq_parameters` is a dictionary passed straight through to
the BigQuery API when the table is **created**. The Beam SDK's own
documentation gives the canonical example:

```text
When creating a new BigQuery table, there are a number of extra
parameters that one may need to specify. For example, clustering,
partitioning, data encoding, etc. It is possible to provide these
additional parameters by passing a Python dictionary as
`additional_bq_parameters` to the transform.
```

```python
additional_bq_parameters = {
    "timePartitioning": {"type": "DAY"},
    "clustering": {"fields": ["country"]},
}

with beam.Pipeline() as p:
    elements = p | "Create" >> beam.Create([
        {"country": "mexico", "timestamp": "12:34:56", "query": "acapulco"},
        {"country": "canada", "timestamp": "12:34:57", "query": "influenza"},
    ])

    elements | "WriteBigQuery" >> beam.io.WriteToBigQuery(
        table="YOUR_PROJECT_ID:YOUR_DATASET.query_events",
        additional_bq_parameters=additional_bq_parameters,
    )
```

What you can put in it is whatever the BigQuery `tables.insert` API
accepts. The ones that matter in practice:

| Key | Effect |
|---|---|
| `timePartitioning` | `{"type": "DAY"}` or `{"type": "HOUR"}` or `{"field": "ts"}` |
| `rangePartitioning` | integer-range partitioning |
| `clustering` | `{"fields": ["country", "region"]}` |
| `description` | free-text table description |
| `labels` | `{"team": "growth"}` — labels, not tags |
| `requirePartitionFilter` | `True` to require a partition filter on every query |

`timePartitioning` and `clustering` are the two that change how the
table behaves for downstream users, and they are worth setting at
creation time — BigQuery will not let you add clustering to an existing
table, and adding partitioning later is a full table rewrite.

The parameter can also be a **callable**, evaluated per element, in
which case each element can target a differently-configured table:

```python
beam.io.WriteToBigQuery(
    table=my_table_callable,
    additional_bq_parameters=my_params_callable,
)
```

### The `with_sharding` misconception

This is the parameter people misremember most often, and the
misremembering causes real incidents.

> **There is no `with_sharding` parameter on `WriteToBigQuery` in Beam
> 2.77.**

The parameters that exist are `with_auto_sharding` and
`num_storage_api_streams`. Passing `with_sharding=True` raises:

```text
TypeError: WriteToBigQuery.__init__() got an unexpected keyword argument 'with_sharding'
```

And `with_auto_sharding` does **not** mean what people think it means
either.

### What sharding actually splits on

**Sharding in the BigQuery write path splits on FILE SIZE, not on row
count.**

This is verifiable in the Beam source. The batch `FILE_LOADS` path
rolls over to a new file when the writer's byte count crosses a
threshold:

```python
writer.write(row)

file_size = writer.tell()
if file_size > self.max_file_size:
    writer.close()
    self._destination_to_file_writer.pop(destination)
    yield pvalue.TaggedOutput(
        WriteRecordsToFile.WRITTEN_FILE_TAG,
        (destination, (file_path, file_size)))
```

`writer.tell()` is the number of **bytes** written. `self.max_file_size`
is a byte threshold. There is no row counter anywhere in the logic.

And the `max_file_size` parameter is documented in those terms:

```text
max_file_size (int): The maximum size for a file to be written and then
loaded into BigQuery. The default value is 4TB, which is 80% of the
limit of 5TB for BigQuery to load any file.
```

So:

| | What people think | What it actually is |
|---|---|---|
| Sharding trigger | N rows per file | **file size in bytes** |
| `max_file_size` unit | rows | **bytes** (default 4 TB) |
| `max_partition_size` unit | rows | **bytes** (default 15 TB) |
| `max_files_per_bundle` unit | rows | **files** (default 20) |
| `with_auto_sharding` | "split by row count" | groups by **table reference**, batching by **byte size** |

The streaming path (`STREAMING_INSERTS`) is different again, and it is
where `with_auto_sharding` applies. There, the sink groups rows by
*destination table* and then batches them:

```python
if not self.with_auto_sharding:
    tagged_data = (
        tagged_data
        | 'WithFixedSharding' >> beam.Map(_add_random_shard)
        | 'CommitInsertIds' >> ReshufflePerKey()
        | 'DropShard' >> beam.Map(lambda kv: (kv[0][0], kv[1])))
else:
    tagged_data = (
        tagged_data
        | 'WithAutoSharding' >> beam.GroupIntoBatches.WithShardedKey(
            (self.batch_size or BigQueryWriteFn.DEFAULT_MAX_BUFFERED_ROWS),
            self.triggering_frequency or
            DEFAULT_BATCH_BUFFERING_DURATION_LIMIT_SEC)
        | 'DropShardKey' >> beam.Map(lambda kv: (kv[0].key, kv[1])))
```

`with_auto_sharding=True` uses `GroupIntoBatches.WithShardedKey`, which
shards by **key** (the table reference) and then batches — and the
batch size is a number of *rows* (`batch_size`, default 500 for the
Storage Write API). So in the streaming path, the batching is by row
count; in the batch file-load path, the file splitting is by byte size.

Two different mechanisms, two different units. That is why "sharding
splits on row count" is a half-truth that produces the wrong
conclusion in the batch case.

**What this means operationally:**

- If you want to control how many files the batch load produces, set
  `max_file_size` in **bytes**. `max_file_size=100 * 1024 * 1024`
  means 100 MB files.
- If you want to control the insert batch size in streaming, set
  `batch_size` in **rows**.
- If you set neither, you get one 4 TB file per destination for batch
  loads (which is fine, because BigQuery's load job is parallel and the
  job is what costs money, not the file).

### `with_auto_sharding`, properly explained

For the streaming path, `with_auto_sharding=True` groups rows by their
destination table so that a single insert stream per table is
maintained, instead of a random shard per row that has to be merged
later. It reduces insert contention and improves throughput.

The cost is that rows for the same table must be grouped, which means
a shuffle. For a pipeline writing to one table, it buys very little.
For a pipeline writing to many tables with a per-row destination (the
"dynamic table" pattern), it matters a lot.

---

## 🧠 BigQuery as a source

### `beam.io.ReadFromBigQuery`

```python
import apache_beam as beam

with beam.Pipeline() as p:
    rows = p | "ReadBigQuery" >> beam.io.ReadFromBigQuery(
        table="YOUR_PROJECT_ID:YOUR_DATASET.orders",
    )
```

And with a query:

```python
with beam.Pipeline() as p:
    rows = p | "ReadBigQuery" >> beam.io.ReadFromBigQuery(
        query="SELECT region, COUNT(*) AS n FROM `YOUR_PROJECT_ID.YOUR_DATASET.orders` GROUP BY region",
    )
```

The transform has two methods, and this is the part worth knowing:

| Method | How it works | When to use it |
|---|---|---|
| `EXPORT` (the default) | Runs a BigQuery **export job** to GCS, then reads the exported Avro files | bulk reads; the export is free |
| `DIRECT_READ` | Reads directly from BigQuery Storage via the Read API | streaming, or when the export is too slow |

`EXPORT` is the default, and it is worth knowing *why* it is the
default: BigQuery export jobs are **free**. You are billed for the
storage read of the exported files and for the compute, but not for the
export itself. That makes a full-table export a cheap way to get data
into a Beam pipeline.

The downside of `EXPORT` is latency: it materialises the whole result
set to GCS first, so a query that returns one row still exports
everything BigQuery decided to materialise.

`DIRECT_READ` avoids that, and supports `use_native_datetime=True`,
which returns `DATETIME` columns as Python `datetime` objects rather
than strings.

There is also an `output_type` parameter:

```text
output_type (str): By default, this source yields Python dictionaries
(`PYTHON_DICT`). There is experimental support for producing a
PCollection with a schema and yielding Beam Rows via the option
`BEAM_ROW`.
```

And `query_output_schema`, which is required when `output_type` is
`BEAM_ROW` and you are using a query — because the schema of a query
result cannot be derived from a table.

### Why a BigQuery source is usually the wrong choice

This is the part of the chapter that is worth arguing for, because it
is the advice most often ignored.

**BigQuery can do the whole transform in SQL.** If your Beam pipeline
reads from BigQuery and writes back to BigQuery, and the transform
between them is expressible in SQL, then you should not write a Beam
pipeline. You should write a BigQuery job.

```sql
SELECT region, COUNT(*) AS order_count, SUM(amount * rate) AS revenue_eur
FROM `YOUR_PROJECT_ID.YOUR_DATASET.orders`
WHERE status = 'complete'
GROUP BY region
```

BigQuery will run this on its own elastic compute, with no cluster to
provision, no worker startup, no shuffle infrastructure, and at a cost
per scanned byte that is usually an order of magnitude below a
Dataflow job. It will also be easier to read, easier to test, and
easier for the next person to reason about.

**The reasons to use Beam as a BigQuery reader are narrow but real:**

1. **The transform is not expressible in SQL.** Beam's Python SDK has
   transforms that SQL does not: complex stateful processing, custom
   windowing with session windows and custom triggers, per-record
   model inference, joining against a model that lives in a file.

2. **You need to join BigQuery with non-BigQuery data at scale.** A
   `beam.pvalue.AsDict` side input, a GCS file, a Pub/Sub stream.
   BigQuery can `EXTERNAL_QUERY` against GCS, but the ergonomics are
   much worse and the cost model is less predictable.

3. **You want one pipeline that runs in both batch and streaming mode.**
   This is Beam's actual thesis, and it is the strongest argument for
   it. The same Beam code that reads a bounded BigQuery table in batch
   mode reads a Pub/Sub stream in streaming mode.

4. **You want to reuse a transform library.** A `DoFn` you have already
   written and tested does not need to be reimplemented in SQL.

5. **You need the Dataflow-specific operational surface** — autoscaling
   against a streaming backlog, per-worker metrics, integration with the
   rest of your Dataflow estate, templating.

### When writing to BigQuery from Beam IS right

The mirror image, and the more common case:

1. **The source is not BigQuery.** GCS files, Pub/Sub, Kafka (off
   Dataflow), an API. This is the classic "land from GCS to BigQuery"
   pipeline, and it is the one the course's `batch_pipeline.py` is
   shaped like.

2. **The transform is too complex for SQL.** Custom windowing, ML
   inference, multi-stage joins with side inputs.

3. **You need a streaming write.** BigQuery's own Streaming Insert API
   is rate-limited (the legacy path is 1,000 rows per second per table
   per project). Dataflow's `WriteToBigQuery` uses the **Storage Write
   API**, which is not subject to that limit and is the recommended
   path for high-throughput streaming.

4. **You need exactly-once-ish semantics.** With
   `ignore_insert_ids=False` (the default) and a deterministic
   pipeline, retries do not duplicate rows.

5. **You want the write to be part of a larger graph** — one pipeline
   that writes to BigQuery *and* to GCS *and* to Pub/Sub, from one
   read. This is exactly the multi-sink pattern from chapter 3.2, and
   it is a genuinely strong reason to use Beam: BigQuery alone cannot
   fan out to three destinations from one scan without three queries.

6. **You want the data in a table you control the schema of.** Beam
   can write Parquet to GCS with an explicit `pyarrow` schema and
   create a BigQuery table over it, and it can do both in one job.

---

## 🛠️ Hands-On: GCS Paths and a Guarded BigQuery Write

### Setup

```bash
cd data-engineering/data-Course/google/Dataflow
source .venv/bin/activate
python resources/sample_data.py --output-dir ./sample_data
```

This chapter's exercises all run locally. The GCS paths are shown as
strings; the BigQuery path is guarded by an environment check, so the
script runs to completion with no credentials and no bill.

### Step 1 — the same pipeline, two paths

Create `work/paths_demo.py`:

```python
"""Show that the only difference between local and GCS is the path."""

import apache_beam as beam


def build(pipeline, path: str):
    """Build the summary pipeline against an arbitrary path."""
    return (
        pipeline
        | "ReadOrders" >> beam.io.ReadFromText(path)
        | "SkipHeader" >> beam.Filter(lambda line: not line.startswith("order_id"))
        | "KeyByRegion" >> beam.Map(lambda line: (line.split(",")[3], 1))
        | "CountByRegion" >> beam.combiners.Count.PerKey()
        | "Format" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]}")
    )


with beam.Pipeline() as p:
    local = build(p, "./sample_data/orders.csv")
    local | "WriteLocal" >> beam.io.WriteToText(
        "./out/paths_local", num_shards=1, shard_name_template=""
    )

print("The pipeline above and the one below differ only in the path.")
print("Swap './sample_data/orders.csv' for 'gs://YOUR_BUCKET/orders.csv'")
print("and add --runner=DataflowRunner to run it in the cloud.")
```

Run it:

```bash
python work/paths_demo.py
cat out/paths_local
```

Expected:

```text
LATAM,1265
APAC,1211
AMER,1284
EMEA,1240
```

The counts come from `resources/sample_data.py`, which is seeded, so
they are stable across runs. The order varies, because Beam makes no
ordering guarantee.

### Step 2 — prove the file system is selected by the path

Create `work/scheme_demo.py`:

```python
"""Show that Beam resolves the file system from the path scheme."""

from apache_beam.io.filesystem import FileSystem
from apache_beam.io.filesystems import FileSystems

print("registered file systems:")
for fs in sorted(FileSystem.get_all_subclasses(), key=lambda f: (f.scheme() or "")):
    scheme = fs.scheme() or "<local>"
    print(f"  {scheme:8s} {fs.__module__}.{fs.__name__}")


def try_glob(pattern: str) -> str:
    """List the files matching a pattern, or report the failure."""
    try:
        matches = FileSystems.match([pattern], [20])
        return f"{len(matches)} match(es)"
    except Exception as exc:
        return f"{type(exc).__name__}: {str(exc)[:120]}"


print()
print("local glob   :", try_glob("./sample_data/orders.csv"))
print("gcs glob     :", try_glob("gs://YOUR_BUCKET/orders.csv"))
```

Run it:

```bash
python work/scheme_demo.py
```

Expected on a machine with `apache-beam[gcp]` installed:

```text
registered file systems:
  <local>  apache_beam.io.localfilesystem.LocalFileSystem
  azfs     apache_beam.io.azure.blobstoragefilesystem.BlobStorageFileSystem
  gs       apache_beam.io.gcp.gcsfilesystem.GCSFileSystem
  hdfs     apache_beam.io.hadoopfilesystem.HadoopFileSystem
  s3       apache_beam.io.aws.s3filesystem.S3FileSystem

local glob   : 1 match(es)
gcs glob     : BeamIOError: Match operation failed with exceptions {'gs://YOUR_BUCKET/orders.csv': BadRequest("GET https://storage.googleapis.com/st...
```

With only the base `apache-beam` installed, the `gs` line is absent
and the GCS glob fails earlier, at resolution time:

```text
ValueError: Unable to get filesystem from specified path, please use the
correct path or ensure the required dependency is installed, e.g., pip
install apache-beam[gcp]. Path specified: gs://YOUR_BUCKET/orders.csv
```

Either way, the point is the first block of output: Beam has a
*registry* of file systems, and the path's scheme selects one. There is
no `GcsFileSystem` transform to reach for.

> **A note on the API.** There is no `apache_beam.io.filesystem.FILE_SYSTEMS`
> constant. The registry is the class hierarchy: `FileSystem` has
> subclasses, and `FileSystem.get_all_subclasses()` lists them. The
> `FileSystems` class (plural, in `apache_beam.io.filesystems`) is the
> static *facade* you call to do I/O — `FileSystems.match(...)`,
> `FileSystems.open(...)`. Two similarly named classes, two different
> jobs. `LocalFileSystem.scheme()` returns `None`, which is why it
> prints as `<local>` above; an unset scheme means "the local disk".

### Step 3 — the shard explosion, counted

This is the exercise that makes the shard-explosion problem concrete.
Create `work/shard_explosion.py`:

```python
"""Show how quickly a per-key output layout becomes a shard explosion."""

from datetime import date, timedelta


def simulate(
    *,
    records_per_day: int,
    keys_per_record: int,
    shards_per_key: int,
    days: int,
) -> None:
    """Compute the object count for a partitioned output layout."""
    objects = records_per_day * keys_per_record * shards_per_key * days
    print(f"  days:                {days:>12,}")
    print(f"  records per day:     {records_per_day:>12,}")
    print(f"  keys per record:     {keys_per_record:>12,}")
    print(f"  shards per key:      {shards_per_key:>12,}")
    print(f"  objects in the bucket:{objects:>12,}")
    print(f"  per prefix (1 day):  {records_per_day * keys_per_record * shards_per_key:>12,}")


print("Good layout — one date partition, 50 regions, 4 shards each:")
simulate(
    records_per_day=50,
    keys_per_record=1,
    shards_per_key=4,
    days=365,
)

print()
print("Bad layout — one output object per customer:")
simulate(
    records_per_day=50_000,
    keys_per_record=1,
    shards_per_key=1,
    days=365,
)

print()
print("Good layout — 30 days retained, one file per day:")
simulate(
    records_per_day=1,
    keys_per_record=1,
    shards_per_key=1,
    days=30,
)
```

Run it:

```bash
python work/shard_explosion.py
```

Expected:

```text
Good layout — one date partition, 50 regions, 4 shards each:
  days:                       365
  records per day:             50
  keys per record:              1
  shards per key:               4
  objects in the bucket:   73,000
  per prefix (1 day):         200

Bad layout — one output object per customer:
  days:                       365
  records per day:         50,000
  keys per record:              1
  shards per key:               1
  objects in the bucket:18,250,000
  per prefix (1 day):      50,000

Good layout — 30 days retained, one file per day:
  days:                        30
  records per day:              1
  keys per record:              1
  shards per key:               1
  objects in the bucket:       30
  per prefix (1 day):           1
```

The middle case is the shard explosion: 18 million objects, and 50,000
in a single day prefix — well past the point where listing operations
start to hurt.

The fix, in one line of code, is to change the *layout*, not the shard
count:

```text
gs://bucket/orders/dt=2026-01-15/region=EMEA/part-00000-of-00004
```

### Step 4 — inspect the BigQuery dispositions that exist

Create `work/bq_dispositions.py`:

```python
"""List the BigQuery dispositions and show how the table name is parsed."""

import apache_beam as beam
from apache_beam.io.gcp.bigquery_tools import parse_table_reference

print("write dispositions:")
for name in ("WRITE_APPEND", "WRITE_TRUNCATE", "WRITE_EMPTY"):
    print(f"  {name:16s} = {getattr(beam.io.BigQueryDisposition, name)}")

print()
print("create dispositions:")
for name in ("CREATE_IF_NEEDED", "CREATE_NEVER"):
    print(f"  {name:16s} = {getattr(beam.io.BigQueryDisposition, name)}")

print()
print("table reference parsing:")
for reference in (
    "my-project:my_dataset.orders",
    "my_dataset.orders",
    "my-project:my_dataset.orders$20260115",
    "my-project:my_dataset.orders$shard_1",
):
    parsed = parse_table_reference(reference)
    print(
        f"  {reference:48s} -> project={parsed.projectId} "
        f"dataset={parsed.datasetId} table={parsed.tableId}"
    )
```

Run it:

```bash
python work/bq_dispositions.py
```

Expected:

```text
write dispositions:
  WRITE_APPEND     = WRITE_APPEND
  WRITE_TRUNCATE   = WRITE_TRUNCATE
  WRITE_EMPTY      = WRITE_EMPTY

create dispositions:
  CREATE_IF_NEEDED = CREATE_IF_NEEDED
  CREATE_NEVER     = CREATE_NEVER

table reference parsing:
  my-project:my_dataset.orders                 -> project=my-project dataset=my_dataset table=orders
  my_dataset.orders                            -> project=None dataset=my_dataset table=orders
  my-project:my_dataset.orders$20260115        -> project=my-project dataset=my_dataset table=orders$20260115
  my-project:my_dataset.orders$shard_1         -> project=my-project dataset=my_dataset table=orders$shard_1
```

The `$` suffix survives parsing as part of the table name, which is
exactly what BigQuery's partition decorator expects.

Note the lower-case project IDs. Beam's project pattern is
`([a-z0-9.-]+:)?[a-z][a-z0-9-]*[a-z0-9]` — **lowercase only**, because
that is what GCP actually issues. An upper-case placeholder like
`YOUR_PROJECT_ID` will not parse:

```text
ValueError: Expected a table reference (PROJECT:DATASET.TABLE or
DATASET.TABLE) instead of YOUR_PROJECT_ID:YOUR_DATASET.orders.
```

So when you substitute your own project ID, keep it lower-case. The
`YOUR_PROJECT_ID` placeholder in the rest of this chapter is a
documentation convention, not a string you can paste into a table
reference.

### Step 5 — check the parameter names against the SDK

The most reliable way to avoid the `additional_configuration` typo is
to read the signature. Create `work/bq_signature.py`:

```python
"""Print the real WriteToBigQuery signature and check the key names."""

import inspect

import apache_beam.io.gcp.bigquery as bigquery

signature = inspect.signature(bigquery.WriteToBigQuery.__init__)
parameters = list(signature.parameters)

print("WriteToBigQuery parameters:")
for name in parameters:
    print(f"  {name}")

print()
for name in (
    "additional_bq_parameters",
    "with_auto_sharding",
    "max_file_size",
    "batch_size",
):
    print(f"{name:26s} present={name in parameters}")

print()
for name in ("with_sharding", "additional_configuration"):
    print(f"{name:26s} present={name in parameters}")
```

Run it:

```bash
python work/bq_signature.py
```

Expected:

```text
WriteToBigQuery parameters:
  self
  table
  dataset
  project
  schema
  create_disposition
  write_disposition
  kms_key
  batch_size
  max_file_size
  max_partition_size
  max_files_per_bundle
  test_client
  custom_gcs_temp_location
  method
  insert_retry_strategy
  additional_bq_parameters
  table_side_inputs
  schema_side_inputs
  triggering_frequency
  use_at_least_once
  validate
  temp_file_format
  ignore_insert_ids
  with_auto_sharding
  num_storage_api_streams
  ignore_unknown_columns
  load_job_project_id
  max_retries
  max_insert_payload_size
  num_streaming_keys
  use_cdc_writes
  primary_key
  expansion_service
  big_lake_configuration
  type_overrides
  schema_update_options

additional_bq_parameters    present=True
with_auto_sharding          present=True
max_file_size               present=True
batch_size                  present=True

with_sharding               present=False
additional_configuration    present=False
```

The last two lines are the point of the exercise. `with_sharding` does
not exist, and `additional_configuration` does not exist.

### Step 6 — the guarded BigQuery write

This is the hands-on the chapter has been building towards: a pipeline
that writes to BigQuery, but only when you tell it to. Create
`work/bigquery_write.py`:

```python
"""Write the revenue summary to BigQuery, guarded by an environment check.

The pipeline always writes the summary to a local file. The BigQuery
sink is only added when BIGQUERY_PROJECT and BIGQUERY_DATASET are set,
so the script runs to completion with no credentials and no bill.

Run it locally (no BigQuery):
    python work/bigquery_write.py

Run it against BigQuery:
    export BIGQUERY_PROJECT=YOUR_PROJECT_ID
    export BIGQUERY_DATASET=your_dataset
    export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
    python work/bigquery_write.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "project"))

import apache_beam as beam  # noqa: E402
from apache_beam.options.pipeline_options import PipelineOptions  # noqa: E402

from transforms import ParseOrderFn, RevenueByRegionFn, to_summary_row  # noqa: E402

SUMMARY_SCHEMA = {
    "fields": [
        {"name": "region", "type": "STRING", "mode": "NULLABLE"},
        {"name": "order_count", "type": "INTEGER", "mode": "NULLABLE"},
        {"name": "revenue_eur", "type": "FLOAT", "mode": "NULLABLE"},
    ],
}

ADDITIONAL_BQ_PARAMETERS = {
    "description": "Per-region revenue summary, written by Apache Beam.",
    "labels": {"course": "dataflow"},
}


def build(pipeline, *, input_path: str, output_path: str, bq_table: str | None):
    """Build the summary pipeline, optionally with a BigQuery sink."""
    orders = (
        pipeline
        | "ReadOrders" >> beam.io.ReadFromText(input_path)
        | "ParseOrders" >> beam.ParDo(ParseOrderFn())
        | "KeepCompleted" >> beam.Filter(lambda order: order["status"] == "complete")
        | "KeyByRegion" >> beam.Map(lambda order: (order["region"], order))
        | "RevenueByRegion" >> beam.CombinePerKey(RevenueByRegionFn())
        | "ToRow" >> beam.Map(to_summary_row)
    )

    orders | "FormatCsv" >> beam.Map(
        lambda row: f"{row['region']},{row['order_count']},{row['revenue_eur']}"
    ) | "WriteCsv" >> beam.io.WriteToText(
        output_path,
        header="region,order_count,revenue_eur",
        num_shards=1,
        shard_name_template="",
    )

    if bq_table:
        orders | "WriteBigQuery" >> beam.io.WriteToBigQuery(
            bq_table,
            schema=SUMMARY_SCHEMA,
            write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            additional_bq_parameters=ADDITIONAL_BQ_PARAMETERS,
            custom_gcs_temp_location=os.environ.get(
                "BIGQUERY_TEMP_LOCATION", "gs://YOUR_BUCKET/temp"
            ),
        )


def main() -> int:
    """Run the pipeline, with BigQuery only when it is configured."""
    project = os.environ.get("BIGQUERY_PROJECT")
    dataset = os.environ.get("BIGQUERY_DATASET")
    table = os.environ.get("BIGQUERY_TABLE", "orders_by_region")

    bq_table = None
    if project and dataset:
        bq_table = f"{project}:{dataset}.{table}"
        print(f"BigQuery sink enabled: {bq_table}")
    else:
        print("BigQuery sink disabled (set BIGQUERY_PROJECT and BIGQUERY_DATASET).")

    options = PipelineOptions()
    with beam.Pipeline(options=options) as pipeline:
        build(
            pipeline,
            input_path="./sample_data/orders.csv",
            output_path="./out/bq_summary",
            bq_table=bq_table,
        )

    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Run it:

```bash
python work/bigquery_write.py
cat out/bq_summary
```

Expected:

```text
BigQuery sink disabled (set BIGQUERY_PROJECT and BIGQUERY_DATASET).
done
region,order_count,revenue_eur
AMER,318,113592.19
APAC,285,108194.92
EMEA,322,118423.22
LATAM,320,110646.18
```

The local write happens unconditionally; the BigQuery write is skipped
because the environment variables are not set. The script exits 0
either way, which is what makes it safe to run in CI.

To enable the BigQuery sink:

```bash
export BIGQUERY_PROJECT=YOUR_PROJECT_ID
export BIGQUERY_DATASET=your_dataset
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
python work/bigquery_write.py
```

You will need `bigquery.tables.create` on the dataset (for
`CREATE_IF_NEEDED`), `bigquery.tables.updateData` on the table (for the
write), and `storage.objects.*` on the temp bucket, because the batch
write path stages files to GCS before loading them.

Note the `custom_gcs_temp_location` parameter in the sink above. It is
not optional decoration — see the next step.

### Step 7 — why the BigQuery sink needs a GCS bucket

The default BigQuery write method is `FILE_LOADS`: Beam writes your
rows to files in Cloud Storage, then starts a BigQuery *load job* that
reads those files. There is no other route, so **the sink needs a GCS
location even when it has nothing else to do with GCS**.

If you do not supply one, the pipeline fails at runtime — after the
read and the transform have already done their work:

```text
ValueError: Invalid GCS location: None.
Writing to BigQuery with FILE_LOADS method requires a GCS location to be
provided to write files to be loaded into BigQuery. Please provide a GCS
bucket through custom_gcs_temp_location in the constructor of
WriteToBigQuery or the fallback option --temp_location, or pass
method="STREAMING_INSERTS" to WriteToBigQuery.
[while running 'WriteBigQuery/BigQueryBatchFileLoads/GenerateFilePrefix']
```

Read that message carefully. It names **three** ways out, and they are
not equivalent:

| Fix | How | When |
|---|---|---|
| `custom_gcs_temp_location="gs://bucket/temp"` | constructor argument | when the sink is created in code |
| `--temp_location gs://bucket/temp` | runner flag | on the Dataflow runner, where the flag is the natural place for it |
| `method="STREAMING_INSERTS"` | constructor argument | only if you want the streaming path — different semantics, different cost |

On the Dataflow runner, `--temp_location` is required anyway for
anything non-trivial, so the flag usually covers it. In a local or unit
test, the constructor argument is the one you reach for.

#### Seeing the check without any credentials

The validation happens in a pure function that Beam calls *before* it
writes anything, so you can exercise it directly — no credentials, no
bucket, no network. Create `work/bq_temp_location.py`:

```python
"""Show the GCS-location check that the BigQuery FILE_LOADS path performs.

This calls Beam's own prefix generator directly, so it needs no
credentials, no bucket and no network.
"""

from apache_beam.io.gcp.bigquery_file_loads import file_prefix_generator


class Stub:
    """A value provider that returns a fixed value.

    `StaticValueProvider(str, None)` does not work here: it coerces the
    value to the string 'None', which is truthy, so the sink would
    prefer it over `temp_location` and never fall back.
    """

    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


def check(temp_location, pipeline_gcs_location=None):
    """Return the prefix Beam would use, or the validation error."""
    generator = file_prefix_generator(
        with_validation=True,
        pipeline_gcs_location=Stub(pipeline_gcs_location),
        temp_location=temp_location,
    )
    try:
        return generator(None)
    except ValueError as exc:
        return f"ValueError: {exc}"


CASES = [
    ("no temp location at all", None, None),
    ("a local path", "./tmp/bq", None),
    ("a GCS bucket", "gs://my-bucket/temp", None),
    ("a GCS location from pipeline options", None, "gs://my-bucket/staging"),
]

for label, temp_location, pipeline_gcs_location in CASES:
    print(f"--- {label} ---")
    print(check(temp_location, pipeline_gcs_location))
    print()
```

Run it:

```bash
python work/bq_temp_location.py
```

Expected:

```text
--- no temp location at all ---
ValueError: Invalid GCS location: None.
Writing to BigQuery with FILE_LOADS method requires a GCS location to be provided to write files to be loaded into BigQuery. Please provide a GCS bucket through custom_gcs_temp_location in the constructor of WriteToBigQuery or the fallback option --temp_location, or pass method="STREAMING_INSERTS" to WriteToBigQuery.

--- a local path ---
ValueError: Invalid GCS location: './tmp/bq'.
Writing to BigQuery with FILE_LOADS method requires a GCS location to be provided to write files to be loaded into BigQuery. Please provide a GCS bucket through custom_gcs_temp_location in the constructor of WriteToBigQuery or the fallback option --temp_location, or pass method="STREAMING_INSERTS" to WriteToBigQuery.

--- a GCS bucket ---
gs://my-bucket/temp/bq_load/3ecbd9668dd946cca2da33148c180cea

--- a GCS location from pipeline options ---
gs://my-bucket/staging/bq_load/ec21ac0430674bf7ba6b484a66f896f0
```

Two things to notice.

**The local path is rejected.** The check is not "is this a path?" —
it is "does this start with `gs://`?". A local directory looks
reasonable and still fails, because BigQuery's load job can only read
from Cloud Storage. This surprises people who try to make a local
`FILE_LOADS` write work.

**The UUID differs between runs.** `bq_load/<uuid>` is generated per
call, so do not paste your output into a test assertion.

The `pipeline_gcs_location` case matters on the Dataflow runner: the
runner sets a GCS location of its own, and the sink prefers it over
`temp_location`. That is why `--temp_location` on the command line
works even when the sink constructor has no `custom_gcs_temp_location`.

> **A trap worth naming.** `StaticValueProvider(str, None)` does *not*
> give you `None` — it coerces the value to the string `'None'`, which
> is truthy, so the sink prefers it over `temp_location` and never
> falls back. The `Stub` class in the script exists to return a real
> `None`. This is a general Beam lesson: value providers are typed, and
> the type you give them determines what a missing value becomes.

> **What you cannot verify offline.** The check above is pure, so it
> runs anywhere. The *rest* of the BigQuery path does not: Beam's test
> client substitutes a fake BigQuery, but the `FILE_LOADS` method still
> writes the staged files to real GCS, and `STREAMING_INSERTS` still
> authenticates. So a "successful" fake-client run proves the schema,
> the dispositions and the row shape — it does not prove that the
> write reached BigQuery. For that you need a real project, and the
> IAM roles listed above.

> **A note on `WriteToBigQuery` and `beam.Row`.** The schema in
> Step 6 uses the BigQuery `TableSchema` dictionary form. When you
> pass a schema, Beam expects rows that match it — either `beam.Row`
> objects with named fields, or plain dictionaries whose keys match the
> field names. Dictionaries work, and they are what the sink in Step 6
> uses. What does *not* work is a row with a field the schema does not
> declare: Beam raises `KeyError` naming the offending field rather
> than silently dropping it.

### Step 8 — the partition decorator, without BigQuery

You can verify the table-reference syntax locally, because Beam's
parser is pure Python. Create `work/partition_decorator.py`:

```python
"""Show what the table decorator does to a table reference."""

import apache_beam.io.gcp.bigquery_tools as bigquery_tools


def parse(reference: str):
    """Parse a table reference and return (project, dataset, table)."""
    parsed = bigquery_tools.parse_table_reference(reference)
    return parsed.projectId, parsed.datasetId, parsed.tableId


REFERENCES = [
    "your-project:analytics.orders",
    "analytics.orders",
    "your-project:analytics.orders$20260115",
    "analytics.orders$20260115",
]

for reference in REFERENCES:
    project, dataset, table = parse(reference)
    print(f"{reference:44s} -> {project} / {dataset} / {table}")

print()
print("The '$' suffix is a BigQuery partition decorator. When the table is")
print("ingestion-time partitioned, writing to 'dataset.table$YYYYmmdd'")
print("routes the rows into that date partition.")
```

Run it:

```bash
python work/partition_decorator.py
```

Expected:

```text
your-project:analytics.orders               -> your-project / analytics / orders
analytics.orders                            -> None / analytics / orders
your-project:analytics.orders$20260115      -> your-project / analytics / orders$20260115
analytics.orders$20260115                   -> None / analytics / orders$20260115
```

### Step 9 — the correct layout for GCS output

Create `work/gcs_layout.py`:

```python
"""Build the GCS output layout, showing the path that gets written."""

from datetime import date


def build_path(*, bucket: str, dataset: str, day: date, region: str | None = None) -> str:
    """Return the output path for one partition.

    The layout is the Hive-style key=value convention:
        gs://bucket/dataset/dt=YYYY-MM-DD/[region=REGION/]part-SSSSS-of-NNNNN
    """
    parts = [f"gs://{bucket}", dataset, f"dt={day.isoformat()}"]
    if region is not None:
        parts.append(f"region={region}")
    parts.append("part-SSSSS-of-NNNNN")
    return "/".join(parts)


TODAY = date(2026, 1, 15)

print("good — bounded prefix, deterministic shards:")
print(" ", build_path(bucket="my-bucket", dataset="orders", day=TODAY, region="EMEA"))
print(" ", build_path(bucket="my-bucket", dataset="orders", day=TODAY, region="AMER"))

print()
print("bad — one object per record:")
print(f"  gs://my-bucket/orders/customer=c000914/order-{TODAY:%Y%m%d}-00000000.csv")

print()
print("the write that produces the good layout:")
print()
print("""import apache_beam as beam

with beam.Pipeline() as p:
    orders = (
        p
        | "Read" >> beam.io.ReadFromText("gs://my-bucket/raw/orders-*.csv")
        | "Parse" >> beam.Map(parse_order)
    )

    orders | "Write" >> beam.io.WriteToText(
        "gs://my-bucket/curated/orders/dt=2026-01-15/",
        num_shards=4,
        shard_name_template="part-SSSSS-of-NNNNN",
    )""")
```

Run it:

```bash
python work/gcs_layout.py
```

Expected:

```text
good — bounded prefix, deterministic shards:
  gs://my-bucket/orders/dt=2026-01-15/region=EMEA/part-SSSSS-of-NNNNN
  gs://my-bucket/orders/dt=2026-01-15/region=AMER/part-SSSSS-of-NNNNN

bad — one object per record:
  gs://my-bucket/orders/customer=c000914/order-20260115-00000000.csv

the write that produces the good layout:
...
```

---

## 🛠️ Common Errors and Fixes

### `TypeError: WriteToBigQuery.__init__() got an unexpected keyword argument 'with_sharding'`

There is no `with_sharding` parameter. It never existed under that
name.

The real parameters are `with_auto_sharding` (streaming insert
batching, grouped by destination table) and `num_storage_api_streams`.

```python
# Wrong
beam.io.WriteToBigQuery(table, with_sharding=True)

# Right — for the streaming path
beam.io.WriteToBigQuery(table, with_auto_sharding=True)
```

And remember what sharding actually does: in the **batch** path it
splits files by **byte size** (`max_file_size`), not by row count. In
the **streaming** path, `batch_size` is a number of rows.

### `TypeError: WriteToBigQuery.__init__() got an unexpected keyword argument 'additional_configuration'`

The parameter is `additional_bq_parameters`.

```python
# Wrong
beam.io.WriteToBigQuery(table, additional_configuration={...})

# Right
beam.io.WriteToBigQuery(table, additional_bq_parameters={...})
```

If you are porting from the Java SDK or from an older snippet, this is
the substitution to make.

### `ValueError: Expected a table reference (PROJECT:DATASET.TABLE or DATASET.TABLE) instead of ...`

Your table string is malformed. The accepted forms are:

```text
PROJECT:DATASET.TABLE
DATASET.TABLE
```

Note the **colon** between the project and the dataset in the fully
qualified form, and the **dot** between the dataset and the table. The
all-dots form `PROJECT.DATASET.TABLE` is *also* accepted (the parser
allows either separator for the project), but the canonical BigQuery
form is the colon, and mixing them is the usual cause of this error.

A common cause is an f-string with a missing piece:

```python
# Wrong — produces "your-project.orders", with no dataset
f"{project}.{table}"

# Right
f"{project}:{dataset}.{table}"
```

The other cause is an **upper-case project ID**. The parser's project
pattern is `([a-z0-9.-]+:)?[a-z][a-z0-9-]*[a-z0-9]` — lower-case only.
`YOUR_PROJECT_ID:YOUR_DATASET.orders` does not parse, because GCP
project IDs are always lower-case:

```text
ValueError: Expected a table reference (PROJECT:DATASET.TABLE or
DATASET.TABLE) instead of YOUR_PROJECT_ID:YOUR_DATASET.orders.
```

The dataset and table names are case-sensitive in the pattern, so only
the project segment is affected.

### `ValueError: Invalid GCS location: None. ... FILE_LOADS method requires a GCS location`

The BigQuery sink is using the default `FILE_LOADS` method and has
nowhere to stage its files. Give it a bucket:

```python
beam.io.WriteToBigQuery(
    table,
    custom_gcs_temp_location="gs://YOUR_BUCKET/temp",
    # ...
)
```

or set `--temp_location gs://YOUR_BUCKET/temp` on the runner. A local
directory does **not** work — the check is for the `gs://` prefix, not
for "is this a path". Step 7 shows the check running offline.

### `ValueError: Unable to get filesystem from specified path ... Path specified: gs://...`

The scheme is not registered. In Beam 2.77 this should not happen for
`gs://` — the base package ships `google-cloud-storage` and registers
`GCSFileSystem` — so if you see it, you are almost certainly running
against a *different* environment than the one you installed into:

```bash
python -c "import apache_beam, sys; print(apache_beam.__file__); print(sys.executable)"
```

That prints the interpreter and the `apache_beam` package that is
actually being imported, which is usually enough to spot a virtualenv
mismatch.

The same error covers `s3://` without `s3fs` and `hdfs://` without the
Hadoop support. For those, install the extra:

```bash
pip install "apache-beam[filesystem]"
```

### `apache_beam.io.filesystem.BeamIOError: Match operation failed with exceptions {...}`

The scheme *is* registered, so the failure is at request time. Read the
exception inside the braces — it tells you which of the two problems
you have:

| Inside the braces | Meaning | Fix |
|---|---|---|
| `Invalid bucket name: 'X'` | the path is malformed | fix the path |
| `does not have storage.objects.list access` | the path is fine, the credentials are not | fix the IAM binding |
| `404` / `NoSuchBucket` | the bucket does not exist | create it, or check the name |
| `Anonymous caller` | no credentials at all | `gcloud auth application-default login` |

A `gs://` glob against a real bucket with no credentials still lists
nothing, and Beam reports it as "no files found" rather than as an
auth failure. That is a genuinely confusing default, which is why the
BigQuery path in this chapter is guarded by an explicit environment
check rather than left to fail.

### `OSError: No files found based on the file pattern`

Your GCS glob matched nothing. In order of likelihood:

1. **The prefix is wrong.** `gs://bucket/orders/orders-*.csv` does not
   match `gs://bucket/orders/part-00000-of-00004`. The glob applies to
   the *filename*, after the directory prefix.
2. **The objects are in a different prefix than you think.** List the
   bucket: `gsutil ls gs://bucket/orders/`.
3. **The path has a trailing slash where the glob expects a
   filename.** `gs://bucket/orders/*` and
   `gs://bucket/orders/orders-*` are different patterns.
4. **The objects do not exist yet**, because they are written by an
   earlier step in the same pipeline. In that case pass
   `validate=False` — but understand that you are moving a clear
   early failure to a late one.

### `RuntimeError: NotImplementedError [while running 'Write/BatchElements(pcoll)']`

This is the classic-DirectRunner failure from chapter 3.3, and it
applies to the BigQuery write path too when it runs through the
pandas-backed machinery. Use `PrismRunner`, or format the records
yourself and use `WriteToText`.

### `google.api_core.exceptions.Forbidden: 403 Permission denied ... User does not have permission to create table`

`CREATE_IF_NEEDED` needs `bigquery.tables.create` on the dataset, which
is a different permission from `bigquery.tables.updateData`.

Either grant the permission, or create the table out of band and use
`CREATE_NEVER`:

```python
beam.io.WriteToBigQuery(
    "YOUR_PROJECT_ID:YOUR_DATASET.orders_by_region",
    create_disposition=beam.io.BigQueryDisposition.CREATE_NEVER,
)
```

The second option is usually better in production, because it means
the table's schema is owned by your schema-management tooling and the
pipeline cannot silently create a table with an inferred schema.

### `google.api_core.exceptions.BadRequest: ... no such field: region`

Your rows do not match the table's schema. The usual causes:

- The table has a column you are not writing, and it is `REQUIRED`.
- The column names differ in case. BigQuery column names are
  case-insensitive for lookup but the stored schema preserves the case
  you created it with.
- The types do not match. `order_count` as a `STRING` in a `INTEGER`
  column will fail.

The fix is to make the row dict match the table exactly. Use
`ignore_unknown_columns=True` if you want to drop extra keys rather
than fail:

```python
beam.io.WriteToBigQuery(
    "YOUR_PROJECT_ID:YOUR_DATASET.orders_by_region",
    ignore_unknown_columns=True,
)
```

### The table has duplicate rows after a re-run

`WRITE_APPEND` is the default, and it appends. A re-run over the same
data range appends the same rows again.

The fix depends on the table shape:

- **Partitioned table:** use `WRITE_TRUNCATE`. It truncates only the
  partition being written, which makes the write idempotent for that
  partition.
- **Unpartitioned table with a primary key:** use
  `ignore_insert_ids=False` (the default) so BigQuery de-duplicates on
  the insert ID — but the insert ID must be deterministic, which means
  deriving it from the row's identity rather than letting Beam
  generate it per bundle.
- **Unpartitioned table, no key:** the only fix is to delete the table's
  contents before the write, which is what `WRITE_TRUNCATE` does.

### `ValueError: Incompatible cluster by column name: amount`

You set `clustering` in `additional_bq_parameters` with a column that
does not exist in the schema you passed. The clustering fields must be
a subset of the table's columns.

### `KeyError: 'temp_location'` on the Dataflow runner

The BigQuery batch write path stages files to GCS before loading them,
and it needs a temp location. On the Dataflow runner this comes from
`--temp_location`. If it is not set, the pipeline fails.

```bash
python project/batch_pipeline.py \
    --runner DataflowRunner \
    --project YOUR_PROJECT_ID \
    --region us-central1 \
    --staging_location gs://YOUR_BUCKET/staging \
    --temp_location gs://YOUR_BUCKET/temp \
    --bigquery-table YOUR_PROJECT_ID:YOUR_DATASET.orders_by_region
```

You can also override just the BigQuery temp location with the
`custom_gcs_temp_location` parameter, which is useful when the
pipeline's general temp location is in a region that BigQuery cannot
load from.

### The write is slow and the job is mostly idle

The BigQuery write is waiting on the load job, not on your Beam
compute. In the batch path, Beam writes files to GCS and then starts a
BigQuery load job; the load job is a separate, billable operation.

Things to check:

1. **How many files?** If `num_shards` is small, you have one load
   job per file and they run in parallel — but a single load job over
   one huge file is also fine. What hurts is *many tiny files*.
2. **`max_files_per_bundle`** (default 20) limits how many files a
   worker writes concurrently. Raising it can help on a high-throughput
   pipeline.
3. **The temp location's region.** A load job that reads files from
   one region into a table in another pays for cross-region transfer.
   Put the temp location in the table's region.

---

## 💡 Production Notes

- **The path is the only thing that changes between local and cloud.**
  Design for that. If your pipeline needs different *code* for local
  and GCS, the logic is in the wrong place — put it behind a function
  that takes a path, as `build_pipeline` in the course's
  `batch_pipeline.py` does.
- **Partition by a bounded key.** `dt=YYYY-MM-DD/region=EMEA/` is
  bounded. `customer=c000914/` is not. The number of objects under a
  prefix is the number that matters, and it should stay in the low
  thousands, not the millions.
- **Target 64–256 MB per output object.** Below that, you pay
  per-object overhead for no benefit. Above that, you have a
  parallelism bottleneck and a slow recovery.
- **Let Beam choose the shard count** unless you have a specific
  reason. `num_shards` is not a knob to turn for fun.
- **Use the deterministic `of-NNNNN` shard naming.** It is what makes a
  retry idempotent instead of duplicating.
- **`WRITE_APPEND` is the default and it is not idempotent.** For a
  derived, partitioned table that can be rebuilt, `WRITE_TRUNCATE` is
  the correct choice. For a streaming table, use insert IDs.
- **`WRITE_TRUNCATE` does not work in streaming mode.** The Beam
  source says so explicitly.
- **Pass `schema` whenever you allow the table to be created.**
  Otherwise Beam infers one from the data, and an inferred schema is a
  schema nobody reviewed.
- **Use `CREATE_NEVER` in production** when the table is managed by
  terraform or dbt. It turns "the table was missing" into a loud
  failure instead of a silently-created table with an inferred
  schema.
- **`additional_bq_parameters` is the parameter name.** Set
  `timePartitioning` and `clustering` when the table is created, because
  BigQuery will not let you add clustering later and adding
  partitioning later is a table rewrite.
- **Sharding splits on file size in the batch path.** `max_file_size`
  is bytes. If you are reasoning about row counts to predict file
  counts, your estimate will be wrong by whatever the average row size
  happens to be — and average row size varies wildly by dataset.
- **BigQuery export jobs are free.** That makes `ReadFromBigQuery` with
  the default `EXPORT` method a cheap way to get a table into a Beam
  pipeline. The cost is latency, since the whole result is materialised
  to GCS first.
- **Prefer a BigQuery job over a Beam pipeline when the transform is
  SQL.** Beam earns its cost when the transform is not SQL, when the
  source is not BigQuery, when you need a streaming write at volume, or
  when one read must fan out to several destinations.
- **Use the Storage Write API for high-throughput streaming.** The
  legacy Streaming Insert API is rate-limited to 1,000 rows per second
  per table per project. Dataflow's `WriteToBigQuery` uses the Storage
  Write API by default for new pipelines.
- **Put the BigQuery temp location in the table's region.** Load jobs
  that read cross-region pay for the transfer.
- **Watch the GCS listing cost.** A pipeline that reads a prefix with
  millions of objects spends real time and real money listing before it
  reads a single byte. Narrow the prefix, and consider an external
  table over a partitioned prefix instead of a wildcard read.

---

## 🔑 Key Takeaways

- **Beam has no "GCS transform."** There is one file transform per
  format; the path's scheme selects the file system. `gs://bucket/x.csv`
  with `ReadFromText` is a GCS read.
- **`gs://` needs no extra at all.** Beam ships `GCSFileSystem` over
  `google-cloud-storage`, which is a base dependency. A bad `gs://`
  path produces one of two very different errors: a `ValueError` at
  scheme-resolution time (unknown scheme), or a `BeamIOError` at
  request time (bad path or bad credentials). Read the message before
  you start installing things.
- **The shard explosion is a layout problem, not a shard-count
  problem.** Partition by a *bounded* key (`dt=.../region=.../`), not
  by something unique per record. Target 64–256 MB per output object.
- **`WriteToBigQuery` takes `schema`, `write_disposition` and
  `create_disposition`.** `WRITE_APPEND` is the default and is not
  idempotent; `WRITE_TRUNCATE` on a partitioned table is.
- **The table reference is `project:dataset.table`, and the partition
  decorator is `project:dataset.table$YYYYmmdd`.** Beam's parser
  accepts both and keeps the `$` suffix as part of the table name.
- **The parameter is `additional_bq_parameters`.** There is no
  `additional_configuration`, and there is no `with_sharding`.
- **Sharding splits on file size, not row count.** `max_file_size` is
  in bytes (default 4 TB); `max_partition_size` is in bytes; only the
  streaming path's `batch_size` is a row count.
- **A BigQuery source is usually the wrong choice**, because BigQuery
  can do the transform in SQL more cheaply. Beam earns its keep when
  the transform is not SQL, when the source is not BigQuery, when you
  need a streaming write at volume, or when one read must fan out to
  several destinations.
- **A BigQuery sink is usually the right choice**, especially for
  "GCS or Pub/Sub to BigQuery" pipelines and for multi-sink graphs that
  BigQuery alone cannot express.

---

## 📚 Practice Exercises

1. **Bucket the output.** Write a pipeline that reads
   `./sample_data/orders.csv` and writes one output file per region
   into `out/by_region/region=EMEA/`, `out/by_region/region=AMER/`
   and so on. Count the resulting objects and compare against the
   single-file version. *Expected answer:* four region prefixes with
   one file each — four objects instead of one, each bounded and
   independently readable.

2. **Make the write idempotent.** Take the course's
   `project/batch_pipeline.py` and write it to BigQuery twice with
   `WRITE_APPEND` into a partitioned table. Count the rows. Then change
   `write_disposition` to `WRITE_TRUNCATE` and write twice again.
   *Expected answer:* `WRITE_APPEND` gives 636 rows after two runs (318
   × 2); `WRITE_TRUNCATE` gives 318, because it replaces the partition
   rather than adding to it.

3. **Prove the sharding unit.** Write 100,000 records of wildly
   different sizes (some 10 bytes, some 10 KB) to BigQuery with
   `max_file_size=1024*1024` and inspect the number of staged files in
   the temp location. *Expected answer:* the number of files is
   determined by total bytes, not record count, so the file count does
   not track the row count at all.

4. **Write a BigQuery table with partitioning and clustering.** Use
   `additional_bq_parameters={"timePartitioning": {"type": "DAY"},
   "clustering": {"fields": ["region"]}}` and `schema=` to create a
   table, then verify with `bq show --schema` that the partition and
   clustering were applied. *Expected answer:* the table is
   ingestion-time partitioned by day and clustered by region.

5. **Compare the two paths.** Write the same summary twice: once to a
   local CSV, once to BigQuery. Measure the wall-clock time of each
   (the BigQuery one needs credentials). Then write the equivalent
   BigQuery SQL job and measure it too. *Expected answer:* for a
   transformation that is pure aggregation, the BigQuery job is
   faster and cheaper than the Beam pipeline, and the Beam pipeline's
   value is that it also writes the CSV — the multi-sink case.

6. **Reflection.** Your team has a nightly job that reads 200 GB of
   CSV from GCS and writes a per-customer summary to BigQuery. A
   colleague proposes `WRITE_APPEND` because "we never delete
   anything". The pipeline re-runs manually after a bug fix roughly
   once a month. *Expected answer:* `WRITE_APPEND` plus monthly
   re-runs means the summary table accumulates duplicates every month
   and nothing in BigQuery can distinguish a real order from a
   duplicate. The correct design is a partitioned table with
   `WRITE_TRUNCATE` per partition, so a re-run is idempotent; if the
   table must be unpartitioned, use deterministic insert IDs with
   `ignore_insert_ids=False`.

---

## 📖 Further Reading

- Apache Beam: Input/output — https://beam.apache.org/documentation/programming-guide/#inputoutput
- Apache Beam: BigQuery I/O — https://beam.apache.org/documentation/io/apache-beam-sdk/pydoc/current/apache_beam.io.gcp.bigquery.html
- Google Cloud: BigQuery Beam pipelines — https://cloud.google.com/dataflow/docs/beam-bigquery
- Google Cloud: BigQuery write API and quotas — https://cloud.google.com/bigquery/streaming-data-into-bigquery
- Google Cloud: Storage Write API — https://cloud.google.com/bigquery/docs/storage-write-api
- Google Cloud: Batch loads — https://cloud.google.com/bigquery/docs/loading-data
- Google Cloud: Partitioned tables and partition decorators — https://cloud.google.com/bigquery/docs/partitioned-tables
- Apache Beam Python SDK API — `apache_beam.io.gcp.bigquery` — https://beam.apache.org/releases/pydoc/current/apache_beam.io.gcp.bigquery.html
