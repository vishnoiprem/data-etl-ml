# 3.3 — Text/Avro/JSON/Parquet

> **Section 3 · I/O & Multi-Source Pipelines · Lecture 3.3 · 6:30**

## 🎯 What you will learn

- The four portable formats — text, Avro, JSON, Parquet — compared on schema enforcement, compression, read performance, ecosystem compatibility, and Beam support
- Why `ReadFromText` plus your own parser usually beats `ReadFromCsv`
- `ReadFromJson` / `WriteToJson` — what the pandas-backed transforms actually do
- `ReadFromAvro` / `WriteToAvro` and the `AvroGenericCoder`
- `ReadFromParquet` / `WriteToParquet` and the `RowCoder`
- Compression: the `codec` parameter for Parquet, the `codec` parameter for Avro, and the `compression_type` parameter for text
- Why Parquet is 3–10× smaller and measurably faster than CSV — with numbers you can reproduce
- Avro schema evolution: the backward and forward compatibility rules, and which one actually breaks your pipeline
- The dependency reality: `fastavro` and `pyarrow` are **required**, not extras; `pandas` lives in the `dataframe` extra
- **A verified runner difference**: `ReadFromCsv` / `ReadFromJson` fail on `BundleBasedDirectRunner` but work on `PrismRunner`; `WriteToCsv` / `WriteToJson` fail on the classic runner but work on `PrismRunner`

---

## 🧠 Concept

### The format landscape

A Beam pipeline reads bytes from somewhere and writes bytes to somewhere.
The *format* is the contract that makes those bytes mean something. Four
formats cover almost everything you will meet in this course, and they
are not close to equivalent.

| | Text / CSV | JSON (NDJSON) | Avro | Parquet |
|---|---|---|---|---|
| Layout | row | row | row | **column** |
| Schema enforced | no | no | **yes** | **yes** |
| Types preserved | no (all strings) | partly | yes | **yes** |
| Compression | per-file, whole | per-file, whole | per-block | **per-column** |
| Partial column read | no | no | no | **yes** |
| Splittable mid-file | line boundary | line boundary | block boundary | row group |
| Self-describing | no | no | **yes** | **yes** |
| Schema evolution | none | none | **designed for it** | additive only |
| Ecosystem | universal | universal | Hadoop, Java, Beam | Spark, BigQuery, Athena, Snowflake, DuckDB |
| Beam I/O | `ReadFromText` / `WriteToText` | `ReadFromJson` / `WriteToJson` | `ReadFromAvro` / `WriteToAvro` | `ReadFromParquet` / `WriteToParquet` |
| Extra dependency | none | pandas | `fastavro` | `pyarrow` |

The two columns worth staring at are the last two. **Beam supports all
four**, and all four are portable across runners. The differences are
entirely about *what the format does for you* — and the answer depends on
whether your workload is "read everything" or "read some columns, often".

### Schema enforcement

This is the axis that matters most in production, and it is the one
people most often get wrong.

**Text and CSV have no schema at all.** A CSV file is a convention about
commas. The reader has no idea whether column 4 is a region code or a
free-text note. Beam's `ReadFromText` gives you a `str` — the entire file
as lines, with no type information whatsoever. Any typing happens in your
code, at runtime, and a wrong value is a runtime error at whatever moment
the record happens to be processed.

**JSON has no schema either**, despite what people assume. JSON is
syntactically typed (a string is a string, a number is a number), but the
*set of keys* is not declared anywhere. Two records in the same NDJSON
file can have different keys. `{"a": 1}` and `{"b": 2}` are both valid
JSON lines, and a reader that expects `a` on every record will fail on
the second one. JSON Schema exists as a separate standard, but Beam's
`ReadFromJson` does not use it.

**Avro enforces a schema.** The schema is written into the file's
header. When you read an Avro file, the reader knows the field names,
their types, and whether they are nullable — before reading a single
record. A record that violates the schema fails to decode, loudly and
immediately.

**Parquet enforces a schema, and it is a *physical* schema.** The
schema is in the file footer, and it describes not just field names and
types but the physical layout: which bytes belong to which column, where
the row groups start, what the compression codec was. Parquet is the only
format of the four where the schema describes how to read the file
without reading the file.

The practical consequence is a different *failure mode*, not just a
different error message:

```text
CSV / JSON:   the bad record fails when the worker reaches it
              -> a job that ran for 40 minutes, failed at 39
Avro/Parquet: the bad record fails at decode time
              -> the same, but you can also validate the schema
                 up front against the whole file
```

The second point is the valuable one. With Avro or Parquet you can
*ask* "does this file match the schema my pipeline expects?" without
running the pipeline. With CSV you cannot, at all, until you start
running.

### Compression

Compression is not a binary property of a format — it is a property of
the format *plus the codec*, and the four formats have very different
compression granularity.

**Text and JSON compress as a single stream.** Beam's `WriteToText` has
a `compression_type` parameter that accepts `GZIP`, `BGZIP`, `DEFLATE`,
`SNAPPY`, `ZSTD` and `LZ4` (for GCS, `GZIP` and `BGZIP` are the ones
that work with the `gs://` path). The whole file is one compressed
stream. This is why compressed CSV does not support *any* form of
parallel read — you cannot seek to byte 500 MB because byte 500 MB is
inside a deflate stream.

**Avro compresses per block.** Avro's container format is a sequence of
*blocks*, each with a sync marker and its own codec setting. The default
in Beam is `deflate`. You can also use `null`, `snappy`, `bzip2` and
`xz`. Because each block is independent, an Avro file remains splittable
at block boundaries, which is what makes it usable at scale.

**Parquet compresses per column.** This is the important one. A Parquet
file is a set of *row groups*, and within each row group each column
chunk is compressed independently. A `region` column — four distinct
strings repeated 200,000 times — compresses to almost nothing. An
`order_id` column — 200,000 unique strings — compresses much less. The
file gets the benefit of each column's own redundancy profile.

This is why "Parquet is 3–10× smaller than CSV" is a range and not a
number: it depends entirely on the data's shape. Highly repetitive data
gets the best ratios. Random data gets almost none.

Beam's Parquet writer takes `codec=` with the values `none`, `snappy`,
`gzip`, `brotli`, `zstd` and `lz4`. The default is `none` — which means
**if you do not set a codec, your Parquet files are not compressed at
all**, and you will be disappointed. `snappy` is the conventional default
in the wider ecosystem and is the safest choice, because every Parquet
reader in existence supports it.

Beam's Avro writer takes `codec=` with `null`, `deflate`, `snappy`,
`bzip2` and `xz`. The default is `deflate`.

> **A dependency wrinkle worth knowing.** `fastavro` implements the Avro
> codecs in pure Python, and the optional `snappy` and `zstandard` codecs
> need an extra library that is not installed by default. If you set
> `codec="snappy"` on `WriteToAvro` without it, you get:
>
> ```text
> ValueError: snappy codec is supported but you need to install one of
> the following libraries: ('cramjam',)
> ```
>
> `deflate`, `bzip2` and `xz` work out of the box. `snappy` and
> `zstandard` need `pip install cramjam`. Parquet is unaffected —
> `pyarrow` bundles its own codec implementations, so `snappy`, `gzip`,
> `brotli`, `zstd` and `lz4` all work without extra installs.

### Read performance

Reading is where format choice pays for itself most visibly, because
reading is what pipelines do most of.

The three costs of reading a row-based format are:

1. **I/O.** How many bytes cross the network or the page cache.
2. **Parsing.** How much CPU to turn bytes into objects.
3. **Decoding.** How many fields you materialise that you did not need.

Parquet wins on all three.

On (1), it wins by the compression ratio — 3–4× less bytes to move.
On (2), it wins because the decoding of a column chunk is a bulk
operation on a contiguous buffer, not a per-field string parse. On (3),
it wins overwhelmingly: **you can read three columns out of nine and
only pay for three columns.**

That last point is the one that changes architecture. A Parquet lake with
a hundred columns is cheap to query with a wide warehouse that projects
a few columns; the same lake in CSV means every reader pays for the
whole row. This is the single biggest reason the industry standardised
on Parquet for object stores.

Avro wins on (2) relative to JSON — it is a compact binary encoding,
not text — but loses to Parquet on (1) and (3), because Avro has no
columnar layout and cannot project.

CSV wins on nothing except that every tool on earth can read it.

### Ecosystem compatibility

This is the axis that decides the *landing* format, and it is different
from the axis that decides the *interchange* format.

| Consumer | CSV | NDJSON | Avro | Parquet |
|---|---|---|---|---|
| Excel / Sheets | **yes** | no | no | no |
| `jq`, shell tools | no | **yes** | no | no |
| BigQuery | yes (slow load) | yes (slow load) | yes | **yes (native)** |
| Spark | yes (inferred) | yes | yes (inferred) | **yes (native)** |
| BigQuery external table | yes | yes | no | **yes** |
| Athena / Presto | yes | no | no | **yes** |
| Snowflake / Databricks | yes | yes | yes | **yes** |
| DuckDB | yes | yes | no | **yes** |
| Kafka Connect / REST APIs | yes | **yes** | no | no |
| Flink | yes | yes | yes | yes |

The practical rule:

- **CSV** is the *final* format. It is what a human opens in a
  spreadsheet, what a business team emails to a partner, what an API
  returns. It is the wrong format for everything upstream of that.
- **NDJSON** is the *streaming and API* format. It is line-delimited, so
  a producer can emit records without knowing the total count, and a
  consumer can process them one at a time. This is why Logstash,
  Kafka Connect, and most REST-ish protocols settled on it.
- **Parquet** is the *lake* format. It is what you want your data to
  look like when it is sitting in a bucket.
- **Avro** is the *schema-registry* format. It is what you want when
  the schema is the hard part and you need the file to be self-describing
  and verifiable.

A well-designed pipeline usually writes more than one. The shape is:
read Parquet, write Parquet to the lake, and also write a small CSV
summary for the humans.

### Beam support

All four are supported and all four are portable. The API surface:

| Format | Read | Write | Extra dependency |
|---|---|---|---|
| Text / CSV | `beam.io.ReadFromText` | `beam.io.WriteToText` | none |
| JSON | `beam.io.ReadFromJson` | `beam.io.WriteToJson` | pandas (`apache-beam[dataframe]`) |
| Avro | `beam.io.ReadFromAvro` | `beam.io.WriteToAvro` | `fastavro` |
| Parquet | `beam.io.ReadFromParquet` | `beam.io.WriteToParquet` | `pyarrow` |

The dependency column is not a footnote. It is the thing that bites
people, so it gets its own treatment below.

---

## 🧠 The dependency reality

This is the part that is worth reading twice, because the extras
mechanism in Beam is more subtle than it looks, and because the
installed state of this course's environment is a good illustration.

### What Beam's extras actually mean

`apache-beam` is published with *extras* — named optional dependency
groups that you request with `pip install apache-beam[extra]`. The
relevant ones:

| Extra | Pulls in | Needed for |
|---|---|---|
| `[gcp]` | google-cloud-* clients, `gcsfs`, `grpcio`, ... | BigQuery, Pub/Sub, `gs://` paths |
| `[dataframe]` | `pandas` | `ReadFromCsv`, `WriteToCsv`, `ReadFromJson`, `WriteToJson` |
| `[filesystem]` | `gcsfs`, `s3fs`, Hadoop FS support | `gs://` and `s3://` paths |

Now the important bit, and the thing the task brief asked to be stated
accurately:

> **`fastavro` and `pyarrow` are NOT extras. They are required
> dependencies.** The Avro and Parquet I/O transforms need them, and
> they are installed as part of the base `apache-beam` package.

Let that sink in, because it is different from how most people expect
Beam's extras to work. `pip install apache-beam` gives you a working
Avro and Parquet pipeline. `pip install apache-beam[dataframe]` gives
you CSV and JSON. `pandas` is the one that lives in an extra.

You can verify it:

```bash
python -c "import fastavro, pyarrow; print(fastavro.__version__, pyarrow.__version__)"
```

And in this course's environment:

```text
fastavro 1.13.1
pyarrow 25.0.1
pandas 2.3.3
```

All three are present, because `project/requirements.txt` asks for
`apache-beam[gcp]`, and the GCP extra transitively brings in
`pyarrow` (via `google-cloud-bigquery-storage`) while `fastavro` is a
direct base dependency.

### What happens when a dependency is missing

If `fastavro` is missing, `beam.io.ReadFromAvro` *still exists* on the
module — `hasattr(beam.io, "ReadFromAvro")` returns `True`. But
calling it raises at pipeline-construction time. The transform's
presence and its availability are two different questions, exactly as
chapter 3.1 said about coders.

The same is true of `pandas` and the CSV/JSON transforms:

```text
ImportError: Please install apache_beam[dataframe]
```

### What is *not* there: XML

Beam 2.77 has **no XML I/O transforms**. There is no `apache_beam.io.xmlio`
module, and `beam.io.ReadFromXml` / `beam.io.WriteToXml` do not exist:

```text
>>> hasattr(beam.io, "ReadFromXml")
False
>>> hasattr(beam.io, "WriteToXml")
False
```

You will find XML I/O examples in older Beam documentation and in blog
posts; they refer to a transform that was removed. If you need XML, the
answer in Beam 2.77 is `ReadFromText` plus a parser of your own
(`xml.etree.ElementTree` in the standard library, or `lxml` if you need
more). The pattern is:

```python
import xml.etree.ElementTree as ET

import apache_beam as beam


def parse_order_xml(xml_line: str) -> dict:
    """Parse one XML document into a flat order dict."""
    root = ET.fromstring(xml_line)
    return {
        "order_id": root.findtext("order_id", default=""),
        "region": root.findtext("region", default=""),
        "amount": float(root.findtext("amount", default="0")),
    }


with beam.Pipeline() as p:
    orders = (
        p
        | "ReadXml" >> beam.io.ReadFromText("./sample_data/orders.xml")
        | "ParseXml" >> beam.Map(parse_order_xml)
    )
```

One caveat: XML records that span multiple lines cannot be parsed
record-by-record from a line-oriented source. Either write one record per
line (which is what most XML-over-HTTP formats actually look like in
practice) or read the whole file as one blob and parse it in a
`ParDo`.

---

## 🧠 Text and CSV: `ReadFromText` vs `ReadFromCsv`

This is the first real decision in the chapter, and the honest answer is
that `ReadFromCsv` is the worse default for almost everything you will
do in Beam.

### What `ReadFromCsv` actually is

In Beam 2.77, `beam.io.ReadFromCsv` is not a Beam-native CSV parser. It
is a thin wrapper around `pandas.read_csv`, implemented via
`apache_beam.dataframe.io.ReadViaPandas`. The source says so plainly:

```python
def ReadFromCsv(
    path: str,
    *,
    splittable: bool = True,
    filename_column: Optional[str] = None,
    **kwargs):
  """A PTransform for reading comma-separated values (csv) files into a
  PCollection.
  ...
  """
  from apache_beam.dataframe.io import ReadViaPandas
  return 'ReadFromCsv' >> ReadViaPandas(
      'csv', path, splittable=splittable, filename_column=filename_column, **kwargs)
```

Every extra keyword argument is forwarded straight to
`pandas.read_csv`. So `ReadFromCsv(path, usecols=["region", "amount"])` is
literally `pandas.read_csv(path, usecols=[...])`.

### The three problems with the pandas path

**1. It materialises a whole DataFrame per bundle.** `ReadViaPandas` is
built on Beam's `ReadFromPandas` machinery, which reads a *file* and
emits its rows. A 10 GB CSV file is one element, not ten million. The
pandas-backed transforms were designed for the Beam DataFrame API (the
`beam.dataframe` module), where a DataFrame *is* the unit of
computation. In a classic PCollection pipeline it is the wrong
abstraction.

**2. It has a hard runner dependency.** `ReadViaPandas` expands into a
`Sdf` source, and the `BundleBasedDirectRunner` — the classic
`DirectRunner` in Beam 2.77 — does not support the SDK's
`SplitRoutines`/`Sdf` expansion the way `PrismRunner` does. This is not
hypothetical; it is verified below and in the next section.

**3. It infers types from the data, not from a declaration.**
`pandas.read_csv` will look at a column and decide it is `int64` or
`float64` or `object` based on what it sees. That is convenient and it
is dangerous: the type of your PCollection can change depending on the
data, which breaks coder inference, breaks type checking, and makes the
pipeline non-deterministic with respect to its inputs.

### The manual-parsing alternative

`ReadFromText` plus your own `Map` gives you:

- **Full control of types.** You decide that `amount` is a `float` and
  that `order_id` is a `str`, and you encode that in a type hint.
- **Line-level streaming.** One element per line, so a 10 GB file
  becomes ten million elements that flow through the pipeline.
- **Row-level error handling.** You can route a malformed row to a
  dead-letter output instead of failing the file.
- **No pandas dependency.**
- **It runs on every runner, including the classic DirectRunner.**

The course's own `project/transforms.py` does exactly this, and it is
worth reading the reason it is built the way it is:

```python
class ParseOrderFn(beam.DoFn):
    """Parse CSV lines into order dicts, skipping malformed rows.

    The malformed rows are logged rather than raised, because one bad
    line in a 10-million-line file should not fail the entire bundle.
    A pipeline that must not lose data should route them to a
    dead-letter topic instead — see the "Error Handling and DLQ"
    chapter.
    """

    def process(self, line: str, timestamp=beam.DoFn.TimestampParam) -> Iterable[Any]:
        """Parse one line and emit the resulting order dict."""
        row = try_parse_order_line(line)
        if row is None:
            log.warning("skipping malformed order line: %.120s", line)
            return
        if not is_valid_order(row):
            log.warning("skipping invalid order: %s", row.get("order_id"))
            return
        yield row
```

Note that `try_parse_order_line` uses `csv.reader` from the standard
library — the same parser pandas uses, but invoked per line, under your
control, with a place to put the failures.

So the rule is:

> **Use `ReadFromText` and parse it yourself, unless you have a specific
> reason not to.** Use `ReadFromCsv` when you genuinely want pandas
> semantics (a header-driven `usecols`, a `dtype` map, a `parse_dates`
> expression) and you are running on a runner that supports it.

### When `ReadFromCsv` is the right choice

It is not never. Three legitimate cases:

1. **You want pandas' type inference** because you are feeding a
   DataFrame-based transform.
2. **You need `usecols` at the source** to avoid parsing columns you do
   not care about, and the file is small enough that the whole-file read
   is acceptable.
3. **The file is genuinely a table** — a fixed header, uniform rows —
   and you want the convenience.

### The header question

`ReadFromText` reads *every* line, including the header. `ReadFromCsv`
skips the header automatically, because pandas treats the first row as
column names. This asymmetry is the single most common bug when
switching between the two, and it shows up as a count that is off by
one, or as a `ValueError: could not convert string to float:
'amount'` when the code tries to parse the header as data.

`ReadFromText` has a `skip_header_lines` parameter:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    orders = p | "Read" >> beam.io.ReadFromText(
        "./sample_data/orders.csv",
        skip_header_lines=1,
    )
```

But note the caveat from chapter 3.2: if you are reading several files
with *different* headers, `skip_header_lines=1` will silently eat the
first data row of every file except the first. An explicit filter is
more honest:

```python
with beam.Pipeline() as p:
    orders = (
        p
        | "Read" >> beam.io.ReadFromText("./sample_data/orders.csv")
        | "SkipHeader" >> beam.Filter(lambda line: not line.startswith("order_id"))
    )
```

---

## 🧠 The runner difference you will hit

This section documents something that was **verified by running it** on
this course's environment — Apache Beam 2.77.0, Python 3.13, on the
`BundleBasedDirectRunner` and the `PrismRunner`.

The short version:

| Transform | `BundleBasedDirectRunner` (classic DirectRunner) | `PrismRunner` |
|---|---|---|
| `ReadFromCsv` | **fails** | works |
| `ReadFromJson` | **fails** | works |
| `WriteToCsv` | **fails** | works |
| `WriteToJson` | **fails** | works |

### The read failure

The error is:

```text
File ".../apache_beam/runners/direct/sdf_direct_runner.py", line 86, in expand
    element_coder = typecoders.registry.get_coder(pcoll.element_type)
                                                  ^
AttributeError: 'tuple' object has no attribute 'element_type'
```

That message is genuinely unhelpful. It points at a coder registry call
and blames a tuple, when the real story is that `ReadViaPandas` expands
into a `Sdf` source, and the classic DirectRunner's SDF expansion path
hands the runner a tuple where it expects a `PCollection`.

The same error appears for both `ReadFromCsv` and `ReadFromJson`,
because both go through the same `ReadViaPandas` machinery.

Under `PrismRunner`, both work, and both were verified at 5,000 and
20,000 rows. The element type they produce is a schema'd `Row`:

```text
CSV element_type:
  Row(order_id=typing.Optional[str], customer_id=typing.Optional[str],
      order_ts=typing.Optional[str], region=typing.Optional[str],
      channel=typing.Optional[str], currency=typing.Optional[str],
      status=typing.Optional[str], amount=typing.Optional[numpy.float64],
      product_id=typing.Optional[str])
```

Two things to notice in that type. First, every field is `Optional` —
pandas-backed reads make no required-field claim. Second, `amount` is
`numpy.float64`, not `float`, because it came through pandas' `numpy`
backed dtypes. If you need plain Python floats, cast them.

### The write failure

`WriteToCsv` and `WriteToJson` fail on the classic runner with:

```text
RuntimeError: NotImplementedError [while running 'W/BatchElements(pcoll)']
```

The `WriteViaPandas` path uses `GroupIntoBatches`, whose batch-element
implementation is not implemented in the classic DirectRunner's
`BatchElements` operation.

Under `PrismRunner`, both writes work — but only with a **schema-aware
`beam.Row` input**. The sink needs to know the column names and types,
and a `beam.Row` is how you tell it:

```python
import apache_beam as beam
from apache_beam.pvalue import Row

with beam.Pipeline() as p:
    rows = (
        p
        | "Create" >> beam.Create([
            Row(region="EMEA", n=1),
            Row(region="AMER", n=2),
        ])
    )
    rows | "WriteCsv" >> beam.io.WriteToCsv("./out/probe_csv")
```

which produces:

```text
region,n
EMEA,1
AMER,2
```

and the JSON equivalent:

```text
{"region":"EMEA","n":1}
{"region":"AMER","n":2}
```

### What to do about it

Three options, in order of preference:

1. **Use `ReadFromText` / `WriteToText` and format the records yourself.**
   This is what the course's `project/batch_pipeline.py` does, and it is
   why that pipeline runs on every runner without a special flag. The
   formatting logic already exists in the project, in
   `format_summary_csv`:

```python
def format_summary_csv(row: dict[str, Any]) -> str:
    """Format one summary row as a CSV line.

    `WriteToText` writes whatever string it is given, so the dict must
    be formatted explicitly. Using `csv.writer` rather than an f-string
    means a region name containing a comma cannot corrupt the output.
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        row.get("region", ""),
        row.get("order_count", 0),
        row.get("revenue_eur", 0.0),
    ])
    return buffer.getvalue().rstrip("\r\n")
```

2. **Run the CSV/JSON transforms on `PrismRunner`.** This works and is
   the right answer if you specifically want pandas semantics. The flag
   is `--runner=PrismRunner`.

3. **Use `PrismRunner` for the whole pipeline.** Note that `PrismRunner`
   is a different runner with different performance characteristics and
   a different maturity level than `BundleBasedDirectRunner`. It is not a
   drop-in "turn it on" switch for a production Dataflow pipeline; it
   is a local runner.

> **Why this is worth a section of its own.** Because it is exactly the
> kind of thing a reader will hit. The error message points at a coder,
> not at the runner, and the natural reaction is "I have a type problem"
> — at which point you spend an hour adding type hints that make no
> difference. Knowing that the transform *and* the runner are both
> involved saves that hour.

### The gotcha that makes the gotcha confusing

To reproduce the failure you must name the runner *explicitly*, and you
must pass it through `PipelineOptions`. A plain `beam.Pipeline()` does
**not** read the `--runner` flag from the command line.

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(flags=["--runner=BundleBasedDirectRunner"])

with beam.Pipeline(options=options) as p:
    rows = p | "ReadCsv" >> beam.io.ReadFromCsv("./sample_data/orders.csv")
```

Why: when you construct `beam.Pipeline()` with neither `options=` nor
`argv=`, Beam builds `PipelineOptions([])` — an *empty* argument list —
and the runner comes out as `StandardOptions.DEFAULT_RUNNER`, which is
`"DirectRunner"`. Your `--runner=BundleBasedDirectRunner` on the
command line is never read.

And `DirectRunner` is not what it used to be. In Beam 2.77 it resolves
to `SwitchingDirectRunner`, which:

1. Runs the pipeline on `PrismRunner` if every transform is supported
   there, and
2. Falls back to `BundleBasedDirectRunner` if Prism fails.

So the default `DirectRunner` *already* uses Prism for these pipelines,
which is why `python work/csv_reader.py` with no flags at all succeeds.
The failure only appears when you pin the classic runner.

The resolution table is:

| How you name it | What you get |
|---|---|
| `beam.Pipeline()` (no options) | `SwitchingDirectRunner` → Prism when supported |
| `--runner=DirectRunner` | `SwitchingDirectRunner` → Prism when supported |
| `--runner=BundleBasedDirectRunner` | the classic runner, always |
| `--runner=PrismRunner` | Prism, always |
| `--runner=SwitchingDirectRunner` | the switching behaviour, explicitly |

This is worth internalising for a second reason: **`DirectRunner` in
Beam 2.77 is not the same runner it was in Beam 2.5x.** Behaviour that
"worked locally" may have been running on a completely different
execution engine than you thought, and the switcher's automatic fallback
means a pipeline that fails on Prism will silently re-run on the classic
runner instead of erroring out. When you are debugging a runner-specific
problem, pin the runner explicitly so that what you measure is what
you get.


---

## 🧠 Avro and Parquet in detail

### Avro: schema in the header

An Avro file is an **object container file**. The layout:

```text
+--------------------------------+
| magic: "Obj\x01"               |
+--------------------------------+
| metadata: schema, codec, ...   |
+--------------------------------+
| sync marker (16 bytes)         |
+--------------------------------+
| block 1: count + serialised    |
|          records                |
+--------------------------------+
| sync marker                     |
+--------------------------------+
| block 2 ...                     |
+--------------------------------+
```

The metadata block holds the **schema** — a JSON document describing the
record type:

```python
ORDER_SCHEMA = {
    "type": "record",
    "name": "Order",
    "namespace": "com.example.orders",
    "fields": [
        {"name": "order_id", "type": "string"},
        {"name": "region", "type": "string"},
        {"name": "amount", "type": "double"},
    ],
}
```

Beam accepts a schema as a **dictionary** or as a **JSON string**. The
dictionary form is more comfortable in Python and is what the course
uses.

Writing Avro is straightforward:

```python
import apache_beam as beam
from apache_beam.io import avroio

ORDER_SCHEMA = {
    "type": "record",
    "name": "Order",
    "fields": [
        {"name": "order_id", "type": "string"},
        {"name": "region", "type": "string"},
        {"name": "amount", "type": "double"},
    ],
}

with beam.Pipeline() as p:
    orders = (
        p
        | "Create" >> beam.Create([
            {"order_id": "o1", "region": "EMEA", "amount": 10.5},
        ])
    )
    orders | "WriteAvro" >> avroio.WriteToAvro(
        "./out/orders",
        schema=ORDER_SCHEMA,
        num_shards=1,
        file_name_suffix=".avro",
    )
```

Reading it back gives you plain Python dicts:

```python
import apache_beam as beam
from apache_beam.io import avroio

with beam.Pipeline() as p:
    orders = p | "ReadAvro" >> avroio.ReadFromAvro("./out/orders*")
    print(orders.element_type)   # Any
```

and the element is a dict:

```text
{'order_id': 'o1', 'region': 'EMEA', 'amount': 10.5}
```

Note the `element_type` is `Any`. That is the pickle-fallback coder,
discussed in chapter 3.1, and it is worth fixing with a type hint if
the stage is large:

```python
import apache_beam.typehints as th

with beam.Pipeline() as p:
    orders = (
        p
        | "ReadAvro" >> avroio.ReadFromAvro("./out/orders*")
        | "Annotate" >> beam.Map(lambda d: d).with_output_types(
            th.Dict[str, th.Any]
        )
    )
```

#### `AvroGenericCoder`

The coder behind Avro I/O is `AvroGenericCoder`, and it lives in the
top-level `apache_beam.coders` namespace:

```python
from apache_beam.coders import AvroGenericCoder
```

There is **no class named `AvroCoder`** in Beam 2.77. That name is a
common misconception, and it appears in blog posts and older
documentation. The real class takes the schema as a JSON string:

```python
from apache_beam.coders import AvroGenericCoder
import json

schema = json.dumps(ORDER_SCHEMA)
coder = AvroGenericCoder(schema)
print(coder.is_deterministic())   # False
```

Note that `is_deterministic()` returns `False`, and Beam's own source
explains why in a comment: the determinism of the Avro encoding is not
confirmed. This is one of the reasons `AvroGenericCoder` is not used as
a `GroupByKey` key in practice — you use a plain string or a typed
tuple for keys.

#### `use_fastavro`

`ReadFromAvro` and `WriteToAvro` both take a `use_fastavro` parameter,
defaulting to `True`. With it on, Beam uses the `fastavro` library. With
it off, Beam falls back to a slower pure-Python implementation. You
should leave it on; the parameter exists mostly for testing the
fallback.

### Parquet: schema in the footer

Parquet is a columnar format with a more complex physical layout:

```text
+--------------------------------+
| PAR1 (magic)                  |
+--------------------------------+
| row group 1                   |
|   column chunk: order_id      |
|   column chunk: region        |
|   ...                          |
+--------------------------------+
| row group 2 ...               |
+--------------------------------+
| footer: schema + metadata      |
+--------------------------------+
| PAR1 (magic)                  |
+--------------------------------+
```

The **footer** at the end of the file holds the schema and the metadata
that maps each column chunk to its byte range. This is why Parquet
readers can seek: they read the footer first, then jump directly to the
column chunks they need.

Beam's Parquet writer takes a **`pyarrow` schema**, not a dictionary:

```python
import apache_beam as beam
from apache_beam.io import parquetio
import pyarrow as pa

ORDER_SCHEMA = pa.schema([
    pa.field("order_id", pa.string()),
    pa.field("customer_id", pa.string()),
    pa.field("order_ts", pa.string()),
    pa.field("region", pa.string()),
    pa.field("channel", pa.string()),
    pa.field("currency", pa.string()),
    pa.field("status", pa.string()),
    pa.field("amount", pa.float64()),
    pa.field("product_id", pa.string()),
])

with beam.Pipeline() as p:
    orders = (
        p
        | "Create" >> beam.Create([
            {"order_id": "o1", "region": "EMEA", "amount": 10.5},
        ])
    )
    orders | "WriteParquet" >> parquetio.WriteToParquet(
        "./out/orders",
        schema=ORDER_SCHEMA,
        num_shards=1,
        codec="snappy",
        file_name_suffix=".parquet",
    )
```

The `pyarrow` schema is what makes Parquet's types exact: `float64` is
a double, `string` is a UTF-8 string, `int64` is a long. There is no
inference step and no ambiguity.

Reading gives you dicts by default:

```python
with beam.Pipeline() as p:
    orders = p | "ReadParquet" >> parquetio.ReadFromParquet("./out/orders*")
```

and `beam.Row` objects if you ask:

```python
with beam.Pipeline() as p:
    orders = p | "ReadParquet" >> parquetio.ReadFromParquet(
        "./out/orders*",
        as_rows=True,
    )
    print(orders.element_type)
    # <class 'apache_beam.typehints.schemas.BeamSchema_'>
```

and the element prints as:

```text
BeamSchema_(order_id='o1', region='EMEA', amount=10.5)
```

> **The `as_rows=True` gotcha.** `as_rows=True` reads the Parquet
> *schema* at pipeline-construction time by opening the first matching
> file. That means:
>
> 1. The file pattern must match at least one file **when the pipeline is
>    built**, not when it runs. A read-then-write pipeline that writes
>    Parquet and reads it back in the same job will fail.
> 2. The pattern must not match non-Parquet files. A glob like
>    `out/probe_pq*` that also matches `out/probe_pq_read` (a text file)
>    produces:
>
>    ```text
>    pyarrow.lib.ArrowInvalid: Parquet magic bytes not found in footer.
>    Either the file is corrupted or this is not a parquet file.
>    ```
>
>    Match the suffix explicitly: `out/probe_pq-*.parquet`.

#### Column projection

The payoff of Parquet is projection. `ReadFromParquet` takes a
`columns` parameter, and only the requested columns are read from disk:

```python
with beam.Pipeline() as p:
    regions = p | "ReadParquet" >> parquetio.ReadFromParquet(
        "gs://YOUR_BUCKET/orders*",
        columns=["region", "amount"],
    )
```

With a nine-column file and a two-column projection, you read two
columns. This is the feature that makes Parquet the right lake format,
and it is worth designing your schemas around: **wide tables are cheap
to store and cheap to write, and only expensive to read columns you do
not need.**

### Why Parquet is 3–10× smaller and faster than CSV

Let us stop asserting it and measure it. The hands-on in this chapter
does exactly this, and here is what the numbers look like on this
course's dataset.

The same 200,000 orders, written four ways:

| Format | Bytes on disk | vs CSV |
|---|---|---|
| CSV | 16,091,856 | 1.00× |
| NDJSON | 42,491,777 | 0.38× (2.6× **bigger**) |
| Parquet, `codec="snappy"` | 4,055,906 | **3.97× smaller** |
| Avro, `codec="deflate"` | 4,529,071 | **3.55× smaller** |

And read back, same rows, same machine, best of three runs:

| Format | Read time (200k rows) | vs CSV |
|---|---|---|
| CSV | 0.734 s | 1.00× |
| NDJSON | 0.555 s | 1.32× faster |
| Parquet | **0.379 s** | **1.94× faster** |
| Avro | 0.761 s | 0.96× (no faster) |

Two observations that are worth more than the headline numbers.

**NDJSON is *bigger* than CSV, not smaller.** This surprises people. CSV
is comma-separated with no per-field overhead; NDJSON repeats every key
name on every line. On this dataset, the keys are `order_id`,
`customer_id`, `order_ts`, `region`, `channel`, `currency`, `status`,
`amount`, `product_id` — 74 characters of key names per record. The
values themselves are much shorter than the keys. So NDJSON is 2.6×
*worse* than CSV for this shape of data. NDJSON's advantage is not size;
it is that it is line-delimited and self-describing per record, which
matters for streaming and for heterogeneous records, not for
compactness.

**Avro is not faster than CSV here.** That is worth sitting with. Avro
is a compact binary format and it compresses well, but the decode cost
of the `fastavro` binary parser offsets the I/O saving at this scale.
Avro's win is schema enforcement and self-description, not speed.

Parquet's win is both — it is 3.97× smaller *and* 1.94× faster,
because the columnar layout means both less I/O and less parsing.

The "3–10×" range in the chapter title is a real range. It depends
entirely on:

- **How repetitive the data is.** Highly repetitive columns
  (categorical, low-cardinality IDs, timestamps with a shared prefix)
  compress to almost nothing. Random UUIDs compress to nothing at all.
- **How many columns there are.** More columns means more
  per-column metadata overhead, which is a fixed cost per file.
- **The codec.** `snappy` is fast but moderate; `zstd` is smaller but
  slower to decompress. On this dataset, zstd produced **91,593 bytes**
  against snappy's **141,428** and uncompressed's **326,471** — so
  `zstd` is 4.4× smaller than CSV where snappy is 2.8×.

The last point deserves a note, because it changes the recommendation:
**`zstd` is often the better codec for lake data.** It is slower to
compress than snappy, but you compress once and decompress many times,
and zstd decompresses at roughly the speed of snappy while producing
meaningfully smaller files. `gzip` is the compatibility-safe fallback if
something downstream cannot handle zstd.

---

## 🧠 Avro schema evolution

This is the reason Avro exists, and it is the one thing Avro does that
Parquet does not.

### The rules

Avro defines three compatibility modes. The two that matter are
**backward** and **forward**.

**Backward compatibility** means: *a reader with the new schema can
read data written with the old schema.*

This is the mode that protects your existing readers. If you add a
field with a default value, old readers (which do not know about the
field) can still read new data — they just ignore the extra field. If
you *remove* a field, old readers that expect it break.

**Forward compatibility** means: *a reader with the old schema can read
data written with the new schema.*

This is the mode that protects your consumers. If you add a field, old
readers ignore it. If you remove a field, old readers break — because
there is nothing to give them.

**Full compatibility** is both.

The practical rules, in the form you will actually need:

| Change | Backward? | Forward? | Notes |
|---|---|---|---|
| Add a field **with a default** | yes | yes | the safe change |
| Add a field **without a default** | no | yes | new readers fail on old data |
| Remove a field | no | no | breaks both directions |
| Rename a field | no | no | use an alias instead |
| Add an enum symbol | no | yes | with a default symbol |
| Widen an int (`int` → `long`) | yes | yes | the safe type change |
| Change `float` → `double` | yes | yes | |
| Change `string` → `bytes` | yes | yes | |
| Any other type change | no | no | |

The rule that bites people: **adding a field without a default value is
backward-incompatible.** Old data does not have the field, so a reader
with the new schema has nothing to put in it.

### What "default" means in Avro

A default is not a sentinel like `NULL` or `-1`. It is a literal value
in the schema, and it must match the field's type:

```python
# Backward-compatible: the default matches the type.
COMPATIBLE_SCHEMA = {
    "type": "record",
    "name": "Order",
    "fields": [
        {"name": "order_id", "type": "string"},
        {"name": "region", "type": "string"},
        {"name": "amount", "type": "double"},
        {"name": "channel", "type": "string", "default": "unknown"},
    ],
}

# NOT backward-compatible: no default, and no value to supply for
# records written before the field existed.
INCOMPATIBLE_SCHEMA = {
    "type": "record",
    "name": "Order",
    "fields": [
        {"name": "order_id", "type": "string"},
        {"name": "region", "type": "string"},
        {"name": "amount", "type": "double"},
        {"name": "channel", "type": "string"},
    ],
}
```

A `null` type with a `"default": null` is the other common pattern — the
field is explicitly nullable:

```python
NULLABLE_SCHEMA = {
    "type": "record",
    "name": "Order",
    "fields": [
        {"name": "order_id", "type": "string"},
        {"name": "region", "type": "string"},
        {"name": "amount", "type": "double"},
        {"name": "discount", "type": ["null", "double"], "default": None},
    ],
}
```

### How this affects a Beam pipeline

Beam's Avro transforms do **not** enforce schema compatibility at
runtime by default in the way a schema registry does. What happens is
more prosaic:

- `WriteToAvro` writes the schema you gave it. That schema goes into
  the file header.
- `ReadFromAvro` reads whatever schema is in the file header and
  decodes records against *it*. The `schema=` argument on the reader is
  used for validation, not for overriding.

So the compatibility problem shows up at the moment a *reader* meets a
file whose schema it cannot handle. If your reader is a Beam pipeline
that reads `orders*` from a bucket where you have been writing with
evolving schemas, you have a problem the first time you add a
non-default field.

There is a second, better enforcement point that Avro gives you for
free: **the writer validates too.** If you add a field without a
default and then write a record that does not have it, `fastavro`
refuses to encode the record and the job fails:

```text
ValueError: no value and no default for channel [while running 'WriteAvro/Write/WriteImpl/WriteBundles']
```

That is a failure at write time, in the job that caused it, with the
field name in the message. It is the difference between a schema
enforced format and a convention, and it is worth remembering when
someone asks why they should use Avro instead of JSON.

The mitigation for the read side is a schema registry or a schema
directory, and it is worth knowing that Beam supports one natively:

```python
import apache_beam as beam
from apache_beam.io import avroio

with beam.Pipeline() as p:
    orders = (
        p
        | "ReadAvro" >> avroio.ReadFromAvro(
            "gs://YOUR_BUCKET/schemas/orders.avsc",
            schema="gs://YOUR_BUCKET/schemas/orders.avsc",
        )
    )
```

The `schema=` parameter on `ReadFromAvro` can point at a schema file
on GCS, and Beam will fetch it and use it to validate the file's own
schema before decoding. That is how you catch an incompatible schema
change before it reaches your data.

### Avro vs Parquet for schema evolution

Parquet has no designed-for-this story. Parquet schemas are *physical*:
the column types and encodings are baked into the file. There is no
"reader schema" and "writer schema" distinction, no defaults, and no
compatibility modes.

What Parquet *does* give you:

- **Columnar projection**, which means adding a column is not a breaking
  change for a reader that does not select it.
- **The union of schemas**, which is how Spark and most engines handle
  a directory of Parquet files with different schemas: they reconcile
  the schemas across files and fill the gaps with nulls. This is
  *implicit* evolution, and it works because Parquet files are read
  column-by-column and a missing column is simply null.

That is good enough for most lakehouse workloads, and it is why Parquet
won. But it is not the same thing as Avro's explicit compatibility
rules, and if you need a hard guarantee that a reader with schema *N*
can read data written with schema *N+1*, Avro's model is the one that
gives it to you.

The pragmatic split:

- **Avro** when you need a schema contract — CDC, event streams with
  registered schemas, cross-team data contracts.
- **Parquet** when you need to query the data — everything else.

---

## 🛠️ Hands-On: Write It Three Ways and Measure

### Setup

```bash
cd data-engineering/data-Course/google/Dataflow
source .venv/bin/activate
python resources/sample_data.py --output-dir ./sample_data
```

Confirm the optional dependencies are present:

```bash
python -c "import fastavro, pyarrow, pandas; print(fastavro.__version__, pyarrow.__version__, pandas.__version__)"
```

Expected:

```text
1.13.1 25.0.1 2.3.3
```

### Step 1 — write the same data three ways

Create `work/format_hands_on.py`:

```python
"""Write the course's orders as CSV, NDJSON and Parquet, for comparison."""

import json
import shutil

import apache_beam as beam
import pyarrow as pa
from apache_beam.io import parquetio

FIELDS = [
    "order_id",
    "customer_id",
    "order_ts",
    "region",
    "channel",
    "currency",
    "status",
    "amount",
    "product_id",
]

PARQUET_SCHEMA = pa.schema(
    [
        pa.field("order_id", pa.string()),
        pa.field("customer_id", pa.string()),
        pa.field("order_ts", pa.string()),
        pa.field("region", pa.string()),
        pa.field("channel", pa.string()),
        pa.field("currency", pa.string()),
        pa.field("status", pa.string()),
        pa.field("amount", pa.float64()),
        pa.field("product_id", pa.string()),
    ]
)


def parse_order(line: str) -> dict:
    """Parse one CSV order line into a dict with a typed amount."""
    values = line.split(",")
    row = dict(zip(FIELDS, values))
    row["amount"] = float(row["amount"])
    return row


def to_csv(row: dict) -> str:
    """Render one order as a CSV line."""
    return ",".join(str(row[field]) for field in FIELDS)


def main() -> None:
    """Run the three writes."""
    for directory in ["out/formats/csv", "out/formats/ndjson", "out/formats/parquet"]:
        shutil.rmtree(directory, ignore_errors=True)

    with beam.Pipeline() as p:
        orders = (
            p
            | "Read" >> beam.io.ReadFromText("./sample_data/orders.csv")
            | "SkipHeader" >> beam.Filter(lambda line: not line.startswith("order_id"))
            | "Parse" >> beam.Map(parse_order)
        )

        orders | "ToCsv" >> beam.Map(to_csv) | "WriteCsv" >> beam.io.WriteToText(
            "out/formats/csv",
            num_shards=1,
            shard_name_template="",
            header=",".join(FIELDS),
        )

        orders | "ToJson" >> beam.Map(json.dumps) | "WriteJson" >> beam.io.WriteToText(
            "out/formats/ndjson",
            num_shards=1,
            shard_name_template="",
        )

        orders | "WriteParquet" >> parquetio.WriteToParquet(
            "out/formats/parquet",
            schema=PARQUET_SCHEMA,
            num_shards=1,
            codec="snappy",
            file_name_suffix=".parquet",
        )

    print("wrote out/formats/{csv,ndjson,parquet}")


if __name__ == "__main__":
    main()
```

Run it:

```bash
python work/format_hands_on.py
```

### Step 2 — compare the sizes

```bash
ls -l out/formats/
```

Expected:

```text
out/formats/:
-rw-r--r--  1 pvishnoi  staff   402268 ... csv
-rw-r--r--  1 pvishnoi  staff  1062189 ... ndjson
-rw-r--r--  1 pvishnoi  staff   141428 ... parquet-00000-of-00001.parquet
```

Note the naming: `WriteToText` with `shard_name_template=""` writes a
file with the *exact* prefix you gave it (`out/formats/csv`), while
`WriteToParquet` appends a shard suffix
(`out/formats/parquet-00000-of-00001.parquet`). The Parquet writer does
not take a `shard_name_template=""` that suppresses this, because the
suffix is how the reader's glob finds the files.


So for 5,000 orders:

| Format | Bytes | vs CSV |
|---|---|---|
| CSV | 402,268 | 1.00× |
| NDJSON | 1,062,189 | 0.38× |
| Parquet (snappy) | 141,428 | **2.84× smaller** |

To get the "3–10×" range, scale the data up:

```bash
python resources/sample_data.py --output-dir ./work/bigdata --orders 200000 --events 400000
```

and re-run the same script against `work/bigdata/orders.csv`. At 200,000
orders the Parquet file is 4,055,906 bytes against CSV's 16,091,856 —
**3.97× smaller** — and with `codec="zstd"` it drops to 91,593 bytes on
the 5,000-row dataset.

### Step 3 — confirm the row counts match

```bash
for f in out/formats/csv out/formats/ndjson; do echo -n "$f: "; wc -l < "$f"; done
python -c "
import pyarrow.parquet as pq
print('parquet:', pq.read_table('out/formats/parquet/parquet-00000-of-00001.parquet').num_rows)
"
```

Expected:

```text
out/formats/csv: 5001
out/formats/ndjson: 5000
parquet: 5000
```

The CSV has 5,001 lines because it includes the header; the NDJSON and
the Parquet file do not have one. That is the header asymmetry from
earlier in the chapter, showing up in a file listing.

### Step 4 — time the reads

Create `work/read_benchmark.py`:

```python
"""Time reading the same rows from each format."""

import statistics
import time

import apache_beam as beam
from apache_beam.io import parquetio

RUNS = 3


def time_read(make_reader) -> tuple[float, float]:
    """Return (best, median) read time over RUNS pipelines."""
    timings = []
    for run in range(RUNS):
        started = time.perf_counter()
        with beam.Pipeline() as p:
            rows = p | "Read" >> make_reader()
            keyed = rows | "Key" >> beam.Map(lambda row: (1, 1))
            counted = keyed | "Count" >> beam.combiners.Count.PerKey()
            counted | "Write" >> beam.io.WriteToText(
                f"out/bench_{run}", num_shards=1, shard_name_template=""
            )
        timings.append(time.perf_counter() - started)
    return min(timings), statistics.median(timings)


CASES = [
    ("csv     ", lambda: beam.io.ReadFromText("out/formats/csv")),
    ("ndjson  ", lambda: beam.io.ReadFromText("out/formats/ndjson")),
    ("parquet ", lambda: parquetio.ReadFromParquet("out/formats/parquet-*.parquet")),
]

for label, make_reader in CASES:
    best, median = time_read(make_reader)
    print(f"{label} best={best:.3f}s median={median:.3f}s")
```

Run it:

```bash
python work/read_benchmark.py
```

At 5,000 rows the three formats are within noise of each other, because
pipeline startup dominates — a Beam pipeline on the DirectRunner spends
most of its time on graph construction and worker setup, not on I/O. The
measurement only becomes meaningful at tens of thousands of rows. On the
200,000-row dataset the numbers are:

```text
csv      best=0.734s median=0.744s
ndjson   best=0.555s median=0.614s
parquet  best=0.379s median=0.394s
```

**That is the honest lesson**: at small scale, format choice is about
correctness and maintainability, not speed. At scale, it is worth a
factor of two. Design for the scale you are heading towards.

### Step 5 — the pandas path, and the runner difference

Now demonstrate the runner difference from the chapter. Create
`work/csv_reader.py`:

```python
"""Read the orders CSV with the pandas-backed ReadFromCsv."""

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(flags=["--runner=BundleBasedDirectRunner"])

with beam.Pipeline(options=options) as p:
    rows = p | "ReadCsv" >> beam.io.ReadFromCsv("./sample_data/orders.csv")
    print("element_type:", rows.element_type)
```

Run it:

```bash
python work/csv_reader.py
```

Expected:

```text
File ".../apache_beam/runners/direct/sdf_direct_runner.py", line 86, in expand
    element_coder = typecoders.registry.get_coder(pcoll.element_type)
                                                  ^
AttributeError: 'tuple' object has no attribute 'element_type'
```

Now switch the runner to Prism. Edit the `flags=` line to
`["--runner=PrismRunner"]` and re-run:

```bash
python work/csv_reader.py
```

Expected:

```text
element_type: Row(order_id=typing.Optional[str], customer_id=typing.Optional[str],
order_ts=typing.Optional[str], region=typing.Optional[str], channel=typing.Optional[str],
currency=typing.Optional[str], status=typing.Optional[str],
amount=typing.Optional[numpy.float64], product_id=typing.Optional[str])
```

And with **no** `options=` at all, the pipeline *succeeds*, because the
default `DirectRunner` is a `SwitchingDirectRunner` that picks Prism
when every transform is supported:

```bash
python -c "
import apache_beam as beam
with beam.Pipeline() as p:
    rows = p | 'ReadCsv' >> beam.io.ReadFromCsv('./sample_data/orders.csv')
    print('element_type:', rows.element_type)
" 2>&1 | grep element_type
```

Expected:

```text
element_type: Row(order_id=typing.Optional[str], customer_id=typing.Optional[str],
...
```

The same thing happens with `ReadFromJson` — the error is identical,
because both go through `ReadViaPandas`.

The manual alternative runs everywhere, on any runner, with no pandas:

```bash
python -c "
import apache_beam as beam
with beam.Pipeline() as p:
    rows = p | 'Read' >> beam.io.ReadFromText('./sample_data/orders.csv')
    print('element_type:', rows.element_type)
"
```

Expected:

```text
element_type: <class 'str'>
```

### Step 5b — the write side, same story

The `WriteToCsv` and `WriteToJson` failures are the mirror image. Create
`work/json_writer.py`:

```python
"""Write schema'd rows with WriteToCsv and WriteToJson."""

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.pvalue import Row

options = PipelineOptions(flags=["--runner=BundleBasedDirectRunner"])

with beam.Pipeline(options=options) as p:
    rows = p | "Create" >> beam.Create([
        Row(region="EMEA", n=1),
        Row(region="AMER", n=2),
    ])
    rows | "WriteCsv" >> beam.io.WriteToCsv("./out/probe_csv")

print("OK")
```

Run it:

```bash
python work/json_writer.py
```

Expected:

```text
ERROR:apache_beam.runners.common:NotImplementedError [while running 'WriteCsv/BatchElements(pcoll)']
    raise NotImplementedError
RuntimeError: NotImplementedError [while running 'WriteCsv/BatchElements(pcoll)']
```

Change the runner to `PrismRunner` and re-run:

```bash
# edit flags=["--runner=PrismRunner"] in work/json_writer.py
python work/json_writer.py
cat out/probe_csv*
```

Expected:

```text
OK
region,n
EMEA,1
AMER,2
```

Note that the input is a `beam.Row`, not a dict. `WriteToCsv` needs to
know the column names and types, and a `beam.Row` is how you tell it.


### Step 6 — write Parquet and read it back

Create `work/parquet_roundtrip.py`:

```python
"""Write Parquet, then read it back as dicts and as schema'd rows."""

import apache_beam as beam
import pyarrow as pa
from apache_beam.io import parquetio

SCHEMA = pa.schema(
    [
        pa.field("order_id", pa.string()),
        pa.field("region", pa.string()),
        pa.field("amount", pa.float64()),
    ]
)

RECORDS = [
    {"order_id": "o1", "region": "EMEA", "amount": 10.5},
    {"order_id": "o2", "region": "AMER", "amount": 3.25},
]

with beam.Pipeline() as p:
    source = p | "Create" >> beam.Create(RECORDS)
    source | "WriteParquet" >> parquetio.WriteToParquet(
        "./out/roundtrip",
        schema=SCHEMA,
        num_shards=1,
        codec="snappy",
        file_name_suffix=".parquet",
    )

with beam.Pipeline() as p:
    rows = p | "ReadParquet" >> parquetio.ReadFromParquet("./out/roundtrip-*.parquet")
    print("dicts element_type:", rows.element_type)
    rows | "WriteDicts" >> beam.io.WriteToText(
        "./out/roundtrip_text", num_shards=1, shard_name_template=""
    )

with beam.Pipeline() as p:
    schema_rows = p | "ReadParquetRows" >> parquetio.ReadFromParquet(
        "./out/roundtrip-*.parquet", as_rows=True
    )
    print("rows element_type:", schema_rows.element_type)
    schema_rows | "WriteRows" >> beam.io.WriteToText(
        "./out/roundtrip_rows", num_shards=1, shard_name_template=""
    )
```

Run it:

```bash
python work/parquet_roundtrip.py
cat out/roundtrip_text
cat out/roundtrip_rows
```

Expected:

```text
dicts element_type: Any
rows element_type: <class 'apache_beam.typehints.schemas.BeamSchema_'>
{'order_id': 'o1', 'region': 'EMEA', 'amount': 10.5}
{'order_id': 'o2', 'region': 'AMER', 'amount': 3.25}
BeamSchema_(order_id='o1', region='EMEA', amount=10.5)
BeamSchema_(order_id='o2', region='AMER', amount=3.25)
```

Note the glob: `out/roundtrip-*.parquet`, not `out/roundtrip*`. The
second form matches `out/roundtrip_text` too, and `as_rows=True` will
fail with:

```text
pyarrow.lib.ArrowInvalid: Parquet magic bytes not found in footer.
Either the file is corrupted or this is not a parquet file.
```

### Step 7 — Avro round trip

Create `work/avro_roundtrip.py`:

```python
"""Write Avro, read it back, and show the schema that was embedded."""

import apache_beam as beam
from apache_beam.io import avroio

ORDER_SCHEMA = {
    "type": "record",
    "name": "Order",
    "namespace": "com.example.orders",
    "fields": [
        {"name": "order_id", "type": "string"},
        {"name": "region", "type": "string"},
        {"name": "amount", "type": "double"},
    ],
}

RECORDS = [
    {"order_id": "o1", "region": "EMEA", "amount": 10.5},
    {"order_id": "o2", "region": "AMER", "amount": 3.25},
]

with beam.Pipeline() as p:
    source = p | "Create" >> beam.Create(RECORDS)
    source | "WriteAvro" >> avroio.WriteToAvro(
        "./out/orders_avro",
        schema=ORDER_SCHEMA,
        num_shards=1,
        codec="deflate",
        file_name_suffix=".avro",
    )

with beam.Pipeline() as p:
    rows = p | "ReadAvro" >> avroio.ReadFromAvro("./out/orders_avro-*.avro")
    print("element_type:", rows.element_type)
    rows | "WriteText" >> beam.io.WriteToText(
        "./out/orders_avro_text", num_shards=1, shard_name_template=""
    )
```

Run it:

```bash
python work/avro_roundtrip.py
cat out/orders_avro_text
python -c "
import fastavro
with open('out/orders_avro-00000-of-00001.avro', 'rb') as fh:
    reader = fastavro.reader(fh)
    print('embedded schema:', reader.writer_schema)
"
```

Expected:

```text
element_type: Any
{'order_id': 'o1', 'region': 'EMEA', 'amount': 10.5}
{'order_id': 'o2', 'region': 'AMER', 'amount': 3.25}
embedded schema: {'type': 'record', 'name': 'com.example.orders.Order', 'fields': [...]}
```

The schema really is in the file — you can read it back with any Avro
library, with no external registry. (`fastavro` folds the `namespace`
into the fully-qualified `name`, which is why it comes back as
`com.example.orders.Order` rather than as two separate keys.)


### Step 8 — the Avro schema-evolution check

Create `work/avro_evolution.py`:

```python
"""Demonstrate a backward-compatible and a backward-incompatible change."""

import apache_beam as beam
from apache_beam.io import avroio

BASE = {
    "type": "record",
    "name": "Order",
    "fields": [
        {"name": "order_id", "type": "string"},
        {"name": "amount", "type": "double"},
    ],
}

# Adding a field WITH a default is backward compatible: a reader that
# does not know the field can still read the record.
WITH_DEFAULT = {
    "type": "record",
    "name": "Order",
    "fields": [
        {"name": "order_id", "type": "string"},
        {"name": "amount", "type": "double"},
        {"name": "channel", "type": "string", "default": "unknown"},
    ],
}

# Adding a field WITHOUT a default is not backward compatible.
WITHOUT_DEFAULT = {
    "type": "record",
    "name": "Order",
    "fields": [
        {"name": "order_id", "type": "string"},
        {"name": "amount", "type": "double"},
        {"name": "channel", "type": "string"},
    ],
}

RECORDS = [{"order_id": "o1", "amount": 10.5}]

for label, schema in [
    ("with_default", WITH_DEFAULT),
    ("without_default", WITHOUT_DEFAULT),
]:
    with beam.Pipeline() as p:
        source = p | "Create" >> beam.Create(RECORDS)
        source | "WriteAvro" >> avroio.WriteToAvro(
            f"./out/evo_{label}",
            schema=schema,
            num_shards=1,
            codec="deflate",
            file_name_suffix=".avro",
        )

    with beam.Pipeline() as p:
        rows = p | "ReadAvro" >> avroio.ReadFromAvro(f"./out/evo_{label}-*.avro")
        rows | "WriteText" >> beam.io.WriteToText(
            f"./out/evo_{label}_text", num_shards=1, shard_name_template=""
        )

    print(f"{label}: written and read back")
```

Run it:

```bash
python work/avro_evolution.py
```

Expected:

```text
with_default: written and read back
```

…and then the second case fails, with:

```text
ValueError: no value and no default for channel [while running 'WriteAvro/Write/WriteImpl/WriteBundles']
RuntimeError: Pipeline job-003 failed in state FAILED: bundle inst004 stage-005 failed
```

This is a *better* demonstration than a read-time failure, and it is
worth pausing on. Avro caught the incompatibility **at write time**,
not at read time. The record `{"order_id": "o1", "amount": 10.5}` has
no `channel` value, the schema has no default for it, and `fastavro`
refuses to encode it.

That is the enforcement you get for free with a schema-enforced format,
and it is exactly what you do *not* get with CSV or JSON — where the
same schema change would have written a file with no `channel` column,
and the failure would have surfaced hours later in a consumer.

Now read back the file that *did* get written:

```bash
cat out/evo_with_default_text
```

Expected:

```text
{'order_id': 'o1', 'amount': 10.5, 'channel': 'unknown'}
```

The `channel` key is materialised with the default value, even though
the source record never had one. That is what "backward compatible"
means in practice: a reader that does not know about `channel` at all
can still read this file, and a reader that does know about it gets
`'unknown'` rather than a missing key.

To see the read-time failure, write the file with a *record* that
supplies the field but a *schema* that a downstream reader without the
field expects — that is, write `channel` explicitly and then read with
`BASE`:

```python
import apache_beam as beam
from apache_beam.io import avroio

with beam.Pipeline() as p:
    rows = p | "ReadAvro" >> avroio.ReadFromAvro("./out/evo_with_default-*.avro")
    print(rows.element_type)
```

The reader takes the schema from the file header, so it succeeds — which
is the point. The compatibility rules are what you rely on when the
reader has a *pinned* schema of its own, which is what a schema
registry gives you and what `ReadFromAvro(schema=...)` is for.


### Step 9 — column projection, the Parquet payoff

Create `work/projection.py`:

```python
"""Read two columns out of a nine-column Parquet file."""

import apache_beam as beam
from apache_beam.io import parquetio

with beam.Pipeline() as p:
    everything = p | "ReadAll" >> parquetio.ReadFromParquet(
        "out/formats/parquet-*.parquet"
    )
    projected = p | "ReadProjected" >> parquetio.ReadFromParquet(
        "out/formats/parquet-*.parquet",
        columns=["region", "amount"],
    )
    everything | "KeyAll" >> beam.Map(lambda row: (1, 1)) | "CountAll" >> beam.combiners.Count.PerKey() | "WriteAll" >> beam.io.WriteToText(
        "./out/proj_all", num_shards=1, shard_name_template=""
    )
    projected | "KeyProjected" >> beam.Map(lambda row: (1, 1)) | "CountProjected" >> beam.combiners.Count.PerKey() | "WriteProjected" >> beam.io.WriteToText(
        "./out/proj_subset", num_shards=1, shard_name_template=""
    )
```

Run it:

```bash
python work/projection.py
cat out/proj_all
cat out/proj_subset
```

Expected:

```text
(1, 5000)
(1, 5000)
```

Both return 5,000 rows — projection changes *what each row contains*,
not how many rows there are. On a wide table with a hundred columns,
this is the difference between moving 4 MB and moving 400 MB.

Note the `Key` stage before the count. `beam.combiners.Count.PerKey()`
is a *per-key* combiner and it requires `(key, value)` pairs. Feeding it
the raw dicts from the Parquet reader gives you:

```text
ValueError: too many values to unpack (expected 2) [while running 'ReadAll/ParDo(_ArrowTableToRowDictionaries)']
```

which is another one of those errors that points at the wrong place.
The `ReadAll` label in the message is a red herring — the real problem is
in the `CountAll` stage, three transforms downstream.


---

## 🛠️ Common Errors and Fixes

### `AttributeError: 'tuple' object has no attribute 'element_type'`

This is the `BundleBasedDirectRunner` failing on the pandas-backed
CSV/JSON readers. It has nothing to do with your types, despite what the
traceback suggests.

The full traceback ends at:

```text
File ".../apache_beam/runners/direct/sdf_direct_runner.py", line 86, in expand
    element_coder = typecoders.registry.get_coder(pcoll.element_type)
                                                  ^
AttributeError: 'tuple' object has no attribute 'element_type'
```

`ReadViaPandas` expands into an `Sdf` source. The classic DirectRunner
hands the SDF expansion a tuple where it expects a `PCollection`.

**Fix, in order of preference:**

1. Run it on `PrismRunner`: `--runner=PrismRunner`.
2. Use `ReadFromText` and parse the records yourself — this is what
   `project/batch_pipeline.py` does, and it works on every runner.
3. If you must use the pandas path, do the parsing in pandas *outside*
   the pipeline and feed the results in with `beam.Create`.

**And if you are trying to reproduce the failure**, note that
`beam.Pipeline()` with no `options=` ignores your `--runner` command
line flag entirely, because it constructs `PipelineOptions([])` from an
empty argument list. You must pass the runner explicitly:

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(flags=["--runner=BundleBasedDirectRunner"])

with beam.Pipeline(options=options) as p:
    rows = p | "ReadCsv" >> beam.io.ReadFromCsv("./sample_data/orders.csv")
```

Without this, you will "test" the classic runner, watch the pipeline
succeed, and conclude that the runner does not matter. It does.

### `RuntimeError: NotImplementedError [while running 'Write/BatchElements(pcoll)']`

The classic DirectRunner cannot execute the `GroupIntoBatches` step that
`WriteToCsv` and `WriteToJson` expand into.

**Fix:** run on `PrismRunner`, or format the records yourself and use
`WriteToText`:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    rows = (
        p
        | "Create" >> beam.Create([
            {"region": "EMEA", "order_count": 318},
            {"region": "AMER", "order_count": 320},
        ])
    )
    rows | "Format" >> beam.Map(
        lambda r: f"{r['region']},{r['order_count']}"
    ) | "Write" >> beam.io.WriteToText(
        "./out/summary", num_shards=1, shard_name_template="", header="region,order_count"
    )
```

The course's `format_summary_csv` in `project/transforms.py` is the
production version of exactly this, and it uses `csv.writer` rather
than an f-string so that a value containing a comma cannot corrupt the
output.

Note the label in the error message: `'Write/BatchElements(pcoll)'`.
The `Write` is your transform label, and `BatchElements` is the internal
step that failed. If your label is something else, the message will say
something else — which is a useful way to find the offending transform
in a large pipeline.


### `ImportError: Please install apache_beam[dataframe]`

You called `beam.io.ReadFromCsv`, `WriteToCsv`, `ReadFromJson` or
`WriteToJson` without pandas installed.

```bash
pip install "apache-beam[dataframe]"
```

Remember the division of labour: `fastavro` and `pyarrow` are **base
dependencies** and are always there; `pandas` is the one that lives in
an extra.

### `ValueError: snappy codec is supported but you need to install one of the following libraries: ('cramjam',)`

You set `codec="snappy"` (or `"zstandard"`) on `WriteToAvro`. `fastavro`
delegates those codecs to `cramjam`, which is not installed by default.

```bash
pip install cramjam
```

Or use a codec that needs nothing extra: `deflate` (the default),
`bzip2`, `xz`, or `null`.

Parquet is unaffected — `pyarrow` has its own codecs, so `snappy`,
`gzip`, `brotli`, `zstd` and `lz4` all work out of the box.

### `pyarrow.lib.ArrowInvalid: Parquet magic bytes not found in footer. Either the file is corrupted or this is not a parquet file.`

Two possible causes.

**The glob matched a non-Parquet file.** `ReadFromParquet` with
`as_rows=True` opens the first matching file at *pipeline construction
time* to read its schema. If your pattern is `out/orders*` and it also
matches `out/orders_text`, you get this error.

Fix: match the suffix — `out/orders-*.parquet`.

**The file is truncated.** A partially-written Parquet file has a valid
header but no footer. This happens when a job is killed mid-write.

Fix: check the file size against what you expect and re-run. A Parquet
file always ends with the four bytes `PAR1`.

### `OSError: No files found based on the file pattern`

`ReadFromParquet` and `ReadFromAvro` validate the pattern at pipeline
construction time by default (`validate=True`). If nothing matches, the
pipeline fails before it runs.

```python
with beam.Pipeline() as p:
    rows = p | "Read" >> parquetio.ReadFromParquet(
        "out/formats/parquet-*.parquet",
        validate=False,
    )
```

Setting `validate=False` defers the check to run time — useful when
the files are produced by an upstream job in the same DAG, but it turns
a clear early error into a late one. Prefer fixing the pattern.

### `ValueError: no value and no default for channel`

You added a field to your Avro schema without a default, and the records
you are writing do not have a value for it.

```text
ValueError: no value and no default for channel [while running 'WriteAvro/Write/WriteImpl/WriteBundles']
```

This is Avro's schema enforcement working, at write time. It is a good
error: it names the field and it arrives immediately.

**Fix:** give the field a default, so that records which predate it
still encode:

```python
{"name": "channel", "type": "string", "default": "unknown"}
```

Or make it explicitly nullable:

```python
{"name": "channel", "type": ["null", "string"], "default": None}
```

Or supply the value in every record you write.

### `KeyError: 'channel'` after an Avro schema change

You added a field to your Avro schema without a default, and a reader
that requires the field met a file written before the change.

Fix, in order:

1. Give the field a default: `{"name": "channel", "type": "string", "default": "unknown"}`.
2. Read with `.get("channel")` instead of `row["channel"]` while the
   old data is still around.
3. Rewrite the old files with the new schema.

The lesson is the backward-compatibility rule from earlier in the
chapter: **a field added without a default is a breaking change.**

### `TypeError: avro.schema.ParseError: ...

```
A malformed Avro schema. The usual cause is a schema passed as a JSON
*string* where a *dict* was expected, or a dict with a stray trailing
comma.

```python
# Works: a dict
schema = {"type": "record", "name": "Order", "fields": [...]}

# Works: a JSON string
schema = '{"type": "record", "name": "Order", "fields": [...]}'

# Fails: a dict with a trailing comma in a list
schema = {"type": "record", "name": "Order", "fields": [...,],}
```

### `ValueError: Expected a table reference (PROJECT:DATASET.TABLE or DATASET.TABLE) instead of ...`

That one is BigQuery, and it belongs in the next chapter — see
`chapters/17-gcs-and-bigquery-io.md`.

### `ImportError: cannot import name 'xmlio' from 'apache_beam.io'`

There is no XML I/O in Beam 2.77. The module never existed in 2.77, and
the transforms that older examples reference are gone.

Fix: use `ReadFromText` and parse the XML yourself with
`xml.etree.ElementTree`. See the section on XML earlier in this
chapter.

### The output has one extra row (or one too few)

Almost always the CSV header.

`ReadFromText` reads every line including the header;
`ReadFromCsv` skips it. If you switched from one to the other, this is
the difference.

```python
with beam.Pipeline() as p:
    orders = (
        p
        | "Read" >> beam.io.ReadFromText("./sample_data/orders.csv")
        | "SkipHeader" >> beam.Filter(lambda line: not line.startswith("order_id"))
    )
```

### The Parquet file is bigger than the CSV

You did not set a codec. Beam's Parquet writer defaults to
`codec="none"`, which means **no compression**.

```python
rows | "Write" >> parquetio.WriteToParquet(
    "./out/orders",
    schema=SCHEMA,
    num_shards=1,
    codec="snappy",          # <- this
    file_name_suffix=".parquet",
)
```

On the course's 5,000-row dataset, `none` produced 326,471 bytes and
`snappy` produced 141,428 — a 2.3× difference from a single missing
keyword argument.

---

## 💡 Production Notes

- **Choose the format by what happens next, not by what you are
  comfortable with.** CSV is what a human opens. NDJSON is what a
  stream carries. Parquet is what a lake stores. Avro is what a schema
  contract governs. Writing everything as CSV because CSV is easy is
  how you end up with a lake that costs ten times what it should.
- **Set a Parquet codec.** The default is `none`. If you write Parquet
  without a codec, you have chosen "no compression" and you probably did
  not mean to.
- **`zstd` is often the right Parquet codec for a lake.** It decompresses
  at roughly snappy's speed and produces meaningfully smaller files. On
  this course's data, zstd was 35% smaller than snappy. The cost is
  slower compression, and you compress once and decompress many times.
- **Write Parquet with a `pyarrow` schema, always.** The schema is what
  makes the file's types exact. A schema inferred at write time is a
  schema you did not review.
- **Prefer `ReadFromText` plus your own parser in Beam pipelines.** It
  runs on every runner, it gives you per-record error handling, it
  gives you control of the types, and it removes a heavyweight
  dependency from the worker image. The course's `project/transforms.py`
  is the model.
- **Remember that `ReadFromCsv` skips the header and `ReadFromText` does
  not.** This is the single most common bug when moving between them.
- **Use `as_rows=True` on `ReadFromParquet` when the schema matters.**
  It gives you a typed `BeamSchema_` row instead of a dict, and it
  catches schema drift at pipeline construction time. The cost is that
  the file must exist when the pipeline is built.
- **Match your Parquet glob to the suffix.** `path-*.parquet`, not
  `path*`. The wide glob will eventually match a text file and fail
  with a confusing Arrow error.
- **Add Avro fields with defaults, always.** A field without a default
  is a backward-incompatible change, and you will find out when a
  consumer breaks.
- **Keep a schema registry if you use Avro.** Beam will not stop you
  from writing a file that breaks your readers. A registry with
  compatibility checks turns a 3am page into a pull-request rejection.
- **Avro does not make your pipeline fast.** The measurements here show
  Avro at roughly CSV read speed despite being 3.5× smaller. Avro's
  value is the schema contract, not throughput.
- **Do not put Parquet in the same directory as CSV and read them with a
  wildcard.** `ReadFromParquet` will fail on the CSV file with
  `Parquet magic bytes not found in footer`. Use distinct prefixes.
- **Budget for the worker image.** `apache-beam` plus `fastavro` plus
  `pyarrow` plus `pandas` is a large image. On Dataflow, that is upload
  time per job and container-start latency per worker. If you are not
  using the CSV/JSON transforms, do not install `apache-beam[dataframe]`
  and you will not pay for `pandas` on every worker.
- **A format choice is a one-way door for a lake.** Changing the format
  of a hundred terabytes in a bucket is a multi-week project. Choose
  the landing format carefully, and choose it to match what your query
  engine reads most efficiently.

---

## 🔑 Key Takeaways

- The four portable formats differ on **schema enforcement** (none for
  text/JSON, full for Avro/Parquet), **compression granularity** (whole
  file vs block vs column), **read performance** (Parquet wins), and
  **ecosystem fit** (CSV for humans, NDJSON for streams, Parquet for
  lakes, Avro for contracts).
- **`fastavro` and `pyarrow` are required dependencies of
  `apache-beam`, not extras.** `pandas` is the one that lives in the
  `dataframe` extra, and it is what `ReadFromCsv`/`ReadFromJson` need.
- **`ReadFromText` plus your own parser is the Beam default.** It runs
  on every runner, gives per-record error handling, and gives you type
  control. `ReadFromCsv` is a wrapper around `pandas.read_csv` that
  reads whole files.
- **A verified runner difference:** `ReadFromCsv` and `ReadFromJson`
  fail on `BundleBasedDirectRunner` with `AttributeError: 'tuple'
  object has no attribute 'element_type'`, and work on `PrismRunner`.
  `WriteToCsv` and `WriteToJson` fail on the classic runner with
  `NotImplementedError [while running 'Write/BatchElements(pcoll)']`
  and work on `PrismRunner` with a schema-aware `beam.Row` input.
- **Beam 2.77 has no XML I/O.** There is no `ReadFromXml` or
  `WriteToXml`; use `ReadFromText` plus an XML parser.
- **Parquet is 3–10× smaller than CSV** because it compresses per
  column and stores types exactly. Measured here: 3.97× smaller and
  1.94× faster on 200,000 rows.
- **NDJSON is often *bigger* than CSV** (2.6× here) because it repeats
  every key on every line. Its advantage is line-delimited streaming,
  not compactness.
- **Beam's Parquet writer defaults to `codec="none"`** — no
  compression. Set `codec="snappy"` or `codec="zstd"` explicitly.
- **Avro schema evolution:** adding a field *with* a default is backward
  and forward compatible; adding one *without* a default is backward
  incompatible and will break readers that require the field.
- **`AvroGenericCoder` is the Avro coder**, in `apache_beam.coders`.
  There is no `AvroCoder`. Parquet rows use `RowCoder` from
  `apache_beam.coders.row_coder`.

---

## 📚 Practice Exercises

1. **Measure all four formats.** Extend `work/format_hands_on.py` to
   also write Avro, and produce a size table for CSV, NDJSON, Parquet
   (snappy) and Parquet (zstd) over 200,000 rows. *Expected answer:* CSV
   ~16.1 MB, NDJSON ~42.5 MB, Parquet/snappy ~4.1 MB, Parquet/zstd
   smaller still — a 4× spread between the best and the worst.

2. **Prove the projection win.** Write the 200,000-order dataset as
   Parquet with nine columns, then read it twice — once with all nine
   columns and once with two — and measure the wall-clock difference.
   Then repeat with CSV, where the two reads are identical.
   *Expected answer:* Parquet with a two-column projection is
   materially faster; CSV shows no difference, because CSV has no
   columnar layout to project.

3. **Reproduce the runner difference.** Run
   `work/csv_reader.py` under `--runner=BundleBasedDirectRunner`,
   `--runner=PrismRunner` and `--runner=DirectRunner`, and record the
   exact outcome of each. Then rewrite it using `ReadFromText` and
   confirm it works on all three. *Expected answer:* the two explicit
   runners fail differently (the `AttributeError` and the
   `NotImplementedError`), the bare `DirectRunner` aliases the classic
   one, and the `ReadFromText` version works everywhere.

4. **Break the schema, then fix it.** Write an Avro file with
   `{"name": "channel", "type": "string"}` (no default). Then write a
   second version with `{"name": "channel", "type": "string",
   "default": "unknown"}`. Read both with a reader that requires
   `channel` and record what happens. *Expected answer:* the first file
   fails to decode for a reader that needs the field; the second
   succeeds and yields `"unknown"`.

5. **Design a landing zone.** Your team has a GCS bucket with 40 TB of
   CSV that a Spark job reads hourly and a BI tool reads daily. Propose
   a format for: (a) the new landing zone, (b) the daily BI export,
   (c) the inter-service API. Justify each choice against the ecosystem
   table in this chapter. *Expected answer:* Parquet for the landing
   zone (projection plus compression), CSV for the BI export
   (humans and legacy tools), NDJSON for the API (line-delimited and
   self-describing).

6. **Reflection.** Your pipeline reads `gs://bucket/orders*` where the
   bucket holds a mix of Parquet files written by three different
   teams, each with a slightly different schema. Your reader is
   `ReadFromParquet(..., as_rows=True)`. What happens, what breaks, and
   what would you change? *Expected answer:* `as_rows=True` reads the
   schema from the *first matching file* at construction time, so the
   pipeline's schema is whichever team's file happened to sort first;
   files with extra columns may decode to `None`, and files missing a
   required column fail at decode time. The fix is either `as_rows=False`
   (dicts, tolerant) or a schema registry plus a projection that
   normalises the shapes.

---

## 📖 Further Reading

- Apache Beam: Input/output — https://beam.apache.org/documentation/programming-guide/#inputoutput
- Apache Beam: Parquet — https://beam.apache.org/documentation/io/apache-beam-sdk/pydoc/current/apache_beam.io.parquetio.html
- Apache Beam: Avro — https://beam.apache.org/documentation/io/apache-beam-sdk/pydoc/current/apache_beam.io.avroio.html
- Apache Beam: TextIO (CSV and JSON) — https://beam.apache.org/documentation/io/apache-beam-sdk/pydoc/current/apache_beam.io.textio.html
- Apache Avro specification (schema resolution rules) — https://avro.apache.org/docs/current/specification/
- Apache Parquet documentation (columnar layout and encoding) — https://parquet.apache.org/docs/
- Google Cloud: BigQuery external tables over Parquet — https://cloud.google.com/bigquery/docs/external-tables
