#!/usr/bin/env python3
"""Build notebooks/03-io-and-file-formats.ipynb."""
import json
from pathlib import Path

CELLS = []


def md(source):
    CELLS.append({"cell_type": "markdown", "metadata": {}, "source": source.strip("\n").splitlines(keepends=True)})


def code(source):
    CELLS.append(
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": source.strip("\n").splitlines(keepends=True),
        }
    )


md(r"""
# 03 · I/O & File Formats

> **Module 3 · I/O & Multi-Source Pipelines · Lecture 3.1**

In this notebook you will:

- Read and write text, and learn why you must never hard-code a shard filename
- See what a **coder** is, and how `TupleCoder` and `TypeOptions` work
- Read CSV and JSON the reliable way — `ReadFromText` plus a parser
- Understand why `ReadFromCsv` and `ReadFromJson` are the fragile path
- Write **Avro** and **Parquet**, and measure the bytes against JSON
- Merge two sources with `Flatten`, and fan one source out to many sinks

Every cell runs on your laptop. Nothing here needs a GCP account, and
nothing reaches the network.

---

## 1. Setup

The sample data is regenerated only when it is missing, because the
generator is seeded and deterministic. That means the numbers in this
notebook are stable across runs and across machines.
""")

code(r"""
import csv
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

COURSE_ROOT = Path.cwd()
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = COURSE_ROOT.parent

PROJECT_DIR = COURSE_ROOT / "project"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

if not (COURSE_ROOT / "sample_data" / "orders.csv").exists():
    subprocess.run(
        [sys.executable, str(COURSE_ROOT / "resources" / "sample_data.py"),
         "--output-dir", str(COURSE_ROOT / "sample_data")],
        check=True,
    )

import apache_beam as beam
from apache_beam import coders
from apache_beam.coders.typecoders import registry
from apache_beam.options.pipeline_options import PipelineOptions, TypeOptions
import apache_beam.typehints as th

# The classic pure-Python runner. It supports the full feature set, which
# matters here because `ReadFromCsv` and `ReadFromJson` do not work on it.
LOCAL_OPTIONS = PipelineOptions(["--runner", "BundleBasedDirectRunner"])

SCRATCH = COURSE_ROOT / "out" / "nb03"
if SCRATCH.exists():
    shutil.rmtree(SCRATCH)
SCRATCH.mkdir(parents=True, exist_ok=True)

ORDERS_CSV = str(COURSE_ROOT / "sample_data" / "orders.csv")
EVENTS_NDJSON = str(COURSE_ROOT / "sample_data" / "events.ndjson")

print("beam        :", beam.__version__)
print("course root :", COURSE_ROOT)
print("scratch     :", SCRATCH)
""")

md(r"""
## 2. Text I/O and the sharded output filename

`ReadFromText` and `WriteToText` are the two transforms you will use in
every pipeline you write, so their defaults are worth knowing exactly.

`WriteToText` takes a **prefix**, not a filename. It writes a set of
**shard files** whose names are derived from that prefix, and the number
of shards is chosen by the runner at execution time — it depends on how
much data there is and how many workers picked it up. The default template
in Beam 2.77 is:

```text
prefix-00000-of-00001
prefix-00001-of-00004
...
```

The old-style `prefix00000of00001` template is what older Beam versions
used. The lesson is the same either way and is the thing worth internalising:

> **The output path you give `WriteToText` is a prefix, and the real file
> names are chosen at run time. Never hard-code one.**

If you do, your pipeline breaks the moment the runner picks a different
number of shards — which it will, without warning, the day the input
grows. The correct way to find your output is a **glob**:

```python
sorted(Path(prefix).parent.glob(Path(prefix).name + "*"))
```

### Why the glob is the *only* correct way

Three reasons, and each one has bitten somebody in production:

1. **The shard count is not yours to choose.** The runner picks it. A
   small input may produce one shard; a large one produces thousands. The
   same code, the same prefix, different files.
2. **The shard count changes between runs.** Retries, autoscaling, and
   input-size changes all move it. A pipeline that reads a hard-coded
   shard name works until the day it does not.
3. **Some sinks write several files per shard.** `WriteToText` with
   `num_shards=1` writes one file, but the default `num_shards=0` means
   "the runner decides", and a multi-worker job writes several.

The glob is the contract. Treat the prefix as a *directory-like handle*,
not a filename.

### A note on `shard_name_template`

When you want a teaching-friendly single file, pass `num_shards=1` and
`shard_name_template=""`. That makes the output exactly the prefix you
asked for. The course project does this so the output is diffable. It is a
teaching choice, not a production one — in production you want the
shards.
""")

code(r"""
# A tiny pipeline, so we can look at exactly what lands on disk.
TEXT_PREFIX = str(SCRATCH / "orders_by_region")

with beam.Pipeline(options=LOCAL_OPTIONS) as p:
    (
        p
        | "CreateRegions" >> beam.Create(["EMEA", "AMER", "APAC"])
        | "FormatRegion" >> beam.Map(lambda region: f"region={region}")
        | "WriteText" >> beam.io.WriteToText(TEXT_PREFIX)
    )

written = sorted(p.name for p in SCRATCH.glob("orders_by_region*"))
print("files written under the prefix:")
for name in written:
    print("   ", name)

print()
print("The path we passed was :", TEXT_PREFIX)
print("The file that exists is:", written[0])
print()
print("Two ways to find the output — both are correct:")
print("  glob  :", written)
print("  prefix:", TEXT_PREFIX, "->", written[0] if written else "(nothing)")

print()
print("--- The three shard-name templates, side by side ---")
for template, label in ((None, "default"), ("", "empty"), ("-SSSS-of-SSSS", "explicit")):
    target = str(SCRATCH / f"tmpl_{label}")
    with beam.Pipeline(options=LOCAL_OPTIONS) as p:
        (
            p
            | "CreateOne" >> beam.Create(["x"])
            | "WriteOne" >> beam.io.WriteToText(target, num_shards=1,
                                                shard_name_template=template)
        )
    names = sorted(p.name for p in SCRATCH.glob(f"tmpl_{label}*"))
    print(f"  shard_name_template={str(template):16s} -> {names}")

print()
print("Note the explicit template uses FOUR digits, not five:")
print("  '-SSSS-of-SSSS' -> 0000, because SSSS is four 'S' characters.")
""")

md(r"""
## 3. Coders and type hints

A **coder** is Beam's answer to "how do I turn this Python object into
bytes?". It is the layer underneath every shuffle, every side input, and
every sink. If Beam cannot pick a coder for your elements, the pipeline
fails at construction time with `CoderNotDefinedError`.

Beam's type-hint system maps a Python type to a coder through a
**registry**:

| Python type | Coder |
|---|---|
| `int` | `VarIntCoder` |
| `str` | `StrUtf8Coder` |
| `bytes` | `BytesCoder` |
| `float` | `FloatCoder` |
| `Tuple[int, str]` | `TupleCoder` |
| `Dict[str, int]` | `MapCoder` |

`TupleCoder` is the one worth understanding, because a `(key, value)`
pair is what every grouping transform consumes. It is a **container
coder**: it holds one coder per field and serialises the tuple field by
field. A `Tuple[int, str]` is encoded as a varint followed by a
length-prefixed UTF-8 string — no pickle, no reflection, and therefore
readable by a non-Python runner.

### `TypeOptions` and `with_output_types`

`TypeOptions` is the `PipelineOptions` view that carries the
type-hinting settings. `with_output_types` is the ergonomic way to use
it: attach a type hint to a transform, and Beam selects the coder for
you.

```python
(p | "Map" >> beam.Map(fn).with_output_types(th.Tuple[str, int]))
```

The hint does two things. It tells Beam **which coder** to use, and it
gives Beam **the schema**, which is what the `Avro` and `Parquet` sinks
need.
""")

code(r"""
# What does the registry pick for each type?
for label, hint in (
    ("int", int),
    ("str", str),
    ("bytes", bytes),
    ("float", float),
    ("Tuple[int, str]", th.Tuple[int, str]),
    ("Dict[str, int]", th.Dict[str, int]),
):
    coder = registry.get_coder(hint)
    print(f"  {label:20s} -> {type(coder).__name__}")

print()
print("TupleCoder is a container coder — one coder per field:")
tuple_coder = registry.get_coder(th.Tuple[int, str])
print("  coders :", tuple_coder.coders)
print("  is_deterministic:", tuple_coder.is_deterministic())

print()
print("The type-hint view that carries these settings:")
options = PipelineOptions([])
print("  TypeOptions view:", type(options.view_as(TypeOptions)).__name__)

print()
print("--- `with_output_types` tells Beam the schema of the output ---")
with beam.Pipeline(options=LOCAL_OPTIONS) as p:
    unannotated = p | "CreateBare" >> beam.Create([("EMEA", 1), ("AMER", 2)])
    annotated = (
        p
        | "CreateHinted" >> beam.Create([("EMEA", 1), ("AMER", 2)])
        | "MapHinted" >> beam.Map(lambda kv: (kv[0], kv[1] + 1))
        .with_output_types(th.Tuple[str, int])
    )

print("without a hint :", unannotated.element_type)
print("with a hint    :", annotated.element_type)
print()
print("Both are Tuple[str, int] here because Beam could infer it from")
print("the literal. The hint matters when inference is impossible — a")
print("function returning a union, an empty collection, or a dict whose")
print("value type varies.")
""")

md(r"""
## 4. CSV — the reliable path, and the fragile one

There are two ways to read CSV in Beam.

**The reliable path** is `ReadFromText` plus the standard library's `csv`
module. You get the raw lines, the standard library does the parsing,
and you control every detail: the header, the quoting, the malformed
rows.

### A gotcha worth ten minutes

`csv.DictReader` treats its **first** row as the header. So you cannot
hand it a single data line and expect a dict:

```python
next(csv.DictReader([line]))   # raises StopIteration
```

The reader consumed `line` as the header and then had nothing left to
read. The fix is to read the header **once**, outside the pipeline, and
zip every data line against it — which is exactly what the course
project's `try_parse_order_line` does. We will use that shape below.

**The fragile path** is `beam.io.ReadFromCsv`. It is more concise, but
it has a real problem on the runner this course uses. `ReadFromCsv` and
`ReadFromJson` both fail under `BundleBasedDirectRunner` with:

```text
AttributeError: 'tuple' object has no attribute 'element_type'
```

That is a genuine Beam bug in 2.77, not a mistake in your code. The
readers work under the **Prism** runner (`beam.DirectRunner` in Beam
2.60+, which is the Go-based in-process runner), so they are not
unusable — they are just not usable on the runner the rest of the course
runs on.

### The fragile path, demonstrated honestly

We will run `ReadFromCsv` under the Prism runner so it works, and show
the failure under the classic runner. The failure is caught in a
`try`/`except` so the notebook still runs top to bottom.

`ReadFromCsv` infers a **row type** from the header — you can see it in
the `element_type` below — and it parses the `amount` column as a
float automatically. That is convenient. It is also a schema *guess*:
the inference happens from the first line, so a file whose header and
first row disagree produces a confusing type error.

The professional answer is: **use `ReadFromText` + the `csv` module for
production code.** It is portable across runners, it handles ragged
rows the way you want, and it gives you the raw line when a row is
malformed, which is exactly what you need for a dead-letter queue.
""")

code(r"""
# --- The reliable path -----------------------------------------------------
#
# `csv.DictReader` treats its FIRST row as the header. So you cannot feed
# it one data line and expect a dict — `next(csv.DictReader([line]))`
# raises StopIteration, because there is no second row to read.
#
# The fix is to read the header ONCE, outside the pipeline, and then zip
# each data line against it. That is exactly what the course project's
# `try_parse_order_line` does.
with open(ORDERS_CSV, encoding="utf-8") as fh:
    CSV_HEADER = next(csv.reader(fh))


def parse_order_line(line):
    # Parse one CSV line into a dict, using the header we read once.
    values = next(csv.reader([line]))
    return dict(zip(CSV_HEADER, values))


with beam.Pipeline(options=LOCAL_OPTIONS) as p:
    (
        p
        | "ReadOrderLines" >> beam.io.ReadFromText(ORDERS_CSV)
        | "SkipOrderHeader" >> beam.Filter(lambda line: not line.startswith("order_id"))
        | "ParseOrderRows" >> beam.Map(parse_order_line)
        | "KeepRegion" >> beam.Map(lambda row: f"{row['region']},{row['currency']},{row['amount']}")
        | "WriteOrderRows" >> beam.io.WriteToText(
            str(SCRATCH / "csv_reliable"), num_shards=1, shard_name_template="")
    )

print("Reliable path (ReadFromText + csv.DictReader):")
for line in sorted((SCRATCH / "csv_reliable").read_text(encoding="utf-8").splitlines())[:4]:
    print("   ", line)

print()
print("Note what the reliable path gives you that the fragile path does not:")
print("  * the raw line is still available, so a DLQ can record it verbatim")
print("  * csv.DictReader handles quoted fields containing commas")
print("  * a ragged row raises here, where you can catch it, not inside a sink")

try:
    with beam.Pipeline(options=LOCAL_OPTIONS) as p:
        _ = p | "ReadCsvFragile" >> beam.io.ReadFromCsv(ORDERS_CSV)
    print("unexpectedly succeeded")
except Exception as exc:
    print("ReadFromCsv under BundleBasedDirectRunner:")
    print(f"   {type(exc).__name__}: {str(exc)[:110]}")
    print()
    print("This is the known Beam 2.77 bug. The same reader works on Prism.")
    print()

# The fragile path under Prism: it works, but it needs its own runner.
PRISM_OPTIONS = PipelineOptions(["--runner", "DirectRunner"])

with beam.Pipeline(options=PRISM_OPTIONS) as p:
    rows = p | "ReadCsvPrism" >> beam.io.ReadFromCsv(ORDERS_CSV)
    print("ReadFromCsv element_type (Prism):")
    print("   ", rows.element_type)
    print()
    print("Beam inferred a row type from the header, and typed `amount`")
    print("as a float. Convenient — but inferred, not declared.")

    keyed = rows | "KeyAll" >> beam.Map(lambda row: ("all", 1))
    counted = keyed | "CountAll" >> beam.combiners.Count.PerKey()
    counted | "WriteCount" >> beam.io.WriteToText(
        str(SCRATCH / "csv_prism_count"), num_shards=1, shard_name_template="")

print()
print("rows read by ReadFromCsv:",
      open(SCRATCH / "csv_prism_count").read().strip())
""")

md(r"""
## 5. JSON — same story, plus JSON Lines

JSON Lines is the format the course uses for events: one JSON object
per line, newline-delimited. It is the natural format for a streaming
pipeline because each line is independently parseable — you never need
to buffer the whole file to read one record, which is exactly what
`ReadFromPubSub` gives you per message.

The reliable path is `ReadFromText` plus `json.loads`. The fragile path
is `beam.io.ReadFromJson`, which has the same runner bug as
`ReadFromCsv`.

Let's do a **JSON Lines round-trip**: read the NDJSON events, parse them,
and write them back out as NDJSON. The output should be byte-identical
in structure to the input, which is the property that matters.
""")

code(r"""
# --- Reliable JSON path: ReadFromText + json.loads -------------------------
with beam.Pipeline(options=LOCAL_OPTIONS) as p:
    (
        p
        | "ReadEventLines" >> beam.io.ReadFromText(EVENTS_NDJSON)
        | "ParseEvents" >> beam.Map(json.loads)
        | "KeepPurchases" >> beam.Filter(lambda event: event["event_type"] == "purchase")
        | "FormatEvent" >> beam.Map(
            lambda event: json.dumps(
                {
                    "event_id": event["event_id"],
                    "region": event["region"],
                    "value": event["value"],
                },
                sort_keys=True,
            )
        )
        | "WriteEvents" >> beam.io.WriteToText(
            str(SCRATCH / "events_roundtrip"), num_shards=1, shard_name_template="")
    )

print("JSON Lines round-trip — first three lines written:")
for line in (SCRATCH / "events_roundtrip").read_text(encoding="utf-8").splitlines()[:3]:
    print("   ", line)

print()
print("The output is NDJSON again: one JSON object per line, newline")
print("delimited. The pipeline did not need to know the file was JSON")
print("at all — `ReadFromText` gave it lines, and `json.loads` gave it")
print("dicts.")

print()
print("The fragile path, ReadFromJson, has the same runner restriction:")
try:
    with beam.Pipeline(options=LOCAL_OPTIONS) as p:
        _ = p | "ReadJsonFragile" >> beam.io.ReadFromJson(EVENTS_NDJSON)
    print("   unexpectedly succeeded")
except Exception as exc:
    print(f"   {type(exc).__name__}: {str(exc)[:110]}")
""")

md(r"""
## 6. Avro and Parquet — the binary formats

JSON is fine for a log or an API, and terrible for a warehouse. Three
properties separate them:

| | JSON Lines | Avro | Parquet |
|---|---|---|---|
| Size | large — the keys repeat in every line | compact — a schema is written once | smallest — columnar + compressed |
| Schema | implicit | explicit, in the file header | explicit, in the file footer |
| Queryable | no | no (row-oriented, still needs a reader) | yes — BigQuery, Spark, DuckDB read it directly |
| Partial read | yes | no | yes — column pruning |
| Evolution | whatever you wrote | schema resolution rules | additive changes only |

### What the libraries add

Neither format is implemented in the Beam SDK itself.

- **Avro** needs `fastavro`. Beam's `avroio` module shells out to it for
  both reading and writing, so the `fastavro` package is a hard
  requirement, not an extra.
- **Parquet** needs `pyarrow`. Beam's `parquetio` module converts rows
  to Arrow tables and writes them with `pyarrow`.

Both are installed in the course environment. But note the runner
restriction, which the course does not mention:

> **`WriteToParquet` raises `NotImplementedError` under
> `BundleBasedDirectRunner`.** It only works under the Prism runner.

`WriteToAvro` works on both.

### The concrete size comparison

This is the number worth remembering. We wrote the **same three rows** in
all three formats and measured the bytes on disk.

### The schema requirement

Avro takes an explicit schema dictionary. Parquet derives its schema
from the **input PCollection's element type**, and it cannot derive one
from a plain `dict`. A `typing.NamedTuple` works, because Beam can turn
a named tuple into a row type.
""")

code(r"""
import typing
from apache_beam.io import avroio, parquetio

ORDER_SCHEMA = {
    "type": "record",
    "name": "Order",
    "fields": [
        {"name": "order_id", "type": "string"},
        {"name": "region", "type": "string"},
        {"name": "amount", "type": "double"},
    ],
}

OrderRow = typing.NamedTuple(
    "OrderRow", [("order_id", str), ("region", str), ("amount", float)]
)

# --- The same real data, written three ways -------------------------------
#
# We use the course's actual 5,000 orders, projected onto a small
# schema, so the byte counts are representative rather than a toy.
CSV_ROWS = []
with open(ORDERS_CSV, encoding="utf-8") as fh:
    reader = csv.DictReader(fh)
    for row in reader:
        CSV_ROWS.append({
            "order_id": row["order_id"],
            "region": row["region"],
            "amount": float(row["amount"]),
        })

# --- JSON baseline ---------------------------------------------------------
with beam.Pipeline(options=LOCAL_OPTIONS) as p:
    (
        p
        | "CreateJsonRows" >> beam.Create(CSV_ROWS)
        | "FormatJsonRows" >> beam.Map(lambda row: json.dumps(row, sort_keys=True))
        | "WriteJson" >> beam.io.WriteToText(
            str(SCRATCH / "rows.json"), num_shards=1, shard_name_template="")
    )

# --- Avro ------------------------------------------------------------------
with beam.Pipeline(options=LOCAL_OPTIONS) as p:
    (
        p
        | "CreateAvroRows" >> beam.Create(CSV_ROWS)
        | "WriteAvro" >> avroio.WriteToAvro(
            str(SCRATCH / "rows.avro"), schema=ORDER_SCHEMA,
            num_shards=1, file_name_suffix=".avro")
    )

# --- Parquet (Prism only) --------------------------------------------------
with beam.Pipeline(options=PRISM_OPTIONS) as p:
    (
        p
        | "CreateParquetRows" >> beam.Create(
            [OrderRow(r["order_id"], r["region"], r["amount"]) for r in CSV_ROWS])
        | "WriteParquet" >> parquetio.WriteToParquet(
            str(SCRATCH / "rows.parquet"), num_shards=1, file_name_suffix=".parquet")
    )

print(f"rows written in each format: {len(CSV_ROWS)}")
print("Avro files   :", sorted(p.name for p in SCRATCH.glob("rows.avro*")))
print("Parquet files:", sorted(p.name for p in SCRATCH.glob("rows.parquet*")))


def size_of(pattern):
    # Total bytes across every file matching a glob.
    return sum(p.stat().st_size for p in SCRATCH.glob(pattern))


json_bytes = size_of("rows.json*")
avro_bytes = size_of("rows.avro*")
parquet_bytes = size_of("rows.parquet*")

print()
print(f"{'format':<10} {'bytes':>10}  {'vs JSON':>9}  {'bytes/row':>11}")
print("-" * 46)
for label, value in (("JSON", json_bytes), ("Avro", avro_bytes), ("Parquet", parquet_bytes)):
    ratio = value / json_bytes if json_bytes else 0
    per_row = value / len(CSV_ROWS) if CSV_ROWS else 0
    print(f"{label:<10} {value:>10}  {ratio:>8.2f}x  {per_row:>10.1f}")

print()
print("The shape of the win:")
print("  * Avro removes the repeated field names — the schema is written")
print("    once in the header, and each record is just the three values.")
print("  * Parquet goes further: it stores columns, not rows, so the")
print("    repeated `region` values compress into almost nothing and a")
print("    query that needs one column reads only that column.")
print()
print("Two caveats, both honest:")
print("  1. JSON here is one object per line with sorted keys. Pretty-")
print("     printed JSON is several times larger again.")
print("  2. Parquet carries fixed per-file metadata (a schema footer and")
print("     row-group indexes). On a handful of rows that overhead makes")
print("     it the biggest file on disk. The crossover is somewhere in")
print("     the low thousands of rows.")

print()
print("--- and both read back, with a glob pattern ---")
print("Avro read-back:")
with beam.Pipeline(options=LOCAL_OPTIONS) as p:
    _ = p | "ReadAvro" >> avroio.ReadFromAvro(str(SCRATCH / "rows.avro*"))
print("   ok — the glob pattern matched the sharded filename.")

print("Parquet read-back:")
with beam.Pipeline(options=PRISM_OPTIONS) as p:
    _ = p | "ReadParquet" >> parquetio.ReadFromParquet(str(SCRATCH / "rows.parquet*"))
print("   ok — same glob pattern requirement.")
""")

md(r"""
## 7. Multi-source with `Flatten`, and multi-sink fan-out

`beam.Flatten` merges a **tuple** of PCollections into one. It is the
simplest transform in Beam and one of the most useful:

```python
merged = (csv_pcoll, json_pcoll) | "Flatten" >> beam.Flatten()
```

The important detail is that `Flatten` takes a **tuple**, not a list, and
that it requires every input to have **the same element type**. A CSV
row and a JSON object are different types, so the first thing to do is
project both onto a common shape. Here, both become a
`(source, key, value)` tuple.

On the sink side, the mirror-image pattern is **fan-out**: one
PCollection feeding several sinks. Beam handles this by **fusion** —
steps that can be merged into one `DoFn` are combined, which is good for
performance but means a side effect in one branch can happen in an
unexpected order. The practical rule: **do not rely on side-effect
ordering across fan-out branches.**

### The fusion caveat, concretely

Beam's optimizer merges a `Map`/`ParDo` into its consumer when it can.
That is why `Map` → `Map` → `WriteToText` is fast: the three steps become
one. It is also why a `DoFn` with a side effect can surprise you — the
side effect may happen once per fused bundle rather than once per
element-group, and its position relative to another branch's side effect
is not guaranteed.

**The rule:** a `DoFn` that has a side effect (writing a file, calling an
API, incrementing a counter) should not be fused with anything else. Use
`beam.Reshuffle()` between the side-effecting step and the next
grouping stage to break fusion deliberately.
""")

code(r"""
# --- Two sources, one PCollection -----------------------------------------
#
# Both sources are projected onto the SAME shape before the Flatten:
# a Beam KV pair whose KEY is itself a tuple, `(source, region)`, and
# whose VALUE is the number 1.
#
# The key can be any hashable, including a tuple — Beam does not care
# how many fields your key has. (A detail worth knowing: the built-in
# `Count.PerKey()` uses only the FIRST field of its input tuple as the
# key, so a composite key needs `CombinePerKey(sum)` instead.)
with beam.Pipeline(options=LOCAL_OPTIONS) as p:
    csv_rows = (
        p
        | "ReadOrdersCsv" >> beam.io.ReadFromText(ORDERS_CSV)
        | "SkipCsvHeader" >> beam.Filter(lambda line: not line.startswith("order_id"))
        | "ParseCsvRow" >> beam.Map(parse_order_line)
        | "ToCommonShape" >> beam.Map(lambda row: ((("csv", row["region"])), 1))
    )

    json_rows = (
        p
        | "ReadEventsJson" >> beam.io.ReadFromText(EVENTS_NDJSON)
        | "ParseJsonRow" >> beam.Map(json.loads)
        | "ToCommonShapeJson" >> beam.Map(lambda event: (("json", event["region"]), 1))
    )

    merged = (csv_rows, json_rows) | "FlattenSources" >> beam.Flatten()

    (
        merged
        | "CountBySourceRegion" >> beam.CombinePerKey(sum)
        | "FormatCounts" >> beam.Map(lambda kv: f"{kv[0][0]},{kv[0][1]},{kv[1]}")
        | "WriteMergedCounts" >> beam.io.WriteToText(
            str(SCRATCH / "merged_counts"), num_shards=1, shard_name_template="")
    )

print("One PCollection, two sources:")
print("  ", (SCRATCH / "merged_counts").read_text(encoding="utf-8").strip().replace("\n", "  |  "))
print()
print("The `Flatten` added no shuffle — it is a cheap union of two")
print("PCollections into one. The shuffle happens later, at the")
print("`CombinePerKey`.")

print()
print("--- One source, several sinks ---------------------------------------------")
with beam.Pipeline(options=LOCAL_OPTIONS) as p:
    source = (
        p
        | "CreateFanout" >> beam.Create(["EMEA", "AMER", "APAC", "EMEA"])
    )

    # Sink A: every element.
    (
        source
        | "WriteAll" >> beam.io.WriteToText(
            str(SCRATCH / "fanout_all"), num_shards=1, shard_name_template="")
    )

    # Sink B: only the elements from EMEA.
    (
        source
        | "KeepOnlyEmea" >> beam.Filter(lambda region: region == "EMEA")
        | "WriteEmea" >> beam.io.WriteToText(
            str(SCRATCH / "fanout_emea"), num_shards=1, shard_name_template="")
    )

    # Sink C: a different projection of the same source.
    (
        source
        | "Uppercase" >> beam.Map(lambda region: region.lower())
        | "WriteLower" >> beam.io.WriteToText(
            str(SCRATCH / "fanout_lower"), num_shards=1, shard_name_template="")
    )

for name in ("fanout_all", "fanout_emea", "fanout_lower"):
    content = (SCRATCH / name).read_text(encoding="utf-8").strip().splitlines()
    print(f"  {name:14s}: {content}")

print()
print("Three sinks, one source. The runner may fuse the shared prefix")
print("into a single DoFn — that is the fusion caveat. It is a")
print("performance win, and the reason you must not rely on the")
print("ORDER of side effects between the branches.")
""")

md(r"""
## 🔑 Takeaways

- **`WriteToText` takes a prefix, not a filename.** The shard count is
  chosen at run time; the default template in Beam 2.77 is
  `prefix-00000-of-00001`. Never hard-code a shard name — glob for it.
- **`shard_name_template=""` with `num_shards=1`** gives you a file with
  exactly the name you asked for. A teaching choice, not a production one.
- **A coder is how Beam serialises your elements.** The type-hint
  registry maps `Tuple[int, str]` to `TupleCoder`, a container coder that
  encodes each field with its own coder — no pickle.
- **`with_output_types`** attaches the hint to a transform, which selects
  the coder *and* supplies the schema the Avro and Parquet sinks need.
- **Use `ReadFromText` + `csv.DictReader` / `json.loads`** for production
  code. `ReadFromCsv` and `ReadFromJson` fail on
  `BundleBasedDirectRunner` in Beam 2.77 and work only on Prism — and
  the reliable path gives you the raw line for a DLQ.
- **JSON Lines** is the natural streaming format: one self-contained
  object per line, parseable without buffering.
- **Avro needs `fastavro`, Parquet needs `pyarrow`** — both required,
  not extras. `WriteToParquet` also only works on the Prism runner, and
  Parquet needs a schema it can derive, so use a `typing.NamedTuple`.
- **`Flatten` merges a tuple of PCollections** with the same element
  type; project heterogeneous sources onto a common shape first.
- **Fan-out to several sinks works, but the runner may fuse the shared
  prefix.** Do not rely on side-effect ordering across branches.
""")

nb = {
    "cells": CELLS,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "version": "3.11"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

out = Path("notebooks/03-io-and-file-formats.ipynb")
out.write_text(json.dumps(nb, indent=1) + "\n", encoding="utf-8")
print(f"wrote {out} with {len(CELLS)} cells")
print("  markdown:", sum(1 for c in CELLS if c["cell_type"] == "markdown"))
print("  code    :", sum(1 for c in CELLS if c["cell_type"] == "code"))
