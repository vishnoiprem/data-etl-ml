# 1.4 — Batch vs Streaming & the Model
> **Section 1 · Beam Fundamentals & Model · Lecture 1.4 · 6:30**

## 🎯 What you will learn

- Bounded vs unbounded PCollections, and what the runner does with each
- The watermark as the unifying abstraction, and why batch is `+inf`
- Event time vs processing time, and why windowing is defined on event time
- The four delivery guarantees, and which one Beam and Dataflow actually give you
- Why **idempotency** matters more than the delivery guarantee
- Stateful processing: the three ways to get it in Beam
- Where "the same code runs in both modes" is true, and where it is a lie

---

## 🧠 Concept

### Bounded and unbounded PCollections

A **PCollection** is a description of a dataset. The single most important
property of a particular PCollection is whether it is **bounded** or
**unbounded**.

| | Bounded | Unbounded |
|---|---|---|
| Size | known, finite | unknown, potentially infinite |
| Example | a file, a BigQuery table, a `beam.Create` list | a Pub/Sub topic, a Kafka partition, a live API feed |
| End of input | definite | never (until you stop it) |
| When is the result final? | when the job finishes | never — results keep being refined |
| Runner behaviour | read everything, then advance the watermark to `+inf` | keep reading, advancing the watermark as it goes |

The runner learns the boundedness of a PCollection from the *source*
transform. `ReadFromText` produces a bounded PCollection. `ReadFromPubSub`
produces an unbounded one. This is not a hint you set; it is a property of
the transform, and it determines the entire downstream execution model.

This is also why a *file* is a perfectly good streaming source for testing.
The course's `streaming_pipeline.py` reads a bounded NDJSON file and applies
all the streaming transforms. The pipeline is a finite job that exercises
every streaming code path — the windows, the triggers, the watermark — with
none of the operational risk of a live topic.

### The watermark: the unifying abstraction

The **watermark** is Beam's estimate of how far in *event time* the input
has progressed. It is the single mechanism that unifies batch and
streaming.

```text
  Event time:  ─────────────────────────────────────────────▶
                  e1    e2      e3        e4        e5
                  |     |       |         |         |
  Watermark:  ─────────────────────────────────────────────▶
                    ▲
                    └── "I have seen everything up to here, and will
                         never see anything earlier than this."
```

The watermark is a *promise about the past*, not a prediction about the
future. When the watermark passes a point, Beam knows that no further
element with a timestamp at or before that point will arrive. That is what
makes it safe to close a window.

**The unifying claim:**

```text
  A BATCH pipeline is a STREAMING pipeline whose input ends.

  When a bounded input is exhausted, the runner advances the watermark
  to +infinity. Every window closes. Every trigger fires. The job ends.
```

This is not a metaphor, and it is not a simplification. It is literally
what the runner does. A batch pipeline and a streaming pipeline running
the same transforms produce the same output; the batch one just arrives
all at once.

Consider a fixed window of one hour with an `AfterWatermark` trigger:

| | Batch | Streaming |
|---|---|---|
| When the window closes | at the end of the job, when the watermark hits `+inf` | when the watermark passes the window's end, in real time |
| How many times the window fires | once | once (or more, with accumulating triggers) |
| When is the result final? | at job completion | at watermark advance, but subject to allowed lateness |

The batch job is not doing anything special. It is doing the same thing,
just with the watermark jumping straight to the end.

### Event time vs processing time

Two clocks, and the difference is the source of most streaming bugs.

**Processing time** is the wall clock of the machine executing the
transform. It is reliable, monotonic, and completely disconnected from
when the event actually happened.

**Event time** is the timestamp carried *in the data* — when the click
happened, when the order was placed, when the sensor sampled.

Consider a pipeline that counts events per minute:

```text
  Event time    Processing time
  ──────────    ───────────────
     e1 (10:00)     arrives 10:00:02
     e2 (10:00)     arrives 10:00:05
     e3 (10:01)     arrives 10:01:01   <- out of order
     e4 (10:00)     arrives 10:01:30   <- LATE, belongs to the 10:00 window
```

- **Processing-time windowing** puts e4 in the 10:01 window, because that
  is when it arrived. The 10:00 window's count is wrong.
- **Event-time windowing** puts e4 in the 10:00 window, because that is
  when it happened. The count is right — *if* the watermark has not yet
  passed 10:01.

This is why **Beam defines windowing on event time**. The alternative —
windowing on arrival time — is not wrong, it is *a different question*.
Sometimes you genuinely want the arrival-time question ("how many
requests hit the server per minute"), and Beam supports it: you can
window on processing time. But for anything that describes *what happened
in the world*, event time is the only correct choice.

Beam's default for a source that carries timestamps is event time. For
`ReadFromText`, every element gets the timestamp of the file's
modification, unless you override it.

### The four delivery guarantees

Every message-delivery system offers a set of guarantees about what
happens when things fail. There are exactly four, and they form a strict
hierarchy.

| Guarantee | What it means | When it breaks |
|---|---|---|
| **At-most-once** | an element is delivered zero or one time. **No duplicates, but data can be lost.** | the consumer crashes after processing but before acknowledging |
| **At-least-once** | an element is delivered one or more times. **No data loss, but duplicates are possible.** | the consumer crashes after acknowledging but before the source knows |
| **Exactly-once** | each element is delivered exactly once, with side effects committed atomically with the processing | requires transactional sinks and a protocol that ties the two together |
| **None** | the system makes no promise at all | — |

**What Beam and Dataflow actually give you:**

| Scenario | Guarantee | Notes |
|---|---|---|
| Batch on Dataflow, output to BigQuery | **exactly-once** | a batch job is atomic per write; a failed job writes nothing |
| Batch on Dataflow, output to GCS | **exactly-once** | output files are written once, then committed |
| Batch on Dataflow, output to an external system | **at-least-once** | unless the sink is transactional |
| Streaming on Dataflow, output to BigQuery | **exactly-once** | Dataflow's checkpointing plus BigQuery's streaming insert idempotency |
| Streaming on Dataflow, output to Pub/Sub | **at-least-once** | Pub/Sub itself is at-least-once; Dataflow cannot make it otherwise |
| Streaming on Dataflow, output to GCS | **at-least-once** | file windows may be written more than once on retry |
| Streaming on Dataflow, output to an external HTTP API | **at-least-once** | unless the API is idempotent and you key your calls |
| Spark (batch or streaming) | **at-least-once** | Spark's exactly-once claim applies to its own sinks, not arbitrary ones |
| Flink | **exactly-once** | for stateful operators and transactional sinks |
| The direct runners | **at-least-once** at best; the bundle-based runner is effectively "none" across a crash | no checkpointing |

Two things to be precise about:

**Exactly-once is a property of the *sink*, not the pipeline.** Dataflow
gives you exactly-once *into BigQuery* because BigQuery's write is
transactional and Beam can attach a deduplication id. Beam cannot give
you exactly-once into a random third-party HTTP endpoint, because there is
no way to make the HTTP call and the checkpoint atomic. The `use_at_least_once`
flag on `WriteToBigQuery` exists precisely to let you *opt out* of
Dataflow's deduplication when you would rather have maximum throughput.

**Exactly-once in streaming has a latency cost.** It requires the runner to
checkpoint and to deduplicate on replay. That is a real cost — in
throughput, in latency, and in state size. Some pipelines are better off
with at-least-once plus idempotent sinks.

### Idempotency: the guarantee that actually matters

Here is the practical argument, and it is the one that should shape your
design.

A delivery guarantee is a property of the *system*. Idempotency is a
property of *your code*. And your code is the part you control, and the
part you can reason about.

**Idempotent** means: applying the same operation to the same input twice
produces the same result as applying it once.

```python
import apache_beam as beam


def set_revenue_billing_table():
    """Write a billing table that can be written many times.

    The sink is keyed by region, and the write is an upsert. Replaying the
    whole pipeline produces the same table — the operation is idempotent.
    """
    pass


# Idempotent: writing "region=EMEA, revenue=100" twice leaves the same
# single row. The key is derived from the data, not from arrival order.
rows = [("EMEA", 100.0), ("AMER", 250.0)]

# Not idempotent: appending a row to a list. Replay duplicates the row.
ledger = []
for region, revenue in rows:
    ledger.append((region, revenue))
```

The rule of thumb:

> **Design every sink to be idempotent, and then the delivery guarantee
> stops mattering.**

If your sink is idempotent, at-least-once delivery costs you a little
extra compute on retry and nothing else. If your sink is not idempotent,
exactly-once delivery is the only thing standing between you and a
duplicated ledger — and exactly-once is not always available.

In Beam specifically, the way to make a sink idempotent is to **carry a
deterministic key in the data**, derived from the event's own identity,
never from arrival time:

```python
import apache_beam as beam
from apache_beam.coders import VarIntCoder
from apache_beam.transforms import userstate


class DeduplicateEvents(beam.DoFn):
    """Drop events already seen, using the event's own id as the key.

    `beam.DoFn.StateParam` takes a *StateSpec* object, not a string. The
    spec is declared as a class attribute so the SDK can build the
    per-key state it needs.
    """

    SEEN = userstate.SetStateSpec("seen", VarIntCoder())

    def process(self, event, seen=beam.DoFn.StateParam(SEEN)):
        event_id = event["event_id"]
        if event_id in seen.read():
            return
        seen.add(event_id)
        yield event
```

The course's `transforms.dedup_key` function exists for exactly this
reason, and its docstring says the important thing out loud: the key must
be derived from the payload's own identity, **never from arrival time**.

There is a subtlety worth stating: true exactly-once deduplication needs
*stateful* processing, and stateful processing in Beam is only fully
supported in streaming mode. In batch, you would need to either sort by
the dedup key or use a stateful `DoFn` with a keyed state — which works
but is more machinery than re-reading a sorted input.

### Stateful processing

State is where a Beam pipeline remembers things between elements. There are
three levels, and they are not interchangeable.

**Level 1 — no state.** A `Map` or `Filter` is stateless: each element is
processed independently. This is the default, and you should stay here as
long as possible. Stateless steps fuse, scale linearly, and never need a
checkpoint.

**Level 2 — keyed, group-scoped state.** `GroupByKey` and `CombinePerKey`
introduce state implicitly: the runner buffers all elements for a key
before producing output. This is the state you get for free, and it is
scoped to a `(key, window)` pair.

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create([("a", 1), ("b", 2), ("a", 3)])
        | "Sum" >> beam.CombinePerKey(sum)
        | "Sink" >> beam.Map(print)
    )
```

The runner must buffer the two `"a"` elements before it can emit their
sum. That buffer is state, and it is bounded by the key cardinality. A
single hot key with ten million elements will exhaust a worker's heap.
This is the single most common cause of an out-of-memory failure in a
Beam streaming pipeline.

**Level 3 — explicit user state.** `beam.DoFn` can declare its own state
specs and timers. This is the most powerful and least portable option.

```python
import apache_beam as beam
from apache_beam.coders import FloatCoder, VarIntCoder
from apache_beam.transforms import userstate


class CountSinceLastSeen(beam.DoFn):
    """Count events per user, resetting after a gap in activity."""

    COUNT = userstate.BagStateSpec("count", VarIntCoder())
    SEEN_AT = userstate.ReadModifyWriteStateSpec("seen_at", FloatCoder())
    FLUSH = userstate.TimerSpec("flush", userstate.TimeDomain.WATERMARK)

    def process(self, item, count=beam.DoFn.StateParam(COUNT),
                seen_at=beam.DoFn.StateParam(SEEN_AT),
                timer=beam.DoFn.TimerParam(FLUSH)):
        # A stateful DoFn receives the whole (key, value) pair.
        key, event = item
        previous = seen_at.read() or 0
        if previous and event["ts"] - previous > 300:
            yield (event["user_id"], len(count.read()))
            count.clear()
        count.add(1)
        seen_at.write(event["ts"])

    @userstate.on_timer(FLUSH)
    def flush(self, count=beam.DoFn.StateParam(COUNT),
              timer=beam.DoFn.TimerParam(FLUSH)):
        """Fire the accumulated count when the timer expires.

        Every declared `TimerSpec` needs a matching callback, registered
        with the `@userstate.on_timer(TIMER_SPEC)` decorator. Without it,
        Beam raises `ValueError: DoFn ... has a TimerSpec without an
        associated on_timer callback`.
        """
        if count.read():
            yield (None, len(count.read()))
            count.clear()


with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create([("u1", {"user_id": "u1", "ts": 1})])
        | "Count" >> beam.ParDo(CountSinceLastSeen())
        | "Sink" >> beam.Map(print)
    )
```

A stateful `DoFn` is applied to a **keyed** PCollection — the runner
needs the key to know which state cell to read and write. Passing an
unkeyed PCollection raises:

```text
ValueError: Input elements to the transform <ParDo(PTransform) label=[Count]>
with stateful DoFn must be key-value pairs.
```

Three details in that example are easy to get wrong, and all three produce
a `ValueError` at class-definition time:

- `beam.DoFn.StateParam` and `beam.DoFn.TimerParam` take a **spec
  object**, not a string. `StateParam("seen")` raises
  `ValueError: DoFn.StateParam expected StateSpec object.` and
  `TimerParam("flush")` raises `ValueError: DoFn.TimerParam expected
  TimerSpec object.` The spec is declared as a class attribute and then
  referenced.
- The coders live in `apache_beam.coders`, not in
  `apache_beam.transforms.userstate`. There is no `userstate.IntCoder()`;
  use `VarIntCoder` for counts and `FloatCoder` for a single mutable
  value. `ReadModifyWriteStateSpec` needs a coder for exactly one value,
  and the standard timestamp coder lives outside the `userstate` module.
- A `TimerSpec` needs a **time domain** *and* a registered callback.
  `userstate.TimeDomain` has `WATERMARK`, `REAL_TIME`, and
  `DEPENDENT_REAL_TIME`. The callback is attached with the
  `@userstate.on_timer(TIMER_SPEC)` decorator — a plain method named
  `on_timer` is not enough, and Beam raises `ValueError: DoFn ... has a
  TimerSpec without an associated on_timer callback`. Real-time timers
  are the ones the Prism runner's visitor rejects.

This is powerful and it is a trap. User state is:

- **Not portable in practice.** The Prism runner's support visitor
  declines pipelines that use *combining* value state, and pipelines with
  real-time (processing-time) timers. The `SwitchingDirectRunner` falls
  back to the bundle-based runner for those, but plain user state —
  `SetStateSpec`, `BagStateSpec`, `ReadModifyWriteStateSpec` — is
  accepted by Prism, and its behaviour there is less well exercised than
  on Dataflow.
- **Only fully supported in streaming.** In batch it works, but the
  semantics are awkward: there is no "session" to end, so a key's state
  is simply discarded when the job finishes.
- **A memory commitment.** Every key you touch holds state until it is
  garbage-collected, and Beam's user state has no TTL by default.

Reach for it only when you genuinely need per-key memory that a
`GroupByKey` cannot express, and you have checked that the runner you
target supports it.

### Where "the same code, two modes" is true — and where it lies

Beam's marketing says the same code runs in batch and streaming mode. This
is true in a specific, narrow sense, and the sense matters.

**It is true for:** the transform vocabulary (`Map`, `Filter`,
`CombinePerKey`, `GroupByKey`, `WindowInto`), the windowing model, the
trigger model, the source/sink shape, and the overall pipeline structure.
The graph you build is genuinely the same.

**It is a lie for:** everything about *what the graph is allowed to do*.

| | Batch | Streaming | Same code? |
|---|---|---|---|
| `GroupByKey` | free — buffer everything, output once | expensive — the buffer is live state, bounded by key cardinality | **no** |
| Re-read the input | allowed — you can read the file 5 times | impossible — the input never ends; you cannot go back | **no** |
| Global sort | allowed — one shuffle, total order | practically impossible — a global sort over an infinite stream never completes | **no** |
| `CombinePerKey` with a large accumulator | fine — the accumulator is one value per key | a memory risk if the key cardinality is high | **no** |
| Output semantics | write once, at the end | write many times, incrementally; results are refined | **no** |
| Failure | retry the job; the input is still there | retry from a checkpoint; the input is gone | **no** |
| Lookahead | allowed — you can read the next file to discover the schema | not allowed | **no** |
| Backfill / reprocessing | trivial — run it again over the historical data | requires a separate batch job over a snapshot | **no** |
| Cost | you pay for the whole run | you pay for the whole time it is running, including idle periods | **no** |
| Idempotency of the source | n/a | Pub/Sub is at-least-once; you must dedup | **no** |

The two rows worth drilling into, because they are where people get hurt:

**`GroupByKey` is free in batch and expensive in streaming.** In a batch
job, `GroupByKey` buffers all the values for a key and emits them at the
end. The buffer is bounded by the total data size, and the runner is
designed for that. In a streaming job, the buffer for a hot key is *live
state* that sits in a worker's heap from the first element to the window
close. A key with a million values per minute will OOM a worker in a way
that a batch job with a billion rows would not.

**Batch can re-read the input; streaming cannot.** This is subtle and it
breaks real designs. In batch, you can read the same file five times and
join the results — the file is there, it is finite, and reading it again
costs nothing but I/O. In streaming, there is no "the input" to re-read;
the topic is a firehose. Any design that needs a second pass — an
enrichment lookup against the full history, a "join with yesterday's
totals" — is not expressible in streaming mode. You must either maintain
that state in the pipeline (stateful processing, with its memory cost) or
use a different mechanism entirely (a side input that is periodically
refreshed, a lookup against a database, a separate batch job).

The honest summary:

> **The pipeline *shape* is portable. The pipeline *semantics* are not.**
> Moving a pipeline from batch to streaming is a redesign, not a
> recompile.

That is also why the course's `streaming_pipeline.py` is a *separate* file
from `batch_pipeline.py`, and why it takes the events PCollection as a
parameter rather than reading a file itself. The structure is shared; the
semantics are not.

---

## 🛠️ Hands-On

### One Logic, Two Modes

The hands-on demonstrates exactly where the "same code" claim holds and
where it breaks.

### Step 1 — Confirm the bounded/unbounded distinction

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])

with beam.Pipeline(options=options) as p:
    (
        p
        | "Create" >> beam.Create([1, 2, 3])
        | "Double" >> beam.Map(lambda x: x * 2)
        | "Sink" >> beam.Map(print)
    )

proto = p.to_runner_api()
print("is bounded:", proto.components.pcollections[list(proto.components.pcollections)[0]].is_bounded)
```

`beam.Create` produces a **bounded** PCollection. `ReadFromPubSub` produces
an **unbounded** one. The runner reads this flag off the proto and behaves
accordingly.

### Step 2 — Watch the watermark advance to `+inf`

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.transforms.window import FixedWindows
from apache_beam.transforms.trigger import AccumulationMode, AfterWatermark
from apache_beam.utils.timestamp import Timestamp

# A bounded source with explicit event-time timestamps.
events = [
    (Timestamp(100.0), "EMEA"),
    (Timestamp(200.0), "AMER"),
    (Timestamp(300.0), "EMEA"),
]

# Pin the runner. The plain "DirectRunner" name routes to Prism, which
# cannot evaluate the `+inf` watermark that closes an `AfterWatermark`
# window, and panics.
options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])

with beam.Pipeline(options=options) as p:
    (
        p
        | "Create" >> beam.Create(events)
        | "Window" >> beam.WindowInto(
            FixedWindows(100),
            trigger=AfterWatermark(),
            accumulation_mode=AccumulationMode.ACCUMULATING,
        )
        | "Key" >> beam.Map(lambda pair: ("all", pair[1]))
        | "Count" >> beam.combiners.Count.PerKey()
        | "Sink" >> beam.Map(print)
    )
```

The output appears only at the end of the run. That is the watermark
advancing to `+inf`, closing both windows, and firing the
`AfterWatermark` trigger. In a streaming pipeline the same output would
arrive incrementally, as the real watermark passed each window boundary.

### Step 3 — Compare the same windowing logic in a streaming shape

The course's streaming pipeline is the same logic with a different source.
Compare the two:

```bash
cd data-engineering/data-Course/google/Dataflow
python resources/sample_data.py --output-dir ./sample_data

# Bounded file, streaming transforms.
python project/streaming_pipeline.py \
  --runner BundleBasedDirectRunner \
  --input ./sample_data/events.ndjson \
  --output ./out/ch14_streaming

cat out/ch14_streaming*
```

Now the same thing reading from a topic — the *identical* windowing and
aggregation code, a different source, and a pipeline that never ends:

```bash
python project/streaming_pipeline.py \
  --runner DataflowRunner \
  --project YOUR_PROJECT_ID \
  --region us-central1 \
  --topic YOUR_TOPIC \
  --output gs://YOUR_BUCKET/streaming
```

The transforms are identical. The *semantics* are not: the second one
never terminates, its results are refined as the watermark advances, and
its memory profile is completely different.

### Step 4 — Measure what `GroupByKey` costs in streaming

This is the "where the same code lies" demonstration. Build a pipeline
that groups by a high-cardinality key, and time it in both shapes.

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

# 200,000 distinct keys, one element each.
data = [(f"key-{i}", i) for i in range(200_000)]


def build_and_run(runner):
    """Run the grouping pipeline under a runner and return elapsed seconds."""
    import time

    options = PipelineOptions(["--runner", runner])
    start = time.perf_counter()
    with beam.Pipeline(options=options) as p:
        (
            p
            | "Create" >> beam.Create(data)
            | "Key" >> beam.Map(lambda kv: kv)
            | "Group" >> beam.GroupByKey()
            | "Count" >> beam.Map(lambda kv: (kv[0], len(list(kv[1]))))
            | "Sink" >> beam.Map(print)
        )
    return time.perf_counter() - start


elapsed = build_and_run("BundleBasedDirectRunner")
print(f"grouped {len(data)} keys in {elapsed:.1f}s")
```

Then compare against the same pipeline *without* the `GroupByKey`:

```python
import time

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

data = [(f"key-{i}", i) for i in range(200_000)]

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])
start = time.perf_counter()
with beam.Pipeline(options=options) as p:
    (
        p
        | "Create" >> beam.Create(data)
        | "Key" >> beam.Map(lambda kv: kv)
        | "Count" >> beam.Map(lambda kv: (kv[0], 1))
        | "Sink" >> beam.Map(print)
    )
print(f"no group: {time.perf_counter() - start:.1f}s")
```

The gap between those two numbers is the cost of the shuffle — the state
that `GroupByKey` introduces. In batch that cost is paid once and bounded
by the data size. In streaming, that same cost is paid *continuously*, and
the buffer for a hot key never shrinks until the window closes.

### Step 5 — Show the event-time vs processing-time difference

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.transforms.window import FixedWindows
from apache_beam.utils.timestamp import Timestamp

# Two events in the same event-time minute, but the second arrives much
# later. With event-time windowing, both land in the same window.
late = [
    (Timestamp(1000.0), "early"),
    (Timestamp(1010.0), "late-but-same-window"),
]

# Pin the runner: any windowed pipeline that closes a window at `+inf`
# panics under Prism.
options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])

with beam.Pipeline(options=options) as p:
    (
        p
        | "Create" >> beam.Create(late)
        | "Window" >> beam.WindowInto(FixedWindows(60))
        | "Key" >> beam.Map(lambda pair: ("k", pair[1]))
        | "Count" >> beam.combiners.Count.PerKey()
        | "Sink" >> beam.Map(print)
    )
```

Both events are in the `[1000, 1060)` window because their *event-time*
timestamps say so, regardless of when they arrived. If the window were
defined on arrival time, they would be in different windows.

### Step 6 — Verify the delivery guarantee of the BigQuery sink

```python
import apache_beam as beam
import inspect

signature = inspect.signature(beam.io.WriteToBigQuery.__init__)
print("use_at_least_once default:", signature.parameters["use_at_least_once"].default)
print("write_disposition default:", signature.parameters["write_disposition"].default)
print("create_disposition default:", signature.parameters["create_disposition"].default)
```

`use_at_least_once=False` is the default, which is how Dataflow gets
exactly-once into BigQuery: it deduplicates on replay. Setting it to
`True` opts out of the deduplication for throughput at the cost of the
guarantee.

### Step 7 — Build an idempotent sink

The whole point of the idempotency argument, in code:

```python
import apache_beam as beam
from apache_beam.io.textio import WriteToText


def build_idempotent_write(pipeline, rows, output_path):
    """Write rows keyed by a deterministic id, so a replay is harmless.

    The output path includes a hash of the row's content, not a timestamp
    or an arrival counter. Re-running the pipeline writes the same file
    names with the same contents.
    """
    return (
        rows
        | "Key" >> beam.Map(lambda row: (row["region"], row))
        | "Format" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]['revenue_eur']}")
        | "Write" >> WriteToText(
            output_path,
            shard_name_template="",
            num_shards=1,
        )
    )


with beam.Pipeline() as p:
    rows = p | "Create" >> beam.Create(
        [{"region": "EMEA", "revenue_eur": 100.0}]
    )
    _ = build_idempotent_write(p, rows, "./out/ch14_idempotent")
```

Re-running this writes the same file with the same contents. A
non-idempotent sink — appending to a list, incrementing a counter without
a key — would double the total on every replay.

---

## 🛠️ Common Errors and Fixes

### `ValueError: Cannot find a suitable windowing for ...` / elements land in the global window

```text
ValueError: Cannot automatically determine the output window of a GroupByKey
```

You applied a windowing to the input but not to the output of the
grouping, or you grouped *before* windowing. In Beam, the windowing
strategy must be consistent across a group-by-key boundary.

**Fix:** window the elements *before* the grouping, and use a
windowing-compatible key function:

```python
import apache_beam as beam
from apache_beam.transforms.window import FixedWindows

with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create([("a", 1), ("b", 2)])
        | "Window" >> beam.WindowInto(FixedWindows(60))
        | "Group" >> beam.GroupByKey()
        | "Sink" >> beam.Map(print)
    )
```

### The streaming pipeline produces no output and exits

```text
INFO:apache_beam.runners.direct.direct_runner:Finished pipeline in 0.5s
```

No output at all from a windowed pipeline, with no error. The usual
cause: the trigger is `AfterWatermark`, and the watermark never advanced
past the window boundary because the runner was not able to close the
windows.

**Fix:** run it under `BundleBasedDirectRunner`, which advances the
watermark to `+inf` for a bounded input. If you are on Prism and you see
the `+inf` panic instead, that is the Prism limitation described in
chapter 1.3.

### `AssertionError: GroupByKey ... unbounded PCollection`

```text
ValueError: GroupByKey cannot be applied to an unbounded PCollection ...
```

This one is not a real Beam error but it is a common mental-model
failure: Beam *can* group an unbounded PCollection, but only with a
windowing strategy. Without one, the group is unbounded and the runner
refuses.

**Fix:** add a `WindowInto` before the grouping.

### `RuntimeError: GroupByKey is not implemented in the FnApiRunner`

```text
RuntimeError: GroupByKey is not implemented in the FnApiRunner
```

The FnAPI harness does not implement the shuffle. Use the switching
runner or the bundle-based runner.

### `ValueError: Timestamp of ... is out of range`

```text
ValueError: Timestamp of 1.7e+09 is out of range
```

Mixing timestamp units. Beam's `Timestamp` is in *seconds* since the
epoch, but `datetime.timestamp()` also gives seconds — whereas
`time.time() * 1000` gives milliseconds, and `time.time()` gives seconds.
A common mistake is multiplying by 1000 when the source is already in
seconds.

**Fix:** use `Timestamp(float(dt.timestamp()))` with a timezone-aware
`datetime`, exactly as the course's `streaming_pipeline.event_timestamp`
does.

### The results differ between the direct runner and Dataflow

```text
# No exception. Just different numbers.
```

Almost always one of two things: a `CombineFn` that is not associative or
commutative, or a function with non-deterministic behaviour (`random`,
`id()`, set iteration order).

**Fix:** make the combiner's `merge_accumulators` a pure function of its
inputs, and test it against a shuffled input.

---

## 💡 Production Notes

- **The delivery guarantee is a runner and sink property; idempotency is
  your property.** Design the sink to be idempotent and the guarantee
  becomes an optimisation rather than a correctness requirement. A sink
  keyed by a deterministic, data-derived id is idempotent by construction.
- **In streaming, Pub/Sub is at-least-once and you must dedup.** The
  `dedup_key` function in `project/transforms.py` derives the key from the
  payload's identity, never from arrival time. Deduplicating on arrival
  order would dedup the wrong events.
- **Key cardinality is your memory bill.** In streaming, the state for a
  `(key, window)` pair stays resident until the window closes. A pipeline
  keyed by `user_id` across a million users with a one-hour window is
  holding a million live accumulators. Check your cardinality before you
  choose your window length.
- **A batch `GroupByKey` over 200 million rows is fine; a streaming
  `GroupByKey` over 200 million rows is a memory incident waiting to
  happen.** Same code, different operational reality. The port from batch
  to streaming is a redesign, and the group-by is usually where it breaks.
- **Never design a streaming pipeline that needs a second pass.** If the
  logic requires re-reading history — a lookup against all prior events, a
  join with yesterday's totals — you need a stateful pipeline, a
  periodically-refreshed side input, or a separate batch job. Decide which
  before you write the code.
- **Backfills are a batch job, always.** Reprocessing three months of
  history is a bounded job over a snapshot, not a "replay" of the
  streaming pipeline. Model it that way, and the "same code" claim holds:
  the transforms are the same; only the source differs.
- **Batch jobs are cheap to retry; streaming jobs are not.** A failed batch
  job restarts from the beginning and the cost is the rerun. A failed
  streaming job resumes from a checkpoint, but the state must be
  restorable, and the recovery time is the checkpoint interval. Size your
  checkpoint interval against your recovery-time objective.
- **Watch the idle bill.** A streaming job that is waiting for a slow
  source is still running, still holding workers, and still billing. If
  your source is bursty, a batch job triggered on a schedule may be both
  cheaper and simpler than a permanently-running stream.

---

## 🔑 Key Takeaways

- A PCollection is **bounded** (finite, known) or **unbounded** (infinite).
  The *source* determines this, and the runner's entire behaviour follows
  from it.
- The **watermark** is Beam's promise about the past: no element earlier
  than this will arrive. It is the mechanism that unifies batch and
  streaming — a batch job advances it to `+inf` when its input ends.
- **Windowing is defined on event time** because the question is usually
  "what happened when", not "when did it reach us". Processing-time
  windowing is a different, also-valid, question.
- The four guarantees are **at-most-once**, **at-least-once**,
  **exactly-once**, and **none**, in increasing strength and cost.
  Dataflow gives exactly-once into BigQuery and GCS in batch, and into
  BigQuery in streaming; everything else is at-least-once or weaker.
- **Exactly-once is a property of the sink**, not of the pipeline. You
  cannot get it into a third-party HTTP API, because the call and the
  checkpoint cannot be made atomic.
- **Idempotency beats the delivery guarantee.** Design sinks so that a
  replay is harmless — a deterministic, data-derived key — and then
  at-least-once costs you compute, not correctness.
- **The "same code, two modes" claim is true for the pipeline *shape* and
  false for its *semantics*.** Batch can `GroupByKey` freely and re-read
  its input; streaming cannot do either without paying for state.

---

## 📚 Practice Exercises

1. **Prove the watermark unifies the two modes.** Build one pipeline with
   `FixedWindows(60)` and `AfterWatermark`, once over `beam.Create` and
   once over a `TestStream` that advances the watermark explicitly.
   Expected answer: identical output; the bounded source reaches `+inf`
   at the end, and the `TestStream` reaches it by advancing explicitly.
   Explain why the `TestStream` version is the one you can rely on in a
   test.

2. **Find the breaking point of the same code.** Write a pipeline that
   (a) groups by a high-cardinality key and (b) joins the input against a
   second file read. Run it as a batch job. Then explain, precisely, the
   two places the streaming version of the same logic breaks, and what you
   would do instead in each case.

3. **Make a sink idempotent.** Take the course's `write_summary_to_csv`
   in `project/transforms.py` and design a version that is safe to
   replay: the output name derived from the content, and the write an
   upsert rather than an append. Expected answer: the content-derived
   filename makes the replay write the same bytes to the same path.

4. **Test a non-associative combiner.** Write a `CombineFn` whose
   `merge_accumulators` rounds to 2 decimal places at each merge. Run it
   over 100,000 values in one bundle, then over 100,000 values split
   into many bundles. Expected answer: the two results differ, because
   rounding at merge time is not associative. Explain how you would
   detect this in a unit test of the pure function.

5. **Measure the cost of the shuffle.** Time the grouping pipeline from
   the hands-on with and without `GroupByKey`, at 10,000 and at 200,000
   elements. Expected answer: the gap widens super-linearly with
   cardinality, because the buffer per key grows. Then explain what this
   implies for a streaming pipeline with a one-hour window.

6. **Reflection.** A colleague says: "We already have the batch pipeline
   working. Turning on streaming is just a flag change." Using the
   comparison table above, write the specific list of things that have to
   be redesigned, and estimate the effort for each. This is the question
   you will be asked, and the honest answer is what separates a
   competent engineer from a hopeful one.

---

## 📖 Further Reading

- Apache Beam: "A Beam Primer" (the model overview) — https://beam.apache.org/documentation/basic-topics/
- Beam's time and windowing model — https://beam.apache.org/documentation/basic-topics/windowing/
- Beam's triggers and watermark semantics — https://beam.apache.org/documentation/basic-topics/trigger/
- Beam's exactly-once state processing (the Flink integration paper) — https://beam.apache.org/documentation/runtime/model/#exactly-once-state-processing
- Google Cloud Dataflow: exactly-once processing — https://cloud.google.com/dataflow/docs/concepts/processing-guarantees
- Google Cloud Pub/Sub: exactly-once delivery — https://cloud.google.com/pubsub/docs/exactly-once-delivery
