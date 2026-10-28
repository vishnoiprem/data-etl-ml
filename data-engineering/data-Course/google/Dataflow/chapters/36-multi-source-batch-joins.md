# 6.7 — Multi-Source Batch Joins & Enrichment

> **Section 6 · Batch Pipeline Engineering · Lecture 6.7 · 6:30**

## 🎯 What you will learn

- The four join mechanisms in Beam, and the one question that decides between them
- Why **most batch joins do not need a shuffle at all**, and when the ones that do are worth it
- **Side inputs** as a broadcast: how they work, what they cost, and where the memory ceiling is
- **`CoGroupByKey`** as a keyed join: one shuffle, correct when both sides are large
- The manual `GroupByKey` + `Flatten` form, and why you should almost never hand-roll it
- Pushing the join into **BigQuery** with `additional_bq_parameters`, and when that beats both
- The **fan-out / duplicate-read trap**: reading the same file twice and flattening the results
- **Full-refresh vs. incremental joins** over a changing dimension table, and the idempotency argument
- Six real error messages you will hit, each with the exact fix
- The join decisions that cost real money on Dataflow: network bytes vs. worker heap

---

## 🧠 Concept

### The thesis

> **In a batch pipeline, a join is a choice of how much you shuffle — and most joins do not need a shuffle at all.**

That is the whole chapter. Everything below is detail on how to make that
choice, and what goes wrong when you make it badly.

The intuition comes from the previous chapter. A `CombinePerKey` is a
shuffle: everything that enters it crosses the network. A side input is
not: it is a **broadcast**, a small table copied to every worker once.
The two costs are different in kind, not just in degree.

- A **side input** costs **memory**: every worker holds the entire
  lookup table, so the cost is `lookup_size × worker_count`.
- A **shuffle join** costs **network and vCPU-hours**: the cost is
  proportional to the total bytes of the data you are joining, plus the
  cost of grouping it.

Choose wrong and you pay in the currency that hurts more. Choose right
and the join is, for many real pipelines, free.

### The four mechanisms

| Mechanism | Network cost | Worker memory | Use when |
|---|---|---|---|
| **Side input** (`beam.pvalue.AsDict` / `AsList` / `AsSingleton`) | `O(1)` shuffles — the table is broadcast, not shuffled | the whole table, on every worker | the right-hand side fits in a worker's heap (tens of MB) |
| **`CoGroupByKey`** | one shuffle of both sides, grouped by key | one key group at a time | both sides are large |
| **`GroupByKey` + `Flatten`** | one shuffle, then a manual merge | one key group at a time, materialised | almost never — it is the hand-rolled `CoGroupByKey` |
| **BigQuery `JOIN`** | none in Beam; BigQuery does its own distributed join | none in Beam | the warehouse already holds both sides |

Read that table twice. The first two rows are the Beam-native options
and they are the ones you will use 90% of the time. The fourth row is
the one people forget, and it is sometimes the whole answer.

### Mechanism 1 — the side input (broadcast)

A **side input** is a PCollection that Beam evaluates once and then
makes available to every worker that needs it, as a plain Python object
at the moment a `DoFn` executes.

The contract has three parts:

1. The side input must be derived from a **fresh pipeline**, not from
   the main input PCollection. In practice this means `pipeline | ...`,
   not `some_pcollection | ...`.
2. It is a **snapshot**. The runner evaluates it at the start of the
   pipeline (or at the window boundary in streaming) and freezes it.
3. It is **broadcast to every worker**. Every worker that runs the
   consuming `DoFn` gets a full copy.

The API is small:

```python
import apache_beam as beam
from apache_beam import pvalue
from apache_beam.io.textio import ReadFromText

with beam.Pipeline() as p:
    reference = (
        p
        | "ReadReference" >> ReadFromText("sample_data/product_reference.ndjson")
        | "ParseReference" >> beam.Map(json.loads)
        | "KeyByProductId" >> beam.Map(lambda row: (row["product_id"], row))
    )

    orders = (
        p
        | "ReadOrders" >> ReadFromText("sample_data/orders.csv")
        | "ParseOrders" >> beam.ParDo(ParseOrderFn())
    )

    enriched = orders | "EnrichWithCategory" >> beam.Map(
        enrich_order,
        reference=beam.pvalue.AsDict(reference),
    )
```

Three things to notice.

**`AsDict` requires `(key, value)` tuples.** This is the most common
side-input bug in Beam, and it fails late — at execution, not at graph
construction. `AsDict` builds a Python dict from the elements, so the
elements must be two-tuples. If you feed it dicts, you get:

```text
ValueError: dictionary update sequence element #0 has length 4; 2 is required
```

The other views:

| View | Requires | Gives you |
|---|---|---|
| `beam.pvalue.AsIter` | anything iterable | an iterator over every element |
| `beam.pvalue.AsList` | anything | a `list` of every element |
| `beam.pvalue.AsDict` | `(key, value)` 2-tuples | a `dict` |
| `beam.pvalue.AsSingleton` | exactly one element | that element |
| `beam.pvalue.AsMultiMap` | `(key, value)` 2-tuples | `dict` of `key → list` |

`AsMultiMap` is the one that solves the many-to-one problem: when one
product has several reference rows (price tiers, regional variants),
`AsDict` keeps only one of them and `AsMultiMap` keeps all.

**The side input is a snapshot, not a live view.** Beam evaluates it
once. In a batch job that means "as of the moment the job started". If
the reference file changes *while the job runs*, the workers that
receive the side input late still get the snapshot, so the job is
internally consistent — but the snapshot may be older than you expect.

**The side input is replicated per worker.** This is the cost, and it
is the number you must size against. On a Dataflow worker with a 2 GB
heap, a 200 MB reference table is not a 200 MB table — it is 200 MB of
your 2 GB budget, per worker, before your pipeline has allocated
anything else.

### Mechanism 2 — `CoGroupByKey` (the keyed join)

`CoGroupByKey` takes several keyed PCollections, groups them by key,
and emits `(key, {tag: iterable})`. Chapter 2.8 covers the mechanics
in detail; here is the join-specific framing.

The shape of a `CoGroupByKey` join is always the same:

```text
   left  ──▶ Map(key) ──┐
                        ├──▶ CoGroupByKey ──▶ FlatMap(merge) ──▶ downstream
   right ──▶ Map(key) ──┘
```

Both sides are keyed. Both sides are shuffled. The merge happens
after the shuffle, in the worker that owns the key.

The critical property: **`CoGroupByKey` groups, it does not match.**
It gives you every left value and every right value for a key, and you
decide what to do with them. If the key is a unique identifier on both
sides, the pairing is 1-to-1 and it is a join. If the key is not
unique, you get a cartesian product within each key and you must
filter it yourself, *after* the shuffle.

For a proper join, the key must be the **complete join condition**. If
you need `ON left.product_id = right.product_id AND left.region =
right.region`, the key is the pair `(product_id, region)`, not
`product_id`. Beam has no way to express a residual predicate — that
is SQL's job, and Beam's lack of it is the reason to push big joins
into BigQuery.

### Mechanism 3 — `GroupByKey` + `Flatten` (the manual form)

You can build the same thing by hand:

```text
   left  ──▶ Map(key) ──▶ GroupByKey ──▶ FlatMap ──┐
                                                   ├──▶ Flatten ──▶ join
   right ──▶ Map(key) ──▶ GroupByKey ──▶ FlatMap ──┘
```

**Do not do this.** Three reasons, all of them real:

1. **It is `CoGroupByKey` with extra steps.** `CoGroupByKey` is
   implemented roughly this way internally. You gain nothing.
2. **Two shuffles instead of one.** `CoGroupByKey` fuses both sides
   into a single group-by stage. Two independent `GroupByKey`s are two
   shuffles, and the merge cannot fuse with either of them.
3. **It loses the grouping boundary.** After `Flatten`, you cannot
   tell which left row paired with which right row unless you carry the
   key in the value. `CoGroupByKey` keeps it in the key, for free.

There is exactly one case where the manual form is right: when you
want a **semi-join** or an **anti-join** — "which left rows have a
matching right row" — and you are joining two independent pipelines
that already exist. But even then, `CoGroupByKey` is usually clearer.

### Mechanism 4 — the BigQuery join (sometimes the whole answer)

This is the option the other three mechanisms keep deferring to.

If **both sides of the join already live in BigQuery**, the join is a
SQL statement that BigQuery will execute on its own distributed
cluster. You do not need Beam for the join at all. You need Beam for
the orchestration: reading the raw orders out of GCS, writing them into
a staging table, running the join, reading the result back out.

In Beam 2.77, `beam.io.WriteToBigQuery` accepts an
`additional_bq_parameters` argument. It is a dict of extra job
configuration, and the key you want is `query`. That parameter takes a
full BigQuery SQL statement, and the rows written by the pipeline are
made available to that statement as a table named
`{pipeline_options.project}.{dataset}.{table}` — the **destination
table itself**, before the load completes.

The name is easy to get wrong, so let it be explicit: the parameter is
`additional_bq_parameters`, and it is passed as a **dict** whose single
key is `"query"`.

```python
with beam.Pipeline(options=options) as p:
    (
        p
        | "ReadOrders" >> ReadFromText(orders_path)
        | "ParseOrders" >> beam.ParDo(ParseOrderFn())
        | "ToRows" >> beam.Map(to_bigquery_row)
        | "WriteWithJoin" >> beam.io.WriteToBigQuery(
            "my_dataset.enriched_orders",
            write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE,
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            additional_bq_parameters={
                "query": """
                    SELECT
                        o.order_id,
                        o.region,
                        o.amount_eur,
                        r.category
                    FROM `{project}.{dataset}.{table}` AS o
                    LEFT JOIN `{project}.{dataset}.product_reference` AS r
                      ON o.product_id = r.product_id
                """
            },
        )
    )
```

The `{}` placeholders in the SQL are substituted by Beam with the
actual project, dataset, and table of the destination.

**Why this beats shuffling to a worker.** Three reasons, in order of
importance:

1. **BigQuery already has the reference table.** If
   `product_reference` is a BigQuery table, loading it into a Beam
   worker means copying it to every worker. Running the join in
   BigQuery means copying nothing.
2. **BigQuery's join is genuinely distributed.** It can hash-join,
   merge-join, and — crucially — broadcast-join a small right-hand
   side with its own cost model, without you having to make that call.
3. **The join predicate can be arbitrary.** BigQuery supports
   `ON a.x = b.x AND a.y > b.y`, `LEFT JOIN`, `FULL OUTER JOIN`, and
   expressions in the `ON` clause. Beam's `CoGroupByKey` supports only
   equality on a hashable key, and everything else is a
   post-shuffle cartesian-product filter.

The cost: you now have a write-then-join-then-read round trip through
BigQuery, and the intermediate data is billed in BigQuery storage. For
a daily batch over billions of rows, that is usually still the cheapest
option. For a 5,000-row file, it is absurd overkill.

### The decision rule

> **If the right-hand side fits in memory → side input.
> If both sides are large → `CoGroupByKey`.
> If the warehouse already holds both sides → join in SQL and read the result.**

Make it quantitative, because "fits in memory" is not a decision, it is
a vague feeling.

Let `L` be the lookup size in bytes and `W` the number of workers.

- A **side input** costs `L × W` bytes of resident memory across the
  cluster, and **zero** network transfer beyond the initial broadcast
  of `L` bytes per worker.
- A **shuffle join** costs `D` bytes moved across the network, where
  `D` is roughly the total size of both sides after your filters, plus
  the grouping overhead.

The side input wins when `L × W` bytes of heap is cheaper than moving
`D` bytes across the network and paying the shuffle's vCPU-hours. On
Dataflow, a worker has a standard heap (2 GB by default, configurable
via `--worker_disk_size` and the machine type), and the network is
cheap but the shuffle is not free: it spills, it reorders, and it
occupies workers.

The practical thresholds:

| Lookup size | Verdict |
|---|---|
| < 10 MB | Side input, without thinking about it |
| 10–100 MB | Side input, but measure the worker heap |
| 100 MB – 1 GB | Side input only if the worker heap is raised; otherwise shuffle |
| > 1 GB | Shuffle, or push to BigQuery |

The 10–100 MB band is where the argument actually happens. Ask two
questions:

1. How many workers will the job have? A job with 1,000 workers and a
   50 MB side input holds 50 GB of lookup data in aggregate. That is
   fine — it is 50 MB per worker, and each worker processes its own
   slice — but it means the side input is a meaningful fraction of
   every worker's heap.
2. How often is the lookup *read*? If each worker touches the lookup
   once per element, a Python `dict` lookup is O(1) and free. If you
   do a linear scan per element, the lookup size multiplies your CPU
   cost, not just your memory.

That second point is a bug in the shipped course project, and it is
worth showing.

### Broadcast vs. shuffle, with the real numbers

Now the actual course data. From `resources/sample_data.py`:

| File | Rows | Bytes on disk |
|---|---|---|
| `sample_data/orders.csv` | 5,000 orders + header | **407,269** |
| `sample_data/product_reference.ndjson` | 50 products | **4,043** |

The reference file is **100× smaller** than the orders file, and it
holds **50 rows** against **5,000**.

Now compute the two costs for a Dataflow job with, say, 10 workers:

| | Side input | `CoGroupByKey` |
|---|---|---|
| Bytes moved by the join | 4,043 × 10 = **40,430** (broadcast) | 407,269 + 4,043 ≈ **411,312** (shuffle) |
| Resident lookup memory | 4,043 × 10 = **40,430** across the cluster | one key group per worker |
| Shuffle stages | **0** | **1** |
| Relative shuffle volume | **1×** (baseline) | **~10×** the reference table |

Two framings, and both are worth internalising:

- **A side input multiplies the lookup size by the worker count.** The
  lookup is 4 KB; at 10 workers that is 40 KB of heap. Boring. At 10,000
  workers with a 50 MB lookup, that is 500 GB across the cluster, and
  the heap pressure is real.
- **A shuffle multiplies the *data* size by the number of keys.** The
  orders file is 407 KB across 200 distinct product IDs and 4 regions.
  The shuffle does not move 407 KB; it moves 407 KB *plus* the
  per-key grouping overhead, and it re-reads and re-sorts it at every
  stage boundary.

The conclusion for this dataset is not close. **The side input is
correct, and the `CoGroupByKey` version is about 10× more expensive
for the same answer.** We will build both in the hands-on so you can
see the identical output, but only one of them is the right answer at
this scale.

> **The trap in the shipped project.** `project/batch_pipeline.py` uses
> `beam.pvalue.AsIter(reference)` and then does a **linear scan** of the
> reference list for every order:

```python
def _enrich_with_category(order: dict, reference: list[dict]) -> dict:
    product_id = order.get("product_id")
    for row in reference:
        if row.get("product_id") == product_id:
            order["category"] = row.get("category", "unknown")
            return order
```

> That is 5,000 orders × 50 reference rows = **250,000 comparisons** on
> this data. At 50 reference rows it is irrelevant. At 50,000 reference
> rows and 50 million orders it is 2.5 trillion comparisons — the
> pipeline spends all of its time in a `for` loop, not in a shuffle.
>
> The fix is `AsDict` plus an O(1) lookup, which is what the hands-on
> below does. Chapter 6.1 flagged this; this chapter fixes it.

### The fan-out and the duplicate-read trap

`Flatten` merges PCollections. One specific use of it is reading the
same source twice, filtering each copy differently, and merging the
results:

```text
   orders.csv ──▶ filter(status = complete) ──┐
                                                ├──▶ Flatten ──▶ downstream
   orders.csv ──▶ filter(status = cancelled) ─┘
```

**When this is correct.** When the source is **immutable** and the two
reads will see exactly the same bytes. A file written once, closed, and
never modified qualifies. A GCS object with a generation number
qualifies. A BigQuery table snapshot qualifies.

**When this is wrong.** When the source is still being written. If the
upstream process is still appending to `orders.csv` while your job
runs, the first read might see 5,000 rows and the second might see
5,300 — and the two branches disagree about what the file contains.
The `Flatten` then produces a PCollection that is not a coherent view of
anything. No error is raised. The numbers are just wrong.

The same trap, in a different shape: reading the same path twice when
the path is a **glob over a directory that is still being populated**.
The glob is resolved at read time, so the two reads can match
different file sets.

> **The rule.** If you read the same source twice, you must be able to
> point at the mechanism that makes the two reads consistent. A closed
> file is consistent by construction. An open file is not. If you
> cannot name the mechanism, read it once.

And when you can avoid the second read entirely, do. The single-read
version is better in every dimension except code brevity:

```python
orders = (
    p
    | "ReadOrders" >> ReadFromText(orders_path)
    | "ParseOrders" >> beam.ParDo(ParseOrderFn())
)

completed = orders | "KeepCompleted" >> beam.Filter(lambda o: o["status"] == "complete")
cancelled = orders | "KeepCancelled" >> beam.Filter(lambda o: o["status"] == "cancelled")

both = (completed, cancelled) | "Flatten" >> beam.Flatten()
```

This reads once, filters twice, and flattens. The cost is one read
instead of two. The output is identical, and it is identical *by
construction* rather than by luck.

Note what happens to the graph: the two `Filter`s now sit downstream of
a single read, so the runner can fuse the parse into them and the file
is read exactly once. The two-read version has two read stages, and
the runner cannot fuse across the `Flatten` boundary because the
`Flatten` inputs come from different sources.

### Full-refresh vs. incremental joins

Now the harder question: the reference table changes over time. What
does it mean to join today's orders against it?

**The full-refresh join.** Read the whole dimension table, join the
whole fact table, write the whole result with `WRITE_TRUNCATE`. Run
it once a day. The output table is a pure function of (orders file,
reference file, code version).

This is **trivially idempotent**: run it twice, and the second run
overwrites the table with identical content. Re-running it after a
failure produces the same answer. There is no watermark, no watermark
table, no dedup logic, no state. This is the argument from chapter 6.3
applied to joins, and it is the strongest argument in batch design.

**The incremental join.** Only process the orders that arrived since
the last run, and join them against the current dimension table. This
is what you want when the fact table is huge and only a slice is new.

The problem: **the dimension table is not a snapshot.** If you join
"yesterday's new orders" against "today's dimension table", you are
producing a row that was never true. The product was renamed on
Tuesday; today's join will show yesterday's order with today's product
name. Every downstream report that reads both tables sees two
inconsistent versions of the same product.

The incremental join needs a **watermark** (chapter 7.5) or a **lookback
window**:

```text
   Incremental join with a lookback
   ───────────────────────────────
   1. Read orders from (last_watermark - lookback) to now.
   2. Read the reference table AS OF the watermark's timestamp.
   3. Join.
   4. Write with WRITE_APPEND, deduplicating on order_id.
   5. Advance the watermark.
```

Step 4 is where incremental joins get dangerous: `WRITE_APPEND` is not
idempotent, so a retry double-counts. You need either a dedup step
(keyed on `order_id`, keeping the latest) or a merge/upsert sink.

**The rule of thumb.**

| Situation | Use |
|---|---|
| The fact table fits in a batch window | Full refresh, `WRITE_TRUNCATE` |
| The fact table is huge, the delta is small | Incremental with a watermark |
| The dimension table changes materially | Snapshot the dimension first, or use `as_of` |
| You need to be able to re-run any day | Full refresh, or incremental with dedup |

The course project takes the full-refresh path, and it is the right
one for the data sizes involved.

---

## 🛠️ Hands-On

### Setup

Everything in this chapter runs against the real course data. Generate
it first, from the course root:

```bash
.venv/bin/python resources/sample_data.py --output-dir ./sample_data
ls -l sample_data/orders.csv sample_data/product_reference.ndjson
```

```text
-rw-r--r--  1 pvishnoi  407269 ... sample_data/orders.csv
-rw-r--r--  1 pvishnoi    4043 ... sample_data/product_reference.ndjson
```

We will use `ReadFromText` plus `csv`/`json` rather than
`beam.io.ReadFromCsv`. The reason is a real bug, covered in
[Common Errors and Fixes](#-common-errors-and-fixes): `ReadFromCsv`
and `ReadFromJson` fail under the course's default
`BundleBasedDirectRunner`.

### Step 1 — the join with a side input

The enrichment function. Note the `AsDict` contract: the reference
PCollection must be `(key, value)` tuples.

```python
import apache_beam as beam
from apache_beam.io.textio import ReadFromText, WriteToText
from apache_beam.options.pipeline_options import PipelineOptions

import json
import sys

sys.path.insert(0, "project")
from transforms import (
    ParseOrderFn,
    RevenueByRegionFn,
    format_summary_csv,
    to_summary_row,
)

ORDERS_PATH = "sample_data/orders.csv"
REFERENCE_PATH = "sample_data/product_reference.ndjson"


def parse_reference_line(line: str) -> dict:
    """Parse one NDJSON line into a product reference dict."""
    text = line.strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def enrich_order(order: dict, reference: dict) -> dict:
    """Attach the product name and category to an order.

    The reference is a side input, already indexed by product_id, so
    this is one dict lookup per order — O(1), not a scan.
    """
    product = reference.get(order.get("product_id"))
    enriched = dict(order)
    if product is None:
        enriched["product_name"] = "unknown"
        enriched["category"] = "unknown"
        return enriched
    enriched["product_name"] = product.get("product_id", "unknown")
    enriched["category"] = product.get("category", "unknown")
    return enriched


options = PipelineOptions(["--runner=BundleBasedDirectRunner"])

with beam.Pipeline(options=options) as p:
    reference = (
        p
        | "ReadReference" >> ReadFromText(REFERENCE_PATH)
        | "ParseReference" >> beam.Map(parse_reference_line)
        | "KeyByProductId" >> beam.Map(lambda row: (row["product_id"], row))
    )

    orders = (
        p
        | "ReadOrders" >> ReadFromText(ORDERS_PATH)
        | "ParseOrders" >> beam.ParDo(ParseOrderFn())
    )

    enriched = orders | "EnrichWithProduct" >> beam.Map(
        enrich_order,
        reference=beam.pvalue.AsDict(reference),
    )

    completed = enriched | "KeepCompleted" >> beam.Filter(
        lambda order: order["status"] == "complete"
    )

    keyed = completed | "KeyByRegion" >> beam.Map(
        lambda order: (order["region"], order)
    )

    summary = keyed | "RevenueByRegion" >> beam.CombinePerKey(RevenueByRegionFn())
    rows = summary | "ToFlatRow" >> beam.Map(to_summary_row)

    rows | "FormatCsv" >> beam.Map(format_summary_csv) | "WriteSummary" >> WriteToText(
        "./out/ch36_side_input",
        header="region,order_count,revenue_eur",
        num_shards=1,
        shard_name_template="",
    )
```

Run it, then read the output file:

```bash
cat ./out/ch36_side_input*
```

The output, which must match the verified course numbers exactly:

```text
region,order_count,revenue_eur
AMER,318,113592.19
APAC,285,108194.92
EMEA,322,118423.22
LATAM,320,110646.18
```

> **Why this matches the shipped pipeline exactly.** The enrichment
> changes the row's *shape*, not its *revenue*. `RevenueByRegionFn`
> reads `amount` and `currency` and ignores everything else, so
> attaching `product_name` and `category` cannot change a single cent.
> That is a property worth designing for: **enrichment should be
> additive.** If your enrichment can change the aggregation, you have
> moved the join across the aggregate and you need to think again.

### Step 2 — the same join with `CoGroupByKey`

Same result, different mechanism. Both sides are keyed by `product_id`,
grouped, and merged after the shuffle.

```python
import apache_beam as beam
from apache_beam.io.textio import ReadFromText, WriteToText
from apache_beam.options.pipeline_options import PipelineOptions

import json
import sys

sys.path.insert(0, "project")
from transforms import (
    ParseOrderFn,
    RevenueByRegionFn,
    format_summary_csv,
    to_summary_row,
)

ORDERS_PATH = "sample_data/orders.csv"
REFERENCE_PATH = "sample_data/product_reference.ndjson"


def parse_reference_line(line: str) -> dict:
    """Parse one NDJSON line into a product reference dict."""
    text = line.strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def merge_product_group(key_value):
    """Merge one CoGroupByKey group into enriched order rows.

    The group is (product_id, {"orders": [...], "reference": [...]}).
    A product appears at most once in the reference, so the merge is
    one-to-one; the cartesian-product risk of CoGroupByKey does not
    apply here.
    """
    product_id, groups = key_value
    references = list(groups.get("reference", []))
    product = references[0] if references else None

    for order in groups.get("orders", []):
        enriched = dict(order)
        if product is None:
            enriched["product_name"] = "unknown"
            enriched["category"] = "unknown"
        else:
            enriched["product_name"] = product.get("product_id", "unknown")
            enriched["category"] = product.get("category", "unknown")
        yield enriched


options = PipelineOptions(["--runner=BundleBasedDirectRunner"])

with beam.Pipeline(options=options) as p:
    reference = (
        p
        | "ReadReference" >> ReadFromText(REFERENCE_PATH)
        | "ParseReference" >> beam.Map(parse_reference_line)
    )
    keyed_reference = reference | "KeyReference" >> beam.Map(
        lambda row: (row["product_id"], row)
    )

    orders = (
        p
        | "ReadOrders" >> ReadFromText(ORDERS_PATH)
        | "ParseOrders" >> beam.ParDo(ParseOrderFn())
    )
    keyed_orders = orders | "KeyOrders" >> beam.Map(
        lambda order: (order["product_id"], order)
    )

    joined = {
        "orders": keyed_orders,
        "reference": keyed_reference,
    } | "CoGroupJoin" >> beam.CoGroupByKey()

    enriched = joined | "MergeProduct" >> beam.FlatMap(merge_product_group)

    completed = enriched | "KeepCompleted" >> beam.Filter(
        lambda order: order["status"] == "complete"
    )
    keyed = completed | "KeyByRegion" >> beam.Map(
        lambda order: (order["region"], order)
    )
    summary = keyed | "RevenueByRegion" >> beam.CombinePerKey(RevenueByRegionFn())
    rows = summary | "ToFlatRow" >> beam.Map(to_summary_row)

    rows | "FormatCsv" >> beam.Map(format_summary_csv) | "WriteSummary" >> WriteToText(
        "./out/ch36_cogroupbykey",
        header="region,order_count,revenue_eur",
        num_shards=1,
        shard_name_template="",
    )
```

```text
region,order_count,revenue_eur
LATAM,320,110646.18
EMEA,322,118423.22
AMER,318,113592.19
APAC,285,108194.92
```

**Same numbers, different row order.** The row order differs because
the `CoGroupByKey` version groups by `product_id` and the final
`CombinePerKey` groups by `region`; there is no ordering guarantee in
either case. If you need a deterministic order, sort before the sink —
but understand that a sorted output is a *presentation* decision, not a
correctness one.

Now compare the mechanisms concretely:

| | Side input | `CoGroupByKey` |
|---|---|---|
| Join stage | a `Map` with a side input | a `CoGroupByKey` + a `FlatMap` |
| Shuffles introduced by the join | **0** | **1** (both sides keyed by `product_id`) |
| Lookup cost per order | one dict lookup | one group materialisation per product |
| Memory on a worker | the whole 4 KB reference | one `product_id` group |
| Works when the reference is 500 MB? | **no** | yes |
| Output | identical | identical |

Print the graph and count the stages — add `print(p)` as the last line
of either pipeline above. The side-input graph has **no keyed stage
between the parse and the enrichment**. The `CoGroupByKey` graph has a
`GroupByKey` — and that is the entire difference in cost.

### Step 3 — flattening two filtered reads

Two ways to get "completed and cancelled orders in one PCollection".

**The two-read version** — two independent reads of the same file:

```python
import apache_beam as beam
from apache_beam.io.textio import ReadFromText
from apache_beam.options.pipeline_options import PipelineOptions

import sys

sys.path.insert(0, "project")
from transforms import ParseOrderFn

ORDERS_PATH = "sample_data/orders.csv"

options = PipelineOptions(["--runner=BundleBasedDirectRunner"])

with beam.Pipeline(options=options) as p:
    completed = (
        p
        | "ReadCompletedSource" >> ReadFromText(ORDERS_PATH)
        | "ParseCompleted" >> beam.ParDo(ParseOrderFn())
        | "KeepCompleted" >> beam.Filter(lambda o: o["status"] == "complete")
    )
    cancelled = (
        p
        | "ReadCancelledSource" >> ReadFromText(ORDERS_PATH)
        | "ParseCancelled" >> beam.ParDo(ParseOrderFn())
        | "KeepCancelled" >> beam.Filter(lambda o: o["status"] == "cancelled")
    )

    merged = (completed, cancelled) | "FlattenStatuses" >> beam.Flatten()

    merged | "CountByStatus" >> beam.Map(lambda o: (o["status"], 1)) | "SumByStatus" >> beam.CombinePerKey(sum) | "Print" >> beam.Map(print)
```

```text
('complete', 1245)
('cancelled', 1188)
```

**The one-read version** — read once, filter twice:

```python
import apache_beam as beam
from apache_beam.io.textio import ReadFromText
from apache_beam.options.pipeline_options import PipelineOptions

import sys

sys.path.insert(0, "project")
from transforms import ParseOrderFn

ORDERS_PATH = "sample_data/orders.csv"

options = PipelineOptions(["--runner=BundleBasedDirectRunner"])

with beam.Pipeline(options=options) as p:
    orders = (
        p
        | "ReadOrders" >> ReadFromText(ORDERS_PATH)
        | "ParseOrders" >> beam.ParDo(ParseOrderFn())
    )

    completed = orders | "KeepCompleted" >> beam.Filter(
        lambda o: o["status"] == "complete"
    )
    cancelled = orders | "KeepCancelled" >> beam.Filter(
        lambda o: o["status"] == "cancelled"
    )

    merged = (completed, cancelled) | "FlattenStatuses" >> beam.Flatten()

    merged | "CountByStatus" >> beam.Map(lambda o: (o["status"], 1)) | "SumByStatus" >> beam.CombinePerKey(sum) | "Print" >> beam.Map(print)
```

```text
('complete', 1245)
('cancelled', 1188)
```

Identical output. The one-read version has **one** read stage; the
two-read version has **two**. The one-read version is also the one
that stays correct if the file is being appended to while the job
runs.

> **The caveat, stated precisely.** The two-read version is only safe
> here because `sample_data/orders.csv` is **immutable**: it was
> written once by `resources/sample_data.py` and closed. If the file
> were still being written, the first read might see 5,000 rows and the
> second 5,012, and the two branches would disagree. Nothing would
> fail. The numbers would just be wrong.
>
> The one-read version has no such caveat, because there is only one
> moment at which the file is read. **Prefer it.**

### Step 4 — pushing the join into BigQuery

When the reference table already lives in BigQuery, do not copy it to
your workers. Write the orders, and let BigQuery join them.

```python
import apache_beam as beam
from apache_beam.io.textio import ReadFromText
from apache_beam.options.pipeline_options import PipelineOptions

import sys

sys.path.insert(0, "project")
from transforms import ParseOrderFn, normalise_currency

ORDERS_PATH = "sample_data/orders.csv"

options = PipelineOptions(
    [
        "--runner=DataflowRunner",
        "--project=YOUR_PROJECT_ID",
        "--region=us-central1",
        "--staging_location=gs://YOUR_BUCKET/staging",
        "--temp_location=gs://YOUR_BUCKET/temp",
    ]
)

JOIN_SQL = """
    SELECT
        o.order_id,
        o.region,
        o.amount_eur,
        r.category
    FROM `{project}.{dataset}.{table}` AS o
    LEFT JOIN `{project}.{dataset}.product_reference` AS r
      ON o.product_id = r.product_id
    WHERE o.amount_eur IS NOT NULL
"""


def to_bigquery_row(order: dict) -> dict:
    """Shape an order into the row the BigQuery join expects."""
    return {
        "order_id": order["order_id"],
        "region": order["region"],
        "product_id": order.get("product_id"),
        "amount_eur": normalise_currency(float(order["amount"]), order["currency"]),
    }


with beam.Pipeline(options=options) as p:
    (
        p
        | "ReadOrders" >> ReadFromText(ORDERS_PATH)
        | "ParseOrders" >> beam.ParDo(ParseOrderFn())
        | "ToBigQueryRow" >> beam.Map(to_bigquery_row)
        | "WriteWithJoin" >> beam.io.WriteToBigQuery(
            "YOUR_PROJECT_ID.enrichment.enriched_orders",
            write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE,
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            additional_bq_parameters={"query": JOIN_SQL},
        )
    )
```

Three details that matter:

1. **The parameter name is `additional_bq_parameters`.** Not
   `query`, not `bq_parameters`, not `extra_query`. It is a **dict**,
   and the key inside it is `"query"`. Getting the outer name wrong
   gives `TypeError: __init__() got an unexpected keyword argument`;
   getting the inner key wrong gives a join that silently does
   nothing — BigQuery loads the rows but applies no query.
2. **The `{project}`, `{dataset}`, `{table}` placeholders are
   substituted by Beam.** Do not hard-code them; the destination table
   is passed as `table` to the constructor and Beam fills the rest in
   from the pipeline options and the table name.
3. **`LEFT JOIN`, not `JOIN`.** A `LEFT JOIN` keeps every order, even
   the 3,794 in this dataset whose `product_id` is not in the 50-row
   reference, with `category` as `NULL`. An inner join would silently
   drop them. Which is right depends on the business rule — but the
   default that loses orders quietly is the wrong default.

Recall the join-miss problem from the course data: the orders file
references **200 distinct product IDs**, and the reference file holds
**50**. So **150 of the 200 products have no reference row at all**,
and **3,794 of the 5,000 orders** get `category = "unknown"` in the
side-input version or `category = NULL` in the BigQuery version. That
is not a bug — it is the data telling you the reference table is
incomplete. Chapter 6.4's DLQ pattern is the tool for deciding what to
do about it, and the choice is a business decision, not a technical
one.

---

## 🛠️ Common Errors and Fixes

### 1. `TypeError: unhashable type: 'dict'`

**The message you get:**

```text
TypeError: unhashable type: 'dict' [while running 'C/ParDo(_PartialGroupByKeyCombiningValues)']
```

**The mistake.** You keyed a join by a dict — usually by passing the
whole row as the key instead of one field of it.

```python
# WRONG: the key is a dict, which is unhashable.
keyed = orders | "Key" >> beam.Map(lambda order: (order, order))
```

**The fix.** The key must be a **hashable** value: a string, number,
tuple of hashables, or `None`.

```python
# RIGHT: key by the join field.
keyed = orders | "Key" >> beam.Map(lambda order: (order["product_id"], order))
```

If you genuinely need a composite key, use a **tuple** — tuples of
hashables are hashable:

```python
keyed = orders | "Key" >> beam.Map(
    lambda order: ((order["product_id"], order["region"]), order)
)
```

Note the failure mode: this error appears **at execution time**, not
when the graph is built. On the Direct Runner it surfaces within
seconds. On Dataflow it surfaces when the first bundle is processed,
which may be several minutes after you submit the job. That is why the
course's audit script checks every `beam.<attr>` access statically —
and why the same discipline applies to keys.

### 2. `RuntimeError: A transform with label "A" already exists in the pipeline`

**The message you get:**

```text
RuntimeError: A transform with label "Enrich" already exists in the pipeline.
To apply a transform with a specified label, write pvalue | "label" >> transform
or use the option "auto_unique_labels" to automatically generate unique transform
labels. Note "auto_unique_labels" could cause data loss when updating a pipeline
or reloading the job state. This is not recommended for streaming jobs.
```

**The mistake.** Two transforms in the same pipeline share a label.
The usual cause is copy-pasting a pipeline block and forgetting to
rename one of the labels.

```python
# WRONG: "Enrich" used twice in one pipeline.
orders = orders | "Enrich" >> beam.Map(enrich)
other = other | "EnrichOther" >> beam.Map(enrich)
```

**The fix.** Every label in one pipeline must be unique. Labels need
only be unique **within a pipeline** — the same label in two different
fenced snippets is fine, because they are two different pipelines.

```python
# RIGHT: distinct labels.
orders = orders | "EnrichOrders" >> beam.Map(enrich)
other = other | "EnrichOther" >> beam.Map(enrich)
```

Note what Beam does *not* do: it does not renumber your labels, and it
does not tell you which two collided — only that the name is taken. The
message even suggests `auto_unique_labels`, and then warns you not to
use it, because auto-generated labels change when the pipeline changes.
**Name your labels.**

### 3. `ValueError: dictionary update sequence element #0 has length 4; 2 is required`

**The message you get:**

```text
ValueError: dictionary update sequence element #0 has length 4; 2 is required
[while running 'Enrich']
```

**The mistake.** You used `beam.pvalue.AsDict` on a PCollection whose
elements are not `(key, value)` pairs. `AsDict` calls `dict()` on the
side input's elements, and `dict()` requires an iterable of two-element
sequences.

```python
# WRONG: elements are dicts, not (key, value) tuples.
reference = (
    p
    | "ReadReference" >> ReadFromText(REFERENCE_PATH)
    | "ParseReference" >> beam.Map(parse_reference_line)
)
enriched = orders | "Enrich" >> beam.Map(
    enrich_order, reference=beam.pvalue.AsDict(reference)
)
```

**The fix.** Key the reference before handing it to `AsDict`.

```python
# RIGHT: elements are (product_id, row) tuples.
reference = (
    p
    | "ReadReference" >> ReadFromText(REFERENCE_PATH)
    | "ParseReference" >> beam.Map(parse_reference_line)
    | "KeyByProductId" >> beam.Map(lambda row: (row["product_id"], row))
)
enriched = orders | "Enrich" >> beam.Map(
    enrich_order, reference=beam.pvalue.AsDict(reference)
)
```

If you do not want a dict at all, use `beam.pvalue.AsList` or
`beam.pvalue.AsIter` — they accept any element type. `AsList` gives you
a list; `AsIter` gives you an iterator, which is the right choice for a
large reference because it does not force materialisation.

### 4. The side input that is not a side input — a silent wrong result

**What happens.** You pass a PCollection where a side input is
expected:

```python
# WRONG: `reference` is a PCollection, not a side input.
enriched = orders | "Enrich" >> beam.Map(
    enrich_order, reference=reference
)
```

**This does not raise.** In apache-beam 2.77 this pipeline **runs to
completion** and produces wrong output. The `reference` argument
arrives in the `DoFn` as an object whose type is
`_InvalidUnpickledPCollection` — a placeholder the runner substitutes
for a PCollection that was passed where a side input was expected. The
pipeline looks fine. The dashboard looks fine. The category column is
wrong.

This is the nastiest error in this chapter because there is no message
to grep for. The defence is structural:

> **Rule: every side input must be wrapped in `beam.pvalue.As*`. If
> you see a bare PCollection in a `DoFn` argument, it is a bug.**

The `As*` wrappers are the only sanctioned way to move a PCollection
into a `DoFn` as data rather than as a pipeline edge. If you find
yourself wanting to pass a PCollection directly, you want a second
input to the `ParDo`, which is a different thing entirely.

### 5. `AttributeError: 'tuple' object has no attribute 'element_type'`

**The message you get:**

```text
AttributeError: 'tuple' object has no attribute 'element_type'
```

**The mistake.** You used `beam.io.ReadFromCsv` (or
`beam.io.ReadFromJson`) under the course's default runner,
`BundleBasedDirectRunner`.

```python
# FAILS under BundleBasedDirectRunner.
(p | "ReadCsv" >> beam.io.ReadFromCsv("sample_data/orders.csv"))
```

**The fix, option A — use Prism.** The Go-based Prism runner shipped
in Beam 2.60+ handles these sources correctly:

```python
options = PipelineOptions(["--runner=PrismRunner"])

with beam.Pipeline(options=options) as p:
    (
        p
        | "ReadCsv" >> beam.io.ReadFromCsv("sample_data/orders.csv")
        | "Print" >> beam.Map(print)
    )
```

**The fix, option B — use `ReadFromText` and parse yourself.** This is
the path the course takes everywhere, and it is the path I would take
in production too, because it gives you control over the header row,
the malformed-row policy, and the exact field types:

```python
import csv
import io

def parse_csv_line(line: str) -> dict:
    """Parse one CSV line into a dict."""
    values = next(csv.reader(io.StringIO(line.strip())))
    return dict(zip(ORDER_FIELDS, values))
```

with the header row dropped explicitly:

```python
orders = (
    p
    | "ReadOrders" >> ReadFromText(ORDERS_PATH)
    | "SkipHeader" >> beam.Filter(lambda line: not line.startswith("order_id,"))
    | "ParseOrders" >> beam.Map(parse_csv_line)
)
```

> Note that `project/transforms.py`'s `ParseOrderFn` already handles
> the header: it logs `skipping malformed order line:
> order_id,customer_id,...` and moves on, because the header has nine
> fields but `amount` is not a float. That warning is expected on
> every run and is not a problem.

### 6. `KeyError` on a lookup miss — or the row that quietly vanishes

**The mistake.** The enrichment function indexes the reference
directly:

```python
def enrich_order(order: dict, reference: dict) -> dict:
    """WRONG: raises KeyError when the product is not in the reference."""
    product = reference[order["product_id"]]
    return {**order, "category": product["category"]}
```

**The message you get:**

```text
KeyError: 'p0199'
```

**Why it matters here.** The course data has 200 distinct product IDs
in the orders and only 50 in the reference. So this fails on **75% of
the distinct products**, and on a large fraction of the order rows.

**The fix, and the real question.** A lookup miss is not a crash —
it is a **business decision** you have not made yet. There are three
defensible answers, and you must pick one explicitly:

| Policy | Behaviour | When it is right |
|---|---|---|
| **Default** | `category = "unknown"`, keep the order | the enrichment is informational; the order's value does not depend on it |
| **Drop** | discard the order entirely | an order without a known product is not a real order (dangerous: it silently changes your revenue) |
| **DLQ** | route the order to a dead-letter queue, keep it out of the main output | the missing reference is a **data-quality incident** someone must fix |

The DLQ version is the one that scales, and it uses the tagged-output
pattern from chapter 6.4. Remember the argument order —
`TaggedOutput(tag, value)`, **tag first**:

```python
import apache_beam as beam
from apache_beam import pvalue


class EnrichOrderFn(beam.DoFn):
    """Attach product attributes, routing lookup misses to the DLQ."""

    def process(self, order: dict, reference: dict):
        """Emit the enriched order, or a DLQ record when the product is missing."""
        product = reference.get(order.get("product_id"))
        if product is None:
            yield pvalue.TaggedOutput(
                "dlq",
                {
                    "order_id": order.get("order_id"),
                    "product_id": order.get("product_id"),
                    "reason": "product not in reference",
                },
            )
            return
        yield {
            **order,
            "product_name": product.get("product_id", "unknown"),
            "category": product.get("category", "unknown"),
        }


with beam.Pipeline(options=options) as p:
    reference = (
        p
        | "ReadReference" >> ReadFromText(REFERENCE_PATH)
        | "ParseReference" >> beam.Map(parse_reference_line)
        | "KeyByProductId" >> beam.Map(lambda row: (row["product_id"], row))
    )

    orders = (
        p
        | "ReadOrders" >> ReadFromText(ORDERS_PATH)
        | "ParseOrders" >> beam.ParDo(ParseOrderFn())
    )

    results = orders | "EnrichWithProduct" >> beam.ParDo(
        EnrichOrderFn(),
        reference=beam.pvalue.AsDict(reference),
    ).with_outputs("dlq")

    good = results[None]
    bad = results["dlq"]
```

There is **no** `beam.FilterInto` in the Python SDK. The
`with_outputs` + `results[tag]` pattern above is the only supported
way to branch on a tagged output.

And then you can *measure* the miss rate, which is the real point:

```python
bad | "CountDlq" >> beam.Map(lambda row: (row["reason"], 1)) | "CountReasons" >> beam.CombinePerKey(sum) | "PrintDlq" >> beam.Map(print)
```

```text
('product not in reference', 3794)
```

That is **3,794 of the 5,000 orders** — 75.9% — landing in the DLQ,
because the orders reference 200 distinct products and the reference
file holds only 50. Only **1,206** orders find a product. A miss rate
like that is not a pipeline bug; it is the data telling you the
reference table is a sample, not the real catalogue.

### 7. The join that produces plausible, wrong numbers

**The symptom.** No error. No exception. The job succeeds. But the
numbers move by a fraction of a percent between runs, and nobody can
say why.

**The cause.** The reference table and the orders were read at
**different points in time**. The pipeline read `orders.csv` at 03:00
and `product_reference.ndjson` at 03:00:02 — but the upstream process
rewrote the reference file at 03:00:01. The fact rows are from one
version of the dimension and the attributes are from another.

This is easy to miss because the pipeline is *internally consistent*: it
used one snapshot of the reference, so every order saw the same
attributes. It is just that the attributes belong to a version of the
world that did not exist when the orders were placed.

**The fix — snapshot the dimension first.** Read the reference once and
write it to an immutable, versioned path before the join:

```text
   Step 1: snapshot the dimension
   ────────────────────────────────
   reference → WriteToText("gs://bucket/reference/dt=2026-01-15/")

   Step 2: join against the snapshot
   ─────────────────────────────────
   orders → read → join(reference/dt=2026-01-15/) → write
```

Now the join input is immutable by construction, and the snapshot's
date is in the path, so the whole result is traceable.

**The fix — use a fixed `as_of` timestamp.** If the dimension table is
versioned (`effective_from`, `effective_to`), key the lookup on the
**order's** timestamp, not on "now":

```python
def lookup_as_of(reference: list, order_ts: str) -> dict:
    """Find the reference row effective at the order's timestamp."""
    wanted = parse_timestamp(order_ts)
    best = None
    for row in reference:
        if row.get("product_id") != order.get("product_id"):
            continue
        start = parse_timestamp(row["effective_from"])
        if start <= wanted:
            best = row
    return best or {}
```

That is a linear scan per order — fine for a small table, and another
argument for `AsMultiMap` or a pre-built index when the table grows.

**The rule.** A join needs both sides to agree on *what time the world
was*. Either snapshot one side, or version it and join on the fact's
timestamp. Never join "current" against "current" and hope they line
up.

### 8. `TypeError: __init__() got an unexpected keyword argument 'query'`

**The mistake.** You passed the BigQuery query directly to
`WriteToBigQuery`.

```python
# WRONG: there is no `query` keyword on WriteToBigQuery.
beam.io.WriteToBigQuery(table, query=JOIN_SQL)
```

**The fix.** The query goes inside the `additional_bq_parameters`
dict, under the key `"query"`.

```python
# RIGHT.
beam.io.WriteToBigQuery(
    table,
    additional_bq_parameters={"query": JOIN_SQL},
)
```

The failure is asymmetric, and that is worth knowing. The **outer**
name wrong (`query=` instead of `additional_bq_parameters=`) raises
immediately at graph construction — loud and harmless. The **inner**
key wrong (`{"sql": ...}` instead of `{"query": ...}`) is silent: the
rows are loaded, the join is never applied, and your output table has
one row per order with no `category` column. That is a wrong-results
bug with no error message, which is why it belongs in this list.

---

## 💡 Production Notes

### Sizing the side input

The side-input ceiling is **per worker**, not per job. The formula:

```text
required_heap ≈ worker_count × lookup_size × (1 + python_object_overhead)
```

The `python_object_overhead` factor is not a rounding error. A
`dict` with 50,000 string keys and 50,000 dict values costs far more
than the 4 KB on disk, because every Python object has a header and a
pointer. As a rough rule of thumb:

- A JSON object on disk costs roughly **3–5×** its size as a Python
  `dict` in memory.
- A `dict` of 50,000 entries with string keys costs roughly **6–8 MB**
  of heap, not the ~5 MB you would guess from the raw text.

So the practical ceiling on a stock Dataflow worker (2 GB heap) is
**around 100–200 MB of lookup table**, and that is a number to treat
with suspicion, because it is the *whole* budget, and your pipeline
needs room for the orders themselves.

Practical mitigations, in order of preference:

1. **Keep the lookup to the fields you need.** The course reference
   has four fields (`product_id`, `category`, `unit_cost`, `active`).
   The join uses two. Projecting to two fields halves the memory.
2. **Use `AsIter` instead of `AsDict`** if you only need to scan, and
   the scan is cheap relative to the work per element.
3. **Raise the worker memory** with a larger machine type, or lower
   the worker count if the join is not the bottleneck.
4. **Push the join to BigQuery.** This is the real answer for a
   multi-hundred-megabyte dimension.

### The dimension table that changes mid-run

You covered the symptom in error 7. The production fix has two parts:

**Part one: make the input immutable.** Snapshot the dimension to a
versioned path before the join. The snapshot is a cheap, idempotent
write of a small table, and it buys you a join input that cannot
change under you.

**Part two: make the snapshot traceable.** Put the snapshot date in the
output path, and — if you can — put the snapshot version in the output
*rows*. A row that says `category = "shoes"` should be able to say
*which* product catalogue it got that from. Without that, an
irreproducible number is one support ticket away.

### When to push the join to BigQuery

Push it when **any** of these is true:

- Both sides are already in BigQuery.
- The right-hand side is bigger than a few hundred MB.
- The join predicate is not plain equality on a key — a range
  predicate, a fuzzy match, a `LIKE`, a `FULL OUTER JOIN` with
  non-equality conditions.
- You need BigQuery-specific features: `ARRAY_AGG`, window functions
  over the joined result, `QUALIFY`, a `PIVOT`.
- The join output is going straight back to BigQuery anyway, in which
  case the round trip through Beam workers is pure waste.

Do **not** push it when:

- The right-hand side is small (the course reference is 4 KB).
- The fact side is streaming into Beam and you want the join to be a
  Beam-native operation with a side input.
- You cannot afford the BigQuery storage cost for the intermediate
  table.
- The job needs to run on Dataflow with no BigQuery dependency at all
  — some regulated environments have that constraint.

The tie-back is chapter 5.5, "when BigQuery SQL is the better answer".
The answer there was *orchestration versus computation*: use Beam for
the parts that need portability, BigQuery for the parts that need SQL.
A join is almost always the second part.

### How joins interact with idempotency and backfills

From chapter 6.3, idempotency means: **run the pipeline twice, get the
same result.** A join adds a new way to break that, and the way it
breaks it is always the same — the join input changed between the two
runs.

| Join type | Idempotent? | Condition |
|---|---|---|
| Full refresh, `WRITE_TRUNCATE` | **Yes**, unconditionally | the inputs are the same |
| Full refresh, `WRITE_APPEND` | **No** | re-running doubles every row |
| Incremental, `WRITE_APPEND` | **No** | a retry double-counts the window |
| Incremental with dedup on the key | **Yes** | the dedup is deterministic |
| Any join, mutable dimension | **No** | the dimension changed between runs |

The two rules that follow:

1. **A backfill must re-read the same join inputs as the original
   run.** If you backfill January in March, you must join January's
   orders against **January's** product catalogue, not today's. This is
   the `as_of` fix from error 7, and it is the single most common
   source of backfill numbers that do not reconcile with the original
   run.
2. **A backfill of a join must use the same disposition as the
   original.** A full-refresh job that wrote with `WRITE_TRUNCATE`
   cannot be backfilled by writing one day's partition with
   `WRITE_APPEND` unless the table is partitioned by day and you
   replace that partition specifically.

### The cost angle

A shuffle costs **network and vCPU-hours**. A side input costs
**memory**. Those are different currencies and they do not convert
cleanly, which is why the decision rule is quantitative rather than
categorical.

Rough numbers for Dataflow:

| Operation | What you pay |
|---|---|
| Side input broadcast | `lookup_size × worker_count` of heap; negligible network |
| `CoGroupByKey` shuffle | ~`total_bytes` across the network, plus per-key grouping overhead, plus worker-hours |
| `CombinePerKey` shuffle | `partial_accumulator × key_count` across the network |
| BigQuery join | BigQuery query bytes + BigQuery storage for the intermediate table |
| Dataflow worker-hour | roughly $0.05–$0.10 depending on machine type and region |

The arithmetic that decides most cases: a shuffle of 1 TB across a
fleet costs real worker-hours and is usually the dominant line item.
A 50 MB side input broadcast across 100 workers costs 5 GB of heap
across the fleet — free, in money, and almost free in worker count
because the workers are doing useful work on the orders while they hold
it.

So the rule is not "side inputs are cheaper". The rule is: **a side
input is cheaper whenever the lookup is small relative to the data you
are joining, and a shuffle is cheaper whenever it is not.**

### A join checklist

Before you ship a join, walk this list:

1. Which mechanism? Side input, `CoGroupByKey`, or BigQuery?
2. What is the lookup size, in bytes, on disk? How many workers?
3. Is the lookup an O(1) dict access or an O(n) scan per element?
4. Is the join key **hashable**, and is it the **complete** join
   condition?
5. Does the right-hand side have a unique row per key? If not, is it
   a one-to-many join, and is `AsMultiMap` / a `CoGroupByKey` group
   the right shape?
6. What happens on a **lookup miss** — default, drop, or DLQ? Is that
   decision written down?
7. Are both join inputs **immutable snapshots** at join time?
8. Can the pipeline be **re-run** and produce the same result? Does
   the disposition match?
9. For a backfill, will it re-read the **same** dimension snapshot as
   the original run?
10. Have you measured the **enriched output**, not just its shape?

---

## 🔑 Key Takeaways

- **A join in Beam is a choice of how much you shuffle.** Side input
  is a broadcast (zero shuffles, memory cost); `CoGroupByKey` is a
  redistribution (one shuffle, network cost).
- **Most batch joins do not need a shuffle.** The course reference
  table is 4,043 bytes and 50 rows; the orders file is 407,269 bytes
  and 5,000 rows. A side input is correct here, and `CoGroupByKey` is
  about 10× more expensive for the identical result.
- **The decision rule:** right side fits in a worker's heap → side
  input. Both sides large → `CoGroupByKey`. Warehouse already holds
  both sides → join in SQL.
- **Size the side input by `lookup_bytes × worker_count`**, and
  remember Python objects cost 3–5× their on-disk size. The practical
  ceiling on a stock 2 GB Dataflow worker is around 100–200 MB.
- **`AsDict` requires `(key, value)` tuples.** Feeding it plain dicts
  raises `ValueError: dictionary update sequence element #0 has length
  4; 2 is required` — at execution, not at graph construction.
- **A side input must be wrapped in `beam.pvalue.As*`.** A bare
  PCollection passed as a side input does **not** error in Beam 2.77;
  it silently produces wrong output. This is the worst failure mode in
  the chapter because there is nothing to grep for.
- **`CoGroupByKey` groups, it does not match.** The key must encode the
  **complete** join condition; anything else is a post-shuffle
  cartesian product. Use `AsMultiMap` for one-to-many joins.
- **Never hand-roll `GroupByKey` + `Flatten`.** It is `CoGroupByKey`
  with two shuffles instead of one and no grouping boundary.
- **Reading the same file twice is a correctness risk, not just a
  cost.** It is only safe when the file is immutable. Prefer one read
  with two filters over two reads and a `Flatten`.
- **Full refresh with `WRITE_TRUNCATE` is trivially idempotent.**
  Incremental joins need a watermark, a lookback window, and dedup on
  the key — and the join must use the *same* dimension snapshot as the
  original run, or the backfill will not reconcile.
- **The BigQuery join is often the whole answer.** `WriteToBigQuery`
  takes `additional_bq_parameters={"query": ...}`; the destination
  table is referenced as `{project}.{dataset}.{table}`. The inner key
  is `"query"` — get it wrong and the join is silently skipped.
- **Enrichment should be additive.** If attaching a product category
  can change a region's revenue, the join is in the wrong place.

---

## 📚 Practice Exercises

1. **Fix the shipped enrichment.** `project/batch_pipeline.py` uses
   `beam.pvalue.AsIter(reference)` and does a linear scan of the
   reference list for every order. Rewrite `_enrich_with_category` to
   use `beam.pvalue.AsDict` over a `KeyByProductId` stage, and confirm
   the output CSV is byte-identical to the current one. *Expected
   answer:* the four rows `AMER,318,113592.19`, `APAC,285,108194.92`,
   `EMEA,322,118423.22`, `LATAM,320,110646.18`, unchanged, because the
   enrichment is additive and does not touch `amount` or `currency`.

2. **Measure the side-input vs. `CoGroupByKey` difference.** Build
   both versions from the hands-on above and compare them on three
   axes: (a) the number of shuffles in the printed graph, (b) wall
   clock on a 50,000-order file, (c) peak worker memory. Then repeat
   with a 50,000-row reference table instead of 50 rows. *Expected
   answer:* with a 50-row reference the side input wins decisively on
   all three axes. With a 50,000-row reference the side input's memory
   cost grows to roughly 50,000 × 3–5× row size per worker (tens of
   MB) while the `CoGroupByKey` version's cost grows with the *orders*,
   not the reference — and the `CoGroupByKey` version is now the right
   answer.

3. **Measure the lookup-miss rate.** Add the DLQ pattern from error 6
   to your enrichment pipeline and count how many orders reference a
   product that is not in `sample_data/product_reference.ndjson`.
   Then compute the same number in pure Python over the CSV. *Expected
   answer:* the orders reference 200 distinct product IDs and the
   reference holds 50, so **3,794 of the 5,000 orders** (the ones
   drawn from the 150 unknown products) miss, leaving **1,206** kept.
   The two numbers must agree exactly, and any discrepancy means the
   side input and the reference file disagree.

4. **One read, two filters.** Rewrite the two-read `Flatten` from the
   hands-on as a single read with two filters, then print both graphs
   and count the read stages. *Expected answer:* the two-read graph has
   two `ReadFromText` stages and the one-read graph has one; the
   outputs are identical; the one-read graph is the one that stays
   correct if the file is still being appended to.

5. **Composite key.** Join orders to the reference on
   `(product_id, region)` instead of `product_id`, using
   `CoGroupByKey`. Then deliberately join on `product_id` only and
   filter on `region` *after* the shuffle. Compare the amount of data
   that crosses the network. *Expected answer:* the composite key
   produces more, smaller groups and no residual filter; the
   `product_id`-only key produces larger groups and then filters them,
   so it moves strictly more data. The lesson: put the **whole** join
   condition in the key.

6. **Many-to-many, done correctly.** Build a reference table with two
   rows per product (say, a regional price list keyed on
   `(product_id, region)`), and join it to the orders. Use
   `beam.pvalue.AsMultiMap` for the side-input version and a
   `CoGroupByKey` group for the shuffle version. *Expected answer:* the
   `AsDict` version silently keeps only one row per key and loses
   rows — that is the bug `AsMultiMap` exists to prevent; the
   `CoGroupByKey` version sees all of them and you decide in the merge
   step which to use.

7. **Push the join to BigQuery.** Build the `additional_bq_parameters`
   version from the hands-on and run it against a real project. Then
   deliberately misspell the inner key (`"sql"` instead of `"query"`)
   and run it again. *Expected answer:* the misspelled version
   **succeeds** and writes the orders with no `category` column at
   all. The outer parameter name wrong raises `TypeError:
   __init__() got an unexpected keyword argument`; the inner key wrong
   is silent. This asymmetry is the whole point of the exercise.

8. **Snapshot the dimension.** Write a version of the pipeline that
   first snapshots `product_reference.ndjson` to a dated path, then
   joins the orders against that snapshot. Then change the reference
   file's categories mid-run and observe what the two pipelines
   produce. *Expected answer:* the snapshot pipeline produces one
   internally consistent answer; the direct pipeline produces an
   answer whose attributes do not match the snapshot's contents, and
   it is not obvious from the output which one is wrong.

9. **Cost the broadcast.** Write a script that computes
   `lookup_bytes × worker_count` for a 10 MB, 100 MB, and 1 GB lookup
   at 10, 100, and 1,000 workers. Mark every combination that exceeds
   a 2 GB worker heap or that costs more worker-hours than a shuffle
   would. *Expected answer:* the interesting region is the 100 MB ×
   1,000 workers cell (100 GB of aggregate heap, 100 MB per worker),
   and the 1 GB row, which is over the heap ceiling at every worker
   count and must be a shuffle or a BigQuery join.

10. **Backfill reconciliation.** Run the full-refresh pipeline for
    2026-01-15, then change one product's category in the reference
    file and re-run it. Explain, using the idempotency argument from
    chapter 6.3, why the second run's output differs from the first
    even though "the pipeline is idempotent". Then design the
    versioning that would make the second run reproduce the first.
    *Expected answer:* idempotency is a statement about the *inputs*,
    not the code — "same inputs, same output". Changing the reference
    file changes the inputs. The fix is versioned dimension rows
    (`effective_from` / `effective_to`) joined on the order's
    timestamp, so the backfill re-reads the same logical dimension.

11. **One-to-many with a side input.** A product can have multiple
    price tiers. Model this with `AsMultiMap` and produce one enriched
    order row per tier, tagging each with its tier. Then count how
    many orders produce more than one output row. *Expected answer:*
    the output row count exceeds the input row count, and the
    aggregation must be done **after** the fan-out (or the tier must
    be part of the group key) — pre-aggregating before the join would
    silently pick one tier per order.

---

## 📖 Further Reading

- Apache Beam: Side Inputs — https://beam.apache.org/documentation/programming-guide/#side-inputs
- Apache Beam: Multiple Inputs and Outputs — https://beam.apache.org/documentation/programming-guide/#multiple-inputs-and-outputs
- Apache Beam: Joining two keyed streams — https://beam.apache.org/documentation/programming-guide/#combinefn
- Beam Python SDK API — `apache_beam.transforms.core.CoGroupByKey` — https://beam.apache.org/releases/pydoc/current/apache_beam.transforms.core.CoGroupByKey.html
- Beam Python SDK API — `apache_beam.pvalue` (`AsDict`, `AsList`, `AsMultiMap`, `TaggedOutput`) — https://beam.apache.org/releases/pydoc/current/apache_beam.pvalue.html
- Beam Python SDK API — `apache_beam.io.WriteToBigQuery` — https://beam.apache.org/releases/pydoc/current/apache_beam.io.BigQueryIO.html
- Google Cloud BigQuery: Working with joins — https://cloud.google.com/bigquery/docs/reference/standard-sql/query-syntax#join_types
- Google Cloud BigQuery: Writing to BigQuery with a query — https://cloud.google.com/bigquery/docs/writing-results
- Google Cloud Dataflow: Optimizing pipelines — https://cloud.google.com/dataflow/docs/optimize-pipelines
- Google Cloud BigQuery: Best practices for loading data — https://cloud.google.com/bigquery/docs/best-practices-loading-data
