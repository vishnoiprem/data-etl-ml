# 5.3 — Apache Beam and Google Cloud Dataflow

> **Section 5 · Processing & Orchestration · Lecture 5.3 · 8:00**

## 🎯 What you will learn

- The Beam model: `PCollection`, `PTransform`, `DoFn`, and the runner SDK harness
- Why a portable abstraction is worth its learning cost
- The core transforms and the vocabulary they give you
- The runner family: Direct, Spark, Flink, Dataflow, and what portability actually means
- The Dataflow service architecture: job graph, stages, workers, autoscaling, streaming
- Templates versus custom jobs
- The `gcloud dataflow` CLI and the SDK-version pinning trap
- Streaming with Beam: windows, triggers, and watermarks
- The Dataflow versus Dataproc decision

---

## 🧠 Concept

### The problem Beam was created to solve

By 2014 the industry had four or five serious streaming and batch engines — MapReduce, Flink, Spark, Samza, Storm — and a streaming library with a growing pile of vendor-specific extensions. The cost was not only technical. It was that **the same business logic had to be rewritten per engine**, and the market was consolidating fast.

Apache Beam's thesis: the *execution engine* is a commodity, and the *programming model* should be the stable thing. Write once against a model, run on any backend that implements it. Google built Beam while designing Dataflow; other vendors contributed runners.

Whether that bet paid off fully is arguable. But the model is excellent, and it is the model Dataflow actually implements — so learning Beam teaches you how Dataflow works under the hood.

### The core abstractions

#### `PCollection`

A **PCollection** is a distributed collection of elements with a schema-ish type. Crucially, it carries an **element timestamp** and a **window** (or the notion of belonging to the global window). That is what makes Beam a *time-aware* model rather than just a collection abstraction.

PCollections come in two flavours:

- **Bounded** — finite, known input. A file, a fixed-size table, a list. You can reason about completion.
- **Unbounded** — infinite input. A Pub/Sub subscription, a Kafka topic. You can never finish processing it; you can only keep up.

Nearly every capability difference between batch and streaming in Beam comes from boundedness. Bounded PCollections are processed with all data present; unbounded ones need windowsing, triggers, and watermarks.

#### `PTransform`

A **PTransform** is a function from one or more input PCollections to zero or more output PCollections. It is the unit of composition: you chain PTransforms into a pipeline.

```text
(pcoll
   | "Read" >> beam.io.ReadFromText(source_path)
   | "Parse" >> beam.Map(parse_line)
   | "Validate" >> beam.Map(validate_row)
   | "Aggregate" >> beam.CombinePerKey(sum))
```

The `>>` is the pipe operator. The string before it is a **label**, used in the UI, in metrics, and in error messages. Labels are not optional decoration: an unlabelled transform shows up as a machine-generated name in the Dataflow UI, and a 3 a.m. incident is much harder to debug when every stage is called `ParDo(8)`.

#### `DoFn`

Most Beam processing happens in a `DoFn` — a class with a `process` method:

```python
class NormaliseEvent(beam.DoFn):
    def process(self, row, currency_rates=DEFAULT_RATES):
        rate = currency_rates.get(row["currency"])
        if rate is None:
            yield {"reason": "unknown_currency", "raw": row}
            return
        yield {
            "event_id": row["event_id"],
            "region": row["region"],
            "amount_eur": round(float(row["amount"]) * rate, 2),
        }
```

`DoFn` has a real reason to exist beyond style. It supports:

- **Setup and teardown** (`setup`, `teardown`) for per-worker resources such as a database connection. Without it, opening a connection per element is catastrophic.
- **State and timers** for stateful streaming processing.
- **Type hints** for more precise schema inference.
- **Bundle** processing, which lets the runner bundle many elements into a single call for efficiency.

A plain function works too:

```text
| "Validate" >> beam.Map(validate_event)
```

`beam.Map` wraps it in a `DoFn` internally. Use a class when you need setup/teardown, state, or timers; use a function otherwise.

#### The runner SDK harness

Beam does not execute pipelines. The **SDK harness** is the interface between your pipeline code and a runner:

```python
beam_pipeline = Pipeline()
pcoll = (
    pipeline
    | "Create" >> beam.Create([1, 2, 3])
    | "Double" >> beam.Map(lambda x: x * 2)
)

result = pipeline.run()
result.wait_until_finish()
```

The harness supplies four things:

1. **The runner** — how the pipeline executes (Direct, Spark, Flink, Dataflow).
2. **The coder** — how `DoFn` objects are serialised and shipped to workers. Different runners use different coders: the Dataflow runner uses dill by default, the Flink runner uses pickling, and the Spark runner uses cloudpickle. A closure that fails to serialise on one runner and works on another is a portability bug you will meet.
3. **The state and timer backend** — where stateful DoFns store their state (in-memory, RocksDB, or the runner's managed state).
4. **The environment** — the SDK version, the runner version, the pipeline options.

### The runner family

| Runner | Bounded | Unbounded | Notes |
|---|---|---|---|
| **Direct Runner** | Yes | Yes (local, with local files) | Runs in a single JVM on the local machine. Excellent for unit tests. It is the default when no runner is specified. |
| **Spark Runner** | Yes | No | Maps Beam onto Spark's RDD and DataFrame model. **Streaming is not supported** — this is a hard limit, not a missing feature. |
| **Flink Runner** | Yes | Yes | Full batch and streaming on Flink. |
| **Dataflow Runner** | Yes | Yes | Google's managed service. Supports streaming, autoscaling, exactly-once state, and templates. |

**What portability actually means.** Beam's portability promise is real but bounded:

- The **model** is portable: transforms, windowing, triggers, and state semantics behave the same.
- The **API surface** differs. `beam.io.ReadFromText` on Dataflow can read GCS directly; on the Spark runner it needs a Hadoop-compatible filesystem. `beam.ResizableWindow` is a Dataflow-specific tuning knob.
- The **guarantees** differ. Exactly-once state processing is a Dataflow feature. On the Spark runner, state is not checkpointed the same way.

The honest summary: Beam gives you a portable *shape*. It does not give you portable *performance* or portable *guarantees*. If you intend to run on exactly one backend, using Beam's Dataflow runner gives you the model without paying the full portability tax.

### Why the abstraction is worth its learning cost

Four reasons, in order of how often they actually matter:

1. **One code path for batch and stream.** A Beam pipeline can be deployed as a batch job over a bounded source or a streaming job over an unbounded source with the same transform logic. The differences are explicit and visible in the pipeline graph, not hidden in a separate streaming codebase.
2. **Time semantics are explicit.** Windows, timestamps, triggers, and watermarks are first-class. There is no ambiguity about whether a timestamp is event time or processing time — the model forces you to say which.
3. **The runner is a deployment detail.** A team can standardise on one runner while keeping the option of moving. Even if you never move, the discipline of the model produces better code.
4. **The abstractions map onto managed services.** Dataflow's autoscaling, checkpointing, and exactly-once semantics are implemented *because* the Beam model exposes the right hooks. Learning the model is learning the service.

### The Dataflow service architecture

When you submit a pipeline to Dataflow, the service compiles it.

```text
your pipeline (Beam SDK)
        │
        ▼
  SDK harness → job graph
        │
        ▼
  Dataflow service: optimiser, scheduler, worker pool
        │
        ▼
  workers execute stages
```

#### The job graph

The Dataflow service turns your pipeline into a **job graph** of operations and transforms. It performs several rewrites:

- **Fusion.** A `Map` immediately followed by another `Map` on the same collection is fused into one `ParDo` stage, avoiding a serialisation boundary.
- **Group-by-key optimisation.** A `CombinePerKey` after a `GroupByKey` may be rewritten so the partial combine happens before the shuffle.
- **Read and write sinking.** Sources and sinks are moved to the edges of the graph so the compute stages are homogeneous.

#### Stages and workers

The job graph is divided into **stages** that can run in parallel. Each stage is executed by a **worker**. Workers are Compute Engine VMs in the Dataflow region, with the driver running on a separate worker.

Dataflow manages the worker pool: it starts workers, assigns stages, and **scales the pool up and down** based on the backlog of pending work. This is the single biggest practical difference from Dataproc, where you choose the cluster size up front and Spark's static stage partitioning means a scale-up does not help a stage already in flight.

#### Autoscaling

Dataflow autoscaling is driven by a measure of **pending work** (the "work backlog") and **CPU utilisation** per worker. The service adds workers when the backlog grows relative to available parallelism and removes them when work dries up.

In practice this means:

- A job that spikes to 200 workers for ten minutes and then runs on two workers costs roughly ten minutes of 200 workers.
- Streaming pipelines settle at a steady-state worker count matching their throughput, and scale down when input slows.

This is why Dataflow streaming is often *cheaper* than a fixed-size streaming cluster on another platform: idle capacity is not paid for.

### Templates versus custom jobs

Dataflow offers two ways to run a pipeline.

**Custom jobs** are arbitrary Beam code you write and submit. You control the transforms, the windowing, the sinks. This is the general case.

**Templates** are pre-packaged Beam pipelines with a fixed structure and a small parameter surface, published to a regional template catalogue. You invoke them by name with parameters:

```bash
gcloud dataflow templates run my-job \
  --project=my-project \
  --region=us-central1 \
  --template=gs://dataflow-templates/latest/streaming/import_csv_gcs.py \
  --parameters="inputPath=gs://bucket/events.csv,outputTable=project:dataset.events,bigqueryDataset=dataset"
```

Templates exist because a large fraction of production data movement is one of a handful of shapes: CSV to BigQuery, GCS to BigQuery, Pub/Sub to BigQuery, BigQuery to GCS, GCS to Pub/Sub. Google maintains these templates, keeps them current, and charges a per-job fee for template invocation rather than requiring you to operate a pipeline.

**My advice:** use templates for the boring 80 percent of table movement where the shape is standard. Write a custom job when you need real transform logic, windowing, state, or anything the template does not express. Do not fork a template to add five lines of logic — at that point you own the fork, its bug fixes, and its SDK upgrades.

### The `gcloud dataflow` CLI

The commands you need:

```bash
# Submit a batch job from a local file
gcloud dataflow jobs run \
  --project=my-project \
  --region=us-central1 \
  --job-file=gs://bucket/jobs/batch.py \
  --temp_location=gs://bucket/tmp \
  --staging_location=gs://bucket/staging

# Submit a streaming job
gcloud dataflow jobs run \
  --project=my-project \
  --region=us-central1 \
  --job-file=gs://bucket/jobs/stream.py \
  --streaming \
  --temp_location=gs://bucket/tmp \
  --staging_location=gs://bucket/staging \
  --region=us-central1 \
  --runner=DataflowRunner \
  --streaming

# List and inspect jobs
gcloud dataflow jobs list --project=my-project --region=us-central1
gcloud dataflow jobs describe JOB_ID --region=us-central1
gcloud dataflow jobs describe JOB_ID --format="value(jobStatus.state)"

# Cancel a job
gcloud dataflow jobs cancel JOB_ID --region=us-central1

# List published templates
gcloud dataflow templates list --region=us-central1
```

The two flags that matter most and are most often wrong:

- **`--temp_location`** — where Dataflow writes shuffle and pipeline work files. It must be a GCS path. Under-provisioning it (or sharing one bucket across many jobs) causes job stalls.
- **`--staging_location`** — where the job's code and dependencies are staged. It must also be GCS, and it must be in the same region as the job for performance.

### The SDK-version pinning trap

This is the error that catches everybody who submits a Beam job for the first time.

```text
RuntimeError: Beam SDK version 2.53.0 is not supported by the Dataflow
runner. Please use a supported version between 2.57.0 and 2.62.0.
```

Or, more cryptically:

```text
ValueError: PipelineOptions specified in the runner are not compatible with
the SDK version in use: apache-beam==2.40.0. The Dataflow service requires
one of: 2.57.0<=apache-beam<=2.62.0
```

**Why it happens.** Beam's SDK is released frequently. The Dataflow service only supports a moving window of SDK versions, because it must be able to run the code the SDK generates. When you `pip install apache-beam` and get the latest, but the Dataflow backend in your region has not been updated yet, the versions disagree.

**The fix.** Pin the SDK version explicitly and match it to what the service supports:

```bash
pip install "apache-beam[gcp]==2.62.0" --index-url https://pypi.org/simple
```

Check the supported range before you build:

```bash
gcloud dataflow jobs describe <a-recent-job-id> --region=us-central1 \
  --format="value(environment.sdkVersion)"
```

**The disciplined answer:** pin the SDK version in a `requirements.txt` that is uploaded with the job, and never rely on "latest". A Beam job that breaks because a transitive dependency changed is exactly the kind of failure that should never reach production.

### Streaming with Beam: windows, triggers, and watermarks

This is where Beam earns its keep. The streaming model has four moving parts.

#### Timestamps and event time

Every element in a PCollection carries a timestamp. For data coming from a source, the timestamp is the **event time** — when the thing happened, as recorded by the producer. Beam does not re-stamp on arrival.

If you ignore event time and use processing time, you get a pipeline that produces correct-looking answers and wrong totals whenever events arrive late.

#### Windows

A **window** partitions the unbounded stream into finite groups for aggregation. The important distinction:

- **Fixed windows** — every window is the same width and boundaries are aligned to the epoch. `[10:00, 11:00)`, `[11:00, 12:00)`. Simple, aligned, and the right default for reporting.
- **Sliding windows** — each window overlaps the previous. `Window.into(FixedWindows.of(1 hour).every(15 minutes))` gives windows at 10:00, 10:15, 10:30, ... Each event lands in four windows. Correct for smoothing and alerting, four times the work.
- **Session windows** — windows are defined by gaps in activity. A user's session ends after 30 minutes of silence. Correct for user-behaviour analysis, harder to reason about and to test.

#### Triggers

A **trigger** decides when a window's result is emitted. This is the mechanism for handling late data.

- **Default trigger** — emit at the end of the window. Late data is dropped.
- **After processing time, or late data** — emit at window end, then re-emit as late data arrives. The count keeps growing.
- **After count** — emit when N elements have arrived. Good for sampling, bad for completeness.
- **Element-wise** — emit every element. Effectively no aggregation.
- **Repeatedly** — emit every N seconds while the window is open. Good for progress reporting.

#### Watermarks

A **watermark** is the pipeline's assertion about event-time completeness: *no element older than this timestamp will arrive any more*. When the watermark passes a window's end, that window is finalised and its state is discarded.

The trade-off is the fundamental one in every streaming system:

- **Low watermark (tight)** — windows close quickly, state is bounded, latency is low, but late data is dropped.
- **High watermark (loose)** — windows stay open longer, late data is included, state grows, and the risk of a late arrival exceeding the watermark is lower.

Beam's `TimestampCombiner` with a `with_lateness` bound and a `allowed_lateness` per window give you explicit control.

**The production pattern**, which the course simulator mirrors exactly: use fixed event-time windows, allow a bounded lateness of a few minutes, and route events that arrive beyond the allowed lateness to a dead-letter path with a count by reason code. That gives you a bounded, correct pipeline and a visible signal when the upstream guarantee breaks.

### The Dataflow versus Dataproc decision

| Dimension | Dataflow (Beam) | Dataproc (Spark) |
|---|---|---|
| Model | Beam PCollection/PTransform | Spark DataFrame/RDD |
| Batch and streaming | One model, both | Separate engines (SQL and Structured Streaming) |
| Streaming state | Managed, exactly-once | Structured Streaming with checkpointing |
| Cluster management | None | You size it (or use Serverless) |
| Autoscaling | Continuous, per-stage | Bounded, static stage partitioning |
| Cost shape | Work performed; scales to near zero | Cluster size × time |
| Ecosystem | Beam SDK only | Entire Spark ecosystem (MLlib, GraphX) |
| Talent pool | Small | Large |
| Templates | Yes, maintained by Google | Workflow templates, plus Spark jobs |
| Best for | Streaming, unified pipelines, managed ops | Complex batch ETL, custom algorithms, ML |

**Choose Dataflow when** the pipeline is streaming, when you need exactly-once stateful processing, when you want one code path for batch and stream, or when you do not want to size clusters and interpret Spark's static partitioning.

**Choose Dataproc when** the work is complex batch ETL, you want the Spark ecosystem, your team already knows Spark, or you need custom UDFs and machine-learning pipelines.

**Choose neither when** the transformation is SQL over a partitioned table. BigQuery will be simpler, and often cheaper.

There is one more consideration that is rarely discussed: **the cost of the abstraction**. Beam's model is precise, and precision has a price. A team that learns Beam can move between Dataflow, Flink, and Spark. A team that learns Spark can move between Spark, Databricks, EMR, and Dataproc. Both are defensible bets. The deciding factor is usually the shape of the workload, not the elegance of the abstraction.

---

## 🛠️ Hands-On

### Exercise 1: the Beam skeleton for the course pipeline

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events, aggregate_events, render_summary_csv

# The Beam version of the course pipeline looks like this:
#
#   pipeline = beam.Pipeline()
#   (
#       pipeline
#       | "Read"   >> beam.io.ReadFromText("gs://bucket/events.csv")
#       | "Parse"  >> beam.Map(parse_line)
#       | "Valid"  >> beam.Map(validate_row)
#       | "Agg"    >> beam.CombinePerKey(sum_amount)
#   )
#
# The transform names change; the stages do not.

with open("sample_data/events.csv", encoding="utf-8") as handle:
    accepted, rejected = ingest_events(handle.read().splitlines())

summary = aggregate_events(accepted)
print(render_summary_csv(summary))
print(f"rejected: {len(rejected)}")
```

Output:

```text
region,event_count,revenue_eur
AMER,1238,464848.02
APAC,1159,421049.85
EMEA,1176,432544.17
LATAM,1227,445554.36
rejected: 0
```

### Exercise 2: model the Beam pipeline as a stage graph

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import (
    ingest_events,
    aggregate_events,
    aggregate_by_window,
    bucket_by_window,
)

with open("sample_data/events.csv", encoding="utf-8") as handle:
    accepted, rejected = ingest_events(handle.read().splitlines())

stages = [
    ("Read", lambda rows: rows),
    ("Parse", lambda rows: rows),
    ("Validate", lambda rows: rows),
    ("Window (fixed, 1h)", bucket_by_window),
    ("GroupByKey", lambda rows: rows),
    ("CombinePerKey", aggregate_events),
]

current = accepted
print(f"{'Stage':22s} {'elements out':>13s}  {'shuffle?':>8s}")
for name, fn in stages:
    before = len(current)
    if fn is bucket_by_window:
        current = list(fn(current).values())
        current = [row for group in current for row in group]
        shuffle = "yes"
    else:
        current = fn(current)
        shuffle = "no"
    print(f"{name:22s} {len(current):13d}  {shuffle:>8s}")

print("rejected:", len(rejected))
```

This is the shape of a Beam graph: a linear spine with one expensive boundary. The `GroupByKey` is the boundary where the pipeline stops being embarrassingly parallel and starts paying for a shuffle.

### Exercise 3: fixed windows with event time

Beam's `FixedWindows` of one hour. The simulator's `bucket_by_window` computes the window start from the **event timestamp**, not from arrival order — the property the whole windowing model exists to guarantee.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events, bucket_by_window, aggregate_events

with open("sample_data/events.csv", encoding="utf-8") as handle:
    accepted, _ = ingest_events(handle.read().splitlines())

windows = bucket_by_window(accepted, window_seconds=3600)
print("windows:", len(windows))
print("window boundaries (half-open [start, end)):")
for start in sorted(windows)[:3]:
    print("  ", start)

per_window = aggregate_by_window(accepted)
print("output rows:", len(per_window))
print("first row:", per_window[0])
```

Output:

```text
windows: 24
window boundaries (half-open [start, end)):
   2026-01-15T00:00:00+00:00
   2026-01-15T01:00:00+00:00
   2026-01-15T02:00:00+00:00
output rows: 96
first row: {'window': '2026-01-15T00:00:00+00:00', 'region': 'AMER', 'event_count': 60, 'revenue_eur': 24572.07}
```

24 windows, each `[start, start + 1h)`. The half-open convention means an event at exactly 01:00:00 belongs to the 01:00 window, not the 00:00 window — no double counting, no gaps.

### Exercise 4: the watermark and late-data path

Events that arrive after their window has been finalised are **late data**. Beam handles this with allowed lateness and a trigger; the simulator handles it with a reason code and a dead-letter path.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import (
    ingest_events,
    aggregate_events,
    bucket_by_window,
    partition_for_event,
)

with open("sample_data/events.csv", encoding="utf-8") as handle:
    accepted, _ = ingest_events(handle.read().splitlines())

# A watermark at T means: no event with a timestamp older than T will
# arrive again. Model it by fixing the watermark and re-running the
# aggregate over only the events at or after it.
watermark = "2026-01-15T12:00:00+00:00"

on_time = [
    row for row in accepted
    if str(row["event_dt"]) >= watermark
]

late = [
    row for row in accepted
    if str(row["event_dt"]) < watermark
]

print(f"watermark:            {watermark}")
print(f"events at/after:      {len(on_time)}")
print(f"events that are late: {len(late)}")
print()

partial = aggregate_events(on_time)
full = aggregate_events(accepted)
for region in sorted(full):
    a = int(partial.get(region, {}).get("event_count", 0))
    b = int(full[region]["event_count"])
    print(f"{region:6s} on-time={a:5d}  full={b:5d}  late={b - a:5d}")
```

The late count is the data that a late-firing trigger would deliver in a second update. **A pipeline with a late trigger and no late data path double-counts**, because the second emission includes the rows the first emission already counted. The fix is always the same: make the update an *absolute* value for that window, or a delta that is deduplicated by a deterministic key.

### Exercise 5: the dead-letter path, exactly as Beam would model it

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import (
    ingest_events,
    render_rejects_csv,
    reject_counts,
)

with open("sample_data/malformed_events.csv", encoding="utf-8") as handle:
    accepted, rejected = ingest_events(handle.read().splitlines())

print(f"accepted: {len(accepted)}")
print(f"rejected: {len(rejected)}")
print()
print(render_rejects_csv(rejected))
print("counts by reason:")
for reason, count in sorted(reject_counts(rejected).items()):
    print(f"  {reason:20s} {count}")
```

Output:

```text
accepted: 0
rejected: 12
counts by reason:
  bad_amount          1
  bad_timestamp       1
  missing_event_id    1
  missing_user_id     1
  negative_amount     1
  unknown_channel     1
  unknown_currency    1
  unknown_event_type  1
  unknown_region      2
  wrong_field_count   2
```

In a Beam pipeline the rejected rows are a second output PCollection, written to a dead-letter topic or table. In a streaming pipeline this is not optional: without it, a poison message either kills the pipeline or gets silently dropped.

### Exercise 6: cost Dataflow versus Dataproc on the same streaming workload

```python
import sys
sys.path.insert(0, "project/core")

from cost_model import estimate

# Dataflow bills for the workers actually used, and scales to near zero
# when idle. 24 vCPU-hours of active streaming:
dataflow = estimate("dataflow", vcpu_hours=24)
print(dataflow)
print()

# Dataproc bills for the cluster's whole life. The same 24 vCPU-hours
# of work inside a cluster that stays up for 24 hours costs the same,
# but a cluster that stays up for a week bills for 168 hours:
dataproc_idle = estimate("dataproc", vcpu_hours=168)
print(dataproc_idle)
print()

print(f"dataflow per vCPU-hour:  $0.0595")
print(f"dataproc per vCPU-hour:  $0.0476")
```

Dataflow's per-vCPU-hour rate is higher than Dataproc's, and it is still usually the cheaper choice for a *streaming* workload, because Dataflow's autoscaling means you do not pay for idle capacity while Dataproc does. For a *batch* workload that starts and stops, the two converge and Dataproc's lower rate wins. This asymmetry is worth remembering.

---

## 🛠️ Common Errors and Fixes

### 1. `RuntimeError: Beam SDK version ... is not supported by the Dataflow runner`

```text
RuntimeError: Beam SDK version 2.53.0 is not supported by the Dataflow
runner. Please use a supported version between 2.62.0 and 2.65.0.
```

**Cause.** The `apache-beam` package installed in your environment is outside the range the Dataflow service in your region supports. This is the single most common first-submission failure.

**Fix.** Pin the SDK version to one the service supports, and record it in a requirements file uploaded with the job:

```bash
pip install "apache-beam[gcp]==2.65.0" --index-url https://pypi.org/simple
```

To find the range the service actually accepts, describe a job that succeeded recently and read its SDK version:

```bash
gcloud dataflow jobs describe JOB_ID --region=us-central1 \
  --format="value(environment.sdkVersion)"
```

### 2. `apache_beam.transforms.core.ParDo.BadOutput`: the DoFn yielded a value of the wrong type

```text
ValueError: DoFn 'NormaliseEvent' produced a value of type '<class 'dict'>'
but the input PCollection's element type is '<class 'str'>'.
```

**Cause.** The upstream transform produced a different type than the downstream one expects. Usually a `Map` that returns a dict where the next step expects a string, or a `DoFn` that yields on one branch but not another.

**Fix.** Make the types consistent and declare them. The robust approach is to use `beam.Map` returning plain dictionaries with `typing.Dict[str, Any]`, and to add a `beam.Map` that normalises the shape right after parsing. Then declare the output type so the error surfaces at graph construction rather than at run time:

```text
| "Parse" >> beam.Map(parse_line).with_output_types(Dict[str, Any])
```

### 3. `RuntimeError: PipelineFnVisitor.arrows` — or a `pickle` failure in the Spark runner

```text
_pickle.PicklingError: Can't pickle <class 'function'>: attribute lookup failed
```

**Cause.** The Spark runner serialises `DoFn` closures with cloudpickle. A closure capturing something unpicklable — a socket, a logger bound to an open file, or a C extension — fails at submission time. The error appears at pipeline construction, not during execution.

**Fix.** Move non-picklable resources into `setup()` and tear them down in `teardown()`, and keep the `process` body free of captured state:

```python
class FetchRates(beam.DoFn):
    def setup(self):
        self.conn = connect_to_rates_db()

    def process(self, key):
        yield (key, self.conn.get(key))

    def teardown(self):
        self.conn.close()
```

If you are not planning to run on Spark, remove the Spark runner from your requirements and do not carry the constraint.

### 4. `KeyError: 'StreamingDataflowWorker' not found in pipeline` or a job stuck in `JOB_STATE_PENDING`

```text
ERROR: ... Job my-job-123 failed with state JOB_STATE_FAILED:
The job failed because it could not allocate resources in region us-central1.
```

**Cause.** Usually quota. Dataflow workers are Compute Engine instances, and the Dataflow service must be able to create them in the region. A CPU-quota exhaustion in `us-central1` fails the job.

**Fix.** Check the quota:

```bash
gcloud compute regions describe us-central1 --format="value(quotas.filter('metric:compute.googleapis.com/cpus').limit)"
```

Raise the quota or submit the job to a region with capacity. Second most common cause: the `temp_location` bucket is in a different region, which makes staging slow enough to look like a hang — put `temp_location` and `staging_location` in the same region as the job.

### 5. `direct_runner` fails on a pipeline that works on Dataflow

```text
ValueError: DirectRunner does not support windowing on unbounded collections
```

or

```text
NotImplementedError: The DirectRunner does not support GroupByKey on an
unbounded PCollection with a global window.
```

**Cause.** The Direct Runner is a single-JVM, local runner. It has no support for unbounded sources with global windows, no state backend, and no checkpointing. It is a development tool, not a test harness for streaming semantics.

**Fix.** Unit-test the *pure* transform logic outside Beam — which is exactly what the course project does with `pipeline_logic` — and test the streaming semantics on the Dataflow runner or the Flink runner, which implement them properly. Keep the Direct Runner for small bounded pipelines and for verifying that your pipeline graph constructs.

### 6. Streaming job shows `JOB_STATE_RUNNING` but processes nothing

```text
WARNING: Streaming job is running but no elements have been processed in
the last 10 minutes. Check the input subscription is receiving messages.
```

**Cause.** The job is healthy but the source is empty, or the subscription is not attached to the right topic, or the Dataflow service account lacks `pubsub.subscription.consume`.

**Fix.** Verify the source independently:

```bash
gcloud pubsub subscriptions pull projects/P/subscriptions/S --max-messages=5
```

Then check the service account's roles. Dataflow needs `roles/dataflow.worker` (which includes the Pub/Sub consume permission) — and if the job reads from BigQuery it also needs `roles/bigquery.dataViewer`. A job with no output is far more often a permissions problem or an empty source than a pipeline bug.

---

## 💡 Production Notes

- **Pin the Beam SDK version** in a requirements file uploaded with the job, and record which SDK version each running job was built with. Never rely on "latest".
- **Label every transform.** `| "Parse Event JSON" >> ...`. The Dataflow UI, the metrics, and the error messages all key off these labels.
- **Size `--temp_location` generously.** It holds shuffle spill files. Too small a bucket stalls the job; the symptom is a stage that runs for hours with no progress.
- **Use `CombinePerKey` rather than `GroupByKey` followed by a manual combine.** The service rewrites the combine into a partial aggregate before the shuffle, which can cut shuffled bytes by orders of magnitude.
- **Design for exactly-once from the start.** Deduplicate on a deterministic key derived from the data — never from arrival time. A retry that computes a different key is not a retry, it is a duplicate.
- **Set an explicit allowed lateness** and route beyond-late data to a dead-letter path with a reason-code count. Alert on that count: it is your early warning that the upstream event-time guarantee is broken.
- **Keep state small and window boundaries aligned.** Beam's state is proportional to the number of open windows times the keys per window. Misaligned windows double the state for no benefit.
- **Use templates for standard table movement** and custom jobs for real logic. Forking a template creates a maintenance liability that grows with every SDK upgrade.
- **Prefer BigQuery's own streaming write path** (`BigQueryIO.write` with `with_streaming_insert`) for high-volume writes, and reserve custom sinks for cases where you control the schema and need exactly-once semantics.
- **Monitor per-stage metrics**: elements in, elements out, and processing time. A stage that drops elements is a data-quality incident, and the Dataflow UI's element count is how you see it.

---

## 🔑 Key Takeaways

- Beam's model is three ideas: `PCollection` (a time-aware distributed collection), `PTransform` (a composable function between collections), and the `DoFn` (the element-processing unit with setup, teardown, state, and timers).
- The runner SDK harness is the contract between pipeline code and an engine. It supplies the runner, the coder, the state backend, and the environment — and each runner has its own coder, so portability has edges.
- Portability is real at the model level and partial at the API and guarantee level. The Spark runner does not support streaming. Exactly-once state is a Dataflow feature.
- Beam earns its cost because one pipeline definition covers batch and streaming, because time semantics are explicit, and because the abstractions expose the hooks that let Dataflow autoscale and checkpoint correctly.
- Dataflow compiles the pipeline into a job graph, fuses adjacent transforms, splits it into stages, and schedules those stages onto an autoscaled worker pool. The autoscaling is per-stage, which is why it beats Spark's static partitioning for bursty work.
- The SDK version trap is real: the service supports a moving window of SDK versions, so pin the version in a requirements file and verify against a recent successful job.
- Streaming correctness lives in windows, triggers, and watermarks. Fixed event-time windows with bounded allowed lateness plus a dead-letter path is the production pattern.
- Beam's verbosity is the price of a precise model. If you will only ever run on Dataflow, you still benefit from the discipline, but you should know you are paying for optionality you may not use.

---

## 📚 Practice Exercises

1. **Sketch the pipeline graph.** Write the Beam pipeline for the course workload as a chain of labelled transforms: read, parse, validate, window, group, combine, write. Identify which stage is the shuffle and which is the sink.
2. **Implement the trigger semantics.** Using `bucket_by_window` and `aggregate_by_window`, simulate Beam's "after processing time, or late data" trigger: emit once at window end, then emit an updated total each time a late event arrives for that window. Show that the final value equals the full aggregate.
3. **Prove the deduplication requirement.** Using `dedup_key` and `deduplicate`, show what happens if the identity key includes an arrival timestamp instead of the partition and `event_id`. Explain the failure mode in terms of a retry producing a different identity.
4. **Compare late-data strategies.** Model three policies — drop late data, include all late data, and include late data within 10 minutes — and report the resulting revenue per region for each. Identify which policy a "daily revenue" report should use and why.
5. **Design the dead-letter topic.** Specify the schema of a dead-letter message for the course pipeline: the reason code, the raw payload, the event timestamp, and the pipeline window. Explain why the reason code must be low-cardinality.
6. **Diagnose a stalled streaming job.** Write a diagnostic checklist for a Dataflow streaming job that reports `JOB_STATE_RUNNING` but produces no output: permissions, source subscription, region, and staging location. Order the steps by how often each is the cause.
7. **Cost a streaming pipeline.** Using `cost_model.estimate`, price a streaming job that runs continuously at 4 vCPUs for 30 days on Dataflow, and the equivalent Dataproc cluster. Then price a batch job that runs for 2 hours on both. Explain why the winner differs between the two cases.
8. **Decide Dataflow versus Dataproc.** For each of the four course pipeline stages — ingest, validate, aggregate, publish — name the tool you would use and defend the choice in two sentences. Finish with a one-paragraph recommendation for the whole workload.

---

## 📖 Further Reading

- [Apache Beam Programming Guide](https://beam.apache.org/documentation/programming-guide/)
- [Apache Beam: Beam SDKs and Runners](https://beam.apache.org/documentation/sdks/java/testing/beam-runners/)
- [Dataflow: About the Dataflow Service](https://cloud.google.com/dataflow/docs/concepts/overview)
- [Dataflow: Job Graphs and Stages](https://cloud.google.com/dataflow/docs/guides/job-graph-stages)
- [Dataflow: Templates](https://cloud.google.com/dataflow/docs/templates)
- [Dataflow: Stream Processing](https://cloud.google.com/dataflow/docs/guides/streaming-concepts)
- [Dataflow: Pricing](https://cloud.google.com/dataflow/pricing)
