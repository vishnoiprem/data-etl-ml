# 8.9 — Troubleshooting & Common Failure Modes

> **Section 8 · Production Operations · Lecture 8.9 · 6:30**

## 🎯 What you will learn

- A systematic triage method that works at 3am, in six steps
- An "error message → real cause" table for the failures that actually happen
- The Dataflow-side failure modes: worker OOM, shuffle spill, the job stuck in `PENDING`, the zombie job
- The local-side failure modes: the wrong virtualenv, the Prism panic, the `+inf` watermark evaluation
- Which log to read, which metric to look at, and which command to run
- A 3am runbook for a failing pipeline
- The discipline of writing the failure down

---

## 🧠 Concept

### The triage method

Debugging a Beam pipeline is hard for one specific reason: **the thing
that failed is not the thing you wrote.** You wrote a Python file. What
failed is a Java process on a worker 30 seconds into a distributed
execution, and the traceback refers to a serialised version of your
`DoFn` running inside a bundle.

That means the instinct to "read the stack trace and fix the line" does
not work directly. You need a **procedure** that reduces the problem
before you diagnose it.

Here is the six-step method. It is ordered by cost, cheapest first, and
it works for local failures and cloud failures alike.

**Step 1 — Reproduce locally on the Direct Runner.**

This is the highest-value step and the most commonly skipped. A Dataflow
job that fails after 40 seconds of staging, 2 minutes of worker startup
and 3 minutes of running can be reproduced in 1.2 seconds on your
laptop, for free, with no credentials.

```bash
python project/batch_pipeline.py \
  --runner BundleBasedDirectRunner \
  --input ./sample_data/orders.csv \
  --output ./out/repro
```

If it fails locally, you have a real stack trace and you skip to step 2.
If it does not fail locally, the bug is in something the local runner
does differently — and the list of what differs is short and worth
knowing: concurrency, ordering, coder inference on workers, IAM, the
filesystem, and the clock.

**Step 2 — Read the actual error.**

Not the summary, not the console message, not what the dashboard
suggests. The *actual* error text, in full, including the exception
type and the chained `Caused by:`. In the Beam UI, the job's error tab
shows the traceback from the worker; in `gcloud`, it is the
`errorMessage` in the job state.

The reason this is step 2 and not step 1 is that most "weird" Beam
failures have a completely different root cause from their message. The
message is a symptom. The table later in this chapter maps the common
messages to their real causes.

**Step 3 — Find the failing stage in the job graph.**

The Dataflow job graph is the single most useful artefact, and it is
under-used. Look at the **Execution Graph** tab. You are looking for:

- The stage where the element count drops to zero unexpectedly.
- The stage with a red border (failed).
- A stage that is much wider or much slower than its neighbours.
- Whether the failure is at the **source** (nothing is read), the
  **middle** (a transform is broken), or the **sink** (the output
  failed).

```bash
# The graph, as text.
gcloud dataflow jobs describe JOB_ID \
  --project YOUR_PROJECT_ID --region us-central1 \
  --format='value(jobGraph)'
```

The shape of the answer narrows the problem enormously. A failure at the
sink is a permissions or schema problem. A failure in the middle is a
data problem. A failure at the source is a path or credential problem.

**Step 4 — Read the worker logs, not the job log.**

The job-level log has the orchestration messages. The *worker* log has
the exception, the bundle that failed, the element that caused it, and
the retry history. On Dataflow, click a stage in the graph and open
**Worker logs** — or use the logging API:

```bash
gcloud logging read \
  'resource.type="dataflow_step" AND labels."dataflow_step_id"="..."' \
  --project YOUR_PROJECT_ID \
  --limit=200 \
  --format='value(timestamp, textPayload)'
```

Locally, the equivalent is the Python traceback on your console, which is
why step 1 is so valuable.

**Step 5 — Look at the metrics.**

Dataflow exposes per-stage metrics that answer "how much data did each
stage see?". A stage that goes from 5,000 elements in to 0 elements out
has a filter that removed everything. A stage that stays at 5,000 but
never terminates is a watermark problem.

```bash
# The current job state and the key metrics.
gcloud dataflow jobs describe JOB_ID \
  --project YOUR_PROJECT_ID --region us-central1 \
  --format='yaml(state, metrics)'
```

The metrics that matter most, in order of diagnostic value:

| Metric | What it tells you |
|---|---|
| Elements out (per stage) | which stage dropped your data |
| Estimated CPU seconds | whether a stage is compute-bound |
| Worker count over time | whether autoscaling is thrashing |
| Shuffle bytes written / read | whether the shuffle is the bottleneck |
| Mean bundle processing time | whether you are hitting a per-bundle timeout |
| `out_of_memory` count | whether workers are dying on memory |
| Duplicate and dropped bytes | whether a sink is rejecting data |

**Step 6 — Reduce to a minimal repro.**

Now, and only now, shrink the problem until the cause is obvious. The
technique is *subtractive*: remove half the input, then half again.

```bash
# Take the first 50 orders.
head -51 sample_data/orders.csv > /tmp/mini.csv

# Run against that.
python project/batch_pipeline.py \
  --input /tmp/mini.csv --output ./out/mini
```

A repro that takes 0.3 seconds and fails every time is worth more than
an hour of bisecting a production dataset. And once you have it, you
can add elements back one at a time until it stops failing — the
failure is the last element you added.

### The "error message → real cause" table

This is the table to memorise. Every entry is a real Beam message.

| Error message | What it really means | The fix |
|---|---|---|
| `RuntimeError: Transform name is already used` | Two transforms in the same pipeline share a label. Beam does not say which. | Rename one. `python resources/audit_course.py` finds it statically. |
| `RuntimeError: Transform name is already used` *after a copy-paste* | You duplicated a whole block of the pipeline, labels included. | Rename the labels in the copied block, or extract the block into a function. |
| `ValueError: accumulation_mode must be provided for non-trivial triggers` | You used `AfterCount`/`AfterWatermark` without saying what happens on refire. | Add `accumulation_mode=AccumulationMode.ACCUMULATING` (or `DISCARDING`). |
| `ValueError: Unsafe trigger: AfterCount(100) may lose data. Reason: MAY_FINISH` | The trigger can fire and then more data can arrive, so Beam cannot prove the result is final. | Set `allowed_lateness=0`, or pass `--allow_unsafe_triggers` if you accept the loss. |
| `AttributeError: module 'apache_beam.transforms.combiners' has no attribute 'Sum'` | There is no `combiners.Sum`. | `beam.CombinePerKey(sum)`. |
| `AttributeError: 'PipelineOptions' object has no attribute 'region'` | `region` is a Dataflow-only option; the base class does not declare it. | `options.view_as(DataflowOptions).region = "us-central1"`, or use `build_options` from the course project. |
| `panic in ElementManager.Bundles watermark evaluation goroutine` | The Prism (Go) runner and `AfterWatermark` do not mix; Prism panics on the `+inf` watermark evaluation. | Use `--runner BundleBasedDirectRunner` for anything with triggers. |
| `TypeError: unhashable type: 'dict'` | You keyed by a dict or a list. Beam needs a hashable key. | Key by a tuple: `(row["region"], row["customer_id"])`. |
| `ModuleNotFoundError: No module named 'apache_beam'` | The wrong virtualenv, or the package is not installed in it. | `which python`; `pip show apache-beam`; `source .venv/bin/activate`. |
| `DefaultCredentialsError: Could not automatically determine credentials` | You ran a `DataflowRunner` job with no application default credentials. | `gcloud auth application-default login`, or use the Direct Runner. |
| `google.api_core.exceptions.Forbidden: 403 ... storage.objects.get` | The Dataflow service agent (or the worker SA) cannot read the object. | Grant `roles/storage.objectViewer` on the bucket. If it is the service agent, remove and re-add it so the cached policy refreshes. |
| `ValueError: ... staging location ... already exists` | Two concurrent jobs share a staging location. | Give every job its own staging and temp prefix. |
| The job succeeds and the output has **0 rows** | A filter removed everything, then `CombinePerKey` over an empty PCollection produced nothing. Beam does not error on an empty PCollection. | Count at each stage while debugging. Check the filter predicate against the actual values. |
| The job **hangs** with no output | A streaming job waiting on a watermark that never advances. | Check the source is producing data, and that `allowed_lateness` is not larger than the gap between events. |
| `KeyError: 'order_id'` | A malformed row reached a `DoFn` that assumed the field exists. | Validate before you access, or use `row.get(...)`. |
| `ValueError: unknown currency: 'CHF'` | The currency is not in the rate table. | Add it to `CURRENCY_TO_EUR` — and update every expected number downstream. |
| `AssertionError` in a test, `[] != [...]` | Ordering difference, or a `WindowedValue` wrapper not unwrapped. | Sort before comparing; unwrap `.value` when `use_global_window=False`. |
| `OSError: [Errno 28] No space left on device` | The local disk filled, usually from a runaway output directory. | Clean `./out/`; check the disk. |
| `TypeError: cannot pickle '_thread.lock' object` | A `DoFn` captured an unpicklable object (a lock, a connection, a session). | Move the setup into `setup()`, which runs per worker. |
| `TypeError: f() got an unexpected keyword argument 'window'` | You passed a `DoFn` parameter as a `DoFn` constructor argument. | `DoFn` parameters (`window`, `timestamp`, `element`) are declared as method parameters, not constructor arguments. |

Two entries deserve a note.

The **staging collision** deserves more attention than it gets, because
the error message is about staging and the real cause is concurrency.
Dataflow's default staging location is shared by every job in a region.
When two jobs start at once — which is exactly what a nightly schedule
does when the previous run is still going — they collide. The fix is
one line per job, and it should never be skipped:

```text
--staging-location gs://YOUR_BUCKET/staging/JOB_NAME
--temp-location gs://YOUR_BUCKET/temp/JOB_NAME
```

The **"output has 0 rows"** case deserves attention because it is the
most common "silent" failure. Beam does not consider an empty PCollection
an error, and `CombinePerKey` over an empty input produces no output and
no warning. A pipeline that filters everything away looks exactly like a
pipeline that succeeded. Two defences:

1. **Assert on a count during development.**
2. **Alert on output count in production**, not just on job state. A
   successful job that produced nothing is a failure, and the job state
   will not tell you.

### The Dataflow-side failure modes

**Worker out of memory.**

The symptom is a stage that repeatedly restarts, with
`out_of_memory` counts climbing and the job eventually failing with
`Job exceeded maximum number of retries`. The cause is almost always a
combiner's accumulator that grows with the group (a `GroupByKey` in
disguise) or a hot key concentrating work on one worker.

The fixes, in order:

1. Replace `GroupByKey` with `CombinePerKey` and a constant-size
   accumulator.
2. Split the hot key before the shuffle (a hot-key splitter), and
   re-merge after.
3. Give the workers more memory: a larger machine type, or
   `--worker_disk_type` with enough space for the shuffle to spill.

**The shuffle spilling to disk.**

When a group does not fit in a worker's memory, Beam spills it to the
temp location. This is not a failure — it is the design working. But it
is slow, and it is a symptom that the accumulator is too big or the
machine is too small. Watch the shuffle bytes metrics: if shuffle write
traffic is an order of magnitude larger than your input, your
aggregation is buffering.

**The job stuck in `PENDING`.**

Almost always an IAM or network problem, not a pipeline problem. The job
cannot start because it cannot create workers. Check, in order:

```bash
# 1. The service agent exists for this region?
gcloud beta services identity create --service=dataflow.engine \
  --project YOUR_PROJECT_ID

# 2. Does the service agent have the storage role?
gcloud projects get-iam-policy YOUR_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:service-*@gcp-sa-dataflow.iam.gserviceaccount.com" \
  --format='table(bindings.role, bindings.members)'

# 3. Does the service agent have compute permissions in the region?
gcloud projects get-iam-policy YOUR_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:service-*@gcp-sa-dataflow.iam.gserviceaccount.com" \
  --format='value(bindings.role)'
```

A `PENDING` job that sits for more than two minutes is a PENDING job
that will never start. Cancel it and fix the IAM, rather than waiting.

**The streaming job whose workers are running but the sink is failing.**

The source and the transforms are fine; the output is broken. The job
stays in `RUNNING` and the data piles up. Symptoms: the lag metric
grows, the sink's error count grows, and the workers look busy. The
causes:

- **Sink permissions.** The worker SA cannot write to the output bucket
  or the BigQuery table.
- **Schema mismatch.** The rows do not match the BigQuery table's
  schema. Look for `Could not parse ... as ...` in the worker log.
- **Quota.** A BigQuery or Pub/Sub quota was hit, and the sink is
  retrying against a wall.

The distinguishing signal is in the stage metrics: if the input stage's
output count is growing and the sink stage's is not, the sink is the
problem.

**The "zombie" job.**

A job in `RUNNING` state that is doing nothing — no workers, no
progress, no metrics changing. This happens when the control plane
loses track of the workers (a transient control-plane failure, a
network partition between the worker and the control plane, or a
worker that hung on an uninterruptible I/O).

The distinguishing test: is the job's *state* `RUNNING` while its
**worker count is zero**? If yes, it is a zombie. The fix is to cancel
and re-run. There is no way to revive it, and waiting does not help.

### The local-side failure modes

**The wrong virtualenv.** The most common local failure by a wide
margin, and the one that produces the most confusing symptoms — because
the command works in the course's venv and fails in yours, or because
you have `apache-beam` from a different version.

```bash
which python
python -c "import apache_beam; print(apache_beam.__version__)"
pip show apache-beam
```

If `python -c "import apache_beam"` fails, you are in the wrong
environment. If it prints a version other than 2.77, you have a version
conflict — and Beam has had breaking changes between minor versions
(most notably the `GroupByKey` → `CombinePerKey` guidance and the
`AfterWatermark` lateness rules).

**The Prism panic.** Beam 2.60+ ships a Go-based runner under the plain
name `DirectRunner` (the "Prism" runner). It is genuinely faster —
often 2–3× — but it does not implement every trigger, and it **panics**
on the `AfterWatermark` trigger and on the `+inf` watermark evaluation
that `TestPipeline` performs:

```text
panic in ElementManager.Bundles watermark evaluation goroutine
```

The course's default is `BundleBasedDirectRunner` for exactly this
reason. Use Prism explicitly for the batch pipeline if you want to try
it (`--runner DirectRunner`), and never for anything with triggers.

**The `+inf` watermark evaluation.** This is the Prism panic's cousin
and it shows up in a different form — a test that hangs, or a `TestPipeline`
that never finishes. `TestPipeline` evaluates the watermark at `+inf` to
close every window and collect the output. A runner that does not
implement that path will hang. The fix is the same: use the classic
runner.

**The Direct Runner is not the Dataflow runner.** A list of differences
that matter when a local run passes and a cloud run fails:

| Behaviour | Direct Runner | Dataflow |
|---|---|---|
| Ordering | not guaranteed | not guaranteed |
| Concurrency | single-process, interleaved | many workers |
| Key iteration order | insertion order | arbitrary |
| Coders | inferred locally | inferred, then serialised |
| Filesystem | local | GCS (eventual listing) |
| Time | your machine's clock | the worker's clock |
| IAM | none | everything |
| Network | none | the VPC |

The one that catches people most often is **ordering**. `GroupByKey`
and `CoGroupByKey` produce groups whose *internal* order is not
guaranteed, on any runner, but the Direct Runner often preserves
insertion order, so a bug that depends on order can pass locally and
fail on Dataflow.

### The observability checklist

| Question | Where to look |
|---|---|
| What failed? | Job → **Error** tab, or `gcloud dataflow jobs describe` → `state.errorMessage` |
| Which stage? | Job → **Execution Graph**, red border |
| Why? | Stage → **Worker logs** → search for the exception |
| How much data reached each stage? | Job → **Job metrics** → elements in/out per stage |
| Is it getting slower? | Job → **Time line**, the stage width over time |
| Is it stuck? | Job → **Job metrics** → worker count; a `RUNNING` job with 0 workers is a zombie |
| Who ran it? | `gcloud dataflow jobs describe` → `jobMetadata`; Cloud Audit Logs |
| What did it read and write? | Cloud Audit Logs, GCS data-access logs |
| Is it billing me? | Cloud Billing → Dataflow, filtered by job name |
| Did the code change? | `gcloud dataflow jobs describe` → the image digest in `jobMetadata.sdkVersion`/`environment` |

The single most useful command, and the one to have in your shell
history:

```bash
gcloud dataflow jobs describe JOB_ID \
  --project YOUR_PROJECT_ID \
  --region us-central1 \
  --format='yaml(state, jobMetadata, metrics)'
```

### A 3am runbook

**A batch pipeline failed. It is 03:14. Do this:**

1. **Do not retry yet.** A retry of a job that will fail the same way
   costs money and buys nothing. (A retry *is* right if the failure is
   clearly transient — a worker OOM on a transient spike, or a
   `PENDING` job whose IAM you are about to fix.)

2. **Read the error, in full.** One command:

   ```bash
   gcloud dataflow jobs describe JOB_ID \
     --project YOUR_PROJECT_ID --region us-central1 \
     --format='value(state.errorMessage)'
   ```

3. **Classify it** with the table above:
   - *IAM / 403* → fix the binding, then retry. The data is not the
     problem.
   - *Worker OOM* → the aggregation is buffering. Retry will fail
     again. Escalate to the pipeline owner, or run it with a bigger
     machine as a stopgap.
   - *Malformed data* → the input changed. The pipeline is probably
     right and the upstream is wrong. If you must deliver tonight,
     filter the bad rows, deliver, and raise it in the morning.
   - *Sink failure* → schema or quota. Check the BigQuery schema first;
     a schema change upstream is the most common cause.

4. **Reproduce locally**, if you can get the data:

   ```bash
   head -1001 gs://YOUR_BUCKET/orders.csv > /tmp/repro.csv
   python project/batch_pipeline.py --input /tmp/repro.csv --output ./out/repro
   ```

   A local repro turns a 3am problem into a 10-minute one.

5. **Check whether the previous run succeeded.** If yesterday's worked
   and today's did not, the input changed. Diff the two inputs:

   ```bash
   gcloud storage cp gs://YOUR_BUCKET/orders.csv ./orders.csv
   ```

6. **Deliver a workaround, and write it down.** Options, in order of
   preference: re-run with a corrected input; re-run with a filter
   parameter; run the previous known-good image (the job's
   `environment` block has the image digest); or, as a last resort,
   produce the number by hand from the source data and deliver it with
   an explicit note about how it was produced.

7. **Write the incident down before you go to bed.** Not the full
   post-mortem — a paragraph. What failed, why, what you did, and what
   still needs fixing. This is the difference between an incident and a
   recurring incident.

### The discipline of writing the failure down

This is the habit that separates a team that gets better from a team
that repeats itself.

Every incident gets an entry. Not in a wiki nobody reads — in the
repository, next to the code, in a file like `docs/incidents.md` or a
ticket that links to the failing job. Each entry has five fields:

```text
Date:
Job / pipeline:
Symptom:              (what you saw, verbatim)
Root cause:           (why it actually happened)
Fix:                  (what you did, and what actually fixed it)
Guardrail:            (what will stop it happening again)
```

The **Guardrail** field is the one that matters, and it is the one
people skip. A guardrail is a test, an assertion, an alert, a stricter
IAM binding, a validation step, or a monitoring check that would have
caught this *before* it reached 3am. An incident with no guardrail is an
incident that will happen again, usually within a month, and usually at
a worse time.

The concrete examples:

| Incident | Guardrail |
|---|---|
| Output had 0 rows | Alert on output row count, not just job state |
| Staging collision | Per-job staging prefix, derived from the job name |
| Malformed row killed the bundle | A DLQ output, plus an alert on DLQ volume |
| IAM missing a role | An IaC check that asserts the bindings exist |
| Wrong currency broke the sum | A unit test asserting every currency is in the rate table |
| The job hung for 6 hours | A runtime alert on "no progress for 30 minutes" |

---

## 🛠️ Hands-On: Reproducing Failures on Purpose

The best way to internalise these failure modes is to cause them
deliberately, once, in a safe place.

### Step 1 — Set up a scratch area

```bash
cd data-engineering/data-Course/google/Dataflow
source .venv/bin/activate
python resources/sample_data.py --output-dir ./sample_data
mkdir -p ./out/failures
```

### Step 2 — Duplicate a transform label

The most common error, and the one Beam's message makes hardest to
diagnose. Note that two branches of the same pipeline both use the label
`"ReadOrders"`:

```text
  import apache_beam as beam

  with beam.Pipeline() as p:
      (
          p
          | "ReadOrders" >> beam.io.ReadFromText("./sample_data/orders.csv")
          | "ParseOrders" >> beam.Map(lambda line: line.split(","))
      )
      (
          p
          | "ReadOrders" >> beam.io.ReadFromText("./sample_data/events.csv")
          | "ParseEvents" >> beam.Map(lambda line: line.split(","))
      )
```

Run it — this is deliberately not a `python` fence, because the duplicate
label is exactly what the course linter flags statically, and because the
point of the exercise is the *runtime* error:

```bash
python -c "
import apache_beam as beam
with beam.Pipeline() as p:
    (
        p
        | 'ReadOrders' >> beam.io.ReadFromText('./sample_data/orders.csv')
        | 'ParseOrders' >> beam.Map(lambda line: line.split(','))
    )
    (
        p
        | 'ReadOrders' >> beam.io.ReadFromText('./sample_data/events.csv')
        | 'ParseEvents' >> beam.Map(lambda line: line.split(','))
    )
"
```

Expected:

```text
RuntimeError: Transform name is already used: ReadOrders
```

Note that the message names the label, but not the *two* transforms that
share it, and not the line numbers. Find it statically:

```bash
python resources/audit_course.py
```

The linter reports the label and the first line it saw it on.

### Step 3 — The empty-output failure

A filter that removes everything, and a `CombinePerKey` over nothing:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    summary = (
        p
        | "ReadOrders" >> beam.io.ReadFromText("./sample_data/orders.csv")
        | "ParseOrders" >> beam.Map(lambda line: line.split(","))
        | "KeepImpossible" >> beam.Filter(lambda row: row[3] == "ATLANTIS")
        | "KeyByRegion" >> beam.Map(lambda row: (row[3], float(row[7])))
        | "Revenue" >> beam.CombinePerKey(sum)
    )
    summary | "WriteSummary" >> beam.io.WriteToText("./out/failures/empty")
```

Run it. The pipeline **succeeds**. The output file is empty. No warning
is printed. This is the failure that costs the most time in production,
because nothing is broken as far as the runner is concerned.

Now add the defence — count what survived:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    orders = (
        p
        | "ReadOrders" >> beam.io.ReadFromText("./sample_data/orders.csv")
        | "ParseOrders" >> beam.Map(lambda line: line.split(","))
        | "KeepImpossible" >> beam.Filter(lambda row: row[3] == "ATLANTIS")
    )
    orders | "Count" >> beam.combiners.Count.PerKey()
```

`Count.PerKey` on an empty PCollection still produces no output, because
`PerKey` groups by key first. For a total count, use the plain
counter:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    orders = (
        p
        | "ReadOrders" >> beam.io.ReadFromText("./sample_data/orders.csv")
        | "ParseOrders" >> beam.Map(lambda line: line.split(","))
        | "KeepImpossible" >> beam.Filter(lambda row: row[3] == "ATLANTIS")
    )
    orders | "CountTotal" >> beam.combiners.Count.Globally()
```

`Count.Globally()` on an empty PCollection emits `0` — which is exactly
what you want for an alert: zero is a value, and it can trip a
threshold. An empty output cannot.

### Step 4 — The unhashable key

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "ReadOrders" >> beam.io.ReadFromText("./sample_data/orders.csv")
        | "SkipHeader" >> beam.Filter(lambda line: not line.startswith("order_id"))
        | "ParseOrders" >> beam.Map(lambda line: line.split(","))
        | "KeyByDict" >> beam.Map(lambda row: ({"region": row[3]}, float(row[7])))
        | "Revenue" >> beam.CombinePerKey(sum)
    )
```

Expected:

```text
TypeError: unhashable type: 'dict'
```

The fix is a tuple key:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "ReadOrders" >> beam.io.ReadFromText("./sample_data/orders.csv")
        | "SkipHeader" >> beam.Filter(lambda line: not line.startswith("order_id"))
        | "ParseOrders" >> beam.Map(lambda line: line.split(","))
        | "KeyByTuple" >> beam.Map(lambda row: ((row[3],), float(row[7])))
        | "Revenue" >> beam.CombinePerKey(sum)
        | "FlattenKey" >> beam.Map(lambda kv: (kv[0][0], kv[1]))
    )
```

### Step 5 — The trigger without an accumulation mode

```python
import apache_beam as beam
from apache_beam.transforms.trigger import AccumulationMode, AfterCount

with beam.Pipeline() as p:
    (
        p
        | "ReadOrders" >> beam.io.ReadFromText("./sample_data/orders.csv")
        | "Windowed" >> beam.WindowInto(
            beam.transforms.window.FixedWindows(60),
            trigger=AfterCount(2),
        )
    )
```

Expected:

```text
ValueError: accumulation_mode must be provided for non-trivial triggers
```

The fix:

```python
import apache_beam as beam
from apache_beam.transforms.trigger import AccumulationMode, AfterCount

with beam.Pipeline() as p:
    (
        p
        | "ReadOrders" >> beam.io.ReadFromText("./sample_data/orders.csv")
        | "Windowed" >> beam.WindowInto(
            beam.transforms.window.FixedWindows(60),
            trigger=AfterCount(2),
            accumulation_mode=AccumulationMode.ACCUMULATING,
        )
    )
```

### Step 6 — The Prism panic

```bash
python project/streaming_pipeline.py \
  --runner DirectRunner \
  --input ./sample_data/events.ndjson \
  --output ./out/failures/prism
```

Expected: a Go panic mentioning
`ElementManager.Bundles watermark evaluation goroutine`.

The fix is the classic runner:

```bash
python project/streaming_pipeline.py \
  --runner BundleBasedDirectRunner \
  --input ./sample_data/events.ndjson \
  --output ./out/failures/classic
```

This is the single most valuable 30 seconds in the whole course if you
intend to work on Beam: it teaches you that "the runner" is a choice,
not a constant, and that a runner can be fast and still wrong for your
problem.

### Step 7 — The malformed row

The sample data ships a deliberately broken file:

```bash
head -5 sample_data/malformed_orders.csv
```

Run the pipeline against it and watch the warning:

```bash
python project/batch_pipeline.py \
  --input ./sample_data/malformed_orders.csv \
  --output ./out/failures/malformed 2>&1 | grep -i "skipping" | head -5
```

The pipeline does not fail. The rows are logged and dropped. That is the
course's chosen behaviour, and it is also why chapter 8.7 lists the
dead-letter path as the most important production gap to close.

### Step 8 — Build a minimal repro, deliberately

The technique from step 6 of the triage method, as a script. Note that
the malformed file from step 7 does **not** make the pipeline fail — the
rows are dropped — so a bisector has to look for a different symptom. The
one used here is "the pipeline exits non-zero", and the script narrows
the input until that stops happening:

```bash
# Bisect: find the smallest prefix that still fails.
python -c "
import subprocess, sys

def run(path):
    result = subprocess.run(
        [sys.executable, 'project/batch_pipeline.py',
         '--input', path, '--output', './out/failures/bisect'],
        capture_output=True, text=True,
    )
    return result.returncode

lines = open('sample_data/orders.csv').read().splitlines()
print('header:', lines[0][:60])

for n in (1, 2, 5, 10, 25, 50):
    subset = lines[: n + 1]
    with open('/tmp/bisect.csv', 'w') as f:
        f.write('\n'.join(subset) + '\n')
    code = run('/tmp/bisect.csv')
    print(f'{n:3d} rows -> exit {code}')
"
```

Expected: every prefix exits `0`, because a truncated orders file is
still a valid orders file. That is the *correct* result, and it is worth
internalising: **a bisector only helps if the failure is deterministic.**
If a prefix of the data reproduces the failure but a larger prefix does
not, you have a different problem — an intermittent one — and bisecting
will mislead you.

To see the bisector actually narrow something, point it at a pipeline
that is genuinely strict. The course's `ParseOrderFn` is deliberately
tolerant — it drops bad rows rather than failing the bundle — so
corrupting a row in `orders.csv` changes nothing: the exit code stays
`0` at every prefix, because every corrupted row is skipped and logged.

That is the lesson, and it is worth stating plainly: **a bisector tells
you which symptom you are chasing, not which code path is guilty.** The
course pipeline is tolerant by design, and chapter 8.7 names the
dead-letter path as the production gap that closes.

To get a bisector that narrows, run the same input through a strict
parser that raises instead of skipping — the same `parse_order_line`
the course exposes for exactly this purpose:

```bash
python -c "
import subprocess, sys

SCRIPT = '''
import sys
sys.path.insert(0, \"project\")
import apache_beam as beam
from transforms import parse_order_line

with beam.Pipeline() as p:
    (
        p
        | \"ReadOrders\" >> beam.io.ReadFromText(sys.argv[1])
        | \"SkipHeader\" >> beam.Filter(
            lambda line: not line.startswith(\"order_id\")
        )
        | \"ParseOrders\" >> beam.Map(parse_order_line)
    )
'''

def run(path):
    result = subprocess.run(
        [sys.executable, '-c', SCRIPT, path],
        capture_output=True, text=True,
    )
    return result.returncode

lines = open('sample_data/orders.csv').read().splitlines()
# Corrupt exactly one row: remove its amount column.
parts = lines[7].split(',')
del parts[7]
lines[7] = ','.join(parts)

for n in (5, 8, 10, 25, 50):
    subset = lines[: n + 1]
    with open('/tmp/bisect.csv', 'w') as f:
        f.write('\n'.join(subset) + '\n')
    code = run('/tmp/bisect.csv')
    print(f'{n:3d} rows -> exit {code}')
"
```

Expected: exit `0` for prefixes that stop before the corrupted row, and
exit `1` for prefixes that include it — the corrupted line is line 7,
so the smallest failing prefix is 8 lines.

The point is not the output. The point is that a bisecting script turns
"the pipeline failed" into "this one row, in this one file, is the
problem" — in a few seconds instead of an hour of guessing.

### Step 9 — Write the failure down

The five-field entry, filled in for real:

```text
Date: 2026-10-28
Job / pipeline: project/batch_pipeline.py, local run
Symptom:  Pipeline exited 0 but the output file contained only a header.
Root cause: The status filter used "Complete" (capital C) while the
             data uses "complete", so every order was filtered out.
             The empty PCollection was not an error.
Fix:  Corrected the case in the filter predicate. Output now has 4 regions
      and 1,245 orders.
Guardrail:  Added a unit test asserting build_revenue_summary over the
            sample data returns 4 regions and 1,245 orders, so a filter
            that removes everything fails a test rather than an
            overnight run.
```

The guardrail is the point. A test that asserts the *expected output
count* catches this class of bug before it reaches production.

---

## 🛠️ Common Errors and Fixes

### `RuntimeError: Transform name is already used: <Label>`

Two transforms in the same pipeline share a label. Beam names the
colliding label but not the two transforms. Find it statically:

```bash
python resources/audit_course.py
```

The linter reports the label and the first line it appeared on.

### `ValueError: accumulation_mode must be provided for non-trivial triggers`

You used a non-default trigger without saying what happens on refire:

```python
trigger=AfterCount(2),
accumulation_mode=AccumulationMode.ACCUMULATING,
```

### `ValueError: Unsafe trigger: AfterCount(100) may lose data. Reason: MAY_FINISH`

The trigger can fire and then more data can arrive for the window, so
Beam cannot prove the result is final. Set `allowed_lateness=0`, or pass
`--allow_unsafe_triggers` and accept the loss.

### `AttributeError: module 'apache_beam.transforms.combiners' has no attribute 'Sum'`

There is no `combiners.Sum`. Use the Python builtin:

```python
beam.CombinePerKey(sum)
```

### `AttributeError: 'PipelineOptions' object has no attribute 'region'`

`region` is declared on `DataflowOptions`, not on the base
`PipelineOptions`:

```python
from apache_beam.options.pipeline_options import DataflowOptions, PipelineOptions

options = PipelineOptions(["--runner", "DataflowRunner"])
dataflow_options = options.view_as(DataflowOptions)
dataflow_options.region = "us-central1"
```

The course's `beam_options.build_options` does this safely — it sets
each attribute only on the subclass that declares it, and logs a
warning when the runner does not support it.

### `panic in ElementManager.Bundles watermark evaluation goroutine`

The Prism (Go) runner and `AfterWatermark` do not mix. Use
`--runner BundleBasedDirectRunner` for anything with triggers or
windowing.

### `TypeError: unhashable type: 'dict'`

The key you grouped by is a dict or a list. Use a tuple:

```python
beam.Map(lambda row: ((row["region"], row["customer_id"]), row["amount"]))
```

### `ModuleNotFoundError: No module named 'apache_beam'`

The wrong virtualenv, or the package is not installed in it:

```bash
which python
python -c "import apache_beam; print(apache_beam.__version__)"
```

### `DefaultCredentialsError: Could not automatically determine credentials`

You ran a `DataflowRunner` job without application default credentials:

```bash
gcloud auth application-default login
```

Or you meant to run locally — use `--runner BundleBasedDirectRunner`.

### `google.api_core.exceptions.Forbidden: 403 GET ... storage.objects.get`

The identity lacked read access. Two things to check:

1. **Which identity?** The message names it. The Dataflow service agent
   needs `roles/storage.objectAdmin` (or object-level equivalents); the
   worker SA needs `roles/storage.objectViewer` on the specific bucket.
2. **If it is the service agent and the role was added after creation**,
   the policy is cached. Remove the service agent and re-add it:

   ```bash
   gcloud beta services identity delete --service=dataflow.engine --project YOUR_PROJECT_ID
   gcloud beta services identity create --service=dataflow.engine --project YOUR_PROJECT_ID
   ```

### The job is stuck in `PENDING`

The service agent cannot create workers. Check that it exists for the
region, and that it has `roles/dataflow.serviceAgent` and
`roles/compute.instanceAdmin.v1` (or the equivalent) in that region. A
`PENDING` job that has been pending for more than two minutes will not
start — cancel it, fix the IAM, and re-run.

### The output has 0 rows and the job succeeded

A filter removed everything. Count with `beam.combiners.Count.Globally()`,
which emits `0` for an empty PCollection, and alert on it.

### The job hangs with no output

A streaming job waiting on a watermark that never advances. Check that
the source is producing data, and that `allowed_lateness` is not larger
than the gap between your events. On a bounded source with the classic
runner, the watermark advances to `+inf` at the end and every window
closes — so a hang usually means the source is still open.

### `AssertionError` in a test, but the pipeline output looks right

Either an ordering difference or a `WindowedValue` wrapper. With
`use_global_window=False`, the elements are `WindowedValue` objects:

```python
def _compare(actual):
    unwrapped = [item.value if hasattr(item, "value") else item for item in actual]
    return sorted(unwrapped) == sorted(expected)
```

### `OSError: [Errno 28] No space left on device`

The local disk is full, usually from accumulated output. Check and
clean:

```bash
df -h .
du -sh out/ 2>/dev/null
rm -rf out/failures
```

---

## 💡 Production Notes

- **Reproduce locally first, always.** A cloud failure that takes 5
  minutes to reproduce can be reproduced in 1.2 seconds on your laptop,
  for free, with the full stack trace. The only thing local cannot
  reproduce is the parts that are genuinely cloud — IAM, the filesystem,
  the network, the clock.
- **The job graph is the fastest diagnostic tool you have.** Finding the
  failing stage takes 20 seconds and usually tells you whether the
  problem is at the source, the middle, or the sink — which is most of
  the diagnosis.
- **A successful job that produced no data is a failure.** The job state
  will not tell you. Alert on the output row count.
- **Never retry a deterministic failure.** A retry of a job that will
  fail identically costs money and delays the real fix. Classify first:
  IAM and quota failures are retryable after a fix; data and schema
  failures are not retryable without a change.
- **Give every job its own staging and temp prefix.** The default is
  shared, and two concurrent jobs will collide. This is the most common
  cause of a job that fails only when it is launched on a schedule.
- **A `RUNNING` job with zero workers is a zombie.** Cancel it and
  re-run. There is no way to revive it and waiting does not help.
- **The Direct Runner and Dataflow differ in ways that matter.** The
  ones that bite: ordering, concurrency, coder inference, the
  filesystem, the clock, and IAM. A local pass is evidence, not proof.
- **Watch the accumulator size, not just the input size.** A job that
  used 2 GB last week and uses 40 GB this week has a growing
  accumulator, and it will OOM before it fails on the hot key.
- **Put the DLQ volume on a dashboard.** The proportion of records
  failing to parse is a leading indicator of an upstream schema change,
  and it is visible days before the pipeline actually breaks.
- **Write the incident down, with a guardrail.** An incident without a
  guardrail is a scheduled incident. The guardrail is a test, an alert,
  an assertion, or a stricter binding — something that would have
  caught it before 3am.

---

## 🔑 Key Takeaways

- **Six steps, cheapest first**: reproduce locally → read the actual
  error → find the failing stage → read the worker logs → check the
  metrics → reduce to a minimal repro.
- **The error message is a symptom.** The table of "error → real cause"
  is the most valuable page in this chapter, because most Beam failures
  have a different root cause from their message.
- **`RuntimeError: Transform name is already used`** is a duplicate
  label, and the course linter finds it statically.
- **A successful job with 0 rows** is the most expensive silent failure
  — always count with `beam.combiners.Count.Globally()`, which emits `0`
  rather than nothing.
- **The `PENDING` job and the `RUNNING`-with-no-workers job are both
  dead.** Cancel, fix, re-run. Waiting does not help either.
- **The Prism runner panics on `AfterWatermark` and on `+inf` watermark
  evaluation.** Use `BundleBasedDirectRunner` for anything with
  triggers.
- **The runner is a choice, not a constant.** The Direct Runner and
  Dataflow differ in ordering, concurrency, coders, filesystem, clock
  and IAM — so a local pass is evidence, not proof.
- **The observability checklist tells you which log, which metric and
  which command for each question** — and the job graph answers "which
  stage?" faster than anything else.
- **Every incident gets an entry with a guardrail.** Without one, it is a
  scheduled incident.

---

## 📚 Practice Exercises

1. **Reproduce every error in the table.** Write a script that triggers
   each of the six most common errors in this chapter, one after
   another, capturing the exception type and message. Save it as
   `resources/failure_repros.py`.
   *Expected answer:* six captured exceptions matching the table's
   messages verbatim.

2. **Build a bisector.** Write a script that takes a failing input file
   and finds the smallest subset of lines that still reproduces the
   failure, by halving the file each time.
   *Expected answer:* the script converges in log2(n) runs — 12 runs for
   5,000 lines — and prints the offending line.

3. **Add a zero-row guard to the project.** Modify
   `project/batch_pipeline.py` so that a `--fail-on-empty` flag causes
   the pipeline to raise when the summary is empty, using
   `beam.combiners.Count.Globally()`. Then verify that a filter that
   removes everything trips the guard.
   *Expected answer:* the guard raises a clear error instead of writing
   an empty file and exiting 0.

4. **Compare the runners.** Run the course's batch pipeline on
   `BundleBasedDirectRunner` and on `DirectRunner` (Prism), timing both.
   Then run the streaming pipeline on both.
   *Expected answer:* Prism is 2–3× faster on the batch pipeline and
   panics on the streaming pipeline.

5. **Write the incident template.** Add an `docs/incidents.md` to the
   project with the five-field template, and write a real entry for the
   zero-row failure you reproduce in exercise 3. Include a guardrail
   that is a test.
   *Expected answer:* an entry with all five fields, and a test in
   `project/tests/` that asserts the expected order count.

6. **Write the 3am runbook for your own project.** Take the pipeline you
   work on most, and write the six commands you would run, in order,
   with the classification decision after each. Then time yourself doing
   a dry run of the first three.
   *Expected answer:* the first three commands are reachable in under
   60 seconds, and the fourth (read the worker logs) is a command you
   have run at least once before you need it.

---

## 📖 Further Reading

- Apache Beam's debugging guide — https://beam.apache.org/documentation/basic-topics/debugging/
- Beam's "Tips and Tricks" for debugging pipelines — https://beam.apache.org/documentation/basic-topics/debugging/#debugging-pipelines
- Dataflow job metrics and monitoring — https://cloud.google.com/dataflow/docs/monitoring/overview
- Dataflow job management — https://cloud.google.com/dataflow/docs/guides/managing-jobs
- Dataflow error messages and troubleshooting — https://cloud.google.com/dataflow/docs/guides/Troubleshooting
- Cloud Logging query language — https://cloud.google.com/logging/docs/view/query
- Beam's `DoFn` documentation — https://beam.apache.org/documentation/sdks/python/transforms/python/do-fn/
- The course FAQ's troubleshooting section — ../resources/FAQ.md
