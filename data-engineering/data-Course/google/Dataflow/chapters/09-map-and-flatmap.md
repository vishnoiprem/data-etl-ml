# 2.4 — Map & FlatMap

> **Section 2 · SDK & Core Transforms · Lecture 2.4 · 6:30**

## 🎯 What you will learn

- The exact semantics of `Map` (1 → 0 or 1) and `FlatMap` (1 → N)
- `MapTuple` and `FlatMapTuple` — multi-input and multi-output transforms
- `Filter`, and what it is actually implemented as
- Side inputs: `AsDict`, `AsIter`, `AsList`, `AsSingleton`, and the failure
  modes of each
- `Reshuffle` — what it does, and the two situations where it is a no-op
- When a `Map` is not enough and a `DoFn` is the right tool
- The performance traps: I/O in a `Map`, generators in a `FlatMap`, and the `Map` that returns `None`

---

## 🧠 Concept

### `Map` — 1 → 0 or 1

`Map` applies a function to each element and emits **at most one** output
element per input element.

```text
input:  [ "a", "b", "c" ]
Map(f): [ f(a), f(b), f(c) ]        f returns non-None
        [ f(a), f(c) ]              f(b) returned None — b is dropped
```

The zero case is the one people trip over. If the function returns `None`,
**the element is silently dropped**. This is Beam's contract: `None` is
the sentinel for "do not emit". It is not an error, and it is not logged.

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create([1, 2, 3, 4])
        | "Map" >> beam.Map(lambda x: x * 2 if x % 2 == 0 else None)
        | "Print" >> beam.Map(print)
    )
```

Output: `2` and `8`. The odds are gone, with no warning.

This matters in two common situations:

1. **A validator that returns a bool.** People write
   `beam.Map(validate_order)` where `validate_order` returns `True`/`False`,
   expecting a filter. They get a PCollection of `True`/`False` instead.
   The transform you want is `beam.Filter`, and it is exactly as easy.

2. **A function with an early return.** A parser that returns `None` for
   a malformed row and a dict for a good one is a filter in disguise. It
   works, but it is a `Map` that drops data, and the drop is invisible in
   the job graph. The course's `ParseOrderFn` handles this case
   *explicitly* with an early `return` in a `DoFn` and a log line, which
   is the honest version of the same idea.

### `FlatMap` — 1 → N

`FlatMap` applies a function to each element and emits **zero or more**
outputs per input.

```text
input:  [ "a,b", "c" ]
FlatMap(split): [ "a", "b", "c" ]
```

The function may return a list, a tuple, a generator, or any iterable.
Beam flattens it.

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create(["a,b", "c"])
        | "Split" >> beam.FlatMap(lambda s: s.split(","))
        | "Print" >> beam.Map(print)
    )
```

Note the asymmetry with `Map`: `Map` returning a list does **not** flatten
it. `beam.Map(lambda s: s.split(","))` gives you two elements, each a
list. `FlatMap` gives you the individual strings. If you want the
elements flattened, you want `FlatMap`.

The `Filter` transform is exactly `FlatMap` with a filter:

```python
import apache_beam as beam
import inspect

print(inspect.getsource(beam.Filter))
```

```text
wrapper = lambda x, *args, **kwargs: [x] if fn(x, *args, **kwargs) else []
```

That is the whole implementation. `Filter` is `FlatMap` that emits the
element or emits nothing. This is worth knowing because it explains
`Filter`'s behaviour precisely: **a filter that raises an exception does
not drop the element — it fails the bundle.** The exception propagates
before the `[x] if ... else []` is evaluated.

### The arity table

| Transform | Input | Output | Notes |
|---|---|---|---|
| `Map` | 1 element | 0 or 1 element | `None` drops the element |
| `FlatMap` | 1 element | 0..N elements | Returns any iterable |
| `MapTuple` | 1 **tuple** | 0 or 1 element | The tuple is unpacked into arguments |
| `FlatMapTuple` | 1 **tuple** | 0..N elements | The tuple is unpacked into arguments |
| `Filter` | 1 element | 0 or 1 element | Keeps the element unchanged |

### `MapTuple` — unpacking a tuple

`MapTuple` takes a function whose *first argument is a tuple* and unpacks
it into multiple arguments:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create([(1, "a"), (2, "b")])
        | "MapTuple" >> beam.MapTuple(lambda k, v: f"{k}:{v}")
        | "Print" >> beam.Map(print)
    )
```

`MapTuple(lambda k, v: ...)` is exactly equivalent to
`Map(lambda kv: ...(kv[0], kv[1]))`. Beam implements it as a `ParDo` with
a `CallableWrapperDoFn` that does the unpacking, so it is not a
separate execution path — just a different calling convention.

The same form works for `FlatMapTuple`:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create([(1, "a"), (2, "b")])
        | "FlatMapTuple" >> beam.FlatMapTuple(lambda k, v: [f"{k}{v}", f"{v}{k}"])
        | "Print" >> beam.Map(print)
    )
```

### Multi-input and multi-output — the two cases people get wrong

There are two different meanings of "multi-output" in Beam, and they need
different transforms.

**Case 1: one input, several outputs.** Use `FlatMap`, not `Map` with a
tuple return:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create(["a,b"])
        # WRONG for what we want: emits ONE element, a tuple
        | "Map" >> beam.Map(lambda s: tuple(s.split(",")))
        | "Print" >> beam.Map(print)
    )
```

That prints `('a', 'b')` — one element. The correct version:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create(["a,b"])
        # RIGHT: emits TWO elements
        | "FlatMap" >> beam.FlatMap(lambda s: s.split(","))
        | "Print" >> beam.Map(print)
    )
```

**Case 2: several inputs.** A `Map` takes exactly one PCollection. To
combine two, you have three options, in increasing order of power:

**Option A — `Flatten` the two PCollections** (if they have the same
schema):

```python
import apache_beam as beam

with beam.Pipeline() as p:
    left = p | "Left" >> beam.Create([1, 2])
    right = p | "Right" >> beam.Create([3, 4])
    merged = (left, right) | "Merge" >> beam.Flatten()
```

**Option B — zip them with `beam.zip`**, which is a different module and
is not part of the core SDK. If you find yourself needing a zip, you
usually want a keyed join instead.

**Option C — `CoGroupByKey`**, which is the right answer for joining two
keyed streams:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    orders = p | "Orders" >> beam.Create([("o1", 100)])
    refunds = p | "Refunds" >> beam.Create([("o1", -20)])

    joined = (
        (orders, refunds)
        | "CoGroup" >> beam.CoGroupByKey()
    )
```

Each output element is `((key, orders_group), (key, refunds_group))`.

**Multi-output with `DoFn` and tagged outputs** — when one input must
produce elements in *different* output PCollections, `Map` and `FlatMap`
cannot express it. You need a `DoFn` with `TaggedOutput`:

```python
import apache_beam as beam
from apache_beam.pvalue import TaggedOutput


class SplitByStatus(beam.DoFn):
    """Route each order into one of two output PCollections."""

    def process(self, order):
        if order["status"] == "complete":
            yield TaggedOutput("completed", order)
        else:
            yield TaggedOutput("other", order)


with beam.Pipeline() as p:
    orders = (
        p
        | "Read" >> beam.io.ReadFromText("./sample_data/orders.csv", skip_header_lines=1)
        | "Parse" >> beam.Map(lambda line: line.split(","))
    )

    outputs = orders | "Split" >> beam.ParDo(SplitByStatus()).with_outputs(
        "completed",
        "other",
        main="main",
    )
    completed = outputs["completed"]
    other = outputs["other"]
```

`DoFn.process` returning a `TaggedOutput` routes the element to a named
output. **The tags must be declared**, and in Beam 2.77 the way to
declare them is `.with_outputs(...)` on the `ParDo`.

```text
TypeError: 'PCollection' object is not subscriptable
```

That is the error you get if you forget it: without `.with_outputs`, the
result of `| beam.ParDo(...)` is an ordinary PCollection, and
`outputs["completed"]` fails.

The `main="main"` argument names the *main* output — the one the `DoFn`
yields to without a tag. A `DoFn` that only ever yields `TaggedOutput`s
has nothing on its main output, so naming it is harmless and keeps the
signature uniform. You can also reach the tagged outputs by attribute:

```python
completed = outputs.completed
```

This is the one place where a `DoFn` genuinely beats `Map`, and it is
worth knowing because "route rows to different tables based on a column"
is an extremely common requirement.

### `Filter` — the details

`Filter` keeps elements for which the predicate returns truthy. Two things
worth being explicit about:

**A filter that raises fails the bundle.** It does not drop the element.
If your predicate can raise on bad data — `float(row[7])` on a
non-numeric amount — the exception propagates and the bundle is retried.
If you want to *drop* bad data, catch the exception in the filter itself
or do the parsing first and filter on a validity flag.

**Filtering on a key is different from filtering on a value.** After a
`CombinePerKey`, your elements are `(key, value)` tuples. A filter on
them sees the tuple, not the value:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create([("a", 1), ("b", 2)])
        | "FilterKey" >> beam.Filter(lambda kv: kv[0] == "a")
        | "Print" >> beam.Map(print)
    )
```

Or unpack the tuple inside the filter, which is the readable form:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create([("a", 1), ("b", 2)])
        | "FilterKey" >> beam.Filter(lambda kv: kv[0] == "a")
        | "Print" >> beam.Map(print)
    )
```

> **There is no `beam.FilterTuple`.** The SDK ships `MapTuple` and
> `FlatMapTuple`, but not a tuple-aware `Filter`. If you want a
> two-argument predicate on a keyed PCollection, unpack inside a
> `Filter` (`lambda kv: kv[0] == "a"`), or — if you need a genuinely
> readable two-argument signature — build a `MapTuple` that maps the
> tuple to a boolean and then `Filter` on that, at the cost of an extra
> transform. The `Filter` form is the one to write.

### Side inputs — the four views

A side input is a PCollection that is materialised and broadcast to every
worker, so that a transform can consult it while processing the main
stream. The side PCollection is read **once per bundle**, not once per
element.

The four views, from `apache_beam.pvalue`:

| View | The side PCollection becomes | Lookup | Use when |
|---|---|---|---|
| `AsDict` | `dict` | O(1) by key | You have `(key, value)` pairs and need random access |
| `AsIter` | a lazy iterator | O(n) per element | The side is large-ish and you scan it, or you only need a subset |
| `AsList` | `list` | O(n) per element, indexable | You need to index it, or it is small |
| `AsSingleton` | the single element | — | The side has exactly one element |

```python
import apache_beam as beam
from apache_beam.pvalue import AsDict, AsIter, AsList, AsSingleton
```

#### `AsDict`

The best choice for a lookup table. The side PCollection must contain
`(key, value)` pairs with unique keys.

```python
import apache_beam as beam

with beam.Pipeline() as p:
    reference = (
        p
        | "ReadReference" >> beam.io.ReadFromText(
            "./sample_data/product_reference.ndjson"
        )
        | "ParseReference" >> beam.Map(json.loads)
        | "KeyById" >> beam.Map(lambda r: (r["product_id"], r))
    )

    (
        p
        | "ReadOrders" >> beam.io.ReadFromText(
            "./sample_data/orders.csv",
            skip_header_lines=1,
        )
        | "ParseOrders" >> beam.Map(lambda line: line.split(","))
        | "Enrich" >> beam.Map(
            lambda row: {**row, "category": reference_lookup.get(row[8], {}).get("category", "unknown")},
            reference_lookup=beam.pvalue.AsDict(reference),
        )
    )
```

The `AsDict` side is converted to a dict **once per bundle**, and then
every element in that bundle does an O(1) lookup. That is the crucial
property: the conversion cost is per-bundle, not per-element.

#### `AsIter` and `AsList`

Both give you the whole side collection. `AsIter` is lazy (an iterator
that is re-created per bundle), `AsList` materialises a list.

```python
import apache_beam as beam

with beam.Pipeline() as p:
    reference = (
        p
        | "ReadReference" >> beam.io.ReadFromText(
            "./sample_data/product_reference.ndjson"
        )
        | "ParseReference" >> beam.Map(json.loads)
    )

    (
        p
        | "ReadOrders" >> beam.io.ReadFromText(
            "./sample_data/orders.csv",
            skip_header_lines=1,
        )
        | "ParseOrders" >> beam.Map(lambda line: line.split(","))
        | "Enrich" >> beam.Map(
            _enrich_with_category,
            reference=beam.pvalue.AsIter(reference),
        )
    )
```

This is the exact form the course's `batch_pipeline.py` uses, with
`_enrich_with_category` doing a linear scan:

```python
def _enrich_with_category(order: dict, reference: list[dict]) -> dict:
    """Attach a product category to an order using a side input."""
    product_id = order.get("product_id")
    for row in reference:
        if row.get("product_id") == product_id:
            order["category"] = row.get("category", "unknown")
            return order
    order["category"] = "unknown"
    return order
```

That is O(reference_size) per order. With 50 reference rows and 5,000
orders, it is 250,000 comparisons — fine. With 50,000 reference rows and
5,000,000 orders, it is 250 billion comparisons, and the job never
finishes. **The fix is `AsDict`**, which turns the scan into a lookup.

The rule: **if you look up by a key, use `AsDict`.** If you scan the
whole side for every element, you have an O(n·m) algorithm and a
guaranteed slow job.

#### `AsSingleton` and the singleton case

`AsSingleton` selects *one* value from the side PCollection. The side
must contain **exactly one element per window**:

```python
import json

import apache_beam as beam

with beam.Pipeline() as p:
    # A one-line config file. `ReadFromText` is a *line* reader, so the
    # file must hold exactly one JSON document on one line.
    config = (
        p
        | "ReadConfig" >> beam.io.ReadFromText("./config/run_config.json")
        | "ParseConfig" >> beam.Map(json.loads)
    )

    (
        p
        | "ReadOrders" >> beam.io.ReadFromText(
            "./sample_data/orders.csv",
            skip_header_lines=1,
        )
        | "Enrich" >> beam.Map(
            lambda row, cfg: {**row, "target_date": cfg["target_date"]},
            cfg=beam.pvalue.AsSingleton(config),
        )
    )
```

> **`ReadFromText` reads lines, not documents.** Pointing it at a
> pretty-printed JSON file such as `sample_data/summary.json` and then
> calling `json.loads` on each line fails, because the file is one JSON
> document spread over seven lines:
>
> ```text
> RuntimeError: json.decoder.JSONDecodeError: Expecting property name
> enclosed in double quotes: line 1 column 2 (char 1)
> ```
>
> The fix is a config file that is genuinely one line, or reading the
> file as a whole document with `beam.io.ReadFromText` and a
> `GroupIntoBatches` that joins the lines before parsing. For a
> single-value config, the one-line file is simpler and it is the shape
> you want in production anyway.

If the side has more than one element, the runtime raises:

```text
ValueError: PCollection of size 2 with more than one element accessed as
a singleton view. First two elements encountered are "..." and "...".
```

If it has none, the side is `EmptySideInput()` — which means the
attribute access on it raises an `AttributeError`, not a clean error. If
you need a default, `AsSingleton` accepts one:

```python
beam.pvalue.AsSingleton(config, default_value={})
```

> **`AsSingleton` is not deprecated in Beam 2.77, but it is the view
> to avoid in new code.** It works, and it is not marked for removal in
> the installed SDK. The reason to avoid it is behavioural, not
> administrative: the singleton case is ambiguous in a streaming
> pipeline, because a side PCollection in the global window has no
> single value until the pipeline ends, and a `ValueError` at runtime is
> a poor way to discover that. The failure modes are also unhelpful —
> more than one element gives a `ValueError` with the first two values
> interpolated into the message, and zero elements gives you an
> `EmptySideInput` that raises `AttributeError` on the first attribute
> access rather than a clean "no value" error.
>
> For a *batch* pipeline with a one-row configuration file, `AsSingleton`
> is perfectly reasonable and it is what you want. For new code, prefer
> `AsList(config)[0]`, which fails loudly and obviously. If you are
> maintaining code that uses `AsSingleton`, it still works in Beam
> 2.77 — leave it alone unless it is causing you trouble.

> **Side inputs are not free.** The side PCollection is materialised and
> held in memory on every worker. A 10 GB side input means 10 GB of RAM
> per worker (or a crash). The rule of thumb: **a side input must fit in
> the memory of a single worker**, comfortably. If it does not, you want a
> join (`CoGroupByKey` or a `GroupByKey`), not a side input.

### `Reshuffle` — the anti-fusion barrier

`Reshuffle` is a `PTransform` that returns a PCollection equivalent to
its input, but that has two operational effects:

1. **It prevents fusion** of the transforms around it.
2. **It provides checkpointing**, so the pipeline can recover from a
   failure without reprocessing everything.

Internally it adds a random key to each element, does a
`ReshufflePerKey` (a shuffle, effectively a `GroupByKey` with a random
key), and then removes the key:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    (
        p
        | "Read" >> beam.io.ReadFromText("./sample_data/orders.csv", skip_header_lines=1)
        | "Parse" >> beam.Map(lambda line: line.split(","))
        | "Reshuffle" >> beam.Reshuffle()
        | "Map" >> beam.Map(lambda row: row[3])
        | "Print" >> beam.Map(print)
    )
```

#### When `Reshuffle` is a no-op

Two cases, and both are common:

**Case 1: there is no expensive work to separate.** `Reshuffle` only
earns its keep when it separates two pieces of work that the runner
would otherwise fuse. If the `Map` before it is trivial, the shuffle is
pure overhead — you have paid for a full data shuffle to break a fusion
that would have cost nothing.

**Case 2: the input is already being shuffled.** If a
`GroupByKey` or `CombinePerKey` immediately precedes the `Reshuffle`,
there is nothing to gain — the data is already distributed and
checkpointed. Reshuffling again is a second shuffle of the same data.

The pattern where `Reshuffle` earns its keep:

```text
Read → [expensive per-record work] → Reshuffle → [GroupByKey]
```

Here, the expensive work happens per-bundle, and the reshuffle splits
the data so that the `GroupByKey` does not become a hot spot. This is the
classic Beam skew fix.

> **The `Reshuffle` in `batch_pipeline.py`.** The course's pipeline reads
> the file, parses it, and combines by region. There is no `Reshuffle`,
> and that is correct — the sample data is 5,000 rows with four keys.
> `Reshuffle` becomes worth its cost at a scale where the per-key
> distribution is skewed, which is what the `--hot-key-rate` flag on the
> sample data generator is there to demonstrate.

### When a `Map` is not enough

`Map` is the right tool most of the time. Reach for a `DoFn` when you
need one of these:

| Need | Why `Map` cannot do it | Use |
|---|---|---|
| Multiple output PCollections | `Map` produces one output | `DoFn` + `TaggedOutput` |
| Access to the element's timestamp | `Map` functions get only the element | `DoFn` with `TimestampParam` |
| Access to the window | same | `DoFn` with `WindowParam` |
| Access to the key (after a `GroupByKey`) | `Map` gets the whole tuple | `DoFn` with `KeyParam` |
| Stateful processing across elements | no state in a `Map` | `DoFn` with `StateParam` |
| Emitting zero elements conditionally | `Map` returning `None` drops one, but is implicit | `DoFn` with an explicit `return` |
| Batch processing | `Map` is per-element | `DoFn` with `yields_batches()` |
| A reusable, testable unit | a lambda is not a unit | a `DoFn` class |

The `DoFn` parameter annotations are the mechanism:

```python
import apache_beam as beam


class ParseOrderFn(beam.DoFn):
    """Parse CSV lines into order dicts, skipping malformed rows."""

    def process(self, line: str, timestamp=beam.DoFn.TimestampParam):
        """Parse one line and emit the resulting order dict."""
        # timestamp is the element's event timestamp
        ...
```

The available parameters are `ElementParam`, `TimestampParam`,
`WindowParam`, `KeyParam`, `PaneInfoParam`, `StateParam`, `TimerParam`,
`RestrictionParam`, `BundleContextParam`, `SideInputParam`,
`WatermarkEstimatorParam`, `SetupContextParam`, and
`DynamicTimerTagParam`.

The course's `project/transforms.py` has two of them, and they are the
right models to copy:

```python
class ParseOrderFn(beam.DoFn):
    """Parse CSV lines into order dicts, skipping malformed rows.

    The malformed rows are logged rather than raised, because one bad
    line in a 10-million-line file should not fail the entire bundle.
    """

    def process(self, line: str, timestamp=beam.DoFn.TimestampParam) -> Iterable[Any]:
        """Parse one line and emit the resulting order dict."""
        row = try_parse_order_line(line)
        if row is None:
            log.warning("skipping malformed order line: %.120s", line)
            return
        if not is_valid_order(row):
            log.warning("skipping invalid order: %s", row.get("order_id"))
            return
        yield row
```

Two things to note in that `DoFn`:

1. **`return` with no value drops the element**, explicitly. The reader
   can see that the malformed row is being discarded on purpose, and
   there is a log line. A `Map` that returns `None` achieves the same
   thing invisibly.
2. **`log.warning` rather than `raise`.** One bad line in a ten-million
   line file should not fail the whole bundle. This is a policy decision
   that is *visible in the code* — which is the point.

### Performance traps

#### Trap 1: a `Map` that does I/O

```text
# BAD: a network call per element
| "Fetch" >> beam.Map(lambda order: requests.get(f"http://api/{order['product_id']}").json())
```

This looks like a `Map` and behaves like a synchronous HTTP client. With
one element per row and 5,000 rows, that is 5,000 sequential HTTP calls
per worker. The pipeline does not parallelise the calls *within* a
bundle — Beam's parallelism is across bundles.

The fix depends on what you actually want:

- **Batch the calls.** One `Map` per bundle, not per element, using
  `yields_batches()`.
- **Use a transform that already does it.** Beam has
  `beam.io.ReadFromBigQuery`, `ReadFromPubSub`, and many more, which are
  built to do the I/O efficiently.
- **Move the I/O out of Beam entirely.** If the enrichment is a lookup
  against a table that changes slowly, that is a *side input*, not a
  per-element call. Load it once per bundle with `AsDict`.

The diagnostic: if a `Map` is slow, look at its body. If the body talks
to the network, that is the problem.

#### Trap 2: a `FlatMap` that returns a generator

```text
# Looks lazy. Is not.
| "Expand" >> beam.FlatMap(lambda row: (f for f in explode(row)))
```

Beam **materialises** the iterable that a `FlatMap` returns. It is not
streamed element by element; Beam collects it and then emits each item.
For a generator that produces ten million items, that is ten million items
in memory on one worker.

The rule: a `FlatMap`'s return value must be **bounded and modest**. If
the expansion size is not known in advance, you want a different design —
usually `GroupByKey` (which streams) rather than `FlatMap` (which
materialises).

The distinction that matters:

| | Materialises? | Use for |
|---|---|---|
| `FlatMap` returning a list | yes | Bounded, modest expansions |
| `FlatMap` returning a generator | yes | Same — the generator is collected |
| `GroupByKey` | no, it streams | Unbounded groups |

#### Trap 3: the `Map` that returns `None`

Covered above, but it belongs in the traps list because it is the
easiest to ship accidentally:

```text
# Silently drops every element for which the function returns None.
| "Validate" >> beam.Map(validate_order)
```

If you meant to filter, use `beam.Filter`. If you meant to transform, do
not return `None`.

#### Trap 4: a `Map` that captures unpicklable state

`Map` functions are serialised and shipped to workers. A lambda that
closes over a database connection, an open file, or a `requests.Session`
will fail to pickle, usually with an error that mentions `Can't pickle
<...>` rather than anything about your transform.

```python
# BAD: closes over a socket
session = requests.Session()
with beam.Pipeline() as p:
    (p | "Fetch" >> beam.Map(lambda x: session.get(x).json()))
```

The fix is a `DoFn` with a `setup` method that opens the connection on the
worker:

```python
import apache_beam as beam


class FetchFn(beam.DoFn):
    """Fetch one record per element, with a per-worker session."""

    def setup(self):
        self.session = requests.Session()

    def process(self, url):
        yield self.session.get(url).json()
```

`setup` runs once per bundle (or per worker, depending on the runner),
on the worker, where the connection is legal.

#### Trap 5: a `Map` that is really a `FlatMap` in disguise

```text
# Emits ONE element that happens to be a list.
| "Split" >> beam.Map(lambda s: s.split(","))
```

If the intent was to explode the record, use `FlatMap`. The difference
shows up immediately downstream: `beam.Map(len)` on the `Map` version
returns the length of the list, and on the `FlatMap` version it returns
the length of each piece.

---

## 🛠️ Hands-On: Parsing, Enriching, and Exploding

### Step 1 — `Map` semantics: the `None` drop

```bash
cd data-engineering/data-Course/google/Dataflow
.venv/bin/python - <<'PY'
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])

with beam.Pipeline(options=options) as p:
    (
        p
        | "Create" >> beam.Create([1, 2, 3, 4, 5, 6])
        | "DoubleOdds" >> beam.Map(lambda x: x * 2 if x % 2 == 0 else None)
        | "Print" >> beam.Map(print)
    )
PY
```

Output: `2 4 6 8 12` — wait, carefully: the *odds* are dropped, so you
see `4 8 12` and the three odd numbers are gone. Compare with the same
pipeline using `Filter`:

```bash
.venv/bin/python - <<'PY'
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])

with beam.Pipeline(options=options) as p:
    (
        p
        | "Create" >> beam.Create([1, 2, 3, 4, 5, 6])
        | "KeepEven" >> beam.Filter(lambda x: x % 2 == 0)
        | "Double" >> beam.Map(lambda x: x * 2)
        | "Print" >> beam.Map(print)
    )
PY
```

Now the odds are filtered out *before* the doubling, and the result is
`4 8 12`. The two pipelines produce the same numbers here, but the
`Filter` version is honest: the dropped elements were never supposed to
be there.

### Step 2 — a parsing `Map` over the real data

```bash
.venv/bin/python - <<'PY'
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])

FIELDS = [
    "order_id",
    "customer_id",
    "order_ts",
    "region",
    "channel",
    "currency",
    "status",
    "amount",
    "product_id",
]


def parse_order_line(line):
    """Parse one CSV line into a dict."""
    values = line.split(",")
    if len(values) != len(FIELDS):
        return None
    return dict(zip(FIELDS, values))


with beam.Pipeline(options=options) as p:
    (
        p
        | "ReadOrders" >> beam.io.ReadFromText(
            "./sample_data/orders.csv",
            skip_header_lines=1,
        )
        | "Parse" >> beam.Map(parse_order_line)
        | "KeepValid" >> beam.Filter(lambda row: row is not None)
        | "ToSummary" >> beam.Map(
            lambda row: f"{row['region']},{float(row['amount']):.2f},{row['status']}"
        )
        | "Print" >> beam.Map(print)
    )
PY
```

Two stages, and both matter:

- `Parse` returns `None` for a malformed line (wrong field count).
- `KeepValid` filters those out — as a **separate, visible** step,
  rather than hiding the drop inside the parse.

The alternative — one `Map` that does both — produces the same output and
loses the information about *why* rows were dropped.

### Step 3 — use the course's own parser instead

The course project already has a tested parser. Use it:

```bash
.venv/bin/python - <<'PY'
import sys

sys.path.insert(0, "project")

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from transforms import is_valid_order, try_parse_order_line

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])


def parse_and_validate(line):
    """Parse one line, keeping only rows that pass every business rule."""
    row = try_parse_order_line(line)
    if row is None:
        return None
    if not is_valid_order(row):
        return None
    return row


with beam.Pipeline(options=options) as p:
    (
        p
        | "ReadOrders" >> beam.io.ReadFromText(
            "./sample_data/orders.csv",
            skip_header_lines=1,
        )
        | "Parse" >> beam.Map(parse_and_validate)
        | "KeepValid" >> beam.Filter(lambda row: row is not None)
        | "Count" >> beam.combiners.Count.Globally()
        | "Print" >> beam.Map(print)
    )
PY
```

`try_parse_order_line` returns `None` for a malformed row, and
`is_valid_order` applies the business rules (known region, known status,
known currency, parseable timestamp, non-negative amount). On the clean
sample data every row passes, so the count is exactly **5000** — the
same as the line count minus the header.

To see the validation actually bite, point the same pipeline at the
deliberately broken file:

```bash
.venv/bin/python - <<'PY'
import sys

sys.path.insert(0, "project")

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from transforms import is_valid_order, try_parse_order_line

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])


def parse_and_validate(line):
    row = try_parse_order_line(line)
    if row is None:
        return None
    if not is_valid_order(row):
        return None
    return row


with beam.Pipeline(options=options) as p:
    (
        p
        | "ReadBroken" >> beam.io.ReadFromText(
            "./sample_data/malformed_orders.csv",
        )
        | "Parse" >> beam.Map(parse_and_validate)
        | "KeepValid" >> beam.Filter(lambda row: row is not None)
        | "Count" >> beam.combiners.Count.Globally()
        | "Print" >> beam.Map(print)
    )
PY
```

All five rows of `malformed_orders.csv` are rejected — a wrong field
count, an unparseable timestamp, an unknown region, an unknown currency,
and an empty row. The count is **0**.

### Step 4 — `FlatMap` that explodes a product reference

The exercise's second deliverable: a `FlatMap` that turns one order
record into several rows — one per product in the order's reference
entry.

First, look at the reference data:

```bash
head -3 sample_data/product_reference.ndjson
```

```text
{"product_id": "p0000", "category": "cat-00", "unit_cost": 3.0, "active": true}
{"product_id": "p0001", "category": "cat-01", "unit_cost": 4.0, "active": true}
{"product_id": "p0002", "category": "cat-02", "unit_cost": 5.0, "active": true}
```

Now explode each order into one row per dimension it belongs to. An
order has a region, a channel, a currency, a status, and a product — so
one order becomes five "fact" rows, each tagged with the dimension it
came from:

```bash
.venv/bin/python - <<'PY'
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])


def explode_order(row):
    """Explode one order into one row per dimension."""
    return [
        ("region", row["region"]),
        ("channel", row["channel"]),
        ("currency", row["currency"]),
        ("status", row["status"]),
        ("product_id", row["product_id"]),
    ]


with beam.Pipeline(options=options) as p:
    (
        p
        | "ReadOrders" >> beam.io.ReadFromText(
            "./sample_data/orders.csv",
            skip_header_lines=1,
        )
        | "Parse" >> beam.Map(lambda line: dict(zip(
            [
                "order_id",
                "customer_id",
                "order_ts",
                "region",
                "channel",
                "currency",
                "status",
                "amount",
                "product_id",
            ],
            line.split(","),
        )))
        | "Explode" >> beam.FlatMap(explode_order)
        | "PrintSample" >> beam.Map(print)
    )
PY
```

Each order produces five elements. The count goes up 5×:

```bash
.venv/bin/python - <<'PY'
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])

with beam.Pipeline(options=options) as p:
    (
        p
        | "ReadOrders" >> beam.io.ReadFromText(
            "./sample_data/orders.csv",
            skip_header_lines=1,
        )
        | "Explode" >> beam.FlatMap(
            lambda line: [
                ("region", line.split(",")[3]),
                ("channel", line.split(",")[4]),
                ("currency", line.split(",")[5]),
                ("status", line.split(",")[6]),
                ("product_id", line.split(",")[8]),
            ]
        )
        | "Count" >> beam.combiners.Count.Globally()
        | "Print" >> beam.Map(print)
    )
PY
```

Expected: **25000** (5,000 orders × 5 dimensions). If you get 5,000, you
used `Map` instead of `FlatMap` and each element is a list.

### Step 5 — a `FlatMap` that explodes a *variable* number of rows

A flatmap that produces a variable number of rows per input — the shape
you get when splitting a comma-separated field list:

```bash
.venv/bin/python - <<'PY'
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])

# A tiny synthetic dataset: each "cart" holds a variable number of items.
CARTS = [
    "cart-1|sku-a,sku-b,sku-c",
    "cart-2|sku-d",
    "cart-3|sku-e,sku-f",
    "cart-4|",
]


def explode_cart(row):
    """Split one cart line into one row per item."""
    cart_id, _, items = row.partition("|")
    for item in items.split(","):
        item = item.strip()
        if not item:
            continue
        yield (cart_id, item)


with beam.Pipeline(options=options) as p:
    (
        p
        | "Create" >> beam.Create(CARTS)
        | "Explode" >> beam.FlatMap(explode_cart)
        | "Print" >> beam.Map(print)
    )
PY
```

Output:

```text
('cart-1', 'sku-a')
('cart-1', 'sku-b')
('cart-1', 'sku-c')
('cart-2', 'sku-d')
('cart-3', 'sku-e')
('cart-3', 'sku-f')
```

Note `cart-4` produces nothing — it had no items. That is `FlatMap`'s
zero case, and it is why `FlatMap` and `Filter` are the same shape.

### Step 6 — `MapTuple` and tuple-aware filtering

```bash
.venv/bin/python - <<'PY'
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])

with beam.Pipeline(options=options) as p:
    (
        p
        | "Create" >> beam.Create([("EMEA", 100.0), ("AMER", 200.0), ("APAC", 50.0)])
        | "FilterBig" >> beam.Filter(lambda kv: kv[1] >= 100.0)
        | "Format" >> beam.MapTuple(lambda region, amount: f"{region}={amount:.2f}")
        | "Print" >> beam.Map(print)
    )
PY
```

Output:

```text
EMEA=100.00
AMER=200.00
```

### Step 7 — side inputs: `AsIter` versus `AsDict`

Build both and compare the code, then compare the output:

```bash
.venv/bin/python - <<'PY'
import json
import sys

sys.path.insert(0, "project")

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])

ORDER_FIELDS = [
    "order_id",
    "customer_id",
    "order_ts",
    "region",
    "channel",
    "currency",
    "status",
    "amount",
    "product_id",
]


def enrich_with_iter(order, reference):
    """Enrich by scanning the side input linearly."""
    for row in reference:
        if row.get("product_id") == order["product_id"]:
            return f"{order['order_id']},{row['category']}"
    return f"{order['order_id']},unknown"


with beam.Pipeline(options=options) as p:
    reference = (
        p
        | "ReadReference" >> beam.io.ReadFromText(
            "./sample_data/product_reference.ndjson"
        )
        | "ParseReference" >> beam.Map(json.loads)
    )

    (
        p
        | "ReadOrders" >> beam.io.ReadFromText(
            "./sample_data/orders.csv",
            skip_header_lines=1,
        )
        | "ParseOrders" >> beam.Map(lambda line: dict(zip(ORDER_FIELDS, line.split(","))))
        | "Enrich" >> beam.Map(
            enrich_with_iter,
            reference=beam.pvalue.AsIter(reference),
        )
        | "PrintSample" >> beam.Map(print)
    )
PY
```

Now the `AsDict` version — same output, different code shape:

```bash
.venv/bin/python - <<'PY'
import json
import sys

sys.path.insert(0, "project")

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])

ORDER_FIELDS = [
    "order_id",
    "customer_id",
    "order_ts",
    "region",
    "channel",
    "currency",
    "status",
    "amount",
    "product_id",
]


def enrich_with_dict(order, reference):
    """Enrich by looking the product up in a dict."""
    row = reference.get(order["product_id"], {})
    return f"{order['order_id']},{row.get('category', 'unknown')}"


with beam.Pipeline(options=options) as p:
    reference = (
        p
        | "ReadReference" >> beam.io.ReadFromText(
            "./sample_data/product_reference.ndjson"
        )
        | "ParseReference" >> beam.Map(json.loads)
        | "KeyById" >> beam.Map(lambda r: (r["product_id"], r))
    )

    (
        p
        | "ReadOrders" >> beam.io.ReadFromText(
            "./sample_data/orders.csv",
            skip_header_lines=1,
        )
        | "ParseOrders" >> beam.Map(lambda line: dict(zip(ORDER_FIELDS, line.split(","))))
        | "Enrich" >> beam.Map(
            enrich_with_dict,
            reference=beam.pvalue.AsDict(reference),
        )
        | "PrintSample" >> beam.Map(print)
    )
PY
```

The `AsDict` version is the one you want. The `AsIter` version is O(n·m)
and the `AsDict` version is O(m).

### Step 8 — a `DoFn` with tagged outputs

Route orders into two output PCollections by status:

```bash
.venv/bin/python - <<'PY'
import sys

sys.path.insert(0, "project")

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.pvalue import TaggedOutput
from transforms import try_parse_order_line

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])


class SplitByStatus(beam.DoFn):
    """Route each order into the completed or the other output."""

    def process(self, line):
        row = try_parse_order_line(line)
        if row is None:
            return
        if row["status"] == "complete":
            yield TaggedOutput("completed", row["order_id"])
        else:
            yield TaggedOutput("other", row["order_id"])


with beam.Pipeline(options=options) as p:
    orders = (
        p
        | "ReadOrders" >> beam.io.ReadFromText(
            "./sample_data/orders.csv",
            skip_header_lines=1,
        )
    )

    outputs = orders | "Split" >> beam.ParDo(SplitByStatus()).with_outputs(
        "completed",
        "other",
        main="main",
    )

    (
        outputs["completed"]
        | "CountCompleted" >> beam.combiners.Count.Globally()
        | "PrintCompleted" >> beam.Map(lambda n: f"completed: {n}")
    )

    (
        outputs["other"]
        | "CountOther" >> beam.combiners.Count.Globally()
        | "PrintOther" >> beam.Map(lambda n: f"other: {n}")
    )
PY
```

Expected: `completed: 1245` and `other: 3755`. The two counts add up to
5,000. The sample data is seeded, so these numbers are the same on every
machine — if you get different ones, you regenerated the sample data with
different parameters.

Two API details in that code are load-bearing, and getting either wrong
produces a confusing failure.

**`.with_outputs(...)` declares the tags.** Without it, the result of
`| beam.ParDo(...)` is an ordinary PCollection and the subscript raises:

```text
TypeError: 'PCollection' object is not subscriptable
```

The `main="main"` argument names the *main* output — the one the `DoFn`
yields to without a tag. A `DoFn` that only ever yields `TaggedOutput`s
has nothing on its main output, so nothing is lost by naming it.

**`Count.Globally()`, not `Count.PerKey()`.** `PerKey()` expects
`(key, value)` tuples and raises a type error on a flat PCollection:

```text
apache_beam.typehints.decorators.TypeCheckError: Input type hint violation
at Count: expected Tuple[TypeVariable[K], TypeVariable[V]], got
<class 'str'>
```

> **A trap in the trap.** `beam.Map(lambda n: f"completed: {n}")` as the
> *last* step of a branch produces no visible output, while
> `beam.Map(print)` appears to work. The reason is that `print` returns
> `None`, so Beam drops the element — but the print already happened as a
> side effect. A `Map` that returns a real value, with nothing
> downstream to consume it, is simply discarded: a PCollection with no
> sink does no work. When you want to *see* values, either use
> `beam.Map(print)` or write to a file. Chapter 1 covers why a
> pipeline with no sink proves nothing; this is the same rule, seen
> from the other side.

### Step 9 — a `DoFn` that drops bad rows explicitly, with a log line

```bash
.venv/bin/python - <<'PY'
import logging
import sys

sys.path.insert(0, "project")

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from transforms import is_valid_order, try_parse_order_line

logging.basicConfig(level=logging.INFO)

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])

log = logging.getLogger("hands_on")


class ParseOrderFn(beam.DoFn):
    """Parse CSV lines into order dicts, skipping malformed rows."""

    def process(self, line):
        row = try_parse_order_line(line)
        if row is None:
            log.warning("skipping malformed order line: %.120s", line)
            return
        if not is_valid_order(row):
            log.warning("skipping invalid order: %s", row.get("order_id"))
            return
        yield row


with beam.Pipeline(options=options) as p:
    (
        p
        | "ReadOrders" >> beam.io.ReadFromText(
            "./sample_data/orders.csv",
            skip_header_lines=1,
        )
        | "ParseOrders" >> beam.ParDo(ParseOrderFn())
        | "Count" >> beam.combiners.Count.Globally()
        | "Print" >> beam.Map(print)
    )
PY
```

Compare the output with Step 3. The counts match, but here the drops are
logged and visible, and the policy is in the code rather than implied by
a `None` return.

### Step 10 — `Reshuffle` in a skewed pipeline

```bash
.venv/bin/python resources/sample_data.py --output-dir ./sample_data --hot-key-rate 0.5
```

```bash
.venv/bin/python - <<'PY'
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])

with beam.Pipeline(options=options) as p:
    (
        p
        | "ReadOrders" >> beam.io.ReadFromText(
            "./sample_data/orders.csv",
            skip_header_lines=1,
        )
        | "Parse" >> beam.Map(lambda line: line.split(","))
        | "KeyByCustomer" >> beam.Map(lambda row: (row[1], float(row[7])))
        | "Reshuffle" >> beam.Reshuffle()
        | "SumByCustomer" >> beam.CombinePerKey(sum)
        | "Count" >> beam.combiners.Count.Globally()
        | "Print" >> beam.Map(print)
    )
PY
```

With 50% of orders on one customer, the `CombinePerKey` has a hot key.
`Reshuffle` distributes the data before the combine, so the hot key's
partial sums are computed in parallel across workers instead of in one.

Regenerate the normal sample data afterwards:

```bash
.venv/bin/python resources/sample_data.py --output-dir ./sample_data
```

---

## 🛠️ Common Errors and Fixes

### The output has fewer rows than expected, and there is no error

Your `Map` returned `None` for some elements and they were dropped.
`None` is Beam's "do not emit" sentinel.

```text
# WRONG — silently filters
| "Validate" >> beam.Map(validate_order)

# RIGHT
| "Validate" >> beam.Filter(lambda row: is_valid_order(row))
```

To find them, add a counting side branch and compare the two counts.

### `TypeError: Map can be used only with callable objects. Received <...> instead`

You passed a `DoFn` *instance* to `Map`. `DoFn` instances only work with
`ParDo`:

```text
# WRONG
| "Parse" >> beam.Map(ParseOrderFn())

# RIGHT
| "Parse" >> beam.ParDo(ParseOrderFn())
```

### `TypeError: MapTuple can be used only with callable objects`

Same cause. And if you pass a two-argument function to `Map` (rather than
`MapTuple`), you get:

```text
TypeError: <lambda>() takes 2 positional arguments but 1 was given
```

That is the classic "I need to unpack the tuple" error. Use `MapTuple`.

### `TypeError: Side inputs must have defaults for MapTuple`

`MapTuple` needs to know which of your function's parameters are the
tuple elements and which are side inputs. If your function has side
input parameters without defaults, Beam cannot tell them apart. Give the
side input parameters defaults, or use `Map` with a lambda and keyword
arguments.

### `ValueError: PCollection of size 2 with more than one element accessed as a singleton view`

`AsSingleton` on a side with more than one element. The side must have
exactly one element per window. Use `AsList` and index it, or restructure.

### `AttributeError: 'EmptySideInput' object has no attribute 'get'`

`AsSingleton` on an *empty* side. The default is `EmptySideInput()`,
which raises on any attribute access. Pass a default:

```python
beam.pvalue.AsSingleton(config, default_value={})
```

### `TypeError: 'NoneType' object has no attribute 'split'`

A `Map` received `None` — either a `Map` that returned `None` upstream,
or a `Map` whose function returned `None` for a malformed record. Find it
by counting before and after the suspect transform.

### `ValueError: Expected type str for element, but got int`

A coder mismatch. The input PCollection's coder and the output coder
disagree. Usually it means you mixed a typed PCollection with a `str`
sink, or the source's element type is not what you assumed. `WriteToText`
will `str()` anything, so this error comes from an intermediate transform
with a type hint.

### The `FlatMap` output has the right number of elements but each is a list

You used `Map` instead of `FlatMap`. `Map` does not flatten.

### The `FlatMap` worker runs out of memory

The return value is being materialised. A `FlatMap` whose function returns
a huge generator collects the whole thing. Bound the expansion, or use
`GroupByKey` for unbounded groups.

### `RuntimeError: Transform name is already used`

Two transforms in the same pipeline share a label. Find it with:

```bash
python resources/audit_course.py
```

### `RuntimeError: cannot pickle '...' object`

Your `Map` function or `DoFn` captured something unpicklable — a
connection, a file handle, a lock. Move it into a `DoFn`'s `setup`
method.

### The side input is empty and the enrichment is silently a no-op

The side PCollection read from a path that matched no files, or a filter
removed everything. Check the side's row count separately.

### The `Reshuffle` made the job slower

Expected when there was no fusion to break. `Reshuffle` costs a full
shuffle. It pays off only when it separates expensive work from a
skewed `GroupByKey`, or provides checkpointing for a long-running stage.

---

## 💡 Production Notes

- **`None` is a load-bearing value in Beam.** A `Map` that returns `None`
  drops the element, silently. In a pipeline that moves money, that is a
  data-loss bug with no stack trace. Make the drop explicit — a `Filter`,
  or a `DoFn` with a `return` and a log line.
- **Prefer `Filter` over `Map`-returning-`None`**, even when they produce
  the same result. The job graph then says what happened, and a reviewer
  reading the graph can see the data was filtered rather than transformed
  into nothing.
- **A `Map` should be pure and cheap.** It should take an element, do
  arithmetic or a lookup, and return an element. If it opens a socket,
  reads a file, or calls a model, it belongs in a `DoFn` with batching,
  or in a side input, or in a different system.
- **Never put a per-element network call in a `Map`.** Beam parallelises
  across bundles, not within one. A `Map` that does HTTP is a serial HTTP
  client wearing a distributed costume.
- **`FlatMap` materialises.** The iterable it returns is collected before
  being emitted. Bounded, modest expansions only. For unbounded groups,
  use `GroupByKey`, which streams.
- **Side inputs must fit in a worker's memory.** They are materialised
  and held on every worker. A side that is 10 GB means 10 GB per worker
  or an out-of-memory kill. If the reference data is larger than memory,
  it is a join, not a side input.
- **Use `AsDict` for lookups, `AsIter`/`AsList` for scans.** The
  difference between O(n·m) and O(m) is the difference between a job that
  finishes and one that does not. If you find yourself writing a `for`
  loop over a side input inside a `Map`, that loop is your bottleneck.
- **Prefer `AsList` over `AsSingleton` in new code.** `AsSingleton` fails
  confusingly on the empty case, and the singleton
  concept does not survive streaming cleanly.
- **`TaggedOutput` is the escape hatch from the one-output rule.** It is
  the only way to route elements to different sinks from a single read.
  Reach for it when the requirement is "split the stream by a column",
  and prefer a `Filter` + two branches when the split is a simple
  predicate.
- **Order matters in the graph, but the runner may reorder execution.**
  A `Filter` after a `Map` is not the same as a `Filter` before it, in
  terms of cost: filter first, then transform. The runner will not
  reorder a `Filter` before a `Map` for you, because that would change
  the semantics.
- **`Reshuffle` is a scalpel, not a hammer.** It is a full shuffle with
  a memory cost. Use it when the job graph shows one slow step
  downstream of an expensive per-record step, and when the data is
  skewed. Do not add it "to be safe".
- **The `DoFn` is the right unit of testability.** A lambda in a
  pipeline can only be tested by running the pipeline. A `DoFn` class can
  be unit-tested directly, and the course's `project/tests/` does exactly
  that for `ParseOrderFn` and `RevenueByRegionFn`.

---

## 🔑 Key Takeaways

- `Map` is **1 → 0 or 1**. Returning `None` drops the element, silently.
  Use `Filter` when you mean to drop.
- `FlatMap` is **1 → N** and accepts any iterable as the return value —
  but it **materialises** that iterable before emitting. Bounded
  expansions only.
- `Filter` is literally `FlatMap` that emits the element or nothing, so a
  filter that raises fails the bundle rather than dropping the element.
- `MapTuple` / `FlatMapTuple` unpack a tuple into multiple function
  arguments. They are a calling convention over `ParDo`, not a separate
  execution path.
- `Map` produces one output PCollection. Multiple outputs need a `DoFn`
  with `TaggedOutput`.
- Side inputs have four views: `AsDict` (O(1) lookup), `AsIter` (lazy
  scan), `AsList` (materialised), `AsSingleton` (exactly one element,
  and it fails unhelpfully when there is none).
- **A side input that you look up by key must be `AsDict`.** A linear
  scan inside a `Map` is O(n·m) and does not scale.
- `Reshuffle` prevents fusion and provides checkpointing. It is a no-op
  when there is no expensive work to separate or the data is already
  shuffled.
- A `DoFn` is the right tool when you need timestamps, windows, keys,
  state, multiple outputs, or batch processing — and it is the right unit
  for testing.
- The three performance traps: **I/O in a `Map`** (serial network calls
  per element), **a generator in a `FlatMap`** (materialised in memory),
  and **a `Map` returning `None`** (silent data loss).

---

## 📚 Practice Exercises

1. **Measure the `None` drop.** Build a pipeline over `orders.csv` with
   two branches: one that uses `Map` returning `None` for invalid rows,
   one that uses `Filter`. Count the elements reaching the sink in each.
   Then add a third branch that counts *all* input rows, and show the
   arithmetic. Finally, make the `Map` version log every dropped row and
   re-run — argue for or against shipping the `Map` version.

2. **Benchmark `AsIter` against `AsDict`.** Generate a reference file of
   50,000 products and an order file of 200,000 orders. Enrich with
   `AsIter` (linear scan) and with `AsDict` (hash lookup). Time both
   locally. Then reason about what happens when the reference grows to
   5,000,000 — does the `AsDict` version still fit the side-input
   memory budget?

3. **Explode a nested field.** Given the NDJSON event data, write a
   `FlatMap` that takes an event and emits one row per (event, dimension)
   pair for region, event_type, and product_id. Then write a `Map` version
   that emits a *list* of those pairs instead, and show the difference in
   the output by counting elements in each.

4. **Compare `FlatMap` and `GroupByKey`.** Given the cart data from Step 5
   of the hands-on, produce the same result two ways: a `FlatMap` that
   explodes each cart, and a `GroupByKey` that groups the items by cart.
   Measure the element counts and the memory profile. Then create a
   synthetic cart with 500,000 items and show which approach survives.

5. **Write a `DoFn` with two outputs.** Write a `DoFn` that routes orders
   into three outputs: `high_value` (amount over 500), `low_value`, and
   `malformed` (rows that fail to parse). Use `TaggedOutput`. Then write
   the same thing with `Filter` + three branches and compare the job
   graphs and the code length. Which do you prefer, and why?

6. **Find the real `Reshuffle` case.** Run the pipeline from Step 10 with
   and without the `Reshuffle` on the skewed data, and time both. Then
   move the `Reshuffle` to *after* the `CombinePerKey` and time it a
   third time. Explain all three numbers in terms of fusion and skew, and
   state the general rule for when `Reshuffle` is worth its cost.

---

## 📖 Further Reading

- Apache Beam Python SDK transforms reference — https://beam.apache.org/releases/pydoc/current/apache_beam.transforms.html
- Apache Beam `Map` transform documentation — https://beam.apache.org/documentation/transforms/python/map/
- Apache Beam `FlatMap` transform documentation — https://beam.apache.org/documentation/transforms/python/flatmap/
- Apache Beam side inputs — https://beam.apache.org/documentation/programming-guide/#side-inputs
- Apache Beam Python API reference (`pvalue`) — https://beam.apache.org/releases/pydoc/current/apache_beam.pvalue.html
- Apache Beam "Beam SDKs: How to handle skewed data" — https://beam.apache.org/documentation/basics/#skew
- Google Cloud Dataflow "Optimizing a pipeline" — https://cloud.google.com/dataflow/docs/guides/optimizing-pipelines
- Python `csv` and `json` module documentation — https://docs.python.org/3/library/json.html
