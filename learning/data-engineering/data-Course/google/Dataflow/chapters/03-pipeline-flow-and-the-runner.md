# 1.3 — Pipeline Flow & the Runner
> **Section 1 · Beam Fundamentals & Model · Lecture 1.3 · 6:30**

## 🎯 What you will learn

- The life of a pipeline: construction, translation, execution, teardown
- The exact steps the Runner API takes, from proto to workers
- What a **bundle** is, why the runner needs one, and how it maps to worker parallelism
- How fusion works, and exactly where fusion must stop
- Checkpointing and state, and why they are the runner's problem
- The three local runners: `BundleBasedDirectRunner`, `SwitchingDirectRunner`, and Prism
- The Prism panic on `AfterWatermark` and `+inf` watermark evaluation, explained
- How the runner chooses worker counts
- `beam.Pipeline()` vs `Pipeline.run()`, and how `--runner` is actually resolved

---

## 🧠 Concept

### The life of a pipeline

A Beam pipeline goes through four phases. Most surprises in Beam come from
confusing phase 1 with phase 3, or from assuming phase 2 is cheap when it
is not.

```text
  PHASE 1 — CONSTRUCTION (in your process, no work happens)
  ─────────────────────────────────────────────────────────────
    with beam.Pipeline() as p:
        p | "Read" >> ReadFromText(src)
          | "Map" >> beam.Map(fn)
          | "Write" >> WriteToText(dst)

    The `with` block builds a DAG of PTransforms.
    Nothing is read. Nothing is written. `beam.Map(fn)` does not call fn.

  PHASE 2 — TRANSLATION (at `run()`, still in your process)
  ───────────────────────────────────────────────────────────
    p.to_runner_api()
      ├─ serialize every DoFn into a ParDoPayload
      ├─ assign a coder to every PCollection
      ├─ attach windowing strategies
      ├─ compute the fusion plan
      └─ emit the Runner API proto

  PHASE 3 — EXECUTION (the runner's process / workers)
  ────────────────────────────────────────────────────
    proto ──▶ SDK harness ──▶ runner-native plan
          ──▶ split_into_bundles ──▶ workers process bundles
          ──▶ write outputs

  PHASE 4 — TEARDOWN
  ─────────────────
    Result state reaches DONE (or FAILED). Temp files cleaned up.
```

Two consequences follow immediately.

**First, an exception in your `Map` function does not happen when you build
the graph.** It happens on a worker, minutes later, inside a bundle. This
is the single most common source of "but it worked when I tested it" in
Beam.

**Second, the translation phase is where labels, coders, and windowing are
resolved.** An error like a duplicate transform label surfaces here, at
`run()`, not at construction.

### The Runner API steps, precisely

When you call `run()`, Beam does the following. The exact ordering varies
slightly between runners, but the substance is stable.

**Step 1 — Proto translation.** The pipeline graph is converted to the
Runner API proto. Each `ParDo`'s `DoFn` is serialised (pickled, or encoded
by the SDK's own serialiser) into a `ParDoPayload`. Each `PCollection` gets
a coder. Windowing strategies are attached.

**Step 2 — Capability check.** The runner compares the proto's
`requirements` list against the capabilities it supports. A runner that
cannot satisfy a requirement raises before any worker starts.

**Step 3 — Environment resolution.** The runner decides *where* the user
code runs. `PortableOptions.environment_type` decides this:

| `environment_type` | Where the user code runs |
|---|---|
| `LOOPBACK` | in the runner's own process — no container, no distribution |
| `DOCKER` | in a container image the runner starts |
| `PROCESS` | as a subprocess of the runner |
| `EMBEDDED` | inside the runner's JVM, in a sandboxed classloader |
| `KUBERNETES` | in a container on a Kubernetes cluster |

**Step 4 — SDK harness translation.** The harness walks the proto and
builds the runner's native execution plan. This is where Beam's
`CombinePerKey` becomes Spark's `reduceByKey` or Flink's
`AggregateFunction`.

**Step 5 — `split_into_bundles`.** The runner partitions the work into
**bundles**. A bundle is the runner's unit of parallelism, of
checkpointing, and of retry.

**Step 6 — Execution.** Workers process bundles. Outputs are written.
State is checkpointed. Metrics are reported.

**Step 7 — Completion.** The result reaches a terminal state: `DONE`,
`FAILED`, or `CANCELLED`.

### What a bundle is, and why it matters

A **bundle** is a chunk of data processed as a unit. It is the smallest
unit of work a runner can checkpoint, retry, or distribute.

```text
        PCollection (logical)
        ┌──────────────────────────────────────────────┐
        │  element 1   element 2   element 3   ...    │
        └──────────────────────────────────────────────┘
                          │
              split_into_bundles()
                          │
        ┌──────────┬──────────┬──────────┐
        ▼          ▼          ▼          ▼
     Bundle A   Bundle B   Bundle C   Bundle D
     (elem 1-25)(elem 26-50)(elem 51-75)(elem 76-100)
        │
        │  each bundle is processed by ONE worker
        │  each bundle is checkpointed independently
        │  a failed bundle is retried without redoing the others
        ▼
     Worker 1
```

Why bundles matter:

- **Parallelism.** N bundles can be processed concurrently by N workers.
  If you have 4 workers and 100 bundles, each worker processes ~25.
- **Checkpointing granularity.** In streaming, the runner checkpoints the
  state of each bundle's processing. A bundle that has been fully
  processed and whose output is durable does not need to be redone.
- **Retry granularity.** If a bundle fails, only that bundle is retried.
  In a batch job, Beam can typically retry from the last successful
  bundle boundary.
- **Memory bounds.** A bundle is bounded in size, so the runner can
  process an unbounded stream in bounded memory. This is why streaming
  pipelines do not run out of memory as data accumulates.

The practical rule: **a bundle is a batch of work, and the number of
bundles is how much parallelism the runner can exploit.** If your pipeline
produces one giant bundle, you have one worker doing all the work no
matter how many workers you provision.

Bundle size is controlled by the runner. Dataflow uses a size hint of
roughly 64 MB per bundle by default; the actual value depends on the
source and the runner. You rarely set it directly, but you should think
about it: a `Map` that touches a side input of 500 MB will load that side
input into memory *per bundle*, and the bundle size affects how many copies
of it exist in flight.

### Fusion, and where fusion stops

**Fusion** is the runner merging adjacent steps into a single processing
step, so intermediate data is never written to storage.

```text
  Unfused graph:                        Fused graph:
  Read ──▶ Parse ──▶ Validate ──▶ Write  Read+Parse+Validate ──▶ Write
        (write)   (write)   (write)
```

Fusing eliminates three I/O round-trips and their latency. On a
1-terabyte intermediate, that is the difference between a 10-minute job
and a 40-minute job.

Fusion happens when a step's output is consumed by exactly one step and
the intermediate can be kept in memory. The classic case is
`Map` → `Filter` → `Map`, which fuses into one step.

**Fusion stops at:**

| Barrier | Why |
|---|---|
| `GroupByKey` | the shuffle boundary — keys must be co-located. This is a materialisation point, always. |
| `CombinePerKey` with a non-trivial `CombineFn` | partial accumulators must be merged across workers, so there is a shuffle |
| `CombinePerKey` with a trivial combiner | a "liftable" combiner (e.g. `sum`, `min`) can often be fused into the upstream step, because the accumulation is associative and the result is order-independent |
| Side inputs | a side input is a *broadcast* — every worker needs the whole thing, so it cannot be a simple in-memory handoff |
| `Reshuffle` | this is a deliberate barrier; it is *the* tool for breaking a fusion you do not want |
| `WindowInto` | a windowing change alters the grouping semantics, so it is a boundary |
| A PCollection consumed by more than one step | the intermediate must be materialised so both consumers can read it |

The distinction between a **liftable** and a **non-liftable** combiner is
the interesting one. `sum` is liftable: `(a + b) + c == a + (b + c)`, so
you can accumulate incrementally in the upstream step and the result is
identical no matter how the data was split. A combiner that is *not*
associative — subtracting an epsilon on each merge, as in exercise 3 of
chapter 1.2 — cannot be lifted, and cannot be fused, and will give
different answers on different runners.

**`Reshuffle` deserves special attention.** It is a barrier by design: it
breaks fusion on purpose, to force a clean, uniform re-shard of the data.
You use it when:

- A skewed key is causing one worker to do all the work, and you want to
  rebalance before a downstream group.
- You want to break a long chain of steps so that intermediate state does
  not accumulate.
- You want to force a consistent partitioning regardless of what the
  upstream source did.

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create([("hot", i) for i in range(1000)])
        | "Rebalance" >> beam.Reshuffle()
        | "Key" >> beam.Map(lambda kv: ("group", kv[1]))
        | "Count" >> beam.combiners.Count.PerKey()
        | "Sink" >> beam.Map(print)
    )
```

### Checkpointing and state

In a streaming pipeline, the runner must periodically persist the pipeline's
internal state so that a failure can be recovered without reprocessing
everything from the beginning. This is **checkpointing**.

What is in a checkpoint:

- The **watermark** — how far in event time the runner believes it is.
- **Per-key state** for stateful operations — the partial accumulators
  for each `(key, window)` being aggregated.
- **Timer state** — pending timers for each key.
- **Bundle progress** — which bundles have been fully processed.

The checkpoint is written atomically. If the worker dies, the runner
restarts from the last successful checkpoint and replays from there. Because
of this, a streaming pipeline's recovery time is bounded by the
**checkpoint interval** plus the time to restore state — not by the total
data processed.

This is a property of the *runner*, not of the SDK. The same Beam pipeline
gets different checkpoint semantics on different runners:

| Runner | Checkpointing | Recovery |
|---|---|---|
| Dataflow (streaming) | automatic, continuous, to GCS | resumes from the last checkpoint; the watermark is restored |
| Flink | checkpoint barriers in the data path | restores from the latest completed checkpoint |
| Spark (Structured Streaming) | micro-batch checkpoints | replays the last incomplete micro-batch |
| Direct runners | none | a failure means restarting the pipeline |

For the direct runners, this matters: a local streaming pipeline that
crashes loses everything and must be restarted from the beginning. That is
why you test streaming logic with `TestStream` — it is deterministic and
fast, and it exercises the windowing and trigger semantics without needing
a real source.

### The local runners: three of them

Beam 2.77 ships several local runners, and they are genuinely different
engines. Confusing them is the most common source of "why did my local run
behave differently from the cloud run?"

| Runner | Engine | Speed | Streaming | Notes |
|---|---|---|---|---|
| `BundleBasedDirectRunner` | pure Python, in-process | slow (baseline) | yes | the reference implementation; supports everything |
| `SwitchingDirectRunner` | picks a specialist at submission time | fast | partly | the class behind the name `DirectRunner` |
| `PrismRunner` | Go, via a local Prism job server | fastest (2–20×) | partly | the portability path; limited feature set |
| `FnApiRunner` | the FnAPI worker model in Python | fast | no | the SDK-harness path without a container |

**`BundleBasedDirectRunner`** is the classic runner. It executes the graph
in your own Python process, one bundle at a time, using pure-Python
transforms. It is slow — roughly 1,000–10,000 elements/second for a simple
`Map` — but it supports every Beam feature, including streaming,
`userstate`, and every trigger.

**`SwitchingDirectRunner`** is what `DirectRunner` resolves to in Beam
2.77. It is a *dispatcher*, not an engine. At submission time it visits
the pipeline and decides:

```text
                  ┌─────────────────────────────────────┐
                  │  SwitchingDirectRunner (== DirectRunner)│
                  └──────────────────┬──────────────────┘
                                     │ visit the graph, check features
             ┌───────────────────────┼────────────────────────┐
             ▼                       ▼                        ▼
      Prism supported?        FnApi supported?        neither
             │                       │                        │
             ▼                       ▼                        ▼
      PrismRunner            FnApiRunner         BundleBasedDirectRunner
      (Go engine)            (Python, batch)     (Python, everything)
```

The visitor checks, among other things, whether the pipeline uses
`TestStream`, Pub/Sub I/O, `userstate` with real-time timers or combining
value state, deferred side-input combiners, exception-handling `DoFn`s,
session windows, and whether `allow_unsafe_triggers` is set. If the
pipeline uses a feature the specialised engine lacks, it falls back.

**The visitor's list is not exhaustive.** Notably, it does *not* exclude
`AfterWatermark` triggers, even though Prism cannot handle them. So a
windowed pipeline under the plain name `DirectRunner` is routed to Prism
and panics at runtime rather than falling back. This is exactly the trap
described below.

**`PrismRunner`** is the most interesting of the three. Prism is a Go
implementation of Beam's portable runner — the same Runner API proto, the
same SDK-harness mechanism, but a much faster engine. On a CPU-bound
pipeline it is routinely 2–20× faster than the bundle-based runner, and
because it is a *portable* runner, it exercises the same proto path that
Dataflow, Spark, and Flink use. That makes it the best local proxy for
"will this work on a real cluster?".

Prism is downloaded automatically on first use and cached under
`~/.apache_beam/cache/prism/`.

### The Prism panic on `AfterWatermark`

This deserves a full explanation, because it is a real and reproducible
failure that catches people out.

**The symptom.** A pipeline using `beam.WindowInto(FixedWindows(...),
trigger=AfterWatermark())` panics under Prism:

```text
ERROR:PrismRunner:panic in ElementManager.Bundles watermark evaluation goroutine (
generating bundle for stage stage-003 at watermark +inf panicked
```

followed by a Go stack trace through
`apache_beam/sdks/v2/go/pkg/beam/runners/prism/internal/engine/elementmanager.go`.

**Why it happens.** Recall the model from chapter 1.1: a batch pipeline is a
streaming pipeline whose input ends. When a bounded input is exhausted,
the runner advances the watermark to `+inf`, which closes every window and
fires every `AfterWatermark` trigger.

In the bundle-based runner, advancing the watermark to `+inf` is a normal,
well-tested path. In Prism, the watermark-advance logic is implemented
differently: when the watermark moves to `+inf`, Prism's
`ElementManager.Bundles` goroutine must generate a *new bundle* for the
affected stage — a "final" bundle containing the remaining elements so
the window can be closed and the trigger fired. In the version shipped
with Beam 2.77, that bundle-generation path panics.

So the failure is not in *your* logic. It is in Prism's handling of the
`+inf` watermark transition, which is exactly the transition a bounded
input triggers. A `+inf` watermark evaluation is a batch-closure event,
and Prism's implementation of it is incomplete.

**Why the course pipeline hits it.** `project/streaming_pipeline.py` uses
`AfterWatermark` with `FixedWindows`. Point it at a bounded file and the
watermark advances to `+inf` at the end — which is the trigger. Hence the
panic.

**The three ways to handle it:**

1. **Use `BundleBasedDirectRunner` for anything with `AfterWatermark`.**
   This is what the course's `beam_options.py` does: `DEFAULT_RUNNER` is
   `BundleBasedDirectRunner`, precisely because Prism cannot handle the
   course's streaming pipeline.

2. **Pin the runner explicitly.** Do *not* rely on the plain name
   `DirectRunner` to save you here. The switching runner's visitor
   excludes `TestStream`, exception-handling `DoFn`s, deferred
   side-input combiners, `userstate` with combining value state, real-time
   timers, and session windows — but it does **not** exclude
   `AfterWatermark`. So `DirectRunner` selects Prism, and Prism panics at
   runtime. The fallback only triggers on a *submission* failure, not on a
   panic mid-run. Use `--runner BundleBasedDirectRunner` and be explicit.

3. **Avoid `AfterWatermark` under Prism.** Use `AfterCount` with
   `allow_unsafe_triggers`, or a `DefaultTrigger`, or restructure to use
   `GroupByKey` without windowing. But this changes the semantics, so it
   is a real trade-off rather than a fix.

**The general lesson.** The switching runner's fallback is a safety net
against *submission* failures, not a guarantee against runtime panics. And
a pipeline that "works locally" may be running on a completely different
engine than you think. Check the log for the line that names the runner
actually used:

```text
INFO:apache_beam.runners.direct.direct_runner:Running pipeline with PrismRunner.
```

If you see that line in a job you expected to be the classic runner, you
know why it panicked.

### How the runner chooses worker counts

The number of workers is a *deployment* decision, and it differs per
runner.

**Dataflow** (serverless, autoscaling). You specify a worker count as a
*range* and Dataflow picks within it:

```bash
--max_num_workers 200
--min_num_workers 10
```

Dataflow starts at the minimum and scales up as the pipeline's
backlog grows, and scales down when the backlog drains. The knob that
matters is the **autoscaling algorithm** — `HighThroughput` (aggressive
scaling, more expensive) versus `Throughput` (conservative). Dataflow's
own guidance: start with the default and change it only if you have
measured a problem.

**Spark** (via the Beam Spark runner). You size the cluster yourself.
The Beam `SparkRunner` takes `--spark_master`, and worker count is a
cluster property. The `num_workers` option exists but is only a hint.

**Prism / Direct runners.** Single-process by default. `PrismRunner` can
use multiple workers through the portable runner's job service, but on a
laptop you are normally running one.

**Flink.** Parallelism is set by the Flink job graph, which the harness
derives from the Beam graph. You can hint at it with
`--parallelism`.

The practical rule for Dataflow: **give the runner a generous maximum and
a modest minimum.** Setting `--max_num_workers 500 --min_num_workers 1` on
a job that only needs 4 workers costs nothing — you pay for what you use.
Setting `--max_num_workers 4` on a job that needs 500 means you sit
backlogged for the whole run.

### `beam.Pipeline()` vs `Pipeline.run()`

There are two ways to execute a pipeline, and they differ in one important
way: when the pipeline runs.

```python
import apache_beam as beam


def run_with_context_manager():
    """Form 1: the context manager runs the pipeline when the block exits."""
    with beam.Pipeline() as p:
        (
            p
            | "Create" >> beam.Create([1, 2, 3])
            | "Double" >> beam.Map(lambda x: x * 2)
            | "Sink" >> beam.Map(print)
        )
    # Execution happened HERE, as the block exited.


def run_with_explicit_run():
    """Form 2: explicit run, with a handle to the result."""
    p = beam.Pipeline()
    (
        p
        | "Create" >> beam.Create([1, 2, 3])
        | "Double" >> beam.Map(lambda x: x * 2)
        | "Sink" >> beam.Map(print)
    )
    result = p.run()
    print(result.state)
    result.wait_until_finish()
    return result


run_with_context_manager()
result = run_with_explicit_run()
```

| | `with beam.Pipeline()` | `p.run()` |
|---|---|---|
| When it runs | when the block exits | when you call `run()` |
| Handle to the result | no (it is in the `with` scope) | yes — `PipelineResult` |
| Can you inspect state? | no | yes: `result.state`, `result.metrics()` |
| Can you cancel? | no | yes: `result.cancel()` |
| Can you run it again? | no, the pipeline is consumed | yes, `p.run()` again |
| Blocks? | yes, unless `--no_wait_until_finish` | no — `run()` returns immediately |

Two further details:

- **The `with` form is not "safer" or "more idiomatic"** — they are
  equivalent in execution. Use the `with` form for scripts. Use `run()`
  when you need the result handle, when you want to submit several
  pipelines from one process, or when you want to submit and return
  (the Dataflow templates and Flex Templates use this).
- **A pipeline object is consumed by `run()`.** Running the same `Pipeline`
  twice raises an error. This matters for the `SwitchingDirectRunner`
  fallback: the switching runner may run your pipeline with Prism, fail,
  and then run it again with the bundle-based runner — all within the same
  `run()` call, so you never see the error.

### How `--runner` is actually resolved

The resolution is a three-step lookup, and it is worth knowing exactly,
because "why did my `--runner` flag do nothing?" is a common question.

```text
  1. argparse (Beam's own)
     `--runner DirectRunner` is parsed into StandardOptions.runner
     as a plain STRING.

  2. Pipeline.__init__ / Pipeline.run
     runner = options.view_as(StandardOptions).runner
     if runner is None:
         runner = StandardOptions.DEFAULT_RUNNER      # "DirectRunner"
     if isinstance(runner, str):
         runner = create_runner(runner)               # import + instantiate

  3. create_runner(runner_name)
     _RUNNER_MAP = {last_component.lower(): full_path, ...}
     runner_name = _RUNNER_MAP.get(name.lower(),
                   _RUNNER_MAP.get(name.lower() + 'runner', name))
     if '.' in runner_name:
         module, cls = runner_name.rsplit('.', 1)
         return getattr(importlib.import_module(module), cls)()
     else:
         raise ValueError(...)
```

The details that matter:

- **The fallback order is exact-match first, then `name + "runner"`.** So
  `--runner Direct` resolves to `DirectRunner`, and `--runner DirectRunner`
  resolves directly. The map is built from the fully-qualified class paths
  in `StandardOptions.ALL_KNOWN_RUNNERS`.
- **If the name has no dot, it is an error.** That is why
  `--runner Foo` gives `ValueError: Unexpected pipeline runner: Foo`.
- **`--runner` is not the same as the `runner` constructor argument.**
  `beam.Pipeline(runner="DataflowRunner")` and
  `beam.Pipeline(options=options)` with `--runner DataflowRunner` end up in
  the same place, but if you pass *both* a runner object and options whose
  `runner` differs, the constructor argument wins.
- **The course's `beam_options.build_options()` filters the argument list
  before Beam sees it**, because Beam's `PipelineOptions` raises
  `SystemExit` on a flag it does not recognise, and the course scripts
  have their own flags (`--input`, `--output`).

---

## 🛠️ Hands-On

### The Same Pipeline, Two Runners

This hands-on runs one pipeline under two local engines and reports the
timings, so you can see the engine difference directly.

### Step 1 — Generate the sample data

```bash
cd data-engineering/data-Course/google/Dataflow
python resources/sample_data.py --output-dir ./sample_data
wc -l sample_data/orders.csv
```

### Step 2 — Run under the bundle-based runner and time it

```bash
time python project/batch_pipeline.py \
  --runner BundleBasedDirectRunner \
  --input ./sample_data/orders.csv \
  --output ./out/ch13_bundled
```

### Step 3 — Run under Prism and time it

```bash
time python project/batch_pipeline.py \
  --runner PrismRunner \
  --input ./sample_data/orders.csv \
  --output ./out/ch13_prism
```

The first Prism run downloads and caches a Go binary under
`~/.apache_beam/cache/prism/`, so it is much slower than subsequent runs.
Run it a second time to get a fair measurement:

```bash
time python project/batch_pipeline.py \
  --runner PrismRunner \
  --input ./sample_data/orders.csv \
  --output ./out/ch13_prism_warm
```

### Step 4 — Compare the outputs

```bash
diff <(cat out/ch13_bundled*) <(cat out/ch13_prism_warm*) && echo "IDENTICAL OUTPUT"
```

Identical output from two completely different engines — one pure Python,
one Go, both going through the Runner API proto — is the portability claim
demonstrated rather than asserted.

### Step 5 — Run the comparison automatically

Put the timings in one table:

```python
import statistics
import subprocess
import sys
import time

RUNNERS = ["BundleBasedDirectRunner", "PrismRunner"]
INPUT = "./sample_data/orders.csv"


def run_once(runner, output):
    """Run the batch pipeline under a runner and return elapsed seconds."""
    start = time.perf_counter()
    proc = subprocess.run(
        [
            sys.executable,
            "project/batch_pipeline.py",
            "--runner",
            runner,
            "--input",
            INPUT,
            "--output",
            output,
        ],
        capture_output=True,
        text=True,
    )
    elapsed = time.perf_counter() - start
    if proc.returncode != 0:
        print(proc.stderr[-2000:])
        raise SystemExit(f"{runner} failed")
    return elapsed


results = {}
for runner in RUNNERS:
    # Warm up: the first Prism run downloads a binary.
    run_once(runner, f"./out/ch13_warm_{runner}")
    timings = [run_once(runner, f"./out/ch13_{runner}") for _ in range(3)]
    results[runner] = statistics.median(timings)

baseline = results["BundleBasedDirectRunner"]
print(f"{'runner':<26}{'median s':>10}{'speedup':>10}")
for runner, seconds in results.items():
    print(f"{runner:<26}{seconds:>10.2f}{baseline / seconds:>9.1f}x")
```

Expect Prism to be several times faster on this workload. The exact factor
depends on your machine and on how much of the pipeline is Python-function
overhead versus actual work.

### Step 6 — Watch the runner actually get chosen

The switching runner logs which engine it picked:

```bash
python project/batch_pipeline.py \
  --runner DirectRunner \
  --input ./sample_data/orders.csv \
  --output ./out/ch13_switching 2>&1 | grep -iE "prism|fnapi|falling back|direct runner" | head -10
```

The log lines that matter:

- `Running pipeline with PrismRunner.` — the specialised engine was used.
- `Pipeline failed on PrismRunner, falling back to DirectRunner.` — Prism
  could not run this pipeline, and the bundle-based runner took over.
- `Exception with PrismRunner: ... Falling back to DirectRunner` — Prism
  raised during preparation.

Note the scope of those fallbacks: they cover *submission* failures. A
Prism panic **during execution** is not caught, and the job dies. The next
step shows that.

### Step 7 — Reproduce the Prism panic

Now watch the panic happen, so you recognise it in the wild:

```bash
python project/streaming_pipeline.py \
  --runner PrismRunner \
  --input ./sample_data/events.ndjson \
  --output ./out/ch13_prism_streaming 2>&1 | head -20
```

You will see the Go panic and the stack trace through
`elementmanager.go`. The fix is to run the streaming pipeline under the
bundle-based runner:

```bash
python project/streaming_pipeline.py \
  --runner BundleBasedDirectRunner \
  --input ./sample_data/events.ndjson \
  --output ./out/ch13_bundled_streaming
```

And it works — because `AfterWatermark` plus a `+inf` watermark is exactly
the path Prism cannot handle.

### Step 8 — Inspect the result handle and the runner resolution

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions
from apache_beam.runners.runner import create_runner

# The result handle.
p = beam.Pipeline()
(
    p
    | "Create" >> beam.Create([1, 2, 3])
    | "Double" >> beam.Map(lambda x: x * 2)
    | "Sink" >> beam.Map(print)
)
result = p.run()
print("state before wait:", result.state)
result.wait_until_finish()
print("state after wait:", result.state)

# The runner resolution.
options = PipelineOptions(["--runner", "PrismRunner"])
name = options.view_as(StandardOptions).runner
print("resolved name:", name)
print("runner class:", type(create_runner(name)).__name__)
```

---

## 🛠️ Common Errors and Fixes

### `panic in ElementManager.Bundles watermark evaluation goroutine: generating bundle for stage stage-003 at watermark +inf panicked`

```text
ERROR:PrismRunner:panic in ElementManager.Bundles watermark evaluation goroutine (
generating bundle for stage stage-003 at watermark +inf panicked

github.com/apache/beam/sdks/v2/go/pkg/beam/runners/prism/internal/engine.(*ElementManager).Bundles.func2.1()
	github.com/apache/beam/sdks/v2/go/pkg/beam/runners/prism/internal/engine/elementmanager.go:410 +0x38
panic({0x1065efee0?, 0x23c84f019ca0?})
	runtime/panic.go:860 +0x12c
```

Prism cannot generate the final bundle when the watermark advances to
`+inf` — the transition that closes a window under an `AfterWatermark`
trigger. This is a Prism limitation, not a bug in your pipeline.

**Fix:** use `--runner BundleBasedDirectRunner` for pipelines with
`AfterWatermark`. Do **not** rely on the plain `DirectRunner` name to save
you: the switching runner's visitor does not exclude `AfterWatermark`, so
it selects Prism and the panic happens anyway. The course's
`beam_options.DEFAULT_RUNNER` is `BundleBasedDirectRunner` for exactly
this reason.

To confirm which engine actually ran, grep the log:

```bash
python project/streaming_pipeline.py \
  --runner DirectRunner \
  --input ./sample_data/events.ndjson \
  --output ./out/ch13_check 2>&1 | grep -i "Running pipeline with"
```

`Running pipeline with PrismRunner.` means Prism was selected — and for an
`AfterWatermark` pipeline, that means the panic is coming.

### `ValueError: Transform name is already used`

```text
RuntimeError: Transform name is already used
```

Two transforms in the same pipeline share a label. The message does not say
which. The error is raised during translation, at `run()` — not when the
graph is built.

**Fix:** the course linter finds this statically, before you run anything:

```bash
python resources/audit_course.py
```

### `RuntimeError: GroupByKey is not implemented in the FnApiRunner`

```text
RuntimeError: GroupByKey is not implemented in the FnApiRunner
```

You are on a runner whose harness does not implement the transform. The
`SwitchingDirectRunner` normally avoids this by falling back, but an
explicit `--runner FnApiRunner` does not.

**Fix:** use `DirectRunner` (the switching one) or
`BundleBasedDirectRunner`.

### `apache_beam.runners.portability.prism_runner.PrismRunner: ... No such file or directory`

```text
FileNotFoundError: [Errno 2] No such file or directory:
'.../apache_beam-v2.77.0-prism-darwin-arm64'
```

The Prism binary could not be downloaded — usually a network restriction
or an unsupported platform.

**Fix:** fall back to the bundle-based runner. If your environment blocks
the download, set `BEAM_RUNNER=BundleBasedDirectRunner` in your `.env` and
the course scripts will use it automatically.

### `ValueError: Unexpected pipeline runner: Foo. Valid values are ...`

```text
ValueError: Unexpected pipeline runner: Foo. Valid values are DataflowRunner,
BundleBasedDirectRunner, DirectRunner, SwitchingDirectRunner, ...
```

The name did not match the runner map, and appending `runner` did not match
either, and the string contains no dot.

**Fix:** use a listed name, or the fully qualified class path.

### The job hangs with no output

```text
WARNING:apache_beam.utils.subprocess_server:Really destroying service at localhost:54096 ...
```

No output and no completion usually means the pipeline is waiting for
something that will never arrive — most often a watermark that never
advances past a window boundary. Under a runner that does not advance the
watermark to `+inf` for a bounded input, an `AfterWatermark` trigger never
fires.

**Fix:** for a bounded file input, always use a runner that advances the
watermark to `+inf` at the end. `BundleBasedDirectRunner` does.

### `error: [Errno 2] No such file or directory: 'out/summary00000of00001'`

The output filename includes the shard suffix, so hard-coding it fails.

**Fix:** glob it, or write a `shard_name_template=""` to get a fixed name:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create(["a", "b"])
        | "Write" >> beam.io.WriteToText(
            "./out/fixed_name",
            num_shards=1,
            shard_name_template="",
        )
    )
```

---

## 💡 Production Notes

- **Development loop: use `BundleBasedDirectRunner`; verify on Prism.**
  The bundle-based runner is slow but feature-complete and produces the
  clearest error messages. Prism is 2–20× faster and exercises the real
  portable path. Use the slow one while you are writing code, and the fast
  one to check that you have not accidentally used a feature that will not
  survive the trip to a cluster.
- **Do not benchmark on the direct runner.** A pure-Python, single-process,
  no-serialisation runner is not a proxy for a distributed one. Numbers
  from `BundleBasedDirectRunner` tell you about your algorithm, not about
  your cluster. Get to Dataflow or a real Spark cluster before you make a
  cost or capacity argument.
- **Prism is the best local portability test you have.** It runs the same
  proto/harness path as Dataflow. If a pipeline works on Prism, it is very
  likely to work on Dataflow. If it fails on Prism with a panic, you have
  found a portability problem in minutes rather than after a 40-minute
  cluster provisioning.
- **Pin your runner; do not trust the fallback.** When
  `SwitchingDirectRunner` falls back, the job still succeeds — you just
  get the slow engine. And the fallback only covers *submission* failures,
  not runtime panics. A pipeline that Prism cannot handle at all (like
  the `AfterWatermark` case) panics rather than falling back. In
  production, name the runner explicitly and alert on the
  `Running pipeline with ...` log line.
- **Bundle size is your memory bound.** In streaming, the state per
  `(key, window)` lives in memory until it is checkpointed. A high-cardinality
  key with a long window can exhaust a worker's heap. If a Dataflow worker
  dies with OOM, look at your key cardinality and your window length
  before you look at anything else.
- **Set `--min_num_workers` deliberately.** Too low and the job spends its
  first minutes under-provisioned; too high and an idle streaming job
  burns money. A streaming job that is waiting on a slow source should
  have a small minimum (1–2) and a generous maximum.
- **The `--no_wait_until_finish` flag exists for a reason.** A Flex
  Template that submits a job and returns immediately needs it. Every
  ordinary script should *not* use it, because the process will exit and
  take your monitoring with it.

---

## 🔑 Key Takeaways

- A pipeline has four phases: **construction** (no work), **translation**
  (to the Runner API proto), **execution** (the runner's workers), and
  **teardown**. Errors in your `Map` surface in phase 3, on a worker.
- A **bundle** is the runner's unit of parallelism, checkpointing, and
  retry. Bundles bound memory, which is how a streaming pipeline processes
  an unbounded stream.
- **Fusion** merges adjacent steps to eliminate intermediate I/O. It stops
  at `GroupByKey`, non-liftable combiners, side inputs, `WindowInto`, and
  any PCollection with more than one consumer. `Reshuffle` is a barrier
  you insert on purpose.
- **Checkpointing and state are the runner's job.** Dataflow checkpoints
  the watermark and per-key state continuously; the direct runners do not
  checkpoint at all, so a local streaming crash loses everything.
- Beam 2.77 has **three local runners**: `BundleBasedDirectRunner` (pure
  Python, complete), `SwitchingDirectRunner` (the class behind the name
  `DirectRunner`, a dispatcher), and `PrismRunner` (Go, 2–20× faster,
  limited features).
- **Prism panics on `AfterWatermark` because it cannot generate the final
  bundle when the watermark advances to `+inf`** — the exact transition
  that closes a window on a bounded input. Use `BundleBasedDirectRunner`
  for those pipelines.
- **`--runner` resolves as a string through a lowercase map, then
  `create_runner` imports the class.** `options.runner` raises
  `AttributeError`; use `options.view_as(StandardOptions).runner`.
- **The runner owns worker counts.** On Dataflow, give a generous
  `--max_num_workers` and a modest `--min_num_workers`; you pay for what
  you use.

---

## 📚 Practice Exercises

1. **Measure the engine difference.** Run the timing script from the
   hands-on with three runners: `BundleBasedDirectRunner`, `DirectRunner`
   (the switching one), and `PrismRunner`. Expected answer: Prism is
   several times faster; `DirectRunner` is close to Prism for a simple
   batch pipeline because the switching runner picks Prism. Then add a
   `GroupByKey` to the pipeline and re-measure — the gap narrows, because
   the shuffle dominates and the engines converge.

2. **Find the fusion boundary.** Write a pipeline of six `Map`/`Filter`
   steps followed by a `CombinePerKey`. Print the number of transforms in
   `p.to_runner_api().components.transforms`. Expected answer: the
   proto lists the *logical* steps, not the fused ones — the fusion plan is
   computed by the runner, and the proto shows the pre-fusion graph. This
   is why "count the steps in the proto" does not tell you how many
   workers actually do work.

3. **Break the `Reshuffle` habit.** Take the course's batch pipeline and
   insert a `beam.Reshuffle()` between `KeyByRegion` and
   `RevenueByRegion`. Measure the run time before and after. Expected
   answer: it gets *slower* on the direct runner, because `Reshuffle` is a
   forced barrier and the direct runner is single-process. Explain why
   the same barrier might be free — or even profitable — on Dataflow.

4. **Prove the `+inf` watermark is the trigger.** Write a small pipeline
   with a `FixedWindows` window and an `AfterWatermark` trigger, reading
   from `beam.Create` (a bounded source). Run it under
   `BundleBasedDirectRunner` (it should print output) and then under
   `PrismRunner` (it should panic). Expected answer: the bounded source
   is what makes the watermark advance to `+inf`, which is what triggers
   the panic. The same pipeline driven by `TestStream` (from
   `apache_beam.testing.test_stream`) and an explicit
   `advance_watermark_to` also advances the watermark, and hits the same
   path.

5. **Inspect the result handle.** Use the `p.run()` form to submit a
   pipeline, and print `result.state` before and after
   `wait_until_finish()`. Expected answer: the state is `RUNNING` (or
   `DONE` for a trivial pipeline) before the wait, and `DONE` after.
   Then add a `Map` that raises, and observe the state become `FAILED`
   with the exception propagated from the worker.

6. **Reflection.** The switching runner falls back silently on some
   unsupported features, and does *not* fall back on others — the
   `AfterWatermark` case panics instead. Write a paragraph on why that
   split behaviour is both a good design (portability is preserved for
   the common cases) and a dangerous one (you may not know which engine
   ran your job, and a runtime panic is worse than a slow run), and
   propose a mitigation you would put in a production pipeline's logging.

---

## 📖 Further Reading

- Apache Beam: "A Beam Primer" (the model overview) — https://beam.apache.org/documentation/basic-topics/
- Beam's Runner API specification — https://beam.apache.org/documentation/runtime/model/
- Apache Beam: Execution model — https://beam.apache.org/documentation/runtime/model/
- Apache Beam: Bundle processing (the FnAPI execution model) — https://beam.apache.org/documentation/runtime/fnapi-performance-model/
- Google Cloud Dataflow: autoscaling — https://cloud.google.com/dataflow/docs/autoscaling
- Apache Beam Prism (the Go portable runner) — https://beam.apache.org/documentation/runners/prism/
