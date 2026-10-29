# 2.6 — ParDo & DoFn

> **Section 2 · SDK & Core Transforms · Lecture 2.6 · 6:30**

## 🎯 What you will learn

- When `beam.Map`/`beam.FlatMap` are enough, and when you need `beam.ParDo`
- The `DoFn` lifecycle: `setup`, `start_bundle`, `process`, `finish_bundle`,
  `teardown` — and what each is actually for
- The `DoFn` parameter protocol: `TimestampParam`, `WindowParam`,
  `PaneInfoParam`, `ElementParam`, `WindowedValueParam`, `KeyParam`
- The stateful-DoFn API: `StateParam`, `TimerParam`, `TimerSpec`, and the
  rules that make it work
- Why a plain instance attribute is **not** durable state
- The serialisation constraint on your `DoFn`
- Side inputs: `beam.pvalue.AsIter`, `AsDict`, `AsSingleton`
- The `process` generator contract, including what happens when you yield
  nothing
- How to write a `ParseOrderFn` with `TimestampParam` and `WindowParam`

---

## 🧠 Concept

### `Map`, `FlatMap`, and `ParDo`

All three are `ParDo` under the hood. `beam.Map` and `beam.FlatMap` are
sugar that construct a `ParDo` with a built-in `DoFn`.

| Transform | Input | Output | Emits |
|---|---|---|---|
| `beam.Map(fn)` | one element | exactly one element | 1:1 |
| `beam.FlatMap(fn)` | one element | zero or more elements | 1:N |
| `beam.ParDo(MyFn())` | one element | zero or more elements | 1:N, with side outputs |

`beam.Map` guarantees exactly one output per input. `beam.FlatMap` and
`beam.ParDo` guarantee zero or more. This is the whole difference, and it
is a real one.

Use `beam.Map` when the function is a pure element-to-element transform.
Use `beam.FlatMap` when the function splits one element into several, or
filters by yielding nothing. Use `beam.ParDo` when you need any of:

- **Side inputs** — `beam.Map` supports them, but `ParDo` is where you use
  them idiomatically.
- **Side outputs** — multiple tagged outputs from one pass. Only `ParDo`
  supports this.
- **DoFn parameters** — `TimestampParam`, `WindowParam`, `PaneInfoParam`
  and friends. `Map` cannot declare these.
- **Stateful processing** — user state and timers. Only `ParDo`.
- **Bundle lifecycle hooks** — `setup`/`teardown` for resource management.

The `Map` sugar exists because the 1:1 case is by far the most common, and
`beam.Map(lambda x: ...)` is shorter than declaring a class. The moment you
need any of the above, reach for `ParDo`.

One subtlety worth knowing: `beam.Map` and `beam.FlatMap` are implemented as
`ParDo` with `MapDoFn`/`FlatMapDoFn`, and those built-in `DoFn`s *do*
support side inputs and `DoFn` parameters. But the parameter must be
declared on the function's signature, which for a lambda is awkward:

```python
# Works, but is unreadable
(
    src
    | "Enrich" >> beam.Map(
        lambda x, ts=beam.DoFn.TimestampParam: (x, ts),
    )
)
```

For anything beyond a trivial enrichment, write a class.

### The `DoFn` lifecycle

A `DoFn` instance is created once per worker process (or once per bundle
on some runners) and then reused for many elements. The lifecycle has five
hooks. Only `process` is required.

```text
  setup()                        once per DoFn instance
     │
     ▼
  ┌──────────────────────────────────────────┐
  │ start_bundle()      ─── one per bundle   │  ← loop
  │   process(el) × N                          │
  │ finish_bundle()     ─── one per bundle   │
  └──────────────────────────────────────────┘
     │                                          │
     ▼                                          │
  teardown()                     once, at the end
```

**`setup()`** — called once when the `DoFn` is initialised. Use it for
expensive, read-only resource setup: opening a database connection, loading
a reference table into memory, starting a client. Anything you create here
should be closed in `teardown()`.

```python
class LookupOrderFn(beam.DoFn):
    def setup(self):
        self.client = OrderServiceClient()

    def teardown(self):
        self.client.close()
```

The critical property: **`setup()` runs once per worker, not once per
element.** If `setup()` takes 30 seconds, you pay 30 seconds per worker, not
per row. This is the single biggest performance lever in a `DoFn`.

**`start_bundle()`** — called before the runner hands the `DoFn` a new
bundle of elements. Use it to reset per-bundle scratch state: counters,
buffers, a connection cursor. Anything you stash on `self` here is
bundle-scoped.

**`process(element, ...)`** — called once per element. This is where your
logic lives.

**`finish_bundle()`** — called after the last element of a bundle. Use it
to flush accumulated state.

**`teardown()`** — called when the `DoFn` is discarded. Close resources
here.

The critical property of the whole lifecycle: **`setup` and `teardown` are
paired, and `start_bundle`/`finish_bundle` are paired.** If you open a
resource in `setup` and the runner reuses the instance for a million
bundles, you must not re-open it in `start_bundle`. A common bug:

```python
# WRONG: opens a new connection per bundle and leaks the old one
def start_bundle(self):
    self.conn = connect()
```

```python
# RIGHT: reset the cursor, keep the connection
def start_bundle(self):
    self.conn.cursor().execute("...")
```

The bundle is the runner's unit of work — a chunk of elements processed
together and serialised as one group. Bundle size is controlled by the
runner and is typically on the order of a few hundred to a few thousand
elements. This is why per-element work should be cheap: you want the setup
cost amortised over many elements.

### The `process` generator contract

`process` is a **generator**. Its contract is precise:

| What you do | What happens |
|---|---|
| `yield value` | `value` is emitted to the output |
| `yield nothing` (bare `return`) | the input element is **dropped** |
| `yield a tuple` | the tuple is emitted as a single element |
| `raise` | the bundle fails and is retried |

The "yield nothing drops the input" rule is the single most important
property of `ParDo`, and it is a silent data-loss mechanism. Compare:

```python
class ParseOrderFn(beam.DoFn):
    def process(self, line):
        row = try_parse_order_line(line)
        if row is None:
            return          # the line silently disappears
        yield row
```

versus a `Map`-style version that would have to raise:

```python
beam.Map(parse_order_line)   # raises ValueError on a malformed line
```

The `DoFn` version is more robust — one bad line does not fail the bundle
— but it is also **silent**. If 1% of your input is malformed, your output
is 1% smaller and nothing tells you. This is the argument for a side
output, which chapter 2.5 covered.

The project's `ParseOrderFn` in `project/transforms.py` does exactly this,
and it logs the skip:

```python
def process(self, line: str, timestamp=beam.DoFn.TimestampParam) -> Iterable[Any]:
    row = try_parse_order_line(line)
    if row is None:
        log.warning("skipping malformed order line: %.120s", line)
        return
    if not is_valid_order(row):
        log.warning("skipping invalid order: %s", row.get("order_id"))
        return
    yield row
```

Note the `log.warning` calls. In production, "the pipeline is silently
dropping rows" is a bug you find too late. Logging every dropped row is
verbose but it is *visible*; and a `log.warning` per dropped row is far
cheaper than a side output to a durable sink if the drop rate is low.

### The `DoFn` parameter protocol

A `DoFn` can declare special parameters by giving them default values that
are Beam's parameter sentinels. The sentinel *is* the declaration.

```python
def process(self, element, timestamp=beam.DoFn.TimestampParam):
    ...
```

The parameters are resolved by the runner at call time and injected as
keyword arguments.

| Parameter | Injects | Notes |
|---|---|---|
| `beam.DoFn.TimestampParam` | the element's event timestamp | a `Timestamp` |
| `beam.DoFn.WindowParam` | the window the element belongs to | an `IntervalWindow` |
| `beam.DoFn.PaneInfoParam` | trigger and pane information | a `PaneInfo` |
| `beam.DoFn.ElementParam` | the element, explicitly | rarely needed |
| `beam.DoFn.WindowedValueParam` | the `WindowedValue` wrapper | when you need the raw wrapper |
| `beam.DoFn.KeyParam` | the key of the KV pair | stateful DoFns only |
| `beam.DoFn.SideInputParam` | a side input, by name | |
| `beam.DoFn.StateParam(spec)` | a state handle | stateful DoFns only |
| `beam.DoFn.TimerParam(spec)` | a timer handle | stateful DoFns only |
| `beam.DoFn.WatermarkEstimatorParam` | the watermark estimator | |
| `beam.DoFn.BundleContextParam` | bundle-level context | |
| `beam.DoFn.RestrictionParam` | the restriction tracker | |

The three you will use most are `TimestampParam`, `WindowParam` and
`PaneInfoParam`.

**`TimestampParam`** gives the element's *event timestamp* — the time the
event happened, as opposed to the time it was processed. In batch mode
this is the ingestion timestamp. In streaming mode, for a Pub/Sub source,
it is the time the message was published (from the message attribute), and
it is what windowing uses to assign the element to a window.

The `Timestamp` object has a useful API:

```text
Timestamp.micros           int    microseconds since the epoch (attribute)
Timestamp.seconds()        float  seconds since the epoch (method)
Timestamp.nanos            int    nanoseconds since the epoch (attribute)
Timestamp.to_utc_datetime()  datetime
Timestamp.predecessor()    Timestamp
Timestamp.successor()      Timestamp
```

Note the inconsistency, because it will bite you: **`micros` and `nanos`
are plain attributes, while `seconds()` is a method.** Writing
`timestamp.micros()` raises `TypeError: 'int' object is not callable`,
and it is a confusing error because everything else about `Timestamp`
looks like a method.

**`WindowParam`** gives the `IntervalWindow` the element falls in. The
global window is the interval `(-inf, +inf)` — its `start` and `end` are
the extreme float values, which is why code that does
`window.end - window.start` on the global window produces garbage rather
than an error.

```python
def process(self, element, window=beam.DoFn.WindowParam):
    # A fixed window's start is the epoch hour boundary.
    window_id = window.start.micros // 3_600_000_000
```

**`PaneInfoParam`** gives information about *which firing* of a window this
call is. A `PaneInfo` has:

```text
pane.index        int    0 for the first firing, 1 for the second, ...
pane.is_first     bool
pane.is_last      bool
pane.index == 0 and not is_last   the "on-time" pane
pane.index > 0                    a "late" pane
```

This is how you implement a "emit only the final result" policy, or
"emit the first value and ignore the rest". It is also how you implement
idempotent sinks: check `pane.is_last` before writing.

**`KeyParam`** injects the key of a KV element. It is only legal on a
stateful `DoFn`, and it is required for state and timers to work — state
is scoped per key.

**`WindowedValueParam`** injects the raw `WindowedValue` wrapper, which
carries the value plus its timestamp and windows. You need it when you
want to *re-emit* an element with a modified timestamp, or when you need
the window list rather than just the current window.

### Stateful `DoFn`s: state and timers

This is the most powerful and most misused part of the Beam Python SDK.

A **stateful** `DoFn` is one that declares a `StateSpec` or a `TimerSpec`.
State is per-key, per-window, and **durable**: it survives bundle
boundaries and worker restarts. Timers let you be invoked later, at a
specific point in the watermark or wall-clock time.

```python
import apache_beam as beam
from apache_beam.transforms import userstate
from apache_beam.transforms.userstate import on_timer
from apache_beam.utils.timestamp import Timestamp


class FloatSumFn(beam.CombineFn):
    """Combine the values added to a combining state cell."""

    def create_accumulator(self):
        return 0.0

    def add_input(self, accumulator, value):
        return accumulator + value

    def merge_accumulators(self, accumulators):
        total = 0.0
        for partial in accumulators:
            total += partial
        return total

    def extract_output(self, accumulator):
        return accumulator


class RecordAccumulator(beam.DoFn):
    """Accumulate a per-key running total and emit it as it grows."""

    # `CombiningValueStateSpec` takes the *combine function*, not a coder.
    # The second positional argument is `coder`, but when `combine_fn` is
    # omitted Beam swaps it round and treats that argument as the combine
    # function. Passing a coder here raises:
    #
    #   TypeError: Expected a CombineFn or callable, got FloatCoder
    #
    # So pass the combine function by keyword.
    TOTAL = userstate.CombiningValueStateSpec("total", combine_fn=FloatSumFn())
    LAST_SEEN = userstate.BagStateSpec("last_seen", beam.coders.FloatCoder())
    FLUSH = userstate.TimerSpec("flush", userstate.TimeDomain.WATERMARK)

    def process(
        self,
        element,
        key=beam.DoFn.KeyParam,
        total=beam.DoFn.StateParam(TOTAL),
        last_seen=beam.DoFn.StateParam(LAST_SEEN),
        flush=beam.DoFn.TimerParam(FLUSH),
    ):
        _, value = element
        total.add(float(value))
        last_seen.add(float(value))
        flush.set(Timestamp.now())
        yield (key, total.read())

    @on_timer(FLUSH)
    def on_flush(self, total=beam.DoFn.StateParam(TOTAL)):
        yield total.read()
```

The rules, all of which I have verified against apache-beam 2.77:

**1. A `StateSpec` or `TimerSpec` is a class attribute, declared with
`userstate`.** The available specs are:

| Spec | Purpose |
|---|---|
| `userstate.BagStateSpec(name, coder)` | an append-only multiset |
| `userstate.SetStateSpec(name, coder)` | a set of distinct values |
| `userstate.CombiningValueStateSpec(name, coder=None, combine_fn=None)` | a single value, merged with a combine function — pass `combine_fn=` by keyword, see rule 1a |
| `userstate.ReadModifyWriteStateSpec(name, coder)` | a value you read, modify, and write back |
| `userstate.OrderedListStateSpec(name, coder)` | an ordered list with position-based access |

**1a. `CombiningValueStateSpec` takes a *combine function*, not a coder —
and you must pass it by keyword.** The signature is
`CombiningValueStateSpec(name, coder=None, combine_fn=None)`, but the
constructor contains a trap: if `combine_fn` is `None` and `coder` is
not, it **swaps the two** and treats your coder as the combine
function. Passing a coder positionally therefore fails at pipeline
construction with:

```text
TypeError: Expected a CombineFn or callable, got FloatCoder
```

This is a genuinely confusing error, because the coder you passed is
exactly the kind of thing the second parameter appears to want. The
fix is to always pass the combine function by keyword:

```python
TOTAL = userstate.CombiningValueStateSpec("total", combine_fn=FloatSumFn())
```

The other state specs are not affected: `BagStateSpec`,
`SetStateSpec`, `ReadModifyWriteStateSpec` and `OrderedListStateSpec`
all take a coder in the second position, as you would expect.

**2. The spec is bound to a `process` parameter using
`beam.DoFn.StateParam(SPEC)`.** The parameter name in the signature is
yours to choose; the *spec* determines what it is.

```python
def process(self, element, total=beam.DoFn.StateParam(TOTAL)):
    ...
```

**3. A `TimerSpec` must have an `on_timer` callback, or the pipeline
fails at build time.** The exact error is:

```text
ValueError: DoFn <Accumulator object at 0x110e44> has a TimerSpec without
an associated on_timer callback: TimerSpec(ts-flush).
```

**4. The `@on_timer` decorator takes the `TimerSpec`, not the
`StateSpec`.** This is a natural mistake to make — the callback often
reads state, so it is tempting to decorate with the state spec. The
signature is:

```python
@on_timer(FLUSH)            # the TimerSpec
def on_flush(self, total=beam.DoFn.StateParam(TOTAL)):
    ...
```

**5. The state and timer specs must be distinct objects, and the
`@on_timer` callback must not be overwritten.** Beam validates this:

```text
ValueError: The on_timer callback for TimerSpec(ts-flush) is not the
specified .on_flush method for DoFn <Accumulator object at 0x...>
(perhaps it was overwritten?).
```

**6. The input to a stateful `DoFn` must be a KV PCollection.** Beam
checks the coder:

```python
if not coder.is_kv_coder():
    raise ValueError(
        'Input elements to the transform %s with stateful DoFn must be '
        'key-value pairs.' % self)
```

This is why every stateful `DoFn` in the wild starts with a `Map` that
keys its input.

**7. A plain instance attribute is NOT durable state.** This is the trap.
Consider:

```python
class BrokenAccumulator(beam.DoFn):
    def __init__(self):
        self.total = 0.0

    def process(self, element):
        self.total += float(element)
        yield (element, self.total)
```

On the Direct Runner this appears to work, because everything runs in one
process. On Dataflow it is **wrong**, in three independent ways:

| Failure | What happens |
|---|---|
| **Bundle boundary** | The runner may call `process` on a fresh `DoFn` instance for the next bundle, or on a different worker. `self.total` resets to `0.0`. |
| **Key interleaving** | Two different keys are processed by the same `DoFn` instance. `self.total` mixes their values. |
| **Window interleaving** | The same key in two different windows shares one counter. |

The Direct Runner is actively misleading here. A unit test on the Direct
Runner will pass and the production job will be wrong. This is the single
strongest argument for using `userstate` whenever you are keeping a
per-element running value.

**8. State is not supported in the `GroupIntoBatches` / bundle-less path.**
`GroupIntoBatches` regroups elements into lists, which destroys the KV
shape that state requires. A stateful `DoFn` downstream of
`GroupIntoBatches` receives *lists*, not KV pairs, and the state machinery
has no key to scope the state by. The same applies to the "bundle-less"
execution path used by some runners and by the Python SDK's
`--runner=PrismRunner` in certain modes. If you need state, you need
KV elements and a normal bundle path.

**9. `GroupByKey` and `CombinePerKey` are the alternatives for most
"accumulate per key" use cases.** If all you want is "count or sum per
key", do not write a stateful `DoFn`. Use a combiner — it is dramatically
faster, because the runner can combine incrementally without any state
round-trip. Stateful `DoFn`s are for the cases a combiner cannot express:
"emit a value every N elements", "emit on a timer", "handle a key with
complex per-key logic".

### `with_output_coder` and the type system

Beam infers the output type of a `DoFn` by inspecting the yielded values, and
it needs a **coder** to serialise them. The inference works by running your
`DoFn` on a sample element in a "dry run" — which means the inference pass
can have side effects, and it can fail on inputs it does not understand.

`with_output_coder` lets you state the coder explicitly:

```python
result = (
    src
    | "Parse" >> beam.ParDo(ParseOrderFn()).with_output_coder(
        beam.coders.FastPrimitivesCoder()
    )
)
```

The rule of thumb: **if the `DoFn` yields dicts, always state the coder.**
Beam's inference for `dict` types is not reliable, and an incorrect
inference produces a job that fails on a worker with a coder error that
says nothing about your code.

`FastPrimitivesCoder` is the fast path for simple Python types — dicts,
lists, tuples, strings, numbers. It is significantly faster than the
default `PickleCoder` for these. The project uses it for exactly this
reason.

There is a matching `with_input_types` / `with_output_types` for *type
hints*, which are not coders:

```python
(
    src
    | "Parse" >> beam.ParDo(ParseOrderFn()).with_output_types(
        beam.typehints.Dict[str, beam.typehints.Any]
    )
)
```

Type hints and coders solve different problems. Type hints are for the
runner's benefit (schema, validation, optimisation). Coders are for
serialisation. You often want both.

### The serialisation constraint on your `DoFn`

Your `DoFn` instance is pickled and shipped to the workers. This has real
consequences.

**What can be pickled:**

- Module-level classes and functions.
- Instances of classes defined at module level, whose `__dict__` contains
  only picklable values.

**What cannot:**

- Lambdas assigned as instance attributes.
- Open sockets, database connections, file handles.
- Generators, locks, thread objects.
- Local classes (defined inside a function).

```python
# BAD: a lambda on the instance cannot be pickled
class BadFn(beam.DoFn):
    def __init__(self):
        self.pred = lambda x: x > 0

# BAD: a local class cannot be pickled
def build():
    class LocalFn(beam.DoFn):
        def process(self, x):
            yield x
    return LocalFn()
```

The error surfaces on the worker, not in your editor:

```text
TypeError: cannot pickle 'function' object
AttributeError: Can't pickle local object 'build.<locals>.LocalFn'
```

The reliable rule: **define `DoFn` classes at module level, and keep
`__init__` arguments to plain data** — strings, numbers, tuples, lists,
dicts, and other picklable values.

```python
class RevenueByRegionFn(beam.CombineFn):
    def __init__(self, statuses=("complete",), rates=None):
        self.statuses = tuple(statuses)
        self.rates = dict(rates or CURRENCY_TO_EUR)
```

Note `tuple(statuses)` and `dict(rates or ...)`: converting to concrete
built-in types at construction time means the instance holds only
picklable values, no matter what the caller passed.

`setup()` exists partly to solve this problem. You can pass a *connection
factory* to the `DoFn` and call it in `setup()` on the worker, where the
connection is actually created:

```python
class DatabaseLookupFn(beam.DoFn):
    def __init__(self, dsn):
        self.dsn = dsn          # a string — picklable

    def setup(self):
        self.conn = psycopg2.connect(self.dsn)   # created on the worker

    def teardown(self):
        self.conn.close()
```

### Side inputs

A side input is a second PCollection made available to a `DoFn` or `Map`.
The main use case: a small lookup table that is far too small to be joined
and far too useful to ignore.

```python
import apache_beam as beam
from apache_beam.pvalue import AsIter

with beam.Pipeline() as p:
    reference = p | "ReadRef" >> beam.io.ReadFromText("./product_reference.ndjson")
    orders = p | "ReadOrders" >> beam.io.ReadFromText("./sample_data/orders.csv")

    (
        orders
        | "Enrich" >> beam.Map(
            _enrich_with_category,
            reference=AsIter(reference),
        )
    )
```

The three side-input adapters, and the shape each requires:

| Adapter | Side input shape | Value you get |
|---|---|---|
| `pvalue.AsIter(pcoll)` | any PCollection | a re-iterable collection of every element |
| `pvalue.AsDict(pcoll)` | PCollection of KV pairs | a `dict` |
| `pvalue.AsSingleton(pcoll)` | PCollection with exactly one element | that one element |

`AsIter` is the most flexible and the most common. It gives you a
collection you can iterate over for each element — which means the lookup
is a **linear scan per element**. For the project's small product reference
table that is fine. For a 100,000-row table and a billion-row stream, it is
a quadratic disaster: 10^14 comparisons.

`AsDict` is the right answer for large reference tables, because it gives
you O(1) lookup. It requires the side input to be a PCollection of KV
pairs that the runner can materialise into a `DictCoder`:

```python
from apache_beam.pvalue import AsDict

reference = p | "ReadRef" >> beam.io.ReadFromText("./product_reference.ndjson")
indexed = reference | "Index" >> beam.Map(lambda l: (product_id, category))

(
    orders
    | "Enrich" >> beam.Map(
        lambda order, ref=AsDict(indexed): enrich(order, ref),
    )
)
```

`AsSingleton` requires exactly one element and gives you that element
directly. Use it for a configuration value, a threshold, a schema.

The rule of thumb for side inputs: **side inputs must be small.** Beam
materialises them per worker. A 1 GB side input means 1 GB of memory on
every worker, and the workers are sized by the throughput you need, not by
the lookup. If the reference table is large, you want a join — and for a
keyed join, that is `CoGroupByKey` (chapter 2.8) or a `CombinePerKey`.

### The full picture

```text
element ──▶ process() ──┬──▶ yield value ──────────▶ main output
                         │
                         ├──▶ yield TaggedOutput(t) ─▶ side output t
                         │
                         └──▶ yield nothing ─────────▶ element dropped

  + TimestampParam, WindowParam, PaneInfoParam  → injected per call
  + StateParam / TimerParam                     → per-key, durable
  + side inputs                                 → read-only lookup
```

---

## 🛠️ Hands-On: A Parsing `DoFn` and a Stateful Accumulator

### Step 1 — the `DoFn` parameter protocol

Create `hands_on_dofn.py`:

```python
"""Explore the DoFn parameter protocol: timestamp, window and pane info."""
import apache_beam as beam
from apache_beam.io.textio import ReadFromText, WriteToText
from apache_beam.transforms.window import FixedWindows


class AnnotateFn(beam.DoFn):
    """Attach the element's timestamp and window to each record."""

    def process(
        self,
        line,
        timestamp=beam.DoFn.TimestampParam,
        window=beam.DoFn.WindowParam,
    ):
        parts = line.split(",")
        order_id = parts[0] if parts else ""
        yield {
            "order_id": order_id,
            "ts_micros": timestamp.micros,
            "window_start": window.start.micros,
            "window_end": window.end.micros,
        }


def build(pipeline, input_path, output_path):
    lines = pipeline | "ReadOrders" >> ReadFromText(input_path)

    annotated = (
        lines
        | "Window" >> beam.WindowInto(FixedWindows(3600))
        | "Annotate" >> beam.ParDo(AnnotateFn())
    )

    (
        annotated
        | "Format" >> beam.Map(
            lambda r: f"{r['order_id']},{r['ts_micros']},{r['window_start']}"
        )
        | "Write" >> WriteToText(output_path, num_shards=1, shard_name_template="")
    )


if __name__ == "__main__":
    with beam.Pipeline() as pipeline:
        build(pipeline, "./sample_data/orders.csv", "./out/hands_on/annotated")
```

Run it and look at the output:

```bash
python hands_on_dofn.py
head -3 out/hands_on/annotated*
```

You will see that `window_start` is a multiple of 3,600,000,000 — one hour
in microseconds — because `FixedWindows(3600)` snaps window boundaries to
the hour. `window_end` is exactly one hour after `window_start`.

Now the crucial experiment: **remove the `WindowInto` and re-run.**

```python
annotated = lines | "Annotate" >> beam.ParDo(AnnotateFn())
```

Without an explicit `WindowInto`, the element is in the global window, whose
bounds are the extreme float values. `window_start` becomes a huge negative
number and `window_end` a huge positive one. That is not a bug — it is the
global window, and it is a common source of confusion when someone
computes `window.end - window.start` and gets nonsense.

### Step 2 — a `ParseOrderFn` with `TimestampParam` and `WindowParam`

Now build a realistic parsing `DoFn` that uses both parameters and routes
malformed lines to a side output. Create `hands_on_parse.py`:

```python
"""A ParseOrderFn that uses TimestampParam and WindowParam, with a DLQ."""
import apache_beam as beam
from apache_beam.io.textio import ReadFromText, WriteToText
from apache_beam.pvalue import TaggedOutput
from apache_beam.transforms.window import FixedWindows

from project.transforms import is_valid_order, normalise_currency, try_parse_order_line


class ParseOrderFn(beam.DoFn):
    """Parse an order line, timestamping it and tagging bad rows for the DLQ."""

    def process(
        self,
        line,
        timestamp=beam.DoFn.TimestampParam,
        window=beam.DoFn.WindowParam,
    ):
        row = try_parse_order_line(line)
        if row is None:
            yield TaggedOutput("malformed", line)
            return
        if not is_valid_order(row):
            yield TaggedOutput("invalid", line)
            return

        # The event timestamp drives the window; the window tells us the hour.
        window_hour = window.start.micros // 3_600_000_000
        row["window_hour"] = window_hour
        row["event_ts_micros"] = timestamp.micros
        row["revenue_eur"] = normalise_currency(
            float(row["amount"]), row["currency"]
        )
        yield row


def build(pipeline, input_path, output_prefix):
    lines = pipeline | "ReadOrders" >> ReadFromText(input_path)

    routed = (
        lines
        | "Window" >> beam.WindowInto(FixedWindows(3600))
        | "Parse" >> beam.ParDo(ParseOrderFn()).with_outputs(
            "malformed", "invalid", main="main"
        )
    )

    (
        routed["main"]
        | "Format" >> beam.Map(
            lambda r: f"{r['order_id']},{r['region']},{r['revenue_eur']},{r['window_hour']}"
        )
        | "WriteMain" >> WriteToText(
            output_prefix + "_main", num_shards=1, shard_name_template=""
        )
    )

    for tag in ("malformed", "invalid"):
        (
            routed[tag]
            | f"Format{tag.capitalize()}" >> beam.Map(lambda l: l)
            | f"Write{tag.capitalize()}" >> WriteToText(
                output_prefix + f"_{tag}", num_shards=1, shard_name_template=""
            )
        )


if __name__ == "__main__":
    with beam.Pipeline() as pipeline:
        build(pipeline, "./sample_data/orders.csv", "./out/hands_on/parsed")
```

Run it:

```bash
python hands_on_parse.py
echo "--- main ---"
head -3 out/hands_on/parsed_main*
echo "--- malformed ---"
head -3 out/hands_on/parsed_malformed*
echo "--- invalid ---"
head -3 out/hands_on/parsed_invalid*
```

Three outputs, one read of the source. The main output has the enriched
rows; the two side outputs have the rejects, separated by reason.

### Step 3 — a `RecordAccumulator` with real user state

Now the stateful `DoFn`. Create `hands_on_stateful.py`:

```python
"""A stateful DoFn: a per-key running total, durable across bundles."""
import apache_beam as beam
from apache_beam.io.textio import ReadFromText, WriteToText
from apache_beam.transforms import userstate
from apache_beam.transforms.userstate import on_timer
from apache_beam.utils.timestamp import Timestamp


class FloatSumFn(beam.CombineFn):
    """Combine the values added to a combining state cell."""

    def create_accumulator(self):
        return 0.0

    def add_input(self, accumulator, value):
        return accumulator + value

    def merge_accumulators(self, accumulators):
        total = 0.0
        for partial in accumulators:
            total += partial
        return total

    def extract_output(self, accumulator):
        return accumulator


class RecordAccumulator(beam.DoFn):
    """Accumulate a per-key running total, flushing on the watermark."""

    # `CombiningValueStateSpec` takes the *combine function*, not a coder.
    # Pass it by keyword. If you pass a coder in the second positional
    # slot, Beam swaps the arguments and treats the coder as the combine
    # function, which raises:
    #
    #   TypeError: Expected a CombineFn or callable, got FloatCoder
    TOTAL = userstate.CombiningValueStateSpec("total", combine_fn=FloatSumFn())
    SEEN = userstate.BagStateSpec("seen", beam.coders.FloatCoder())
    FLUSH = userstate.TimerSpec("flush", userstate.TimeDomain.WATERMARK)

    def process(
        self,
        element,
        key=beam.DoFn.KeyParam,
        total=beam.DoFn.StateParam(TOTAL),
        seen=beam.DoFn.StateParam(SEEN),
        flush=beam.DoFn.TimerParam(FLUSH),
    ):
        _, value = element
        total.add(float(value))
        seen.add(float(value))
        flush.set(Timestamp.now())
        yield (key, total.read())

    @on_timer(FLUSH)
    def on_flush(self, total=beam.DoFn.StateParam(TOTAL)):
        yield ("flushed", total.read())


def build(pipeline, input_path, output_path):
    lines = pipeline | "ReadOrders" >> ReadFromText(input_path)

    keyed = (
        lines
        | "Extract" >> beam.Map(
            lambda l: (l.split(",")[3] if len(l.split(",")) > 3 else "?", 1.0)
        )
    )

    accumulated = keyed | "Accumulate" >> beam.ParDo(RecordAccumulator())

    (
        accumulated
        | "Format" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]}")
        | "Write" >> WriteToText(output_path, num_shards=1, shard_name_template="")
    )


if __name__ == "__main__":
    with beam.Pipeline() as pipeline:
        build(pipeline, "./sample_data/orders.csv", "./out/hands_on/accumulated")
```

Run it:

```bash
python hands_on_stateful.py
head -5 out/hands_on/accumulated*
```

The output shows a running total per region, growing as more elements for
that region arrive.

### Step 4 — prove that a plain attribute is not durable

This is the experiment that matters most. Create `hands_on_notdurable.py`:

```python
"""Demonstrate that a plain instance attribute is not durable state."""
import apache_beam as beam
from apache_beam.io.textio import ReadFromText, WriteToText


class BrokenAccumulator(beam.DoFn):
    """A DoFn that 'accumulates' with a plain attribute. This is a bug."""

    def __init__(self):
        self.total = 0.0

    def process(self, element):
        # `element` is the KV pair produced by the "Key" step below.
        key, value = element
        self.total += float(value)
        yield (key, self.total)


def build(pipeline, input_path, output_path):
    lines = pipeline | "ReadOrders" >> ReadFromText(input_path)

    keyed = lines | "Key" >> beam.Map(lambda l: ("all", 1.0))

    accumulated = keyed | "Accumulate" >> beam.ParDo(BrokenAccumulator())

    (
        accumulated
        | "Format" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]}")
        | "Write" >> WriteToText(output_path, num_shards=1, shard_name_template="")
    )


if __name__ == "__main__":
    with beam.Pipeline() as pipeline:
        build(pipeline, "./sample_data/orders.csv", "./out/hands_on/notdurable")
```

Run it:

```bash
python hands_on_notdurable.py
head -5 out/hands_on/notdurable*
```

Now compare the two versions. The broken version's maximum running total
is the **whole** input size — around 5001.0 for a 5001-row file — because
`self.total` is a single number shared by every element, regardless of
key:

```bash
cut -d, -f2 out/hands_on/notdurable | sort -n | tail -1
```

The stateful version's maximum is about **1284.0** — roughly a quarter
of the input, because the total is *per region*, and there are four
regions:

```bash
cut -d, -f2 out/hands_on/accumulated | sort -n | tail -1
```

That difference is the bug. `self.total` is not scoped to the key at
all, and it is not durable.

The subtlety, and the reason this experiment is worth running: **on the
Direct Runner the broken version appears to accumulate correctly** —
you see a monotonically increasing sequence, because the runner keeps
the `DoFn` instance alive for the duration of the bundle and your input
happens to fit in one. The two real defects only bite under conditions
you will meet in production:

- **Key blindness.** The attribute is global to the instance, not per
  key. The moment the runner processes elements for two keys
  interleaved, the totals contaminate each other — visible above as a
  maximum of 5001 instead of ~1284.
- **Bundle blindness.** At a bundle boundary the attribute resets, so
  the running total silently jumps back down. This does not appear at
  all on a small local run, and does appear on Dataflow, where the
  instance is a different object on a different worker.

This is why "it passed on my machine" is not a defence here.

### Step 5 — the `DoFn` lifecycle hooks

Add a `DoFn` that uses `setup` and `teardown` and logs the lifecycle:

```python
import apache_beam as beam
import logging


class LifecycleFn(beam.DoFn):
    """Log each lifecycle hook so you can see the ordering."""

    def setup(self):
        logging.info("SETUP")

    def start_bundle(self):
        logging.info("START_BUNDLE")

    def process(self, element):
        yield element

    def finish_bundle(self):
        logging.info("FINISH_BUNDLE")

    def teardown(self):
        logging.info("TEARDOWN")


with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create([1, 2, 3])
        | "Lifecycle" >> beam.ParDo(LifecycleFn())
        | "Print" >> beam.Map(print)
    )
```

Run with logging enabled:

```bash
python -c "
import logging
logging.basicConfig(level=logging.INFO)
exec(open('hands_on_lifecycle.py').read())
" 2>&1 | grep -E "SETUP|START_BUNDLE|FINISH_BUNDLE|TEARDOWN"
```

You will see `SETUP` once, then alternating `START_BUNDLE` /
`FINISH_BUNDLE`, then `TEARDOWN` once. This is the shape to internalise:
**setup and teardown are per-instance; start_bundle and finish_bundle are
per-bundle.**

---

## 🛠️ Common Errors and Fixes

### `ValueError: DoFn ... has a TimerSpec without an associated on_timer callback`

```text
ValueError: DoFn <Accumulator object at 0x110e44> has a TimerSpec without
an associated on_timer callback: TimerSpec(ts-flush).
```

Every `TimerSpec` must have a callback. Add one, and decorate it with the
**`TimerSpec`**:

```python
@on_timer(FLUSH)
def on_flush(self, total=beam.DoFn.StateParam(TOTAL)):
    yield total.read()
```

### `ValueError: @on_timer decorator expected TimerSpec.`

```text
ValueError: @on_timer decorator expected TimerSpec.
```

You decorated with the `StateSpec` instead of the `TimerSpec`. The
decorator takes the timer.

### `ValueError: The on_timer callback for TimerSpec(ts-flush) is not the specified .on_flush method for DoFn ...`

```text
ValueError: The on_timer callback for TimerSpec(ts-flush) is not the
specified .on_flush method for DoFn <Accumulator object at 0x110e44>
(perhaps it was overwritten?).
```

Something reassigned the callback method after the decorator ran — often a
subclass overriding it, or a copy-paste that renamed the method but not the
decorator argument. The name in the decorator's target and the method name
must agree.

### `ValueError: Input elements to the transform ParDo(...) with stateful DoFn must be key-value pairs.`

```text
ValueError: Input elements to the transform ParDo(Accumulate) with stateful
DoFn must be key-value pairs.
```

Your input to the stateful `DoFn` is not a KV PCollection. Key it first:

```python
keyed = lines | "Key" >> beam.Map(lambda l: (region, value))
accumulated = keyed | "Accumulate" >> beam.ParDo(RecordAccumulator())
```

### `AttributeError: 'Accumulator' object has no attribute 'total'`

```text
AttributeError: 'Accumulator' object has no attribute 'total'
```

You accessed the state handle as an attribute, but state handles are only
available as the injected `StateParam` argument. `self.total` is a plain
Python attribute, not the state. Use the injected parameter.

### `TypeError: Expected a CombineFn or callable, got FloatCoder`

```text
TypeError: Expected a CombineFn or callable, got FloatCoder
```

You passed a coder as the second positional argument to
`userstate.CombiningValueStateSpec`. The constructor's signature is
`CombiningValueStateSpec(name, coder=None, combine_fn=None)`, but when
`combine_fn` is omitted it **swaps the two arguments** and treats your
coder as the combine function. A coder is not callable, so Beam
rejects it.

Pass the combine function by keyword:

```python
# wrong
TOTAL = userstate.CombiningValueStateSpec("total", beam.coders.FloatCoder())

# right
TOTAL = userstate.CombiningValueStateSpec("total", combine_fn=FloatSumFn())
```

This only affects `CombiningValueStateSpec`. The other state specs —
`BagStateSpec`, `SetStateSpec`, `ReadModifyWriteStateSpec`,
`OrderedListStateSpec` — do take a coder in the second position.

### `TypeError: cannot pickle 'function' object`

```text
TypeError: cannot pickle 'function' object
```

A lambda is stored on the `DoFn` instance, or a local function is used as a
`DoFn`. Both are unpicklable. Move the function to module level, or use a
class with `__call__`.

### `AttributeError: Can't pickle local object 'build.<locals>.LocalFn'`

```text
AttributeError: Can't pickle local object 'build.<locals>.LocalFn'
```

The `DoFn` class is defined inside a function. Move it to module level. The
worker needs to import it by name.

### `apache_beam.transforms.userstate.DeterministicTag` — state and a `GroupIntoBatches` pipeline

If you place a stateful `DoFn` after `beam.GroupIntoBatches`, the elements
it receives are *lists*, not KV pairs, and the state has no key to scope
by. The build may succeed and the run will fail, or — worse — produce
per-batch rather than per-key state. Keep stateful `DoFn`s on a KV path
with a normal bundle flow.

### The output is missing rows and nothing was logged

Your `process` yielded nothing for those rows. Add a `log.warning` in the
drop branch — the project's `ParseOrderFn` does exactly this. Silence in
a `DoFn` is a data-loss bug waiting to be discovered by an auditor.

### `TypeError: 'AsDict' object is not subscriptable`

```text
TypeError: 'AsDict' object is not subscriptable
```

`pvalue.AsDict` must be used as a *default argument* of the function, and
the side input must be a PCollection of KV pairs that the runner can
materialise as a dict:

```python
from apache_beam.pvalue import AsDict

indexed = reference | "Index" >> beam.Map(lambda r: (r["product_id"], r["category"]))
(
    orders
    | "Enrich" >> beam.Map(
        lambda order, ref=AsDict(indexed): enrich(order, ref),
    )
)
```

If you indexed a list of dicts, build the KV PCollection first.

### `ValueError: Type of ... is not assignable to type hint ...`

A type hint or coder mismatch. Either the `DoFn` yields something
different from what you declared, or your `with_output_coder` is wrong.
For dict outputs, drop the hint and state the coder:

```python
orders = orders | "Parse" >> beam.ParDo(ParseOrderFn()).with_output_coder(
    beam.coders.FastPrimitivesCoder()
)
```

---

## 💡 Production Notes

- **`setup()` is the biggest performance lever in a `DoFn`.** If your
  `process` calls `json.loads` on a 40 KB configuration blob, or builds a
  lookup dict, you are doing that work *per element*. Move it to `setup()`
  and you do it once per worker. On a Dataflow job with 200 workers
  processing 2 billion elements, the difference between 2 billion
  deserialisations and 200 is roughly 4 CPU-hours versus 4 CPU-seconds.
- **The Direct Runner lies about state.** A `DoFn` that accumulates into a
  plain attribute passes the Direct Runner tests and produces wrong numbers
  on Dataflow. This is the single most common way a Beam pipeline ships
  broken. If you are keeping per-key running state, use `userstate`, and
  test with a `CombinePerKey` cross-check as chapter 2.7 shows.
- **State and timers are not supported everywhere.** The Python SDK's
  stateful processing is implemented per-runner, and some execution paths —
  including the bundle-less path used by `GroupIntoBatches` — cannot
  support it. Check that your runner and your pipeline shape support state
  before you design around it. If you need a portable aggregation, use a
  combiner; stateful `DoFn`s are a Java-SDK-strong, Python-SDK-risky tool.
- **Prefer a combiner to a stateful `DoFn` for anything expressible as an
  aggregation.** `CombinePerKey` merges partial results *during* the
  shuffle, so the network transfer is proportional to the number of keys,
  not the number of elements. A stateful `DoFn` that emits a running total
  per element transfers one record per element. For a million elements and
  a thousand keys, that is a thousandfold difference in network traffic.
- **A `DoFn` instance is pickled per worker.** Keep `__init__` arguments
  small. Passing a 50 MB lookup table into the `DoFn` constructor means
  shipping 50 MB to every worker at startup; passing the *path* and
  loading it in `setup()` means the same bytes but loaded lazily and
  possibly cached at the OS level.
- **Do not use `setup()` for anything with a side effect on a shared
  system.** `setup()` runs once per worker, and with 200 workers you get
  200 concurrent calls. A `setup()` that writes to a database creates 200
  racing transactions.
- **Side inputs are per-worker memory.** A 1 GB `AsIter` side input costs
  1 GB of RAM per worker. Workers are sized by throughput, so a 200-worker
  job spends 200 GB on the same lookup. Above roughly 50 MB, use a join.
- **The `process` generator is a generator, not a list.** Yield as you
  go; do not build a list and return it. A `DoFn` that materialises its
  entire output in memory defeats the bundle model and can OOM a worker
  on a large group.
- **A `DoFn` that yields nothing drops the element.** This is a feature
  (it is how `FlatMap` filters) and a footgun (it is how data vanishes).
  Log every drop, and consider a side output for anything you would have
  to explain to an auditor.
- **`PaneInfoParam` is how you make sinks idempotent.** Check
  `pane.is_last` before a final write, so that a retried bundle does not
  double-count in a downstream system. Retries are normal on Dataflow; a
  non-idempotent sink is a data-corruption bug waiting for a network blip.
- **Bundle size is a tuning knob, not a constant.** Large bundles amortise
  per-element overhead but increase memory per worker and make retries
  expensive. If your `DoFn` has heavy per-element cost, a smaller bundle
  spreads it better. If it has heavy per-bundle setup, a larger bundle
  wins. Know which you have.

---

## 🔑 Key Takeaways

- `beam.Map`, `beam.FlatMap` and `beam.ParDo` are all `ParDo`. Reach for
  `ParDo` when you need side inputs, side outputs, `DoFn` parameters, or
  user state.
- The `DoFn` lifecycle is `setup` → (`start_bundle` → `process` × N →
  `finish_bundle`)\* → `teardown`. `setup`/`teardown` are per-instance;
  `start_bundle`/`finish_bundle` are per-bundle.
- `process` is a generator. **Yielding nothing drops the input element**,
  silently. Log every drop.
- `DoFn` parameters are declared as default arguments: `timestamp=
  beam.DoFn.TimestampParam`, `window=beam.DoFn.WindowParam`,
  `pane_info=beam.DoFn.PaneInfoParam`, `key=beam.DoFn.KeyParam`. A
  `TimerSpec` **must** have an `@on_timer` callback, and the decorator
  takes the `TimerSpec` — not the `StateSpec`. Both rules are enforced at
  build time.
- A **plain instance attribute is not durable state.** It resets at bundle
  boundaries, mixes keys, and mixes windows. The Direct Runner hides this
  bug; Dataflow exposes it.
- State is per-key and per-window, and it is **not supported in the
  bundle-less / `GroupIntoBatches` path**. Use a combiner where you can.
- `CombiningValueStateSpec` takes a **combine function**, and you must
  pass it by keyword — a coder in that slot is silently reinterpreted as
  the combine function and fails with `TypeError`.
- Your `DoFn` instance is pickled to the workers: define classes at
  module level, keep `__init__` arguments to plain data, and create
  resources in `setup()`. Always state the output coder for
  dict-producing `DoFn`s with
  `.with_output_coder(beam.coders.FastPrimitivesCoder())` — Beam's type
  inference for dicts is not reliable.

---

## 📚 Practice Exercises

1. **Add a `PaneInfoParam`.** Extend the `AnnotateFn` from the hands-on to
   inject `pane_info=beam.DoFn.PaneInfoParam` and emit `pane.index` and
   `pane.is_last` alongside the timestamp. Run it over a windowed input
   with `beam.transforms.trigger.AfterCount(100)` and observe the pane
   index increment. *Expected:* index 0 on the first firing, 1 on the
   second.

2. **Prove the `setup()` amortisation.** Write a `DoFn` whose `setup()`
   sleeps for one second, and one whose `process` sleeps for one second.
   Run each over 1,000 elements on the Direct Runner and time them.
   *Expected:* the `setup()` version is dramatically faster, because
   `setup()` runs once, not 1,000 times.

3. **Use `with_output_coder`.** Write a `DoFn` that yields a dict and run
   it without an explicit coder, then with
   `.with_output_coder(beam.coders.FastPrimitivesCoder())`. Inspect the
   pipeline graph in both cases and note the coder attached to the output.
   *Expected:* the explicit coder is visible and stable.

4. **Break the pickling rule deliberately.** Add a lambda to a `DoFn`'s
   `__init__` and run the pipeline. Capture the exact error. Then move
   the lambda to module level and confirm it works. *Expected:*
   `TypeError: cannot pickle 'function' object` on the worker.

5. **Build a side-input enrichment with `AsDict`.** Read
   `sample_data/product_reference.ndjson`, index it by `product_id`, and
   enrich each order with its category using `pvalue.AsDict`. Compare the
   result with an `AsIter`-based linear-scan version.
   *Expected:* identical output; the `AsDict` version is O(1) per lookup.

6. **Reflection.** A pipeline accumulates a per-customer lifetime balance
   and writes it to BigQuery on every event. Explain, in terms of bundle
   boundaries, key interleaving and window interleaving, what goes wrong
   if the accumulation uses a plain attribute instead of `userstate`.

---

## 📖 Further Reading

- Apache Beam: ParDo — https://beam.apache.org/documentation/programming-guide/#pardo
- Apache Beam: DoFn sids — https://beam.apache.org/documentation/programming-guide/#dofn-sids
- Apache Beam: State and Timers — https://beam.apache.org/documentation/programming-guide/#state-and-timers
- Apache Beam Python API: `beam.DoFn` — https://beam.apache.org/documentation/sdks/python/apache_beam.sdk.html#apache_beam.DoFn
- Apache Beam Python API: `apache_beam.transforms.userstate` — https://beam.apache.org/documentation/sdks/python/apache_beam.transforms.userstate.html
- Google Cloud Dataflow: Dataflow streaming model — https://cloud.google.com/dataflow/docs/concepts/streaming-processing
