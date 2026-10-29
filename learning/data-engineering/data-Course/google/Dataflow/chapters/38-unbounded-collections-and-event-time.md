# 7.2 — Unbounded Collections & Event Time

> **Section 7 · Streaming Pipelines · Lecture 7.2 · 6:30**

## 🎯 What you will learn

- What actually changes when a PCollection goes from bounded to unbounded
- Why the watermark never reaches `+inf` in a streaming job, and what that means for state
- Event time vs processing time vs ingestion time — and which one your business logic needs
- The `beam.window.TimestampedValue` API, and how to re-stamp an element
- `ReadFromPubSub` with `timestamp_attribute`, and the publish-time trap
- Why wall-clock reads in your logic are a bug in a streaming pipeline
- The "early" and "late" data problems, stated precisely
- `beam.DoFn.TimestampParam` and `beam.DoFn.WindowParam`
- How Beam timestamps an element read from a file — and why `parse_event_payload` + `TimestampedValue` is not optional
- The backfill-in-streaming pattern: bounded source + preserved event timestamps = identical results

---

## 🧠 Concept

### Bounded and unbounded

A PCollection is **bounded** if its contents are finite and known. It is
**unbounded** if the contents are not known in advance and may never stop
growing.

| | Bounded | Unbounded |
|---|---|---|
| Example | a `gs://` file, `beam.Create([...])` | a Pub/Sub subscription, a Kafka topic |
| Ends? | Yes | No |
| Watermark at the end | `+inf` | never `+inf` |
| Window state | discarded at the end | lives for the job's lifetime |
| Runner mode | batch | streaming |
| Job exits? | yes, on its own | no, until you cancel it |

The critical mechanism is the **watermark**. The watermark is Beam's
estimate of how far through the *event time* stream you have processed. It
answers the question: *"can I be sure no more elements with timestamps
earlier than T will arrive?"*

When a bounded source is exhausted, Beam sets the watermark to `+inf` — the
only truthful answer, because no more data will ever come. That single act
closes every window, fires every trigger, and produces the final output.

In an unbounded source, `+inf` is a lie and Beam never says it. The
watermark advances as new data arrives, based on the timestamps it has
observed. Windows close only when the stream has genuinely moved past them.

This is the whole difference, and it propagates into everything else.

### What changes downstream

**1. State must be bounded and checkpointed.**

In a batch job, the runner can hold all the state in memory and throw it
away at the end. In a streaming job, the state for a window that is
"still open" must survive worker restarts, rescaling, and preemption. That
is why Dataflow streams checkpoint window state to a persistent backend
periodically. Your pipeline's memory footprint is not "the data" — it is
"the windows that are currently open, plus their aggregate state."

Practically: a `GlobalWindow` in a streaming job accumulates state for the
**entire lifetime of the job**, and it is checkpointed the whole time. A
24-hour fixed window accumulates for 24 hours. That is the memory cost
model, and it is why window size is a capacity decision, not just a
reporting decision.

**2. `GroupByKey` becomes dangerous.**

`GroupByKey` must buffer every element for a key until the group is
complete. In a batch job the group is complete when the input ends. In a
streaming job, a group in the global window is **never** complete — so
`GroupByKey` on the global window in a streaming job buffers everything,
forever, and then emits it all at the end (which never comes).

The rule is absolute:

> **Never use `GroupByKey` on the global window in a streaming pipeline.**

Use `CombinePerKey` with a bounded accumulator instead. A combiner keeps a
*fixed-size* accumulator per key, no matter how many elements pass through.
A counter is an integer. A sum is a float. A top-K is a bounded heap. These
are O(1) in the number of elements, and that is what makes them survive in
a streaming job.

**3. The runner must handle unbounded input.**

This is not a pipeline-logic change but it is worth understanding, because
it explains some behaviour that looks like a bug:

- A streaming job never completes. `beam.Pipeline()` as a context manager
  on the Dataflow runner starts the job and returns; it does not block
  until the job finishes, because it never does.
- Autoscaling is continuous. A streaming job scales workers up and down
  based on backlog and CPU, without a fixed end point.
- State is periodically checkpointed and, on failure, restored to the last
  checkpoint. Unacked Pub/Sub messages are also redelivered, so after a
  failure you may see elements reprocessed.

### Three clocks

This is the single most important conceptual distinction in streaming, and
getting it wrong produces numbers that look plausible and are wrong.

| Clock | What it is | Where it comes from |
|---|---|---|
| **Ingestion time** | when Pub/Sub accepted the message | the publish time, set by the broker |
| **Processing time** | when *your worker* handled the element | the runner's clock |
| **Event time** | when the event actually happened in the world | inside your payload |

Consider a mobile client that loses connectivity for five minutes, then
reconnects and replays five clicks it buffered locally.

| Click | Event time | Ingestion time | Processing time |
|---|---|---|---|
| click 1 | 10:00 | 10:05 | 10:05:01 |
| click 2 | 10:01 | 10:05 | 10:05:01 |
| click 3 | 10:02 | 10:05 | 10:05:02 |

Now: which clock should the "events per minute" dashboard use?

**Event time**, unambiguously. The user did five things between 10:00 and
10:02. The dashboard that counts those actions in the 10:00 minute is
correct. The dashboard that counts them in the 10:05 minute is measuring
the network, not the user.

But event time has a problem: the data arrives out of order, and it may
arrive long after the fact. That is what watermarks, triggers, and allowed
lateness exist to manage.

**Processing time** is what you get for free, and it is almost never what
you want. It is the "when did my code see this" clock. It is not
reproducible (a re-run over the same data gives different answers), and it
is not a business concept.

**Ingestion time** sits between the two. It is stable and monotonic — no
two messages have the same publish time in a meaningful sense, and it never
goes backwards. It is a decent fallback, and it is exactly what you get
when you use `ReadFromPubSub` without `timestamp_attribute`.

**The rule:** if the business question is about *when something happened*,
use event time. If it is about *when the system saw it*, use ingestion
time. If it is about *when the pipeline processed it*, use processing time
— and you should ask why you care.

### Re-stamping with `beam.window.TimestampedValue`

Beam lets you set the timestamp of an element explicitly. The API:

```text
beam.window.TimestampedValue(value, timestamp)
```

The `value` can be any type Beam can encode. The `timestamp` can be a
float (epoch seconds), an int, or a `beam.window.Timestamp`.

```python
import apache_beam as beam
from beam_options import build_options
from apache_beam.utils.timestamp import Timestamp

element = beam.window.TimestampedValue(
    {"region": "EMEA", "value": 42.0},
    Timestamp(1768472700.0),
)
```

A `TimestampedValue` flows through the pipeline as an ordinary element. The
runner unpacks it at the point where it assigns the element to a window.

`TimestampedValue` is the mechanism behind every event-time pipeline. When
`ReadFromPubSub` uses `timestamp_attribute`, Beam is doing this for you
internally. When you read from a file, Beam is **not** — and that is the
critical detail.

### `timestamp_attribute` — and the publish-time trap

From the `ReadFromPubSub` documentation:

> `timestamp_attribute`: Message value to use as element timestamp. If None,
> uses message publishing time as the timestamp.

So the default is the **publish time**. The publish time is an *ingestion*
clock. It is monotonic and stable, which makes it a reasonable default for
a naive pipeline, and wrong for a pipeline whose windows represent business
time.

With the timestamp attribute set, Beam uses the attribute's value as the
element timestamp. The value must be either:

- a number of **milliseconds since the Unix epoch**, or
- an **RFC 3339 string** in UTC, e.g. `2026-01-15T10:05:00Z`.

Note the milliseconds: Pub/Sub's publish time is in nanoseconds, but
`timestamp_attribute` values are interpreted as **milliseconds**. Getting
this wrong by a factor of 1000 is a classic mistake — every event lands
in the wrong window, but the pipeline still succeeds and produces output
that looks like data.

### Wall-clock in your logic is a bug

Here is a rule that sounds harsh and is correct:

> **Never call `datetime.now()` or `time.time()` inside a `DoFn` that
> participates in a windowed aggregation.**

The reason is reproducibility. A windowed aggregation's output is a
function of *which elements landed in which window*. If your logic also
reads the wall clock, the output is a function of the elements **and when
the job happened to run**. Run the same data twice, get two different
answers. Replay a partition, get a different answer than the original
run. Debug a discrepancy between the streaming and the batch pipeline and
find that the batch ran at 03:00 and the stream at 14:00.

The three legitimate uses of a wall clock are:

1. **Inside a trigger.** `AfterProcessingTime` is *defined* in terms of
   processing time. That is not a bug — it is the trigger's contract.
2. **In metadata or logging.** "How long did this bundle take?" is a
   legitimate processing-time question.
3. **In a non-windowed side path.** A health-check metric, a heartbeat
   topic, a progress ticker.

Everywhere else, the clock comes from the element.

### Early and late data

Both problems exist, and they are mirror images.

**Late data** is data that arrives *after* the window it belongs to has
already been finalized. The classic case: a mobile app buffers events
offline and flushes them when connectivity returns, possibly minutes or
hours later. Its event time belongs to a window that the watermark has
already passed.

The response to late data is **allowed lateness**: you declare that a
window may still be updated for some period after it first fires. Beam
then re-fires the window when the late element arrives, and the output
reflects the corrected total. The cost is that the window's state must be
retained for that extra period, and that the consumer of your output must
be able to accept corrections.

**Early data** is data that arrives *before* the window it belongs to has
closed — but that is simply "on time" data, and it is not a problem. The
real meaning of "early" in the Beam sense is: data whose event time is
*behind* the current watermark but which the pipeline has not seen yet.
That is late data by another name. Some documentation uses "early" for the
complementary case of data arriving *ahead* of the watermark — which
happens when a producer's clock is skewed into the future, and which causes
a window to be held open longer than expected, or a watermark to stall.

Both problems have the same root cause: **the pipeline's knowledge of
"now" is an estimate, and reality disagrees with the estimate.** The
mechanisms for handling it are:

| Mechanism | What it does | Cost |
|---|---|---|
| **Trigger** | decides when a window fires | more state, or more output |
| **Allowed lateness** | how long a fired window can still be updated | more state retained |
| **Accumulation mode** | whether a firing carries the total or the delta | depends on the consumer |
| **Watermark** | the estimate of how far the stream has progressed | needs an idle-source strategy |

### `TimestampParam` and `WindowParam`

A `DoFn` can ask Beam to inject the current element's timestamp and the
current window. The syntax is a class attribute with a special default:

```python
class ReportEvent(beam.DoFn):
    def process(self, element, ts=beam.DoFn.TimestampParam,
                window=beam.DoFn.WindowParam):
        yield f"{element} @ {ts} in {window}"
```

| Parameter | Type | What you get |
|---|---|---|
| `beam.DoFn.TimestampParam` | `Timestamp` | the element's event-time timestamp |
| `beam.DoFn.WindowParam` | `BoundedWindow` | the window the element is in |
| `beam.DoFn.ElementParam` | any | the element itself (rarely needed) |
| `beam.DoFn.ElementTypeParam` | type hint | the element's type (rarely needed) |

`WindowParam` is how you get the window's boundaries into your output. The
course's `streaming_pipeline.py` uses `TimestampParam` in exactly this
way, in `ParseOrderFn` in `transforms.py`:

```python
def process(self, line: str, timestamp=beam.DoFn.TimestampParam) -> Iterable[Any]:
    """Parse one line and emit the resulting order dict."""
```

The window is a `BoundedWindow`. For a fixed window it is an
`IntervalWindow` with `.start` and `.end`; for the global window it is a
`GlobalWindow` with no bounds. That distinction matters when you format
output — the course pipeline documents it explicitly:

```python
def to_window_row(item) -> str:
    """Format a windowed aggregation into a CSV line.

    The key is just the region. Beam carries the window separately, and
    exposes it to a `DoFn` through the `TimestampParam`, so the window
    start is not part of the key here.
    """
```

### How Beam timestamps an element read from a file

This is the detail that trips up everyone moving from batch to streaming.

**When Beam reads an element from a file, it timestamps it with the read
time.** The file has no timestamps of its own — a line of text in a
`.ndjson` file carries a timestamp only if you parse it out and tell Beam
about it.

So if you read `sample_data/events.ndjson` — 20,000 events, each with an
`event_ts` spread across 2026-01-15 — and window them into one-hour
buckets, **every event lands in the same window**. Not because the events
are close together, but because Beam read them all at 14:29 today.

Let me demonstrate that, because the difference is the whole point.

```python
import apache_beam as beam
from beam_options import build_options
from apache_beam.transforms.window import FixedWindows

with beam.Pipeline(options=build_options([])) as p:
    (
        p
        | "Read" >> beam.io.ReadFromText("./sample_data/events.ndjson")
        | "Key" >> beam.Map(lambda line: ("all", line))
        | "Window" >> beam.WindowInto(FixedWindows(3600))
        | "Count" >> beam.combiners.Count.PerKey()
    )
```

The output is a single row with all 20,000 events in it. The one-hour
window is meaningless, because the window boundaries are "the hour during
which we read the file."

Now re-stamp each event to its own event time:

```python
import apache_beam as beam
from beam_options import build_options
from apache_beam.transforms.window import FixedWindows
from apache_beam.utils.timestamp import Timestamp
from transforms import parse_event_payload, parse_timestamp


def to_timestamp(event):
    """Re-stamp an event with its own event-time timestamp."""
    epoch = float(parse_timestamp(str(event["event_ts"])).timestamp())
    return beam.window.TimestampedValue(event, Timestamp(epoch))


with beam.Pipeline(options=build_options([])) as p:
    (
        p
        | "Read" >> beam.io.ReadFromText("./sample_data/events.ndjson")
        | "Parse" >> beam.Map(parse_event_payload)
        | "Restamp" >> beam.Map(to_timestamp)
        | "Key" >> beam.Map(lambda event: (event["region"], event["value"]))
        | "Window" >> beam.WindowInto(FixedWindows(3600))
        | "Count" >> beam.combiners.Count.PerKey()
    )
```

Now you get 24 windows — one per hour of 2026-01-15 — with the events
correctly distributed. **Same data, same window size, completely different
answer.** The only difference is the timestamp.

This is why `parse_event_payload` and the re-stamping step are not
optional decoration. Parsing alone does not change the timestamp; the
`TimestampedValue` wrapper does.

### The backfill-in-streaming pattern

The previous section sets up the most valuable trick in this module.

Because Beam is one model, a **bounded** source with **preserved event
timestamps** produces *exactly* the same windowed result as an unbounded
stream would, once the stream has advanced past the same point.

Think about it: the window boundaries are determined by the event
timestamps. The contents of each window are determined by which elements'
timestamps fall in it. The output is determined by the trigger firing
rules. None of that depends on *when* the elements arrived, or on how many
arrive per second.

So a backfill is:

1. Read the historical data from a bounded source (files in GCS, a
   BigQuery table, a snapshot export).
2. Re-stamp every element to its true event time.
3. Apply the same windowing, trigger, and aggregation as the live pipeline.
4. The result is the same numbers the live pipeline would have produced.

Verified, with the course's own sample data:

| Source | Windows produced | Result |
|---|---|---|
| File, **not** re-stamped | 1 | 20,000 in one bucket |
| File, re-stamped to event time | 24 | 20,000 spread across the day, correct per hour |

This is a genuinely useful capability, and it is worth internalising as a
principle rather than a trick:

> **If your streaming pipeline's output depends only on event time — not on
> processing time or arrival order — then you can always recompute it
> exactly, from a bounded source, with the same code.**

That is the payoff of the whole "batch is streaming with an end" idea. It
means:

- **Backfills** are free: replay history through the same pipeline.
- **Repairs** are free: if you find a bug in the aggregation, fix it and
  replay.
- **Audits** are free: recompute yesterday's numbers and compare.
- **Parity testing** are free: run the batch pipeline and the streaming
  pipeline over the same data and assert they agree.

The catch: this only holds if the pipeline is truly event-time-driven. The
moment you put a wall-clock read inside a `DoFn`, the property is gone, and
your backfill will not match your live output. That is why "wall-clock in
your logic is a bug" is not a style preference — it is the thing that
protects this property.

---

## 🛠️ Hands-On

The exercise in this chapter is to build the two versions side by side and
watch them disagree. The disagreement is the lesson.

### Step 1 — Generate the sample data

```bash
cd data-engineering/data-Course/google/Dataflow
python resources/sample_data.py --output-dir ./sample_data
```

### A note on the runner

Every command below builds its options with the course's own helper:

```python
from beam_options import build_options

options = build_options([])
```

`build_options` defaults to `BundleBasedDirectRunner` — the classic,
pure-Python runner — rather than Beam 2.60+'s newer Go-based
`DirectRunner` (the "Prism" runner). Prism does not yet support every
trigger and windowing combination: it panics on the `+inf` watermark
evaluation that happens at the end of a windowed batch run. The classic
runner supports the full feature set, which is what a course needs.

The `project/` directory has to be importable, so set `PYTHONPATH`:

```bash
export PYTHONPATH="$PWD/project"
```

### Step 2 — The un-stamped version (the wrong one)

```bash
python -c "
import apache_beam as beam
from beam_options import build_options
from apache_beam.transforms.window import FixedWindows

with beam.Pipeline(options=build_options([])) as p:
    (
        p
        | 'Read' >> beam.io.ReadFromText('./sample_data/events.ndjson')
        | 'Key' >> beam.Map(lambda line: ('all', line))
        | 'Window' >> beam.WindowInto(FixedWindows(3600))
        | 'Count' >> beam.combiners.Count.PerKey()
        | 'Format' >> beam.Map(lambda kv: f'{kv[0]},{kv[1]}')
        | 'Write' >> beam.io.WriteToText(
            './out/eventtime_unstamped',
            num_shards=1,
            shard_name_template='',
        )
    )
" 2>&1 | grep -v "INFO\|WARNING"

cat out/eventtime_unstamped
```

Expected output — **one row**:

```text
all,20000
```

Every event is in one window, because Beam stamped them all with the read
time.

### Step 3 — The re-stamped version (the right one)

```bash
python -c "
import apache_beam as beam
from beam_options import build_options
from apache_beam.transforms.window import FixedWindows
from apache_beam.utils.timestamp import Timestamp
from transforms import parse_event_payload, parse_timestamp


def to_timestamp(event):
    epoch = float(parse_timestamp(str(event['event_ts'])).timestamp())
    return beam.window.TimestampedValue(event, Timestamp(epoch))


with beam.Pipeline(options=build_options([])) as p:
    (
        p
        | 'Read' >> beam.io.ReadFromText('./sample_data/events.ndjson')
        | 'Parse' >> beam.Map(parse_event_payload)
        | 'Restamp' >> beam.Map(to_timestamp)
        | 'Key' >> beam.Map(lambda event: (event['region'], event['value']))
        | 'Window' >> beam.WindowInto(FixedWindows(3600))
        | 'Count' >> beam.combiners.Count.PerKey()
        | 'Format' >> beam.Map(lambda kv: f'{kv[0]},{kv[1]}')
        | 'Write' >> beam.io.WriteToText(
            './out/eventtime_restamped',
            num_shards=1,
            shard_name_template='',
        )
    )
" 2>&1 | grep -v "INFO\|WARNING"

wc -l out/eventtime_restamped
head -5 out/eventtime_restamped
```

Expected: **96 rows** (24 hours × 4 regions), with counts spread across
the day, and each region's total summing to 20,000.

### Step 4 — Prove the totals are identical

The distributions differ completely, but the total must be the same. This
is the invariant that makes backfills safe.

```bash
echo "un-stamped total: $(cut -d, -f2 out/eventtime_unstamped | awk '{s+=$1} END {print s}')"
echo "re-stamped total: $(cut -d, -f2 out/eventtime_restamped | awk '{s+=$1} END {print s}')"
```

Both print `20000`. Same data, same total, completely different
distribution. And the row counts differ sharply:

```bash
echo "un-stamped windows: $(wc -l < out/eventtime_unstamped)"
echo "re-stamped windows: $(wc -l < out/eventtime_restamped)"
```

```text
un-stamped windows: 1
re-stamped windows: 96
```

96 = 24 hours × 4 regions. That is the correct answer for one-hour windows
over a single day of events.

### Step 5 — The backfill, using the real pipeline

Now run the course's actual streaming pipeline over the same file:

```bash
python project/streaming_pipeline.py \
    --input ./sample_data/events.ndjson \
    --output ./out/backfill \
    --window-seconds 3600

cat out/backfill
```

```text
region,event_count,total_value
APAC,4885,291314.62
EMEA,5099,302548.0
LATAM,4979,299522.51
AMER,5037,302651.93
```

Note two things about this output, and both are instructive.

**First, only five rows.** Four regions, one row each. The window size was
3600 seconds, so you would expect up to 24 hourly buckets per region — 96
rows. You get 4. Why?

Because `streaming_pipeline.py` reads the file with `ReadFromText` and
**does not re-stamp the elements**. Beam stamped every element with the
read time, so all 20,000 events fall into the single hour during which
the file was read. One window, four regions, four rows.

This is exactly the trap described in the concept section, and it is
present in the course's own pipeline — which makes it a good illustration
rather than a hypothetical. The pipeline's `event_timestamp` helper is
already written for you:

```python
def event_timestamp(event: dict):
    """Return the event's timestamp as a Beam timestamp.

    Using the event's own timestamp rather than arrival time is what makes
    windowing meaningful. Arrival-time windowing in a pipeline that sees
    out-of-order data produces silently wrong results.
    """
```

The helper exists and is correct; the file source simply does not call
it. The topic source gets correct event times for free, because
`ReadFromPubSub` with `timestamp_attribute` stamps each message from its
attribute.

**Second, the counts are the whole day.** `AMER,5037` is every AMER event
in the file, not the count in one hour. So the number is right for the
window it actually used, and wrong for the window you asked for.

This is the practical shape of the problem. A file-backed backfill that
does not re-stamp produces a **whole-day aggregate dressed up as an
hourly one** — and because the numbers are plausible, nobody notices.

### Step 6 — Fix the backfill

Here is the corrected backfill. The only change is the re-stamping step:

```bash
python -c "
import apache_beam as beam
from beam_options import build_options
from apache_beam.transforms.window import FixedWindows
from apache_beam.utils.timestamp import Timestamp
from transforms import parse_event_payload, parse_timestamp


def to_timestamp(event):
    epoch = float(parse_timestamp(str(event['event_ts'])).timestamp())
    return beam.window.TimestampedValue(event, Timestamp(epoch))


with beam.Pipeline(options=build_options([])) as p:
    (
        p
        | 'Read' >> beam.io.ReadFromText('./sample_data/events.ndjson')
        | 'Parse' >> beam.Map(parse_event_payload)
        | 'Restamp' >> beam.Map(to_timestamp)
        | 'Key' >> beam.Map(lambda event: (event['region'], event['value']))
        | 'Window' >> beam.WindowInto(FixedWindows(3600))
        | 'Count' >> beam.combiners.Count.PerKey()
        | 'Format' >> beam.Map(lambda kv: f'{kv[0]},{kv[1]}')
        | 'Write' >> beam.io.WriteToText(
            './out/backfill_fixed',
            num_shards=1,
            shard_name_template='',
        )
    )
" 2>&1 | grep -v "INFO\|WARNING"

echo "rows: $(wc -l < out/backfill_fixed)"
```

Now you get **96 rows** — 24 hours × 4 regions — and the per-region totals
sum to the same 20,000.

**This is the backfill guarantee, and it is conditional.** The guarantee
holds when the pipeline's output depends only on event time. The course
pipeline's file path does not currently re-stamp, so its file-backed
output and its topic-backed output would *not* agree. Fix the file path
once, and both paths agree by construction.

That is the single most valuable thing to take from this chapter: **the
live path and the backfill path must share the same normalisation stage.**
When they do, backfills are free and you can trust them.

### Step 7 — Watch the wall-clock bug happen

Now write a version that uses the wall clock, and observe that it is not
reproducible:

```bash
python -c "
import time

import apache_beam as beam
from beam_options import build_options
from apache_beam.transforms.window import FixedWindows


def stamp_with_wall_clock(line):
    # WRONG. The window now depends on when the job ran.
    return beam.window.TimestampedValue(line, time.time())


with beam.Pipeline(options=build_options([])) as p:
    (
        p
        | 'Read' >> beam.io.ReadFromText('./sample_data/events.ndjson')
        | 'Stamp' >> beam.Map(stamp_with_wall_clock)
        | 'Key' >> beam.Map(lambda line: ('all', line))
        | 'Window' >> beam.WindowInto(FixedWindows(3600))
        | 'Count' >> beam.combiners.Count.PerKey()
        | 'Format' >> beam.Map(lambda kv: f'{kv[0]},{kv[1]}')
        | 'Write' >> beam.io.WriteToText(
            './out/wallclock', num_shards=1, shard_name_template=''
        )
    )
" 2>&1 | grep -v "INFO\|WARNING"

cat out/wallclock
```

The count is still 20,000 — but the window boundaries are now "the hour
in which the job ran." Run it again in an hour and the *boundaries* move.
The count would be the same only because the whole file is read in under a
second; on a larger file it would split arbitrarily.

This is the bug that does not announce itself. The pipeline succeeds. The
numbers are plausible. They are just meaningless.

### Step 8 — Late events

The sample data generator can produce events that belong to the very start
of the day but are stamped at the end of it:

```bash
python resources/sample_data.py \
    --output-dir ./sample_data_late \
    --late-events 500
```

```bash
python project/streaming_pipeline.py \
    --input ./sample_data_late/events.ndjson \
    --output ./out/late \
    --window-seconds 3600 \
    --allowed-lateness-seconds 300
```

Notice what the pipeline does with `--allowed-lateness-seconds 300`: it
logs a warning and **falls back to zero lateness**, because a non-zero
lateness makes the trigger unsafe and Beam would refuse the job.

```text
allowed_lateness=300s requires --allow_unsafe_triggers; falling back to 0s so the pipeline stays safe
```

The safe choice is deliberate, and it is the subject of chapter 7.4.

---

## 🛠️ Common Errors and Fixes

### `TypeError: TimestampedValue.__init__() missing 1 required positional argument: 'timestamp'`

You passed only the value. `TimestampedValue` needs both, in this order:

```python
# wrong
beam.window.TimestampedValue(event)

# right
beam.window.TimestampedValue(event, Timestamp(epoch_seconds))
```

### The timestamp is off by a factor of 1000

Almost always a milliseconds/seconds confusion. `Timestamp` takes **epoch
seconds** as a float. If you have milliseconds, divide by 1000.

```python
# wrong — milliseconds passed as seconds
Timestamp(1768472700000.0)

# right
Timestamp(1768472700000.0 / 1000.0)
```

The symptom is every event landing in a window decades away, or the
pipeline producing one enormous window per event.

### `AttributeError: 'str' object has no attribute 'timestamp'`

You passed an ISO string where a `datetime` was expected. Use the course's
parser, which returns a timezone-aware `datetime`:

```python
from transforms import parse_timestamp

epoch = float(parse_timestamp(event["event_ts"]).timestamp())
```

Note `parse_timestamp` raises `ValueError` on a malformed timestamp, and
assumes UTC when the string has no offset. That assumption must be
consistent across every producer, or your windowing will be subtly wrong.

### All the events land in one window

This is the classic "you forgot to re-stamp" symptom, and it is the reason
step 2 of the hands-on exists.

Beam timestamps file elements with the **read time**. You must either
read the timestamp out of the payload and wrap the element in a
`TimestampedValue`, or use a source that carries timestamps natively (like
`ReadFromPubSub` with `timestamp_attribute`).

Check with a quick diagnostic:

```text
| "Debug" >> beam.Map(
    lambda e: f"{e['event_ts']} -> {beam.DoFn.TimestampParam}"
)
```

Or, more simply, print the window bounds:

```python
class ShowWindow(beam.DoFn):
    def process(self, element, window=beam.DoFn.WindowParam):
        yield f"{element['event_id']} in [{window.start}, {window.end})"
```

If all the window bounds are identical, you have not re-stamped.

### `ValueError: Invalid timestamp` from `parse_timestamp`

The payload's timestamp field is not ISO-8601, or it is an empty string.
`parse_timestamp` accepts `2026-01-15T10:05:00+00:00` and
`2026-01-15T10:05:00Z`, and treats a naive timestamp as UTC.

```python
# wrong — a Unix epoch integer as a string
parse_timestamp("1768472700")

# right
parse_timestamp("2026-01-15T10:05:00+00:00")
```

### `TypeError: cannot pickle 'datetime.datetime' object` in a DoFn

You returned a `datetime` from a `DoFn` and Beam's default coder cannot
handle it. Convert to a `Timestamp` or a float epoch first.

```python
# wrong
yield {"event_ts": event["event_ts"]}  # if the value is a datetime object

# right
yield {"event_ts": float(parse_timestamp(...).timestamp())}
```

### `TypeError: DoFn.__init__() got an unexpected keyword argument 'timestamp'`

`TimestampParam` and `WindowParam` are not constructor arguments. They are
**default parameter values** on the `process` method:

```python
# wrong
class MyFn(beam.DoFn):
    def __init__(self, timestamp):
        self.timestamp = timestamp

# right
class MyFn(beam.DoFn):
    def process(self, element, ts=beam.DoFn.TimestampParam):
        ...
```

### The output differs between two runs of the same file

Something in your pipeline reads the wall clock. Search for `datetime.now`,
`time.time`, `datetime.utcnow`, and `datetime.now(timezone.utc)`.

The count of elements is stable, but the *window boundaries* move, so
which elements fall in which window changes. Replace the clock read with
the element's timestamp.

### `RuntimeError: ... may lose data. Reason: MAY_FINISH`

That is a trigger-safety error, not a timestamp error. See chapter 7.4
and the "Common Errors" section of chapter 7.1. The fix is
`--allow_unsafe_triggers`, but the real fix is usually to reconsider the
trigger.

### The backfill does not match the live output

Three possible causes, in order of likelihood:

1. **The live pipeline uses publish time and the backfill uses event
   time.** They are different clocks, so the numbers differ. Fix by using
   `timestamp_attribute` in the live path, or by re-stamping in the
   backfill.
2. **The backfill re-stamps but the live pipeline does not.** Same root
   cause, opposite direction.
3. **The pipeline reads the wall clock.** Then the two runs are not
   comparable at all.

---

## 💡 Production Notes

- **Put the event timestamp in a Pub/Sub attribute at publish time.** The
  producer knows the event time; the consumer should not have to dig it
  out of a JSON payload and re-stamp. Every hour of re-stamping you can
  avoid is an hour of drift you cannot have.
- **Watch for clock skew in producers.** A device with a wrong clock emits
  events with future timestamps, which hold windows open and stall the
  watermark. If you see a window that never closes, suspect a skewed
  producer before you suspect Beam. A common mitigation is to clamp
  element timestamps to the current watermark.
- **The `timestamp_attribute` format is milliseconds, not seconds.** This
  is the single most common integration bug. A pipeline that produces
  "one event per window, in 1970" is usually this.
- **Event time is what makes backfills possible.** If you cannot reproduce
  a historical result, you cannot trust your historical reports. Treat
  reproducibility as a requirement of the pipeline, not a nice-to-have.
- **Parity-test your batch and streaming pipelines.** Run both over the
  same bounded data and assert the windowed outputs match. This catches
  the class of bug where the streaming path has a subtly different filter
  or a different window size. It is cheap insurance and it runs in CI.
- **Do not use `GlobalWindow` in a streaming pipeline.** It accumulates
  state for the job's lifetime, it is checkpointed continuously, and it
  never emits a partial result. If you need a "running total", use a
  tumbling window with a sensible size.
- **Re-stamping is a transformation, and transformations are
  composable.** A common production pattern is a shared "normalise"
  stage that parses the payload, validates it, assigns the event
  timestamp, and sets the id — applied identically to the live and backfill
  paths. Any divergence between the two paths is a bug waiting to happen.
- **Beware the "quietly correct" failure.** A wall-clock bug usually
  produces a *plausible* number, not an error. The only reliable defence
  is a determinism test: run the same input twice, assert the output is
  byte-identical.
- **Ingestion time is a legitimate choice — make it deliberate.** If your
  business is genuinely about system arrival ("orders received per
  minute"), ingestion time is correct and simpler. Document which clock
  you chose and why, in the pipeline's docstring. Chapter 7.1's
  `streaming_pipeline.py` is a good model: it explains the choice in the
  `event_timestamp` docstring.

---

## 🔑 Key Takeaways

- **Bounded** PCollections have an end; the watermark reaches `+inf` and
  every window closes. **Unbounded** PCollections never do, so state must
  be bounded, checkpointed, and constantly maintained.
- **Never `GroupByKey` on the global window in a streaming job** — the
  group is never complete, so it buffers everything forever. Use
  `CombinePerKey` with an O(1) accumulator.
- There are **three clocks**: ingestion (publish), processing (worker), and
  event (what happened in the world). Business logic almost always wants
  event time.
- `beam.window.TimestampedValue(value, timestamp)` re-stamps an element.
  `ReadFromPubSub(timestamp_attribute=...)` does it for you — and the
  value must be **epoch milliseconds** or an **RFC 3339 UTC string**.
- **Wall-clock reads inside windowed logic are a bug.** They make the
  output depend on when the job ran, which destroys reproducibility and
  backfills.
- **Beam timestamps file elements with the read time.** A file of
  historical events is all "now" unless you re-stamp it — which is exactly
  why `parse_event_payload` plus `TimestampedValue` is not optional.
- **Late data** (arrives after its window closed) is handled by allowed
  lateness; **early data** (arrives before the watermark advances) is the
  mirror case. Both mean the pipeline's estimate of "now" was wrong.
  `beam.DoFn.TimestampParam` and `beam.DoFn.WindowParam` inject the
  element's event timestamp and the window bounds into a `DoFn`.
- **Bounded source + preserved event timestamps = identical results.**
  That is the backfill guarantee, and it holds only if the pipeline is
  free of wall-clock reads and the live and backfill paths share the same
  normalisation stage.


---

## 📚 Practice Exercises

1. **Three clocks, one dataset.** Build three pipelines over
   `sample_data/events.ndjson` that window the same events by (a) event
   time, (b) ingestion time (i.e. do not re-stamp), and (c) processing
   time (stamp with `time.time()` at read). Produce the number of
   one-hour windows and the count in each. Explain in writing which one
   you would use for a "hourly active users" metric, and why the other
   two are wrong for that question.

2. **Prove the backfill guarantee.** Run the course's
   `streaming_pipeline.py` over `sample_data/events.ndjson` with
   `--window-seconds 3600` and again with `--window-seconds 21600`. Write
   a small script that sums the per-window counts from each run and
   asserts the totals are equal. Then explain why the *per-window*
   numbers differ but the totals do not.

3. **Re-stamp with millisecond precision.** The payload's `event_ts` is
   ISO-8601. Add a `event_ts_ms` field to the sample events (or generate
   a small file by hand), publish-style attribute, and demonstrate the
   milliseconds/seconds bug: show the one-hour window count for a
   correct millisecond timestamp versus a value mistakenly passed as
   seconds. Include the resulting window boundaries in your answer.

4. **Add a `WindowParam` diagnostic.** Write a `DoFn` that emits
   `event_id`, the element timestamp, and the window's start and end
   bounds. Run it over ten events from `sample_data/events.ndjson` with
   and without re-stamping. Show the two sets of window bounds and
   explain the difference.

5. **Build a determinism test.** Run the same bounded pipeline twice into
   two different output paths and assert the files are byte-identical.
   Then deliberately introduce a `datetime.now()` call into one branch,
   show the test now fails, and explain which class of production bug this
   test is designed to catch.

6. **Reconcile two clock sources.** Publish 100 events to a Pub/Sub topic
   where the attribute timestamp is the *event* time, then re-read the
   same events from a file where you must parse the timestamp out of the
   payload. Write a script that computes the one-hour windowed counts from
   both and asserts they agree. This is the parity test described in the
   production notes — build it properly, with a meaningful failure
   message.

---

## 📖 Further Reading

- Beam's windowing guide — https://beam.apache.org/documentation/programming-guide/#windowing
- Beam timestamps and windowing — https://beam.apache.org/documentation/programming-guide/#timestamps
- Beam's data model — https://beam.apache.org/documentation/programming-guide/#beam-model
- Dataflow streaming execution model — https://cloud.google.com/dataflow/docs/concepts/streaming-execution
- Dataflow watermarks and out-of-order data — https://cloud.google.com/dataflow/docs/guides/watermarks
- Google Cloud Pub/Sub message ordering and timestamps — https://cloud.google.com/pubsub/docs/subscription-message-retention
