# Dataflow & Beam Glossary

> Every term used in this course, defined.

---

## A

**Accumulation mode** — Controls what a windowed aggregation emits when a
trigger fires. `DISCARDING` emits only what arrived since the last firing
(a delta); `ACCUMULATING` emits the running total for the window.

**AfterCount** — A trigger that fires once a window has seen `n` elements.
Fast and predictable, but Beam cannot prove it is safe, because an
element can still arrive after the last firing. Requires
`--allow_unsafe_triggers`.

**AfterProcessingTime** — A trigger that fires a fixed duration after
processing time first observes a window. Never fires for data that
arrives after the window is closed. Requires `--allow_unsafe_triggers`.

**AfterWatermark** — A trigger that fires when the watermark advances past
the end of the window. Only safe with **zero allowed lateness**; with
lateness, Beam raises `ValueError: Unsafe trigger`.

**Allowed lateness** — How long after a window's end the pipeline will
still accept elements for that window. Every second of lateness is a
second of extra state the runner must retain.

**Apache Beam** — An open-source SDK for defining batch and streaming
data pipelines with one API. Runs on Dataflow, Flink, Spark, Samza, and
locally.

**Autoscale** — Dataflow's scaling algorithm. `Basic` scales on CPU
utilisation; `Aggressive` scales on a linear approximation of backlog and
memory, and reaches the worker limit faster.

**Avro** — A row-oriented, schema-based file format and a Beam coder.
Beam can read and write `.avro` natively, and it is the format to reach
for when the schema must be enforced on the wire.

---

## B

**Backfill** — Re-processing a historical time range through a pipeline
that is normally incremental. In streaming, a backfill is usually a
bounded run over archived data with the event timestamps preserved.

**Batch pipeline** — A pipeline over a **bounded** input: it knows the
full extent of the data up front, and it terminates. A batch job's output
is complete when the job succeeds.

**Beam SQL** — A SQL-like interface over PCollections, built on the
DataFrames API. It is expressive but has a narrower feature set than the
Python SDK.

**BigQuery** — Google's serverless data warehouse. Beam writes to it with
`WriteToBigQuery`, and can read from it with the BigQuery source.

**Bundle** — The unit of work a Beam runner processes. A bundle is a
batch of elements, and it is the boundary at which state is checkpointed
in a streaming pipeline.

**BundleBasedDirectRunner** — The classic, pure-Python in-process runner.
It supports the full trigger and windowing feature set, and is the
course's default because it is the runner that behaves like Dataflow.

---

## C

**Coder** — The serialiser Beam uses to move elements between workers.
Beam picks one from the type hints; without them it falls back to
`FastPrimitivesCoder` and guesses at runtime.

**Checkpointing** — The runner periodically persisting pipeline state so a
failed job can resume. Dataflow checkpoints streaming jobs roughly every
5 minutes; a resumed job replays from the last checkpoint, so the sink
must be idempotent.

**CoGroupByKey** — Merges N keyed PCollections into one PCollection of
`(key, {tag: iterable})` tuples. The Beam equivalent of a `FULL OUTER
JOIN` on the key.

**CombineFn** — The four-method interface for a scalable aggregation:
`create_accumulator`, `add_input`, `merge_accumulators`, `extract_output`.
The accumulator must be a small, mergeable summary — not the full list.

**Combiner** — A `CombineFn` shipped with Beam, e.g.
`beam.combiners.Count.PerKey()`.

**Composite** — A transform built from other transforms. Composite
transforms are how you make a pipeline readable: `beam.CombinePerKey(sum)`
is a composite, not a primitive.

**Coder inference** — Beam choosing a coder from the type hints on your
function. This is why the type hints matter: they turn a runtime
`TypeError` on a worker into a construction-time error on your laptop.

---

## D

**Dataflow** — Google's managed runner for Beam pipelines. Handles
scheduling, autoscaling, checkpointing and state management.

**Dataflow service agent** — The Google-managed identity that creates
workers and accesses GCS on the pipeline's behalf. It is separate from
both your account and the worker service account.

**Dataflow template** — A pre-built, parameterised pipeline. There are two
kinds: **classic templates** (Java or Python classes packaged as a JAR or
a wheel, invoked by a fully-qualified class name) and **flex templates**
(a Python file uploaded to GCS, invoked by its GCS path).

**DirectRunner** — A local runner. In Beam 2.60+ the bare name `DirectRunner`
refers to the new Go-based **Prism** runner, which is faster but does not
yet support every trigger and windowing combination.

**DLQ** — Dead-letter queue. A sink for elements that could not be
processed, so that one bad record does not fail the whole pipeline.

**Durability** — The guarantee that a pipeline's state survives worker
rescheduling. On Dataflow, state is checkpointed and restored on failure.

---

## E

**Element** — A single item in a PCollection. Its type is determined by
the coder.

**Exactly-once** — A processing guarantee where each element is processed
exactly one time. Beam's Dataflow runner offers at-least-once by default
for streaming; exactly-once is achieved with idempotent sinks or
checkpointing.

**Encoder** — A Beam-specific concept for a coder that does not have a
natural schema, e.g. a `Row` or a proto. Distinct from a coder: a coder
knows how to serialise a Python type; an encoder handles types that the
coder infrastructure cannot represent directly.

---

## F

**FixedWindows** — Tumbling, non-overlapping windows of a fixed duration.
`FixedWindows(60)` gives one window per minute, aligned to the epoch.

**FlatMap** — A transform that expands one element into zero or more
elements.

**Flatten** — Merges multiple PCollections of the same type into one.

**Fusion** — The runner's optimisation that chains compatible transforms
into a single step, avoiding an intermediate serialisation. Fusion does
not cross a `GroupByKey`, a side input, or a `Reshuffle`.

---

## G

**Global window** — The single unbounded window that contains all
elements. `GroupByKey` without a `WindowInto` uses it.

**GroupByKey** — Groups the elements of a keyed PCollection by key. It
materialises every group in memory, which makes it the transform most
likely to exhaust a worker. Prefer `CombinePerKey`.

**GCS** — Google Cloud Storage. Beam reads and writes it with
`ReadFromText`, `WriteToText`, and the Avro/Parquet/JSON variants.

---

## H

**Hot key** — A key with a disproportionate share of the data. Hot keys
cause skew: one worker does most of the work while the rest wait.

**Hot key splitter** — A transform that splits a hot key's elements
across multiple sub-keys before the shuffle, then re-merges them after.
Beam has no built-in one — you write it.

---

## I

**Idempotency** — The property that re-processing the same input produces
the same output and does not corrupt state. Essential for at-least-once
delivery.

**Immutable** — A PCollection's contents never change after creation.
Downstream transforms derive new PCollections from it.

**Instance** — The Python object a `DoFn` is attached to. It is
**serialised to the workers**, so it must be picklable and must not hold
open file handles or network connections.

---

## J

**Java SDK** — The original Beam SDK. It is the most performant, and it
is what the classic Dataflow templates are written in.

---

## K

**Keyed PCollection** — A PCollection of `(key, value)` tuples. The output
of a `GroupByKey`, `CombinePerKey` or `CoGroupByKey` is keyed, and the
input to a `ParDo` over a keyed collection is keyed.

---

## L

**Lateness** — Data that arrives after the window it belongs to has
already closed. See *allowed lateness*.

**Local runner** — A runner that executes in the current process. It needs
no credentials and no network, and it is what the course uses for
everything that does not need Dataflow specifically.

---

## M

**Merge window** — A window that overlaps two adjacent windows, used to
merge results that a late element causes to be recomputed.

**MIME type** — The content type a `WriteToText`/text source uses, e.g.
`text/csv` or `application/json`. Beam does not infer the file format
from it; it is metadata for downstream consumers.

**Monotonicity** — The requirement that a PCollection's elements have
non-decreasing timestamps. `Reshuffle` breaks it deliberately so that
skewed keys get re-distributed.

---

## N

**Never trigger** — A trigger that never fires on its own; the window
result is emitted only when the pipeline ends. It is always safe.

**Nondeterminism** — The same input producing different output on
different runs. In Beam it usually comes from a non-associative
combiner, or from an operation that depends on the order elements
arrive.

---

## O

**Output PCollection** — The PCollection a transform produces. Every
transform has one, even when you discard it.

**Output coder** — The coder used to serialise the output. You can force
one with `.with_output_coder(...)`.

---

## P

**Pane** — One firing of a windowed trigger. `PaneInfo` describes it:
`index`, `n`, `nonspeculative_index`, `is_first`, `is_last`.

**PaneInfo** — The object passed to a `DoFn` via `PaneInfoParam`,
describing the current firing.

**PCollection** — A distributed collection of elements of a given type.
The core data abstraction of Beam. Immutable, and lazily computed.

**PipelineOptions** — The configuration object for a pipeline, built from
command-line flags. It has subclasses (`StandardOptions`, `TypeOptions`,
`DataflowOptions`) for different flag groups.

**Portability** — The property that a Beam pipeline can run on multiple
runners. Full portability requires avoiding runner-specific transforms
and sticking to the common API surface.

**PTransform** — A transform from one PCollection to another. The
"verb" of the Beam API.

**Pub/Sub** — Google's messaging service. The standard source for
streaming Beam pipelines.

---

## R

**RecordAccumulator** — A `DoFn` that accumulates elements in
`add_input` and emits them in `flush` at the end of the bundle. The
Beam-sanctioned way to hold state across elements in a bundle.

**Reshuffle** — A transform that applies a GroupByKey internally to force
a shuffle, breaking fusion and redistributing hot keys. It has no output
semantics — the elements are the same, only their distribution changes.

**Runner** — The backend that executes a Beam pipeline: Direct,
Dataflow, Flink, Spark, or Samza. A runner is chosen with `--runner`.

---

## S

**Sampler** — A `DoFn` that can sample a subset of elements, used to
approximate expensive aggregations.

**SessionWindows** — Windows delimited by a gap in the data. A new window
starts when an element arrives more than `gap` after the previous one.
The standard way to model user sessions.

**Side input** — A small PCollection made available to every worker as
part of a transform's input. Beam broadcasts it; it must fit in memory
everywhere.

**Sink** — A transform that writes elements out: `WriteToText`,
`WriteToBigQuery`, `WriteToAvro`, `WriteToParquet`.

**Skew** — Uneven distribution of work across workers, caused by hot
keys. See *hot key*.

**SlidingWindows** — Overlapping windows: `SlidingWindows(size, period)`
produces a new window every `period` seconds, each covering `size`
seconds.

**Source** — A transform that reads elements in: `ReadFromText`,
`ReadFromPubSub`, `ReadFromBigQuery`.

**Stateful DoFn** — A `DoFn` that keeps state across bundles, using
`@beam.DoFn.StateParam` and `@beam.DoFn.TimerParam`. State is
checkpointed by the runner.

**Streaming pipeline** — A pipeline over an **unbounded** input. It runs
indefinitely, processing elements as they arrive.

**Struct** — A deprecated Beam type for a typed record, replaced by
`NamedTuple` and `dataclass` with type hints.

**System latency** — The delay between the watermark advancing and the
runner acting on it — for example, the gap between a window closing and
its output being written.

---

## T

**Timestamp** — The event time of an element. Beam tracks a timestamp per
element, and windows are defined over timestamps, not wall-clock time.

**TimestampedValue** — A value with an explicit timestamp, produced with
`beam.window.TimestampedValue(value, timestamp=...)`. This is how you
re-stamp an element to control which window it lands in.

**Trigger** — The rule that decides when a windowed aggregation emits its
result.

**TypeOptions** — The `PipelineOptions` subclass holding `--type_check`
and `--allow_unsafe_triggers`.

---

## U

**Unbounded** — An input with no known end. Streaming sources are
unbounded; a Pub/Sub subscription is unbounded.

---

## V

**VoidPCollection** — A PCollection with no elements, used as the output
of a transform whose real output goes to a side effect.

---

## W

**Watermark** — Beam's estimate of how far through the event-time
timeline the pipeline has processed. The watermark is the minimum of the
timestamps seen so far, minus the allowed lateness. It is what lets the
runner know a window is "done".

**Worker** — One machine executing part of a pipeline. On Dataflow, a
worker is a Compute Engine VM running the Beam SDK.

**Window** — A bounded interval of event time. A windowed transform groups
elements by the window they fall into.

**WindowInto** — The transform that assigns elements to windows. Always
followed by a windowed aggregation (`GroupByKey`, `CombinePerKey`).

---

## X

**Xlang** — The cross-language Beam API. Not covered in this course; it
matters when a pipeline mixes Java and Python transforms.

---

## Y

**YAML** — The configuration format for Dataflow job templates and the
`gcloud dataflow jobs run` YAML form.

---

## Z

**Zoom lens** — A programming technique where one pipeline is written once
and run at multiple granularities — a "day view", a "month view" and a
"year view" over the same data, differing only in window size.

**Zombie** — A Dataflow streaming job whose workers are running but which
has no consumer — typically because a sink is failing silently.
