# 6.6 — Case Study 1 — Template Method

> **Section 6 · Batch Pipeline Engineering · Lecture 6.6 · 6:30**

## 🎯 What you will learn

- How to take a one-sentence business request and turn it into a pipeline that survives production
- The **Template Method** pattern in Beam: a fixed skeleton with parameterised steps, and why the course project uses it
- The full design of the revenue-by-region pipeline, stage by stage, with the reason each stage sits where it does
- The data contract: the exact nine CSV columns, and the seven business rules that decide whether a row counts
- The implementation, using the real `project/transforms.py` code, annotated line by line
- How to test the pipeline so the feedback loop is seconds rather than minutes
- How to deploy it as a Dataflow flex template, and what the runtime arguments are for
- The verification numbers, which you can check yourself: **AMER 318/113592.19, APAC 285/108194.92, EMEA 322/118423.22, LATAM 320/110646.18**
- **A real defect in the shipped template**: `WRITE_APPEND` in a full-refresh batch job, and the one-line fix
- The honest limitations of the design, and what I would change before running it against real money

---

## 🧠 Concept

### What a case study is for

The previous five chapters gave you the toolbox. Filters, coders,
combiners, DLQs, backfills. Each one is a tool, and a tool in isolation
does not tell you *when* to reach for it.

This chapter is different in kind. It takes one real requirement — a
small, unglamorous one — and walks it all the way from the sentence a
stakeholder would say to a pipeline running on Dataflow. There is no
synthetic "clickstream at planetary scale" here. The requirement is
deliberately modest so that every design decision is visible and
defensible:

> Every day, we get a CSV of orders. We need to know how much revenue
> each region made, in euros, so we can put it on a dashboard by 8am.

That sentence contains, unstated, at least eight engineering
requirements. Making them explicit is most of the work.

### The Template Method

The course project uses a pattern called **Template Method** — a
design pattern from the Gang of Four, applied to Beam pipelines.

The idea: define the **skeleton** of an algorithm once, in a base
class or a function, and let subclasses or callers fill in the
variable parts. The skeleton decides *the order of the steps* and
*which steps exist*. The parameterisation decides *the data*, not the
structure.

In Beam terms, the skeleton is the sequence of transforms:

```text
   read ──▶ parse ──▶ validate ──▶ filter ──▶ key ──▶ combine ──▶ shape ──▶ write
```

What varies between deployments is:

| The variable part | Varies between | Where it is decided |
|---|---|---|
| Which records count | live run vs. backfill vs. a one-off audit | `--statuses` |
| Where the input comes from | local file vs. GCS vs. Pub/Sub | `--input` |
| Where the output goes | local file vs. GCS vs. BigQuery | `--output`, `--bigquery-table` |
| How much to include | reference table present or not | `--reference` |
| Which runner executes it | local vs. Dataflow vs. Spark | `--runner` |

What does **not** vary is the order of the stages, the validation
rules, the aggregation logic, or the output schema. Those are the
algorithm, and the algorithm is fixed.

This is the opposite of what a lot of "flexible" pipelines become. The
temptation in a pipeline is to add a flag for everything — and every
flag you add multiplies the number of code paths, and the number of
code paths is where the bugs live. A Template Method keeps the number
of paths bounded by the number of parameters, and keeps the structure
in one place where it can be reviewed once.

Compare the two extremes:

```text
   BAD: one pipeline, 14 flags, 2^14 possible behaviours
   GOOD: one skeleton, 5 parameters, 2^5 possible behaviours
   BETTER: one skeleton, 5 parameters, but the parameters are
           validated and the branches are in the skeleton, not
           scattered through it
```

The project gets most of the way to the third one. Where it falls
short — and where I would fix it — is at the end of this chapter.

### Why the skeleton is fixed

There is a specific reason to keep the stage order fixed: **the stage
order is what makes the output a function of the input.**

If the order changes, the numbers change, and there is no way to tell
whether a number changed because the data changed or because the code
changed. That distinction is the difference between a pipeline you can
backfill and a pipeline you cannot.

The order is not arbitrary, though. Every stage is placed where it is
for a reason:

```text
   read ──▶ parse ──▶ validate ──▶ filter ──▶ key ──▶ combine ──▶ shape ──▶ write
             │           │            │          │        │         │          │
             │           │            │          │        │         │          └─ 4 rows out
             │           │            │          │        │         └───────────── one flat row per region
             │           │            │          │        └─────────────────────── count + revenue per key
             │           │            │          └────────────────────────────── one (key, value) per element
             │           │            └───────────────────────────────────────── drop rows we do not count
             │           └────────────────────────────────────────────────────── drop rows that break a rule
             └───────────────────────────────────────────────────────────────── produce one dict per input line
```

Read the pipeline **right to left** for the cost argument, and **left
to right** for the correctness argument.

**Left to right** (correctness): every element that reaches the
aggregator has been parsed, has passed every business rule, and has a
status we count. The aggregator sees only clean, countable rows.

**Right to left** (cost): the aggregator sees the fewest elements
possible. In the course data that is 1,245 rows, not 5,000 — a
**4.02× reduction** in what crosses the shuffle boundary. The filter
is before the combine for that reason, and not because it reads
better.

That 4.02× is not a round number in this case by accident. It is
`5000 / 1245`. The 5,000 is every order in the file; the 1,245 is the
number with `status == "complete"`. Chapter 6.1 measured this
directly. The point of repeating it here is that it is the *reason*
the design looks the way it does, and a design without reasons is a
design that gets "cleaned up" by the next person who touches it.

### Why not filter inside the combiner?

A reasonable question: why is the filter a separate stage at all? Why
does `RevenueByRegionFn.add_input` not check the status itself?

Two reasons.

First, **the combiner is a `CombineFn`, and `CombineFn` must be
associative and commutative.** If the filter lived inside `add_input`,
the combiner would be *filtering*, and a `CombineFn` that discards
inputs based on their content is much harder to reason about — in
particular, `merge_accumulators` would have to know about the filter
too, or the merge would not be consistent with the accumulation.

Second, and more practically: the combiner is **reused** by other
pipelines. The streaming pipeline, the backfill pipeline, and the audit
pipeline all aggregate the same way; they differ in which rows reach
them. Putting the policy at the boundary keeps the aggregation
mechanical.

The rule of thumb: **the combiner computes; the pipeline decides.**

### The four stages, and why there are four

Actually there are four *logical* stages in the design, even though the
code has more transforms than that. Grouping them makes the shape
clear:

| Stage | Transforms | Output shape | Why it is a separate stage |
|---|---|---|---|
| **1. Ingest** | `ReadOrders` | `str` (raw line) | The only stage that knows about files, paths, and encoding |
| **2. Interpret** | `ParseOrders` | `dict` (order) | The only stage that knows the file format |
| **3. Select** | `KeepCompletedOrders` | `dict` (order) | The only stage that knows business policy |
| **4. Aggregate** | `KeyByRegion` → `RevenueByRegion` → `ToFlatRow` | `dict` (summary row) | The only stage that knows the output schema |

The boundaries are not arbitrary. Each one is a place where a
requirement changed in the past, or will change in the future:

- The **input path** changes every day. Stage 1 absorbs that.
- The **file format** changes when the upstream system changes. Stage 2
  absorbs that. If the format changed, `ParseOrderFn` changes and
  nothing else does.
- The **status policy** changes when finance changes their mind about
  what counts as revenue. Stage 3 absorbs that.
- The **output schema** changes when the dashboard changes. Stage 4
  absorbs that.

If a stage had no independent reason to change, it should not be a
separate stage. That is the test for whether your decomposition is
real.

### The data contract

A pipeline without a written data contract is a pipeline whose
behaviour is defined by whatever the last producer happened to send.
This is the part of the design that is most often missing and most
often regretted.

#### The input schema

The input is a CSV file with a header row and exactly nine columns:

| # | Column | Type | Example | Nullable |
|---|---|---|---|---|
| 1 | `order_id` | string | `o00000000` | no |
| 2 | `customer_id` | string | `c000914` | no |
| 3 | `order_ts` | ISO-8601 timestamp | `2026-01-15T00:54:38+00:00` | no |
| 4 | `region` | enum | `AMER` | no |
| 5 | `channel` | string | `web` | yes |
| 6 | `currency` | ISO-4217 code | `GBP` | no |
| 7 | `status` | enum | `complete` | no |
| 8 | `amount` | decimal | `700.97` | no |
| 9 | `product_id` | string | `p0173` | yes |

In the code, that is `ORDER_FIELDS` in `project/transforms.py`:

```python
ORDER_FIELDS = [
    "order_id",
    "customer_id",
    "order_ts",
    "region",
    "channel",
    "currency",
    "status",
    "amount",
    "product_id",
]
```

Note that `channel` and `product_id` are **not validated**. They are
read, carried through, and ignored. That is deliberate: the contract
says they may be absent or unknown, and the pipeline does not need
them for this report. Rejecting a row because `product_id` is blank
would throw away revenue that is perfectly good for the purpose the
pipeline serves.

#### The validation rules

`is_valid_order` is the executable form of the contract. There are
seven rules, and they are written out explicitly rather than derived
from a schema:

```python
def is_valid_order(row: dict[str, Any]) -> bool:
    """Check that an order row satisfies every business rule."""
    if not row.get("order_id"):
        return False
    if not row.get("customer_id"):
        return False
    if row.get("region") not in VALID_REGIONS:
        return False
    if row.get("status") not in VALID_STATUSES:
        return False
    if row.get("currency", "").upper() not in CURRENCY_TO_EUR:
        return False
    try:
        parse_timestamp(str(row.get("order_ts", "")))
    except ValueError:
        return False
    try:
        amount = float(row.get("amount"))
    except (TypeError, ValueError):
        return False
    if amount < 0:
        return False
    return True
```

The rules, in order:

| # | Rule | Why it exists |
|---|---|---|
| 1 | `order_id` is non-empty | It is the deduplication key and the audit handle |
| 2 | `customer_id` is non-empty | Revenue without a customer cannot be attributed |
| 3 | `region` ∈ {AMER, APAC, EMEA, LATAM} | A bad region silently creates a new group |
| 4 | `status` ∈ {active, complete, cancelled, refunded} | An unknown status means unknown policy |
| 5 | `currency` is a known code | The conversion would raise |
| 6 | `order_ts` parses as ISO-8601 | The dashboard groups by day |
| 7 | `amount` is numeric and ≥ 0 | A negative amount is a refund, not revenue |

Rule 3 deserves a note, because it is the rule people argue about. A
row with `region = "UNKNOWN"` is *not* the same as a row with a
malformed timestamp. The first is data the pipeline does not understand;
the second is data the pipeline understands and rejects. If a new
region is added to the business, you add it to `VALID_REGIONS` and the
pipeline starts counting it. If a row has `region = "AMER "` with a
trailing space, that is a producer bug, and the right response is to
route it to a DLQ rather than to silently normalise it.

#### The output schema

The output is three columns, always in this order:

| Column | Type | Meaning |
|---|---|---|
| `region` | string | The group key |
| `order_count` | integer | How many counted orders landed in the region |
| `revenue_eur` | decimal(2) | The summed, currency-converted revenue |

Three columns, four rows. A summary that small looks trivial, and that
is the point: **the output is small enough to be completely understood
by everyone who touches it.** There is no schema evolution story here
because there is nothing to evolve.

### The currency conversion, and why it is a limitation

The pipeline converts every amount into EUR using a static table:

```python
CURRENCY_TO_EUR: dict[str, float] = {
    "EUR": 1.0,
    "USD": 0.92,
    "GBP": 1.17,
    "JPY": 0.0064,
}
```

And rounds to two decimal places:

```python
def normalise_currency(amount: float, currency: str) -> float:
    """Convert an amount into EUR using the static rate table."""
    rate = CURRENCY_TO_EUR.get(currency.upper())
    if rate is None:
        raise ValueError(f"unknown currency: {currency!r}")
    return round(amount * rate, 2)
```

This is the most obviously *not production* part of the pipeline, and
it is worth understanding exactly why, because the failure mode is
subtle.

**The problem is not that the rates are stale. The problem is that
the pipeline does not know what date the rates apply to.**

If you convert a January order using a January rate, the result is
correct. If you backfill January next month using today's rate, the
result is different — and it is different *for every region that has
any non-EUR orders*, in a way that has nothing to do with the region's
actual performance.

The fix is not complicated, and it is a good exercise:

1. Store the rates with an effective date.
2. Carry the **order date** on each row through to the conversion.
3. Select the rate whose effective window contains the order date.
4. Record the rate table version in the output, so a number can always
   be traced back to the rates that produced it.

Point 4 is the one people forget, and it is the one that saves you
when finance asks "why did EMEA change by 2% when nothing happened?"

For the course, static rates are the right call: they keep the
expected outputs stable so the tests can assert exact numbers. But the
pipeline as shipped would be wrong to deploy unchanged.

### The combiner

The aggregation is a `CombineFn` with an explicit accumulator:

```python
class RevenueByRegionFn(beam.CombineFn):
    """Aggregate order count and revenue per region."""

    def create_accumulator(self) -> dict[str, float]:
        """Create an empty accumulator."""
        return {"order_count": 0.0, "revenue_eur": 0.0}

    def add_input(self, accumulator: dict[str, float], order: dict[str, Any]) -> dict[str, float]:
        """Add one order to the accumulator."""
        accumulator["order_count"] += 1
        accumulator["revenue_eur"] += normalise_currency(
            float(order["amount"]), order["currency"]
        )
        return accumulator

    def merge_accumulators(
        self, accumulators: Iterable[dict[str, float]]
    ) -> dict[str, float]:
        """Merge partial accumulators from different workers."""
        total = self.create_accumulator()
        for partial in accumulators:
            total["order_count"] += partial["order_count"]
            total["revenue_eur"] += partial["revenue_eur"]
        return total

    def extract_output(self, accumulator: dict[str, float]) -> dict[str, float]:
        """Produce the final output from the accumulator."""
        return {
            "order_count": int(accumulator["order_count"]),
            "revenue_eur": round(accumulator["revenue_eur"], 2),
        }
```

Three properties are worth calling out.

**The accumulator is a dict, not a tuple.** A tuple would be faster to
serialise, and Beam would not care which you used — but a dict with
named fields means `extract_output` reads like the business rule it
implements. At 5,000 rows the speed difference is irrelevant; at 5
billion rows, the code is still readable.

**`merge_accumulators` is correct by construction.** It adds up
partials. Addition of floats is commutative (up to floating-point
rounding, which the final `round` absorbs), so the merge gives the
same answer regardless of the order Beam happens to merge in. The
project's `test_merge_is_order_independent` test asserts exactly this.

**The rounding happens once, at the end.** `add_input` does *not*
round. If it did, the result would depend on how the inputs were
partitioned across workers — the same 1,000 orders would sum
differently depending on whether they arrived in one bundle or fifty.
Rounding at the end, after all merges, is the only way to make the
output a function of the input.

That last point is a genuinely important property and it is worth
saying loudly, because it is easy to get wrong and the symptom
(discrepant totals across runs) is maddening to debug.

### The shape of the output

Two transforms sit between the combiner and the sink, and they exist
because Beam's `CombinePerKey` produces *keyed* output:

```python
def to_summary_row(item: tuple[str, dict[str, float]]) -> dict[str, Any]:
    """Flatten a (region, summary) pair into a flat output row."""
    key, value = item
    return {
        "region": key,
        "order_count": value["order_count"],
        "revenue_eur": value["revenue_eur"],
    }
```

and then the CSV formatting:

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

`to_summary_row` takes a **single tuple argument** because it is used
as a `beam.Map` function, and `Map` applies its function to one element
at a time. A two-argument function would need `beam.Map(lambda kv: ...)`
instead. This trips people up constantly.

`format_summary_csv` uses `csv.writer` rather than an f-string. The
comment in the source says why: "Using `csv.writer` rather than an
f-string means a region name containing a comma cannot corrupt the
output." It costs two lines and it removes a whole class of bug.

Note also that the `Map` to a flat row happens **before** the fan-out
to two sinks. In `project/batch_pipeline.py`:

```python
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

The CSV sink needs a *string*; the BigQuery sink needs a *dict*. The
fan-out is from `rows`, not from the stringified version, because
BigQuery should receive the typed row, not a parsed-back CSV line.

---

## 🧠 The testing strategy

### Three layers, and why three

The project has two test files, and they split along the line that
matters: **does this test need a runner?**

| Layer | File | Needs Beam? | Speed | What it catches |
|---|---|---|---|---|
| Pure logic | `project/tests/test_transforms.py` | no | ~0.1 s | Wrong arithmetic, wrong validation rules |
| Combiner | `project/tests/test_pipelines.py` | yes | ~1 s | Wrong merge semantics, wrong windowing |
| End-to-end | `project/tests/test_pipelines.py` | yes | ~2 s | Wrong wiring, wrong output format |

The pure layer is the important one, and the reason is a design
decision in `project/transforms.py`:

```python
try:  # pragma: no cover - import guard is exercised only when Beam is absent
    import apache_beam as beam
    from apache_beam.coders import FastPrimitivesCoder
    from apache_beam.io.textio import WriteToText

    BEAM_AVAILABLE = True
except ImportError:  # pragma: no cover
    beam = None  # type: ignore[assignment]
    FastPrimitivesCoder = None  # type: ignore[assignment]
    WriteToText = None  # type: ignore[assignment]
    BEAM_AVAILABLE = False
```

`transforms.py` has a **pure half** — `parse_order_line`,
`normalise_currency`, `is_valid_order`, `build_revenue_summary`,
`dedup_key`, `window_key` — that depends on nothing but the standard
library. It has a **Beam half** — `ParseOrderFn`, `RevenueByRegionFn`,
`to_summary_row`, `format_summary_csv` — that only exists when
`apache_beam` is importable.

The pure half exists because `apache-beam` is a heavy install, and
because a test that runs in 10 milliseconds can be run on every save,
while a test that takes 4 seconds can be run before you push. The
pure half is where most of the logic lives, so most of the tests live
there too.

There is also a **pure twin** of the combiner:

```python
def build_revenue_summary(
    rows: Iterable[dict[str, Any]],
    *,
    statuses: Sequence[str] = ("complete",),
) -> dict[str, dict[str, float]]:
    """Aggregate revenue per region from a collection of orders."""
    wanted = set(statuses)
    summary: dict[str, dict[str, float]] = {}

    for row in rows:
        if not is_valid_order(row):
            continue
        if row["status"] not in wanted:
            continue
        region = row["region"]
        bucket = summary.setdefault(region, {"order_count": 0.0, "revenue_eur": 0.0})
        bucket["order_count"] += 1
        bucket["revenue_eur"] += normalise_currency(float(row["amount"]), row["currency"])

    for bucket in summary.values():
        bucket["revenue_eur"] = round(bucket["revenue_eur"], 2)
    return summary
```

`build_revenue_summary` does exactly what `RevenueByRegionFn` does,
in plain Python. Two implementations of the same thing is normally a
smell — but here it buys something real: the pure version is the
**reference implementation** and the Beam version is the one under
test, and the two can be compared directly. If they disagree, one of
them is wrong and the test tells you which.

### The unit tests

The validation tests are parameterised, which is the right shape for
"seven rules":

```python
@pytest.mark.parametrize(
    "field,value",
    [
        ("order_id", ""),
        ("customer_id", ""),
        ("region", "UNKNOWN_REGION"),
        ("status", "weird"),
        ("currency", "XYZ"),
        ("order_ts", "not-a-timestamp"),
        ("amount", "not-a-number"),
        ("amount", -5.0),
    ],
)
def test_invalid_field_rejected(self, field, value):
    """A bad value in any validated field rejects the row."""
    row = dict(VALID_ORDER)
    row[field] = value
    assert is_valid_order(row) is False
```

Eight cases, one test. Adding a rule means adding a tuple, not writing
a new test function. And because each case changes exactly one field,
a failure points at exactly one rule.

There is a matching positive test — a row that passes every rule — so
that a change which makes the validator reject everything is caught
immediately. A validator that always returns `False` passes every
negative test.

### The combiner test

The combiner test is the one that matters most, because the combiner
is the part of the pipeline that runs in parallel and merges in an
arbitrary order:

```python
def test_merge_is_order_independent(self):
    """The combiner gives the same answer however the inputs are merged."""
    orders = [
        {"amount": 10.0, "currency": "EUR"},
        {"amount": 20.0, "currency": "EUR"},
        {"amount": 30.0, "currency": "EUR"},
    ]
    combiner = RevenueByRegionFn()

    left = combiner.create_accumulator()
    for order in orders[:2]:
        left = combiner.add_input(left, order)

    right = combiner.create_accumulator()
    for order in reversed(orders[2:]):
        right = combiner.add_input(right, order)

    merged = combiner.merge_accumulators([left, right])
    assert combiner.extract_output(merged) == {
        "order_count": 3,
        "revenue_eur": 60.0,
    }
```

Read what this test is actually doing: it builds two accumulators from
**disjoint halves** of the input, and it accumulates the second half in
**reverse order**. If the combiner were order-dependent, the two
accumulators would hold different values and the merge would not
reproduce the total.

This is the property that makes a `CombineFn` scalable. Beam merges
partial accumulators from different workers in an arbitrary order,
determined by which worker finished first. If the merge were not
order-independent, the job's answer would depend on the wall-clock
timing of the cluster. That is the single worst class of bug in a
distributed pipeline: it is not reproducible, it is not fixable by
retrying, and it usually shows up as a small discrepancy that nobody
can account for.

### The end-to-end test

The pipeline-level test uses a fixture for the temporary directory and
Beam's modern `TestPipeline` API:

```python
def test_end_to_end_revenue_summary(self, tmp_path):
    """The pipeline reads orders and writes the per-region summary."""
    from batch_pipeline import build_pipeline

    input_file = tmp_path / "orders.csv"
    input_file.write_text("\n".join(ORDER_LINES) + "\n", encoding="utf-8")
    output_prefix = tmp_path / "summary"

    with TestPipeline(options=beam_test_options()) as pipeline:
        build_pipeline(
            pipeline,
            input_path=str(input_file),
            output_path=str(output_prefix),
        )

    # The sink writes one sharded file plus the header.
    output_files = sorted(tmp_path.glob("summary*"))
    assert output_files, "the pipeline produced no output file"

    contents = "\n".join(f.read_text(encoding="utf-8") for f in output_files)
    assert "region,order_count,revenue_eur" in contents
    assert "EMEA,3,401.0" in contents
    assert "AMER,1,50.0" in contents
```

Three details worth copying:

**The test data is inline, five lines, hand-checkable.** `ORDER_LINES`
is a module-level constant:

```python
ORDER_LINES = [
    "o1,c1,2026-01-15T10:00:00+00:00,EMEA,web,EUR,complete,100.00,p1",
    "o2,c2,2026-01-15T11:00:00+00:00,EMEA,web,USD,complete,200.00,p2",
    "o3,c3,2026-01-15T12:00:00+00:00,AMER,web,EUR,complete,50.00,p3",
    "o4,c4,2026-01-15T13:00:00+00:00,AMER,web,EUR,cancelled,999.00,p4",
    "o5,c5,2026-01-15T14:00:00+00:00,EMEA,web,GBP,complete,100.00,p5",
]
```

Five orders, three currencies, two regions, one cancelled order that
must be excluded. The expected numbers are computed by hand in the
assertions: EMEA is `100.00 + 200.00 × 0.92 + 100.00 × 1.17 = 401.00`
and AMER is `50.00` because the cancelled 999.00 is filtered out.

You can verify the arithmetic yourself in ten seconds. That is the
whole point — a test whose expected value you cannot check by eye is a
test that will be rubber-stamped.

**The test asserts on the output file, not on a `PCollection`.** The
sink is the contract. If the file contains `EMEA,3,401.0`, the
pipeline did the right thing, whatever happened internally.

**`beam_test_options()` comes from `conftest.py`:**

```python
TEST_RUNNER = BundleBasedDirectRunner


def beam_test_options(**extra):
    """Return PipelineOptions for a local test run."""
    options = PipelineOptions(
        [
            "--runner",
            TEST_RUNNER,
            "--job_name",
            "test",
        ]
    )
    for key, value in extra.items():
        setattr(options, key, value)
    return options
```

`BundleBasedDirectRunner` rather than the newer Go-based
`DirectRunner`, for the same reason `beam_options.py` defaults to it:
the Prism runner does not yet support every trigger and windowing
combination, and the streaming pipeline's `AfterWatermark` trigger
panics on it. If you write a test that panics with an opaque message
about watermarks, this is why.

### Why the tests assert on substrings

```python
assert "EMEA,3,401.0" in contents
```

This is a substring assertion, not an exact-match assertion on the
whole file. That is a deliberate trade-off.

An exact match would be stronger — it would also catch a change in row
*order*. But `CombinePerKey` gives no ordering guarantee, so an exact
match would be **flaky**: it would pass on one run and fail on the next
depending on how the runner scheduled the work. A flaky test is worse
than a weak test, because it teaches the team to ignore red builds.

The substring form asserts the things that are actually guaranteed:
the header is right, and each region's numbers are right. The ordering
is not guaranteed, so the test does not assert on it.

If you need a deterministic order in the output — for a diff against a
golden file, or for a checksum — sort explicitly before writing, and
then assert exactly.

### What is not tested

Honesty about the gaps:

- **The BigQuery write is not tested.** It requires a BigQuery
  emulator or a real project, and neither is worth the setup cost for
  a course. In production this should be a separate integration test
  in CI, marked so it does not run on every pull request.
- **The DLQ path is not tested in this pipeline**, because
  `ParseOrderFn` skips malformed rows rather than routing them. Chapter
  6.4 shows how to add that, and what to test when you do.
- **The exchange rates are not tested against reality.** The test
  asserts that `100.0 GBP` becomes `117.0`, which is the *table's*
  claim, not the world's. Nothing can test that without a rates feed.
- **There is no test for a 5,000-row file.** The end-to-end test uses
  five rows. A test that runs the full sample data and asserts the
  four exact numbers is the obvious next step, and it is Exercise 1
  below.

---

## 🛠️ Hands-On

### Setup

You need the course project and the sample data. From the course root:

```bash
ls sample_data/orders.csv
ls project/transforms.py
```

Both should exist. If the sample data is missing, generate it:

```bash
.venv/bin/python resources/sample_data.py
```

Confirm the environment:

```bash
.venv/bin/python -c "import apache_beam; print(apache_beam.__version__)"
```

### Step 1 — run the pipeline and read the output

Run the shipped pipeline against the sample data:

```bash
.venv/bin/python project/batch_pipeline.py \
    --input ./sample_data/orders.csv \
    --output ./out/case-study/summary
```

The output directory contains one file. Read it:

```bash
cat ./out/case-study/summary*
```

You should see:

```text
region,order_count,revenue_eur
AMER,318,113592.19
APAC,285,108194.92
EMEA,322,118423.22
LATAM,320,110646.18
```

**These four numbers are the reference output of the whole course.** Every
subsequent chapter, every exercise, and every verification in this
case study checks against them.

### Step 2 — verify the numbers yourself

Do not take the numbers on trust. Compute them independently, with a
script that shares no code with the pipeline:

```python
"""Recompute the summary without Apache Beam."""
import csv
import collections

RATES = {"EUR": 1.0, "USD": 0.92, "GBP": 1.17, "JPY": 0.0064}

total_orders = 0
summary = collections.defaultdict(lambda: [0, 0.0])

with open("sample_data/orders.csv", encoding="utf-8") as handle:
    for row in csv.DictReader(handle):
        total_orders += 1
        if row["status"] != "complete":
            continue
        rate = RATES.get(row["currency"].upper())
        if rate is None:
            continue
        bucket = summary[row["region"]]
        bucket[0] += 1
        bucket[1] += round(float(row["amount"]) * rate, 2)

print("rows in file:", total_orders)
for region in sorted(summary):
    count, revenue = summary[region]
    print(f"  {region},{count},{round(revenue, 2)}")
```

Save it as `verify_summary.py` in the course root and run it:

```bash
.venv/bin/python verify_summary.py
```

Expected:

```text
rows in file: 5000
  AMER,318,113592.19
  APAC,285,108194.92
  EMEA,322,118423.22
  LATAM,320,110646.18
```

Two independent implementations — one in Beam, one in plain Python with
the `csv` module — producing the same four numbers. That is a much
stronger statement than "the pipeline did not crash".

Now the status breakdown, which explains the 4.02×:

```bash
.venv/bin/python -c "
import csv, collections
rows = list(csv.DictReader(open('sample_data/orders.csv')))
counts = collections.Counter(r['status'] for r in rows)
for status, n in sorted(counts.items()):
    print(f'  {status}: {n}')
print('total:', len(rows))
"
```

Expected:

```text
  active: 1262
  cancelled: 1188
  complete: 1245
  refunded: 1305
total: 5000
```

1,245 of 5,000 rows have `status == "complete"`. `5000 / 1245 = 4.016…`
— the **4.02× shuffle reduction** from Chapter 6.1. The filter that
makes this pipeline cheap is the filter that makes it *correct*, and
the reason it is placed before the combiner rather than inside it.

### Step 3 — prove the output is a function of the input

An idempotent pipeline produces the same output when you run it twice.
Run it again, to the same path:

```bash
.venv/bin/python project/batch_pipeline.py \
    --input ./sample_data/orders.csv \
    --output ./out/case-study/summary
cat ./out/case-study/summary*
```

The output is **identical**, and the file still has four data rows. This
is `FileBasedSink` doing a replace, not an append — the sink deletes
the existing destination before writing. Chapter 6.3 goes into the
mechanics.

Compare that with a destination that uses the default BigQuery
disposition. That is Step 5.

### Step 4 — change the policy without changing the code

The `--statuses` flag is the Template Method's parameterisation in
action. Run the same pipeline, counting `complete` and `active`:

```bash
.venv/bin/python project/batch_pipeline.py \
    --input ./sample_data/orders.csv \
    --output ./out/case-study/summary_active \
    --statuses complete,active
cat ./out/case-study/summary_active*
```

Expected:

```text
region,order_count,revenue_eur
AMER,634,222386.3
EMEA,608,215970.2
APAC,598,225810.57
LATAM,667,237869.33
```

1,245 + 1,262 = 2,507 orders counted, which is exactly
`complete + active`. The **code did not change** — only the parameter
did. That is the entire point of the Template Method: the policy moved
to the boundary, and the skeleton stayed fixed.

The row *order* may differ between runs — `CombinePerKey` gives no
ordering guarantee, and the runner is free to schedule the four keys in
any order it likes. The values are what matter.

### Step 5 — the defect in the shipped template

Now the real finding. The flex template at
`project/templates/batch_template.py` writes to BigQuery with
`WRITE_APPEND`:

```python
if bigquery_table:
    summary | "WriteBigQuery" >> beam.io.WriteToBigQuery(
        bigquery_table,
        write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
        create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
    )
```

`project/batch_pipeline.py` has the same line.

**`WRITE_APPEND` is the wrong disposition for this job.** This pipeline
computes a *full refresh* of the revenue summary from the complete order
history — it is not an incremental delta. Appending means:

| Run | Table contents | Revenue for a region |
|---|---|---|
| 1 | 4 rows (the correct summary) | 318 orders, 113592.19 |
| 2 | 8 rows (the summary, twice) | 636 orders, 227184.38 |
| 3 | 12 rows | 954 orders, 340776.57 |

Every re-run **doubles** the revenue. A retry after a transient
failure — the single most common reason to re-run a batch job — would
silently corrupt the table. There is no error, no failed job, no alert.
The dashboard just shows twice the revenue.

The same bug is flagged in Chapter 5.4, and the reasoning is repeated
here because this is the case study: the pattern is a *full refresh*, so
the disposition must be `WRITE_TRUNCATE`.

The fix:

```python
if bigquery_table:
    summary | "WriteBigQuery" >> beam.io.WriteToBigQuery(
        bigquery_table,
        write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE,
        create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
    )
```

And if the table is **date-partitioned**, `WRITE_TRUNCATE` truncates
only the partition the job writes to — so a backfill for January 10th
does not touch January 15th. That is the property that makes the
pipeline backfillable, and Chapter 6.5 covers it in detail.

There is one restriction to know, and it is not about `WRITE_TRUNCATE`
at all. Beam's source has this check:

```text
    if write_disposition in (BigQueryDisposition.WRITE_EMPTY,
                             BigQueryDisposition.WRITE_TRUNCATE):
      raise ValueError(
          'Write disposition %s is not supported for'
          ' streaming inserts to BigQuery' % write_disposition)
```

So `WRITE_TRUNCATE` is refused on the **streaming inserts** path — the
`method="streaming_inserts"` variant, which is what a *streaming*
pipeline uses. This is a batch pipeline, and the batch path (a BigQuery
load job) accepts `WRITE_TRUNCATE` without complaint.

That is the right rule for the right reason: a truncate is a
full-refresh operation, and a streaming pipeline never has a "full
refresh" moment. If you ever convert this pipeline to streaming, you
must go back to `WRITE_APPEND` — and then you need a different
idempotency strategy, because there is no longer a single write to
repeat.

The same reasoning applies to the CSV sink, and it is already correct
there — `FileBasedSink` replaces rather than appends, which gives the
same idempotency for free. The two sinks behave differently by
default, which is exactly the kind of trap that costs a week.

### Step 6 — test the pipeline

Run the full suite:

```bash
.venv/bin/python -m pytest project/tests/ -q
```

Expected:

```text
.............................................................            [100%]
61 passed, 1 warning in 4.44s
```

The warning is a pytest collection warning about `TestPipeline` having
an `__init__` constructor — it comes from Beam's own testing module and
is harmless.

Now add the test the project is missing: the full-file end-to-end
check against the four reference numbers. Create
`project/tests/test_reference_output.py`:

```python
"""Assert the pipeline reproduces the documented reference output."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

apache_beam = pytest.importorskip("apache_beam", reason="apache-beam is not installed")

from apache_beam.testing.test_pipeline import TestPipeline  # noqa: E402

from conftest import beam_test_options  # noqa: E402

#: The documented reference output. Four regions, 1,245 counted orders.
EXPECTED = {
    "AMER": (318, 113592.19),
    "APAC": (285, 108194.92),
    "EMEA": (322, 118423.22),
    "LATAM": (320, 110646.18),
}


def _parse(output_file):
    """Parse a summary CSV into a dict of region -> (count, revenue)."""
    rows = {}
    for line in output_file.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("region,"):
            continue
        region, count, revenue = line.split(",")
        rows[region] = (int(count), float(revenue))
    return rows


def test_matches_documented_reference_output(tmp_path):
    """The pipeline reproduces the numbers in the course material."""
    from batch_pipeline import build_pipeline

    sample = Path(__file__).resolve().parents[2] / "sample_data" / "orders.csv"
    assert sample.is_file(), f"sample data missing: {sample}"

    output_prefix = tmp_path / "summary"

    with TestPipeline(options=beam_test_options()) as pipeline:
        build_pipeline(
            pipeline,
            input_path=str(sample),
            output_path=str(output_prefix),
        )

    output_files = sorted(tmp_path.glob("summary*"))
    assert output_files, "the pipeline produced no output file"

    actual = _parse(output_files[0])
    assert actual == EXPECTED
```

Run it:

```bash
.venv/bin/python -m pytest project/tests/test_reference_output.py -v
```

Expected:

```text
test_matches_documented_reference_output PASSED
```

Now run the whole suite again:

```bash
.venv/bin/python -m pytest project/tests/ -q
```

Expected:

```text
62 passed, 2 warnings in 3.08s
```

The count has gone from 61 to 62. That new test is the one that makes
the course's numbers a **contract** rather than a claim: if a change to
the pipeline shifts the revenue, it fails, and the failure says exactly
what moved.

### Step 7 — deploy it as a flex template

Build the template image:

```bash
gcloud dataflow flex-template build batch_template.py \
    --project YOUR_PROJECT_ID \
    --region us-central1 \
    --image gcr.io/YOUR_PROJECT_ID/dataflow/batch-template:latest \
    --temp-location gs://YOUR_BUCKET/tmp
```

Then run it:

```bash
gcloud dataflow jobs run revenue-summary-2026-01-15 \
    --project YOUR_PROJECT_ID \
    --region us-central1 \
    --image gcr.io/YOUR_PROJECT_ID/dataflow/batch-template:latest \
    --temp-location gs://YOUR_BUCKET/tmp \
    --staging-location gs://YOUR_BUCKET/staging \
    --input gs://YOUR_BUCKET/orders/dt=2026-01-15/orders.csv \
    --output gs://YOUR_BUCKET/summary/dt=2026-01-15 \
    --bigquery-table YOUR_PROJECT_ID.your_dataset.orders_by_region \
    --statuses complete
```

Look at what is and is not in that command:

**Parameters (the operator's choices):** `--input`, `--output`,
`--bigquery-table`, `--statuses`, `--temp-location`,
`--staging-location`, and the job name.

**Structure (fixed in the code):** the stage order, the validation
rules, the exchange rate table, the combiner, the output schema.

**Not a parameter:** anything that would change the *meaning* of the
numbers. There is no `--include-cancelled` flag separate from
`--statuses`, and no `--rounding-mode` flag. Those would be new
requirements, and new requirements mean new code and new review, not
new arguments.

Note that `--input` and `--output` are `required=True` in the template,
unlike `project/batch_pipeline.py` where they have defaults. That is
the right asymmetry: a template that runs on Dataflow should never
silently use a local path.

### Step 8 — the full design, assembled

Here is the complete pipeline as one function, which is the skeleton
the Template Method protects:

```python
def build_pipeline(
    pipeline: beam.Pipeline,
    *,
    input_path: str,
    output_path: str,
    bigquery_table: str | None = None,
    statuses: tuple[str, ...] = ("complete",),
) -> None:
    """Build the revenue pipeline for the flex template."""
    orders = (
        pipeline
        | "ReadOrders" >> ReadFromText(input_path)
        | "ParseOrders" >> beam.ParDo(ParseOrderFn())
    )

    completed = orders | "KeepCompletedOrders" >> beam.Filter(
        lambda order: order["status"] in statuses
    )

    summary = (
        completed
        | "KeyByRegion" >> beam.Map(lambda order: (order["region"], order))
        | "RevenueByRegion" >> beam.CombinePerKey(RevenueByRegionFn())
        | "ToFlatRow" >> beam.Map(to_summary_row)
    )

    summary | "FormatCsv" >> beam.Map(format_summary_csv) | "WriteSummary" >> WriteToText(
        output_path,
        header="region,order_count,revenue_eur",
        num_shards=1,
        shard_name_template="",
    )

    if bigquery_table:
        summary | "WriteBigQuery" >> beam.io.WriteToBigQuery(
            bigquery_table,
            write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE,
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
        )
```

Seven transforms. One conditional branch. Every design decision from
this chapter is visible in twenty lines:

- The filter is **before** the combine (cost: 4.02×).
- The `Map` to a flat row is **after** the combine (the combiner is
  keyed; the output is not).
- The CSV formatting is **after** the fan-out point, so BigQuery gets
  typed rows.
- The BigQuery write is **conditional**, so the pipeline runs with no
  BigQuery at all.
- `num_shards=1` and `shard_name_template=""` give one predictable
  file — right for a four-row output, wrong for a large one.

---

## 🛠️ Common Errors and Fixes

### `AssertionError: the pipeline produced no output file`

The most common failure in the end-to-end test.

**The real message:**

```text
E       assert output_files, "the pipeline produced no output file"
E       assert []
```

**Cause:** the output file is not where the test is looking. The
project's `WriteToText` call uses `num_shards=1` and
`shard_name_template=""`, so the file is named exactly after the output
prefix — `summary`, not `summary-00000-of-00001`.

**Fix:** glob for the prefix, not for a specific filename:

```python
output_files = sorted(tmp_path.glob("summary*"))
assert output_files, "the pipeline produced no output file"
```

Note the `*`. A test that globs for `summary` exactly will pass today
and fail the moment someone changes the shard template.

### `OSError: No files found based on the file pattern ./sample_data/orders.csv`

**The real message:**

```text
OSError: No files found based on the file pattern ./sample_data/orders.csv
```

**Cause:** the working directory is not the course root. `ReadFromText`
resolves relative paths against the process's current directory, and
the course root is `data-engineering/data-Course/google/Dataflow/`.

**Fix:** run from the course root, or use an absolute path. The test
suite avoids the problem entirely by building the sample path relative
to the test file:

```python
sample = Path(__file__).resolve().parents[2] / "sample_data" / "orders.csv"
```

That is the right pattern for anything that might run from anywhere.

### `ModuleNotFoundError: No module named 'transforms'`

**The real message:**

```text
ModuleNotFoundError: No module named 'transforms'
```

**Cause:** a script outside `project/` is importing `transforms`
directly. The module lives at `project/transforms.py`.

**Fix:** either run the script from inside `project/`, or add the path
before the import:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from transforms import ParseOrderFn, RevenueByRegionFn
```

`project/batch_pipeline.py` does exactly this on line 34.

### `ValueError: could not convert string to float: 'amount'`

**The real message:**

```text
ValueError: could not convert string to float: 'amount'
```

**Cause:** a hand-written test CSV includes the header row, so the
first "row" has nine fields — which passes the field-count check — and
`amount` is the literal string `"amount"`.

This is a genuinely subtle bug, because the header row *looks* like a
valid row. It is a validation gap, not a parsing gap: the parser
accepts the right *shape* and the wrong *content*.

**Fix:** the project's `try_parse_order_line` already coerces the
amount and returns `None` on failure:

```text
    try:
        row["amount"] = float(row["amount"])
    except (TypeError, ValueError):
        return None
```

But a header row still needs to be skipped by the source. When
writing test fixtures, either omit the header or filter it in the
source:

```python
lines = (
    pipeline
    | "ReadOrders" >> beam.io.ReadFromText(input_path)
    | "DropHeader" >> beam.Filter(lambda line: not line.startswith("order_id,"))
)
```

### `TypeError: '>' not supported between instances of 'int' and '_InvalidUnpickledPCollection'`

**The real message:**

```text
TypeError: '>' not supported between instances of 'int' and '_InvalidUnpickledPCollection'
```

**Cause:** a `PCollection` was captured in a closure and used in an
arithmetic comparison — for example, computing a DLQ rate by dividing
by the total count.

**Fix:** pass the count as a **side input**, and use a `DoFn` rather
than a `Map`, because `beam.Map` functions cannot take side-input
keyword arguments:

```python
class ComputeRateFn(beam.DoFn):
    def process(self, dlq_count, total=beam.DoFn.ElementParam):
        yield {
            "dlq_count": dlq_count,
            "total": total,
            "dlq_rate": dlq_count / max(total, 1),
        }


stats = dlq_count | "ComputeRate" >> beam.ParDo(
    ComputeRateFn(), total=beam.pvalue.AsSingleton(total)
)
```

Chapter 6.4 covers this pattern in full.

### `TypeError: Map.<locals>.<lambda>() got an unexpected keyword argument 'total'`

**The real message:**

```text
TypeError: Map.<locals>.<lambda>() got an unexpected keyword argument 'total'
```

**Cause:** `beam.Map` was given a function with side-input keyword
arguments. `Map` functions take exactly one argument — the element.

**Fix:** use `beam.ParDo` with a `DoFn` that declares the side input
via `beam.DoFn.ElementParam`. This is the error above, in a different
guise.

### `AttributeError: 'property' object has no attribute 'windowfn'`

**The real message:**

```text
AttributeError: 'property' object has no attribute 'windowfn'
```

**Cause:** `beam.pvalue.AsSingleton(...)` was passed as a **default
argument value** on the `DoFn` method, instead of being passed at the
`ParDo` call site.

**Fix:** declare the parameter with a default of `beam.DoFn.ElementParam`
and pass the side input when you construct the `ParDo`:

```python
stats = dlq_count | "ComputeRate" >> beam.ParDo(
    ComputeRateFn(), total=beam.pvalue.AsSingleton(total)
)
```

### `TypeError: FileBasedSink.__init__() missing 1 required positional argument: 'coder'`

**The real message:**

```text
TypeError: FileBasedSink.__init__() missing 1 required positional argument: 'coder'
```

**Cause:** a custom sink subclassed `FileBasedSink` without passing the
`coder` argument to `super().__init__()`.

**Fix:**

```python
super().__init__(
    path,
    coder=coders.ToBytesCoder(),
    shard_name_template="",
    num_shards=1,
)
```

Chapter 6.3 builds this sink in full, to demonstrate the append
failure mode.

### `TypeError: unsupported operand type(s) for >>: 'str' and 'AppendingTextSink'`

**The real message:**

```text
TypeError: unsupported operand type(s) for >>: 'str' and 'AppendingTextSink'
```

**Cause:** a `FileBasedSink` subclass was used directly as a transform.
A sink is not a `PTransform`.

**Fix:** wrap it in `beam.io.Write`:

```python
summary | "WriteSummary" >> beam.io.Write(AppendingTextSink(OUTPUT, header="..."))
```

### `RuntimeError: Transform name is already used`

**The real message:**

```text
RuntimeError: Transform name is already used
```

**Cause:** the same label appears twice in one Python scope. Beam
requires unique labels within a pipeline construction function.

**Fix:** give each transform a distinct label. It is worth noting that
Beam's uniqueness rule is *per pipeline*, not per file, so two helper
functions that are each called once in the same pipeline also
collide.

This is why the labels in `build_pipeline` are all distinct even
though `project/batch_pipeline.py` and `project/templates/batch_template.py`
use the same names — they are never built in the same pipeline.

### `TypeError: 'Order' is not iterable`

**The real message:**

```text
TypeError: 'Order' is not iterable
```

**Cause:** `beam.io.WriteToParquet` received dataclass-like elements.
Its internal `_RowDictionariesToArrowTable` does `row[n]`, which needs
a mapping, not an arbitrary object.

**Fix:** convert to a dict before the write:

```python
from dataclasses import asdict

rows | "ToDict" >> beam.Map(asdict) | "WriteParquet" >> beam.io.WriteToParquet(
    path, schema=pyarrow_schema, num_shards=1
)
```

Chapter 6.2 covers the Parquet path in full.

### `RuntimeError: Pipeline failed in state RUNNING`

**The real message:**

```text
RuntimeError: Pipeline failed in state RUNNING
```

The real cause is always earlier in the log. Search upwards for the
first `ERROR` line, not the last.

The most common causes in this pipeline:

- `ValueError: unknown currency: 'XYZ'` — a currency was added to the
  data that is not in `CURRENCY_TO_EUR`. But note that `is_valid_order`
  rejects unknown currencies *before* the converter sees them, so this
  error means a code path bypassed the validator.
- `AttributeError: 'NoneType' object has no attribute 'get'` — a row
  reached a transform expecting a dict.
- `FileNotFoundError` on a GCS path — the bucket, the path, or the
  service account is wrong.

---

## 💡 Production Notes

### What the numbers cost on Dataflow

The course data is 5,000 rows, which is nothing. To make the cost
model concrete, scale it: a real order feed is roughly 5 million rows
per day.

| Metric | 5,000 rows (course) | 5,000,000 rows (realistic) |
|---|---|---|
| Bytes read | ~1.1 MB | ~1.1 GB |
| Shuffle elements | 5,000 (or 1,245 filtered) | 5,000,000 (or 1,245,000 filtered) |
| Output | 4 rows | 4 rows |
| Wall clock, 1 worker | ~2 s | ~3 min |
| Wall clock, 10 workers | ~2 s (fixed overhead) | ~25 s |
| Dataflow cost, n1-standard-4 | ~$0.01 | ~$0.35 |
| Shuffle bytes | ~0.2 MB | ~180 MB |

The interesting number is the last one. The shuffle dominates the
cost, and the shuffle is exactly what the early filter reduces. The
4.02× filter saving is not a micro-optimisation — at 5 million rows it
is the difference between a $0.35 job and a $1.40 job, and the
difference between a 25-second job and a 100-second job.

The deeper point: **the filter is a business rule that happens to be
an optimisation**. You cannot reorder the stages for performance and
preserve correctness, because "only completed orders count" is a
statement about what revenue *is*. The optimisation and the requirement
are the same decision, which is the ideal situation — there is no
tension to resolve, and no future change to the business rule will
quietly undo the optimisation.

### What breaks at 3am

Ranked by how often it happens and how badly it hurts:

**1. The upstream file is late or truncated.** The most common failure
by a wide margin. A producer writes 5 million rows but only flushes
4.2 million before the window closes. The pipeline succeeds. The
dashboard shows a revenue number that is 16% too low, and nothing
alerts.

The defence is a **completeness check that is not part of the
pipeline**: compare the row count against an expected count from the
producer's own control table, and fail loudly when they disagree. A
pipeline cannot detect its own incompleteness — only the producer's
metadata can.

**2. A schema change upstream.** A new column appears, or a column is
renamed. The field-count check catches a *renamed* column (wrong
number of fields, or a non-numeric amount). It does **not** catch an
*added* column, because `try_parse_order_line` rejects any row whose
field count differs from nine — including a row with ten.

That is correct behaviour, and it is also a hard failure: every row in
the file is rejected, the output is empty, and the only symptom is a
warning log per row. Route the malformed rows to a DLQ (Chapter 6.4)
and you get a count and a sample of what changed, instead of a
million warnings.

**3. The BigQuery write fails after the CSV write succeeded.** The
fan-out means the two sinks have independent fate. The CSV is correct;
the table is stale. The job reports partial success in some runner
versions and total failure in others — **check the actual state of
both sinks, not the job status.**

**4. A retry doubles the BigQuery table.** Covered in Step 5. This is
the failure that produces no signal at all, and it is why
`WRITE_TRUNCATE` is not optional for a full-refresh batch job.

**5. The exchange rate table is stale.** Covered above. Silent,
cumulative, and discovered by finance rather than by monitoring.

### The monitoring that is worth building

For a pipeline this small, three signals are enough:

**Row count in, row count out.** The pipeline logs the skipped-row
count as warnings. Turn that into a metric and alert on it: a jump from
zero malformed rows to 0.5% of the file is a schema change, not bad
data.

**Output row count.** The summary always has one row per region that
had revenue. If AMER disappears from the output, either AMER had no
orders (possible, worth a warning) or the filter changed (not
possible). Alerting on a *missing region* is cheap and catches a class
of bug that a total-value alert misses.

**Output total.** EUR 450,856.51 for the course data. A day-over-day
change of more than, say, 30% is worth a human look. It will fire
sometimes for legitimate reasons — a large order, a seasonality effect
— and that is fine. The alert is a prompt to look, not a conclusion.

Do **not** alert on the exact revenue. It changes every day, and an
alert on a number that always changes is an alert nobody reads.

### Idempotency, restated precisely

The pipeline is idempotent **as a whole** because:

| Property | How it is achieved |
|---|---|
| The transforms are deterministic | No wall-clock reads, no unseeded randomness, no `id()`-based keys |
| The output path is a function of the input date | `dt=2026-01-15` in, `dt=2026-01-15` out |
| The CSV sink replaces | `FileBasedSink` deletes the destination before writing |
| The BigQuery sink truncates | `WRITE_TRUNCATE`, after the Step 5 fix |
| The staging location is unique per run | Derived from the date and mode |

Two of those needed changing. The first three rows are properties of
the design; the last two are properties of the *deployment*. A
pipeline can be idempotent in its logic and non-idempotent in its
configuration, and the configuration is where the incidents happen.

### The observability gap

The pipeline logs warnings for malformed rows but emits no metrics.
In production, use Beam's metrics API:

```python
class ParseOrderFn(beam.DoFn):
    """Parse CSV lines into order dicts, counting what it rejects."""

    def process(self, line: str, timestamp=beam.DoFn.TimestampParam) -> Iterable[Any]:
        """Parse one line and emit the resulting order dict."""
        row = try_parse_order_line(line)
        if row is None:
            self._malformed.inc()
            log.warning("skipping malformed order line: %.120s", line)
            return
        if not is_valid_order(row):
            self._invalid.inc()
            log.warning("skipping invalid order: %s", row.get("order_id"))
            return
        self._accepted.inc()
        yield row

    def setup(self):
        """Create the counters."""
        self._malformed = beam.metrics.Metrics.counter("orders", "malformed")
        self._invalid = beam.metrics.Metrics.counter("orders", "invalid")
        self._accepted = beam.metrics.Metrics.counter("orders", "accepted")
```

The counters are visible in the Dataflow job graph, exportable to
Cloud Monitoring, and alertable. That turns "there was a warning in the
log" into "the malformed rate crossed 0.1%", which is a signal you can
page on.

### The deployment shape

In production I would split this into two artifacts:

- **The pipeline image**, built once from a tagged commit and pushed to
  Artifact Registry. Never built at job-launch time.
- **The launch configuration**, a YAML or a scheduler job that names
  the image and supplies the parameters. The parameters change daily;
  the code does not.

That separation is what makes the pipeline auditable. When a dashboard
disagrees with the source system six months later, you need to know
which version of the code produced the number. `gcloud dataflow jobs
describe` gives you the image; the image's tag gives you the commit;
the commit gives you the diff.

### What I would change in production

The pipeline is correct, tested, and deployable. These are the changes
I would make before it touched real revenue, in priority order.

**1. Fix the `WRITE_APPEND` disposition.** Already covered in Step 5,
and it is a one-line change. It goes first because it is the only
defect that silently produces wrong numbers.

**2. Version the exchange rates by date.** Store rates with an
effective date, carry the order date to the conversion, and select the
rate by that date. Add a `rates_version` column to the output so every
number is traceable to the rates that produced it.

The current design converts using "whatever rate is in the table", which
means a backfill produces different numbers than the original run. That
is not acceptable for a financial report, and it is invisible — both
runs succeed.

**3. Add a DLQ and make the rejected-row rate a metric.** Right now a
malformed row is logged and dropped. That is the right behaviour for a
course, and it is wrong for a financial pipeline: every rejected row
should land somewhere a human can look at it, and the rate should
alarm. Chapter 6.4 has the pattern.

**4. Add the completeness check.** Compare the input row count against
the producer's expected count, and fail the job when they disagree.
This is the only defence against a truncated upstream file, and it has
to live outside the pipeline — the pipeline cannot know how many rows
it should have received.

**5. Handle late-arriving orders.** The pipeline assumes every order
for a date is in that date's file. In reality, an order placed at
23:59 on the 15th may be written to the 16th's file. The current
design has no notion of a data date separate from the run date, so
such an order is either missed or double-counted on a later re-run.

The fix is a **data date** — the date the order belongs to, taken from
`order_ts` — and a re-run window: each day's job processes the previous
N days, replacing (not appending to) each partition. N is a business
decision, not a technical one.

**6. Partition the output by date.** Related to the previous item. The
output path should be `summary/dt=YYYY-MM-DD/`, with the BigQuery
table partitioned on the same field. Without partitioning, every run
rewrites the whole table and every backfill is a full refresh. With
partitioning, a backfill touches one partition and a re-run of one day
is cheap.

**7. Write Parquet, not CSV, to the lake.** CSV is fine for a
dashboard and terrible for a data lake. Parquet is columnar, typed,
compressed, and readable by everything. Chapter 6.2 covers the
schema and the writer.

**8. Move the reference join to a shuffle join.** The current
`_enrich_with_category` does a **linear scan** of the reference list
for every order. That is O(n × m) — 5,000 orders × 50 reference rows
is 250,000 comparisons, and at 5 million orders it is 250 million. The
fix is either a `CoGroupByKey` (a shuffle join) or, better, a side
input wrapped in `beam.pvalue.AsDict` so the lookup is O(1).

This one is worth dwelling on, because the reference table is small
enough that the linear scan is invisible on the course data — it is
fast enough to look correct, and it will fall over in production.

**9. Use `beam.Reshuffle` before the combiner when the key is skewed.**
If one region ever dominated the data, `CombinePerKey` would put all
of its orders on one worker. `beam.Reshuffle` distributes them. The
course data is balanced (1,211–1,284 rows per region), so the shuffle
is not needed now, but a distribution shift in the business would
change that.

**10. Assert the expected output shape.** Add a stage at the end that
checks the output has one row per expected region, and fails the job if
not. It is a `Filter` and a `CombinePerKey` and it converts a silent
zero-row output into a failed job.

### What I would *not* change

Some things look like over-engineering and are not:

- **The explicit `CombineFn`.** `beam.CombinePerKey(sum)` would be
  shorter for one metric, but you need two metrics, and once you have
  two metrics the explicit combiner is clearer than a tuple of sums. The
  explicit version also gives you the accumulator you can reason about.

- **The pure/twin split in `transforms.py`.** Two implementations of
  the same logic is normally a smell. Here the pure one is the
  reference and the Beam one is under test, and the difference in test
  runtime (milliseconds versus seconds) is what makes the fast feedback
  loop possible.

- **The explicit label on every transform.** `pipeline | beam.Map(f)`
  works. But an unlabelled transform gets an auto-generated name like
  `Map/Map/Map`, which tells you nothing in the job graph at 2am.
  `"KeyByRegion"` tells you everything.

- **`num_shards=1` for the CSV sink.** For a four-row output it is
  right. It is also wrong for any output large enough to matter, which
  is why item 7 above replaces the CSV sink with Parquet rather than
  tuning the shard count.

---

## 🔑 Key Takeaways

- **The Template Method fixes the stage order and parameterises only the data.** The skeleton is the algorithm; the parameters are the policy. Every flag you add multiplies the number of code paths, and code paths are where bugs live.
- **The stage order is not a style choice — it is the cost model.** Filter before the combine: 1,245 elements cross the shuffle instead of 5,000, a 4.02× reduction measured on the course data. The filter is a business rule that happens to be an optimisation, which is the ideal situation.
- **The combiner computes; the pipeline decides.** A `CombineFn` must be associative and commutative, so filtering inside `add_input` would make the merge semantics much harder to reason about. Keep policy at the boundary.
- **Round once, at the end.** If `add_input` rounded each amount, the total would depend on how the inputs happened to be partitioned across workers. `extract_output` rounds because that is the only place where the answer is independent of the execution.
- **The pure half is the reference implementation.** `build_revenue_summary` and `RevenueByRegionFn` implement the same logic twice on purpose: the pure one is testable without Beam, runs in milliseconds, and serves as the oracle for the Beam one.
- **A pipeline is idempotent only if its configuration is too.** The logic was already deterministic; `WRITE_APPEND` and a shared output prefix were what broke it. Configuration is where the incidents happen.
- **`WRITE_APPEND` in a full-refresh batch job is a defect, not a default.** It doubles the revenue on every re-run, with no error and no alert. `WRITE_TRUNCATE` — or `WRITE_TRUNCATE` on a partitioned table — is the correct disposition.
- **The reference numbers are a contract, not a claim.** AMER 318/113592.19, APAC 285/108194.92, EMEA 322/118423.22, LATAM 320/110646.18, totalling 1,245 counted orders out of 5,000. A test that asserts them makes the next change reviewable.
- **A pipeline cannot detect its own incompleteness.** Only the producer's expected row count can. The upstream-file-is-truncated failure needs a check that lives outside the pipeline.
- **Never assert on row order.** `CombinePerKey` gives no ordering guarantee, so an exact-match test is flaky. Assert on the values, and sort explicitly if you need a deterministic order.

---

## 📚 Practice Exercises

1. **Add the reference-output test.** Create
   `project/tests/test_reference_output.py` as in Step 6, with the four
   expected regions and their exact counts and revenue. Then run the
   full suite and confirm all tests still pass. **Expected:** the new
   test passes and the suite count increases by one.

2. **Prove the filter placement is the cost.** Write a script that runs
   the pipeline twice — once with the filter before the combine, once
   with it after — and counts the elements entering the shuffle using
   `beam.metrics.Metrics.counter` in a `DoFn`. **Expected:** 5,000
   elements in the filter-last version and 1,245 in the filter-first
   version, with identical output values. Chapter 6.1 has the
   measurement.

3. **Parameterise the output path by date.** Add a `--data_date`
   argument to `project/batch_pipeline.py` and derive the output path
   as `output_path + "/dt=" + data_date`. Run it for two dates and
   confirm the two partitions coexist. **Expected:** two directories,
   each with its own summary file, and the live one untouched. Chapter
   6.5 has the full treatment.

4. **Fix the BigQuery disposition and prove it.** Change `WRITE_APPEND`
   to `WRITE_TRUNCATE` in both `project/batch_pipeline.py` and
   `project/templates/batch_template.py`. Then write a test that
   asserts the chosen disposition, using `beam.io.BigQueryDisposition`
   — you may need to read the transform's attributes rather than
   running it. **Expected:** the test fails before the change and
   passes after, and it will fail again if anyone reintroduces
   `WRITE_APPEND`.

5. **Make the reference join O(1).** The current
   `_enrich_with_category` scans the whole reference list for every
   order. Replace the side input with `beam.pvalue.AsDict(reference)`
   so the lookup is a dict access. **Expected:** the same output, with
   the per-order cost going from O(m) to O(1). Use
   `sample_data/product_reference.ndjson` as the input.

6. **Add a DLQ to the parse stage.** Modify `ParseOrderFn` — or wrap it
   — to route malformed and invalid rows to a tagged side output, and
   write them to a file. Then count how many of the five rows in
   `sample_data/malformed_orders.csv` land in the DLQ. **Expected:**
   all five, each with a reason. Chapter 6.4 has the tagged-output
   pattern, and it is the single highest-value change you can make to
   this pipeline before it runs in production.

---

## 📖 Further Reading

- [Apache Beam Python SDK Quickstart](https://beam.apache.org/documentation/sdks/python/getting-started/) — the shortest path from `pip install` to a running pipeline.
- [Beam's Intro to Beam](https://beam.apache.org/documentation/basic-concepts/introduction/) — the canonical vocabulary for PCollection, PTransform, and the runner, which is what the Template Method skeleton is built from.
- [Beam SDK How-to Guides: Combiners](https://beam.apache.org/documentation/sdks/python/how-to/combiners/) — how `CombineFn` merging works, and why associativity matters.
- [BigQuery write dispositions](https://cloud.google.com/bigquery/docs/writing-append) — the authoritative list of `WRITE_APPEND`, `WRITE_TRUNCATE`, and `WRITE_EMPTY`, and the restriction on truncated tables.
- [Dataflow flex templates](https://cloud.google.com/dataflow/docs/templates/overview-flex-templates) — how a Python file becomes a deployable Dataflow template.
- [Testing Beam pipelines](https://beam.apache.org/documentation/sdks/python/testing/) — `TestPipeline`, `assert_that`, and the direct runner's role in unit testing.
