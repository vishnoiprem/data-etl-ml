# 6.2 — Schema, Coders & Encoders

> **Section 6 · Batch Pipeline Engineering · Lecture 6.2 · 6:30**

## 🎯 What you will learn

- What a coder actually is, and why Beam cannot run a distributed pipeline without one
- How Beam picks a coder: the registry, the type hint, the fallback chain, and the runtime escape hatch
- `FastPrimitivesCoder` — what it handles natively, and the fact that it is **not deterministic** in apache-beam 2.77
- `RowCoder` and `beam.pvalue.Row` — and the fact that `apache_beam.rows` **does not exist** in this environment
- `AvroGenericCoder` and schema inference, and how to register a schema'd type
- Why an explicit coder matters, and the `pickle` coder warning
- `NullableCoder`, and what it does to determinism
- Beam's schema machinery: `apache_beam.typehints.schemas`, and `registry.register_row`
- Schema evolution in a batch pipeline, and the operational trap in `ReadFromCsv` with schema inference

---

## 🧠 Concept

### The problem coders solve

Beam's execution model is: workers exchange *encoded* elements. A worker
reads a file, decodes an element into a Python object, runs your function,
encodes the result, and ships it across the network. Another worker decodes
it and continues.

Every one of those encode/decode steps needs a coder — an object that knows
how to turn a Python value into bytes and back. Beam cannot run a
distributed pipeline without them, and if the coder on the sending side
does not match the coder on the receiving side, you get garbage or an
exception.

The rule that follows: **the coder is part of your pipeline's contract.** It
determines what can cross a shuffle, whether the results are reproducible,
and whether the output can be read by another system.

### How Beam decides the coder

There are exactly four mechanisms, in the order Beam consults them.

#### 1. The coder registry

Beam keeps a global registry mapping Python types to coder classes. It is
populated with the standard types at import time:

| Python type | Coder | Deterministic? |
|---|---|---|
| `int` | `VarIntCoder` | yes |
| `float` | `FloatCoder` | yes |
| `str` | `StrUtf8Coder` | yes |
| `bytes` | `BytesCoder` | yes |
| `bool` | `BooleanCoder` | yes |
| `dict` | `FastPrimitivesCoder` | **no** |
| `tuple` | `FastPrimitivesCoder` | **no** |
| `list` | `FastPrimitivesCoder` | **no** |
| `NoneType` | `FastPrimitivesCoder` | **no** |

You can inspect it at runtime:

```python
from apache_beam.coders import registry

print(registry.get_coder(int))    # VarIntCoder
print(registry.get_coder(str))    # StrUtf8Coder
print(registry.get_coder(dict))   # FastPrimitivesCoder
```

Read that table carefully, because it is the single most useful fact in
this chapter. **The five scalar types get dedicated, deterministic
coders. The four container types all fall back to
`FastPrimitivesCoder`, which is not deterministic.**

This is the part that surprises people. `MapCoder`, `TupleCoder`, and
`ListCoder` all exist in `apache_beam.coders` — they are real, and they
are deterministic. But the registry does not hand them out for the bare
Python types. `MapCoder` is only reachable through
`MapCoder.from_type_hint`, that is, from a `Dict[str, int]`-style type
hint. `TupleCoder` is reachable the same way, from a
`Tuple[int, str]`-style hint. `ListCoder`, likewise, from
`List[str]`.

So the rule is not "containers are pickled". The rule is: **a type
hint gets you a precise, deterministic coder; a bare Python type gets
you the pickled fallback.** Annotate and you get structure. Do not
annotate and you get bytes.

For `NoneType` the answer looks strange — `FastPrimitivesCoder` for
`None`? — but it is the same rule: there is no `NoneTypeCoder`, and
`FastPrimitivesCoder` handles `None` by encoding it as a pickled
`None`. To get a real nullable coder, use a type hint of
`Optional[X]`, which produces a `NullableCoder` wrapping the coder for
`X`.

#### 2. The type hint

If you tell Beam the element type, it looks up the coder for that type.
The type hint comes from one of three places:

- **Explicit annotation.** `with_input_types(...)` / `with_output_types(...)`
  on a `DoFn` or a `PTransform`.
- **Function return annotation.** `def parse(line: str) -> Order:` — Beam
  reads the annotation.
- **Inference from the source.** `beam.Create([...])` knows the type of the
  elements it was handed.

The project's `ParseOrderFn` has no annotations, so its output type is
`Any`:

```python
from transforms import ParseOrderFn

with beam.Pipeline() as pipeline:
    orders = (
        pipeline
        | "Create" >> beam.Create([VALID_LINE])
        | "Parse" >> beam.ParDo(ParseOrderFn())
    )
    print(orders.element_type)   # Any
```

`Any` means "the runner will work it out" — which is exactly the
ambiguity this chapter is about.

#### 3. The fallback chain

When no coder is registered for the type, Beam walks a fallback chain. The
chain, verified in apache-beam 2.77, is:

```text
ProtoCoder  →  ProtoPlusCoder  →  FastPrimitivesCoder
```

The first two handle protobuf types. The third handles everything else.

`FastPrimitivesCoder` encodes natively for a set of primitives and
delegates anything else to its own fallback — a `PickleCoder`:

```python
from apache_beam.coders import FastPrimitivesCoder

coder = FastPrimitivesCoder()
coder.encode("hello")        # a compact varint-tagged encoding
coder.encode({"a": 1})       # also native
coder.encode(SomeClass())    # falls back to pickle
```

The fallback marker is visible in the bytes: a native encoding starts with
a small tag byte, while a pickled value starts with `\x80\x05` — the
standard Python pickle protocol marker.

#### 4. The runtime escape hatch

For a source that produces a specific type, you can hand the coder
directly. `ReadFromText` takes a `coder=` argument:

```python
from apache_beam.coders import StrUtf8Coder

lines = pipeline | "Read" >> beam.io.ReadFromText(path, coder=StrUtf8Coder())
```

That is the *only* place in apache-beam 2.77 where you name a coder
directly on a transform.

> **A note on `with_output_coder`.**
>
> There is no `with_output_coder` method anywhere in apache-beam 2.77:
>
> ```text
> AttributeError: 'ParDo' object has no attribute 'with_output_coder'
> ```
>
> It is not on `PTransform`, not on `ParDo`, not on `Map`. The method you
> want is **`with_output_types`**, which takes a *type hint* rather than a
> coder. If you pass a coder instance to it, you get:
>
> ```text
> TypeError: Type hints for a PTransform must be a non-sequence, a type,
> or a TypeConstraint. StrUtf8Coder is an instance of StrUtf8Coder.
> ```
>
> To control the coder of a transform's output in 2.77, register a coder
> for your type (see below) and then annotate the type. That is the
> supported path.

### `FastPrimitivesCoder` and its limits

`FastPrimitivesCoder` is the workhorse fallback. It is fast because it
encodes primitives into a compact tagged binary format rather than into
JSON or pickle.

What it handles natively (verified in 2.77): `int`, `float`, `str`,
`bytes`, `bool`, `list`, `dict`, `tuple`, `set`, `complex`, `None`.

What it does **not** handle natively: **any user-defined class**. Those
fall through to `PickleCoder`.

The critical limitation, and the one that surprises people:

```python
from apache_beam.coders import FastPrimitivesCoder

print(FastPrimitivesCoder().is_deterministic())
# False
```

**`FastPrimitivesCoder` is not deterministic in apache-beam 2.77.** The
reason is structural: `is_deterministic()` delegates to its fallback
coder, and the fallback is a `PickleCoder`, which is not deterministic.

Determinism matters because of the shuffle. When Beam combines elements,
it needs a stable encoding so that equal keys encode identically and land
on the same worker. A non-deterministic coder can break that.

The standard coders — `StrUtf8Coder`, `VarIntCoder`, `FloatCoder`,
`BytesCoder`, `BooleanCoder` — are all deterministic. The problem is
specific to the fallback path.

There is a second, subtler limit: **`FastPrimitivesCoder` encodes a `dict`
as a dict, and dict iteration order in Python is insertion order.** Two
dicts with the same key-value pairs but different insertion order encode
differently:

```python
from apache_beam.coders import PickleCoder

coder = PickleCoder()
coder.encode({"b": 1, "a": 2})
# b'\x80\x05...}\x94(\x8c\x01b\x94K\x01\x8c\x01a\x94K\x02u.'
coder.encode({"a": 2, "b": 1})
# b'\x80\x05...}\x94(\x8c\x01a\x94K\x02\x8c\x01b\x94K\x01u.'
```

Different bytes. Same logical value. For a *value* that is harmless — the
value is semantically the same. For a *key* it is fatal, because the
shuffle routes by the encoded bytes.

This is exactly why the course project's `ParseOrderFn` yields **dicts**
rather than custom objects, and why the project never uses a dict as a
shuffle key. It keys by `order["region"]` — a plain string.

### `RowCoder` and `beam.pvalue.Row`

Beam's "schema'd" row type has a confusing history, and the confusion is
routinely baked into generated code and blog posts. Here is the verified
situation in apache-beam 2.77.

#### `apache_beam.rows` does not exist

```bash
python -c "import apache_beam.rows"
```

```text
ModuleNotFoundError: No module named 'apache_beam.rows'
```

And:

```bash
python -c "from apache_beam import rows"
```

```text
ImportError: cannot import name 'rows' from 'apache_beam'
```

There is no `apache_beam.rows` module and no `apache_beam.rows.Row` class
in this environment. Any code that says

```python
from apache_beam.rows import Row
```

will fail at import time.

#### What *does* exist: `beam.pvalue.Row`

```python
from apache_beam.pvalue import Row

row = Row(order_id="o1", region="EMEA", amount=100.0)
print(row.order_id)          # o1
print(row.as_dict())         # {'order_id': 'o1', ...}
```

`beam.pvalue.Row` is a **dynamic** row: it is just a thin wrapper around
`__dict__`. It has no schema of its own — the schema is inferred from the
keys at the point where Beam inspects it.

Two properties of `beam.pvalue.Row` matter:

1. **Field order is significant.** Since Beam 2.30, `Row(x=3, y=4)` is
   not equal to `Row(y=4, x=3)`. This is deliberate: the row's schema is
   ordered, and reordering fields is a schema change.
2. **It is not the same thing as a schema'd row.** A `beam.pvalue.Row` has
   no registered schema, so it encodes with the fallback coder — which
   means pickle. That is the opposite of what you want.

#### The supported path: a dataclass registered with `register_row`

This is the modern, documented way to get a schema'd, typed, deterministic
row in Beam 2.77:

```python
from dataclasses import dataclass

from apache_beam.coders import typecoders


@dataclass
class Order:
    order_id: str
    region: str
    amount: float


typecoders.registry.register_row(Order)
```

`register_row` does two things: it registers a `RowCoder` for the type,
and it registers the type's schema with the schema registry. After that:

```python
coder = typecoders.registry.get_coder(Order)
print(coder)                        # RowCoder
print(coder.is_deterministic())     # True
```

The schema itself comes from `apache_beam.typehints.schemas`:

```python
from apache_beam.typehints.schemas import typing_to_runner_api

schema = typing_to_runner_api(Order)
print(schema)
```

```text
row_type {
  schema {
    fields { name: "order_id" type { atomic_type: STRING } }
    fields { name: "region"   type { atomic_type: STRING } }
    fields { name: "amount"   type { atomic_type: DOUBLE } }
    id: "6b416d20-ce1e-4c6e-a3fb-5ae229ddf65e"
  }
}
```

That `id` is a UUID derived from the schema. It is how Beam identifies
the schema across the wire, and it is why two pipelines with the same
field names but different types get different schema ids.

#### `apache_beam.schema` also does not exist

For the same reason:

```bash
python -c "import apache_beam.schema"
```

```text
ModuleNotFoundError: No module named 'apache_beam.schema'
```

The Beam schema machinery lives in `apache_beam.typehints.schemas` and
`apache_beam.coders.row_coder`. The `apache_beam.schema` module name
belongs to the **Java** SDK's schema extensions, not the Python one.

#### `RowCoder` and `force_deterministic`

`RowCoder` has a `force_deterministic` flag. The constructor is
`RowCoder(schema, force_deterministic=False)`, and the `schema` it
wants is the **inner schema proto** — not the `FieldType` wrapper that
`typing_to_runner_api` returns:

```python
from apache_beam.coders import RowCoder
from apache_beam.typehints.schemas import typing_to_runner_api

row_type = typing_to_runner_api(Order)
schema = row_type.row_type.schema      # <- the .row_type.schema part matters

coder = RowCoder(schema)
print(coder)                            # RowCoder
print(coder.is_deterministic())         # True

forced = RowCoder(schema, force_deterministic=True)
print(forced.is_deterministic())        # True
```

Pass `typing_to_runner_api(Order)` directly and you get:

```text
AttributeError: id
```

Because `FieldType` has no `id` — the `id` lives one level down, on
`row_type.schema`. This is the single most common way to get this
wrong.

With the flag set, Beam raises rather than silently producing a
non-deterministic encoding when a field type cannot be encoded
deterministically. In practice the flag matters for `map` and `list`
fields, whose ordering is not stable.

### `AvroGenericCoder` and schema inference

`AvroGenericCoder` encodes Avro records. Two details about its API trip
people up, and both are silent until you encode something:

```python
import json

from apache_beam.coders import AvroGenericCoder
from apache_beam.coders.avro_record import AvroRecord

AVRO_SCHEMA = {
    "type": "record",
    "name": "Order",
    "fields": [
        {"name": "order_id", "type": "string"},
        {"name": "region", "type": "string"},
        {"name": "amount", "type": "double"},
    ],
}

# 1. The schema is a JSON *string*, not a dict.
coder = AvroGenericCoder(json.dumps(AVRO_SCHEMA))

# 2. The value is an AvroRecord, not a plain dict.
record = AvroRecord({"order_id": "o1", "region": "EMEA", "amount": 10.5})
encoded = coder.encode(record)
print(encoded)
print(coder.decode(encoded).record)
```

Output:

```text
b'\x04o1\x08EMEA\x00\x00\x00\x00\x00\x00%@'
{'order_id': 'o1', 'region': 'EMEA', 'amount': 10.5}
```

Pass a dict as the schema and you get:

```text
TypeError: the JSON object must be str, bytes or bytearray, not dict
```

Pass a plain dict as the value and you get:

```text
AssertionError
```

— because `AvroCoderImpl.encode` asserts that the value is an
`AvroRecord`. An assertion, not a validation, so it disappears entirely
under `python -O`.

One more wrinkle: `AvroGenericCoder` reports
`is_deterministic() == False`. The Avro *binary* encoding is
deterministic, but the coder in 2.77 does not claim to be. If Avro
records are your shuffle key, be aware of that.

The "schema inference" that people associate with Avro is really the
behaviour of the *schema-bearing IO transforms*. `beam.io.WriteToAvro`
takes the schema explicitly:

```python
AVRO_SCHEMA = {
    "type": "record",
    "name": "Order",
    "fields": [
        {"name": "order_id", "type": "string"},
        {"name": "region", "type": "string"},
        {"name": "amount", "type": "double"},
    ],
}

rows | "WriteAvro" >> beam.io.WriteToAvro(
    "gs://bucket/orders", schema=AVRO_SCHEMA, num_shards=1
)
```

Note the contrast with the coder: `WriteToAvro` accepts the schema as a
**dict**, because it converts it itself before handing it to the
coder.

Avro's schema-in-file is the reason Avro is the right choice for a
long-lived, cross-team data contract: the reader does not need to know
the schema in advance, and the schema travels with the data.

### Why an explicit coder matters

Five reasons, in descending order of how often they bite.

**1. Determinism.** The shuffle routes by encoded key. A non-deterministic
key coder means two logically-equal keys can encode differently and land
on different workers, and the aggregation splits.

**2. Performance.** `PickleCoder` serialises the object's entire class
definition on first use. For a dict of nine fields, `FastPrimitivesCoder`
is roughly 10–20× smaller and 5–10× faster. Over a 5 TB shuffle, that is
the difference between a 40-minute job and a 6-hour job.

**3. Cross-language compatibility.** `PickleCoder` output is readable only
by Python. If your consumer is Java, Spark, or BigQuery, a pickle-encoded
intermediate is a dead end. `AvroGenericCoder` and `RowCoder` output is
portable.

**4. Schema enforcement.** With an explicit coder, a mismatched element
fails loudly at the boundary. With the fallback, it fails obscurely three
stages later.

**5. Version stability.** A pickle-encoded intermediate file is tied to
the exact class definition that produced it. Rename a field, change a
default, and the old files become unreadable — with no error until you try.

### The `pickle` coder warning

Beam's own documentation warns about the fallback:

```text
WARNING: Using fallback coder for typehint: <class 'MyCustomType'>.
```

That warning is your signal that a custom class is being pickled. In
apache-beam 2.77 the warning is emitted through the logging system rather
than `warnings.warn`, so you may need to configure logging to see it.

The fix is to register a coder:

```python
from apache_beam.coders import coders


class OrderCoder(coders.Coder):
    """Encode an Order as a compact, deterministic byte string."""

    def encode(self, order):
        return f"{order.order_id}|{order.region}|{order.amount}".encode("utf-8")

    def decode(self, encoded):
        order_id, region, amount = encoded.decode("utf-8").split("|")
        return Order(order_id, region, float(amount))

    def to_type_hint(self):
        return Order

    def is_deterministic(self):
        return True


coders.registry.register_coder(Order, OrderCoder)
```

The registry is `apache_beam.coders.typecoders.registry` — the
`apache_beam.coders` package re-exports `coders`, `FastPrimitivesCoder`
and friends, but the `registry` object lives in `typecoders`:

```python
from apache_beam.coders import typecoders

typecoders.registry.register_coder(Order, OrderCoder)
```

### `NullableCoder`

`NullableCoder` wraps another coder to add a null flag. It is what you
get automatically for `Optional[X]` type hints:

```python
from apache_beam.coders import NullableCoder, FloatCoder

coder = NullableCoder(FloatCoder())
print(coder.encode(None))    # b'\x00'
print(coder.encode(1.5))     # b'\x01?\xf8\x00\x00\x00\x00\x00\x00'
print(coder.decode(b'\x00')) # None
```

One byte of overhead: `\x00` for null, `\x01` followed by the value's
encoding otherwise.

`NullableCoder` is deterministic if its inner coder is deterministic, and
it inherits `is_deterministic()` from it.

The practical use is in a schema'd type:

```python
from dataclasses import dataclass
from typing import Optional

from apache_beam.coders import typecoders


@dataclass
class Order:
    order_id: str
    region: str
    amount: float
    discount_code: Optional[str] = None


typecoders.registry.register_row(Order)
```

The `Optional[str]` field becomes a nullable string in the schema, and the
generated `RowCoder` handles the null case.

### Beam schema

Beam's schema is a protobuf message (`schema_pb2.Schema`) with a list of
fields, each of which has a name and a type. The type can be atomic
(`STRING`, `INT64`, `DOUBLE`, `BOOL`, `BYTES`), a nested `row_type`, an
`array_type`, a `map_type`, or a `logical_type` (which carries a
semantic annotation like a timestamp).

Three ways to obtain one:

**From a dataclass or namedtuple**, via `typing_to_runner_api`:

```python
from apache_beam.typehints.schemas import typing_to_runner_api

schema = typing_to_runner_api(Order)
```

**From an Avro schema**, via `avro_schema_to_beam_schema`:

```python
from apache_beam.io.avroio import avro_schema_to_beam_schema

beam_schema = avro_schema_to_beam_schema(avro_schema)
```

**From a Parquet file**, via `beam.io.parquetio` and the Arrow bridge —
which is what `ReadFromParquet` does when `as_rows=True`.

The schema's `id` field is a UUID. Beam uses it to match schemas across
the Runner API boundary, and it is regenerated when the schema changes.
This is why two structurally identical schemas produced by two different
runs have the *same* id (the id is derived from the content) while two
different schemas have different ids.

### Schema evolution in a batch pipeline

A batch pipeline's schema is not a runtime negotiation — it is baked into
the pipeline when the graph is constructed. There is no "the producer
added a column and we adapt".

The three situations:

**Additive change (new nullable column).** The safest case. If the source
gains a column with a default, old files and new files coexist. But the
*inferred* schema of a new file will differ from the inferred schema of
an old file, so a pipeline that reads both in one job will fail or produce
nulls, depending on how the reader is configured.

**Breaking change (type change, removed column).** The pipeline must be
updated. There is no negotiation.

**Silent change.** The worst case: the new column has a type the reader
can coerce, so the pipeline runs and produces subtly wrong data.

#### The `ReadFromCsv` inference trap

This is the specific trap this chapter is about.

In apache-beam 2.77, `beam.io.ReadFromCsv` is the **pandas-based**
reader. Its signature is:

```text
ReadFromCsv(path: str, *, splittable: bool = True,
            filename_column: Optional[str] = None, **kwargs)
```

The `**kwargs` are forwarded to `pandas.read_csv`. There is **no
`infer_schema` parameter** — pandas infers dtypes by default and `infer_schema`
is not a pandas `read_csv` argument.

> **A note on the old `apache_beam.io.csvio` module.** Older Beam
> versions had `apache_beam.io.csvio.ReadFromCsv` with a `coder` argument
> and a `ReadFromCsv` that did *not* infer a schema — it produced dicts.
> That module does not exist in 2.77:
>
> ```text
> ModuleNotFoundError: No module named 'apache_beam.io.csvio'
> ```
>
> The modern equivalent of the old dict-producing reader is
> `beam.io.ReadFromText` plus an explicit parse step — which is exactly
> what the course project does.

What `beam.io.ReadFromCsv` actually does with `infer_schema=True`-style
behaviour is *implicit*: pandas infers the dtypes from the data, and Beam
wraps the resulting DataFrame rows in a **generated schema'd named tuple**
whose type name embeds a UUID:

```text
BeamSchema_9f0dc081_09f7_4369_a0e6_ea4ed11d6b72(order_id='o1', region='EMEA', amount=10.5)
```

The UUID changes when the schema changes. Read a file with three columns
and one with four, and you get two *different* types:

```text
# three columns
BeamSchema_9f0dc081_09f7_4369_a0e6_ea4ed11d6b72(order_id='o1', region='EMEA', amount=10.5)

# four columns
BeamSchema_26b77c0a_187e_42b4_8b3a_edf5133e3194(order_id='o1', region='EMEA', amount=10.5, channel='web')
```

The UUID is a hash of the inferred schema, so it is regenerated on
every run. Do not paste one into a test assertion.

This is where the operational trap bites. **The inferred schema is baked
into the pipeline at construction time.** If the file changes between the
moment the pipeline is built and the moment the worker reads it — which
is exactly what happens when a producer writes a new version of the file
while a backfill is running — the reader has already committed to the old
schema.

And worse: if you select columns explicitly with `usecols=`, the drift
is **silent**:

```python
# The pipeline declares three columns. The file has four.
rows = pipeline | "Read" >> beam.io.ReadFromCsv(
    "gs://bucket/orders_2026_01_15.csv",
    usecols=["order_id", "region", "amount"],
)
```

The `channel` column is **dropped without an error**. The job succeeds.
The output is wrong.

> **`dtype` is not `usecols`.** `ReadFromCsv` forwards its keyword
> arguments straight to `pandas.read_csv`. `dtype` *casts* the columns
> you name and leaves the rest in place. `usecols` *selects*, and
> therefore discards. It is `usecols` that loses data silently.

Three defences:

1. **Pin the schema explicitly** with `usecols=` (the column set) and
   `dtype=` (the column types), and treat a schema change as a code
   change. Pinning turns a silent wrong answer into a loud failure —
   provided you also validate the header.
2. **Validate the header yourself.** Read the file as text, check the
   first line against an expected set of column names, and route
   mismatches to a DLQ. This is what the course project does, by parsing
   every line with `try_parse_order_line`, which rejects any row whose
   field count does not match `ORDER_FIELDS`.
3. **Version the output, not the input.** Write to a date-partitioned
   prefix and never overwrite a partition that has already been written.
   A schema change then lands in a new partition, and the old partition
   remains readable.

The rule: **never let a schema be inferred from data you do not control
at the moment you read it.**

---

## 🛠️ Hands-On: Define a Schema and Write Parquet

### Setup

```bash
cd data-engineering/data-Course/google/Dataflow
source .venv/bin/activate
python resources/sample_data.py --output-dir ./sample_data
```

### Step 1 — see the default coder for the project's pipeline

Create `hands_on_coders.py`:

```python
"""Inspect the coders Beam picks for the course pipeline."""
import apache_beam as beam
from apache_beam.coders import registry

from transforms import ParseOrderFn

VALID_LINE = (
    "o1,c1,2026-01-15T10:00:00+00:00,EMEA,web,EUR,complete,100.00,p1"
)


def main():
    with beam.Pipeline() as pipeline:
        orders = (
            pipeline
            | "Create" >> beam.Create([VALID_LINE])
            | "Parse" >> beam.ParDo(ParseOrderFn())
        )
        print("element_type:", orders.element_type)

    print()
    print("registry lookups:")
    for python_type in (int, float, str, bytes, bool, dict, tuple):
        print(f"  {python_type.__name__:>6} -> {registry.get_coder(python_type)}")


if __name__ == "__main__":
    main()
```

Run it:

```bash
python hands_on_coders.py
```

Expected:

```text
element_type: Any

registry lookups:
     int -> VarIntCoder
   float -> FloatCoder
     str -> StrUtf8Coder
   bytes -> BytesCoder
    bool -> BooleanCoder
    dict -> FastPrimitivesCoder
   tuple -> FastPrimitivesCoder
```

Three things to notice. `element_type` is `Any` — the `ParseOrderFn` has
no type annotations, so Beam has nothing to infer from. A bare `dict`
maps to `FastPrimitivesCoder`, not to `MapCoder`. And a bare `tuple`
maps to `FastPrimitivesCoder` too, even though `TupleCoder` exists in
`apache_beam.coders`.

`TupleCoder` is not something the registry hands out for a plain Python
type. It is a `FastCoder` with a *list of component coders*, and it is
only reachable through `TupleCoder.from_type_hint` — that is, when Beam
resolves a `TupleConstraint` from a **type hint** such as
`Tuple[int, str]`. Ask the registry for the unparameterised `tuple` and
you get the pickled fallback. Ask it for `Tuple[int, str]` and you get
the same answer, because `registry.get_coder` looks up the *Python
class* `typing.Tuple`, not the constraint.

The practical consequence: an untyped tuple of mixed values gets
pickled. If a tuple is your shuffle key, annotate it.

### Step 2 — check the determinism of the coders

Add this to the script, or run it directly:

```python
from apache_beam.coders import (
    BooleanCoder,
    BytesCoder,
    FastPrimitivesCoder,
    FloatCoder,
    PickleCoder,
    StrUtf8Coder,
    VarIntCoder,
)

for coder in (
    StrUtf8Coder(),
    VarIntCoder(),
    FloatCoder(),
    BytesCoder(),
    BooleanCoder(),
    FastPrimitivesCoder(),
    PickleCoder(),
):
    print(f"{type(coder).__name__:<22} deterministic={coder.is_deterministic()}")
```

Expected:

```text
StrUtf8Coder           deterministic=True
VarIntCoder            deterministic=True
FloatCoder             deterministic=True
BytesCoder             deterministic=True
BooleanCoder           deterministic=True
FastPrimitivesCoder    deterministic=False
PickleCoder            deterministic=False
```

`FastPrimitivesCoder` inherits its determinism from its `PickleCoder`
fallback. That is the warning sign: **if your shuffle key might be
encoded by `FastPrimitivesCoder`, pin a deterministic coder for it.**

### Step 3 — define a schema and register it

Create `hands_on_schema.py`:

```python
"""Define a Beam schema, register it, and write Parquet."""
from dataclasses import dataclass
from typing import Optional

from apache_beam.coders import typecoders
from apache_beam.typehints.schemas import typing_to_runner_api


@dataclass
class Order:
    """One order, with a schema Beam knows about."""

    order_id: str
    region: str
    amount: float
    discount_code: Optional[str] = None


def register():
    """Register the Order type and return its schema."""
    typecoders.registry.register_row(Order)
    return typing_to_runner_api(Order)


if __name__ == "__main__":
    schema = register()
    print(schema)
    coder = typecoders.registry.get_coder(Order)
    print()
    print("coder:", coder)
    print("deterministic:", coder.is_deterministic())
```

Run it:

```bash
python hands_on_schema.py
```

Expected shape:

```text
row_type {
  schema {
    fields { name: "order_id" type { atomic_type: STRING } }
    fields { name: "region" type { atomic_type: STRING } }
    fields { name: "amount" type { atomic_type: DOUBLE } }
    fields { name: "discount_code" type { atomic_type: STRING nullable: true } }
    id: "..."
  }
}
coder: RowCoder
deterministic: True
```

Note the `nullable: true` on `discount_code` — that is `Optional[str]`
becoming a nullable string in the schema.

### Step 4 — write to Parquet

`beam.io.WriteToParquet` takes a **`pyarrow.Schema`**, not a Beam Row
schema and not an Avro dict. That is the detail that catches everyone
the first time.

Create `hands_on_parquet.py`:

```python
"""Write schema'd orders to Parquet and read them back."""
import shutil
from dataclasses import asdict, dataclass
from typing import Optional

import apache_beam as beam
import pyarrow as pa
from apache_beam.coders import typecoders

INPUT = "./sample_data/orders.csv"
OUTPUT = "./out/hands_on/orders_parquet"


@dataclass
class Order:
    """One order, with a schema Beam knows about."""

    order_id: str
    region: str
    amount: float
    discount_code: Optional[str] = None


typecoders.registry.register_row(Order)

# `WriteToParquet` wants a pyarrow schema.
ARROW_SCHEMA = pa.schema(
    [
        pa.field("order_id", pa.string()),
        pa.field("region", pa.string()),
        pa.field("amount", pa.float64()),
    ]
)


def parse_line(line):
    """Turn one CSV line into an Order, or None if it does not fit."""
    parts = line.split(",")
    if len(parts) != 9:
        return None
    try:
        amount = float(parts[7])
    except ValueError:
        # The header row lands here: it has nine fields, but "amount"
        # is not a number.
        return None
    return Order(
        order_id=parts[0],
        region=parts[3],
        amount=amount,
    )


def main():
    shutil.rmtree(OUTPUT, ignore_errors=True)

    with beam.Pipeline() as pipeline:
        (
            pipeline
            | "ReadOrders" >> beam.io.ReadFromText(INPUT)
            | "ParseOrders" >> beam.Map(parse_line)
            | "KeepValid" >> beam.Filter(lambda order: order is not None)
            # `WriteToParquet` indexes rows by column name (`row[n]`),
            # so the element must be a dict, not the dataclass.
            | "ToDict" >> beam.Map(asdict)
            | "WriteParquet" >> beam.io.WriteToParquet(
                OUTPUT,
                schema=ARROW_SCHEMA,
                num_shards=1,
            )
        )

    print("written")


if __name__ == "__main__":
    main()
```

Run it:

```bash
python hands_on_parquet.py
ls -la out/hands_on/orders_parquet*
```

You should see a single file `orders_parquet-00000-of-00001`.

Read it back with `pyarrow`:

```python
import pyarrow.parquet as pq

table = pq.read_table("./out/hands_on/orders_parquet-00000-of-00001")
print(table.schema)
print(table.num_rows, "rows")
print(table.to_pydict()["region"][:5])
```

Expected:

```text
order_id: string
region: string
amount: double
5000 rows
['AMER', 'EMEA', 'LATAM', 'APAC', 'EMEA']
```

Note the row order. `WriteToParquet` writes the elements in the order
they arrive, and the order they arrive in is whatever the runner
happened to produce. It is *not* sorted, and it is *not* guaranteed to
be stable across runs once a shuffle is involved. Parquet has no
ordering guarantee — if you need a deterministic order, sort it
explicitly before the write.

### Step 5 — read the Parquet back into Beam

```python
import apache_beam as beam

with beam.Pipeline() as pipeline:
    (
        pipeline
        | "ReadParquet" >> beam.io.ReadFromParquet(
            "./out/hands_on/orders_parquet-00000-of-00001",
            as_rows=True,
        )
        | "Print" >> beam.Map(print)
    )
```

Expected:

```text
BeamSchema_(order_id='o00000000', region='AMER', amount=700.97)
BeamSchema_(order_id='o00000001', region='EMEA', amount=211.61)
...
```

With `as_rows=True`, the rows come back as a generated named tuple whose
type carries the schema. With `as_rows=False` (the default), they come
back as plain dicts.

### Step 6 — watch the CSV schema drift happen

Now the trap. Create `hands_on_schema_drift.py`:

```python
"""Demonstrate the ReadFromCsv schema-inference trap."""
import os

import apache_beam as beam

WORK = "./out/hands_on/drift"
os.makedirs(WORK, exist_ok=True)

V1 = os.path.join(WORK, "v1.csv")
V2 = os.path.join(WORK, "v2.csv")

with open(V1, "w", encoding="utf-8") as handle:
    handle.write("order_id,region,amount\no1,EMEA,10.5\no2,AMER,20.0\n")

with open(V2, "w", encoding="utf-8") as handle:
    handle.write(
        "order_id,region,amount,channel\no1,EMEA,10.5,web\no2,AMER,20.0,mobile\n"
    )


def read(path, label, **kwargs):
    """Read a CSV and print the inferred row type."""
    with beam.Pipeline() as pipeline:
        rows = (
            pipeline
            | "Read" >> beam.io.ReadFromCsv(path, **kwargs)
            | "Print" >> beam.Map(print)
        )
        print(f"--- {label} ---")


def main():
    read(V1, "v1: three columns, schema inferred")
    read(V2, "v2: four columns, schema inferred")

    # Now read the *v2* file but select only the three v1 columns.
    # The fourth column is dropped — silently, with no error.
    read(
        V2,
        "v2 read with usecols pinned to the v1 shape — the new column is dropped silently",
        usecols=["order_id", "region", "amount"],
    )


if __name__ == "__main__":
    main()
```

Run it:

```bash
python hands_on_schema_drift.py
```

Expected:

```text
--- v1: three columns, schema inferred ---
BeamSchema_9f0dc081_09f7_4369_a0e6_ea4ed11d6b72(order_id='o1', region='EMEA', amount=10.5)
BeamSchema_9f0dc081_09f7_4369_a0e6_ea4ed11d6b72(order_id='o2', region='AMER', amount=20.0)

--- v2: four columns, schema inferred ---
BeamSchema_26b77c0a_187e_42b4_8b3a_edf5133e3194(order_id='o1', region='EMEA', amount=10.5, channel='web')
BeamSchema_26b77c0a_187e_42b4_8b3a_edf5133e3194(order_id='o2', region='AMER', amount=20.0, channel='mobile')

--- v2 read with usecols pinned to the v1 shape — the new column is dropped silently ---
BeamSchema_d5bbfd24_f5e2_4fa9_88dd_2aa2a2d9a693(order_id='o1', region='EMEA', amount=10.5)
BeamSchema_d5bbfd24_f5e2_4fa9_88dd_2aa2a2d9a693(order_id='o2', region='AMER', amount=20.0)
```

The UUIDs in those type names are regenerated on every run — they are a
hash of the inferred schema, not a stable identifier. Do not write
them into a test assertion.

Three things to take away:

1. **The inferred type name contains a UUID that changes with the
   schema.** The two files produce two different Python types.
2. **The inferred schema is baked in at pipeline-construction time.** The
   worker does not re-read the header and renegotiate.
3. **`usecols` drops columns without an error.** The third run read a
   four-column file and produced three-column rows. The job succeeded.
   The data was wrong.

One clarification, because it is a common misunderstanding: **`dtype`
is not `usecols`.** `ReadFromCsv` forwards its keyword arguments to
`pandas.read_csv`, and pandas' `dtype` only *casts* the columns you
name — it does not drop the ones you leave out. Passing
`dtype={"order_id": str, "region": str, "amount": float}` to the
four-column file still yields four-column rows, with `channel` intact.
It is `usecols` that selects, and therefore that discards.

Both arguments have a place. `dtype` pins the *type* of a column you
are keeping, which is what you want when pandas might otherwise
infer `object` for a column of numbers with a stray blank. `usecols`
pins the *set* of columns, which is how you accidentally lose data.
If you use `usecols`, treat it as a schema declaration and keep it
next to the contract it mirrors.

### Step 7 — the safe alternative

The course project avoids the whole problem by not inferring anything. It
reads text and validates every row explicitly:

```python
from transforms import try_parse_order_line

with open("./sample_data/orders.csv", encoding="utf-8") as handle:
    for line in handle:
        row = try_parse_order_line(line)
        if row is None:
            print("rejected:", line.strip())
            continue
        print(row["order_id"], row["region"])
```

`try_parse_order_line` checks that the row has exactly `len(ORDER_FIELDS)`
fields and that `amount` parses as a float. A file with an extra column
produces `None` for every row, and every row is rejected — loudly, in the
DLQ, rather than silently.

That is the production pattern: **validate the contract yourself, in
code, at the boundary.** It is slower than letting pandas infer, and it is
the only approach that fails loudly when the producer changes.

---

## 🛠️ Common Errors and Fixes

### `ModuleNotFoundError: No module named 'apache_beam.rows'`

```text
ModuleNotFoundError: No module named 'apache_beam.rows'
```

There is no `apache_beam.rows` module in apache-beam 2.77. Use
`beam.pvalue.Row` for dynamic rows, or a registered dataclass for
schema'd ones:

```python
# WRONG — does not exist
from apache_beam.rows import Row

# RIGHT — dynamic row
from apache_beam.pvalue import Row

# RIGHT — schema'd row
from apache_beam.coders import typecoders

typecoders.registry.register_row(Order)
```

### `ModuleNotFoundError: No module named 'apache_beam.schema'`

```text
ModuleNotFoundError: No module named 'apache_beam.schema'
```

The Python SDK's schema machinery is in `apache_beam.typehints.schemas`
and `apache_beam.coders.row_coder`. `apache_beam.schema` is the Java
SDK's module name.

### `AttributeError: 'ParDo' object has no attribute 'with_output_coder'`

```text
AttributeError: 'ParDo' object has no attribute 'with_output_coder'
```

There is no `with_output_coder` in apache-beam 2.77. Use
`with_output_types` with a *type*, and control the coder by registering
one for that type:

```python
from apache_beam.coders import coders

coders.registry.register_coder(Order, OrderCoder)
orders | "Parse" >> beam.ParDo(ParseOrderFn()).with_output_types(Order)
```

### `TypeError: Type hints for a PTransform must be a non-sequence, a type, or a TypeConstraint. StrUtf8Coder is an instance of StrUtf8Coder.`

```text
TypeError: Type hints for a PTransform must be a non-sequence, a type, or a TypeConstraint.
```

You passed a coder to `with_output_types`. It wants a type.

### `AttributeError: module 'apache_beam.coders.coders' has no attribute 'registry'`

The registry lives in `apache_beam.coders.typecoders`:

```python
# WRONG
from apache_beam.coders import coders
coders.registry.register_coder(Order, OrderCoder)

# RIGHT
from apache_beam.coders import typecoders
typecoders.registry.register_coder(Order, OrderCoder)
```

### `AttributeError: 'dict' object has no attribute 'names'` on `WriteToParquet`

```text
AttributeError: 'dict' object has no attribute 'names'
```

`WriteToParquet` expects a **`pyarrow.Schema`**, not a dict and not a Beam
Row schema:

```python
import pyarrow as pa

ARROW_SCHEMA = pa.schema(
    [
        pa.field("order_id", pa.string()),
        pa.field("region", pa.string()),
        pa.field("amount", pa.float64()),
    ]
)
```

### `AttributeError: id` when constructing a `RowCoder` from a hand-built schema

```text
AttributeError: id
```

The schema proto you built is missing its `id` field. Use
`typing_to_runner_api` (for a dataclass) or
`avro_schema_to_beam_schema` (for an Avro dict) so the id is generated
for you.

### `WARNING: Using fallback coder for typehint: <class 'MyType'>`

Your custom class is being pickled. Register a coder for it, or use a
dataclass with `registry.register_row`.

### The CSV read silently dropped a column

This is the `ReadFromCsv` inference trap, not a bug in your code. If you
passed `usecols=`, the reader kept exactly the columns you named and
discarded the rest — with no error and no warning. Pin the *complete*
column set, and validate the header separately.

If you did **not** pass `usecols`, look at `dtype` instead: a `dtype`
value that does not match the data (a column of numbers pinned to `str`,
say) will make pandas raise, and a column pandas cannot parse at all will
come through as `object`. Neither case drops a column on its own.

### `ValueError: Cannot provide coder for <class 'X'>`

No coder is registered for the type and the fallback chain could not
handle it. Register one:

```python
typecoders.registry.register_coder(X, XCoder)
```

### The Parquet output has one file per key

`WriteToParquet` takes `num_shards`. Pin it to a value matched to your
output size, and partition by date if the output is large.

---

## 💡 Production Notes

- **A coder is a contract, not an implementation detail.** The moment
  your pipeline writes an intermediate file, the coder in that file is
  part of your compatibility surface. Version it deliberately.
- **`FastPrimitivesCoder` is not deterministic in 2.77.** This surprises
  people because the name suggests it is the "safe" fast path. If you
  shuffle by a value that could be encoded by it, register a
  deterministic coder for that type.
- **Never use a dict as a shuffle key without a deterministic coder.**
  Dict insertion order leaks into the encoded bytes, and two logically
  equal keys can hash to different workers.
- **Pickle is a compatibility trap.** A pickle-encoded intermediate is
  Python-only, version-locked, and non-deterministic. It is acceptable
  inside a single job where everything is in memory; it is not acceptable
  in a file that another system will read.
- **Avro is the right default for a cross-team data contract.** The
  schema travels with the data, so consumers do not need to be
  deployed in lockstep. The cost is that Avro's type system is narrower
  than Python's — no `Optional` without a union, no arbitrary nesting.
- **Parquet is the right default for analytics.** Columnar, compressed,
  and readable by every engine. Write it with `pyarrow.Schema` and read it
  with `as_rows=True` when you want the schema back.
- **BigQuery has its own schema negotiation**, and it is the one place
  where additive changes *are* handled gracefully: `WriteToBigQuery` with
  `ignore_unknown_columns=True` skips source columns the table does not
  have, and `schema_update_options` can add fields. That is a BigQuery
  feature, not a Beam one.
- **The schema is baked in at construction, not at read time.** Any
  source whose schema can drift between graph construction and bundle
  execution — a file being rewritten, a table being altered, a producer
  deploying a new version — needs either a pinned schema plus a header
  check, or an explicit per-record validation. The course project's
  `try_parse_order_line` is the model.
- **The UUID in an inferred schema name is your drift detector.** If a
  job's output type name changes between two runs, the input schema
  changed. Log `element_type` and alert on the change.
- **Registering a coder at import time is not enough on Dataflow.** The
  registration happens in the worker process. If the `DoFn` is defined in
  a module that the worker does not import, the coder is missing on the
  worker and you get the pickle fallback — or a crash. Keep the
  registration next to the class definition, in the same module the
  `DoFn` imports.
- **Beam Row schemas are content-addressed.** The schema id is derived
  from the field names and types, so an unrelated field *reordering* can
  change the id. Two pipelines that "have the same schema" but build it
  differently can end up with different ids and fail to join.

---

## 🔑 Key Takeaways

- A coder turns Python values into bytes and back. Every element that
  crosses a shuffle or a file boundary is encoded, so the coder is part of
  your pipeline's contract.
- Beam picks a coder in this order: the **registry** lookup for the
  type, the **type hint**, the fallback chain
  (`ProtoCoder → ProtoPlusCoder → FastPrimitivesCoder`), and finally the
  runtime fallback to `PickleCoder`.
- **`FastPrimitivesCoder` is not deterministic in apache-beam 2.77**,
  because its fallback is a `PickleCoder`. The standard coders
  (`StrUtf8Coder`, `VarIntCoder`, `FloatCoder`, `BytesCoder`,
  `BooleanCoder`) are.
- **`apache_beam.rows` does not exist** in this environment, and neither
  does `apache_beam.schema`. The dynamic row is `beam.pvalue.Row`; the
  schema machinery is `apache_beam.typehints.schemas` and
  `apache_beam.coders.row_coder`.
- The supported schema'd path is a dataclass plus
  `typecoders.registry.register_row(Order)`, which registers a
  deterministic `RowCoder` and a content-addressed schema.
- **`with_output_coder` does not exist** in 2.77. Use
  `with_output_types` with a type, and register a coder for that type.
- `NullableCoder` adds a one-byte null flag and inherits determinism
  from its inner coder. `Optional[X]` type hints produce one
  automatically.
- **`beam.io.ReadFromCsv` is the pandas reader in 2.77** and infers a
  schema whose type name embeds a UUID that changes with the schema. A
  pinned `usecols` **silently drops the columns it does not name** — the
  operational trap. (`dtype` only casts; it does not drop.) Validate the
  contract yourself, at the boundary.
- `beam.io.WriteToParquet` takes a **`pyarrow.Schema`**, not a dict and
  not a Beam Row schema — and the element it receives must be
  dict-like, because the writer indexes rows by column name.

---

## 📚 Practice Exercises

1. **Write a custom deterministic coder.** Implement an `OrderCoder` for
   the project's order dict that encodes the nine `ORDER_FIELDS` into a
   compact, deterministic byte string, and register it with
   `typecoders.registry.register_coder(dict, OrderCoder)` — well, for a
   dict subclass, since you cannot register a coder for the built-in
   `dict` without shadowing it globally. *Expected:* the coder round-trips
   every order in `sample_data/orders.csv`, `is_deterministic()` returns
   `True`, and the encoded bytes for two logically equal dicts with
   different key insertion orders are identical.

2. **Compare the encoded sizes.** Encode the course's order dict with
   `FastPrimitivesCoder` and with `PickleCoder`, and measure the byte
   count for 1,000 orders. *Expected:* the pickle encoding is
   substantially larger — the pickler stores the class and the dict
   machinery on first use — and the ratio is roughly 2–4× for a
   nine-field dict.

3. **Prove the determinism difference.** Encode the same `dict` with
   `PickleCoder` twice, inserting the keys in different orders, and show
   the bytes differ. Then encode with `StrUtf8Coder` and show they do
   not. *Expected:* the two pickle encodings are different byte strings
   that decode to equal dicts; the string encodings are identical.

4. **Write the same output as CSV, Avro and Parquet.** Produce three
   outputs from the same pipeline — `WriteToText` with a header,
   `WriteToAvro` with an Avro dict schema, and `WriteToParquet` with a
   `pyarrow.Schema` — and read all three back. *Expected:* the CSV is
   human-readable but has no embedded schema; the Avro file embeds its
   schema in the file header; the Parquet file embeds it in the footer.
   Explain which one you would hand to a team that will read it in Java.

5. **Add a nullable column to the schema.** Add `discount_code:
   Optional[str]` to the `Order` dataclass, re-register it, and write the
   Parquet output with the column present but null for every row.
   *Expected:* the generated schema shows `nullable: true` on that field,
   and `NullableCoder` handles the null. Then make the field non-nullable
   and confirm the schema changes accordingly.

6. **Reflection.** A nightly job reads
   `gs://bucket/orders/dt=2026-01-15/orders-*.csv` with
   `beam.io.ReadFromCsv`, infers the schema, and writes Parquet. One
   morning the producer adds a `promotion_code` column to *one* of the
   three files. Describe exactly what happens — in the Direct Runner, in
   a Dataflow batch job with 10 workers, and on a re-run the next day —
   and propose two changes to the pipeline that would make the failure
   loud instead of silent. *Expected:* the inferred type name's UUID
   changes, so the three files produce two different types; the worker
   that reads the drifted file either fails on the type mismatch or
   produces rows with a null column, depending on the runner's type
   checking; and the next day's run infers a different schema again, so
   the output schema is not stable across days. The fixes are to pin the
  schema explicitly and to validate the header of every file against it.

---

## 📖 Further Reading

- Apache Beam: Type hints and element types — https://beam.apache.org/documentation/programming-guide/#type-hints
- Apache Beam: Data encoding — https://beam.apache.org/documentation/programming-guide/#data-encoding
- Apache Beam Python API: `apache_beam.coders` — https://beam.apache.org/documentation/sdks/python/apache_beam.coders.html
- Apache Beam: Schema — https://beam.apache.org/documentation/programming-guide/#schemas
- Google Cloud Dataflow: BigQuery sinks and write dispositions — https://cloud.google.com/dataflow/docs/guides/bigquery
- Google Cloud Dataflow: Avro and Parquet formats — https://cloud.google.com/dataflow/docs/guides/avro-parquet
