# 3.1 — I/O Catalogue & Coders

> **Section 3 · I/O & Multi-Source Pipelines · Lecture 3.1 · 6:30**

## 🎯 What you will learn

- The full Beam I/O catalogue, organised by category, with the real API names
- Coders vs encoders: what the difference is and why the vocabulary confuses people
- The coder hierarchy — `BytesCoder`, `StrUtf8Coder`, `FastPrimitivesCoder`, `TupleCoder`, `AvroGenericCoder`, `RowCoder`, `NullableCoder`, `PickleCoder` and the rest
- How type-hint-driven coder inference works, and why it beats guessing at runtime
- How to attach an explicit coder to a transform, and when you must
- The `PickleCoder` warning: why the default fallback is a production liability
- `NullableCoder` for optional fields, and `RowCoder` for BigQuery `Row` objects
- A decision table for "which coder do I use"

---

## 🧠 Concept

### The I/O catalogue

Apache Beam's I/O is not one API. It is a *catalogue* — a set of transforms
that vary in portability, maturity, and whether they need a runner-specific
backend. Treating it as a flat list is the first mistake; treating it as a
catalogue organised by *category* is how you actually choose.

#### File formats

These are the portable formats. They work on every runner, because they are
defined by the file itself rather than by a service.

| Transform | Module | Portable | Notes |
|---|---|---|---|
| `ReadFromText` / `WriteToText` | `apache_beam.io.textio` | yes | lines of text; the universal fallback |
| `ReadFromCsv` / `WriteToCsv` | `apache_beam.io.textio` | yes | **pandas-backed**; needs `apache_beam[dataframe]` |
| `ReadFromJson` / `WriteToJson` | `apache_beam.io.textio` | yes | **pandas-backed**; needs `apache_beam[dataframe]` |
| `ReadFromAvro` / `WriteToAvro` | `apache_beam.io.avroio` | yes | schema-enforced, columnar-ish, `fastavro` |
| `ReadFromParquet` / `WriteToParquet` | `apache_beam.io.parquetio` | yes | columnar, typed, `pyarrow` |
| `ReadFromTFRecord` / `WriteToTFRecord` | `apache_beam.io.tfrecordio` | yes | TensorFlow's record format |

> **The pandas surprise.** In Beam 2.77, `ReadFromCsv`, `WriteToCsv`,
> `ReadFromJson` and `WriteToJson` are *thin wrappers around pandas*, not
> native Beam transforms. They are implemented via
> `apache_beam.dataframe.io.ReadViaPandas` and
> `WriteViaPandas`. If pandas is not installed, these names still exist
> on `beam.io` — but calling them raises
> `ImportError: Please install apache_beam[dataframe]`. This matters
> because "the transform exists" and "the transform is available" are
> different questions. Chapter 3.3 covers the practical consequences.

#### Messaging

| Transform | Module | Portable | Notes |
|---|---|---|---|
| `ReadFromPubSub` / `WriteToPubSub` | `apache_beam.io.gcp.pubsub` | no | GCP-only; the Dataflow streaming source of truth |
| `ReadFromKafka` / `WriteToKafka` | `apache_beam.io.kafka` | partly | Java-based expansion service; not supported on Dataflow |
| `ReadFromKinesis` / `WriteToKinesis` | `apache_beam.io.kinesisio` | no | AWS only |
| `ReadFromJms` / `WriteToJms` | `apache_beam.io.jmsio` | no | via expansion service |

Pub/Sub is a first-class GCP citizen: `beam.io.ReadFromPubSub` is
re-exported from `apache_beam.io`, and the `streaming_pipeline.py` in this
course uses it directly. Kafka is *not* supported on the Dataflow Runner —
the Kafka I/O transforms rely on a Java `ExternalTransform` and Dataflow
runs Python SDK workers, so `ReadFromKafka` fails there with an expansion
service error. Use Pub/Sub on Dataflow, and Kafka only on Spark/Flink with
the appropriate Java runtime.

#### Databases and NoSQL

| Transform | Module | Portable | Notes |
|---|---|---|---|
| `ReadFromBigQuery` / `WriteToBigQuery` | `apache_beam.io.gcp.bigquery` | no | GCP-only; full schema handling |
| `ReadFromJdbc` / `WriteToJdbc` | `apache_beam.io.jdbc` | partly | needs a JVM and a driver jar; expansion service |
| `ReadFromMongoDB` / `WriteToMongoDB` | `apache_beam.io.mongodbio` | no | needs `pymongo` |
| `ReadFromSpanner` | `apache_beam.io.gcp.spannerio` | no | GCP-only |
| `WriteToSpanner` | `apache_beam.io.gcp.spannerio` | no | GCP-only |

JDBC and Kafka are both *expansion service* transforms: they shell out to
a JVM. That makes them work identically on any runner that can start a
JVM (Spark, Flink, Dataflow with a Java runtime), but it also means they
are slower, harder to reason about, and — on Dataflow — often awkward
because the driver jar has to be staged to a bucket.

#### File systems

Beam does not have a separate "GCS transform". It has **one** file
transform per *format*, and the *path* selects the file system.

| Scheme | Backend | Notes |
|---|---|---|
| `gs://bucket/path` | Cloud Storage | needs `gcsfs`; the `filesystem` extra provides it |
| `hdfs://namenode/path` | HDFS | needs `hadoopfilesystem` |
| `s3://bucket/path` | S3 | via the `s3fs` extra, or `apache_beam.io.aws` |
| `./local/path` | local disk | always available, used by the DirectRunner |
| `file:///abs/path` | local disk | absolute local paths |

This is a design decision worth internalising: **the format transform and
the file system are orthogonal**. `WriteToParquet("gs://bucket/orders")`
writes Parquet to GCS. `WriteToText("s3://bucket/orders")` writes text
lines to S3. You never need a "GCS transform" — you need a path.

The `filesystem` extra is the umbrella:

```bash
pip install apache-beam[filesystem]
```

which pulls in `gcsfs`, `s3fs`, and the Hadoop file system support. In
Beam 2.77 `gcsfs` is *not* installed by default; a pipeline that reads
`gs://` on the DirectRunner without it fails with a `BeamIOError` about
an unregistered file system, not with an `ImportError`. The error message
is unhelpful, which is why it is worth knowing the cause in advance.

---

## 🧠 Coders

### Encoders vs coders

The Beam vocabulary is confusing here, and the confusion is not your fault.
Two different words get used for closely related things.

**Encoder** is the *Java* term. In the Java SDK, `Coder` subclasses
implement `encode(T)` and `decode(InputStream)`. The Java SDK also has
`SchemaCoder` and `Coder` as separate hierarchies, and "encoder" shows up
in the `DoFn` API for stateful processing.

**Coder** is the term the Python SDK settled on. A `Coder` is an object
that knows how to turn a Python value into a byte string and back. The
canonical definition in `apache_beam/coders/coders.py`:

```python
class Coder:
    """A Coder encodes and decodes values to and from a stream of bytes."""

    def encode(self, value):
        """Encodes the given value as a byte stream."""
        raise NotImplementedError

    def decode(self, encoded):
        """Decodes the given bytes into a value."""
        raise NotImplementedError
```

The two words are used somewhat interchangeably in the wild — "the
encoder" often means "the coder" — and the Python SDK's own docstrings
occasionally say "encoder" when they mean "coder". When you see
"coder" in this course, read "coder"; when you see "encoder" in Beam
documentation, read "coder" unless the context is clearly Java stateful
processing.

**Why coders exist at all.** A PCollection is a *distributed* collection.
When a `Map` runs on worker 7 and a `CombinePerKey` runs on worker 3, the
value must cross the wire. The coder is the contract for that
serialisation. It also determines:

- **What can be fused.** A step whose output is not written to durable
  storage may be fused with its neighbours. Coder properties (notably
  determinism) affect whether the runner can do this.
- **What can be grouped.** `GroupByKey` requires a coder for the *key*
  that is byte-comparable, because Beam sorts and merges keys.
- **How much you pay.** A `FastPrimitivesCoder` encodes a `float64` in
  8 bytes. A `PickleCoder` encodes it in a pickle stream with a
  protocol header and type tag. Over a petabyte, that difference is real
  money.

### The coder hierarchy

Beam's coders form a shallow tree. The leaves are concrete; the interior
nodes are *composite* coders that delegate to children.

| Coder | Import path | Encodes | Typical use |
|---|---|---|---|
| `BytesCoder` | `apache_beam.coders` | `bytes` | raw byte payloads, Pub/Sub messages |
| `StrUtf8Coder` | `apache_beam.coders` | `str` | text lines; the default for `ReadFromText` |
| `BooleanCoder` | `apache_beam.coders` | `bool` | one bit, as a byte |
| `VarIntCoder` | `apache_beam.coders` | `int` | variable-length integer |
| `FloatCoder` | `apache_beam.coders` | `float` | IEEE-754 double |
| `BytesCoder` (raw) | `apache_beam.coders` | `bytes` | identical to the above |
| `TupleCoder` | `apache_beam.coders` | `tuple` | composite; needs a child coder per field |
| `MapCoder` | `apache_beam.coders` | `dict` | composite; key and value coders; **never deterministic** |
| `ListCoder` | `apache_beam.coders` | `list` | composite |
| `IterableCoder` | `apache_beam.coders` | `Iterable` | composite |
| `NullableCoder` | `apache_beam.coders` | `Optional[T]` | composite; wraps a value coder |
| `SingletonCoder` | `apache_beam.coders` | one constant | composite |
| `WindowedValueCoder` | `apache_beam.coders` | `(value, timestamp, window)` | composite; used internally |
| `FastPrimitivesCoder` | `apache_beam.coders` | many types | the fast path; falls back to pickle |
| `DeterministicFastPrimitivesCoder` | `apache_beam.coders` | many types | pickle-free deterministic encoding |
| `PickleCoder` | `apache_beam.coders` | anything | the fallback; last resort |
| `DillCoder` | `apache_beam.coders` | anything | pickle for lambdas; needs `dill` |
| `ProtoCoder` | `apache_beam.coders` | protobuf messages | typed, deterministic |
| `AvroGenericCoder` | `apache_beam.coders` | Avro records | Avro-native rows |
| `RowCoder` | `apache_beam.coders.row_coder` | `apache_beam.pvalue.Row` | BigQuery-style row objects |

Two of these deserve special attention because they are the ones you will
actually reach for.

#### `FastPrimitivesCoder`

This is the coder that makes Beam fast. It has hand-written, efficient
encoders for the common Python types, and it falls back to a
`PickleCoder` for everything else.

Its inference behaviour is what you will see in practice. Asking the
coder registry for a coder for a given type gives:

| Type | Coder chosen | Why |
|---|---|---|
| `int` | `VarIntCoder` | variable-length, small ints cost 1 byte |
| `float` | `FloatCoder` | 8-byte IEEE-754 |
| `str` | `StrUtf8Coder` | UTF-8, no length prefix needed for line-oriented data |
| `bytes` | `BytesCoder` | length-prefixed raw bytes |
| `bool` | `BooleanCoder` | one byte |
| `dict` | `FastPrimitivesCoder` | pickles the whole dict, with the fallback |
| `list` | `FastPrimitivesCoder` | same |
| `tuple` | `FastPrimitivesCoder` | same, unless you give an explicit hint |

That last row is the interesting one. A bare `tuple` type hint does not
tell Beam the field types, so it pickles. A *parameterised* hint like
`Tuple[int, str]` does, and you get a `TupleCoder` with a `VarIntCoder`
and a `StrUtf8Coder` inside — no pickle, byte-comparable keys, and
`GroupByKey` can merge them efficiently.

#### `PickleCoder`

`PickleCoder` is the fallback of last resort. Beam's own source says so:

```python
class PickleCoder(_PickleCoderBase):
    """Coder using Python's pickle functionality."""
```

and the registry falls back to it when it has no better answer. That
fallback is fine for a tutorial and a liability in production. Three
reasons:

1. **It is slow.** Pickle is a general-purpose serialiser. It writes
   type tags, memo tables and protocol headers. For a `float64`, a
   `VarIntCoder`-equivalent writes 8 bytes; pickle writes a stream with
   framing. Across a 1 TB stage, that difference is minutes of CPU and
   real money.

2. **It is not deterministic.** Beam's source notes this explicitly:
   *"Note that the default coder, the PickleCoder, is not deterministic"*.
   A deterministic coder produces the same bytes for the same value,
   every time, on every worker. Non-deterministic coders prevent certain
   optimisations and, in streaming, prevent exactly-once semantics.
   `PickleCoder.as_deterministic_coder()` returns a
   `FastPrimitivesCoder` instead — Beam's own answer to the problem.

3. **It breaks the fusion boundary.** A step whose output coder is
   non-deterministic cannot be reordered or fused as freely, because the
   runner cannot prove the reordering is safe. This is why a pipeline
   full of pickled dicts tends to be full of intermediate steps, and
   full of GCS round-trips that you did not ask for.

The course's own `transforms.py` is a good illustration. It parses
orders into plain `dict` objects, which means the coder for that stage
is `FastPrimitivesCoder` with a `PickleCoder` fallback — fine for a
course, worth revisiting if you push it to production scale.

#### `NullableCoder`

`NullableCoder` wraps another coder to represent "this value, or nothing".
It is what you want for optional fields, and it is what the registry
chooses automatically for an `Optional[T]` type hint:

```python
import apache_beam.typehints as th
from apache_beam.coders.typecoders import registry

# What the registry picks for Optional[str]
coder = registry.get_coder(th.Optional[str])
print(type(coder).__name__)   # NullableCoder
```

The important detail is that `NullableCoder` is a *composite* coder: it
holds a `value_coder` and encodes a presence flag alongside the value.
That is why you cannot construct it without one:

```python
from apache_beam.coders import coders

# This raises: TypeError: NullableCoder.__init__() missing 1 required
# positional argument: 'value_coder'
bad = coders.NullableCoder()

# This is correct
good = coders.NullableCoder(coders.StrUtf8Coder())
```

In practice, you rarely construct one by hand. If you annotate a
`DoFn`'s output as `Optional[str]`, Beam selects `NullableCoder` for
you.

#### `RowCoder` and `Row` objects

`apache_beam.pvalue.Row` is a row abstraction: a schema plus values,
designed to look like a named tuple but to carry a schema. `RowCoder`
(located at `apache_beam.coders.row_coder.RowCoder`, not in
`apache_beam.coders`) encodes them.

You get `Row` objects most often from the Parquet and Avro readers when
you ask for them:

```python
from apache_beam.io import parquetio

rows = p | "ReadParquet" >> parquetio.ReadFromParquet(
    "gs://YOUR_BUCKET/orders*",
    as_rows=True,
)
```

Each element is then a row object whose attributes are the schema fields:

```python
def describe(row):
    return f"{row.region} {row.revenue}"

summary = rows | "Describe" >> beam.Map(describe)
```

`Row` objects are also what `WriteToBigQuery` consumes when you pass a
`schema`. You can build them explicitly:

```python
from apache_beam.pvalue import Row

row = Row(region="EMEA", order_count=12, revenue_eur=340.25)
```

`RowCoder` is *not* in `apache_beam.coders`' top-level namespace, which
is a common source of `ImportError`. The import that works:

```python
from apache_beam.coders.row_coder import RowCoder
```

---

## 🧠 Type hints and coder inference

### How inference actually works

Beam does not guess at runtime by inspecting the first element it sees.
It uses **type hints** — the `element_type` annotation on a
`PCollection`.

When you build a pipeline, each transform declares the type of its
output. The coder for that output is then derived from the type hint by
the coder registry, in `apache_beam/coders/typecoders.py`:

```python
from apache_beam.coders import typecoders

registry = typecoders.registry

print(type(registry.get_coder(int)).__name__)          # VarIntCoder
print(type(registry.get_coder(str)).__name__)          # StrUtf8Coder
print(type(registry.get_coder(bool)).__name__)         # BooleanCoder
print(type(registry.get_coder(th.Tuple[int, str])).__name__)   # TupleCoder
print(type(registry.get_coder(th.Dict[str, int])).__name__)    # MapCoder
print(type(registry.get_coder(th.Optional[str])).__name__)    # NullableCoder
```

The resolution order for a type hint is:

1. Is there a coder registered for this exact type? Use it.
2. Is it a composite constraint — `Tuple`, `Dict`, `List`, `Iterable`,
   `Optional`? Build a composite coder from the component coders.
3. Is it `Any`, `object`, or a `TypeVariable`? Use the **fallback coder**
   (which is `FastPrimitivesCoder` wrapping `PickleCoder`).
4. Otherwise: fall back.

The critical consequence: **an unannotated element type gives you the
fallback coder**, and the fallback coder pickles. Type hints are not
decoration — they are how Beam decides how to move your data.

### Why hints beat runtime guessing

Consider the naive approach: look at the first element, look at its type,
pick a coder. It sounds fine. It is wrong in three specific ways.

**First, a distributed pipeline has no "first element."** The runner may
process bundles in any order, on any worker, and may schedule a
`CombinePerKey`'s merge before every worker has seen the first input.
A coder that depends on data arrival order is not a coder, it is a
race condition.

**Second, elements are heterogeneous in practice.** A stream where 99.99%
of elements are `dict` and 0.01% are `None` will infer `dict` from the
first element and then fail — or silently pickle — on the `None`. With
a type hint of `Optional[dict]`, the coder handles both, every time.

**Third, inference is per-element and unbounded in cost.** A
"look at the first element" coder must be shipped to every worker
anyway, so you pay the pickling cost for the schema inference and then
again for the data.

Type-hint-driven inference is *static*: the decision is made when the
graph is built, is identical on every worker, and is inspectable before
the job runs. This is the same design principle as the rest of Beam —
describe the computation, let the runner execute it.

### Reading the inferred element type

Every `PCollection` exposes `element_type`:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    text = p | "Read" >> beam.io.ReadFromText("./sample_data/orders.csv")
    print(text.element_type)   # <class 'str'>
```

This is the fastest way to check that your hints are doing what you
think. If `element_type` is `typing.Any`, the coder is the fallback and
your data is being pickled.

### Attaching explicit coders

There are three levels at which you can be explicit.

**Level 1 — the IO transform's `coder=` parameter.** The Beam *source
and sink* transforms accept a coder:

```python
import apache_beam as beam
from apache_beam.coders import coders

with beam.Pipeline() as p:
    raw = p | "ReadBytes" >> beam.io.ReadFromText(
        "./sample_data/orders.csv",
        coder=coders.BytesCoder(),
    )
    print(raw.element_type)   # <class 'bytes'>
```

The default for `ReadFromText` is `StrUtf8Coder`; for `WriteToText` it
is `ToBytesCoder`, which encodes `str` as UTF-8 and passes `bytes`
through unchanged. Overriding to `BytesCoder` on the read side gives
you raw bytes, which is what you want when the file is not valid UTF-8
or when you are parsing binary formats.

> **`coder=` does not exist on `Map` or `ParDo`.** This is the single
> most common mistake in this area, and the error message points at
> your function rather than at the transform:
>
> ```text
> TypeError: int() got an unexpected keyword argument 'coder'
> ```
>
> `beam.Map` and `beam.FlatMap` are *factories* that forward `**kwargs`
> to the callable you gave them. `beam.ParDo` forwards them to your
> `DoFn.process`. Neither accepts a `coder` argument. If you write
> `beam.Map(int, coder=...)`, the `coder=` keyword lands in `int()`.
>
> The fix is to use a type hint (level 3 below). That is the mechanism
> Beam gives you for controlling the coder of a composite transform's
> output, and it does more work than a coder override would.

**Level 2 — a coder on a `DoFn`'s own output.** A `DoFn` can declare
its coder directly on the method, by pairing a type hint with the
decorator:

```python
import apache_beam as beam
import apache_beam.typehints as th


class ParseAmount(beam.DoFn):
    @beam.typehints.with_output_types(th.Optional[float])
    def process(self, line: str):
        try:
            return float(line.strip())
        except ValueError:
            return None
```

**Level 3 — the type hint on the transform.** This is the idiomatic
modern way, and it covers more than a coder does, because a hint also
constrains the transform's input type, which the runner uses for type
checking.

```python
import apache_beam as beam
import apache_beam.typehints as th

with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create([1, 2, 3])
        | "Square" >> beam.Map(lambda x: x * x).with_output_types(int)
    )
```

`with_output_types` is a method on the *transform instance*, so it
chains after `beam.Map(...)`, not inside it. The `PTransform` base class
in Beam 2.77 provides:

- `with_input_types(type_hint, **tagged_type_hints)`
- `with_output_types(type_hint, **tagged_type_hints)`

For a `DoFn`, you can also declare the hint on the method itself:

```python
import apache_beam as beam
import apache_beam.typehints as th


class ParseAmount(beam.DoFn):
    @beam.typehints.with_output_types(th.Optional[float])
    def process(self, line: str):
        try:
            return float(line.strip())
        except ValueError:
            return None
```

`beam.typehints.with_output_types` and `beam.typehints.with_input_types`
are exported at the top level of `apache_beam.typehints`, and
`beam.typehints` is accessible as `beam.typehints` after
`import apache_beam as beam`.

> **A note on `with_output_coder`.** You may see `with_output_coder`
> referenced in older Beam examples and in the Java SDK's
> `withOutputCoder`. The Python SDK in 2.77 does **not** expose a
> `with_output_coder` method on `PTransform` — there is no such method in
> `apache_beam.transforms.core.PTransform`. The Python equivalents are
> the `coder=` keyword argument (on I/O transforms only) and
> `with_output_types` (everywhere). If you copy Java-flavoured snippets
> into a Python pipeline, translate them.

### Registering a coder for a custom type

When you have your own class, you can register a coder for it so that
Beam stops falling back to pickle:

```python
from apache_beam.coders import coders
from apache_beam.coders.typecoders import registry


class Order:
    def __init__(self, order_id, region, amount):
        self.order_id = order_id
        self.region = region
        self.amount = amount


class OrderCoder(coders.Coder):
    def encode(self, order):
        return f"{order.order_id}|{order.region}|{order.amount}".encode("utf-8")

    def decode(self, encoded):
        order_id, region, amount = encoded.decode("utf-8").split("|")
        return Order(order_id, region, float(amount))


registry.register_coder(Order, OrderCoder)
```

Note the last line: **`register_coder` takes the coder *class*, not an
instance.** Passing `OrderCoder()` raises:

```text
TypeError: Coder registration requires a coder class object.
Received OrderCoder instead.
```

`registry` lives at `apache_beam.coders.typecoders.registry` and exposes
`register_coder`, `get_coder`, `register_fallback_coder` and
`register_row`.

The cleanest way to write a custom coder is to subclass
`coders.Coder` and implement `encode` and `decode`. If you want a
fast, deterministic encoding of a structured type, subclass
`coders.FastCoder` and implement `_create_impl` returning a coder impl
— but that requires implementing the low-level `encode_to_stream` /
`decode_from_stream` protocol, and for most cases the simple
`Coder` subclass above is the right trade-off.

### The decision table

| Situation | Coder to use | How to set it |
|---|---|---|
| Text lines, one record per line | `StrUtf8Coder` | the default for `ReadFromText` |
| Raw binary payloads | `BytesCoder` | `coder=coders.BytesCoder()` |
| Pub/Sub message payloads | `BytesCoder` | the default for `ReadFromPubSub` |
| A single `int` / `float` / `bool` field | `VarIntCoder` / `FloatCoder` / `BooleanCoder` | inferred from the type hint |
| A tuple of known field types | `TupleCoder` | hint `th.Tuple[int, str]` |
| A dict with known key/value types | `MapCoder` | hint `th.Dict[str, int]` |
| An optional field | `NullableCoder` | hint `th.Optional[str]` |
| BigQuery `Row` objects | `RowCoder` | `from apache_beam.coders.row_coder import RowCoder` |
| Avro records | `AvroGenericCoder` | `from apache_beam.coders import AvroGenericCoder` |
| A Parquet/Arrow row | `RowCoder` (via `as_rows=True`) | `parquetio.ReadFromParquet(..., as_rows=True)` |
| A protobuf message | `ProtoCoder` | `coders.ProtoCoder(MyMessage)` |
| Your own class | a custom `Coder` | `registry.register_coder(MyClass, MyCoder)` |
| A `str` field that should be `bytes` | `ToBytesCoder` | the default for `WriteToText` |
| **Anything you cannot justify** | **not `PickleCoder`** | add a hint; check `element_type` |

The last row is the one worth memorising. If you look at a PCollection
and its `element_type` is `Any`, you have a pickling problem, and the
fix is almost always a type hint rather than a coder override.

---

## 🛠️ Hands-On: Inspecting and Controlling Coders

### Setup

```bash
cd data-engineering/data-Course/google/Dataflow
source .venv/bin/activate
python resources/sample_data.py --output-dir ./sample_data
```

### Step 1 — see what the registry picks

Create `work/coders_lab.py`:

```python
"""Inspect the coder Beam infers for various type hints."""

from apache_beam.coders import coders
from apache_beam.coders.typecoders import registry
import apache_beam.typehints as th

HINTS = [
    ("int", int),
    ("float", float),
    ("str", str),
    ("bytes", bytes),
    ("bool", bool),
    ("bare dict", dict),
    ("Dict[str, int]", th.Dict[str, int]),
    ("Tuple[int, str]", th.Tuple[int, str]),
    ("Optional[str]", th.Optional[str]),
    ("List[int]", th.List[int]),
]

for label, hint in HINTS:
    coder = registry.get_coder(hint)
    deterministic = coder.is_deterministic()
    print(f"{label:20s} -> {type(coder).__name__:32s} deterministic={deterministic}")
```

Run it:

```bash
python work/coders_lab.py
```

Expected output:

```text
int                  -> VarIntCoder                   deterministic=True
float                -> FloatCoder                    deterministic=True
str                  -> StrUtf8Coder                  deterministic=True
bytes                -> BytesCoder                    deterministic=True
bool                 -> BooleanCoder                  deterministic=True
bare dict            -> FastPrimitivesCoder           deterministic=False
Dict[str, int]       -> MapCoder                      deterministic=False
Tuple[int, str]      -> TupleCoder                    deterministic=True
Optional[str]        -> NullableCoder                 deterministic=True
List[int]            -> ListCoder                     deterministic=True
```

Three things to notice.

`bare dict` is **not deterministic** — that is the pickle fallback, and
it is the state the course's `transforms.py` leaves you in.

`Dict[str, int]` is *also* not deterministic, and this is the subtle
one. Beam builds a real `MapCoder` with a `StrUtf8Coder` key and a
`VarIntCoder` value, but `MapCoder.is_deterministic()` returns `False`
unconditionally, because **Python dict ordering is not guaranteed**. Two
workers that receive the same key-value pairs in different orders would
encode them differently. Beam's source is explicit:

```python
class MapCoder(Coder):
    def is_deterministic(self):
        # Map ordering is non-deterministic
        return False
```

This is exactly why you should not key a `GroupByKey` by a dict. The
fix is not a different hint — it is a different *key type*. Use a
`Tuple[str, str]` or a plain string key, both of which are deterministic.

`Tuple[int, str]` *is* deterministic, because a tuple has a defined
order and each field has a real primitive coder.

### Step 2 — check the element type of a real pipeline

Create `work/element_type_lab.py`:

```python
"""Show the element_type of each stage in the course's batch pipeline."""

import apache_beam as beam
from apache_beam.coders import coders
import apache_beam.typehints as th

with beam.Pipeline() as p:
    text = p | "Read" >> beam.io.ReadFromText("./sample_data/orders.csv")
    print("ReadFromText   ->", text.element_type)

    tagged = (
        p
        | "Create" >> beam.Create(["EMEA", "AMER"])
        | "Tag" >> beam.Map(lambda r: ("orders", r)).with_output_types(
            th.Tuple[str, str]
        )
    )
    print("Tagged tuple   ->", tagged.element_type)

    optional = (
        p
        | "Create2" >> beam.Create(["1.5"])
        | "ToFloat" >> beam.Map(float).with_output_types(th.Optional[float])
    )
    print("Optional float ->", optional.element_type)

    as_bytes = p | "ReadBytes" >> beam.io.ReadFromText(
        "./sample_data/orders.csv",
        coder=coders.BytesCoder(),
    )
    print("Read as bytes  ->", as_bytes.element_type)
```

Run it:

```bash
python work/element_type_lab.py
```

Expected output:

```text
ReadFromText   -> <class 'str'>
Tagged tuple   -> Tuple[<class 'str'>, <class 'str'>]
Optional float -> Union[<class 'NoneType'>, <class 'float'>]
Read as bytes  -> <class 'bytes'>
```

The `Optional[float]` case is worth pausing on. `with_output_types`
with an `Optional` hint is what makes the coder a `NullableCoder` — a
coder that can represent "no value" without ambiguity. Without the hint,
Beam cannot tell whether `None` is a legitimate value or a type error,
and you get pickle.

### Step 3 — prove that a hint changes the coder

Where does `Any` actually come from? Not from `beam.Map` — Beam
inspects the lambda's return type and infers a real type. It comes from
a `DoFn` whose `process` method has no return annotation. That is
exactly the shape of the course's `ParseOrderFn`.

Create `work/hint_effect.py`:

```python
"""Show that a type hint changes the inferred coder."""

import sys

sys.path.insert(0, "project")

import apache_beam as beam
import apache_beam.typehints as th

from transforms import ParseOrderFn

with beam.Pipeline() as p:
    # The course's own DoFn: no return annotation on process(), so Beam
    # has no type to work with and falls back to Any.
    lines = p | "Read" >> beam.io.ReadFromText("./sample_data/orders.csv")
    unannotated = lines | "ParseBare" >> beam.ParDo(ParseOrderFn())
    print("DoFn, no annotation ->", unannotated.element_type)

    # The same DoFn, annotated on the transform.
    annotated = lines | "ParseAnnotated" >> beam.ParDo(
        ParseOrderFn()
    ).with_output_types(th.Dict[str, th.Any])
    print("DoFn, annotated      ->", annotated.element_type)
```

Run it:

```bash
python work/hint_effect.py
```

Expected output:

```text
DoFn, no annotation -> Any
DoFn, annotated      -> Dict[<class 'str'>, Any]
```

`Any` on the first line is the tell. `Any` means "no hint", which means
the fallback coder, which means pickle. Note that the *inner* `Any` in
the annotated case is deliberate: the order dict has nine fields of
mixed types, and `th.Dict[str, th.Any]` says "string keys, arbitrary
values" — which is honest, and still far better than an unannotated
`DoFn`.

> **A `DoFn` may return a dict, but it may not *yield* one.**
> `beam.Map` accepts a function that returns a dict. `beam.ParDo` does
> not: Beam's own check raises
> `TypeError: Returning a dict from a ParDo or FlatMap is not allowed.
> Please use list({'k': 'a,b'}) if you really want this behavior.`
> The course's `ParseOrderFn` uses `yield row`, which is a different
> thing — it yields the dict *as a single element*, and that is
> allowed. The error only fires when a `DoFn.process` *returns* a dict
> rather than yielding it. If you hit it, change `return {...}` to
> `yield {...}`.

### Step 3b — the "returning a dict" trap, demonstrated

Create `work/dict_return.py`:

```python
"""Show the difference between yielding a dict and returning one."""

import apache_beam as beam


class ReturnsDict(beam.DoFn):
    def process(self, value):
        return {"k": value}          # wrong: this raises


class YieldsDict(beam.DoFn):
    def process(self, value):
        yield {"k": value}           # right: yields one dict element


with beam.Pipeline() as p:
    source = p | "Create" >> beam.Create(["a", "b"])

    (
        source
        | "Yield" >> beam.ParDo(YieldsDict())
        | "Format" >> beam.Map(lambda d: f"k={d['k']}")
        | "Write" >> beam.io.WriteToText("./out/dict_yield", num_shards=1)
    )
```

Run it:

```bash
python work/dict_return.py
cat out/dict_yield*
```

Expected output:

```text
k=a
k=b
```

Swap `YieldsDict` for `ReturnsDict` and the job fails with the
`TypeError` above. This distinction is worth internalising, because the
error message's suggestion — "use `list({...})`" — is actively wrong
advice for your case. You want to yield the dict, not wrap it in a
list.

### Step 4 — register a coder for a custom class

Create `work/custom_coder.py`:

```python
"""Register a deterministic coder for a custom Order class."""

import apache_beam as beam
from apache_beam.coders import coders
from apache_beam.coders.typecoders import registry


class Order:
    def __init__(self, order_id, region, amount):
        self.order_id = order_id
        self.region = region
        self.amount = amount

    def __repr__(self):
        return f"Order({self.order_id!r}, {self.region!r}, {self.amount!r})"


class OrderCoder(coders.Coder):
    """A compact, deterministic text encoding for Order."""

    def encode(self, order):
        return f"{order.order_id}|{order.region}|{order.amount:.2f}".encode("utf-8")

    def decode(self, encoded):
        order_id, region, amount = encoded.decode("utf-8").split("|")
        return Order(order_id, region, float(amount))


registry.register_coder(Order, OrderCoder)

print("registered coder:", type(registry.get_coder(Order)).__name__)
print("deterministic:", registry.get_coder(Order).is_deterministic())

with beam.Pipeline() as p:
    orders = (
        p
        | "Create" >> beam.Create([Order("o1", "EMEA", 10.5), Order("o2", "AMER", 3.25)])
        | "Annotate" >> beam.Map(lambda o: o)
    )
    print("element_type:", orders.element_type)
```

Run it:

```bash
python work/custom_coder.py
```

Expected output:

```text
registered coder: OrderCoder
deterministic: False
element_type: <class '__main__.Order'>
```

Compare the last line with step 3: a custom class with a registered
coder reports its real type, not `Any`.

The `deterministic: False` line is worth a second look. A custom
`coders.Coder` subclass does **not** get determinism for free. The base
`Coder.is_deterministic()` returns `False` unless you override it. If
your custom type is going to be a `GroupByKey` key, or you want the
runner to be able to fuse the stage, override it:

```python
class OrderCoder(coders.Coder):
    def encode(self, order):
        return f"{order.order_id}|{order.region}|{order.amount:.2f}".encode("utf-8")

    def decode(self, encoded):
        order_id, region, amount = encoded.decode("utf-8").split("|")
        return Order(order_id, region, float(amount))

    def is_deterministic(self):
        return True
```

That is an honest claim here: the encoding is a pure function of the
value, with no dictionary iteration order and no object identity in it.

### Step 5 — the pickle cost, measured

This is the exercise that makes the argument concrete. Write a hundred
thousand small records twice — once as a hinted `Tuple[int, str]`, once
as a bare `dict` — and compare the encoded bytes.

Create `work/pickle_cost.py`:

```python
"""Measure the byte cost of a hinted tuple versus an unhinted dict."""

import apache_beam.typehints as th
from apache_beam.coders.typecoders import registry

N = 100_000


def encode_all(elements, coder):
    """Return the total encoded size of a list of elements."""
    return sum(len(coder.encode(e)) for e in elements)


hinted = [("o0001", "EMEA") for _ in range(N)]
unhinted = [{"order_id": "o0001", "region": "EMEA"} for _ in range(N)]

tuple_coder = registry.get_coder(th.Tuple[str, str])
dict_coder = registry.get_coder(dict)

tuple_bytes = encode_all(hinted, tuple_coder)
dict_bytes = encode_all(unhinted, dict_coder)

print(f"tuple elements: {N}")
print(f"  coder: {type(tuple_coder).__name__}")
print(f"  total bytes: {tuple_bytes:,}")
print(f"  bytes per element: {tuple_bytes / N:.2f}")

print(f"dict elements: {N}")
print(f"  coder: {type(dict_coder).__name__}")
print(f"  total bytes: {dict_bytes:,}")
print(f"  bytes per element: {dict_bytes / N:.2f}")

print(f"ratio (dict/tuple): {dict_bytes / tuple_bytes:.2f}x")
```

Run it:

```bash
python work/pickle_cost.py
```

Expected output:

```text
tuple elements: 100000
  coder: TupleCoder
  total bytes: 1,000,000
  bytes per element: 10.00
dict elements: 100000
  coder: FastPrimitivesCoder
  total bytes: 3,300,000
  bytes per element: 33.00
ratio (dict/tuple): 3.30x
```

The exact byte counts depend on your Python version's pickle protocol,
but the shape is stable: **the unhinted dict costs roughly three times
more to move, and it is not deterministic.** At 100 million elements
that gap becomes tens of gigabytes of extra network traffic per stage,
per pipeline run — and, unlike the tuple, the dict's bytes are not
reproducible, so they cannot be deduplicated or cached.

Note that `coders.typecoders` is *not* reachable as an attribute of the
`apache_beam.coders` module. Import the registry directly:

```python
from apache_beam.coders.typecoders import registry
```

### Step 6 — annotate the course's order dicts

The course's `transforms.py` produces plain dicts from an unannotated
`DoFn`, so that stage falls back to pickle. Here is how you would fix
it without changing the parsing logic — a type hint is enough:

```python
import apache_beam as beam
import apache_beam.typehints as th

with beam.Pipeline() as p:
    (
        p
        | "Read" >> beam.io.ReadFromText("./sample_data/orders.csv")
        | "Parse" >> beam.Map(lambda line: line.split(","))
        | "Annotate" >> beam.Map(lambda parts: parts).with_output_types(
            th.List[str]
        )
    )
```

Annotating the intermediate `List[str]` is the cheap, high-value fix: a
list of strings is a `ListCoder` of `StrUtf8Coder`s, and the stage
stops pickling.

The real pipeline's parse stage is a `ParDo`, so the equivalent fix
there is to annotate the transform:

```python
from apache_beam.coders import coders
import apache_beam.typehints as th

orders = (
    lines
    | "ParseOrders" >> beam.ParDo(ParseOrderFn()).with_output_types(
        th.Dict[str, th.Any]
    )
)
```

Note that `th.Dict[str, th.Any]` is a *composite* hint, so Beam builds a
`MapCoder` with a `StrUtf8Coder` key and a `FastPrimitivesCoder` value —
a real, structured encoding rather than a whole-dict pickle. The inner
`Any` is honest: the order record has nine fields of mixed types, and
naming them all would mean a `NamedTuple` or a schema, which is a
different design decision.

---

## 🛠️ Common Errors and Fixes

### `AttributeError: module 'apache_beam.coders' has no attribute 'AvroCoder'`

There is no class called `AvroCoder` in Beam 2.77. The Avro coder is
called **`AvroGenericCoder`**, and it lives in the top-level
`apache_beam.coders` namespace:

```python
from apache_beam.coders import AvroGenericCoder
```

The class you are probably thinking of, `RowCoder`, is in a different
place:

```python
from apache_beam.coders.row_coder import RowCoder
```

`BytesCoder`, `StrUtf8Coder`, `TupleCoder`, `FastPrimitivesCoder`,
`PickleCoder`, `BooleanCoder`, `NullableCoder`, `DillCoder`,
`ProtoCoder` and `SingletonCoder` *are* in `apache_beam.coders`.

### `TypeError: NullableCoder.__init__() missing 1 required positional argument: 'value_coder'`

`NullableCoder` is a composite coder and needs a child coder:

```python
from apache_beam.coders import coders

coder = coders.NullableCoder(coders.StrUtf8Coder())
```

The better fix is to let the type hint do it. Annotate the output as
`th.Optional[str]` and Beam builds the `NullableCoder` itself.

### `AttributeError: 'PTransform' object has no attribute 'with_output_coder'`

There is no `with_output_coder` in the Beam 2.77 Python SDK. It is a
Java-SDK idiom (`Coder` selection via `withOutputCoder`). The Python
equivalents are:

```python
# Attach a coder to an IO transform — coder= is supported here
text = p | "Read" >> beam.io.ReadFromText(path, coder=coders.BytesCoder())

# Annotate the element type of a composite transform — this is the
# supported way to control a Map or ParDo's output coder
mapped = p | "MapWithHint" >> beam.Map(func).with_output_types(int)
```

### `TypeError: int() got an unexpected keyword argument 'coder'`

You passed `coder=` to `beam.Map` or `beam.FlatMap`. Those factories
forward unknown keyword arguments to *your callable*, not to the
transform:

```python
# Wrong: `coder` is forwarded to int().
beam.Map(int, coder=coders.VarIntCoder())

# Wrong: `coder` is forwarded to MyDoFn.process.
beam.ParDo(MyDoFn(), coder=coders.VarIntCoder())

# Right: annotate the output type.
beam.Map(int).with_output_types(int)
beam.ParDo(MyDoFn()).with_output_types(int)
```

`coder=` is supported on the Beam **I/O** transforms — `ReadFromText`,
`WriteToText`, and the other source and sink classes — and nowhere
else.

### `TypeError: 'PTransform' object has no attribute 'with_output_types'` — no, it does, but you called it wrong

`with_output_types` is a method on the *transform instance*, not on the
factory function. This is wrong:

```python
# Wrong: with_output_types is not a keyword of the factory.
beam.Map(fn, with_output_types=int)
```

This is right:

```python
# Right: chain it onto the transform instance.
beam.Map(fn).with_output_types(int)
```

The same applies to `beam.ParDo(MyDoFn()).with_output_types(int)` and to
`beam.Flatten().with_output_types(th.Tuple[str, str])`.

### `ImportError: Please install apache_beam[dataframe]`

You called `beam.io.ReadFromCsv`, `WriteToCsv`, `ReadFromJson` or
`WriteToJson` without pandas installed. Those four transforms are
pandas-backed in Beam 2.77.

```bash
pip install "apache-beam[dataframe]"
```

The alternative — and usually the better one — is to use
`ReadFromText` and parse the records yourself. Chapter 3.3 shows why.

### `RuntimeError: CoderRegistry has no fallback coder. This can happen if the fast_coders module could not be imported.`

Your `apache_beam.coders.fast_coders` C extension failed to build or
import — usually a Python-version mismatch with a prebuilt wheel. Check:

```bash
python -c "from apache_beam.coders import fast_coders; print('ok')"
```

If that raises, reinstall Beam:

```bash
pip install --force-reinstall --no-cache-dir apache-beam
```

### `RuntimeError: Cannot deterministically encode ... ` on a `GroupByKey` stage

The key's coder is not deterministic, so Beam cannot merge partial
results safely. This almost always means the key type is unannotated and
fell back to pickle.

```python
# Wrong: the key is a bare dict, so the coder is PickleCoder.
beam.Map(lambda row: ({"region": row[3]}, row[7]))

# Right: a hashable, typed key.
beam.Map(lambda row: (row[3], row[7])).with_output_types(th.Tuple[str, str])
```

### `AttributeError: 'NoneType' object has no attribute 'encode'`

A `ParDo` emitted `None`. A `DoFn.process` that returns `None` instead of
yielding nothing is a common mistake:

```python
# Wrong: yields None as an element.
def process(self, line):
    return None

# Right: yield nothing.
def process(self, line):
    return
    yield  # unreachable, but the function is a generator
```

Cleaner: use `return` and no `yield` at all, so the function is a plain
function returning `None`. Beam treats that as "emit nothing".

### `ValueError: Type hint for ... must be a type, a TypeConstraint, or a callable`

Your hint is an *instance* rather than a type. Write `th.Optional[str]`,
not `th.Optional(str)`.

---

## 💡 Production Notes

- **Check `element_type` in code review.** If it is `typing.Any`, the
  stage is pickling. This is the single most valuable one-line review
  comment in a Beam codebase, and it takes seconds to check.
- **Prefer hints over coder overrides.** A hint constrains the input
  type, the output type, and the coder, in one declaration. A `coder=`
  override only constrains the encoding, and leaves the type check
  blind.
- **Never let `PickleCoder` reach a `GroupByKey` key.** Non-deterministic
  keys break merging and can produce silently wrong results under
  retries. If your key is a custom class, register a deterministic
  coder for it.
- **Coder choice is a cost decision, not a style decision.** A
  `FastPrimitivesCoder` with a `StrUtf8Coder` child encodes a `str` in
  roughly one byte per character. Pickle adds framing. On a stage that
  moves a terabyte, that is a line item.
- **Determinism is what buys you fusion.** Beam can only fuse a step
  into its neighbour when it can prove the reordering is safe.
  Non-deterministic coders are one of the things that make fusion
  impossible. If your pipeline has an unexpectedly large number of
  steps in the Dataflow graph, look at the coders.
- **Register coders at import time, in one module.** A `register_coder`
  call buried in a transform's `expand` runs on the driver, but the
  workers need the registration too. Put it in a module that both
  import, so it happens on every worker.
- **`bytes` is a better default than `str` for binary payloads.** A
  `StrUtf8Coder` will raise `UnicodeDecodeError` on a file with a
  stray byte. A `BytesCoder` will not, and you can decode explicitly
  with an error policy you control.
- **Pin your Beam version.** Coder inference has changed across
  releases — `DeterministicFastPrimitivesCoder` is new, and the
  fallback behaviour is not identical between 2.5x and 2.7x. A pipeline
  that "changed behaviour after an upgrade" is almost always a coder
  change.

---

## 🔑 Key Takeaways

- Beam's I/O is a **catalogue**, not one API: portable file formats,
  runner-specific messaging, databases, and one file transform per
  format with the *path* selecting the file system.
- A **coder** turns a Python value into bytes and back. "Encoder" is the
  Java term for the same idea; the two words are used interchangeably.
- The registry infers coders **from type hints**, not from inspecting
  data. `int` → `VarIntCoder`, `str` → `StrUtf8Coder`, `bool` →
  `BooleanCoder`, `Tuple[int, str]` → `TupleCoder`, `Optional[str]` →
  `NullableCoder`.
- **A missing hint means the fallback coder, which means pickle.** An
  `element_type` of `typing.Any` is the diagnostic.
- `FastPrimitivesCoder` is the fast path; `PickleCoder` is the
  fallback. Pickle is slow, **non-deterministic**, and blocks fusion.
- `NullableCoder` is a composite coder — it needs a child coder, and
  you rarely construct it by hand because `Optional[T]` selects it for
  you.
- `AvroGenericCoder` lives in `apache_beam.coders`; `RowCoder` lives in
  `apache_beam.coders.row_coder`. There is no class named `AvroCoder`.
- There is **no `with_output_coder`** in the Python SDK. Use
  `coder=...` on I/O transforms, or `with_output_types(...)` everywhere.
- `coder=` is **not** accepted by `beam.Map` or `beam.ParDo` — those
  forward unknown keywords to your callable. Use a type hint.

---

## 📚 Practice Exercises

1. **Build a coder inventory.** Write a script that walks a pipeline
   object and prints the `element_type` of every PCollection it can
   reach. Run it against `project/batch_pipeline.py`'s
   `build_pipeline` and list every stage that falls back to `Any`.
   *Expected answer:* at least the `ParseOrders` stage, because
   `ParseOrderFn` emits plain dicts.

2. **Make a stage deterministic.** Change the parse stage of
   `project/batch_pipeline.py` so that `orders` has a concrete
   `element_type` instead of `Any`, without changing
   `transforms.py`. *Expected answer:* annotate the `ParDo` with
   `.with_output_types(th.Dict[str, th.Any])` and check
   `orders.element_type` — it should no longer be `Any`.

3. **Write a custom coder.** Implement a `RegionRevenueCoder` that
   encodes a `(str, float)` pair as `b"EMEA=1234.56"` and decodes it
   back. Register it for a `RegionRevenue` namedtuple and confirm
   `registry.get_coder(RegionRevenue).is_deterministic()` is `True`.
   Then use it as a `GroupByKey` key and confirm the aggregation works.

4. **Measure the pickle tax.** Extend `work/pickle_cost.py` to compare
   three encodings of the same 100,000 records: a bare dict, a hinted
   `Dict[str, str]`, and a hinted `Tuple[str, str]`. Report bytes per
   element for each. *Expected answer:* the bare dict is the largest and
   the only non-deterministic one.

5. **Prove the fallback.** Write a pipeline that groups by a bare dict
   key and one that groups by a string key, and run both with
   `--runner DirectRunner` and with the `DirectRunner` in
   `--runner=FnApiRunner` style strict type checking if your Beam
   version supports it. Explain which one Beam warns about and why.

6. **Reflection.** Your team wants to swap `str` fields for a
   `Decimal` type for financial accuracy. List, in order, the three
   things you would have to change: the type hint, the coder, and the
   function that produces the value. Which of the three is easiest to
   get wrong, and what is the symptom when you do?

---

## 📖 Further Reading

- Apache Beam: Type Hints — https://beam.apache.org/documentation/programming-guide/#type-hints
- Apache Beam: Coders — https://beam.apache.org/documentation/programming-guide/#coders
- Beam Python SDK API — `apache_beam.coders` — https://beam.apache.org/releases/pydoc/current/apache_beam.coders.coders.html
- Beam Python SDK API — `apache_beam.coders.row_coder` — https://beam.apache.org/releases/pydoc/current/apache_beam.coders.row_coder.html
- Beam Python SDK API — `apache_beam.coders.typecoders` — https://beam.apache.org/releases/pydoc/current/apache_beam.coders.typecoders.html
- Beam: Choosing a Coder (design doc) — https://beam.apache.org/roadmap/beam-coder-choice/
