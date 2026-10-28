"""Generate notebooks/08-monitoring-and-cost.ipynb.

Every Beam API used here was verified against apache-beam 2.77.0 in the
course venv before the notebook was written:

  * Metrics.counter(namespace, name)  -- TWO args, no label parameter
  * counter.inc(value)                -- no `label=` keyword (TypeError)
  * result.metrics().query(...)       -- keyed by CATEGORY, not namespace
  * metric_result.key.metric.namespace / .name
  * metric_result.key.step
  * metric_result.committed
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nblib import build, code, md, setup_cell  # noqa: E402

CELLS: list[dict] = []

# ===========================================================================
# Title
# ===========================================================================
CELLS.append(md("""
# 08 · Monitoring & Cost

> **Module 8 · Production Operations · Lectures 8.2–8.4**

In this notebook you will:

- Read Dataflow's built-in monitoring signals and know which one to open first
- Instrument a real Beam pipeline with **custom `beam.metrics` counters**
- Understand autoscaling: the three knobs, the loop, and the two failure modes
- Build a **vCPU-hour cost model** and work a cost worksheet end to end
- Price a forgotten streaming job — the failure that actually shows up on invoices
- Measure a pipeline locally and extrapolate to a cloud estimate

---

Everything here runs on your laptop. No GCP account, no credentials, no bill.
The only thing that is "simulated" is the cloud itself — the *arithmetic* is
exactly the arithmetic you have to do before you press the button.
"""))

CELLS.append(setup_cell())

# ===========================================================================
# 1. The monitoring model
# ===========================================================================
CELLS.append(md("""
## 1. The monitoring model: what Dataflow already tells you

Before you write a single custom metric, you should know what the platform
gives you for free. Dataflow exposes a fixed set of signals per job.

| Signal | Namespace | What it measures | Why you care |
|---|---|---|---|
| `JOB_STATE_*` | system | `PENDING` → `RUNNING` → `DONE` / `FAILED` / `CANCELLED` | The job's lifecycle |
| `worker_health` | system | Worker status codes | Are workers dying and being replaced? |
| `max_workers` | system | Peak worker count reached | Did the autoscaler need to scale up? |
| `bytes_counter` | system | Bytes read from input | Is my input actually arriving? |
| `bundle_size` | system | Elements per bundle | Is the bundling doing its job? |
| `estimated_cpu` | system | CPU-seconds consumed | The real driver of cost |
| `total_gb_processed` | system | GB of data processed | A second cost signal |

Two of these deserve emphasis, because they answer the two questions you
actually get paged for:

- **"Is the job stuck or just slow?"** → compare `max_workers` and
  `estimated_cpu` over time. Flat `estimated_cpu` with flat `max_workers`
  means the job is *idle*, not *busy*. A stuck job and a healthy job that
  has finished its work look identical on a dashboard unless you look at
  whether the CPU signal is still moving.
- **"Why was this job expensive?"** → `estimated_cpu` is the answer. Dataflow
  bills **vCPU-hours**, so the CPU-seconds your job burned *are* the invoice.

The crucial thing the platform *cannot* tell you is whether your data was
**correct**. Dataflow can tell you it processed 4.2 GB and took 400 vCPU-hours.
It cannot tell you that 30% of those rows were silently dropped. That gap is
where custom metrics live.
"""))

CELLS.append(code("""
# The system namespace is where Dataflow's own metrics live.  We can read
# them back from a local pipeline result, which is how we are going to
# learn the API before using it on a real job.
import tempfile

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions

options = PipelineOptions()
options.view_as(StandardOptions).runner = "BundleBasedDirectRunner"

out_dir = tempfile.mkdtemp(prefix="nb08-probe-")

with beam.Pipeline(options=options) as p:
    (p
     | "Read" >> beam.Create(
         [{"region": "AMER", "amount": 10.0},
          {"region": "APAC", "amount": 20.0},
          {"region": "AMER", "amount": 5.0}])
     | "Write" >> beam.io.WriteToText(out_dir))

# `pipeline_result.metrics()` gives you the metric results of the *executed*
# pipeline.  Querying with an empty filter returns everything, grouped by
# metric CATEGORY.
pipeline_result = p.result
all_metrics = pipeline_result.metrics().query()
print("top-level keys (metric CATEGORIES):", sorted(all_metrics.keys()))
for category, results in sorted(all_metrics.items()):
    names = sorted({r.key.metric.name for r in results})
    namespaces = sorted({r.key.metric.namespace for r in results})
    print(f"  {category:<16} {len(results):>3} result(s)  "
          f"namespaces={namespaces} names={names}")
"""))

# ===========================================================================
# 2. Custom metrics
# ===========================================================================
CELLS.append(md("""
## 2. Custom metrics: the API you actually need

`apache_beam.metrics` gives you three metric types:

| Type | Constructor | What it tracks | Typical use |
|---|---|---|---|
| Counter | `Metrics.counter(ns, name)` | Monotonic total | Rows read, rows rejected |
| Gauge | `Metrics.gauge(ns, name)` | Last value set | Current backlog depth |
| Distribution | `Metrics.distribution(ns, name)` | Percentiles | Latency of each record |

The call signature is `Metrics.<type>(namespace, name)` — **two arguments**,
and the namespace should be **stable across runs**. It is your series name,
and changing it breaks every dashboard you ever built.

### The rule that actually bites: the name must be constant

**A metric's namespace and name must be compile-time constants.**

Beam identifies a metric by its `(namespace, name)` pair. If you build the
name from the *data* — `f"revenue_{region}"` — then every distinct value
produces a distinct metric. Three regions is fine. Thirty thousand customer
IDs is a metric-cardinality explosion that will overwhelm the monitoring
backend and get your job throttled or rejected.

| Metric name | Safe? | Why |
|---|---|---|
| `"rows_seen"` | Yes | One metric, one time series |
| `f"rejected_{reason}"` | **No** | Unbounded series count |
| `f"revenue_{customer_id}"` | **No** | Unbounded series count |

### And a surprise: Beam 2.77 counters have no labels

You might expect to fix the cardinality problem with a *label* —
`counter.inc(label={"region": "AMER"})`. That is the natural instinct, and
in some Beam versions it is the API. **In Beam 2.77 it does not exist**,
and the error is not subtle:

```
TypeError: __call__() got an unexpected keyword argument 'label'
```

The signature is `Metrics.counter(namespace, name)` — two arguments, no
label parameter — and the updater is `inc(value)`. The `MetricName`
dataclass *has* a `labels` field, but the public `Metrics.counter()`
constructor does not populate it.

So what do you actually do when you need per-region visibility? You have
three options, and the course project uses the first:

1. **A fixed, bounded set of metric names.** You know the dimensions in
   advance (`rows_seen_amer`, `rows_seen_apac`, ...). Simple, and works.
2. **Aggregate counters by category**, and keep the fine-grained breakdown
   in the *output data* rather than in the metrics.
3. **Use a different mechanism** — a `Distribution` for percentiles, or
   write the breakdown to BigQuery and query it there.

We will demonstrate the cardinality explosion live in §2.4, and show the
bounded-name fix next to it. The explosion fails *silently* on a laptop and
fails loudly in production, which is exactly the kind of bug worth knowing
about.
"""))

CELLS.append(code("""
from apache_beam.metrics import Metrics, MetricsFilter

# --- The correct pattern -------------------------------------------------
# A class-level counter: one object, one metric, one time series.

class GoodInstrumentedFn(beam.DoFn):
    \"\"\"Counts every row it sees, plus the revenue it carries.\"\"\"

    ROWS_SEEN = Metrics.counter("dataflow_course", "rows_seen")
    REVENUE_EUR = Metrics.gauge("dataflow_course", "revenue_eur")

    def process(self, row):
        GoodInstrumentedFn.ROWS_SEEN.inc()
        GoodInstrumentedFn.REVENUE_EUR.set(row["amount"])
        yield row


# --- The cardinality trap -------------------------------------------------
# The metric NAME is built from the element.  Every distinct element value
# becomes its own metric.

class CardinalityTrapFn(beam.DoFn):
    \"\"\"One metric per distinct region -- an explosion waiting to happen.\"\"\"

    def process(self, row):
        Metrics.counter("dataflow_course", f"seen_{row['region']}").inc()
        yield row


# --- The bounded fix ------------------------------------------------------
# The dimensions are known in advance, so the metric names are too.

KNOWN_REGIONS = ("AMER", "APAC", "EMEA", "LATAM")


class BoundedNamesFn(beam.DoFn):
    \"\"\"One counter per KNOWN region -- a bounded, fixed set of metrics.\"\"\"

    def process(self, row):
        region = row["region"]
        if region in KNOWN_REGIONS:
            Metrics.counter("dataflow_course", f"bounded_seen_{region.lower()}").inc()
        yield row


# --- The attempt to use a label -------------------------------------------
# This is the API you would expect.  It does not exist in Beam 2.77.
try:
    Metrics.counter("dataflow_course", "probe").inc(label={"region": "AMER"})
    print("label= accepted -- labels are available")
except TypeError as exc:
    print(f"label= REJECTED -> TypeError: {exc}")

print()
print("Metrics.counter     :", hasattr(Metrics, "counter"))
print("Metrics.gauge       :", hasattr(Metrics, "gauge"))
print("Metrics.distribution:", hasattr(Metrics, "distribution"))
print("MetricsFilter methods:",
      [m for m in dir(MetricsFilter) if m.startswith("with_")])
"""))

CELLS.append(md("""
### 2.3 Reading metrics back

The read API has three moving parts:

- `pipeline_result.metrics()` → the whole metric store for the run
- `.query(filter)` → a dict keyed by **category**, not by namespace
- `MetricsFilter()` → narrows by namespace, name, or step

The shape surprises people, so here it is exactly:

```python
{
  "counters":      [MetricResult, ...],
  "gauges":        [MetricResult, ...],
  "distributions": [MetricResult, ...],
  "histograms":    [...],
  "string_sets":   [...],
  "bounded_tries": [...],
}
```

The top-level keys are the metric **categories**. The namespace and name
live on each result, at `metric_result.key.metric.namespace` and
`metric_result.key.metric.name`. There is no top-level namespace map —
you have to walk the list yourself.

| Filter method | Narrows to |
|---|---|
| `with_namespace("ns")` | one namespace |
| `with_name("name")` | one metric name within the namespace |
| `with_step("step")` | one transform step |

One more surprise: the same metric name can appear under **several steps**,
each with its own committed value. A counter incremented in two different
`ParDo`s reports as two results, and you have to sum them.
"""))

CELLS.append(code("""
rows = [
    {"region": "AMER", "amount": 10.0},
    {"region": "APAC", "amount": 20.0},
    {"region": "AMER", "amount": 5.0},
    {"region": "EMEA", "amount": 7.5},
]

with beam.Pipeline(options=options) as p:
    (p
     | "Rows" >> beam.Create(rows)
     | "Good" >> beam.ParDo(GoodInstrumentedFn())
     | "Trapped" >> beam.ParDo(CardinalityTrapFn())
     | "Bounded" >> beam.ParDo(BoundedNamesFn()))

pipeline_result = p.result
pipeline_result.wait_until_finish()

queried = pipeline_result.metrics().query(
    MetricsFilter().with_namespace("dataflow_course")
)

print("top-level keys (categories):", sorted(queried.keys()))
print()
print("counters in the 'dataflow_course' namespace:")
for metric_result in queried.get("counters", []):
    metric = metric_result.key.metric
    print(f"  {metric.name:<20} committed={metric_result.committed!s:<6} "
          f"step={metric_result.key.step}")
"""))

CELLS.append(md("""
### 2.4 The failure, demonstrated

Look at the counters printed above:

- `Good` produced exactly **one** metric, `rows_seen`, with a committed
  value of 4 — the four input rows.
- `Trapped` produced **one metric per distinct region**, because the metric
  name was built from the data. Four rows, three metrics.

Now imagine the same code keyed on `customer_id` instead of `region`. The
metric count becomes the number of distinct customers, and the Dataflow
monitoring backend has to store, index, and alert on every one of them.
The job does not crash. The job gets *slow*, then starts getting throttled,
and the pipeline falls behind with no obvious cause.

This is the failure mode a laptop will never warn you about, because on a
laptop the "monitoring backend" is a dictionary in memory.

### The fix, side by side

```python
# WRONG -- unbounded series count.
Metrics.counter("ns", f"seen_{row['region']}").inc()

# RIGHT, when the dimensions are known in advance -- bounded set of names.
if row["region"] in KNOWN_REGIONS:
    Metrics.counter("ns", f"bounded_seen_{row['region'].lower()}").inc()

# RIGHT, when they are not -- aggregate by category, and keep the
# fine-grained breakdown in the output data, not in the metrics.
Metrics.counter("ns", "rows_seen").inc()
```

The `Bounded` step above shows the middle option in action: the metric
names are `bounded_seen_amer`, `bounded_seen_apac`, and so on — a set
fixed by `KNOWN_REGIONS`, not by the data. An unknown region would simply
not be counted, which is a decision you make deliberately, not by
accident.
"""))

CELLS.append(code("""
# Count the series explosion directly -- the number that matters.
def series_for(namespace, category="counters"):
    names = []
    for metric_result in queried.get(category, []):
        metric = metric_result.key.metric
        if metric.namespace == namespace:
            names.append(metric.name)
    return sorted(names)


all_names = series_for("dataflow_course")
print(f"distinct counters in namespace 'dataflow_course': {len(all_names)}")
for name in all_names:
    print("   ", name)
print()

region_scoped = [n for n in all_names if n.startswith("seen_")]
bounded = [n for n in all_names if n.startswith("bounded_seen_")]
print(f"metrics whose NAME encodes the region (the trap): {len(region_scoped)}")
for name in region_scoped:
    print("   ", name)
print()
print(f"metrics from the bounded fix                    : {len(bounded)}")
for name in bounded:
    print("   ", name)
print()
print("Same information, same number of series -- but the bounded version")
print("gets there without ever building a name from the data, so the set")
print("of possible names is fixed by KNOWN_REGIONS, not by the data.")
print()
print("Every name in the trap is a separate time series the monitoring")
print("backend has to store.  With four regions that is fine.  With four")
print("million customer IDs it is an outage.")
"""))

CELLS.append(code("""
# Reading one specific metric back, and summing across steps.
filter_ = (MetricsFilter()
           .with_namespace("dataflow_course")
           .with_name("rows_seen"))
by_step = pipeline_result.metrics().query(filter_)

total = 0
print(f"{'step':<14} {'committed':>10}")
for metric_results in by_step.values():
    for metric_result in metric_results:
        committed = metric_result.committed
        if isinstance(committed, list):
            committed = committed[0] if committed else None
        total += committed or 0
        print(f"{metric_result.key.step:<14} {committed!s:>10}")
print(f"{'TOTAL':<14} {total:>10}   (4 input rows)")
"""))

# ===========================================================================
# 3. Autoscaling
# ===========================================================================
CELLS.append(md("""
## 3. Autoscaling: three knobs and one loop

Dataflow's autoscaler is a **feedback loop**, not a static sizing rule. It
observes the backlog and the current worker count, and it adjusts.

Three knobs control it:

| Knob | Flag | What it bounds | Default |
|---|---|---|---|
| Minimum workers | `--min_workers` | The floor — always-on cost | 0 for streaming, 1 for batch |
| Maximum workers | `--max_workers` | The ceiling — worst-case burst | 20 for streaming, 100 for batch |
| Autoscaling mode | `--autoscaling_algorithm` | *How* it reacts | `Basic` / `ScaleUp` / `Standard` |

The three modes, in increasing sophistication:

| Mode | Behaviour | When to use it |
|---|---|---|
| `Basic` | Only scales up when the backlog grows | Simple, conservative, may lag |
| `ScaleUp` | Scales up eagerly; scales down only when idle | Steady, predictable workloads |
| `Standard` | Uses a backlog-age heuristic | The current default for streaming |

### The loop, in one line

> Backlog grows → workers increase → throughput rises → backlog shrinks →
> workers idle → workers decrease → repeat.

### The two failure modes

Every autoscaling bug is one of these two, and they pull in opposite
directions:

1. **Ceiling too low.** The backlog grows faster than the maximum worker
   count can ever absorb. The job is *alive and healthy* — it just never
   catches up. Autoscaling cannot help because it is already at the wall.
2. **Floor too high.** The minimum worker count is set for peak, so a
   trickle of traffic still pays for a full cluster. The job is *idle* and
   still burning money.

Both are invisible in a dashboard that only shows "is the job running?" and
are obvious the moment you plot backlog against worker count.
"""))

CELLS.append(code("""
# A miniature model of the autoscaler loop, so the feedback behaviour is
# concrete.  This is NOT Beam's autoscaler -- it is the shape of the loop,
# written out so you can watch it converge (or fail to).
from dataclasses import dataclass


@dataclass
class AutoscalerState:
    \"\"\"The signals the autoscaler actually reacts to.\"\"\"

    workers: int
    backlog: int
    max_workers: int
    min_workers: int
    throughput_per_worker: int = 100


def step(state, demand):
    \"\"\"One tick: data arrives, workers work, then the count adjusts.

    The order matters, and it is the order a real autoscaler uses:
    observe the backlog, decide the new worker count, and let the new
    workers do their work on the next tick.
    \"\"\"
    # 1. New data arrives.
    state.backlog += demand
    # 2. The current workers drain what they can.
    capacity = state.workers * state.throughput_per_worker
    state.backlog = max(0, state.backlog - capacity)
    # 3. Scale UP if anything is left over -- we cannot keep up even at
    #    the current size.
    if state.backlog > 0:
        state.workers = min(state.max_workers, state.workers * 2)
    # 4. Scale DOWN when the backlog is comfortably below capacity.
    elif state.workers > state.min_workers:
        state.workers = max(state.min_workers, state.workers // 2)
    return state


def simulate(demand, *, max_workers=20, min_workers=1, steps=12, label=""):
    state = AutoscalerState(workers=min_workers, backlog=0,
                            max_workers=max_workers, min_workers=min_workers)
    print(f"\\n{label}")
    print(f"  demand={demand}/tick, max_workers={max_workers}, "
          f"min_workers={min_workers}")
    print(f"  {'tick':>4} {'workers':>8} {'backlog':>9}")
    for tick in range(steps):
        state = step(state, demand)
        marker = "  <-- at the ceiling" if state.workers == state.max_workers else ""
        print(f"  {tick:>4} {state.workers:>8} {state.backlog:>9}{marker}")
    converged = state.backlog == 0
    print(f"  -> final backlog {state.backlog}, workers {state.workers}"
          f"  ({'CONVERGED' if converged else 'NOT CONVERGED'})")
    return state


# A. Demand 150/tick, capacity 100/worker/tick -> 2 workers keep up.
simulate(demand=150, label="A. Ceiling is high enough")
# B. Same demand, ceiling of 1 worker.  The backlog grows forever.
simulate(demand=150, max_workers=1, label="B. Ceiling too LOW (failure mode 1)")
# C. Demand 10/tick, but the floor is 8 workers -- 7 of them are idle.
simulate(demand=10, max_workers=20, min_workers=8,
         label="C. Floor too high (failure mode 2)")
"""))

# ===========================================================================
# 4. The cost model
# ===========================================================================
CELLS.append(md("""
## 4. The cost model: vCPU-hours

This is the arithmetic. Dataflow bills the resources your job actually
uses, per second, with a minimum billing quantum.

### The formulas

**Batch** (resources exist only while the job runs):

```
cost = workers * machine_type_vcpus * (runtime_seconds / 3600) * vcpu_hour_rate
```

**Streaming** (resources exist continuously — *this is the dangerous one*):

```
cost = workers * machine_type_vcpus * (wall_clock_seconds / 3600) * vcpu_hour_rate
          + data_processed_gb * per_gb_rate
```

The streaming formula is the same as the batch one, except the divisor is
**wall-clock time, not work time**. A streaming job that receives 12 events
an hour still holds a full cluster open for 24 hours.

### The rates

Prices are regional and change; treat these as *shape* numbers, not quotes:

| Machine type | vCPUs | vCPU-hour rate (illustrative) |
|---|---|---|
| `n1-standard-2` | 2 | $0.055 |
| `n1-standard-4` | 4 | $0.055 |
| `n1-standard-8` | 8 | $0.055 |

| Other charge | Rate (illustrative) |
|---|---|
| Streaming, per GB processed | $0.015 |
| Cross-region traffic, per GB | $0.05 |

Two things the model does *not* hide:

- **Cross-region traffic is brutal.** Streaming data crossing a region
  boundary costs 3–4× more per GB than the processing itself.
- **Minimum runtime.** A batch job that finishes in 40 seconds still pays
  for the startup and teardown of its workers.

### The most important cost lever

Runtime is `work / throughput`, and throughput is *not* linear in workers.
Doubling workers on a pipeline with a hot key gives you almost nothing —
the hot key is the serial bottleneck. **Optimisation pays for itself
through runtime, and a skew fix can save more money than a cheaper machine
type ever will.**
"""))

CELLS.append(code("""
# The cost model, as code.
RATES = {
    "n1-standard-2": 0.055,
    "n1-standard-4": 0.055,
    "n1-standard-8": 0.055,
}
VCPU = {
    "n1-standard-2": 2,
    "n1-standard-4": 4,
    "n1-standard-8": 8,
}
STREAMING_PER_GB = 0.015
INTERREGION_PER_GB = 0.05


def batch_cost(*, workers: int, machine_type: str, runtime_seconds: float) -> float:
    \"\"\"Cost of a batch job that ran for `runtime_seconds`.\"\"\"
    if machine_type not in RATES:
        raise KeyError(f"unknown machine type: {machine_type}")
    vcpu_hours = VCPU[machine_type] * (runtime_seconds / 3600.0)
    return workers * vcpu_hours * RATES[machine_type]


def streaming_cost(*, workers: int, machine_type: str,
                   wall_clock_seconds: float, gb_processed: float = 0.0,
                   cross_region_gb: float = 0.0) -> float:
    \"\"\"Cost of a streaming job, which bills for wall-clock time.\"\"\"
    vcpu_hours = VCPU[machine_type] * (wall_clock_seconds / 3600.0)
    compute = workers * vcpu_hours * RATES[machine_type]
    return (compute
            + gb_processed * STREAMING_PER_GB
            + cross_region_gb * INTERREGION_PER_GB)


def fmt_usd(amount: float) -> str:
    return f"${amount:,.2f}"


print("batch, 4 x n1-standard-2, 10 minutes:")
print("   ", fmt_usd(batch_cost(workers=4, machine_type="n1-standard-2",
                               runtime_seconds=600)))
print("streaming, 4 x n1-standard-2, 24 hours, 50 GB:")
print("   ", fmt_usd(streaming_cost(workers=4, machine_type="n1-standard-2",
                                    wall_clock_seconds=86400, gb_processed=50)))
"""))

# ===========================================================================
# 5. The cost worksheet
# ===========================================================================
CELLS.append(md("""
## 5. The cost worksheet

A worksheet is the difference between "we think it costs $3" and "we know
it costs $3.41, and here is the sensitivity table showing what happens if
we double the workers".

Here is a nightly batch job with a realistic shape:

| Parameter | Value |
|---|---|
| Schedule | Daily, 02:00 UTC |
| Machine type | `n1-standard-2` (2 vCPU) |
| Workers (peak) | 8 |
| Runtime | 22 minutes |
| Input size | 40 GB |
| Output size | 2 GB |

We compute the monthly cost and then ask three questions:

1. What if runtime doubles (a bad week, or a data quality regression)?
2. What if we scale out to 16 workers to halve the runtime? (Does it save?)
3. What is the break-even runtime at 16 workers?

Question 2 is the interesting one, and the answer is usually **no**,
because the cost of a batch job is `workers × time` and halving the time
by doubling the workers is *exactly break-even* — before you account for
the fact that more workers also means more shuffling.
"""))

CELLS.append(code("""
# --- The worksheet parameters ---------------------------------------------
NIGHTLY = {
    "schedule_per_month": 30,          # nightly
    "machine_type": "n1-standard-2",
    "workers": 8,
    "runtime_seconds": 22 * 60,        # 22 minutes
    "input_gb": 40.0,
    "output_gb": 2.0,
}

monthly = batch_cost(
    workers=NIGHTLY["workers"],
    machine_type=NIGHTLY["machine_type"],
    runtime_seconds=NIGHTLY["runtime_seconds"],
) * NIGHTLY["schedule_per_month"]

print("=== Nightly batch worksheet ===")
print(f"  machine type        : {NIGHTLY['machine_type']} "
      f"({VCPU[NIGHTLY['machine_type']]} vCPU)")
print(f"  workers (peak)      : {NIGHTLY['workers']}")
print(f"  runtime             : {NIGHTLY['runtime_seconds'] // 60} min "
      f"({NIGHTLY['runtime_seconds']} s)")
print(f"  runs per month      : {NIGHTLY['schedule_per_month']}")
print()
per_run = batch_cost(
    workers=NIGHTLY["workers"],
    machine_type=NIGHTLY["machine_type"],
    runtime_seconds=NIGHTLY["runtime_seconds"],
)
print(f"  cost per run        : {fmt_usd(per_run)}")
print(f"  cost per month      : {fmt_usd(monthly)}")
print(f"  annualised          : {fmt_usd(monthly * 12)}")
print()
print("  Note: this is the COMPUTE cost only.  Storage for 2 GB of output")
print("  per night is ~$0.12/month and is not the interesting number.")
"""))

CELLS.append(code("""
# --- Sensitivity ----------------------------------------------------------
def cost_for(workers: int, runtime_seconds: int) -> float:
    return batch_cost(workers=workers, machine_type=NIGHTLY["machine_type"],
                      runtime_seconds=runtime_seconds) * NIGHTLY["schedule_per_month"]


baseline = cost_for(NIGHTLY["workers"], NIGHTLY["runtime_seconds"])

print("=== Sensitivity: runtime regression ===")
print(f"  {'runtime':>10} {'monthly':>12} {'vs baseline':>14}")
for factor in (1, 2, 4, 8):
    runtime = NIGHTLY["runtime_seconds"] * factor
    amount = cost_for(NIGHTLY["workers"], runtime)
    delta = (amount - baseline) / baseline * 100
    print(f"  {runtime // 60:>7} min {fmt_usd(amount):>12} {delta:>13.0f}%")

print()
print("=== Sensitivity: scale out (does more compute pay for itself?) ===")
print(f"  {'workers':>8} {'runtime':>10} {'monthly':>12} {'vs baseline':>14}")
# Assume throughput scales sub-linearly: 0.8 efficiency per doubling.
for workers in (4, 8, 16, 32):
    doublings = max(0, (workers // NIGHTLY["workers"]).bit_length() - 1)
    speedup = 2 ** doublings * (0.8 ** doublings)
    runtime = int(NIGHTLY["runtime_seconds"] / speedup)
    amount = cost_for(workers, runtime)
    delta = (amount - baseline) / baseline * 100
    print(f"  {workers:>8} {runtime // 60:>7} min {fmt_usd(amount):>12} {delta:>13.0f}%")

print()
print("Break-even analysis at 16 workers:")
ratio = 16 / NIGHTLY["workers"]
print(f"  16 workers break even only if the runtime shrinks by exactly {ratio:.1f}x.")
print("  A 2x worker increase halves runtime at best -> break even, minus overhead.")
print("  Conclusion: for a BATCH job, scaling out buys you latency, not money.")
print("  Scaling out only saves money if it keeps a STREAMING job's workers")
print("  down, which is a different lever entirely.")
"""))

# ===========================================================================
# 6. The forgotten streaming job
# ===========================================================================
CELLS.append(md("""
## 6. The failure that actually shows up on the invoice

Here is the number that surprises people. A forgotten streaming job — one
nobody cancelled, one that keeps "running" with no input — bills for
**wall-clock time**, every hour, every day, forever.

The arithmetic, with a deliberately modest footprint:

- 100 workers of `n1-standard-2` (2 vCPU each) = **200 vCPU**
- 200 vCPU × $0.055/vCPU-hour = **$11.00 per hour**
- × 24 hours = **$264.00 per day**
- × 30 days = **$7,920 per month**

For a job that is processing nothing.

Compare that with the nightly batch job from §5 — a few dollars a month.
The forgotten streaming job costs **hundreds of times** as much as the
batch job that does all the real work.

The lesson is not "don't run streaming jobs". It is:

> **Streaming cost is dominated by *uptime*, not throughput.** Every design
> decision about a streaming pipeline is really a decision about how long
> the cluster is held open.

That reframes a lot of choices:

| Decision | Cost consequence |
|---|---|
| Minimum workers on a low-traffic stream | You pay for idle capacity 24/7 |
| Max workers on a spiky stream | You pay for peak capacity during spikes |
| Idle-cluster shutdown (`--num_workers` tuning) | The cluster can drain to near-zero |
| Bounded sources instead of unbounded | A bounded job stops; a streaming job does not |

### The safety net: a scheduled cancellation guard

Because the failure mode is *silence*, the fix has to be external to the
job. A scheduled check that cancels jobs with no activity is the standard
control. Here is the shape of it (shown as bash — it needs `gcloud`, and it
must not run against a real project by accident).
"""))

CELLS.append(code("""
# The arithmetic, printed.
idle_workers = 100
machine = "n1-standard-2"
hours_per_day = 24
days_per_month = 30

hourly = idle_workers * VCPU[machine] * RATES[machine]
daily = hourly * hours_per_day
monthly = daily * days_per_month
batch_monthly = cost_for(NIGHTLY["workers"], NIGHTLY["runtime_seconds"])

print("=== The cost of a forgotten streaming job ===")
print(f"  workers                 : {idle_workers} x {machine} "
      f"= {idle_workers * VCPU[machine]} vCPU")
print(f"  per hour                : {fmt_usd(hourly)}")
print(f"  per day                 : {fmt_usd(daily)}")
print(f"  per month               : {fmt_usd(monthly)}")
print()
print(f"  Compare: nightly batch job  : {fmt_usd(batch_monthly)} / month")
print(f"  Ratio                     : {monthly / batch_monthly:.0f}x")
print()
print("  And that is a job with NO input and NO output.")
"""))

CELLS.append(md("""
A scheduled guard, as it would be deployed (bash, **not executed** here):

```bash
# Runs every night. Cancels streaming jobs whose data-pipeline counters
# have not moved in 24 hours.
gcloud dataflow jobs list \\
  --filter='state:JOB_STATE_RUNNING AND jobType:JOB_TYPE_STREAMING' \\
  --format='value(name,region,id)' \\
| while read -r name region job_id; do
    last_activity=$(
      gcloud logging read \\
        "resource.type=dataflow_step AND resource.labels.job_id=$job_id" \\
        --limit=1 --format='value(timestamp)' 2>/dev/null
    )
    if [ -z "$last_activity" ]; then
      echo "Cancelling idle job $name in $region"
      gcloud dataflow jobs cancel "$job_id" --region="$region" --quiet
    fi
  done
```

Two notes on why it is shaped this way:

- It queries the **logs**, not the metrics API, because the logs query
  needs no extra IAM beyond log reading, and it is the same query you
  would run by hand when debugging.
- It is **idempotent and quiet**. A guard that emails you every hour is a
  guard you will turn off.

The complementary control is a budget alert on the billing account, because
a guard that depends on `gcloud` working will eventually not work.
"""))

# ===========================================================================
# 7. Local timing and extrapolation
# ===========================================================================
CELLS.append(md("""
## 7. Measuring locally, extrapolating to the cloud

The final piece of the cost workflow: you cannot get a cloud estimate from
a laptop, but you *can* get a **relative** one, and relative is what you
need to answer "is this optimization worth it?".

### The method

1. Run the pipeline locally with a **fixed** input size.
2. Record the local runtime, `t_local`.
3. Measure how the runtime changes when you change one thing (a filter, a
   combiner, a different partitioning).
4. The *ratio* between the two local runtimes is a good estimate of the
   ratio between the two cloud runtimes — because the cluster overhead and
   the data size are common to both.

The absolute number needs calibration:

```
t_cloud  ~= t_startup + (t_local / speedup_factor)
t_cost   ~= workers * vcpus * t_cloud / 3600 * rate
```

Where `speedup_factor` is how much faster the cloud is than your laptop for
this workload, and `t_startup` is the cluster spin-up (tens of seconds).

The startup term matters more than people think: a pipeline that runs in
10 seconds locally may take 60 seconds in the cloud, 50 of which is
waiting for workers.
"""))

CELLS.append(code("""
import shutil
import tempfile
import time

from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions

from transforms import build_revenue_summary, normalise_currency, try_parse_order_line

ORDERS_CSV = COURSE_ROOT / "sample_data" / "orders.csv"


def load_orders():
    rows = []
    with ORDERS_CSV.open(encoding="utf-8") as handle:
        next(handle)  # skip the header
        for line in handle:
            parsed = try_parse_order_line(line)
            if parsed is not None:
                rows.append(parsed)
    return rows


def time_run(fn, *args, repeats=3):
    \"\"\"Return the best of `repeats` runs -- best, because we want the
    uncontended measurement, not the one that hit a GC pause.\"\"\"
    timings = []
    for _ in range(repeats):
        start = time.perf_counter()
        fn(*args)
        timings.append(time.perf_counter() - start)
    return min(timings)


orders = load_orders()
print(f"loaded {len(orders)} orders from {ORDERS_CSV.name}")

# The pure reference implementation -- no Beam at all.
t_pure = time_run(lambda: build_revenue_summary(orders))
print(f"pure build_revenue_summary : {t_pure * 1000:8.1f} ms")


# The same work, but through a Beam pipeline with a CombinePerKey.
def run_beam(rows):
    options = PipelineOptions()
    options.view_as(StandardOptions).runner = "BundleBasedDirectRunner"
    out = tempfile.mkdtemp(prefix="nb08-timing-")
    try:
        with beam.Pipeline(options=options) as p:
            (p
             | "Read" >> beam.Create(rows)
             | "ToPairs" >> beam.Map(
                 lambda r: (r["region"],
                            normalise_currency(float(r["amount"]), r["currency"])))
             | "Sum" >> beam.CombinePerKey(sum)
             | "Format" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]:.2f}")
             | "Write" >> beam.io.WriteToText(out))
        return out
    except Exception:
        shutil.rmtree(out, ignore_errors=True)
        raise


t_beam = time_run(run_beam, orders)
print(f"Beam CombinePerKey pipeline : {t_beam * 1000:8.1f} ms")
print(f"Beam overhead               : {(t_beam - t_pure) * 1000:8.1f} ms "
      f"({t_beam / t_pure:.1f}x the pure implementation)")
print()
print("The overhead is Beam's runner, coder, and bundle machinery -- the")
print("same machinery that makes the pipeline scale out on Dataflow.")
"""))

CELLS.append(code("""
# --- Extrapolation --------------------------------------------------------
ASSUMPTIONS = {
    "startup_seconds": 45,          # cluster spin-up + staging
    "local_to_cloud_speedup": 4.0,  # how much faster the cloud is, here
    "workers": 8,
    "machine_type": "n1-standard-2",
}

t_local = t_pure  # the work-only part of the measurement
t_cloud = (ASSUMPTIONS["startup_seconds"]
           + (t_local / ASSUMPTIONS["local_to_cloud_speedup"]))

est_batch = batch_cost(
    workers=ASSUMPTIONS["workers"],
    machine_type=ASSUMPTIONS["machine_type"],
    runtime_seconds=t_cloud,
)

print("=== Cloud extrapolation (illustrative) ===")
print(f"  local work time            : {t_local * 1000:.1f} ms")
print(f"  assumed startup            : {ASSUMPTIONS['startup_seconds']} s")
print(f"  assumed speedup            : {ASSUMPTIONS['local_to_cloud_speedup']}x")
print(f"  estimated cloud runtime    : {t_cloud:.2f} s")
print(f"  estimated monthly cost     : {fmt_usd(est_batch * 30)}")
print()
print("The startup term dominates at this scale, which is exactly why the")
print("absolute number is unreliable and the RATIO is reliable.")
print()


# The useful part: a relative comparison. Same input, one change.
def run_filtered_first(rows):
    \"\"\"Same result, but the status filter runs before the aggregation.\"\"\"
    valid = [r for r in rows if r.get("status") == "complete"]
    return build_revenue_summary(valid)


t_filtered = time_run(run_filtered_first, orders)
ratio = t_filtered / t_pure
print("=== Relative measurement (the reliable part) ===")
print(f"  unfiltered   : {t_pure * 1000:.1f} ms")
print(f"  filter-first : {t_filtered * 1000:.1f} ms")
print(f"  ratio        : {ratio:.3f}x")
print()
print("A ratio like this transfers to the cloud even though the absolute")
print("numbers do not: the cluster overhead is common to both runs.")
"""))

# ===========================================================================
# 8. Reading numbers off a real job
# ===========================================================================
CELLS.append(md("""
## 8. Reading the numbers off a real Dataflow job

Everything above is a model. Here is how you read the *actual* numbers off a
real job in the console and on the command line. These are **bash/markdown
commands — they are not executed** by this notebook, because they need a
project and credentials.
"""))

CELLS.append(md("""
These commands are **not executed** by this notebook — they need a project
and credentials. Copy them verbatim.

```bash
# 1. The job's headline metrics, straight from the CLI.
gcloud dataflow jobs describe "$JOB_ID" \\
  --region="$REGION" \\
  --format='yaml(state, currentStateTime, createTime, runtimeSecs)'

# 2. The metrics that actually explain the bill, from the monitoring API.
gcloud monitoring time-series list \\
  --filter='metric.type="dataflow.googleapis.com/job/estimated_cpu"' \\
  --format='value(points[0].value.int64Value)' \\
  --project="$PROJECT_ID"

# 3. The autoscaler's view: peak workers reached.
gcloud monitoring time-series list \\
  --filter='metric.type="dataflow.googleapis.com/job/max_workers"' \\
  --format='value(points[0].value.int64Value)' \\
  --project="$PROJECT_ID"

# 4. The backlog signal -- the one that tells you the job is behind.
gcloud monitoring time-series list \\
  --filter='metric.type="dataflow.googleapis.com/job/work_lag"' \\
  --format='value(points[0].value.int64Value)' \\
  --project="$PROJECT_ID"

# 5. What you paid, from the billing export.
gcloud billing accounts list --format='value(name)'
```
"""))

CELLS.append(md("""
### Reading the chart that matters

On the Dataflow job graph, the single most useful customisation is a
**two-axis plot**: `estimated_cpu` (or `total_gb_processed`) on one axis,
`max_workers` on the other, over job runtime.

- **Both rising together** → the autoscaler is doing its job.
- **CPU flat, workers rising** → the cluster is bigger than the work. You
  are paying for idle capacity. Lower `min_workers`.
- **CPU rising, workers flat** → you are pinned at `max_workers`. Raise the
  ceiling, or fix the skew.
- **Both flat, backlog rising** → the job is blocked on something that is
  not CPU: a slow sink, a lock, a bad join.

That last row is why `work_lag` belongs on the same chart. It is the only
one of these four signals that distinguishes "slow" from "stuck".
"""))

# ===========================================================================
# 9. Monitoring checklist
# ===========================================================================
CELLS.append(md("""
## 9. The monitoring checklist

The practical checklist, in the order you should apply it.

| # | Check | Signal | Healthy |
|---|---|---|---|
| 1 | Is the job running? | `JOB_STATE_*` | `RUNNING` |
| 2 | Is it doing work? | `estimated_cpu` delta | Increasing |
| 3 | Is it keeping up? | `work_lag` | Flat or falling |
| 4 | Is the cluster right-sized? | `max_workers` vs `estimated_cpu` | Tracking each other |
| 5 | Are workers stable? | `worker_health` | No repeated failures |
| 6 | Is my data arriving? | `bytes_counter` | Growing |
| 7 | Is my data *correct*? | **custom counters** | Reconciles with input |
| 8 | Is the bundle size sane? | `bundle_size` | Not stuck at 1 |
| 9 | Am I paying for idle? | `estimated_cpu` when idle | Near zero |

Row 9 deserves a note: in a streaming job, `estimated_cpu` should drop
toward zero when no data is arriving. If it does not, your workers are
spinning — usually a polling sink or a trigger that fires too eagerly.

### Row 7 is the one people skip

The built-in metrics are all about *resources*. The one that matters for
*correctness* has to be yours. A pipeline that reads 1,000,000 rows,
writes 700,000, and reports "healthy" has a 30% data loss rate and every
dashboard in the world will tell you it is fine.

This is why the reconciliation check in the next cell is the most important
metric code you will write.
"""))

CELLS.append(code("""
# --- Instrument the REAL project pipeline with reconciling counters -------
from apache_beam.metrics import Metrics

from transforms import CURRENCY_TO_EUR, try_parse_order_line

ORDERS_READ = Metrics.counter("dataflow_course", "orders_read")
ORDERS_VALID = Metrics.counter("dataflow_course", "orders_valid")
ORDERS_REJECTED = Metrics.counter("dataflow_course", "orders_rejected")
REJECTED_CSV = Metrics.counter("dataflow_course", "orders_rejected_malformed_csv")
REJECTED_CURRENCY = Metrics.counter("dataflow_course", "orders_rejected_bad_currency")


class InstrumentedRead(beam.DoFn):
    \"\"\"Counts what came in, what parsed, and what did not.

    The rejection counters are split BY REASON, using a bounded set of
    metric names -- exactly the pattern section 2.4 recommends.
    \"\"\"

    def process(self, line):
        ORDERS_READ.inc()
        parsed = try_parse_order_line(line)
        if parsed is None:
            ORDERS_REJECTED.inc()
            REJECTED_CSV.inc()
            return
        # A row can parse and still be unusable: an unknown currency is a
        # business-rule rejection, not a parse failure.
        if parsed["currency"].upper() not in CURRENCY_TO_EUR:
            ORDERS_REJECTED.inc()
            REJECTED_CURRENCY.inc()
            return
        ORDERS_VALID.inc()
        yield parsed


# Use the CLEAN file plus the deliberately malformed one, so the rejection
# path is actually exercised rather than always counting zero.
rows = []
with (COURSE_ROOT / "sample_data" / "orders.csv").open(encoding="utf-8") as fh:
    next(fh)
    rows.extend(fh.readlines())

malformed_path = COURSE_ROOT / "sample_data" / "malformed_orders.csv"
if malformed_path.exists():
    with malformed_path.open(encoding="utf-8") as fh:
        rows.extend(fh.readlines())
    print(f"injected {len(rows) - 5000} malformed rows from "
          f"{malformed_path.name}")

options = PipelineOptions()
options.view_as(StandardOptions).runner = "BundleBasedDirectRunner"

with beam.Pipeline(options=options) as p:
    (p
     | "Rows" >> beam.Create(rows)
     | "Parse" >> beam.ParDo(InstrumentedRead())
     | "ToPairs" >> beam.Map(
         lambda r: (r["region"],
                    normalise_currency(float(r["amount"]), r["currency"])))
     | "Sum" >> beam.CombinePerKey(sum)
     | "Format" >> beam.Map(lambda kv: (kv[0], kv[1])))

pr = p.result
pr.wait_until_finish()

q = pr.metrics().query(MetricsFilter().with_namespace("dataflow_course"))


def committed(name):
    total = 0
    for metric_results in q.values():
        for metric_result in metric_results:
            if metric_result.key.metric.name == name:
                value = metric_result.committed
                if isinstance(value, list):
                    value = value[0] if value else 0
                total += value or 0
    return total


read = committed("orders_read")
valid = committed("orders_valid")
rejected = committed("orders_rejected")
malformed = committed("orders_rejected_malformed_csv")
bad_currency = committed("orders_rejected_bad_currency")

print("=== Reconciliation ===")
print(f"  read            : {read}")
print(f"  valid           : {valid}")
print(f"  rejected        : {rejected}")
print(f"    malformed CSV : {malformed}")
print(f"    bad currency  : {bad_currency}")
print()
if read == valid + rejected:
    print("  RECONCILED: read == valid + rejected")
else:
    print(f"  MISMATCH: {read} != {valid} + {rejected}")
if rejected == malformed + bad_currency:
    print("  All rejections accounted for by the per-reason counters.")
else:
    print(f"  MISMATCH: {rejected} != {malformed} + {bad_currency}")
"""))

# ===========================================================================
# 10. Common errors
# ===========================================================================
CELLS.append(md("""
## 10. Common errors and fixes

| Symptom | Real cause | Fix |
|---|---|---|
| `TypeError: __call__() got an unexpected keyword argument 'label'` | Beam 2.77 counters have no labels | Use a bounded set of metric names |
| Hundreds of near-identical metrics in the console | Metric name built from the data | Constant names; keep detail in the output |
| Counter reports `0` | Counter never incremented on that path | Check the `DoFn` branch you thought ran |
| `AttributeError: 'PipelineOptions' object has no attribute 'staging_location'` | Read the attribute off the base class | `options.view_as(GoogleCloudOptions)` |
| `AttributeError: 'PipelineOptions' object has no attribute 'runner'` | `runner` lives on `StandardOptions` | `options.view_as(StandardOptions).runner` |
| Custom metric missing from the console | Namespace/name changed between runs | Keep the namespace stable forever |
| `estimated_cpu` flat, job "running" | Job is blocked, not busy | Check `work_lag`, then the sink |
| Workers ramp to `max_workers` immediately | `min_workers` set to peak | Lower the floor; let the autoscaler react |
| Job idles but the invoice still climbs | Streaming bills wall-clock time | Cancel it, or shrink `min_workers` |
| Bundle size stuck at 1 | Bundling disabled, or source is uncoalesced | Raise `--max_bundle_size` |
| Estimates wildly off | Forgot the startup term | Add 30–60 s for cluster spin-up |
| Cost spikes after a schema change | Shuffle volume grew | Check `bytes_counter`, not just runtime |

The first two rows are the ones that will actually bite you, and both were
demonstrated live earlier in this notebook: the `label=` `TypeError` and the
metric-cardinality explosion. The `PipelineOptions` traps were
demonstrated in Notebook 07.

### The one-line mental model

> **Dataflow bills vCPU-hours. Runtime is `work / throughput`. Throughput is
> limited by your slowest stage, not your average one. So the cheapest
> optimisation is the one that removes the slowest stage — not the one that
> buys cheaper workers.**
"""))

CELLS.append(md("""
## 🔑 Takeaways

- **Dataflow's built-in signals are about resources, not correctness.**
  `estimated_cpu` and `max_workers` explain the invoice; only a custom
  counter can tell you that 30% of your rows vanished.

- **A metric's namespace and name must be constants.** Building the name
  from the data (`f"seen_{region}"`) creates one time series per distinct
  value — an unbounded cardinality explosion that is invisible locally and
  fatal in production.

- **Beam 2.77 counters have no labels.** `counter.inc(label={...})` raises
  `TypeError: __call__() got an unexpected keyword argument 'label'`. The
  constructor is `Metrics.counter(namespace, name)` and the updater is
  `inc(value)`. Use a bounded set of metric names instead.

- **Read metrics back as `{category: [MetricResult]}`**, not as a flat
  name→value map. The namespace lives at `key.metric.namespace`, the name
  at `key.metric.name`, and the same name can appear under several steps.

- **Autoscaling is a feedback loop between backlog and worker count.**
  Both failure modes are sizing errors: a ceiling too low (backlog grows
  forever) and a floor too high (idle capacity you pay for 24/7).

- **Cost is `workers × vCPUs × hours × rate`,** and for streaming the
  hours are *wall-clock* — uptime, not work.

- **A forgotten streaming job is the most expensive mistake in Dataflow.**
  100 idle workers is ~$264/day and ~$7,920/month — hundreds of times the
  nightly batch job that does the real work.

- **Batch scaling out buys latency, not money.** Doubling workers and
  halving the runtime is break-even before shuffle overhead; scale out to
  shorten a *streaming* job's wall clock or to reduce its worker floor.

- **Trust ratios, not absolute numbers, from local measurement.** The
  cluster startup term dominates locally-measured runtimes, so a local
  measurement tells you which of two versions is faster, not what either
  will cost.
"""))

if __name__ == "__main__":
    out = (Path(__file__).resolve().parent.parent
           / "notebooks" / "08-monitoring-and-cost.ipynb")
    path = build(CELLS, "nb08", out_path=out)
    print(f"wrote {path} with {len(CELLS)} cells")
