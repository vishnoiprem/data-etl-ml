# 2.3 — Write Outputs

> **Section 2 · SDK & Core Transforms · Lecture 2.3 · 6:30**

## 🎯 What you will learn

- `WriteToText` in full: sharding, `shard_name_template`, `num_shards`, `file_name_suffix`, `header`, `compression_type`, and `coder`
- Why output files are named `prefix00000of00004` and what that naming buys you
- The `str()` trap — why a dict written by `WriteToText` comes out as a Python repr, and how to fix it with `csv.writer`
- `WriteToCsv`, `WriteToJson`, `WriteToAvro`, and `WriteToParquet` — and when each is the right format
- `WriteToBigQuery`: the schema requirement, `write_disposition` and `create_disposition`, and the table-reference syntax
- `WriteToPubSub`, including `id_label` for round-trip deduplication
- How to design an output contract that a downstream consumer can actually rely on

---

## 🧠 Concept

### A sink is a contract

A sink is not "a place to put the data". It is a **contract with a consumer**
that you are not in the room to negotiate with. When you write a file, the
consumer needs to know:

- Where it is (the path).
- What it is called (the filename, including any shard suffix).
- What is inside it (the encoding, the format, the schema, the column
  order).
- How many files there will be (the shard count).
- Whether re-running the pipeline will overwrite or duplicate.

`WriteToText` makes most of those decisions for you, and its defaults are
*defensible* but not always *what you want*. That is why this chapter is
about the parameters.

### `WriteToText` — the full signature

```python
import inspect
import apache_beam as beam

print(inspect.signature(beam.io.WriteToText))
```

```text
(file_path_prefix: str, file_name_suffix='', append_trailing_newlines=True,
 num_shards=0, shard_name_template: Optional[str] = None,
 coder=ToBytesCoder(), compression_type='auto', header=None, footer=None, *,
 max_records_per_shard=None, max_bytes_per_shard=None, skip_if_empty=False,
 triggering_frequency=None)
```

| Parameter | Default | What it does |
|---|---|---|
| `file_path_prefix` | — | The output path *prefix*. Files are named `<prefix><shard><suffix>`. |
| `file_name_suffix` | `''` | A suffix appended to every output file, e.g. `'.csv'`. |
| `append_trailing_newlines` | `True` | Write `\n` after each element. |
| `num_shards` | `0` | The number of output files. `0` means "the runner decides". |
| `shard_name_template` | `None` | The template used to name shards. |
| `coder` | `ToBytesCoder()` | The codec. `ToBytesCoder` calls `str()` on the element. |
| `compression_type` | `'auto'` | Detect from the file extension. Also `gzip`, `bzip2`, `deflate`, `lzma`, `zstd`, `uncompressed`. |
| `header` | `None` | A string written at the top of every shard. |
| `footer` | `None` | A string written at the bottom of every shard. |
| `max_records_per_shard` | `None` | Start a new shard after this many records. |
| `max_bytes_per_shard` | `None` | Target maximum bytes per shard. |
| `skip_if_empty` | `False` | Write no files at all if the PCollection is empty. |

### Sharding — why `prefix00000of00004`

When you write with `WriteToText`, the output is not one file. It is
several, and they are named with the shard number and the shard count
baked into the name:

```text
out/summary-00000-of-00004
out/summary-00001-of-00004
out/summary-00002-of-00004
out/summary-00003-of-00004
```

(Small detail: Beam 2.77's default template puts a **hyphen** before the
shard number, so the files are `summary-00000-of-00004`, not
`summary00000of00004`. Older Beam versions and some sinks use the
no-hyphen form. Never hard-code either form.)

**Why sharding exists at all.** A single output file is a serialisation
bottleneck:

- One writer process, one file, one stream. The sink's throughput caps
  the pipeline's throughput.
- No parallelism on the write side, even if the compute side has 500
  workers.
- A failed write means the whole file must be redone.

Sharding fixes all three. Each shard is written by a different worker, in
parallel, and a failure only affects one shard. The cost is that the
consumer now has several files instead of one — which is why the shard
count is *in the filename*. A consumer that globs `summary*` and sorts
knows it got everything; a consumer that expects exactly one file has to
be told the shard count or be told to concatenate.

**The shard count must be in the filename** because the count is decided
by the runner, at execution time, and is not knowable in advance. Putting
it in the name means a consumer can detect an incomplete write: if you
see `summary-00000-of-00004` through `summary-00003-of-00004`, you have
all four. If you see only three, the job died.

#### `num_shards`

`num_shards=0` (the default) means "the runner decides", and on Dataflow
the runner picks a number based on the amount of data. That is the right
default for production: it maximises write parallelism.

Setting `num_shards=1` forces a single output file. This is a real
requirement in some situations:

- The downstream consumer is a `COPY` command that takes one file.
- The output is a "manifest" or a small aggregate that must be atomic.
- You are writing to a path that another job polls, and a partial set of
  shards would be read as complete.

The Beam docs warn that constraining the shard count reduces performance.
That is correct: `num_shards=1` puts a single worker in charge of the
write. For a small aggregate, that is fine. For 10 TB, it is not.

> **The course project uses `num_shards=1` deliberately.** The summary
> output is four rows. Sharding it across eight files would be absurd, and
> the summary's *total* is a single number, so a consumer that wants "the
> total" must not have to add up shards. The `batch_pipeline.py` write
> looks like this:
>
> ```text
> rows | "FormatCsv" >> beam.Map(format_summary_csv)
>      | "WriteSummaryCsv" >> WriteToText(
>          output_path,
>          header="region,order_count,revenue_eur",
>          num_shards=1,
>          shard_name_template="",
>        )
> ```
>
> Note `shard_name_template=""` — that is what makes the filename exactly
> `<prefix>` with no shard suffix at all. See below.

#### `shard_name_template`

The template controls the shard part of the filename. Beam accepts exactly
four forms:

| Template | Resulting filename | Notes |
|---|---|---|
| `None` (default) | `summary-00000-of-00004` | Bounded PCollection. Unbounded gets `-W-` (window). |
| `'-SSSSS-of-NNNNN'` | `summary-00000-of-00004` | The explicit default. |
| `'-W-SSSSS-of-NNNNN'` | `summary-W-00000-of-00004` | Windowed naming; `W` becomes the window index. |
| `'-V-SSSSS-of-NNNNN'` | `summary-V-20260115T00-00-00-00000-of-00004` | Windowed naming with a UTC timestamp. |
| `''` | `summary` | Exactly one file. Equivalent to `num_shards=1`. |

`S` is replaced with the zero-padded shard number, `N` with the
zero-padded shard count. Five `S`s means five digits: `00000` through
`99999`. If you expect more than 100,000 shards, you need more `S`s.

Setting `shard_name_template=""` is how you get a single file with a
predictable name. It is the right choice for a small aggregate that
another job will poll:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create(["a", "b"])
        | "Write" >> beam.io.WriteToText(
            "./out/single",
            num_shards=1,
            shard_name_template="",
        )
    )
```

The output file is exactly `./out/single` — no suffix, no shard number. A
downstream job can then do a deterministic `gsutil cp gs://bucket/out/single`
and be certain it got the whole thing.

> **Do not set `shard_name_template=""` on a large output.** You get one
> file, one writer, and a serialisation bottleneck. The template is a
> formatting knob, not a performance knob — except in exactly this case,
> where it is one of the biggest.

#### `file_name_suffix`

`file_name_suffix` is appended after the shard part:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create(["a", "b"])
        | "Write" >> beam.io.WriteToText(
            "./out/rows",
            file_name_suffix=".csv",
            num_shards=1,
        )
    )
```

produces `./out/rows-00000-of-00001.csv`.

The suffix does double duty: it names the format for humans, and it drives
**compression detection**. With `compression_type='auto'`, Beam looks at
the *final* path's extension to decide whether to compress. So:

```text
file_name_suffix=".csv"    → not compressed
file_name_suffix=".csv.gz" → gzip compressed
file_name_suffix=".gz"     → gzip compressed
```

This is the mechanism behind a common surprise: writing to
`gs://bucket/output` with no suffix produces uncompressed files, and
writing to `gs://bucket/output.gz` produces compressed ones. If you want
compression, put the extension in the suffix.

#### `append_trailing_newlines`

`append_trailing_newlines=True` (the default) writes `\n` after every
element. This is what makes the output a valid text file — a file with
`a` and `b` and no newlines is `ab`, one line, not two.

Set it to `False` when the element already contains its own newline, or
when you are writing a format that manages its own line endings.

The `header` parameter interacts with this: the header is written at the
top of **every** shard, and a `\n` is added after it if
`append_trailing_newlines` is set. So with `num_shards=4`, your output
has the header four times — once per file. That is correct, because each
file must be independently readable.

#### `coder`

The coder is the codec used to turn each element into bytes. The default
is `ToBytesCoder()`, and this is the source of the most important pitfall
in this chapter.

### The `str()` trap — the exact bug the course project hit

`ToBytesCoder` calls `str()` on the element. It does not call a CSV
writer, a JSON encoder, or anything else. It does `str()`.

For a `str` element, `str(x)` is a no-op. For anything else, you get
Python's `repr`:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create([{"region": "EMEA", "revenue_eur": 118423.22}])
        | "Write" >> beam.io.WriteToText("./out/dict_demo")
    )
```

The output file contains:

```text
{'region': 'EMEA', 'revenue_eur': 118423.22}
```

Not:

```text
EMEA,118423.22
```

That is a Python dict repr, with single quotes, with a space after the
colon, and with the field order being the dict's insertion order — not
your intended column order.

This is exactly the bug that `project/transforms.py`'s
`format_summary_csv` exists to fix. The function's docstring says it
outright:

```text
`WriteToText` writes whatever string it is given, so the dict must be
formatted explicitly. Using `csv.writer` rather than an f-string means a
region name containing a comma cannot corrupt the output.
```

#### The fix: format the element before it reaches the sink

```python
import csv
import io


def format_summary_csv(row):
    """Format one summary row as a CSV line."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            row.get("region", ""),
            row.get("order_count", 0),
            row.get("revenue_eur", 0.0),
        ]
    )
    return buffer.getvalue().rstrip("\r\n")
```

Two details in that function that matter:

1. **`csv.writer`, not an f-string.** A region name containing a comma
   (`"EMEA, West"`) would, in an f-string, produce two columns and
   corrupt the row. `csv.writer` quotes it properly. A f-string version
   is *almost* right and fails on exactly the data you did not test with.
2. **`.rstrip("\r\n")`.** `csv.writer` terminates each row with `\r\n`.
   `WriteToText` then adds another `\n` (because
   `append_trailing_newlines=True`), giving you `\r\n\n` — a blank line
   between every record. Stripping the writer's own terminator and
   letting `WriteToText` add one gives exactly one newline per record.

And the pipeline:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "Read" >> beam.io.ReadFromText("./sample_data/orders.csv", skip_header_lines=1)
        | "Parse" >> beam.Map(lambda line: line.split(","))
        | "Key" >> beam.Map(lambda row: (row[3], float(row[7])))
        | "Sum" >> beam.CombinePerKey(sum)
        | "ToRow" >> beam.Map(lambda kv: {"region": kv[0], "revenue_eur": kv[1]})
        | "Format" >> beam.Map(format_summary_csv)
        | "Write" >> beam.io.WriteToText(
            "./out/summary",
            header="region,revenue_eur",
            num_shards=1,
            shard_name_template="",
        )
    )
```

The `Format` step is not optional decoration. It is the step that
converts a structured element into the text the sink expects. Skipping it
is the bug.

> **The general rule.** `WriteToText` writes *strings*. If your PCollection
> contains dicts, tuples, or numbers, something must convert them to
> strings first, and that something is a `Map` you have to write. This is
> not a limitation of the SDK; it is the design. A text sink has no idea
> what your data means.

### `WriteToCsv` — the built-in alternative

Beam also ships `beam.io.WriteToCsv`, which does the formatting for you:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "Read" >> beam.io.ReadFromText("./sample_data/orders.csv", skip_header_lines=1)
        | "Parse" >> beam.Map(lambda line: line.split(","))
        | "Dict" >> beam.Map(
            lambda row: {
                "order_id": row[0],
                "region": row[3],
                "amount": row[7],
            }
        )
        | "Write" >> beam.io.WriteToCsv(
            "./out/orders_csv",
            header=["order_id", "region", "amount"],
        )
    )
```

`WriteToCsv` writes proper CSV with quoting. It is less code and it is
correct.

Its actual signature is worth knowing, because it is not the same shape
as `WriteToText`:

```text
WriteToCsv(path, num_shards=None, file_naming=None, **kwargs)
```

Everything in `**kwargs` is forwarded to `pandas.DataFrame.to_csv`. That
is where `header=` comes from — and it means `header` is a **pandas**
parameter, not a Beam one:

- `header=True` (the pandas default) writes the column names from the
  dict keys.
- `header=["order_id", "region", "amount"]` writes those names in that
  order.
- `header=False` writes no header row at all.

Three practical consequences:

- **`WriteToCsv` and `WriteToText` do not have the same `header`
  parameter.** `WriteToText` takes `header="region,order_count"` — a
  *string* it writes verbatim. `WriteToCsv` takes a *list* of column
  names. Passing the string form to `WriteToCsv` is a pandas error, not
  a Beam error, and the traceback points at pandas.
- **The column order comes from the dict keys**, and pandas' `to_csv`
  uses the dict's key order for a list of dicts. Python 3.7+ preserves
  insertion order, so the order is deterministic — but a refactor that
  reorders the dict construction reorders the file. Pass the list
  explicitly to make the contract visible.
- **The file naming is different.** `WriteToCsv` uses
  `fileio.default_file_naming`, which names files `path-XXXXX-of-NNNNN`
  — the same shape as `WriteToText`'s default, but a different mechanism,
  and it does not accept `shard_name_template`. To get a single
  predictable file, use `num_shards=1` and a `file_naming` of your own,
  or use `WriteToText` with `shard_name_template=""`.

### The runner caveat for `WriteToCsv` and `WriteToJson`

`WriteToCsv` and `WriteToJson` are **DataFrame-API** transforms. They
need the `apache-beam[dataframe]` extra, which is not installed by
default:

```text
ImportError: Please install apache_beam[dataframe]
```

Installing it is necessary but not sufficient. These transforms require
a **schema-aware** PCollection, and they convert that PCollection into a
`pandas.DataFrame` using the batched `DoFn.process_batch` API. The
course's default runner is `BundleBasedDirectRunner`, and that runner
dispatches the element-wise `process` method — so the batched path
raises:

```text
RuntimeError: NotImplementedError [while running 'Write/BatchElements(pcoll)']
  at apache_beam/transforms/core.py line 742, in process
    raise NotImplementedError
```

The `NotImplementedError` comes from the base `DoFn.process`, which is
what the runner calls when a `DoFn` only implements `process_batch`. The
transform itself is fine; the runner is calling the wrong method.

Two fixes, in order of preference:

**1. Use `PrismRunner`.** It implements the batched `process_batch`
dispatch correctly, and `WriteToCsv` / `WriteToJson` work as documented:

```bash
.venv/bin/python your_pipeline.py --runner=PrismRunner
```

PrismRunner is the portable, future-facing runner in Beam 2.77, and it
runs the same Python `DoFn` code that `DataflowRunner` runs on the
service.

**2. Make the PCollection schema-aware and use `beam.Row`.** A plain
dict does not carry a schema, so Beam cannot infer the columns:

```text
TypeError: Could not determine schema for type hint Dict[<class 'str'>, Union[<class 'int'>, <class 'str'>]].
Did you mean to create a schema-aware PCollection? See https://s.apache.org/beam-python-schemas
```

`beam.Row` carries the schema with the element, so Beam can infer the
columns:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create([{"a": 1, "b": "x"}])
        | "ToRow" >> beam.Map(lambda d: beam.Row(a=d["a"], b=d["b"]))
        | "Write" >> beam.io.WriteToCsv("./out/csv")
    )
```

Under `PrismRunner` that writes:

```text
a,b
1,x
```

> **Do not confuse the two `header` meanings.** `WriteToText(header=...)`
> takes a **string** it writes verbatim as the first line.
> `WriteToCsv(header=...)` takes a **pandas** header — `True`, `False`,
> or a list of column names — and forwards it to `to_csv`.
>
> Do not confuse `WriteToJson`'s `orient` either. It is also a pandas
> parameter, forwarded from
> `WriteToJson(path, *, num_shards=None, file_naming=None, orient="records", lines=None, **kwargs)`.
> The default `orient="records"` gives one JSON object per line, which is
> the NDJSON shape most consumers expect. `orient="columns"` gives a
> column-oriented layout instead.

For the course, the explicit `format_summary_csv` + `WriteToText` path is
used, because it makes the formatting visible, it works on every runner,
and it has no extra dependency. In a project where you want the simplest
thing that works and you control the runner, `WriteToCsv` is the right
call.

### `WriteToJson`

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create([{"a": 1, "b": "x"}])
        | "ToRow" >> beam.Map(lambda d: beam.Row(a=d["a"], b=d["b"]))
        | "Write" >> beam.io.WriteToJson("./out/json")
    )
```

Like `WriteToCsv`, `WriteToJson` is a DataFrame-API transform, needs
`apache-beam[dataframe]`, needs a schema-aware input, and fails under
`BundleBasedDirectRunner` with the same `NotImplementedError`. Run it
under `PrismRunner`, and it writes one JSON object per line:

```text
{"a":1,"b":"x"}
```

The portable equivalent — and the one the course project uses — is
`WriteToText` + `json.dumps`:

```python
import json

import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create([{"a": 1, "b": "x"}])
        | "Encode" >> beam.Map(json.dumps)
        | "Write" >> beam.io.WriteToText("./out/json")
    )
```

`json.dumps` is the exact analogue of `csv.writer` for JSON: it escapes
correctly, it does not depend on dict insertion order for its output, and
it produces a valid JSON document per line.

### `WriteToAvro`

```python
import apache_beam as beam

AVRO_SCHEMA = {
    "type": "record",
    "name": "Order",
    "fields": [
        {"name": "order_id", "type": "string"},
        {"name": "region", "type": "string"},
        {"name": "amount", "type": "double"},
    ],
}

with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create([
            {"order_id": "o1", "region": "EMEA", "amount": 10.5},
        ])
        | "Write" >> beam.io.WriteToAvro(
            "./out/orders.avro",
            schema=AVRO_SCHEMA,
            file_name_suffix=".avro",
        )
    )
```

`WriteToAvro` parameters that matter:

| Parameter | Default | Notes |
|---|---|---|
| `schema` | `None` | An Avro schema **as a dict**. Required if the elements do not carry one. |
| `codec` | `'deflate'` | Block compression. Any Avro codec name. |
| `use_fastavro` | `True` | Use the `fastavro` library. Faster, and the schema is written into the file header. |
| `file_name_suffix` | `''` | Set to `'.avro'` so the file is identifiable. |

Avro's payoff is **schema evolution**. The schema is written into the
file's header, so a reader that does not know a new field skips it, and a
reader that needs a field the writer did not have gets `null`. If your
downstream consumers evolve independently of your producers, Avro removes
a whole class of "the pipeline broke because someone added a column"
incidents.

### `WriteToParquet`

```python
import apache_beam as beam
import pyarrow

PARQUET_SCHEMA = pyarrow.schema(
    [
        ("order_id", pyarrow.string()),
        ("region", pyarrow.string()),
        ("amount", pyarrow.float64()),
    ]
)

with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create([
            {"order_id": "o1", "region": "EMEA", "amount": 10.5},
        ])
        | "Write" >> beam.io.WriteToParquet(
            "./out/orders.parquet",
            schema=PARQUET_SCHEMA,
            file_name_suffix=".parquet",
        )
    )
```

`WriteToParquet` takes a **`pyarrow.schema`**, not a dict. That is the
biggest difference from `WriteToAvro` and it is a common trip-up. Other
parameters:

| Parameter | Default | Notes |
|---|---|---|
| `schema` | `None` | A `pyarrow.Schema`. |
| `row_group_buffer_size` | 64 MB | The row-group size. Also the split boundary for readers. |
| `record_batch_size` | 1000 | Rows per record batch. |
| `codec` | `'none'` | `snappy` is the usual choice — fast, and well supported everywhere. |
| `use_compliant_nested_type` | `False` | Parquet v2 nested-type layout. |

Parquet is the right output when the consumer is an analytics engine:
BigQuery, Bigtable, Spark, Snowflake, DuckDB. It is columnar, so a
consumer that reads 3 of 100 columns reads roughly 3% of the bytes. The
cost is that Parquet is not human-readable and not line-oriented.

### `WriteToBigQuery`

`WriteToBigQuery` is the most parameter-heavy sink in the SDK.

```text
(table, dataset=None, project=None, schema=None,
 create_disposition='CREATE_IF_NEEDED', write_disposition='WRITE_APPEND', ...)
```

#### The table reference

The `table`/`dataset`/`project` triple has a shorthand. When `dataset` is
`None`, the `table` argument must carry the whole reference:

```text
DATASET.TABLE
PROJECT:DATASET.TABLE
```

Note the **colon** in the project-qualified form. This is BigQuery's API
convention, not a typo, and it is a genuine trap — `project.dataset.table`
with dots is **not** accepted here.

```python
import apache_beam as beam

# Fully qualified, with the colon
beam.io.WriteToBigQuery(
    "YOUR_PROJECT_ID:sales.orders_by_region",
    schema=SCHEMA,
)
```

```python
import apache_beam as beam

# Or the triple
beam.io.WriteToBigQuery(
    "orders_by_region",
    dataset="sales",
    project="YOUR_PROJECT_ID",
    schema=SCHEMA,
)
```

#### The schema requirement

**`WriteToBigQuery` needs a `schema` unless the table already exists and
`CREATE_IF_NEEDED` can use the existing table's schema.** The `schema`
parameter accepts:

- A dict in the BigQuery API schema format.
- A JSON string in the BigQuery API schema format.
- A `Schema` object.
- A callable that returns one of the above, receiving the element.

The dict form:

```python
import apache_beam as beam

ORDER_SCHEMA = {
    "fields": [
        {"name": "order_id", "type": "STRING", "mode": "REQUIRED"},
        {"name": "region", "type": "STRING", "mode": "NULLABLE"},
        {"name": "amount", "type": "FLOAT", "mode": "NULLABLE"},
    ]
}
```

The `fields` wrapper is required. A bare list of field dicts is not
accepted.

The three-part form — `name`, `type`, `mode` — is the BigQuery schema
format. `mode` is one of `REQUIRED`, `NULLABLE`, or `REPEATED`. Beam's
`mode` handling for `REQUIRED` and `NULLABLE` is equivalent (both allow
nulls on the read side in practice), but `REPEATED` means the field is an
array.

**The `CREATE_IF_NEEDED` inference question.** When
`create_disposition=CREATE_IF_NEEDED` and the table does not yet exist,
Beam *can* create it. But:

- If `schema` is `None`, Beam has nothing to create the table from, and
  the job fails with a schema error.
- If the table *does* exist, `CREATE_IF_NEEDED` is a no-op and the
  existing table's schema is used.

So the practical rule is: **always pass a `schema`.** It is required for
the create case, harmless for the existing-table case, and it documents
the contract in the code where a reader can see it.

The `SCHEMA_AUTODETECT` constant exists:

```python
import apache_beam as beam

beam.io.WriteToBigQuery(
    "YOUR_PROJECT_ID:sales.events",
    schema=beam.io.SCHEMA_AUTODETECT,
    create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
    write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
)
```

but it is only supported with the `FILE_LOADS` method — **not** with
streaming inserts, where Beam raises:

```text
ValueError: Schema auto-detection is not supported for streaming inserts
into BigQuery. Only for File Loads.
```

And with Avro-based file loads it is also rejected:

```text
ValueError: Schema auto-detection is not supported when using Avro based
file loads into BigQuery. Please specify a schema or set
temp_file_format="NEWLINE_DELIMITED_JSON"
```

#### `write_disposition` — what happens to the existing rows

| Value | Behaviour | Use when |
|---|---|---|
| `WRITE_APPEND` | Add rows to whatever is there. The default. | Streaming, and incremental batch. |
| `WRITE_TRUNCATE` | Delete everything, then write. | Idempotent full refresh. |
| `WRITE_EMPTY` | Write only if the table is **empty**; fail otherwise. | "Write once" semantics — a guard against double-processing. |

`WRITE_APPEND` is the default, and it is a footgun in batch pipelines: run
the job twice and you have double the data, with no error. If your batch
job is a full refresh, use `WRITE_TRUNCATE` — then re-running it is
idempotent, and a consumer that reads the table always sees a coherent
snapshot.

`WRITE_EMPTY` is the safest of the three for exactly-once-ish semantics:
if the table already has rows, the job fails loudly rather than
duplicating. Combine it with `id_label`-style primary-key logic for
stronger guarantees.

#### `create_disposition` — what happens if the table is missing

| Value | Behaviour |
|---|---|
| `CREATE_IF_NEEDED` | Create the table if it does not exist. The default. |
| `CREATE_NEVER` | Fail if the table does not exist. |

`CREATE_NEVER` is a genuine safety control: it means the job will not
silently create a table with a subtly wrong schema. Use it when the table
is managed by a migration tool and a job should not be able to create it.

#### The retry and job options

The write path has two distinct mechanisms, and it is worth being precise
about which is which — because a lot of advice on this topic names
parameters that do not exist.

**Streaming inserts** use `insert_retry_strategy` and `max_retries`:

```python
import apache_beam as beam

beam.io.WriteToBigQuery(
    "YOUR_PROJECT_ID:sales.events",
    schema=EVENT_SCHEMA,
    write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
    create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
    insert_retry_strategy=beam.io.BigQueryDisposition.WRITE_APPEND,
    max_retries=10000,
)
```

`insert_retry_strategy` accepts a `google.api_core.retry.Retry` object or
`None` (no retry). `max_retries` caps the number of streaming-insert
retries and is bounded by BigQuery's own quota limit — Beam raises if you
exceed it.

**File loads** use a different path: Beam writes NDJSON or Avro files to a
temporary GCS location and submits a BigQuery **load job**. The relevant
parameters are `custom_gcs_temp_location`, `temp_file_format`,
`max_file_size`, and `max_files_per_bundle`.

> **A note on names you will see in older examples.** There is no
> `bigquery_jobs_insert_retries` parameter and no `with_job` method on
> `WriteToBigQuery` in Beam 2.77. Both appear in old blog posts and in
> the `google-cloud-bigquery` client's own API (which is a different
> library with a different surface). If you are porting code that uses
> them, the 2.77 equivalents are `insert_retry_strategy` / `max_retries`
> for streaming inserts, and the `custom_gcs_temp_location` /
> `temp_file_format` family for file loads. Verify against
> `inspect.signature(beam.io.WriteToBigQuery)` before you copy any
> parameter name from a tutorial.

#### The streaming-specific constraints

`WriteToBigQuery` behaves differently in a streaming pipeline, and the
differences are enforced at pipeline construction time:

- `with_auto_sharding=True` is **streaming-only**. In a batch pipeline it
  raises:

  ```text
  ValueError: with_auto_sharding is not applicable to batch pipelines.
  ```

- `triggering_frequency` with `STREAMING_INSERTS` requires
  `with_auto_sharding=True`:

  ```text
  ValueError: triggering_frequency with STREAMING_INSERTS can only be used
  with with_auto_sharding=True.
  ```

- `schema_update_options` is only supported with `FILE_LOADS`:

  ```text
  ValueError: schema_update_options is only supported when writing to
  BigQuery with FILE_LOADS.
  ```

A complete BigQuery write, as the course project does it:

```python
import apache_beam as beam

SUMMARY_SCHEMA = {
    "fields": [
        {"name": "region", "type": "STRING", "mode": "REQUIRED"},
        {"name": "order_count", "type": "INTEGER", "mode": "REQUIRED"},
        {"name": "revenue_eur", "type": "FLOAT", "mode": "NULLABLE"},
    ]
}

with beam.Pipeline() as p:
    (
        p
        | "Read" >> beam.io.ReadFromText("./sample_data/orders.csv", skip_header_lines=1)
        | "Parse" >> beam.Map(lambda line: line.split(","))
        | "Key" >> beam.Map(lambda row: (row[3], float(row[7])))
        | "Sum" >> beam.CombinePerKey(sum)
        | "ToRow" >> beam.Map(
            lambda kv: {
                "region": kv[0],
                "order_count": 1,
                "revenue_eur": kv[1],
            }
        )
        | "WriteBigQuery" >> beam.io.WriteToBigQuery(
            "YOUR_PROJECT_ID:sales.orders_by_region",
            schema=SUMMARY_SCHEMA,
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE,
        )
    )
```

### `WriteToPubSub`

```text
(topic: str, with_attributes: bool = False, id_label: Optional[str] = None,
 timestamp_attribute: Optional[str] = None, publish_with_ordering_key: bool = False)
```

| Parameter | Effect |
|---|---|
| `topic` | `projects/<p>/topics/<t>`. |
| `with_attributes` | `True` → elements are `PubsubMessage` objects; `False` → elements are `bytes`. |
| `id_label` | Sets an **attribute** named `id_label`'s value on each message, with a unique value per message. Used by `ReadFromPubSub(id_label=...)` for deduplication. |
| `timestamp_attribute` | Sets an attribute carrying the message's publish time. |
| `publish_with_ordering_key` | Enables ordered publishing within an ordering key. |

The `id_label` round trip is the interesting part. When you write with
`id_label="event_id"`, each message carries an attribute whose name is
`event_id` and whose value is the element's `event_id`. When you later
read with `id_label="event_id"`, Beam knows the identity of each record
and can deduplicate within the run.

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create([
            {"event_id": "e1", "payload": "hello"},
        ])
        | "ToMessage" >> beam.Map(
            lambda e: beam.io.PubsubMessage(
                data=e["payload"].encode("utf-8"),
                attributes={"event_id": e["event_id"]},
            )
        )
        | "Write" >> beam.io.WriteToPubSub(
            topic="projects/YOUR_PROJECT_ID/topics/events",
            with_attributes=True,
            id_label="event_id",
        )
    )
```

> **`id_label` on the write side is a *name*, not a value.** It says
> "put a unique id in the attribute called `event_id`". It does not
> extract the field for you — the element you write must already carry
> the identity, and Beam's `PubsubMessage` construction is what places
> it in the attribute.

The `publish_with_ordering_key=True` option enables message ordering
within an ordering key. It requires the element to have an
`ordering_key` attribute, and it comes with a real cost: **ordering keys
reduce throughput**, because messages sharing a key must go through the
same ordering path.

---

## 🛠️ Hands-On: Writing to Local and GCS Paths

### Step 1 — the naive write, and what it produces

```bash
cd data-engineering/data-Course/google/Dataflow
.venv/bin/python - <<'PY'
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])

with beam.Pipeline(options=options) as p:
    (
        p
        | "Create" >> beam.Create([
            {"region": "EMEA", "revenue_eur": 118423.22},
            {"region": "AMER", "revenue_eur": 113592.19},
        ])
        | "Write" >> beam.io.WriteToText("./out/naive")
    )
PY
```

```bash
ls out/naive*
cat out/naive*
```

Output — note the dict reprs:

```text
{'region': 'EMEA', 'revenue_eur': 118423.22}
{'region': 'AMER', 'revenue_eur': 113592.19}
```

And note the filename: `out/naive-00000-of-00001`.

### Step 2 — the correct write, with `csv.writer`

```bash
.venv/bin/python - <<'PY'
import csv
import io

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])


def format_summary_csv(row):
    """Format one summary row as a CSV line."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            row.get("region", ""),
            row.get("order_count", 0),
            row.get("revenue_eur", 0.0),
        ]
    )
    return buffer.getvalue().rstrip("\r\n")


with beam.Pipeline(options=options) as p:
    (
        p
        | "Create" >> beam.Create([
            {"region": "EMEA", "order_count": 322, "revenue_eur": 118423.22},
            {"region": "AMER", "order_count": 318, "revenue_eur": 113592.19},
        ])
        | "Format" >> beam.Map(format_summary_csv)
        | "Write" >> beam.io.WriteToText(
            "./out/summary",
            header="region,order_count,revenue_eur",
            num_shards=1,
            shard_name_template="",
        )
    )
PY
```

```bash
ls out/summary*
cat out/summary*
```

Output:

```text
region,order_count,revenue_eur
EMEA,322,118423.22
AMER,318,113592.19
```

And the filename is exactly `out/summary` — no shard suffix, because of
`shard_name_template=""`.

### Step 3 — prove the `csv.writer` advantage

```bash
.venv/bin/python - <<'PY'
import csv
import io

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])


def format_with_csv(row):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([row["region"], row["order_count"]])
    return buffer.getvalue().rstrip("\r\n")


def format_with_fstring(row):
    return f"{row['region']},{row['order_count']}"


ROWS = [{"region": "EMEA, West", "order_count": 322}]

with beam.Pipeline(options=options) as p:
    (
        p
        | "Create" >> beam.Create(ROWS)
        | "FormatCsv" >> beam.Map(format_with_csv)
        | "WriteCsv" >> beam.io.WriteToText("./out/quoting_csv")
    )

with beam.Pipeline(options=options) as p:
    (
        p
        | "Create" >> beam.Create(ROWS)
        | "FormatFstring" >> beam.Map(format_with_fstring)
        | "WriteFstring" >> beam.io.WriteToText("./out/quoting_fstring")
    )
PY
```

```bash
echo "--- csv.writer ---"
cat out/quoting_csv*
echo "--- f-string ---"
cat out/quoting_fstring*
```

```text
--- csv.writer ---
"EMEA, West",322
--- f-string ---
EMEA, West,322
```

The f-string version is corrupt: three columns where there should be two.
Any region, customer name, or free-text field containing a comma breaks
it. This is the bug that only shows up in production data.

### Step 4 — see the sharding

Force a shard count and look at the filenames:

```bash
.venv/bin/python - <<'PY'
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])

with beam.Pipeline(options=options) as p:
    (
        p
        | "Create" >> beam.Create([f"row-{i}" for i in range(200)])
        | "Write" >> beam.io.WriteToText("./out/sharded", num_shards=4)
    )
PY
```

```bash
ls -1 out/sharded*
```

```text
out/sharded-00000-of-00004
out/sharded-00001-of-00004
out/sharded-00002-of-00004
out/sharded-00003-of-00004
```

```bash
cat out/sharded* | wc -l
```

`200`. Every row is there, spread across four files, and the count is in
each filename.

### Step 5 — the `gs://` path shape

The code does not change when the path does. Only the path string:

```bash
.venv/bin/python - <<'PY'
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])

OUTPUT = "gs://YOUR_BUCKET/dataflow/summary"

with beam.Pipeline(options=options) as p:
    (
        p
        | "Read" >> beam.io.ReadFromText(
            "./sample_data/orders.csv",
            skip_header_lines=1,
        )
        | "Parse" >> beam.Map(lambda line: line.split(","))
        | "Key" >> beam.Map(lambda row: (row[3], float(row[7])))
        | "Sum" >> beam.CombinePerKey(sum)
        | "ToRow" >> beam.Map(
            lambda kv: {"region": kv[0], "revenue_eur": round(kv[1], 2)}
        )
        | "Format" >> beam.Map(
            lambda row: f"{row['region']},{row['revenue_eur']:.2f}"
        )
        | "Write" >> beam.io.WriteToText(
            OUTPUT,
            header="region,revenue_eur",
            file_name_suffix=".csv",
        )
    )
PY
```

The output objects are:

```text
gs://YOUR_BUCKET/dataflow/summary-00000-of-00001.csv
```

To see them:

```bash
gsutil ls gs://YOUR_BUCKET/dataflow/
gsutil cat gs://YOUR_BUCKET/dataflow/summary-00000-of-00001.csv
```

> **The `gs://` path is a prefix, not a file.** This is the single most
> common GCS mistake: writing to `gs://bucket/summary.csv` produces
> `gs://bucket/summary.csv-00000-of-00001` — the shard suffix is appended
> to whatever you passed. If you want a predictable single object, write
> to `gs://bucket/summary` with `num_shards=1` and
> `shard_name_template=""`.

### Step 6 — compressed output

```bash
.venv/bin/python - <<'PY'
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])

with beam.Pipeline(options=options) as p:
    (
        p
        | "Create" >> beam.Create([f"row-{i}" for i in range(100)])
        | "Write" >> beam.io.WriteToText(
            "./out/compressed",
            file_name_suffix=".csv.gz",
        )
    )
PY
```

```bash
ls -1 out/compressed*
gunzip -c out/compressed*.gz | wc -l
```

The filename ends in `.gz`, and `compression_type='auto'` compressed it.
100 rows come back out.

### Step 7 — the full course pipeline, and its output contract

```bash
python project/batch_pipeline.py \
    --input ./sample_data/orders.csv \
    --output ./out/summary
```

```bash
ls -1 out/summary*
cat out/summary*
```

```text
region,order_count,revenue_eur
AMER,318,113592.19
APAC,285,108194.92
EMEA,322,118423.22
LATAM,320,110646.18
```

The output contract is:

| Property | Value |
|---|---|
| Path | `./out/summary` (a prefix in the general case) |
| Filename | Exactly `summary` — single file, predictable name |
| Format | CSV, comma-separated, no quoting needed for this data |
| Header | `region,order_count,revenue_eur`, written once |
| Row count | 4 (one per region) |
| Re-run | Overwrites. Deterministic. |

A downstream job can depend on every one of those.

---

## 🛠️ Common Errors and Fixes

### The output contains `{'region': 'EMEA', ...}` instead of CSV

The `str()` trap. You wrote dicts directly to a text sink. Format them
first:

```text
| "Format" >> beam.Map(format_summary_csv)
| "Write" >> beam.io.WriteToText("./out/summary", header="region,order_count,revenue_eur")
```

### The output has a blank line between every record

`csv.writer` terminates rows with `\r\n`, and `WriteToText` adds another
`\n`. Strip the writer's terminator:

```python
return buffer.getvalue().rstrip("\r\n")
```

### The header appears once per file, and there are four files

That is correct. `WriteToText` writes the header into **every** shard so
each file is independently readable. If you need one header across the
whole dataset, concatenate the shards and keep only the first — or write
with `num_shards=1`.

### The output file is named `summary00000of00004` and my glob `summary*` returns nothing

Check the hyphen. In Beam 2.77 the default template is
`-SSSSS-of-NNNNN`, so the file is `summary-00000-of-00004`. Always glob
with `summary*`, never with the full name.

### `ValueError: Invalid create disposition ...`

`create_disposition` must be one of `CREATE_IF_NEEDED` or `CREATE_NEVER`.
Use the constants:

```python
create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED
```

### `ValueError: Invalid write disposition ...`

`write_disposition` must be one of `WRITE_APPEND`, `WRITE_TRUNCATE`, or
`WRITE_EMPTY`.

### `ValueError: A schema must be provided when writing to BigQuery using Avro based file loads`

`WriteToBigQuery` with Avro temp files needs an explicit `schema`. Pass
one, or switch the temp format:

```python
beam.io.WriteToBigQuery(
    table,
    schema=MY_SCHEMA,
    temp_file_format="NEWLINE_DELIMITED_JSON",
)
```

### `ValueError: Schema auto-detection is not supported for streaming inserts into BigQuery`

`SCHEMA_AUTODETECT` only works with `FILE_LOADS`. Pass an explicit
schema.

### `ValueError: with_auto_sharding is not applicable to batch pipelines`

`with_auto_sharding` is streaming-only. Remove it, or set
`--streaming` and make the pipeline a streaming one.

### `ValueError: schema_update_options is only supported when writing to BigQuery with FILE_LOADS`

Same family of constraint. `schema_update_options` needs file loads, not
streaming inserts.

### `ValueError: max_retries cannot be more than 10000`

`max_retries` is bounded by BigQuery's streaming-insert quota limit. Beam
raises rather than letting you set an impossible value.

### `TypeError: WriteToParquet.__init__() got an unexpected keyword argument 'schema_dict'`

`WriteToParquet` takes a `pyarrow.Schema` object under the name
`schema`, not a dict:

```python
import pyarrow

schema = pyarrow.schema([("region", pyarrow.string())])
beam.io.WriteToParquet("./out/rows", schema=schema)
```

### `ImportError: Please install apache_beam[dataframe]`

`beam.io.WriteToCsv` and `beam.io.WriteToJson` are DataFrame-API
transforms. Use `WriteToText` + `csv.writer` / `json.dumps` instead, or
install the extra.

### `RuntimeError: NotImplementedError [while running 'Write/BatchElements(pcoll)']`

You ran `WriteToCsv` or `WriteToJson` under `BundleBasedDirectRunner`.
Those transforms use the batched `DoFn.process_batch` API, and the
`BundleBasedDirectRunner` calls the element-wise `process` method
instead, which the base `DoFn` leaves as `raise NotImplementedError`.

Run the pipeline with `--runner=PrismRunner`, and make the input
schema-aware with `beam.Row` so Beam can infer the columns.

### `TypeError: Could not determine schema for type hint Dict[...]`

`WriteToCsv` and `WriteToJson` need a schema-aware PCollection, and a
plain dict does not carry one. Convert the elements to `beam.Row` first:

```text
| "ToRow" >> beam.Map(lambda d: beam.Row(a=d["a"], b=d["b"]))
```

### The output file exists but is empty

Two causes:

1. The PCollection was empty. `WriteToText` still creates the shard files
   unless you pass `skip_if_empty=True`.
2. The pipeline failed. Check the job's logs — a sink failure is a job
   failure, and the file may be created before the failure.

### `PermissionDenied` writing to `gs://`

Under the local runner, the credentials in effect are application default
credentials:

```bash
gcloud auth application-default login
```

Under `DataflowRunner`, the service account needs
`roles/storage.objectAdmin` (or `roles/storage.objectCreator` for
write-only prefixes).

---

## 💡 Production Notes

- **The output contract is a document.** Write down the path, the
  filename pattern, the format, the schema, the column order, the shard
  count behaviour, and the re-run semantics. Put it in the repo. The
  person who maintains the consumer is not you.
- **Use `WRITE_TRUNCATE` for batch full-refresh writes.** `WRITE_APPEND`
  is the default and it means a re-run duplicates your data with no
  error. A batch job that overwrites its own output is idempotent, and
  idempotent jobs are the ones you can re-run at 3am without thinking.
- **Never use `WRITE_APPEND` for a batch pipeline without a
  deduplication key.** If you must append, the write has to be idempotent
  at the row level — a BigQuery `MERGE` on a primary key, not a plain
  insert.
- **Shard count in the filename is a correctness feature, not
  decoration.** A consumer that sees `summary-00000-of-00004` through
  `summary-00003-of-00004` knows it has the complete output. A consumer
  that sees three of four knows the job died. Do not strip the suffix to
  "tidy up" the filenames.
- **Small aggregates: one file, predictable name.** `num_shards=1` with
  `shard_name_template=""` gives a deterministic path that a downstream
  job can poll without listing. Large outputs: let the runner choose the
  shard count.
- **Choose the output format for the consumer, not for you.** CSV for
  humans and for tools that read CSV. JSON Lines for event streams and
  for anything that will be re-parsed. Parquet for analytics engines that
  read a subset of columns. Avro for schema evolution across teams.
  BigQuery for anything that will be queried in SQL.
- **Do not rely on dict insertion order for CSV column order.** It is
  preserved in Python 3.7+, but a refactor that reorders the dict
  reorders the file. Pass the column list explicitly to `WriteToCsv`, or
  use an explicit formatter.
- **`WriteToText` calls `str()`.** Always ask what `str()` does to your
  element type. For a dict it is a repr. For a `datetime` it is
  `2026-01-15 00:54:38+00:00`, not ISO-8601. For a `Decimal` it is
  `'12.34'`, which may not be what the consumer wants.
- **Compression is decided by the output file extension**, via
  `compression_type='auto'`. If your output is not compressed and you
  expected it to be, check the suffix. Gzip costs CPU on both ends; for
  Parquet, use `codec='snappy'` instead — Parquet's own encoding already
  does most of the work.
- **BigQuery `WriteToBigQuery` uses the Java SDK.** It needs a JVM on the
  worker. On `DataflowRunner` that is always available. On a local runner
  it is not, unless you install a JRE and set `JAVA_HOME`.
- **Pub/Sub `id_label` on the write side is a contract with the read
  side.** If you write with `id_label="event_id"` and read with
  `id_label="order_id"`, deduplication silently does nothing. Put the
  attribute name in a shared constant.
- **Message ordering costs throughput.** `publish_with_ordering_key=True`
  routes messages with the same key down one path, which limits
  parallelism. Use it only where the business requires it, and prefer
  sorting downstream where you can.

---

## 🔑 Key Takeaways

- `WriteToText` writes **sharded** files named
  `<prefix>-<shard>-of-<count><suffix>`. The count is in the name so a
  consumer can detect an incomplete write.
- `num_shards=0` (the default) lets the runner decide. `num_shards=1`
  plus `shard_name_template=""` gives one file with a predictable name —
  correct for small aggregates, a bottleneck for large ones.
- `file_name_suffix` names the format **and** drives compression
  detection, because `compression_type='auto'` looks at the final
  extension.
- `header` is written into **every** shard, so each file is independently
  readable.
- **`WriteToText` calls `str()` on each element.** Dicts come out as
  Python reprs. Format them first with `csv.writer` (which also quotes
  correctly) or `json.dumps`.
- `WriteToAvro` takes a schema **dict**; `WriteToParquet` takes a
  **`pyarrow.Schema`**. They are not interchangeable.
- `WriteToBigQuery` needs an explicit `schema` for the create case, uses
  `WRITE_APPEND` / `WRITE_TRUNCATE` / `WRITE_EMPTY` for the write
  disposition, and takes a fully-qualified table as
  `PROJECT:DATASET.TABLE` — with a **colon**.
- `WriteToPubSub`'s `id_label` writes a unique-id attribute that
  `ReadFromPubSub`'s `id_label` can use for deduplication. The two names
  must match.
- There is no `bigquery_jobs_insert_retries` and no `with_job` in Beam
  2.77. The real knobs are `insert_retry_strategy` and `max_retries` for
  streaming inserts, and the `custom_gcs_temp_location` /
  `temp_file_format` family for file loads.

---

## 📚 Practice Exercises

1. **Build the output contract table.** For each of the four sinks
   (`WriteToText`, `WriteToJson`, `WriteToParquet`, `WriteToBigQuery`),
   write down the full contract: what the consumer must know to read the
   output correctly. Then identify which contract elements are *not*
   discoverable from the data itself — those are the ones you must
   document.

2. **Prove the `str()` trap for three types.** Write a PCollection
   containing a dict, a `datetime`, and a `float`, and write it directly
   with `WriteToText`. Then write it through a formatting `Map` and
   compare. For the datetime, show the difference between `str(dt)` and
   `dt.isoformat()` and say which one a downstream consumer usually
   wants.

3. **Explore the shard template.** Produce the same output with four
   different `shard_name_template` values: `None`, `'-SSSSS-of-NNNNN'`,
   `'-W-SSSSS-of-NNNNN'`, and `''`. Record the resulting filenames. Then
   determine which of the four the course's own `batch_pipeline.py` uses
   and what the consequence is for a consumer.

4. **Prove that `csv.writer` beats f-strings.** Generate 1000 region names,
   10% of which contain a comma, a quote, or a newline. Write them with
   both approaches. Then read both outputs back with Python's `csv.reader`
   and show that the f-string version does not round-trip. Count the rows
   that fail to parse.

5. **Implement a proper CSV writer without the DataFrame extra.** Write
   a `format_row` function that takes a dict and an explicit list of
   column names, uses `csv.writer`, and returns a single line. Make it
   handle: missing keys (empty string), `None` values (empty string),
   embedded commas and quotes, and non-ASCII characters. Verify with
   `csv.reader` round-trip.

6. **Design the idempotent BigQuery write.** Write a Beam pipeline that
   appends to a BigQuery table and is safe to re-run. Explain why
   `WRITE_APPEND` alone is not safe, what `WRITE_TRUNCATE` trades away,
   and how you would use a `primary_key` with `use_cdc_writes` to get
   exactly-once semantics for an update stream. State clearly which of
   your guarantees depend on the sink and which depend on the source.

---

## 📖 Further Reading

- Apache Beam `WriteToText` reference — https://beam.apache.org/releases/pydoc/current/apache_beam.io.textio.html
- Apache Beam `WriteToBigQuery` reference — https://beam.apache.org/releases/pydoc/current/apache_beam.io.gcp.bigquery.html
- Apache Beam `WriteToPubSub` reference — https://beam.apache.org/releases/pydoc/current/apache_beam.io.gcp.pubsub.html
- Apache Beam file-based I/O documentation — https://beam.apache.org/documentation/io/file-based-io/
- Apache Beam Python API reference — https://beam.apache.org/releases/pydoc/current/index.html
- Google Cloud BigQuery write dispositions — https://cloud.google.com/bigquery/docs/reference/rest/v2/tables#BigQueryDisposition
- Google Cloud BigQuery loading data with a schema — https://cloud.google.com/bigquery/docs/loading-data-cloud-storage-csv
- Python `csv` module documentation — https://docs.python.org/3/library/csv.html
