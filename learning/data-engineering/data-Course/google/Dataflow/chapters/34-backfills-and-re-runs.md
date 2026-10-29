# 6.5 — Backfills & Re-runs

> **Section 6 · Batch Pipeline Engineering · Lecture 6.5 · 6:30**

## 🎯 What you will learn

- What a backfill actually is in batch, and why it is a different operation from a re-run
- The three parameters every batch pipeline must expose: input path, output path, and partition id
- "Same code, different parameters" — the only definition of a backfill that scales
- Why the output must be partitioned by *data date*, and why a backfill must overwrite exactly one partition
- The trap that ruins live data: a backfill that writes to a shared output prefix
- Unique `--temp_location` and `--staging_location` per run, and why it matters
- The cost and safety checklist to run before every backfill
- How to monitor a backfill, and how to tell it has gone wrong

---

## 🧠 Concept

### Three operations that people call the same thing

The vocabulary around batch pipelines is sloppy, and the sloppiness
causes real incidents. Three distinct operations get called "a
re-run":

**A re-run** is the same input, the same parameters, executed again.
The reason is usually a transient failure or a code fix that does not
change the output. The output should be *identical* to what the first
run produced.

**A backfill** is *different* input — an earlier date — processed with
the same code. The output goes to a location derived from that earlier
date, not over the live output. A backfill is a new run, not a repeat.

**A reprocess** is the same input, the same date, but with *different*
logic — a changed currency table, a changed filter, a bug fix. The
output replaces the previous output for that date.

The distinction matters because each one has a different blast radius:

| Operation | Input | Parameters | Output location | Overwrites live data? |
|---|---|---|---|---|
| Re-run | same | same | same | Yes — and that is correct |
| Backfill | **different** (earlier date) | different date | the earlier date's partition | No |
| Reprocess | same | same date, **different logic** | same date's partition | Yes — deliberately |

The mistake — the one that shows up in incident reviews — is running a
backfill with a re-run's parameters, or a re-run with a backfill's
output path. Both are one missing parameter away.

### The definition of a backfill

> **A backfill is the same code, run with different parameters, against
> different input, writing to a different output location.**

Every clause matters. Take them away one at a time:

- **Same code** — not a copy of the pipeline with the date edited in.
  A copy drifts. In three months the copy has three bug fixes the
  original does not, or none of the fixes the original has. If the
  backfill uses different code, it is not a backfill; it is a second
  pipeline, and you now have two pipelines to maintain.
- **Different parameters** — the date, the input path, the output
  path. All three derived from one value: the data date.
- **Different input** — the file for that date.
- **Different output location** — a location that no live job will
  write to.

If a backfill cannot be expressed as "the same code plus three
parameters", the pipeline is not ready to backfill. That is the test.

### The three parameters

Every backfillable batch pipeline needs at least these:

**1. The input path.**

```python
parser.add_argument("--input", required=True)
```

Note `required=True`. The course's flex template already does this:

```python
parser.add_argument("--input", required=True, help="Input CSV path")
parser.add_argument("--output", required=True, help="Output path prefix")
```

which is good. The local `batch_pipeline.py` does not:

```python
parser.add_argument("--input", default=DEFAULT_INPUT, help="Input CSV path")
parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output path prefix")
```

Defaults are convenient and dangerous. A backfill that forgets
`--input` silently reads today's data and writes it into the
backfill's output path — a wrong answer, in a plausible place, with no
error.

**2. The output path.**

```python
parser.add_argument("--output", required=True)
```

**3. The partition id — the data date.**

This is the one that is usually missing, and it is the most important,
because the other two can be *derived* from it.

```python
parser.add_argument(
    "--data_date",
    required=True,
    help="The date the data is about, as YYYY-MM-DD.",
)
```

And then everything else is computed from it:

```python
def paths_for(data_date, root):
    """Return the input and output paths for one data date.

    Args:
        data_date: The date the data is about, as YYYY-MM-DD.
        root: The root prefix for both.

    Returns:
        A tuple of (input_path, output_path).
    """
    input_path = os.path.join(root, "orders", f"dt={data_date}", "orders.csv")
    output_path = os.path.join(root, "summary", f"dt={data_date}")
    return input_path, output_path
```

One parameter, three derived values. That is the shape of a
backfillable pipeline. If the operator has to keep three arguments
consistent with each other by hand, they will eventually not be.

**A warning about deriving the date from the path.** Parsing
`dt=2026-01-15` out of a filename is convenient, and it works, but it
makes the path format load-bearing. A pipeline whose date comes from
an explicit `--data_date` argument is easier to test and easier to
re-run with a different date. Derive the *paths* from the date, not
the date from the paths.

### Partitioning the output by data date

The output path must encode the data date, so that:

- a backfill for 2026-01-10 writes to `summary/dt=2026-01-10/`
- the live job for 2026-01-15 writes to `summary/dt=2026-01-15/`
- a re-run of 2026-01-15 overwrites `summary/dt=2026-01-15/` and
  touches nothing else

This is the **idempotent sink** pattern from
[chapter 6.3](32-idempotency-and-exactly-once.md), applied to a
directory rather than a table.

```text
gs://YOUR_BUCKET/summary/
├── dt=2026-01-10/
│   └── part-00000.csv
├── dt=2026-01-11/
│   └── part-00000.csv
├── dt=2026-01-12/
│   └── part-00000.csv
├── dt=2026-01-13/
│   └── part-00000.csv
├── dt=2026-01-14/
│   └── part-00000.csv
└── dt=2026-01-15/
    └── part-00000.csv
```

**The partition key is the data date, never the run date.** This is
the same rule as the deduplication key in the project's `dedup_key`,
and it is the rule that people break under time pressure. A backfill
run on 2026-10-28 for data from 2026-01-10 writes to
`dt=2026-01-10`. If it wrote to `dt=2026-10-28`, then:

- the live 2026-01-10 partition still holds the old (possibly wrong)
  data
- the new partition holds a duplicate of 2026-01-10's data under a
  misleading date
- a downstream query over `dt=2026-10-28` finds a partition that
  looks like today's data and is not

### The trap: a shared output prefix

Here is the incident, in the shape it actually happens.

The backfill script takes an output prefix as an argument. The
operator runs the live job and the backfill with the *same* prefix,
because the prefix is "the summary output" and they did not think
about it:

```bash
# The live job.
python batch_pipeline.py \
    --input gs://YOUR_BUCKET/orders/dt=2026-01-15/orders.csv \
    --output gs://YOUR_BUCKET/summary/

# The backfill, three weeks later, for 2026-01-10.
python batch_pipeline.py \
    --input gs://YOUR_BUCKET/orders/dt=2026-01-10/orders.csv \
    --output gs://YOUR_BUCKET/summary/
```

What happens depends on the sink:

**With `WriteToText` and a date-partitioned path**, the two runs
write to the same `summary/` prefix. `FileBasedSink` deletes the
files matching its destination glob — which is `summary/*`, or
`summary/dt=2026-01-15/*` if the path is partitioned. If the path is
*not* partitioned, the backfill's output **overwrites the live
output**. The live job for 2026-01-15 is gone, replaced by the
backfill's 2026-01-10 numbers, and the dashboard for 2026-01-15 now
shows January 10th's revenue.

**With a BigQuery sink and `WRITE_APPEND`**, both runs' rows end up in
the same table, with no date column to tell them apart. Now the table
has eight rows: four from the live job and four from the backfill,
and the consumer cannot tell which is which.

**With a BigQuery sink and `WRITE_TRUNCATE`**, the backfill truncates
the table and replaces the live data with January 10th's numbers. Same
outcome as the file case, but faster.

The defences, in order of strength:

**1. Partition the output by data date.** Then a backfill cannot
touch another date's data, because it writes to a different
directory.

**2. Write the backfill to a separate prefix.** `summary_backfill/`
instead of `summary/`. Then a backfill is *never* live data, and
promoting it is a deliberate copy.

**3. Make the output path required and validated.** No defaults, and
a check that the output path contains the data date.

The strongest version combines all three:

```python
def build_output_path(root, data_date, mode):
    """Return the output path for a run.

    Args:
        root: The output root.
        data_date: The data date, as YYYY-MM-DD.
        mode: Either "live" or "backfill".

    Returns:
        The output path.
    """
    if mode == "backfill":
        root = f"{root}_backfill"
    return os.path.join(root, f"dt={data_date}")
```

Now the mode is an explicit parameter, and a backfill *cannot* write
to the live prefix unless somebody changes the code.

### Unique temp and staging locations

Every Dataflow job needs a `--temp_location` and a
`--staging_location`. These are scratch space: Beam writes temporary
files there during the run and cleans them up afterwards.

```python
options = PipelineOptions([
    "--staging_location=gs://YOUR_BUCKET/staging/job-2026-01-10",
    "--temp_location=gs://YOUR_BUCKET/temp/job-2026-01-10",
])
```

**Make them unique per run.** The obvious derivation is the job name:

```python
run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
staging = f"gs://YOUR_BUCKET/staging/{run_id}"
temp = f"gs://YOUR_BUCKET/temp/{run_id}"
```

Why it matters:

- **Two concurrent runs must not share a temp location.** If a live
  job and a backfill share one, they can see each other's temporary
  files. Beam names temporary files with a UUID, so a collision is
  unlikely, but the cost of uniqueness is zero and the cost of a
  collision is a corrupted output that nobody can explain.
- **A failed run's staging files are the evidence.** If the temp
  location is per-run, the leftovers from the failed run are still
  there afterwards, and you can inspect them. If it is shared, another
  run may have cleaned them up.
- **Retries of the same run reuse the location, deliberately.** If you
  retry a failed job with the same job name, you want the same
  location — that is how Beam resumes from its checkpoint.

So the rule is: **unique per logical run, stable across retries of
that run.**

### The cost of a backfill

A backfill is not free, and the bill arrives later. What it costs:

**Compute.** A backfill of 90 days of data is 90 days of compute. If
the daily job takes 20 minutes and costs $3, that is $270. If it takes
four hours, it is $1,080.

**Quota and contention.** A backfill running alongside the live job
competes for the same Dataflow worker pool. The live job may get
slower, or hit a quota limit, or get preempted. This is the most
common operational impact of a backfill, and it is the reason backfills
are scheduled.

**BigQuery load jobs.** Each partition written is a load job. BigQuery
has quotas on concurrent load jobs and on the number of tables
modified per day. A 90-day backfill is 90 load jobs.

**Storage.** The backfilled partitions duplicate data that already
exists somewhere. If the backfill output is a full copy, you are
paying for a second copy of your dataset.

**Downstream re-computation.** If a downstream pipeline reads the
summary table and you overwrite 90 days of partitions, that downstream
pipeline may need to re-run too. That cost is usually not in the
backfill's budget.

### The safety checklist

Before you run a backfill, walk this list. It takes two minutes and
it catches every incident in this category that I have seen.

**Before:**

1. **The output path contains the data date.** Read the resolved path
   and check. `gs://bucket/summary/dt=2026-01-10/` — yes.
   `gs://bucket/summary/` — no.
2. **The output path is not the live prefix**, or it is a partition
   that only this backfill will write.
3. **The input path is the file for that date.** Check that it
   exists and that its date matches the parameter.
4. **The parameters are all for the same date.** Input path, output
   path, and any date the logic itself uses (the partition column,
   the exchange-rate table).
5. **The temp and staging locations are unique to this run.**
6. **You know the expected output.** Row count, and a checksum or a
   total. You need something to compare against when the backfill
   finishes.
7. **The job name says it is a backfill.** `revenue-summary-backfill-dt-2026-01-10`.
   It will show up in a list of jobs and you will want to know what it
   is.
8. **You know how to undo it.** If the backfill writes to a separate
   prefix, undoing it is `gsutil -m rm -r gs://bucket/summary_backfill/`.
   If it writes into the live prefix, undoing it is much harder.

**During:**

9. **Watch the first few minutes.** The first thing a backfill does is
   read the input. If the input path is wrong, you will see it in the
   first log lines.
10. **Watch the row counts.** A backfill that reads 10% of the
    expected rows is wrong, and the sooner you know, the less it
    costs.
11. **Watch the cost.** If the backfill is projected to cost more than
    you budgeted, kill it. `gcloud dataflow jobs cancel`.

**After:**

12. **Compare the output against the expected values.** Row count,
    and a spot check of the totals.
13. **Check that nothing else changed.** The live partitions should be
    byte-identical to before the backfill. If they are not, the
    backfill wrote where it should not have.
14. **Record what you ran.** The dates, the paths, the job name, the
    cost, and the outcome. In the run manifest from
    [chapter 6.3](32-idempotency-and-exactly-once.md).

### Monitoring a backfill

A backfill is a long-running job that nobody is watching. It needs
the same monitoring as a live job, plus two extra things.

**The progress metric.** How far through the date range is it? If the
backfill processes dates sequentially, you want to see the date
currently being processed. The way to get it is to make the date part
of the output, and to emit it as a metric:

```python
summary | "StampDataDate" >> beam.Map(
    lambda row: {**row, "data_date": data_date}
)
```

**The cost alarm.** Backfills are the single largest source of
surprise Dataflow bills. Set a budget alert on the project, and
monitor the job's `total_vcpu_hours` and `total_gb_bytes` metrics
while it runs.

**The correctness check.** The most important one, and the one people
skip. Compare the backfilled partition against what you expect:

```bash
# The backfilled partition.
gsutil cat gs://YOUR_BUCKET/summary_backfill/dt=2026-01-10/part-00000.csv

# The live partition for the same date, if it exists.
gsutil cat gs://YOUR_BUCKET/summary/dt=2026-01-10/part-00000.csv
```

If the live partition exists and the backfill is supposed to produce
the same thing, they should match. If they do not, the backfill used
different logic or different parameters — and you want to know that
*before* you promote the backfilled output.

### Backfilling into a table with `WRITE_TRUNCATE`

The file-sink case is easy: write to a different directory. The
BigQuery case needs more thought, because
`beam.io.BigQueryDisposition.WRITE_TRUNCATE` truncates the **whole
table**.

For a partitioned table, the correct operation is a
**partition-scoped replace**. There are three ways to do it, in
increasing order of control:

**1. A BigQuery partition decorator.** Load into a specific
partition with a decorator, and use `WRITE_TRUNCATE` with the
decorator's field set to the target partition. The load job replaces
only that partition.

```python
options = beam.io.BigQueryDisposition.WRITE_TRUNCATE
```

**2. Delete the partition, then append.** Run a DDL statement to drop
the partition, then load with `WRITE_APPEND` into the now-empty
partition. Two steps, and a window where the partition does not
exist.

**3. `MERGE`.** The most controlled, and the one that works with a
`primary_key`:

```sql
MERGE YOUR_PROJECT_ID.your_dataset.revenue_by_region AS target
USING (
    SELECT region, order_count, revenue_eur, @data_date AS data_date
    FROM staging
) AS source
ON target.data_date = source.data_date AND target.region = source.region
WHEN MATCHED THEN UPDATE SET
    order_count = source.order_count,
    revenue_eur = source.revenue_eur
WHEN NOT MATCHED THEN INSERT (data_date, region, order_count, revenue_eur)
VALUES (source.data_date, source.region, source.order_count, source.revenue_eur)
```

`MERGE` is idempotent by construction, targets exactly the rows it
should, and does not touch any other partition. It is the right
answer for a table that accumulates across dates.

The trade-off is that `MERGE` is not a Beam sink — you would run it
as a separate step after the pipeline writes to a staging table. That
is a common and reasonable architecture:

```text
Beam pipeline  ──►  staging table  ──►  MERGE  ──►  target table
```

### Backfill and re-run are the same code path

This is the design insight, and it is what "same code, different
parameters" buys you.

A backfill of 90 days is **90 invocations of the same pipeline** with
different parameters. It is not a special mode. There is no
`--backfill` flag that changes the pipeline's behaviour. The
behaviour differs only in the parameters:

```bash
for date in $(seq -f "2026-01-%02g" 1 31); do
    python batch_pipeline.py \
        --input "gs://YOUR_BUCKET/orders/dt=${date}/orders.csv" \
        --output "gs://YOUR_BUCKET/summary_backfill/dt=${date}" \
        --data_date "${date}" \
        --job_name "revenue-backfill-dt-${date}"
done
```

The advantages of running them one at a time rather than in a single
job:

- **Each run is independently retryable.** One date fails; you fix it
  and re-run that date.
- **Each run has its own staging location**, so they cannot interfere.
- **The cost is bounded.** One date at a time, with a pause between.
- **You can stop.** A single job over 90 days has to be cancelled
  from the start.

The disadvantage is 90 job submissions, 90 staging locations, and 90
sets of logs. For a small number of dates that is fine; for 900 dates
you want a driver script that manages the loop, handles failures, and
records the results.

### The design test

Here is the question to ask about any batch pipeline, and it is the
question this chapter has been answering:

> **Could you run this pipeline for a date from three months ago,
> right now, without changing a single line of code?**

If the answer is no, the pipeline is not backfillable, and you have a
choice: refactor it so that it is, or accept that every backfill is a
manual, error-prone, bespoke operation.

The things that make the answer "no" are always the same:

- A hard-coded input path.
- A hard-coded output path.
- A date read from the clock inside the logic.
- A lookup table read at run time rather than pinned per run.
- A status filter baked into the code rather than a parameter.

All five are in the course project today, in one form or another. The
exercises at the end of this chapter are about fixing them.

---

## 🛠️ Hands-On

### Setup

```bash
cd data-engineering/data-Course/google/Dataflow
source .venv/bin/activate
python resources/sample_data.py --output-dir ./sample_data
```

### Step 1 — the design test: can you backfill without changing code?

Let us start by checking the current state of the project.

```bash
grep -n "add_argument" project/batch_pipeline.py
```

Expected:

```text
202:    parser.add_argument("--input", default=DEFAULT_INPUT, help="Input CSV path")
203:    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output path prefix")
...
221:    parser.add_argument("--staging_location", default=None, help="Dataflow staging path")
222:    parser.add_argument("--temp_location", default=None, help="Dataflow temp path")
```

Two observations:

- **`--input` and `--output` have defaults.** A backfill that forgets
  one of them silently reads or writes the wrong place.
- **There is no `--data_date`.** So the output path cannot be
  partitioned by data date, and there is no way to express "this run
  is for 2026-01-10" other than by hand-editing the path.

The flex template is better — `--input` and `--output` are both
`required=True` — but it also has no `--data_date`.

### Step 2 — build the parameterised pipeline

Let us fix it. Create `hands_on_backfill.py`:

```python
"""Parameterise the pipeline by data date and run a backfill."""
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
LIVE_PREFIX = "./out/hands_on/backfill/live"
BACKFILL_PREFIX = "./out/hands_on/backfill/backfill"


def build(output_prefix, data_date):
    """Build and run the summary for one data date.

    Args:
        output_prefix: Where to write the output.
        data_date: The date the data is about, as YYYY-MM-DD.

    Returns:
        Nothing.
    """
    output_path = os.path.join(output_prefix, f"dt={data_date}")
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


def show(root):
    """Print every output file and its contents.

    Args:
        root: The root directory to walk.

    Returns:
        Nothing.
    """
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in sorted(filenames):
            path = os.path.join(dirpath, name)
            print(" ", path)
            with open(path, encoding="utf-8") as handle:
                for line in handle:
                    print("     ", line.rstrip())


def main():
    """Run the live job and then a backfill into a different prefix.

    Returns:
        Nothing.
    """
    shutil.rmtree(os.path.dirname(LIVE_PREFIX), ignore_errors=True)

    # The live job, for today's data.
    build(LIVE_PREFIX, "2026-01-15")

    # Two backfill dates, into a *different* prefix.
    build(BACKFILL_PREFIX, "2026-01-10")
    build(BACKFILL_PREFIX, "2026-01-11")

    print("live prefix:")
    show(LIVE_PREFIX)
    print("backfill prefix:")
    show(BACKFILL_PREFIX)


if __name__ == "__main__":
    main()
```

Run it:

```bash
python hands_on_backfill.py
```

Expected:

```text
live prefix:
  ./out/hands_on/backfill/live/dt=2026-01-15
      region,order_count,revenue_eur
      AMER,318,113592.19
      APAC,285,108194.92
      EMEA,322,118423.22
      LATAM,320,110646.18
backfill prefix:
  ./out/hands_on/backfill/backfill/dt=2026-01-10
      region,order_count,revenue_eur
      AMER,318,113592.19
      APAC,285,108194.92
      EMEA,322,118423.22
      LATAM,320,110646.18
  ./out/hands_on/backfill/backfill/dt=2026-01-11
      region,order_count,revenue_eur
      LATAM,320,110646.18
      AMER,318,113592.19
      APAC,285,108194.92
      EMEA,322,118423.22
```

The tree now looks like this:

```text
out/hands_on/backfill/
├── backfill/
│   ├── dt=2026-01-10
│   └── dt=2026-01-11
└── live/
    └── dt=2026-01-15
```

Three separate partitions, in two separate prefixes. The backfill
wrote only to `backfill/`, and only to the two dates it was asked
for. The live partition was not touched.

Note that the numbers are identical across all three dates, because
we are reading the same input file each time. That is fine for the
demonstration — the point is the *paths*, not the values.

And note the row order differs between the two backfill partitions —
and between runs of the same script. `CombinePerKey` gives no ordering
guarantee, as always. If you need a stable order, sort the output
explicitly; never let a test depend on the order the runner happened to
produce.

### Step 3 — the trap: a backfill into the live prefix

Now let us reproduce the incident. What happens if the backfill writes
to the same prefix as the live job?

Create `hands_on_shared_prefix.py`:

```python
"""Show what a backfill into the live prefix does."""
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
SHARED_PREFIX = "./out/hands_on/shared/summary"


def build(data_date, statuses):
    """Build and run the summary for one data date.

    Args:
        data_date: The date the data is about, as YYYY-MM-DD.
        statuses: The statuses to include.

    Returns:
        Nothing.
    """
    output_path = os.path.join(SHARED_PREFIX, f"dt={data_date}")
    with beam.Pipeline() as pipeline:
        orders = (
            pipeline
            | "ReadOrders" >> beam.io.ReadFromText(INPUT)
            | "ParseOrders" >> beam.ParDo(ParseOrderFn())
        )
        summary = (
            orders
            | "KeepStatuses" >> beam.Filter(lambda o: o["status"] in statuses)
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


def show():
    """Print every output file and its contents.

    The output may be a directory (when the date partition is in the
    path) or a single file (when it is not), so handle both.

    Returns:
        Nothing.
    """
    if os.path.isfile(SHARED_PREFIX):
        paths = [SHARED_PREFIX]
    else:
        paths = []
        for dirpath, _dirnames, filenames in os.walk(SHARED_PREFIX):
            for name in sorted(filenames):
                paths.append(os.path.join(dirpath, name))

    for path in sorted(paths):
        print(" ", path)
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                print("     ", line.rstrip())


def main():
    """Run a live job, then a backfill, and show the result.

    Returns:
        Nothing.
    """
    shutil.rmtree(os.path.dirname(SHARED_PREFIX), ignore_errors=True)

    # The live job: complete orders only.
    build("2026-01-15", ("complete",))
    print("after the live job:")
    show()

    # A backfill for an earlier date, with a DIFFERENT filter.
    # It writes to the same shared prefix.
    build("2026-01-10", ("complete", "active"))
    print()
    print("after the backfill:")
    show()


if __name__ == "__main__":
    main()
```

Run it:

```bash
python hands_on_shared_prefix.py
```

Expected:

```text
after the live job:
  ./out/hands_on/shared/summary/dt=2026-01-15
      region,order_count,revenue_eur
      AMER,318,113592.19
      APAC,285,108194.92
      EMEA,322,118423.22
      LATAM,320,110646.18

after the backfill:
  ./out/hands_on/shared/summary/dt=2026-01-10
      region,order_count,revenue_eur
      EMEA,608,215970.2
      APAC,598,225810.57
      LATAM,667,237869.33
      AMER,634,222386.3
  ./out/hands_on/shared/summary/dt=2026-01-15
      region,order_count,revenue_eur
      AMER,318,113592.19
      APAC,285,108194.92
      EMEA,322,118423.22
      LATAM,320,110646.18
```

**With the date in the path, the backfill did no damage.** It wrote to
`dt=2026-01-10` and left `dt=2026-01-15` alone. That is the defence
working.

Now let us remove the defence and see the incident. Change the
output path to drop the date partition:

```python
output_path = SHARED_PREFIX
```

and re-run. Now both runs write to `summary/`, and `FileBasedSink`
deletes the previous output before writing the new one:

```text
after the live job:
  ./out/hands_on/shared/summary
      region,order_count,revenue_eur
      AMER,318,113592.19
      APAC,285,108194.92
      EMEA,322,118423.22
      LATAM,320,110646.18

after the backfill:
  ./out/hands_on/shared/summary
      region,order_count,revenue_eur
      APAC,598,225810.57
      LATAM,667,237869.33
      AMER,634,222386.3
      EMEA,608,215970.2
```

**The live job's output is gone.** The backfill's numbers — which
include `active` orders, because the backfill used a different
filter — now sit where 2026-01-15's revenue should be. The dashboard
for 2026-01-15 shows the backfill's data, and there is no trace of
what was overwritten.

That is the incident, in full: no error, no failed job, no alert. Just
a wrong number on a dashboard, discovered weeks later, with no way to
know what it should have been.

Let us also check the BigQuery variant of the same mistake. With
`WRITE_APPEND` and no date partition in the table:

```text
after the live job:   4 rows
after the backfill:   8 rows
```

Eight rows in a table that should have four, with no column
distinguishing which four are January 15th and which are January
10th. With `WRITE_TRUNCATE`, you get four rows — the backfill's —
and the live data is destroyed.

### Step 4 — the correct way: derive every path from one parameter

Let us build the version that makes the mistake impossible.

Create `hands_on_parameterised.py`:

```python
"""Derive every path from one data_date parameter."""
import os
import shutil
import sys
from datetime import datetime, timezone

sys.path.insert(0, "project")

import apache_beam as beam

from transforms import (
    ParseOrderFn,
    RevenueByRegionFn,
    format_summary_csv,
    to_summary_row,
)

INPUT = "./sample_data/orders.csv"
ROOT = "./out/hands_on/parameterised"


def paths_for(data_date, mode="live"):
    """Return every path for a run, derived from the data date.

    Args:
        data_date: The date the data is about, as YYYY-MM-DD.
        mode: Either "live" or "backfill".

    Returns:
        A dict with the input path, the output path, the staging
        location and the temp location.
    """
    if mode == "backfill":
        output_root = os.path.join(ROOT, "summary_backfill")
    else:
        output_root = os.path.join(ROOT, "summary")

    run_id = f"{mode}-{data_date}"
    return {
        "input_path": INPUT,
        "output_path": os.path.join(output_root, f"dt={data_date}"),
        "staging_location": os.path.join(ROOT, "staging", run_id),
        "temp_location": os.path.join(ROOT, "temp", run_id),
        "job_name": f"revenue-summary-{run_id}",
    }


def build(paths):
    """Build and run the summary with the given paths.

    Args:
        paths: A dict of paths, as returned by `paths_for`.

    Returns:
        Nothing.
    """
    with beam.Pipeline() as pipeline:
        orders = (
            pipeline
            | "ReadOrders" >> beam.io.ReadFromText(paths["input_path"])
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
            paths["output_path"],
            header="region,order_count,revenue_eur",
            num_shards=1,
            shard_name_template="",
        )


def main():
    """Run a live job and two backfills, and print the path plan.

    Returns:
        Nothing.
    """
    shutil.rmtree(ROOT, ignore_errors=True)

    print("live run for 2026-01-15:")
    live = paths_for("2026-01-15")
    for key, value in sorted(live.items()):
        print(f"  {key}: {value}")
    build(live)

    print()
    print("backfill for 2026-01-10:")
    backfill = paths_for("2026-01-10", mode="backfill")
    for key, value in sorted(backfill.items()):
        print(f"  {key}: {value}")
    build(backfill)

    print()
    print("the tree:")
    for dirpath, _dirnames, filenames in os.walk(ROOT):
        for name in sorted(filenames):
            print("  ", os.path.join(dirpath, name))


if __name__ == "__main__":
    main()
```

Run it:

```bash
python hands_on_parameterised.py
```

Expected:

```text
live run for 2026-01-15:
  input_path: ./sample_data/orders.csv
  job_name: revenue-summary-live-2026-01-15
  output_path: ./out/hands_on/parameterised/summary/dt=2026-01-15
  staging_location: ./out/hands_on/parameterised/staging/live-2026-01-15
  temp_location: ./out/hands_on/parameterised/temp/live-2026-01-15

backfill for 2026-01-10:
  input_path: ./sample_data/orders.csv
  job_name: revenue-summary-backfill-2026-01-10
  output_path: ./out/hands_on/parameterised/summary_backfill/dt=2026-01-10
  staging_location: ./out/hands_on/parameterised/staging/backfill-2026-01-10
  temp_location: ./out/hands_on/parameterised/temp/backfill-2026-01-10

the tree:
   ./out/hands_on/parameterised/summary/dt=2026-01-15
   ./out/hands_on/parameterised/summary_backfill/dt=2026-01-10
```

One parameter — `data_date` — and one mode. Everything else is
derived. The operator cannot get the input path and the output path
out of sync, because neither is typed by hand.

Two things to notice in the path plan:

- **The staging and temp locations are unique per run.** They contain
  the mode and the date, so two concurrent runs cannot collide, and a
  retry of the same run reuses the same location — which is what you
  want for checkpoint resumption.
- **The output root differs by mode.** A backfill *cannot* write to
  the live prefix unless somebody changes the code, not just the
  arguments.

### Step 5 — the backfill driver

A 90-day backfill is 90 runs. Let us write the driver.

Create `hands_on_driver.py`:

```python
"""Drive a multi-date backfill, one run at a time."""
import os
import shutil
import subprocess
import sys
from datetime import date, timedelta

ROOT = "./out/hands_on/driver"
SCRIPT = "hands_on_parameterised.py"


def date_range(start, days):
    """Return `days` consecutive dates starting at `start`.

    Args:
        start: The first date.
        days: How many dates to produce.

    Returns:
        A list of date objects.
    """
    return [start + timedelta(days=offset) for offset in range(days)]


def main():
    """Run the backfill for a range of dates and report what happened.

    Returns:
        The process exit code.
    """
    shutil.rmtree(ROOT, ignore_errors=True)

    start = date(2026, 1, 5)
    dates = date_range(start, 5)

    results = []
    for data_date in dates:
        iso = data_date.isoformat()
        output = os.path.join(ROOT, "summary_backfill", f"dt={iso}")

        command = [
            sys.executable,
            SCRIPT,
            "--data_date", iso,
            "--mode", "backfill",
        ]
        print(f"running backfill for {iso} -> {output}")

        # In a real driver this would be a `subprocess.run` against
        # `gcloud dataflow jobs run`, and you would poll the job until
        # it finished before starting the next one.
        results.append((iso, output))

    print()
    print("plan:")
    for iso, output in results:
        print(f"  {iso} -> {output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

For a real backfill against Dataflow, the driver would shell out to
`gcloud`:

```bash
for date in 2026-01-05 2026-01-06 2026-01-07; do
    gcloud dataflow jobs run "revenue-summary-backfill-dt-${date}" \
        --project YOUR_PROJECT_ID \
        --region us-central1 \
        --image gcr.io/YOUR_PROJECT_ID/dataflow/batch-template:latest \
        --temp-location "gs://YOUR_BUCKET/temp/backfill-${date}" \
        --staging-location "gs://YOUR_BUCKET/staging/backfill-${date}" \
        --input "gs://YOUR_BUCKET/orders/dt=${date}/orders.csv" \
        --output "gs://YOUR_BUCKET/summary_backfill/dt=${date}" \
        --data_date "${date}"
done
```

The structure to notice: **one date per invocation, one staging
location per invocation, and the date in the job name.** Every one of
those is a decision that makes a failure recoverable — you re-run one
date, not the whole range.

### Step 6 — add the parameters to the project

Now let us apply the design to the course project.

Add to `project/batch_pipeline.py`:

```python
parser.add_argument(
    "--data_date",
    default=None,
    help="The date the data is about, as YYYY-MM-DD. Used to partition the output.",
)
parser.add_argument(
    "--mode",
    default="live",
    choices=("live", "backfill"),
    help="Which output prefix to write to.",
)
```

And a path helper:

```python
def build_paths(root, data_date, mode="live"):
    """Return every path for a run, derived from the data date.

    Args:
        root: The output root.
        data_date: The date the data is about, as YYYY-MM-DD.
        mode: Either "live" or "backfill".

    Returns:
        A dict with the output path, staging location and temp location.
    """
    if mode == "backfill":
        output_root = f"{root}_backfill"
    else:
        output_root = root

    run_id = f"{mode}-{data_date}"
    return {
        "output_path": os.path.join(output_root, f"dt={data_date}"),
        "staging_location": os.path.join(root, "staging", run_id),
        "temp_location": os.path.join(root, "temp", run_id),
        "job_name": f"revenue-summary-{run_id}",
    }
```

The `choices=("live", "backfill")` on `--mode` is worth the two
seconds it costs: argparse rejects anything else, so a typo cannot
write to an unexpected prefix.

A test for it:

```python
def test_backfill_writes_to_a_different_prefix(tmp_path):
    """A backfill must not be able to write to the live output prefix."""
    from batch_pipeline import build_paths

    root = str(tmp_path / "summary")

    live = build_paths(root, "2026-01-15")
    backfill = build_paths(root, "2026-01-10", mode="backfill")

    assert live["output_path"] != backfill["output_path"]
    assert "2026-01-15" in live["output_path"]
    assert "2026-01-10" in backfill["output_path"]
    assert "backfill" in backfill["output_path"]
    assert live["temp_location"] != backfill["temp_location"]
```

That test is the executable form of the safety checklist. It is short,
it runs in milliseconds, and it will fail the moment somebody
"simplifies" the path logic.

---

## 🛠️ Common Errors and Fixes

### The backfill overwrote the live output

The output path was not partitioned by data date, and the backfill
wrote to the same prefix as the live job.

The immediate fix is to restore the live partition — from the
backups, from the raw input, or by re-running the live job for that
date. The durable fix is the partitioned output path plus a separate
backfill prefix.

### The backfill wrote to the right place but the wrong date

The partition key was derived from the run date rather than the data
date. `dt=2026-10-28` for data from 2026-01-10. See
[chapter 6.3](32-idempotency-and-exactly-once.md).

### `ValueError: Invalid write disposition` after adding a partition decorator

A partition decorator is applied through the BigQuery table's schema,
not through the Beam sink's `write_disposition`. The disposition stays
`WRITE_TRUNCATE`; the decorator selects the partition.

### The backfill job was throttled or preempted

Backfills compete with the live job for workers. Schedule them
off-peak, or split the range into several concurrent runs with
distinct staging locations.

### `RuntimeError: Transform name is already used`

You built the pipeline twice in one process — for example, calling
`build_pipeline` twice inside one `with beam.Pipeline()` block. See
[chapter 2.5](10-filter-and-flatten.md).

### The backfill produced different numbers from the live run for the same date

Almost always one of:

- a different status filter
- a different exchange-rate table
- a different input file (a corrected version of the source)
- code that changed between the live run and the backfill

This is the "reprocess" case, not the "backfill" case, and it is
expected. What matters is that you *know* which of the four it is.

### `gsutil rm -r gs://YOUR_BUCKET/summary/` — you deleted the live data

There is no undo for a recursive delete. The mitigation is versioning
on the bucket (`gsutil versioning set on gs://YOUR_BUCKET`) or
BigQuery time travel, and it is worth enabling both before you need
them.

---

## 💡 Production Notes

### Make the output path required

The flex template already does:

```python
parser.add_argument("--output", required=True, help="Output path prefix")
```

Do the same in the local script. A default output path is a loaded
weapon in the hands of a backfill that forgets its arguments.

### Derive, do not duplicate

Every path should come from one function that takes the data date.
Three arguments that must agree are three chances to disagree.

### Keep a run manifest

Every run — live or backfill — should record: the input path, the
output path, the data date, the mode, the job name, the git commit,
the start and end times, the row counts, and the cost. When someone
asks "why does 2026-01-10 have 457 orders in AMER when every other day
has 318?", the manifest is the answer.

### Schedule backfills

A backfill is a batch of expensive jobs. Run it when the cluster is
quiet, at a rate the service can absorb. The Dataflow job queue
exists for this.

### Budget the backfill before you run it

Estimate the cost from the date count and the cost of one day. If the
number is uncomfortable, reduce the scope — fewer dates, a sample, or
a cheaper pipeline for the backfill than for the live run.

### Use a different, cheaper pipeline for large backfills

The live job may be optimised for latency (many shards, aggressive
windowing). A backfill should be optimised for cost (fewer, larger
shards, no unnecessary fan-out). Running the live configuration over
90 days of data can cost several times what it needs to.

### Enable versioning and time travel

GCS bucket versioning and BigQuery table time travel are the two
cheapest insurance policies in this entire chapter. Both are
retrospective — you cannot enable them after the incident.

### Keep the backfill output separate until it is verified

Do not write a backfill into the live prefix and then "check it
afterwards". Write it to `summary_backfill/`, verify it, and promote
it deliberately.

### Have a rollback plan before you start

What is the exact command that undoes this backfill? If you cannot
write it down in one line before you start, you are not ready to
start.

---

## 🔑 Key Takeaways

1. **A re-run, a backfill and a reprocess are three different
   operations.** Same input/same parameters is a re-run; different
   input is a backfill; same input with different logic is a
   reprocess.
2. **A backfill is the same code plus different parameters.** If it
   needs a code change, it is not a backfill — it is a second
   pipeline, and you now have two to maintain.
3. **Three parameters: input path, output path, and the data date.**
   The first two should be *derived* from the third.
4. **Never hard-code a path.** The course's `batch_pipeline.py` has
   defaults for `--input` and `--output`; the flex template
   correctly makes them `required=True`.
5. **The partition key is the data date, never the run date.**
   `dt=2026-01-10`, not `dt=2026-10-28`.
6. **Partitioning the output by data date is what makes a backfill
   safe.** With `dt=` in the path, the backfill demonstrably left the
   live partition untouched; without it, the live data was destroyed.
7. **A backfill into the live prefix is the classic incident.** With
   `WriteToText` it overwrites; with `WRITE_APPEND` it duplicates;
   with `WRITE_TRUNCATE` it overwrites. All three fail silently.
8. **Use a separate prefix for backfills** (`summary_backfill/`), so
   that a backfill is never live data until it is promoted.
9. **Make the mode an explicit parameter with `choices=`,** so
   argparse rejects anything unexpected.
10. **Unique temp and staging locations per run, stable across
    retries.** Derived from the mode and the date.
11. **The staging location of a failed run is your evidence.** Do not
    share it.
12. **Run a backfill one date per invocation.** Each run is
    independently retryable, individually cancellable, and has its
    own cost.
13. **The `WRITE_TRUNCATE` disposition truncates the whole table.** For
    a table that accumulates across dates, use a partition-scoped
    replace or a `MERGE`.
14. **The design test**: could you run this pipeline for a date from
    three months ago, right now, without changing a single line of
    code? If not, the pipeline is not backfillable.

---

## 📚 Practice Exercises

1. **Add `--data_date` and `--mode` to `project/batch_pipeline.py`.**
   Thread them through `build_pipeline` and use them to build the
   output path, the staging location, the temp location and the job
   name. Add the `build_paths` helper from Step 6.

2. **Make `--input` and `--output` required in
   `project/batch_pipeline.py`.** Remove the defaults, update the
   README and the template invocation examples, and confirm the
   pipeline still runs with explicit arguments.

3. **Write the partition-key test.** Assert that the live and
   backfill output paths differ, that each contains its own data
   date, and that the staging and temp locations differ. Then break
   the implementation deliberately and confirm the test fails.

4. **Add a `--date-range` option.** Accept `--from-date` and
   `--to-date`, validate that the range is well-formed and not
   inverted, and print the list of dates that would be processed
   without running anything. Add a `--dry-run` flag.

5. **Build the BigQuery backfill.** Specify the partitioned table's
   schema, the partition decorator, and the exact `MERGE` statement
   that promotes a backfilled partition into the live table. Prove
   the `MERGE` is idempotent by running it twice.

6. **Write the run manifest.** Add a `--manifest` argument that writes
   a JSON file recording the input path, the output path, the data
   date, the mode, the job name, the git commit, the start and end
   timestamps, the input and output row counts, and the estimated
   cost. Produce one for a backfill run.

7. **Audit the project for backfill blockers.** Find every place the
   pipeline depends on something other than its input and its
   parameters: a default path, a hard-coded date, a lookup table read
   at run time, a status filter baked into the code. For each one,
   decide whether it blocks a backfill and fix it.

8. **Simulate the incident and write the postmortem.** Use Step 3's
   script to destroy the live output, then write the postmortem as if
   you were the on-call engineer: timeline, impact, root cause, and
   the two changes that would have prevented it.

---

## 📖 Further Reading

- Google Cloud Dataflow — running a Dataflow job — https://cloud.google.com/dataflow/docs/guides/launching-a-dataflow-pipeline-job
- Google Cloud Dataflow — flex templates — https://cloud.google.com/dataflow/docs/guides/flex-templates
- Google Cloud Dataflow — template parameters — https://cloud.google.com/dataflow/docs/guides/using-flex-templates#template-parameters
- Google Cloud BigQuery — partition decorators — https://cloud.google.com/bigquery/docs/partitioned-tables#partition-decorators
- Google Cloud BigQuery — `MERGE` statement — https://cloud.google.com/bigquery/docs/reference/standard-sql/dml-syntax#merge_statement
- Google Cloud BigQuery — table time travel — https://cloud.google.com/bigquery/docs/time-travel
- Google Cloud Storage — object versioning — https://cloud.google.com/storage/docs/object-versioning
- Google Cloud Dataflow — cost optimisation for batch jobs — https://cloud.google.com/dataflow/docs/guides/cost-optimization
- Apache Beam programming guide — "Templates" and "Multiple Outputs" — https://beam.apache.org/documentation/programming-guide/
- [Chapter 6.1 — Batch Design Patterns](30-batch-design-patterns.md)
- [Chapter 6.3 — Idempotency & Exactly-Once](32-idempotency-and-exactly-once.md)
- [Chapter 6.4 — Error Handling & DLQ](33-error-handling-and-dlq.md)
- [Chapter 6.6 — Case Study 1 — Template Method](35-case-study-template-method.md)
