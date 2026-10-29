# Top 50 — Google Dataflow with Apache Beam

> **50 questions · The highest-yield subset · Read this the night before**

These fifty questions were selected from the full bank by five criteria:
**high decision impact** (the answer changes what you build), **cross-layer**
(the answer connects the model to the runtime to the operations), **quantifiable**
(a number is attached), **contested** (reasonable senior engineers disagree),
and **common misconception** (the wrong answer is what a lot of people say).

Every answer is written the way a senior engineer who has actually run this in
production would say it out loud: the direct answer first, then the mechanism,
then when the obvious alternative wins, then the failure you have seen, and
the numbers.

---

## The model

### 1. What are the three core abstractions in Beam, and what breaks if you get one of them wrong?

`PCollection` (the data), `PTransform` (the operation), `PRunner` (the executor).
A PCollection is an immutable, lazy description of a distributed dataset; a
PTransform is a function from PCollections to PCollections; a PRunner takes
the graph and executes it.

Getting the PCollection wrong is the expensive mistake. Treat it as a Python
list and you will write `for row in pcoll:` and get an empty loop. The
mechanism that saves you is laziness: nothing is computed until a sink consumes
it, and the runner is free to fuse, reorder and parallelise the graph.
Immutability is what lets you fan one PCollection out to five branches.

The runner buys portability of *behaviour* but not of *configuration*: the
graph is portable, the flags are not.

**Failure story:** a candidate wrote `results = p | "Sum" >> beam.CombinePerKey(sum)`
then `print(results)`. Nothing printed, and the job succeeded in 4 seconds.
The graph was built, never run. Every branch must end in a sink.

### 2. Why must a PCollection be immutable, and what breaks if you mutate one?

Because Beam may execute the same step more than once, on different workers,
in a different order, and may retry a bundle after a failure. If a transform
could mutate its input, a retry would double-count, and two branches reading
the same PCollection could see different values.

The mechanism is that Beam's execution model is a dataflow: elements flow
through immutable stages, and the only mutable thing is *state*, which is
explicit and checkpointed (timers, `BagState`, `SetState`,
`CombiningValueState`).

**Failure story:** a "cheap" optimisation kept a module-level dict as a
running total inside a `DoFn`. On `DirectRunner` it produced the right
number — one process, one copy. On Dataflow each worker kept a private copy,
and the reported revenue was the per-worker partial multiplied by the worker
count: a 400× overstatement on a 400-worker job. The fix is
`beam.CombinePerKey(sum)`.

### 3. What exactly is a bundle, and why does it decide your job's performance?

A bundle is the unit of work a runner processes: a batch of elements grouped
by key so that per-key state and combiners can be applied incrementally
without a full shuffle. The runner sizes bundles (default 128 elements in the
Python SDK) and processes them in parallel across workers.

The mechanism that matters: for a keyed operation, elements of the same key
must land in the same bundle, otherwise the combiner's partial results have
to be merged. Beam handles this by keying the upstream step's output, so the
"read" side of a shuffle is bundle-aligned by construction.

**Failure story:** a pipeline fine at 10 GB started taking 40 minutes per job
at 400 GB. The graph showed a wide, slow `GroupByKey` stage and one worker
at 100% CPU while 199 idled. That was skew — one key holding 40% of the rows
— not bundle size. The fix was to split the hot key upstream.

### 4. Where does fusion help, and where does it hurt you?

Fusion is the runner merging consecutive compatible steps into one stage so
intermediate data is never written or re-read. `Map → Filter → Map` collapses
into a single fused step, saving a serialisation and a GCS round trip. This
is the payoff of expressing work in the model instead of scripting it.

Fusion hurts in two situations: when the fused stage cannot be parallelised
as well as the stages were separately (a heavy `ParDo` fused with a wide read
can pin one stage), and when you *want* a materialisation point — a
deliberate `Reshuffle` breaks fusion and forces a barrier.

**Failure story:** a job used 200 workers on a 10 GB input and was billed
$14 for 6 minutes of wall clock. The graph showed one fused stage that could
not start until a large fraction of the input had been read. Adding a
`Reshuffle` before the expensive `ParDo` split the stage and cut the job to
90 seconds and $0.40. Fusion is usually your friend, but it is a *decision
made for you*.

### 5. Is Beam's "batch is streaming whose input ends" literally true?

Yes, and the mechanism is the watermark. When a bounded source is exhausted,
the runner advances the watermark to `+inf`, which closes every window, fires
every `AfterWatermark`, and lets the pipeline finish. A batch job is a
streaming job that receives one final "no more data" signal.

This is why a batch pipeline and a streaming pipeline sharing the same
windowing code produce the same numbers. The only differences are that the
batch job terminates and that its input is known in advance.

**Where it breaks:** it holds only for *bounded* inputs. A batch job reading
a Kafka topic with no end offset, or a Pub/Sub subscription, is a streaming
job submitted by the batch runner. Beam does not infer boundedness from the
file extension.

### 6. What does Beam actually guarantee about delivery, and what does it not?

Beam guarantees **at-least-once** delivery of elements within a pipeline, and
exactly-once *state* semantics for keyed state (a `CombiningValueState` update
is not applied twice for the same element). It does **not** guarantee
exactly-once end-to-end delivery to an external sink. If a worker dies after
writing to BigQuery but before checkpointing, the bundle is replayed and the
rows are written twice.

The mechanism is the checkpoint: the runner periodically snapshots the state
of every bundle's watermark and per-key state, and on recovery it replays
from the last checkpoint. Anything that happened outside Beam's state
boundary is not covered by that guarantee.

**Failure story:** a nightly BigQuery load produced a table with exactly
1.004× the expected row count, and the discrepancy grew with job size. The
sinks were appends with no primary-key dedup. The fix was to write into a
staging table and `MERGE` into the target on a key, which makes the write
idempotent regardless of replay.

### 7. Why does a PCollection print as a graph rather than as data?

Because Beam is lazy: constructing a PCollection only records a step in the
pipeline graph. `print(pcoll)` gives you the `PCollection` object's repr,
which for the Python SDK renders the pipeline's step list — it is a debugging
aid, not a data dump. Actual values only exist inside a running bundle.

This trips up people coming from Spark, where `df.show()` and
`df.count()` trigger actions. Beam's equivalent of an action is **any
terminal transform**: a write, a `beam.combiners.Count.PerKey()` feeding a
sink, or `assert_that` inside a `TestPipeline`.

**Failure story:** a "pipeline" that only built a PCollection and printed it
exited 0 in 3 seconds, and the job dashboard showed no worker ever started.
The failure was invisible in CI because the exit code was 0 — CI needs an
assertion, not a print.

---

## Execution and the runner

### 8. How does Beam decide which runner to use?

`--runner` on the command line, resolved at pipeline construction time and
baked into the graph as an immutable pipeline option. With no flag, the
Python SDK defaults to `BundleBasedDirectRunner`. The flag is **read-only** —
assigning `options.runner = "..."` raises `AttributeError` — because the
runner choice changes the graph structure, the serialisation format and the
deployment target, and the runner must know before the graph is built.

A `PipelineOptions` object is not a config dict. To read a runner-specific
flag you must view the right subclass:

```python
from apache_beam.options.pipeline_options import GoogleCloudOptions, PipelineOptions

options = PipelineOptions(["--runner=DataflowRunner", "--region=us-central1"])
region = options.view_as(GoogleCloudOptions).region
```

**Failure story:** `options.region = "us-central1"` raised
`AttributeError: 'PipelineOptions' object has no attribute 'region'`, and
the candidate called it a Beam bug. It is not: `region` lives on
`GoogleCloudOptions`; `view_as` is how you reach it.

### 9. What is the difference between `BundleBasedDirectRunner` and the Prism `DirectRunner`?

`BundleBasedDirectRunner` is the classic pure-Python runner: it implements
the full trigger and windowing feature set and behaves like Dataflow.
Prism is a Go-based runner shipped from Beam 2.60 that is typically 2–3×
faster but does not implement every trigger — it panics on `AfterWatermark`
and on the `+inf` watermark evaluation that `TestPipeline` performs.

The mechanism behind the panic: Prism evaluates the watermark in a separate
goroutine, and the `+inf` end-of-input evaluation is not yet supported there.
Use Prism for batch pipelines where you want speed; use the classic runner
for anything touching triggers, windows or `TestPipeline`.

**Failure story:** a test suite passed locally on Prism and failed in CI with
`panic in ElementManager.Bundles watermark evaluation goroutine`. The
pipeline was fine; the runner was wrong for the test. One line —
`--runner=BundleBasedDirectRunner` — fixed it.

### 10. How does the runner parallelise a shuffle, and what does that cost?

A shuffle is two-phase: a *read* phase where upstream workers partition
output by key and write partitions to a shuffle store (GCS on Dataflow), and
a *write* phase where downstream workers read the partitions for their key
range and apply the aggregation. The expensive part is that the data crosses
the network and lands in durable storage twice.

The cost is why `CombinePerKey` and `GroupByKey` behave so differently. A
`GroupByKey` must materialise every element of a group before user code sees
it, so its memory is O(group size) and it fails on a hot key. A
`CombinePerKey` keeps a compact accumulator per key, so memory is O(keys ×
accumulator size).

**Numbers:** a shuffle writes roughly 2× the shuffled bytes to GCS plus the
network transfer. At $0.02/GB, a 1 TB shuffle is about $40 of storage traffic
before vCPU-hours. Filtering before the shuffle is the highest-leverage
optimisation.

### 11. Why does the same Beam code behave differently on different runners?

Because the model specifies *semantics*, not *execution*. Bundle sizes, fusion
decisions, shuffle partitioning and worker counts are all runner-specific.
Beam guarantees the output is the same *set* of elements; it does not
guarantee the same order, the same number of stages, or the same intermediate
file layout.

The mechanism that bites is **ordering**. A `Map` that preserves input order
in the Direct Runner may not on Dataflow, because elements are distributed
across workers. `beam.combiners.Count` and `CombinePerKey` are
order-independent by construction; a `GroupByKey` followed by a `Map` that
takes `min()` of a list is not.

**Failure story:** a test asserted `assert_that(result, equal_to([...]))`, passed
locally, and failed on Dataflow. The pipeline was correct; the assertion was
order-sensitive. But the *same* symptom can be a real bug in a
non-associative combiner — so check the merge function first.

### 12. What does "the runner can rearrange the graph" buy you that a Spark job does not have?

It buys you **fusion and global optimisation**. The runner can fuse adjacent
steps, sink partial results, split sources, and reorder work to reduce I/O —
because the graph is a declarative description, not a sequence of commands.
Spark's DataFrame API optimises *within* the DataFrame abstraction; a shell
script has no such freedom.

The related capability is **runner-specific rewrites**: Dataflow can push a
`WriteToBigQuery` into a native streaming sink, or fuse a `ReadFromBigQuery`
with the transform that follows, because the graph tells it what the data is
*for*.

**Where it does not help:** when you need to control the physical plan
precisely — a specific partitioning, a fixed shard count — the abstraction
gets in your way and you insert explicit barriers like `Reshuffle`.

### 13. Why does the Python SDK sometimes feel slower than Java, and when does that matter?

The Python SDK does more work per element: it constructs Python objects, calls
the coder to serialise them, and crosses a pickling boundary into the runner's
data plane. The Java SDK works on byte arrays and encoded elements, so it does
far less per-element work. In practice the Python SDK is roughly 1.5–3×
slower on CPU-bound pipelines, and much worse on fine-grained pipelines with
millions of tiny elements.

It matters when the pipeline is per-element-CPU-bound at high volume — heavy
parsing, string munging, thousands of `Map` steps. It does *not* matter when
the pipeline is I/O- or shuffle-bound, which is most production pipelines.
The lever is fewer, coarser steps: one `ParDo` doing five things beats five
`Map`s doing one each.

**Production note:** the SDK you develop against is not the SDK that runs in
production, especially with classic templates — see
[Question 38](#38-why-is-the-sdk-version-in-a-template-a-production-risk-and-how-do-you-mitigate-it).

---

## Transforms and combiners

### 14. When is `Map` the wrong choice?

Whenever you need one input to produce zero or many outputs. `Map` is strictly
one-to-zero-or-one; a `Map` that returns a list gives you a PCollection of
lists, which you will either flatten later (an extra step) or, worse, write
into a text sink and get `['a', 'b']` in your output.

`FlatMap` is `Map` with the fan-out. Use it when cardinality changes:
splitting a CSV line into fields, exploding a nested JSON array, expanding a
row into per-item records.

**Failure story:** a job wrote a BigQuery `REPEATED` field correctly by
accident, but a downstream consumer read the column as a `STRING` and got
`"['a', 'b']"`. The `Map` produced a Python list, the `FastPrimitivesCoder`
serialised it, and the JSON sink stringified it. The fix was `FlatMap` plus
an explicit `Row` output. The general lesson: if a `Map` returns a
collection, you almost always wanted a `FlatMap`.

### 15. What is the difference between `ParDo` and `Map`, and when do you actually need `ParDo`?

`Map` is a `ParDo` specialised for a one-to-one function. `ParDo` can emit
zero, one or many elements per input, and it can read side inputs, windowing
parameters, `PaneInfo`, and state.

You need `ParDo` for a *side effect* — emitting to multiple outputs, emitting
conditionally, or reading a `WindowedValue` with its timestamp. You do **not**
need it for "more complex logic": a `Map` whose function does five things is
still a `Map`, and a `DoFn` subclass costs you a class, a serialisation
boundary, and a `setup()`/`teardown()` lifecycle.

**Failure story:** a candidate rewrote every `Map` as a `ParDo` subclass "for
flexibility". The job failed at submission with a pickling error that named
neither the `DoFn` class nor the `requests.Session` it held in `__init__`.
`Map` on a module-level function has the same pickling requirement, but the
traceback is shorter and the intent is clearer.

### 16. Why does `CombinePerKey` scale where `GroupByKey` does not?

Because `CombinePerKey` never materialises the group. It applies your function
incrementally to a compact **accumulator** and merges partial accumulators
across the shuffle. `GroupByKey` buffers every element of every group in
memory, then hands you the whole list.

The mechanism: Beam's combiner protocol has four methods —
`create_accumulator`, `add_input`, `merge_accumulators`, `extract_output`.
The runner calls `add_input` per element and `merge_accumulators` to combine
partials from different workers. Memory is O(keys × accumulator size), not
O(data).

**Where the alternative wins:** `GroupByKey` is *correct* and sometimes
*necessary* — when the answer genuinely depends on the whole group (an exact
median, a percentile, a sort, a "top 10 by a non-combinable score"). An exact
median cannot come from a mergeable summary, but an approximate one can come
from a bounded sample, and Beam ships `beam.combiners.Sample` for that. A 1 TB
`GroupByKey` OOMs; the same data through a `CombineFn` holding a 10-element
top-k heap runs on 4 workers.

### 17. What makes a `CombineFn` correct, and what happens when you get it wrong?

The merge must be **associative and commutative**: `merge(merge(a, b), c)` must
equal `merge(a, merge(b, c))`, and `merge(a, b)` must equal `merge(b, a)`.
Beam merges partial accumulators from different workers in an arbitrary order,
and the sharding differs between the Direct Runner and Dataflow.

When you get it wrong the symptom is a number that is *close* but not
identical, and that differs between runs. Float addition is the classic case:
adding the same values in a different order changes the last digit. The
production-safe pattern is to accumulate in integers (cents, not euros) and
divide once at `extract_output`.

**Failure story:** a revenue total reconciled against the source of truth for
six months, then failed a monthly audit by €0.02 — the classic
floating-point merge-order artefact. It only surfaced on Dataflow, because
the sharding differed from local.

### 18. Why is there no `beam.combiners.Sum`?

Because a sum needs no special machinery — Python's builtin `sum` is already
associative and commutative over numbers, and Beam can lift any such function
into a `CombineFn` for you. The combiners module ships only the operations
that need real logic: `Count`, `Mean`, `Min`, `Max`, `Sample`, `Distinct`,
`Top`, `Largest`, `Smallest`.

```python
import apache_beam as beam

beam.CombinePerKey(sum)
```

The key convention matters as much as the function: the values being summed
must be the numbers themselves, so key on the entity and put the amount in
the value. `beam.CombinePerKey(lambda kv: kv[1])` works but hides the
convention.

**Common misconception:** people reach for `beam.combiners.Sum` and get
`AttributeError: module 'apache_beam.transforms.combiners' has no attribute
'Sum'`. Beam has an internal sum combine function, but it is not part of the
public `combiners` surface in 2.77.

### 19. When is a side input the wrong tool?

Whenever the side input is big, frequently updated, or per-key. A side input is
**broadcast to every worker** at the start of the bundle; it is not keyed, not
shuffled, and not incrementally updated. It is a lookup table that fits in
memory everywhere.

| Side input size | Right tool |
|---|---|
| Fits in memory, static | `beam.pvalue.AsDict` / `AsIter` |
| Large, static | shuffle join via `CoGroupByKey` |
| Large, frequently updated | a real table (BigQuery) joined downstream |

**Failure story:** a product reference table with 4 million rows was loaded
as an `AsIter` side input. The job worked on 20 workers and OOMed on 200,
because 4 million rows were copied to each of 200 workers — 800 million rows
in RAM across the cluster. The fix was to `Flatten` the reference into the
main stream and `CoGroupByKey` it, or move the lookup to BigQuery.

### 20. What is `CoGroupByKey` for, and what is it not?

It is a **multi-way join on the key**, performed inside the runner. Feed it a
tuple of keyed PCollections and it emits `(key, {tag: [values], ...})` for
every key, including keys present in only some inputs — a full outer join.

It is **not** a general join: no equi-join on a non-key field, no inequality
predicates, no windowed-equality variant in the core SDK. Nor is it a
replacement for a database join when the join is a fraction of a large
dataset — shuffling both sides costs real money.

**Failure story:** a team replaced a BigQuery `JOIN` with `CoGroupByKey` and
the job got *slower*, because the join had been pushed down to BigQuery's
distributed execution and the Beam version had to move both tables through a
GCS shuffle. Use `CoGroupByKey` for small-to-medium keyed streams; let
BigQuery do the join when the tables are large and the join is not the point.

### 21. What is `Reshuffle` for, and when is it a mistake?

`Reshuffle` inserts a shuffle barrier: it redistributes elements across workers
and breaks fusion, so downstream work is spread evenly even when the upstream
distribution is uneven.

The mistake is using it as a generic "fix skew" button. It costs a full
shuffle — GCS writes, network, time — for a problem you might have fixed
upstream, and it can make a *non-associative* operation wrong by changing
order. It also does not fix true key skew: if one key holds 40% of the data,
reshuffling spreads that key's rows across workers, but they still all have
to be merged back to one key at the end.

**The correct fix for a hot key** is a hot key splitter: split the hot key into
N sub-keys before the aggregation and re-merge after. That keeps the result
exact. Use `Reshuffle` when the distribution is uneven but no single key
dominates, or when you need a fusion break.

---

## Windowing and streaming

### 22. What is a watermark, in one sentence?

A watermark is the runner's estimate of how far it has progressed through
the event-time timeline, and it is roughly **the minimum event timestamp
seen so far, minus the allowed lateness**.

Everything about late data follows from that definition. A window closes
when the watermark passes its end, not when wall-clock time passes its end —
so the *slowest* upstream source governs the pace of the entire pipeline. A
single lagging source stalls every downstream window.

**Failure story:** a job's output appeared in bursts 45 minutes apart while
the source was producing events continuously. The second input was a
database table polled every hour, and its oldest row was 50 minutes old, so
the watermark was pinned 50 minutes behind real time. The fix was to emit
the polled rows with the timestamp of the *poll*, not the timestamp of the
row's own modification time.

### 23. Why is `AfterWatermark` with non-zero allowed lateness an error?

Because Beam cannot prove the result is complete. `AfterWatermark` fires
when the watermark passes the window end; if allowed lateness is non-zero,
more data can still arrive for that window, so a fired result may be
superseded. Beam refuses the combination:

```text
ValueError: Unsafe trigger: AfterWatermark() may lose data. Reason: MAY_FINISH
```

This is a *correctness* guard, not an inconvenience. The exception is
`--allow_unsafe_triggers`, which tells Beam you accept the risk — and with
`ACCUMULATING` the late data is merged into the same output element, so
downstream consumers see the corrected value rather than a duplicate.

**The trade-off:** with allowed lateness you get corrected results but the
output for a window can be written more than once, so the sink must be
idempotent. Without it you get exactly one final result per window, and late
data is dropped.

### 24. What is the difference between `ACCUMULATING` and `DISCARDING`?

`ACCUMULATING` emits the running total for the window at every firing.
`DISCARDING` emits only the elements that arrived since the previous firing.

With `AfterCount(2)` over 5 elements, `ACCUMULATING` emits 2, 4, 5 and
`DISCARDING` emits 2, 2, 1. That is the whole difference, and it decides
whether your consumer can treat the output as a snapshot or as a delta.

**Failure story:** an alerting pipeline emitted per-window deltas, but the
consumer summed them against a table that was already cumulative. Every
alert double-counted. The pipeline was correct; the contract between
producer and consumer was not written down. Fix: pick one mode, state it in
the schema, and make the consumer match.

### 25. Fixed, sliding, or session windows — when does each one win?

`FixedWindows` are tumbling and non-overlapping — hourly rollups, daily
aggregates. `SlidingWindows` overlap — rolling averages, rate limits, "any
user active in the last 5 minutes". Session windows are gap-delimited — a
user session ends after 30 minutes of inactivity.

The trade-off is state and output volume. A sliding window of size W and
period P produces W/P outputs per period per key, and Beam keeps the state
for all overlapping windows of the active period. Session windows are the
most expensive of the three in state, because the window boundaries are
determined by the data, not by the clock — Beam has to keep a window open
until it can prove no more data will arrive for it.

**Common misconception:** `SlidingWindows(period=60, size=300)` does not
mean "5 one-minute buckets merged". It means 5 overlapping 5-minute windows
per minute, so the same element appears in 5 outputs.

### 26. Pub/Sub is at-least-once — how do you deduplicate, and what does the dedup key have to be?

You deduplicate on a key derived from the **payload's own identity**, never from
arrival time or a record offset. Pub/Sub's `message_id` is per-publish and is
not stable across redeliveries of the same logical event in every publish
pattern, so the business identifier (`event_id`, `order_id`) is the one to use.

The mechanism: keep a bounded set of recently-seen keys in `SetState` and skip
anything already present. The set must be time-bounded — a `SetState` that
grows forever is a memory leak, and a `GlobalWindows` set is unbounded by
construction.

**Failure story:** a dedup key built from `int(time.time())` deduplicated
nothing, because redelivery happens within milliseconds, not seconds, and
the key was recomputed on each attempt. Event counts ran 3–5% high under
Pub/Sub load, invisible until compared against a batch backfill.

### 27. Why is a plain attribute on a `DoFn` not durable state?

Because the `DoFn` instance is created per worker, per bundle, and
serialised between the driver and the worker. An attribute set in `process()`
dies with the bundle, and it is not restored when a bundle is replayed after
a failure.

Durable state in Beam is explicit: `StateSpec` types like `SetState`,
`BagState`, `CombiningValueState`, plus `TimerSpec`s. These are checkpointed
by the runner and are correctly restored on recovery. A `DoFn` attribute is
not.

**Failure story:** a dedup implementation used `self.seen = set()` on the
`DoFn`. On the Direct Runner it appeared to work — one process, one
instance. On Dataflow, each worker had its own partial set, and after a
worker restart the set was empty again, so the first 30 seconds of every
recovery re-counted every event. The fix was `SetState` with a timestamp
for expiry.

### 28. What are the stateful-DoFn APIs, and when should you reach for them?

`StateSpec` for per-key state (`SetState`, `BagState`, `CombiningValueState`,
`ValueState`) and `TimerSpec` for time-based callbacks (`Timer(time_domain,
key)`, `AfterProcessingTime`, `AfterWatermark`). The state is keyed by the
element's key, checkpointed by the runner, and restored on recovery.

Use them when the answer depends on *history for a key* — dedup, session
detection, a per-user counter, "wait 30 seconds of silence and then emit".
Do **not** use them for a plain aggregate: `CombinePerKey` is faster, simpler
and has no per-key bookkeeping overhead.

**The mechanism that makes it work:** the runner holds the state for the
active key, and the `Timer` fires in the context of that key, so you get
"on timer for key K, look at K's state".

### 29. How do you test streaming behaviour deterministically?

`TestStream`. It is a source you control: you decide exactly which elements
arrive, in what order, and at what timestamps, including the element that
arrives after its window has already fired. That makes late-data and
re-triggering behaviour reproducible.

The trap is the runner: the Prism `DirectRunner` panics on `AfterWatermark`
and on the `+inf` watermark evaluation, so `TestStream` tests need
`BundleBasedDirectRunner`. And windowed assertions need
`use_global_window=False`, which changes the element type to `WindowedValue`
— you must unwrap `.value` before comparing, or the assertion fails with a
confusing type error.

**Failure story:** a test that passed on a laptop and failed in CI was
running Prism. It was not a flake — it was a deterministic panic on a
feature the runner does not implement.

---

## Correctness and guarantees

### 30. Does Beam give you exactly-once semantics?

No — not end to end. Beam gives you **at-least-once** processing with
exactly-once *state* updates. The distinction is where the boundary is:
state lives inside Beam and is checkpointed, so a replayed bundle does not
double-apply a state update; anything written to an external system is
outside that boundary and can be duplicated.

The practical rule: make every sink idempotent. Write to a staging table and
`MERGE` into the target on a business key; use `CREATE_IF_NEEDED` plus a
`MERGE` in BigQuery, or write to a sink with a natural key and a
deduplicating merge. Sinks that are not idempotent — appending to a table
without a key — will drift, and the drift scales with job size and failure
rate.

### 31. What makes a Beam pipeline deterministic, and why does it matter?

Deterministic means: the same input produces the same output set regardless of
how the runner shards, schedules, retries or reorders the work. That requires
(a) a combiner whose merge is associative and commutative, (b) no dependence
on wall-clock time or worker-local randomness, and (c) a sink whose output
does not depend on the order of writes.

It matters because Dataflow is not a machine you can reproduce. Retry
boundaries, bundle boundaries and shuffle partitioning all differ on every
run. A pipeline that is only *nearly* deterministic passes in testing and
produces a different number every night.

**The pattern:** `beam.combiners.Sample` with a fixed seed rather than
`random.random()`; `datetime.now()` only for watermarks or metadata, never
for a business value; a `CombineFn` whose accumulator is a summary, not a
list.

### 32. How do you handle a poison pill — a record that cannot be parsed?

Route it to a **dead-letter queue** and keep the pipeline running. In Beam
that means a side output: `beam.ParDo(fn, side_outputs={"bad": "bad"})`, then
`FilterInto` to split the main output from the bad one. Write the bad branch
to a separate sink.

The alternative — raising inside `process()` — fails the bundle, and in
streaming that means the pipeline retries forever on the same message.
That is the classic poison-pill loop: a single malformed record pins the
watermark and every downstream window stops.

**The trade-off:** silently skipping is also wrong, because you have no
record of what you lost. The rule is: every record you drop must be
*counted and visible*. The course's own `ParseOrderFn` logs skipped rows —
which is the right behaviour for a course, and not enough for production,
where the DLQ is the point.

### 33. How do you make a pipeline survive a schema change in the input?

Treat the schema as an explicit contract, not an inference. Parse into a
versioned internal representation, and map unknown fields to a default rather
than crashing. With `ReadFromCsv` and `infer_schema=True`, Beam infers the
schema from a *sample* of the file, so a type change late in the file (a
status code that becomes `"007"` instead of `"7"`) is a runtime failure on a
worker, not a validation failure at submission.

The production pattern: pin the schema, validate against it, send mismatches
to the DLQ. If the schema must change, make it backwards compatible first
(new optional field), deploy, then start writing the field.

**Failure story:** a CSV column changed from an integer to a decimal string.
`infer_schema` sampled the first 1000 rows, got `INT64`, and the job died 4
minutes in on a single row — after 80% of the input had been paid for.

### 34. What is idempotency in the context of a Beam sink, and how do you get it?

Idempotency means: running the same write twice leaves the target in the same
state as running it once. Beam gives at-least-once delivery, so any sink that
appends is not idempotent — and neither is one that appends *and* deletes.

The mechanisms: in BigQuery, write to a staging table with a run-id partition
and `MERGE` into the target on a business key. In a file sink, write to a
*new* output prefix per run and treat the prefix, not the file, as the unit
of idempotency. In Pub/Sub, enable **ordering keys** so the same key is
delivered in order, and dedup on a monotonically increasing sequence number.

**The rule that saves the most time:** never make the sink's target the same
path across runs. Parameterise the output path with a run ID, and make the
*promotion* of that output the idempotent step.

### 35. How do you verify that a backfill produced the right numbers?

Backfill the same window twice into two different output paths and diff them.
A deterministic pipeline must produce byte-identical output (modulo the
shuffling of shards). If they differ, you have a non-deterministic
combiner, a wall-clock dependency, or an ordering assumption — and you have
found a bug that would have shown up as a nightly variance months later.

Then reconcile the total against the source of truth: row counts, sum of
amounts, and the count of records routed to the DLQ. Three numbers, always
the same three. And check the *disposition* count — if 100,000 rows went in
and 99,900 came out, the missing 100 are where your next incident starts.

---

## Dataflow operations and cost

### 36. What does Dataflow actually bill you for?

**vCPU-hour, not bytes.** A standard worker runs at roughly $0.05–0.10 per
vCPU-hour, with a separate per-GB charge for streaming data processing and
BigQuery billed separately for the writes and queries.

This is the mental model that changes decisions. Bytes are a *driver* of
cost, not the *unit* of it. A pipeline that processes the same 1 TB
differently can differ by 5× in cost, and the difference is usually in the
worker count and the shuffle, not the input size.

**The number that shocks people:** a streaming job left running over a
weekend at 100 workers costs 100 × 72 × $0.06 = **$432**, for a pipeline
that may have produced nothing useful. A 5,000-row batch job on one
`n1-standard-2` worker costs **under a cent**. Set a budget alert.

### 37. How does autoscaling work, and what is the actual cost of leaving it on?

Dataflow's `Basic` autoscaling targets a per-worker backlog and scales the
worker count between 1 and `--max_workers`. `Aggressive` scales faster and
more eagerly, trading spend for latency. Scaling up has a real cost: a new
worker must start, download dependencies, and get a shuffle partition, so
aggressive scaling on a spiky workload can spend more than it saves.

The real cost of leaving autoscaling on is that it scales to the *backlog*,
not to the *value*. A pipeline with a partition-key hot spot will autoscale
to 100 workers and leave 99 idle, waiting on the hot partition.

**Failure story:** a job on a small input spun up 100 workers in the first
few minutes — autoscaling reacting to startup latency, not throughput. At
$0.06/vCPU-hour that is $6 per run, every run, for a job that needed one
worker. The fix was `--num_workers=1 --autoscaling_algorithm=NONE` for the
small path.

### 38. Why is the SDK version in a template a production risk, and how do you mitigate it?

Because a classic Dataflow template bundles the SDK version installed when it
was built. You write code against Beam 2.77, but the template on the server
may be running 2.60, and the API surface differs — `beam.pvalue.AsSingleton`
was deprecated in favour of `AsDict`/`AsIter`, `AsSingleton` on an empty
PCollection now raises at *construction* time rather than run time, and other
behaviours have tightened.

Flex templates sidestep most of this: the template is a Python file in GCS
and the worker installs the SDK from your `requirements.txt` at run time, so
the version is pinned in source control rather than baked into a server-side
artefact.

**Mitigation, in order of preference:** (1) use flex templates and pin
`apache-beam` in `requirements.txt`; (2) if you must use a classic template,
rebuild it in CI on every SDK bump and smoke-test before promoting; (3) never
assume a deprecated API keeps working, and never assume a *new* API exists on
the server.

### 39. What is a flex template, and what is it not?

A flex template is a Python file uploaded to a GCS path, run by that path
with `--parameters` for its inputs. You can update the file and rerun
without rebuilding anything.

It is **not** a container image, **not** a compiled artefact, and **not**
self-contained: the worker installs your dependencies at run time, so the
run is not reproducible unless your requirements are pinned and your GCS
file is immutable per run. It is also not a different execution model — it
is the same Beam graph, launched with a different packaging.

**The practical difference that matters:** the classic template pins the SDK
at build time; the flex template pins it at run time from your requirements
file. That moves the "which version is running?" question from "what did we
publish six months ago?" to "what is in git right now?".

### 40. What is the standard triage order when a Dataflow job fails?

Work down the stack, cheapest check first:

1. **`gcloud dataflow jobs describe JOB_ID --format='value(status.errorMessage)'`** —
   the top-level error. Most failures are here.
2. **The job graph** — `gcloud dataflow jobs graph show JOB_ID`. Which stage
   failed: the read, the shuffle, or the write?
3. **Worker logs** — `gcloud logging read "resource.type=cloud_dataflow_job
   AND resource.labels.job_id=JOB_ID"`. The user code exception lives here,
   not in the job status.
4. **Metrics** — `gcloud dataflow jobs describe JOB_ID --format='value(metrics)'`.
   `estimatedProgress` stuck at 0 with work committed means a stuck worker,
   not a slow one.

**Most common causes, in order:** a 403 on `storage.objects.get` (the Dataflow
service agent is missing `roles/storage.objectAdmin` — and if you added the
role *after* the agent was created, you must remove and re-add it for the
policy to take effect), a missing API enablement, a staging-location
collision between concurrent jobs, and an OOM in a `GroupByKey`.

### 41. How do you stop a streaming job, and what happens if you forget to?

`gcloud dataflow jobs cancel JOB_ID`. The job moves to `Cancelled` and its workers
are reclaimed. There is no "update in place" — applying a code change means
cancelling and relaunching, which is why the state and exactly-once story
matter: the new job starts from a new checkpoint and reprocesses from the
source's retention point unless you set an explicit offset or timestamp.

**The forgotten-job failure story:** a streaming job was left running after a
demo. It consumed ~$0.06/vCPU-hour on 40 workers for 3 weeks — roughly
**$1,200** — producing rows nobody read. Guard rails: budget alerts at 50%
and 90%, a nightly check for streaming jobs older than 24 hours that are not
on an allowlist, and a hard `--max_workers` on every streaming job so a
scale-up bug cannot become a five-figure bill.

### 42. How do you detect and fix skew?

Skew is when one key carries a disproportionate share of the work. The symptom
is specific: the job is not slow overall, it is *one worker* at 100% CPU while
the rest idle, and the stage shows high `MaxBundleDuration` alongside low
`bundleProcessedCount` on the others.

The fixes, cheapest first:

1. **Filter or pre-aggregate upstream** so the hot key never reaches the
   shuffle. Free, and the right first move.
2. **`Reshuffle`** when the distribution is uneven but no single key dominates.
3. **A hot key splitter** when one key dominates and the answer must be
   exact: split the key into N sub-keys before the aggregation, re-merge after.

**The number:** a 1% key holding 30% of the rows puts 30% of the shuffle on
one worker. On a 30-minute job that is roughly 9 minutes of tail latency, and
the job cannot finish until that one worker does.

---

## Design and trade-offs

### 43. When should you do the join in Beam and when should you do it in BigQuery?

Do it in BigQuery when the join is between two large tables, the join key is
not the pipeline's grouping key, and the join is not the point of the
pipeline — BigQuery's distributed execution is faster and cheaper than moving
both tables through a GCS shuffle. Do it in Beam when the join involves a
stream, must happen inside a window, or when the joined result *is* the
pipeline's output.

The mechanism behind the cost difference: a Beam join is a shuffle — both
sides are written to GCS, partitioned, and read back. A BigQuery join is also
a shuffle, but BigQuery already holds the data in that form and charges for
bytes scanned rather than for a pipeline stage.

**Failure story:** a team moved a 2 TB `JOIN` from BigQuery into Beam with
`CoGroupByKey` because "we already have a Beam pipeline". The job cost $180
in shuffle traffic and 40 minutes, versus $35 and 3 minutes for the BigQuery
query. "We are already in Beam" is not a reason to move a join.

### 44. What is the real cost of `GroupByKey`, and when is it genuinely justified?

`GroupByKey` materialises every element of every group in memory on one worker.
Memory is O(largest group), and the largest group is a function of your
*worst* key, not your average. A `GroupByKey` over 1 TB with a top-heavy
distribution fails long before the average group size is a problem.

It is justified when the answer genuinely requires the whole group and cannot
be summarised: an exact median, a percentile, a sort, a "top 10 by a score
that is not a simple max". Even some of these have a scalable answer —
`beam.combiners.Sample` gives an approximate percentile, and a bounded top-k
heap inside a `CombineFn` gives an exact top 10 by any comparable score at
O(k) memory per key.

**The tell that you should have used a `CombineFn`:** your `GroupByKey` is
followed by a `Map` that reduces the list to a single value. If the reduction
is associative, it belongs in the combiner.

### 45. How do you choose between a `ParDo` that aggregates and a `CombinePerKey`?

Use `CombinePerKey` whenever the aggregation is per-key and expressible as
a mergeable summary. It fuses the aggregation into the shuffle's *write* phase,
so partial results are combined **before** the data crosses the network —
that is where the saving comes from. A `ParDo` that aggregates runs *after*
the shuffle, so every element crosses the network individually.

The trade-off: `CombinePerKey` requires a mergeable accumulator and cannot
emit more than one element per key per window. If you need per-key *and*
per-value outputs, or a non-mergeable reduction, use a `ParDo` after the
`GroupByKey`.

**Failure story:** a pipeline used `beam.Map` to build a dict per key, then
`CombinePerKey` to merge the dicts. The merge was correct, but the dicts were
already materialised in memory before the shuffle — the exact cost
`CombinePerKey` is meant to avoid. The fix: make the accumulator the dict
itself and let `add_input` mutate it in place.

### 46. What is a bundle-size problem, and how do you tell it apart from a shuffle problem?

A bundle-size problem shows up as high `bundleProcessedDuration` with
`bundleSize` near the limit and most time spent processing elements rather
than waiting. A shuffle problem shows up as a wide stage with a long
"waiting for data" and the bottleneck labelled in the job graph as the
`GroupByKey`/`CombinePerKey` step.

The mechanism: bundle size caps how much state a worker holds per key. Too
small and you pay per-bundle overhead thousands of times; too large and one
worker holds too much and the OOM killer gets you. The Python SDK default is
128 elements; Dataflow manages this for you and you rarely touch it.

**The practical rule:** before you tune bundle size, look at the job graph.
Almost every "the pipeline is slow" report is a shuffle or skew problem, and
tuning bundle size is a distraction from both.

### 47. How do you make a pipeline testable without a cluster?

Three layers, and each catches a different class of bug:

1. **Pure functions.** Put the business logic in ordinary Python functions
   with no Beam imports, and unit-test them. Highest-value layer: most of a
   pipeline's logic lives here, and it runs in milliseconds with no Beam
   installed.
2. **`TestPipeline` with `assert_that`.** The modern API; `PTest` is
   deprecated. This tests the *graph* — wiring, labels, transforms — on the
   Direct Runner.
3. **`TestStream`.** For streaming semantics, the only way to test late data
   and re-triggering deterministically.

**The failure story:** a team tested only end-to-end. A bug in the currency
conversion was caught by a staging environment three weeks later, after the
pipeline had been re-run over 30 days of backfill. The pure-function layer
would have caught it in under a second.

### 48. What do you do when a job produces zero rows?

Check the filter first — it is the cause roughly 80% of the time. Beam does
not error on an empty PCollection; it just produces nothing, and the job
succeeds in 4 seconds with a green checkmark.

The order that finds it fastest: (1) count the input, (2) count after each
`Filter`, (3) count after the `CombinePerKey`. Put the counts in as
`beam.combiners.Count.PerKey()` stages feeding a sink you actually read. Zero
after the first filter means the filter is wrong; zero at the source means
the path is wrong.

**The production failure story:** a nightly job wrote to a BigQuery table with
`WRITE_TRUNCATE` and the filter excluded every row because a schema change
renamed a status value. The job succeeded, the table was truncated, and the
previous night's data was gone. The `WRITE_TRUNCATE`-with-no-count-check is
the real bug. Use `WRITE_APPEND` to a partition, and assert the row count.

### 49. How do you handle late data when the late data is a design decision rather than a bug?

Decide explicitly whether you want *corrected* results, *updated* results, or
*approximate but fast* results, and write that decision into the schema. With
`allowed_lateness` and `ACCUMULATING`, late data produces an updated output for
a window that was already written — so the sink must accept corrections, and
downstream consumers must be able to tell a correction from a new value. With
`DISCARDING` and no lateness, late data is silently dropped: a legitimate
choice for an approximate dashboard, but only if you say so.

**The failure story:** a "revenue per hour" table was written with
`WRITE_APPEND` to a table with no version column. Late data produced a second
row for the same hour, and the dashboard summed both. The fix was a version or
`event_ts`-keyed `MERGE` so the last correction wins.

### 50. What is the single most common mistake in a Beam interview answer?

Answering with the *name* of a transform instead of the *mechanism* and the
*cost*. "Use `CombinePerKey`" is a non-answer. "`CombinePerKey` keeps one
accumulator per key and merges partials during the shuffle, so memory is
O(keys) not O(data) — which is why the job that OOMs on `GroupByKey` at 1 TB
runs on four workers" is an answer: mechanism, number, boundary condition.

The second most common is claiming a guarantee Beam does not make — "exactly
once" is the trap. Beam gives at-least-once delivery with exactly-once state;
sinks must be idempotent. The third is treating "portable" as "the same flags
work everywhere": the *graph* is portable, the *configuration* is not.

**Why this matters:** a senior interviewer is not checking whether you know
the API. They are checking whether you can predict what your code will do at
100× the data volume, on a runner you do not control, when something fails at
3 a.m. Every answer here is structured to give that signal: the mechanism, the
trade-off, the failure, the number.

---

## Where to go next

- The full module-by-module bank lives alongside this file — start with
  [README.md](README.md) for the study plan and the question index.
- For the foundational reading behind questions 1–13, see
  [01-what-is-apache-beam.md](../chapters/01-what-is-apache-beam.md).
- The one-page reference for transforms, triggers and flags is
  [CHEATSHEET.md](../resources/CHEATSHEET.md).
