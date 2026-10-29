# 8.2 — Monitoring & Autoscaling

> **Section 8 · Production Operations · Lecture 8.2 · 6:30**

## 🎯 What you will learn

- What to monitor for a batch job versus a streaming job, and why the two lists barely overlap
- How to read the Dataflow UI's Metrics tab and the job graph's stage heatmap
- The built-in metrics that Dataflow exports, and what each one is good for diagnosing
- How to write custom metrics with `beam.metrics.Metrics` and export them to Cloud Monitoring
- How autoscaling actually works: `Basic` versus `Aggressive` versus `NONE`
- How `--min-workers` and `--max-workers` interact with the autoscaling algorithm
- Why Dataflow does **not** scale a streaming job to zero, and what that costs
- How to tune a batch job's worker count without guessing
- Which alerts are worth having, and which are noise

---

## 🧠 Concept

### Two different jobs, two different monitoring problems

A batch job and a streaming job fail in opposite ways, and this is the fact
that most teams get wrong when they build one dashboard for both.

| | Batch | Streaming |
|---|---|---|
| **The failure mode** | It runs too long, or produces the wrong answer | It falls behind, or stops producing output |
| **The question** | "Is it progressing, and will it finish?" | "Is it keeping up with the input?" |
| **The clock** | Wall time since start | Watermark lag |
| **The output** | A file that either exists or does not | A continuous stream of results |
| **Cost driver** | Workers × duration | Workers × *time alive* |
| **Scaling** | Scales up from the data volume, then down | Scales with the arrival rate, continuously |
| **Idle behaviour** | Job ends, workers die, cost stops | **Workers stay and bill** |

A batch job that takes 40 minutes instead of 8 is a performance problem.
A streaming job that is 40 minutes behind is a **correctness** problem
for anything downstream that expects fresh data — the dashboard shows
stale numbers, and the alerts that fire on those stale numbers fire late.

The monitoring for the two jobs shares almost nothing. That is why
Dataflow's own metric set has a batch group and a streaming group, and
why this chapter splits them.

### What to monitor for a batch job

| Metric | Where | What it tells you | The number to watch |
|---|---|---|---|
| Job state | UI, `gcloud dataflow jobs describe` | Did it succeed, fail, or get cancelled | `JOB_STATE_DONE` / `JOB_STATE_FAILED` |
| Wall time | UI, metrics | How long it took, versus how long it should take | Ratio to the last 7 successful runs |
| `estimated_cpu_seconds` | Metrics tab | The runner's *estimate* of CPU work | Compare with actual — a large gap means the estimate is bad |
| Actual CPU seconds | Billing export | What you were actually billed for | The gap against the estimate |
| Worker count over time | UI, autoscaling graph | Whether the job scaled, and when | Flat at 1 for a whole run means the job is serialised |
| Shuffle bytes | Metrics tab | How much data crossed the network | Should be proportional to the input, not 10× it |
| `beam.io.read.bytes` | Metrics tab | Bytes read from the source | Compare with the source's actual size |
| `beam.io.write.bytes` | Metrics tab | Bytes written to the sink | Should be roughly proportional to the output rows |
| Output row count | The sink's own table | Did the right number of rows land | The single most important correctness check |
| Worker failures | UI, job graph | Retries, and where they happen | Any non-zero count is worth reading about |

The last one deserves emphasis. **The row count at the sink is the only
metric that answers "did the job work"**. Everything else answers "did the
job run". A job that succeeds, reads all the bytes, and writes half the
rows is a silent data-loss incident that no infrastructure metric will
catch. Always compare the sink's row count against the input row count
minus the rows you expected to filter out.

### What to monitor for a streaming job

| Metric | Where | What it tells you | Alarm threshold (typical) |
|---|---|---|---|
| **Watermark lag** | Metrics tab, `watermark_lag` | How far behind real time the pipeline is | Minutes, not hours |
| **Backlog** | UI, worker metrics | Elements waiting to be processed | Growing monotonically is the alarm |
| Output throughput | Metrics tab | Results per second | Zero output while input is flowing is a hard failure |
| Window firing rate | Metrics tab | Windows closed per minute | Should track the window size and input rate |
| DLQ rate | Your own metric | Elements that failed processing | Any sustained rate above 0.1% |
| Input rate | Metrics tab | Elements per second | Compare against output rate |
| Worker churn | UI, autoscaling graph | Workers added/removed repeatedly | Rapid oscillation means thrashing |
| Idleness | UI | Time with no work | A streaming job is never "done" — but it can be starved |

**Watermark lag is the single most important streaming metric.** The
watermark is Beam's estimate of the latest event time it has seen enough
data about. The lag between the watermark and wall-clock time is how far
behind the pipeline is. If the watermark advances at the same rate as the
clock, the pipeline is keeping up. If it stalls, the pipeline is either
starved of input or falling behind.

A useful threshold: if your business tolerance is "data no more than 15
minutes stale", then a watermark lag of 15 minutes is your ceiling, and
you should alert at, say, 10 minutes — before the SLO is breached, not
after.

### The Dataflow UI

The UI at `https://console.cloud.google.com/dataflow` is the primary
operational surface. Four areas matter.

**The job list.** Shows every job, its state, its type (batch/streaming),
and when it was created. A streaming job that is not in this list is not
running; a streaming job that *is* here when you expected it to be gone is
billing you.

**The job graph.** The visual DAG of your pipeline, with each stage
rendered as a box. This is where you answer "where is the time going?".
The boxes are shaded by throughput and by the time spent in that step, and
there is a "heat map" toggle that colours stages by relative cost. A stage
that is a thin sliver is cheap; a stage that is a fat, hot box is where
your time and money are going.

Three readings of the job graph worth memorising:

- **One fat stage, many thin ones** — the pipeline is serialised. A
  `GroupByKey` on a low-cardinality key, or a single-threaded step, is
  the usual cause. You want a wide, even shape.
- **One stage much wider than the others** — the pipeline is fusing
  aggressively, which is good, or it has a single hot key, which is bad.
  Check the skew chapter (8.3).
- **A stage that is wide but takes as long as the narrow ones** — the
  bottleneck is downstream I/O, not compute. You are network-bound.

**The Metrics tab.** A chart per metric, over time, with the job's
timeline underneath. This is where you read `beam.io.read.bytes`,
`beam.io.write.bytes`, `estimated_cpu_seconds`, `total_element_count`,
and the streaming metrics. The autoscaling graph lives here too, showing
the worker count over the life of the job.

**The Worker log / Job log.** Two levels of log. The *job log* is the
driver's log — graph construction, autoscaling decisions, and
requirements. The *worker log* is the user code's log, at whatever level
your code sets. The job log is where you find "why did it request 200
workers" and "the user code threw an exception".

**The Dataflow UI's own metric names.** Dataflow exports its metrics
under the `dataflow.googleapis.com/` metric family, and your custom
metrics land under your own metric family. On the Metrics tab, built-in
metrics use names like:

- `beam.io.read.bytes` — bytes read from the source
- `beam.io.write.bytes` — bytes written to the sink
- `estimated_cpu_seconds` — the runner's CPU estimate
- `total_element_count` — elements processed
- `watermark_lag` — streaming only: how far behind the watermark is
- `dataflow_job/...` — job-level metrics from the service

### Custom metrics with `beam.metrics.Metrics`

The built-in metrics tell you about the *system*. They cannot tell you
about the *business*: how many orders were rejected as duplicates, how many
fell below the fraud threshold, how many were routed to the manual-review
queue. For that you need your own metrics.

The API is `beam.metrics.Metrics`:

```python
from apache_beam.metrics import Metrics

counter = Metrics.counter("orders", "rejected")
distribution = Metrics.distribution("orders", "amount")
```

Both are classmethods taking a **namespace** and a **name**:

| Call | Result | Use for |
|---|---|---|
| `Metrics.counter(namespace, name)` | A `DelegatingCounter` | Counting events: rows read, rows rejected, DLQ entries |
| `Metrics.distribution(namespace, name)` | A `DelegatingDistribution` | Measuring values: order amounts, latencies, batch sizes |

A counter is incremented:

```python
counter.inc()
counter.inc(5)
```

A distribution is updated with a value:

```python
distribution.update(42.5)
```

**A counter is not a gauge.** `inc()` adds; there is no `set()`. If you
want to report "there are 1,200 items in flight right now", you cannot use
a counter — a counter only ever goes up. Either use a distribution with a
label, or report the value as a `Beam` side output that you write to
Cloud Monitoring yourself. This is a real trap: a "queue depth" counter
that only ever increments tells you the *total* ever queued, which is
usually not what you wanted.

**The namespace and name matter.** The namespace groups related metrics;
the name is the metric itself. The convention is a lowercase dotted
namespace describing the subsystem (`orders`, `payments`, `fraud`) and a
snake_case name for the quantity (`rows_rejected`, `amount_eur`). These
names become the Cloud Monitoring metric names, so pick them once and
live with them. Renaming a metric breaks every dashboard and alert that
references it.

**Where to declare the metric.** The declaration must happen at **module
level**, not inside `process()`. Beam's metrics API is namespace-based:
the `namespace` argument is what scopes the metric, and a metric declared
inside a hot loop creates a new metric object per invocation, which is
both slow and wrong.

```python
# Correct: module level
from apache_beam.metrics import Metrics

ORDERS_REJECTED = Metrics.counter("orders", "rejected")


class RejectingFn(beam.DoFn):
    def process(self, order):
        if not is_valid_order(order):
            ORDERS_REJECTED.inc()
            return
        yield order
```

**Labelled metrics.** Beam supports labels on metrics, which become
dimensions in Cloud Monitoring. A label turns one metric into a
time series per label value — useful for "how many rejections per
region", and dangerous when the label has high cardinality.

```python
from apache_beam.metrics import Metrics

REJECTED = Metrics.counter("orders", "rejected")


class RejectingFn(beam.DoFn):
    def process(self, order):
        if not is_valid_order(order):
            REJECTED.inc(label=order.get("region", "unknown"))
            return
        yield order
```

Do not label by `order_id` or by anything with more than a few hundred
distinct values. Each label value is a separate time series in Cloud
Monitoring, and Cloud Monitoring charges per time series. A pipeline
labelling by order id creates millions of series, which is both a
performance problem and a bill.

**Exporting to Cloud Monitoring.** When you run with `DataflowRunner`, Beam
exports user metrics to Cloud Monitoring automatically, under the metric
family of your Cloud Monitoring project. The `MonitoringInfo` objects
carry the metric name, the namespace, the labels, and the value. You do
not need to write any export code — but you do need:

- a Cloud Monitoring project (usually the same one as the Dataflow job)
- the `roles/monitoring.metricWriter` role on the job's service account
- the metrics to be exported by the runner, which is the default

If metrics are not appearing, the most common cause is a missing
`monitoring.metricWriter` role on the service account, not a code problem.

**Testing metrics without GCP.** `MetricsFilter` is the *filter*, not
the query. The query lives on the pipeline result:

```python
from apache_beam.metrics import MetricsFilter


def test_rejected_counter():
    """The counter is incremented once per rejected order."""
    with beam.Pipeline(options=beam_test_options()) as pipeline:
        (
            pipeline
            | "Create" >> beam.Create([VALID_LINE, "garbage"])
            | "Parse" >> beam.ParDo(ParseOrderFn())
        )
        result = pipeline.run()
        result.wait_until_finish()
        results = result.metrics().query(MetricsFilter())

    counters = results["counters"]
    total = sum(c.committed for c in counters)
    assert total == 1
```

Two details in that snippet:

- **`MetricsFilter` has no `get_counters()` method.** It is a filter
  *builder* — `with_name`, `with_namespace`, `with_step` — and the
  query is `result.metrics().query(filter)`. The query returns a dict
  with the keys `"counters"`, `"distributions"`, `"gauges"`, and
  `"string_sets"`.
- **You need `pipeline.run()`, not the `TestPipeline` context manager**,
  because the metrics live on the pipeline *result*. `TestPipeline` runs
  the pipeline for you but discards the result object.

Each `MetricResult` exposes `key` (with `key.metric.name` and
`key.metric.namespace`) and `committed` (the aggregated value).

### Autoscaling

Dataflow's autoscaling chooses how many workers to run based on the
observed state of the job. There are three algorithms, and the default
changed in 2020.

| Algorithm | Signal | Behaviour | Use when |
|---|---|---|---|
| `Basic` | CPU utilisation only | Scales on average CPU across workers | Legacy jobs; predictable CPU-bound work |
| `Aggressive` | Backlog, memory, and CPU | Scales on the *backlog* — pending work per worker | **The default. Use this.** |
| `NONE` | None | Fixed worker count | Small jobs where scaling overhead exceeds the benefit |

The `Aggressive` algorithm is the default, and it is the right default.
The `Basic` algorithm's flaw is that it scales on CPU, and CPU is a
*lagging* indicator: by the time a worker is at 100% CPU, the backlog has
already built up. `Aggressive` scales on the backlog, which is a leading
indicator. It can start workers before the CPU is saturated, which is
exactly what you want when the work per element is unpredictable.

The `NONE` algorithm is a legitimate choice for small batch jobs. A job
that processes 5,000 rows takes 20 seconds on one worker. Starting a
second worker costs the runner the time to spin it up, transfer the
shuffle data, and tear it down — often more than the job itself. For
jobs under about 10 minutes, fixed workers are frequently both faster and
cheaper.

**`--min-workers` and `--max-workers`.** These set the bounds that
autoscaling works within.

```bash
python project/batch_pipeline.py \
    --runner DataflowRunner \
    --project YOUR_PROJECT_ID \
    --region us-central1 \
    --staging_location gs://YOUR_BUCKET/staging \
    --temp_location gs://YOUR_BUCKET/temp \
    --min_workers 1 \
    --max_workers 50 \
    --autoscaling_algorithm Aggressive
```

The rules that matter:

- `--min-workers` is the **floor**. The job will never run with fewer.
  For a streaming job this is also the **steady-state cost**, because
  Dataflow never scales a streaming job below the minimum.
- `--max-workers` is the **ceiling**. Set it to a number you are willing
  to pay for. This is the single most important cost-control flag in
  Dataflow, and it is the one most often omitted.
- Setting `--max-workers` equal to `--min-workers` is how you turn
  autoscaling off cleanly, without using `NONE`.
- If you omit `--max-workers`, Dataflow uses a very large number. A job
  with a hot key and no ceiling can request hundreds of workers to
  process what a single worker could do in seconds.

**Machine type.** `--machine_type` sets the vCPU and memory of each
worker. The standard types are:

| Machine type | vCPU | Memory | Use for |
|---|---|---|---|
| `n1-standard-1` | 1 | 3.75 GB | Tiny jobs, I/O-light |
| `n1-standard-2` | 2 | 7.5 GB | The sensible default |
| `n1-standard-4` | 4 | 15 GB | I/O-bound work, large shuffles |
| `n1-standard-8` | 8 | 30 GB | Very large shuffles, memory-heavy |
| `n1-highmem-2` | 2 | 13.5 GB | Large in-memory aggregations |
| `n1-highcpu-2` | 2 | 1.8 GB | Heavy parsing, little state |

**Dataflow does not size machines per stage.** The same machine type
applies to every worker in the job. If one stage is CPU-bound and another
is I/O-bound, you are forced to pick one compromise. The lever that
replaces per-stage sizing is **splitting the pipeline into two jobs** —
which costs a shuffle between them, and is therefore only worth it for
jobs large enough that the per-stage saving exceeds the shuffle cost.

**Scale to zero.** This is the question everyone asks and the answer is
unambiguous:

> **Dataflow does not scale streaming jobs to zero. A streaming job always
> keeps at least one worker, and that worker bills even when the pipeline
> is completely idle.**

The reason is structural, not a policy choice. A streaming pipeline's
stateful operators — `GroupByKey`, windowing, `CombinePerKey` — must keep
their state to be able to resume. Teardown would mean discarding that
state, and a pipeline that discards its state and restarts is not a
pipeline — it is a series of unrelated jobs.

The practical consequences:

- A streaming job that processes nothing at 3am still costs
  `min_workers × hours × rate`. With 10 workers at $0.06/vCPU-hour on
  `n1-standard-2` (2 vCPU each), that is 10 × 2 × $0.06 = **$1.20 per
  hour**, or **$28.80 over a weekend**.
- The only way to stop the billing is to **cancel the job**. A cancelled
  streaming job loses its state and its watermark position.
- The right design is a **scheduled batch job** for anything that does
  not need sub-minute freshness. Run it, let it exit, pay for the minutes
  it ran.
- If you need continuous processing but not continuous *billed* workers,
  the pattern is a scheduled job that reads the backlog and exits — a
  "micro-batch" streaming design.

**Batch scaling guidance.** The default advice — "start at 1 worker and
let it scale" — is correct, and here is why:

1. The `Aggressive` algorithm starts from the minimum and scales up based
   on observed backlog. Starting at 1 means the job pays only for what it
   needs.
2. The scale-up is cheap in wall time. Starting a worker takes 30–60
   seconds; if the job has 20 minutes of work left, that is 5% overhead.
3. Starting high is expensive in money and can be *slower*: a job that
   requests 100 workers for 5,000 rows spends most of its time in worker
   startup, shuffle transfer, and teardown.

The exception: a job whose data is enormous and whose per-element cost is
predictable may benefit from starting higher, because the ramp-up
underruns the actual work. Measure, do not guess.

**Tuning by observation.** The workflow that actually works:

1. Run the job once with `--min_workers 1 --max_workers 20` and
   `Aggressive`.
2. Read the autoscaling graph in the Metrics tab. Note the peak worker
   count and where it plateaued.
3. If the plateau was at the ceiling, raise `--max_workers` and re-run.
4. If the plateau was well below the ceiling and the job still finished
   slowly, the bottleneck is not parallelism — it is skew, I/O, or a
   serial stage. Read the job graph.

### Alerts worth having

Most alerting setups for Dataflow are noise. These are the ones that earn
their keep.

| Alert | Condition | Severity | Why |
|---|---|---|---|
| Batch job failed | `JOB_STATE_FAILED` | Page | Obvious, but the most important |
| Batch job missing | No successful run in the expected window | Page | The silent failure — a job that never started |
| Streaming watermark lag | Lag > 10 min for 5 min | Page | The streaming SLO |
| Streaming output stopped | Output rate = 0 while input > 0 for 5 min | Page | A hard failure that looks like "no traffic" |
| DLQ rate | > 0.1% of input for 10 min | Ticket | Data quality degradation |
| Worker count oscillating | More than N scale events in 10 min | Ticket | Autoscaling thrash |
| Estimated vs actual CPU | Ratio outside 0.5×–2× for 3 runs | Ticket | The estimate is drifting; re-plan capacity |
| Sink row count deviation | Output rows outside the expected band | Page | Silent data loss |
| Cost anomaly | Daily spend > 2× the 30-day median | Ticket | A runaway job |
| Quota | vCPU-hours in the region near the limit | Ticket | A silent infrastructure failure |

Two principles:

- **Alert on outcomes, not on causes.** "Watermark lag" is an outcome
  users feel. "Worker count changed" is a cause, and workers change
  count constantly and harmlessly.
- **Every alert needs a runbook.** An alert nobody can act on is training
  your team to ignore alerts. The runbook is a short document: what it
  means, what to check first, what the fix is, and when to escalate.

---

## 🛠️ Hands-On: Adding a Custom Counter Metric to the Batch Pipeline

This hands-on adds a production-quality counter to the batch pipeline:
one that counts the orders rejected by validation, labelled by reason.

### Step 1 — look at the current pipeline

```bash
cd data-engineering/data-Course/google/Dataflow
source .venv/bin/activate
sed -n '100,135p' project/batch_pipeline.py
```

The `ParseOrders` step is where malformed and invalid rows are dropped.

### Step 2 — add the metric to `project/transforms.py`

Metrics must be declared at module level. Add the import near the top of
`transforms.py`, after the `apache_beam` import block:

```python
from apache_beam.metrics import Metrics
```

Then declare the counters at module level, outside the `if BEAM_AVAILABLE`
block (so the names exist regardless, and so the import does not fail when
Beam is absent — guard it inside the block or use a lazy import). The
cleanest approach is to declare them inside the `if BEAM_AVAILABLE:` block
alongside the `DoFn`s, because that is the only place Beam exists:

```python
if BEAM_AVAILABLE:  # pragma: no cover - requires the optional dependency

    #: Counts of orders dropped by the parser, labelled by reason.
    #:
    #: Declared at module level on purpose: Beam's metrics API is
    #: namespace-based, and a metric declared inside `process` would create
    #: a new metric object on every element.
    ORDERS_MALFORMED = Metrics.counter("orders", "malformed")
    ORDERS_INVALID = Metrics.counter("orders", "invalid")

    class ParseOrderFn(beam.DoFn):
        """Parse CSV lines into order dicts, skipping malformed rows."""

        def process(self, line: str, timestamp=beam.DoFn.TimestampParam) -> Iterable[Any]:
            """Parse one line and emit the resulting order dict."""
            row = try_parse_order_line(line)
            if row is None:
                log.warning("skipping malformed order line: %.120s", line)
                ORDERS_MALFORMED.inc()
                return
            if not is_valid_order(row):
                log.warning("skipping invalid order: %s", row.get("order_id"))
                ORDERS_INVALID.inc()
                return
            yield row
```

And in the `else:` branch (the Beam-absent placeholder), add matching
placeholders so the module's public surface does not change:

```python
class _ZeroCounter:
    """A counter that does nothing, for the Beam-absent case."""

    def inc(self, *args, **kwargs):
        """Ignore the increment."""


ORDERS_MALFORMED = _ZeroCounter()
ORDERS_INVALID = _ZeroCounter()
```

Attach those two names to the `else:` branch of the `if BEAM_AVAILABLE:`
block in `transforms.py`, so the module's public surface is the same
whether or not Beam is installed.
    ORDERS_MALFORMED = _ZeroCounter()
    ORDERS_INVALID = _ZeroCounter()
```

### Step 3 — run the pipeline and see the counter

```bash
python resources/sample_data.py --output-dir ./sample_data
python project/batch_pipeline.py --input ./sample_data/orders.csv --output ./out/summary
```

Now run it with a file that contains malformed rows so the counter
actually moves:

```bash
ls sample_data/
```

The generator produces `malformed_orders.csv` alongside the clean file.
Run the pipeline over it:

```bash
python project/batch_pipeline.py \
    --input ./sample_data/malformed_orders.csv \
    --output ./out/summary_malformed
```

The counters are emitted through the runner. On the Direct Runner, they
appear in the log output. To read them programmatically, run the pipeline
explicitly and query the pipeline result:

```python
from apache_beam.metrics import MetricsFilter

with beam.Pipeline(options=beam_test_options()) as pipeline:
    (
        pipeline
        | "Read" >> beam.io.ReadFromText("./sample_data/malformed_orders.csv")
        | "Parse" >> beam.ParDo(ParseOrderFn())
    )
    result = pipeline.run()
    result.wait_until_finish()
    results = result.metrics().query(MetricsFilter())

for counter in results["counters"]:
    print(counter.key.metric.name, counter.key.metric.namespace, counter.committed)
```

### Step 4 — write a test for the metric

Add this to `project/tests/test_pipelines.py`:

```python
class TestMetrics:
    """The counters the parser emits."""

    def test_malformed_counter_is_incremented(self):
        """A malformed line increments the malformed counter."""
        from apache_beam.metrics import MetricsFilter

        with beam.Pipeline(options=beam_test_options()) as pipeline:
            (
                pipeline
                | "Create" >> beam.Create([VALID_ORDER_LINE, "garbage"])
                | "Parse" >> beam.ParDo(ParseOrderFn())
            )
            result = pipeline.run()
            result.wait_until_finish()
            results = result.metrics().query(MetricsFilter())

        counters = results["counters"]
        total = sum(c.committed for c in counters)
        assert total == 1
```

Two notes on that test:

- **It uses `beam.Pipeline`, not `TestPipeline`.** The metrics live on
  the pipeline *result*, and `TestPipeline` discards it. If you want
  `TestPipeline`'s cleanup behaviour as well, call `pipeline.run()` on
  the `TestPipeline` instance — it is a `Pipeline` subclass.
- **The query returns counters from every step**, so summing the
  committed values is the robust way to assert on the total. Narrow it
  with `MetricsFilter().with_namespace("orders")` when you know the
  namespace.

### Step 5 — verify the test catches a regression

Temporarily remove the `ORDERS_MALFORMED.inc()` line from
`project/transforms.py` and re-run:

```bash
python3 -m pytest project/tests/test_pipelines.py -k metrics -v
```

```text
FAILED project/tests/test_pipelines.py::TestMetrics::test_malformed_counter_is_incremented
assert 0 == 1
```

Restore the line and confirm the suite is green:

```bash
python3 -m pytest project/tests/ -q
```

### Step 6 — run on Dataflow and read the metric in Cloud Monitoring

```bash
python project/batch_pipeline.py \
    --runner DataflowRunner \
    --project YOUR_PROJECT_ID \
    --region us-central1 \
    --staging_location gs://YOUR_BUCKET/staging \
    --temp_location gs://YOUR_BUCKET/temp \
    --temp_location gs://YOUR_BUCKET/temp \
    --job_name orders-summary \
    --autoscaling_algorithm Aggressive \
    --min_workers 1 \
    --max_workers 20
```

Then read the metric back:

```bash
gcloud monitoring time-series list \
    --project YOUR_PROJECT_ID \
    --filter='metric.type="custom.googleapis.com/orders/malformed"'
```

And chart it:

```bash
gcloud monitoring charts create \
    --project YOUR_PROJECT_ID \
    --title "Orders rejected" \
    --x-axis-data-source="custom.googleapis.com/orders/malformed"
```

If the query returns nothing, check the service account's
`roles/monitoring.metricWriter` binding before suspecting the code.

---

## 🛠️ Common Errors and Fixes

### `AttributeError: module 'apache_beam' has no attribute 'metrics'`

`beam.metrics` is a submodule that is not imported by `import apache_beam
as beam` in every context. Import it explicitly:

```python
from apache_beam.metrics import Metrics
```

### `AttributeError: 'DelegatingCounter' object has no attribute 'set'`

Counters only go up. There is no `set()`. Use `inc()` to increment, and
`dec()` to decrement. To report a current value, use a distribution or
write the value to your own sink.

### `AttributeError: 'MetricsFilter' object has no attribute 'get_counters'`

`MetricsFilter` is a **filter builder**, not a query. It has
`with_name`, `with_namespace`, `with_step` — and no getters. The query
lives on the pipeline result:

```python
result = pipeline.run()
result.wait_until_finish()
results = result.metrics().query(MetricsFilter())
counters = results["counters"]
```

### `AttributeError: 'MetricKey' object has no attribute 'namespace'`

The namespace is on `key.metric.namespace`, not on `key` directly. The
full path is `counter.key.metric.namespace`, and the value is
`counter.committed`.

### The metrics query returns an empty list

Two likely causes:

1. **You used `TestPipeline` instead of `beam.Pipeline`.** `TestPipeline`
   runs the pipeline but discards the result object, so there is nothing
   to query. Call `pipeline.run()` and keep the result.
2. **The counter was never incremented on the runner.** A counter
   declared inside `process()` is scoped to that element, not to the
   pipeline. Declare it at module level.

### The metric never appears in Cloud Monitoring

Three likely causes, in order of frequency:

1. The service account lacks `roles/monitoring.metricWriter`.
2. The metric was declared inside `process()` rather than at module
   level, so it is scoped to the element rather than the namespace.
3. The metric namespace contains characters Cloud Monitoring rejects.
   Namespaces must be non-empty and no longer than 250 characters, and
   the name must be a valid Cloud Monitoring metric name.

### `ValueError: Metric name ... is invalid`

Cloud Monitoring metric names must match `[a-zA-Z][a-zA-Z0-9_]*` and be
at most 200 characters. Use lowercase snake_case.

### The counter is 10× the number of bad rows

You declared the metric inside `process()`, so it is created per element
and each instance counts separately. Move the declaration to module
level.

### The watermark lag metric is missing on a batch job

`watermark_lag` is a streaming metric. Batch jobs do not have one,
because a batch job's watermark advances to `+inf` at the end and there
is nothing to lag behind.

### The autoscaling graph shows a flat line at 1 worker

Either the job is small enough that `Aggressive` decided not to scale, or
the algorithm is `Basic` and the work is I/O-bound rather than CPU-bound.
Check the `--autoscaling_algorithm` flag and the job graph — a wide but
slow stage means I/O, not CPU.

### `ValueError: max_workers must be greater than or equal to min_workers`

The two flags are inconsistent. If you meant a fixed worker count, set
them equal.

### The job requests far more workers than you expected

You did not set `--max_workers`, so Dataflow used a very large default.
This is the most common cause of a Dataflow bill shock. Always set the
ceiling.

### `google.api_core.exceptions.Forbidden: Permission 'monitoring.metricWriter' denied`

The job's service account needs the metric-writer role. Grant it:

```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:YOUR_PROJECT_ID-dataflow@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/monitoring.metricWriter"
```

### The streaming job shows no output but the input is flowing

Check the worker log for an exception. Then check the watermark: if the
watermark is stuck at its initial value, the pipeline is not receiving
elements at all, and the problem is upstream of your code — a Pub/Sub
subscription with no attached worker, or a source that is not advancing.

---

## 💡 Production Notes

- **The row count at the sink is your most important metric.** Everything
  else in the platform tells you the job ran. Only the sink tells you it
  worked. Build the comparison automatically: expected input rows minus
  expected filtered rows equals expected output rows.
- **Watermark lag, not throughput, is the streaming SLO.** Throughput can
  be high while the pipeline is falling behind. Alert on lag.
- **A streaming job that produces nothing still bills.** 10 workers on
  `n1-standard-2` is $1.20 per hour, $28.80 over a weekend, for a job
  that is doing nothing. Cancel it, or design it as a scheduled batch
  job.
- **Always set `--max_workers`.** It is the cheapest insurance in Dataflow.
  The default ceiling is effectively unlimited, and one job with a hot
  key can request hundreds of workers.
- **Autoscaling to zero is a batch-only concept.** Do not design a
  streaming architecture that assumes it.
- **Machine type is a job-wide decision, not a per-stage one.** If a
  pipeline has one memory-hungry stage and one CPU-hungry stage, you are
  choosing a compromise. Splitting the job is the alternative, and it
  costs a shuffle.
- **Do not label metrics by high-cardinality fields.** One time series per
  `order_id` is a Cloud Monitoring bill and a query performance problem.
  Keep labels to a few hundred values at most.
- **Alert on outcomes.** "No successful batch job in 4 hours" catches the
  failure mode that matters. "Worker count changed" catches nothing,
  because the worker count changes constantly and harmlessly.
- **Read the job graph before you optimise.** A wide-but-slow stage means
  I/O-bound; a fat-and-slow stage means skew or serialisation. The
  optimisation for each is completely different, and guessing wastes a
  day.
- **Estimate the CPU before you trust the estimate.**
  `estimated_cpu_seconds` is derived from a sample and is routinely off
  by 30% on a first run. Calibrate it against your own history, and use
  *your* number, not the runner's, for capacity planning.

---

## 🔑 Key Takeaways

- **Batch and streaming fail in opposite ways**, so they need different metrics. Batch: did it finish, and did it produce the right rows? Streaming: is it keeping up?
- **The Dataflow UI has four areas**: the job list, the job graph (with its stage heatmap), the Metrics tab, and the logs. Learn where the autoscaling graph lives.
- **Built-in metrics worth knowing**: `beam.io.read.bytes`, `beam.io.write.bytes`, `estimated_cpu_seconds`, `total_element_count`, and the streaming-only `watermark_lag`.
- **Custom metrics use `beam.metrics.Metrics.counter(namespace, name)` and `Metrics.distribution(namespace, name)`**, declared at **module level**, with `inc()` and `update()`.
- **`Aggressive` autoscaling is the default and the right choice** — it scales on the backlog, not on lagging CPU signals. `Basic` is legacy. `NONE` is for small batch jobs.
- **`--min-workers` is the floor and the streaming steady-state cost; `--max-workers` is your cost ceiling. Always set the ceiling.**
- **Dataflow does not scale streaming to zero.** A streaming job always keeps at least one worker, and it bills while idle.
- **Alert on outcomes, not causes, and give every alert a runbook.**

---

## 📚 Practice Exercises

1. **Add a distribution metric for order amounts.** Declare `Metrics.distribution("orders", "amount_eur")` at module level in `project/transforms.py` and update it with the order's normalised amount in `ParseOrderFn`. Write a test that asserts the distribution's `sum` equals the total revenue for a known input. *Expected answer:* `result.metrics().query(MetricsFilter())["distributions"]` returns `MetricResult` objects whose `.committed` is a `DistributionResult` with `.sum`, `.count`, `.min`, and `.max`; for three EUR orders of 10, 20 and 30, `sum` is 60.0 and `count` is 3.

2. **Build a batch cost estimator.** Write a function that takes the input file size, the average bytes per row, and the observed wall time of a 1-worker run, and returns the estimated vCPU-hours for a 50-worker run at 60% efficiency. Apply it to the course's 5,000-order sample file. *Expected answer:* with 5,000 rows at roughly 110 bytes each (about 550 KB) and a 20-second single-worker run, a 50-worker run at 60% efficiency is about 50 × (20/50) / 0.6 ≈ 33 vCPU-seconds, so the cost is negligible — which is the point: the estimator is most useful on the large end.

3. **Set a worker ceiling and prove it holds.** Run the batch pipeline on Dataflow with `--min_workers 1 --max_workers 5` and `--autoscaling_algorithm Aggressive` over the 5,000-row sample. Read the autoscaling graph in the Metrics tab. *Expected answer:* the peak worker count never exceeds 5, and the job is likely to run entirely on 1 worker because the dataset is too small to create a backlog.

4. **Write a watermark-lag alert rule.** Create a Cloud Monitoring alerting policy that fires when the streaming pipeline's `watermark_lag` exceeds 600 seconds for 5 minutes. Use `gcloud monitoring policies create` with a custom metric descriptor for `dataflow.googleapis.com/watermark_lag`. *Expected answer:* the policy needs an `OR` condition with a `filter` matching the metric type and a `condition.threshold.value` of 600 with `comparison` `COMPARISON_GT` and a `condition.duration` of 300 seconds.

5. **Detect a metric that is double-counting.** Add `ORDERS_INVALID.inc()` to a place where it will be reached twice per rejected order, then query the metrics with `result.metrics().query(MetricsFilter())` and show the count is 2× the expected value. Explain in writing why a metric declared inside a hot loop behaves this way. *Expected answer:* the counter is created per invocation of `process`, so each element increments its own metric instance; the fix is to declare the counter once at module level.

6. **Design the alert set for a nightly batch job.** Write down five alerting rules for a job that must produce a table by 06:00 every day, with a runbook line for each. *Expected answer:* (1) job failed, page; (2) no job started by 02:00, page; (3) job still running at 05:00, page; (4) sink row count outside the expected band, page; (5) vCPU-hours in the month-to-date over 150% of the 3-month average, ticket. Each needs a runbook line naming the first thing to check.

---

## 📖 Further Reading

- Google Cloud Dataflow: Monitoring a streaming pipeline — https://cloud.google.com/dataflow/docs/monitoring/streaming-pipeline
- Google Cloud Dataflow: Monitoring metrics — https://cloud.google.com/dataflow/docs/monitoring/metrics
- Google Cloud Dataflow: Monitoring and logging — https://cloud.google.com/dataflow/docs/monitoring
- Google Cloud Dataflow: Autoscaling — https://cloud.google.com/dataflow/docs/autoscaling
- Google Cloud Dataflow: Optimizing your pipeline's performance — https://cloud.google.com/dataflow/docs/optimize-performance
- Apache Beam: Metrics — https://beam.apache.org/documentation/sdks/python/apache-beam-metrics-metrics-py/
