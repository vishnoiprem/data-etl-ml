# 7.5 — Watermarks & Allowed Lateness

> **Section 7 · Streaming Pipelines · Lecture 7.5 · 6:30**

## 🎯 What you will learn

- What a watermark actually is, and why "roughly the minimum timestamp seen so far, minus allowed lateness" is a useful mental model rather than the whole truth
- What it means for a window to "close" — and why closing is not the same as being finished
- The `allowed_lateness` parameter on `beam.WindowInto`, and the exact semantics of a late element
- Why Beam refuses `AfterWatermark` combined with non-zero allowed lateness, and what `--allow_unsafe_triggers` really does
- How the course project's fallback logic protects you from that error
- The watermark-advance problem in multi-source pipelines, and how a per-source hold-back fixes it
- The state cost of keeping a window open, and the arithmetic you should do before choosing a lateness budget
- The one rule that should decide your trigger and lateness configuration

---

## 🧠 Concept

### What a watermark is

A watermark is a **promise about the future made by the pipeline**. It says:
"I have now seen every element that could possibly carry an event timestamp
earlier than this."

That promise is the only thing that lets a streaming pipeline ever finish
anything. Without it, every window would have to stay open forever, because
in principle any element with any timestamp could still arrive.

Beam's estimate is derived from the event timestamps it has observed. The
mental model most people carry is:

```text
watermark ≈ (minimum event timestamp seen so far) − allowed lateness
```

That model captures the *shape* of the behaviour but is not the definition.
Two refinements matter in practice:

1. **The minimum is taken over the inputs that are still live.** A pipeline
   with two sources advances its watermark to the *smaller* of the two input
   watermarks. A source that has finished contributing no longer holds the
   watermark back.
2. **The runner may hold the watermark back deliberately.** Beam's runners
   keep the watermark slightly behind the observed minimum so that elements
   that arrive out of order within a small tolerance are not immediately
   treated as late. This is a safety margin, and its size is a runner
   implementation detail.

What the watermark means for a specific window is much more concrete:

> A window is **on time** if its end timestamp is at or before the current
> watermark. A window is **late** if its end timestamp is strictly after the
> current watermark.

### What "the window closed" actually means

This is where most tutorials mislead people, so it is worth being precise.

When the watermark advances past a window's end timestamp, Beam **fires**
that window's trigger. The window does not produce one final answer and
disappear — it produces a **pane**, and the window's state is **retained**
so that later elements can still update it, *provided* the pipeline allows
lateness.

So there are three distinct events, and they are not simultaneous:

| Event | Meaning | State retained? |
|---|---|---|
| Window fires | The trigger fires; output is emitted for this pane | Yes, if lateness allows |
| Lateness expires | The watermark advances past `window end + allowed_lateness` | No — state is garbage-collected |
| Data loss | A late element arrives after lateness expired | The element is **dropped** |

The critical consequence: **a window that has fired is not necessarily
finished.** With `ACCUMULATING` accumulation and non-zero allowed lateness,
a window can fire more than once, and each firing emits the *running total*
including everything that arrived up to that point.

If you are writing to a sink that cannot handle a row being written twice,
this matters a great deal. A BigQuery table keyed on `(region, window)` with
a `MERGE` or a `REPLACE` disposition handles it. A `WriteToText` sink does
not — it appends a new file per window, and a window that fires twice
produces two rows.

### The `allowed_lateness` API

`beam.WindowInto` takes `allowed_lateness` as a keyword argument, measured
in **seconds**:

```python
import apache_beam as beam
from apache_beam.transforms.window import FixedWindows
from apache_beam.transforms.trigger import AccumulationMode, AfterWatermark

windowed = (
    events
    | "ApplyWindow" >> beam.WindowInto(
        FixedWindows(size=3600),
        trigger=AfterWatermark(),
        accumulation_mode=AccumulationMode.ACCUMULATING,
        allowed_lateness=300,
    )
)
```

The semantics, precisely:

- The window's end timestamp is `window_end = window_start + size`.
- The window's state is retained until the watermark reaches
  `window_end + allowed_lateness`.
- An element whose event timestamp falls in the window but which arrives
  after the window fired is a **late element**.
- If the late element arrives while the window is still within its lateness
  budget, it is **merged into the window's existing state** and the window
  fires again with the updated total.
- If it arrives after the budget expired, it is **dropped**.

The `allowed_lateness` parameter is a `Duration` in the runner API but a
plain integer number of seconds in the Python SDK. `300` means five
minutes.

### Why `AfterWatermark` plus allowed lateness is an error

This surprises nearly everyone the first time. The reasoning is worth
understanding, because it teaches you what Beam considers "safe".

Beam's contract for a *safe* trigger is:

> A trigger is safe if, when it fires, the result is guaranteed to include
> every element that will ever belong to the window.

`AfterWatermark` fires when the watermark passes the window end. With
`allowed_lateness = 0`, that is a guarantee: once the watermark has passed
the window end, no more elements can arrive for that window (the promise
was "I have seen every element with a timestamp earlier than this").

With `allowed_lateness = 300`, the promise is weaker: the watermark says
"I have seen everything earlier than this", but the runner is *deliberately*
holding the watermark back so that late elements can still be absorbed.
There is therefore a window of time during which more elements can arrive
for a window that has already fired. The result emitted at the first firing
is **not final** — and if the accumulation mode is `DISCARDING`, the later
elements are simply lost.

Beam refuses this combination because it cannot prove the result is
complete. The check lives in `GroupByKey` (and therefore in `CombinePerKey`
and `CoGroupByKey`, which group internally), not in `WindowInto`:

```text
ValueError: GroupByKey: Unsafe trigger: `AfterWatermark()` may lose data. Reason: MAY_FINISH. This can be overriden with the --allow_unsafe_triggers flag.
```

Two details in that message are worth noting:

- `MAY_FINISH` is the `DataLossReason` enum value. `AfterCount` reports
  the same reason, for the same underlying issue: the trigger fires before
  the window is provably complete.
- The message says "overriden" (sic). That is Beam's own spelling, reproduced
  here verbatim.

### The `--allow_unsafe_triggers` escape hatch

The flag lives on `TypeOptions`, and it is a **per-pipeline acknowledgement**
that you understand you are choosing a trigger Beam cannot prove safe:

```bash
python project/streaming_pipeline.py --allow_unsafe_triggers ...
```

or programmatically:

```python
from apache_beam.options.pipeline_options import PipelineOptions, TypeOptions

options = PipelineOptions(["--allow_unsafe_triggers"])
options.view_as(TypeOptions).allow_unsafe_triggers = True
```

With the flag set, Beam downgrades the error to a warning and keeps running:

```text
WARNING:apache_beam.transforms.core: GroupByKey: Unsafe trigger `AfterWatermark()` detected (reason: MAY_FINISH). This is being allowed because --allow_unsafe_triggers is set. This could lead to missing or incomplete groups.
```

What the flag does **not** do:

- It does not make the trigger safe.
- It does not change the semantics of `ACCUMULATING` versus `DISCARDING`.
- It does not tell the runner to retain state for longer.

All it does is stop Beam from refusing. Whether the pipeline produces
correct results is now entirely your responsibility.

### The course project's fallback behaviour

`project/streaming_pipeline.py` refuses to start in an unsafe configuration.
It inspects the options for `allow_unsafe_triggers`, and if the caller asked
for lateness without opting in, it falls back to zero with a warning rather
than failing at the `GroupByKey` stage:

```text
WARNING __main__: allowed_lateness=300s requires --allow_unsafe_triggers; falling back to 0s so the pipeline stays safe
```

This is a deliberate design choice, and it is worth understanding *why* it
is the right one for a course project:

- The default invocation of the pipeline — the one a reader types first —
  always succeeds. There is no configuration that produces a confusing
  `ValueError` from deep inside `GroupByKey`.
- The fallback is **loud**. A `WARNING` on stderr is visible; a silent
  downgrade is not.
- The fallback is **safe**. Zero allowed lateness with `AfterWatermark` and
  `ACCUMULATING` is the one combination Beam can prove is complete.

The logic, in the project's own words:

```python
# With allowed lateness, the trigger becomes unsafe unless the caller
# opts in. Fall back to a zero-lateness window so the default run is
# always safe and always succeeds.
effective_lateness = allowed_lateness_seconds
if effective_lateness and not unsafe:
    log.warning(
        "allowed_lateness=%ds requires --allow_unsafe_triggers; "
        "falling back to 0s so the pipeline stays safe",
        effective_lateness,
    )
    effective_lateness = 0
```

Note that the fallback only applies to the *lateness*. The `AfterCount`
trigger path is handled separately — if you ask for `--trigger-count N`,
the pipeline uses `AfterCount` with `DISCARDING`, and Beam will complain
about *that* unless the flag is set. The two decisions are independent.

### The watermark-advance problem in a multi-source pipeline

This is the failure mode that catches teams the first time they connect two
real sources.

**The rule:** a PCollection's watermark is the **minimum** of the watermarks
of its inputs. If you `Flatten` two sources — a busy clickstream topic and a
quiet reference-data topic — the merged PCollection's watermark is the
minimum of the two. The clickstream advances; the quiet source does not; the
merged watermark does not move.

The consequence is severe: **every window downstream of the merge stops
closing.** If the reference-data topic publishes once an hour, your hourly
windows close at best once an hour — and only if the reference topic's
watermark advances past the hour boundary. If the reference topic publishes
once a day, your hourly windows close once a day.

```text
   clickstream topic ──┐
                        ├── Flatten ──▶ watermark = min(w1, w2) ──▶ windows stall
   reference topic ────┘
```

In practice you see this as a dashboard that is hours behind, with no
errors and no alerts. The pipeline is healthy. It is simply never allowed
to finish a window.

**The fix: a per-source watermark hold-back.** The idea is to decouple each
source's *data* from its *watermark*, and then re-impose the hold-back
explicitly on the merged stream.

Beam's `TimestampCombiner` is the tool for the second half. The four
constants are:

| Constant | Meaning |
|---|---|
| `TimestampCombiner.OUTPUT_AT_EOW` | the output timestamp is the window's end |
| `TimestampCombiner.OUTPUT_AT_EARLIEST` | the earliest input timestamp in the pane |
| `TimestampCombiner.OUTPUT_AT_LATEST` | the latest input timestamp in the pane |
| `TimestampCombiner.OUTPUT_AT_EARLIEST_TRANSFORMED` | the earliest transformed input timestamp |

The important one for this problem is `OUTPUT_AT_EOW`, which makes the
output timestamp of a grouping operation equal to the end of the window
rather than to any input timestamp. That is what lets a merged stream
report progress at the rate of the *fastest* source rather than the slowest.

The structure of the fix is:

```text
for each source:
    read the source
    re-timestamp its elements (so the source's own watermark drives it)
    hold the source's watermark back by a fixed offset

merge the held-back streams
apply the window
```

Concretely, the pieces you need are:

```python
import apache_beam as beam
from apache_beam.transforms.trigger import TimestampCombiner
from apache_beam.transforms.window import FixedWindows
```

and the hold-back is expressed by re-stamping each source's elements to a
fixed lag behind the event time — for example, a clickstream source lagged
by 120 seconds and a reference source lagged by 300 seconds. The merged
watermark then advances at the rate of the *minimum* of the two lagged
streams, but it is a bounded, known lag rather than an unbounded stall.

You can also apply the timestamp combiner on the `WindowInto`:

```python
windowed = (
    merged
    | "ApplyWindow" >> beam.WindowInto(
        FixedWindows(size=3600),
        trigger=AfterWatermark(),
        accumulation_mode=AccumulationMode.ACCUMULATING,
        timestamp_combiner=TimestampCombiner.OUTPUT_AT_EOW,
    )
)
```

`OUTPUT_AT_EOW` is the right choice for windowed aggregations because the
output of a window is logically *about* the window, not about any
individual element that happened to land in it. Using
`OUTPUT_AT_EARLIEST` instead would make the output timestamp depend on the
earliest element, which re-introduces a dependence on whichever source
happened to be slowest.

There is a second, complementary technique that Dataflow deployments use:
**the watermark hold-back flag on the source itself.** In the Dataflow
streaming model, each source reports an output watermark, and the runner
takes the minimum across the inputs. By lagging one source's reported
watermark, you make the merged watermark advance on a predictable schedule
even if that source is genuinely quiet.

### The state cost of lateness

Allowed lateness is not free, and the cost is easy to underestimate.

Every open window holds state. For a `CombinePerKey` over a fixed window,
that state is the partial accumulator for each key in the window. If you
have 10,000 distinct keys per hour and you allow one hour of lateness, you
are holding roughly **two hours' worth** of accumulators live at any moment
(one hour of windows still accumulating, one hour of windows closed but
still updatable).

The general formula:

```text
live_state ≈ (number of open windows) × (state per window)
           ≈ (window_size + allowed_lateness) / window_size
             × (steady-state state of a closed-window pipeline)
```

Concretely, for a 1-hour window with 24 hours of allowed lateness, you hold
**25×** the state you would hold with zero lateness. For a 1-hour window
with 7 days of allowed lateness, you hold **169×**.

On Dataflow, state lives in the workers' local disks and in the streaming
engine's state backend. The practical consequences:

- **Disk pressure.** Workers hold state for every key in every open window.
  A job with a large lateness budget can exhaust the worker's disk quota
  and start spilling or failing bundles.
- **Hot keys.** A single key with a very large accumulation (a session
  window on a whale user) can dominate one worker's state.
- **Cost.** Dataflow bills for worker-hours. Holding state for a week of
  lateness on a high-cardinality key space is a line item you will see.
- **Recovery time.** After a worker dies, its state must be reconstructed.
  Longer-held state means longer recovery.

The latency-versus-cost trade-off is the whole game:

| Allowed lateness | Late data captured | Live state multiplier (1h window) |
|---|---|---|
| 0 s | none | 1× |
| 5 min | bursts of a few minutes | ~1.08× |
| 1 h | an hour of stragglers | ~2× |
| 24 h | a whole day of stragglers | ~25× |

### The practical guidance

The course project's own comment states the rule, and it is the right rule:

> So the pipeline takes the safe path by default — `AfterWatermark` with
> zero allowed lateness — and opts into the unsafe path only when the
> caller explicitly asks for it.

Stated as a decision procedure:

**Option A — exact results, no late data.**
Use `AfterWatermark` with `AccumulationMode.ACCUMULATING` and
`allowed_lateness=0`. This is the only combination Beam can prove is
complete. Every element that arrives before the watermark passes its
window is counted exactly once, and the output is final.

**Option B — approximate results, low latency.**
Use `AfterCount` with `AccumulationMode.DISCARDING`. The window emits
partial totals every N elements. You lose the tail of the window — the
elements that arrive after the last firing — but you get results
continuously. This is the right choice for a live dashboard that tolerates
being approximately right, and it is what `--trigger-count N` selects.

**Option C — exact results, tolerate late data, and accept the risk.**
Use `AfterWatermark` with `allowed_lateness > 0` and
`AccumulationMode.ACCUMULATING`, and pass `--allow_unsafe_triggers`. The
late data is merged into the window's total, and the window fires again
with the updated value. Your sink must be able to handle a row being
written more than once. Pair it with a `late=` sub-trigger so the merged
data is actually emitted (see the hands-on section below).

**What to avoid.** `AfterWatermark` with `allowed_lateness > 0` and
`DISCARDING`. The late elements are merged into the window's state but then
thrown away at the next firing, because `DISCARDING` emits only what
arrived since the previous firing. You pay the state cost of the lateness
budget and get nothing for it. Beam allows this combination (with the
flag), but it is strictly worse than both Option A and Option B.

The rule of thumb: **use zero lateness with `AfterWatermark` and
`ACCUMULATING`, or use `AfterCount` and accept the drop.** The middle
ground is a business decision about how much your numbers are worth, not a
technical default.

---

## 🛠️ Hands-On

All commands are run from the course root,
`data-engineering/data-Course/google/Dataflow/`.

### Step 1 — Generate data with late events

The sample-data generator has a `--late-events` flag that backdates the
tail of the event list:

```bash
python resources/sample_data.py --output-dir ./sample_data --late-events 100
```

The generator stamps the last 100 events at 23:59 on the target date,
while their file position puts them at the end of the stream. That is
exactly the shape of a late-data problem: the element's *event time* is far
behind the *arrival order*.

```bash
# Show the last three lines and the timestamps
tail -3 ./sample_data/events.ndjson | python -c "
import json, sys
for line in sys.stdin:
    e = json.loads(line)
    print(e['event_id'], e['event_ts'], e['region'], e['value'])
"
```

### Step 2 — Run the default pipeline and observe the fallback

```bash
python project/streaming_pipeline.py \
    --input ./sample_data/events.ndjson \
    --output ./out/lateness_default \
    --window-seconds 3600
```

Watch for the warning on stderr:

```text
WARNING __main__: allowed_lateness=300s requires --allow_unsafe_triggers; falling back to 0s so the pipeline stays safe
```

That is the fallback from chapter 7.4 doing its job. The run succeeds, and
the effective allowed lateness is **0**.

```bash
cat ./out/lateness_default* | sort
```

```csv
region,event_count,total_value
AMER,5037,302651.93
APAC,4885,291314.62
EMEA,5099,302548.0
LATAM,4979,299522.51
```

### Step 3 — Ask for lateness without opting in

Make the request explicit and watch the guard fire:

```bash
python project/streaming_pipeline.py \
    --input ./sample_data/events.ndjson \
    --output ./out/lateness_guarded \
    --window-seconds 3600 \
    --allowed-lateness-seconds 900 \
    2>&1 | grep -i "falling back"
```

```text
WARNING __main__: allowed_lateness=900s requires --allow_unsafe_triggers; falling back to 0s so the pipeline stays safe
```

Still succeeds. Still falls back to 0.

### Step 4 — Opt in explicitly

Now pass the flag:

```bash
python project/streaming_pipeline.py \
    --input ./sample_data/events.ndjson \
    --output ./out/lateness_allowed \
    --window-seconds 3600 \
    --allowed-lateness-seconds 900 \
    --allow_unsafe_triggers \
    2>&1 | grep -iE "falling back|unsafe"
```

```text
WARNING apache_beam.transforms.core: GroupByKey: Unsafe trigger `AfterWatermark()` detected (reason: MAY_FINISH). This is being allowed because --allow_unsafe_triggers is set. This could lead to missing or incomplete groups.
```

Note what is **absent**: the "falling back" warning. The 900-second lateness
budget was honoured. And note the second warning — this time from Beam
itself, at the `GroupByKey` stage, telling you the trigger is not
provably safe.

The output is identical to Step 2:

```csv
region,event_count,total_value
AMER,5037,302651.93
APAC,4885,291314.62
EMEA,5099,302548.0
LATAM,4979,299522.51
```

### Step 5 — Why the numbers did not change

This is worth pausing on, because it is the sort of thing that erodes
confidence in a windowing pipeline.

The reason is that **a bounded file source is not a streaming source**.
When the runner finishes reading a bounded input, it advances the watermark
to `+inf`, which closes every window at once and makes every element
on-time. There is no "late" data in a batch run — the notion only exists
relative to a watermark that advances *incrementally*.

The late events are still in the totals, because in a batch run they
simply late elements in a batch run they arrive in time. They are counted
exactly once.

To actually observe late-data behaviour, you need a source whose watermark
advances incrementally while data continues to arrive. Step 6 builds that
scenario by hand.

### Step 6 — A deterministic late-data experiment

This is the experiment that makes `allowed_lateness` concrete. We want to
see, side by side, what happens to a late element when there is a lateness
budget and when there is not.

**A note on `TestStream` first.** It is tempting to reach for
`TestStream` here, because it lets you advance the watermark by hand. But
`TestStream` in the `DirectRunner` does not reliably reproduce a *true*
late arrival — an element that is genuinely delivered after the watermark
has already passed the window end. In practice it produces the same output
whether the lateness budget is 300 seconds or 0, which makes it useless for
demonstrating the very thing you want to demonstrate. Rather than show you
a result that does not reproduce, this step drives Beam's **trigger driver**
directly. That is the same machinery Beam's own `trigger_test.py` uses, and
it gives exact control over the input watermark.

Save this as `_run/late_demo.py`:

```python
"""Show what allowed_lateness actually does to a late element.

The DirectRunner's TestStream does not reproduce a true late arrival, so
this script drives the trigger driver directly -- the same mechanism Beam's
own trigger_test.py uses.

Usage:
    python _run/late_demo.py 300    # 300 seconds of allowed lateness
    python _run/late_demo.py 0      # no allowed lateness
"""

import sys

from apache_beam.runners.direct.clock import TestClock
from apache_beam.transforms.core import Windowing
from apache_beam.transforms.trigger import (
    AccumulationMode,
    AfterCount,
    AfterWatermark,
    GeneralTriggerDriver,
    InMemoryUnmergedState,
)
from apache_beam.transforms.window import FixedWindows, WindowFn
from apache_beam.utils.timestamp import Duration, Timestamp
from apache_beam.utils.windowed_value import WindowedValue

BASE = Timestamp(0)
WINDOW_FN = FixedWindows(100)


def _bundles(data, size):
    """Yield bundles of windowed values, the way the runner delivers them."""
    bundle = []
    for timestamp, element in data:
        windows = WINDOW_FN.assign(WindowFn.AssignContext(timestamp, element))
        bundle.append(WindowedValue(element, timestamp, windows))
        if len(bundle) == size:
            yield bundle
            bundle = []
    if bundle:
        yield bundle


def run(lateness: int) -> None:
    """Fire a window, then deliver a late element into it."""
    windowing = Windowing(
        WINDOW_FN,
        triggerfn=AfterWatermark(early=AfterCount(3), late=AfterCount(2)),
        accumulation_mode=AccumulationMode.DISCARDING,
        allowed_lateness=lateness,
    )
    driver = GeneralTriggerDriver(windowing, TestClock())
    state = InMemoryUnmergedState()

    # Nine on-time elements in the window [0, 100).
    on_time = zip(range(9), "abcdefghi")
    for bundle in _bundles(on_time, 2):
        for pane in driver.process_elements(
                state, bundle, BASE, BASE):
            print("on-time pane:", sorted(pane.value))

    # The watermark timer fires: the window is now closed.
    while state.timers:
        for window, (name, domain, timestamp, _) in state.get_and_clear_timers():
            for pane in driver.process_timer(
                    window, name, domain, timestamp, state, BASE):
                print("watermark pane:", sorted(pane.value))

    # The watermark has moved to 200 -- past the window end of 100.
    late = zip(range(5), "vwxyz")
    merged = False
    for bundle in _bundles(late, 2):
        for pane in driver.process_elements(
                state, bundle, BASE + Duration(seconds=200),
                BASE + Duration(seconds=200)):
            print("LATE pane:", sorted(pane.value))
            merged = True

    if merged:
        print("RESULT: late elements were MERGED into the closed window")
    else:
        print("RESULT: late elements were DROPPED (window expired)")


if __name__ == "__main__":
    run(int(sys.argv[1]) if len(sys.argv) > 1 else 300)
```

Run it twice.

With a 300-second lateness budget:

```bash
python _run/late_demo.py 300
```

```text
on-time pane: ['a', 'b', 'c', 'd']
on-time pane: ['e', 'f', 'g', 'h']
watermark pane: ['i']
LATE pane: ['v', 'w']
LATE pane: ['x', 'y']
RESULT: late elements were MERGED into the closed window
```

With no lateness budget at all:

```bash
python _run/late_demo.py 0
```

```text
on-time pane: ['a', 'b', 'c', 'd']
on-time pane: ['e', 'f', 'g', 'h']
watermark pane: ['i']
RESULT: late elements were DROPPED (window expired)
```

That is the whole point of `allowed_lateness`, made visible. The elements
`v`, `w`, `x`, `y`, `z` have timestamps inside the already-closed window.
With a budget they are re-opened and merged; without one they are silently
discarded and the totals are permanently wrong.

#### Why the elements were dropped — the exact rule

Beam does not decide this with a heuristic. In
`apache_beam/transforms/trigger.py`, the trigger driver assigns each
element to its windows like this:

```python
for wv in windowed_values:
    for window in wv.windows:
        # ignore expired windows
        if input_watermark > window.end + self.allowed_lateness:
            continue
        windows_to_elements[window].append((wv.value, wv.timestamp))
```

Read that condition as a sentence: **an element is discarded if the input
watermark has passed the window's end plus the allowed lateness.** In the
demo above the window ends at 100 and the watermark is at 200:

| `allowed_lateness` | Window expires at | Watermark (200) past expiry? | Outcome |
| --- | --- | --- | --- |
| 300 | 100 + 300 = 400 | No | Merged |
| 0 | 100 + 0 = 100 | Yes | Dropped |

Note the second row carefully. With `allowed_lateness=0` the window expires
the instant its end timestamp is reached, so **there is no grace period at
all** — not even one second. This is the single most common
misunderstanding about lateness: "zero lateness" does not mean "no
tolerance", it means "no tolerance whatsoever".

#### A wrinkle worth knowing: the `late=` sub-trigger

Notice the trigger in the demo is
`AfterWatermark(early=AfterCount(3), late=AfterCount(2))` and not a bare
`AfterWatermark()`. This is not decoration — it changes the behaviour.

A bare `AfterWatermark()` fires exactly once, when the watermark passes the
window end. When a late element then arrives, the driver accepts it back
into the window (because the lateness budget has not expired), but the
trigger has already fired and has no further firing rule, so **the merged
data is never emitted**. The late element is counted, but nobody sees it.

`AfterWatermark(late=AfterCount(2))` supplies the missing rule: a
sub-trigger that is evaluated *after* the window has closed. Late elements
accumulate against it, and each time it fires the merged contents are
emitted. That is where the two `LATE pane` lines above come from.

So if you want late data to actually reach your sink, you need **both**:

1. `allowed_lateness` large enough that the late element has not expired,
   **and**
2. a `late=` sub-trigger on `AfterWatermark` that fires after the window
   closes.

Forgetting the second is a subtle way to lose data silently, because the
pipeline runs, the elements are accepted, and the output is still wrong.

#### Why `TestStream` was not used

It is worth being explicit, because you may try this yourself and get
confused. `TestStream` is excellent for testing *watermark advancement* and
*trigger timing*, and it is the right tool for the vast majority of
windowing tests — including the project's own `TestWindowing` suite. But
the `DirectRunner`'s `TestStream` does not produce a genuine late arrival:
it tends to re-order or buffer elements such that the "late" element is
still treated as on-time, and the same output appears with and without a
lateness budget. When you need to assert on *late-data handling
specifically*, drive the trigger driver directly, as above, or use a real
streaming source such as Pub/Sub — which is exactly what chapter 7.7 does.


### Step 7 — The `AfterCount` alternative

```bash
python project/streaming_pipeline.py \
    --input ./sample_data/events.ndjson \
    --output ./out/lateness_count \
    --window-seconds 3600 \
    --trigger-count 1000 \
    --allow_unsafe_triggers \
    2>&1 | grep -i "unsafe"
```

```text
WARNING apache_beam.transforms.core: GroupByKey: Unsafe trigger `AfterCount(1000)` detected (reason: MAY_FINISH). This is being allowed because --allow_unsafe_triggers is set. This could lead to missing or incomplete groups.
```

With `AfterCount` the window fires every 1000 elements. With
`DISCARDING`, each firing emits only what arrived since the last firing —
the deltas, not the running total. A sink consuming this stream must sum
the deltas to get the total, and the last partial window is never emitted
at all.

### Step 8 — Inspect the effective windowing

To see exactly what Beam built, print the windowing of a PCollection:

```python
import apache_beam as beam
from apache_beam.transforms.window import FixedWindows
from apache_beam.transforms.trigger import AccumulationMode, AfterWatermark

with beam.Pipeline() as p:
    windowed = (
        p
        | "Create" >> beam.Create([1, 2, 3])
        | "Window"
        >> beam.WindowInto(
            FixedWindows(3600),
            trigger=AfterWatermark(),
            accumulation_mode=AccumulationMode.ACCUMULATING,
            allowed_lateness=300,
        )
    )
    print(windowed.windowing)
```

The output shows the trigger, the accumulation mode, the window function,
and the allowed lateness, all in one place.

---

## 🛠️ Common Errors and Fixes

### `ValueError: GroupByKey: Unsafe trigger: \`AfterWatermark()\` may lose data. Reason: MAY_FINISH. This can be overriden with the --allow_unsafe_triggers flag.`

Beam refuses a trigger it cannot prove safe. The trigger fires before the
window is provably complete.

Two legitimate fixes:

**Fix 1 — use the safe configuration** (recommended):

```python
beam.WindowInto(
    FixedWindows(3600),
    trigger=AfterWatermark(),
    accumulation_mode=AccumulationMode.ACCUMULATING,
    allowed_lateness=0,
)
```

**Fix 2 — acknowledge the risk** with the flag:

```bash
python project/streaming_pipeline.py --allow_unsafe_triggers ...
```

```python
options = PipelineOptions(["--allow_unsafe_triggers"])
options.view_as(TypeOptions).allow_unsafe_triggers = True
```

In the course project, the flag alone is not enough — the project also
checks for it before honouring `--allowed-lateness-seconds`. Without the
flag, it falls back to 0 with a warning.

### `ValueError: Unsafe trigger: \`AfterCount(100)\` may lose data. Reason: MAY_FINISH`

Same underlying issue, different trigger. `AfterCount` fires every N
elements regardless of whether more are coming, so it can never be proven
safe.

The course project's `--trigger-count N` path requires the flag:

```bash
python project/streaming_pipeline.py --trigger-count 1000 --allow_unsafe_triggers ...
```

### `WARNING: Unsafe trigger ... This could lead to missing or incomplete groups.`

This is the warning you get *after* passing `--allow_unsafe_triggers`. It
is not an error — the pipeline is running. It is Beam reminding you, every
time the `GroupByKey` is built, that you opted out of a guarantee.

If you see this and did not intend to, you passed the flag somewhere you
did not mean to. Check your command line.

### `ValueError: accumulation_mode must be provided for non-trivial triggers`

`AfterCount` and `AfterWatermark` need an explicit accumulation mode:

```python
accumulation_mode=AccumulationMode.ACCUMULATING
```

or

```python
accumulation_mode=AccumulationMode.DISCARDING
```

### The lateness was ignored and the numbers did not change

Two likely causes:

1. **You did not pass `--allow_unsafe_triggers`.** The project falls back
   to 0. Look for the "falling back" warning.
2. **Your source is bounded.** A file source advances the watermark to
   `+inf` at the end, so every element is on time and allowed lateness has
   nothing to act on. To observe late-data behaviour you need a source
   whose watermark advances *incrementally* while data keeps arriving — a
   real streaming source such as Pub/Sub, or the trigger-driver harness
   from the hands-on section above. Note that the `DirectRunner`'s
   `TestStream` does not reproduce a true late arrival, so it will show
   you the same numbers with and without a lateness budget.

### The output has duplicate rows for the same region

That is `ACCUMULATING` plus a non-zero lateness budget doing exactly what it
is supposed to do: the window fired once on time, and again when the late
data merged in. `WriteToText` appends; it does not replace.

Use a sink that can upsert, or switch to `DISCARDING`, or set the lateness
to zero.

### `panic in ElementManager.Bundles watermark evaluation goroutine`

The Prism runner (`--runner DirectRunner` in Beam 2.60+) does not support
the `AfterWatermark` trigger. Use the classic runner:

```bash
python project/streaming_pipeline.py --runner BundleBasedDirectRunner ...
```

The course project defaults to `BundleBasedDirectRunner` for exactly this
reason.

### `AttributeError: module 'apache_beam.transforms.combiners' has no attribute 'Sum'`

There is no `combiners.Sum`. A sum is the builtin `sum` function wrapped by
Beam:

```python
sums = keyed | "SumValues" >> beam.CombinePerKey(sum)
```

---

## 💡 Production Notes

- **Measure your actual lateness before you budget for it.** Publish
  events with both their event time and their arrival time, and histogram
  the difference. The 99th percentile of `arrival_time − event_time` is
  the lateness budget you actually need — not a round number someone
  guessed. Most clickstream pipelines need 30 seconds to 5 minutes;
  pipeline-generated data needs almost none.

- **The watermark stalling problem is silent.** There is no error, no
  metric, no alert. Your dashboard is just late. If you merge sources,
  put an explicit watermark-age metric on the job — in Dataflow this is the
  **Watermark Age** metric on the streaming stages — and alert on it. A
  watermark age that grows without bound is the single most common
  streaming pipeline incident.

- **Hold back the watermark per source, not globally.** The correct fix
  for a slow source is to give that source its own lag, not to stall the
  whole pipeline. Concretely: lag the clickstream source by 2 minutes and
  the reference source by 5 minutes; the merged watermark advances at the
  slower of the two, but at a *known* rate. Use
  `TimestampCombiner.OUTPUT_AT_EOW` on the merged window so the output
  timestamp reflects the window, not the slowest input.

- **Allowed lateness is a memory commitment.** Multiply it out before you
  deploy: a 1-hour window with 24 hours of lateness holds 25× the state.
  On Dataflow, watch the **Bundled Data Size** and **Worker Disk Usage**
  metrics. A job that is slow and then fails with a disk-exhausted error
  was almost always over-late.

- **Prefer a deterministic lateness policy to a "best effort" one.** If
  you allow lateness, make the sink idempotent and the replay deterministic.
  The combination "replay from Pub/Sub + allowed lateness + a non-idempotent
  sink" is how you get double-counted revenue.

- **Know your delivery guarantee.** Pub/Sub is at-least-once, so the same
  event can arrive twice. A windowed aggregation that counts events will
  count some of them twice. The project has a `dedup_key` helper in
  `project/transforms.py` precisely for this — derive the deduplication key
  from the payload's own identity (`event_id`), never from arrival time.
  Deduplicate *before* the window, not after.

- **`--allow_unsafe_triggers` belongs in a runbook, not in a habit.** In a
  production template it should be a deliberate, reviewed flag with a
  comment explaining which late-data risk you have accepted. A flag that
  nobody remembers adding is a flag nobody understands.

---

## 🔑 Key Takeaways

- A **watermark** is the pipeline's promise about how far event time has
  progressed; a window is late once the watermark passes its end timestamp.
- **Firing is not finishing.** With allowed lateness, a fired window stays
  open, retains its state, and can fire again. State is released only when
  the watermark passes `window_end + allowed_lateness`.
- `allowed_lateness` on `beam.WindowInto` is a **number of seconds**; a
  late element arriving inside the budget is **merged into the window**,
  and one arriving after is **dropped**.
- Beam refuses `AfterWatermark` with non-zero lateness because it cannot
  prove the fired result is final:
  `ValueError: GroupByKey: Unsafe trigger: \`AfterWatermark()\` may lose
  data. Reason: MAY_FINISH`.
- `--allow_unsafe_triggers` **only suppresses the error**; it changes no
  semantics and makes nothing safer.
- The course project detects the missing opt-in and **falls back to zero
  lateness with a warning** rather than failing.
- A merged PCollection's watermark is the **minimum** across its inputs,
  so one quiet source stalls every downstream window; fix it with a
  **per-source hold-back** and `TimestampCombiner.OUTPUT_AT_EOW`.
- Lateness has a **state cost**: a 1-hour window with 24 hours of lateness
  holds roughly 25× the live state.
- The rule: **zero lateness with `AfterWatermark` and `ACCUMULATING`, or
  `AfterCount` and accept the drop.**

---

## 📚 Practice Exercises

1. **Measure the actual lateness.** Write a script that reads
   `./sample_data/events.ndjson` and, for each event, computes the
   difference between its position in the file and its event timestamp.
   Produce a histogram of how many events are "late" by more than 60
   seconds. Based on the result, argue for a specific `--allowed-lateness-seconds`
   value for the course pipeline, and compute the live-state multiplier it
   implies for a 1-hour window.

2. **Prove the fallback.** Modify a *copy* of `project/streaming_pipeline.py`
   so that instead of falling back to zero lateness it raises a
   `ValueError`. Then run it three ways: with no flag, with
   `--allow_unsafe_triggers`, and with the flag but `--trigger-count 0`.
   Record the exact error message from the first run.

3. **Measure the difference between ACCUMULATING and DISCARDING with
   lateness.** Extend `_run/late_demo.py` so that it fires a window twice —
   once on time and once after a late element arrives — and run it with
   `AccumulationMode.ACCUMULATING` and then with
   `AccumulationMode.DISCARDING`. Report the exact count each mode emits
   and explain why they differ. (Use the trigger-driver harness rather than
   `TestStream`, which does not produce a true late arrival.) Then repeat
   the experiment with `allowed_lateness=0` and explain why the late
   elements vanish in that case, quoting the expiry rule from the driver.

4. **Count the state multiplier.** For a 1-hour fixed window with
   10,000 distinct keys per window, and an allowed lateness of 6 hours,
   calculate the number of live key-window accumulators at steady state.
   Then repeat for a 5-minute window with the same 6 hours of lateness.
   Explain why the second number is much larger even though the window is
   smaller.

5. **Design the hold-back.** You are merging a clickstream topic (peak 50,000
   events/second) with a product-catalog topic (one update every 30
   minutes). Propose a per-source lag for each, justify it, and state what
   the merged watermark will do in the 30 minutes between catalog updates.
   Explain what `TimestampCombiner.OUTPUT_AT_EOW` contributes.

6. **Design a sink for re-firing windows.** Your pipeline uses
   `AfterWatermark`, `ACCUMULATING`, and 10 minutes of allowed lateness, so
   a window can produce up to several rows. Design the BigQuery schema and
   write disposition that makes re-firing correct. Explain why
   `WriteToText` is the wrong sink here.

---

## 📖 Further Reading

- Apache Beam: Windowing — https://beam.apache.org/documentation/programming-guide/#windowing
- Apache Beam: Triggers — https://beam.apache.org/documentation/programming-guide/#triggers
- Apache Beam: WindowFn, Triggers, and Timestamps (the model reference) — https://beam.apache.org/documentation/model/a-beam-primer/#windowing
- Google Cloud Dataflow: Watermarks and late data — https://cloud.google.com/dataflow/docs/concepts/watermarks
- Google Cloud Dataflow: Optimizing watermarks in streaming pipelines — https://cloud.google.com/dataflow/docs/guides/streaming/optimizing-watermarks
- Apache Beam Python SDK: `WindowInto` API reference — https://beam.apache.org/releases/pydoc/current/apache_beam.transforms.core.html#apache_beam.transforms.core.WindowInto
