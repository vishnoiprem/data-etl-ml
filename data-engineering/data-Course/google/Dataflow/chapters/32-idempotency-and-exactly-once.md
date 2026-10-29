# 6.3 — Idempotency & Exactly-Once

> **Section 6 · Batch Pipeline Engineering · Lecture 6.3 · 6:30**

## 🎯 What you will learn

- The four delivery/execution guarantees — at-most-once, at-least-once, exactly-once, effectively-once — and which of them Beam actually provides
- Why "exactly-once" in Beam is a statement about *processing*, not about the *sink*
- The idempotent-sink pattern: `WRITE_TRUNCATE`, deterministic partition keys, and why the partition key is the whole trick
- What actually happens when you re-run a batch job into an appending sink — the double-count, measured
- The `dedup_key` pattern from the course project, and why the key must come from the payload's own identity
- Insert-only versus upsert, and where BigQuery's `insert_id` and CDC `primary_key` fit
- Why "designing for replay" beats "designing for exactly-once": deterministic transforms, no wall-clock in logic, no unseeded randomness
- A real finding in the course's own `project/templates/batch_template.py`: `WRITE_APPEND` where `WRITE_TRUNCATE` belongs

---

## 🧠 Concept

### The four guarantees, and the words that are always wrong

Distributed systems literature has settled on four delivery/execution
guarantees. They are easy to state and easy to confuse with one another,
because each describes a *different pair* of things: what happens on
retry, and what the observer sees.

| Guarantee | On retry / crash | What the observer sees |
|---|---|---|
| **At-most-once** | The retry is suppressed. | Each message processed **zero or one** time. Records can be lost. |
| **At-least-once** | The retry happens. | Each message processed **one or more** times. Records can be duplicated. |
| **Effectively-once** | The retry happens, and the effect is deduplicated. | Each message has **one logical effect**, even though it was physically applied more than once. |
| **Exactly-once** | The retry happens, and the whole system is modelled so the effect is atomic with the processing. | Each message has one effect, guaranteed by the system as a whole. Requires a transactional resource. |

Two of the phrases in that table need sharpening before you can apply
them to Beam.

**"Exactly-once" is a property of a *system*, not of a *transform*.**
It cannot be delivered by a library alone. It requires (a) a reliable
transport that retries, (b) a deterministic, replayable processing step,
and (c) a sink that either commits atomically with the offset or is
idempotent by construction. A stream processor can give you (b). It
cannot give you (a) or (c) on its own — those belong to the broker and
to the database.

**"Effectively-once" is what you actually build.** It is
at-least-once delivery plus an idempotent sink. This is the pattern
that 95% of production pipelines use, including every pipeline in this
course. It is achievable without any distributed transactions, and it
does not require the sink to support them.

### What Beam guarantees, specifically

Beam's own documentation is careful about this, and it is worth
quoting the shape of the argument rather than the slogan.

Beam's guarantee is:

> Beam's execution model provides **at-least-once** delivery of input
> elements, and the runner ensures that a bundle's side effects are
> either all applied or none applied, for the transforms it manages.
> Exactly-once end-to-end semantics additionally require the sink to
> support them.

Concretely, in a streaming pipeline:

- The runner **checkpoints** the pipeline state, including the
  per-key state of `GroupByKey` and the input offsets.
- When a worker dies, it restarts and **replays from the last
  checkpoint**. The elements after the checkpoint are re-delivered.
- Beam does **not** re-deliver elements before the checkpoint, because
  the checkpoint captured the state that consumed them.
- Therefore each *input element* is processed at least once, and the
  *in-memory state* is consistent — no lost increments, no double
  increments **within the runner's own state**.

The gap is at the boundary: **the sink.** When the runner writes to
BigQuery, to a file, or to Pub/Sub, that write is *outside* the
checkpointed state. If the worker writes to the sink and then dies
before the checkpoint is committed, the sink has the record but the
checkpoint says it does not — and on restart the element is replayed
and written again.

That is the whole story. Beam gives you exactly-once *processing*. It
cannot give you exactly-once *sinks*, because it does not own the
transaction.

### Batch is a special case of the same problem

In batch, the input is bounded and the job runs to completion. But the
failure modes are the same, and the re-run is the *normal* case, not
the exceptional one:

- A job fails at 90% because of a transient GCS 503. You re-run it.
  If the sink appended, the first 90% is now written twice.
- A job succeeds but you discover the filter was wrong. You fix the
  code and re-run. If the sink appended, the wrong rows are now
  permanent.
- A backfill for 2026-01-15 runs while the 2026-01-16 live job also
  runs. If both write to the same table with `WRITE_APPEND`, the
  totals are wrong in a way nobody notices for a month.

**Batch pipelines are re-run far more often than streaming pipelines
are restarted.** A scheduled batch job that fails is retried. A
scheduled batch job that *succeeds but is wrong* is re-run after the
fix. So idempotency is not a nice-to-have for batch; it is the
difference between a re-run and an incident.

### The three properties of an idempotent sink

A sink is idempotent if running the same input twice produces the same
final state as running it once. There are exactly three ways to achieve
that, and you should pick one deliberately.

#### 1. Replace, don't append

The sink discards whatever was there and writes the new content.

- BigQuery: `WRITE_TRUNCATE`
- A file sink: `WriteToText` and the other `FileBasedSink` transforms
  already do this (see below)
- A GCS object: overwrite the same key

This is the default choice for a **full-refresh** batch job, and it is
what the course project should be doing.

#### 2. Deterministic partition keys, and overwrite within the partition

The sink appends, but each run writes to a *specific, computable
location* that a previous run for the same data would also have
written to. The location is overwritten, not appended to.

- BigQuery partitioned table: `order_date=2026-01-15` — a run for
  2026-01-15 overwrites that partition and touches nothing else.
- GCS: `gs://bucket/revenue/dt=2026-01-15/part-00000.csv` — the same
  key is overwritten.
- Delta/Iceberg/Hudi: a `MERGE` on a primary key.

This is the right choice when the output is naturally partitioned by
date and you want history preserved for other dates.

The key insight is that **the partition key must be derivable from the
data**, not from the job's run time. If the key is
`dt=<the date the job started>`, then a re-run of the same data writes
to a *different* partition and you get the duplicate. If the key is
`dt=<the date the data is about>`, a re-run overwrites in place.

#### 3. Natural idempotency at the row level

The sink upserts on a primary key. Two runs of the same input produce
one row per key.

- BigQuery: `MERGE` on `order_id`, or the Storage Write API's
  `UPSERT` mutation with a `primary_key`
- BigQuery streaming inserts: `insert_id`, which BigQuery
  deduplicates on for a **best-effort window**
- A key-value store: a `PUT` on a deterministic key

This is the right choice for incremental or CDC-shaped data.

#### And the anti-pattern: append with no key

`WRITE_APPEND` with no partitioning, no primary key, no insert ids.
Two runs, two copies, no way to tell which is which, no way to undo.

That is exactly what the course's flex template does today. See
[the real finding](#the-real-finding-in-the-course-template) below.

### What Beam's file sinks actually do on a re-run

This is worth verifying rather than assuming, because the answer is
counter-intuitive and the assumption is common.

`beam.io.WriteToText` is built on `FileBasedSink`. Its `pre_finalize`
step does this:

```python
# apache_beam/io/filebasedsink.py
def pre_finalize(self, init_result, writer_results):
  num_shards = len(list(writer_results))
  dst_glob = self._get_final_name_glob(num_shards)
  dst_glob_files = [
      file_metadata.path for mr in FileSystems.match([dst_glob])
      for file_metadata in mr.metadata_list
  ]

  if dst_glob_files:
    _LOGGER.warning(
        'Deleting %d existing files in target path matching: %s',
        len(dst_glob_files),
        self.shard_name_glob_format)
    FileSystems.delete(dst_glob_files)
```

**It deletes the existing files matching the destination glob before
writing.** So `WriteToText` is a *replace*, not an append, and
re-running it over the same prefix is safe with respect to
duplication.

You can see this in the log output of a second run:

```text
WARNING:root:Deleting 1 existing files in target path matching: append2-*
```

Two details that bite:

1. **The glob is the destination glob, not the whole prefix
   directory.** If you write to `gs://bucket/revenue/` with
   `num_shards=1` and the default template, the glob is
   `revenue-*`, and only those files are deleted. If a previous run
   wrote a *different* number of shards — say you changed `num_shards`
   from 1 to 4 — the old `revenue-00000-of-00001` file does **not**
   match the new `revenue-*-of-00004` glob, so it survives and now
   sits alongside the new files. That is a real, silent corruption:
   your downstream reader globs `revenue-*` and gets five regions'
   worth of rows across two runs.

2. **`shard_name_template=""` changes the file name.** With the empty
   template the output is a single file named exactly after the
   prefix — no suffix at all. The project uses this so the output is
   one clean CSV file. The delete glob then matches that exact path.

So: `WriteToText` is idempotent by replacement, and the danger is not
duplication but *orphaned files from a previous shape*.

### The measured double-count

Let us measure the failure mode the other sinks have, so the numbers
are real rather than asserted.

The course data has 5,000 orders, of which 1,245 are `complete` and
valid. Aggregated by region, the correct answer is:

| Region | Order count | Revenue (EUR) |
|---|---|---|
| AMER | 318 | 113592.19 |
| APAC | 285 | 108194.92 |
| EMEA | 322 | 118423.22 |
| LATAM | 320 | 110646.18 |

Now run the pipeline twice against an *appending* sink. The second run
writes the same four rows again, and the table now holds:

| Region | Order count | Revenue (EUR) | Correct? |
|---|---|---|---|
| AMER | 636 | 227184.38 | **wrong — doubled** |
| APAC | 570 | 216389.84 | **wrong — doubled** |
| EMEA | 644 | 236846.44 | **wrong — doubled** |
| LATAM | 640 | 221292.36 | **wrong — doubled** |

This is the shape of the incident. Nothing errors. Nothing logs. The
job succeeds twice. The dashboard shows revenue exactly 2× and the
first thing anyone notices is that the forecast is wrong.

The tell is that *every* number is exactly double. That is a useful
diagnostic: if a revenue number is exactly 2×, look for a re-run, not
for a data problem.

### Idempotency is a property of the *whole* pipeline, not the sink

A sink can be perfectly idempotent and the pipeline can still produce
the wrong answer, because something upstream changed between the two
runs.

The classic failure: the pipeline reads "the current exchange rate
table" from somewhere, converts USD to EUR, and writes the result. Run
it on Monday, the rate is 0.92. Re-run it on Tuesday, the rate is
0.94. The sink truncates perfectly. But the two runs produced
different answers for the same input — and the second run has silently
overwritten the first with a *different* number.

If the pipeline must be re-runnable and produce the same answer, then
everything the computation depends on must be **pinned for the run**:

- The exchange rates used (the course project hard-codes them in
  `CURRENCY_TO_EUR`, which is a simplification — see the case study
  in chapter 6.6)
- The reference/lookup data (the product category file in
  `batch_pipeline.py`)
- The set of statuses included
- The schema

The general principle: **the output of a batch job must be a function
of (input, parameters) only.** If it depends on anything else — the
clock, the current contents of a mutable lookup table, a random seed —
then it is not reproducible, and "re-run" does not mean "get the same
answer".

This is what people mean by "designing for replay".

### Determinism, and where wall-clock time sneaks in

Beam's runner can replay a bundle. For the replay to be correct, the
transform must produce the same output for the same input. The usual
violations:

**Wall-clock time in the logic.**

```python
# WRONG — the output depends on when the job ran
class StampOrder(beam.DoFn):
    def process(self, order):
        yield {**order, "loaded_at": datetime.now(timezone.utc).isoformat()}
```

If a bundle is retried, the retry stamps a *later* time. Now two
copies of the same order carry different `loaded_at` values, and if
`loaded_at` is part of your dedup key or your partition key, the
retry writes to a different place.

The fix is to move the timestamp out of the *logic* and into the
*metadata*. Beam gives you the window end timestamp as a side input:

```python
# RIGHT — the timestamp comes from the window, which is deterministic
class StampOrder(beam.DoFn):
    def process(self, order, ts=beam.DoFn.TimestampParam):
        yield {**order, "loaded_at": ts.to_utc_datetime().isoformat()}
```

For a batch job with a single global window, that timestamp is the
job's end time — which is deterministic *per run* but not across
runs. For a job that must be byte-identical across re-runs, pass the
data date in as a **pipeline parameter** instead. That is the subject
of chapter 6.5.

**Unseeded randomness.**

```python
# WRONG — a retry gets a different value
class Jitter(beam.DoFn):
    def process(self, order):
        yield {**order, "sample_rate": random.random()}
```

If the random value is part of the output, a retry produces a
different row. If it is part of a *filter* (`if random.random() < 0.01`),
a retry can include a row the first attempt excluded — so a retry
*changes the population*, not just its values.

If you need randomness, seed it from the element:

```python
# RIGHT — the same element always gets the same jitter
import hashlib

def stable_jitter(order_id: str) -> float:
    digest = hashlib.sha256(order_id.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") / 2**32
```

**Iteration order over an unordered collection.**

```python
# WRONG — set iteration order depends on the hash seed, which varies
# per process
for category in set(order["categories"]):
    ...
```

Use a sorted list, or a dict keyed by the value.

**Non-deterministic coders.** Covered in chapter 6.2 — if your shuffle
key is encoded by `FastPrimitivesCoder` (which is what a bare `dict` or
`tuple` gets), the encoding is not guaranteed stable.

### The `dedup_key` pattern from the project

The course project has a deduplication key helper:

```python
def dedup_key(event: dict[str, Any]) -> str:
    """Return the deduplication key for an event.

    Pub/Sub is at-least-once, so the same event can arrive twice. The
    deduplication key must be derived from the payload's own identity, never
    from arrival time.
    """
    return str(event.get("event_id") or event.get("user_id", ""))
```

Read the docstring carefully — it encodes the entire rule:

> The deduplication key must be derived from the payload's own identity,
> never from arrival time.

That is the whole discipline. A dedup key built from the arrival time
(or from `uuid4()`, or from `datetime.now()`) is not a dedup key at
all: a redelivery of the same message gets a different key, and the
duplicate survives the deduplication.

The same rule applies to the *partition key* in the idempotent-sink
pattern. `dt=<data date>`, not `dt=<run date>`.

### Insert-only versus upsert

Two different shapes, used for two different kinds of data.

**Insert-only** means "this row is a new fact, add it to the set of
facts". The classic example is a payment. A payment that happens twice
is two payments, and you would want both. Insert-only sinks append and
rely on the producer's keys being unique; if the producer guarantees
that, insertion is enough and it is the cheapest option.

**Upsert** means "this row is the current state of entity X". The
classic example is a customer balance. Writing the same balance twice
must leave one balance, not two. Upsert sinks need a primary key.

The decision comes down to a question about the domain: **can this fact
legitimately occur twice?**

| Fact | Repeated? | Shape |
|---|---|---|
| A payment | No — but a *redelivery* of the same payment looks identical | Upsert on payment_id |
| A page view | Yes — a user really can view a page twice | Insert-only, or a count |
| A customer balance | No — one balance per customer, per day | Upsert on (customer_id, date) |
| A daily revenue total | No — one total per region, per day | Upsert on (region, date) |

The course project's revenue summary is the last row: one total per
region per day. That is an upsert, and it is exactly what
`WRITE_TRUNCATE` on a date-partitioned table, or `MERGE` on
`(region, date)`, is for.

### BigQuery's own mechanisms

BigQuery offers two mechanisms that help, and it is worth knowing which
one is which.

**`insert_id` (streaming inserts).** When you stream rows into
BigQuery, each row may carry an `insert_id`. BigQuery uses it to
deduplicate *best-effort* — within a time window, not forever. The
window is finite and undocumented in detail; do not treat it as a
guarantee. And it only applies to the streaming-inserts path.

Beam exposes it through `ignore_insert_ids`:

```text
ignore_insert_ids: If using the STREAMING_INSERTS method to write data
    to BigQuery, `insert_ids` are a feature of BigQuery that support
    deduplication of events. If your use case is not sensitive to
    duplication of data inserted to BigQuery, set `ignore_insert_ids`
    to True to increase the throughput for BQ writing.
```

So the *default* is `False` — Beam keeps the insert ids, and BigQuery
deduplicates. Setting it to `True` turns deduplication off and speeds
up the write. For an idempotent pipeline you want it `False`.

**CDC writes with a primary key.** In 2.77, `WriteToBigQuery` supports
`use_cdc_writes=True` with a `primary_key` list. That maps onto the
Storage Write API's `UPSERT` and `DELETE` mutations:

```text
required string properties ``mutation_type`` (``UPSERT`` or
``DELETE``) and ``change_sequence_number``.
primary_key: When using CDC write on BigQuery and
    CREATE_IF_NEEDED mode for the underlying tables a list of column names
    is required to be configured as the primary key.
```

Each row must carry a `mutation_type` of `UPSERT` or `DELETE` and a
`change_sequence_number`. The primary key identifies the row; the
sequence number orders the mutations. **This is effectively-once
delivery at the row level**, provided your `change_sequence_number` is
itself deterministic and monotonic.

Note the caveat in the source: `primary_key` is only required in
`CREATE_IF_NEEDED` mode. If the table already exists with a primary
key declared, you do not pass it.

**`use_at_least_once`.** Also Storage-Write-API-only:

```text
use_at_least_once: Intended only for STORAGE_WRITE_API. When True, will
    use at-least-once semantics. This is cheaper and provides lower
    latency, but will potentially duplicate records.
```

This is the explicit trade: cheaper and lower latency, but duplicates
possible. It is the *opposite* of what an idempotent pipeline wants,
and it is the default (`False`) only because the default is the safer
one.

### The real finding in the course template

The course's flex template at `project/templates/batch_template.py`
writes to BigQuery like this:

```python
if bigquery_table:
    summary | "WriteBigQuery" >> beam.io.WriteToBigQuery(
        bigquery_table,
        write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
        create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
    )
```

**`WRITE_APPEND` is the wrong disposition for this job.** The job
computes a *complete* daily revenue summary from a *complete* input
file. Every run produces the same four rows for the same input. With
`WRITE_APPEND`:

- Re-running the job doubles the summary.
- Re-running after a fix leaves the old, wrong rows in the table
  forever.
- Running a backfill for 2026-01-15 appends 2026-01-15's totals to
  whatever the daily run already wrote for that date.

And nothing about the pipeline is protected: the BigQuery write is
outside the checkpointed state, the job is trivially re-runnable, and
the operator has a natural reflex to re-run when a job fails.

The fix, for a full-refresh job:

```python
if bigquery_table:
    summary | "WriteBigQuery" >> beam.io.WriteToBigQuery(
        bigquery_table,
        write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE,
        create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
    )
```

`WRITE_TRUNCATE` deletes the table's contents and writes the new rows.
A re-run produces the same table. A failed re-run leaves the table
untouched, because the truncate happens as part of the load job, not
before it.

There is a caveat, and it is the reason this is a *finding* rather than
a blind edit: `WRITE_TRUNCATE` replaces the **entire table**. If the
table is meant to hold one row per (region, date) across many days,
truncating it destroys every day but the one you just computed.

The right design for that shape is a **date-partitioned table** plus a
partition-scoped replace — i.e. write to a specific partition and
overwrite only that partition. That is chapter 6.5's subject.

For now, the honest statement is: **as written, the template is
correct only if the target table holds exactly one day's summary.** If
it does not, the disposition needs to become partition-aware, and that
is a code change with a schema migration behind it.

### A checklist you can run a pipeline against

1. **Is the sink idempotent?** Replace, or deterministic partition key,
   or upsert on a primary key. If it is `WRITE_APPEND` with no key —
   stop.
2. **Is the partition key derived from the data?** `dt=<data date>`,
   never `dt=<run date>`.
3. **Does the output depend only on (input, parameters)?** No wall-clock
   time in the logic, no unseeded randomness, no mutable lookup tables
   read at run time.
4. **Is the whole run parameterised** — input path, output path,
   partition id, and every lookup table? See chapter 6.5.
5. **Can you re-run it and get the same answer?** Not "will not
   duplicate" — the same *answer*. If the answer can change, the run is
   not reproducible.
6. **What happens if the job fails halfway?** With `WRITE_TRUNCATE`,
   nothing: the truncate is part of the load. With an appending sink,
   you have a partial write and no clean way to undo it.

---

## 🛠️ Hands-On

### Setup

```bash
cd data-engineering/data-Course/google/Dataflow
source .venv/bin/activate
python resources/sample_data.py --output-dir ./sample_data
```

### Step 1 — build the pipeline once, run it twice

The point of this exercise is to see, with your own eyes, what the
*same* pipeline does when the sink appends versus when it replaces.

Create `hands_on_idempotency.py`:

```python
"""Run the same batch pipeline twice and observe the sink's behaviour."""
import os
import shutil
import sys

sys.path.insert(0, "project")

import apache_beam as beam

from transforms import (
    ParseOrderFn,
    RevenueByRegionFn,
    format_summary_csv,
    to_summary_row,
)

INPUT = "./sample_data/orders.csv"
OUTPUT = "./out/hands_on/idempotency"


def build(output_path):
    """Build and run the revenue summary pipeline.

    Args:
        output_path: Where to write the summary CSV.

    Returns:
        Nothing.
    """
    with beam.Pipeline() as pipeline:
        orders = (
            pipeline
            | "ReadOrders" >> beam.io.ReadFromText(INPUT)
            | "ParseOrders" >> beam.ParDo(ParseOrderFn())
        )
        summary = (
            orders
            | "KeepComplete" >> beam.Filter(lambda o: o["status"] == "complete")
            | "KeyByRegion" >> beam.Map(lambda o: (o["region"], o))
            | "RevenueByRegion" >> beam.CombinePerKey(RevenueByRegionFn())
            | "ToFlatRow" >> beam.Map(to_summary_row)
            | "FormatCsv" >> beam.Map(format_summary_csv)
        )
        summary | "WriteSummary" >> beam.io.WriteToText(
            output_path,
            header="region,order_count,revenue_eur",
            num_shards=1,
            shard_name_template="",
        )


def show(label):
    """Print the contents of the output file.

    Args:
        label: A label to print above the contents.

    Returns:
        Nothing.
    """
    print(f"--- {label} ---")
    with open(OUTPUT, encoding="utf-8") as handle:
        print(handle.read())


def main():
    """Run the pipeline twice and print the output after each run.

    Returns:
        Nothing.
    """
    shutil.rmtree(OUTPUT, ignore_errors=True)

    build(OUTPUT)
    show("after run 1")

    build(OUTPUT)
    show("after run 2")


if __name__ == "__main__":
    main()
```

Run it:

```bash
python hands_on_idempotency.py
```

Expected:

```text
--- after run 1 ---
region,order_count,revenue_eur
AMER,318,113592.19
APAC,285,108194.92
EMEA,322,118423.22
LATAM,320,110646.18

--- after run 2 ---
region,order_count,revenue_eur
AMER,318,113592.19
APAC,285,108194.92
EMEA,322,118423.22
LATAM,320,110646.18
```

**Identical.** The second run did not double anything.

Watch the log output, though. On *both* runs you will see:

```text
WARNING:apache_beam.io.filebasedsink:Deleting 1 existing files in target path matching:
```

The warning fires on the first run too, even though there was nothing
to delete — Beam logs the count of files it *found* before deleting
them, and the first run finds one file: its own temporary file, which
matches the destination glob because the temporary and the final file
share the prefix. That is the mechanism working, not a bug. (The glob
prints empty here because `shard_name_template=""` makes the output
file name exactly the prefix, so the glob has no wildcard in it.)

`WriteToText` deleted the previous output before writing the new one.
That is why it is idempotent.

One more thing to notice: the region order is not guaranteed.
`CombinePerKey` gives no ordering guarantee, so the four rows can come
out in any order. On the Direct Runner they often come out sorted
because the combiner happens to see the keys in order, but that is an
accident of the implementation, not a contract. Always compare sorted
output when you assert on results:

```bash
python hands_on_idempotency.py > /tmp/twice.txt
grep -A5 "after run 2" /tmp/twice.txt | tail -n +2 | sort
```

### Step 2 — see the double-count with an appending sink

Now let us reproduce the failure mode that the file sink does *not*
have. We will build the appending sink that BigQuery's `WRITE_APPEND`
behaves like, and show the doubling.

Create `hands_on_append.py`:

```python
"""Show what an appending sink does on a re-run."""
import os
import sys

sys.path.insert(0, "project")

import apache_beam as beam
from apache_beam.coders import coders
from apache_beam.io import filebasedsink

from transforms import (
    ParseOrderFn,
    RevenueByRegionFn,
    format_summary_csv,
    to_summary_row,
)

INPUT = "./sample_data/orders.csv"
OUTPUT = "./out/hands_on/appending_sink.csv"


class AppendingTextSink(filebasedsink.FileBasedSink):
    """A text sink that appends instead of replacing.

    This mimics what a BigQuery table with `WRITE_APPEND` does: the
    rows from a second run are added to the rows from the first.

    Two methods differ from `beam.io.WriteToText`'s sink:

    * `pre_finalize` does not delete the existing destination files.
    * `finalize_write` concatenates the new content onto the existing
      file instead of renaming over it.
    """

    def __init__(self, path, header=None):
        """Create the sink.

        Args:
            path: The output file path.
            header: An optional header line.
        """
        super().__init__(
            path,
            coder=coders.ToBytesCoder(),
            shard_name_template="",
            num_shards=1,
        )
        self._header = header

    def pre_finalize(self, init_result, writer_results):
        """Do not delete the existing files — that is the whole point.

        `FileBasedSink.pre_finalize` deletes every file matching the
        destination glob. Overriding it to do nothing turns the sink
        from a replace into an append.

        Args:
            init_result: The initialisation result.
            writer_results: The write results.

        Returns:
            Nothing.
        """
        return None

    def write_encoded_record(self, file_handle, encoded_value):
        """Write one already-encoded record to the file handle.

        Args:
            file_handle: The open file handle.
            encoded_value: The encoded bytes of the record.

        Returns:
            Nothing.
        """
        file_handle.write(encoded_value)
        file_handle.write(b"\n")

    def open(self, temp_path):
        """Open the temp file and write the header.

        Args:
            temp_path: The path of the temp file.

        Returns:
            The open file handle.
        """
        file_handle = super().open(temp_path)
        if self._header is not None:
            file_handle.write(coders.ToBytesCoder().encode(self._header))
            file_handle.write(b"\n")
        return file_handle

    def finalize_write(self, init_result, writer_results, unused):
        """Append the new content to the existing file.

        `FileBasedSink.finalize_write` renames the temp file over the
        destination, which replaces it. Here we read the existing
        destination, append the new content to it, and write the
        result back.

        Args:
            init_result: The initialisation result.
            writer_results: The write results.
            unused: Unused pre-finalisation results.

        Returns:
            Nothing.
        """
        destination = self._get_final_name(0, 1)
        existing = b""
        if os.path.exists(destination):
            with open(destination, "rb") as handle:
                existing = handle.read()

        with open(writer_results[0], "rb") as handle:
            new_content = handle.read()

        with open(destination, "wb") as handle:
            handle.write(existing + new_content)

        os.remove(writer_results[0])


def build():
    """Build and run the revenue summary pipeline into the appending sink.

    Returns:
        Nothing.
    """
    with beam.Pipeline() as pipeline:
        orders = (
            pipeline
            | "ReadOrders" >> beam.io.ReadFromText(INPUT)
            | "ParseOrders" >> beam.ParDo(ParseOrderFn())
        )
        summary = (
            orders
            | "KeepComplete" >> beam.Filter(lambda o: o["status"] == "complete")
            | "KeyByRegion" >> beam.Map(lambda o: (o["region"], o))
            | "RevenueByRegion" >> beam.CombinePerKey(RevenueByRegionFn())
            | "ToFlatRow" >> beam.Map(to_summary_row)
            | "FormatCsv" >> beam.Map(format_summary_csv)
        )
        summary | "WriteSummary" >> beam.io.Write(
            AppendingTextSink(
                OUTPUT, header="region,order_count,revenue_eur"
            )
        )


def show(label):
    """Print the contents of the output file.

    Args:
        label: A label to print above the contents.

    Returns:
        Nothing.
    """
    print(f"--- {label} ---")
    with open(OUTPUT, encoding="utf-8") as handle:
        print(handle.read())


def main():
    """Run the pipeline twice and print the output after each run.

    Returns:
        Nothing.
    """
    if os.path.exists(OUTPUT):
        os.remove(OUTPUT)

    build()
    show("after run 1")

    build()
    show("after run 2")


if __name__ == "__main__":
    main()
```

Run it:

```bash
python hands_on_append.py
```

Expected:

```text
--- after run 1 ---
region,order_count,revenue_eur
AMER,318,113592.19
APAC,285,108194.92
EMEA,322,118423.22
LATAM,320,110646.18

--- after run 2 ---
region,order_count,revenue_eur
AMER,318,113592.19
APAC,285,108194.92
EMEA,322,118423.22
LATAM,320,110646.18
region,order_count,revenue_eur
LATAM,320,110646.18
AMER,318,113592.19
APAC,285,108194.92
EMEA,322,118423.22
```

There it is. Two copies of the summary, and a second header line in
the middle. Both runs succeeded. Nothing logged an error. This is
exactly what `WRITE_APPEND` does to a BigQuery table, and exactly what
the course's flex template does today.

Note the header, too: the second run wrote the header again. A
BigQuery table would not have that artefact — it would have eight rows
where there should be four. The header is a quirk of the file sink;
the doubling is the real lesson.

Three implementation details in that sink are worth knowing, because
each one is a `FileBasedSink` contract you have to honour:

- **A `FileBasedSink` is not a `PTransform`.** You cannot use it
  directly with `>>`. Wrap it: `pcoll | "Write" >> beam.io.Write(sink)`.
  Passing it straight to `>>` gives you
  `TypeError: unsupported operand type(s) for >>: 'str' and 'AppendingTextSink'`.
- **You must implement `write_encoded_record`, not `write`.** The base
  class's `write_record` encodes with `self.coder` and calls
  `write_encoded_record`, which raises `NotImplementedError` by default.
- **`FileBasedSink.__init__` requires a `coder`.** The signature is
  `FileBasedSink(file_path_prefix, coder, file_name_suffix='',
  num_shards=0, shard_name_template=None, ...)`. Omitting it gives
  `TypeError: FileBasedSink.__init__() missing 1 required positional
  argument: 'coder'`.

And the one that actually produces the append behaviour: overriding
`pre_finalize` to do nothing stops Beam deleting the existing
destination file. Overriding `finalize_write` to concatenate instead
of rename stops the new content from replacing the old. You need
**both** — overriding only `pre_finalize` still produces a replacing
sink, because `finalize_write` renames the temp file over the
destination.

### Step 3 — the deterministic partition key

Here is the idempotent version of the same shape: write to a
data-derived location, so a re-run overwrites in place.

Create `hands_on_partition_key.py`:

```python
"""Show how a deterministic partition key makes a re-run safe."""
import os
import shutil
import sys

sys.path.insert(0, "project")

import apache_beam as beam

from transforms import (
    ParseOrderFn,
    RevenueByRegionFn,
    format_summary_csv,
    to_summary_row,
)

INPUT = "./sample_data/orders.csv"
OUTPUT_ROOT = "./out/hands_on/partitions"

# The data date. In production this is a pipeline parameter, derived
# from the input path or passed with --data_date.
DATA_DATE = "2026-01-15"


def partition_path(data_date):
    """Return the output path for one data date.

    Args:
        data_date: The date the data is about.

    Returns:
        The partition path.
    """
    return os.path.join(OUTPUT_ROOT, f"dt={data_date}")


def build(data_date):
    """Build and run the revenue summary pipeline for one data date.

    Args:
        data_date: The date the data is about.

    Returns:
        Nothing.
    """
    output_path = partition_path(data_date)
    with beam.Pipeline() as pipeline:
        orders = (
            pipeline
            | "ReadOrders" >> beam.io.ReadFromText(INPUT)
            | "ParseOrders" >> beam.ParDo(ParseOrderFn())
        )
        summary = (
            orders
            | "KeepComplete" >> beam.Filter(lambda o: o["status"] == "complete")
            | "KeyByRegion" >> beam.Map(lambda o: (o["region"], o))
            | "RevenueByRegion" >> beam.CombinePerKey(RevenueByRegionFn())
            | "ToFlatRow" >> beam.Map(to_summary_row)
            | "FormatCsv" >> beam.Map(format_summary_csv)
        )
        summary | "WriteSummary" >> beam.io.WriteToText(
            output_path,
            header="region,order_count,revenue_eur",
            num_shards=1,
            shard_name_template="",
        )


def show(data_date, label):
    """Print the contents of one partition.

    Args:
        data_date: The date the data is about.
        label: A label to print above the contents.

    Returns:
        Nothing.
    """
    path = partition_path(data_date)
    print(f"--- {label} ({path}) ---")
    with open(path, encoding="utf-8") as handle:
        print(handle.read())


def main():
    """Re-run one partition and show that it is unchanged.

    Returns:
        Nothing.
    """
    shutil.rmtree(OUTPUT_ROOT, ignore_errors=True)

    build(DATA_DATE)
    show(DATA_DATE, "after run 1")

    build(DATA_DATE)
    show(DATA_DATE, "after run 2 (same data date)")

    # Now write a *different* data date to a different partition.
    build("2026-01-16")
    show("2026-01-16", "a different data date, a different partition")

    # The first partition is untouched.
    show(DATA_DATE, "the first partition, after the second date ran")


if __name__ == "__main__":
    main()
```

Run it:

```bash
python hands_on_partition_key.py
```

Expected:

```text
--- after run 1 (./out/hands_on/partitions/dt=2026-01-15) ---
region,order_count,revenue_eur
AMER,318,113592.19
APAC,285,108194.92
EMEA,322,118423.22
LATAM,320,110646.18

--- after run 2 (same data date) (./out/hands_on/partitions/dt=2026-01-15) ---
region,order_count,revenue_eur
EMEA,322,118423.22
LATAM,320,110646.18
AMER,318,113592.19
APAC,285,108194.92

--- a different data date, a different partition (./out/hands_on/partitions/dt=2026-01-16) ---
region,order_count,revenue_eur
AMER,318,113592.19
APAC,285,108194.92
EMEA,322,118423.22
LATAM,320,110646.18

--- the first partition, after the second date ran (./out/hands_on/partitions/dt=2026-01-15) ---
region,order_count,revenue_eur
EMEA,322,118423.22
LATAM,320,110646.18
AMER,318,113592.19
APAC,285,108194.92
```

Look closely at the second and fourth blocks. The rows are the **same
four values**, but in a **different order** from the first block. That
is `CombinePerKey` doing exactly what it promises: no ordering
guarantee. Run it again and the order may change again.

This matters for the "idempotent" claim, and it is worth being precise
about what idempotency means here. The *content* is identical — the
same four regions with the same counts and the same revenue. The
*byte order* is not guaranteed. So:

- A **sink** is idempotent when re-running produces the same final
  *state* — the same set of rows, in whatever order.
- A **file** is byte-identical only if you sort before writing.

If you need a byte-stable file — for a checksum, for a diff, for a
contract test — sort the rows before the write:

```python
keyed = summary | "SortByRegion" >> beam.Map(lambda row: (row[0], row))
sorted_rows = keyed | "SortRows" >> beam.combiners.Top.Largest(4)
```

or, more simply, sort the four rows in Python before writing them,
because a batch summary is small:

```python
rows = sorted(rows, key=lambda row: row[0])
```

Note that `beam.combiners.Top.Largest(4)` is itself a shuffle — you
have paid a network round trip to buy an ordering. For a four-row
summary, sorting in Python is strictly better. Sort in Beam only when
the number of rows makes it impossible to hold in memory.

The 2026-01-16 partition has the same numbers as 2026-01-15 because we
are reading the same input file both times — that is fine for the
demonstration, and it is exactly the point: **the partition key comes
from the data, so the same data always lands in the same place, and a
different date never touches it.**

The directory now looks like this:

```text
out/hands_on/partitions/
├── dt=2026-01-15
└── dt=2026-01-16
```

### Step 4 — make the run date-independent

The previous step hard-coded `DATA_DATE`. In a real pipeline it is a
parameter, and it must come from the *data*, not from the clock.

Create `hands_on_reproducible.py`:

```python
"""Show the difference between a data-derived date and a wall-clock date."""
import os
import shutil
import sys
from datetime import date

sys.path.insert(0, "project")

import apache_beam as beam

from transforms import (
    ParseOrderFn,
    RevenueByRegionFn,
    format_summary_csv,
    to_summary_row,
)

INPUT = "./sample_data/orders.csv"
OUTPUT_ROOT = "./out/hands_on/reproducible"


def build(data_date):
    """Build and run the pipeline for one data date.

    Args:
        data_date: The date the data is about, as a string.

    Returns:
        Nothing.
    """
    output_path = os.path.join(OUTPUT_ROOT, f"dt={data_date}")
    with beam.Pipeline() as pipeline:
        orders = (
            pipeline
            | "ReadOrders" >> beam.io.ReadFromText(INPUT)
            | "ParseOrders" >> beam.ParDo(ParseOrderFn())
        )
        summary = (
            orders
            | "KeepComplete" >> beam.Filter(lambda o: o["status"] == "complete")
            | "KeyByRegion" >> beam.Map(lambda o: (o["region"], o))
            | "RevenueByRegion" >> beam.CombinePerKey(RevenueByRegionFn())
            | "ToFlatRow" >> beam.Map(to_summary_row)
            | "FormatCsv" >> beam.Map(format_summary_csv)
        )
        summary | "WriteSummary" >> beam.io.WriteToText(
            output_path,
            header="region,order_count,revenue_eur",
            num_shards=1,
            shard_name_template="",
        )


def main():
    """Compare a data-derived date with a wall-clock date.

    Returns:
        Nothing.
    """
    shutil.rmtree(OUTPUT_ROOT, ignore_errors=True)

    # The RIGHT way: the date comes from the data being processed.
    build("2026-01-15")
    print("data-derived partition:", sorted(os.listdir(OUTPUT_ROOT)))

    # The WRONG way: the date comes from the clock. Re-running the
    # same data tomorrow writes to a different partition, so the old
    # partition still holds the old answer and the new partition
    # holds a duplicate of it.
    tomorrow = date.today().isoformat()
    build(tomorrow)
    print("wall-clock partition:  ", sorted(os.listdir(OUTPUT_ROOT)))
    print()
    print("Both partitions now exist, holding the same data.")
    print("A re-run tomorrow would add a third.")


if __name__ == "__main__":
    main()
```

Run it:

```bash
python hands_on_reproducible.py
```

Expected:

```text
data-derived partition: ['dt=2026-01-15']
wall-clock partition:   ['dt=2026-01-15', 'dt=2026-10-28']
```

The date will be whatever today is when you run it. The lesson is the
*shape*: a wall-clock date creates a new partition on every re-run, so
the same data ends up in N places, and none of them overwrite each
other.

### Step 5 — the fix for the course template

Let us look at the actual template and apply the fix.

```bash
grep -n "BigQueryDisposition" project/templates/batch_template.py
```

Current state:

```text
118:            write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
119:            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
```

The corrected version:

```python
if bigquery_table:
    summary | "WriteBigQuery" >> beam.io.WriteToBigQuery(
        bigquery_table,
        write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE,
        create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
    )
```

`WRITE_TRUNCATE` is the right disposition **when the table holds one
run's worth of data**. If the table is meant to accumulate across
days, the fix is different: partition the table by the data date and
truncate only the partition being rewritten. BigQuery's partition
expiry and partition-scoped load jobs handle that; it is a schema
change, not a one-word change.

A test that would have caught this:

```python
def test_bigquery_disposition_is_not_append():
    """The template must not append — a re-run would double the totals."""
    source = TEMPLATE_PATH.read_text(encoding="utf-8")
    assert "WRITE_APPEND" not in source, (
        "batch_template.py uses WRITE_APPEND; a re-run would double the "
        "revenue summary. Use WRITE_TRUNCATE for a full-refresh batch job."
    )
```

That is a crude test, but it is the kind of guard that belongs in a
repo where the answer to a double-counted dashboard is "somebody
re-ran the job".

### Step 6 — assert idempotency in a test

The strongest guarantee you can give is a test that runs the pipeline
twice and asserts the output is unchanged. The course already has
`project/tests/test_pipelines.py` with a `TestBatchPipeline` class.

Add this:

```python
def test_rerunning_the_batch_pipeline_produces_the_same_output(self, tmp_path):
    """A re-run must not change the result. Idempotency, asserted."""
    from batch_pipeline import build_pipeline

    input_file = tmp_path / "orders.csv"
    input_file.write_text("\n".join(ORDER_LINES) + "\n", encoding="utf-8")
    output_prefix = tmp_path / "summary"

    def run_once():
        """Run the pipeline and return the output rows, sorted.

        Returns:
            The sorted list of output lines.
        """
        with TestPipeline(options=beam_test_options()) as pipeline:
            build_pipeline(
                pipeline,
                input_path=str(input_file),
                output_path=str(output_prefix),
            )
        output_files = sorted(tmp_path.glob("summary*"))
        contents = "\n".join(f.read_text(encoding="utf-8") for f in output_files)
        return sorted(contents.splitlines())

    first = run_once()
    second = run_once()

    # `CombinePerKey` gives no ordering guarantee, so compare the
    # sorted rows rather than the raw text. Without this the test is
    # flaky for the wrong reason, and a flaky test is a test people
    # delete.
    assert first == second
```

Two details make this test work with the existing project code:

- **`tmp_path` is a pytest fixture**, and it gives each test its own
  directory. The existing `test_end_to_end_revenue_summary` uses it the
  same way.
- **The helper is a nested function**, so the two runs share the same
  `input_file` and `output_prefix` — which is the whole point. The
  second run must land on top of the first run's output.

The reason it passes is `FileBasedSink`'s delete-then-write behaviour.
If someone changes the template to `WRITE_APPEND` for the BigQuery
sink, this test still passes — it exercises the *file* sink. To cover
the BigQuery sink too, combine it with the disposition check from Step
5.

---

## 🛠️ Common Errors and Fixes

### `RuntimeError: Transform name is already used`

Not idempotency — but it shows up whenever you re-run a pipeline
definition in one process. Two transforms in the same pipeline share a
label. See [chapter 2.5](10-filter-and-flatten.md).

### The output has double the rows after a re-run

Your sink appends. Check the disposition:

```python
write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE
```

And check whether the target table is meant to accumulate. If it is,
you need a date partition and a partition-scoped replace, not a
table-scoped truncate.

### The output has *extra* rows from an older run with a different shape

You changed `num_shards` between runs. `FileBasedSink` deletes the
files matching the *new* destination glob; the old shard files from a
different shard count do not match it and survive.

The fix is to write to a fresh prefix whenever the shard count changes,
or to delete the old prefix explicitly before the run.

### `AssertionError` from `AvroCoderImpl.encode`

Not idempotency — an Avro coder detail. See
[chapter 6.2](31-schema-coders-and-encoders.md).

### The re-run produces different numbers than the original

Your pipeline is not a pure function of its input. Look for:

- a lookup table read at run time (the course project's
  `CURRENCY_TO_EUR` is hard-coded, which *hides* this problem — a
  production pipeline would read rates from somewhere and must pin
  them per run)
- `datetime.now()` inside a `DoFn`
- `random.random()` without a stable seed
- set iteration order

### `ValueError: Invalid write disposition ...`

You passed the string `"WRITE_TRUNCATE"` where a `BigQueryDisposition`
constant was expected, or a typo. The valid values are:

```python
beam.io.BigQueryDisposition.WRITE_TRUNCATE
beam.io.BigQueryDisposition.WRITE_APPEND
beam.io.BigQueryDisposition.WRITE_EMPTY
```

### `ValueError: Invalid create disposition ...`

Valid create dispositions are `CREATE_NEVER` and `CREATE_IF_NEEDED`
only. There is no `CREATE_TRUNCATE`.

---

## 💡 Production Notes

### The re-run is not an exception, it is the normal path

Design for the re-run. In a mature batch pipeline you will see more
re-runs than first runs: transient failures, bad logic, schema changes,
late-arriving data, cost experiments. A pipeline that is only correct
on the first run is not production-ready.

### Prefer `WRITE_TRUNCATE` for full-refresh jobs

If the job computes the complete state of something from a complete
input, replace rather than append. It is simpler to reason about, it
is self-healing (a re-run fixes a partial write), and it eliminates an
entire class of incident.

The exception is a job whose output is genuinely incremental — where
run N is supposed to add to what run N-1 left. For those, use a
partition-scoped replace or an upsert.

### Give every run its own staging and temp locations

```python
options = PipelineOptions([
    "--staging_location=gs://YOUR_BUCKET/staging/job-2026-01-15",
    "--temp_location=gs://YOUR_BUCKET/temp/job-2026-01-15",
])
```

If two runs share a temp location, they can interfere — Beam's
temporary files are named by a UUID, so in practice collisions are
rare, but the cost of a unique location is zero and the debugging
cost of a collision is high. Unique per run is also what makes the
staging files from a failed run available for inspection.

### Make the output path a required parameter

A pipeline with a default output path will, at some point, write to
the default path when someone meant to write somewhere else — during a
backfill, most likely. Make the output path required, or at least
validate it.

### Use `--job_name` to make the run identifiable

```python
options = PipelineOptions([
    "--job_name=revenue-summary-dt-2026-01-15",
])
```

When you are looking at a doubled dashboard at 2am, knowing which run
produced the bad number is half the work.

### Monitor the row count, not just the job status

The single most valuable alert for this class of bug is a row-count
check that fires when the output row count is not what the input
implies:

```python
expected = count_input_orders()
actual = count_output_rows()
if actual != expected:
    alert("revenue summary row count mismatch", expected, actual)
```

A doubled table is a row-count anomaly before it is a revenue anomaly,
and the row count is available much sooner.

### Keep a run manifest

For every run, record: the input paths, the output path, the parameters,
the job name, the git commit, the start and end times, and the row
counts. When someone asks "why does 2026-01-15 have twice the revenue
of every other day?", the answer should be a lookup, not an
investigation. A manifest is 20 lines of code and it is the difference
between an afternoon and a week.

### Make the sink's disposition visible in the code review checklist

The single-word change from `WRITE_APPEND` to `WRITE_TRUNCATE` is easy
to miss in a diff and expensive to miss in production. Put it in the
review checklist. Or put it in a test, as in Step 5 — a test is better
than a checklist, because a checklist depends on somebody remembering.

---

## 🔑 Key Takeaways

1. **Beam provides exactly-once *processing*, not exactly-once
   *sinks*.** The sink write is outside the checkpointed state, so a
   crash between the write and the checkpoint replays the element.
2. **Effectively-once is the pattern you actually build**: at-least-once
   delivery plus an idempotent sink. It needs no distributed
   transactions.
3. **There are exactly three idempotent sink shapes**: replace
   (`WRITE_TRUNCATE`), deterministic partition key, or upsert on a
   primary key. `WRITE_APPEND` with no key is the anti-pattern.
4. **The partition key must come from the data**, not from the run's
   clock. `dt=<data date>`, never `dt=<run date>`.
5. **`beam.io.WriteToText` is a replace, not an append** — Beam's
   `FileBasedSink` deletes the existing destination-glob files before
   writing. Re-running it is safe.
6. **The danger with file sinks is not duplication but orphans**: change
   `num_shards` between runs and the old shard files survive, because
   they do not match the new destination glob.
7. **The output must be a pure function of (input, parameters).** No
   wall-clock time in the logic, no unseeded randomness, no mutable
   lookup tables read at run time.
8. **Beam's `DoFn.TimestampParam` gives you a deterministic timestamp**
   from the window. For a byte-identical-across-runs job, pass the data
   date in as a pipeline parameter instead.
9. **The course's `batch_template.py` uses `WRITE_APPEND` where
   `WRITE_TRUNCATE` belongs.** For a full-refresh daily summary that
   is a double-count waiting to happen.
10. **`WRITE_TRUNCATE` replaces the whole table.** If the table
    accumulates across days, you need a date partition and a
    partition-scoped replace — a schema change, not a one-word change.
11. **BigQuery's `insert_id` deduplication is best-effort and
    time-limited.** Do not treat it as a guarantee.
12. **`use_cdc_writes=True` with a `primary_key` gives row-level
    effectively-once semantics** via `UPSERT`/`DELETE` mutations — but
    only if your `change_sequence_number` is deterministic and
    monotonic.
13. **A re-run that produces exactly double is a re-run bug, not a data
    bug.** That symmetry is a useful diagnostic.
14. **Test idempotency by running twice and comparing sorted output.**
    `CombinePerKey` gives no ordering guarantee, so a raw text
    comparison is flaky for the wrong reason.

---

## 📚 Practice Exercises

1. **Add an idempotency test to the course project.** Extend
   `project/tests/test_pipelines.py` so that the batch pipeline runs
   twice against the same output path and the second run's output
   matches the first, sorted. Make it fail if anyone changes the
   template's write disposition to `WRITE_APPEND`.

2. **Reproduce the "different shard count leaves orphans" bug.** Run
   the pipeline with `num_shards=1`, then with `num_shards=4`, into the
   same prefix. List the files. Explain why the first run's file
   survives. Then fix it by deleting the prefix before the run, and by
   writing to a versioned prefix.

3. **Parameterise the data date end to end.** Add a `--data_date`
   argument to `project/batch_pipeline.py`, thread it through
   `build_pipeline`, and use it to build the output path
   (`.../dt=<data_date>/`) and the partition column. Prove that two
   runs with the same `--data_date` write to the same place and that
   two runs with different dates do not interfere.

4. **Audit every transform in the project for wall-clock
   dependencies.** Grep for `now()`, `today()`, `utcnow()`,
   `random.` and `uuid4()` inside `DoFn.process` methods. For each
   hit, decide whether it makes the output non-reproducible and, if
   so, replace it with a value derived from the element or from
   `TimestampParam`.

5. **Make the output path a required parameter.** Remove the default
   from `--output` in `project/batch_pipeline.py` so the job cannot
   accidentally write to a shared path. Update the README and the
   template's arguments accordingly.

6. **Design the upsert variant.** Specify how the revenue summary
   would be written to a BigQuery table partitioned by
   `order_date`, with one row per (region, order_date). Give the table
   schema, the partition decorator, the load job's
   `write_disposition`, and the exact steps for a
   partition-scoped replace. Explain why a table-scoped
   `WRITE_TRUNCATE` would be wrong here.

7. **Write the run manifest.** Add a `--manifest` argument to the
   batch pipeline that writes a JSON file recording the input paths,
   the output path, the parameters, the git commit, the start and end
   timestamps, and the input and output row counts. Show the
   manifest for one of the hands-on runs.

---

## 📖 Further Reading

- Apache Beam programming guide — the "Multiple Outputs" and
  "Encoding and Coder" sections — https://beam.apache.org/documentation/programming-guide/
- Beam's Exactly-Once Semantics in Beam — https://beam.apache.org/documentation/exactly-once/
- Google Cloud Dataflow — data processing model — https://cloud.google.com/dataflow/docs/concepts/processing-elements
- Google Cloud Dataflow — performing a full refresh update on a
  BigQuery table — https://cloud.google.com/dataflow/docs/guides/bigquery-full-refresh
- BigQuery — using partition decorators to limit data loads — https://cloud.google.com/bigquery/docs/partitioned-tables#partition-decorators
- BigQuery — WRITE_TRUNCATE, WRITE_APPEND and WRITE_EMPTY — https://cloud.google.com/bigquery/docs/reference/standard-sql/data-definition-language
- BigQuery — streaming inserts and `insert_id` deduplication — https://cloud.google.com/bigquery/docs/streaming-data-into-bigquery#insert_ids
- BigQuery Storage Write API — change streams and upserts — https://cloud.google.com/bigquery/docs/reference/storage-write-api
- Google Cloud Dataflow — exactly-once processing with BigQuery — https://cloud.google.com/dataflow/docs/concepts/exactly-once
- [Chapter 6.1 — Batch Design Patterns](30-batch-design-patterns.md)
- [Chapter 6.2 — Schema, Coders & Encoders](31-schema-coders-and-encoders.md)
- [Chapter 6.4 — Error Handling & DLQ](33-error-handling-and-dlq.md)
- [Chapter 6.5 — Backfills & Re-runs](34-backfills-and-re-runs.md)
