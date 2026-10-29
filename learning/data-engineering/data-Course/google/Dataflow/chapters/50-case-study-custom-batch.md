# 8.7 — Case Study 2 — Custom Batch

> **Section 8 · Production Operations · Lecture 8.7 · 6:30**

## 🎯 What you will learn

- A real multi-source batch revenue pipeline, from business problem to deployed template
- Why the product reference is a **side input**, not a shuffle-join
- Why currency conversion happens **before** the aggregation, inside the `DoFn`
- Why the status filter happens **before** the aggregation, and what that saves
- Why the `CombineFn` accumulates `(count, revenue_sum)` rather than a list
- Why the output is formatted with `csv.writer` before the text sink
- The test strategy: pure logic, pipeline graph, and expected numbers
- The verified output, to the cent
- The deployment as a flex template
- The honest limitations, and what production would change

---

## 🧠 Concept

### The business problem

A subscription commerce company closes its books nightly. Two systems
produce the data:

1. **An order export** — a CSV of every order in the last day, dropped
   into Cloud Storage by the fulfilment system at 01:00 UTC.
2. **A product reference** — an NDJSON file, one JSON object per product,
   holding the product's category and unit cost. This is the company's
   slowly-changing dimension: it is updated whenever merchandising
   changes a category, which is weekly, and it is a full snapshot, not a
   delta.

Finance needs one number per region, per day, in EUR. The awkward parts,
which are the whole problem:

- Orders arrive in **four currencies**, so the amounts are not directly
  summable.
- Orders arrive in **four statuses**, and only some of them are revenue.
  Cancelled orders must not be counted. Refunded orders must not be
  counted as positive revenue.
- The product reference must be **joined in**, because a future version of
  this report breaks revenue down by category.
- The report must be **backfillable**: when finance restates last
  quarter, we re-run it over a past date range and the numbers must be
  identical to the original run, or nobody trusts the restatement.
- It must be **testable without GCP**, because the person who writes the
  business logic should not need a cloud project to verify it.

### The requirements, stated precisely

| # | Requirement | How it is met |
|---|---|---|
| R1 | Read from two sources | `ReadFromText` on the orders CSV and on the reference NDJSON |
| R2 | Enrich with a side input | `beam.pvalue.AsIter(reference)` |
| R3 | Filter to valid orders only | status filter plus the validation inside `ParseOrderFn` |
| R4 | Aggregate per region | `CombinePerKey(RevenueByRegionFn())` |
| R5 | Write CSV locally or BigQuery in the cloud | `WriteToText` always, `WriteToBigQuery` optionally |
| R6 | Idempotent and backfillable | no wall-clock in the logic, no append-to-existing, deterministic combiner |
| R7 | Testable without GCP | pure logic separated from Beam; `DirectRunner` needs no credentials |

R6 deserves a note, because "idempotent" is often claimed and rarely
achieved. This pipeline is idempotent because:

- Nothing in the logic reads the current time. The only timestamp in the
  output is the event timestamp from the data.
- The combiner is associative and commutative, so the result does not
  depend on how the input was sharded.
- The output path is a *prefix*, and the writer refuses to overwrite an
  existing file by default — so a re-run is a *new* prefix, and the
  contents are identical.

### Design decision (a): the reference is a side input, not a shuffle-join

This is the decision the case study is really about, so it is worth
being precise about why.

The reference file has **50 rows**. The order file has **5,000 rows**.
The classic "obvious" solution is a join: key both sides by `product_id`
and `CoGroupByKey` them.

That is the wrong tool, for three reasons:

**1. A shuffle is a network operation with a persistent cost.** A
`CoGroupByKey` writes every keyed element to the shuffle store and reads
it back, then groups by key. For 50 reference rows, that is 50 rows
shuffled and re-grouped — a full round-trip through the shuffle store
for 3 KB of data.

**2. A side input is distributed by the runner for free.** A side input
in Beam is materialised once and delivered to each worker as a
broadcast. With 50 rows, every worker holds 3 KB. The lookup is then a
local dictionary access, not a network round-trip.

**3. The size matters, and it is the only thing that matters.** The
decision rule is simple:

> If the reference fits comfortably in the memory of every worker — call
> it under 100 MB, and under a few thousand entries for comfort — use a
> side input. If it does not, use a real join.

The threshold is not arbitrary. A side input is *broadcast to every
worker*. With 100 workers on a `n1-standard-4` (16 GB), 100 MB per
worker is 10 GB across the job. That is fine. At 1 GB per worker it is
100 GB and the job will not schedule. The rule of thumb is: **measure the
reference, and if it is under 100 MB, side input; otherwise join.**

There is a subtlety worth knowing, because it bites people. A side input
created by `AsIter` over a `ReadFromText` is *re-read per worker* unless
the runner can broadcast it. In practice, Beam materialises side inputs
into a side-input file in the staging/temp location and distributes it,
so it is read once and then fanned out. But the side input is built as
part of the job graph, which means it is materialised **every time the
job runs**, even though the reference changes weekly. For a nightly
pipeline reading a 50-row file, that is irrelevant. For a pipeline that
materialises a 10 GB side input every hour, it is a design problem —
and the answer is a different job, or a real join.

The course pipeline uses `AsIter` and does a linear scan per order. For
5,000 orders against 50 reference rows, that is 250,000 comparisons —
nothing. For a production-scale reference, you would use `AsDict` and
build the dict once per worker in the `DoFn`'s `setup()`.

### Design decision (b): currency conversion happens before the aggregation

The pipeline converts the amount to EUR **inside** the `DoFn`, before
the key/value pair is emitted. The alternative — convert after the
aggregation — is not even expressible, because after aggregation you have
a sum of mixed currencies, which is meaningless.

But the deeper point is about **where the combiner's complexity lives**:

```text
WRONG:  Map → (region, (amount, currency)) → Combine → convert sum
        (the sum is of mixed currencies; and converting a sum requires
         a "weighted" sum, which needs a different combiner anyway)

RIGHT:  Map → convert → (region, amount_eur) → Combine → sum
        (the combiner is `sum`, or a trivial accumulator)
```

With conversion before the aggregation, the combiner is a plain sum. The
business rule lives in the `DoFn`, where it can be unit-tested as a
pure function. The combiner is a generic, reusable, obviously-correct
piece of machinery. This separation is what makes the pipeline
trustworthy.

The course pipeline puts the conversion in `RevenueByRegionFn.add_input`
rather than in a separate `Map`, and the reason is worth stating: the
conversion needs the *currency*, which travels with the order. Putting
it in a `Map` would mean emitting `(region, amount_eur)` and therefore
projecting the order into a new dict first. Doing it in `add_input` keeps
the element that crosses the shuffle as the order itself, and the
accumulator as a small fixed-size dict.

The consequence for the combiner: the accumulator is
`{"order_count": 0.0, "revenue_eur": 0.0}` — two numbers, regardless of
how many orders pass through it. That is the property that makes it
mergeable.

### Design decision (c): the status filter happens before the aggregation

The pipeline filters to `status in statuses` *before* the
`CombinePerKey`. This looks obvious and is often got wrong.

Consider the sample data: 5,000 orders, of which 1,245 are `complete`.
If the filter comes after the aggregation, **all 5,000 orders cross the
shuffle** and only 1,245 survive the filter afterwards.

```text
WRONG:  Parse → KeyByRegion → CombinePerKey → Filter
        shuffle payload: 5,000 elements

RIGHT: Parse → Filter → KeyByRegion → CombinePerKey
        shuffle payload: 1,245 elements
```

That is a **4× reduction in shuffle volume** on this dataset, and it
scales with the ratio of unwanted to wanted data. On a pipeline where
90% of orders are `cancelled`, filtering first cuts the shuffle by 10×.

The general principle, and it is the single highest-leverage
optimisation in Beam:

> **Filter and aggregate as early as possible.** Every element you
> remove before a shuffle is bandwidth you never spend.

The order of operations in this pipeline, and the reason for each, is
therefore:

```text
Read → Parse (drop malformed, drop invalid) → [Enrich] → Filter (status)
     → KeyByRegion → CombinePerKey → Format → Write
```

Enrichment sits *before* the filter in the course pipeline. That is
deliberate in this specific case — the enrichment is cheap and the
filter is on a field the enrichment does not touch — but in production
you would filter first if the enrichment were expensive, since the filter
can only remove elements from the shuffle if it runs first.

### Design decision (d): the accumulator is `(count, revenue_sum)`, not a list

The classic beginner mistake is to accumulate the *values*:

```python
# WRONG — the accumulator grows with the number of elements
def create_accumulator(self):
    return []

def add_input(self, acc, order):
    acc.append(order["amount"])
    return acc
```

This is the `GroupByKey` pattern wearing a `CombineFn` costume. The
accumulator now holds one float per order. For a region with 300 orders
that is fine. For a region with 300 million orders, that accumulator
cannot be merged, cannot be spilled to disk, and cannot be merged in
parallel. The runner would have to hold every element of the group in
memory — which is exactly the problem `CombinePerKey` exists to solve.

The correct accumulator is a **constant-size summary**:

```python
def create_accumulator(self):
    return {"order_count": 0.0, "revenue_eur": 0.0}
```

Two numbers, whatever the input size. The properties this gives you:

- **Mergeable.** `merge_accumulators` is just addition, which is
  associative and commutative, so the result is independent of how the
  runner sharded the input.
- **Spillable.** A partial accumulator can be written to the shuffle
  store and read back.
- **Parallelisable.** Each worker accumulates its own partial, and the
  runner merges them in any order.

The rule is: **the accumulator must be a summary of the group, not the
group.** If your accumulator is proportional to the number of elements,
you have written a `GroupByKey` and you should have used one (or fixed
the combiner).

### Design decision (e): format with `csv.writer` before the text sink

`WriteToText` calls `str()` on each element. Feed it a dict and you get:

```text
{'region': 'EMEA', 'order_count': 322, 'revenue_eur': 118423.22}
```

Feed it a `float` and you get `118423.22` — but you lose the region
entirely. The pipeline formats explicitly:

```python
def format_summary_csv(row: dict[str, Any]) -> str:
    """Format one summary row as a CSV line."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            row.get("region", ""),
            row.get("order_count", 0),
            row.get("revenue_eur", 0.0),
        ]
    )
    return buffer.getvalue().rstrip("\r\n")
```

Why `csv.writer` and not an f-string:

1. **Quoting.** If a region name contained a comma, an f-string would
   produce a broken CSV line. `csv.writer` quotes it correctly.
2. **Type handling.** `csv.writer` calls `str()` on each field
   consistently, so a `Decimal` and a `float` format identically.
3. **The newline handling.** `csv.writer` on an empty `StringIO`
   produces `\r\n` line endings, which is why the function strips
   `\r\n` before returning — `WriteToText` adds its own newline.

### The implementation

The full pipeline, using the real function names from `project/`:

```python
import apache_beam as beam


class ParseOrderFn(beam.DoFn):
    """Parse CSV lines into order dicts, skipping malformed rows."""

    def process(self, line: str) -> Iterable[Any]:
        row = try_parse_order_line(line)
        if row is None:
            log.warning("skipping malformed order line: %.120s", line)
            return
        if not is_valid_order(row):
            log.warning("skipping invalid order: %s", row.get("order_id"))
            return
        yield row


class RevenueByRegionFn(beam.CombineFn):
    """Aggregate order count and revenue per region."""

    def create_accumulator(self) -> dict[str, float]:
        return {"order_count": 0.0, "revenue_eur": 0.0}

    def add_input(self, accumulator, order):
        accumulator["order_count"] += 1
        accumulator["revenue_eur"] += normalise_currency(
            float(order["amount"]), order["currency"]
        )
        return accumulator

    def merge_accumulators(self, accumulators):
        total = self.create_accumulator()
        for partial in accumulators:
            total["order_count"] += partial["order_count"]
            total["revenue_eur"] += partial["revenue_eur"]
        return total

    def extract_output(self, accumulator):
        return {
            "order_count": int(accumulator["order_count"]),
            "revenue_eur": round(accumulator["revenue_eur"], 2),
        }
```

Note the `int()` cast in `extract_output`. The accumulator uses floats
because `+=` on a float is fine and because the merge of floats is
unambiguous; the output converts the count back to an integer because
`322.0` in a report is a bug waiting to be noticed. A count is an
integer, and it should look like one.

And the pipeline itself:

```python
def build_pipeline(
    pipeline: beam.Pipeline,
    *,
    input_path: str,
    output_path: str,
    bigquery_table: str | None = None,
    statuses: tuple[str, ...] = ("complete",),
    reference_path: str | None = None,
) -> None:
    """Build the batch revenue pipeline."""
    lines = pipeline | "ReadOrders" >> ReadFromText(input_path)

    orders = lines | "ParseOrders" >> beam.ParDo(ParseOrderFn())

    if reference_path:
        reference = (
            pipeline
            | "ReadReference" >> ReadFromText(reference_path)
            | "ParseReference" >> beam.Map(_parse_reference_line)
        )
        orders = orders | "EnrichWithCategory" >> beam.Map(
            _enrich_with_category, reference=beam.pvalue.AsIter(reference)
        )

    completed = orders | "KeepCompletedOrders" >> beam.Filter(
        lambda order: order["status"] in statuses
    )

    keyed = completed | "KeyByRegion" >> beam.Map(
        lambda order: (order["region"], order)
    )

    summary = keyed | "RevenueByRegion" >> beam.CombinePerKey(RevenueByRegionFn())

    rows = summary | "ToFlatRow" >> beam.Map(to_summary_row)

    rows | "FormatCsv" >> beam.Map(format_summary_csv) | "WriteSummaryCsv" >> WriteToText(
        output_path,
        header="region,order_count,revenue_eur",
        num_shards=1,
        shard_name_template="",
    )

    if bigquery_table:
        rows | "WriteSummaryBigQuery" >> beam.io.WriteToBigQuery(
            bigquery_table,
            write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
        )
```

### The test strategy

Three layers, each testing a different thing.

**Layer 1 — pure logic, no Beam at all.** `project/transforms.py`
deliberately splits the business logic from the Beam wiring. The pure
half depends on nothing but the standard library, so
`project/tests/test_transforms.py` runs without `apache-beam` installed.
This is the layer that carries the business rules:

```python
from transforms import build_revenue_summary, normalise_currency


def test_normalise_currency_rounds_to_two_places():
    assert normalise_currency(100.0, "GBP") == 117.0
    assert normalise_currency(1000.0, "JPY") == 6.4


def test_build_revenue_summary_ignores_non_complete_orders():
    rows = [
        {
            "order_id": "o1",
            "customer_id": "c1",
            "order_ts": "2026-01-15T00:00:00+00:00",
            "region": "EMEA",
            "channel": "web",
            "currency": "EUR",
            "status": "complete",
            "amount": 10.0,
            "product_id": "p1",
        },
        {
            "order_id": "o2",
            "customer_id": "c1",
            "order_ts": "2026-01-15T00:00:00+00:00",
            "region": "EMEA",
            "channel": "web",
            "currency": "EUR",
            "status": "cancelled",
            "amount": 99.0,
            "product_id": "p1",
        },
    ]
    summary = build_revenue_summary(rows)
    assert summary["EMEA"]["order_count"] == 1
    assert summary["EMEA"]["revenue_eur"] == 10.0
```

**Layer 2 — the combiner's merge property.** The combiner is where the
subtle bugs live, so it gets its own test:

```python
from transforms import RevenueByRegionFn


def test_combiner_is_order_independent():
    combiner = RevenueByRegionFn()
    orders = [
        {"region": "EMEA", "amount": 10.0, "currency": "EUR"},
        {"region": "EMEA", "amount": 20.0, "currency": "USD"},
    ]
    acc_a = combiner.create_accumulator()
    for order in orders:
        acc_a = combiner.add_input(acc_a, order)
    acc_b = combiner.create_accumulator()
    for order in reversed(orders):
        acc_b = combiner.add_input(acc_b, order)
    assert combiner.extract_output(acc_a) == combiner.extract_output(acc_b)
```

**Layer 3 — the pipeline graph.** `project/tests/test_pipelines.py`
runs the graph on the `DirectRunner` and asserts on the output. This
catches wiring bugs — a mislabeled transform, a filter applied to the
wrong field — that layers 1 and 2 cannot see, because they never build
the graph.

The rule of thumb for a Beam project: **the business rules go in the
pure layer, and the pure layer is where most of the tests go.** A
pipeline whose business logic can only be tested through the runner is a
pipeline whose business logic is under-tested.

### The verification

The expected output, generated from the deterministic sample data:

```text
region,order_count,revenue_eur
AMER,318,113592.19
APAC,285,108194.92
EMEA,322,118423.22
LATAM,320,110646.18
```

| Region | Orders | Revenue (EUR) |
|---|---|---|
| AMER | 318 | 113,592.19 |
| APAC | 285 | 108,194.92 |
| EMEA | 322 | 118,423.22 |
| LATAM | 320 | 110,646.18 |
| **Total** | **1,245** | **450,856.51** |

Two things to notice about these numbers:

**1,245 out of 5,000.** The remaining 3,755 orders are `active`,
`cancelled` or `refunded`, and the filter removes them before the
shuffle. The 4× ratio is exactly the point of design decision (c).

**The revenue is not a round number per region.** It is a sum of EUR,
GBP, JPY and USD amounts, each rounded to two decimals *before* being
summed. This is a real, and often argued-about, decision: the course's
`normalise_currency` rounds each converted amount to the cent, and then
the sum of rounded amounts is rounded again. The alternative — sum the
raw converted values and round once at the end — gives a different
number, sometimes by a few cents.

Which is right? **Rounding per transaction is what a ledger does.** It
matches what the finance system will produce when it posts the
individual converted transactions, which is what the report has to
reconcile against. The alternative (round only at the end) is faster
and arguably more mathematically accurate, but it will never match the
ledger, and a report that does not match the ledger is a report nobody
uses.

This is the kind of decision that looks like an implementation detail
and turns out to be the difference between a report finance trusts and
one they rebuild in a spreadsheet.

### The deployment

The flex template, `project/templates/batch_template.py`, wraps the same
`build_pipeline`. The deployment is three commands:

```bash
# 1. Build the template image.
gcloud dataflow flex-template build project/templates/batch_template.py \
  --project YOUR_PROJECT_ID \
  --region us-central1 \
  --image gcr.io/YOUR_PROJECT_ID/dataflow/batch-template:latest \
  --temp-location gs://YOUR_BUCKET/tmp

# 2. Run it.
gcloud dataflow jobs run dataflow-batch-template \
  --project YOUR_PROJECT_ID \
  --region us-central1 \
  --image gcr.io/YOUR_PROJECT_ID/dataflow/batch-template:latest \
  --temp-location gs://YOUR_BUCKET/tmp \
  --input gs://YOUR_BUCKET/orders.csv \
  --output gs://YOUR_BUCKET/summary \
  --reference gs://YOUR_BUCKET/product_reference.ndjson

# 3. Schedule it — Cloud Scheduler + a service account, or a Dataflow
#    scheduled job via the API.
```

The critical property of this deployment: **the image contains the code,
and the parameters contain only the data locations.** Change the code, and
you rebuild the image. Change a path, and you re-run with a new
parameter. The two are never confused.

### The limitations, honestly

This is a course pipeline, and it has five limitations that production
would fix. Stating them is more useful than pretending they are not
there.

**1. The exchange rates are static.** `CURRENCY_TO_EUR` is a hard-coded
dict in `transforms.py`. It does not change, ever. A real pipeline reads
a daily rates table from BigQuery, converts using *the rate on the
transaction date*, and handles the fact that rates are published with a
lag. The static table is what makes the expected outputs in this chapter
stable, and that is a real trade-off — a pipeline that is testable is
worth more than one that is currently accurate.

**2. The BigQuery output is not partitioned.** `WriteToBigQuery` with
`WRITE_APPEND` writes to the table as one blob. Production would write
to a **partitioned table**, partitioned by the report date, so that a
backfill of one day does not rewrite the table and so that queries can
prune partitions. It would also set a **write disposition** deliberately:
`WRITE_APPEND` for the nightly incremental run, `WRITE_TRUNCATE` for a
full backfill, and `WRITE_EMPTY` for the idempotent case where a rerun
must not duplicate rows.

**3. There is no schema versioning.** The BigQuery table's schema is
whatever `CREATE_IF_NEEDED` inferred the first time. If the output gains
a column in six months, nothing in this pipeline notices or handles it.
Production would manage the schema explicitly — an Avro schema in the
repository, or `BigQuerySchemaUpdateOption` with an allowlist, or a
migration step before the pipeline runs.

**4. The currency conversion rounds per transaction.** Defensible (see
above), but it is a decision that finance should sign off on explicitly,
and it should be a documented parameter of the pipeline rather than an
implementation detail buried in a helper.

**5. There is no dead-letter path.** `ParseOrderFn` *logs* malformed
rows and drops them. The pipeline does not fail, and it does not record
what it dropped. A production pipeline writes the malformed rows to a
dead-letter GCS object or Pub/Sub topic, so that a data-quality team can
see and fix them. Logging them to the worker log is better than nothing
and worse than a DLQ: the rows are recoverable only by scraping logs.

---

## 🛠️ Hands-On: Building and Verifying the Pipeline

### Step 1 — Generate the sample data

```bash
cd data-engineering/data-Course/google/Dataflow
source .venv/bin/activate
python resources/sample_data.py --output-dir ./sample_data
```

```bash
wc -l sample_data/orders.csv sample_data/product_reference.ndjson
```

Expected: 5,001 lines in `orders.csv` (5,000 orders plus a header) and
50 lines in `product_reference.ndjson`.

### Step 2 — Run the pipeline locally

```bash
python project/batch_pipeline.py \
  --runner BundleBasedDirectRunner \
  --input ./sample_data/orders.csv \
  --output ./out/summary \
  --reference ./sample_data/product_reference.ndjson
```

### Step 3 — Verify the output against the expected numbers

```bash
cat out/summary*
```

Expected:

```text
region,order_count,revenue_eur
AMER,318,113592.19
APAC,285,108194.92
EMEA,322,118423.22
LATAM,320,110646.18
```

If the numbers differ, the most likely causes are:

- The sample data was generated with `--hot-key-rate` or
  `--late-events`, which changes the dataset.
- A different `--statuses` value was used.
- The pipeline is running against a different input file.

### Step 4 — Prove the filter is doing the work

Count the orders that survive the filter, and compare with the shuffle
payload size:

```bash
python -c "
import csv
from collections import Counter

statuses = Counter()
with open('sample_data/orders.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        statuses[row['status']] += 1

total = sum(statuses.values())
complete = statuses['complete']
print('total orders   :', total)
print('complete       :', complete)
print('filtered out   :', total - complete)
print('ratio kept     : %.2f' % (complete / total))
print('shuffle saved  : %.2fx' % (total / complete))
"
```

Expected: 5,000 total, 1,245 complete, and a ratio kept of 0.25 — a
**4× reduction** in shuffle volume from moving the filter before the
aggregation.

### Step 5 — Prove the combiner is order-independent

This is the property that makes the result reproducible across runs and
across runners:

```bash
python -c "
import sys
sys.path.insert(0, 'project')

from transforms import RevenueByRegionFn, try_parse_order_line

orders = []
with open('sample_data/orders.csv') as f:
    next(f)
    for line in f:
        row = try_parse_order_line(line.strip())
        if row:
            orders.append(row)

combiner = RevenueByRegionFn()

forward = combiner.create_accumulator()
for order in orders:
    forward = combiner.add_input(forward, order)

backward = combiner.create_accumulator()
for order in reversed(orders):
    backward = combiner.add_input(backward, order)

a = combiner.extract_output(forward)
b = combiner.extract_output(backward)
print('forward :', a)
print('backward:', b)
print('identical:', a == b)
"
```

Expected: `identical: True`.

### Step 6 — Prove the side input beats a join (at this scale)

Measure the cost of both approaches. The side input's cost is a linear
scan per order; the join's cost is a shuffle. At this scale the side
input wins on both:

```bash
python -c "
import sys, time
sys.path.insert(0, 'project')

from transforms import try_parse_order_line

orders = []
with open('sample_data/orders.csv') as f:
    next(f)
    for line in f:
        row = try_parse_order_line(line.strip())
        if row:
            orders.append(row)

reference = []
with open('sample_data/product_reference.ndjson') as f:
    for line in f:
        import json
        reference.append(json.loads(line))

start = time.perf_counter()
hits = 0
for order in orders:
    for ref in reference:
        if ref.get('product_id') == order.get('product_id'):
            hits += 1
            break
elapsed = time.perf_counter() - start

print('reference rows   :', len(reference))
print('orders           :', len(orders))
print('lookup           :', hits, 'hits')
print('elapsed          : %.4f s' % elapsed)
print('shuffled elements:', len(orders), '(a join would move all of these)')
"
```

The comparison to make explicit: a `CoGroupByKey` join would shuffle
**5,000 keyed elements** and re-group them. The side input shuffles
**50 reference rows** once and does 250,000 local comparisons. For a
reference of this size, the side input is not marginally better — it is
a different order of magnitude.

### Step 7 — Run the tests

```bash
python -m pytest project/tests/ -q
```

Expected: all tests pass, with no GCP credentials and no network.

### Step 8 — Deploy as a flex template

```bash
# Build.
gcloud dataflow flex-template build project/templates/batch_template.py \
  --project YOUR_PROJECT_ID \
  --region us-central1 \
  --image gcr.io/YOUR_PROJECT_ID/dataflow/batch-template:latest \
  --temp-location gs://YOUR_BUCKET/tmp

# Run.
gcloud dataflow jobs run dataflow-batch-template \
  --project YOUR_PROJECT_ID \
  --region us-central1 \
  --image gcr.io/YOUR_PROJECT_ID/dataflow/batch-template:latest \
  --temp-location gs://YOUR_BUCKET/tmp \
  --staging-location gs://YOUR_BUCKET/staging \
  --input gs://YOUR_BUCKET/orders.csv \
  --output gs://YOUR_BUCKET/summary \
  --reference gs://YOUR_BUCKET/product_reference.ndjson \
  --bigquery-table YOUR_PROJECT_ID.revenue.orders_by_region
```

### Step 9 — Compare the two implementations

The script and the template run the same logic. Run both and diff the
output:

```bash
python project/templates/batch_template.py \
  --input ./sample_data/orders.csv \
  --output ./out/from_template

diff <(sort out/summary*) <(sort out/from_template*) && echo "IDENTICAL"
```

Expected: `IDENTICAL`. If it is not, the two implementations have
drifted — which is exactly the failure mode chapter 8.6 warns about,
and the reason the template should import the script's `build_pipeline`
rather than copying it.

---

## 🛠️ Common Errors and Fixes

### The output is a Python dict repr

```text
{'region': 'EMEA', 'order_count': 322, 'revenue_eur': 118423.22}
```

`WriteToText` calls `str()` on each element. Format the row first:

```text
| "FormatCsv" >> beam.Map(format_summary_csv)
```

### The output has no header row

`WriteToText` with `header=...` writes the header only when
`num_shards=1` — with multiple shards, Beam cannot safely write one
header. The course pipeline sets `num_shards=1` and
`shard_name_template=""` so the file is named exactly as you asked.

### `RuntimeError: Transform name is already used`

Two transforms in the same pipeline share a label. The most common
cause in a pipeline like this is having both `ReadFromText` branches
labelled `"Read"`. The course uses `"ReadOrders"` and `"ReadReference"`.

Run the linter to find it statically:

```bash
python resources/audit_course.py
```

### The count is off by a few orders

The filter is not the only thing dropping rows. `ParseOrderFn` also
drops rows that fail `is_valid_order` — a missing `order_id`, an
unknown region, an unknown currency, a negative amount, an unparseable
timestamp. Check the malformed file to see the shape of the bad rows:

```bash
head -5 sample_data/malformed_orders.csv
```

### The revenue differs from the expected numbers by a few cents

Almost always the rounding question. The course rounds each converted
amount to the cent before summing. If you changed `normalise_currency`
to return the raw converted value, the totals change. Either behaviour
is defensible — but it must be consistent, and it must be the one that
matches the finance ledger.

### `ValueError: unknown currency: 'CHF'`

`is_valid_order` rejects currencies that are not in `CURRENCY_TO_EUR`,
so `ParseOrderFn` drops them and logs a warning. If you *want* CHF
counted, add it to `CURRENCY_TO_EUR` — and update the expected numbers
in this chapter, because they will change.

### The BigQuery table has duplicate rows after a re-run

`WRITE_APPEND` appends. Re-running the same job against the same date
appends again. This is the idempotency gap the course leaves open.
Production would key the output by date and use a
`WRITE_TRUNCATE`-per-partition disposition, or a merge with a
deduplication key.

### `FileNotFoundError` on `sample_data/orders.csv`

The sample data has not been generated:

```bash
python resources/sample_data.py --output-dir ./sample_data
```

### The template job fails with `ModuleNotFoundError: No module named 'transforms'`

The container image does not contain the project modules. Either copy
them into the image, or install the project as a package. The course
template works around it with `sys.path.insert`, which is fine for a
course and not for a production image.

---

## 💡 Production Notes

- **The side-input decision is a size decision.** Under ~100 MB and a few
  thousand entries, side input. Above it, a join. Measure the reference
  before you decide, and do not let "the old system used a join" be the
  answer.
- **A side input is broadcast to every worker.** 100 MB × 100 workers is
  10 GB across the job. Know the multiplier before you pick a reference
  table that is "only 200 MB".
- **Filter before you shuffle.** It is the single highest-leverage
  optimisation in Beam, and it is measured in bandwidth. In this
  pipeline it is a 4× reduction; on a pipeline where 90% of events are
  irrelevant it is 10×.
- **Keep the combiner's accumulator constant-size.** If the accumulator
  grows with the number of elements, you have built a `GroupByKey` with
  extra steps, and it will fail on the hot key first.
- **Rounding is a business decision, not an arithmetic detail.** Sum the
  rounded transactions to match the ledger, or sum the raw values to
  match the maths. Pick one, write it down, and make finance agree.
- **The enrichment ordering depends on cost.** Filter first if the
  enrichment is expensive and the filter is independent of it. Enrich
  first if the filter depends on an enriched field. This pipeline filters
  on `status`, which the enrichment does not touch.
- **The reference is read on every run.** That is fine for a nightly job
  reading 50 rows and wrong for an hourly job reading 10 GB. If the
  reference materialisation cost ever shows up in the job graph, the fix
  is a separate job that produces a versioned lookup artefact — not a
  slower pipeline.
- **Backfill means the output must not depend on "now".** Nothing in this
  pipeline reads the wall clock, which is why a backfill produces the
  same numbers as the original run. The day you add `datetime.now()` to
  a filename, backfill becomes a different operation from run.
- **`num_shards=1` is a teaching choice, not a production choice.** It
  makes the output readable and the diff meaningful. In production, let
  the sink shard, or write to BigQuery and let the table handle it.
- **The dead-letter gap is the most important one to close.** Dropping
  malformed rows into a log is data loss with extra steps. In production,
  route them to a DLQ and alert on the DLQ volume.

---

## 🔑 Key Takeaways

- The **side input** is right for the product reference because it is
  small — under 100 MB, a few thousand entries. Above that, a real join.
- **Currency conversion happens before the aggregation**, in the `DoFn`,
  so the combiner stays a trivial sum and the business rule stays in a
  testable pure function.
- **The status filter happens before the aggregation**, so only 1,245 of
  5,000 orders cross the shuffle — a 4× reduction on this dataset.
- **The accumulator is `(count, revenue_sum)`**, a constant-size summary.
  An accumulator that grows with the group is a `GroupByKey` in disguise.
- **The output is formatted with `csv.writer`** because `WriteToText`
  calls `str()`, and because a region name with a comma must not corrupt
  the file.
- **The business logic lives in the pure half of `transforms.py`**, which
  is testable without Beam and without GCP. That is the layer where most
  of the tests should live.
- The verified output is **AMER 318/113592.19, APAC 285/108194.92,
  EMEA 322/118423.22, LATAM 320/110646.18** — 1,245 orders, 450,856.51
  EUR.
- The production gaps are **real exchange rates, partitioned BigQuery
  output, a deliberate write disposition, schema versioning, and a
  dead-letter path** — and the dead-letter path is the one to close
  first.

---

## 📚 Practice Exercises

1. **Change the status set.** Run the pipeline with
   `--statuses complete,active` and with `--statuses complete`. Record
   the order counts and revenue for each. Then explain why a pipeline
   that counts `active` orders as revenue is a business decision, not a
   code change, and what question you would ask finance.

2. **Measure the side-input threshold.** Rewrite the enrichment to use
   `beam.pvalue.AsDict` with a dictionary lookup instead of `AsIter`
   with a linear scan. Measure both on the sample data, and then reason
   about the crossover point: at what reference size does the dict beat
   the scan? *Expected answer:* the dict wins from a handful of rows
   upward, because it is O(1) per lookup rather than O(n); the real
   threshold is not CPU but the memory cost of broadcasting the
   reference to every worker.

3. **Prove the filter placement.** Move the status filter to *after*
   `CombinePerKey` and measure the change in shuffle bytes — using the
   Dataflow job graph on GCP, or by counting elements on the Direct
   Runner with a counter. Then write one sentence on why the earlier
   placement is correct.

4. **Break the combiner on purpose.** Change `merge_accumulators` to
   `accumulators[0]` (returning only the first partial instead of
   merging them all). Run the pipeline and observe what happens. Then
   explain why the result is still "plausible" on small data and why it
   is catastrophically wrong on large data. *Expected answer:* on the
   sample data, one worker does most of the work so the first partial
   happens to be nearly complete; with real parallelism the answer
   depends on the sharding, so the result is not reproducible.

5. **Add a dead-letter output.** Extend `ParseOrderFn` to emit the
   malformed lines to a second output using `beam.pvalue.AsList` or a
   `DoFn` with two outputs, and write them to a separate file. Then
   count them: `head -5 sample_data/malformed_orders.csv` gives a hint
   of how many there are. *Expected answer:* one malformed row (the
   header, which the reader treats as data) — the count is small, which
   is exactly why the DLQ needs to be an alert, not a report.

6. **Make it backfillable.** Add a `--report-date` parameter that is
   written into the output row and is used as the BigQuery partition.
   Then run the pipeline twice with the same `--report-date` and show
   that the *contents* are identical, while the file paths differ.
   *Expected answer:* identical contents, because nothing in the logic
   depends on the current time.

---

## 📖 Further Reading

- Apache Beam's side inputs — https://beam.apache.org/documentation/sdks/python/side-inputs/
- Apache Beam's CombineFn — https://beam.apache.org/documentation/sdks/python/transforms/python/combine/
- Beam's guide to combining — https://beam.apache.org/documentation/basic-topics/combining/
- Writing and running a Dataflow flex template — https://cloud.google.com/dataflow/docs/guides/templates/flex/using-python
- BigQuery write dispositions — https://cloud.google.com/bigquery/docs/writing-append
- BigQuery partitioned tables — https://cloud.google.com/bigquery/docs/partitioned-tables
- Dead-letter topics on Pub/Sub — https://cloud.google.com/pubsub/docs/subscription-message-retention
