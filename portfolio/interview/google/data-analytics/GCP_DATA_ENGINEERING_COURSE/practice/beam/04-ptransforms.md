# 04 — PTransforms

> **Practice Module 04 · Beam · 45 minutes**

## 🎯 What you will learn

- What a **PTransform** is: a parallel data-processing operation, and the pipeline
  step you write.
- The **six** transforms every Beam interview question comes back to, each one run
  for real.
- The `|` versus `>>` label syntax, and why `>` does not work.
- Why `Map` and `FlatMap` are different, and when each one is right.

---

## 🧠 Concept

A **PTransform** is a parallel data-processing operation. It takes one or more
PCollections as input, applies some processing, and produces one or more
PCollections as output. It is a *step in a pipeline*.

The name breaks down as **P**arallel **Transform**. The parallel is the point:
the same operation runs across every element, on many workers, at once.

### The six transforms

| # | Transform | Shape | What it does |
|---|---|---|---|
| 1 | **`Map`** | 1 → 1 | One input element becomes one output element. |
| 2 | **`FlatMap`** | 1 → N | One input element becomes zero or more output elements. |
| 3 | **`Filter`** | 1 → 0/1 | A predicate drops the elements that fail it. |
| 4 | **`ParDo`** | 1 → N | The general form; `Map` and `FlatMap` are special cases. |
| 5 | **`GroupByKey`** | K → V… | Groups values by key into an iterable. |
| 6 | **`CombinePerKey`** | K → V | Groups values by key and merges them into one value. |

`Map` and `FlatMap` are conveniences. `ParDo` is the primitive they are built
from, and it is the one you reach for when you need multiple outputs, side
outputs, state, or a timestamp.

### Label syntax

Every step in a pipeline should carry a label, so the graph is readable and
errors name the step that failed.

```python
result = source | "Parse" >> beam.Map(parse_fn)
```

- `|` passes the PCollection into the transform.
- `>>` applies the transform. It is required — `>` is not a valid operator on a
  PCollection and raises a `TypeError`.
- The string between them is the label.

You can also write the transform first and apply it with `>>`, but you lose the
label, so there is rarely a reason to:

```python
result = src >> beam.Map(parse_fn)   # no label
```

### `Map` versus `FlatMap`

`Map` is one-in-one-out. If your function returns a list, that list becomes a
*single element* — a list inside the PCollection. `FlatMap` unpacks it.

```python
beam.Map(lambda x: [x, x])     # one element, which is a two-item list
beam.FlatMap(lambda x: [x, x])  # two elements
```

This is the most common source of confusion in the first hour with Beam, and it
is worth being able to state the difference cold.

---

## 🛠️ Hands-On

Every block below writes its results to a temporary directory and prints them
back, because a Beam pipeline writes to its sinks — not to stdout. The helper
comes from `beam_lib`.

### 💻 Runs locally — Map, FlatMap and Filter

```python
import pathlib
import tempfile

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions([
    "--runner=DirectRunner",
    "--environment_type=LOOPBACK",
])

out = pathlib.Path(tempfile.mkdtemp())


def show(name, pc):
    """Write a PCollection to a temp file and read it back."""
    path = str(out / name)
    _ = pc | f"Write {name}" >> beam.io.WriteToText(
        path, shard_name_template="", append_trailing_newlines=False
    )
    return path


with beam.Pipeline(options=options) as p:
    src = p | "Create" >> beam.Create(["apple", "banana", "cherry", "date"])

    mapped = src | "Map" >> beam.Map(lambda w: (w, len(w)))
    flatmapped = src | "FlatMap" >> beam.FlatMap(lambda w: [(w, c) for c in w[:2]])
    filtered = src | "Filter" >> beam.Filter(lambda w: len(w) > 5)

    show("map", mapped)
    show("flatmap", flatmapped)
    show("filter", filtered)

for name in ("map", "flatmap", "filter"):
    print(f"== {name}")
    print((out / name).read_text())
```

Expected output:

```text
== map
('apple', 5)('banana', 6)('cherry', 6)('date', 4)
== flatmap
('apple', 'a')('apple', 'p')('banana', 'b')('banana', 'a')('cherry', 'c')('cherry', 'h')('date', 'd')('date', 'a')
== filter
bananacherry
```

Three shapes, one source.

- **Map** produced four elements from four. The tuple `('apple', 5)` is a single
  element, not two.
- **FlatMap** produced eight. Each word was expanded into two characters, and
  the tuple is still one element.
- **Filter** produced two. `apple` and `date` failed `len(w) > 5` and were
  dropped — a filter removes elements, it does not emit nulls.

### 💻 Runs locally — Map and FlatMap on the same function

The distinction above, isolated. One function, two transforms, different
element counts.

```python
import pathlib
import tempfile

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions([
    "--runner=DirectRunner",
    "--environment_type=LOOPBACK",
])

out = pathlib.Path(tempfile.mkdtemp())

with beam.Pipeline(options=options) as p:
    src = p | "Create" >> beam.Create([1, 2, 3])

    # Map: the returned list is ONE element.
    mapped = src | "Map" >> beam.Map(lambda x: [x, x * 10])

    # FlatMap: the returned list is UNPACKED into elements.
    flatmapped = src | "FlatMap" >> beam.FlatMap(lambda x: [x, x * 10])

    _ = mapped | "Write map" >> beam.io.WriteToText(
        str(out / "map"), shard_name_template="", append_trailing_newlines=False
    )
    _ = flatmapped | "Write flatmap" >> beam.io.WriteToText(
        str(out / "flatmap"), shard_name_template="", append_trailing_newlines=False
    )

print("map (3 elements, each a list):")
print((out / "map").read_text())
print("flatmap (6 elements, each a scalar):")
print((out / "flatmap").read_text())
```

Expected output:

```text
map (3 elements, each a list):
[1, 10][2, 20][3, 30]
flatmap (6 elements, each a scalar):
110220330
```

This is the single most useful thing to internalise about Beam's shape rules:
**`Map` never changes how many elements there are, and `FlatMap` does.**

### 💻 Runs locally — GroupByKey and CombinePerKey

Both operate on key-value pairs. `GroupByKey` gives you the whole group;
`CombinePerKey` gives you a merged value and throws the group away.

```python
import pathlib
import tempfile

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions([
    "--runner=DirectRunner",
    "--environment_type=LOOPBACK",
])

out = pathlib.Path(tempfile.mkdtemp())

pairs = [("a", 1), ("b", 2), ("a", 3), ("b", 4), ("a", 5)]

with beam.Pipeline(options=options) as p:
    src = p | "Create" >> beam.Create(pairs)

    grouped = src | "GroupByKey" >> beam.GroupByKey()
    combined = src | "CombinePerKey" >> beam.CombinePerKey(sum)

    _ = grouped | "Write grouped" >> beam.io.WriteToText(
        str(out / "grouped"), shard_name_template="", append_trailing_newlines=False
    )
    _ = combined | "Write combined" >> beam.io.WriteToText(
        str(out / "combined"), shard_name_template="", append_trailing_newlines=False
    )

print("grouped:")
print((out / "grouped").read_text())
print("combined:")
print((out / "combined").read_text())
```

Expected output (unordered):

```text
grouped:
('a', [1, 3, 5])('b', [2, 4])
combined:
('a', 9)('b', 6)
```

`GroupByKey` is the general one. `CombinePerKey(sum)` is `GroupByKey` plus a
merge function, and it is what you want when the group is too large to
materialise — or when you only need the total, not the parts.

Note that the *order of the keys* is not guaranteed — `a` might come before `b`
on one run and after it on the next. The order of the *values within* a group
is preserved, because that is the order they arrived in. If you need the keys
ordered, sort them explicitly.

Note the input: five `(key, value)` tuples. Feed either transform bare values
and Beam rejects the graph before any data moves:

```text
TypeCheckError: The transform 'Sum' requires PCollections of type
'Tuple[TypeVariable[K], Any]' but was applied to a PCollection of type
'<class 'int'>' (produced by the transform 'Create').
```

### 💻 Runs locally — ParDo, the general form

`ParDo` is what `Map` and `FlatMap` are built on. Use it when you need side
outputs, a timestamp, or state.

```python
import pathlib
import tempfile

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam import pvalue

options = PipelineOptions([
    "--runner=DirectRunner",
    "--environment_type=LOOPBACK",
])

out = pathlib.Path(tempfile.mkdtemp())


class SplitParDo(beam.DoFn):
    """Split each word into (word, length); odd lengths go to a side output."""

    def process(self, word):
        if len(word) % 2:
            yield pvalue.TaggedOutput("odd", word)
        else:
            yield word, len(word)


with beam.Pipeline(options=options) as p:
    src = p | "Create" >> beam.Create(["apple", "banana", "cherry", "date"])

    results = src | "Split" >> beam.ParDo(SplitParDo()).with_outputs("odd", main="main")

    _ = results["main"] | "Write main" >> beam.io.WriteToText(
        str(out / "main"), shard_name_template="", append_trailing_newlines=False
    )
    _ = results["odd"] | "Write odd" >> beam.io.WriteToText(
        str(out / "odd"), shard_name_template="", append_trailing_newlines=False
    )

print("main (even lengths):")
print((out / "main").read_text())
print("odd (side output):")
print((out / "odd").read_text())
```

Expected output:

```text
main (even lengths):
('banana', 6)('cherry', 6)('date', 4)
odd (side output):
apple
```

A side output is a second PCollection produced by the same `DoFn`. The main
output carries the even-length words; the side output carries the odd-length
ones. Without `with_outputs`, every element would have to take the same path.

Note the API: `pvalue.TaggedOutput("odd", word)` *wraps* the value with the tag
it belongs to. There is no `DoFn.SideOutputParam` in current Beam — the tag is
carried on the yielded value itself.

### 💻 Runs locally — the label syntax, and what `>` does

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions([
    "--runner=DirectRunner",
    "--environment_type=LOOPBACK",
])

with beam.Pipeline(options=options) as p:
    src = p | "Create" >> beam.Create([1, 2, 3])

    # The labelled form.
    labelled = src | "Times two" >> beam.Map(lambda x: x * 2)

    # The form that does not work.
    try:
        _ = src > "Times two" >> beam.Map(lambda x: x * 2)
    except TypeError as e:
        print(f"'>' is not a valid operator: {type(e).__name__}")

    print(f"labelled form built: {labelled is not None}")
```

Expected output:

```text
'>' is not a valid operator: TypeError
labelled form built: True
```

`>>` applies the transform. `>` is the *chained comparison* operator in Python,
and a PCollection does not support it — hence the `TypeError`.

### 💻 Runs locally — reading the transform graph

The pipeline is a graph. It is built before anything runs, and you can walk it
without running it.

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions([
    "--runner=DirectRunner",
    "--environment_type=LOOPBACK",
])

with beam.Pipeline(options=options) as p:
    src = p | "Create" >> beam.Create([1, 2, 3])
    _ = src | "Double" >> beam.Map(lambda x: x * 2)
    _ = src | "Label" >> beam.Map(lambda x: f"row {x}")

root = p.transforms_stack[0]
print("steps in the graph:")
for part in root.parts:
    print(f"  {part.full_label}  ->  {type(part.transform).__name__}")
```

Expected output:

```text
steps in the graph:
  Create  ->  Create
  Double  ->  ParDo
  Label  ->  ParDo
```

Two things to notice. `beam.Map` is a `ParDo` underneath — it *is* a `ParDo`
with a fixed 1→1 shape, which is why `ParDo` is the primitive. And the labels
you wrote are the labels in the graph; an unlabelled step gets an empty name.

---

## 🛠️ Common Errors and Fixes

### `TypeError: unsupported operand type(s) for |: 'PCollection' and 'str'`

You wrote `>` instead of `>>`, or you forgot the label entirely. The syntax is
`pcoll | "Label" >> transform`.

### `TypeCheckError: The transform 'Sum' requires PCollections of type 'Tuple[...]'`

`GroupByKey` and `CombinePerKey` need `(key, value)` pairs. Map to a tuple
first: `beam.Map(lambda x: ("key", x))`.

### `FlatMap` produced one element where I expected several

Your function returns a *nested* iterable. `FlatMap` flattens one level, so a
list of lists stays a list of lists. Flatten it yourself, or return tuples
rather than lists.

### `AttributeError: 'PCollection' object has no attribute 'append'`

You are treating a PCollection like a list. It is not one — use a transform.

### My side output is empty

You have to ask for it. `with_outputs("odd", main="main")` returns a dict-like
result; the side output is `results["odd"]` and the main output is
`results["main"]`. Without `with_outputs`, the tag on `TaggedOutput` has
nowhere to go.

### `AttributeError: type object 'DoFn' has no attribute 'SideOutputParam'`

There is no such parameter. In current Beam a side output is produced by
yielding `pvalue.TaggedOutput("tag", value)` and declaring the tag with
`with_outputs("tag")`.

### `TypeError: 'ParDo' object is not callable`

`beam.Map(fn)` returns a `ParDo`, and you cannot call it directly. Use the
pipe syntax: `src | "Label" >> beam.Map(fn)`.

---

## 💡 Production Notes

- **Label every step.** The label appears in the graph, in the error message, and
  in the Dataflow console. An unlabelled step is called `AnonymousTransform` and
  tells you nothing at 3am.
- **`GroupByKey` is a shuffle.** It moves data across workers. That is the most
  expensive thing a Beam pipeline does, and it is why `CombinePerKey` exists —
  it performs the same shuffle but ships less data home.
- **`CombinePerKey` before `GroupByKey` in spirit, even if you cannot reorder
  the graph.** If you only need the sum, do not materialise the group.
- **Side outputs are not free.** They are additional PCollections, and if the
  side output is not consumed it can be silently dropped — which is a bug you
  want to catch in review, not in production.
- **`ParDo` for anything non-trivial.** A `Map` with a five-line lambda is fine.
  The moment you need a timestamp, state, or a second output, it is a `DoFn`.

---

## 🔑 Key Takeaways

- A **PTransform** is a parallel data-processing operation: PCollections in,
  PCollections out.
- The six: **Map** (1→1), **FlatMap** (1→N), **Filter** (drops failures),
  **ParDo** (the general form), **GroupByKey** (groups), **CombinePerKey**
  (groups and merges).
- `Map` never changes the element count; `FlatMap` does.
- **Label every step**: `pcoll | "Label" >> transform`. `>` is not valid.
- `GroupByKey` and `CombinePerKey` both need `(key, value)` tuples, and both
  perform a shuffle.

---

## 📚 Practice Exercises

1. Write a pipeline with one source and three branches: a `Map`, a `FlatMap` and
   a `Filter`. Count the elements in each output. What would happen if you
   replaced the `FlatMap` with a `Map`?
2. Feed the same `(key, value)` PCollection to `GroupByKey` and to
   `CombinePerKey`. Which one would you use to find the *median*? Why is that
   harder than the mean?
3. Write a `DoFn` with a side output that routes records into "valid" and
   "invalid" PCollections. Which of the user's `Usecase1.ipynb` design does
   this match?

---

## 📖 Further Reading

- Beam's transform reference: <https://beam.apache.org/documentation/programming-model/model/#transforms>
- Beam's side inputs and outputs: <https://beam.apache.org/documentation/programming-model/model/#side-inputs-outputs>
- Apache Beam SDKs: <https://beam.apache.org/documentation/sdks/java/>

---

**Previous:** [03 — PCollections](03-pcollections.md) ·
**Next:** [05 — Dataflow vs Dataproc](05-dataflow-vs-dataproc.md)
