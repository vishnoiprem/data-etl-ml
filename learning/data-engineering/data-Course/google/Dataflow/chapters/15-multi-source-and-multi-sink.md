# 3.2 — Multi-Source & Multi-Sink

> **Section 3 · I/O & Multi-Source Pipelines · Lecture 3.2 · 6:30**

## 🎯 What you will learn

- Reading from several sources and merging them with `beam.Flatten`
- The **tag pattern** — adding a source-name tag so downstream logic can tell the sources apart
- Why `Flatten` requires compatible types, and how to reconcile that with a tag
- Writing to several sinks from one PCollection, and what that costs
- The **read-once principle**: one source read, fanned out to many consumers
- `beam.Reshuffle` as a deliberate fusion barrier
- Branching with side outputs via tagged outputs
- Why "one read, many consumers" changes your cost model

---

## 🧠 Concept

### The shape of a multi-source pipeline

Almost every real pipeline reads more than one thing. The orders live in
GCS as Parquet; the product catalogue lives in BigQuery; a reference
table lives in a local file; corrections arrive over Pub/Sub. Then it
writes more than one thing: a summary to BigQuery, a raw extract to a
bucket, rejected records to a dead-letter topic.

The naive way to build this is to treat each source as a separate
pipeline and reconcile the results afterwards. That works until it
doesn't, because the reconciliation then happens outside the runner, on
one machine, with no windowing and no exactly-once semantics.

The Beam way is to express the whole thing as one graph. That is what
this chapter is about.

### `beam.Flatten`: merging PCollections

`Flatten` is the simplest and most useful transform in Beam:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    a = p | "A" >> beam.Create([1, 2, 3])
    b = p | "B" >> beam.Create([4, 5])
    merged = (a, b) | "Flatten" >> beam.Flatten()
```

`Flatten` takes a tuple of PCollections and produces one PCollection
containing all their elements. There is no ordering guarantee and no
deduplication: it is a concatenation in a distributed, unordered sense.

The `Flatten` transform accepts the inputs as a tuple:

```python
merged = (a, b) | "Flatten" >> beam.Flatten()
```

You can also flatten a list of PCollections, which is what you want
when the number of sources is dynamic:

```python
branches = [p | f"Read{i}" >> beam.io.ReadFromText(path) for i, path in enumerate(paths)]
merged = branches | "Flatten" >> beam.Flatten()
```

> **`Flatten` and the `pipeline=` keyword.** `Flatten` needs to know
> which pipeline owns it. It normally infers that from the input
> PCollections, but if you flatten an *empty* tuple — or a tuple whose
> members might be empty — you must pass it explicitly:
> `beam.Flatten(pipeline=p)`. The signature is `Flatten(**kwargs)`, and
> the only accepted keyword is `pipeline`.

### The type constraint

`Flatten` requires all its inputs to have the **same element type**.
This is not a stylistic preference; it is a hard constraint, because
`Flatten` produces a single PCollection, and a PCollection has one
element type and therefore one coder.

In Beam 2.77, the type checker catches a mismatch at graph-construction
time:

```text
apache_beam.typehints.decorators.TypeCheckError: Input type hint
violation at Flatten: expected Tuple[TypeVariable[K], TypeVariable[V]],
got <class 'str'>
```

The practical consequence: **if your sources have different shapes,
you must reconcile them before flattening.** This is where the tag
pattern earns its keep.

### The tag pattern

Suppose you have two sources: a CSV file of orders and a JSON file of
returns. Both are records, but they have different fields, and
downstream you need to know which is which — because a return should
subtract from revenue and an order should add to it.

The naive approach is to normalise both into one flat schema with a
`record_type` column:

```text
orders.csv   ->  {record_type: "order",  order_id: ..., amount: ...}
returns.json ->  {record_type: "return", order_id: ..., amount: ...}
```

This works, but it is fragile: every source needs a matching column,
and the column is easy to forget when you add a third source.

The **tag pattern** is the more robust alternative. Instead of making
the *record* carry the source identity, you make the *merge* carry it,
by tagging each branch with its source name before flattening:

```python
import apache_beam as beam
import apache_beam.typehints as th

with beam.Pipeline() as p:
    orders = p | "ReadOrders" >> beam.io.ReadFromText("./sample_data/orders.csv")
    returns = p | "ReadReturns" >> beam.io.ReadFromText("./sample_data/returns.csv")

    tagged_orders = orders | "TagOrders" >> beam.Map(
        lambda line: ("orders", line)
    ).with_output_types(th.Tuple[str, str])

    tagged_returns = returns | "TagReturns" >> beam.Map(
        lambda line: ("returns", line)
    ).with_output_types(th.Tuple[str, str])

    merged = (tagged_orders, tagged_returns) | "Flatten" >> beam.Flatten()
```

Now the merged PCollection has a uniform type — `(source_name, line)` —
and downstream you branch on the tag:

```python
revenue = merged | "Revenue" >> beam.Map(
    lambda tagged: compute_revenue(tagged[0], tagged[1])
)
```

The type constraint is satisfied *and* the source identity is preserved,
because the tag made both branches the same shape.

This is a Beam idiom with a name in other systems: in Spark it is
`unionByName` with a literal column; in Flink it is a side-output tag;
in Kafka Streams it is a repartition topic. Beam has no built-in
equivalent, so the pattern is done by hand — and it is worth
recognising it when you see it.

#### Reconciling heterogeneous sources

If the sources have genuinely different schemas, you have two options.

**Option A — cast to a common type before tagging.** Normalise each
source to the same record shape, then tag:

```python
def _to_order_record(line: str) -> dict:
    """Parse an order line into a common record shape."""
    parts = line.split(",")
    return {
        "order_id": parts[0],
        "region": parts[3],
        "amount": float(parts[7]),
    }


with beam.Pipeline() as p:
    orders = p | "ReadOrders" >> beam.io.ReadFromText("./sample_data/orders.csv")
    events = p | "ReadEvents" >> beam.io.ReadFromText("./sample_data/events.ndjson")

    tagged_orders = (
        orders
        | "ParseOrders" >> beam.Map(_to_order_record)
        | "TagOrders" >> beam.Map(lambda r: ("orders", r)).with_output_types(
            th.Tuple[str, th.Dict[str, th.Any]]
        )
    )

    tagged_events = (
        events
        | "ParseEvents" >> beam.Map(_to_event_record)
        | "TagEvents" >> beam.Map(lambda r: ("events", r)).with_output_types(
            th.Tuple[str, th.Dict[str, th.Any]]
        )
    )

    merged = (tagged_orders, tagged_events) | "Flatten" >> beam.Flatten()
```

Both branches now have the type `Tuple[str, Dict[str, Any]]`, so
`Flatten` is happy. Note the `.with_output_types(...)` on both tag
stages — that is what makes the two branches' types *provably*
identical rather than merely coincidentally similar. It is also what
stops the stages falling back to the pickle coder.

**Option B — keep the native types and merge into a union.** If the
shapes really are irreconcilable, and you only need to route them
differently, then you do not need a `Flatten` at all. You need a
branch, which is the next section.

#### A real example: merging the course's own data

The course's `sample_data/` directory has `orders.csv` and
`orders.ndjson` — the same orders in two formats. Merging them with a
tag is a natural exercise:

```python
import apache_beam as beam
import apache_beam.typehints as th

with beam.Pipeline() as p:
    csv_orders = p | "ReadCsv" >> beam.io.ReadFromText("./sample_data/orders.csv")
    ndjson_orders = p | "ReadNdjson" >> beam.io.ReadFromText("./sample_data/orders.ndjson")

    tagged_csv = csv_orders | "TagCsv" >> beam.Map(
        lambda line: ("csv", line)
    ).with_output_types(th.Tuple[str, str])

    tagged_ndjson = ndjson_orders | "TagNdjson" >> beam.Map(
        lambda line: ("ndjson", line)
    ).with_output_types(th.Tuple[str, str])

    merged = (tagged_csv, tagged_ndjson) | "Flatten" >> beam.Flatten()

    counts = (
        merged
        | "CountBySource" >> beam.combiners.Count.PerKey()
        | "Format" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]}")
        | "Write" >> beam.io.WriteToText("./out/source_counts", num_shards=1)
    )
```

The output is two lines — `csv,5000` and `ndjson,5000` — because the
tag made the two sources separable after the merge. Without the tag,
you would have 10,000 indistinguishable lines and no way to tell which
format each came from.

### Multi-sink: one PCollection, many outputs

A PCollection is immutable, and every consumer of it sees the same
elements. This means you can attach as many sinks as you like:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    summary = (
        p
        | "Read" >> beam.io.ReadFromText("./sample_data/orders.csv")
        | "KeyByRegion" >> beam.Map(lambda line: (line.split(",")[3], 1))
        | "CountByRegion" >> beam.combiners.Count.PerKey()
    )

    summary | "WriteCsv" >> beam.io.WriteToText("./out/summary_csv", num_shards=1)
    summary | "WriteJson" >> beam.io.WriteToText("./out/summary_json", num_shards=1)
    summary | "WriteBigQuery" >> beam.io.WriteToBigQuery(
        "YOUR_PROJECT.your_dataset.orders_by_region",
        write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
        create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
    )
```

`summary` is consumed three times. Because PCollections are immutable
and lazy, this is not "copying" the data three times — see the next
section.

### The read-once principle

This is the property that makes the whole design work, and it is worth
stating precisely.

**A PCollection is read once by the runner, and its result is fanned
out to every consumer.**

When you write `summary` into three sinks, the runner does not run the
read-and-aggregate stage three times. It runs it once, and the
downstream fork distributes the result to the three sink stages. The
job graph in the Dataflow UI shows this as a single upstream stage with
three outgoing edges.

Why this matters:

| | Without the DAG | With the DAG |
|---|---|---|
| Source read | once per branch | once |
| Parse | once per branch | once |
| Aggregation | once per branch | once |
| Storage writes | N | N (unavoidable — the sinks are external) |
| Network transfer of intermediate data | N × size | 1 × size, fanned out internally |

The savings are not in the *number* of writes — you still write to three
sinks, because that is what you asked for. The savings are in
everything *upstream* of the fork: the read, the parse, the aggregate.
If those are expensive — and a GCS read of 2 TB of Parquet is — you
pay once.

This is also why the Beam model pushes you toward "compute once, use
many" rather than "read once per output". The runner is a *graph
executor*, and a graph shares its upstream nodes.

#### The cost model this implies

Three practical consequences follow.

**1. Branching is cheap; branching at the wrong place is not.** Adding a
sink downstream of an existing branch costs a write. Adding a sink
directly on the raw source costs a re-read.

**2. The point of branch placement is to maximise sharing.** If three
outputs all need the parsed records, put the `Parse` stage *before*
the fork:

```text
                    ┌──> Sink A (raw lines)
Read ──> Parse ─────┼──> Sink B (parsed records)
                    └──> Sink C (aggregates)
```

vs.

```text
Read ──┬──> Sink A (raw lines)      [re-reads the source]
       ├──> Parse ──> Sink B
       └──> Parse ──> Sink C        [re-parses]
```

The second graph has two read stages and two parse stages. It looks
equivalent in the code, because in the code both are "apply a
transform to a PCollection". In the runner, they are not.

**3. Materialisation points are where you pay.** If two branches need
the same expensive intermediate, but the runner cannot fuse them
together (because a `GroupByKey` sits between, or because the branches
diverge in incompatible ways), the intermediate gets written to
GCS. That is a real cost, and it is why the placement of `Reshuffle`
matters.

### `beam.Reshuffle`: a deliberate fusion barrier

By default, the runner tries to **fuse** adjacent steps. `Map` followed
by `Filter` becomes one step, and the intermediate never touches disk.
Fusion is a large performance win and it is entirely automatic.

Sometimes you need to *prevent* fusion. The canonical case is a
branch where one side is cheap and the other side is a heavy
`GroupByKey`:

```text
Read ──> Parse ──┬──> Filter ──> WriteCheap      (fuses with Parse)
                  └──> GroupByKey ──> Aggregate   (needs a materialised input)
```

Beam's own documentation for `Reshuffle` describes it precisely:

> PTransform that returns a PCollection equivalent to its input, but
> operationally provides some of the side effects of a GroupByKey, in
> particular checkpointing, and preventing fusion of the surrounding
> transforms.

A `Reshuffle` adds a temporary random key to each element, groups by
it (which forces a shuffle), and removes the key. The net effect on the
data is *nothing* — the elements come out the same. The net effect on
the *graph* is significant: it is a barrier that the runner cannot fuse
across.

```python
import apache_beam as beam

with beam.Pipeline() as p:
    parsed = (
        p
        | "Read" >> beam.io.ReadFromText("./sample_data/orders.csv")
        | "Parse" >> beam.Map(lambda line: line.split(","))
    )

    # Force a checkpoint between the two branches so the heavy side does
    # not hold up the light side.
    barrier = parsed | "Reshuffle" >> beam.Reshuffle()

    barrier | "CheapBranch" >> beam.Map(lambda parts: parts[0]) | "WriteCheap" >> beam.io.WriteToText(
        "./out/ids", num_shards=1
    )

    barrier | "HeavyBranch" >> beam.Map(lambda parts: (parts[3], 1)) | "GroupByRegion" >> beam.combiners.Count.PerKey() | "WriteHeavy" >> beam.io.WriteToText(
        "./out/counts", num_shards=1
    )
```

`Reshuffle` is a tool of last resort, and you should reach for it
knowing what it costs: a full shuffle of the data, which for a large
input means a `GroupByKey`-scale network transfer and a checkpoint. On
Dataflow, that shuffle is billed at the same rate as any other shuffle
stage.

Use it when:

- one branch is on the latency-critical path and another is heavy;
- you need a checkpoint for exactly-once semantics in a streaming
  pipeline;
- you need to break a dependency cycle in the runner's fusion plan;
- you are hitting a memory problem caused by a stage being fused into
  a downstream `GroupByKey`.

Do not use it because the job graph "looks wrong". Read the graph
first.

### Branching with side outputs

There are two ways to split a PCollection, and they are not
interchangeable.

**Branch by reusing the PCollection.** The simplest approach, shown
above: apply two different transforms to the same PCollection. Each
branch sees every element.

**Branch by tagged outputs.** A `DoFn` that emits tagged outputs
*routes* elements: each element goes to exactly one output. This is
the right tool when the branches are mutually exclusive — when
"large orders" and "small orders" are disjoint.

```python
import apache_beam as beam
from apache_beam import pvalue


class SplitByAmount(beam.DoFn):
    """Route orders to one of two tagged outputs by amount."""

    def process(self, order):
        if order["amount"] >= 100.0:
            yield pvalue.TaggedOutput("large", order)
        else:
            yield pvalue.TaggedOutput("small", order)


with beam.Pipeline() as p:
    orders = p | "Read" >> beam.io.ReadFromText("./sample_data/orders.csv")

    split = orders | "SplitByAmount" >> beam.ParDo(
        SplitByAmount()
    ).with_outputs("large", "small")

    split["large"] | "FormatLarge" >> beam.Map(lambda o: f"large,{o}") | "WriteLarge" >> beam.io.WriteToText(
        "./out/large", num_shards=1
    )
    split["small"] | "FormatSmall" >> beam.Map(lambda o: f"small,{o}") | "WriteSmall" >> beam.io.WriteToText(
        "./out/small", num_shards=1
    )
```

The mechanics of `with_outputs`:

- `beam.ParDo(SplitByAmount())` returns a `ParDo`.
- `.with_outputs("large", "small")` returns a `DoOutputsTuple` — a
  `DoFnRunner`-style object that holds one PCollection per tag.
- `split["large"]` retrieves the PCollection for that tag.

Two things to get right:

**The tags must be declared.** If you call `.with_outputs("large")` but
your `DoFn` emits `"small"`, the run *succeeds* and the `"large"`
branch is silently empty. Beam 2.77 does not validate the two lists
against each other. Declare every tag you emit — and count the
elements in each branch so a silent drop is visible.

**`with_outputs` returns a tuple, not a PCollection.** It does not
support `|` directly on the whole tuple; you index into it first.

The difference between the two branching styles:

| | Reuse the PCollection | Tagged outputs |
|---|---|---|
| Element routing | every branch sees every element | each element goes to one branch |
| Cardinality | N branches × M elements | M elements total, split |
| Use when | branches are complementary views | branches are exclusive classifications |
| Cost | a copy per branch | one pass, filtered |

Note the cost difference. Reusing a PCollection for two sinks means
the data is fanned out — two copies in flight. Tagged outputs route
each element exactly once, so a 1 TB source split into 99% small and 1%
large moves 1 TB through the split, not 2 TB.

> **There is no `beam.FilterInto` in Beam 2.77.** The Python SDK does
> not expose a `FilterInto` transform, and it does not have a `beam.tee`
> function either. The Java SDK has `DoFn.withOutputTags` and
> `TestStream`; the Python SDK's equivalents are `pvalue.TaggedOutput`
> and `beam.ParDo(...).with_outputs(...)` as shown above. If you are
> porting Java snippets, translate rather than transliterate.

### Putting it together

A complete multi-source, multi-sink pipeline:

```text
        ┌──> orders.csv ──┐
        │                 ├──> Parse ──> Validate ──┐
        ├──> events.ndjson┘                          │
        │                                            ├──> Tag ──> Flatten
        └──> product_reference.ndjson ──> Side input ┘         │
                                                               │
                                    ┌──────────────────────────┼──────────────┐
                                    ▼                          ▼              ▼
                             Aggregate by region      Write summary    Write per-region
                              (CombinePerKey)          to BigQuery      to GCS
```

Every source is read once. The parse and validation happen once. The
summary is written to two sinks from one aggregation. The product
reference is a *side input*, not a branch — it is broadcast to every
worker rather than fanned out, because every worker needs all of it.

---

## 🛠️ Hands-On: Build a Multi-Source, Multi-Sink Pipeline

### Setup

```bash
cd data-engineering/data-Course/google/Dataflow
source .venv/bin/activate
python resources/sample_data.py --output-dir ./sample_data
```

### Step 1 — merge two sources with the tag pattern

Create `work/multi_source.py`:

```python
"""Merge two order sources with a source tag, then aggregate by region."""

import apache_beam as beam
import apache_beam.typehints as th

INPUTS = {
    "csv": "./sample_data/orders.csv",
    "ndjson": "./sample_data/orders.ndjson",
}


def build(pipeline):
    """Merge every source into one tagged PCollection."""
    tagged_branches = []

    for source_name, path in INPUTS.items():
        branch = (
            pipeline
            | f"Read{source_name.title()}" >> beam.io.ReadFromText(path)
            | f"SkipHeader{source_name.title()}" >> beam.Filter(
                lambda line: not line.startswith("order_id")
            )
            | f"Tag{source_name.title()}" >> beam.Map(
                lambda line, name=source_name: (name, line)
            ).with_output_types(th.Tuple[str, str])
        )
        tagged_branches.append(branch)

    return tagged_branches | "Flatten" >> beam.Flatten()


with beam.Pipeline() as p:
    merged = build(p)

    counts = (
        merged
        | "CountBySource" >> beam.combiners.Count.PerKey()
        | "FormatCounts" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]}")
        | "WriteCounts" >> beam.io.WriteToText(
            "./out/source_counts", num_shards=1, shard_name_template=""
        )
    )
```

Run it:

```bash
python work/multi_source.py
cat out/source_counts*
```

Expected output:

```text
csv,5000
ndjson,5000
```

Both sources carry the same 5,000 orders, and the tag lets you prove
it. Without the tag, the merged collection would be 10,000 anonymous
lines.

Note the `SkipHeader` filter. Without it, the CSV branch reports
`csv,5001` — because `ReadFromText` reads every line, including the
header. This is the single most common bug in a multi-source pipeline,
and it is worth noticing that *only* the CSV branch is affected. That
asymmetry is exactly what the tag pattern makes visible: with a
per-source count you can see that one source is off by one. Without
the tag, you would have 10,001 lines and no way to tell which source
the extra one came from.

### Step 2 — reconcile different shapes

The two sources above have the same shape. Now merge sources that do
not: a CSV of orders and an NDJSON of events.

Create `work/multi_shape.py`:

```python
"""Merge records of different shapes by normalising, then tagging."""

import json

import apache_beam as beam
import apache_beam.typehints as th

RECORD_TYPE = th.Tuple[str, th.Dict[str, th.Any]]


def order_to_record(line: str) -> dict:
    """Parse a CSV order line into a common record shape."""
    parts = line.split(",")
    return {
        "id": parts[0],
        "region": parts[3],
        "value": float(parts[7]),
    }


def event_to_record(line: str) -> dict:
    """Parse an NDJSON event line into a common record shape."""
    payload = json.loads(line)
    return {
        "id": payload["event_id"],
        "region": payload["region"],
        "value": float(payload["value"]),
    }


with beam.Pipeline() as p:
    orders = (
        p
        | "ReadOrders" >> beam.io.ReadFromText("./sample_data/orders.csv")
        | "SkipHeader" >> beam.Filter(lambda line: not line.startswith("order_id"))
        | "ParseOrders" >> beam.Map(order_to_record)
        | "TagOrders" >> beam.Map(
            lambda record: ("order", record)
        ).with_output_types(RECORD_TYPE)
    )

    events = (
        p
        | "ReadEvents" >> beam.io.ReadFromText("./sample_data/events.ndjson")
        | "ParseEvents" >> beam.Map(event_to_record)
        | "TagEvents" >> beam.Map(
            lambda record: ("event", record)
        ).with_output_types(RECORD_TYPE)
    )

    merged = (orders, events) | "Flatten" >> beam.Flatten()

    (
        merged
        | "TotalBySource" >> beam.Map(lambda tagged: (tagged[0], tagged[1]["value"]))
        | "SumBySource" >> beam.CombinePerKey(sum)
        | "Format" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]:.2f}")
        | "Write" >> beam.io.WriteToText(
            "./out/totals_by_source", num_shards=1, shard_name_template=""
        )
    )
```

Run it:

```bash
python work/multi_shape.py
cat out/totals_by_source*
```

Expected output:

```text
order,2396837.96
event,1196037.06
```

Two lines, two different record types, one merged PCollection. The
`.with_output_types(RECORD_TYPE)` on both tag stages is what makes this
provably type-safe — without it, the `Flatten` would rely on the two
branches happening to agree.

The `SkipHeader` filter is not optional here. Without it, the CSV
branch's `float("amount")` raises
`ValueError: could not convert string to float: 'amount'` and the job
fails. That is the *good* failure mode — a loud one. The bad failure
mode is a filter that silently drops the header and leaves you with a
count of 4,999 and no explanation.

### Step 3 — one source, three sinks

Create `work/multi_sink.py`:

```python
"""Read the orders once and write three different outputs."""

import apache_beam as beam

INPUT = "./sample_data/orders.csv"


def build(pipeline):
    """Return the aggregated per-region summary."""
    return (
        pipeline
        | "ReadOrders" >> beam.io.ReadFromText(INPUT)
        | "KeyByRegion" >> beam.Map(lambda line: (line.split(",")[3], 1))
        | "CountByRegion" >> beam.combiners.Count.PerKey()
    )


with beam.Pipeline() as p:
    summary = build(p)

    # Sink 1: a plain text listing.
    (
        summary
        | "FormatList" >> beam.Map(lambda kv: f"{kv[0]}={kv[1]}")
        | "WriteList" >> beam.io.WriteToText(
            "./out/sink_list", num_shards=1, shard_name_template=""
        )
    )

    # Sink 2: a CSV with a header.
    (
        summary
        | "FormatCsv" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]}")
        | "WriteCsv" >> beam.io.WriteToText(
            "./out/sink_csv",
            num_shards=1,
            shard_name_template="",
            header="region,count",
        )
    )

    # Sink 3: a JSON-per-line dump, for a downstream system that
    # prefers JSON.
    (
        summary
        | "FormatJson" >> beam.Map(
            lambda kv: '{"region": "%s", "count": %d}' % (kv[0], kv[1])
        )
        | "WriteJson" >> beam.io.WriteToText(
            "./out/sink_json", num_shards=1, shard_name_template=""
        )
    )
```

Run it:

```bash
python work/multi_sink.py
echo "--- list"
cat out/sink_list*
echo "--- csv"
cat out/sink_csv*
echo "--- json"
cat out/sink_json*
```

Expected output:

```text
--- list
LATAM=1265
APAC=1211
AMER=1284
EMEA=1240
region=1
--- csv
region,count
LATAM,1265
APAC,1211
AMER,1284
EMEA,1240
region,1
--- json
{"region": "LATAM", "count": 1265}
{"region": "APAC", "count": 1211}
{"region": "AMER", "count": 1284}
{"region": "EMEA", "count": 1240}
{"region": "region", "count": 1}
```

The order of the rows varies between runs — Beam makes no ordering
guarantee — but the counts are stable, because
`resources/sample_data.py` is seeded.

The `region=1` row is the header line, caught by the same
`KeyByRegion` step that caught every data row. It is a reminder that
`ReadFromText` reads every line, and that a multi-source pipeline is
where header handling tends to be forgotten. Filter it out:

```text
| "SkipHeader" >> beam.Filter(lambda line: not line.startswith("order_id"))
```

Now the point of the exercise — **the source was read once**. Three
sinks, one read stage, one aggregation stage. In the Dataflow job
graph this appears as a single upstream chain with three outgoing
edges, not three parallel copies of the read.

### Step 4 — branch with tagged outputs

Create `work/side_outputs.py`:

```python
"""Route orders into two disjoint branches using tagged outputs."""

import apache_beam as beam
from apache_beam import pvalue


class SplitByAmount(beam.DoFn):
    """Route each order to exactly one of two tagged outputs."""

    def process(self, order):
        if order["amount"] >= 500.0:
            yield pvalue.TaggedOutput("large", order)
        else:
            yield pvalue.TaggedOutput("small", order)


with beam.Pipeline() as p:
    orders = (
        p
        | "ReadOrders" >> beam.io.ReadFromText("./sample_data/orders.csv")
        | "SkipHeader" >> beam.Filter(lambda line: not line.startswith("order_id"))
        | "ParseOrders" >> beam.Map(
            lambda line: {"amount": float(line.split(",")[7])}
        )
    )

    split = orders | "SplitByAmount" >> beam.ParDo(
        SplitByAmount()
    ).with_outputs("large", "small")

    (
        split["large"]
        | "FormatLarge" >> beam.Map(lambda o: "large")
        | "WriteLarge" >> beam.io.WriteToText(
            "./out/large_orders", num_shards=1, shard_name_template=""
        )
    )

    (
        split["small"]
        | "FormatSmall" >> beam.Map(lambda o: "small")
        | "WriteSmall" >> beam.io.WriteToText(
            "./out/small_orders", num_shards=1, shard_name_template=""
        )
    )
```

Run it:

```bash
python work/side_outputs.py
echo "large: $(wc -l < $(ls out/large_orders*))"
echo "small: $(wc -l < $(ls out/small_orders*))"
```

Expected output:

```text
large:     2399
small:     2601
```

The two counts sum to exactly 5,000 — every order went to exactly one
branch, and none was counted twice. The split is roughly even because
`resources/sample_data.py` generates amounts from a uniform
distribution over 5–950, so about half land above the 500 threshold.

The `SkipHeader` filter matters here: without it, `float("amount")`
raises `ValueError: could not convert string to float: 'amount'` and
the job fails.

The key property: **each element went to exactly one branch**. The
source was read once, and the data was not duplicated.

### Step 5 — a fusion barrier with `Reshuffle`

Create `work/reshuffle_barrier.py`:

```python
"""Use Reshuffle to break fusion between a branch and a heavy stage."""

import apache_beam as beam

INPUT = "./sample_data/orders.csv"


def build(pipeline):
    """Return the parsed orders, after a reshuffle barrier."""
    parsed = (
        pipeline
        | "ReadOrders" >> beam.io.ReadFromText(INPUT)
        | "SkipHeader" >> beam.Filter(lambda line: not line.startswith("order_id"))
        | "Parse" >> beam.Map(lambda line: line.split(","))
    )

    # The barrier: the data is unchanged, but the runner can no longer
    # fuse the two branches below into the parse stage.
    return parsed | "Reshuffle" >> beam.Reshuffle()


with beam.Pipeline() as p:
    parsed = build(p)

    # Cheap branch: just the order ids.
    (
        parsed
        | "TakeId" >> beam.Map(lambda parts: parts[0])
        | "WriteIds" >> beam.io.WriteToText(
            "./out/order_ids", num_shards=1, shard_name_template=""
        )
    )

    # Heavy branch: a full aggregation.
    (
        parsed
        | "KeyByRegion" >> beam.Map(lambda parts: (parts[3], 1))
        | "CountByRegion" >> beam.combiners.Count.PerKey()
        | "FormatCounts" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]}")
        | "WriteCounts" >> beam.io.WriteToText(
            "./out/region_counts", num_shards=1, shard_name_template=""
        )
    )
```

Run it:

```bash
python work/reshuffle_barrier.py
cat out/order_ids* | head -3
cat out/region_counts*
```

Expected output:

```text
o00000000
o00000001
o00000002
LATAM,1265
APAC,1211
AMER,1284
EMEA,1240
```

The data is unchanged by the `Reshuffle` — same 5,000 ids, same four
regions, same counts as the unbarriered version. What changed is the
graph: the runner now has a checkpoint between the parse and the two
branches.

### Step 6 — verify the read-once property in the graph

Create `work/graph_shape.py`:

```python
"""Print the pipeline graph so you can see the fork."""

import apache_beam as beam

INPUT = "./sample_data/orders.csv"


def show_graph(pipeline):
    """Print each step of the pipeline graph."""
    for applied in pipeline.transforms_stack:
        for part in applied.parts:
            print(f"  {part.full_label} | {type(part.transform).__name__}")


with beam.Pipeline() as p:
    summary = (
        p
        | "ReadOrders" >> beam.io.ReadFromText(INPUT)
        | "KeyByRegion" >> beam.Map(lambda line: (line.split(",")[3], 1))
        | "CountByRegion" >> beam.combiners.Count.PerKey()
    )

    summary | "WriteA" >> beam.io.WriteToText("./out/graph_a", num_shards=1)
    summary | "WriteB" >> beam.io.WriteToText("./out/graph_b", num_shards=1)
    summary | "WriteC" >> beam.io.WriteToText("./out/graph_c", num_shards=1)

    print("--- pipeline graph ---")
    show_graph(p)
```

Run it:

```bash
python work/graph_shape.py
```

Expected output:

```text
--- pipeline graph ---
  ReadOrders | ReadFromText
  KeyByRegion | ParDo
  CountByRegion | PerKey
  WriteA | WriteToText
  WriteB | WriteToText
  WriteC | WriteToText
```

`ReadOrders`, `KeyByRegion` and `CountByRegion` each appear **once**,
and the three write steps hang off the end. The runner executes that
single upstream chain and fans the result out to the three sinks. If
you had written three separate read stages instead, `ReadOrders` would
appear three times in this list — and the job would cost three times
as much to run.

> **On printing the pipeline object.** `print(pipeline)` used to render
> a readable step list in older Beam versions. In Beam 2.77 the
> `Pipeline.__repr__` is the default object repr —
> `<apache_beam.pipeline.Pipeline object at 0x...>` — and shows you
> nothing. The `transforms_stack` walk above is the replacement, and
> it gives you more: the transform *class* as well as the label, so
> you can see that `KeyByRegion` is a `ParDo` (a `Map` compiles down to
> a `ParDo`) and that `CountByRegion` is a `PerKey` (a
> `CombinePerKey` compiles down to a per-key combiner).

On Dataflow, this same structure is visible in the job graph as one
`ReadOrders` step with three outgoing edges.

---

## 🛠️ Common Errors and Fixes

### `apache_beam.typehints.decorators.TypeCheckError: Input type hint violation at Flatten: expected Tuple[TypeVariable[K], TypeVariable[V]], got <class 'str'>`

Your branches have different element types. `Flatten` requires them to
match. Reconcile the shapes — normalise both branches to a common
record — and then tag them, as in step 2 of the hands-on.

If you only need to *route* rather than *merge*, use tagged outputs
instead of `Flatten`; they have no such constraint.

### `TypeError: 'PCollection' object is not subscriptable`

You tried to index the result of `beam.ParDo(...)` directly. You need
`with_outputs` first:

```python
# Wrong
split = p | "SplitNoOutputs" >> beam.ParDo(SplitFn())
big = split["big"]

# Right
split = p | "SplitWithOutputs" >> beam.ParDo(SplitFn()).with_outputs("big", "small")
big = split["big"]
```

`with_outputs` returns a `DoOutputsTuple`, and only that type supports
`[]`.

### A tagged output that is never emitted produces an *empty* PCollection — silently

This is not an error, and that is what makes it dangerous. If your
`DoFn` emits `"big"` but you declared `.with_outputs("large", "small")`,
the pipeline runs successfully and `split["large"]` is simply empty:

```python
split = rows | "Split" >> beam.ParDo(SplitFn()).with_outputs("large", "small")
split["large"] | "Write" >> beam.io.WriteToText("./out/large", num_shards=1)
# -> writes an empty file. No error, no warning.
```

Beam 2.77 does not validate that the declared tags and the emitted tags
match. The consequence is a pipeline that looks healthy, produces
output, and quietly drops every record.

**Always assert the counts.** The cheapest defence is to count the
elements in each branch and fail loudly if a count is implausible:

```python
counts = (
    split["large"]
    | "CountLarge" >> beam.combiners.Count.PerKey()
    | "WriteCounts" >> beam.io.WriteToText("./out/branch_counts", num_shards=1)
)
```

A branch that should hold 2,399 records and holds zero is now visible
in the output rather than inferred from a missing report.

### `ValueError: Output tags must be specified for Beam ParDo.`

You used `beam.ParDo(...)` with a `DoFn` that emits tagged outputs, but
forgot to call `.with_outputs(...)`. The tags in `with_outputs` and the
tags in `pvalue.TaggedOutput(...)` must match exactly.

```python
# These must agree:
split = rows | "Split" >> beam.ParDo(SplitFn()).with_outputs("large", "small")

# in SplitFn.process:
yield pvalue.TaggedOutput("large", order)     # declared
yield pvalue.TaggedOutput("small", order)     # declared
```

### `RuntimeError: Transform name is already used`

Two transforms in the same pipeline share a label. In a multi-source
pipeline this is easy to hit, because the natural pattern is to build
the same stage in a loop:

```python
# Wrong: every branch is labelled "Read".
for path in paths:
    p | "Read" >> beam.io.ReadFromText(path)

# Right: make the label unique.
for i, path in enumerate(paths):
    p | f"Read{i}" >> beam.io.ReadFromText(path)
```

The course linter finds this statically:

```bash
python resources/audit_course.py
```

### `ValueError: "Flatten" requires a pipeline to be specified as there are no deferred inputs.`

`Flatten` with an empty tuple has no PCollection to infer the pipeline
from. Pass the pipeline explicitly:

```python
merged = () | "Flatten" >> beam.Flatten(pipeline=p)
```

This is worth remembering because it is the shape you hit when a
multi-source pipeline's source list turns out to be empty at graph
build time — for example when the list is built from a glob that
matched nothing. The `pipeline=` keyword is the documented escape
hatch, and it works.

### `TypeError: Returning a dict from a ParDo or FlatMap is not allowed. Please use list({'k': 'a,b'}) if you really want this behavior.`

A `DoFn.process` *returned* a dict instead of yielding it. Change
`return {...}` to `yield {...}`. The error's suggestion to use
`list({...})` is wrong for your case — you want to yield the dict as a
single element, not wrap it in a list.

### `TypeError: int() got an unexpected keyword argument 'coder'`

You passed `coder=` to `beam.Map` or `beam.ParDo`. Those forward
unknown keywords to your callable. Use
`.with_output_types(...)` instead. Chapter 3.1 covers this in detail.

### The merged output has the wrong counts

Check three things, in order:

1. **Headers.** `ReadFromText` reads every line, including the header.
   Filter it: `beam.Filter(lambda line: not line.startswith("order_id"))`.
2. **Duplicate sources.** If two paths point at the same data (a `.csv`
   and its `.ndjson` twin, say), you have double-counted. That is not a
   bug in the merge — it is a bug in the input list.
3. **The tag is on the wrong element.** If you tag *after* aggregating,
   the tag describes the group, not the source. Tag before merging.

### `AttributeError: module 'apache_beam' has no attribute 'tee'`

There is no `beam.tee` in Beam 2.77. The Python SDK has no `tee`
function. For one-to-many branching, use the two techniques in this
chapter: reuse the PCollection (broadcast) or use tagged outputs
(routing).

---

## 💡 Production Notes

- **Branch as late as possible.** The whole point of the DAG is that the
  shared prefix runs once. If two outputs need the same parsed records,
  put the parse before the fork. This is the single highest-leverage
  structural decision in a multi-sink pipeline.
- **A `Flatten` is a union, not a join.** It concatenates elements; it
  does not match them up. If you need to combine two sources *per key*,
  you want `beam.CoGroupByKey`, which the course's
  `streaming_pipeline.py` already uses.
- **Tag at the branch point, not inside the record.** A tag column in
  the data means every downstream consumer has to know about it. A tag
  on the merge is invisible to consumers that do not care.
- **`Reshuffle` is a shuffle with a price tag.** It costs a full
  network shuffle and a checkpoint. Use it when a latency-critical
  branch is being held up by a heavy sibling, not as a default
  "let me separate these" tool.
- **Tagged outputs halve the data movement when the branches are
  exclusive.** Routing 1 TB into 99%/1% branches moves 1 TB, not 2 TB.
  If your branches are a classification rather than a view, tagged
  outputs are strictly better than branching.
- **Watch for the header line in every branch.** A multi-source
  pipeline is where `skip_header_lines` gets forgotten. `ReadFromText`
  has a `skip_header_lines` parameter, but if you read several files
  with different headers you will need an explicit filter.
- **Side inputs are broadcast, not fanned out.** A small reference
  table should be a side input (`beam.pvalue.AsIter`), which every
  worker gets a copy of. If you merge a reference table into the main
  stream and then filter it back out, you have paid to move it once
  per record.
- **On Dataflow, the fork is visible in the job graph.** A single
  upstream step with three edges is the shape you want. If you see
  three separate `ReadOrders` steps, you have accidentally written
  three pipelines and merged the results at the end — and you are
  paying three times the read cost.
- **Multi-source pipelines multiply the data-quality surface.** Each
  source has its own encoding, its own null convention, its own
  timezone. Validate each branch *before* the merge, so a bad record
  is rejected where it can be attributed to a source.
- **A tagged output that is never emitted is silently empty.** Beam
  2.77 does not validate declared tags against emitted tags. Count the
  elements in every tagged branch and alert on an implausible count —
  a branch that drops to zero is otherwise invisible.
- **A `Flatten` of sources with different headers will double-count.**
  If one source has a header line and another does not, the tagged
  counts will show it — which is exactly why the tag pattern is worth
  the extra `Map`.

---

## 🔑 Key Takeaways

- `beam.Flatten` merges PCollections into one, but requires **identical
  element types** — the type checker enforces this at graph build time.
- The **tag pattern** reconciles heterogeneous sources: normalise each
  branch to a common shape, tag it with its source name, then flatten.
  The result is uniform *and* attributable.
- `.with_output_types(...)` on every branch is what makes a `Flatten`
  provably type-safe, and it also stops the branch falling back to
  pickle.
- A PCollection is **read once and fanned out**. Three sinks off one
  aggregation is one read, one parse, one aggregate — three writes.
- **Branch placement is the cost model.** Sharing an expensive
  upstream stage is free; duplicating it is not.
- `beam.Reshuffle` is a **fusion barrier**: it changes the graph, not
  the data, at the price of a shuffle and a checkpoint.
- **Tagged outputs route; reusing a PCollection broadcasts.** Use
  tagged outputs for exclusive classifications, reuse for
  complementary views.
- There is **no `beam.tee` and no `beam.FilterInto`** in Beam 2.77.
  The Python equivalents are `pvalue.TaggedOutput` and
  `.with_outputs(...)`.

---

## 📚 Practice Exercises

1. **Merge and attribute.** Merge `sample_data/orders.csv` and
   `sample_data/events.ndjson` into one tagged PCollection, then produce
   a per-region count broken down by source. *Expected answer:* four
   regions × two sources = eight rows, using a
   `Tuple[str, str]` key of `(region, source)`.

2. **Move the fork.** Take your pipeline from exercise 1 and move the
   `Flatten` to *after* the per-region aggregation, tagging the
   aggregate instead of the record. Compare the two graphs (print `p`)
   and explain which one re-reads the source. *Expected answer:* the
   first graph reads each source once; the second needs the tag applied
   before the merge, so the source identity is lost unless you carry it
   through the key.

3. **Add a third sink without a second read.** Extend step 3 of the
   hands-on with a third output — a Parquet file, using
   `parquetio.WriteToParquet` with a `pyarrow` schema — and confirm
   from the printed graph that the read stage still appears only once.

4. **Exclusive routing at scale.** Rewrite the exercise-1 pipeline so
   that orders above 500 in value go to a `"premium"` branch and
   everything else to `"standard"`, using tagged outputs rather than a
   `Flatten`. Report the two counts and confirm they sum to 5,000 after
   the header is filtered out. *Expected answer:* 1 premium, 4,999
   standard.

5. **Break the fusion deliberately.** Put a `Reshuffle` between your
   parse stage and your aggregation, and between your parse stage and a
   cheap filter branch. Print the graph before and after and describe
   what the runner can no longer do. *Expected answer:* the runner can
   no longer fuse the parse into either branch; a checkpoint and a
   shuffle are introduced.

6. **Reflection.** Your team wants one pipeline to serve both a
   nightly Parquet export and a live dashboard. The export needs the
   full order records; the dashboard needs a running per-region total.
   Where do you put the fork, and what is the cost of each choice?
   *Expected answer:* fork after the parse and validate, so both
   branches share one read. The dashboard branch adds a
   `GroupByKey`; the export branch adds a `WriteToParquet`. For a live
   dashboard you would run this as a streaming pipeline, and the export
   branch would need a windowed trigger rather than a batch close.

---

## 📖 Further Reading

- Apache Beam: Multiple Inputs and Outputs — https://beam.apache.org/documentation/programming-guide/#multiple-inputs-and-outputs
- Apache Beam: Combining pipeline data — https://beam.apache.org/documentation/programming-guide/#combining-pipeline-data
- Beam Python SDK API — `apache_beam.transforms.core.Flatten` — https://beam.apache.org/releases/pydoc/current/apache_beam.transforms.core.Flatten.html
- Beam Python SDK API — `apache_beam.transforms.core.Reshuffle` — https://beam.apache.org/releases/pydoc/current/apache_beam.transforms.core.Reshuffle.html
- Beam Python SDK API — `apache_beam.pvalue` (tagged outputs) — https://beam.apache.org/releases/pydoc/current/apache_beam.pvalue.html
- Google Cloud Dataflow: Optimizing pipelines — https://cloud.google.com/dataflow/docs/optimize-pipelines
