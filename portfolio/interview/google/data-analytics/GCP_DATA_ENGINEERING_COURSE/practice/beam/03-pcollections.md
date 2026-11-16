# 03 — PCollections

> **Practice Module 03 · Beam · 40 minutes**

## 🎯 What you will learn

- What a PCollection actually is: a *distributed, parallel collection of elements*.
- The seven properties that define it, and the code that demonstrates each one.
- Why a PCollection is **immutable**, and what that forces you to write.
- The difference between a **bounded** and an **unbounded** PCollection, and why the
  distinction changes what a pipeline can do.
- Why you cannot address an individual element.

---

## 🧠 Concept

A **PCollection** is the data representation in Beam: a distributed, parallel
collection of elements. It is not a list. It is a *promise* about data that a runner
will distribute across workers.

It has seven properties. Each one is worth being able to state, because every Beam
interview question eventually turns into one of them.

| # | Property | What it means |
|---|---|---|
| 1 | **Immutability** | A transform returns a *new* PCollection. It never modifies the old one. |
| 2 | **Unbounded** | Potentially infinite. A stream. The source assigns timestamps. |
| 3 | **Bounded** | Known, fixed size. A batch file. Every element gets the same timestamp. |
| 4 | **Element type** | Any type, but all elements in one PCollection share a type. |
| 5 | **Operation type** | No grained operations. You cannot address element *n*. |
| 6 | **Timestamps** | Every element carries one. Windows are built from them. |
| 7 | **Ownership** | A PCollection belongs to the Pipeline that created it. |

### 1 — Immutability

This is the property that shapes how you write Beam code. If `Map` mutated its
input, then a PCollection you kept a reference to would change under you, and the
graph would not be a graph — it would be a sequence of side effects.

So a transform *produces* a new PCollection. To keep the old one, you keep the
variable. That is why the lab material writes:

```python
pc1 = pipeline | "Read" >> beam.io.ReadFromText(path)
pc2 = pc1   | "Map"   >> beam.Map(fn)
pc3 = pc2   | "Filter" >> beam.Filter(pred)
```

`pc1` still holds the original rows after `pc2` and `pc3` have been applied.

### 2 and 3 — Bounded versus unbounded

- A **bounded** PCollection has a known, finite size. `ReadFromText` on a file
  produces one. Every element gets the *same* timestamp — the minimum timestamp of
  the input.
- An **unbounded** PCollection has no known end. `ReadFromPubSub` produces one. The
  source assigns each element a timestamp, usually the event's own time.

The distinction is not academic. `GroupByKey` on an unbounded PCollection cannot
finish — there is always more data. So a streaming pipeline needs **windowing** to
turn the unbounded stream into a set of bounded groups. That is the whole reason
module 06 exists.

### 4 — Element type

All elements in one PCollection have the same type. `Map` may change the type of
the PCollection it produces (that is allowed), but within one PCollection the type
is uniform. Beam uses this for type checking: a `CombinePerKey` applied to a
PCollection of ints, rather than tuples, fails at graph-construction time with a
`TypeCheckError` — before any data moves.

`TypeCheckError` derives from `Exception`, **not** from `TypeError`. Catching it
with `except TypeError` does not work; import it explicitly from
`apache_beam.typehints.decorators`.

### 5 — Operation type

There are no grained operations. You cannot write `pc[3]`, you cannot call
`pc.append(...)`, you cannot loop over a PCollection. Beam has no notion of "the
tenth element". The runner is free to split, reorder and parallelise the elements
any way it likes, because your code cannot depend on their order or position.

This is also why **Beam output order is not guaranteed**. Two runs of the same
pipeline can produce the same elements in a different order. Any lab that prints
results must either sort them or compare them as sets.

### 6 — Timestamps

Every element carries a timestamp. This is what makes windowing possible: a window
is a time range, and elements are assigned to windows by their timestamps.

### 7 — Ownership

A PCollection belongs to the specific `Pipeline` object that created it. You cannot
pass a PCollection to another pipeline, and you cannot reuse one across pipelines.

---

## 🛠️ Hands-On

### 💻 Runs locally — immutability: the original survives

Two branches hang off the same source. The `Map` produces a *new* PCollection,
so `pc1` still holds the original rows afterwards.

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions([
    "--runner=DirectRunner",
    "--environment_type=LOOPBACK",
])

with beam.Pipeline(options=options) as p:
    pc1 = p | "Create" >> beam.Create([1, 2, 3])
    pc2 = pc1 | "Double" >> beam.Map(lambda x: x * 2)

    # pc1 is untouched by the Map. A transform produces a new PCollection.
    _ = pc1 | "Show original" >> beam.Map(lambda x: print(f"original: {x}"))
    _ = pc2 | "Show doubled" >> beam.Map(lambda x: print(f"doubled:  {x}"))
```

Expected output (unordered):

```text
original: 1
doubled:  2
original: 2
doubled:  4
original: 3
doubled:  6
```

Note what this transcript is *not* promising. The two branches are independent,
and the runner is free to interleave them differently on every run — the
ordering above is one valid arrangement, not a contract. Run it again and you
may well see `doubled` first. This is property 5 in action: **there is no
guaranteed order**.

To get a transcript you can actually diff, collect the results and sort them.
That is the next block.

### 💻 Runs locally — the same pipeline, with a stable transcript

Collect both branches under one key, then sort the collected list. The
ordering problem disappears, and `pc1` is still visibly unmodified.

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions([
    "--runner=DirectRunner",
    "--environment_type=LOOPBACK",
])

with beam.Pipeline(options=options) as p:
    pc1 = p | "Create" >> beam.Create([1, 2, 3])
    pc2 = pc1 | "Double" >> beam.Map(lambda x: x * 2)

    originals = pc1 | "Label original" >> beam.Map(lambda x: ("all", f"original: {x}"))
    doubled = pc2 | "Label doubled" >> beam.Map(lambda x: ("all", f"doubled:  {x}"))

    merged = (originals, doubled) | "Merge" >> beam.Flatten()
    grouped = merged | "Group" >> beam.GroupByKey()
    _ = (
        grouped
        | "Sort" >> beam.Map(lambda kv: sorted(kv[1]))
        | "Print" >> beam.Map(print)
    )
```

Expected output:

```text
['doubled:  2', 'doubled:  4', 'doubled:  6', 'original: 1', 'original: 2', 'original: 3']
```

Two lessons in one block. The elements are sorted, so the transcript is
reproducible — and the labels prove which PCollection each element came from.
`pc1` yielded `1, 2, 3`; the doubling lives entirely in `pc2`.

Note the pattern, because it is the general one: **Beam cannot sort
PCollections directly.** You group everything under a key, `GroupByKey`
reassembles it as one list, and you sort that list in Python. This is also why
`beam.Map(lambda x: x)` after a `Flatten` is *not* a sort — it is a no-op that
looks like one.

### 💻 Runs locally — bounded PCollections all share one timestamp

A bounded source stamps every element with the *minimum* timestamp of the input.
The timestamp itself is only visible from inside a `DoFn`, via the
`TimestampParam` window parameter.

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions([
    "--runner=DirectRunner",
    "--environment_type=LOOPBACK",
])

class ShowTs(beam.DoFn):
    def process(self, element, ts=beam.DoFn.TimestampParam):
        yield f"{element} @ {ts}"

with beam.Pipeline(options=options) as p:
    (
        p
        | "Create" >> beam.Create(["a", "b", "c"])
        | "Stamp" >> beam.ParDo(ShowTs())
        | "Print" >> beam.Map(print)
    )
```

Expected output:

```text
a @ Timestamp(-9223372036854.775000)
b @ Timestamp(-9223372036854.775000)
c @ Timestamp(-9223372036854.775000)
```

Three facts in one block.

**Every element carries the same timestamp.** The three values are identical,
because a bounded source stamps the whole PCollection with one time — the
minimum timestamp of the input. In a streaming source, each element carries its
own event time instead.

**The value is Beam's minimum timestamp, not the epoch.** `Create` has no
timestamp of its own to offer, so it uses `Timestamp.MIN_TIMESTAMP`, which is
`-9223372036854.775000` seconds. That is the floor of the representable range,
not "no timestamp" and not zero.

**`to_utc_datetime()` overflows on it.** This is a real trap, and it catches
people who try to format the timestamp as a date:

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions([
    "--runner=DirectRunner",
    "--environment_type=LOOPBACK",
])

class ShowTs(beam.DoFn):
    def process(self, element, ts=beam.DoFn.TimestampParam):
        try:
            print(f"{element} @ {ts.to_utc_datetime()}")
        except OverflowError as e:
            print(f"{element} @ {ts}  (not a representable datetime: {e})")

with beam.Pipeline(options=options) as p:
    (
        p
        | "Create" >> beam.Create(["a", "b", "c"])
        | "Stamp" >> beam.ParDo(ShowTs())
    )
```

Expected output:

```text
a @ Timestamp(-9223372036854.775000)  (not a representable datetime: date value out of range)
b @ Timestamp(-9223372036854.775000)  (not a representable datetime: date value out of range)
c @ Timestamp(-9223372036854.775000)  (not a representable datetime: date value out of range)
```

Left unhandled, the same code raises `OverflowError: date value out of range
[while running 'Stamp']` and the job fails. `MIN_TIMESTAMP` is roughly a
billion years before the epoch, which no `datetime` can represent. When you
need a readable timestamp, convert it yourself, or read the window's own
`start`/`end`, which the runner has already clamped to something printable.

### 💻 Runs locally — element type is enforced at graph-construction time

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.typehints.decorators import TypeCheckError

options = PipelineOptions([
    "--runner=DirectRunner",
    "--environment_type=LOOPBACK",
])

# This raises before any data moves.
try:
    with beam.Pipeline(options=options) as p:
        (
            p
            | "Create" >> beam.Create([1, 2, 3])
            | "CombinePerKey" >> beam.CombinePerKey(sum)
        )
except TypeCheckError as e:
    print(f"rejected at graph time: {type(e).__name__}")
    print("CombinePerKey needs (key, value) tuples, not bare ints")
```

Expected output:

```text
rejected at graph time: TypeCheckError
CombinePerKey needs (key, value) tuples, not bare ints
```

Beam checks the element type when the graph is built, so this failure costs
nothing — no job was submitted, no data was read. Note that `TypeCheckError`
derives straight from `Exception`, *not* from `TypeError`, so `except
TypeError` will not catch it. Import it explicitly:

```python
from apache_beam.typehints.decorators import TypeCheckError
```

### 💻 Runs locally — no grained operations

A PCollection exposes none of the sequence protocol. You cannot index it, take
its length, or iterate over it.

```python
import apache_beam as beam

dunder = ("__getitem__", "__len__", "__iter__")
exposed = [name for name in dunder if hasattr(beam.PCollection, name)]

print("A PCollection has no grained operations.")
print(f"  exposed of {dunder}: {exposed or 'none'}")
```

Expected output:

```text
A PCollection has no grained operations.
  exposed of ('__getitem__', '__len__', '__iter__'): none
```

And `beam.Map(lambda x: x)` is not a sort — it is a no-op that looks like one.
Beam cannot sort a PCollection. If you need ordered output, group the elements
under one key, `GroupByKey` them back into a list, and sort that list in
Python.

---

## 🛠️ Common Errors and Fixes

### `TypeCheckError: The transform 'Sum' requires PCollections of type 'Tuple[...]'`

`CombinePerKey` and `GroupByKey` need key-value pairs. Map to a tuple first:
`beam.Map(lambda x: ("key", x))`.

### `AttributeError: 'PCollection' object has no attribute 'append'`

You are treating a PCollection like a list. It is not one — use a transform.

### The output order changed between two runs

That is expected. Beam does not guarantee element order. Sort the results before
comparing them, or compare them as sets.

### `AttributeError: type object 'DoFn' has no attribute 'TimestampParam'`

On older Beam the parameter was called `beam.DoFn.timestamp`. On current Beam the
symbols are `beam.DoFn.TimestampParam`, `beam.DoFn.WindowParam` and
`beam.DoFn.StateParam`. `StateParam` additionally needs a `StateSpec` object, not
a string.

### `OverflowError: date value out of range`

You called `to_utc_datetime()` on Beam's `MIN_TIMESTAMP` — the value a bounded
source stamps on its elements. It is about a billion years before the epoch, so
no `datetime` can hold it. Print the `Timestamp` directly, or read the window's
own `start`/`end`.

### `except TypeError` did not catch the `TypeCheckError`

`TypeCheckError` inherits from `Exception`, not from `TypeError`. Import it
explicitly:

```python
from apache_beam.typehints.decorators import TypeCheckError
```

### The output order changed between two runs

That is expected. Beam does not guarantee element order. Sort the results before
comparing them, or compare them as sets. Note that this suite's verifier knows
the difference: a block headed `Expected output (unordered):` is compared as a
multiset of lines, and one headed `Expected output:` must match exactly.

---

## 💡 Production Notes

- **Immutability is a feature.** It is what lets the runner fuse steps, reorder
  work, and retry safely. A pipeline that mutates shared state cannot be retried.
- **Bounded and unbounded change the shape of the code.** A batch pipeline ends at a
  sink. A streaming pipeline needs windows, triggers and watermarks, or it never
  produces output at all.
- **Never rely on order.** If your business logic needs an ordering, put it in the
  data — a sequence number, a timestamp — and sort on it explicitly.
- **Type errors are cheap.** A `TypeCheckError` at graph time is free; the same
  mistake found in production is a failed job and a page.

---

## 🔑 Key Takeaways

- A PCollection is a **distributed, parallel collection of elements** — not a list.
- **Immutable**: transforms return new PCollections. The old one is unchanged.
- **Bounded** = finite, all elements share one timestamp. **Unbounded** = a stream,
  each element carries its own.
- A bounded source stamps its elements with Beam's `MIN_TIMESTAMP`
  (`Timestamp(-9223372036854.775000)`), which no `datetime` can represent.
- **Element type** is uniform within a PCollection, and Beam enforces it at graph
  construction time with a `TypeCheckError` — which is an `Exception`, not a
  `TypeError`.
- **No grained operations**: no indexing, no `len()`, no iteration. Order is not
  guaranteed, and Beam cannot sort a PCollection for you.
- Every element carries a **timestamp**; that is what windows are built from.
- A PCollection is **owned** by the Pipeline that made it.

---

## 📚 Practice Exercises

1. Write a pipeline that produces two PCollections from one source and show that
   neither affects the other. What would break if transforms mutated their input?
2. Use `beam.DoFn.TimestampParam` in a `ParDo` to print the timestamp of every
   element from a `Create` source. Then do the same for a `ReadFromText` source
   over a real file. Why is the second one still the epoch?
3. Write a pipeline whose output order would give different answers if the runner
   reordered it. What is the fix?

---

## 📖 Further Reading

- Beam's PCollection reference: <https://beam.apache.org/documentation/programming-model/model/#pcollections>
- The Beam SDK's type hints: <https://beam.apache.org/documentation/programming-model/#type-hints>

---

**Previous:** [00 — The Beam Workbench](00-workbench.md) ·
**Next:** [04 — PTransforms](04-ptransforms.md)
