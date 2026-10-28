# 2.8 — CoGroupByKey & GroupByKey

> **Section 2 · SDK & Core Transforms · Lecture 2.8 · 6:30**

## 🎯 What you will learn

- `beam.GroupByKey` in depth: the output shape, why it must be near the
  sink, and what it costs
- Why `GroupByKey.ResultIterable` / `GBKResult` **do not exist** in
  apache-beam 2.77, and what to use instead
- `beam.CoGroupByKey`: the input shape, the output shape, and the tags
- The Beam equivalent of a SQL FULL OUTER JOIN
- How `CoGroupByKey` avoids a round-trip through BigQuery
- Why `beam.Reshuffle` after `CoGroupByKey` is the skew fix
- The "join two keyed streams" pattern
- When `CoGroupByKey` is the wrong tool — the cartesian product case
- Hands-on: merge a per-region count stream and a per-region sum stream,
  and prove the result matches a single `CombinePerKey`

---

## 🧠 Concept

### `GroupByKey` in depth

We have met `GroupByKey` in chapter 2.7. Let us now be precise about its
contract, because the details are what make it usable in production.

**Input shape:** a PCollection of `(key, value)` tuples.

**Output shape:** a PCollection of `(key, iterable_of_values)` tuples.

```python
import apache_beam as beam

with beam.Pipeline() as p:
    kv = p | "Create" >> beam.Create(
        [("a", 1), ("a", 2), ("b", 3)]
    )

    (
        kv
        | "Group" >> beam.GroupByKey()
        | "Print" >> beam.Map(print)
    )
```

Output:

```text
('a', <iterable containing 1, 2>)
('b', <iterable containing 3>)
```

Three properties of the output that matter:

**1. The value is an iterable, not a list.** The concrete type depends on
the runner. On the Direct Runner it is a list; on Dataflow it is a
`GroupByKey.ResultIterable` or a similar lazy wrapper whose contents are
only materialised as you iterate. **You must not assume it is a list.** Code
like `kv[1].append(x)` or `kv[1][0]` is wrong in general, and
`kv[1].sort()` is wrong because `ResultIterable` has no `sort`.

The portable way to consume it is to iterate:

```text
| "Group" >> beam.GroupByKey()
| "Count" >> beam.Map(lambda kv: (kv[0], len(list(kv[1]))))
```

`list(...)` materialises it deliberately, at a point where you have decided
that materialising is acceptable.

**2. There is no `GroupByKey.ResultIterable` and no `GBKResult` in the
Python SDK.** These are Java SDK types, and the Python SDK does not expose
them. You can verify:

```bash
python -c "
import apache_beam as beam
print(hasattr(beam.GroupByKey, 'ResultIterable'))
"
# False
```

The Python SDK's `GroupByKey` class has no `ResultIterable` attribute at
all. What it does have is a nested `ReifyWindows` `DoFn` and the standard
`PTransform` surface. If you are porting Java Beam code, this is the
difference you will hit first.

**3. The grouping is per-window.** If the input has been windowed, the
group is per `(key, window)` pair. The output element's window is the
union of the input windows for that key in that group.

### Why `GroupByKey` must be the last step before a sink

`GroupByKey` produces an iterable that the *consumer* has to iterate. That
iteration happens wherever the downstream transform lives — which, in a
distributed pipeline, is wherever the runner decides to put that transform.

This creates a serious problem if you put a `GroupByKey` in the middle of a
pipeline:

```text
GroupByKey → Map → Sink
```

The `Map` after the `GroupByKey` will iterate the group. If the group is
large, that `Map` step needs a lot of memory — and it runs on whatever
worker the group landed on. The group was already the bottleneck (one key,
one worker), and now the work on it is also on that one worker.

The rule is:

> **A `GroupByKey` should be immediately before a sink, or immediately
> before a transform that reduces the group to a small value.**

Good:

```text
GroupByKey → Map(len) → sink            # reduces to an int
GroupByKey → Map(aggregate) → sink      # reduces to a summary
GroupByKey → sink                       # writes the group as-is
```

Bad:

```text
GroupByKey → FlatMap(explode) → Map(enrich) → Map(validate) → sink
```

The `FlatMap` explodes the group back into individual elements — you have
paid for a full shuffle and materialised the group, and then thrown the
grouping away.

This is exactly why `CombinePerKey` exists. If what you want is a
reduction, `CombinePerKey` reduces *during* the shuffle and never
materialises the group.

### The memory cost of `GroupByKey`

Let us put numbers on it.

Suppose 10^9 elements across 10^5 keys — 10,000 elements per key on
average. `GroupByKey` materialises each group: 10,000 values in memory on
one worker. If the values are 100-byte dicts, that is 1 MB per group. Fine.

Now suppose a skewed distribution: 5% of the keys hold 50% of the elements.
One key holds 5 million elements. At 100 bytes each, that is 500 MB — over
the default Dataflow worker heap of 2 GB when you add the Python object
overhead (a dict with nine string keys is roughly 1 KB in CPython, not
100 bytes). 5 million × 1 KB is 5 GB. **That worker OOMs.**

The same pipeline with `CombinePerKey(RevenueByRegionFn())` moves a dict
with two float keys per group. 5 million elements reduce to one dict.

| | `GroupByKey` | `CombinePerKey` |
|---|---|---|
| Shuffle payload | every value | one accumulator per key |
| Peak memory per worker | the largest group | one accumulator |
| 5M-element group, 1 KB values | ~5 GB | ~200 bytes |
| Suitable for | small groups, or a final write | everything |

The honest summary: **`GroupByKey` is a formatting step, not an
aggregation step.** Use it when you need to write a group as a group, or
when you need every value for a reason the combiner cannot express (a
median, a full sort, a deduplicated set). Otherwise, use a combiner.

### `beam.CoGroupByKey`

`CoGroupByKey` is the Beam primitive for joining several keyed streams.

**Input shape:** a dictionary (or a tuple) of PCollections.

**Output shape:** `(key, {tag: iterable_of_values})`.

```python
import apache_beam as beam

with beam.Pipeline() as p:
    counts = p | "CreateCounts" >> beam.Create([("EMEA", 3), ("AMER", 1)])
    sums = p | "CreateSums" >> beam.Create([("EMEA", 100.0), ("APAC", 50.0)])

    joined = {"counts": counts, "sums": sums} | "Join" >> beam.CoGroupByKey()

    (
        joined
        | "Print" >> beam.Map(print)
    )
```

Output:

```text
('AMER', {'counts': [1], 'sums': []})
('APAC', {'counts': [], 'sums': [50.0]})
('EMEA', {'counts': [3], 'sums': [100.0]})
```

Note carefully what this output tells you:

- `AMER` appears because it is in `counts` only. Its `sums` entry is an
  **empty iterable**, not missing.
- `APAC` appears because it is in `sums` only. Its `counts` entry is an
  **empty iterable**.
- `EMEA` appears in both.

**Every key from every input appears in the output**, with an empty
iterable for the inputs in which it does not appear. That is exactly the
semantics of a **SQL FULL OUTER JOIN**.

```sql
SELECT c.region, c.count, s.revenue
FROM counts c
FULL OUTER JOIN sums s ON c.region = s.region;
```

### The tag mechanics

`CoGroupByKey` accepts either a dictionary or a tuple of PCollections.

**Dictionary form (with named tags):** the output's inner dict is keyed by
your tag strings.

```python
joined = {"counts": counts, "sums": sums} | "Join" >> beam.CoGroupByKey()
# → (key, {"counts": [...], "sums": [...]})
```

**Tuple form (positional):** the output's inner value is a *tuple* of
iterables, indexed positionally.

```python
joined = (counts, sums) | "Join" >> beam.CoGroupByKey()
# → (key, ([...], [...]))
```

Use the dictionary form. The positional form is positional-only for a
reason: the moment you add a third input, you have to remember which
position is which. Named tags are self-documenting, and Beam restores them
for you.

**There is a subtlety with tag length.** Looking at the Beam source, tags
that are all strings shorter than 10 characters are passed through the
pipeline as data. Longer tags, or non-string tags, are replaced with
generated indices and restored by a `RestoreTags` step:

```python
if all(isinstance(tag, str) and len(tag) < 10 for tag in tags):
    # Pass the tags as data.
    pcolls_dict = pcolls
    restore_tags = None
else:
    # Pass the tags in the restore_tags closure.
    ...
```

The practical consequence is benign — the output is the same either way —
but it means a long tag adds a `Map` step to the graph. Keep tags short
and you avoid the extra stage.

**Non-string tags** work too. `CoGroupByKey` accepts arbitrary hashable
tags:

```python
joined = {1: counts, 2: sums} | "Join" >> beam.CoGroupByKey()
# → (key, {1: [...], 2: [...]})
```

The output type is `Dict[Union[key_types], Union[Iterable[value_types]]]`.

### `CoGroupByKey` as a FULL OUTER JOIN

The join pattern is: key both streams by the join key, `CoGroupByKey` them,
then decide, per key, what to do.

```python
import apache_beam as beam


def full_outer_join(joined):
    """Turn a CoGroupByKey result into joined rows, including unmatched keys."""
    key, groups = joined
    left = list(groups.get("left", []))
    right = list(groups.get("right", []))
    if not left and not right:
        return
    if not left:
        for r in right:
            yield (key, None, r)
        return
    if not right:
        for l in left:
            yield (key, l, None)
        return
    for l in left:
        for r in right:
            yield (key, l, r)
```

This is a full outer join. But look at the inner loop: `for l in left:
for r in right` — it is a **cartesian product** within each key. If a key
has 1,000 values on the left and 1,000 on the right, you emit 1,000,000
rows.

**This is the important limitation.** `CoGroupByKey` does the *grouping*;
it does not do the *matching*. It is the SQL `FULL OUTER JOIN ... ON
key = key` with the match condition already satisfied by the grouping. Any
further predicate — `ON left.id = right.id` where `id` is not the grouping
key — is a cartesian product you must filter yourself, and that filter
runs *after* the shuffle.

### The "join two keyed streams" pattern

The idiomatic use of `CoGroupByKey` is not a general-purpose join. It is
**merging two streams that have already been aggregated**, where the join
key *is* the complete join condition.

The canonical example: you have a per-region count from one pipeline and a
per-region revenue from another, and you want them side by side.

```text
orders  ──▶ CombinePerKey(count)  ──┐
                                     ├──▶ CoGroupByKey ──▶ join rows
orders  ──▶ CombinePerKey(revenue) ──┘
```

This is safe because both inputs have at most one row per key. The
cartesian product is 1×1.

When is a general join safe?

| Situation | Safe? | Why |
|---|---|---|
| Both sides aggregated to one row per key | **Yes** | product is 1×1 |
| Join key is a unique identifier on both sides | **Yes** | product is 1×1 |
| One side is a small dimension table | **Yes**, with care | product is n×1 per key |
| Both sides have many rows per key | **No** | cartesian product, filter after the shuffle |
| Join is not on a key at all | **No** | `CoGroupByKey` is the wrong tool entirely |

### When `CoGroupByKey` is the wrong tool

Three cases, in increasing order of how wrong it is.

**1. The join is not on a key — a cartesian product.**

If you want every order paired with every customer, or every product
cross-referenced with every region, you do not need a join at all. You
need a `FlatMap` that generates the cross product:

```python
# A cartesian product of two lists.
regions = p | "CreateRegions" >> beam.Create(["EMEA", "AMER"])
products = p | "CreateProducts" >> beam.Create(["p1", "p2"])

(
    regions
    | "CrossJoin" >> beam.FlatMap(
        lambda r: [(r, p) for p in ["p1", "p2"]]
    )
)
```

Using `CoGroupByKey` for this would be wrong twice over: you would have to
key by a constant to make every element land in the same group, and then
you would materialise the entire product in one worker. A hot key with
everything in it is the classic way to OOM a Dataflow job.

**2. The join key is not the complete join condition.**

If you need `ON left.region = right.region AND left.date = right.date`,
then key by the *pair* `(region, date)`. The grouping key must capture
the entire equality condition, because after the shuffle there is nothing
left to join on.

```python
# Correct: the full join condition is in the key.
keyed_left = left | "KeyLeft" >> beam.Map(lambda r: ((r["region"], r["date"]), r))
keyed_right = right | "KeyRight" >> beam.Map(lambda r: ((r["region"], r["date"]), r))
joined = {"left": keyed_left, "right": keyed_right} | "Join" >> beam.CoGroupByKey()
```

**3. One side is large.**

`CoGroupByKey` materialises the group on the worker that owns the key. If
one side has millions of rows per key, you have the same memory problem
`GroupByKey` has. The fix is the same: aggregate first, join after.

**4. You want to join to a table in a database.**

This is the case where `CoGroupByKey` is *better* than the obvious
alternative — see below.

### How `CoGroupByKey` avoids a round-trip through BigQuery

The obvious way to join a streaming stream to a BigQuery table is to
export the stream to BigQuery and run a SQL join. That works, but it costs
you a lot:

- The streaming insert pipeline is already running; adding a second sink
  doubles the BigQuery write cost.
- BigQuery streaming inserts cost roughly $0.01/GB of streamed data in
  insert-time and $0.01/GB for the storage, plus the query cost.
- The join query runs continuously, even when nothing has changed.
- You add latency: the data must land in BigQuery, then be queried, then
  the result must land somewhere else.
- You add a failure mode: a BigQuery quota error now fails your streaming
  pipeline.

`CoGroupByKey` keeps the join inside the Beam pipeline:

```text
                     ┌──▶ CombinePerKey ──┐
stream ──▶ parse ────┤                    ├──▶ CoGroupByKey ──▶ sink
                     └──▶ CombinePerKey ──┘
```

The dimension table is read once (as a side input or a small PCollection),
keyed, and joined in the same shuffle. There is no intermediate BigQuery
table, no continuous query, and no extra latency.

The practical recipe for joining a stream to a BigQuery dimension table
without a round trip:

```python
with beam.Pipeline() as p:
    # Read the dimension table once. It is small, so a side input is fine.
    dimension = (
        p
        | "ReadDimension" >> beam.io.ReadFromBigQuery(
            table="my-project.my_dataset.products",
            query="SELECT product_id, category FROM products",
        )
        | "KeyDimension" >> beam.Map(lambda r: (r["product_id"], r["category"]))
    )

    # Join the stream against it.
    enriched = (
        orders
        | "KeyOrders" >> beam.Map(lambda o: (o["product_id"], o))
        | "Join" >> beam.CoGroupByKey(
            {"orders": keyed_orders, "dimension": dimension}
        )
    )
```

With this approach there is no BigQuery *write* at all — just one read at
pipeline start. For a dimension table of 50,000 rows and a stream of 10
million events per hour, the round-trip approach costs roughly $10/hour
in insert charges alone (at $0.01/GB and roughly 2 GB/hour of streamed
events), plus the continuous query. The in-pipeline join costs one table
read.

The trade-off: the dimension table must be small enough to fit in memory on
each worker. Above roughly 50,000 rows, use a keyed side input
(`pvalue.AsDict`) or accept a BigQuery lookup per batch.

### `Reshuffle` after `CoGroupByKey`

`CoGroupByKey` produces, for each key, a dict of iterables. The output is
key-ordered, and the downstream work is "process each group".

If one key is hot — say `EMEA` holds 40% of the rows — the worker that owns
`EMEA` does all the work for that key while other workers idle. This is
skew, and it is the dominant failure mode of `CoGroupByKey` and
`GroupByKey` alike.

`beam.Reshuffle` after the join spreads the *groups* across workers:

```python
joined = {"counts": counts, "sums": sums} | "Join" >> beam.CoGroupByKey()

# Spread the grouped output so downstream work is balanced.
spread = joined | "Reshuffle" >> beam.Reshuffle()
```

Why it works: `Reshuffle` re-partitions the output by hashing the key, so
each key's group lands on a worker chosen by the hash — not by whatever
worker happened to own the key in the join's shuffle. With enough workers,
the work spreads.

The caveat: `Reshuffle` does not split a single hot group. If `EMEA` has
40 million values, `Reshuffle` still puts all 40 million on one worker.
To break that, you need to **split the key** before the join — salt
bucketing — so that `EMEA` becomes `EMEA#0` … `EMEA#15`, each with its own
group. Then `Reshuffle` or a second combine distributes them, and you
recombine afterwards.

```text
hot key "EMEA" ──▶ salt ──▶ "EMEA#0".."EMEA#15" ──▶ group ──▶ work ──▶ unsalt
```

This is the standard remedy for skew, and it is the reason `Reshuffle`
exists. In the batch pipeline in this course the keys are regions — four
of them — so skew is not the issue at this scale; it becomes one the moment
you key by `customer_id`.

### The full picture

```text
   counts stream ──┐
                   ├──▶ CoGroupByKey ──▶ Reshuffle ──▶ Map ──▶ sink
   sums stream ────┘
                            │
                            ▼
              (key, {"counts": [...], "sums": [...]})
```

---

## 🛠️ Hands-On: Merging a Count Stream and a Sum Stream

### Step 1 — build the two streams

We will build two independently-aggregated streams over the same orders,
then merge them with `CoGroupByKey`. Create `hands_on_cogroupbykey.py`:

```python
"""Merge a per-region count stream and a per-region sum stream with CoGroupByKey."""
import apache_beam as beam
from apache_beam.io.textio import ReadFromText, WriteToText

from project.transforms import (
    ParseOrderFn,
    RevenueByRegionFn,
    to_summary_row,
)

INPUT = "./sample_data/orders.csv"
OUTPUT = "./out/hands_on/joined"


def build(pipeline, input_path, output_path):
    lines = pipeline | "ReadOrders" >> ReadFromText(input_path)
    orders = lines | "ParseOrders" >> beam.ParDo(ParseOrderFn())

    completed = orders | "KeepCompleted" >> beam.Filter(
        lambda o: o["status"] == "complete"
    )
    keyed = completed | "KeyByRegion" >> beam.Map(lambda o: (o["region"], o))

    # Two independent aggregations of the same data.
    #
    # The revenue sum has to normalise currency first, so it uses the
    # project's combiner rather than a plain `sum`. A lambda that summed
    # `order["revenue_eur"]` would raise `KeyError`, because the raw
    # order rows have `amount` and `currency`, not `revenue_eur`.
    counts = keyed | "CountByRegion" >> beam.combiners.Count.PerKey()
    sums = keyed | "SumByRegion" >> beam.CombinePerKey(RevenueByRegionFn())

    # Merge them by key.
    joined = {"counts": counts, "sums": sums} | "CoGroupByKey" >> beam.CoGroupByKey()

    # Spread the joined groups across workers before the downstream work.
    spread = joined | "Reshuffle" >> beam.Reshuffle()

    (
        spread
        | "FlattenGroups" >> beam.Map(
            lambda kv: (
                kv[0],
                # `Count.PerKey()` already reduced each key to a single
                # number, so the "counts" iterable holds one scalar per
                # key. Summing it is correct; `len(list(...))` would
                # always be 1.
                sum(kv[1]["counts"]),
                sum(v["revenue_eur"] for v in kv[1]["sums"]),
            )
        )
        | "Format" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]},{kv[2]:.2f}")
        | "Write" >> WriteToText(output_path, num_shards=1, shard_name_template="")
    )


if __name__ == "__main__":
    with beam.Pipeline() as pipeline:
        build(pipeline, INPUT, OUTPUT)
```

Run it:

```bash
python hands_on_cogroupbykey.py
cat out/hands_on/joined*
```

Output shape:

```text
AMER,318,113592.19
APAC,285,108194.92
EMEA,322,118423.22
LATAM,320,110646.18
```

The counts and sums are for the same regions, merged side by side.

> **A trap worth pausing on.** `Count.PerKey()` outputs `(region, 318)` —
> a *single scalar* per key, not a list of 318 values. After the
> `CoGroupByKey`, the `"counts"` iterable therefore holds **one** element
> per region, and `len(list(kv[1]["counts"]))` is always `1`, no matter
> how many orders there were. The correct extraction is
> `sum(kv[1]["counts"])`.
>
> This is the general hazard of joining *already-aggregated* streams: the
> shape of the value depends on which transform produced it, and the join
> preserves that shape. Getting it wrong produces a plausible-looking
> number that is silently wrong — which is exactly what the diff against
> the single-`CombinePerKey` reference is there to catch.

### Step 2 — prove it matches a single `CombinePerKey`

The point of the exercise is that the joined result equals the result you
would get from one combined aggregation. Extend the script to compute
both and compare. This is the complete `hands_on_cogroupbykey.py` —
add the `build_reference` function and the new `__main__` block to the
file from Step 1:

```python
def build_reference(pipeline, input_path, output_path):
    """The single-CombinePerKey reference: one aggregation, no join."""
    lines = pipeline | "RefReadOrders" >> ReadFromText(input_path)
    orders = lines | "RefParseOrders" >> beam.ParDo(ParseOrderFn())
    completed = orders | "RefKeepCompleted" >> beam.Filter(
        lambda o: o["status"] == "complete"
    )
    keyed = completed | "RefKeyByRegion" >> beam.Map(lambda o: (o["region"], o))
    summary = keyed | "RefRevenue" >> beam.CombinePerKey(RevenueByRegionFn())

    (
        summary
        | "RefToRows" >> beam.Map(to_summary_row)
        | "RefFormat" >> beam.Map(
            lambda r: f"{r['region']},{r['order_count']},{r['revenue_eur']:.2f}"
        )
        | "RefWrite" >> WriteToText(
            output_path, num_shards=1, shard_name_template=""
        )
    )


if __name__ == "__main__":
    # Two separate pipelines, not two graphs in one `with` block. The
    # Python SDK's Prism runner cannot run two pipelines concurrently in
    # one process, and the `Ref*` labels would collide with the first
    # pipeline's labels if they shared one.
    with beam.Pipeline() as pipeline:
        build(pipeline, INPUT, OUTPUT)

    with beam.Pipeline() as pipeline:
        build_reference(pipeline, INPUT, OUTPUT + "_reference")
```

Run it and compare:

```bash
python hands_on_cogroupbykey.py
diff <(sort out/hands_on/joined*) <(sort out/hands_on/joined_reference*) \
  && echo "MATCH: the join reproduces the single-combine result"
```

The two files must be identical. The `CoGroupByKey` version reaches the
same answer through two aggregations and a join; the reference reaches it
through one aggregation. When they agree, the join logic is correct.

### Step 3 — inspect the group shapes

The `CoGroupByKey` output has a specific shape, and it is worth printing
raw to see it:

```python
import apache_beam as beam
from apache_beam.io.textio import ReadFromText

with beam.Pipeline() as p:
    counts = p | "CreateCounts" >> beam.Create([("EMEA", 3), ("AMER", 1)])
    sums = p | "CreateSums" >> beam.Create([("EMEA", 100.0), ("APAC", 50.0)])

    joined = {"counts": counts, "sums": sums} | "Join" >> beam.CoGroupByKey()

    (
        joined
        | "ShowShape" >> beam.Map(
            lambda kv: (
                kv[0],
                sorted(kv[1].keys()),
                {tag: sorted(values) for tag, values in kv[1].items()},
            )
        )
        | "Print" >> beam.Map(print)
    )
```

Output:

```text
('AMER', ['counts', 'sums'], {'counts': [1], 'sums': []})
('APAC', ['counts', 'sums'], {'counts': [], 'sums': [50.0]})
('EMEA', ['counts', 'sums'], {'counts': [3], 'sums': [100.0]})
```

This is the FULL OUTER JOIN semantics, visible: `AMER` has an **empty
`sums` iterable**, not a missing key. `APAC` has an empty `counts`.

Now the crucial production detail — the **empty iterable is not `None` and
not a missing key**. Code that does this is wrong:

```python
# WRONG: KeyError on keys that appear in only one side
value = kv[1]["sums"][0]
```

The correct code handles the empty case:

```python
# CORRECT
sums = list(kv[1]["sums"])
value = sums[0] if sums else None
```

### Step 4 — `GroupByKey` and its memory profile

For comparison, run the same data through a `GroupByKey` and watch the
output shape:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    kv = p | "Create" >> beam.Create(
        [("EMEA", 1), ("EMEA", 2), ("EMEA", 3), ("AMER", 4)]
    )

    (
        kv
        | "Group" >> beam.GroupByKey()
        | "ShowType" >> beam.Map(
            lambda kv: (kv[0], type(kv[1]).__name__, sorted(kv[1]))
        )
        | "Print" >> beam.Map(print)
    )
```

Output:

```text
('EMEA', 'list', [1, 2, 3])
('AMER', 'list', [4])
```

On the Direct Runner the iterable happens to be a `list`. On Dataflow it
is a lazy wrapper with no `sort` method. This is why the portable code is:

```text
| "Count" >> beam.Map(lambda kv: (kv[0], len(list(kv[1]))))
```

### Step 5 — the `Reshuffle` after the join

Add the `Reshuffle` and watch the graph change:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    counts = p | "CreateCounts" >> beam.Create([("EMEA", 3)])
    sums = p | "CreateSums" >> beam.Create([("EMEA", 100.0)])

    joined = {"counts": counts, "sums": sums} | "Join" >> beam.CoGroupByKey()
    spread = joined | "Reshuffle" >> beam.Reshuffle()

    print(p)
```

The graph now has an extra stage after the join. `Reshuffle` is a shuffle
boundary — it forces the grouped output to be materialised and
repartitioned. That costs a network transfer, and it is only worth paying
when the downstream work is genuinely skewed.

The decision rule:

| Downstream work | `Reshuffle`? |
|---|---|
| A `Map` that reduces each group to a small value | No — the reduce is cheap and the join already shuffled |
| A `FlatMap` that expands groups, or a heavy per-group computation | **Yes** — this is where skew bites |
| A sink that writes groups as-is | Sometimes — it depends on the sink's own parallelism |
| Groups are small and keys are many | No |

### Step 6 — a full outer join over two real streams

Now the general join pattern, with the empty-iterable handling done
properly:

```python
import apache_beam as beam
from apache_beam.io.textio import ReadFromText, WriteToText


def full_outer_join(joined):
    """Yield (key, left_value, right_value) for every key in either stream."""
    key, groups = joined
    left = list(groups.get("left", []))
    right = list(groups.get("right", []))
    if not left and not right:
        return
    if not left:
        for r in right:
            yield (key, None, r)
        return
    if not right:
        for l in left:
            yield (key, l, None)
        return
    for l in left:
        for r in right:
            yield (key, l, r)


with beam.Pipeline() as p:
    left = p | "ReadLeft" >> ReadFromText("./sample_data/orders.csv")
    right = p | "ReadRight" >> ReadFromText("./sample_data/malformed_orders.csv")

    keyed_left = left | "KeyLeft" >> beam.Map(lambda l: (l.split(",")[3], l))
    keyed_right = right | "KeyRight" >> beam.Map(lambda l: (l.split(",")[3], l))

    joined = {"left": keyed_left, "right": keyed_right} | "Join" >> beam.CoGroupByKey()

    (
        joined
        | "Flatten" >> beam.FlatMap(full_outer_join)
        | "Format" >> beam.Map(lambda kv: f"{kv[0]},{kv[1] is not None},{kv[2] is not None}")
        | "Write" >> WriteToText(
            "./out/hands_on/outer", num_shards=1, shard_name_template=""
        )
    )
```

Note the `for l in left: for r in right` nested loop. With one row per
region per side, it is 1×1. If you key by `customer_id` instead of
`region`, it becomes n×m — and you will discover the cost of a
post-shuffle cartesian product the hard way.

---

## 🛠️ Common Errors and Fixes

### `AttributeError: type object 'GroupByKey' has no attribute 'ResultIterable'`

```text
AttributeError: type object 'GroupByKey' has no attribute 'ResultIterable'
```

The Python SDK does not expose `ResultIterable` or `GBKResult` — those are
Java SDK types. Consume the group as an iterable:

```text
| "Count" >> beam.Map(lambda kv: (kv[0], len(list(kv[1]))))
```

### `KeyError: 'sums'`

```text
KeyError: 'sums'
```

You indexed the inner dict with a tag that is not present. This happens if
you used the tuple form of `CoGroupByKey` (positional) but indexed by
name, or if you misspelled the tag. Use the dictionary form with matching
tag names, and remember that the inner dict has an entry for *every* tag —
possibly an empty one.

### `AttributeError: 'ResultIterable' object has no attribute 'sort'`

The group iterable is not a list. Use `sorted(list(kv[1]))`, or convert it
once at the top of the `Map`.

### `TypeError: unhashable type: 'dict'`

```text
TypeError: unhashable type: 'dict'
```

Your input to `CoGroupByKey` is not KV pairs. It needs `(key, value)`
tuples. Add a `Map` that keys each stream.

### `TypeError: CoGroupByKey() missing 1 required keyword-only argument: 'pipeline'`

```text
TypeError: CoGroupByKey() missing 1 required keyword-only argument: 'pipeline'
```

Only when you call `CoGroupByKey` with no inputs at all — the transform
cannot infer the pipeline. Supply it:

```python
beam.CoGroupByKey(pipeline=p)
```

In normal use (`{...} | "Join" >> beam.CoGroupByKey()`) the pipeline is
inferred and you should not pass it.

### The output has more rows than expected

A cartesian product. Your key is not unique on one side, and the nested
loop in `full_outer_join` is generating the cross product. Check:

```bash
# How many rows per key on each side?
python -c "
import csv, collections
left = collections.Counter()
with open('./sample_data/orders.csv') as f:
    for row in csv.reader(f):
        if len(row) > 3:
            left[row[3]] += 1
print(dict(left))
"
```

If a count exceeds 1 and you are not expecting a cross product, your join
key is too coarse.

### `ValueError: GroupByKey cannot be applied to an unbounded PCollection with global windowing and a default trigger`

```text
ValueError: GroupByKey cannot be applied to an unbounded PCollection with
global windowing and a default trigger
```

You grouped an unbounded stream with no explicit window. Either add
`beam.WindowInto` with an explicit trigger, or use `CombinePerKey` /
`Reshuffle` instead.

### `RuntimeError: Transform name is already used` after adding the reference pipeline

You added a second pipeline to the same module and reused a label. The
course linter scopes labels per function, so two functions in the same
file may each use `"ReadOrders"` — but two pipelines in the *same*
function may not. Run:

```bash
python resources/audit_course.py
```

### The `CoGroupByKey` result is empty for one tag

Check the tag spelling in the input dict versus the tag you read. Also
check that the branch you expected to be non-empty is actually producing
elements — a `Filter` upstream of it may be removing everything.

---

## 💡 Production Notes

- **`GroupByKey` is a formatting step.** Use it when the sink wants the
  group. Use `CombinePerKey` when you want a summary. If you find
  yourself writing `GroupByKey → Map(len) → CombinePerKey(sum)`, replace
  the whole thing with `Count.PerKey()` — one shuffle instead of two.
- **The `CoGroupByKey` output contains an empty iterable for every absent
  tag.** This is the FULL OUTER JOIN semantics, and it is also the most
  common source of `IndexError` in join code. Always guard with
  `if values:` or `len(list(values)) > 0`.
- **A `CoGroupByKey` join with a large right-hand side is a memory
  incident waiting to happen.** The right-hand group is materialised on
  the worker that owns the key. Aggregate the right side down to one row
  per key *before* the join, and the group becomes small.
- **Joining to BigQuery in-pipeline saves real money and real latency.**
  The round-trip pattern (export the stream, run a continuous SQL join)
  doubles your BigQuery write cost and adds a query's worth of latency to
  every record. The in-pipeline pattern reads the dimension table once at
  pipeline start and joins in the same shuffle.
- **Dimension tables above roughly 50,000 rows belong in a keyed side
  input or a BigQuery lookup.** `CoGroupByKey` materialises the whole
  group; if the dimension table has 10 million rows under one key, that
  worker OOMs. Use `pvalue.AsDict` for a side-input lookup, or
  `beam.io.ReadFromBigQuery` with a `WITHIN` batch lookup.
- **`Reshuffle` after `CoGroupByKey` fixes group skew, not group size.**
  If a single key holds 40 million rows, `Reshuffle` still routes all 40
  million to one worker. To break a single hot key, salt it before the
  join and recombine after.
- **Salt-bucketing is the standard skew remedy, and it is not free.** The
  salt must be chosen so that the recombination afterwards is exact — a
  random salt means you must merge all buckets, which is another
  `CombinePerKey`. The gain is that the merge is now parallel. Only do it
  when the skew is real; for a four-region dataset it is pure overhead.
- **The tag length matters more than it looks.** Tags of 10 characters or
  fewer are passed through the pipeline as data. Longer tags cause Beam to
  substitute generated indices and add a `RestoreTags` `Map` step to the
  graph. Use short tags.
- **`CoGroupByKey` on unbounded input inherits the watermark rules of
  every branch.** As with `Flatten`, the merged watermark is the minimum
  across the branches. A quiet branch stalls the join's watermark and
  therefore the window firing.
- **On Dataflow, prefer `CombinePerKey` over `CoGroupByKey` for pure
  aggregations.** `CoGroupByKey` carries the full group into the output;
  if you only need a summary, that is wasted network traffic. Use
  `CoGroupByKey` for *merging* independently-produced aggregates, which
  is its sweet spot.
- **Watch the job graph after adding a join.** A `CoGroupByKey` stage
  that is followed by another shuffle stage is usually a sign you could
  have done the aggregation in one pass.

---

## 🔑 Key Takeaways

- `beam.GroupByKey` takes KV pairs and produces `(key, iterable_of_values)`.
  The iterable is **not** a list — it is lazy on Dataflow, and
  `GroupByKey.ResultIterable` / `GBKResult` **do not exist** in the
  Python SDK. Iterate it; do not index or sort it directly.
- `GroupByKey` materialises every group, so its peak memory is the
  largest group. It is a **formatting step for the sink**, not an
  aggregation step. Use `CombinePerKey` for aggregation.
- `beam.CoGroupByKey` takes `{'tag': pcoll}` and produces
  `(key, {'tag': iterable})`. Every key from every input appears in the
  output, with **empty iterables** for the inputs it is missing from.
- That is exactly a **SQL FULL OUTER JOIN**. The empty iterable is the
  detail that causes most join bugs. The dictionary form gives named
  tags; the tuple form gives positional tuples. Prefer the dictionary
  form — tags longer than 9 characters add a `RestoreTags` step to the
  graph.
- `CoGroupByKey` joins a stream to a BigQuery dimension table **without a
  round trip** — one table read at start-up instead of a continuous export,
  a continuous query, and the extra latency.
- `beam.Reshuffle` after a `CoGroupByKey` breaks group skew by
  redistributing the groups. It does not split a single hot group — that
  needs salt-bucketing.
- `CoGroupByKey` is the wrong tool for a cartesian product (use
  `FlatMap`), for a join whose condition is not the grouping key (put the
  whole condition in the key), and when one side has many rows per key
  (aggregate first).
- The safe join is: **aggregate each side to one row per key, then join.**
  The cross-validation in the hands-on proves this reproduces the
  single-`CombinePerKey` answer exactly — a diff, not an eyeball.

---

## 📚 Practice Exercises

1. **Prove the join matches the single combine.** Extend the hands-on so
   the `CoGroupByKey` result and the `CombinePerKey` result are both
   written, then `diff` them.
   *Expected:* the files are identical, including the rounding.

2. **Handle the empty iterable correctly.** Extend the outer-join function
   to use `left`/`right` values where one side is empty, and write three
   distinct output columns: `key`, `left_present`, `right_present`.
   *Expected:* rows where only one side is present are emitted, not
   dropped and not an `IndexError`.

3. **Prove the FULL OUTER JOIN semantics.** Join a stream of keys
   `{a, b}` against a stream of keys `{b, c}` and print the raw output.
   *Expected:* three keys in the output — `a`, `b`, `c` — with `a`'s
   second tag empty and `c`'s first tag empty.

4. **Replace a `GroupByKey` + `Map` with a combiner.** Rewrite the
   hands-on pipeline to produce the same output using
   `beam.combiners.Count.PerKey()` instead of `GroupByKey` → `Map(len)`.
   Compare the job graphs and count the stages.
   *Expected:* one fewer stage and one fewer shuffle.

5. **Add a third tag.** Extend the join to merge a per-region count, a
   per-region sum, and a per-region max. Write all three in one row.
   *Expected:* the output dict has three keys, and a tag longer than 9
   characters adds a `RestoreTags` stage to the printed graph.

6. **Reflection.** A pipeline joins a 10-million-row order stream to a
   200-row customer table, keyed by `customer_id`. Some customers have
   50,000 orders. Explain, in terms of the materialised group, what
   happens on the worker that owns such a customer, and propose a change
   that avoids it without changing the output.

---

## 📖 Further Reading

- Apache Beam: Grouping by key — https://beam.apache.org/documentation/programming-guide/#grouping-by-key
- Apache Beam: Combining and joining keyed collections — https://beam.apache.org/documentation/programming-guide/#combine
- Apache Beam Python API: `beam.CoGroupByKey` — https://beam.apache.org/documentation/sdks/python/apache_beam.transforms.core.html#apache_beam.CoGroupByKey
- Apache Beam Python API: `beam.GroupByKey` — https://beam.apache.org/documentation/sdks/python/apache_beam.transforms.core.html#apache_beam.GroupByKey
- Google Cloud Dataflow: Join streams with CoGroupByKey — https://cloud.google.com/dataflow/docs/guides/streaming-group-by-key
- Google Cloud Dataflow: Optimise joins with CoGroupByKey — https://cloud.google.com/dataflow/docs/optimize-joins
