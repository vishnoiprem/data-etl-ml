# 7.4 — Triggers & Accumulation Modes

> **Section 7 · Streaming Pipelines · Lecture 7.4 · 6:30**

## 🎯 What you will learn

- What a trigger actually is: the rule for *when* a windowed aggregation emits
- The full trigger catalogue — `DefaultTrigger`, `AfterCount`, `AfterProcessingTime`, `AfterWatermark`, `Never`, `AfterAny`, `AfterAll`, `Repeatedly`
- `AccumulationMode.ACCUMULATING` vs `DISCARDING`, with the exact numbers from the course's tests
- The real `AfterCount` API — the `count=` keyword argument
- Why `AfterCount` and `AfterProcessingTime` are "unsafe" and need `--allow_unsafe_triggers`
- The `Never` trigger and final-output-at-pipeline-end behaviour
- The early/late firing composite pattern — `AfterWatermark(early=..., late=...)`
- The design question behind every trigger choice: *what does the consumer of this output actually need?*

---

## 🧠 Concept

### What a trigger is

A window says **which** elements are grouped together. A trigger says
**when** the result for that group is emitted.

Without a trigger, Beam uses the default: fire once, when the watermark
passes the end of the window. That is the behaviour you want for a daily
report — one number per day, correct, emitted when the day is over.

But a trigger lets you say more:

- Fire **early**, before the window closes, so a dashboard updates live.
- Fire **repeatedly**, so you get a running total.
- Fire on **count**, so you get results at a predictable cadence regardless
  of time.
- **Never** fire, and only emit at the very end.

Every trigger answers the same question with a different policy.

### The trigger catalogue

The public API is `apache_beam.transforms.trigger`, re-exported as
`beam.transforms.trigger`.

| Trigger | Fires when | Time domain | Safe? |
|---|---|---|---|
| `DefaultTrigger` | when the watermark passes the window end | event | yes |
| `AfterWatermark()` | when the watermark passes the window end | event | yes, if lateness is 0 |
| `AfterCount(n)` | after `n` elements have arrived in the window | — | **no** |
| `AfterProcessingTime(delay)` | `delay` after the first element arrives | processing | **no** |
| `AfterAny(*triggers)` | when *any* subtrigger fires | mixed | depends |
| `AfterAll(*triggers)` | when *all* subtriggers have fired | mixed | depends |
| `Repeatedly(trigger)` | whenever the subtrigger fires, forever | mixed | depends |
| `Never` | never — output only at the end of the pipeline | — | yes |

Note what is **not** in this list: `EarlyFirings` and `LateFirings` were
removed from Beam's Python API. The supported way to express early and
late firing is the `early` and `late` parameters of `AfterWatermark`:

```python
from apache_beam.transforms.trigger import AfterCount, AfterWatermark

trigger = AfterWatermark(
    early=AfterCount(100),
    late=AfterCount(1),
)
```

The `early` subtrigger fires speculatively while the window is still open.
The `late` subtrigger fires again when late data arrives after the
watermark has passed. This is the composite pattern, and it is covered in
detail below.

There is also `Never`. It is not exported under that name from
`apache_beam.transforms.trigger` — the class is the private `_Never` — but
it *is* reachable through the trigger factory, and it is what the
`DefaultTrigger`'s counterpart behaviour is built on. In practice, for
Python, you reach "never fire" by using a trigger that has no firing
condition, and the pipeline's final output is produced when the runner
drains the pending state at the end.

### `DefaultTrigger` and `AfterWatermark`

`DefaultTrigger` is what you get if you do not specify one. The Beam
source describes it exactly:

> Semantically `Repeatedly(AfterWatermark())`, but more optimized.

So `DefaultTrigger` is `AfterWatermark` in a form the runner can optimise.
You will see `DefaultTrigger` in job graphs even when you never named it.

`AfterWatermark` fires when the watermark passes the window's end. The
watermark is Beam's estimate of how far through event time the stream has
progressed (chapter 7.2), so `AfterWatermark` means "fire when Beam is
confident no more on-time data for this window will arrive."

The subtlety that drives most of this chapter: **once you allow late
data, `AfterWatermark` is no longer the last firing.** A late element
arrives, it updates the window, and the window fires again. So
`AfterWatermark` combined with non-zero allowed lateness is an **unsafe**
trigger, and Beam refuses it by default.

### `AfterCount` — the API

The signature is:

```text
AfterCount(count)
```

`count` is a **positional-or-keyword** parameter. The course's
`streaming_pipeline.py` uses the keyword form:

```python
trigger = AfterCount(count=trigger_count)
```

Both work; the keyword form is clearer, because `AfterCount(2)` at a call
site is easy to misread as a window size.

`AfterCount(n)` fires the window's aggregation every time `n` **new**
elements have arrived in it. Note "new" — the count is of elements since
the last firing, not since the window opened. (Whether the *output* is a
running total or a delta is the accumulation mode's business, covered
below.)

The count is **per key, per window**. A window with three regions'
worth of events accumulates three separate counters, each firing when it
reaches `n`.

`AfterCount` is **never safe**, and Beam says so. The reason is structural:
the trigger fires on a condition that has nothing to do with whether more
data is coming. A window can close with elements still in flight, and the
trigger will have fired before those elements arrived. Beam's error
message names the reason:

```text
ValueError: GroupByKey: Unsafe trigger: `AfterCount(2)` may lose data. Reason: MAY_FINISH. This can be overriden with the --allow_unsafe_triggers flag.
```

`MAY_FINISH` means: this trigger can fire while the window still has
pending data, and it may never fire again for elements that arrive
afterwards.

### `AfterProcessingTime`

`AfterProcessingTime(delay=0)` fires `delay` seconds of **processing
time** after the first element for the window arrives.

This is the trigger to reach for when you want results promptly regardless
of how the event-time stream is progressing — for example, a
"give me the current total every minute" behaviour on a sparse stream
where the watermark would otherwise stall.

It is also **unsafe**, for the same structural reason as `AfterCount`: it
fires on a wall-clock condition, so it can fire while elements are still
in flight.

And it has a second, subtler problem: it is **not reproducible**. Two
runs of the same data produce different numbers of firings, because
processing time is not deterministic. If you need reproducibility, do not
use `AfterProcessingTime`.

### The unsafe triggers and `--allow_unsafe_triggers`

Beam's safety rule, stated precisely:

> A trigger is **safe** only if it can never fire while more elements for
> the window are still in flight.

That holds for `AfterWatermark` **only when allowed lateness is zero**.
Once you allow late data, a window can be updated after it fires, so the
trigger becomes unsafe.

`AfterCount` and `AfterProcessingTime` are never safe.

When you use one, Beam raises the `ValueError` above and refuses to run.
You can override it with `--allow_unsafe_triggers`:

```bash
python project/streaming_pipeline.py --trigger-count 100 --allow_unsafe_triggers
```

But understand what you are accepting. The flag means: *"I know this
trigger may fire while data is in flight, and I accept that the output
may be incomplete or may need correction."* It is not a performance knob.
It is a correctness waiver.

The course's `streaming_pipeline.py` encodes the safe default explicitly:

```python
unsafe = bool(getattr(options, "allow_unsafe_triggers", False)) if options else False

if trigger_count:
    trigger = AfterCount(count=trigger_count)
    accumulation_mode = AccumulationMode.DISCARDING
else:
    trigger = AfterWatermark()
    accumulation_mode = AccumulationMode.ACCUMULATING
```

and then falls back to zero lateness when the caller has not opted in:

```python
effective_lateness = allowed_lateness_seconds
if effective_lateness and not unsafe:
    log.warning(
        "allowed_lateness=%ds requires --allow_unsafe_triggers; "
        "falling back to 0s so the pipeline stays safe",
        effective_lateness,
    )
    effective_lateness = 0
```

That is the right shape: **default to safe, and make the caller ask
explicitly for the unsafe path.**

### `Never` and final output at pipeline end

`Never` is a trigger that does not fire. Its docstring in the Beam
source is precise about what it does:

> No potential data loss. Though Never doesn't explicitly trigger, it
> still collects data on windowing closing.

So with a `Never` trigger, the window's state is still collected, and the
output is produced when the runner **drains the pending state at the end
of the pipeline**. In a batch job, that is when the input is exhausted. In
a streaming job, that is when you cancel it — which makes `Never` a poor
choice for a streaming pipeline, since it means you get *no* output until
the job stops.

For a batch pipeline, `Never` is a way to say "one complete aggregate at
the end, no intermediate results." It is rarely necessary — the default
trigger gives you that for free — but it is useful when you want to be
explicit that no speculative output should be produced.

In Python, the class is not exported under the public name `Never` from
`apache_beam.transforms.trigger`; it is the private `_Never`, reachable
through the trigger factory:

```python
from apache_beam.transforms.trigger import TriggerFn
```

The practical guidance is: **in Python, reach the "fire only at the end"
behaviour by using the default trigger in a batch pipeline.** The
explicit `Never` trigger is a Java-first API.

### `AfterAny`, `AfterAll`, and `Repeatedly`

**`AfterAny(*triggers)`** fires when *any* of its subtriggers fires. Its
docstring:

> Fires when any subtrigger fires. Also finishes when any subtrigger
> finishes.

**`AfterAll(*triggers)`** fires when *all* of its subtriggers have fired:

> Fires when all subtriggers have fired. Also finishes when all
> subtriggers have finished.

The difference shows up in a composite: `AfterAny(AfterCount(10),
AfterProcessingTime(60))` fires as soon as *either* 10 elements have
arrived *or* 60 seconds of processing time have passed. `AfterAll` waits
for both — which is a stricter condition, and therefore usually safer.

**`Repeatedly(trigger)`** re-arms the subtrigger after every firing:

> Repeatedly invoke the given trigger, never finishing.

So `Repeatedly(AfterCount(1))` fires after every single element — an
output per element. Combined with `AfterWatermark`, it produces the
speculative-plus-final pattern that `DefaultTrigger` optimises.

Both `AfterAny` and `AfterAll` are how you build the early/late composite
in the general case. `AfterWatermark(early=..., late=...)` is the
specialised, optimised form.

### The early/late firing composite

This is the pattern that lets you have both a live-updating dashboard and
a final, correct answer.

```python
from apache_beam.transforms.trigger import AfterCount, AfterWatermark

trigger = AfterWatermark(
    early=AfterCount(100),   # fire every 100 elements, speculatively
    late=AfterCount(1),      # fire again whenever late data arrives
)
```

Three phases:

1. **Early.** As elements arrive, the `early` subtrigger fires the
   aggregation every 100 elements. The result is a *partial* count — the
   window is still open and more elements are coming. This is what makes
   a live dashboard move.

2. **On time.** When the watermark passes the window's end, the trigger
   fires once more with the complete on-time result.

3. **Late.** If an element arrives after the watermark passed, the `late`
   subtrigger fires again with the corrected total.

The accumulation mode determines what each of those firings *contains*,
which is the subject of the next section.

Note the semantics of the `late` subtrigger: `AfterCount(1)` means "fire
again as soon as one late element arrives." `AfterCount(1)` is what you
want if you want the corrected total promptly. A larger count would
batch the corrections.

There is a cost to all of this. The early firings mean the window's
state is retained and re-emitted many times, and the late firings mean
the state is retained past the watermark. Both are memory and I/O
costs, paid on every checkpoint.

### `AccumulationMode` — the two modes

This is the single most important knob once you have a trigger that fires
more than once.

The question it answers: **does a firing contain the window's running
total, or only what has arrived since the last firing?**

| Mode | Each firing contains | Use for |
|---|---|---|
| `ACCUMULATING` | the **running total** for the window | dashboards showing a total |
| `DISCARDING` | the **delta** since the last firing | alerting on changes, event sinks |

The API:

```python
from apache_beam.transforms.trigger import AccumulationMode

beam.WindowInto(
    FixedWindows(3600),
    trigger=AfterCount(2),
    accumulation_mode=AccumulationMode.ACCUMULATING,
)
```

`ACCUMULATING` is the default when you do not specify one.

### The exact numbers

This is the part worth memorising, because it is concrete. Take a window
that receives **5 elements**, with a trigger of `AfterCount(2)`.

The trigger's contract is: fire when the window's element count reaches
`2`. Beam's source says it precisely:

> Fire when there are at least count elements in this window pane.

So the trigger fires after the 2nd element, after the 4th, and after the
5th (the last element satisfies the remaining remainder). Three firings.

| Firing | Elements seen so far | `ACCUMULATING` | `DISCARDING` |
|---|---|---|---|
| 1 | 2 | **2** | **2** |
| 2 | 4 | **4** | **2** |
| 3 | 5 | **5** | **1** |
| | | running totals | deltas |

- **ACCUMULATING** emits `2, 4, 5` — the running total.
- **DISCARDING** emits `2, 2, 1` — the deltas.

These are the expectations encoded in the course's test suite:

```python
def test_accumulating_mode_emits_running_total(self):
    """ACCUMULATING emits the window total each time it fires."""
    events = [(f"2026-01-15T10:0{i}:00+00:00", 1.0) for i in range(5)]

    with TestPipeline(options=beam_test_options()) as pipeline:
        result = (
            pipeline
            | "Create" >> beam.Create(events)
            | "WithTimestamps" >> beam.Map(
                lambda pair: (
                    beam.window.Timestamp(
                        _to_epoch(pair[0])
                    ),
                    pair[1],
                )
            )
            | "Window" >> beam.WindowInto(
                FixedWindows(3600),
                trigger=AfterCount(2),
                accumulation_mode=AccumulationMode.ACCUMULATING,
            )
            | "KeyByRegion" >> beam.Map(lambda pair: ("all", pair[1]))
            | "Count" >> beam.combiners.Count.PerKey()
        )
        # With accumulation, the counts are 2, 4, 5 — the running
        # total — rather than the deltas 2, 2, 1.
        assert_that(
            result,
            _windowed_values([("all", 2), ("all", 4), ("all", 5)]),
            use_global_window=False,
        )
```

and:

```python
def test_discarding_mode_emits_deltas(self):
    """DISCARDING emits only what arrived since the last firing."""
    events = [(f"2026-01-15T10:0{i}:00+00:00", 1.0) for i in range(5)]

    with TestPipeline(options=beam_test_options()) as pipeline:
        result = (
            pipeline
            | "Create" >> beam.Create(events)
            | "WithTimestamps" >> beam.Map(
                lambda pair: (
                    beam.window.Timestamp(_to_epoch(pair[0])),
                    pair[1],
                )
            )
            | "Window" >> beam.WindowInto(
                FixedWindows(3600),
                trigger=AfterCount(2),
                accumulation_mode=AccumulationMode.DISCARDING,
            )
            | "KeyByRegion" >> beam.Map(lambda pair: ("all", pair[1]))
            | "Count" >> beam.combiners.Count.PerKey()
        )
        # With discarding, the counts are the deltas 2, 2, 1.
        assert_that(
            result,
            _windowed_values([("all", 2), ("all", 2), ("all", 1)]),
            use_global_window=False,
        )
```

Two consequences follow from these numbers, and both matter in practice.

**First, the two modes are not interchangeable — they are different
datasets.** `2, 4, 5` and `2, 2, 1` contain the same information
(the total is 5, and the deltas sum to 5), but they are different
*shapes*. A consumer that sums the ACCUMULATING stream gets 11; a
consumer that sums the DISCARDING stream gets 5.

**Second, the sum of the DISCARDING stream equals the total, and the
last element of the ACCUMULATING stream equals the total.** So if you
want "the total for the window" as a single number, take the last
ACCUMULATING value, or sum the DISCARDING values. Do not sum the
ACCUMULATING values — you will over-count by roughly the square of the
number of firings.

### What the Direct Runner actually does

Here is a subtlety worth knowing before you try to reproduce those numbers
locally, because it will save you an hour of confusion.

**The `2, 4, 5` and `2, 2, 1` sequences describe the trigger's contract.
The Direct Runner does not produce them.**

The Direct Runner (`BundleBasedDirectRunner`) processes the input in
bundles. All five elements arrive in a single bundle, and the trigger's
`should_fire` check happens at bundle boundaries — not after every
element. So the window fires **once**, at the end of the bundle, with
the final value.

You can see this directly. The `PaneInfo` of the single output element
says so:

```text
TestWindowedValue(
    value=('all', 5),
    timestamp=Timestamp(...),
    windows=[[...]],
    pane_info=PaneInfo(first: True, last: True, timing: EARLY, index: 0, ...),
)
```

`first: True, last: True` means exactly one pane — one firing. And the
value is `('all', 5)` in **both** accumulation modes, because with a
single firing there is no difference between "the total" and "the delta
since the last firing"; they are the same number.

This is not a bug in the runner. It is a difference in **execution
model**. The multiple-firing behaviour is a property of a *streaming*
runner, where the trigger is evaluated as elements stream in and bundles
are small. The Dataflow runner does produce the intermediate firings.

The practical consequence for this chapter: **you cannot fully verify
trigger firing behaviour on the Direct Runner.** The course's
`streaming_pipeline.py` is right to make the unsafe path opt-in, and the
right way to validate a trigger's firing behaviour is to run it on
Dataflow and inspect the output.

The same caveat applies to the course's test helper. `assert_that` with a
plain function matcher runs the matcher but **does not check its return
value** — `assert_that` wires the matcher in with a plain `Map`. The
course's `_windowed_values` helper is therefore not enforcing its
assertion on the Direct Runner. If you write your own trigger tests,
either use `equal_to(...)` (a real matcher class) or assert explicitly
inside a `ParDo` that raises on mismatch.

### The trigger design question

Everything above is mechanism. The mechanism is only half the work. The
real question is:

> **What does the consumer of this output actually need?**

Two consumers, two correct answers:

**A dashboard showing "orders so far today".** It wants the **running
total**, updated frequently. Every time it reads, it wants the current
total, not an increment. → `ACCUMULATING`, with an early trigger so it
updates live.

```text
ACCUMULATING, AfterCount(100)
   →  100, 200, 300, 450, 600
      the dashboard just overwrites the value each time
```

**An alerting system watching for spikes.** It wants the **delta**, so it
can compare the last N minutes against the previous N minutes. If it
received running totals, it would have to subtract consecutive values
itself — and any missed firing would corrupt its state permanently.

```text
DISCARDING, AfterCount(100)
   →  100, 100, 100, 150, 150
      the alerter adds each delta to its own counter
```

A third consumer wants something else again: **a daily report that must
be correct**. It wants exactly one firing, at the end, with the complete
total. → the default trigger, `AfterWatermark`, with `ACCUMULATING`, and
zero allowed lateness.

The mistake is to pick a trigger first and then look for a consumer that
wants it. Pick the consumer first. The trigger and the accumulation mode
follow.

A useful way to think about it:

| Question | Consumer type | Trigger | Mode |
|---|---|---|---|
| "What is the total right now?" | dashboard | early firing | `ACCUMULATING` |
| "How much changed since last time?" | alerting | early firing | `DISCARDING` |
| "What was the total for the day?" | report | default (`AfterWatermark`) | `ACCUMULATING` |
| "What happened after I already reported?" | correction-tolerant | default + allowed lateness | `ACCUMULATING` |

### The full configuration, in one place

Here is the shape of a fully-specified windowing configuration:

```python
from apache_beam.transforms.window import FixedWindows
from apache_beam.transforms.trigger import (
    AccumulationMode,
    AfterCount,
    AfterWatermark,
)

windowed = parsed | "ApplyWindow" >> beam.WindowInto(
    FixedWindows(size=3600),           # the partition
    trigger=AfterWatermark(            # when to fire
        early=AfterCount(100),         # speculative, while open
        late=AfterCount(1),            # again, on late data
    ),
    accumulation_mode=AccumulationMode.ACCUMULATING,  # what a firing contains
    allowed_lateness=300,              # how long late data is accepted
)
```

Every one of those four choices is independent, and each answers a
different question. The course's `streaming_pipeline.py` uses the simpler
form and picks between two complete configurations based on whether the
caller asked for an unsafe trigger:

| | Safe path | Unsafe path |
|---|---|---|
| Trigger | `AfterWatermark()` | `AfterCount(count=n)` |
| Accumulation | `ACCUMULATING` | `DISCARDING` |
| Allowed lateness | 0 (enforced) | as requested |
| Flag | none | `--allow_unsafe_triggers` |

---

## 🛠️ Hands-On

The exercise runs the same aggregation in both accumulation modes and shows
the different output.

### Step 1 — Generate the sample data

```bash
cd data-engineering/data-Course/google/Dataflow
export PYTHONPATH="$PWD/project"
python resources/sample_data.py --output-dir ./sample_data
```

### Step 2 — The two modes side by side

```bash
python -c "
import apache_beam as beam
from beam_options import build_options
from apache_beam.transforms.window import FixedWindows
from apache_beam.transforms.trigger import AfterCount, AccumulationMode
from apache_beam.utils.timestamp import Timestamp
from transforms import parse_timestamp


def to_timestamp(ts):
    epoch = float(parse_timestamp(ts).timestamp())
    return beam.window.TimestampedValue(1.0, Timestamp(epoch))


events = [(f'2026-01-15T10:0{i}:00+00:00', 1.0) for i in range(5)]

for mode, label in [
    (AccumulationMode.ACCUMULATING, 'accumulating'),
    (AccumulationMode.DISCARDING, 'discarding'),
]:
    with beam.Pipeline(options=build_options(['--allow_unsafe_triggers'])) as p:
        (
            p
            | 'Create' >> beam.Create(events)
            | 'Stamp' >> beam.Map(lambda pair: to_timestamp(pair[0]))
            | 'Window' >> beam.WindowInto(
                FixedWindows(3600),
                trigger=AfterCount(count=2),
                accumulation_mode=mode,
            )
            | 'Key' >> beam.Map(lambda value: ('all', value))
            | 'Count' >> beam.combiners.Count.PerKey()
            | 'Format' >> beam.Map(lambda kv: f'{kv[0]},{kv[1]}')
            | 'Write' >> beam.io.WriteToText(
                f'./out/trigger_{label}',
                num_shards=1,
                shard_name_template='',
            )
        )
" 2>&1 | grep -v "INFO\|WARNING"

echo "ACCUMULATING:"
cat out/trigger_accumulating
echo "DISCARDING:"
cat out/trigger_discarding
```

Expected output:

```text
ACCUMULATING:
all,5
DISCARDING:
all,5
```

**Both modes produce `all,5`.** That surprises people, and it is worth
understanding why rather than shrugging at it.

The Direct Runner reads all five elements in a single bundle. The trigger
is evaluated at *bundle boundaries*, not after every element, so the
window fires **once** — with the final value. With a single firing there
is no difference between "the total so far" and "the delta since the
last firing"; they are the same number.

The `2, 4, 5` and `2, 2, 1` sequences are what the trigger *contract*
says, and what a streaming runner such as Dataflow produces, where
bundles are small and the trigger is evaluated as elements stream in.

You can confirm the single firing for yourself with `PaneInfo`.
`assert_that(..., reify_windows=True)` reports each element's pane info,
and `first: True, last: True` confirms that only one pane was emitted:

```python
from apache_beam.testing.util import assert_that
```

So the honest summary for this step is: **the accumulation mode only
matters once a window fires more than once, and the Direct Runner does
not produce multiple firings.** To see the modes differ, run the same
pipeline on Dataflow, where the trigger is evaluated per element rather
than per bundle.

The takeaway is not "the modes are the same". The takeaway is that **you
cannot verify trigger firing behaviour on the Direct Runner** — and a
course that claims otherwise is teaching you something you will later
find out was never true.

### Step 3 — See the unsafe-trigger error

Remove the flag and run it again:

```bash
python -c "
import apache_beam as beam
from beam_options import build_options
from apache_beam.transforms.window import FixedWindows
from apache_beam.transforms.trigger import AfterCount, AccumulationMode
from apache_beam.utils.timestamp import Timestamp
from transforms import parse_timestamp


def to_timestamp(ts):
    epoch = float(parse_timestamp(ts).timestamp())
    return beam.window.TimestampedValue(1.0, Timestamp(epoch))


events = [(f'2026-01-15T10:0{i}:00+00:00', 1.0) for i in range(5)]

with beam.Pipeline(options=build_options([])) as p:
    (
        p
        | 'Create' >> beam.Create(events)
        | 'Stamp' >> beam.Map(lambda pair: to_timestamp(pair[0]))
        | 'Window' >> beam.WindowInto(
            FixedWindows(3600),
            trigger=AfterCount(count=2),
            accumulation_mode=AccumulationMode.ACCUMULATING,
        )
        | 'Key' >> beam.Map(lambda value: ('all', value))
        | 'Count' >> beam.combiners.Count.PerKey()
        | 'Format' >> beam.Map(lambda kv: f'{kv[0]},{kv[1]}')
        | 'Write' >> beam.io.WriteToText(
            './out/trigger_unsafe', num_shards=1, shard_name_template=''
        )
    )
" 2>&1 | tail -5
```

The job fails at graph construction:

```text
ValueError: GroupByKey: Unsafe trigger: `AfterCount(2)` may lose data. Reason: MAY_FINISH. This can be overriden with the --allow_unsafe_triggers flag.
```

Note that this happens **before any data is read**. Beam validates the
trigger against the windowing configuration when it builds the graph, so
you find out in seconds rather than hours into a job.

### Step 4 — The safe path, and the fallback

Now use the course pipeline's default (safe) path:

```bash
python project/streaming_pipeline.py \
    --input ./sample_data/events.ndjson \
    --output ./out/trigger_safe \
    --window-seconds 3600 \
    --allowed-lateness-seconds 300
```

The warning tells you what happened:

```text
allowed_lateness=300s requires --allow_unsafe_triggers; falling back to 0s so the pipeline stays safe
```

The pipeline refused to run an unsafe configuration and degraded to a
safe one instead of failing outright. It uses `AfterWatermark()` with
`ACCUMULATING`, and the window's total is emitted once, when the window
closes.

### Step 5 — Opt into the unsafe path explicitly

```bash
python project/streaming_pipeline.py \
    --input ./sample_data/events.ndjson \
    --output ./out/trigger_unsafe_ok \
    --window-seconds 3600 \
    --trigger-count 100 \
    --allow_unsafe_triggers
```

Now the trigger is `AfterCount(count=100)` with `DISCARDING`, and the
allowed lateness is honoured rather than zeroed.

### Step 6 — Early and late firings

The composite pattern. This pipeline fires speculatively every 100
elements while the window is open, and again whenever late data arrives:

```bash
python -c "
import apache_beam as beam
from beam_options import build_options
from apache_beam.transforms.window import FixedWindows
from apache_beam.transforms.trigger import AfterCount, AfterWatermark, AccumulationMode
from apache_beam.utils.timestamp import Timestamp
from transforms import parse_timestamp


def to_timestamp(ts):
    epoch = float(parse_timestamp(ts).timestamp())
    return beam.window.TimestampedValue(1.0, Timestamp(epoch))


events = [(f'2026-01-15T10:0{i}:00+00:00', 1.0) for i in range(5)]

with beam.Pipeline(options=build_options(['--allow_unsafe_triggers'])) as p:
    (
        p
        | 'Create' >> beam.Create(events)
        | 'Stamp' >> beam.Map(lambda pair: to_timestamp(pair[0]))
        | 'Window' >> beam.WindowInto(
            FixedWindows(3600),
            trigger=AfterWatermark(
                early=AfterCount(count=2),
                late=AfterCount(count=1),
            ),
            accumulation_mode=AccumulationMode.ACCUMULATING,
        )
        | 'Key' >> beam.Map(lambda value: ('all', value))
        | 'Count' >> beam.combiners.Count.PerKey()
        | 'Format' >> beam.Map(lambda kv: f'{kv[0]},{kv[1]}')
        | 'Write' >> beam.io.WriteToText(
            './out/trigger_early_late',
            num_shards=1,
            shard_name_template='',
        )
    )
" 2>&1 | grep -v "INFO\|WARNING"

cat out/trigger_early_late
```

On the Direct Runner you will see a single `all,5` — the same
bundle-boundary behaviour as step 2. On Dataflow, where the trigger is
evaluated per element, you will see the early speculative firings (2, 4)
followed by the final on-time firing (5). The `late` subtrigger does not
fire in either case, because no late data arrived — the sample events are
all on time.

The value of this exercise is mostly in the **configuration**, not the
output: it shows the exact shape of the composite trigger, and it is the
form you will write in production.

### Step 7 — Run the tests

The course's test suite encodes the trigger expectations:

```bash
python3 -m pytest project/tests/test_pipelines.py::TestWindowing -v
```

```text
project/tests/test_pipelines.py::TestWindowing::test_fixed_window_groups_by_time PASSED
project/tests/test_pipelines.py::TestWindowing::test_accumulating_mode_emits_running_total PASSED
project/tests/test_pipelines.py::TestWindowing::test_discarding_mode_emits_deltas PASSED
```

Run them, and they pass. But read the "What the Direct Runner actually
does" section above before you trust them: on the Direct Runner these
tests pass whether or not the accumulation mode is set correctly,
because the runner emits a single firing and the test helper's matcher
return value is not enforced.

**A test that passes for the wrong reason is worse than no test**, because
it gives you false confidence about the part of your pipeline that is
hardest to get right. If you rely on trigger semantics, verify them on
Dataflow.

---

## 🛠️ Common Errors and Fixes

### `ValueError: GroupByKey: Unsafe trigger: `AfterCount(2)` may lose data. Reason: MAY_FINISH. This can be overriden with the --allow_unsafe_triggers flag.`

You used `AfterCount` (or `AfterProcessingTime`, or a non-zero allowed
lateness with a watermark trigger) without opting in.

Three ways to fix it, in order of preference:

1. **Use the default trigger.** `AfterWatermark()` with zero allowed
   lateness is safe, and it is correct for a "one result per window"
   requirement.
2. **Use `AfterWatermark(early=..., late=...)`** for speculative output.
   This is the safe way to get early firings, and it is the right answer
   for a live dashboard.
3. **Pass `--allow_unsafe_triggers`** if you genuinely need
   `AfterCount` — and understand that you are accepting incomplete or
   correctable output.

### `TypeError: AfterCount.__init__() missing 1 required positional argument: 'count'`

You called `AfterCount()` with no argument.

```python
# wrong
AfterCount()

# right
AfterCount(count=100)
```

Note `count` is required. There is no sensible default.

### `AttributeError: module 'apache_beam.transforms.trigger' has no attribute 'EarlyFirings'`

`EarlyFirings` and `LateFirings` were removed from Beam's Python API.
Use the `early` and `late` parameters of `AfterWatermark`:

```python
# removed
beam.WindowInto(FixedWindows(3600), trigger=EarlyFirings(AfterCount(100)))

# current
beam.WindowInto(
    FixedWindows(3600),
    trigger=AfterWatermark(early=AfterCount(count=100)),
)
```

### `AttributeError: module 'apache_beam.transforms.trigger' has no attribute 'Never'`

The class exists but is private (`_Never`) and is not exported under the
public name. In Python, get the "output only at the end" behaviour from
the default trigger in a batch pipeline, which is what you want anyway.

### The output has more rows than expected

You are firing more than once per window. Check the trigger:

- `AfterCount(n)` fires every `n` elements.
- `AfterWatermark(early=...)` fires speculatively as well as finally.
- `Repeatedly(trigger)` fires every time the subtrigger fires, forever.

For exactly one output per window, use the default trigger with no
`early` subtrigger.

### The output has fewer rows than expected

Check the accumulation mode. `DISCARDING` emits the delta since the last
firing — if you are summing those deltas expecting a total, you get the
total, but if you are reading each row as "the total so far", the numbers
look too small.

Also check the **key**. The count is per key *per window*. If your key
changes between firings — for example, if you are keying by something
that includes the firing count — each firing is a different key and you
get one row each.

### The dashboard shows a number that goes down

You are using `ACCUMULATING` but the pipeline is emitting **per-key**
values that you are summing across keys incorrectly, or the key is not
stable. With `ACCUMULATING`, each firing for a key contains that key's
running total. Summing those across firings double-counts.

The fix is to take the **last** value per key per window, not the sum.

### The output is not reproducible between runs

`AfterProcessingTime` is defined in terms of processing time, which is
not deterministic. Two runs of the same data fire it a different number
of times.

```python
# not reproducible
trigger=AfterProcessingTime(delay=60)

# reproducible
trigger=AfterCount(count=100)
```

If reproducibility matters, use only event-time-domain triggers:
`AfterWatermark`, `AfterCount`.

### `RuntimeError: Transform name is already used`

Two transforms with the same label in one pipeline. In a loop that runs
the same pipeline twice, give each run a distinct label:

```text
for label in ("accumulating", "discarding"):
    (
        p
        | f"Create{label}" >> beam.Create(events)
        ...
    )
```

### The late data is not reflected in the output

The trigger fired and the window was closed before the late element
arrived, and no late firing was configured. Three things must all be
true:

1. `allowed_lateness` is non-zero.
2. The trigger has a `late` subtrigger — or you are using a trigger that
   re-fires on late data.
3. The unsafe-trigger override is in place, because non-zero lateness
   makes the trigger unsafe.

If all three hold, a late element updates the window and fires it again
with the corrected total.

---

## 💡 Production Notes

- **Design the trigger from the consumer, not from the data.** The
  single most valuable question in streaming is *"what does the consumer
  of this output actually need?"* A dashboard wants the running total; an
  alerting system wants deltas; a daily report wants one final number.
  These are three different trigger and accumulation configurations, and
  picking the wrong one produces a pipeline that is subtly wrong rather
  than visibly broken.
- **Treat `--allow_unsafe_triggers` as a correctness waiver, not a
  performance knob.** It means "I accept that the output may be
  incomplete or may need correction." Every use of it should be a
  deliberate decision with a named owner, and the comment in the code
  should say why.
- **`AfterCount` is the right trigger for throughput-shaped data and the
  wrong one for correctness-shaped data.** If you need every element
  counted exactly once in exactly one output row, `AfterCount` can give
  you a partial result that you must later correct. `AfterWatermark`
  with zero lateness gives you one correct result.
- **`AfterProcessingTime` is a last resort.** It is not reproducible, it
  depends on machine speed, and it makes the number of firings vary
  between runs. Use it only when the alternative is no output at all —
  a sparse stream whose watermark never advances.
- **Early firings cost you three things:** extra output volume, extra
  checkpoint I/O, and state retained longer. A dashboard that updates
  every 100 elements on a high-volume stream is generating a lot of
  writes. Measure the output rate before you enable it.
- **The `late` subtrigger is how you deliver corrections.** If your
  consumers can handle "the number changed", the late firing gives them
  the corrected value with a timestamp. If they cannot, you need a
  downstream reconciliation step instead — which is more work, but
  sometimes necessary.
- **Prefer `ACCUMULATING` when in doubt.** It is the default, it is
  self-describing (each row is a total, not an increment), and a
  consumer that reads the last row gets the right answer. `DISCARDING`
  requires the consumer to understand that it must accumulate.
- **Never sum an ACCUMULATING stream.** The sums over-count. If you need
  a total across firings, use `DISCARDING`, or take the last value.
- **Alert on the number of firings.** A sudden change in how often a
  window fires is a leading indicator of a data-volume change or a
  problem with a producer. This is a metric most pipelines do not have,
  and it is cheap to add.
- **A "safe" trigger that fires zero times is a silent failure.** If the
  watermark never advances — which happens with an idle source — a
  watermark trigger produces nothing at all. Configure an idle-source
  strategy, or use a count trigger as a heartbeat, so you notice.
- **Document the trigger and accumulation mode in the pipeline's
  docstring.** Six months later, the difference between "2, 4, 5" and
  "2, 2, 1" is not obvious from the output. The course's
  `streaming_pipeline.py` does this well — its comments explain the
  safety reasoning, not just the mechanics.

---

## 🔑 Key Takeaways

- A **window** says which elements are grouped; a **trigger** says **when**
  the group is emitted. They are independent choices.
- The catalogue is `DefaultTrigger`, `AfterWatermark`, `AfterCount`,
  `AfterProcessingTime`, `AfterAny`, `AfterAll`, `Repeatedly`, and
  `Never`. `EarlyFirings` and `LateFirings` were **removed** — use
  `AfterWatermark(early=..., late=...)`.
- `AfterCount(count=n)` fires every `n` elements per key per window, and
  is **never safe**: it can fire while elements are still in flight.
- `AfterProcessingTime(delay)` fires on wall-clock time. It is unsafe
  *and* not reproducible.
- A trigger is safe only if it cannot fire while elements are in flight.
  `AfterWatermark` is safe **only with zero allowed lateness**. Unsafe
  configurations need `--allow_unsafe_triggers`, which is a correctness
  waiver.
- `ACCUMULATING` emits the **running total**; `DISCARDING` emits the
  **delta**. Over 5 elements with `AfterCount(2)`, the trigger's contract
  gives accumulating **2, 4, 5** and discarding **2, 2, 1** — the course's
  own test expectations. The **Direct Runner emits a single firing**,
  because it evaluates triggers per bundle rather than per element, so
  verify multi-firing behaviour on Dataflow.
- Never sum an ACCUMULATING stream. Take the last value per key per
  window instead.
- The design question is **"what does the consumer need?"** A dashboard
  wants running totals and early firings; an alerting system wants deltas;
  a daily report wants one correct final value.

---

## 📚 Practice Exercises

1. **Reproduce the course's tests.** Write a script that runs the
   five-element `AfterCount(2)` window under both accumulation modes,
   writes the output, and asserts the exact sequences `2, 4, 5` and
   `2, 2, 1`. Then extend it to 6 elements and work out by hand what
   each mode emits, and verify your prediction against the run.

2. **Design for two consumers.** Build one pipeline that writes a
   dashboard feed (accumulating, early firing) and one that writes an
   alerting feed (discarding, early firing) from the same events. Explain
   why one pipeline cannot serve both without a downstream transformation,
   and describe that transformation.

3. **Early and late firings in practice.** Use
   `AfterWatermark(early=AfterCount(count=10), late=AfterCount(count=1))`
   with `allowed_lateness=300`. Run it over
   `sample_data_late/events.ndjson` (generated with `--late-events 500`)
   and over the normal sample data. Compare the number of firings and
   explain the difference in terms of the late subtrigger.

4. **Count the firings.** Instrument a pipeline to report how many times
   each window fired, and run it with `AfterCount(100)` at three different
   data volumes. Show that the number of firings scales with volume, and
   explain what that means for the output rate and the checkpoint cost.

5. **Prove the invariant.** Write a script that takes the DISCARDING
   output and asserts that the sum of the deltas equals the last
   ACCUMULATING value, for several random event counts. Then explain why
   summing the ACCUMULATING stream gives the wrong answer, with the
   numbers.

6. **Compare `AfterProcessingTime` and `AfterCount` for
   reproducibility.** Run a pipeline with `AfterProcessingTime(delay=10)`
   twice over the same input and compare the outputs. Explain why they
   differ, and state what that implies for using this trigger in a
   pipeline whose output is written to a report.

---

## 📖 Further Reading

- Beam's triggers and accumulations — https://beam.apache.org/documentation/programming-guide/#triggers
- Beam's windowing guide — https://beam.apache.org/documentation/programming-guide/#windowing
- Dataflow's "Windowing and triggers" guide — https://cloud.google.com/dataflow/docs/guides/windowing
- Dataflow's "Late data and allowed lateness" — https://cloud.google.com/dataflow/docs/guides/watermarks
- Beam's trigger API reference — https://beam.apache.org/releases/pydoc/current/apache_beam.transforms.trigger.html
- Beam's `WindowInto` API reference — https://beam.apache.org/releases/pydoc/current/apache_beam.transforms.core.html
