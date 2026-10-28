# 6.1 — Batch Design Patterns

> **Section 6 · Batch Pipeline Engineering · Lecture 6.1 · 6:30**

## 🎯 What you will learn

- The five canonical batch pipeline shapes, and how to recognise which one you are looking at
- The "filter early" principle: why pushing a `Filter` before a `CombinePerKey` cut the shuffle on the course data by **4.02×**
- The "aggregate early" pattern and the "partition early" pattern, and when each pays
- Side input versus shuffle: the decision that determines whether your join is O(1) or O(n)
- Multi-source flatten and multi-sink fan-out, and what they cost
- The "write many small files" anti-pattern, and the three ways to fix it
- Why the course's own `batch_pipeline.py` filters in the wrong place, and what to write instead

---

## 🧠 Concept

### Why batch has its own design vocabulary

Batch is the mode where the input is bounded and known. That single fact
changes everything about how you design the graph, and the change is not
subtle.

In streaming, you cannot know how many elements will arrive, so you
partition state, cap the accumulators, and design for a world where the
job runs forever. In batch, the input ends. The watermark advances to `+inf`
at the end of the read, every window closes, and the job terminates. That
means:

- **Memory is not the constraint** — the runner can materialise a whole
  partition if it wants to.
- **Restarts are cheap** — you can re-run the job from the beginning.
- **The output is a pure function of the input** — if your transforms are
  deterministic, re-running gives the same answer.

That last property is the one that makes batch design tractable, and it is
the one that people throw away by accident.

The five shapes below are the ones you will meet over and over. They are
not arbitrary: they are the distinct ways of arranging **read**, **filter**,
**join**, **aggregate** and **write** in a graph where the input is bounded.

### The five canonical shapes

#### Shape A — read → transform → write

The simplest. No grouping, no shuffle.

```text
   source ──▶ Parse ──▶ Filter ──▶ Map ──▶ sink
```

Used for: normalisation, reformatting, cleaning, format conversion,
CDC-style upserts into a table. The project has one of these in
`project/streaming_pipeline.py` and the reference lookup is built from it.

Cost: one stage, usually fused into a single worker pass. No network
transfer beyond the read and the write.

The mistake people make here is adding a `CombinePerKey` "for a count". If
all you want is a count of the rows, `beam.combiners.Count.Globally()` is
still a shuffle, but `GroupByKey` on a synthetic key is a much bigger one.

#### Shape B — read → join → aggregate → write

The classic ETL. Two inputs meet, they are joined, and the joined stream is
aggregated.

```text
   orders ───────▶ Parse ──┐
                            ├──▶ Join ──▶ KeyByRegion ──▶ CombinePerKey ──▶ sink
   reference ───▶ Parse ──┘
```

The join is the interesting part, and it has two very different
implementations: a **shuffle join** (`CoGroupByKey` / `GroupByKey` on a
composite key) or a **side-input join** (a small table broadcast to every
worker).

The project uses the side-input variant. See
`project/batch_pipeline.py`:

```python
reference = (
    pipeline
    | "ReadReference" >> ReadFromText(reference_path)
    | "ParseReference" >> beam.Map(_parse_reference_line)
)
orders = orders | "EnrichWithCategory" >> beam.Map(
    _enrich_with_category, reference=beam.pvalue.AsIter(reference)
)
```

That is Shape C, actually — let me be precise and introduce it properly,
because it is the one the course project uses.

#### Shape C — read → enrich → aggregate → write (with a side input)

```text
   orders ────────▶ Parse ──▶ Enrich(+side input) ──▶ Filter ──▶ CombinePerKey ──▶ sink
                                                        ▲
   reference ──▶ Parse ─────────────────────────────────┘  (broadcast)
```

The reference table is small — a few thousand product rows, in the course
project — so it is loaded once into each worker's memory and joined
in-process. No shuffle is required for the join at all.

#### Shape D — multi-source flatten

```text
   source A ──▶ Parse ──┐
                         ├──▶ Flatten ──▶ ... ──▶ sink
   source B ──▶ Parse ──┘
```

Used for: consolidating several files into one table, merging a batch
extract with a stream backlog, reading both a CSV and an NDJSON dump of the
same logical dataset.

#### Shape E — multi-sink fan-out

```text
              ┌──▶ sink 1 (CSV)
   pipeline ──┼──▶ sink 2 (BigQuery)
              └──▶ sink 3 (audit log)
```

Used for: publishing the same result to several consumers. Beam's
immutability makes this free at the graph level — the PCollection is
consumed by several sinks without being re-computed.

### The "filter early" principle

This is the single highest-leverage rule in batch pipeline design, and the
course's own data lets us measure it precisely.

The intuition: a `CombinePerKey` is a **shuffle**. Everything that enters
it crosses the network. Everything that does not enter it does not. So
the size of the set of elements that reach the `CombinePerKey` is
*exactly* the amount of data you shuffle.

Put the filter before the shuffle and you shuffle less. Put it after and
you shuffle everything, then throw most of it away.

Here is the two versions.

**Filter after (the shape in `project/batch_pipeline.py` today):**

```text
   ReadOrders ──▶ ParseOrders ──▶ KeyByRegion ──▶ KeepCompleted ──▶ CombinePerKey
                                  ^^^^^^^^^^^^                        ^^^^^^^^^^^^^
                                  5,000 elements shuffled            1,245 survive
```

**Filter before:**

```text
   ReadOrders ──▶ ParseOrders ──▶ KeepCompleted ──▶ KeyByRegion ──▶ CombinePerKey
                                  ^^^^^^^^^^^^                        ^^^^^^^^^^^^^
                                  1,245 elements shuffled            1,245 survive
```

The numbers, measured on `sample_data/orders.csv`:

| Metric | Filter after | Filter before |
|---|---|---|
| Elements entering the shuffle | 5,000 | 1,245 |
| Elements leaving the shuffle | 1,245 | 1,245 |
| Shuffle reduction | — | **4.02×** |

The two pipelines produce **identical output**. Same counts, same revenue,
to the cent. But one of them ships four times as much data across the
network for nothing.

**4.02×** is `5000 / 1245 = 4.016…`. In a batch job the shuffle is
usually the dominant cost, so this is very close to a 4× reduction in
runtime and in Dataflow worker-hours.

But hold on — is that right? Why doesn't the runner's fusion optimisation
just move the filter anyway?

Because the runner *cannot*. The `CombinePerKey` is a **fusion barrier**:
the elements must be partitioned by key before they can be combined, and
the runner has no freedom to reorder a filter across a key-based
redistribution. The filter is semantically tied to the keying. If the
filter is on the *value* and the key is derived from the same value, the
runner still cannot push it, because moving it would change which worker
sees which element — which changes the pre-shuffle combine grouping, and
in a non-associative combiner, that changes the answer.

So filter placement is *your* decision, and it is a permanent one.

There is a subtlety worth being precise about. The filter in the
"filter after" version runs **after** `KeyByRegion`, so the keying `Map`
and the `CombinePerKey` may fuse into one stage. The filter in the
"filter before" version runs **before** the keying, so the parse, the
filter and the keying may fuse into one stage. Either way the runner
produces two stages in the good case and three in the bad case. The
difference is not the number of stages — it is **how many elements cross
the network**.

That distinction is the whole lesson. Stage count is a proxy; bytes
shuffled is the thing.

#### When filter-early is *not* free

Pushing a filter earlier is not always correct, and there are two real
cases where you must not do it.

**Case 1 — the filter depends on the key.** If the filter predicate
reads the *key* rather than the value, and the keying `Map` is what
derives the key, then filtering before the keying is not merely wasteful,
it is *impossible* — there is no key yet. You have to key first.

**Case 2 — the filter predicate is expensive.** If the predicate costs
more than the shuffle saves (say, it does a regex over a 10 KB string, or
a lookup against a remote service), then filtering before the keying
means running that predicate on 5,000 rows serially on the parsing
workers, while filtering after the keying means running it on the same
5,000 rows but in parallel across the shuffle output workers. This is
rare in practice, but the general rule holds: **push the filter early when
the predicate is cheap, keep it late when the predicate is expensive or
key-dependent.**

The course's `is_valid_order` is a good example of a cheap predicate:
a handful of dict lookups and a float cast. That is exactly the case where
filter-early is free money.

#### The "aggregate early" pattern

Aggregate early means: **reduce the cardinality of your data as soon as
you can, so that later stages carry less.**

The canonical instance is replacing `GroupByKey` with `CombinePerKey`.
`GroupByKey` ships every value under a key across the network and
materialises the whole group on one worker. `CombinePerKey` ships *partial
summaries* — for the course's `RevenueByRegionFn`, a two-field dict of
floats.

```text
   5,000 orders                       5,000 orders
        │                                  │
        ▼                                  ▼
   GroupByKey                        CombinePerKey
   ship 5,000 values                 ship 4 partials
   hold 1,250 per key                hold 1 dict per key
```

There is a second, subtler instance of aggregate-early: **pre-aggregating
before a join**. If you are joining orders to a product reference and then
aggregating by region, but you could aggregate by `(region, product_id)`
first and then join the small result, you have moved the shuffle from
"5,000 rows" to "400 rows". This is the classic *star schema* fact-table
design, expressed as a Beam graph.

The trap: pre-aggregating before a join is only valid if the join does not
change the grouping key. If the reference table could re-classify a row
into a different region, then aggregating by region before the join
produces the wrong answer.

#### The "partition early" pattern

Partition early means: **decide the output partitioning before you do the
expensive work**, so that the expensive work happens in parallel and
naturally lands in the right place.

In Beam, this is most often expressed as writing to a **date-partitioned
output path**:

```text
   orders ──▶ ExtractDate ──▶ CombinePerKey ──▶ WriteToText(
       gs://bucket/revenue/dt=2026-01-15/
   )
```

The critical detail is that the partition must be in the **path**, not just
in a column. If the partition is a column, the sink still writes one big
file and you have gained nothing at the file level. If the partition is in
the path, the sink produces many small files that are independently
readable, independently deletable, and independently re-writable — which
is what makes a safe backfill possible (chapter 6.5).

Partitioning early also means *hash* partitioning for parallelism: a
`Reshuffle` after a `GroupByKey` spreads the grouped output so that the
downstream per-key work is balanced. Both are "partition early" in the
sense that they fix the data layout before the expensive stage.

#### Side input versus shuffle

This is the decision that determines whether a join is O(n) or O(1) in
network transfer.

| | Side input | Shuffle join |
|---|---|---|
| Mechanism | small table broadcast to every worker | `CoGroupByKey` on a composite key |
| Network cost | table size × worker count | proportional to the join cardinality |
| Memory on each worker | the whole side table | one group at a time |
| Requires the left side to be small? | no | no |
| Requires the *right* side to be small? | **yes** | no |
| Late data / streaming | snapshot at window start | live |

The rule: **if one side of the join fits comfortably in the memory of every
worker (say, under 100 MB), use a side input. Otherwise use a shuffle
join.**

The course project's reference table is a side input. `_enrich_with_category`
does a **linear scan** of the reference list for every order:

```python
def _enrich_with_category(order: dict, reference: list[dict]) -> dict:
    product_id = order.get("product_id")
    for row in reference:
        if row.get("product_id") == product_id:
            order["category"] = row.get("category", "unknown")
            return order
    order["category"] = "unknown"
    return order
```

That is O(n) per order — 5,000 × 2,000 = 10 million comparisons in this
course's dataset. Fine at this size; a genuine performance bug at
production scale. The production version would build a dict once:

```python
def _enrich_with_category(order: dict, reference: dict[str, str]) -> dict:
    """Attach a product category to an order using a side input."""
    order["category"] = reference.get(order.get("product_id"), "unknown")
    return order
```

with the side input built as a `beam.pvalue.AsDict` PCollection:

```python
reference = (
    pipeline
    | "ReadReference" >> ReadFromText(reference_path)
    | "ParseReference" >> beam.Map(_parse_reference_line)
    | "KeyByProductId" >> beam.Map(lambda row: (row["product_id"], row))
)
orders = orders | "EnrichWithCategory" >> beam.Map(
    _enrich_with_category, reference=beam.pvalue.AsDict(reference)
)
```

Note that `beam.pvalue.AsDict` is a **wrapper, not a transform**. You
construct it with the PCollection — `beam.pvalue.AsDict(reference)` — and
pass it as the side-input argument. It is exactly the right tool for
"small lookup table, broadcast to everyone", and exactly the wrong tool
for a table that does not fit in worker memory.

The decision rule again, in one line: **a side input is a broadcast; a
shuffle is a redistribution.** If you can afford the broadcast, the
broadcast is almost always faster, because it costs zero shuffles.

### Multi-source flatten: when it is free and when it is not

`beam.Flatten` merges a tuple of PCollections into one. It adds no shuffle
of its own. The cost comes from the fact that merging two *independent
sources* forces a materialisation — the runner must read both sources and
combine them before the downstream can proceed.

```text
   source A ──▶ Map ──┐
                       ├──▶ Flatten ──▶ Map ──▶ sink     (one read, fusible)
   source A ──▶ Map ──┘

   source A ──▶ Map ──┐
                       ├──▶ Flatten ──▶ Map ──▶ sink     (two reads, one merge)
   source B ──▶ Map ──┘
```

The rule from chapter 2.5 applies: a `Flatten` that merges two branches of
the *same* source fuses; a `Flatten` that merges two different sources
does not.

In batch, the practical concern with flatten is **partitioning**. Two
files in two directories, one with a date partition and one without, will
not be read in a compatible way by a downstream date-partitioned sink.
Flatten them and the sink has to cope with rows that have no partition —
which in practice means the sink writes them to a default partition, and
the backfill logic later cannot find them.

#### The multi-source flatten in a batch backfill

A common real pattern: process the *live* partition plus a *backfill*
partition in one job, so the aggregate is complete.

```text
   live/2026-01-15/ ──▶ Parse ──┐
                                 ├──▶ Flatten ──▶ CombinePerKey ──▶ write
   backfill/2026-01-08/ ─▶ Parse ┘
```

This works, and it is the right way to produce a corrected aggregate over a
period. But it is *not* the same as writing the backfill partition
separately — see chapter 6.5 for why the separate write is safer.

### Multi-sink fan-out

Beam PCollections are immutable, so consuming the same PCollection from
three sinks does not re-compute it. The graph is:

```text
                          ┌──▶ WriteToText(csv)
   rows ──▶ FormatCsv ────┼──▶ WriteToBigQuery(table)
                          └──▶ WriteToText(audit)
```

Each sink is an independent write. The costs are real, though:

- **BigQuery load jobs cost money per load.** Three sinks that each do a
  load is three times the cost.
- **A failing sink fails the job.** If the audit sink's bucket does not
  exist, the whole pipeline fails, even though the primary sink succeeded.
  In Dataflow this means the primary write is rolled back too, because
  Dataflow's exactly-once processing guarantee applies to the whole graph.
- **Sink write times differ.** The CSV write finishes in 3 seconds; the
  BigQuery load takes 4 minutes. The job does not complete until the
  slowest one does.

The production discipline: **the primary sink and the secondary sinks must
be independent jobs**, not independent branches of one job. If the audit
trail is not important enough to fail the revenue report, it must not be in
the same pipeline.

There is one exception, and it is important: a **local** sink that cannot
fail (a `beam.Map(print)` for debugging, or a metrics counter) is fine in
the same job.

### The "write many small files" anti-pattern

This is the single most common way a Beam batch job goes wrong in
production, and it fails *quietly* — the job is green, the data is correct,
and then three weeks later the downstream job cannot read it.

The cause: the default `num_shards` for a Beam file sink is chosen by the
runner based on the input size, and for a small input it is often 1. For a
large input it can be very large. Meanwhile, a `CombinePerKey` produces one
element per key, so the sink writes one file per worker.

```text
   4 regions → 4 elements → 4 files
   40,000 product_ids → 40,000 elements → 40,000 files
```

Forty thousand files in a GCS bucket causes real problems:

| Problem | Detail |
|---|---|
| Listing cost | GCS `LIST` on 40,000 objects is slow and expensive; the first read of a prefix takes minutes |
| `gsutil cp` / `gcloud storage cp` | Thousands of per-object HTTP requests, rate-limited |
| Hive/Spark reads | Thousands of small files means thousands of split tasks; the job spends all its time on task scheduling |
| Deletion | A backfill that has to delete a partition touches 40,000 objects |
| Cost | GCS LIST and GET operations are billed per request; 40,000 files × 20 downstream reads is 800,000 requests |

There are three fixes, and in practice you want the first two together.

**Fix 1 — control the shard count.** `WriteToText` takes `num_shards`:

```python
rows | "WriteSummaryCsv" >> WriteToText(
    output_path,
    header="region,order_count,revenue_eur",
    num_shards=1,
    shard_name_template="",
)
```

The course project already does this, and it is why the summary is a
single file called exactly `out/summary` rather than
`out/summary00000of00001`.

But `num_shards=1` is only right when the output is genuinely small. For a
million-row output you want `num_shards=0` (runner-chosen) or a number
matched to your parallelism — the rule of thumb is one shard per 100–500 MB.

**Fix 2 — write to a partitioned prefix.** Many small files *inside a
partition* is fine; many small files *at the root of a shared prefix* is
not. Partitioning by data date gives you:

```text
gs://bucket/revenue/dt=2026-01-15/part-00000-of-00004
gs://bucket/revenue/dt=2026-01-15/part-00001-of-00004
```

Four files per day, and the partition as a unit can be listed, read,
replaced or deleted in one operation.

**Fix 3 — compact after the fact.** `gcloud storage cp --recursive` with a
wildcard, or a `gsutil compose` operation, merges the shards. This is the
fallback when you did not control the shard count at write time.

The general rule: **the number of output files should be a function of the
output size, not of the number of keys or the number of workers.** If your
output is four regions, one file is right. If your output is four million
rows, four files of a megabyte each is wrong — you want roughly forty
files of a hundred megabytes each.

### What the course project gets right and wrong

`project/batch_pipeline.py` today:

```text
   ReadOrders ──▶ ParseOrders ──▶ KeyByRegion ──▶ KeepCompletedOrders ──▶ RevenueByRegion
```

The filter is in the wrong place — it should be before `KeyByRegion` —
and that is a real 4.02× shuffle cost on the course data.

But there is a subtlety that makes this less obvious than it looks.
`ParseOrderFn` already calls `is_valid_order`, which validates the row
completely. So the pipeline's `KeepCompletedOrders` filter is a *status*
filter, not a validity filter — it removes rows whose status is not
`complete`, and the project wants that to be **configurable** at runtime
(`--statuses complete,active`).

So the correct fix is not to move the existing filter. It is to split the
concern in two:

```text
   ReadOrders ──▶ ParseOrders ──▶ KeepValid ──▶ KeepStatus ──▶ KeyByRegion ──▶ RevenueByRegion
```

with `KeepValid` doing the cheap validation (which `ParseOrderFn` already
does, so it can stay inside the parse) and `KeepStatus` doing the
status selection before the keying.

That is exactly what the hands-on below does.

---

## 🧠 The cost model in one table

Before the hands-on, here is the whole chapter compressed into a cost
comparison you can reason from.

| Stage | What it costs | Dominant at 5,000 rows | Dominant at 5 billion rows |
|---|---|---|---|
| `Parse` (Map/ParDo) | CPU, serialisation | ~0 | ~0 (parallel) |
| `Filter` before keying | CPU only | negligible | negligible |
| `Filter` after keying | **network** | negligible | **dominant** |
| `KeyByRegion` (Map) | CPU | ~0 | ~0 |
| `CombinePerKey` | **network + memory** | small | **dominant** |
| `GroupByKey` | network + **memory** | small | **dominant + OOM risk** |
| Side input join | worker memory | ~0 | **dominant** if the table is big |
| `WriteToText` | network + object count | ~0 | **dominant** if shards are many |

The pattern: at small scale everything is CPU and nothing is interesting.
At large scale, network and object count dominate everything else. Every
design rule in this chapter is really a rule about moving work off the
network and off the object count.

---

## 🛠️ Hands-On: Filter-After vs Filter-Before, Measured

### Setup

```bash
cd data-engineering/data-Course/google/Dataflow
source .venv/bin/activate
python resources/sample_data.py --output-dir ./sample_data
wc -l sample_data/orders.csv
```

You should see `5001 sample_data/orders.csv` — 5,000 data rows plus a
header.

### Step 1 — count what the shuffle would carry

The shuffle in a `CombinePerKey` carries the elements that enter it. So
"how many elements enter the keying stage" is the right measurement. Build
a script that counts the elements at that point in two different graphs.

Create `hands_on_filter_position.py`:

```python
"""Measure how many elements reach the shuffle in two pipeline shapes."""
import shutil
import sys
from pathlib import Path

import apache_beam as beam

sys.path.insert(0, str(Path(__file__).resolve().parent / "project"))

from transforms import ParseOrderFn

INPUT = "./sample_data/orders.csv"
OUT_FILTER_FIRST = "./out/hands_on/shuffle_filter_first"
OUT_FILTER_LAST = "./out/hands_on/shuffle_filter_last"


def count_elements(pipeline, *, filter_before_keying):
    """Count the elements that enter the keyed stage.

    When `filter_before_keying` is True the filter runs before the keying
    Map, so only the surviving elements are keyed — and only those cross
    the shuffle. When it is False the keying Map runs first, so every
    element is keyed and every element is shuffled.

    The count is taken on the *keyed* PCollection, because that is the
    one whose elements cross the network.
    """
    lines = pipeline | "ReadOrders" >> beam.io.ReadFromText(INPUT)
    orders = lines | "ParseOrders" >> beam.ParDo(ParseOrderFn())

    if filter_before_keying:
        keyed = (
            orders
            | "KeepCompleteFirst" >> beam.Filter(
                lambda order: order["status"] == "complete"
            )
            | "KeyByRegionFirst" >> beam.Map(
                lambda order: (order["region"], order)
            )
        )
    else:
        keyed = orders | "KeyByRegionLast" >> beam.Map(
            lambda order: (order["region"], order)
        )
        keyed | "KeepCompleteLast" >> beam.Filter(
            lambda pair: pair[1]["status"] == "complete"
        )

    # Count the *keyed* PCollection: those are the elements that cross
    # the network into the aggregation.
    total = keyed | "CountElements" >> beam.combiners.Count.Globally()
    return total


def main():
    for name, output, before in (
        ("filter-first", OUT_FILTER_FIRST, True),
        ("filter-last", OUT_FILTER_LAST, False),
    ):
        shutil.rmtree(output, ignore_errors=True)
        with beam.Pipeline() as pipeline:
            counted = count_elements(pipeline, filter_before_keying=before)
            (
                counted
                | f"Write{name}" >> beam.io.WriteToText(
                    output, num_shards=1, shard_name_template=""
                )
            )
        with open(output, encoding="utf-8") as handle:
            print(f"{name}: {handle.read().strip()} elements enter the shuffle")


if __name__ == "__main__":
    main()
```

Run it:

```bash
python hands_on_filter_position.py
```

Expected output:

```text
filter-first: 1245 elements enter the shuffle
filter-last: 5000 elements enter the shuffle
```

The **answer** is identical in both cases — 1,245 complete orders. The
**cost** is not: 5,000 elements cross the shuffle in the second graph and
1,245 in the first.

Compute the saving:

```bash
python -c "print(f'{5000/1245:.2f}x')"
```

```text
4.02x
```

That is the real, measured shuffle saving on the course data: **4.02×**.

### Step 2 — verify the two pipelines produce identical output

The saving is only worth having if the answer is unchanged. Build both
full pipelines and diff the results.

Create `hands_on_two_shapes.py`:

```python
"""Two shapes of the same pipeline; the output must be byte-identical."""
import shutil
import sys
from pathlib import Path

import apache_beam as beam

sys.path.insert(0, str(Path(__file__).resolve().parent))

from transforms import (
    ParseOrderFn,
    RevenueByRegionFn,
    format_summary_csv,
    to_summary_row,
)

INPUT = "./sample_data/orders.csv"
OUT_FILTER_FIRST = "./out/hands_on/summary_filter_first"
OUT_FILTER_LAST = "./out/hands_on/summary_filter_last"


def build(pipeline, output_path, *, filter_before_keying):
    """Build the revenue pipeline in one of the two shapes."""
    lines = pipeline | "ReadOrders" >> beam.io.ReadFromText(INPUT)
    orders = lines | "ParseOrders" >> beam.ParDo(ParseOrderFn())

    if filter_before_keying:
        # Filter first, then key: only the survivors are keyed, and only
        # the survivors cross the shuffle.
        survivors = (
            orders
            | "KeepCompleteFirst" >> beam.Filter(
                lambda order: order["status"] == "complete"
            )
            | "KeyByRegionFirst" >> beam.Map(
                lambda order: (order["region"], order)
            )
        )
    else:
        # Key first, then filter: every order is keyed, so every order is
        # shuffled. The filter removes 3,755 of them afterwards.
        keyed = orders | "KeyByRegionLast" >> beam.Map(
            lambda order: (order["region"], order)
        )
        survivors = keyed | "KeepCompleteLast" >> beam.Filter(
            lambda pair: pair[1]["status"] == "complete"
        )

    summary = survivors | "RevenueByRegion" >> beam.CombinePerKey(RevenueByRegionFn())

    (
        summary
        | "ToFlatRow" >> beam.Map(to_summary_row)
        | "FormatCsv" >> beam.Map(format_summary_csv)
        | "WriteSummary" >> beam.io.WriteToText(
            output_path,
            header="region,order_count,revenue_eur",
            num_shards=1,
            shard_name_template="",
        )
    )


def main():
    for name, output, before in (
        ("filter_first", OUT_FILTER_FIRST, True),
        ("filter_last", OUT_FILTER_LAST, False),
    ):
        shutil.rmtree(output, ignore_errors=True)
        with beam.Pipeline() as pipeline:
            build(pipeline, output, filter_before_keying=before)

    first = open(OUT_FILTER_FIRST, encoding="utf-8").read().splitlines()
    last = open(OUT_FILTER_LAST, encoding="utf-8").read().splitlines()
    print("filter-first output:")
    for line in sorted(first):
        print(" ", line)
    print("filter-last output:")
    for line in sorted(last):
        print(" ", line)
    # A `CombinePerKey` produces a shuffled output with no ordering
    # guarantee, so the two files are compared as *sets* of lines.
    print("IDENTICAL" if sorted(first) == sorted(last) else "DIFFERENT")


if __name__ == "__main__":
    main()
```

Run it:

```bash
python hands_on_two_shapes.py
```

Expected:

```text
filter-first output:
  AMER,318,113592.19
  APAC,285,108194.92
  EMEA,322,118423.22
  LATAM,320,110646.18
  region,order_count,revenue_eur
filter-last output:
  AMER,318,113592.19
  APAC,285,108194.92
  EMEA,322,118423.22
  LATAM,320,110646.18
  region,order_count,revenue_eur
IDENTICAL
```

Note that the two files may list the regions in a *different order* from
run to run — `CombinePerKey` produces a shuffled output with no ordering
guarantee. That is why the comparison is done on sorted lines.

The same check from the shell:

```bash
sort out/hands_on/summary_filter_first > /tmp/ff.txt
sort out/hands_on/summary_filter_last > /tmp/fl.txt
diff /tmp/ff.txt /tmp/fl.txt && echo "MATCH"
```

### Step 3 — read the two job graphs

The stage structure is visible in the pipeline description. Build both
graphs and print them:

```python
import apache_beam as beam

for before in (True, False):
    p = beam.Pipeline()
    lines = p | "ReadOrders" >> beam.io.ReadFromText("./sample_data/orders.csv")
    orders = lines | "ParseOrders" >> beam.Map(lambda line: line)
    if before:
        kept = orders | "KeepCompleteFirst" >> beam.Filter(
            lambda line: ",complete," in line
        )
        keyed = kept | "KeyByRegionFirst" >> beam.Map(lambda line: ("k", line))
    else:
        keyed = orders | "KeyByRegionLast" >> beam.Map(lambda line: ("k", line))
        keyed | "KeepCompleteLast" >> beam.Filter(
            lambda pair: ",complete," in pair[1]
        )
    keyed | "Revenue" >> beam.CombinePerKey(sum)
    print("filter before keying:" if before else "filter after keying:")
    print(p)
    print()
```

What you are looking for is *where the shuffle boundary falls*. In the
filter-first graph, the `Filter` and the keying `Map` sit on the same side
of the `CombinePerKey`. In the filter-last graph, the `Filter` sits on the
other side — after the redistribution.

### Step 4 — the side-input enrichment, done the right way

The project enriches orders with a product category using a side input,
but scans the list linearly. Build the dict version and measure the
difference.

Create `hands_on_side_input.py`:

```python
"""Enrich orders with a product category using a side input."""
import json
import shutil
import sys
from pathlib import Path

import apache_beam as beam

sys.path.insert(0, str(Path(__file__).resolve().parent / "project"))

from transforms import ParseOrderFn

ORDERS = "./sample_data/orders.csv"
REFERENCE = "./sample_data/product_reference.ndjson"
OUTPUT = "./out/hands_on/enriched"


def parse_reference_line(line):
    """Parse one JSON reference line."""
    text = line.strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def enrich(order, categories):
    """Attach a category using a dict lookup."""
    order["category"] = categories.get(order.get("product_id"), "unknown")
    return order


def main():
    shutil.rmtree(OUTPUT, ignore_errors=True)

    with beam.Pipeline() as pipeline:
        lines = pipeline | "ReadOrders" >> beam.io.ReadFromText(ORDERS)
        orders = lines | "ParseOrders" >> beam.ParDo(ParseOrderFn())

        # The reference table is keyed by product_id, so it can be turned
        # into a dict on every worker.
        reference = (
            pipeline
            | "ReadReference" >> beam.io.ReadFromText(REFERENCE)
            | "ParseReference" >> beam.Map(parse_reference_line)
            | "KeyByProductId" >> beam.Map(
                lambda row: (row.get("product_id"), row.get("category", "unknown"))
            )
        )

        # `AsDict` is a *side-input wrapper*, not a transform. You pass it
        # the PCollection as an argument — it is not applied with `>>`.
        enriched = orders | "EnrichWithCategory" >> beam.Map(
            enrich, categories=beam.pvalue.AsDict(reference)
        )

        (
            enriched
            | "Format" >> beam.Map(
                lambda order: f"{order.get('product_id')},{order.get('category')}"
            )
            | "Write" >> beam.io.WriteToText(
                OUTPUT, num_shards=1, shard_name_template=""
            )
        )

    with open(OUTPUT, encoding="utf-8") as handle:
        lines = handle.read().splitlines()
    print(f"enriched {len(lines)} orders")
    for line in sorted(lines)[:5]:
        print(" ", line)


if __name__ == "__main__":
    main()
```

Run it:

```bash
python hands_on_side_input.py
```

Expected shape:

```text
enriched 5000 orders
  p0000,cat-00
  p0000,cat-00
  p0000,cat-00
  p0001,cat-01
  p0001,cat-01
```

(The product ids repeat because the sample generator picks from a small
product pool.)

Note what did **not** happen: there is no shuffle. The reference table was
broadcast to the workers as a dict. That is the entire point of the side
input — a join that costs zero network transfer.

> **A note on the `AsDict` API.** `beam.pvalue.AsDict` is a *wrapper*, not
> a transform. `beam.pvalue.AsDict(reference)` takes the PCollection as a
> constructor argument. Writing `reference | "ToDict" >> beam.pvalue.AsDict()`
> raises:
>
> ```text
> TypeError: AsSideInput.__init__() missing 1 required positional argument: 'pcoll'
> ```
>
> The same is true of `AsIter`, `AsSingleton`, `AsList` and `AsMultiMap`.

Compare with the project's linear-scan version, which is O(orders ×
reference rows):

```bash
wc -l sample_data/product_reference.ndjson
```

With 50 reference rows and 5,000 orders that is 250,000 string
comparisons in a single-threaded Python loop. The dict version does 5,000
hash lookups. At production scale — 50 million orders, 2 million
products — the difference is 10^14 comparisons versus 5×10^7 lookups.

### Step 5 — multi-sink fan-out, and why it should be two jobs

Build the fan-out and then think about what happens when one sink fails.

Create `hands_on_fanout.py`:

```python
"""One pipeline, three sinks."""
import shutil

import apache_beam as beam

INPUT = "./sample_data/orders.csv"
CSV_OUTPUT = "./out/hands_on/fanout_csv"
AUDIT_OUTPUT = "./out/hands_on/fanout_audit"


def main():
    for path in (CSV_OUTPUT, AUDIT_OUTPUT):
        shutil.rmtree(path, ignore_errors=True)

    with beam.Pipeline() as pipeline:
        lines = pipeline | "ReadOrders" >> beam.io.ReadFromText(INPUT)
        orders = lines | "ParseOrders" >> beam.Map(
            lambda line: line.split(",")
        )

        # Sink 1: the primary, human-readable summary.
        (
            orders
            | "FormatSummary" >> beam.Map(
                lambda row: f"{row[3]},{row[6]},{row[7]}"
            )
            | "WriteCsv" >> beam.io.WriteToText(
                CSV_OUTPUT, num_shards=1, shard_name_template=""
            )
        )

        # Sink 2: an audit trail of the raw rows.
        (
            orders
            | "FormatAudit" >> beam.Map(lambda row: ",".join(row))
            | "WriteAudit" >> beam.io.WriteToText(
                AUDIT_OUTPUT, num_shards=1, shard_name_template=""
            )
        )

        # Sink 3: a metric, not a file.
        (
            orders
            | "CountRows" >> beam.combiners.Count.Globally()
            | "LogCount" >> beam.Map(
                lambda count: print(f"rows seen: {count}")
            )
        )


if __name__ == "__main__":
    main()
```

Run it:

```bash
python hands_on_fanout.py
```

The three sinks all work. But now imagine the audit bucket does not exist.
The job fails — and because Dataflow's exactly-once guarantee covers the
whole graph, the primary CSV write is rolled back too.

The production version is two jobs:

```text
Job 1 (critical):  orders ──▶ WriteToBigQuery(revenue_summary)
Job 2 (best-effort): orders ──▶ WriteToText(audit)
```

with job 2 scheduled independently and its failures ignored by whatever
sits downstream.

### Step 6 — check the output file count

The "many small files" problem is measurable. Look at how many files a
sink produces.

```bash
ls -1 out/hands_on/ | head -20
ls -1 out/hands_on/ | wc -l
```

The course project pins `num_shards=1` and `shard_name_template=""`, so
you get exactly one file per sink. Remove those two arguments and the
runner picks its own shard count:

```python
# Before: exactly one file, at exactly this path.
rows | "WriteSummaryCsvPinned" >> beam.io.WriteToText(
    output_path,
    header="region,order_count,revenue_eur",
    num_shards=1,
    shard_name_template="",
)

# After: the runner chooses, and the path gets a suffix.
rows | "WriteSummaryCsvRunner" >> beam.io.WriteToText(
    output_path,
    header="region,order_count,revenue_eur",
)
```

The second form writes `summary00000of00001`, `summary00001of00001`, …
The count depends on the runner and the parallelism. On Dataflow with 100
workers and a large output, that is 100 files per sink — which is fine —
but a `CombinePerKey` over 40,000 keys with `num_shards=0` is where the
anti-pattern starts.

The rule to remember: **pin the shard count when the output is small and
known; let the runner choose when the output is large and unknown; never
let the output file count be a function of your key count.**

---

## 🛠️ Common Errors and Fixes

### `RuntimeError: Transform name is already used`

The two shapes in the hands-on both use `"ReadOrders"`. They are in
different functions, so they are different pipelines — that is fine. But
two transforms with the same label **inside one function** collide:

```text
RuntimeError: Transform name is already used
```

The message does not say which pair. Catch it statically:

```bash
python resources/audit_course.py
```

### `KeyError: 'status'` after moving the filter

You moved the `Filter` before the parse, so the elements are still raw
CSV lines, not dicts:

```text
KeyError: 'status'
```

The filter must come *after* the parse. The order is: read → parse →
filter → key → combine.

### `TypeError: AsSideInput.__init__() missing 1 required positional argument: 'pcoll'`

`beam.pvalue.AsDict` is a **wrapper**, not a transform. You construct it
with the PCollection, you do not apply it with `>>`:

```python
# WRONG: AsDict is not a PTransform
reference = (
    pipeline
    | "ReadReferenceWrong" >> ReadFromText(path)
    | "ToDict" >> beam.pvalue.AsDict()
)

# RIGHT: AsDict wraps the PCollection and is passed as an argument
reference = (
    pipeline
    | "ReadReference" >> ReadFromText(path)
    | "KeyByProductId" >> beam.Map(lambda row: (row["product_id"], row))
)
orders | "Enrich" >> beam.Map(
    _enrich_with_category, reference=beam.pvalue.AsDict(reference)
)
```

### `ValueError: Cannot combine ... with itself` when flattening

You flattened a `GroupByKey` output with a non-`GroupByKey` output. The
shapes differ: `(key, iterable)` versus `(key, scalar)`.

### `TypeError: 'int' object is not subscriptable`

`beam.combiners.Count.Globally()` produces a **scalar**, not a list of one
value. Do not unwrap it:

```python
# WRONG
counted | "ExtractCount" >> beam.Map(lambda counts: counts[0])

# RIGHT
counted | "LogCount" >> beam.Map(lambda count: print(f"rows seen: {count}"))
```

(`beam.CombineGlobally(sum)` *does* produce a one-element list, which is
where the confusion comes from. `Count.Globally` is a dedicated combiner
with its own semantics.)

### `TypeError: 'str' object has no attribute 'get'` in the enrichment step

The side input is fine; the *order* is not. You are still passing raw CSV
strings into the enrichment function, which expects a parsed dict. Parse
first:

```python
orders = lines | "ParseOrders" >> beam.ParDo(ParseOrderFn())
```

### The output row order changed between runs

Expected. `CombinePerKey` produces a shuffled output with no ordering
guarantee. Compare sorted output, never raw output:

```bash
sort out/a > /tmp/a.txt && sort out/b > /tmp/b.txt && diff /tmp/a.txt /tmp/b.txt
```

### The output file is not where you expected it

`WriteToText` writes a *prefix*. With `num_shards=1` and
`shard_name_template=""` the file is at the exact prefix. Without those,
the file is `<prefix>00000of00001`. Never hard-code either; always glob:

```bash
cat out/hands_on/summary*
```

### `FileNotFoundError` when writing to a new prefix

The parent directory must exist or be creatable:

```bash
mkdir -p out/hands_on
```

### The filter-first pipeline is *slower* on a tiny dataset

At 5,000 rows the shuffle is free and the extra stage costs a little. This
is expected: the saving is proportional to the data volume, and the cost
is a constant. Filter-early is a decision that pays at scale, not at
course scale. Measure at realistic scale, or reason from the element
counts as the hands-on does.

---

## 💡 Production Notes

- **The shuffle is the budget.** On Dataflow, network transfer inside a
  region is cheap per GB but the shuffle also determines how many worker
  hours you burn. A 4× reduction in shuffled elements on a job that runs
  200 vCPU-hours is roughly 50 vCPU-hours saved — around $50 at $1/vCPU-hour
  for the n1-standard worker family, plus the shuffle processing overhead
  which is typically another 30% of the job cost.
- **Filter before the keying, always, when the predicate is cheap and does
  not read the key.** This is the default. The exception — a key-dependent
  or expensive predicate — is rare enough that it should be a comment in
  the code, not an accident.
- **Watch the "filter after the join" case.** `Join → Filter → Combine`
  is much harder to fix than `Filter → Join → Combine`, because the filter
  is on the joined result. If you can push the predicate back before the
  join, do.
- **A side input is a broadcast and it costs worker memory.** The rule of
  thumb is under 100 MB per worker. Above that, use a shuffle join. Note
  that Dataflow workers have a fixed memory budget — exceeding it kills
  the worker, retries the bundle, and eventually fails the job with a
  `ProcessExit` or OOM that looks nothing like a memory problem.
- **The side input is a snapshot.** In a streaming pipeline, the side
  input is read once at the start of the window, not per element. If the
  reference data changes mid-window, the change is not seen until the next
  window. This is a correctness trap in enrichment pipelines.
- **`num_shards=1` is a correctness decision for small outputs and a
  performance bug for large ones.** Know which one you are.
- **Multi-sink fan-out inside one job couples the sinks' fates.** Dataflow
  rolls back every sink when any sink fails. If one sink is optional, it
  belongs in a different job.
- **BigQuery load jobs are per-load billed.** A fan-out to two BigQuery
  tables is two load jobs, two schema validations, and two sets of
  streaming buffer inserts. Budget for it.
- **Watch the element count, not just the runtime.** A job that suddenly
  shuffles 10× more elements than yesterday is usually a filter that
  stopped matching — a producer changed a status value, or a currency
  code. Put a counter on the pre-shuffle stage and alert on the ratio.
- **A `CombinePerKey` over a high-cardinality key is a `GroupByKey` in
  disguise.** If your key is `order_id`, you have written a distributed
  `DISTINCT`. Think about whether you want a per-region aggregate (4 keys)
  or a per-order lookup (5,000 keys) — the second is a different pipeline
  shape and a different sink strategy.

---

## 🔑 Key Takeaways

- Five canonical batch shapes: read-transform-write, read-join-aggregate-write,
  read-enrich-aggregate-write (side input), multi-source flatten, multi-sink
  fan-out. Recognising the shape tells you where the cost is.
- **Filter early.** On the course data, 1,245 of 5,000 orders reach the
  aggregation — a **4.02× shuffle saving** with byte-identical output. The
  filter's position relative to the `CombinePerKey` is your decision, not
  the runner's, because the key-based redistribution is a fusion barrier.
- **Aggregate early**: replace `GroupByKey` with `CombinePerKey` so the
  shuffle carries summaries, not values. Pre-aggregate before a join when
  the join cannot change the grouping key.
- **Partition early**: put the output partition in the *path*, not a
  column. That is what makes a partition independently readable,
  replaceable and deletable — and therefore backfillable.
- **Side input versus shuffle**: a side input is a broadcast (O(worker
  memory), zero shuffles) and requires a *small* right-hand table; a
  shuffle join is a redistribution and scales to any size.
- **Multi-sink fan-out is free in the graph but couples the sinks'
  fates.** Dataflow rolls back every sink when any one fails, so optional
  sinks belong in separate jobs.
- **The "many small files" anti-pattern fails silently.** Pin
  `num_shards` when the output size is known, partition by date when it is
  not, and never let the file count be a function of your key count.

---

## 📚 Practice Exercises

1. **Measure the saving at three filter positions.** Build three versions of
   the revenue pipeline — filter before the parse, between the parse and
   the keying, and after the keying — and count the elements that enter
   the `CombinePerKey` in each. *Expected:* the first is 5,000 (the filter
   cannot precede the parse, because the elements are strings), the second
   is 1,245, and the third is 5,000. The second position is the only one
   that pays.

2. **Break the side input.** Convert the reference table to 500,000 rows
   and re-run the enrichment. Then convert the side input to a shuffle
   join with `beam.CoGroupByKey` and compare the two. *Expected:* the
   side-input version gets slower per element (a linear or dict lookup
   against a large table on every worker) but performs no shuffle; the
   `CoGroupByKey` version performs a shuffle but keeps worker memory
   bounded. Explain which one you would pick at 50 million orders and
   2 million products.

3. **Prove the outputs are identical.** Extend the hands-on's Step 2 to
   compare the two summaries as *sets* of lines, and then deliberately
   change one pipeline to filter on `"complete"` **and** `"EUR"` and
   confirm the diff catches it. *Expected:* the diff reports exactly one
   changed row — the region whose revenue changed when the currency
   filter was added.

4. **Fix the project.** Move the status filter in `project/batch_pipeline.py`
   to before the `KeyByRegion` step, keeping `--statuses` configurable.
   Then re-run `python3 -m pytest project/tests/ -v` and confirm the suite
   still passes, including `test_filtered_statuses`. *Expected:* all tests
   pass; the AMER row becomes `AMER,2,1049.0` in the `test_filtered_statuses`
   case exactly as before, because the cancelled order is still included
   when `cancelled` is in the requested statuses.

5. **Count the files.** Write a pipeline that writes 40,000 rows to a
   `WriteToText` sink with `num_shards=0`, and one with `num_shards=4`.
   List the files in each output directory. *Expected:* the first writes
   the runner-chosen number of shards (often 1 locally, more on Dataflow);
   the second writes exactly 4. Then explain what happens to a downstream
   Hive query over the first directory.

6. **Reflection.** A pipeline reads a 12 TB daily extract, joins it to a
   40 MB dimension table, and aggregates by `customer_id` (18 million
   distinct values). Which of the five shapes is it, where is the shuffle,
   and what would you change to make it tractable? *Expected:* it is
   Shape C (read-enrich-aggregate-write); the join is a side input (40 MB
   is fine) but the aggregation key is high-cardinality, so the
   `CombinePerKey` produces 18 million output rows and the sink will
   write 18 million small files. The fix is to aggregate at a lower
   cardinality (by region and date), or to write to a partitioned prefix
   with a controlled shard count.

---

## 📖 Further Reading

- Apache Beam: Transforming keyed collections — https://beam.apache.org/documentation/programming-guide/#transforms
- Apache Beam: Element type and schemas — https://beam.apache.org/documentation/programming-guide/#element-types
- Apache Beam: Side inputs — https://beam.apache.org/documentation/programming-guide/#side-inputs
- Apache Beam: File naming and sharding — https://beam.apache.org/documentation/programming-guide/#file-naming
- Google Cloud Dataflow: Optimise aggregation with CombinePerKey — https://cloud.google.com/dataflow/docs/optimize-aggregates
- Google Cloud Dataflow: Dynamic work rebalancing — https://cloud.google.com/dataflow/docs/guides/dynamic-work-rebalancing
