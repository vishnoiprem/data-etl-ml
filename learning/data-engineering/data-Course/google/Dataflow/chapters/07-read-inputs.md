# 2.2 — Read Inputs

> **Section 2 · SDK & Core Transforms · Lecture 2.2 · 6:30**

## 🎯 What you will learn

- Every read transform in the Beam Python SDK, and which one to reach for
- `ReadFromText` in depth: local paths, `gs://` paths, wildcards, compression, and the `skip_header_lines` parameter
- The header pitfall — why `ReadFromText` gives you the header row and what to do about it
- How file splitting actually works, and why a single 10 GB CSV is a problem you must solve before Beam ever sees it
- Reading CSV, JSON, Avro, and Parquet — and when the "obvious" choice is wrong
- Streaming sources: `ReadFromPubSub` with `id_label` and `timestamp_attribute`, and why at-least-once delivery is a design constraint
- `ReadFromBigQuery`: the query/table spec, and when BigQuery-to-BigQuery SQL beats a Beam pipeline
- `ReadFromKafka` and why it lives in contrib

---

## 🧠 Concept

### The shape of a source

Every Beam source has the same internal structure, whether it reads a file,
a topic, or a table:

```text
        ┌─────────────────────────────────────────────┐
        │  FileBasedSource / _PubSubSource / BigQuery  │
        │                                             │
        │  1. match files      → list of shards        │
        │  2. split into bundles → bounded byte ranges  │
        │  3. read records     → PCollection elements  │
        └─────────────────────────────────────────────┘
```

The middle step is the one that determines your throughput. A source
produces **bundles** — chunks of work sized for one worker to process. How
many bundles a source produces, and how big they are, is the difference
between a pipeline that uses 50 workers and one that uses 5 and takes ten
times as long.

### The read-transform menu

| Transform | Reads | Element type | Splitting |
|---|---|---|---|
| `ReadFromText` | newline-delimited text | `str` | yes (uncompressed) |
| `ReadFromTextWithFilename` | text + the file it came from | `(filename, str)` | yes |
| `ReadFromCsv` | CSV via the DataFrame API | `pandas.Series` | via the DataFrame API — needs `PrismRunner` |
| `ReadFromJson` | JSON via the DataFrame API | `pandas.Series` | via the DataFrame API — needs `PrismRunner` |
| `ReadFromAvro` | Avro | `dict` (or `AvroRow` with `as_rows=True`) | yes |
| `ReadFromParquet` | Parquet | `dict` (or `ParquetRow`) | yes (by row group) |
| `ReadFromPubSub` | Pub/Sub topic or subscription | `bytes` or `PubsubMessage` | n/a (streaming) |
| `ReadFromBigQuery` | a BigQuery table or a query result | `dict` | export-based or direct read |
| `ReadFromKafka` | Kafka topic | `bytes` | n/a (streaming) — **contrib only** |

### `ReadFromText` — the workhorse

`ReadFromText` is the transform you will use most, and it has more
parameters than its name suggests.

```python
import inspect
import apache_beam as beam

print(inspect.signature(beam.io.ReadFromText))
```

```text
(file_pattern=None, min_bundle_size=0, compression_type='auto',
 strip_trailing_newlines=True, coder=StrUtf8Coder(), validate=True,
 skip_header_lines=0, delimiter=None, escapechar=None, **kwargs)
```

Parameter by parameter:

| Parameter | Default | What it does |
|---|---|---|
| `file_pattern` | `None` | The path. May be a local path, a `gs://` URI, or a pattern containing `*`, `?`, or `[...]`. |
| `min_bundle_size` | `0` | The smallest bundle the source will produce, in bytes. `0` means "let the runner decide". |
| `compression_type` | `'auto'` | `auto` detects from the file extension. Also accepts `gzip`, `bzip2`, `deflate`, `lzma`, `zstd`, `uncompressed`. |
| `strip_trailing_newlines` | `True` | Removes the `\n` from each line. If `False`, your lines keep their newline. |
| `coder` | `StrUtf8Coder()` | The codec. `StrUtf8Coder` is UTF-8; `StrUtf16Coder` is for UTF-16 files. |
| `validate` | `True` | Check the paths exist at pipeline *construction* time. Set `False` if the files are created by an earlier pipeline step. |
| `skip_header_lines` | `0` | **Number of header lines to skip at the start of each file.** |
| `delimiter` | `None` | Treat the file as delimited records rather than newline-delimited. |
| `escapechar` | `None` | A single byte that escapes the delimiter (and itself). |

#### The `skip_header_lines` parameter

This is the parameter people miss. `ReadFromText` in Beam 2.x **does** have
`skip_header_lines`, and it is the right way to handle a CSV header:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "ReadOrders" >> beam.io.ReadFromText(
            "./sample_data/orders.csv",
            skip_header_lines=1,
        )
        | "Print" >> beam.Map(print)
    )
```

Two properties of `skip_header_lines` that matter:

1. **It skips from *each* file**, not just the first. If your pattern
   matches ten files each with its own header, all ten headers are
   skipped. That is almost always what you want, and it is *not* what
   `beam.Filter(lambda line: not line.startswith("order_id"))` gives you
   — that filter drops any line starting with `order_id`, including a
   legitimate order whose id happens to start with that string.
2. **It is applied by the source, not by a transform.** The header never
   enters the PCollection, so it never reaches your workers, and there is
   no per-element cost.

> **The header pitfall, stated precisely.** `ReadFromText` is a *line*
> reader, not a CSV reader. It does not know what a header is. It gives you
> the header line as an ordinary element, and every downstream `Map` that
> assumes a numeric field will blow up on it. Three fixes, in order of
> preference:
>
> 1. `skip_header_lines=1` — the header never enters the graph.
> 2. A `beam.Filter` on the first element's content — works, but it is a
>    content heuristic, not a guarantee.
> 3. `ReadFromCsv` — parses the header and gives you structured rows.
>    Requires the DataFrame extras **and** `PrismRunner`; see "Story two"
>    below for the exact failure under the default runner.

#### Local paths and `gs://` paths

`ReadFromText` takes one string and figures out the filesystem from the
scheme. `./sample_data/orders.csv` is local. `gs://my-bucket/orders.csv`
is Cloud Storage. The same transform, the same code:

```python
import apache_beam as beam

def build(p, path):
    return p | "Read" >> beam.io.ReadFromText(path)

# These are the same transform. Only the path differs.
local = build(beam.Pipeline(), "./sample_data/orders.csv")
cloud = build(beam.Pipeline(), "gs://my-bucket/orders.csv")
```

The path resolution happens through Beam's `FileSystems` registry, which
ships handlers for the local filesystem, GCS, HDFS, and S3 (via the
`filesystem` extras). The `gcp` extras add the GCS handler and its
credentials.

> **The `gs://` credentials question.** When a pipeline reads
> `gs://my-bucket/...` under `DataflowRunner`, the workers use the
> pipeline's service account — the one you passed with
> `--service_account_email`, or the default compute service account for
> the project. Under the local runner, Beam uses *application default
> credentials*: `gcloud auth application-default login`. If you get
> `PermissionDenied` on a `gs://` path, this is almost always the cause.

#### Wildcards and `gs://` patterns

`file_pattern` is a glob, not a path. The pattern is matched by the
filesystem, and every match becomes a separate split:

```text
gs://my-bucket/orders/*.csv          all .csv files directly under orders/
gs://my-bucket/orders/2026-01-*.csv  all files whose name starts 2026-01-
gs://my-bucket/orders/part-???.csv   exactly three characters in ? position
gs://my-bucket/orders/[ab]*.csv      names starting with a or b
```

Two rules about wildcards and GCS specifically:

- **The `gs://` prefix is part of the pattern, not a separate scheme
  argument.** `gs://bucket/orders*.csv` works; `bucket/orders*.csv` does
  not — that would be a relative local path.
- **A pattern that matches nothing is an error, not an empty result.** By
  default Beam raises at pipeline construction:

  ```text
  ValueError: Pattern 'gs://my-bucket/orders/*.csv' did not match any files
  ```

  If your files are created by an earlier step in the same pipeline, pass
  `validate=False` so the check is deferred to execution time.

### File splitting — why one big file is a problem

This is the mechanism behind most "my Beam pipeline is slow" tickets.

When a `FileBasedSource` runs, it does two things:

1. **Matches** the pattern to a list of files (the "shards").
2. **Splits** each file into bundles of roughly `min_bundle_size` bytes,
   or whatever size the runner asks for.

The critical detail is in `apache_beam/io/filebasedsource.py`:

```text
splittable = (compression_type == CompressionTypes.UNCOMPRESSED)
```

**A compressed file is not splittable.** Neither is an Avro or Parquet file
in the general case — they are splittable only at specific record-group
boundaries, which the source can discover but only if the format supports
it. A gzip file is a single stream: you cannot seek to byte 500 MB and
start decoding, because the decoder state at that offset depends on every
byte before it.

So, concretely:

| Input | Splits | Parallelism ceiling |
|---|---|---|
| 1 uncompressed 10 GB CSV | many (one per bundle) | fine — hundreds of workers |
| 1 gzip'd 10 GB CSV | **one** | **one worker** |
| 1 gzip'd 10 GB CSV in 100 files | 100 (one per file) | 100 workers |
| 1000 uncompressed CSVs, 10 MB each | many | fine |

The rule that falls out: **the unit of parallelism for a file-based source
is the file.** Splitting within a file helps, but only for uncompressed
files. To use 200 workers on a 10 GB gzipped file, you must first split it
into 200 files.

This is why the classic pre-Beam advice — "write many small files, not one
big one" — is still exactly right. On GCS, the convention is one object per
partition per hour, sized in the tens-to-hundreds of megabytes.

#### The fix: split the file first

The most common production pattern is a "pre-split" step:

```bash
# Split a 10 GB gzip'd file into 200 shards on a local machine
zcat huge.csv.gz | split -l 50000 -d -a 5 --additional-suffix=.csv \
    -- sharded/part-
gsutil -m rsync sharded/ gs://my-bucket/orders/
```

Then read the directory, not the file:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "ReadParts" >> beam.io.ReadFromText("gs://my-bucket/orders/part-*.csv")
        | "Parse" >> beam.Map(parse_line)
    )
```

### Reading CSV

There are two completely different "read a CSV" stories in Beam, and
conflating them is a common source of confusion.

**Story one: `ReadFromText` + a parsing `Map`.** This is what the course
project does, and it is the right default:

```python
import apache_beam as beam
from apache_beam.io.textio import ReadFromText

with beam.Pipeline() as p:
    (
        p
        | "ReadOrders" >> ReadFromText("./sample_data/orders.csv", skip_header_lines=1)
        | "Parse" >> beam.Map(lambda line: line.split(","))
    )
```

You get full control over parsing, you can use the standard library's
`csv` module (which handles quoted fields containing commas), and there are
no extra dependencies.

**Story two: `beam.io.ReadFromCsv`.** This belongs to the Beam **DataFrame
API**, a pandas-like layer. It is *not* the same thing as the classic
`ReadFromText`-style I/O, and it has a different dependency footprint:

```python
import apache_beam as beam

# Requires apache-beam[dataframe]
with beam.Pipeline() as p:
    (
        p
        | "ReadCsv" >> beam.io.ReadFromCsv("./sample_data/orders.csv")
        | "Print" >> beam.Map(print)
    )
```

`ReadFromCsv` is a thin wrapper over `pandas.read_csv`, so it inherits
pandas' semantics: the header becomes the column names, dtypes are
inferred, and the element type is a `pandas.Series`. It is useful when
you want pandas semantics, and it is the wrong tool when you want
streaming, fine-grained control, or predictable performance.

`ReadFromJson` is the DataFrame-API counterpart and has the same
dependency requirement. It is worth being explicit about this because the
`apache-beam[dataframe]` extra is not installed by default:

```text
ImportError: Please install apache_beam[dataframe]
```

Installing the extra is not enough to make it work on the pinned course
stack. The DataFrame API in Beam 2.77 expands into a tuple of
PCollections, and the course's default runner — `BundleBasedDirectRunner`
— asks that tuple for a coder, which tuples do not have:

```text
AttributeError: 'tuple' object has no attribute 'element_type'
  at apache_beam/runners/direct/sdf_direct_runner.py line 86, in expand
    element_coder = typecoders.registry.get_coder(pcoll.element_type)
```

You see this with `apache-beam 2.77.0`, `pandas 2.3.3`, and
`pyarrow 25.0.1` — the versions installed by `pip install apache-beam==2.77.0`
on Python 3.13. The failure happens at **pipeline expansion**, not at
transform construction, which makes it look like a runner bug rather than
a missing dependency.

`PrismRunner` handles the tuple correctly, and both DataFrame reads work
under it:

```bash
.venv/bin/python your_pipeline.py --runner=PrismRunner
```

- `ReadFromCsv("./sample_data/orders.csv")` reads 5,000 rows.
- `ReadFromJson("./sample_data/events.ndjson")` reads 20,000 rows.

That is the runner to use if you want the DataFrame API.

The equivalent, dependency-free NDJSON read is a `ReadFromText` plus
`json.loads`:

```python
import json

import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "ReadEvents" >> beam.io.ReadFromText("./sample_data/events.ndjson")
        | "Parse" >> beam.Map(json.loads)
    )
```

`project/transforms.py` has this pattern already, in
`parse_event_payload`, and it is the one the course uses.

> **The honest comparison.**
>
> | | `ReadFromText` + `Map` | `ReadFromCsv` / `ReadFromJson` |
> |---|---|---|
> | Extra dependency | none | `apache-beam[dataframe]` + pandas + pyarrow |
> | Runner needed | any | `PrismRunner` (see above) |
> | Element type | `str` → your parsed type | `pandas.Series` |
> | Header handling | `skip_header_lines=1` | automatic |
> | Streaming | yes | no |
> | Schema control | total | pandas inference |
> | Speed | fast | slower (Series overhead per row) |
>
> The course uses the left column everywhere. The DataFrame API is covered
> in a later module.

### Reading Avro

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "ReadAvro" >> beam.io.ReadFromAvro("./sample_data/orders.avro")
        | "Print" >> beam.Map(print)
    )
```

`ReadFromAvro` needs a schema. If the file has one written into its
header (the Avro "schema" metadata key), Beam reads it automatically. If
you are reading raw Avro without a schema, pass one in — Beam's
`beam.io.avroio` expects a schema *registry name* or a schema *JSON*:

```python
import apache_beam as beam

# A schema in the Avro "schema registry" format.
AVRO_SCHEMA = """
{
  "type": "record",
  "name": "Order",
  "fields": [
    {"name": "order_id", "type": "string"},
    {"name": "region", "type": "string"},
    {"name": "amount", "type": "double"}
  ]
}
"""

with beam.Pipeline() as p:
    (
        p
        | "ReadAvro" >> beam.io.ReadFromAvro(
            "./sample_data/orders.avro",
            schema=AVRO_SCHEMA,
        )
        | "Print" >> beam.Map(print)
    )
```

`as_rows=True` gives you `AvroRow` objects instead of dicts, with
attribute access and lazily-decoded fields.

Avro's real advantage is **schema evolution**: the schema travels with the
data, and a reader that does not know a new field ignores it. If your
upstream producers are not under your control, Avro removes a whole class
of breakage.

### Reading Parquet

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "ReadParquet" >> beam.io.ReadFromParquet("./sample_data/orders.parquet")
        | "Print" >> beam.Map(print)
    )
```

Parquet is **columnar**. That has two consequences that matter:

1. **It is the right format when you read a few columns of a wide table.**
   Reading 3 of 100 columns reads roughly 3% of the bytes. CSV reads all
   of them.
2. **It is splittable at row-group boundaries.** A Parquet file is a
   sequence of row groups (typically 128 MB each), and Beam splits at those
   boundaries. A 10 GB Parquet file splits into ~80 bundles. A 10 GB gzip'd
   CSV splits into one.

`columns=["order_id", "region"]` restricts the read to a projection, and
`as_rows=True` gives you `ParquetRow` objects with attribute access.

### Reading Pub/Sub

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "ReadPubSub" >> beam.io.ReadFromPubSub(
            topic="projects/YOUR_PROJECT_ID/topics/orders",
        )
        | "Decode" >> beam.Map(lambda b: b.decode("utf-8"))
    )
```

`ReadFromPubSub` has four parameters, and each one is a design decision:

```python
import inspect
import apache_beam as beam

print(inspect.signature(beam.io.ReadFromPubSub))
```

```text
(topic=None, subscription=None, id_label=None, with_attributes=False,
 timestamp_attribute=None)
```

| Parameter | Effect |
|---|---|
| `topic` | `projects/<p>/topics/<t>`. A temporary subscription is created for you. |
| `subscription` | `projects/<p>/subscriptions/<s>`. Use an existing subscription. |
| `id_label` | The message **attribute** whose value is the record's unique ID. Enables exact deduplication. |
| `with_attributes` | `True` → elements are `PubsubMessage` objects carrying `data` and `attributes`. `False` → elements are raw `bytes`. |
| `timestamp_attribute` | The message attribute to use as the element's **event timestamp**. Falls back to the publish time. |

#### `id_label` — the deduplication mechanism

Pub/Sub is **at-least-once** delivery. A message can be delivered twice,
and your pipeline must not double-count. `id_label` is how you make
deduplication exact rather than best-effort.

The rule: `id_label` names an *attribute*, not a field in the payload.
Both the producer and the consumer must agree on the attribute name and
on the value's uniqueness. The course's `project/transforms.py` has the
matching half of this:

```python
def dedup_key(event: dict[str, Any]) -> str:
    """Return the deduplication key for an event.

    Pub/Sub is at-least-once, so the same event can arrive twice. The
    deduplication key must be derived from the payload's own identity, never
    from arrival time.
    """
    return str(event.get("event_id") or event.get("user_id", ""))
```

The `id_label` on the read side, with `with_attributes=True`:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "ReadPubSub" >> beam.io.ReadFromPubSub(
            topic="projects/YOUR_PROJECT_ID/topics/events",
            id_label="event_id",
            with_attributes=True,
            timestamp_attribute="event_ts",
        )
        | "Extract" >> beam.Map(
            lambda msg: (msg.attributes.get("event_id", ""), msg.data)
        )
    )
```

> **What `id_label` actually does.** It does not deduplicate for you. It
> tells Beam which attribute carries the record's identity, so that Beam's
> internal exactly-once machinery (the state backend) can deduplicate
> *within a single pipeline run*. It does **not** deduplicate across
> pipeline restarts unless you use a state-and-timer backend that
> survives restarts, and it does **not** deduplicate against a different
> pipeline's output. If your requirement is "this event must be counted
> exactly once, forever", you need your own idempotent sink — a BigQuery
> table with a merge on a primary key, or a `MERGE` statement — not just
> `id_label`.

#### `timestamp_attribute` and event time

The default element timestamp for a Pub/Sub element is the message's
**publish time**. That is almost never the timestamp you want for business
logic, because publish time includes producer-side buffering and network
delay.

`timestamp_attribute` overrides it with an attribute from the message:

```text
Timestamp values should be in one of two formats:
  - a number of milliseconds since the Unix epoch
  - a string in RFC 3339 format, UTC timezone — e.g. 2015-10-29T23:41:41.123Z
```

This is what makes Beam's windowing correct for a stream: the event's
*event time* drives which window it lands in, and the publish time only
drives when the watermark advances.

> **The parameter is called `timestamp_attribute`, not
> `with_timestamp_attributes`.** The plural form appears in the Dataflow
> *Python* job construction options, not in the SDK transform. If you
> write `with_timestamp_attributes=True` you get:

  ```text
  TypeError: ReadFromPubSub.__init__() got an unexpected keyword argument 'with_timestamp_attributes'
  ```

### Reading BigQuery

`ReadFromBigQuery` has two mutually exclusive modes: read a **table**, or
read the result of a **query**.

```python
import apache_beam as beam

# Mode 1: a table
with beam.Pipeline() as p:
    (
        p
        | "ReadTable" >> beam.io.ReadFromBigQuery(
            table="orders",
            dataset="sales",
            project="YOUR_PROJECT_ID",
        )
    )
```

```python
import apache_beam as beam

# Mode 2: a query
with beam.Pipeline() as p:
    (
        p
        | "ReadQuery" >> beam.io.ReadFromBigQuery(
            query="SELECT region, SUM(amount) AS revenue FROM `sales.orders` GROUP BY region",
            use_standard_sql=True,
        )
    )
```

The `table`/`dataset`/`project` triple has a shorthand. When `dataset` is
`None`, the `table` argument must carry the whole reference:

```text
DATASET.TABLE
PROJECT:DATASET.TABLE
```

Note the **colon**, not a dot, in the project-qualified form. This is a
BigQuery API convention, and it is a genuine trap — `project.dataset.table`
with a dot is not accepted by this parameter.

There are two read *methods*:

| `method` | How it works | When to use it |
|---|---|---|
| `EXPORT` (default) | Exports the data to Avro files in GCS, then reads those files | Large scans, and you want the export path |
| `DIRECT_READ` | Reads directly from the BigQuery Storage API | Low-latency reads, and you want the data never to leave BigQuery |

`DIRECT_READ` is the modern default for interactive work. It supports
`output_type="BEAM_ROW"` (typed `Row` objects with a schema), which is
much better than dicts for anything that touches BigQuery again.

#### When you should not use Beam at all

This is the most important thing to say about `ReadFromBigQuery`, and it is
the advice most tutorials skip.

**If your pipeline is BigQuery → BigQuery, write SQL.**

```sql
CREATE OR REPLACE TABLE `sales.orders_by_region` AS
SELECT
  region,
  COUNT(*) AS order_count,
  SUM(amount * CASE currency WHEN 'USD' THEN 0.92
                              WHEN 'GBP' THEN 1.17
                              WHEN 'JPY' THEN 0.0064
                              ELSE 1.0 END) AS revenue_eur
FROM `sales.orders`
WHERE status = 'complete'
GROUP BY region;
```

Reasons, in order of weight:

1. **BigQuery's query engine is not Beam.** BigQuery's slots, remote
   execution, and columnar storage are designed for exactly this work.
   A `CombinePerKey` in Beam does a shuffle; a `GROUP BY` in BigQuery does
   not, in the same sense, and BigQuery charges for bytes scanned rather
   than for shuffle volume.
2. **A Beam BigQuery read materialises the data.** Even with `DIRECT_READ`,
   every row crosses into the Beam graph, is encoded, decoded, shuffled
   across workers, and is then written back. That is four network hops and
   two encodings for data that never needed to leave BigQuery's storage.
3. **BigQuery slots are cheaper than Dataflow workers** for this shape of
   work, and often the query is free under the 1 TB/month tier.
4. **Schema and types are handled correctly.** Beam's dict-based BigQuery
   I/O loses type information relative to BigQuery's own typed tables. The
   SQL path cannot.

**Beam earns its place when the pipeline is not BigQuery → BigQuery.**
Beam is the right tool when:

- The source is not BigQuery (files, Pub/Sub, Kafka, another database).
- The transform is not expressible in SQL — a per-record model call, a
  graph traversal, a stateful sessionisation, an enrichment against a
  side input.
- The job is streaming and BigQuery Streaming Insert is the sink.
- The same code must also run on a different runner (Flink, Spark).

The rule of thumb: **if the whole job can be one `CREATE TABLE AS SELECT`,
write the SQL.** The Beam chapter on BigQuery covers the cases where you
cannot.

### Reading Kafka

Kafka support is **not in the standard wheel**. It lives in a separate
contrib package:

```text
apache-beam-contrib-kafka-io
```

```python
from apache_beam.contrib.io.kafka.io import ReadFromKafka

with beam.Pipeline() as p:
    (
        p
        | "ReadKafka" >> ReadFromKafka(
            topic="orders",
            consumer_config={
                "bootstrap.servers": "broker1:9092,broker2:9092",
                "group.id": "beam-course",
                "auto.offset.reset": "earliest",
            },
            commit_size_in_records=1,
            key_coder=beam.coders.BytesCoder(),
            value_coder=beam.coders.BytesCoder(),
        )
        | "Decode" >> beam.Map(lambda kv: kv[1].decode("utf-8"))
    )
```

Two things to know:

- **Contrib packages are versioned separately** from the SDK. The contrib
  package version must match the `apache-beam` version. A mismatch is the
  usual cause of `ImportError` or of a mysterious `NoClassDefFoundError`
  from the Java side.
- **Kafka in Beam is a source, not a full connector.** There is no
  `WriteToKafka` in the same package. The Kafka *sink* story on Dataflow
  is usually "write to Pub/Sub, use a Kafka bridge downstream", or a
  third-party sink.

The `commit_size_in_records=1` matters: it controls how often the
consumer offsets are committed, which is the knob that trades
duplicates against latency.

---

## 🛠️ Hands-On: Reading Every Sample File

The sample dataset has six files in four formats. This exercise reads all
of them and counts the rows, which is the sanity check every source
transform should get.

### Step 0 — regenerate the sample data if you have not

```bash
cd data-engineering/data-Course/google/Dataflow
python resources/sample_data.py --output-dir ./sample_data
```

### Step 1 — read a text file and count the rows

```bash
.venv/bin/python - <<'PY'
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])

with beam.Pipeline(options=options) as p:
    (
        p
        | "ReadOrders" >> beam.io.ReadFromText("./sample_data/orders.csv")
        | "Count" >> beam.combiners.Count.Globally()
        | "Print" >> beam.Map(print)
    )
PY
```

The count is **5001**, not 5000. That extra one is the header. The next
step removes it.

### Step 2 — skip the header at the source

```bash
.venv/bin/python - <<'PY'
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])

with beam.Pipeline(options=options) as p:
    (
        p
        | "ReadOrders" >> beam.io.ReadFromText(
            "./sample_data/orders.csv",
            skip_header_lines=1,
        )
        | "Count" >> beam.combiners.Count.Globally()
        | "Print" >> beam.Map(print)
    )
PY
```

Now the count is **5000**. `skip_header_lines=1` is the fix.

### Step 3 — read the NDJSON file and parse it

```bash
.venv/bin/python - <<'PY'
import json

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])

with beam.Pipeline(options=options) as p:
    (
        p
        | "ReadEvents" >> beam.io.ReadFromText("./sample_data/events.ndjson")
        | "Parse" >> beam.Map(json.loads)
        | "Count" >> beam.combiners.Count.Globally()
        | "Print" >> beam.Map(print)
    )
PY
```

Expected: **20000**.

### Step 4 — read the reference file as a side input

```bash
.venv/bin/python - <<'PY'
import json

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])


def enrich(row, reference):
    """Attach the product category looked up in the side-input dict."""
    entry = reference.get(row[8], {})
    return (row[0], row[3], entry.get("category", "unknown"))


with beam.Pipeline(options=options) as p:
    reference = (
        p
        | "ReadReference" >> beam.io.ReadFromText(
            "./sample_data/product_reference.ndjson"
        )
        | "ParseReference" >> beam.Map(json.loads)
        | "KeyById" >> beam.Map(lambda r: (r["product_id"], r))
    )

    (
        p
        | "ReadOrders" >> beam.io.ReadFromText(
            "./sample_data/orders.csv",
            skip_header_lines=1,
        )
        | "ParseOrders" >> beam.Map(lambda line: line.split(","))
        | "Enrich" >> beam.Map(
            enrich,
            reference=beam.pvalue.AsDict(reference),
        )
        | "PrintSample" >> beam.Map(print)
    )
PY
```

Sample output:

```text
('o00004995', 'AMER', 'cat-21')
('o00004996', 'APAC', 'cat-07')
('o00004997', 'LATAM', 'unknown')
```

Note two things about the shape.

**The side-input function must accept the side input as a parameter.** A
`lambda` that takes only the element raises:

```text
TypeError: Map.<locals>.<lambda>() got an unexpected keyword argument 'reference'
```

The side input is passed as a keyword argument, and the function must
have a matching parameter.

**`AsDict` turns the reference PCollection of `(key, value)` pairs into a
dict**, so the lookup is O(1) instead of a linear scan. The course's
`batch_pipeline.py` uses the `AsIter` form, which is a linear scan —
correct for 50 rows, wrong for 500,000. Chapter 2.4 covers side inputs
properly.

### Step 5 — read every sample file and count all of them at once

This is the exercise's real deliverable: one pipeline, four sources, four
counts.

```bash
.venv/bin/python - <<'PY'
import json

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])


def tagged(name, pcoll):
    """Tag every element of a PCollection with its source file name."""
    return pcoll | f"Tag{name}" >> beam.Map(lambda x, n=name: (n, 1))


with beam.Pipeline(options=options) as p:
    orders_csv = (
        p
        | "ReadOrdersCsv" >> beam.io.ReadFromText(
            "./sample_data/orders.csv",
            skip_header_lines=1,
        )
    )

    orders_ndjson = (
        p
        | "ReadOrdersNdjson" >> beam.io.ReadFromText(
            "./sample_data/orders.ndjson"
        )
        | "ParseOrdersNdjson" >> beam.Map(json.loads)
    )

    events_csv = (
        p
        | "ReadEventsCsv" >> beam.io.ReadFromText(
            "./sample_data/events.csv",
            skip_header_lines=1,
        )
    )

    events_ndjson = (
        p
        | "ReadEventsNdjson" >> beam.io.ReadFromText(
            "./sample_data/events.ndjson"
        )
        | "ParseEventsNdjson" >> beam.Map(json.loads)
    )

    reference = (
        p
        | "ReadReference" >> beam.io.ReadFromText(
            "./sample_data/product_reference.ndjson"
        )
    )

    malformed = (
        p
        | "ReadMalformed" >> beam.io.ReadFromText(
            "./sample_data/malformed_orders.csv"
        )
    )

    (
        (
            tagged("orders.csv", orders_csv),
            tagged("orders.ndjson", orders_ndjson),
            tagged("events.csv", events_csv),
            tagged("events.ndjson", events_ndjson),
            tagged("product_reference.ndjson", reference),
            tagged("malformed_orders.csv", malformed),
        )
        | "FlattenSummary" >> beam.Flatten()
        | "CountPerFile" >> beam.CombinePerKey(sum)
        | "FormatSummary" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]}")
        | "WriteSummary" >> beam.io.WriteToText(
            "./out/read_summary",
            num_shards=1,
            shard_name_template="",
        )
    )
PY
```

```bash
cat out/read_summary
```

Expected counts:

```text
orders.csv,5000
orders.ndjson,5000
events.csv,20000
events.ndjson,20000
product_reference.ndjson,50
malformed_orders.csv,5
```

Two things about this pipeline are worth noticing.

**`beam.Flatten` takes a tuple of PCollections, not a dict.** Passing a
dict raises:

```text
ValueError: Input to Flatten must be an iterable. Got a value of type
<class 'apache_beam.pipeline.Pipeline'> instead.
```

**The counting is a keyed aggregate, not a global count.** A global count
would tell you the total across all six files (50,055) but not which file
each row came from. Tagging each element with its source name and then
running a `CombinePerKey` gives you a per-file count in one pass — and
that is the shape almost every "tally up several inputs" pipeline takes.

The row order is not guaranteed. That is not a bug — Beam does not
guarantee ordering, and the runner is free to process elements in any
order. (Chapter 4 covers ordering guarantees and when you need to restore
them.)

### Step 6 — read from a `gs://` path

If you have a bucket, upload the sample data and read it back:

```bash
gsutil -m cp -r ./sample_data gs://YOUR_BUCKET/sample_data/
```

```bash
.venv/bin/python - <<'PY'
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])

with beam.Pipeline(options=options) as p:
    (
        p
        | "ReadRemote" >> beam.io.ReadFromText(
            "gs://YOUR_BUCKET/sample_data/orders.csv",
            skip_header_lines=1,
        )
        | "Count" >> beam.combiners.Count.Globally()
        | "Print" >> beam.Map(print)
    )
PY
```

The identical pipeline with a `gs://` path is the point of the Beam model:
the code is portable, only the path and the runner change.

### Step 7 — count rows with the shell, as a cross-check

```bash
wc -l sample_data/orders.csv sample_data/events.csv
```

`orders.csv` reports 5001 lines: 5000 records plus the header. Your
pipeline said 5000 after `skip_header_lines=1`. The two agree, which is
what a cross-check is for.

---

## 🛠️ Common Errors and Fixes

### `ValueError: Pattern 'gs://my-bucket/orders/*.csv' did not match any files`

The glob matched nothing. Three causes, in order of likelihood:

1. The bucket or prefix is wrong. Check with `gsutil ls gs://my-bucket/`.
2. The objects are there but the pattern is wrong — `gs://bucket/orders*`
   does not match `gs://bucket/orders/part-1.csv`.
3. The files are produced by an earlier step in the same pipeline. Pass
   `validate=False` so the check happens at execution time, not
   construction time.

### `PermissionDenied: 403 ... does not have storage.objects.get access`

The credentials do not cover the bucket. Under the local runner, run:

```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

Under `DataflowRunner`, the pipeline's service account needs
`roles/storage.objectViewer` (read) or `roles/storage.objectAdmin`
(write).

### `ValueError: Could not split file ... it is compressed`

Not a real Beam error, but the real symptom of the compressed-file
splitting problem. A gzip'd file is one split. Pre-split it.

### `TypeError: ReadFromPubSub.__init__() got an unexpected keyword argument 'with_timestamp_attributes'`

The parameter is `timestamp_attribute` (singular), and it takes the *name
of a message attribute*, not a boolean.

```python
beam.io.ReadFromPubSub(
    topic="projects/YOUR_PROJECT_ID/topics/events",
    timestamp_attribute="event_ts",
)
```

### `ValueError: PCollection of size 2 with more than one element accessed as a singleton view`

You used `AsSingleton` on a PCollection with more than one element. It
must contain exactly one value per window. Use `AsList` or `AsIter`
instead. (Chapter 2.4 covers the four side-input views.)

### `ImportError: Please install apache_beam[dataframe]`

`beam.io.ReadFromCsv` and `beam.io.ReadFromJson` belong to the DataFrame
API and need the extra:

```bash
pip install "apache-beam[dataframe]"
```

For this course, use `ReadFromText` plus a `Map` instead.

### `AttributeError: 'tuple' object has no attribute 'element_type'`

You installed the `apache-beam[dataframe]` extra, so the import error is
gone, but the read still fails. This one comes from the
`BundleBasedDirectRunner`:

```text
AttributeError: 'tuple' object has no attribute 'element_type'
  at apache_beam/runners/direct/sdf_direct_runner.py line 86, in expand
    element_coder = typecoders.registry.get_coder(pcoll.element_type)
```

The DataFrame read transforms expand into a tuple of PCollections, and
that runner asks the tuple for a coder, which tuples do not have. Run
the pipeline with `--runner=PrismRunner` to use the DataFrame API, or
use `ReadFromText` + `Map` — which is what the course does.

### `KeyError: 'order_id'` after reading a CSV

The header line got through and was parsed as a record, or the header was
skipped but the field positions are off. Two checks:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "Read" >> beam.io.ReadFromText("./sample_data/orders.csv")
        | "PrintFirst" >> beam.Map(print)
    )
```

If the first printed line is `order_id,customer_id,...`, the header is
there — add `skip_header_lines=1`.

### The count is one more than expected

You are reading a CSV without `skip_header_lines=1`. See above.

### `AttributeError: 'NoneType' object has no attribute 'split'`

A `Map` received `None`. This happens when a `Map` function returns `None`
— Beam treats that as "emit nothing", and downstream code that expected an
element gets nothing instead. Chapter 2.4 covers this.

### The pipeline reads one file but there are 200 in the directory

`file_pattern` pointed at the directory, not a glob. Use
`"gs://bucket/orders/*.csv"`, not `"gs://bucket/orders/"`.

### `FileNotFoundError` on a local path that you can see

Check the working directory. Course paths are relative to the course root,
not to wherever the script lives.

---

## 💡 Production Notes

- **The unit of parallelism for file sources is the file.** Uncompressed
  files split internally; compressed files do not. If a job is slow and
  the profiler shows one busy worker while the rest idle, the input is
  one compressed file. Pre-split it upstream.
- **On GCS, write many small objects.** The convention is one object per
  partition per hour, in the tens-to-hundreds of megabytes. A single
  10 GB object is a single split and a single bottleneck.
- **`skip_header_lines` beats a header filter.** It removes the header
  before it reaches a worker, it is correct across multiple files, and it
  cannot accidentally drop a data row whose content happens to look like
  a header.
- **Every read transform has a `validate` flag.** Leave it `True` for
  inputs that exist before the job starts. Turn it off only for inputs
  that a previous step in the same pipeline creates — and understand that
  you are trading a fast failure for a slow one.
- **Pub/Sub is at-least-once. Design for it.** `id_label` makes
  deduplication exact *within* a run, not across runs. The only way to be
  exactly-once forever is an idempotent sink: a BigQuery `MERGE` on a
  primary key, or a `INSERT ... ON CONFLICT DO NOTHING` in Postgres.
- **Set the event timestamp explicitly for every stream.** The default
  publish time includes producer buffering. If your windowing is wrong by
  a few minutes, this is why.
- **Prefer `DIRECT_READ` for BigQuery** when you are reading a table
  directly: it avoids the export-to-GCS round trip entirely.
- **Know when to write SQL instead.** A Beam pipeline that reads BigQuery
  and writes BigQuery with nothing but a `GROUP BY` in between is a
  `CREATE TABLE AS SELECT` written the expensive way. Beam earns its keep
  when the transform is not SQL-shaped.
- **Read from a manifest, not from a directory listing, at scale.** A
  `gs://bucket/orders/*` pattern over 100,000 objects makes one enormous
  LIST call. Write a manifest file listing the object names and pass
  *that* to the pipeline.
- **Watch the decompression CPU bill.** `compression_type='auto'` on a
  gzip'd file means the worker spends CPU gunzipping. Sometimes that is
  the right trade (smaller network transfers) and sometimes it is not
  (compression ratio below ~3× usually is not worth the CPU).

---

## 🔑 Key Takeaways

- The read-transform menu: `ReadFromText`, `ReadFromCsv`, `ReadFromJson`,
  `ReadFromAvro`, `ReadFromParquet`, `ReadFromPubSub`, `ReadFromBigQuery`,
  `ReadFromKafka` (contrib).
- `ReadFromText` is a **line** reader, not a CSV reader. Use
  `skip_header_lines=1` — it removes the header at the source and works
  per-file, so it is correct across a multi-file glob.
- `file_pattern` is a **glob**, not a path. `gs://bucket/orders/*.csv`
  matches many files; a directory path matches nothing.
- **Splitting is the performance story.** Uncompressed files split into
  many bundles; compressed files are one split. A 10 GB gzip'd CSV is one
  worker, no matter how many workers the job requests.
- `ReadFromCsv` and `ReadFromJson` are **DataFrame API** transforms. They
  need `apache-beam[dataframe]` **and** `PrismRunner` — under the
  course's default `BundleBasedDirectRunner` they fail at expansion with
  `AttributeError: 'tuple' object has no attribute 'element_type'`. The
  portable equivalent is `ReadFromText` + `Map`.
- `ReadFromPubSub`: `id_label` names the deduplication attribute;
  `timestamp_attribute` names the event-time attribute. Pub/Sub is
  **at-least-once**, so idempotent sinks are the real requirement.
- `ReadFromBigQuery` takes either `table`/`dataset`/`project` or `query`,
  and the fully-qualified table form is `PROJECT:DATASET.TABLE` — with a
  **colon**.
- **BigQuery → BigQuery should be SQL.** Beam is for the parts that SQL
  cannot express.

---

## 📚 Practice Exercises

1. **Prove the header difference.** Run the same pipeline over
   `orders.csv` three times: with no options, with `skip_header_lines=1`,
   and with a `beam.Filter` that drops lines starting with `order_id`.
   Count the rows in each. Then add a *legitimate* order whose `order_id`
   is literally `order_id_special` to a copy of the file and re-run the
   filter version. Explain which of the two header strategies is correct
   and why.

2. **Measure splitting.** Generate 5000 orders, then write the same data
   to three files: one 10 MB CSV, one gzip'd 10 MB CSV, and 100 gzip'd
   100 KB CSVs. Read each with `ReadFromText` and print the number of
   bundles the source produces (use `source.split()` on the transform's
   internal source, or infer it from the Dataflow job graph's step
   statistics). Explain the difference.

3. **Build a pre-splitter.** Write a script that reads a gzip'd CSV and
   writes N compressed shards, then read the shards with
   `ReadFromText("part-*.csv.gz")`. Verify that the total row count is
   unchanged and that the row *order* is not preserved across shards.

4. **Compare the JSON paths.** Read `events.ndjson` twice — once with
   `ReadFromText` + `json.loads` under the default runner, and once with
   `beam.io.ReadFromJson` under `PrismRunner` after installing
   `apache-beam[dataframe]`. Compare the element types, the runtime, and
   the memory profile on the 20,000-row sample. Which would you use for a
   2-billion-row production stream, and why?

5. **Read a Pub/Sub topic with an explicit event time.** Create a topic
   and a subscription, publish ten messages with an `event_ts` attribute
   in RFC 3339, and read them with `timestamp_attribute="event_ts"` and
   `with_attributes=True`. Print each message's data and attributes.
   Then publish the same ten messages again and show that `id_label`
   deduplicates them within the run. Explain what `id_label` does *not*
   guarantee.

6. **Decide SQL vs Beam.** For each of these four jobs, decide whether a
   Beam pipeline is the right tool, and justify the answer in two
   sentences: (a) copy a BigQuery table to another BigQuery table with a
   filter; (b) read Pub/Sub events, call a machine-learning model on each,
   and write the predictions back to BigQuery; (c) aggregate Parquet files
   in GCS into a new Parquet file; (d) join a BigQuery dimension table
   against a Kafka stream.

---

## 📖 Further Reading

- Apache Beam Python SDK IO documentation — https://beam.apache.org/documentation/io/beam-io/
- Apache Beam `ReadFromText` reference — https://beam.apache.org/releases/pydoc/current/apache_beam.io.textio.html
- Apache Beam `ReadFromPubSub` reference — https://beam.apache.org/releases/pydoc/current/apache_beam.io.gcp.pubsub.html
- Apache Beam `ReadFromBigQuery` reference — https://beam.apache.org/releases/pydoc/current/apache_beam.io.gcp.bigquery.html
- Apache Beam Python API reference — https://beam.apache.org/releases/pydoc/current/index.html
- Google Cloud BigQuery export documentation — https://cloud.google.com/bigquery/docs/exporting-data
- Google Cloud Pub/Sub message attributes — https://cloud.google.com/pubsub/docs/samples/message-attributes
- Apache Beam and Flink/Kafka contrib packages — https://beam.apache.org/releases/pydoc/current/apache_beam.contrib.html
