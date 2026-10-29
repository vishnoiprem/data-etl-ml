# 8.3 — Skew, Hot Keys & Reshuffle

> **Section 8 · Production Operations · Lecture 8.3 · 6:30**

## 🎯 What you will learn

- What skew is, and the three different shapes it takes in a Beam pipeline
- How to detect skew from the job graph, from worker CPU, and from wall time
- The four causes of skew, and how to tell them apart from each other
- What `beam.Reshuffle` actually does — and the two critical caveats that make it **not** the hot-key fix
- Why `Reshuffle` breaks timestamp monotonicity and does not change the key
- The hot key splitter pattern: split before the shuffle, re-merge after
- The "combine before the shuffle" pattern, and why it is the highest-value fix
- The "filter and aggregate upstream" pattern
- The "partition by a higher-cardinality key" pattern
- `beam.GroupIntoBatches`, and the semantic change it makes

---

## 🧠 Concept

### What skew is

A Beam pipeline distributes work across workers by **key**. The `GroupByKey`
stage routes every element to the worker that owns its key, and that worker
does all the work for that key. When the key distribution is uneven, one
worker gets a disproportionate share of the work while the others sit
idle.

```text
Even distribution (4 workers)          Skewed (4 workers)

key→worker:  a→w1 b→w2 c→w3 d→w4     key→worker:  a→w1 b→w1 c→w1 d→w1
load:       [25%, 25%, 25%, 25%]      load:       [97%,  1%,  1%,  1%]
```

This is not an abstract concern. A pipeline with one hot key is not
"somewhat slower" than one without — it is bounded below by the time it
takes one worker to process the hot key's elements, while 99% of the
cluster does nothing. Adding workers does not help. The job gets *more
expensive* and no faster.

The classic symptom: **a job that takes ten times longer than the
theoretical minimum**. The theoretical minimum is `total_elements /
(total_available_cores) × per_element_cost`. When a job takes 10× that,
almost always one worker is the critical path.

### Three shapes of skew

Not all skew looks the same, and the fix differs.

**Shape 1 — one key, many elements.** A single key owns a large fraction
of the data. A user id, a session id, a "null" or default key that every
unparseable record falls into. This is the classic hot key.

**Shape 2 — many keys, uneven sizes.** The distribution is skewed but not
pathological: the top key has 10× the average, the next has 8×, and so on.
This is the normal result of real-world data (Zipf's law). It is often
tolerable — you need enough parallelism that the largest key is still
small relative to the cluster.

**Shape 3 — few keys in total.** The cardinality is low. 500 records keyed
by `region` across 4 regions is not "skew" in the classic sense, but it
means the `GroupByKey` stage has at most 4 parallel tasks, no matter how
many workers you have. This is a *parallelism* problem, not a *balance*
problem, and the fix is different: increase the key cardinality, or
restructure the aggregation.

That distinction matters. Shape 3 is fixed by re-keying. Shapes 1 and 2
are fixed by splitting or pre-aggregating. `Reshuffle` helps with neither.

### Detecting skew

**The job graph.** In the Dataflow UI, the stage that performs the
`GroupByKey` will show an uneven shape. Look at the stage's box: if it
has a narrow band of activity at the top and a long tail, or if one
worker shows activity while its neighbours are empty, you have skew.

**Worker CPU.** In the Metrics tab, or on the worker log, one worker
sitting at 100% CPU while every other worker is below 5% is the
clearest signal. For batch jobs the autoscaling graph often shows the
job *not* scaling up — because the backlog is not increasing; one worker
is just busy.

**Wall time versus theoretical minimum.** This is the quantitative check,
and it is worth doing deliberately:

```text
theoretical_minutes = (total_elements / total_cores) × per_element_seconds
efficiency = theoretical_minutes / actual_minutes
```

An efficiency of 0.9–1.0 means the job is well parallelised. Below 0.5
means something is serialising the work. Below 0.1 means there is a
single hot key.

**Direct measurement.** When you need certainty, measure the key
distribution yourself before you run the job:

```python
import apache_beam as beam
from apache_beam.io.textio import ReadFromText
from apache_beam.pvalue import AsIter


class ReportFn(beam.DoFn):
    """Print the key distribution, largest first."""

    def process(self, _, pairs=beam.DoFn.SideInputParam):
        items = sorted(list(pairs), key=lambda kv: kv[1], reverse=True)
        total = sum(count for _, count in items)
        print(f"distinct keys: {len(items)}")
        print(f"total elements: {total}")
        for key, count in items[:5]:
            print(f"  {key}: {count} ({count / total:.1%})")


with beam.Pipeline() as pipeline:
    counts = (
        pipeline
        | "Read" >> ReadFromText("./sample_data/orders.csv")
        | "Key" >> beam.Map(lambda line: (line.split(",")[1], 1))
        | "Count" >> beam.combiners.Count.PerKey()
    )
    (
        pipeline
        | "Create" >> beam.Create([1])
        | "Report" >> beam.ParDo(ReportFn(), pairs=AsIter(counts))
    )
```

A PCollection is a *description* of data, not the data itself — you
cannot iterate over one or subscript it. To get values back into ordinary
Python, read them as a side input (`AsIter`) and let a `DoFn` consume
them. The `Create([1])` step exists because a `ParDo` needs a
PCollection to consume; the single dummy element is what triggers the
report.

Then look at the top few keys. A healthy distribution has a long tail; a
hot key stands out immediately.

### The causes of skew

**1. A genuinely hot key.** One customer, one session, one device, one
partition key generates a large share of the data. Real causes: a
"default" or "unknown" key that every unparseable record falls into; a
single customer placing a huge number of orders; a partition key that
was never designed to be distributed.

**2. A bad hash function.** If you derive the key with something like
`int(customer_id) % 1000` and customer ids are sequential, you have
created a hot key on purpose. Worse, some hash functions cluster
similar inputs into the same bucket. Beam's own partitioning is
well-distributed; a key you invented may not be.

**3. A small number of distinct keys.** The cardinality is lower than the
number of workers, so the parallelism ceiling is the cardinality. This is
shape 3 above.

**4. A `GroupByKey` on a low-cardinality key.** This is shape 3 again, and
it is the most common one in practice because it is easy to write:

```text
| "KeyByRegion" >> beam.Map(lambda order: (order["region"], order))
| "RevenueByRegion" >> beam.CombinePerKey(RevenueByRegionFn())
```

Four regions, a hundred workers, and the aggregation stage can use four
workers. If the job takes an hour, this is why.

### `beam.Reshuffle` — what it really does

`Reshuffle` is one of the most misapplied transforms in Beam, and the
misapplication is expensive. Here is what it actually does, from the SDK
source:

```text
Reshuffle adds a temporary random key to each element, performs a
ReshufflePerKey, and finally removes the temporary key.
```

Expanded, that is three steps:

```text
input
  │
  ▼
AddRandomKeys:    (random.randrange(0, num_buckets), element)
  │
  ▼
ReshufflePerKey:  a GroupByKey on the random key
  │
  ▼
RemoveRandomKeys: element
```

So `Reshuffle` **adds a `GroupByKey` internally**. That is the whole
point: a `GroupByKey` is a shuffle boundary, and a shuffle boundary
prevents the fusion of the surrounding steps. `Reshuffle` is the idiomatic
way to say "break fusion here, checkpoint my data, and give me a fresh
distribution of the elements across workers."

Three things it is genuinely good for:

- **Breaking fusion** when you need a stage boundary, a checkpoint, or a
  separate autoscaling configuration.
- **Checkpointing** in streaming pipelines, so state survives a worker
  restart.
- **Rebalancing** an already-grouped PCollection — if the elements are
  unevenly distributed *because of how they were grouped*, a `Reshuffle`
  redistributes them randomly.

### The two critical caveats

Everything above is true, and none of it fixes a hot key. Two caveats,
both of which are load-bearing:

**Caveat 1: `Reshuffle` does not change the key.** It adds a *temporary
random* key, groups by it, and then **removes** it. The output has
exactly the same keys as the input. If you then `GroupByKey` on the real
key, every element for that real key goes back to the same worker. The
randomisation was undone.

This is why the following is a common and expensive mistake:

```python
# This does NOT fix a hot key.
(
    p
    | "Key" >> beam.Map(lambda x: (x["hot_key"], x))
    | "Reshuffle" >> beam.Reshuffle()
    | "GroupByKey" >> beam.GroupByKey()
)
```

The `Reshuffle` scatters the elements across workers by a random key.
The `GroupByKey` immediately re-gathers them by the hot key. You paid
for two shuffles and got the original problem back.

**Caveat 2: `Reshuffle` breaks timestamp monotonicity.** Because the
elements are re-keyed and re-emitted, their timestamps are no longer
monotonic within the stream. For a pipeline with windowing or triggers
this can change the semantics: an element can arrive at the trigger
after a later-timestamped element did. In a streaming pipeline, this can
cause a window to fire in a different order than it would have.

Neither caveat is a reason to avoid `Reshuffle` — but both are reasons to
know what it does before you reach for it.

### The hot key splitter pattern

The real fix for a genuinely hot key is to **split the key before the
shuffle and re-merge after**. This is the classic Beam "hot key" recipe,
and it works because it makes the parallelism explicit.

```text
                     ┌── shard 0 ──┐
hot key ──► Split ───┼── shard 1 ──┤──► Re-merge ──► result
                     └── shard N ──┘
```

The split key is derived deterministically from the *element*, not from
the position in the stream, so the same element always lands in the same
shard. That is essential: if the shard assignment were random per
attempt, the re-merge would not be able to reconstruct the original
grouping.

The implementation, using the course's `customer_id` as the hot key:

```python
import hashlib

import apache_beam as beam


SHARDS = 32


def split_key(order):
    """Return the (sharded_key, order) pair for an order.

    The shard is derived from the element's own identity, so the same
    order always lands in the same shard. That determinism is what makes
    the re-merge correct.

    The sharded key is a **string**, not a tuple — see the note below.
    """
    digest = hashlib.sha1(order["order_id"].encode("utf-8")).digest()
    shard = int.from_bytes(digest[:4], "big") % SHARDS
    return f"{shard}:{order['customer_id']}", order


def drop_shard(item):
    """Strip the shard prefix from a (sharded_key, count) pair."""
    sharded_key, count = item
    return sharded_key.split(":", 1)[1], count
```

> **Why a string key and not a tuple?** This is a real Beam gotcha, and
> it will bite you. When the key is a **tuple whose components have
> different types** — `(int, str)` — Beam's key coder flattens it, and
> `GroupByKey`/`Count.PerKey` emit only the last component. A key of
> `(shard, customer_id)` where `shard` is an `int` silently becomes just
> the shard, and the customer is gone.
>
> ```text
> key = (13, "c000001")
> GroupByKey emits:  (13, 168)      # customer_id is LOST
> ```
>
> A **string** key is encoded whole and survives the shuffle intact:
>
> ```text
> key = "13:c000001"
> GroupByKey emits:  ("13:c000001", 168)
> ```
>
> If you must use a tuple key, make every component the same type
> (e.g. `("13", "c000001")`), or key by a single string and parse it
> downstream. The string form above is the most robust.

The pipeline:

```python
with beam.Pipeline() as p:
    (
        p
        | "Read" >> beam.io.ReadFromText("./sample_data/orders.csv")
        | "Parse" >> beam.ParDo(ParseOrderFn())
        | "Split" >> beam.Map(split_key)
        # Now the key is "shard:customer_id" — 32× more parallel.
        | "CombineShards" >> beam.CombinePerKey(RevenueByRegionFn())
        | "DropShard" >> beam.Map(drop_shard)
        # Re-merge the per-shard partials.
        | "MergeShards" >> beam.CombinePerKey(RevenueByRegionFn())
    )
```

Note the second `CombinePerKey`: the per-shard partials have to be
**summed**, not merely grouped. `RevenueByRegionFn`'s accumulator is
summable — it is a count and a sum — so the re-merge is another
`CombinePerKey` over the shard-stripped key.

Note the shape of the fix: the `CombinePerKey` now operates on the key
`"shard:customer_id"`, so there are `SHARDS × distinct_keys` groups
instead of `distinct_keys`. The hot customer's orders are spread over 32
groups, each of which is processed by a different worker.

The re-merge step then has to combine the 32 partial results back into
one. There are two ways:

**Re-merge with a second `CombinePerKey`** — group by the original key
only:

```python
def build_split_pipeline(pipeline):
    """Split the hot key, aggregate per shard, then re-merge."""
    keyed = (
        pipeline
        | "Read" >> beam.io.ReadFromText("./sample_data/orders.csv")
        | "Parse" >> beam.ParDo(ParseOrderFn())
        | "Split" >> beam.Map(split_key)
    )

    per_shard = keyed | "CombinePerShard" >> beam.CombinePerKey(RevenueByRegionFn())

    # The key is "shard:original_key". Drop the shard prefix.
    return (
        per_shard
        | "DropShard" >> beam.Map(drop_shard)
        | "MergeShards" >> beam.CombinePerKey(RevenueByRegionFn())
    )
```

**Re-merge by summing the shard summaries.** If the accumulator is
summable (which `RevenueByRegionFn`'s is — it is a count and a sum), you
can merge the shard partials directly without a second shuffle, by
grouping the per-shard results in memory. For a small number of shards
this is cheap and avoids a second network round trip.

**The cost of splitting.** Splitting adds a key transformation and (if
you re-merge with a second `CombinePerKey`) a second shuffle. The rule is
that splitting is worth it when the hot key's share of the work
exceeds the cost of the extra shuffle. If the hot key is 60% of the data
on a 100-worker cluster, splitting is clearly worth it. If it is 12% on
a 100-worker cluster, it is probably not.

**Choosing the shard count.** Rule of thumb: `SHARDS` should be at least
as large as the number of workers you expect to run, and large enough
that the per-shard work is a manageable size. 32 or 64 is a reasonable
starting point. Too many shards means a large second shuffle; too few
means the split did not achieve enough parallelism.

**The shard count must be fixed.** If `SHARDS` changes between runs, the
same element lands in a different shard, and a pipeline that resumed from
a checkpoint would produce different results. Pick a number and keep it.

### The "combine before the shuffle" pattern

This is the highest-value fix in the entire chapter, and it is usually
available.

The insight: **a `GroupByKey` shuffles every element. If you can reduce
the number of elements that need to cross the network before the shuffle,
you win.** `CombinePerKey` does exactly this — it pre-aggregates locally
on each worker, and only the partial accumulators cross the network.

Compare these two pipelines:

```text
Bad:  Map(key) ──► GroupByKey ──────────► aggregate
                  └─ every element crosses the network

Good: Map(key) ──► CombinePerKey ────────► aggregate
                  └─ one accumulator per (worker, key) crosses
```

The savings are proportional to the data volume. If a worker processes
1,000,000 elements across 1,000 keys, `GroupByKey` shuffles 1,000,000
elements; `CombinePerKey` shuffles at most 1,000 accumulators — a
1,000× reduction in network traffic.

For the course's `CombinePerKey(sum)` case, the substitution is
mechanical:

```python
# Instead of:
grouped = keyed | "GroupByKey" >> beam.GroupByKey()

# Use:
grouped = keyed | "CombinePerKey" >> beam.CombinePerKey(sum)
```

There is a subtlety. `GroupByKey` gives you a *list* of all the values
for a key; `CombinePerKey` gives you the *combined result*. If you need
the individual values, you need `GroupByKey` and there is no pre-shuffle
reduction available. But if you want an aggregate — which is the
overwhelming majority of cases — `CombinePerKey` is strictly better.

The same reasoning extends to a `CoGroupByKey`: each side of the join can
be pre-aggregated with a `CombinePerKey` first, so the join shuffles
partial results rather than raw elements.

### The "filter and aggregate upstream" pattern

The cheapest shuffle is the one that does not happen. If you can discard
data before the expensive stage, do it.

```text
Bad:  Read (10M rows) ──► Filter (keep 1%) ──► GroupByKey ──► aggregate
                          └─ 10M rows still counted by the runner

Good: Read (10M rows) ──► Filter (keep 1%) ──► GroupByKey ──► aggregate
                          └─ but the Filter is fused into the read, so the
                             shuffle only carries the surviving 100K rows
```

The important detail: **the runner fuses a `Filter` into the stage before
the shuffle.** A filter that is not separated by a `Reshuffle` (or any
other shuffle boundary) costs essentially nothing — it runs on the worker
that read the data, and only the survivors cross the network.

This is why "filter early" is more than a stylistic preference: it is
the difference between shuffling 10 million elements and shuffling 100
thousand.

The counter-example is instructive: if you put a `Reshuffle` between the
read and the filter, the filter now runs *after* the shuffle, and you
have paid to move all 10 million rows across the network in order to
discard 99% of them. This is the most common way people accidentally
make a pipeline slower, and it is exactly what chapter 8.4 warns about.

### The "partition by a higher-cardinality key" pattern

Shape 3 skew — few keys, low parallelism — is fixed by increasing the
key's cardinality.

```text
Before:  key = region                      → 4 groups, 4-way parallelism
After:   key = (region, day_of_week)       → 28 groups, 28-way parallelism
```

The transformation is a `Map` that appends a component to the key:

```python
def add_day_bucket(order):
    """Key by region and day, to increase the aggregation's parallelism."""
    day = order["order_ts"][:10]
    return (order["region"], day), order
```

This is safe when the result you want is per-(region, day). If you want
per-region, you then need to re-merge — which brings back the same
trade-off as the hot key splitter, and for the same reason.

**When the higher-cardinality key is genuinely the answer:** when the
output is naturally more granular. A daily revenue report does not need
to aggregate across days, so keying by `(region, day)` is not a trick —
it is the actual specification. The trick is only needed when the output
cardinality is *lower* than the parallelism you need.

### `GroupIntoBatches`

`beam.GroupIntoBatches` is a micro-batch transform. It groups elements
into fixed-size batches.

The API, verified against apache-beam 2.77:

```python
beam.GroupIntoBatches(batch_size, max_buffering_duration_secs=None)
```

- `batch_size` — the maximum number of elements per batch.
- `max_buffering_duration_secs` — an optional upper bound on how long an
  incomplete batch waits before being emitted anyway. Without it, a
  partial batch waits indefinitely for more elements.

**It takes keyed input and produces keyed output.** This is the detail
that catches everyone. The input must be `(key, value)` pairs, and the
output is `(key, [values])` — a *tuple*, not a bare list.

```python
with beam.Pipeline() as p:
    (
        p
        | "Read" >> beam.io.ReadFromText("./sample_data/orders.csv")
        | "Parse" >> beam.ParDo(ParseOrderFn())
        # The orders must be keyed before batching.
        | "Key" >> beam.Map(lambda order: ("orders", order))
        | "Batch" >> beam.GroupIntoBatches(batch_size=500)
        # The output is ("orders", [order, order, ...]).
        | "InsertBatch" >> beam.Map(lambda kv: insert_many(kv[1]))
    )
```

Feeding it unkeyed elements fails immediately:

```text
TypeCheckError: Input type hint violation at Batch:
expected Tuple[TypeVariable[K], TypeVariable[V]], got <class 'int'>
```

The use case is reducing per-element overhead. If every element requires a
network round trip — a call to an external API, a database query, a
`BigQuery` row insert — then 1,000 round trips are far more expensive
than 10 calls of 100 rows each.

**The caveat: it changes semantics.** `GroupIntoBatches` is not a
transparent optimisation. It:

- **Reorders elements.** Elements within a batch are in arrival order,
  but batches are not ordered relative to each other in any guarantee you
  can rely on. If your downstream logic depends on ordering, this breaks
  it.
- **Introduces buffering latency.** An element can sit in a partial batch
  waiting to be full. That is real added latency, and for a latency-
  sensitive pipeline it matters.
- **Changes the output shape.** The output is `(key, [values])`, not
  elements. Every downstream transform must be adapted.

For a `DoFn` that needs the batch, the pattern is a `ParDo` that takes
the `(key, values)` tuple:

```python
class InsertBatchFn(beam.DoFn):
    """Insert a whole batch with one call."""

    def process(self, item):
        key, batch = item
        insert_many(batch)
        yield len(batch)
```

**`GroupIntoBatches` is not a skew fix.** It groups elements *within* a
key, but the elements still have to arrive at the same worker. If your
hot key is the problem, batching does not help — and in fact it makes it
worse, because the batch is larger and the hot worker has more to do in
one call.

### Choosing a fix

| Symptom | Likely cause | Fix |
|---|---|---|
| One key has 60% of the elements | Genuine hot key | Hot key splitter, or combine-before-shuffle |
| Key cardinality is 4, cluster is 100 | Low cardinality | Higher-cardinality key, or split into two jobs |
| One worker at 100% CPU, others idle | Hot key | Hot key splitter |
| Job does not scale up despite a backlog | Low parallelism | Higher-cardinality key |
| Huge shuffle bytes | Shuffling raw elements | `CombinePerKey` instead of `GroupByKey` |
| Everything is slow, one stage dominates | Often not skew | Check the job graph for a serial stage |

---

## 🛠️ Hands-On: Generating Skewed Data and Measuring the Difference

This hands-on generates a dataset with one hot customer, then measures how
the hot key affects the pipeline.

### Step 1 — generate skewed data

```bash
cd data-engineering/data-Course/google/Dataflow
source .venv/bin/activate
python resources/sample_data.py --output-dir ./sample_data --hot-key-rate 0.5
```

The `--hot-key-rate 0.5` flag tells the generator to route 50% of all
orders to a single customer id (`c000001`). The generator is seeded, so
the output is byte-identical on every run.

Check the distribution:

```bash
python3 - <<'PY'
import collections
import csv

counts = collections.Counter()
with open("./sample_data/orders.csv", newline="", encoding="utf-8") as handle:
    for row in csv.DictReader(handle):
        counts[row["customer_id"]] += 1

top = counts.most_common(5)
print("distinct customers:", len(counts))
print("total orders:", sum(counts.values()))
for customer, count in top:
    print(f"  {customer}: {count} orders ({count / sum(counts.values()):.1%})")
PY
```

```text
distinct customers: 250
total orders: 5000
  c000001: 2503 orders (50.1%)
  c000042: 42 orders (0.8%)
  c000117: 38 orders (0.8%)
  c000088: 35 orders (0.7%)
  c000203: 33 orders (0.7%)
```

One key owns half the data.

### Step 2 — measure the key distribution with Beam

Now measure it with Beam itself, using a no-shuffle counting job. A
`PCollection` is a description, not data, so to read the counts back you
attach them as a **side input** and materialise them inside a `DoFn`:

```python
import apache_beam as beam
from apache_beam.io.textio import ReadFromText
from apache_beam.pvalue import AsIter

INPUT = "./sample_data/orders.csv"


class ReportFn(beam.DoFn):
    """Print the key distribution, largest first."""

    def process(self, _, pairs=beam.DoFn.SideInputParam):
        items = sorted(list(pairs), key=lambda kv: kv[1], reverse=True)
        total = sum(count for _, count in items)
        print(f"distinct keys: {len(items)}")
        print(f"total elements: {total}")
        for key, count in items[:5]:
            print(f"  {key}: {count} ({count / total:.1%})")


with beam.Pipeline() as pipeline:
    counts = (
        pipeline
        | "Read" >> ReadFromText(INPUT)
        | "KeyByCustomer" >> beam.Map(lambda line: (line.split(",")[1], 1))
        | "Count" >> beam.combiners.Count.PerKey()
    )
    (
        pipeline
        | "Create" >> beam.Create([1])
        | "Report" >> beam.ParDo(ReportFn(), pairs=AsIter(counts))
    )
```

```text
distinct keys: 250
total elements: 5000
  c000001: 2503 (50.1%)
  c000042: 42 (0.8%)
  c000117: 38 (0.8%)
  c000088: 35 (0.7%)
  c000203: 33 (0.7%)
```

Two details in that `DoFn` are worth noticing:

- **`beam.DoFn.SideInputParam` is how a side input reaches `process`.**
  It is a `DoFn` parameter, and it is the only way to get a side input
  into a `DoFn`. A plain `beam.Map` cannot take a keyword argument, so
  `beam.Map(fn, pairs=AsIter(counts))` fails with
  `TypeError: got an unexpected keyword argument 'pairs'`.
- **`AsIter` gives an iterable, not a sized collection.** Calling `len()`
  on it raises `TypeError: object of type '_StateBackedIterable' has no
  len()`. Wrap it in `list()` first.

`beam.combiners.Top.Largest(n)` is the transform to use when you want
the top-n without materialising everything — it keeps only n elements in
state, which is what makes it safe on an unbounded PCollection:

```python
with beam.Pipeline() as pipeline:
    counts = (
        pipeline
        | "Read" >> ReadFromText(INPUT)
        | "KeyByCustomer" >> beam.Map(lambda line: (line.split(",")[1], 1))
        | "Count" >> beam.combiners.Count.PerKey()
    )
    top = counts | "TakeTop" >> beam.combiners.Top.Largest(5)
```

### Step 3 — run the pipeline on skewed data and time it

```bash
time python project/batch_pipeline.py \
    --input ./sample_data/orders.csv \
    --output ./out/skewed_summary
```

```text
real    0m4.812s
user    0m1.902s
sys     0m0.744s
```

Now regenerate the data *without* the hot key and run the same pipeline:

```bash
python resources/sample_data.py --output-dir ./sample_data_uniform
time python project/batch_pipeline.py \
    --input ./sample_data_uniform/orders.csv \
    --output ./out/uniform_summary
```

```text
real    0m4.104s
user    0m1.788s
sys     0m0.711s
```

The difference is small on one worker with 5,000 rows — of course it is.
**Skew does not hurt on a single worker.** That is the whole point: the
cost of skew is that it prevents you from using more workers, so the
effect only becomes visible at scale.

### Step 4 — make the skew visible with a controlled experiment

Measure the *work per key* directly, which is what actually determines
the runtime when the parallelism is bounded by the key count. The
`ReportFn` from Step 2 is reused here.

```python
import time

import apache_beam as beam
from apache_beam.io.textio import ReadFromText
from apache_beam.pvalue import AsIter

INPUT = "./sample_data/orders.csv"
SHARDS = 32


def measure(label, input_path):
    """Time the pipeline and report the wall time."""
    start = time.monotonic()
    with beam.Pipeline() as pipeline:
        result = (
            pipeline
            | "Read" >> ReadFromText(input_path)
            | "KeyByCustomer" >> beam.Map(lambda line: (line.split(",")[1], 1))
            | "Count" >> beam.combiners.Count.PerKey()
        )
        (
            pipeline
            | "Trigger" >> beam.Create([1])
            | "Report" >> beam.ParDo(ReportFn(), pairs=AsIter(result))
        )
    elapsed = time.monotonic() - start
    print(f"{label}: {elapsed:.3f}s")
    return elapsed


measure("skewed (50% hot key)", INPUT)
```

Now the version with the hot key split:

```python
import hashlib

import apache_beam as beam
from apache_beam.io.textio import ReadFromText
from apache_beam.pvalue import AsIter

INPUT = "./sample_data/orders.csv"
SHARDS = 32


def split_key(line):
    """Split a line's customer key into a sharded key and a value.

    The shard comes from a hash of the order id, so the same order always
    lands in the same shard. The sharded key is a **string**, not a
    tuple — see the note on tuple keys above.
    """
    order_id = line.split(",")[0]
    digest = hashlib.sha1(order_id.encode("utf-8")).digest()
    shard = int.from_bytes(digest[:4], "big") % SHARDS
    return f"{shard}:{line.split(',')[1]}", 1


def measure_split(label, input_path):
    """Time the pipeline with the hot key split across shards."""
    start = time.monotonic()
    with beam.Pipeline() as pipeline:
        result = (
            pipeline
            | "Read" >> ReadFromText(input_path)
            | "Split" >> beam.Map(split_key)
            | "CountShards" >> beam.combiners.Count.PerKey()
        )
        (
            pipeline
            | "Trigger" >> beam.Create([1])
            | "Report" >> beam.ParDo(ReportFn(), pairs=AsIter(result))
        )
    elapsed = time.monotonic() - start
    print(f"{label}: {elapsed:.3f}s")
    return elapsed


measure_split("split into 32 shards", INPUT)
```

Compare the *shape* rather than the absolute time: the split version
produces 32× more groups, which is what translates into parallelism when
the job runs on Dataflow with more than one worker.

### Step 5 — verify the split preserves the answer

A split that changes the result is worse than no split. Verify it. The
verification needs the per-key counts back in Python, so it attaches
them as a **side input** and writes them out from the `DoFn`:

```python
import hashlib
import json
import tempfile

import apache_beam as beam
from apache_beam.io.textio import ReadFromText
from apache_beam.pvalue import AsIter

INPUT = "./sample_data/orders.csv"
SHARDS = 32


def split_key(line):
    """Split a line's customer key into a sharded key and a value."""
    order_id = line.split(",")[0]
    digest = hashlib.sha1(order_id.encode("utf-8")).digest()
    shard = int.from_bytes(digest[:4], "big") % SHARDS
    return f"{shard}:{line.split(',')[1]}", 1


def drop_shard(item):
    """Strip the shard prefix from a (sharded_key, count) pair."""
    sharded_key, count = item
    return sharded_key.split(":", 1)[1], count


def run_and_collect(build_counts):
    """Run a pipeline and return the collected counts as a plain dict."""
    path = tempfile.mktemp(suffix=".json")

    class WriteFn(beam.DoFn):
        """Write the side input to a file so the driver can read it."""

        def process(self, _, pairs=beam.DoFn.SideInputParam):
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(dict(list(pairs)), handle)
            return []

    with beam.Pipeline() as pipeline:
        counts = build_counts(pipeline)
        (
            pipeline
            | "Trigger" >> beam.Create([1])
            | "Write" >> beam.ParDo(WriteFn(), pairs=AsIter(counts))
        )

    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


plain_counts = run_and_collect(
    lambda pipeline: (
        pipeline
        | "ReadPlain" >> ReadFromText(INPUT)
        | "KeyByCustomer" >> beam.Map(lambda line: (line.split(",")[1], 1))
        | "CountPlain" >> beam.combiners.Count.PerKey()
    )
)

split_counts = run_and_collect(
    lambda pipeline: (
        pipeline
        | "ReadSplit" >> ReadFromText(INPUT)
        | "Split" >> beam.Map(split_key)
        | "CountShards" >> beam.combiners.Count.PerKey()
        | "DropShard" >> beam.Map(drop_shard)
        # The per-shard counts have to be SUMMED, not counted.
        | "SumShards" >> beam.CombinePerKey(sum)
    )
)

assert plain_counts == split_counts, "the split changed the answer"
print(f"identical across {len(plain_counts)} customers")
```

```text
identical across 250 customers
```

The split is semantics-preserving. That is the property you are actually
testing — not the speed, which is the same on one worker.

### Step 6 — try the anti-pattern, and see why it fails

This is the mistake that costs real money:

```python
import apache_beam as beam
from apache_beam.io.textio import ReadFromText

INPUT = "./sample_data/orders.csv"


with beam.Pipeline() as pipeline:
    (
        pipeline
        | "Read" >> ReadFromText(INPUT)
        | "KeyByCustomer" >> beam.Map(lambda line: (line.split(",")[1], 1))
        | "Reshuffle" >> beam.Reshuffle()
        | "GroupByKey" >> beam.GroupByKey()
        | "Count" >> beam.Map(lambda kv: (kv[0], len(kv[1])))
    )
```

The `Reshuffle` scatters the elements across workers by a random key.
The `GroupByKey` immediately re-gathers them by the real key. The hot
customer's 2,503 elements all end up back on the same worker. You paid
for **two** shuffles and got the original problem back.

To see it clearly, count the groups on each side of the `Reshuffle`:

```python
with beam.Pipeline() as pipeline:
    before = (
        pipeline
        | "Read" >> ReadFromText(INPUT)
        | "KeyByCustomer" >> beam.Map(lambda line: (line.split(",")[1], 1))
        | "CountBefore" >> beam.combiners.Count.PerKey()
    )
    groups_before = len(list(before))
    print(f"groups before reshuffle: {groups_before}")
```

250 groups before. After the `Reshuffle` and the `GroupByKey`, still 250
groups — and one of them holds half the elements. The `Reshuffle` did
nothing for the hot key, because it does not change the key.

### Step 7 — clean up

```bash
rm -rf ./sample_data_uniform ./out/skewed_summary* ./out/uniform_summary*
```

Regenerate the clean sample data for the next chapter:

```bash
python resources/sample_data.py --output-dir ./sample_data
```

---

## 🛠️ Common Errors and Fixes

### `ValueError: If 'num_buckets' is set, it has to be an integer greater than 0`

`beam.Reshuffle(num_buckets=...)` rejects zero and negative values. Pass
a positive integer, or omit the argument for the default.

### The `Reshuffle` did not fix my hot key

It will not, and it cannot. `Reshuffle` adds a *temporary random* key,
groups by it, and removes it. The output has the same keys as the input.
Use the hot key splitter.

### The `Reshuffle` changed my windowing behaviour

`Reshuffle` breaks timestamp monotonicity: elements are re-emitted with
their timestamps intact but in a different order, so an element can
arrive at the trigger after a later-timestamped one did. If your pipeline
depends on ordering or on precise trigger behaviour, do not put a
`Reshuffle` between a windowing stage and its aggregation.

### `KeyError: (0, 'EMEA')` after splitting

You split the key but did not drop the shard before the final aggregation.
The key is now `"shard:original_key"`, and the downstream code expects
just `original_key`. Add the `Map` that strips it:

```text
| "DropShard" >> beam.Map(drop_shard)
```

### The split silently lost half the key

This is the nastiest one, because **nothing fails**. You keyed by a tuple
`(shard, customer_id)` where `shard` is an `int`, and Beam's key coder
flattened the tuple: `GroupByKey` and `Count.PerKey` emitted
`(shard, count)` and the customer id was gone.

```text
key = (13, "c000001")
emitted: (13, 168)          # customer_id LOST, no error raised
```

The fix is a **string** key, or a tuple whose components are all the
same type:

```python
return f"{shard}:{order['customer_id']}", order
```

Always assert that the split and the unsplit pipelines produce identical
results. That assertion is what catches this.

### The split produced different results from the unsplit pipeline

Two separate causes, check them in order:

1. **The shard assignment is not deterministic.** `hashlib.sha1` on the
   element's own identity is deterministic; `random.randrange` is not. If
   you used a random shard, the same element can land in different shards
   on different attempts, and a resumed pipeline will produce different
   totals.
2. **The re-merge counted instead of summed.** After the per-shard
   aggregation, the re-merge must **sum** the shard partials. Using
   `Count.PerKey` there counts the *number of shards* per customer, not
   the number of elements. Use `CombinePerKey(sum)`.

### `TypeError: unhashable type: 'list'`

Your key contains a list or a dict. Use a tuple, or convert the value to
a string.

### `ValueError: Window is already closed` after a `Reshuffle`

The `Reshuffle` moved elements in time relative to the watermark. Put the
`Reshuffle` before the `WindowInto`, not after it.

### `GroupIntoBatches` made my pipeline produce no output

`GroupIntoBatches` is a **keyed** transform. It takes `(key, value)` pairs
and emits `(key, [values])` — a tuple whose second element is the list of
batched values. Two mistakes produce the same silence:

1. You fed it unkeyed values. A `DoFn` that receives the whole tuple must
   unpack it (`key, batch = item`); a `Map` that receives it will treat
   the tuple as a single value.
2. You expected bare lists downstream and wrote a `DoFn` whose `process`
   takes a list. It now receives the `(key, values)` tuple, so it must
   unpack first.

### `TypeCheckError: Input type hint violation at Batch: expected Tuple[TypeVariable[K], TypeVariable[V]], got <class 'int'>`

`GroupIntoBatches` received a bare element instead of a `(key, value)`
pair. Key the input first — `beam.Map(lambda order: ("orders", order))` —
then batch it. The output key is the one you supplied, so use a constant
key like `"orders"` if you want everything in a single batch stream.

### `GroupIntoBatches` is buffering forever

Without `max_buffering_duration_secs`, a partial batch waits indefinitely
for more elements. On a bounded source the batch fills and flushes at the
end; on a streaming source with a trickle of data it never flushes. Set
the timeout.

### `KeyError: 'region'` in the hot key splitter

You split on a field the records do not have. The course's `orders.csv`
columns are `order_id, customer_id, order_ts, region, channel, currency,
status, amount, product_id` — `customer_id` is index 1, `order_id` is
index 0.

### The `CombinePerKey` version is slower than `GroupByKey`

`CombinePerKey` merges accumulators, which is more CPU work per element
than appending to a list, and the pre-aggregation only pays off when
there are many elements per key. If your keys have one element each,
`CombinePerKey` is pure overhead. Check the cardinality first.

---

## 💡 Production Notes

- **Skew does not show up on one worker.** Every skew problem you fix
  was invisible on the Direct Runner. Test skew with a deliberately
  skewed dataset and reason about the group count, not the wall time.
- **The number of groups is your parallelism ceiling.** Before optimising
  anything else, count the distinct keys. If the count is smaller than
  your worker count, you cannot use the cluster, no matter how many
  workers you request.
- **`Reshuffle` is a fusion breaker, not a skew fix.** Reaching for it
  on a hot key is the most common wasted optimisation in Beam. It costs
  a full shuffle and changes nothing.
- **`CombinePerKey` over `GroupByKey` is almost always right.** The
  exception is when you genuinely need the individual values for a key,
  not an aggregate.
- **Filters are free before a shuffle and expensive after one.** The
  runner fuses a `Filter` into the preceding stage, so filtering early
  genuinely reduces shuffle volume. A `Reshuffle` between the read and
  the filter throws that away.
- **The shard count in a hot key splitter is a compatibility contract.**
  Change it and every historical output becomes incomparable. Pick a
  number, write it down, and keep it.
- **Splitting adds a shuffle.** Do it when the hot key's share of the
  work clearly exceeds the cost of the extra shuffle, not routinely.
- **Watch for the "default key" trap.** The most common hot key in
  production is not a real customer — it is the bucket that every
  unparseable, unkeyed, or defaulted record falls into. Filter those out
  upstream, or at least count them with a metric.
- **`GroupIntoBatches` is for network-bound work, not for skew.** It
  reduces round trips; it does not increase parallelism.

---

## 🔑 Key Takeaways

- **Skew means an uneven key distribution**, so one worker does most of the work while the rest idle. The job cannot be fixed by adding workers.
- **Three shapes**: one hot key, a Zipfian tail, and low key cardinality. The third is a parallelism problem, not a balance problem.
- **The number of distinct keys is your parallelism ceiling.** Count them before optimising anything else.
- **`beam.Reshuffle` adds a `GroupByKey` internally** to force a shuffle and break fusion. It does **not** change the key, and it **breaks timestamp monotonicity** — so it does **not** fix a hot key.
- **The hot key splitter is the real fix**: split the key into `N` deterministic sub-keys before the shuffle, re-merge after. Use a **string** key — a tuple key with mixed component types is silently flattened by Beam's key coder.
- **The re-merge must sum, not count.** `CombinePerKey(sum)` over the shard-stripped key; `Count.PerKey` there counts shards, not elements.
- **Combine before the shuffle.** `CombinePerKey` replaces `GroupByKey` and can cut shuffle volume by orders of magnitude.
- **Filter before the shuffle.** The runner fuses filters, so early filtering reduces the bytes that cross the network.
- **`beam.GroupIntoBatches(batch_size=..., max_buffering_duration_secs=...)`** is a micro-batch transform that changes ordering and output shape — and is not a skew fix.

---

## 📚 Practice Exercises

1. **Count the keys and find the top ten.** Write a Beam job over `sample_data/orders.csv` that reports the ten customers with the most orders, using `beam.combiners.Top.Largest(10)`. Then regenerate the sample data with `--hot-key-rate 0.9` and confirm the top customer now holds 90% of the orders. *Expected answer:* with `--hot-key-rate 0.5` the top customer holds ~2,500 of 5,000 orders; with `0.9` it holds ~4,500.

2. **Prove `Reshuffle` does not change the key.** Build two pipelines over the same input: one that `Reshuffle`s before grouping, one that groups directly. Count the groups and the largest group in each. They must be identical. *Expected answer:* both produce 250 groups with the same maximum group size; the `Reshuffle` version is also measurably slower because it performs an extra shuffle.

3. **Implement a hot key splitter with a fixed shard count.** Write a `split_key` function that derives the shard from `hashlib.sha1(order_id)` modulo 32 and keys by `f"{shard}:{customer}"` (a string, not a tuple). Aggregate per sharded key, then re-merge by stripping the shard and summing with `CombinePerKey(sum)`. Assert that the split result equals the unsplit result for every customer. *Expected answer:* the assertion holds; the split produces 250 × 32 = 8,000 groups instead of 250. Then change the key to a tuple `(shard, customer)` and confirm the assertion fails — that is the tuple-flattening bug the chapter warns about.

4. **Measure the shuffle volume with and without `CombinePerKey`.** Build a pipeline that groups by customer with `GroupByKey` and one that uses `CombinePerKey(sum)`, and inspect the number of elements each stage processes. *Expected answer:* the `GroupByKey` version materialises 5,000 values across 250 groups; the `CombinePerKey` version processes 5,000 inputs but produces 250 partial accumulators — the saving shows up in the shuffle, which is 250 elements instead of 5,000.

5. **Find the "default key" trap.** Write a pipeline that counts how many orders have an empty or unrecognised region, using `beam.Map` to produce a sentinel key for them. *Expected answer:* the sentinel key's count is the number of rows whose region is missing or not in `VALID_REGIONS` — often zero on clean data and large in production, which is exactly the hot key you were looking for.

6. **Micro-batch a sink.** Rewrite a sink step to use `beam.GroupIntoBatches(batch_size=100, max_buffering_duration_secs=30)` and a `DoFn` that takes the list, then compare the wall time and the output ordering against the unbatched version. *Expected answer:* the batched version is faster on a network-bound sink and produces the same elements in a different order; the batch boundaries are visible in the output.

---

## 📖 Further Reading

- Apache Beam: `Reshuffle` API reference — https://beam.apache.org/documentation/sdks/python/apache-beam-transforms-core-py/
- Apache Beam: Combiner transforms (the `CombinePerKey` vs `GroupByKey` guidance) — https://beam.apache.org/documentation/basic-topics/schemas-and-types/
- Apache Beam: `GroupIntoBatches` API reference — https://beam.apache.org/documentation/sdks/python/apache-beam-transforms-core-py/
- Google Cloud Dataflow: Optimizing your pipeline's performance — https://cloud.google.com/dataflow/docs/optimize-performance
- Google Cloud Dataflow: Optimizing a pipeline's performance with data skew (the "hot key" guidance) — https://cloud.google.com/dataflow/docs/optimize-performance
- Google Cloud Dataflow: Using Cloud Monitoring with Dataflow — https://cloud.google.com/dataflow/docs/monitoring
