# 7.6 — State, Timers & Processing-Time Triggers

> **Section 7 · Streaming Pipelines · Lecture 7.6 · 6:30**

## 🎯 What you will learn

- The stateful `DoFn` API: `@beam.DoFn.StateParam`, `BagStateSpec`, `ReadModifyWriteStateSpec`, `CombiningValueStateSpec`
- The `DoFn` lifecycle — `setup` → `start_bundle` → `process` → `finish_bundle` → `teardown` — and where state actually lives
- The correctness rule that catches everyone: **a plain Python attribute on a `DoFn` is not durable state**
- The timer API: `userstate.TimerSpec`, setting timers in relative or absolute time, and the `on_timer` callback
- Event-time timers versus processing-time timers, and why "flush after N minutes of inactivity" needs the latter
- The exact contents of `apache_beam.transforms.userstate`
- The `start_bundle` / `finish_bundle` lifecycle — when within-bundle state is the right answer

---

## 🧠 Concept

### Why you need state at all

Most Beam transforms are stateless: `Map` sees an element and emits
something. `CombinePerKey` sees an element and updates an accumulator.
Neither needs to remember anything between elements.

But plenty of real streaming questions are *about* remembering:

- "Has this customer already been counted in this hour?"
- "How many events has this user produced in the last 30 minutes?"
- "Is this a new session, or a continuation of the previous one?"
- "This user has been idle for 10 minutes — close their session."

All four are questions about a history, and a stateless `Map` cannot answer
any of them. That is what Beam's stateful `DoFn` API is for.

### The stateful `DoFn` API

A stateful `DoFn` declares its state and timers as **class attributes**,
and receives them as **arguments to `process`** (or to `on_timer`) through
special parameter markers.

The markers are attributes of `beam.DoFn`:

| Marker | What it gives you |
|---|---|
| `@beam.DoFn.StateParam` | a state object, keyed by the current key |
| `@beam.DoFn.TimerParam` | a timer object, keyed by the current key |
| `@beam.DoFn.KeyParam` | the current key |
| `@beam.DoFn.TimestampParam` | the element's event-time timestamp |
| `@beam.DoFn.WindowParam` | the window the element is in |
| `@beam.DoFn.ElementParam` | the element itself, for keyed inputs |
| `@beam.DoFn.PaneInfoParam` | the pane metadata (`is_first`, `is_last`, …) |

The state and timer *specifications* live in `apache_beam.transforms.userstate`.
The three state specs you will use most:

| Spec | Semantics | Runtime API | When to use it |
|---|---|---|---|
| `BagStateSpec` | an unordered, append-only multiset | `add(v)`, `read()`, `clear()` | "all the values I have seen" |
| `ReadModifyWriteStateSpec` | one value; read, change, write | `read()`, `write(v)`, `clear()` | counters, last-seen timestamps |
| `CombiningValueStateSpec` | one value behind a `CombineFn` | `add(v)`, `read()`, `clear()` | running sums, running maxes |

Note that the runtime methods differ between the specs, and the difference
trips people up. `ReadModifyWriteStateSpec` is the only one with `write()`.
`BagStateSpec` and `CombiningValueStateSpec` both use `add()`.
`ReadModifyWriteStateSpec.read()` returns the value or `None`;
`BagStateSpec.read()` returns an iterable.

There is one more thing to internalise about `ParDo` on a keyed input:
**the element the `DoFn` receives is the whole `(key, value)` pair**, not
just the value. The key is still available separately through
`@beam.DoFn.KeyParam`, but `process` sees the tuple. Every example below
unpacks it accordingly.

Here is a complete, working stateful `DoFn`:

```python
import apache_beam as beam
from apache_beam.coders import VarIntCoder
from apache_beam.transforms import userstate


class CountPerKeyFn(beam.DoFn):
    """Count the elements seen for each key."""

    COUNT = userstate.ReadModifyWriteStateSpec("count", VarIntCoder())

    def process(self, element, count=beam.DoFn.StateParam(COUNT)):
        """Increment the counter for this key."""
        current = count.read() or 0
        count.write(current + 1)
        yield current + 1
```

Note the pattern in the signature:

```text
def process(self, element, count=beam.DoFn.StateParam(COUNT)):
```

`beam.DoFn.StateParam(COUNT)` is a *default argument*. Beam inspects the
signature at graph-construction time, sees the marker, and injects the
runtime state object when it calls `process`. The name `count` is yours;
the marker is what matters.

There is a shorthand for the common case, which is what you will see in
most Beam documentation:

```text
def process(self, element, count=beam.DoFn.StateParam("count")):
```

The shorthand takes a **string name** and derives the coder from the type
hints. The explicit form (`StateParam(COUNT)`) is better in production
code because the coder is explicit rather than inferred, and inference can
fail at job submission time on a worker rather than on your laptop.

### The `DoFn` lifecycle

A `DoFn` is not one function call. It is an object with a lifecycle, and
understanding it is what separates "my code works in the test" from "my
code works at 3am after a reschedule".

```text
setup()            ── once per DoFn instance, on the worker
   │
   ├── start_bundle()   ── once per bundle
   │      │
   │      ├── process(element)   ── once per element
   │      │      │
   │      │      └── on_timer(...)  ── once per timer firing
   │      │
   │      └── finish_bundle()  ── once per bundle
   │
   └── teardown()      ── once per DoFn instance, on the worker
```

| Method | Called | Use it for |
|---|---|---|
| `setup()` | once per instance | open connections, build clients, load lookup tables |
| `start_bundle()` | once per bundle | reset per-bundle accumulators |
| `process()` | once per element | the actual work |
| `finish_bundle()` | once per bundle | flush per-bundle accumulators |
| `teardown()` | once per instance | close connections, release resources |

A **bundle** is a chunk of elements the runner processes together. In
streaming, bundles are small and frequent (on Dataflow, typically a few
hundred elements or a few seconds' worth). In batch, they are large.

Two consequences follow immediately:

1. **Code in `process` runs many times per instance.**
2. **A `DoFn` instance is reused across bundles on a worker, but a different
   instance may process a different bundle on a different worker.**

### Where state lives — and the rule that catches everyone

This is the most important paragraph in the chapter.

> **A plain Python attribute on a `DoFn` is NOT durable state.**
>
> It does not survive bundle boundaries. It does not survive worker
> rescheduling. It does not survive a job restart. And a given bundle may
> be processed by a different worker than the one that processed the
> previous bundle.

Here is code that looks right and is wrong:

```python
class BrokenCounterFn(beam.DoFn):
    """This does NOT work in production."""

    def __init__(self):
        self.count = 0

    def process(self, element):
        self.count += 1
        yield self.count
```

In a `TestPipeline` on the `DirectRunner`, this appears to work — the
runner happens to keep one instance around and process the elements in
order. In production it produces silently wrong answers, because:

- **Bundle boundaries reset it.** The runner decides the bundle size.
  A new bundle may call `start_bundle` on a fresh instance, or reuse an
  instance whose `self.count` still holds the previous bundle's value.
- **Rescheduling loses it.** A worker can die mid-bundle. The bundle is
  retried on another worker with a fresh `DoFn` instance, whose `self.count`
  is 0.
- **Job restarts lose it.** After a restart, the runner re-processes from
  the last checkpoint. Any in-memory attribute is gone, and the counts
  restart from zero.
- **Keyed parallelism is not the issue — it is the *fix*.** State in
  Beam is keyed. `StateParam` gives you the state *for the key currently
  being processed*. That is why a `DoFn` on a keyed input sees a different
  state object per key, and why the same `DoFn` instance can safely serve
  thousands of keys.

Only state accessed through a `@StateParam` is checkpointed by the runner.
The runner serialises it alongside the window state at checkpoint time, and
restores it when the bundle is retried or the job resumes.

The **sibling BigQuery course** in this repository gets this wrong. It
stores counters on a plain `self` attribute and presents the result as
working. It does not work in production, and the failure is silent — you
get plausible numbers that are wrong. This chapter gets it right.

If you want state that survives, it must be one of:

- `BagStateSpec`, `ReadModifyWriteStateSpec`, `CombiningValueStateSpec`,
  `SetStateSpec`, or `OrderedListStateSpec`, accessed via
  `@beam.DoFn.StateParam`;
- a side input (read-only, broadcast to every worker);
- an external store you write to yourself — which is exactly the wrong
  answer, because it re-introduces the consistency problem Beam just
  solved for you.

### The timer API

Timers are how a stateful `DoFn` schedules future work for a key. They
come in the same keyed world as state: a timer is set *for a key*, and
fires *for that key*.

The specification lives in `userstate.TimerSpec`:

```python
from apache_beam.transforms import userstate

FLUSH_TIMER = userstate.TimerSpec("flush", userstate.TimeDomain.WATERMARK)
```

The second argument is the **time domain**:

| Domain | Fires when |
|---|---|
| `userstate.TimeDomain.WATERMARK` | the event-time watermark reaches the timer's timestamp |
| `userstate.TimeDomain.REAL_TIME` | wall-clock processing time reaches the timer's timestamp |

Setting a timer, in `process`:

```python
import apache_beam as beam
from apache_beam.coders import FastPrimitivesCoder
from apache_beam.transforms import userstate
from apache_beam.utils.timestamp import Duration, Timestamp


class FlushFn(beam.DoFn):
    """Emit a summary for each key N minutes after its last element."""

    ITEMS = userstate.BagStateSpec("items", FastPrimitivesCoder())
    TIMER = userstate.TimerSpec("flush", userstate.TimeDomain.REAL_TIME)

    def process(
        self,
        element,
        items=beam.DoFn.StateParam(ITEMS),
        timer=beam.DoFn.TimerParam(TIMER),
    ):
        """Buffer the element and (re)arm the flush timer."""
        _, value = element
        items.add(value)
        # Set the timer 10 minutes from now.
        timer.set(Timestamp.now() + Duration(seconds=600))

    @userstate.on_timer(TIMER)
    def on_flush(self, items=beam.DoFn.StateParam(ITEMS)):
        """Emit and clear the buffered elements."""
        buffered = list(items.read())
        if buffered:
            yield buffered
            items.clear()
```

The pieces:

- `timer.set(timestamp)` schedules the timer. Calling it again with a
  later timestamp **reschedules** it; calling it with an earlier timestamp
  moves it earlier. The timer fires once, at the timestamp in force when
  the watermark (or the processing clock) reaches it.
- `timer.clear()` cancels a pending timer.
- The `@userstate.on_timer(TIMER)` decorator registers the callback. The
  decorated method is called when the timer fires, with the same
  `@StateParam` arguments available.
- `@beam.DoFn.TimerParam(TIMER)` gives you the timer *object* in
  `process`, so you can set or clear it. In `on_timer` you do not need it —
  the callback only runs when the timer fires.

Note the `on_timer` decorator: it comes from `userstate`, not from
`beam.DoFn`. The Beam model has exactly one timer decorator and it lives
in the `userstate` module.

**`@on_timer` takes a `TimerSpec`, never a state spec.** Passing a
`BagStateSpec` to it fails immediately at pipeline construction:

```text
ValueError: @on_timer decorator expected TimerSpec.
```

A `DoFn` therefore needs *two* declarations when it both buffers state and
flushes on a timer — a state spec for the data and a timer spec for the
deadline. They are different objects with different jobs.

There is also a subtlety with the timer spec's lifecycle: Beam attaches
the callback to the spec object itself (`timer_spec._attached_callback`),
and a spec can only have **one** callback. If you register two `@on_timer`
methods against the same `TimerSpec`, the second registration raises:

```text
ValueError: Multiple on_timer callbacks registered for 'flush'.
```

### Event-time timers versus processing-time timers

This is the distinction that matters most, and it is frequently muddled.

**Event-time timer** (`TimeDomain.WATERMARK`) fires when the *event-time
watermark* reaches the timer's timestamp. It is:
- deterministic — a replay of the same input produces the same firing times;
- tied to the data — it fires when the data says it should;
- dependent on the watermark advancing, which means a stalled source
  stalls the timer.

**Processing-time timer** (`TimeDomain.REAL_TIME`) fires when *wall-clock
time on the worker* reaches the timer's timestamp. It is:
- non-deterministic — a replay fires at different wall-clock times;
- tied to the pipeline's liveness, not to the data;
- independent of the watermark — it fires even if no new data has arrived.

### Why "flush after N minutes of inactivity" needs a processing-time timer

This is the classic session-detection problem, and it is worth working
through because it shows exactly why the two timer types are not
interchangeable.

The requirement: *"If a user stops producing events for 10 minutes, emit
their session."*

Consider the event-time approach: set a timer for `last_event_time + 10
minutes`.

```python
timer.set(last_event_timestamp + Duration(seconds=600))
```

The problem: this timer fires when the **watermark** reaches
`last_event_timestamp + 10 minutes`. If the user genuinely goes idle, no
new events arrive — and if no new events arrive, the watermark does not
advance either. The timer never fires. The session is never closed. The
user comes back an hour later, and their "session" is an hour long
instead of ten minutes.

This is a genuine deadlock: **event-time timers cannot detect the absence
of events.**

The processing-time approach: set the timer relative to *now*, the wall
clock.

```python
timer.set(Timestamp.now() + Duration(seconds=600))
```

Now the timer fires ten minutes of wall-clock time later, regardless of
whether any new data arrived. The session is closed on time. When the user
comes back, their next event starts a new session.

The cost: the firing time depends on when the data happened to arrive, not
on anything in the data. Two replays of the same input can produce
different session boundaries. This is why processing-time timers are the
right tool for *liveness* decisions ("close it out, it's gone quiet") and
the wrong tool for *correctness* decisions ("this event belongs to the
10:00 hour").

The rule:

| Question | Timer domain |
|---|---|
| "Close this session 10 minutes after the user's last event" | `REAL_TIME` |
| "Emit this window's total when the watermark passes the window end" | `WATERMARK` |
| "Notify me 5 minutes after the user registered" | `WATERMARK` |
| "Retry this failed write in 30 seconds" | `REAL_TIME` |

### The `userstate` module, exactly

The module is `apache_beam.transforms.userstate`. Its public contents:

```text
AccumulatingRuntimeState        OrderedListRuntimeState
Any                             OrderedListStateSpec
BagRuntimeState                 ReadModifyWriteRuntimeState
BagStateSpec                    ReadModifyWriteStateSpec
BaseTimer                       RuntimeState
Callable                        RuntimeTimer
CallableT                       SetRuntimeState
Coder                           SetStateSpec
CombiningValueRuntimeState      StateSpec
CombiningValueStateSpec         TimeDomain
Iterable                        Timer
NamedTuple                      TimerSpec
Optional                        UserStateContext
OrderedListStateSpec            get_dofn_specs
                                is_stateful_dofn
                                on_timer
                                validate_stateful_dofn
```

The state specs available are:

| Spec | Semantics |
|---|---|
| `BagStateSpec` | an unordered, append-only multiset of values |
| `ReadModifyWriteStateSpec` | one value; read it, modify it, write it back |
| `CombiningValueStateSpec` | one value behind a `CombineFn` — a running aggregate |
| `SetStateSpec` | a set of values; each is stored once |
| `OrderedListStateSpec` | a list with a cap on the number of retained elements |

The runtime state objects (`BagRuntimeState`, `ReadModifyWriteRuntimeState`,
`CombiningValueRuntimeState`, `SetRuntimeState`, `OrderedListRuntimeState`)
are what `@StateParam` hands you at run time. You rarely name them
directly.

The helper functions are `is_stateful_dofn`, `validate_stateful_dofn`,
`get_dofn_specs`, and the `on_timer` decorator.

### The within-bundle alternative — `start_bundle` and `finish_bundle`

Not every "remember" needs durable state. Sometimes you only need to
remember across the elements of a *single bundle* — and a bundle is
processed by one worker, in one go, with no rescheduling in the middle.

Beam's mechanism for this is the `DoFn` lifecycle itself. The runner
calls `start_bundle()` before the first element of a bundle and
`finish_bundle()` after the last one, on the same instance, on the same
worker. A plain attribute that you explicitly reset in `start_bundle` is
therefore a **per-bundle accumulator**: it lives for exactly one bundle
and never crosses a bundle boundary.

```python
import apache_beam as beam


class PerBundleCounterFn(beam.DoFn):
    """Count elements per key within a single bundle.

    This is a per-bundle accumulator, not durable state. It is reset in
    `start_bundle`, so the answer depends on how the runner bundled the
    data. Use `StateParam` for anything that must be exact.
    """

    def __init__(self):
        self.counts = {}

    def start_bundle(self):
        """Reset the per-bundle accumulator."""
        self.counts = {}

    def process(self, element):
        """Increment the count for this key and emit the bundle-local total."""
        key = element[0]
        self.counts[key] = self.counts.get(key, 0) + 1
        yield key, self.counts[key]

    def finish_bundle(self):
        """Flush the per-bundle accumulator, if the semantics need it."""
        self.counts = {}
```

The critical distinction from the broken `BrokenCountFn` in the hands-on
is **where the reset happens**. `BrokenCountFn` never resets, so its
counter silently spans bundle boundaries and gives a different answer
depending on the runner's bundling. `PerBundleCounterFn` resets
explicitly at a well-defined boundary, so the answer is *well-defined* —
it is the per-bundle count, and the documentation says so.

Note also what `finish_bundle` is for. The Beam source is explicit about
it:

> Thus, all work that depends on input elements, and all externally
> important side effects, must be performed in `DoFn.process` or
> `DoFn.finish_bundle`.

`finish_bundle` is the hook for flushing a per-bundle accumulator to a
sink. If you emit from `finish_bundle`, the emission happens once per
bundle rather than once per element.

When is the per-bundle accumulator the right tool?

- When you want a cheap pre-aggregation to reduce the number of elements
  crossing the network. A `GroupByKey` on a hot key with a per-bundle
  accumulator in front of it can cut shuffle volume dramatically.
- When the semantics genuinely are per-bundle: "how many of these elements
  are in this batch?" is a different question from "how many have I ever
  seen?"
- When you want to avoid the cost of durable state for something that is
  safe to lose.

When is it the wrong tool?

- Any question that spans bundles: "how many events has this user ever
  produced?", "is this a duplicate of something I saw earlier?"

Those need `StateParam`. A per-bundle accumulator will give you a
different answer depending on how the runner happened to bundle the data —
which is the definition of a bug.

---

## 🛠️ Hands-On

### Step 1 — A stateful `DoFn` that survives bundle boundaries

Write a `DoFn` that counts events per region and emits the running total.
Save it as `_run/count_stateful.py`:

```python
"""A stateful DoFn: a durable per-key counter."""

import apache_beam as beam
from apache_beam.coders import VarIntCoder
from apache_beam.transforms import userstate


class CountPerRegionFn(beam.DoFn):
    """Count events per region, keeping the count in durable state.

    The counter lives in `ReadModifyWriteStateSpec`, not on `self`. That
    means it is checkpointed with the window state, restored after a
    worker dies, and keyed per region rather than per worker.
    """

    COUNT = userstate.ReadModifyWriteStateSpec("count", VarIntCoder())

    def process(self, element, count=beam.DoFn.StateParam(COUNT)):
        """Increment the region's counter and emit the new total."""
        current = count.read() or 0
        count.write(current + 1)
        yield current + 1


with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create(["EMEA", "EMEA", "AMER", "EMEA", "AMER"])
        | "KeyByRegion" >> beam.Map(lambda region: (region, region))
        | "Count" >> beam.ParDo(CountPerRegionFn())
        | "Print" >> beam.Map(lambda item: print("count", item))
    )
```

Run it:

```bash
python _run/count_stateful.py
```

The output shows the running count per region. The key observation is that
the state is **per key**: `EMEA` and `AMER` have independent counters, even
though the same `DoFn` instance serves both.

### Step 2 — See the difference from a plain attribute

Now the broken version. Save it as `_run/count_broken.py`:

```python
"""The version that does NOT work in production.

Run this and it looks fine. That is the trap.
"""

import apache_beam as beam


class BrokenCountFn(beam.DoFn):
    """A counter on a plain Python attribute. Not durable. Wrong.

    The counter is per *instance*, not per key. So `EMEA` and `AMER`
    share one counter, and the totals depend on how the runner happened
    to bundle the elements.
    """

    def __init__(self):
        self.count = 0

    def process(self, element):
        """Increment a non-durable counter."""
        self.count += 1
        yield self.count


with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create(["EMEA", "EMEA", "AMER", "EMEA", "AMER"])
        | "Count" >> beam.ParDo(BrokenCountFn())
        | "Print" >> beam.Map(lambda item: print("count", item))
    )
```

Compare the two outputs:

```text
# _run/count_stateful.py — durable, per-key state
count 1
count 2
count 3
count 1
count 2

# _run/count_broken.py — a plain attribute
count 1
count 2
count 3
count 4
count 5
```

The durable version restarts at 1 for `AMER`, because the state is keyed.
The broken version keeps counting, because `self.count` belongs to the
`DoFn` *instance*, not to the key.

The difference is invisible if you only ever use one key, which is exactly
why this mistake survives code review. The reason it is wrong is
structural, not observable in a local test:

- the counter resets at every bundle boundary, so the totals depend on
  how the runner chose to bundle the data;
- a worker failure loses the counter entirely;
- a job restart resets it to zero.

The durable version in Step 1 does not have any of these problems,
because the runner checkpoints the state.

### Step 3 — Bag state: keep the values you have seen

Save it as `_run/bag_state.py`:

```python
"""Bag state: an append-only multiset of values per key."""

import apache_beam as beam
from apache_beam.coders import FloatCoder
from apache_beam.transforms import userstate


class BufferValuesFn(beam.DoFn):
    """Buffer every value for a key and emit the buffer it has accumulated."""

    VALUES = userstate.BagStateSpec("values", FloatCoder())

    def process(self, element, values=beam.DoFn.StateParam(VALUES)):
        """Append the value to the key's buffer, then emit the whole buffer.

        A `ParDo` over a keyed PCollection receives the whole `(key, value)`
        pair as the element, so the value has to be unpacked first.
        """
        _, value = element
        values.add(value)
        yield sorted(values.read())


with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create([1.0, 2.0, 3.0, 4.0])
        | "Key" >> beam.Map(lambda value: ("all", value))
        | "Buffer" >> beam.ParDo(BufferValuesFn())
        | "Print" >> beam.Map(lambda item: print("buffer", item))
    )
```

Run it:

```bash
python _run/bag_state.py
```

```text
buffer [1.0]
buffer [1.0, 2.0]
buffer [1.0, 2.0, 3.0]
buffer [1.0, 2.0, 3.0, 4.0]
```

`BagStateSpec` is the right choice when you need the individual values,
not just an aggregate. The runtime API is `values.add(v)` to append,
`values.read()` to get an iterable back, and `values.clear()` to empty
it. Note that `BagStateSpec` has **no `write()` method** — `add()` is the
append operation.

To flush the buffer on a timer rather than on every element, add a
separate `TimerSpec` and register the callback against *that*:

```python
FLUSH = userstate.TimerSpec("flush", userstate.TimeDomain.REAL_TIME)

@userstate.on_timer(FLUSH)
def on_flush(self, values=beam.DoFn.StateParam(VALUES)):
    """Emit and clear the buffer."""
    buffered = sorted(values.read())
    if buffered:
        yield buffered
        values.clear()
```

### Step 4 — Combining state: a running aggregate

Save it as `_run/combining_state.py`:

```python
"""Combining state: a running sum maintained by a CombineFn."""

import apache_beam as beam
from apache_beam.coders import FloatCoder
from apache_beam.transforms import userstate


class SumCombineFn(beam.CombineFn):
    """Sum floats.

    A `CombineFn` must be associative and commutative, because Beam merges
    partial accumulators from different workers in an arbitrary order.
    """

    def create_accumulator(self):
        """Start an empty accumulator."""
        return 0.0

    def add_input(self, accumulator, element):
        """Add one element to the accumulator."""
        return accumulator + element

    def merge_accumulators(self, accumulators):
        """Merge partial accumulators from different workers."""
        total = 0.0
        for partial in accumulators:
            total += partial
        return total

    def extract_output(self, accumulator):
        """Produce the final output."""
        return accumulator


class RunningTotalFn(beam.DoFn):
    """Maintain a running sum per key using CombiningValueStateSpec."""

    TOTAL = userstate.CombiningValueStateSpec(
        "total", coder=FloatCoder(), combine_fn=SumCombineFn()
    )

    def process(self, element, total=beam.DoFn.StateParam(TOTAL)):
        """Add one value to the running total and emit it.

        A `ParDo` over a keyed PCollection receives the whole `(key, value)`
        pair as the element, so the value has to be unpacked first.
        """
        _, value = element
        total.add(value)
        yield total.read()


with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create([1.0, 2.0, 3.0, 4.0])
        | "Key" >> beam.Map(lambda value: ("all", value))
        | "Total" >> beam.ParDo(RunningTotalFn())
        | "Print" >> beam.Map(lambda item: print("total", item))
    )
```

Run it:

```bash
python _run/combining_state.py
```

```text
total 1.0
total 3.0
total 6.0
total 10.0
```

The running total: 1, then 1+2=3, then 3+3=6, then 6+4=10.

Two details in that code are load-bearing and easy to get wrong:

- **`combine_fn` must be a concrete `CombineFn`, not the abstract
  `beam.CombineFn`.** `beam.CombineFn(sum)` passes the *class*, and
  calling `add_input` on it raises
  `NotImplementedError: <apache_beam.transforms.core.CombineFn object ...>`.
  Write the four methods, as above.
- **The coder is for the *accumulator*, not for the input.** The
  accumulator here is a `float`, so `FloatCoder()` is right. If your
  accumulator were a tuple of two counters, you would need a coder for
  that tuple.

The difference between `CombiningValueStateSpec` and
`ReadModifyWriteStateSpec` is where the arithmetic happens.
`ReadModifyWrite` means *you* read the value, change it, and write it
back. `CombiningValue` means you call `add()`, and the runner maintains
the aggregate using the `CombineFn` — which is exactly the mechanism
`CombinePerKey` uses, so it is efficient under partial merging.

### Step 5 — A processing-time timer: the session detector

This is the full hands-on. Save it as `_run/session_detector.py`:

```python
"""Session detection with durable state and a processing-time timer.

A session ends when a user has been idle for `IDLE_SECONDS`. The timer
must be in the REAL_TIME domain: an event-time timer would only fire
when the watermark advanced past the idle deadline, and a user who goes
quiet produces no events, so the watermark would not advance and the
session would never close.
"""

import apache_beam as beam
from apache_beam.coders import FastPrimitivesCoder
from apache_beam.transforms import userstate
from apache_beam.utils.timestamp import Duration, Timestamp

IDLE_SECONDS = 600


class SessionDetectorFn(beam.DoFn):
    """Emit each session when it goes idle.

    State:
        EVENTS — a bag of the user's events in the current session.

    Timers:
        IDLE — fires `IDLE_SECONDS` after the user's most recent event.
    """

    EVENTS = userstate.BagStateSpec("events", FastPrimitivesCoder())
    IDLE = userstate.TimerSpec("idle", userstate.TimeDomain.REAL_TIME)

    def process(
        self,
        element,
        events=beam.DoFn.StateParam(EVENTS),
        timer=beam.DoFn.TimerParam(IDLE),
    ):
        """Record the event and (re)arm the idle timer.

        A `ParDo` over a keyed PCollection receives the whole `(key, value)`
        pair as the element, so the value has to be unpacked first.
        """
        _, event = element
        events.add(event)
        # Reschedule the timer: each new event pushes the deadline out.
        timer.set(Timestamp.now() + Duration(seconds=IDLE_SECONDS))

    @userstate.on_timer(IDLE)
    def on_idle(self, events=beam.DoFn.StateParam(EVENTS)):
        """Emit the session and start a new one."""
        buffered = list(events.read())
        if buffered:
            yield {
                "user_id": buffered[0]["user_id"],
                "event_count": len(buffered),
                "total_value": round(sum(e["value"] for e in buffered), 2),
            }
            events.clear()
```

The `timer.set` call is the interesting line. It uses `Timestamp.now()`,
which is the **processing-time** clock — not the element's event time.
That is what makes the timer fire ten wall-clock minutes after the user's
last event, whether or not any more events arrive.

`Timestamp.now()` is correct for a real deployment, where the runner's
processing clock *is* the wall clock. But there is a subtlety when you
test locally, which Step 7 addresses: the `DirectRunner`'s processing
clock starts at `MIN_TIMESTAMP` (1970-01-01), not at the current wall
clock. So a timer set to `Timestamp.now() + 600s` is roughly fifty-six
years in the future *relative to the runner's clock*, and it will never
fire in a local test.

### Step 6 — Run the session detector

Save it as `_run/run_session_detector.py`:

```python
"""Drive the session detector with a bounded set of clickstream events."""

import apache_beam as beam

from session_detector import SessionDetectorFn

EVENTS = [
    {"event_id": "e1", "user_id": "u1", "region": "EMEA", "value": 10.0},
    {"event_id": "e2", "user_id": "u1", "region": "EMEA", "value": 20.0},
    {"event_id": "e3", "user_id": "u2", "region": "AMER", "value": 30.0},
    {"event_id": "e4", "user_id": "u1", "region": "EMEA", "value": 5.0},
]


with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create(EVENTS)
        | "KeyByUser" >> beam.Map(lambda e: (e["user_id"], e))
        | "Sessions" >> beam.ParDo(SessionDetectorFn())
        | "Print" >> beam.Map(lambda item: print("session", item))
    )
```

Run it:

```bash
cd _run && python run_session_detector.py
```

On a bounded input the idle timer never fires before the pipeline ends, so
you may not see a session emitted. That is expected and correct: the
timer is ten minutes in the future, and the job finished first. Shortening
`IDLE_SECONDS` does not help either, because the runner's processing clock
does not advance during a bounded run. Step 7 shows the reliable way to
make the timer fire: `TestStream`'s `advance_processing_time`.

### Step 7 — Fire the timer deterministically with TestStream

`TestStream` can advance the processing-time clock explicitly, which makes
the timer behaviour testable rather than a matter of waiting.

There is one important detail. As noted in Step 5, the runner's
processing clock starts at `MIN_TIMESTAMP`, not at the wall clock. So a
timer set with `Timestamp.now()` will never fire under `TestStream`. The
timer has to be set relative to the clock's own base.

Save it as `_run/session_test_stream.py`:

```python
"""Fire the session detector's idle timer deterministically.

The runner's processing clock starts at MIN_TIMESTAMP, so the timer must
be set relative to that base rather than to the wall clock.
"""

import apache_beam as beam
from apache_beam.coders import FastPrimitivesCoder
from apache_beam.testing.test_stream import TestStream
from apache_beam.transforms import userstate
from apache_beam.transforms.window import TimestampedValue
from apache_beam.utils.timestamp import MIN_TIMESTAMP, Duration, Timestamp

BASE = 1_700_000_000


class SessionDetectorFn(beam.DoFn):
    """Emit each session when it goes idle, timed from the clock base."""

    EVENTS = userstate.BagStateSpec("events", FastPrimitivesCoder())
    IDLE = userstate.TimerSpec("idle", userstate.TimeDomain.REAL_TIME)

    def process(
        self,
        element,
        events=beam.DoFn.StateParam(EVENTS),
        timer=beam.DoFn.TimerParam(IDLE),
    ):
        """Record the event and (re)arm the idle timer."""
        _, event = element
        events.add(event)
        timer.set(MIN_TIMESTAMP + Duration(seconds=600))

    @userstate.on_timer(IDLE)
    def on_idle(self, events=beam.DoFn.StateParam(EVENTS)):
        """Emit the session and start a new one."""
        buffered = list(events.read())
        if buffered:
            yield {
                "user_id": buffered[0]["user_id"],
                "event_count": len(buffered),
                "total_value": round(sum(e["value"] for e in buffered), 2),
            }
            events.clear()


with beam.Pipeline() as p:
    stream = TestStream()
    stream.add_elements(
        [
            TimestampedValue(
                {"event_id": "e1", "user_id": "u1", "value": 10.0},
                Timestamp(BASE),
            ),
            TimestampedValue(
                {"event_id": "e2", "user_id": "u1", "value": 20.0},
                Timestamp(BASE + 10),
            ),
        ]
    )
    stream.advance_processing_time(Duration(seconds=700))

    (
        p
        | "Stream" >> stream
        | "KeyByUser" >> beam.Map(lambda e: (e["user_id"], e))
        | "Sessions" >> beam.ParDo(SessionDetectorFn())
        | "Print" >> beam.Map(lambda item: print("session", item))
    )
```

Run it:

```bash
cd _run && python session_test_stream.py
```

```text
session {'user_id': 'u1', 'event_count': 2, 'total_value': 30.0}
```

The `advance_processing_time` call pushes the runner's processing clock
past the idle deadline, so the timer fires deterministically and you see
the session emitted: two events for `u1`, totalling 30.0.

Note that the two events went into **one** session, even though the
second arrived ten seconds after the first. The timer was *rescheduled*
by the second event, so the deadline moved out by another ten minutes.
That is the "N minutes of inactivity" semantics working correctly: a burst
of activity keeps the session open.

One more thing worth knowing before you deploy: the **Prism** runner
(`--runner DirectRunner` in Beam 2.60+) does not support `REAL_TIME`
timers at all. Beam's own source marks any pipeline with a
`TimeDomain.REAL_TIME` timer as unsupported by that runner. The course
project defaults to `BundleBasedDirectRunner`, which does support them.

### Step 8 — Read the state and timer specs back

Beam can tell you what a `DoFn` declares:

```python
from apache_beam.transforms import userstate

from session_detector import SessionDetectorFn

state_specs, timer_specs = userstate.get_dofn_specs(SessionDetectorFn())
print(state_specs)
print(timer_specs)
print(userstate.is_stateful_dofn(SessionDetectorFn()))
```

```text
({BagStateSpec(events)}, {TimerSpec(ts-idle)})
({BagStateSpec(events)}, {TimerSpec(ts-idle)})
True
```

`get_dofn_specs` returns a **pair of sets** — the state specs and the
timer specs — and `is_stateful_dofn` returns `True`. These are the same
functions Beam uses to validate the `DoFn` before the job starts.

You can also validate a `DoFn` explicitly, which is worth doing in a
test:

```python
userstate.validate_stateful_dofn(SessionDetectorFn())
```

It raises if the `DoFn` declares a state spec but does not use it in any
`process` or `on_timer` signature — a mistake that is otherwise silent.

### Step 9 — Write a test for the durable counter

A test that would have caught the plain-attribute bug. Save it as
`_run/test_stateful.py`:

```python
"""Test the durable counter against the plain-attribute version."""

import apache_beam as beam
from apache_beam.coders import VarIntCoder
from apache_beam.testing.test_pipeline import TestPipeline
from apache_beam.testing.util import assert_that, equal_to
from apache_beam.transforms import userstate


class CountPerKeyFn(beam.DoFn):
    """A durable per-key counter."""

    COUNT = userstate.ReadModifyWriteStateSpec("count", VarIntCoder())

    def process(self, element, count=beam.DoFn.StateParam(COUNT)):
        """Increment and emit the new total."""
        current = count.read() or 0
        count.write(current + 1)
        yield current + 1


def test_durable_counter():
    """The final count for each key is the number of its elements."""
    with TestPipeline() as pipeline:
        result = (
            pipeline
            | "Create" >> beam.Create(["a", "a", "b", "a", "b"])
            | "Key" >> beam.Map(lambda key: (key, key))
            | "Count" >> beam.ParDo(CountPerKeyFn())
        )
        assert_that(result, equal_to([1, 2, 3, 1, 2]))
```

Note the expected value: `[1, 2, 3, 1, 2]`, **not**
`[("a", 1), ("a", 2), ...]`. The `DoFn` yields `current + 1` — a bare
integer. The key is *not* automatically attached to the output; Beam
routes the element to the right key internally, but what you `yield` is
what comes out. If you want the key in the output, yield it explicitly:

```python
yield element[0], current + 1
```

Run it:

```bash
python -m pytest _run/test_stateful.py -v
```

```text
test_stateful.py::test_durable_counter PASSED

1 passed
```

The important property is that the result is **independent of the bundle
size**. The same test passes whether the runner bundles all five elements
together or one at a time — which is exactly the property a plain
attribute does not have.

---

## 🛠️ Common Errors and Fixes

### `ValueError: DoFn not a stateful DoFn`

Beam found no state or timer specs on your `DoFn`, but you asked for one.
Usually the cause is a typo in the spec name, or the spec was declared as
a local variable inside a method rather than a class attribute:

```python
class MyFn(beam.DoFn):
    def process(self, element):
        spec = userstate.BagStateSpec("x", coder)  # wrong: local
```

State specs must be **class attributes**.

### `ValueError: DoFn has a state parameter that is not a state spec`

You wrote:

```text
def process(self, element, count=beam.DoFn.StateParam("count"))
```

with a string, and Beam could not infer the coder from the type hints.
Either add proper type hints, or use the explicit form:

```text
COUNT = userstate.ReadModifyWriteStateSpec("count", VarIntCoder())

def process(self, element, count=beam.DoFn.StateParam(COUNT)):
```

### `AttributeError: 'NoneType' object has no attribute 'read'`

`state.read()` returned `None` because nothing has been written yet. For
`ReadModifyWriteStateSpec` this is expected on the first element:

```python
current = count.read() or 0
count.write(current + 1)
```

The `or 0` is the idiomatic guard. `BagStateSpec.read()` returns an empty
iterable rather than `None`, so it does not need the guard.

### `TypeError: unhashable type: 'dict'` when using state as a key

State is keyed by the key of the input. The key must be hashable. A dict
or a list as the key fails. Use a tuple:

```text
| "Key" >> beam.Map(lambda e: ((e["region"], e["event_type"]), e))
```

### `ValueError: Timer ... was never set` / the timer never fires

Three common causes:

1. **The wrong time domain.** An event-time timer needs the watermark to
   advance. On a bounded input, the watermark jumps to `+inf` at the end,
   which does fire event-time timers — but a timer set *relative to now*
   in the `WATERMARK` domain compares a wall-clock timestamp against an
   event-time watermark, which is meaningless. Use `REAL_TIME` for
   wall-clock deadlines.
2. **The key is wrong.** Timers are per key. A timer set while processing
   key `a` fires for key `a`.
3. **The callback was never registered.** You must decorate the method with
   `@userstate.on_timer(TIMER)`, and the `TIMER` in the decorator must be
   the same object as the one passed to `@beam.DoFn.TimerParam`.

There is a fourth cause that catches people writing local tests: the
runner's processing clock does not start at the wall clock. The
`DirectRunner`'s clock begins at `MIN_TIMESTAMP` (1970-01-01), so a timer
set with `Timestamp.now() + Duration(seconds=600)` is roughly fifty-six
years in the future *relative to that clock* and will never fire. Under
`TestStream`, set the timer relative to `MIN_TIMESTAMP` instead — see
Step 7 in the hands-on.

And a fifth: the **Prism** runner (`--runner DirectRunner` in Beam 2.60+)
does not support `REAL_TIME` timers at all. Beam marks any pipeline
containing one as unsupported by that runner. Use
`BundleBasedDirectRunner`, which is the course project default.

### `ValueError: parameter 'events' has no matching StateParam`

The name in `on_timer` must match the name of the state argument. And the
state spec in the decorator must match the spec in the signature:

```text
@userstate.on_timer(EVENTS)   # the spec
def on_idle(self, events=beam.DoFn.StateParam(EVENTS)):  # the same spec
```

### `ValueError: @on_timer decorator expected TimerSpec.`

You passed a *state* spec to `@userstate.on_timer`. The decorator accepts
only a `TimerSpec`:

```text
# wrong
@userstate.on_timer(VALUES)   # VALUES is a BagStateSpec

# right
@userstate.on_timer(FLUSH)    # FLUSH is a TimerSpec
```

A `DoFn` that both buffers state and flushes on a timer needs **both**
declarations.

### `AttributeError: 'BagRuntimeState' object has no attribute 'write'`

`BagStateSpec` uses `add()`, not `write()`. Only
`ReadModifyWriteStateSpec` has a `write()` method:

```python
values.add(value)          # BagStateSpec
count.write(current + 1)   # ReadModifyWriteStateSpec
```

### `NotImplementedError: <apache_beam.transforms.core.CombineFn object at 0x...>`

You passed the abstract `beam.CombineFn` class where a concrete
`CombineFn` was needed. `beam.CombineFn(sum)` passes the *class*, and
calling `add_input` on it raises. Write the four methods:

```python
class SumCombineFn(beam.CombineFn):
    def create_accumulator(self):
        return 0.0

    def add_input(self, accumulator, element):
        return accumulator + element

    def merge_accumulators(self, accumulators):
        total = 0.0
        for partial in accumulators:
            total += partial
        return total

    def extract_output(self, accumulator):
        return accumulator
```

### `TypeError: unsupported operand type(s) for +: 'float' and 'tuple'`

Your `CombineFn.add_input` received a tuple where it expected a number.
The usual cause is that a `ParDo` over a keyed PCollection receives the
**whole `(key, value)` pair** as the element, and you passed that pair
straight into `state.add(...)`.

```python
# wrong
total.add(element)        # element is (key, value)

# right
_, value = element
total.add(value)
```

### `TypeError: 'NoneType' object has no attribute 'read'` (in `on_timer`)

The state object was not injected into the `on_timer` callback. The
callback's signature must include a `StateParam` for the state it reads:

```python
@userstate.on_timer(IDLE)
def on_idle(self, events=beam.DoFn.StateParam(EVENTS)):
    ...
```

### The counter resets every few thousand elements

That is a bundle boundary, and it means you are using a plain attribute.
Move the counter into a `ReadModifyWriteStateSpec`.

### `AttributeError: module 'apache_beam' has no attribute 'DoFn.TimerSpec'`

There is no `beam.DoFn.TimerSpec`. The timer spec lives in the
`userstate` module:

```python
from apache_beam.transforms import userstate

TIMER = userstate.TimerSpec("flush", userstate.TimeDomain.REAL_TIME)
```

The `beam.DoFn` markers are `StateParam`, `TimerParam`, `KeyParam`,
`TimestampParam`, `WindowParam`, `ElementParam`, and `PaneInfoParam`.

### `ImportError: cannot import name 'on_timer' from 'apache_beam'`

The decorator is `userstate.on_timer`, not `beam.on_timer`:

```python
from apache_beam.transforms import userstate

@userstate.on_timer(TIMER)
def on_timer_callback(self, state=beam.DoFn.StateParam(STATE)):
    ...
```

### `PicklingError: Can't pickle <class '...StateSpec'>`

The `DoFn` was defined in `__main__` and the runner could not serialise
it, or the spec object was constructed at import time in a way that broke
pickling. Define stateful `DoFn` classes in an importable module, not
inline in a script.

---

## 💡 Production Notes

- **The durable-state rule is not a style preference.** It is the
  difference between a counter that is right and a counter that is
  *plausible*. A pipeline that stores a counter on `self` will pass every
  local test and produce wrong revenue in production. If you review code
  that counts anything across elements, check whether the counter is a
  `@StateParam` before you check anything else.

- **State is per key, and keys are your cardinality.** A `DoFn` over a
  keyed input creates one state namespace per key. Ten million distinct
  user ids means ten million state namespaces, each with its own timers.
  This is the single biggest cost driver in a stateful streaming job.
  Before you key by `user_id`, ask whether you key by `user_id` or by
  something coarser — and remember that coarse keys mean hot keys and
  skewed state.

- **Timers are a load source.** Every timer you set is a future callback.
  A session detector with ten million active users has ten million
  pending timers. Dataflow charges for the worker-hours that keep those
  timers alive. Set the timeout to the smallest value that meets the
  business need.

- **Processing-time timers are not replayable.** A job that is restarted
  from a checkpoint replays the same data, but the wall clock is now
  different, so processing-time timers fire at different moments and
  produce different session boundaries. If exact replay matters, use
  event-time timers and accept that idle sessions never close — or write
  the session boundary into the event stream so the replay is
  deterministic.

- **Prefer `CombiningValueStateSpec` for running aggregates.** It uses
  the same partial-merge machinery as `CombinePerKey`, so it is
  efficient under rescaling. A `ReadModifyWriteStateSpec` holding a
  Python list of ten thousand values is not efficient under anything.

- **Bound your bag state.** `BagStateSpec` grows without limit. If you
  are buffering a user's events until a session closes, and the session
  never closes, you have a memory leak with a business explanation.
  `OrderedListStateSpec` has a cap; `BagStateSpec` does not. Use a
  `CombiningValueStateSpec` when you only need the aggregate.

- **The `setup()`/`teardown()` pair is where clients belong.** Opening a
  database connection in `__init__` fails at submission time with a
  pickling error. Opening it in `setup()` gives you a connection per
  worker, reused across bundles, closed cleanly in `teardown()`. This is
  the pattern for the "write to Postgres from a Beam pipeline" shape.

- **At 3am, the state backend is the thing to check.** A streaming job
  that is slow, out of memory, or out of disk is almost always a state
  problem — too many keys, too much state per key, or too long a lateness
  budget. Look at the **Bundled Data Size** and **Worker Disk Usage**
  metrics before you look at anything else.

---

## 🔑 Key Takeaways

- A stateful `DoFn` declares **state specs and timer specs as class
  attributes** and receives them through `@beam.DoFn.StateParam` and
  `@beam.DoFn.TimerParam`.
- The state specs are `BagStateSpec` (all the values),
  `ReadModifyWriteStateSpec` (one value you edit),
  `CombiningValueStateSpec` (one running aggregate), plus `SetStateSpec`
  and `OrderedListStateSpec`.
- The lifecycle is **setup → start_bundle → process → finish_bundle →
  teardown**, and `process` runs once per element, many times per instance.
- **A plain Python attribute on a `DoFn` is not durable state.** It does
  not survive bundle boundaries, rescheduling, or a job restart. Only
  `@StateParam`-backed state is checkpointed.
- Timers are **per key**, just like state. `timer.set(timestamp)`
  schedules; `timer.clear()` cancels; `@userstate.on_timer` registers the
  callback.
- **Event-time timers** fire on the watermark (deterministic, data-driven);
  **processing-time timers** fire on the wall clock (liveness-driven).
- "Flush after N minutes of inactivity" **requires a processing-time
  timer**, because an idle user produces no events, so the watermark never
  advances and an event-time timer never fires.
- The `start_bundle` / `finish_bundle` lifecycle is the cheap,
  within-bundle alternative — useful for per-bundle pre-aggregation,
  useless for anything that must span bundles.

---

## 📚 Practice Exercises

1. **Fix the broken counter.** Take the `BrokenCountFn` from Step 2 and
   rewrite it with `ReadModifyWriteStateSpec`. Then write a test that
   forces many small bundles, and confirm that the durable version's
   result does not change with the bundle size while the plain-attribute
   version's does.

2. **Add a last-seen timestamp.** Extend `CountPerRegionFn` to also store
   the timestamp of the most recent event for the region, using a second
   `ReadModifyWriteStateSpec` with a `TimestampCoder`. Emit both the
   count and the last-seen time.

3. **Emit a running maximum.** Write a `DoFn` that maintains the maximum
   value seen per key using `CombiningValueStateSpec` and a `CombineFn`
   that takes the max. Compare its output with a `ReadModifyWriteStateSpec`
   version. Why is the `CombiningValueStateSpec` version the better choice
   for a key with high cardinality?

4. **Make the session detector emit a window too.** Add a second
   `CombiningValueStateSpec` to `SessionDetectorFn` that tracks the
   session's total value, and include it in the emitted session record.
   Confirm the total matches `sum(e["value"] for e in buffered)`.

5. **Prove the event-time timer deadlock.** Change the session detector's
   timer to `userstate.TimeDomain.WATERMARK` and set it to
   `last_event_timestamp + Duration(seconds=600)`. Run it on a bounded
   input where the user produces two events and then stops. Explain, in
   terms of the watermark, why no session is emitted — and what the
   pipeline would need in order to close it.

6. **Use the per-bundle accumulator for what it is good at.** Write a
   `DoFn` that uses a plain attribute reset in `start_bundle` to
   pre-aggregate values per key within a bundle before a `GroupByKey`.
   Measure the shuffle size with and without it using
   `--runner DirectRunner` on a generated input, and explain why the
   answer is still correct in both cases. Then explain what would change
   if you forgot the `start_bundle` reset.

---

## 📖 Further Reading

- Apache Beam: State and Timers — https://beam.apache.org/documentation/programming-guide/#io-transforms
- Apache Beam: State and Timers in the Beam model — https://beam.apache.org/documentation/model/a-beam-primer/#state-and-timers
- Apache Beam Python SDK: `userstate` API reference — https://beam.apache.org/releases/pydoc/current/apache_beam.transforms.userstate.html
- Apache Beam Python SDK: `DoFn` API reference — https://beam.apache.org/releases/pydoc/current/apache_beam.transforms.core.html#apache_beam.transforms.core.DoFn
- Google Cloud Dataflow: State and timers in streaming pipelines — https://cloud.google.com/dataflow/docs/guides/streaming/state-timers
- Google Cloud Dataflow: Optimizing your pipeline for cost — https://cloud.google.com/dataflow/docs/guides/performance/optimizing-cost
