# 2.5 — Filter & Flatten

> **Section 2 · SDK & Core Transforms · Lecture 2.5 · 6:30**

## 🎯 What you will learn

- What `beam.Filter` actually does, and why a filter is a *lossy* transform
- `beam.FilterInto` does **not** exist in apache-beam 2.77 — and what the Beam way
  to build a dead-letter queue actually is
- `beam.Flatten`: merging many PCollections into one, and the type/coder rule
  that governs it
- Why `Flatten` after a `GroupByKey` is cheap, and `Flatten` before one is not
- `beam.Reshuffle`: what it changes, what it does not, and when it is worth a stage
- The fusion optimisation, and the label-uniqueness rule it makes observable
- How to build a "cancelled orders" side output alongside a main output

---

## 🧠 Concept

### The shape of this chapter

`Filter` and `Flatten` look trivial. `Filter` drops elements. `Flatten` merges
collections. They are the two transforms that change the *shape* of a
PCollection rather than the shape of its elements, and they are the two most
frequently misapplied transforms in a Beam codebase.

The interesting questions are not "what does the API look like" but:

- What happens to the elements you drop? (Answer: they are gone, unless you
  route them somewhere.)
- What does it cost to merge two PCollections? (Answer: it depends entirely on
  where the merge sits relative to a shuffle.)
- When does a `Flatten` change the *grouping* of data versus merely changing
  where it came from?

### `beam.Filter`: a predicate on the element

`beam.Filter` takes a callable that receives one element and returns a
boolean. Elements for which the predicate is true pass through; elements for
which it is false are **silently dropped**.

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create([1, 2, 3, 4, 5])
        | "KeepEven" >> beam.Filter(lambda x: x % 2 == 0)
        | "Print" >> beam.Map(print)
    )
```

There is no second return channel. A `Filter` predicate that returns `False`
is a one-way door: the element is gone, and no downstream transform can know
it existed.

This is a deliberate design decision, and it is the right one for the 99% case.
If `Filter` returned `(element, kept: bool)` instead, every transform in the
pipeline would have to deal with a tuple, and the common case — "give me the
rows that match" — would become noisier. Beam keeps the primitive narrow and
provides a separate mechanism for the case where you must not lose data.

### `beam.FilterInto` does not exist

This is worth stating plainly, because it is a common interview trap and a
common hallucination in generated code:

```text
# This does NOT exist in apache-beam 2.77:
beam.FilterInto(predicate)
```

You can verify it in one line:

```bash
python -c "import apache_beam as beam; print(hasattr(beam, 'FilterInto'))"
# False
```

There is no `beam.FilterInto` in the SDK, and there is no `FilterInto` in
`apache_beam.transforms` either. The Python SDK has no transform that
splits one input into "kept" and "rejected" in a single pass, because the
model has no way to express "these two outputs are complementary views of
the same input" as a primitive.

The Beam way to build a dead-letter queue is a **`ParDo` with a tagged side
output**. The `DoFn` decides, per element, which output to emit to. The
main output carries the good elements; a named side output carries the
rejected ones.

The mechanism has three parts:

| Part | API | Purpose |
|---|---|---|
| 1. Tag the output | `beam.pvalue.TaggedOutput("dlq", value)` | mark an element as belonging to a side output |
| 2. Declare the output | `.with_outputs("dlq", main="main")` | turn the `ParDo` result into a `DoOutputsTuple` |
| 3. Read the outputs | `result["main"]`, `result["dlq"]` | address each output PCollection |

Here is the whole mechanism, working:

```python
import apache_beam as beam
from apache_beam.pvalue import TaggedOutput


class RouteOrdersFn(beam.DoFn):
    """Split orders into a main output and a dead-letter output."""

    def process(self, order):
        if order.get("status") == "cancelled":
            yield TaggedOutput("cancelled", order)
        else:
            yield order


with beam.Pipeline() as p:
    orders = p | "Create" >> beam.Create(
        [
            {"order_id": "o1", "status": "complete"},
            {"order_id": "o2", "status": "cancelled"},
            {"order_id": "o3", "status": "complete"},
        ]
    )

    routed = orders | "RouteOrders" >> beam.ParDo(RouteOrdersFn()).with_outputs(
        "cancelled", main="main"
    )

    (
        routed["main"]
        | "WriteGood" >> beam.Map(lambda o: f"good:{o['order_id']}")
        | "PrintGood" >> beam.Map(print)
    )

    (
        routed["cancelled"]
        | "WriteDlq" >> beam.Map(lambda o: f"dlq:{o['order_id']}")
        | "PrintDlq" >> beam.Map(print)
    )
```

The output:

```text
good:o1
good:o3
dlq:o2
```

The critical detail: **the two outputs are two views of the same single
pass over the input.** The source is read once. There is no second
`Filter` over a re-read of the data, which is the naive way people build
DLQs and which doubles your ingest cost.

Note the shape of the API. `.with_outputs("cancelled", main="main")` returns a
`DoOutputsTuple`, not a `PCollection`. That is why you must index it:

```python
routed["main"]      # the PCollection of kept elements
routed["cancelled"] # the PCollection of rejected elements
```

Trying to use `routed` directly is a `TypeError`:

```text
TypeError: 'PCollection' object is not subscriptable
```

...which is confusing when it happens, because the error appears at the point
of use rather than at the point of the mistake. If you see that error, look
back for the missing `.with_outputs(...)`.

### The tradeoff: `Filter` versus side output

| | `beam.Filter` | `ParDo` + `with_outputs` |
|---|---|---|
| Elements dropped | gone | captured on a side output |
| Source read | once | once |
| Per-element cost | predicate call | generator dispatch + tag check |
| Code size | one line | a `DoFn` class |
| Use when | you genuinely do not care | you must not lose data |

The rule of thumb: **use `Filter` when dropping is the intent; use a side
output when dropping is a failure.** A malformed-record filter is a failure
filter. A "only EMEA orders" filter is an intent filter.

If you only need the *count* of rejected elements rather than the elements
themselves, a `Filter` plus a `CombinePerKey` on the rejected branch is
cheaper than a side output — but you still need the side output to know
*which* ones were rejected.

### `beam.Flatten`: merging PCollections

`Flatten` takes a tuple of PCollections and produces one PCollection
containing the union of their elements.

```python
import apache_beam as beam

with beam.Pipeline() as p:
    online = p | "CreateOnline" >> beam.Create([("a", 1), ("b", 2)])
    batch = p | "CreateBatch" >> beam.Create([("b", 3), ("c", 4)])

    merged = (online, batch) | "Flatten" >> beam.Flatten()

    (
        merged
        | "Sum" >> beam.CombinePerKey(sum)
        | "Print" >> beam.Map(print)
    )
```

Output:

```text
('a', 1)
('b', 5)
('c', 4)
```

Three things about `Flatten` that people get wrong.

**1. The order of the tuple is irrelevant; the content is not.** `Flatten`
produces a *multiset*. There is no ordering guarantee, no "first input
first" behaviour. If you need to know which source an element came from,
tag it before flattening:

```python
merged = (
    (online | "TagOnline" >> beam.Map(lambda kv: ("online", kv))),
    (batch | "TagBatch" >> beam.Map(lambda kv: ("batch", kv))),
) | "Flatten" >> beam.Flatten()
```

**2. `Flatten` requires a common element type across its inputs.** This is
the coder rule. When Beam serialises a `Flatten` into the Runner API, it
needs a single output coder for the merged PCollection. If the inputs have
incompatible types, the runner cannot pick one.

In practice, this surfaces in three ways:

```python
# This is fine: both branches are str
a = p | "CreateA" >> beam.Create(["x", "y"])
b = p | "CreateB" >> beam.Create(["z"])
merged = (a, b) | "FlattenStr" >> beam.Flatten()

# This is also fine at runtime: the coder falls back to a generic one
c = p | "CreateC" >> beam.Create([1, 2])
d = p | "CreateD" >> beam.Create(["z"])
merged2 = (c, d) | "FlattenMixed" >> beam.Flatten()
```

The second case is the interesting one. Beam does *not* raise a build-time
error for `int` and `str`; it falls back to a permissive coder. But this is
a latent bug, not a feature. If one branch is `int` and another is `str`,
downstream code that assumes a type will fail on a worker at 3am rather
than in your editor.

The disciplined fix is to reconcile the types yourself, explicitly, before
flattening:

```python
# Reconcile deliberately: both branches become str
a = p | "CreateA" >> beam.Create([1, 2])
b = p | "CreateB" >> beam.Create([3, 4])
merged = (
    (a | "ToStrA" >> beam.Map(str)),
    (b | "ToStrB" >> beam.Map(str)),
) | "Flatten" >> beam.Flatten()
```

Or, if the branches genuinely have different schemas, normalise them to a
common record type before the merge. In this course's project the pattern
is exactly that: `ParseOrderFn` produces the same dict shape regardless of
which source the order came from, so the two branches can be flattened.

**3. `Flatten` with unbounded inputs.** `Flatten` on an unbounded PCollection
is legal and is the standard way to merge several streaming sources into
one. The semantics are the ones you would expect: the merged PCollection
is unbounded, elements arrive as their branch produces them, and the
watermark of the merged collection is the **minimum** of the branch
watermarks.

That last point has a real consequence. If branch A is idle for a while —
say a Pub/Sub topic that has gone quiet — the merged watermark does not
advance past A's watermark. Downstream windowing on the merged collection
stalls. This is the classic "one slow input blocks the whole pipeline"
failure, and it is a property of the merge, not of your window logic.

`beam.Reshuffle` is the tool for the *grouping* part of this problem, not
for the watermark. For the watermark problem, the fix is a source that
emits idle watermarks, or a `Trigger` with an idle-time fallback.

### `Flatten` and the shuffle boundary

This is the single most important thing to understand about `Flatten`, and
it is worth a diagram.

A shuffle is a redistribution: all elements with the same key go to the
same worker. `GroupByKey` and `CombinePerKey` both shuffle. `Flatten` does
**not** shuffle — it just merges streams.

So the position of a `Flatten` relative to a `GroupByKey` determines the
cost:

```text
Flatten  →  GroupByKey          ONE shuffle
GroupByKey  →  Flatten          ONE shuffle
```

Both of those are fine — a single shuffle either way. The difference shows
up when there are *multiple* shuffles on one path.

```text
Flatten(A, B) → GroupByKey → Flatten(C, D) → GroupByKey
```

Here you have two shuffles, which is unavoidable: you cannot group before
merging, and you cannot merge before the second grouping. The point is that
`Flatten` itself adds no shuffle, so a `Flatten` that sits *between* two
shuffles costs nothing extra.

The rule in one sentence: **a `Flatten` after a `GroupByKey` is fine — the
grouping has already happened, and the flattened groups are still groups.
A `Flatten` before a `GroupByKey` is also fine, but the merge must be
complete before the grouping starts, or you are grouping a partial view.**

The practical failure mode of "flatten before a group" is not a wrong
answer; it is a *partial* answer. If branch A is still being written when
the `GroupByKey` fires, the group for a key may contain only branch A's
elements. In batch mode, where the input is bounded, the watermark advances
to `+inf` at the end and the group is complete. In streaming mode, it is
not, unless you have a trigger that waits for the watermark.

### Labels and `Flatten`: why the linter checks uniqueness

Beam requires every transform in a pipeline to have a unique label. If two
transforms share a label, the pipeline fails at construction:

```text
RuntimeError: Transform name is already used
```

The error message does not say *which* transforms collided. The course
linter (`resources/audit_course.py`) catches this statically instead.

The reason this matters specifically for `Flatten` is that `Flatten` takes
*a tuple* of inputs, and the natural way to write it is to name each branch
inside the tuple. If you use the same label for two branches, you collide:

```text
# BAD: "Read" is used twice in one pipeline
a = p | "Read" >> beam.io.ReadFromText("./a.csv")
b = p | "Read" >> beam.io.ReadFromText("./b.csv")
merged = (a, b) | "Flatten" >> beam.Flatten()
```

The fix is to give each branch its own label. This is not a bureaucratic
requirement — the label is what you see in the Dataflow job graph, and it
is how you identify which branch is slow when the merged pipeline has a
hot spot:

```python
# GOOD
a = p | "ReadOrders" >> beam.io.ReadFromText("./a.csv")
b = p | "ReadRefunds" >> beam.io.ReadFromText("./b.csv")
merged = (a, b) | "FlattenSources" >> beam.Flatten()
```

The same rule applies inside the tuple when you tag branches before
flattening, and it applies to the `Flatten` label itself.

### `beam.Reshuffle`: what it changes

`Reshuffle` is a transform that **re-partitions** a PCollection. It forces a
shuffle even when the runner's optimiser would not insert one, which
distributes elements across workers so that downstream per-key work is
balanced.

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create([1, 2, 3, 4, 5])
        | "Reshuffle" >> beam.Reshuffle()
        | "Print" >> beam.Map(print)
    )
```

Three facts about `Reshuffle` that matter in practice:

**1. It preserves every element.** `Reshuffle` is not a filter and not a
reducer. The output contains exactly the input elements, possibly
reordered. If elements disappear, the bug is elsewhere.

**2. It does not change the key.** `Reshuffle` on a KV PCollection outputs
the same KV pairs. It does not re-key, does not re-order, and does not
deduplicate.

**3. It does change the *distribution*.** Before `Reshuffle`, all elements
for key `"EMEA"` might sit on one worker. After `Reshuffle`, they are
spread across workers by a hash of the key — which is exactly what you
want before a `GroupByKey` that would otherwise hit one hot worker.

When `Reshuffle` is worth a stage:

| Situation | Use `Reshuffle`? |
|---|---|
| Skewed keys, before a `GroupByKey` | **Yes** — this is the canonical use |
| After a `GroupByKey`, to spread the grouped output | **Yes** — the groups are now large, spread them |
| To fix a slow downstream sink | Sometimes — it balances the fan-out |
| To "make it parallel" | **No** — the runner already parallelises `Map` and `Filter` |
| Between two shuffles | **No** — you pay a shuffle for nothing |

The classic pattern is `Reshuffle` **after** a `GroupByKey` or
`CoGroupByKey`, because after grouping, the output is sorted by key and the
downstream work is "process each group". Without a `Reshuffle`, the
downstream sees groups clustered by key, so a worker handling EMEA gets all
the EMEA groups.

The anti-pattern is putting `Reshuffle` between a `Map` and a `Filter` to
"help parallelism". `Map` and `Filter` are already fully parallel and are
usually fused into a single stage by the runner. Inserting a `Reshuffle`
there forces a full network shuffle of the entire dataset for no benefit.
It is the most expensive no-op in Beam, and you will see it in real
codebases.

### The fusion optimisation, and where `Flatten` sits in it

The runner analyses the graph and fuses adjacent steps that can be executed
together without a materialisation boundary. The classic fusion is:

```text
Map → Filter → Map   ⇒   one stage, one serialisation
```

Three transforms act as **fusion barriers** — the runner must materialise
the intermediate result because the next step needs the data organised
differently:

| Transform | Why it breaks fusion |
|---|---|
| `GroupByKey` | groups by key — a redistribution |
| `CombinePerKey` | groups by key — a redistribution |
| `Reshuffle` | deliberately re-partitions |
| `Flatten` | **usually does not** — see below |

`Flatten` is the interesting case. A `Flatten` is *not* a barrier in the
usual sense: merging two streams does not require re-grouping. The runner
can frequently fuse a `Flatten` into the downstream `Map`/`Filter`.

However, `Flatten` **does** prevent fusion across it in one specific
scenario: if a `Flatten` merges inputs that arrived through *different
sources*, the runner must materialise each source's contribution before it
can merge them. A `Flatten` of two `Map`ed branches of the *same* source
fuses; a `Flatten` of two `ReadFromText` calls does not.

This matters for cost. Here is a pipeline that reads one file and splits it:

```python
with beam.Pipeline() as p:
    lines = p | "Read" >> beam.io.ReadFromText("./orders.csv")

    complete = lines | "KeepComplete" >> beam.Filter(lambda l: ",complete," in l)
    cancelled = lines | "KeepCancelled" >> beam.Filter(lambda l: ",cancelled," in l)

    merged = (complete, cancelled) | "Flatten" >> beam.Flatten()
```

Here the `Flatten` merges two branches of the *same* source, so the runner
can fuse the whole thing — one read, two filters, one output. No
intermediate file is written for the filter results.

Now compare:

```python
with beam.Pipeline() as p:
    orders = p | "ReadOrders" >> beam.io.ReadFromText("./orders.csv")
    refunds = p | "ReadRefunds" >> beam.io.ReadFromText("./refunds.csv")

    merged = (orders, refunds) | "Flatten" >> beam.Flatten()
```

Two independent sources. The runner reads both and materialises the merge
point. Two reads, one merge, one output — still efficient, but now the
merge is a real stage rather than a fused operation.

The lesson: **`Flatten` is cheap, but it is not free, and it is not always
fusible.** Put it where the data is genuinely divergent, not as a
ceremonial step.

### The full picture

```text
                    ┌──────────────┐
   source 1 ───────▶│              │
                    │  ParDo       │──▶ main output ──▶ downstream
   source 2 ───────▶│  + side out  │──▶ dlq output  ──▶ DLQ sink
                    └──────────────┘

   (branch A) ──┐
                ├──▶ Flatten ──▶ GroupByKey ──▶ CombinePerKey ──▶ sink
   (branch B) ──┘
```

---

## 🧠 Filter, Flatten, and the project's data flow

The course project already contains a `Filter` and a `Flatten` candidate.
Here is the filter in `project/batch_pipeline.py`:

```text
| "KeepCompletedOrders" >> beam.Filter(
    lambda order: order["status"] in statuses
)
```

Note that the predicate closes over `statuses`, a parameter of
`build_pipeline`. The closure is evaluated on the worker, so `statuses` must
be picklable — a tuple of strings is; a set is; a database cursor is not.

For the hands-on, you will build the richer version: a `ParDo` with a side
output that captures cancelled orders *and* keeps the rest, and a `Flatten`
that merges two independent sources.

---

## 🛠️ Hands-On: Cancelled-Order Side Output and a Two-Source Flatten

### Setup

Make sure you are in the course root and the sample data exists:

```bash
cd data-engineering/data-Course/google/Dataflow
source .venv/bin/activate
python resources/sample_data.py --output-dir ./sample_data
ls sample_data/
```

You should see `orders.csv`, `orders.ndjson`, `events.ndjson`, `events.csv`,
`malformed_orders.csv`, `product_reference.ndjson` and `summary.json`.

### Step 1 — a side output that captures cancelled orders

Create `hands_on_filter.py`:

```python
"""Route cancelled orders to a side output; keep everything else on the main output."""
import apache_beam as beam
from apache_beam import pvalue
from apache_beam.io.textio import ReadFromText, WriteToText
from apache_beam.pvalue import TaggedOutput

INPUT = "./sample_data/orders.csv"
MAIN_OUTPUT = "./out/hands_on/main"
DLQ_OUTPUT = "./out/hands_on/cancelled"


class RouteOrdersFn(beam.DoFn):
    """Emit cancelled orders on the 'cancelled' side output, all others on main."""

    def process(self, line):
        parts = line.split(",")
        if len(parts) < 9:
            yield TaggedOutput("cancelled", line)
            return
        if parts[6] == "cancelled":
            yield TaggedOutput("cancelled", line)
            return
        yield line


def build(pipeline):
    lines = pipeline | "ReadOrders" >> ReadFromText(INPUT)

    routed = lines | "RouteOrders" >> beam.ParDo(RouteOrdersFn()).with_outputs(
        "cancelled", main="main"
    )

    (
        routed["main"]
        | "FormatMain" >> beam.Map(lambda l: "kept:" + l)
        | "WriteMain" >> WriteToText(MAIN_OUTPUT, num_shards=1, shard_name_template="")
    )

    (
        routed["cancelled"]
        | "FormatDlq" >> beam.Map(lambda l: "cancelled:" + l)
        | "WriteDlq" >> WriteToText(DLQ_OUTPUT, num_shards=1, shard_name_template="")
    )


if __name__ == "__main__":
    with beam.Pipeline() as pipeline:
        build(pipeline)
```

Run it:

```bash
python hands_on_filter.py
echo "--- main ---"
cat out/hands_on/main*
echo "--- cancelled ---"
cat out/hands_on/cancelled*
```

Check the counts. Every input line appears in exactly one of the two
outputs:

```bash
cat sample_data/orders.csv out/hands_on/main* out/hands_on/cancelled* | grep -c .
```

Compare against the source line count:

```bash
wc -l < sample_data/orders.csv
```

The two numbers must match. If a line appears in both, or in neither, your
`process` is not emitting on exactly one path.

### Step 2 — flattening two sources

Now merge two genuinely different sources. Create `hands_on_flatten.py`:

```python
"""Flatten the orders file and the malformed-orders file into one stream."""
import apache_beam as beam
from apache_beam.io.textio import ReadFromText, WriteToText

ORDERS = "./sample_data/orders.csv"
MALFORMED = "./sample_data/malformed_orders.csv"
OUTPUT = "./out/hands_on/merged"


def build(pipeline):
    orders = pipeline | "ReadOrders" >> ReadFromText(ORDERS)
    malformed = pipeline | "ReadMalformed" >> ReadFromText(MALFORMED)

    # Tag the branches so the merged output records its provenance.
    tagged = (
        (orders | "TagOrders" >> beam.Map(lambda l: ("orders", l))),
        (malformed | "TagMalformed" >> beam.Map(lambda l: ("malformed", l))),
    )

    merged = tagged | "FlattenSources" >> beam.Flatten()

    (
        merged
        | "Count" >> beam.combiners.Count.PerKey()
        | "Format" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]}")
        | "Write" >> WriteToText(OUTPUT, num_shards=1, shard_name_template="")
    )


if __name__ == "__main__":
    with beam.Pipeline() as pipeline:
        build(pipeline)
```

Run it:

```bash
python hands_on_flatten.py
cat out/hands_on/merged*
```

Expected shape:

```text
orders,5000
malformed,12
```

The exact counts depend on the sample generator, but two properties are
guaranteed: there is one row per tag, and the counts sum to the total
number of lines across both inputs.

```bash
cat sample_data/orders.csv sample_data/malformed_orders.csv | grep -c .
```

### Step 3 — flatten after a group, and the shuffle you just paid for

`Flatten` is free of shuffles, but `GroupByKey` is not. Put a `Flatten`
after a `GroupByKey` and observe the job graph:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    orders = p | "ReadOrders" >> beam.io.ReadFromText("./sample_data/orders.csv")
    refunds = p | "ReadRefunds" >> beam.io.ReadFromText("./sample_data/malformed_orders.csv")

    grouped_orders = orders | "GroupOrders" >> beam.GroupByKey()
    grouped_refunds = refunds | "GroupRefunds" >> beam.GroupByKey()

    merged = (grouped_orders, grouped_refunds) | "FlattenGroups" >> beam.Flatten()

    (
        merged
        | "Count" >> beam.Map(lambda kv: (kv[0], len(list(kv[1]))))
        | "Print" >> beam.Map(print)
    )
```

Print the graph:

```python
print(p)
```

You will see two `GroupByKey` stages and one `Flatten` stage. The `Flatten`
itself is not a shuffle; the two `GroupByKey`s are. This is the point:
**the cost of a `Flatten` is the cost of the shuffles around it, not the
merge.**

### Step 4 — a `Reshuffle` that earns its keep

`Reshuffle` forces a repartition. To see it matter, put it where the work
is actually skewed:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    keyed = p | "Create" >> beam.Create(
        [("EMEA", i) for i in range(1000)] + [("AMER", i) for i in range(5)]
    )

    spread = keyed | "Reshuffle" >> beam.Reshuffle()

    (
        spread
        | "GroupByRegion" >> beam.GroupByKey()
        | "Print" >> beam.Map(lambda kv: (kv[0], len(list(kv[1]))))
    )
```

Without the `Reshuffle`, everything for a given key is already colocated
because it was created together in one `Create`. With it, the runner
spreads the work. The *output* is identical either way — that is the point
of the exercise. `Reshuffle` changes the execution, not the result.

Now run this version and observe the cost:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    keyed = p | "Create" >> beam.Create([("EMEA", 1), ("AMER", 2)])

    # Pointless Reshuffle: the next stage is a Map, which is already parallel.
    wasteful = keyed | "Reshuffle" >> beam.Reshuffle()

    (
        wasteful
        | "Double" >> beam.Map(lambda kv: (kv[0], kv[1] * 2))
        | "Print" >> beam.Map(print)
    )
```

Compare the job graphs. The second pipeline has a shuffle stage that buys
nothing. This is the anti-pattern to look for in code review.

---

## 🛠️ Common Errors and Fixes

### `AttributeError: module 'apache_beam' has no attribute 'FilterInto'`

```text
AttributeError: module 'apache_beam' has no attribute 'FilterInto'
```

There is no `beam.FilterInto` in apache-beam 2.77. The DLQ pattern is a
`ParDo` with a tagged side output:

```python
routed = orders | "Route" >> beam.ParDo(RouteOrdersFn()).with_outputs(
    "cancelled", main="main"
)
```

### `TypeError: 'PCollection' object is not subscriptable`

```text
TypeError: 'PCollection' object is not subscriptable
```

You used `routed["main"]` but `routed` is a plain `PCollection`. It only
becomes subscriptable after `.with_outputs(...)`:

```python
routed = orders | "Route" >> beam.ParDo(RouteOrdersFn()).with_outputs(
    "cancelled", main="main"
)
```

### `ValueError: Tag 'dlq' is neither the main tag 'None' nor any of the tags ['cancelled']`

```text
ValueError: Tag 'dlq' is neither the main tag 'None' nor any of the tags ['cancelled']
```

The tag you emit in `TaggedOutput` does not match the tag you declared in
`with_outputs`. These two strings must be identical:

```text
yield TaggedOutput("cancelled", order)          # in the DoFn
.with_outputs("cancelled", main="main")          # at the call site
```

### `RuntimeError: Transform name is already used`

```text
RuntimeError: Transform name is already used
```

Two transforms in the same pipeline share a label. The message does not say
which. Catch it before you run:

```bash
python resources/audit_course.py
```

### `RuntimeError: Transform name is already used` after adding a `Flatten`

Almost always the same cause: the two branches of the flatten tuple reuse a
label.

```text
# BAD
a = p | "Read" >> beam.io.ReadFromText("./a.csv")
b = p | "Read" >> beam.io.ReadFromText("./b.csv")

# GOOD
a = p | "ReadOrders" >> beam.io.ReadFromText("./a.csv")
b = p | "ReadRefunds" >> beam.io.ReadFromText("./b.csv")
```

### `TypeError: unhashable type: 'list'` after a `Flatten`

```text
TypeError: unhashable type: 'list'
```

You flattened two KV streams and then applied a keyed transform, but one
branch's "value" is a list — the `GroupByKey` output shape, not a scalar.
Flattening a `GroupByKey` result with a non-`GroupByKey` result mixes
shapes. Flatten like with like:

```python
# BAD: mixes (key, iterable) with (key, scalar)
merged = (grouped, flat_kv) | "FlattenMixed" >> beam.Flatten()

# GOOD: flatten before grouping, or group both
merged = (raw_a, raw_b) | "FlattenRaw" >> beam.Flatten()
grouped = merged | "Group" >> beam.GroupByKey()
```

### `ValueError: GroupByKey cannot be applied to an unbounded PCollection with global windowing and a default trigger`

```text
ValueError: GroupByKey cannot be applied to an unbounded PCollection
with global windowing and a default trigger
```

You grouped an unbounded stream without specifying a window. Either add
`beam.WindowInto` with an explicit trigger, or use `CombinePerKey` /
`Reshuffle` instead of a raw `GroupByKey`.

### The side output is empty

Check three things in order:

1. Is the tag string in `TaggedOutput` identical to the one in
   `with_outputs`? A typo here gives you a `ValueError`, not an empty
   output, so if you got no error the tags probably match.
2. Does the predicate actually fire? `parts[6] == "cancelled"` assumes a
   specific column index. The `orders.csv` header is
   `order_id,customer_id,order_ts,region,channel,currency,status,amount,product_id`
   — `status` is index 6, and `amount` is index 7.
3. Are you reading the right output? `routed["cancelled"]` is the DLQ;
   `routed["main"]` is everything else.

### `FileNotFoundError` on the output path

`WriteToText` writes a *prefix*, and the runner creates files named
`<prefix>00000of00001`. The prefix directory must exist or be creatable:

```bash
mkdir -p out/hands_on
```

Never hard-code the sharded filename. Read it with a glob:

```bash
cat out/hands_on/main*
```

---

## 💡 Production Notes

- **A dropped element is gone.** In Dataflow, a `Filter` that removes 0.1% of
  a 2-billion-row input removes 2 million rows, and the job succeeds. There
  is no error, no warning, and the row count in the output is the only
  evidence. If a filter is *expecting* to drop rows, put a counter on the
  rejected branch and alert on it. A filter that suddenly drops 40% is a
  data incident, and a job that fails is easier to notice than a job that
  quietly succeeds with the wrong number.
- **A DLQ is a first-class sink, not a log line.** Log-based DLQs lose data
  when the log pipeline drops under volume. Write the rejected elements to
  a durable sink — a second BigQuery table, a Pub/Sub topic, a GCS path —
  and *count* them. The whole point is that you can reprocess them later
  when you fix the parser.
- **The side-output DLQ reads the source once.** The naive alternative —
  `Filter` for the good rows, then re-read the source and `Filter` again
  for the bad rows — doubles your ingest cost and can produce inconsistent
  results if the source changes between the two reads. On a 10 TB/day
  ingest at $0.10/GB scanned, that is real money.
- **`Flatten` of two sources does not dedupe.** If both sources contain the
  same record, `Flatten` emits it twice. Deduplicate with `Distinct` on a
  dedup key (the project has `dedup_key` for exactly this) *before* the
  flatten, not after.
- **Watch the watermark across a flatten.** Merging a live Pub/Sub branch
  with a quiet one stalls the merged watermark. On Dataflow this shows up
  as a job that is "healthy" but whose windowed output stops advancing. The
  fix is an idle-watermark source, not a `Reshuffle`.
- **A `Reshuffle` is a full network shuffle.** On Dataflow, that means
  moving your entire dataset across the network. At 5 TB and roughly
  $0.05/GB of intra-region network egress, one careless `Reshuffle` costs
  around $250 per run. Never place one between a `Map` and a `Filter`.
- **`Reshuffle` after `GroupByKey` is the canonical use.** After grouping,
  the output is key-ordered and a hot key's group lands on one worker.
  A `Reshuffle` afterwards spreads the *groups* so downstream per-group
  work is balanced. This is the skew fix that works without changing your
  key function.
- **Watch for the accidental `Flatten` in a loop.** A `FlatMap` that
  yields zero elements is a `Filter`; a `FlatMap` that yields many is a
  `Flatten` in disguise, and the runner treats it differently. Prefer
  explicit `Flatten` when merging named branches — the label in the job
  graph is worth it.
- **Label discipline pays for itself in incidents.** At 3am, the question
  is "which branch of the flatten was slow?" A graph with
  `ReadOrders`/`ReadRefunds`/`FlattenSources` answers it. A graph with
  three nodes called `Read` does not.

---

## 🔑 Key Takeaways

- `beam.Filter` takes a predicate and **silently drops** the elements that
  fail it. Dropping is only correct when you genuinely do not care.
- **`beam.FilterInto` does not exist** in apache-beam 2.77. The Beam way to
  build a DLQ is a `ParDo` with `beam.pvalue.TaggedOutput` and
  `.with_outputs(tag, main=...)`, which reads the source exactly once.
- `beam.Flatten` merges a tuple of PCollections into a multiset. It adds no
  shuffle of its own, but it is not always fusible — merging two independent
  sources forces a materialisation.
- `Flatten` needs a **common element type** across its inputs. Reconcile
  types explicitly rather than relying on the fallback coder, which defers
  the failure to a worker.
- A `Flatten` after a `GroupByKey` is fine: the grouping already happened
  and the flattened items are still groups. A `Flatten` before one is fine
  too, but the merge must complete before the grouping starts or you group
  a partial view.
- `beam.Reshuffle` re-partitions without changing the elements or the keys.
  Its canonical use is breaking key skew after a `GroupByKey` or
  `CoGroupByKey`. It is a waste between a `Map` and a `Filter`.
- Transform labels must be unique per pipeline. `RuntimeError: Transform
  name is already used` does not tell you which pair collided — the course
  linter finds it statically.
- `Filter` and `Flatten` are the two transforms that change the *shape* of
  a PCollection, which makes them the two most worth thinking about
  carefully.

---

## 📚 Practice Exercises

1. **Add a third side output.** Extend the `RouteOrdersFn` from the hands-on
   so that `refunded` orders go to their own `refunded` output and
   everything else stays on the main output. Write all three to disk.
   *Expected:* the three counts sum to the input line count, and
   `with_outputs` now lists two tags.

2. **Prove the source is read once.** Build a pipeline with the side-output
   DLQ and a second, naive DLQ that re-reads the source and filters
   again. Print the pipeline graph for both and identify the extra read
   step. *Expected:* the naive version has two `ReadFromText` steps.

3. **Reconcile a type mismatch.** Flatten a branch of `int` and a branch of
   `str` and show the pipeline runs. Then change it to `str` on both
   branches and show the result is the same shape but with a stable coder.
   *Expected:* both run; the second is the version you would ship.

4. **Measure the cost of a `Reshuffle`.** Build two pipelines over the same
   input: one with `Map → Filter` and one with `Map → Reshuffle → Filter`.
   Print both graphs and count the stages. *Expected:* the second has a
   shuffle stage that the first does not, for identical output.

5. **Tag before you flatten.** Modify the hands-on flatten so the merged
   output records which source each line came from, and produce a count per
   source. *Expected:* the counts match the line counts of the two input
   files exactly.

6. **Reflection.** Your pipeline reads a live Pub/Sub topic and a nightly
   GCS file, flattens them, and windows the result by hour. The hourly
   windows stop advancing at some point during the day. Explain, in terms
   of the merged watermark, why that happens, and propose two fixes.

---

## 📖 Further Reading

- Apache Beam: Filtering and Merging Collections — https://beam.apache.org/documentation/programming-guide/#filtering
- Apache Beam SDKs: Beam Python API reference — https://beam.apache.org/documentation/sdks/python/apache_beam.sdk.html
- Apache Beam: Multiple Outputs / side outputs — https://beam.apache.org/documentation/programming-guide/#multiple-outputs
- Apache Beam: Reshuffle — https://beam.apache.org/documentation/programming-guide/#reshuffle
- Google Cloud Dataflow: Optimize your pipeline with fusion — https://cloud.google.com/dataflow/docs/optimize-aggregates
- Google Cloud Dataflow: Reshuffle and skewed data — https://cloud.google.com/dataflow/docs/guides/skewed-data-processing-guide
