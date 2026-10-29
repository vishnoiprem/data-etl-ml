# 6.4 — Error Handling & DLQ

> **Section 6 · Batch Pipeline Engineering · Lecture 6.4 · 6:30**

## 🎯 What you will learn

- What actually happens when a `DoFn` raises: the bundle is retried, and then the job fails
- Why "log and skip" is data loss with extra steps, and what the alternative is
- The working DLQ pattern in apache-beam 2.77: a `ParDo` with a tagged side output — and the fact that **`beam.FilterInto` does not exist**
- `try_parse_order_line` and `is_valid_order`: the two different kinds of "bad row", and why conflating them is a bug
- The difference between "skip the bad row" and "route the bad row", in terms of auditability
- Poison pills: what they are, why a batch pipeline can survive them, and why a streaming pipeline cannot
- The four failure modes you will actually meet, and the right response to each
- How to monitor a DLQ, and the alert that tells you the problem is a data problem and not a code problem

---

## 🧠 Concept

### The question is not "should the job fail?"

The first instinct on encountering a malformed row is to decide whether
the job should fail or continue. That framing is wrong for batch, and
it is wrong in a way that produces bad systems.

The right question is: **what should happen to this row, and how will
anyone find out?**

There are only two honest answers:

1. **The row is invalid and will never be valid.** Route it somewhere
   a human can look at it, and count it.
2. **The row is invalid but might become valid later** — a late
   reference record, a currency that has not been loaded yet, an order
   that arrived before its customer. Route it to a *retry* location
   with a deadline, and count it.

"Skip it and log a line" is a third answer, and it is the worst of the
three: the data is gone, the log is not queryable, and nobody is
paged. It is data loss with a comforting log message attached.

### What actually happens when a `DoFn` raises

This is worth being precise about, because the mechanics determine what
your options are.

When `DoFn.process` raises an exception:

1. **The bundle fails.** A bundle is a chunk of elements — typically a
   few hundred to a few thousand, depending on the source and the
   runner's configuration.
2. **The runner retries the bundle.** The Dataflow service retries a
   failed bundle a number of times before giving up. On the Direct
   Runner, the behaviour differs, but a failure still propagates.
3. **If the retries are exhausted, the job fails.** The job's state
   becomes `JOB_STATE_FAILED`, and it stops.

Two consequences follow, and they pull in opposite directions.

**Consequence one: the elements in the failed bundle are not
partially processed.** Beam's model is that a bundle is retried as a
unit. So a `DoFn` that raises on element 400 of a 1,000-element bundle
does not lose elements 1–399 — they are reprocessed on the retry. That
is good: raising is *safe* with respect to the elements in the same
bundle.

**Consequence two: a single poison-pill element takes down every
bundle that contains it.** If one element in a 10-million-line file
raises every time, and the runner re-bundles the file the same way,
then every bundle containing that element fails, retries, and fails
again. The job never completes. And because the file is re-read from
the same offset, the poison pill lands in a bundle again and again.

This is the **poison pill** problem, and it is the central tension of
error handling in Beam.

You have exactly three ways out:

| Strategy | What it does | Cost |
|---|---|---|
| **Let it fail** | The job fails; a human fixes the data or the code and re-runs. | The whole job is blocked by one row. |
| **Skip the element** | The `DoFn` catches the exception and continues. | The row is lost unless you route it somewhere. |
| **Route the element** | The `DoFn` catches the exception and yields it to a side output. | The main output is complete; the bad row is preserved and countable. |

The third is the right answer, and it is what the rest of this chapter
is about.

### The DLQ pattern that actually works in 2.77

There is a transform that many blog posts and LLM answers claim exists:

```text
orders | "Split" >> beam.FilterInto("valid", "dlq", lambda o: is_valid(o))
```

It does not. Verified in this environment:

```bash
python -c "import apache_beam as beam; print(hasattr(beam, 'FilterInto'))"
python -c "import apache_beam.transforms as t; print(hasattr(t, 'FilterInto'))"
```

```text
False
False
```

`beam.FilterInto` is a common hallucination. There is no such
transform in apache-beam 2.77, in `apache_beam.transforms`, or anywhere
else in the package. If you see it in a tutorial, that tutorial was
written by something that had never run it.

**The working pattern is a `ParDo` with a tagged side output.** Three
ingredients:

**1. `beam.pvalue.TaggedOutput(tag, value)`** — mark an element as
belonging to a side output instead of the main one.

```python
from apache_beam.pvalue import TaggedOutput

yield TaggedOutput("dlq", element)
```

**2. `.with_outputs(...)`** — declare the side output at the call
site. This turns the `ParDo`'s result into a `DoOutputsTuple`, which
is subscriptable by tag.

```python
routed = lines | "Route" >> beam.ParDo(RouteFn()).with_outputs(
    "dlq", main="main"
)
```

**3. Read the outputs by tag.**

```python
routed["main"] | "WriteGood" >> ...
routed["dlq"] | "WriteDlq" >> ...
```

The `main=` argument names the main output. Without it, the main
output is tagged `None` and you would write `routed[None]`. Both forms
work; naming it `"main"` is clearer.

Here is the whole thing, complete:

```python
from apache_beam.pvalue import TaggedOutput

class RouteOrderFn(beam.DoFn):
    """Route malformed rows to the DLQ, valid rows to the main output."""

    def process(self, line):
        row = try_parse_order_line(line)
        if row is None:
            yield TaggedOutput("dlq", line)
            return
        if not is_valid_order(row):
            yield TaggedOutput("dlq", line)
            return
        yield row


routed = lines | "RouteOrders" >> beam.ParDo(RouteOrderFn()).with_outputs(
    "dlq", main="main"
)
routed["main"] | "WriteGood" >> beam.io.WriteToText(GOOD_PATH)
routed["dlq"] | "WriteDlq" >> beam.io.WriteToText(DLQ_PATH)
```

Three rules that make this work:

- **The tag string must be identical in both places.** `TaggedOutput("dlq", ...)`
  and `.with_outputs("dlq", ...)` — same string, same spelling, same
  case. A mismatch produces a `KeyError` at runtime when you subscript
  the tuple.
- **A `DoFn` that yields a `TaggedOutput` must not also yield a plain
  value for the same element.** They go to different outputs; mixing
  them for one element is a logic error.
- **A side output is not a side *input*.** `TaggedOutput` sends data
  out of a `DoFn`; `beam.pvalue.AsDict` brings data in. They are
  unrelated mechanisms that unfortunately share the word "side".

### Why the project needs a DLQ at all

The course's `ParseOrderFn` currently does this:

```python
def process(self, line: str, timestamp=beam.DoFn.TimestampParam) -> Iterable[Any]:
    """Parse one line and emit the resulting order dict."""
    row = try_parse_order_line(line)
    if row is None:
        log.warning("skipping malformed order line: %.120s", line)
        return
    if not is_valid_order(row):
        log.warning("skipping invalid order: %s", row.get("order_id"))
        return
    yield row
```

Read the docstring:

> The malformed rows are logged rather than raised, because one bad
> line in a 10-million-line file should not fail the entire bundle.
> A pipeline that must not lose data should route them to a
> dead-letter topic instead — see the "Error Handling and DLQ" chapter.

The reasoning about not raising is correct. But the *implementation* is
the "skip and log" option, which loses the row. The docstring even
says so. This chapter is about doing better.

The two checks are also doing different jobs, and the distinction
matters more than it first appears.

### Two kinds of "bad row"

`try_parse_order_line` returns `None` when the row **does not have the
expected shape**:

```python
def try_parse_order_line(line: str) -> dict[str, Any] | None:
    text = line.strip()
    if not text:
        return None
    try:
        values = next(csv.reader(io.StringIO(text)))
    except (csv.Error, StopIteration):
        return None
    if len(values) != len(ORDER_FIELDS):
        return None
    row = dict(zip(ORDER_FIELDS, values))

    # Coerce the numeric field so downstream code can trust its type.
    try:
        row["amount"] = float(row["amount"])
    except (TypeError, ValueError):
        return None
    return row
```

It checks the field count and coerces the amount. It does **not** check
whether the region is a real region, or the currency a real currency,
or the timestamp parseable.

`is_valid_order` checks the **business rules** on a well-shaped row:

```python
def is_valid_order(row: dict[str, Any]) -> bool:
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

And its docstring is the clearest statement of the distinction in the
whole project:

> The rules are deliberately explicit rather than schema-driven, because
> a production pipeline needs to distinguish "this row is bad" from
> "this row is a different shape than I expected". The second is a bug;
> the first is data.

That is the taxonomy, and it maps onto different responses:

| Category | Example | What it means | Response |
|---|---|---|---|
| **Shape error** | 3 fields instead of 9 | The producer changed the format. This is a *contract break*. | **Alert loudly.** Every row will be rejected. Stop and fix the producer. |
| **Business-rule violation** | `region=UNKNOWN_REGION` | The row is well-formed but breaks a rule. | **Route to the DLQ.** Count it. Investigate the trend. |
| **Value error** | `amount=not-a-number` | The field is there but unparseable. | **Route to the DLQ.** This may be a producer bug or a genuine data issue. |
| **Transient** | GCS 503 on a read | Nothing is wrong with the data. | **Retry.** Beam does this for you. Do not route to the DLQ. |

The critical insight: **a shape error is not a per-row problem, it is
a per-file problem.** If every row in a file has the wrong field count,
routing them all to the DLQ produces a DLQ with 10 million entries and
a green job. The pipeline "succeeded" and produced nothing. That is
worse than failing.

So the DLQ needs a **guard**: if the DLQ rate crosses a threshold,
fail the job. This is the mechanism that turns "the producer changed
the format" from a silent catastrophe into a failed job with an alert.

### Skip versus route

Let us put the two side by side, because the difference is easy to
underestimate.

**Skip:**

```python
def process(self, line):
    row = try_parse_order_line(line)
    if row is None:
        log.warning("skipping malformed order line: %.120s", line)
        return
    yield row
```

What an operator sees:

- The job succeeds.
- The output has 4,999 rows instead of 5,000.
- There is a `WARNING` line in the worker logs, if anybody is reading
  worker logs, which nobody is.

What the data looks like a month later: 4,999 rows, no explanation, no
way to reconstruct the missing one, no way to know whether it was one
row or ten thousand.

**Route:**

```python
def process(self, line):
    row = try_parse_order_line(line)
    if row is None:
        yield TaggedOutput("dlq", line)
        return
    yield row
```

What an operator sees:

- The job succeeds.
- The output has 4,999 rows.
- The DLQ has one row in it, with the original text.
- A count: `dlq_count = 1`.
- A metric, a log line, and — if you set the threshold — possibly an
  alert.

What the data looks like a month later: 4,999 rows, one row in the
DLQ, and an answer to the question "what happened to that row?".

The output data is *identical*. The difference is entirely in the
**auditability** of the operation. That is the whole argument for the
DLQ.

### The DLQ row should carry the reason

A DLQ containing only the raw line tells you *that* a row was rejected,
not *why*. You then have to re-run the validation logic offline to
find out, which is work, and which nobody will do.

Better: write a structured DLQ record with the raw line *and* the
reason.

```python
def process(self, line):
    row = try_parse_order_line(line)
    if row is None:
        yield TaggedOutput("dlq", {"raw": line, "reason": "unparseable"})
        return
    if not is_valid_order(row):
        yield TaggedOutput("dlq", {"raw": line, "reason": "business_rule"})
        return
    yield row
```

Now the DLQ is queryable. "How many rows were rejected because the
region was unknown?" is a filter over the DLQ, not a re-run.

Even better, name the specific rule:

```python
def rejection_reason(row: dict[str, Any]) -> str:
    """Return why this row is invalid, or an empty string."""
    if not row.get("order_id"):
        return "missing_order_id"
    if row.get("region") not in VALID_REGIONS:
        return "unknown_region"
    if row.get("currency", "").upper() not in CURRENCY_TO_EUR:
        return "unknown_currency"
    if row.get("status") not in VALID_STATUSES:
        return "unknown_status"
    return ""
```

That function is worth having even if you never build a DLQ. It turns
a boolean into a diagnosis.

### Poison pills

A **poison pill** is an element that causes the same failure every
time it is processed. In a streaming pipeline it is fatal in a
particular way: the element sits in a Pub/Sub subscription, the
pipeline keeps retrying it, and the pipeline never advances past it.
The subscription's backlog grows without bound.

In batch, a poison pill is less dramatic, because the input is
bounded and you can re-run. But it is not harmless:

- The job fails, and fails the same way, every time.
- If the pill is in the middle of a file, you cannot make progress past
  it without editing the input — which breaks reproducibility.
- If the failure is intermittent (a network hiccup that only sometimes
  fails), the job fails *randomly*, which is worse than failing
  consistently.

The DLQ pattern is the batch answer: catch the failure at the element
level, route the element out, and let the job finish. The streaming
answer is the same pattern plus a **dead-letter topic** and a
**redrive** process.

The design rule for a robust DLQ:

> **A DLQ must never be able to re-inject its contents into the main
> pipeline without review.**

A DLQ that is automatically replayed is not a DLQ; it is a loop. If
the row is genuinely invalid, replaying it will fail again, and if the
replay is automatic, you have built an infinite retry with extra
storage.

If you do want automated redriving — for the transient cases — then
the DLQ needs a deadline: a row that has been in the DLQ for seven days
without being fixed is escalated to a human queue, not retried
forever.

### The failure-mode table

Here is the practical version. For each failure mode: what it looks
like, whether Beam retries it, and what you should do.

| Failure mode | Symptom | Beam retries? | Response |
|---|---|---|---|
| **Parse error** (bad CSV, wrong field count, unparseable number) | `ValueError` in the `DoFn` | Yes, then the job fails | Catch it in the `DoFn`; route to the DLQ with a reason |
| **Schema mismatch** (the file gained or lost a column) | Every row fails, or a `KeyError` on a missing field | Yes, then the job fails | **Alert.** This is a contract break, not a row problem. Route *and* fail the job if the DLQ rate is too high |
| **Missing key** (no `order_id`, no `customer_id`) | `KeyError` downstream, or a `None` in the output | Yes, then the job fails | Catch it at the parse boundary; route to the DLQ |
| **Transient GCS / BigQuery error** (503, 429, connection reset) | `httplib` error, `ConnectionError`, `RetryError` | **Yes, indefinitely** — this is the whole point of the retry policy | **Nothing.** Do not catch it. Let Beam retry. Catching it converts a transient error into permanent data loss |
| **Business-rule violation** (`region=UNKNOWN_REGION`) | Nothing — it just produces a wrong answer | No, because it did not fail | Route to the DLQ with a reason; alert on the rate |
| **Downstream sink failure** (BigQuery load job rejected) | The job fails at the write | Yes, the write is retried | Let it retry. If it keeps failing, the data is too big or the schema is wrong — a code problem, not a row problem |

The row that stands out is **the transient error**. It is very tempting
to wrap your whole `process` body in a `try`/`except` and route
everything that goes wrong to the DLQ. Do not do that. A transient
GCS error inside a `DoFn` — say, a `ReadFromText` source that fails
mid-file, or a side-input lookup that times out — is *not* a bad row.
Routing it to the DLQ converts a five-second retry into permanent
data loss.

The rule: **catch only the exceptions that mean "this element is
bad", and let everything else propagate.**

### Monitoring the DLQ

A DLQ nobody watches is a garbage dump. Three things to build:

**1. A count.** The number of rows routed to the DLQ, emitted as a
metric.

```python
dlq_count = routed["dlq"] | "CountDlq" >> beam.combiners.Count.Globally()
```

`Count.Globally()` returns a **scalar**, not a one-element list. If
you pipe it into a `Map` that does `for value in result:`, you will
get `TypeError: 'int' object is not iterable`.

**2. A rate against the total.** The absolute count is not the alert;
the *rate* is. One bad row in ten million is noise. One bad row in a
thousand is a producer problem.

```python
total = lines | "CountTotal" >> beam.combiners.Count.Globally()
dlq = routed["dlq"] | "CountDlq" >> beam.combiners.Count.Globally()
rate = dlq | "ComputeRate" >> beam.ParDo(
    ComputeRateFn(), total=beam.pvalue.AsSingleton(total)
)
```

The `total` has to arrive as a **side input**, because `total` and
`dlq` are computed by two different branches of the graph and neither
can see the other's value. The computation therefore lives in a
`DoFn` — a `beam.Map` does not accept side-input keyword arguments.

The `max(total, 1)` inside that `DoFn` guards the division by zero on
an empty input.

**3. A threshold that fails the job.** When the rate crosses a
threshold, the job should fail — loudly, with the DLQ preserved for
inspection. This is the guard that turns a contract break into an
incident rather than a silent success.

```python
class DlqRateGuard(beam.DoFn):
    """Fail the job when too many rows were rejected."""

    def process(self, stats):
        rate = stats["dlq_rate"]
        if rate > 0.01:
            raise ValueError(
                f"DLQ rate {rate:.4f} exceeds the 1% threshold — "
                f"{stats['dlq_count']} rows rejected. The input contract "
                f"may have changed."
            )
        yield stats
```

Raising here fails the job. The DLQ rows have already been written, so
they are there for inspection.

**4. The DLQ needs a partition key too.** If the DLQ lives in GCS, it
should be partitioned by the same data date as the main output. A DLQ
for 2026-01-15 should not be overwritten by the DLQ for 2026-01-16 —
and if you ever want to replay it, you need to know which date it
belongs to.

### Writing the DLQ: format choices

The DLQ is a dataset, and you will query it. Three decisions:

**Format.** JSON Lines is the usual choice: one JSON object per line,
greppable, parseable by anything, and easy to load into BigQuery with
`bq load --source_format=NEWLINE_DELIMITED_JSON`. CSV is fine if the
rows are flat and you want to eyeball them, but a reason code with
commas in it will break it.

**What to include.** At minimum: the raw input, the reason, and the
data date. Ideally also: the source filename, the source offset if you
have it, and the job name.

**Where to put it.** GCS or Pub/Sub, partitioned by data date. Never
in the same table as the main output — a DLQ row in the results table
would be counted by your dashboards.

### Streaming: the same pattern, plus a redrive

The batch DLQ writes to a file. The streaming DLQ writes to a Pub/Sub
**dead-letter topic**, and the redrive is a separate job.

```python
routed = (
    incoming
    | "Route" >> beam.ParDo(RouteFn()).with_outputs("dlq", main="main")
)
routed["main"] | "WriteResults" >> beam.io.WriteToBigQuery(RESULTS_TABLE)
routed["dlq"] | "WriteDlq" >> beam.io.WriteToPubSub(DLQ_TOPIC)
```

The redrive job reads the DLQ topic, tries to process each message,
and writes the successes back to the main input. It needs a deadline:
after N attempts, the message goes to a "permanently failed" topic
that a human looks at.

This is the same design as the batch DLQ, with the addition of
**attempt counting**, which the batch version gets for free from the
partition key.

---

## 🛠️ Hands-On

### Setup

```bash
cd data-engineering/data-Course/google/Dataflow
source .venv/bin/activate
python resources/sample_data.py --output-dir ./sample_data
```

The course ships a file of deliberately bad rows:

```bash
cat sample_data/malformed_orders.csv
```

Expected:

```text
not-an-order,missing-fields,garbage
o99999999,c000001,not-a-timestamp,EMEA,web,EUR,complete,not-a-number,p0001
o99999998,c000002,2026-01-01T00:00:00+00:00,UNKNOWN_REGION,web,EUR,complete,100.00,p0002
o99999997,c000003,2026-01-01T00:00:00+00:00,EMEA,web,XYZ,complete,100.00,p0003
,,,,
```

Five rows, each failing for a different reason:

| Row | Fails because |
|---|---|
| `not-an-order,missing-fields,garbage` | **Shape error** — three fields instead of nine |
| `o99999999,...` | **Value error** — `not-a-timestamp` and `not-a-number` |
| `o99999998,...` | **Business rule** — `UNKNOWN_REGION` is not in `VALID_REGIONS` |
| `o99999997,...` | **Business rule** — `XYZ` is not in `CURRENCY_TO_EUR` |
| `,,,,` | **Shape error** — nine fields, but every one is empty |

### Step 1 — see the current behaviour: skip and log

First, let us see what the project does today. Run the pipeline over the
malformed file and watch the log.

Create `hands_on_skip.py`:

```python
"""Show what the project's current skip-and-log behaviour produces."""
import sys

sys.path.insert(0, "project")

import apache_beam as beam

from transforms import ParseOrderFn

INPUT = "./sample_data/malformed_orders.csv"


def main():
    """Read the malformed file and count what survives.

    Returns:
        Nothing.
    """
    with beam.Pipeline() as pipeline:
        orders = (
            pipeline
            | "ReadOrders" >> beam.io.ReadFromText(INPUT)
            | "ParseOrders" >> beam.ParDo(ParseOrderFn())
        )
        count = orders | "CountOrders" >> beam.combiners.Count.Globally()

        # `count` is a PCollection, so printing it prints the
        # PCollection repr. To see the value, map it to a string and
        # print *that*.
        count | "PrintCount" >> beam.Map(
            lambda c: print("rows that survived:", c)
        )


if __name__ == "__main__":
    main()
```

Run it:

```bash
python hands_on_skip.py
```

Expected:

```text
WARNING:transforms:skipping malformed order line: not-an-order,missing-fields,garbage
WARNING:transforms:skipping malformed order line: o99999999,c000001,not-a-timestamp,EMEA,web,EUR,complete,not-a-number,p0001
WARNING:transforms:skipping invalid order: o99999998
WARNING:transforms:skipping invalid order: o99999997
WARNING:transforms:skipping malformed order line: ,,,,
rows that survived: 0
```

Two things to notice in that log.

**`o99999999` is reported as "malformed", not "invalid".** Its
`amount` is the string `not-a-number`, so `try_parse_order_line`
cannot coerce it and returns `None` — the row never reaches
`is_valid_order`. The two checks fire at different points, and a row
can fail either one.

**The count is 0**, printed from *inside* the pipeline. Printing the
`PCollection` object directly gives you
`PCollection[CountOrders/CombineGlobally(CountCombineFn)/InjectDefault.None]`,
which is the pipeline graph, not the number. The `beam.Map` wrapper
is what turns it into the value.

Zero rows survive. All five bad rows are rejected. But look at what
you have: five lines in a log, and no record anywhere that those five
lines existed as data. If a producer asks "what happened to my
`o99999998`?", the answer is "a log line, three weeks ago, in a log
that has probably rotated".

Also note that the *reasons* are collapsed into two messages:
"skipping malformed order line" and "skipping invalid order". You
cannot tell from the log that `o99999998` failed because of its
*region* and `o99999997` because of its *currency*.

### Step 2 — build the DLQ with the tagged-output pattern

Now the real thing. Create `hands_on_dlq.py`:

```python
"""Build a DLQ with the tagged-output pattern."""
import os
import shutil
import sys

sys.path.insert(0, "project")

import apache_beam as beam
from apache_beam.pvalue import TaggedOutput

from transforms import is_valid_order, try_parse_order_line

INPUT = "./sample_data/orders.csv"
MALFORMED = "./sample_data/malformed_orders.csv"
DLQ = "./out/hands_on/dlq"
GOOD = "./out/hands_on/good"


def rejection_reason(row):
    """Return why this row is invalid, or an empty string.

    Args:
        row: A parsed order dict.

    Returns:
        A short reason code, or "" when the row is valid.
    """
    if not row.get("order_id"):
        return "missing_order_id"
    if not row.get("customer_id"):
        return "missing_customer_id"
    if row.get("region") not in ("AMER", "EMEA", "APAC", "LATAM"):
        return "unknown_region"
    if row.get("currency", "").upper() not in ("EUR", "USD", "GBP", "JPY"):
        return "unknown_currency"
    if row.get("status") not in ("active", "complete", "cancelled", "refunded"):
        return "unknown_status"
    return ""


class RouteOrderFn(beam.DoFn):
    """Route bad rows to the DLQ, good rows to the main output."""

    def process(self, line):
        """Parse, validate and route one line.

        Args:
            line: One raw CSV line.

        Yields:
            A dict for a good row, or a TaggedOutput for a bad one.
        """
        row = try_parse_order_line(line)
        if row is None:
            yield TaggedOutput("dlq", {"raw": line, "reason": "unparseable"})
            return

        reason = rejection_reason(row)
        if reason:
            yield TaggedOutput("dlq", {"raw": line, "reason": reason})
            return

        yield row


def main():
    """Run the pipeline and write the good rows and the DLQ.

    Returns:
        Nothing.
    """
    shutil.rmtree(DLQ, ignore_errors=True)
    shutil.rmtree(GOOD, ignore_errors=True)

    with beam.Pipeline() as pipeline:
        orders = pipeline | "ReadOrders" >> beam.io.ReadFromText(INPUT)
        malformed = pipeline | "ReadMalformed" >> beam.io.ReadFromText(MALFORMED)

        # `Flatten` takes a *tuple* of PCollections, not a chained `|`.
        lines = (orders, malformed) | "Flatten" >> beam.Flatten()

        routed = lines | "RouteOrders" >> beam.ParDo(RouteOrderFn()).with_outputs(
            "dlq", main="main"
        )

        routed["main"] | "WriteGood" >> beam.io.WriteToText(
            GOOD,
            header="order_id,region,status,amount",
            num_shards=1,
            shard_name_template="",
        )

        routed["dlq"] | "WriteDlq" >> beam.io.WriteToText(
            DLQ,
            header="reason,raw",
            num_shards=1,
            shard_name_template="",
        )


if __name__ == "__main__":
    main()
```

Run it:

```bash
python hands_on_dlq.py
```

Then look at the DLQ:

```bash
cat out/hands_on/dlq
```

Expected:

```text
reason,raw
{'raw': 'not-an-order,missing-fields,garbage', 'reason': 'unparseable'}
{'raw': 'o99999999,c000001,not-a-timestamp,EMEA,web,EUR,complete,not-a-number,p0001', 'reason': 'unparseable'}
{'raw': 'order_id,customer_id,order_ts,region,channel,currency,status,amount,product_id', 'reason': 'unparseable'}
{'raw': ',,,,', 'reason': 'unparseable'}
{'raw': 'o99999998,c000002,2026-01-01T00:00:00+00:00,UNKNOWN_REGION,web,EUR,complete,100.00,p0002', 'reason': 'unknown_region'}
{'raw': 'o99999997,c000003,2026-01-01T00:00:00+00:00,EMEA,web,XYZ,complete,100.00,p0003', 'reason': 'unknown_currency'}
```

Every bad row is there, with a reason. Six DLQ rows: the five
malformed rows plus the header row from `orders.csv`.

Note the format. `WriteToText` uses `ToBytesCoder`, which calls
`str()` on whatever it is given — so a dict becomes its Python repr,
not the `reason,raw` CSV the header advertises. That is a formatting
artefact of this exercise, not a routing bug. In production you would
format the DLQ row explicitly before writing it:

```python
routed["dlq"] | "FormatDlq" >> beam.Map(
    lambda record: f"{record['reason']},{record['raw']}"
)
```

or write it as JSON Lines, which is the format that survives
commas in the raw line. A raw line can contain a comma — most of
them do — so a naive CSV join of a reason and a raw line is itself a
CSV-correctness bug. JSON Lines does not have that problem.

And the good file:

```bash
head -3 out/hands_on/good
wc -l out/hands_on/good
```

Expected:

```text
order_id,region,status,amount
{'order_id': 'o00000001', 'customer_id': 'c004469', 'order_ts': '2026-01-15T03:09:55+00:00', 'region': 'EMEA', 'channel': 'web', 'currency': 'JPY', 'status': 'active', 'amount': 211.61, 'product_id': 'p0129'}
{'order_id': 'o00000000', 'customer_id': 'c000914', 'order_ts': '2026-01-15T00:54:38+00:00', 'region': 'AMER', 'channel': 'web', 'currency': 'GBP', 'status': 'complete', 'amount': 700.97, 'product_id': 'p0173'}
```

The good output is 5,001 lines: a header plus 5,000 rows. Every
valid order from `orders.csv` survived, and every bad row from
`malformed_orders.csv` was routed out.

Two artefacts of the exercise that are worth calling out:

- **The header row of `orders.csv` is in the DLQ.** It has nine fields,
  so `try_parse_order_line` accepts it, but `amount` is the string
  `"amount"`, which does not parse as a float — so it returns `None`
  and the row is routed as `unparseable`. In a real pipeline you would
  either skip the header explicitly (`skip_header_lines=1` on
  `ReadFromText`) or accept that the header is one rejected row. Both
  are fine; what matters is that the header is *visible* rather than
  silently treated as data.
- **The good rows are written as Python dict reprs**, because
  `WriteToText` uses `ToBytesCoder` and `str()`s whatever it gets. In
  a real pipeline you would format the rows explicitly. The DLQ has
  the same issue — the `reason,raw` header does not match the
  dict-repr lines. Again: the *routing* is what this exercise is
  about; the formatting is a separate concern.

### Step 3 — prove that `beam.FilterInto` does not exist

It is worth confirming the hallucination directly, because you will
meet it in blog posts and in AI-generated code.

```bash
python -c "import apache_beam as beam; print(hasattr(beam, 'FilterInto'))"
python -c "import apache_beam.transforms as t; print(hasattr(t, 'FilterInto'))"
```

Expected:

```text
False
False
```

And what happens if you use it anyway:

```text
import apache_beam as beam

with beam.Pipeline() as pipeline:
    (
        pipeline
        | "ReadOrders" >> beam.io.ReadFromText(INPUT)
        | "Split" >> beam.FilterInto("valid", "dlq", lambda line: True)
    )
```

```text
AttributeError: module 'apache_beam' has no attribute 'FilterInto'
```

The working alternative is always the tagged-output pattern. If you
want something that reads like `FilterInto`, write it yourself:

```python
def filter_into(fn, *tags, main="main"):
    """Return a ParDo that routes elements to side outputs by predicate.

    Args:
        fn: A predicate taking one element and returning a tag or None.
        *tags: The side-output tags to declare.
        main: The tag for the main output.

    Returns:
        A ParDo with the declared outputs.
    """

    class _FilterIntoFn(beam.DoFn):
        """Route each element to the tag its predicate selects."""

        def process(self, element):
            tag = fn(element)
            if tag is None:
                yield TaggedOutput(main, element)
            else:
                yield TaggedOutput(tag, element)

    return beam.ParDo(_FilterIntoFn()).with_outputs(*tags, main=main)
```

But be honest about what it is: `FilterInto` from the old Beam SDK
was never a Python API. The Java SDK has `withOutputTags`. The Python
idiom has always been `ParDo` plus `TaggedOutput`.

### Step 4 — count the DLQ and compute the rate

A DLQ without a count is a garbage dump. Let us measure.

Create `hands_on_dlq_metrics.py`:

```python
"""Count the DLQ and compute the rejection rate."""
import sys

sys.path.insert(0, "project")

import apache_beam as beam
from apache_beam.pvalue import TaggedOutput

from transforms import is_valid_order, try_parse_order_line

INPUT = "./sample_data/orders.csv"
MALFORMED = "./sample_data/malformed_orders.csv"


class RouteOrderFn(beam.DoFn):
    """Route bad rows to the DLQ, good rows to the main output."""

    def process(self, line):
        """Parse, validate and route one line.

        Args:
            line: One raw CSV line.

        Yields:
            A dict for a good row, or a TaggedOutput for a bad one.
        """
        row = try_parse_order_line(line)
        if row is None or not is_valid_order(row):
            yield TaggedOutput("dlq", line)
            return
        yield row


class ComputeRateFn(beam.DoFn):
    """Compute the rejection rate against the total row count.

    The total arrives as a side input, because the two counts are
    computed by different branches of the graph and neither can see
    the other's value.
    """

    def process(self, dlq_count, total=beam.DoFn.ElementParam):
        """Compute the rejection rate.

        Args:
            dlq_count: The number of rejected rows.
            total: The total number of input rows, as a side input.

        Yields:
            A dict with the counts and the rate.
        """
        yield {
            "dlq_count": dlq_count,
            "total": total,
            "dlq_rate": dlq_count / max(total, 1),
        }


def main():
    """Print the DLQ count and the rejection rate.

    Returns:
        Nothing.
    """
    with beam.Pipeline() as pipeline:
        orders = pipeline | "ReadOrders" >> beam.io.ReadFromText(INPUT)
        malformed = pipeline | "ReadMalformed" >> beam.io.ReadFromText(MALFORMED)
        lines = (orders, malformed) | "Flatten" >> beam.Flatten()

        routed = lines | "RouteOrders" >> beam.ParDo(RouteOrderFn()).with_outputs(
            "dlq", main="main"
        )

        total = lines | "CountTotal" >> beam.combiners.Count.Globally()
        dlq_count = routed["dlq"] | "CountDlq" >> beam.combiners.Count.Globally()

        stats = dlq_count | "ComputeRate" >> beam.ParDo(
            ComputeRateFn(), total=beam.pvalue.AsSingleton(total)
        )
        stats | "PrintStats" >> beam.Map(print)


if __name__ == "__main__":
    main()
```

Run it:

```bash
python hands_on_dlq_metrics.py
```

Expected:

```text
{'dlq_count': 6, 'total': 5006, 'dlq_rate': 0.0011985617259288853}
```

Six DLQ rows: the five malformed rows plus the header row from
`orders.csv`. The total is 5,006 — 5,000 orders plus the header plus
the five malformed rows. The rate is about 0.12%.

Three things to notice, and the second one is a trap:

- **`Count.Globally()` returns a scalar.** The `dlq_count` PCollection
  contains a single `int`. That is why `dlq_count / max(total, 1)`
  works, and why `for value in result:` would fail with
  `TypeError: 'int' object is not iterable`.
- **`total` is a `PCollection`, not an `int`.** The first version of
  this script computed the rate inside a `beam.Map` closure:

  ```text
  stats = dlq_count | "ComputeRate" >> beam.Map(
      lambda d: {"dlq_count": d, "total": total, "dlq_rate": d / max(total, 1)}
  )
  ```

  and failed with:

  ```text
  TypeError: '>' not supported between instances of 'int' and '_InvalidUnpickledPCollection'
  ```

  The `lambda` closes over the *PCollection object*, not its value.
  Comparing it with `1` fails. You cannot read a PCollection's value
  from a closure — it does not exist yet at graph-construction time.
- **The fix is a side input.** `beam.pvalue.AsSingleton(total)` turns
  the PCollection into a side input, and `beam.ParDo(ComputeRateFn(),
  total=...)` passes it to the `DoFn` as the `total` argument.

  `AsSingleton` is a side-input **wrapper**, not a transform — you
  pass it as an argument, you do not apply it with `>>`. See
  [chapter 6.1](30-batch-design-patterns.md).

  Note also that the side input has to be attached to a **`DoFn`**,
  not to a `beam.Map`. A `beam.Map` does not accept side-input keyword
  arguments, and trying gives you:

  ```text
  TypeError: Map.<locals>.<lambda>() got an unexpected keyword argument 'total'
  ```

  So the computation moves into a `DoFn` with a `total` parameter.

### Step 5 — the guard that turns a contract break into an incident

Now the important part. Route the bad rows to the DLQ *and* fail the
job when too many rows are rejected.

Create `hands_on_dlq_guard.py`:

```python
"""Fail the job when the DLQ rate crosses a threshold."""
import sys

sys.path.insert(0, "project")

import apache_beam as beam
from apache_beam.pvalue import TaggedOutput

from transforms import is_valid_order, try_parse_order_line

INPUT = "./sample_data/orders.csv"
MALFORMED = "./sample_data/malformed_orders.csv"

THRESHOLD = 0.01


class RouteOrderFn(beam.DoFn):
    """Route bad rows to the DLQ, good rows to the main output."""

    def process(self, line):
        """Parse, validate and route one line.

        Args:
            line: One raw CSV line.

        Yields:
            A dict for a good row, or a TaggedOutput for a bad one.
        """
        row = try_parse_order_line(line)
        if row is None or not is_valid_order(row):
            yield TaggedOutput("dlq", line)
            return
        yield row


class ComputeRateFn(beam.DoFn):
    """Compute the rejection rate against the total row count."""

    def process(self, dlq_count, total=beam.DoFn.ElementParam):
        """Compute the rejection rate.

        Args:
            dlq_count: The number of rejected rows.
            total: The total number of input rows, as a side input.

        Yields:
            A dict with the counts and the rate.
        """
        yield {
            "dlq_count": dlq_count,
            "total": total,
            "dlq_rate": dlq_count / max(total, 1),
        }


class DlqRateGuard(beam.DoFn):
    """Fail the job when too many rows were rejected."""

    def process(self, stats):
        """Raise if the rejection rate is above the threshold.

        Args:
            stats: A dict with `dlq_count` and `dlq_rate`.

        Yields:
            The stats, when the rate is acceptable.
        """
        rate = stats["dlq_rate"]
        if rate > THRESHOLD:
            raise ValueError(
                f"DLQ rate {rate:.4f} exceeds the {THRESHOLD:.2%} threshold — "
                f"{stats['dlq_count']} rows rejected. The input contract "
                f"may have changed."
            )
        yield stats


def main():
    """Run the pipeline with the guard enabled.

    Returns:
        Nothing.
    """
    with beam.Pipeline() as pipeline:
        orders = pipeline | "ReadOrders" >> beam.io.ReadFromText(INPUT)
        malformed = pipeline | "ReadMalformed" >> beam.io.ReadFromText(MALFORMED)
        lines = (orders, malformed) | "Flatten" >> beam.Flatten()

        routed = lines | "RouteOrders" >> beam.ParDo(RouteOrderFn()).with_outputs(
            "dlq", main="main"
        )

        total = lines | "CountTotal" >> beam.combiners.Count.Globally()
        dlq_count = routed["dlq"] | "CountDlq" >> beam.combiners.Count.Globally()

        stats = dlq_count | "ComputeRate" >> beam.ParDo(
            ComputeRateFn(), total=beam.pvalue.AsSingleton(total)
        )

        stats | "Guard" >> beam.ParDo(DlqRateGuard()) | "PrintStats" >> beam.Map(print)


if __name__ == "__main__":
    main()
```

Run it:

```bash
python hands_on_dlq_guard.py
```

Expected:

```text
{'dlq_count': 6, 'total': 5006, 'dlq_rate': 0.0011985617259288853}
```

The guard did not fire, because 0.12% is below the 1% threshold. Now
lower the threshold so the guard trips:

```bash
python - <<'EOF' > /tmp/guard_fail.py
import pathlib
source = pathlib.Path("hands_on_dlq_guard.py").read_text()
print(source.replace("THRESHOLD = 0.01", "THRESHOLD = 0.0001"))
EOF
python /tmp/guard_fail.py
```

Expected — the job fails:

```text
ValueError: DLQ rate 0.0012 exceeds the 0.01% threshold — 6 rows rejected. The input contract may have changed.
```

Note the message: `0.0012` is the rate, and `0.01%` is the
threshold. The rate is 0.12%, the threshold is 0.01%, so the rate is
twelve times the threshold and the guard fires. The two numbers are
easy to confuse, which is why the message prints both.

And the important part: **the DLQ rows were still written.** The
guard runs in a separate branch of the graph, and the DLQ write
completes independently. When the job fails, the operator has the
bad rows to look at.

That is the design you want: the guard turns a silent success into a
loud failure, and the failure comes with the evidence attached.

### Step 6 — add the DLQ to the project

Now let us improve the project itself. The change is to
`ParseOrderFn`: instead of logging and skipping, route to a DLQ.

```python
class ParseOrderFn(beam.DoFn):
    """Parse CSV lines into order dicts, routing bad rows to a DLQ.

    The malformed rows are routed to a side output rather than raised,
    because one bad line in a 10-million-line file should not fail the
    entire bundle. The rows are preserved, not dropped, so that they
    can be counted, alerted on and replayed after the upstream
    contract is fixed.
    """

    def process(self, line: str, timestamp=beam.DoFn.TimestampParam) -> Iterable[Any]:
        """Parse one line and emit the resulting order dict.

        Args:
            line: The raw CSV line.
            timestamp: The timestamp of the element.

        Yields:
            The order dict, or a TaggedOutput for a bad row.
        """
        row = try_parse_order_line(line)
        if row is None:
            yield TaggedOutput("dlq", {"raw": line, "reason": "unparseable"})
            return
        if not is_valid_order(row):
            yield TaggedOutput("dlq", {"raw": line, "reason": "business_rule"})
            return
        yield row
```

And at the call site:

```python
routed = (
    lines
    | "ParseOrders" >> beam.ParDo(ParseOrderFn()).with_outputs("dlq", main="main")
)
routed["main"] | "KeepCompletedOrders" >> beam.Filter(
    lambda order: order["status"] in statuses
)
routed["dlq"] | "WriteDlq" >> beam.io.WriteToText(
    dlq_path,
    header="reason,raw",
    num_shards=1,
    shard_name_template="",
)
```

The `dlq_path` needs to be a new parameter on `build_pipeline`, and it
needs to be **partitioned by the data date** — a DLQ for 2026-01-15
must not be overwritten by the DLQ for 2026-01-16.

A test for the routing:

```python
def test_malformed_rows_go_to_the_dlq(tmp_path):
    """Bad rows are routed to the DLQ, not silently dropped."""
    from batch_pipeline import build_pipeline

    input_file = tmp_path / "orders.csv"
    input_file.write_text(
        "\n".join(ORDER_LINES) + "\nnot-an-order,missing-fields,garbage\n",
        encoding="utf-8",
    )
    output_prefix = tmp_path / "summary"
    dlq_prefix = tmp_path / "dlq"

    with TestPipeline(options=beam_test_options()) as pipeline:
        build_pipeline(
            pipeline,
            input_path=str(input_file),
            output_path=str(output_prefix),
            dlq_path=str(dlq_prefix),
        )

    dlq_files = sorted(tmp_path.glob("dlq*"))
    assert dlq_files, "the pipeline produced no DLQ file"
    contents = "\n".join(f.read_text(encoding="utf-8") for f in dlq_files)
    assert "not-an-order" in contents
```

The assertion is the important part: it says the bad row is *somewhere
we can find it*. Without it, "skip and log" and "route to the DLQ"
are indistinguishable from the outside.

---

## 🛠️ Common Errors and Fixes

### `AttributeError: module 'apache_beam' has no attribute 'FilterInto'`

`beam.FilterInto` does not exist in apache-beam 2.77, in
`apache_beam.transforms`, or anywhere else. It is a common
hallucination.

Use the tagged-output pattern instead: `beam.pvalue.TaggedOutput` in
the `DoFn`, `.with_outputs("dlq", main="main")` at the call site.

See [chapter 2.5](10-filter-and-flatten.md) for the full pattern.

### `KeyError: 'dlq'` when subscripting the outputs tuple

The tag string in `TaggedOutput("dlq", ...)` does not match the tag
string in `.with_outputs("dlq", ...)`. They must be byte-for-byte
identical.

A second cause: you forgot `main=` and then subscripted with
`"main"` when the main output is tagged `None`. Either name it
explicitly (`main="main"`) or subscript with `None`.

### `TypeError: 'int' object is not iterable`

`beam.combiners.Count.Globally()` returns a **scalar**, not a
one-element list. Do not iterate over it.

```text
# WRONG
count | "PrintIt" >> beam.Map(lambda c: [x for x in c])

# RIGHT
count | "PrintIt" >> beam.Map(print)
```

### `TypeError: '>' not supported between instances of 'int' and '_InvalidUnpickledPCollection'`

You closed over a `PCollection` and tried to use it as a value.

```text
# WRONG — `total` is a PCollection, not an int
stats = dlq_count | "ComputeRate" >> beam.Map(
    lambda d: {"dlq_rate": d / max(total, 1)}
)
```

The value of a `PCollection` does not exist at graph-construction
time. To use it, pass it as a **side input**, and do the computation
in a `DoFn` — a `beam.Map` does not accept side-input keyword
arguments.

```text
# RIGHT
stats = dlq_count | "ComputeRate" >> beam.ParDo(
    ComputeRateFn(), total=beam.pvalue.AsSingleton(total)
)
```

### `TypeError: Map.<locals>.<lambda>() got an unexpected keyword argument 'total'`

You passed a side input to a `beam.Map`. `beam.Map` takes only the
element; side inputs need a `DoFn` with a matching parameter.

### `AttributeError: 'property' object has no attribute 'windowfn'`

You tried to use `beam.pvalue.AsSingleton(...)` as a *default argument
value* in a `DoFn.process` signature:

```text
def process(self, x, total=beam.pvalue.AsSingleton(beam.pvalue.PCollection)):
```

`AsSingleton` needs a real `PCollection`, and it is attached at the
`ParDo` call site, not in the signature. Use
`total=beam.DoFn.ElementParam` in the signature and pass
`total=beam.pvalue.AsSingleton(total)` to `beam.ParDo`.

### `ValueError: cannot convert string to float: 'amount'`

The header row. `ReadFromText` reads the first line like any other.
Skip it:

```python
beam.io.ReadFromText(INPUT, skip_header_lines=1)
```

or let it be routed to the DLQ, which is at least visible.

### `NotImplementedError` from a `FileBasedSink` subclass

You implemented `write` instead of `write_encoded_record`. The base
class's `write_record` encodes with `self.coder` and then calls
`write_encoded_record`, which raises `NotImplementedError` by
default.

### `TypeError: unsupported operand type(s) for >>: 'str' and 'MySink'`

A `FileBasedSink` is not a `PTransform`. Wrap it:

```python
pcoll | "Write" >> beam.io.Write(MySink(...))
```

### The DLQ is empty but the job lost rows

Your `DoFn` is still using the old skip-and-log pattern, or the DLQ
branch is not connected to the pipeline. Check that:

1. The `DoFn` yields `TaggedOutput("dlq", ...)`.
2. `.with_outputs("dlq", main="main")` is applied.
3. `routed["dlq"]` is connected to a write transform.

### The job fails with a transient error that was routed to the DLQ

You caught too much. Catch only the exceptions that mean "this element
is bad"; let transient infrastructure errors propagate so Beam can
retry them.

### Every row is in the DLQ

The contract changed — a column was added, removed or renamed. This
is exactly the case the DLQ rate guard exists for. Check the first
line of the input file against the expected header.

---

## 💡 Production Notes

### Put the DLQ somewhere queryable, not somewhere loggable

Worker logs are not a data store. They are ephemeral, they are not
queryable, they are not partitioned, and they are not retained on a
schedule you control.

A DLQ should be a GCS prefix (partitioned by data date) or a Pub/Sub
topic. Both can be loaded into BigQuery, queried, and alerted on.

### Alert on the rate, not the count

One bad row is noise. One thousand bad rows is a producer problem.
One million is a contract break.

Set the threshold from the observed baseline. If your normal rate is
0.001%, alert at 1%. If it is 0%, alert at 0.1% — because a rate that
has never been non-zero is not going to stay that way.

### Write the reason, and keep the raw line

The reason code makes the DLQ queryable. The raw line makes it
replayable. You need both: the reason to triage, the raw line to fix
and re-run.

### Give the DLQ the same partitioning as the main output

`dlq/dt=2026-01-15/` next to `output/dt=2026-01-15/`. That way a
backfill and its DLQ land together, and a replay knows which date it
is replaying.

### Make replay a manual, reviewed operation

A DLQ that is automatically replayed will loop on the rows that are
genuinely invalid. If you want automated redriving, separate the
DLQ into two buckets: **retryable** (transient failures, with a
deadline and an attempt counter) and **terminal** (a contract
violation, for a human).

### Keep the rejection reason close to the validation logic

Duplicated validation rules drift. `is_valid_order` returns a bool;
`rejection_reason` returns a code. Two copies of the same rules will
disagree, and then the DLQ will contain rows that the main pipeline
accepted. Write the reason function once and derive the boolean from
it:

```python
def is_valid_order(row):
    """Check that an order row satisfies every business rule."""
    return not rejection_reason(row)
```

### Count DLQ rows per reason, not just in total

"A thousand rows rejected" is a statistic. "A thousand rows rejected
for `unknown_currency`" is a diagnosis. Emit the reason as a metric
label and you get the breakdown for free.

### Do not put the DLQ in the results table

A DLQ row in the results table is a DLQ row your dashboards count.
Separate tables, separate paths, separate queries.

### In streaming, the DLQ needs an attempt counter

Batch gets attempt counting for free from the partition key. In
streaming, put a `retry_count` in the message attributes and
increment it on each redrive, and escalate after N attempts.

---

## 🔑 Key Takeaways

1. **`beam.FilterInto` does not exist.** Not in apache-beam 2.77, not
   in `apache_beam.transforms`, nowhere. The working pattern is
   `beam.pvalue.TaggedOutput` plus `.with_outputs(...)`.
2. **A `DoFn` that raises fails the bundle, which is retried, and
   then fails the job.** The elements in the failed bundle are not
   partially processed — they are reprocessed on the retry.
3. **A poison pill kills every bundle that contains it.** Catching the
   exception at the element level is the only way past it.
4. **Catch only "this element is bad" exceptions.** Catching transient
   GCS or BigQuery errors converts a five-second retry into permanent
   data loss.
5. **Skip and route produce identical output data.** The difference is
   entirely auditability — and that is the whole argument for the
   DLQ.
6. **Shape errors and business-rule violations are different
   problems.** A shape error means the producer changed the contract
   and *every* row will be rejected. Route them, and fail the job on
   the rate.
7. **The DLQ needs a reason code.** "This row was rejected" is a
   statistic; "this row was rejected because its currency was XYZ" is
   a diagnosis.
8. **`beam.combiners.Count.Globally()` returns a scalar**, not a
   list. Iterating over it raises `TypeError: 'int' object is not
   iterable`.
9. **`beam.pvalue.AsDict` / `AsSingleton` are side-input wrappers, not
   transforms.** Pass them as arguments; do not apply them with `>>`.
10. **The DLQ rate guard is what makes the DLQ safe.** Without it, a
    contract break produces a green job and an empty result.
11. **The guard and the DLQ write must be independent branches**, so
    that the bad rows are preserved even when the job fails.
12. **The DLQ must never be replayed automatically** without review,
    or it becomes an infinite retry loop.
13. **Partition the DLQ by the data date**, exactly like the main
    output, so a backfill and its DLQ land together.
14. **The course project's `ParseOrderFn` currently skips and logs.**
    The docstring even says a DLQ would be better. This chapter is
    the implementation of that better version.

---

## 📚 Practice Exercises

1. **Implement the DLQ in `project/transforms.py`.** Change
   `ParseOrderFn` to yield `TaggedOutput("dlq", ...)` for bad rows,
   with a reason code. Update the docstring to match. Keep the
   `try_parse_order_line` / `is_valid_order` split — do not merge
   them.

2. **Add the DLQ write to `project/batch_pipeline.py`.** Add a
   `dlq_path` parameter to `build_pipeline`, connect
   `routed["dlq"]` to a write, and partition the path by the data
   date. Update `parse_args` and the README.

3. **Write the reason function.** Add `rejection_reason(row)` to
   `project/transforms.py` returning a specific code for each rule
   (`missing_order_id`, `unknown_region`, `unknown_currency`, …), and
   rewrite `is_valid_order` in terms of it. Prove with a test that
   the two agree for every rule.

4. **Add the DLQ rate guard.** Emit the DLQ count and the total as
   metrics, and fail the job when the rate crosses a configurable
   threshold. Add a `--dlq_threshold` argument. Write a test that
   feeds a file where every row is malformed and asserts the job
   fails.

5. **Build a DLQ query.** Load the DLQ GCS prefix into BigQuery and
   write a query that counts rejections by reason and by data date.
   Produce the "top three rejection reasons this week" query.

6. **Write a redrive script.** Take the DLQ, re-run the validation
   logic offline, and split the rows into "now valid" (which you would
   replay) and "still invalid" (which you would escalate). Prove it
   is safe to run twice.

7. **Prove the shape-error case.** Write a test that changes the
   input file's header (adds a tenth column) and asserts that the
   guard fires, because every row is now a shape error. This is the
   scenario that separates "route to the DLQ" from "route to the DLQ
   *and* fail loudly".

---

## 📖 Further Reading

- Apache Beam programming guide — "Multiple Outputs" (side outputs and
  `TaggedOutput`) — https://beam.apache.org/documentation/programming-guide/#multiple-outputs
- Apache Beam programming guide — "Error Handling in Beam" — https://beam.apache.org/documentation/programming-guide/#error-handling
- Apache Beam — `ParDo.with_outputs` API reference — https://beam.apache.org/releases/pydoc/current/_modules/apache_beam/transforms/core.html
- Google Cloud Dataflow — handling errors with a dead-letter topic — https://cloud.google.com/dataflow/docs/guides/error-handling
- Google Cloud Pub/Sub — dead-letter topics — https://cloud.google.com/pubsub/docs/handling-failures
- BigQuery — loading JSON Lines from GCS — https://cloud.google.com/bigquery/docs/loading-data-cloud-storage-json
- Google Cloud Dataflow — data quality and error handling patterns — https://cloud.google.com/dataflow/docs/guides/data-quality
- [Chapter 2.5 — Filter & Flatten](10-filter-and-flatten.md)
- [Chapter 6.1 — Batch Design Patterns](30-batch-design-patterns.md)
- [Chapter 6.3 — Idempotency & Exactly-Once](32-idempotency-and-exactly-once.md)
- [Chapter 6.5 — Backfills & Re-runs](34-backfills-and-re-runs.md)
