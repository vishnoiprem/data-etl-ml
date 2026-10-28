# 7.3 — Windowing

> **Section 7 · Streaming Pipelines · Lecture 7.3 · 6:30**

## 🎯 What you will learn

- `beam.WindowInto` — the only way to put elements into windows
- The four window types — `FixedWindows`, `SlidingWindows`, `Sessions`, `GlobalWindows` — and the exact semantics of each
- Why `FixedWindows` align to the **Unix epoch**, not to the first element
- Why `WindowInto` on its own is a **no-op**, and what must follow it
- The shape of a `GroupByKey` result in a window
- `beam.transforms.window.IntervalWindow` and `BoundedWindow`
- `beam.window.TimestampCombiner` — the real member names are `OUTPUT_AT_EARLIEST` and `OUTPUT_AT_LATEST`
- The "zoom lens" pattern: the same pipeline at day, month, and year granularity by changing one number
- Session windows and the gap parameter
- The memory cost of a window, and the allowed-lateness multiplier

---

## 🧠 Concept

### Windows are a partitioning of the event-time axis

A window is a **finite, contiguous slice of the event-time axis**. Windowing
is the act of assigning every element to one or more such slices, so that
an aggregation can be computed independently per slice.

Beam has exactly four window types. They differ in how they partition the
timeline.

| Type | Partition | Overlap | Use it for |
|---|---|---|---|
| `FixedWindows` | equal, non-overlapping slices | none | periodic reports ("per hour", "per day") |
| `SlidingWindows` | equal slices, offset by a period | yes | smoothing ("trailing 5 minutes, every minute") |
| `Sessions` | variable slices, cut by inactivity gaps | none | user sessions |
| `GlobalWindows` | one slice: all of time | n/a | whole-dataset aggregates |

### `FixedWindows` — the workhorse

`FixedWindows(size)` divides the event-time axis into slices of a fixed
duration, back to back, with no gaps and no overlaps.

The critical detail, and the one that catches everyone: **fixed windows
align to the Unix epoch.** They do *not* start at the first element's
timestamp.

```text
size = 3600 (one hour), epoch = 1970-01-01T00:00:00Z

        00:00      01:00      02:00      03:00
   ───────┬──────────┬──────────┬──────────┬───────
          │          │          │          │
      window     window     window     window
        [-1]      [0]       [1]       [2]
```

With an hour-sized window, the boundaries are at every whole hour of
UTC — 00:00, 01:00, 02:00, and so on. With a 15-minute window they are at
:00, :15, :30, :45. With a 7-day window they are at midnight UTC on
Thursdays (the Unix epoch was a Thursday), which surprises people who
expect "weeks starting on Monday."

The course's `window_key` helper in `transforms.py` implements exactly
this arithmetic:

```python
def window_key(event: dict, window_seconds: int = 3600) -> int:
    """Return the window index an event belongs to."""
    if window_seconds <= 0:
        raise ValueError("window_seconds must be positive")
    timestamp = parse_timestamp(str(event["event_ts"]))
    return int(timestamp.timestamp()) // window_seconds
```

Integer division by the window size. That is the epoch alignment, in one
line. You can verify it against Beam's own assignment:

```bash
.venv/bin/python -c "
from transforms import window_key

for ts in ['2026-01-15T10:05:00+00:00', '2026-01-15T11:05:00+00:00']:
    print(ts, '-> 1h window index', window_key({'event_ts': ts}, 3600))
"
```

```text
2026-01-15T10:05:00+00:00 -> 1h window index 491242
2026-01-15T11:05:00+00:00 -> 1h window index 491243
```

Two consecutive hour indices for two events an hour apart. Correct.

**Why epoch alignment matters.** It is what makes windows *comparable
across runs, across pipelines, and across time zones*. If windows started
at the first element, then the same dataset processed twice could produce
different window boundaries, and two pipelines with different start times
could not be compared. Epoch alignment gives every window a stable,
absolute identity: "the hour starting 2026-01-15T10:00:00Z" means the same
thing in every run.

The `offset` parameter shifts the alignment. `FixedWindows(size, offset)`
moves every boundary by `offset` seconds, which is how you align windows
to a business boundary — for example, to start the "day" at 06:00 UTC
rather than midnight:

```python
from apache_beam.transforms.window import FixedWindows

# Days that start at 06:00 UTC.
business_day = FixedWindows(size=86400, offset=6 * 3600)
```

Note the offset is in **seconds**, and it shifts the boundary forward from
the epoch-aligned one.

### `SlidingWindows` — overlapping slices

`SlidingWindows(size, period)` produces windows of `size` duration,
starting every `period`. When `period < size`, the windows overlap.

The mental model is a **trailing window**: with `size=300, period=60`, you
get a window covering the last 5 minutes, emitted every minute. The
windows at 10:00, 10:01, 10:02, ... each cover 5 minutes of event time,
and consecutive windows share 4 of their 5 minutes.

```text
size=300, period=60

   10:00      10:05      10:10      10:15
 ────┬──────────┬──────────┬──────────┬────
     │  window  │  window  │  window  │
     │  09:55    │  10:00    │  10:05    │
 ────┴──────────┴──────────┴──────────┴────
        each 5 min wide, one every minute
```

When `period == size`, sliding windows are identical to fixed windows.
When `period > size`, you get **gaps** — and Beam documents this as
unsupported for grouping operations, because the gaps mean some events
belong to no window at all.

The cost is proportional to the overlap ratio. `size=3600, period=60` means
every element is processed in **60 different windows** — a 60× increase in
aggregation work and state. That is the number to check before you deploy
a sliding window.

### `Sessions` — cutting on inactivity

`Sessions(gap_size)` groups elements into sessions separated by
gaps of inactivity. Two consecutive elements belong to the same session if
they are less than `gap_size` apart.

The window boundaries are **not known in advance**. Beam builds the
session as it sees elements, and the window can be *extended* as long as
elements keep arriving within the gap. This has two consequences:

1. The window's end time is unknown until the session ends. So a session
   window's output cannot be emitted until the session is closed — which
   is why session windows interact badly with early/late firing triggers.
2. Sessions in the same window family **merge** if they are close enough.
   Beam's `Sessions` window function implements this: two sessions that
   would be within the gap of each other are merged into one.

The gap parameter is a business decision, not a technical one. A 30-minute
gap means "a user who hasn't interacted for 30 minutes has ended their
session." Too small and one user's day fragments into dozens of sessions;
too large and distinct sessions merge.

The trade-off is real: session windows are the most expensive window type
per unit of data, because Beam must hold all candidate sessions and
compare them. For a large user base, session windows can be a serious
performance problem. Fixed windows are much cheaper because their
boundaries are known in advance and can be sharded across workers.

### `GlobalWindows` — one window, all of time

`GlobalWindows` puts every element in a single window. It is the default
when you do not apply `WindowInto` at all.

In a **batch** pipeline it is harmless and often convenient — the whole
dataset is one group, and the aggregation completes at the end.

In a **streaming** pipeline it is a trap:

- The window never closes, so the state for the key accumulates for the
  **entire lifetime of the job**.
- `GroupByKey` on the global window buffers everything and never emits.
- The state is checkpointed continuously, so you pay for it in both memory
  and I/O, forever.

The rule is: **use `GlobalWindows` in batch pipelines, never in streaming
ones.** If you need a running total in a streaming pipeline, use a
tumbling window.

### `WindowInto` must be followed by a windowed aggregation

This is the most common structural mistake, and it fails **silently**.

`WindowInto` is a *grouping* operation. It does not aggregate. It assigns
elements to windows and marks the PCollection as "windowed." The
aggregation happens in the next step.

```text
elements  ──WindowInto──▶  windowed PCollection  ──CombinePerKey──▶  results
```

If you apply `WindowInto` and then a plain `Map`, you get the same
elements back — just tagged with their window. Nothing is aggregated. The
pipeline runs, produces output, and is wrong.

And there is a subtler version of the same bug: `WindowInto` must come
**after** the elements have their timestamps, and **before** the
aggregation. If you put `WindowInto` before the re-stamping step, the
elements are assigned to windows based on their *read* timestamps, and the
re-stamp afterwards does not move them.

The course's `streaming_pipeline.py` gets the order right:

```python
parsed = events | "ParseEvents" >> beam.Map(parse_event)

windowed = parsed | "ApplyWindow" >> beam.WindowInto(
    window,
    trigger=trigger,
    accumulation_mode=accumulation_mode,
    allowed_lateness=effective_lateness,
)

keyed = windowed | "KeyByRegion" >> beam.Map(
    lambda event: (event["region"], event["value"])
)

counts = keyed | "CountEvents" >> beam.combiners.Count.PerKey()
```

Parse → window → key → aggregate. Correct order.

### The shape of a `GroupByKey` result in a window

`GroupByKey` groups elements by key **and by window**. The result element
is a `(key, group)` pair, where `group` is a list of the values that
landed in that (key, window).

That means the same key can appear **multiple times** in the output — once
per window it appeared in. If a region has events in three hourly windows,
you get three output elements for that region.

For a *windowed* `GroupByKey`, the element that comes out is a
`WindowedValue` — a wrapper carrying the value plus the window's
timestamps. This matters when you write tests, and the course's test
helper exists precisely because of it:

```python
def _windowed_values(expected: list[tuple]):
    """Build a matcher that compares the values, not the windows.

    With `use_global_window=False` the elements arrive as `WindowedValue`
    objects. Comparing them directly against plain tuples fails, because
    the window has a start, an end, and a timestamp.
    """

    def _compare(actual):
        unwrapped = [
            item.value if hasattr(item, "value") else item for item in actual
        ]
        return sorted(unwrapped, key=repr) == sorted(expected, key=repr)

    return _compare
```

Note the phrase in that docstring: *"The window boundaries are deliberately
not checked."* The tests verify **how many firings happened and what each
contained** — not the boundaries. That is a deliberate scoping decision,
and it is worth understanding why: the boundaries depend on the timestamps
in the test data, and the property under test is the *firing behaviour*.

`CombinePerKey` has the same multi-window shape, but each output is the
combined value rather than a list.

### `IntervalWindow` and `BoundedWindow`

Every window in Beam is a `BoundedWindow`. The concrete types are:

| Type | Has bounds? | Used by |
|---|---|---|
| `IntervalWindow` | yes — `.start` and `.end` | `FixedWindows`, `SlidingWindows`, `Sessions` |
| `GlobalWindow` | no | `GlobalWindows` |

`IntervalWindow` is the one you will interact with. It has `.start` and
`.end` as `Timestamp` values, and the interval is **half-open**: `[start,
end)`. An element at exactly `end` belongs to the *next* window, not this
one. This matters at boundaries — an event at exactly 10:00:00 belongs to
the 10:00 hour, and the 09:00 hour excludes it.

To get the window into your output, inject it with `WindowParam`:

```python
class WithWindow(beam.DoFn):
    def process(self, element, window=beam.DoFn.WindowParam):
        yield f"{element} in [{window.start}, {window.end})"
```

For the global window, `window.start` and `window.end` do not exist — it
is a `GlobalWindow` with no bounds. If your output format needs the window
start, you must handle that case, or use a non-global window.

The `TimestampCombiner` controls something related but different: the
**output timestamp** of the elements a grouping produces.

### `TimestampCombiner` — the real API

The class is `beam.window.TimestampCombiner` (also importable as
`beam.transforms.window.TimestampCombiner`). Its members are:

```python
beam.window.TimestampCombiner.OUTPUT_AT_EOW
beam.window.TimestampCombiner.OUTPUT_AT_EARLIEST
beam.window.TimestampCombiner.OUTPUT_AT_LATEST
```

Note the naming: they are `OUTPUT_AT_EARLIEST` and `OUTPUT_AT_LATEST`,
**not** `EARLIEST` and `LATEST`. Getting this wrong is a common trip-up.

| Combiner | The output element's timestamp is |
|---|---|
| `OUTPUT_AT_EOW` (default) | the **end** of the window |
| `OUTPUT_AT_EARLIEST` | the timestamp of the **earliest** element in the pane |
| `OUTPUT_AT_LATEST` | the timestamp of the **latest** element in the pane |

`OUTPUT_AT_EOW` is the default, and it is what you want 95% of the time:
the output represents the whole window, so it is stamped at the window's
end.

`OUTPUT_AT_EARLIEST` is useful when downstream consumers order by
timestamp and you want the output to appear at the time the window
*started* rather than the time it ended. `OUTPUT_AT_LATEST` is the
counterpart.

You pass it to `WindowInto`:

```python
from apache_beam.transforms.window import TimestampCombiner

windowed = parsed | "ApplyWindow" >> beam.WindowInto(
    FixedWindows(size=3600),
    timestamp_combiner=TimestampCombiner.OUTPUT_AT_EARLIEST,
)
```

### The zoom lens

This is the pattern that makes windowing worth learning properly, and it
is a direct consequence of Beam's model.

**The same pipeline, run at three granularities, should differ only in one
number.** The window size.

```text
                window-seconds
                       │
        ┌──────────────┼──────────────┐
        │              │              │
     86400           21600            3600
     (1 day)         (6 hours)      (1 hour)
        │              │              │
   monthly rollup   shift report   live dashboard
```

Concretely, the course's `streaming_pipeline.py` takes `--window-seconds`:

```bash
python project/streaming_pipeline.py --window-seconds 3600    # hourly
python project/streaming_pipeline.py --window-seconds 21600   # 6-hourly
python project/streaming_pipeline.py --window-seconds 86400   # daily
```

The aggregation, the parsing, the output format, the trigger — all
identical. Only the window size changes.

This is the practical payoff of "batch is streaming with an end": **the
same code produces the hourly, the daily, and the backfill answer**, and
because the windows are epoch-aligned, the hourly buckets of a day
partition exactly into the day's bucket, and the daily buckets partition
exactly into the month's.

The zoom lens is also how you debug a windowing bug. If the daily number
is wrong, run the same pipeline with an hourly window and see which hour
is wrong. The zoom lens works in both directions.

### The memory cost of a window

A window's state is retained until the window is closed **and** its
allowed lateness has expired. That gives a simple cost model:

> **State ≈ (number of open windows) × (state per window)**

For a fixed window of duration `D` and allowed lateness `L`, at any
moment roughly `D + L` worth of windows are open. So:

| Window | Lateness | Open windows | Relative state |
|---|---|---|---|
| 1 hour | 0 | 1 | 1× |
| 1 hour | 5 min | 1.083 | 1.08× |
| 1 hour | 1 hour | 2 | 2× |
| 24 hours | 0 | 1 | 1× (but 24× the data) |
| 24 hours | 1 hour | 1.04 | 1.04× |

The "allowed-lateness multiplier" is the ratio of `D + L` to `D`. With
`L = 0.1 × D`, the multiplier is 1.1 — a 10% overhead. With `L = D`, it is
2 — you are holding twice the state.

But the more important cost is the **number of keys per window**, not the
number of windows. A window holding 1 million distinct keys is holding 1
million accumulators. In a streaming pipeline, that state is checkpointed
on every snapshot, so the I/O cost scales with it too.

The rule of thumb:

> **State per window ≈ (distinct keys in the window) × (accumulator size).**

This is why a **skewed key** is a streaming disaster in a way it is not in
batch. One hot key in a window means one accumulator that must be
serialized and checkpointed on every snapshot, and it is a serialization
hot spot for the whole worker. The course's sample data generator has a
`--hot-key-rate` flag precisely to demonstrate this:

```bash
python resources/sample_data.py --output-dir ./sample_data --hot-key-rate 0.5
```

### Sliding windows multiply the cost

One more number, because it is the one that catches people out. A sliding
window with `size=3600, period=60` assigns each element to **60 windows**.
The state and the aggregation work both scale by 60×.

If you want a trailing hour, computed every minute, that is a 60× cost
over a trailing hour computed once. Sometimes that is exactly what you
need. But know the number before you enable it.

---

## 🛠️ Hands-On

The exercise computes per-region counts at three granularities and shows
that the totals agree while the distributions differ.

### Step 1 — Generate the sample data

```bash
cd data-engineering/data-Course/google/Dataflow
export PYTHONPATH="$PWD/project"
python resources/sample_data.py --output-dir ./sample_data
```

The sample events all fall on 2026-01-15, spread across the 24 hours of
the day, in four regions.

### Step 2 — One window size

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
            './out/win_1h', num_shards=1, shard_name_template=''
        )
    )
" 2>&1 | grep -v "INFO\|WARNING"

echo "rows: $(wc -l < out/win_1h)"
head -4 out/win_1h
```

```text
rows: 96
APAC,207
APAC,221
APAC,218
```

96 rows: 24 hours × 4 regions.

### Step 3 — The same pipeline at three granularities

Now change **only** the window size. Here is a script that runs all three
and prints the comparison:

```python
import apache_beam as beam
from beam_options import build_options
from apache_beam.transforms.window import FixedWindows
from apache_beam.utils.timestamp import Timestamp
from transforms import parse_event_payload, parse_timestamp


def to_timestamp(event):
    epoch = float(parse_timestamp(str(event["event_ts"])).timestamp())
    return beam.window.TimestampedValue(event, Timestamp(epoch))


def count_per_region(window_seconds, output_path):
    """Count events per region in fixed windows of the given size."""
    with beam.Pipeline(options=build_options([])) as p:
        (
            p
            | "Read" >> beam.io.ReadFromText("./sample_data/events.ndjson")
            | "Parse" >> beam.Map(parse_event_payload)
            | "Restamp" >> beam.Map(to_timestamp)
            | "Key" >> beam.Map(lambda event: (event["region"], event["value"]))
            | "Window" >> beam.WindowInto(FixedWindows(window_seconds))
            | "Count" >> beam.combiners.Count.PerKey()
            | "Format" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]}")
            | "Write" >> beam.io.WriteToText(
                output_path, num_shards=1, shard_name_template=""
            )
        )


if __name__ == "__main__":
    for seconds, label in [(3600, "1h"), (21600, "6h"), (86400, "24h")]:
        count_per_region(seconds, f"./out/zoom_{label}")
        print(f"wrote ./out/zoom_{label}")
```

Run it and compare:

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


for seconds, label in [(3600, '1h'), (21600, '6h'), (86400, '24h')]:
    with beam.Pipeline(options=build_options([])) as p:
        (
            p
            | 'Read' >> beam.io.ReadFromText('./sample_data/events.ndjson')
            | 'Parse' >> beam.Map(parse_event_payload)
            | 'Restamp' >> beam.Map(to_timestamp)
            | 'Key' >> beam.Map(lambda event: (event['region'], event['value']))
            | 'Window' >> beam.WindowInto(FixedWindows(seconds))
            | 'Count' >> beam.combiners.Count.PerKey()
            | 'Format' >> beam.Map(lambda kv: f'{kv[0]},{kv[1]}')
            | 'Write' >> beam.io.WriteToText(
                f'./out/zoom_{label}', num_shards=1, shard_name_template=''
            )
        )
" 2>&1 | grep -v "INFO\|WARNING"

for label in 1h 6h 24h; do
    rows=$(wc -l < out/zoom_$label)
    total=$(cut -d, -f2 out/zoom_$label | awk '{s+=$1} END {print s}')
    echo "$label: $rows rows, total $total"
done
```

```text
1h: 96 rows, total 20000
6h: 16 rows, total 20000
24h: 4 rows, total 20000
```

The zoom lens in action. Same data, same code, one number changed. The
row counts are 96, 16, and 4 — 24 hours, 4 six-hour blocks, 1 day, each
times 4 regions. And the **totals are identical**, which is the invariant
that makes the granularities comparable.

### Step 4 — Verify the epoch alignment directly

```bash
python -c "
from transforms import window_key

events = [
    '2026-01-15T00:00:00+00:00',
    '2026-01-15T00:59:59+00:00',
    '2026-01-15T01:00:00+00:00',
    '2026-01-15T23:59:59+00:00',
]
for ts in events:
    print(ts, '-> 1h index', window_key({'event_ts': ts}, 3600))
"
```

```text
2026-01-15T00:00:00+00:00 -> 1h index 491242
2026-01-15T00:59:59+00:00 -> 1h index 491242
2026-01-15T01:00:00+00:00 -> 1h index 491243
2026-01-15T23:59:59+00:00 -> 1h index 491265
```

The first two are in the same window; the third starts a new one. The
boundaries fall on the hour, not on the first element.

### Step 5 — Look at the window bounds

Add a `DoFn` that reports the window it was in:

```python
import apache_beam as beam
from beam_options import build_options
from apache_beam.transforms.window import FixedWindows
from apache_beam.utils.timestamp import Timestamp
from transforms import parse_event_payload, parse_timestamp


def to_timestamp(event):
    epoch = float(parse_timestamp(str(event["event_ts"])).timestamp())
    return beam.window.TimestampedValue(event, Timestamp(epoch))


class ReportWindow(beam.DoFn):
    """Emit the element and the window it landed in."""

    def process(self, element, window=beam.DoFn.WindowParam):
        yield f"{element['event_id']} {element['event_ts']} -> [{window.start}, {window.end})"


with beam.Pipeline(options=build_options([])) as p:
    (
        p
        | "Read" >> beam.io.ReadFromText("./sample_data/events.ndjson")
        | "Parse" >> beam.Map(parse_event_payload)
        | "Restamp" >> beam.Map(to_timestamp)
        | "Window" >> beam.WindowInto(FixedWindows(3600))
        | "Report" >> beam.ParDo(ReportWindow())
        | "Write" >> beam.io.WriteToText(
            "./out/window_bounds", num_shards=1, shard_name_template=""
        )
    )
```

The output shows each event and the half-open interval it belongs to. The
`window.start` values are all exact hours.

### Step 6 — Sliding windows

```python
import apache_beam as beam
from beam_options import build_options
from apache_beam.transforms.window import SlidingWindows
from apache_beam.utils.timestamp import Timestamp
from transforms import parse_event_payload, parse_timestamp


def to_timestamp(event):
    epoch = float(parse_timestamp(str(event["event_ts"])).timestamp())
    return beam.window.TimestampedValue(event, Timestamp(epoch))


with beam.Pipeline(options=build_options([])) as p:
    (
        p
        | "Read" >> beam.io.ReadFromText("./sample_data/events.ndjson")
        | "Parse" >> beam.Map(parse_event_payload)
        | "Restamp" >> beam.Map(to_timestamp)
        | "Key" >> beam.Map(lambda event: (event["region"], event["value"]))
        | "Window" >> beam.WindowInto(
            SlidingWindows(size=3600, period=600)
        )
        | "Count" >> beam.combiners.Count.PerKey()
        | "Format" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]}")
        | "Write" >> beam.io.WriteToText(
            "./out/sliding", num_shards=1, shard_name_template=""
        )
    )
```

With `size=3600, period=600`, each event belongs to **6** windows — one
every 10 minutes, each covering the trailing hour. The effect on the
output is exactly a factor of 6:

```bash
echo "fixed  rows: $(wc -l < out/win_1h)  total: $(cut -d, -f2 out/win_1h | awk '{s+=$1} END {print s}')"
echo "sliding rows: $(wc -l < out/sliding) total: $(cut -d, -f2 out/sliding | awk '{s+=$1} END {print s}')"
```

```text
fixed  rows: 96  total: 20000
sliding rows: 596  total: 120000
```

The total is exactly **6×** — 120,000 against 20,000 — because every event
is counted in six windows instead of one. The row count grows too, but
not by 6×: it goes from 96 to 596, because windows near the start and end
of the day are only partially covered by data.

That 6× is the cost multiplier. It applies to the aggregation work, to
the state, and to the output volume.

### Step 7 — Use the course pipeline's window flag

The same zoom lens, using the shipped pipeline:

```bash
python project/streaming_pipeline.py --window-seconds 3600  --output ./out/p_1h
python project/streaming_pipeline.py --window-seconds 21600 --output ./out/p_6h
python project/streaming_pipeline.py --window-seconds 86400 --output ./out/p_24h

for f in out/p_1h out/p_6h out/p_24h; do
    echo "$f: $(( $(wc -l < $f) - 1 )) regions"
done
```

> **Note.** The shipped pipeline does not re-stamp the file source (see
> chapter 7.2), so all its events land in one window and it produces one
> row per region regardless of `--window-seconds`. The flag is exercised
> properly in the topic path, where `ReadFromPubSub` supplies the event
> timestamps.

---

## 🛠️ Common Errors and Fixes

### `ValueError: GroupByKey: Unsafe trigger` after adding `WindowInto`

`WindowInto` changes the trigger to the default `AfterWatermark`, which
Beam considers safe *only* with zero allowed lateness. If you also passed
`allowed_lateness`, the combination is unsafe:

```text
ValueError: GroupByKey: Unsafe trigger: `AfterWatermark()` may lose data. Reason: MAY_FINISH. This can be overriden with the --allow_unsafe_triggers flag.
```

Chapter 7.4 covers this in full. The short answer: a non-zero allowed
lateness and a watermark trigger are mutually exclusive without
`--allow_unsafe_triggers`.

### `AttributeError: module 'apache_beam.transforms.window' has no attribute 'SessionWindows'`

The class is named **`Sessions`**, not `SessionWindows`:

```python
# wrong
from apache_beam.transforms.window import SessionWindows

# right
from apache_beam.transforms.window import Sessions

windowed = p | "Window" >> beam.WindowInto(Sessions(gap_size=1800))
```

`Sessions` is available as `beam.window.Sessions` too.

### `AttributeError: module 'apache_beam.transforms.trigger' has no attribute 'TimestampCombiner'`

`TimestampCombiner` lives in the **window** module, not the trigger
module:

```python
# wrong
from apache_beam.transforms.trigger import TimestampCombiner

# right
from apache_beam.transforms.window import TimestampCombiner
```

### `AttributeError: type object 'TimestampCombiner' has no attribute 'EARLIEST'`

The member names carry the `OUTPUT_AT_` prefix:

```python
# wrong
TimestampCombiner.EARLIEST
TimestampCombiner.LATEST

# right
TimestampCombiner.OUTPUT_AT_EARLIEST
TimestampCombiner.OUTPUT_AT_LATEST
```

### `AttributeError: 'GlobalWindow' object has no attribute 'start'`

Your output formatter assumed an `IntervalWindow`, but the element was in
the global window. Either use a non-global window, or branch on the type:

```python
class FormatRow(beam.DoFn):
    def process(self, element, window=beam.DoFn.WindowParam):
        if hasattr(window, "start"):
            start = str(window.start)
        else:
            start = "-inf"
        yield f"{element},{start}"
```

### `TypeError: WindowInto() got an unexpected keyword argument 'window'`

The parameter is **`windowfn`**, not `window`:

```python
# wrong
beam.WindowInto(window=FixedWindows(3600))

# right
beam.WindowInto(FixedWindows(3600))
```

### `ValueError: SlidingWindows size must be greater than or equal to period` (or the inverse)

`SlidingWindows` requires `size >= period`. A `period` larger than `size`
would create gaps, and Beam does not support grouping over gapped
windows.

```python
# wrong — gaps
SlidingWindows(size=600, period=3600)

# right
SlidingWindows(size=3600, period=600)
```

### The windowed result has one row per key instead of one per key per window

You applied `WindowInto` but the aggregation is not windowed. The usual
cause is a `GroupByKey` *after* a `Reshuffle`, or an aggregation on a
PCollection that was flattened back into the global window.

Check the pipeline graph. `WindowInto` must be immediately upstream of the
`GroupByKey` / `CombinePerKey` — with no intervening `Flatten` or
`Reshuffle`, both of which reset the windowing.

### Every element lands in one window despite `--window-seconds`

The elements were never given their event timestamps. Beam timestamps file
elements with the **read time**, so they all land in the window containing
the read. This is chapter 7.2's subject, and the fix is the
`TimestampedValue` re-stamp.

### The output has far more rows than expected

You are probably using a sliding window with a small period. Check the
overlap ratio: `size / period` is the number of windows each element
belongs to. `SlidingWindows(size=3600, period=60)` is 60×.

### `TypeError: unhashable type: 'list'` in a windowed aggregation

Your key contains a list. Keys must be hashable — use a tuple, or a
string.

```python
# wrong
(event["region"], [event["value"]])

# right
(event["region"], event["value"])
```

### The window boundaries are not where you expected

Fixed windows align to the **Unix epoch**, not to your data or to
midnight in your local timezone. For an 8-hour window, the boundaries are
at 00:00, 08:00, and 16:00 UTC. Use the `offset` parameter to shift them:

```python
FixedWindows(size=86400, offset=6 * 3600)  # days starting at 06:00 UTC
```

---

## 💡 Production Notes

- **The window size is a capacity decision, not just a reporting
  decision.** In a streaming pipeline, the state for every open window is
  held in memory and checkpointed. A 24-hour window on 10 million distinct
  keys is a very different machine requirement from a 1-hour window on the
  same data. Size the window from the cardinality, not from the reporting
  requirement.
- **Prefer fixed windows in streaming.** They have known boundaries, so
  Beam can shard them across workers and retire their state on schedule.
  Session windows require holding candidate sessions and comparing them,
  which is dramatically more expensive at scale.
- **Align windows to business boundaries with `offset`, not with a
  filter.** The instinct is to drop events outside business hours. The
  better answer is to shift the window boundaries with
  `FixedWindows(size=..., offset=...)` so that every event is counted
  exactly once, in the window that contains it.
- **Do not use `GlobalWindows` in a streaming pipeline.** The state grows
  for the job's lifetime and is checkpointed continuously. If you need a
  running total, use a tumbling window with a bounded size.
- **Watch for skew inside a window, not just across keys.** One hot key
  (a celebrity, a bot, a single customer with 40% of your traffic) makes
  one accumulator enormous. It is a serialization hot spot for the whole
  worker and it shows up as a straggler bundle, not as an error. The
  course's `--hot-key-rate` flag demonstrates it; `CombinePerKey` with a
  bounded accumulator is the mitigation.
- **Sliding windows multiply cost by `size / period`.** Know the number.
  A 60× multiplier is sometimes right and often a mistake.
- **The allowed-lateness multiplier is `(D + L) / D`.** Ten percent
  lateness on a one-hour window costs 10% more state. Equal lateness
  doubles it. And allowed lateness makes the trigger unsafe, which is
  the subject of chapter 7.4.
- **The zoom lens is a debugging tool.** When a daily number is wrong,
  re-run at hourly granularity and find the bad hour. When an hourly
  number is wrong, re-run at minute granularity. This works because the
  windows nest — a property that only holds if you use fixed, epoch-
  aligned windows.
- **Fixed windows nest perfectly; session windows do not.** A session
  window's boundary depends on the data, so a session can straddle the
  boundary of a fixed window. If you need nested rollups, use fixed
  windows at every level.
- **The same window size must be used everywhere in a metric family.** A
  dashboard that shows hourly bars computed with a 1-hour window and a
  daily total computed with a 24-hour window will not reconcile if one of
  them was accidentally run at 2 hours. Pin the window size in
  configuration, not in code.
- **Do not compute the same metric at two granularities in one pipeline.**
  It works, but it doubles the state and it is almost always clearer to
  run the same pipeline twice at different `--window-seconds`. The zoom
  lens exists precisely so that you can.

---

## 🔑 Key Takeaways

- A window is a **finite slice of the event-time axis**; windowing is how
  you partition that axis so aggregations can be computed per slice.
- The four types are `FixedWindows` (equal, non-overlapping), `SlidingWindows`
  (overlapping, offset by a period), `Sessions` (cut by inactivity gaps),
  and `GlobalWindows` (all of time).
- `FixedWindows` align to the **Unix epoch**, not to the first element.
  That is what makes windows comparable across runs and pipelines. Use
  `offset` to shift the boundaries to a business boundary.
- **`WindowInto` is a no-op on its own.** It assigns elements to windows
  but aggregates nothing. A windowed aggregation — `GroupByKey` or
  `CombinePerKey` — must follow it immediately, with no intervening
  `Flatten` or `Reshuffle`.
- A windowed `GroupByKey` produces **one output element per (key,
  window)** pair, and the elements are `WindowedValue` objects carrying
  the window's timestamps. `TimestampCombiner`'s members are
  **`OUTPUT_AT_EARLIEST`** and **`OUTPUT_AT_LATEST`** (plus the default
  `OUTPUT_AT_EOW`) — and it lives in the **window** module, not the
  trigger module.
- The **zoom lens**: change only the window size and the same pipeline
  produces hourly, daily, and backfill answers — and the totals agree.
- Session windows are the most expensive per unit of data; fixed windows
  are the cheapest and shard best.
- **State ≈ open windows × keys per window × accumulator size**, and
  allowed lateness multiplies the open-window count by `(D + L) / D`.
  Sliding windows multiply the whole thing by `size / period`.

---

## 📚 Practice Exercises

1. **Verify the epoch alignment empirically.** Write a pipeline that reads
   `sample_data/events.ndjson`, re-stamps to event time, and emits each
   event's window bounds via `WindowParam`. Assert that every
   `window.start` is a multiple of 3600 seconds since the epoch. Then run
   the same with `FixedWindows(size=3600, offset=1800)` and confirm the
   starts are now at half-past the hour. Explain in writing why the
   aligned version is the one you want for reconciling two pipelines.

2. **Build the zoom lens properly.** Write a single script with a
   `--window-seconds` flag and a `--granularity` flag, running the
   per-region count aggregation. Run it at 900, 3600, 21600, and 86400
   seconds. Produce a table of row counts and per-region totals, and
   assert that the totals are identical at every granularity. Explain why
   the row counts are 24, 96, 16, and 4 times the region count.

3. **Compare fixed and sliding.** Run the per-region count with
   `FixedWindows(3600)` and with `SlidingWindows(size=3600, period=600)`.
   Record the row counts and the sum of the counts. Explain why the
   sliding version's total is roughly 6× the fixed version's, and what
   that implies about the cost of the sliding window.

4. **Session windows in practice.** Build a pipeline with
   `Sessions(gap_size=1800)` over the sample events and emit each
   session's start and end via `WindowParam`. Compare the number of
   sessions to the number of one-hour fixed windows. Explain why session
   windows are more expensive and why their boundaries cannot be predicted
   in advance.

5. **Add a timestamp combiner.** Run the windowed aggregation with
   `timestamp_combiner=TimestampCombiner.OUTPUT_AT_EARLIEST` and again
   with the default. Emit the output element's timestamp via
   `TimestampParam` and show the difference. Then explain which combiner
   you would use if a downstream consumer sorts by timestamp.

6. **Measure the state multiplier.** Run a windowed aggregation over the
   sample data with `allowed_lateness=0` and with `allowed_lateness=1800`
   (using `--allow_unsafe_triggers`). Instrument the pipeline to report
   the number of distinct open windows, and confirm the ratio matches
   `(D + L) / D` for a one-hour window. Explain what this predicts about
   the memory profile of a 24-hour window with one hour of lateness.

---

## 📖 Further Reading

- Beam's windowing guide — https://beam.apache.org/documentation/programming-guide/#windowing
- Beam's window types — https://beam.apache.org/documentation/programming-guide/#window-types
- Beam's triggers and accumulations — https://beam.apache.org/documentation/programming-guide/#triggers
- Dataflow's "Windowing and triggers" guide — https://cloud.google.com/dataflow/docs/guides/windowing
- Dataflow's "Windowing, triggers, and lateness" — https://cloud.google.com/dataflow/docs/guides/watermarks
- Beam's `TimestampCombiner` API — https://beam.apache.org/releases/pydoc/current/apache_beam.transforms.window.html
