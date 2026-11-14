# Dataflow and Apache Beam — Interview Questions

## 🎯 How to use this file

Ten questions on Cloud Dataflow and Apache Beam: how the model and the runner divide the work, what windowing and triggering actually guarantee, how exactly-once is achieved, how the service scales, and when Beam is the wrong choice.

The trap in this topic is that **Beam and Dataflow are not the same thing, and candidates routinely conflate them.** Beam is a programming model — an open-source SDK that defines what a pipeline *means*. Dataflow is one runner — Google's managed service that executes a Beam pipeline on autoscaling VMs. Every question here separates the two.

The second trap is the guarantee. "Dataflow is exactly-once" is a sentence that is **true about committed pipeline results and false about everything else**. Your side effects, your logs, and your external API calls are all at-least-once no matter what the service promises.

## Questions

### Q1. What is the difference between Apache Beam and Cloud Dataflow?

**Answer.** **Apache Beam is the programming model** — an open-source SDK that defines what a pipeline *means*. **Cloud Dataflow is one runner** — Google's managed service that executes a Beam pipeline on autoscaling workers. Beam code can also run on Flink, Spark, or a local Direct Runner.

**Mechanism.** The model supplies the abstractions: `PCollection` (a dataset, either **bounded** with a fixed size or **unbounded** and continuously updating), `DoFn` (your per-element logic), `ParDo` (applies a `DoFn` to every element), `GroupByKey`, `WindowInto`, and `Trigger`. The runner supplies the execution: it receives the pipeline, translates its transforms, I/O, aggregation, windowing and triggers into operations on its own platform, and runs it. In Dataflow that means uploading your code and dependencies to Cloud Storage, creating a job, allocating worker VMs, deploying the code, and orchestrating execution. Beam's supported SDKs are **Java, Python and Go**; its runners are **Direct Runner, Flink, Spark, Dataflow**, plus others.

**Trade-off.** Portability is the payoff and abstraction cost is the price. A hand-written Spark job can always do something Beam cannot express. And debugging a Beam pipeline means understanding two systems at once — the model *and* the runner — because the semantics come from one and the behaviour from the other.

**In practice.** The model/runner split is the thing to say out loud in an interview, because it shows you know which part is portable. Beam's portability claim is real but narrow: it is strongest on the **model** (windowing, triggers, exactly-once semantics) and weakest on **engine-specific optimisations**. The course's `bucket_by_window` and `aggregate_by_window` are exactly Beam's fixed-window and grouped-aggregation semantics expressed in pure Python — which is how you can unit-test windowing logic without a cluster.

**Failure story.** A team wrote a Beam pipeline and ran it on the Direct Runner locally, where it behaved perfectly — output was correct, order was right, nothing failed. Deployed to Dataflow streaming, it silently produced wrong results. The bug was a transform that relied on the Direct Runner's sequential element-by-element execution; in a distributed runner the elements arrived interleaved, and the transform's state was wrong. The lesson: **the Direct Runner is a semantics check, not a performance test**, and the only thing that proves a pipeline is correct is running it on the runner you will actually deploy to.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from service_catalog import SERVICES

service = SERVICES["dataflow"]
print(f"{service.name}: {service.summary}")
print("pricing:", service.pricing_model)
print("resources:", service.key_resources)

# The runner is one of several. Beam's model is what travels between them.
RUNNERS = ("Direct Runner", "Flink", "Spark", "Dataflow")
SDKS = ("Java", "Python", "Go")
print("beam runners:", ", ".join(RUNNERS))
print("beam sdks:", ", ".join(SDKS))
print("categories:", sorted({s.category for s in SERVICES.values()}))
```

Expected output:

```text
Dataflow: Managed runner for Apache Beam batch and streaming pipelines.
pricing: Per vCPU-hour, with streaming billed per worker-hour.
resources: ('Job', 'Template', 'Pipeline', 'Worker Pool')
beam runners: Direct Runner, Flink, Spark, Dataflow
beam sdks: Java, Python, Go
categories: ['AI & ML', 'Analytics', 'Compute', 'Databases', 'Integration', 'Security & Governance', 'Storage', 'Streaming & Messaging']
```

---

### Q2. What are Beam's core abstractions, and what does each one cost you?

**Answer.** Five: **`PCollection`** (the dataset), **`DoFn`** (your logic), **`ParDo`** (apply a `DoFn` to every element), **`GroupByKey`** (group by key), and **`Pipeline`** (the wiring). On top of those sit **`WindowInto`** and **`Trigger`**, which are what make streaming work.

**Mechanism.** A `PCollection` is bounded or unbounded; transforms consume and produce them. `ParDo` is the core parallel operation — it applies your `DoFn` to every element and collects zero or more outputs. `GroupByKey` groups elements sharing a key, and in the aggregation model elements are grouped by a common key *and window*, then combined with an operation that is **associative and commutative** — that property is what lets the runner combine partial results across workers in any order. `WindowInto` divides an unbounded collection into finite groups by element timestamp. A `Trigger` controls when aggregated output is emitted: with bounded data, after all input is processed; with unbounded data, when the **watermark** passes the window's end.

**Trade-off.** `GroupByKey` is the expensive one, and this is the single most important fact about Beam. Grouping requires a **shuffle** — moving data between workers by key — which is where the network, the state and the skew all live. In Beam the runner can often fuse a `ParDo` chain into one step, but a `GroupByKey` is a genuine barrier: nothing flows past it until the grouping is complete. A pipeline with many `GroupByKey`s is a pipeline with many shuffles.

**In practice.** The rule I apply: **push work as far past the `GroupByKey` as possible.** Do the filtering, mapping and enrichment *before* you group, and keep what you group by as narrow as you can. And always check the grouping key for skew — the same skew problem that strangles a BigQuery shuffle strangles a Beam `GroupByKey`, for exactly the same reason: one worker holds one key's rows and the rest wait. Beam's `WindowInto` + `Trigger` give you a second lever BigQuery SQL does not: you can emit *early and repeatedly* with a trigger instead of waiting for the window to close.

**Failure story.** A team wrote a Beam pipeline with a `GroupByKey` immediately after the read, grouping raw events by customer to fetch their profile, then doing the actual aggregation. The shuffle moved every event across the network, and the second aggregation was a second shuffle — while the profile fetch was a per-key side operation that needed only the distinct customer set. The fix was to deduplicate the keys *before* the `GroupByKey` and carry the events alongside as a side input, so the shuffle carried one row per customer instead of one per event. Runtime dropped by an order of magnitude and the bill with it.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import bucket_by_window, aggregate_by_window, hours_spanned

rows = [
    {"event_id": f"e{i}", "event_dt": f"2026-01-15T{h:02d}:30:00+00:00",
     "event_type": "order", "region": "AMER", "amount_eur": 10.0}
    for i, h in enumerate([0, 0, 1, 1, 1, 2, 2, 3])
]

print("hours spanned:", hours_spanned(rows))

windows = bucket_by_window(rows, window_seconds=3600)
for key in sorted(windows):
    print(f"  {key}: {len(windows[key])} events")

# The trigger fires per (window, key) — that is the output shape.
output = aggregate_by_window(rows, window_seconds=3600)
print("output rows:", len(output))
for row in output:
    print("  ", row)
```

Expected output:

```text
hours spanned: 4
  2026-01-15T00:00:00+00:00: 2 events
  2026-01-15T01:00:00+00:00: 3 events
  2026-01-15T02:00:00+00:00: 2 events
  2026-01-15T03:00:00+00:00: 1 events
output rows: 4
   {'window': '2026-01-15T00:00:00+00:00', 'region': 'AMER', 'event_count': 2, 'revenue_eur': 20.0}
   {'window': '2026-01-15T01:00:00+00:00', 'region': 'AMER', 'event_count': 3, 'revenue_eur': 30.0}
   {'window': '2026-01-15T02:00:00+00:00', 'region': 'AMER', 'event_count': 2, 'revenue_eur': 20.0}
   {'window': '2026-01-15T03:00:00+00:00', 'region': 'AMER', 'event_count': 1, 'revenue_eur': 10.0}
```

Eight events, four hourly windows, four output rows. The shuffle is over the *grouping key* — here `(window, region)` — and every one of those rows is a partial aggregate the runner can combine in any order.

*See also: [05-processing-and-orchestration.md Q4](05-processing-and-orchestration.md) for the Beam model from the processing-and-orchestration angle.*

---

### Q3. What is a window, and what does the trigger actually control?

**Answer.** A **window** is the finite group an unbounded collection is divided into, by element timestamp. The **trigger** controls *when the aggregated output for that window is emitted*. The window decides the data; the trigger decides the timing.

**Mechanism.** `WindowInto` defines how elements enter initial windows and how grouped windows merge. A `Trigger` then decides the emission point. With **bounded** data, output is emitted after all input is processed — there is only one chance. With **unbounded** data, the default trigger fires when the **watermark** passes the window's end. Beam also provides predefined triggers that can be combined. The watermark is the pipeline's declaration that no more events will arrive with a timestamp at or before it; data arriving after that is **late data**, and it goes to a side output (or is dropped, if you define none).

**Trade-off.** The window/trigger pair is the main latency-versus-completeness dial in a streaming pipeline. A window that is too wide is late but complete. A window that is too narrow is prompt but drops data that arrived late. A trigger that fires early (before the watermark) gives you lower latency at the cost of emitting a partial aggregate that you must then correct — which means your output is *not* a single final number but a series of updates, and every downstream consumer has to handle that. Firing exactly once at the watermark gives a clean number and maximum latency.

**In practice.** I set the window from the *business* grain — an hourly window because the report is hourly, not because it is convenient — and I set the watermark from the *observed lateness distribution*, not a guess: if 99.9% of events arrive within 90 seconds of their event time, the watermark sits at 90 seconds. And I always define a **side output for late data** so it can be reprocessed, because a silently dropped late event is a wrong number with no trace of how it went wrong.

**Failure story.** A team ran an hourly aggregation that emitted on a fixed 15-minute trigger, producing a partial result every 15 minutes and a final result at the hour. Downstream, a reconciliation job compared the pipeline's hourly total against the source database and raised an alarm every single hour for three weeks. The team initially assumed the pipeline was broken. It was not — it was emitting *by design*, and the reconciler had been written assuming one final value per window. The fix was on the consumer side: the reconciler had to sum the partials, or the trigger had to fire only at the watermark. They chose the reconciler, because the early emissions were worth more than the reconciliation effort.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import bucket_by_window, watermark_lag
from datetime import datetime, timezone, timedelta

rows = [
    {"event_id": "e1", "event_dt": "2026-01-15T10:00:00+00:00"},
    {"event_id": "e2", "event_dt": "2026-01-15T10:45:00+00:00"},
    {"event_id": "e3", "event_dt": "2026-01-15T11:20:00+00:00"},
]

# The window boundary is on the hour, regardless of when the event arrived.
windows = bucket_by_window(rows, window_seconds=3600)
for key in sorted(windows):
    print(f"{key}: {[r['event_id'] for r in windows[key]]}")

# The watermark: when the pipeline declares it is done with a window.
processing_time = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
lag = watermark_lag(rows, processing_time=processing_time)
print("watermark lag:", lag)
print("lag in seconds:", lag.total_seconds())

# An event that arrives after the watermark passed its window is LATE.
late = {"event_id": "late-1", "event_dt": "2026-01-15T10:30:00+00:00"}
watermark = processing_time - timedelta(minutes=20)
from pipeline_logic import parse_timestamp
is_late = parse_timestamp(late["event_dt"]) < watermark
print("late event:", late["event_id"], "-> late:", is_late)
```

Expected output:

```text
2026-01-15T10:00:00+00:00: ['e1', 'e2']
2026-01-15T11:00:00+00:00: ['e3']
watermark lag: 0:40:00
lag in seconds: 2400.0
late event: late-1 -> late: True
```

The 10:45 event belongs to the 10:00 window, not an 11:00 window — **window boundaries are on the clock, not on the data**. And `late-1` at 10:30 arrived after the watermark passed its window, so it is late data: it belongs in a side output, not in the window's result.

*See also: [05-processing-and-orchestration.md Q5](05-processing-and-orchestration.md) for the watermark and late-data treatment in the course's own module.*

---

### Q4. Dataflow's "exactly-once" — what is actually guaranteed?

**Answer.** Exactly-once applies to **committed pipeline results**: each input record is not lost, and results are committed without duplication. It does **not** guarantee exactly-once for your code, your logs, or your external side effects.

**Mechanism.** Streaming workers shuffle data between them; the sender retries until it gets an acknowledgement, giving at-least-once transfer with upstream backup. Each message carries a **unique ID**, and receivers retain processed IDs and discard repeats. Outputs are **checkpointed to stable storage** after each stage, preserving stable record IDs across retries, so a consistent store prevents duplicate output writes. To keep this cheap, workers use time-bucketed **Bloom filters** for fast duplicate checks, with older IDs removed by garbage collection; a system-timestamp watermark determines which IDs can be discarded and also reveals pipeline lag.

**Trade-off.** The limitations are the whole answer. Exactly-once does not apply to user-code execution or external side effects — **retries and worker failures can cause a transform or a remote call to run multiple times, possibly concurrently**. Logs show processing *attempts*, not successful commits, and may be duplicated, throttled or lost. Exactly-once also does not guarantee *completeness*: late records can be dropped depending on watermark and windowing policy. So a pipeline that writes to a REST API is not exactly-once no matter what the service says.

**In practice.** The rule: **exactly-once is a property of the pipeline's outputs, so anything you do outside the pipeline needs its own idempotency.** Custom sinks should be idempotent, and non-deterministic processing can be stabilised with `Reshuffle`, durable shuffles and `RequiresStableInput`. Prefer built-in Beam sinks where they exist. And note the interaction with Pub/Sub: Pub/Sub delivers at-least-once, so the same record may reach Dataflow more than once — Dataflow's exactly-once layer reconciles that upstream behaviour by deduplicating on stable IDs and checkpointing outputs, so duplicate Pub/Sub deliveries do not produce duplicate *committed results*. For non-deterministic sources the connector must supply unique record IDs; deterministic sources such as Pub/Sub Lite and Kafka use recorded offsets.

**Failure story.** A team relied on Dataflow's exactly-once to write to a payments API. The pipeline called the API, then wrote a success record to BigQuery. A worker was preempted between the API call and the BigQuery write, the stage retried, and the API was called **twice**. Dataflow's exactly-once guarantee was intact the whole time — the BigQuery record appeared exactly once — and the customer was charged twice. The guarantee was real and it covered the wrong thing. The fix was an idempotency key derived from the business transaction, sent to the API, so the second call was a no-op on the server side. Exactly-once in the pipeline, idempotency at the boundary.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import dedup_key, deduplicate, dedup_key_set

# Exactly-once handles duplicate DELIVERIES. It does not handle duplicate
# SIDE EFFECTS — those need their own idempotency key.
rows = [
    {"event_id": "txn-1", "event_dt": "2026-01-15", "amount_eur": 10.0},
    {"event_id": "txn-1", "event_dt": "2026-01-15", "amount_eur": 10.0},  # redelivered
    {"event_id": "txn-2", "event_dt": "2026-01-15", "amount_eur": 20.0},
]

deduped = deduplicate(rows, partition="20260115")
print("delivered:", len(rows))
print("committed:", len(deduped))

# The key that makes the EXTERNAL call idempotent too.
key = dedup_key("txn-1", "20260115")
print("idempotency key:", key)
print("stable across retries:", dedup_key("txn-1", "20260115") == key)
print("keys:", sorted(dedup_key_set(rows, partition="20260115")))
```

Expected output:

```text
delivered: 3
committed: 2
idempotency key: 20260115:txn-1
stable across retries: True
keys: ['20260115:txn-1', '20260115:txn-2']
```

Three delivered, two committed — the redelivery collapsed. But the idempotency key is the part **you** must carry to the API, because that is the layer exactly-once does not cover.

---

### Q5. What is the difference between exactly-once and at-least-once streaming mode?

**Answer.** **Exactly-once** is the default for Dataflow streaming jobs: no record is lost and results are committed without duplication. **At-least-once** guarantees no record is lost but retries can produce duplicates — and it costs materially less.

**Mechanism.** Exactly-once is the default for **regular** Dataflow streaming jobs. **Streaming templates** default according to their template metadata: a custom template supporting both modes defaults to exactly-once unless `defaultStreamingMode` says otherwise, and the console's streaming-mode selector is disabled when a template supports only one mode. At-least-once is enabled per job with the `streaming_mode_at_least_once` service option — `--dataflowServiceOptions=streaming_mode_at_least_once` in Java, `--dataflow_service_options=streaming_mode_at_least_once` in Python or Go. For templates it is `--additional-experiments=streaming_mode_at_least_once` (or `streaming_exactly_once`), and the two are mutually exclusive. Changing mode on a running job requires **launching a replacement job**.

**Trade-off.** Exactly-once gives stronger guarantees and typically consumes more resources. At-least-once often uses significantly fewer resources, with lower cost and latency, and its baseline duplicate rate is typically **under 1%** — though failures or repeated RPC calls can cause spikes. The catch is that at-least-once requires the **Streaming Engine with resource-based billing**, and the compute-unit rate is unchanged, so the saving comes from total resource consumption being lower rather than a cheaper unit. At-least-once is **incompatible with `BigQueryIO`'s `FILE_LOADS` method**; for BigQuery you use `STORAGE_API_AT_LEAST_ONCE`.

**In practice.** I pick at-least-once for **map-only workloads**, for pipelines with a downstream dedup step, and for sinks that cannot guarantee exactly-once delivery — with Pub/Sub input it is the optimised choice. I keep exactly-once for aggregations and business-critical work: fraud detection, threat detection, inventory dashboards. And the decision is not reversible in place: switching mode means a **replacement job**, so choose it at design time, not during an incident.

**Failure story.** A team switched a high-volume telemetry pipeline to at-least-once to cut cost, then found that a downstream BigQuery table had gained duplicate rows and a `COUNT(DISTINCT)`-free dashboard was overstating volume by 3%. The duplicate rate looked fine in aggregate — under 1% — but the pipeline had a *specific* failure mode: a worker was being preempted repeatedly during a shuffle, so one narrow window of the data was redelivered many times while the rest of the stream was clean. Percentages hide concentration. The lesson: **at-least-once duplicates are not uniformly spread**, so the fix has to be a dedup that keys on the record, not a hope that the rate stays low.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import deduplicate, dedup_key_set

# A narrow window hit by a repeated retry: duplicates concentrate,
# even when the overall rate is low.
rows = (
    [{"event_id": f"ok-{i}", "event_dt": "2026-01-15"} for i in range(990)]
    + [{"event_id": "hot-1", "event_dt": "2026-01-15"} for _ in range(10)]
)

delivered = len(rows)
committed = len(deduplicate(rows, partition="20260115"))
dupes = delivered - committed

print(f"delivered: {delivered}")
print(f"committed: {committed}")
print(f"duplicates: {dupes}")
print(f"overall rate: {dupes / delivered * 100:.2f}%")
print("but one key carried:", sum(1 for r in rows if r["event_id"] == "hot-1"), "copies")
print("dedup key:", sorted(dedup_key_set(rows, partition="20260115"))[:1])
```

Expected output:

```text
delivered: 1000
committed: 991
duplicates: 9
overall rate: 0.90%
but one key carried: 10 copies
dedup key: ['20260115:hot-1']
```

An overall rate of **0.90%** — under the 1% baseline — and all ten copies land on **one key**. The percentage hides the concentration, which is exactly why you cannot use a duplicate *rate* as your safety argument for at-least-once.

---

### Q6. How does Dataflow scale, and what is streaming work rebalancing?

**Answer.** Dataflow distributes processing across VMs and **adds or removes workers as needed**. Streaming work rebalancing is the separate mechanism that moves *work* between existing workers so a skewed stage does not leave workers idle.

**Mechanism.** The service parallelises across worker VMs, adds or removes workers as needed, and can dynamically rebalance work. Workers are deleted automatically when jobs finish or are cancelled. Work rebalancing addresses a different problem from autoscaling: autoscaling adds capacity, but if the work itself is unevenly distributed across the workers you already have, adding workers does not fix the straggler — it adds workers that also sit idle. Rebalancing redistributes the existing work.

**Trade-off.** Autoscaling costs money proportional to the workers you provision, and for a skewed pipeline it buys you idle workers. Rebalancing costs the time of moving state between workers, and it is disruptive — in-flight work has to be checkpointed and resumed elsewhere. So you reach for rebalancing when the imbalance is real, and for a bigger machine or a different key when it is structural.

**In practice.** The sequence I use: (1) check whether the stage is *skewed* (one key holding most of the rows) or simply *too small* (one worker doing everything because there is only one); (2) if skewed, rebalancing or salting; (3) if too small, scale up. And because workers are deleted when the job finishes, the cost of a streaming job is driven by **how many workers you keep alive**, not by how much data you processed. A pipeline that idles at 100 workers to handle a spike that lasts 10 minutes is paying for 100 workers for the whole day.

**Failure story.** A streaming job was configured with a fixed 200-worker pool to handle a predictable daily spike. The pipeline then processed the spike in 10 minutes and sat idle for the other 23 hours and 50 minutes — billing for 200 workers that did nothing. The fix was autoscaling with a low minimum worker count, which let the pool shrink to near zero between spikes. The catch the team hit next: autoscaling reacts *after* load appears, so a sudden burst has a ramp-up delay and the first few minutes of the spike are processed at the smaller size. The right answer was to size the *minimum* to the steady-state load, not to zero, so the ramp delay was covered without paying for the spike all day.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from service_catalog import SERVICES

service = SERVICES["dataflow"]
regions = service.availability.available
print(f"{service.name} available in {len(regions)} regions")
print("first three:", regions[:3])

# The billing shape: streaming bills for workers that stay alive.
from cost_model import DATAFLOW_PER_VCPU_HOUR, estimate

# A fixed 200-worker pool billing all day.
vcpu_per_worker = 4
workers = 200
hours = 24
fixed = estimate("dataflow", vcpu_hours=workers * vcpu_per_worker * hours,
                 apply_free_tier=False).total
print(f"fixed pool: {workers} workers x {hours}h -> ${fixed:.2f}")

# Autoscaled: the pool shrinks between spikes.
active_hours = 0.5
scaled = estimate("dataflow", vcpu_hours=workers * vcpu_per_worker * active_hours,
                  apply_free_tier=False).total
print(f"autoscaled: {workers} workers x {active_hours}h -> ${scaled:.2f}")
print(f"saving: {(1 - scaled / fixed) * 100:.1f}%")
```

Expected output:

```text
Dataflow available in 12 regions
first three: ('us-central1', 'us-east1', 'us-east4')
fixed pool: 200 workers x 24h -> $1142.40
autoscaled: 200 workers x 0.5h -> $23.80
saving: 97.9%
```

**$1,142.40 versus $23.80** for the same peak. This is the number that makes the point: in a streaming pipeline you pay for workers that are *alive*, so an idle pool is pure waste.

---

### Q7. What are Dataflow's job states, and which ones mean the job is still running?

**Answer.** A job moves through `JOB_STATE_STOPPED` → `JOB_STATE_PENDING` → `JOB_STATE_RUNNING` → a terminal state. The terminal states are **`JOB_STATE_DONE`**, **`JOB_STATE_CANCELLED`** and **`JOB_STATE_DRAINED`**. Once a job reaches a terminal state the service makes no further state updates.

**Mechanism.** A newly created job begins in `JOB_STATE_STOPPED` unless another state is specified, and it can be changed to running through `jobs.update`. The job enters `JOB_STATE_PENDING` when it starts, and `JOB_STATE_RUNNING` means it is executing and may later transition to a terminal state. `JOB_STATE_UPDATED` refers to the state of a job that was **replaced by another job** — this is the one that catches people, because it is not in the list of terminal states the way the others are. `JOB_STATE_DRAINED` is reached through a `jobs.update` request.

**Trade-off.** The trap here is treating "not `DONE`" as "still running". A `CANCELLED` job is not running and will never run again, and neither is a `DRAINED` one — but a monitoring script that only checks for `DONE` will keep waiting on both. And `JOB_STATE_UPDATED` means your job was *replaced*, which usually means someone launched a new version and the old one stopped — a normal operational event that a naive script will report as a failure.

**In practice.** The check I write is: **success is `DONE`; failure is `CANCELLED`; `DRAINED` and `UPDATED` are neither, and both mean "this job identity is finished — go look at the replacement."** For a streaming job, `DONE` is not the normal terminal state — a streaming pipeline runs until you stop it, so the script that watches a streaming job is watching for a state transition it triggered. And for a batch job, `PENDING` is where the interesting failures live: a job can sit in `PENDING` for a long time waiting for quota, and the difference between "queued" and "stuck" is a timeout you have to set.

**Failure story.** A production scheduler treated any state that was not `DONE` as "still in progress" and retried the job on a 30-minute timeout. It retried `CANCELLED` jobs forever — cancelling a job did not stop the scheduler from launching a new one, and the new one was cancelled by the same policy, and so on. The bill showed hundreds of identical batch jobs. The fix was a proper terminal-state check: `DONE` succeeded, `CANCELLED` failed loudly, and everything else was left alone. The general lesson is that **"not success" and "still running" are different states, and conflating them turns any terminal failure into an infinite retry loop.**

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")

TERMINAL = {"JOB_STATE_DONE", "JOB_STATE_CANCELLED", "JOB_STATE_DRAINED"}
SUCCESS = {"JOB_STATE_DONE"}

def classify(state: str) -> str:
    """Map a Dataflow job state to an operational decision."""
    if state in SUCCESS:
        return "succeeded"
    if state == "JOB_STATE_CANCELLED":
        return "failed - do not retry blindly"
    if state == "JOB_STATE_DRAINED":
        return "finished - check for a replacement job"
    if state == "JOB_STATE_UPDATED":
        return "replaced by another job"
    if state == "JOB_STATE_PENDING":
        return "queued - watch for a timeout"
    if state == "JOB_STATE_RUNNING":
        return "still running"
    return "unknown"

for state in [
    "JOB_STATE_PENDING",
    "JOB_STATE_RUNNING",
    "JOB_STATE_DONE",
    "JOB_STATE_CANCELLED",
    "JOB_STATE_DRAINED",
    "JOB_STATE_UPDATED",
]:
    print(f"{state:<24} {classify(state)}")

# The bug: "not DONE" is not "still running".
states = ["JOB_STATE_CANCELLED", "JOB_STATE_DRAINED", "JOB_STATE_UPDATED"]
naive = [s for s in states if s != "JOB_STATE_DONE"]
correct = [s for s in states if s not in TERMINAL]
print(f"\nnaive 'not DONE' says still running: {len(naive)}")
print(f"actually terminal: {len(correct)}")
```

Expected output:

```text
JOB_STATE_PENDING        queued - watch for a timeout
JOB_STATE_RUNNING        still running
JOB_STATE_DONE           succeeded
JOB_STATE_CANCELLED      failed - do not retry blindly
JOB_STATE_DRAINED        finished - check for a replacement job
JOB_STATE_UPDATED        replaced by another job

naive 'not DONE' says still running: 3
actually terminal: 1
```

The naive check treats **three** finished states as "still running". Only **one** of them is in the documented terminal set — `JOB_STATE_UPDATED` is not, and `JOB_STATE_DRAINED` is terminal but is *not* `DONE`, so a script that only checks for `DONE` waits on both. A scheduler must follow the replacement rather than wait on the old identity.

---

### Q8. When would you choose Dataflow over Dataproc, Spark or BigQuery?

**Answer.** Choose **Dataflow** when the pipeline is *continuous and stateful* — unbounded input, windowing, exactly-once — or when you want one codebase to run in both streaming and batch mode. Choose **Dataproc/Spark** for heavy, batch-only work with a large Spark ecosystem dependency. Choose **BigQuery** when the job is a query over data already there.

**Mechanism.** Dataflow and Dataproc differ in *what they optimise*. Dataflow is a managed runner for a model where **unbounded data is the default case** — streaming pipelines are first-class, exactly-once is on by default, and windowing and triggers are part of the model. Dataproc is managed Spark: the batch model, with streaming available but as a secondary mode. BigQuery is a serverless warehouse with no pipeline runtime at all — no windowing, no triggers, no exactly-once machinery; you get a SQL answer from data that is already loaded.

**Trade-off.** Dataflow's cost model is per worker-hour, so it is a poor fit for a job that finishes in 40 seconds — you pay for the worker startup and teardown. BigQuery is priced per byte scanned, so the two cost curves cross: for a *small* scan BigQuery's per-byte price is high and a small Dataflow job is cheaper, but BigQuery's cost grows with the data while a Dataflow job's cost is roughly fixed by its duration — so past about **0.2 TB** scanned, BigQuery wins on price. The real trade is not price, it is capability: BigQuery gives you a SQL answer over data already loaded, with no windowing, no triggers and no exactly-once machinery. And Dataflow's exactly-once is a *runtime* property you pay for in compute; if the work is a plain batch transform, you are buying machinery you will not use.

**In practice.** My decision order: if the answer is expressible as SQL over data in BigQuery, **write the SQL** — it is easier to maintain, and past a fraction of a terabyte it is also cheaper. If the pipeline is unbounded, needs windowing with early triggers, or must handle exactly-once end to end, use **Dataflow**. If it is batch-only and the team already lives in Spark, use **Dataproc**. And I use **Dataflow specifically when the same logic must run in both modes** — that is the case Beam's model-versus-runner split was designed for, and it is the one thing Spark does not give you.

**Failure story.** A team migrated a nightly batch aggregation to Dataflow "because streaming was the future". The job took 4 minutes of compute but 9 minutes wall-clock, because Dataflow spins up workers, deploys the code, runs, and tears down — and the pipeline's actual work was a 4-minute BigQuery scan of 2 TB. The Dataflow version cost **$0.95** against **$12.50** for the BigQuery scan, so on price alone it looked like a win. The real cost was elsewhere: the job now had a code dependency, a deployment step, and a worker-startup tail on every run, and the team could no longer fix a wrong number with a one-line SQL change. They migrated back. The lesson: **the streaming feature set is only worth paying for when the input is actually unbounded** — and "it was cheaper" is the wrong reason to migrate, because the expensive part of a pipeline is rarely the compute. The same scan at 100 TB would have cost **$625** in BigQuery against a Dataflow job that still cost **$0.95**, which is the actual argument for Dataflow: *the cost stops scaling with the data.*

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from cost_model import (estimate, DATAFLOW_PER_VCPU_HOUR, DATAPROC_PER_VCPU_HOUR,
                        BIGQUERY_ONDEMAND_PER_TB)

# The same 4-minute job, three ways.
work_vcpu_hours = 4 * 4        # 4 workers x 4 vCPU x 1 hour (padded for startup)

dataflow = estimate("dataflow", vcpu_hours=work_vcpu_hours, apply_free_tier=False).total
dataproc = estimate("dataproc", vcpu_hours=work_vcpu_hours, apply_free_tier=False).total
bigquery = estimate("bigquery", scanned_tb=2.0, apply_free_tier=False).total

print(f"Dataflow:  ${dataflow:>8.2f}   (${DATAFLOW_PER_VCPU_HOUR}/vCPU-hour)")
print(f"Dataproc:  ${dataproc:>8.2f}   (${DATAPROC_PER_VCPU_HOUR}/vCPU-hour)")
print(f"BigQuery:  ${bigquery:>8.2f}   (${BIGQUERY_ONDEMAND_PER_TB}/TB scanned)")

# Neither is universally cheaper: it depends on the job.
print(f"\nDataflow is {dataflow / bigquery:.2f}x the BigQuery cost at 2 TB")

# Crossover: BigQuery at $6.25/TB beats this Dataflow job (16 vCPU-hours) once
# 6.25 * TB > 16 * 0.0595  ->  TB > 16 * 0.0595 / 6.25
crossover_tb = work_vcpu_hours * DATAFLOW_PER_VCPU_HOUR / BIGQUERY_ONDEMAND_PER_TB
print(f"BigQuery becomes cheaper past {crossover_tb:.1f} TB scanned")

# The batch job that does not need a streaming runtime.
batch = estimate("dataflow", vcpu_hours=1 * 4 * 0.1, apply_free_tier=False).total
print(f"\nshort batch on Dataflow: ${batch:.2f} (paying for startup)")

# The point of Dataflow: the cost stops scaling with the data.
bigquery_100 = estimate("bigquery", scanned_tb=100.0, apply_free_tier=False).total
print(f"\nat 100 TB scanned:")
print(f"  BigQuery: ${bigquery_100:>8.2f}   (scales with the bytes)")
print(f"  Dataflow: ${dataflow:>8.2f}   (scales with the work, not the bytes)")
```

Expected output:

```text
Dataflow:  $    0.95   ($0.0595/vCPU-hour)
Dataproc:  $    0.76   ($0.0476/vCPU-hour)
BigQuery:  $   12.50   ($6.25/TB scanned)

Dataflow is 0.08x the BigQuery cost at 2 TB
BigQuery becomes cheaper past 0.2 TB scanned

short batch on Dataflow: $0.02 (paying for startup)

at 100 TB scanned:
  BigQuery: $  625.00   (scales with the bytes)
  Dataflow: $    0.95   (scales with the work, not the bytes)
```

Neither is universally cheaper. At 2 TB scanned BigQuery costs **more** than a small Dataflow job — but the crossover is remarkably low, around **0.2 TB**: past that, BigQuery's per-byte price wins, because the Dataflow job's cost is fixed at 16 vCPU-hours no matter how much data it reads. The real point is the last block: at 100 TB the same BigQuery scan costs **$625.00** while the Dataflow job still costs **$0.95**, because one curve scales with the bytes and the other scales with the work. That is the actual argument for Dataflow — not that it is cheaper per job, but that **its cost stops scaling with the data**.

And the line before that: a short batch job on Dataflow still pays for worker startup, so Dataflow is the wrong tool for sub-minute work regardless of the rate card.

---

### Q9. What are side inputs, and what is the difference between them and state?

**Answer.** A **side input** is a smaller dataset made available to every element of a main `PCollection` — a lookup table, configuration, or broadcast dictionary. **State** is per-key state that a transform maintains across the elements it processes. The difference is scope: side input is the *same* for all elements; state is *per key*.

**Mechanism.** Beam passes a side input as a keyed view the `DoFn` reads during processing. The critical rule is that a side input is read **per element**, so a lookup against a huge side input is a network round-trip per element — Beam offers broadcast-style side inputs for small data. State, by contrast, is keyed: a keyed transform maintains a value per key, which is what makes a running aggregate possible without a `GroupByKey`.

**Trade-off.** Side inputs are the cheapest way to enrich an element with reference data, but they are read per element, so the size matters and a 10 GB side input used as a per-element lookup will destroy the pipeline. State avoids the shuffle of a `GroupByKey` but has to be checkpointed, and it is bounded — unbounded state is the classic way a streaming pipeline runs out of memory. The other side input has to be considered too: a side input that changes mid-pipeline does **not** refresh for elements already in flight.

**In practice.** The rule: **if the reference data is small and changes rarely, use a side input; if it is large or changes often, use a join or a lookup against a keyed store instead.** For a side input I keep it under a few hundred MB and I accept that it is a *snapshot* — the pipeline picks up changes when it restarts, not while it runs. For state I always bound it: a per-key count is fine, a per-key list of every event ever seen is not, and the difference is a bounded window or a TTL.

**Failure story.** A team used a side input holding a 6 GB customer table and read it per element to attach a segment. The pipeline crawled — every element paid a lookup against a side input too large to be broadcast. The fix was to shrink the side input to the *fields actually used* and the rows actually needed (the segment lookup was a 3 MB table once narrowed to the two columns and the active customers), which let Beam broadcast it. The lesson: **a side input is a broadcast, and a broadcast is only free while it is small.**

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import aggregate_events

# A side input: the same small lookup for every element.
segments = {"u0": "enterprise", "u1": "consumer", "u2": "consumer"}

rows = [
    {"event_id": f"e{i}", "user_id": f"u{i % 3}", "event_dt": "2026-01-15T00:00:00+00:00",
     "event_type": "order", "region": "AMER", "amount_eur": 10.0}
    for i in range(6)
]

# Enrich per element — the side input is read for EVERY element.
enriched = [
    {**row, "segment": segments[row["user_id"]]}
    for row in rows
]
print("rows enriched:", len(enriched))

# ...which is why the side input must be small.
side_input_bytes = len(str(segments).encode())
print(f"side input size: {side_input_bytes} bytes")
print(f"broadcastable: {side_input_bytes < 10 * 1024 * 1024}")

# State is per KEY, not global: a running count per customer.
counts = {}
for row in rows:
    key = row["user_id"]
    counts[key] = counts.get(key, 0) + 1
print("state keys:", dict(sorted(counts.items())))
print("total state entries:", len(counts))
```

Expected output:

```text
rows enriched: 6
side input size: 56 bytes
broadcastable: True
state keys: {'u0': 2, 'u1': 2, 'u2': 2}
total state entries: 3
```

The side input is read **six times** — once per element — so its size multiplies across the pipeline. The state, by contrast, has **three** entries no matter how many events arrive, because it is keyed rather than global. That is the whole difference in one line.

*See also: [05-processing-and-orchestration.md Q6](05-processing-and-orchestration.md) for the side-input pattern applied to a currency-rate table.*

---

### Q10. How do you test a Beam pipeline, and what does "the pipeline passed" mean?

**Answer.** Test the **pure logic** as plain Python functions, then test the **semantics** against the runner you will deploy to. "The pipeline passed" means nothing until you know which of those two you tested.

**Mechanism.** Beam's model separates *what the pipeline computes* from *how it is executed*, which is exactly what makes it testable. The windowing and aggregation logic can be written as ordinary functions over a list of dicts — which is what the course's `bucket_by_window`, `aggregate_by_window` and `deduplicate` are — and unit-tested with no cluster at all. The **Direct Runner** runs the actual Beam pipeline locally, which checks that the *model* is wired correctly: the windows, the triggers, the serialization, the I/O. It does not check performance and, as the Q1 failure story shows, it can differ from a distributed runner on anything that depends on ordering or parallelism.

**Trade-off.** The Direct Runner is fast and free and it is not a distributed execution, so it will not surface skew, will not show you the real shuffle cost, and can mask ordering assumptions. Running against a small Dataflow job in batch mode catches the things the Direct Runner misses but costs real money and real time. The trade-off is not "cheap versus expensive" — it is **which layer of the stack you are testing**, and a bug can live in any layer.

**In practice.** Three layers, in order. (1) **Pure functions** — the windowing, the aggregation, the dedup, the validation — tested against the course's own verified outputs (4800 events, 12 malformed rows, 24 hourly windows producing 96 window-region rows, the per-region summary). (2) **The Direct Runner** — the pipeline graph, the I/O wiring, the triggers, run on every commit. (3) **A small Dataflow job** — run before release, to confirm the model behaves the same on the real runner. And the assertion discipline carries over from the rest of the bank: **assert on output row counts and on totals**, because a pipeline that runs to completion with wrong numbers is the failure mode that unit tests miss and staging catches.

**Failure story.** A team tested their Beam pipeline only with the Direct Runner and a unit test on the aggregation function. It passed both, and then in production the streaming job silently dropped 3% of events. The cause was a stateful transform that was correct when the Direct Runner processed elements one at a time, but lost records under the distributed runner's parallel execution. The tell was in the metrics — events in versus events committed — and nothing in the test suite compared them. The fix was a staging job against real Dataflow plus an input-versus-output assertion. The lesson: **a pipeline test that does not compare input volume to output volume cannot detect a pipeline that drops data.**

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import ingest_events, aggregate_by_window, bucket_by_window, deduplicate

# The clean file exercises the accept path; the malformed file exercises the
# reject path — a pipeline test that only sees clean data is not testing the
# pipeline.
good = open("sample_data/events.csv").read().splitlines()
bad = open("sample_data/malformed_events.csv").read().splitlines()

# The header is a line in the file but not an event. The malformed file has
# no header, so only the clean file needs it stripped.
is_header = lambda ln: ln.strip().lower().startswith("event_id,")
data_rows = len([ln for ln in good if ln.strip() and not is_header(ln)]) + \
            len([ln for ln in bad if ln.strip() and not is_header(ln)])
print("data rows  :", data_rows)

accepted, rejected = ingest_events(good + bad)
print("accepted   :", len(accepted))
print("rejected   :", len(rejected))

# Layer 1: the pure aggregation, checked against known totals.
# aggregate_by_window emits one row per (window, region); the window count
# is the number of distinct hourly buckets.
windows = bucket_by_window(accepted, window_seconds=3600)
output = aggregate_by_window(accepted, window_seconds=3600)
print("windows    :", len(windows))
print("window rows:", len(output))

# Layer 3: the assertion that catches a dropping pipeline.
assert len(accepted) + len(rejected) == data_rows, "events went missing"
print("in + rejected == in:", True)

# A second run of the same data must produce identical output — idempotency.
again = aggregate_by_window(deduplicate(accepted, partition="20260115"),
                             window_seconds=3600)
print("deterministic across runs:", again == output)

total_events = sum(r["event_count"] for r in output)
print("events accounted for:", total_events, "of", len(accepted))
assert total_events == len(accepted), "output row count does not match input"
print("no events dropped: True")
```

Expected output:

```text
data rows  : 4812
accepted   : 4800
rejected   : 12
windows    : 24
window rows: 96
in + rejected == in: True
deterministic across runs: True
events accounted for: 4800 of 4800
no events dropped: True
```

**4,812 rows in, 4,800 accepted, 12 rejected, and 24 hourly windows.** That last assertion — *events accounted for equals events accepted* — is the one that would have caught the 3% drop, and it costs one line. Note the two counts: **24 windows** but **96 window rows**, because the aggregation key is `(window, region)` and there are four regions. If you assert on row counts, assert on the key you actually aggregate by — asserting "24 output rows" would have failed against a correct pipeline. Also note the header: it is a line in the file but not an event, so a naive `len(lines)` comparison is off by one and the assertion fires on a healthy pipeline.

---

## 📚 Related chapters

- [5.3 — Apache Beam & Cloud Dataflow](../chapters/22-apache-beam-and-dataflow.md)
- [5.2 — Apache Spark & Cloud Dataproc](../chapters/21-apache-spark-and-dataproc.md)
- [5.4 — Airflow, Composer & Workflows](../chapters/23-airflow-composer-and-workflows.md)
- [4.2 — Pub/Sub](../chapters/17-pubsub.md)
- [3.2 — BigQuery Platform Overview](../chapters/13-bigquery-platform-overview.md)

For the hands-on version of the cost arithmetic in Q6 and Q8, see
[`practice/02-query-cost-lab.ipynb`](../practice/notebooks/02-query-cost-lab.ipynb).

## 📖 Further Reading

- [Apache Beam](https://beam.apache.org/)
- [Beam capability matrix — SDKs and runners](https://beam.apache.org/documentation/runners/capability-matrix/)
- [Dataflow overview](https://docs.cloud.google.com/dataflow/docs/overview)
- [Beam programming model](https://docs.cloud.google.com/dataflow/docs/concepts/beam-programming-model)
- [Exactly-once processing](https://docs.cloud.google.com/dataflow/docs/concepts/exactly-once)
- [Streaming modes — exactly-once vs at-least-once](https://docs.cloud.google.com/dataflow/docs/guides/streaming-modes)
- [Dataflow pricing](https://cloud.google.com/dataflow/pricing)
- [Dataflow monitoring overview](https://docs.cloud.google.com/dataflow/docs/guides/monitoring-overview)
- [Dataflow jobs API — job states](https://docs.cloud.google.com/dataflow/docs/reference/rest/v1b3/projects.locations.jobs)
