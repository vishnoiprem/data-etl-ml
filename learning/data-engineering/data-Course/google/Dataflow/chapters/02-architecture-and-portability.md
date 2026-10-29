# 1.2 — Architecture & Portability
> **Section 1 · Beam Fundamentals & Model · Lecture 1.2 · 6:30**

## 🎯 What you will learn

- The three physical layers of a Beam pipeline: SDK, Runner, and harness
- What the Runner API proto actually contains, and why it is the portability boundary
- How an SDK harness turns a portable graph into runner-native execution
- The "one model, many runners" design and what it buys you
- How Beam differs from Spark (DAG-as-data) and from Flink (record-centric vs data-centric)
- What genuinely breaks when you cross a runner boundary
- The Java SDK vs Python SDK trade-off, in engineering terms
- Where the Beam YAML and submit-framework direction is heading

---

## 🧠 Concept

### The three layers

A Beam pipeline is not one program. It is three cooperating layers, and most
confusion about Beam comes from conflating them.

```text
┌──────────────────────────────────────────────────────────────────────┐
│  1. SDK LAYER — where you write code                                │
│                                                                      │
│     Python / Java / Go / Scala SDK                                  │
│     PCollection · PTransform · DoFn · CombineFn                     │
│                                                                      │
│     Your pipeline graph lives here.                                 │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
                                │  to_runner_api() → proto
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│  2. RUNNER API — the portable contract (a protobuf)                 │
│                                                                      │
│     Pipeline { components { transforms{}, pcollections{} } }         │
│                                                                      │
│     A language-neutral, execution-neutral description of the DAG.   │
│     No Python objects. No Spark RDDs. Just a graph.                 │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
                                │  SDK harness translates the proto
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│  3. RUNNER LAYER — where the work happens                           │
│                                                                      │
│     DataflowRunner · SparkRunner · FlinkRunner · PrismRunner        │
│                                                                      │
│     Runner owns: scheduling, sharding, state, checkpointing,        │
│                  autoscaling, and the physical execution.           │
└──────────────────────────────────────────────────────────────────────┘
```

The rule that makes this design work: **the SDK never decides how to
execute. The runner always decides.** Your code describes *what* should
happen; the runner decides *where*, *in what order*, and *with how much
parallelism*.

This is the inverse of what you may be used to. In Spark, your code *is*
the execution plan: `groupByKey()` materialises a shuffle; `repartition()`
materialises another shuffle. The DAG is implicit in the operator chain, and
the Catalyst optimiser inspects that chain to rearrange it. In Beam, your
code is a *description* of data flow, and the runner is free to fuse,
regroup, or re-shuffle it however it likes.

### The Runner API proto

When you call `beam.Pipeline.run()`, Beam does not execute your Python
functions. It translates the whole graph into a protobuf — the **Runner
API** — and hands that proto to the runner.

You can see the proto for yourself:

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.runners.runner import create_runner

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])

with beam.Pipeline(options=options) as p:
    (
        p
        | "Create" >> beam.Create([1, 2, 3])
        | "Double" >> beam.Map(lambda x: x * 2)
    )

# `p` is a `Pipeline`; the portable form is the proto.
proto = p.to_runner_api()
print(type(proto).__name__)
print(sorted(proto.components.transforms.keys()))
```

The interesting thing about this proto is what it does **not** contain. It
does not contain:

- Python lambdas or closures — those are captured into a serialised
  `ParDoPayload` as bytes, with a coder telling the harness how to
  reconstruct them.
- Any reference to Spark's `RDD`, Flink's `DataStream`, or Dataflow's
  worker pool.
- Any statement about how many workers to use, or how data is sharded.
- Any ordering guarantee between two independent branches.

The proto contains a *graph*:

| Proto field | What it holds |
|---|---|
| `components.transforms` | every PTransform, keyed by a unique ID |
| `components.pcollections` | every PCollection, with its coder |
| `components.encodings` | the per-transform payload (the serialised `DoFn`) |
| `components.windowing_strategies` | the windowing assigned to each PCollection |
| `requirements` | a list of capabilities the runner must satisfy |

That last row is the safety net. A runner that cannot support something the
pipeline needs must say so *before* the job starts, not halfway through.

### The SDK harness — where portability actually happens

A runner that wants to be portable cannot simply execute the proto. Spark
does not know what a Beam window is. Flink does not know what a Beam
`CombineFn` is. So each runner implements an **SDK harness**: a component
that reads the Runner API proto and *translates* it into the runner's
native execution model.

```text
   Runner API proto                        Spark-native plan
   ───────────────────                      ─────────────────
   ParDo (ParDoPayload)         ──►        RDD.mapPartitions(...)
   GroupByKey                   ──►        RDD.reduceByKey(...)
   CombinePerKey(CombineFn)     ──►        RDD.combineByKey(...)
   WindowInto(FixedWindows)     ──►        SlidingWindowedRDD / windowed reduce
   ReadFromText                 ──►        sc.textFile(...) / hadoop FileInputFormat
```

The harness is where the "same code, many runners" claim is either earned
or broken. If a runner's harness has no faithful translation for a proto
construct, that construct either fails at submission time or — worse — is
silently emulated incorrectly.

This is why the portability boundary is not at the SDK layer. It is at the
**proto layer**, and it is only as good as the least complete harness.

### One model, many runners

The design goal is a single API — the Beam model — that any runner can
implement, so that:

- **Google** can build a managed serverless runner (Dataflow) and keep the
  SDK open, so other engines can compete without Google locking in users.
- **You** can write a pipeline once and move it between Dataflow, Spark,
  Flink, or a local Prism instance without rewriting the business logic.
- **A runner author** only has to implement one harness, not a new SDK.

| Runner | Harness target | Execution model |
|---|---|---|
| `DataflowRunner` | Google Cloud Dataflow | serverless, autoscaled workers, streaming checkpoints |
| `SparkRunner` | Apache Spark | RDD/DataFrame, executor + driver, shuffle via external shuffle service |
| `FlinkRunner` | Apache Flink | DataStream/DataSet, checkpointed operator chain, exactly-once via checkpoints |
| `PrismRunner` | Apache Beam Prism (Go) | portable runner, local job server, Go execution engine |
| `BundleBasedDirectRunner` | pure Python | in-process, single machine, no distribution |

Two properties of this design are worth internalising:

1. **The graph is portable. The configuration is not.** `--autoscaling_algorithm`
   is Dataflow-only. `--num_workers` is Spark-flavoured. `--streaming` means
   something different on every runner. Portability lives in the transforms,
   not in the flags.

2. **Portability is opt-in per transform, not automatic.** Beam's core
   transforms — `Map`, `Filter`, `CombinePerKey`, `GroupByKey`, `WindowInto`,
   `Reshuffle` — are portable because a harness can translate each of them.
   A runner-specific transform is a hard boundary: it will not run anywhere
   else, and Beam will refuse to submit the pipeline to a runner that
   cannot handle it.

### How Beam differs from Spark

Spark's model is **RDD-as-data**: you manipulate a lazy, distributed
collection through an operator chain, and the Catalyst optimiser inspects
that chain to build a physical plan. Beam's model is **DAG-as-data**: the
graph is the primary object, and the runner owns the plan.

| Dimension | Spark | Beam |
|---|---|---|
| Primary abstraction | `RDD` / `DataFrame` — a distributed collection | `PCollection` — an immutable, timestamped description of a dataset |
| Where the plan lives | in the SDK (Catalyst), visible to the user | in the runner, opaque to the user |
| Optimisation | Catalyst rewrites the operator chain | runner fuses and regroups; SDK never sees the physical plan |
| State | mutable; `Dataset` operations can mutate partitions under you | immutable; every transform produces a new PCollection |
| Ordering | the user reasons about it; repartitioning has semantics | Beam makes no cross-key ordering promise at all; `Reshuffle` is the explicit tool |
| Time | processing time by default; event time only in Structured Streaming | event time is first-class; the watermark is a modelled concept |
| The unit of work | a stage plus a shuffle | a **bundle** — the runner's unit of parallelism and checkpointing |

The immutability difference is more than a stylistic preference. It is what
makes the following safe:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    source = p | "Read" >> beam.Create([("a", 1), ("b", 2), ("c", 3)])

    # Two independent branches consume the same PCollection.
    evens = source | "KeepEven" >> beam.Filter(lambda kv: kv[1] % 2 == 0)
    total = source | "SumByKey" >> beam.CombinePerKey(sum)
    _ = (evens, total)
```

In Spark, a `DataFrame` can be cached and then mutated by a subsequent
action; lineage and caching interact in ways that produce stale results if
you are not careful. In Beam, `source` is a description. Both branches read
the same immutable description, and the runner decides whether to read the
source once or twice.

### How Beam differs from Flink

Flink's model is **record-centric**: a stream of records flowing through
an operator chain, where each operator owns keyed state and the runtime
checkpoints that state. Beam's model is **data-centric**: a graph of
datasets, where state is a *derived consequence* of grouping, and
checkpointing is the runner's business.

| Dimension | Flink | Beam |
|---|---|---|
| Core object | a `StreamExecutionEnvironment` holding operators | a `Pipeline` holding a graph of PTransforms |
| Time | event time, watermarks, and `TimerService` are built in and central | event time, watermarks, and triggers are part of the *portable model*, expressed via `WindowInto` |
| State | explicit keyed state on operators (`ValueState`, `ListState`) plus timers | state is implied by `GroupByKey`/`CombinePerKey`; explicit state via `userstate` is an SDK feature |
| Exactly-once | a runtime property of the checkpointing protocol | a property the *runner* may or may not offer; the SDK does not promise it |
| Batch | a separate API (`DataSet`) or a bounded stream | literally the same code, watermark to `+inf` |
| Triggering | native: `EventTimeTrigger`, `ProcessingTimeTrigger`, custom | portable: `AfterWatermark`, `AfterCount`, `AfterProcessingTime`, and combinations |

The important difference is *where exactly-once lives*. In Flink it is a
property of the engine: the runtime implements a checkpoint/ack protocol
and the user inherits it. In Beam, exactly-once is a *capability the runner
advertises*. The SDK expresses the same pipeline either way; what changes
is the guarantee you get from the runner you picked.

### What breaks when you cross runners

Crossing a runner boundary is a real engineering decision, not a checkbox.
These are the failure modes, in rough order of how often they bite:

| Break point | What happens | Mitigation |
|---|---|---|
| Runner-specific transform | Pipeline fails at submission: `Beam has not been implemented on this runner` | keep runner-specific transforms behind a factory that returns `None` when unavailable |
| Runner-specific I/O | `ReadFromPubSub` only exists on Dataflow and the Direct runners | abstract sources behind a function that picks an implementation per runner |
| Unsupported coders | the runner cannot encode your type — e.g. a custom `CombineFn` accumulator with a runner-specific coder | pick a coder the runner supports, or use a primitive accumulator |
| Missing capability | a runner rejects a `requirements` entry in the proto | check `runner.supported_capabilities` before submitting |
| Windowing semantics | Flink translates Beam windows to Flink windows; subtle differences in late-data handling and allowed lateness remain | write window tests that run on the target runner, not only locally |
| State and timers | `userstate` and timer semantics are not identical across runners | avoid `userstate` in portable code; use `CombinePerKey` where you can |
| Exactly-once | Spark's `at-least-once` for some sinks, Flink's `exactly-once`, Dataflow's `exactly-once` for streaming | design sinks to be idempotent, and never trust the delivery guarantee alone |
| Performance profile | the same graph has different costs on different runners — Spark's shuffle is expensive, Flink's state is expensive, Dataflow's autoscaling amortises it | benchmark on the target runner, on the target data shape |

The last row is the one that causes the most disappointment. "It runs on
both" is not "it performs the same on both". A pipeline that takes four
minutes on Dataflow may take twenty on Dataproc, because the shuffle
profile is completely different.

### Java SDK vs Python SDK

Both SDKs implement the same model. The trade-offs are concrete.

| Dimension | Java SDK | Python SDK |
|---|---|---|
| Startup latency | JVM start ~1–2 s plus Beam's own init; ~5–10 s total | ~1–2 s interpreter + import overhead |
| Throughput | roughly 2–5× Python for tight per-element loops | slower per element; dominated by GIL-bound Python work |
| Type system | static; a `CombineFn` is checked at compile time | dynamic; errors surface at run time on a worker |
| Type hints | not needed | optional but recommended: `beam.typehints` catches whole-pipeline mismatches before submission |
| Custom state & timers | first-class, mature | supported, but the ergonomics are rougher and some corner cases are unimplemented |
| Newest features | usually first | sometimes behind; some runner features are Java-only |
| Glue to existing code | strong if your codebase is JVM | strong if your codebase is Python |
| Development loop | slower (compile step) | fast (notebook-friendly, `direct_runner` in-process) |

The honest summary: **the Python SDK is the one to learn first** — the
course is built on it, the API surface is identical, and the direct runner
gives you a sub-second edit/run loop. But there is a specific set of cases
where Java is the right call:

- Very high per-element cost, where Python overhead dominates the actual
  business logic.
- Heavy use of `userstate` and custom timers, where the Java SDK is
  better-tested.
- A need to call into existing JVM libraries (Flink's own state backends,
  Kafka Streams interop, Debezium connectors).

The thing to internalise: **the model does not change between SDKs.** A
`CombineFn` in Java and a `CombineFn` in Python do the same thing. That
equivalence is what makes the portability claim meaningful — it is not
just "the same API in two languages", it is the same semantics.

### Where this is heading: Beam YAML and the submit-framework model

The SDK layer is not where the future is. The direction is toward
*declarative* pipelines defined in YAML, with a "submit framework" that
owns the plumbing — the environment, the pipeline options, the deployment
target, the monitoring — and exposes only a small surface to the user.

```yaml
# A sketch of the Beam YAML shape (not the exact current schema).
define: revenue_by_region
args:
  input: gs://YOUR_BUCKET/orders.csv
  output: gs://YOUR_BUCKET/summary

steps:
  - name: read
    transform: ReadFromText
    args:
      file_path: {ref: "input"}

  - name: parse
    transform: Map
    args:
      fn: "{module: transforms, function: parse_order_line}"

  - name: aggregate
    transform: CombinePerKey
    args:
      fn: "{module: transforms, function: RevenueByRegionFn}"

  - name: write
    transform: WriteToText
    args:
      file_path_prefix: {ref: "output"}
```

Why this matters to you as an engineer:

- **Configuration stops being code.** The same YAML can be submitted to
  Dataflow, Spark, or Flink by changing the submit framework.
- **A pipeline becomes a deployable artefact.** It has a name, a version,
  parameters, and a lifecycle — much more like a service than a script.
- **The SDK remains the escape hatch.** YAML cannot express every
  `CombineFn`; you will still drop to the SDK for the hard 20%.

The practical advice: learn the SDK model first, because the model is
what the YAML expresses. A team that starts with YAML and never learns
`CombineFn` associativity will be unable to debug the 20%.

---

## 🛠️ Hands-On

### Inspecting the Portable Graph

The fastest way to internalise this chapter is to look at the proto and the
harness behaviour directly.

### Step 1 — Build a graph and print its Runner API proto

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])

with beam.Pipeline(options=options) as p:
    (
        p
        | "Create" >> beam.Create([1, 2, 3])
        | "Double" >> beam.Map(lambda x: x * 2)
        | "Filter" >> beam.Filter(lambda x: x > 4)
    )

proto = p.to_runner_api()
print("transform count:", len(proto.components.transforms))
for name, transform in sorted(proto.components.transforms.items()):
    print(name, "->", transform.unique_name)
print("requirements:", list(proto.requirements))
```

The `requirements` list is the runner's capability contract. A runner that
cannot satisfy a requirement must reject the job at submission.

### Step 2 — See the same graph under a different runner

The *proto* is identical regardless of runner. Only the harness and the
execution differ. This is the portability claim, and you can observe it:

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions


def graph_signature(runner_name):
    """Build the same graph and describe it, without running it."""
    options = PipelineOptions(["--runner", runner_name])
    with beam.Pipeline(options=options) as p:
        (
            p
            | "Create" >> beam.Create([1, 2, 3])
            | "Double" >> beam.Map(lambda x: x * 2)
        )
    proto = p.to_runner_api()
    return {
        "runner": runner_name,
        "transforms": sorted(t.unique_name for t in proto.components.transforms.values()),
        "requirements": sorted(proto.requirements),
    }


for name in ("BundleBasedDirectRunner", "PrismRunner", "SparkRunner", "FlinkRunner"):
    try:
        print(graph_signature(name))
    except Exception as exc:  # a runner may not be installed
        print(name, "unavailable:", type(exc).__name__, str(exc)[:80])
```

Note the `unique_name` values are identical across runners. The runner
name is *not* part of the portable graph — it is part of the deployment.

### Step 3 — Inspect the capability requirements of a real pipeline

Use the course's own streaming pipeline, which uses windowing and
triggers, and look at what it demands of a runner:

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.transforms.window import FixedWindows
from apache_beam.transforms.trigger import AccumulationMode, AfterWatermark

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])

with beam.Pipeline(options=options) as p:
    (
        p
        | "Create" >> beam.Create([(1.0, "a"), (2.0, "b")])
        | "Window" >> beam.WindowInto(
            FixedWindows(60),
            trigger=AfterWatermark(),
            accumulation_mode=AccumulationMode.ACCUMULATING,
        )
        | "Key" >> beam.Map(lambda pair: ("k", pair[1]))
        | "Count" >> beam.combiners.Count.PerKey()
        | "Sink" >> beam.Map(print)
    )

proto = p.to_runner_api()
print("requirements:", sorted(proto.requirements))
for name, transform in sorted(proto.components.transforms.items()):
    if transform.unique_name.startswith("Window"):
        print("windowing strategies:", len(proto.components.windowing_strategies))
```

The windowing strategies are stored once, per PCollection, in the proto.
The harness reads them and builds the runner's native windowing — Flink
windows, Spark windowed RDDs, or Prism's event-time state.

### Step 4 — Confirm the runner resolution path

The `--runner` flag is not read by your code. It is read by Beam's option
parser and resolved to a class name:

```python
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions
from apache_beam.runners.runner import create_runner

for name in ("DirectRunner", "BundleBasedDirectRunner", "PrismRunner", "FlinkRunner"):
    options = PipelineOptions(["--runner", name])
    resolved = options.view_as(StandardOptions).runner
    runner = create_runner(resolved)
    print(f"{name:>24} -> {resolved:>24} -> {type(runner).__module__}.{type(runner).__name__}")
```

Two things to note. First, `view_as(StandardOptions).runner` returns a
**string**, not a runner object — the object is constructed later, by
`create_runner`. Second, `DirectRunner` and `SwitchingDirectRunner` are the
*same class* in Beam 2.77: `DirectRunner` is an alias for the switching
runner, which picks a specialised engine at submission time.

### Step 5 — Run the course pipeline on two runners

```bash
cd data-engineering/data-Course/google/Dataflow
python resources/sample_data.py --output-dir ./sample_data

python project/batch_pipeline.py \
  --runner BundleBasedDirectRunner \
  --input ./sample_data/orders.csv \
  --output ./out/portability_bundled

python project/batch_pipeline.py \
  --runner PrismRunner \
  --input ./sample_data/orders.csv \
  --output ./out/portability_prism

diff <(cat out/portability_bundled*) <(cat out/portability_prism*) && echo "IDENTICAL OUTPUT"
```

The two runs use different engines — a pure-Python one and a Go one — and
produce byte-identical output. That is portability working, in the most
concrete way available.

---

## 🛠️ Common Errors and Fixes

### `Beam has not been implemented on this runner`

```text
apache_beam runners.base_dofn_runner.BaseDofnRunner: ... 
RuntimeError: Beam has not been implemented on this runner.
```

You used a runner-specific transform (a Dataflow I/O, a Flink-specific
connector) and submitted the pipeline to a runner that does not implement
it. The `requirements` list in the proto carries that capability, and the
runner rejects the job at submission — which is the good outcome.

**Fix:** keep runner-specific transforms behind a factory that can return
`None`, and branch on the runner:

```python
import apache_beam as beam


def make_source(pipeline, options, path):
    """Return a source appropriate to the runner in use."""
    runner = options.view_as(beam.options.pipeline_options.StandardOptions).runner
    if runner == "DataflowRunner":
        return pipeline | "ReadGCS" >> beam.io.ReadFromText(path)
    return pipeline | "ReadLocal" >> beam.io.ReadFromText(path)
```

### `AttributeError: 'PipelineOptions' object has no attribute 'runner'`

```text
AttributeError: 'PipelineOptions' object has no attribute 'runner'
```

`runner` is not on the base `PipelineOptions` class. It lives on the
`StandardOptions` subclass, and the base class raises `AttributeError` for
any unknown attribute. This bites people who write `options.runner` by
habit.

**Fix:** use `view_as`:

```python
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions

options = PipelineOptions(["--runner", "DataflowRunner"])
runner_name = options.view_as(StandardOptions).runner
print(runner_name)
```

### `ValueError: Unexpected pipeline runner: Foo. Valid values are ...`

```text
ValueError: Unexpected pipeline runner: Foo. Valid values are DataflowRunner,
BundleBasedDirectRunner, DirectRunner, SwitchingDirectRunner, InteractiveRunner,
FlinkRunner, FnApiRunner, KafkaStreamsRunner, PortableRunner, PrismRunner,
SparkRunner, TestDirectRunner, TestDataflowRunner
```

The runner name is resolved by lower-casing it and looking it up in a map
built from the fully-qualified class paths. If it does not match, and
appending `runner` does not match either, the raw string is used — and a
raw string with no dots is rejected.

**Fix:** use one of the listed names, or the fully qualified class path:

```bash
python project/batch_pipeline.py \
  --runner apache_beam.runners.portability.spark_runner.SparkRunner
```

### `ImportError: Google Cloud Dataflow runner not available`

```text
ImportError: Google Cloud Dataflow runner not available, please install apache_beam[gcp]
```

The `DataflowRunner` class is in the `apache-beam[gcp]` extra. A plain
`pip install apache-beam` does not include it.

**Fix:** install the extra, or use a local runner for development.

### The pipeline runs on one runner and not another, with no error

This is the dangerous one. There is no error message — the pipeline simply
produces *different numbers* on a different runner. The usual causes:

- A `CombineFn` that is not associative or not commutative, so the merge
  order changes the answer. The direct runner happens to merge in a
  benign order; a distributed runner does not.
- A non-deterministic function (using `random`, `id()`, or a dict
  iteration order) that happens to be deterministic on one worker.
- A `GroupByKey` assumption about ordering, which Beam explicitly does not
  guarantee.

**Fix:** test the combiner as a pure function over a shuffled input, and
assert that the result is order-independent. The course's
`RevenueByRegionFn` is written so that `merge_accumulators` is a plain
sum over partials — that property is what makes it safe.

### `error: [Errno 2] No such file or directory: 'gs://...'`

A local runner cannot read `gs://` paths unless `gcsfs` is installed and
credentials are configured.

**Fix:** use a local path with the Direct runners, or install
`apache-beam[gcp]` and authenticate before pointing at a `gs://` path.

---

## 💡 Production Notes

- **The runner, not the SDK, is where your performance lives.** A Beam
  pipeline on Dataflow with 10 workers and a Beam pipeline on Dataflow
  with 200 workers differ by roughly 20×. The SDK code is identical.
  Before optimising Python, ask whether the runner gave you enough
  parallelism.
- **Read the fusion plan, not the source.** Dataflow's job graph shows
  exactly which steps were fused. A pipeline that looks like six stages
  on paper may run as three. Optimising a step that was fused away is
  wasted effort; optimise the boundary that actually materialises.
- **Keep runner-specific code isolated.** A common production pattern is a
  `sources.py` / `sinks.py` module that exposes `read_orders(pipeline, path)`
  and `write_summary(pipeline, rows, path)`, each branching internally on
  the runner. This keeps the portable core — the business logic — clean.
- **Portability is an escape hatch, not a goal.** Most production teams
  should target *one* runner and use portability as insurance against
  pricing or product changes, not as a design constraint that slows every
  decision.
- **Check `requirements` before a big submission.** A pipeline whose proto
  requires a capability the runner lacks will be rejected at submission.
  Catching that in a dry run saves a 40-minute cluster-provisioning delay.
- **The SDK layer is the smallest part of the system.** Your transform
  code is maybe 200 lines. The runner handles thousands of concurrent
  workers, autoscaling, checkpointing, and retries. The engineering effort
  belongs in the code you write, not in re-implementing what the runner
  already does.

---

## 🔑 Key Takeaways

- A Beam pipeline has **three layers**: the SDK (your code), the Runner
  API (a portable protobuf), and the runner (execution). The SDK never
  decides how to run.
- Portability lives in the **Runner API proto** and is realised by each
  runner's **SDK harness**, which translates portable constructs into
  runner-native ones.
- Beam is **DAG-as-data** (the runner owns the plan) where Spark is
  **RDD-as-data** (Catalyst owns the plan, in the SDK). Beam's
  immutability is a guarantee, not a style choice.
- Beam is **data-centric** (state is a consequence of grouping) where
  Flink is **record-centric** (state is an explicit property of
  operators). Exactly-once lives in the *runner* in Beam, and in the
  *runtime* in Flink.
- Crossing runners breaks on: **runner-specific transforms, runner-specific
  I/O, unsupported coders, missing capabilities, windowing semantics,
  state/timers, and the delivery guarantee** — and, most insidiously, on
  *performance* without any error at all.
- The **Python SDK** is the right default for learning and for most
  workloads; **Java** wins on tight per-element loops, mature `userstate`,
  and JVM library interop. The model is identical, so skills transfer.
- **Beam YAML and the submit-framework model** are where the SDK layer is
  heading: configuration out of code, pipelines as deployable artefacts,
  with the SDK kept as the escape hatch for the hard 20%.

---

## 📚 Practice Exercises

1. **Diff the protos.** Build the same three-step pipeline under
   `BundleBasedDirectRunner` and under `PrismRunner`. Dump
   `p.to_runner_api()` to a file for each and diff them. Expected answer:
   the `components.transforms`, `pcollections`, and `windowing_strategies`
   are identical; only the deployment metadata differs. Explain why that
   is the whole portability claim in one file.

2. **Find the requirement.** Use the course's `build_streaming_pipeline`
   with a `FixedWindows` + `AfterWatermark` trigger. Print the proto's
   `requirements` list. Then add a `beam.Reshuffle` and print it again.
   Expected answer: the requirement list grows, and the reshuffle adds a
   `GroupByKey`-shaped requirement. Explain what a runner that lacks it
   would have to do.

3. **Break a combiner.** Copy `RevenueByRegionFn` from
   `project/transforms.py` into a scratch file and make
   `merge_accumulators` subtract a fixed epsilon each time it merges
   (i.e. make it non-associative). Run the batch pipeline with 1 and with
   4 workers on the Direct runner. Expected answer: the single-worker
   result is correct; the multi-worker result drifts by a multiple of the
   epsilon, because the number of merges depends on how the data was
   split. This is the exact failure mode that makes "it worked on my
   laptop" a lie.

4. **Runner capability matrix.** Write a script that, for each of
   `DirectRunner`, `BundleBasedDirectRunner`, `PrismRunner`,
   `SparkRunner`, and `FlinkRunner`, attempts to build the course's
   streaming pipeline and reports whether it was accepted, and which
   runner it actually used. Expected answer: `PrismRunner` is rejected for
   the streaming pipeline because of the `AfterWatermark` trigger, and
   `SwitchingDirectRunner` (i.e. `DirectRunner`) silently falls back to
   the bundle-based runner.

5. **A portability-safe source.** Write a `read_orders(pipeline, path)`
   function that returns a Pub/Sub source when the runner is
   `DataflowRunner` and a text source otherwise, and a matching
   `write_summary`. Expected answer: the function inspects
   `options.view_as(StandardOptions).runner` and branches; the business
   logic downstream is untouched.

6. **Reflection.** Beam says "the runner can rearrange the graph" and
   Spark says "the optimiser can rewrite your plan". Both claims sound
   similar. Write a paragraph explaining what is genuinely different, and
   give one concrete case where the difference would let you ship a
   change in Beam that you could not ship in Spark.

---

## 📖 Further Reading

- Apache Beam: "A Beam Primer" (the official model overview) — https://beam.apache.org/documentation/basic-topics/
- Beam's Runner API specification — https://beam.apache.org/documentation/runtime/model/
- Apache Beam SDK development — https://beam.apache.org/documentation/sdks/python/
- Google Cloud Dataflow overview — https://cloud.google.com/dataflow/docs/about-dataflow
- Apache Beam portability: the Flink runner — https://beam.apache.org/documentation/runners/flink/
- Apache Beam: "The Top 10 Challenges for Big Data" (the paper that motivated the project) — https://research.google/pubs/pub43018/
