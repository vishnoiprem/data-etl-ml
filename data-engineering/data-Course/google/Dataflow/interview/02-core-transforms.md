# Module 2 — SDK & Core Transforms

> **16 questions · Module 2 · SDK & Core Transforms**

---

## Map, FlatMap and Filter

### 1. When do you reach for `FlatMap` instead of `Map`, and what is the failure mode of getting it wrong?

`Map` is one-in, zero-or-one-out: it applies a function to each element and emits at most one result per input. `FlatMap` is one-in, zero-or-many-out: the function returns an iterable and Beam emits all of it. Use `FlatMap` whenever one input row legitimately expands into several output rows — exploding a comma-separated field, flattening a nested JSON array, turning one order into one row per line item.

The failure mode of getting it wrong is quiet data loss, and it is the single most common Beam bug. `Map` with a function that returns a *list* does not flatten it; it emits the list as a single element. Downstream, a `Filter` or a `Map` that expects a scalar now receives a `list`, and the symptom is a `TypeError` deep in an unrelated transform, or — worse — a `KeyError` swallowed by a `try` block, or a BigQuery load that silently wrote an array column where a string was expected.

The inverse failure is worse: using `FlatMap` where you meant `Map`. If the function returns `None` for rows you wanted to drop, `FlatMap` raises `TypeError: 'NoneType' object is not iterable` at run time on a worker, not at graph-construction time.

A useful discipline: `FlatMap` should return an empty iterable for "drop this row", never `None`. And when you genuinely want a one-or-nothing semantic, `Filter` is clearer than a `Map` that returns `None`:

```python
with beam.Pipeline() as p:
    rows = (
        p
        | "Create" >> beam.Create([("a", [1, 2]), ("b", [])])
        | "Flatten" >> beam.FlatMap(lambda kv: kv[1])
        | "Print" >> beam.Map(print)
    )
```

The mechanism: `Filter` is literally implemented as a `FlatMap` whose wrapper returns `[x] if fn(x) else []`. So `Filter` is the zero-or-one case of `FlatMap`, and understanding that one line removes a whole category of confusion.

### 2. What is `MapTuple` for, and when is it better than `Map`?

`MapTuple` applies a function to the *components* of a `(key, value)` pair separately rather than to the pair as a whole. `Map` on a keyed PCollection gives your function the whole tuple; `MapTuple` gives it the key and the value as two arguments.

The use case is when the key and the value have different types and you want type safety on both. It is also the natural way to keep the key intact while transforming the value — with `Map` you must return `(kv[0], new_value)` and get the key's type right by hand.

```python
import apache_beam as beam

with beam.Pipeline() as p:
    pairs = p | "Create" >> beam.Create([("EMEA", 10.5), ("AMER", 3.25)])
    tagged = pairs | "Tag" >> beam.MapTuple(lambda k, v: (k, f"{v:.2f}"))
    _ = tagged | "Print" >> beam.Map(print)
```

The trade-off: `MapTuple` is less flexible. You cannot drop the element, and you cannot add a component — the output is always a two-tuple. If you need either, use `Map` with an explicit lambda.

The production detail that matters: `MapTuple` gives Beam better type hints, and type hints give you a better coder. `Map` with an untyped lambda falls back to `FastPrimitivesCoder` and guesses at runtime; a `MapTuple` with annotated parameters lets Beam pick the coder statically and fail fast if the types do not match. On a large job that difference is minutes of wasted cluster time.

The failure story: a team wrote `MapTuple(lambda k, v: (k, v * 2))` where `v` was sometimes a string. Beam's type inference was silent, so the pipeline ran and failed on the worker with `TypeError: can't multiply sequence by non-int of type 'str'` — on element 4 million, roughly 20 minutes in. With `Map` and a matching annotation, the same mismatch would have been caught at pipeline construction.

### 3. What is a side input, and when is using one the wrong call?

A side input is a second PCollection made available to a transform as a read-only lookup. The runner broadcasts it to every worker, so the transform can look values up in memory without a shuffle.

The mechanism: the side input's contents are materialised once and shipped to each worker; the transform receives it in place of the PCollection argument at execution time. `beam.pvalue.AsDict`, `AsIter`, and `AsList` are the current views — `AsSingleton` is deprecated for anything but a single value, and `AsSingleton` on an empty PCollection raises at pipeline *construction* time, not at run time.

The rule for when a side input is the wrong call: **when the build side does not comfortably fit in the memory of every worker.** The limit is roughly 100 MB of decoded objects per worker. A side input is a broadcast, so its cost is multiplied by your worker count, and it is re-read at every bundle boundary. The course's own `_enrich_with_category` does a linear scan of the reference list for every order — fine for a tiny product table, and O(n×m) the moment the table grows.

There is a second wrong-call case: **when the side input is large but you only need a few keys per element.** A side input forces the *whole* build side onto every worker even if each worker touches three keys. The right answer there is a shuffle join (`CoGroupByKey`) or a pre-aggregated `CombinePerKey`.

The production failure story: an orders pipeline enriched each order with a currency rate from a side input. The rates file started at 400 rows and was fine for two years. It then grew to 40 million rows — 6 GB decoded — and workers began OOMing. The job failed with `Java heap space` on one worker, retried three times, and failed the whole run at a cost of about 40 wasted minutes. The fix was to move to a `CoGroupByKey` join against a `CombinePerKey`-aggregated rates table. The lesson: a side input is a size-bounded optimisation, and **nothing enforces the bound for you** — the reference table grew, and the pipeline did not complain until a worker died.

### 4. What is the difference between `ParDo` and `Map`, and when do you actually need `ParDo`?

`Map` is a `ParDo` with a fixed shape: one input, zero or one output, no side outputs, no access to the element's timestamp or window. `ParDo` is the general form: a `DoFn` whose `process` method can yield zero, one, or many outputs, access `timestamp`, `window`, and `pane_info`, and emit **tagged side outputs**.

Reach for `ParDo` when you need any of: timestamp or window access, side outputs, per-element state, `StartBundle`/`FinishBundle` hooks, or a reusable, unit-testable class instead of a lambda. The course's `ParseOrderFn` is a `ParDo` for exactly this reason — it is a named, testable class with a docstring, and it can later be extended with timestamp handling without rewriting the call site.

The trade-off is footguns. `ParDo` can emit *zero* elements, which silently drops data, and it can emit many, which silently explodes downstream. `Map` cannot do either, so the shape of the data flow is visible in the transform name. The course's guidance — prefer `Map`/`Filter` where you can — is right: use `ParDo` because you need its power, not because it is more general.

The mechanism difference that matters at scale: `Map` and `Filter` are *liftable* and fusible into surrounding steps, because their per-element semantics compose. A `ParDo` with a `CombineFn`-like side effect or with `FinishBundle` semantics generally is not, so it becomes a fusion barrier and costs you a materialisation.

The production failure story: someone replaced a `Filter` with a `ParDo` that returned `None` for invalid rows. `None` is not an iterable, so the `ParDo` raised `TypeError: 'NoneType' object is not iterable` on the first bad row — on a worker, 20 minutes into the job. The rule for a `ParDo` that drops data is to `return` without yielding, never to yield `None`.

## ParDo and DoFn

### 5. What is the lifecycle of a `DoFn`, and which parts run once versus once per element?

A `DoFn` has three hooks. `setup()` runs **once per DoFn instance** — that is, once per worker, per bundle-processing thread, before any elements. `process()` runs **once per element**. `teardown()` runs **once per DoFn instance**, after the last element.

This lifecycle is the reason DoFn instances are cheap to create but expensive to hold state in. If you put a per-element counter on `self`, it accumulates across every element that instance sees — and an instance's lifetime is not the pipeline's lifetime. Beam may create several instances across the run, and you cannot assume one instance sees all the data. Per-element state that must be correct has to live in a keyed accumulator (a `CombineFn`) or in explicit `userstate`, not on `self`.

The `setup()` hook is where you put expensive, reusable resources: an open database connection, a loaded ML model, a parsed CSV schema. `setup()` failing fails the whole bundle, not one element — which is what you want for a resource that must exist.

The practical failure story: a `DoFn` opened a database connection in `process()` and never closed it. The connection pool was exhausted after about 10,000 elements, and the worker started failing with `OperationalError: too many connections`. The fix was to move the connection to `setup()` and close it in `teardown()` — one connection per worker instead of one per element.

The trap in `setup()`: it runs on the worker, not on the driver. Anything it does is serialised to the worker and re-executed there, so a `setup()` that reads a local file path will only work if that path exists on the worker — which, on Dataflow, it does not.

### 6. Why must `DoFn` classes be picklable, and what actually breaks when they are not?

A `DoFn` is serialised to the worker. On Dataflow, that means pickling the class and its state into the pipeline proto, shipping it to the worker, and unpickling it there. Anything captured in a closure or held as instance state must survive that round trip.

The things that do not survive: open sockets and database connections, file handles, threads and locks, a lambda defined inside another lambda (nested closures often fail to pickle), and an unpicklable third-party object such as a compiled regex cache or a DB-API cursor.

Beam usually gives you a clear error — `TypeError: cannot pickle '_thread.lock' object` — but not always at the moment you expect. Sometimes the error appears at submission and sometimes only when a worker actually unpickles the `DoFn`, which means the job starts, provisions workers, and then fails minutes later. That is a particularly expensive failure mode: you pay for the workers before the job tells you the code was never going to work.

The discipline that prevents it: keep `DoFn` classes free of side effects in `__init__`, do the work in `setup()`, and make sure every attribute you set is picklable. A `DoFn` that holds only primitive attributes and a `logging.Logger` is safe. Note that `logging.Logger` objects are picklable in CPython 3.7+ (they pickle by name), but a logger with a `FileHandler` attached to an open file is not.

The production symptom worth recognising: a job that fails on every worker with `PicklingError` *after* successful submission. The fix is always the same: move the unpicklable object out of the `DoFn` and into `setup()`, or into a side input that Beam manages.

### 7. What is `PaneInfo` for, and when do you actually need it?

`PaneInfo` describes the *firing* of a window rather than the data in it: `index` (which firing this is, zero-based), `n` (the total number of firings for this window, `None` if not yet final), `is_first`, and `is_last`.

You need it when the same window fires more than once and you must not double-count. The canonical case: a window with an `AfterCount(10)` trigger fires every ten elements. Each firing is a "pane". With `DISCARDING` accumulation, each firing contains only what arrived since the last firing, so the panes add up to the whole window — and you can just emit each pane. With `ACCUMULATING`, each firing contains the *running total* for the window, so emitting every pane means the consumer sees the same elements repeatedly, and a naive `INSERT` writes the same row N times.

`PaneInfo` is how you tell the two situations apart: `pane_info.index == 0` is the first firing, and `pane_info.is_last` marks the final firing of the window.

```python
import apache_beam as beam


class EmitOnLastPane(beam.DoFn):
    def process(self, element, pane_info=beam.DoFn.PaneInfoParam):
        if pane_info.is_last:
            yield element
```

The mechanism: `PaneInfo` is supplied by the runner as a `DoFn` parameter, exactly like `timestamp` and `window`. It is derived from the trigger's firing state, so it is only meaningful in a windowed context; in the global window it reports a single pane.

The production failure story: a pipeline used `AfterCount(100)` with `ACCUMULATING` to get running totals, and wrote each pane to BigQuery with `WRITE_APPEND`. A window of 1,000 elements fired ten times, and the final running total was written ten times. The revenue dashboard read the sum of that column and reported the day's revenue as roughly 5.5× the real figure. The fix was to write only on `pane_info.is_last`, or to switch to `DISCARDING` and let the consumer sum the deltas.

### 8. How do the `DoFn` parameter annotations work, and why do they matter for performance?

A `DoFn` can declare extra parameters by giving them a default of one of Beam's sentinel objects: `beam.DoFn.TimestampParam`, `WindowParam`, `PaneInfoParam`, `ElementParam`, `KeyParam`, `BundleContextParam`, `SideInputParam`. The runner then injects the corresponding value at execution time.

They matter for three reasons. First, **correctness**: `timestamp` is the element's *event* time, not its arrival time, and without the annotation you simply do not have it. In Beam every element carries a timestamp, defaulting to the arrival timestamp, and `timestamp` is the only way to read it. Second, **type hints**: annotating `process` lets Beam infer the element type statically and pick a better coder. Third, **fusing**: a `DoFn` that reads the timestamp forces the runner to keep per-element timestamps through the pipeline, which is a real cost on a high-volume stream — the timestamp metadata is carried on every element.

```python
import apache_beam as beam


class ParseFn(beam.DoFn):
    def process(self, line, timestamp=beam.DoFn.TimestampParam):
        yield {"line": line, "event_time": timestamp.to_rfc3339()}
```

The failure story for getting the timestamp wrong is the classic event-time bug: a pipeline that used processing time (no timestamp parameter) put 3% of events into the wrong hour, because those events arrived out of order. Every hourly total was off by a few percent, the totals still summed to the grand total, and nothing looked broken. Reading `timestamp` and re-stamping with `beam.window.TimestampedValue` fixed it.

## Combining

### 9. `CombinePerKey` versus `GroupByKey` — when is the difference between them a survival issue?

Always prefer `CombinePerKey`. `GroupByKey` materialises every value for a key in memory before you do anything with it; `CombinePerKey` keeps a compact accumulator and merges partial results. For a group of a million values, `GroupByKey` holds a million values on one worker; `CombinePerKey` holds one accumulator.

The mechanism: `CombinePerKey` fuses a `CombineFn` into the *upstream* step where it can. Partial accumulators are computed per bundle, then merged across workers during the shuffle — and the merge is the only point where a real cross-worker shuffle is strictly needed. `GroupByKey` cannot do this: it must gather the raw values before any reduction can start.

The memory difference is not incremental. A `GroupByKey` over a skewed key — one customer with 50 million orders — puts all 50 million on one worker. A `CombinePerKey` over the same data keeps 50 million *scalar accumulations* spread across the bundles, and the shuffle carries partial sums. For a sum, that is a difference between "one worker needs 8 GB" and "one worker needs 8 bytes".

The failure story: a sessionisation pipeline used `GroupByKey` and worked fine on a 2 GB dataset. At 40 GB it failed with `OutOfMemoryError: Java heap space` on a single worker, repeatedly, and the job never completed. Replacing it with `CombinePerKey` over a custom accumulator that tracked session boundaries made it pass in the same wall-clock time.

The caveat, and it is a real one: **`CombinePerKey` cannot express everything `GroupByKey` can.** If you need the actual values — to sort them, to take the top N, to compute a median without approximation — you need the values, and `GroupByKey` is the honest answer. In that case, control the memory instead: use `beam.combiners.Sample` for sampling, `beam.combiners.Top` for top-N, and consider pre-filtering to reduce the group size.

### 10. What are the four methods of a `CombineFn`, and what does each one do?

`create_accumulator()` returns the empty accumulator. `add_input(acc, element)` folds one element into an accumulator. `merge_accumulators(accs)` merges an iterable of accumulators into one. `extract_output(acc)` converts the final accumulator into the output element.

The order of operations matters: `create_accumulator` runs once per bundle (and once per worker), `add_input` runs once per element, `merge_accumulators` runs during the shuffle, and `extract_output` runs once per key at the end.

The accumulator is the state that travels between workers, so its size *is* your memory bound. An accumulator that grows with the number of inputs — a list, a set, a dict of every element seen — is a `GroupByKey` wearing a disguise, and it will OOM on exactly the same inputs. A scalar or fixed-size-tuple accumulator is what you want.

The course's `RevenueByRegionFn` is the shape to copy: the accumulator is a two-field dict (`order_count`, `revenue_eur`), `add_input` mutates and returns it, `merge_accumulators` sums two partials field by field, and `extract_output` rounds and casts the count to an `int`.

```python
import apache_beam as beam


class SumFn(beam.CombineFn):
    def create_accumulator(self):
        return 0.0

    def add_input(self, acc, value):
        return acc + value

    def merge_accumulators(self, accs):
        return sum(accs)

    def extract_output(self, acc):
        return acc
```

The failure story: a team wrote a `CombineFn` whose accumulator was a `list` of all values, intending to sort at the end. It passed every unit test and worked on the sample data. On the first full-scale run it OOMed on a hot key. The accumulator had to become a fixed-size structure — for a median, either an approximate quantile sketch or a fixed-width histogram.

### 11. Why does associativity matter so much for a `CombineFn`, and what happens when you violate it?

Because Beam merges partial accumulators from different workers **in an arbitrary order**, and the merge must produce the same result regardless of that order. That is the definition of an associative and commutative operation: `merge(merge(a, b), c) == merge(a, merge(b, c))` and `merge(a, b) == merge(b, a)`.

The reason the order is arbitrary is structural: the runner splits the input into bundles, gives bundles to workers arbitrarily, and merges the partial results as they arrive. A combiner that is not order-independent makes the *output* depend on the physical execution — the same input produces different numbers on different days, or on different runners. That is not a rounding curiosity; it is a pipeline whose results cannot be reproduced or audited.

The failure story that makes this concrete: a team implemented a running percentage by accumulating `(sum, count)` and computing the ratio in `extract_output` — that is fine and associative. But a different team implemented "average with a shrinkage penalty" by subtracting a small epsilon on every `add_input` to damp runaway values. Under a small input the epsilon was invisible; at scale the accumulated penalty differed by a factor of 2 between the bundle-based runner and Dataflow, and the team's revenue adjustment report did not reconcile with the raw numbers. The fix was to make the operation exactly associative — fold the damping into a function of the *accumulator*, not of the count of calls.

The practical test: if you cannot express your combiner as a pure function of the accumulator and the input, you probably want `GroupByKey`, or a different algorithm.

### 12. Why is there no `beam.combiners.Sum`, and what do you use instead?

There is no `beam.combiners.Sum` because a sum does not need a custom `CombineFn` — Python's builtin `sum` is already associative and commutative, and Beam can lift it directly into the upstream step. The `beam.combiners` namespace exists for the operations that need *something* beyond a builtin: `Count`, `Mean`, `ToList`, `ToSet`, `ToDict`, `Top`, `Largest`, `Smallest`, `Sample`. Those all need a `CombineFn` because the builtin does not exist or because the combinable form is not obvious.

So the answer to "how do I sum by key" is `beam.CombinePerKey(sum)`:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    totals = (
        p
        | "Create" >> beam.Create([("EMEA", 10.5), ("EMEA", 4.5), ("AMER", 3.0)])
        | "SumByRegion" >> beam.CombinePerKey(sum)
    )
    _ = totals | "Print" >> beam.Map(print)
```

The equivalent for a count is `beam.combiners.Count.PerKey()`, which is a `CombineFn` counting elements per key. `beam.combiners.Mean.PerKey()` exists too, and is worth knowing because a mean is *not* something you can compute by combining two means — the `CombineFn` carries the `(sum, count)` pair internally so that merging is still associative. That is the general pattern: when the output is not directly combinable, the accumulator holds enough state to make it so.

The failure story: someone read a blog post using `beam.combiners.Sum.PerKey()` and got `AttributeError: module 'apache_beam.transforms.combiners' has no attribute 'Sum'`. It is a one-line fix, but the confusing part is that `Count`, `Mean`, and `Top` all *do* have `PerKey` variants, so the namespace looks like it should have `Sum` too. It does not, because `sum` is already a builtin.

## Grouping and joining

### 13. What is `CoGroupByKey`, and what is it explicitly not?

`CoGroupByKey` groups multiple keyed PCollections by key simultaneously and emits, for each key, a tuple with one list per input collection. It is the Beam equivalent of a **full outer join** on the key.

What it is *not*: it is not a general join. It does not join on anything other than the key, it does not support join predicates like "key equality and timestamp within 5 seconds", and it does not produce a cartesian product across different keys. If you want to join orders to shipments where the shipment arrived *after* the order but within 24 hours, `CoGroupByKey` on the order ID will not do it — you need a temporal join, which means a custom `CombineFn` over a window, or a different tool.

The mechanism: `CoGroupByKey` is a group-by across N inputs. For each key, it materialises the values from each input — so it has the *same memory profile* as `GroupByKey`, not `CombinePerKey`. If you only need aggregates from each side, aggregate each side first with `CombinePerKey` and then `CoGroupByKey` the two small results. That is the single most valuable piece of advice about `CoGroupByKey`: **never group raw inputs with it; group pre-aggregated inputs with it.**

```python
import apache_beam as beam

with beam.Pipeline() as p:
    orders = p | "Orders" >> beam.Create([("a", 1), ("b", 2)])
    refunds = p | "Refunds" >> beam.Create([("a", 10)])
    joined = (
        {"orders": orders, "refunds": refunds}
        | "CoGroup" >> beam.CoGroupByKey()
    )
    _ = joined | "Print" >> beam.Map(print)
```

The failure story: a pipeline joined 200 million order rows to a 200 million refund rows with `CoGroupByKey` directly. It OOMed on the first hot key. The fix was to `CombinePerKey` each side down to a per-key total first — reducing both sides from hundreds of millions of values to a few hundred thousand keys — and then `CoGroupByKey` the aggregates. The job then completed in a fraction of the time.

### 14. What does `Reshuffle` do, and when is it the right tool?

`Reshuffle` is a deliberate barrier that re-partitions the data uniformly. It breaks fusion on purpose and forces a clean re-shard, so that downstream stages receive evenly distributed keys rather than whatever partitioning the upstream source happened to produce.

Use it for two things. First, **skew**: when one hot key sends all the work to one worker, `Reshuffle` before the downstream group spreads the load. Second, **fusion control**: when a long chain of steps is fused into one stage and you want to break it so intermediate state does not accumulate, or so you get a checkpoint boundary in streaming.

The mechanism is a shuffle that is cheap in a specific way: it shuffles the data but *does not* merge anything, so the values are redistributed without being combined. The classic pattern is to fan out a hot key into N synthetic keys, then re-key after the group.

The trade-off is that `Reshuffle` costs a full shuffle — network plus disk. It is not free, and it disables fusion across that boundary. Using it "to be safe" on every pipeline is a real cost with no benefit.

The failure story: a pipeline aggregated by `customer_id`, and one customer generated 40% of all traffic. The stage took 11 hours; 99% of it was one worker processing one key while the rest of the cluster sat idle. The fix was the hot-key splitter: expand the hot key into `(customer_id, fanout_index)` pairs before the group, then merge the partial results afterwards. A `Reshuffle` would also have spread the load, but it would have shuffled the *entire* dataset to fix one key, which was more expensive than the targeted splitter.

### 15. What is `Flatten`, and what coder compatibility does it require?

`Flatten` merges multiple PCollections into one — the equivalent of `UNION ALL`. It is the simplest transform in Beam and the one most likely to fail at run time for a reason that is not obvious at graph-construction time.

The constraint is **coder compatibility**: every PCollection being flattened must have the same coder, or at least coders that can encode each other's elements. When Beam merges the inputs it has to pick one coder for the output. If the inputs disagree, you get a failure at *execution* time — often `AssertionError: Coder of type X does not match expected Y`, or a confusing decode error far downstream.

The common cause is that the two branches were built with different type hints, or one branch went through a transform that changed the element type. If one branch is `TupleCoder` of `(str, float)` and the other is `FastPrimitivesCoder` of the same shape, the merge can fail even though the *values* look identical. The fix is to make the types explicit on both sides, with matching type hints.

A related trap: `Flatten` requires all inputs to be `PCollection`s of the *same* element type — it is not a place to merge a keyed stream with an unkeyed one.

The production failure story: a pipeline flattened a keyed branch (from `Map(lambda r: (r["id"], r))`) with an unkeyed branch (from `Map(parse)`), and got `ValueError: PCollection type mismatch` at submission on some runners and a worker-side decode error on others. The fix was to key both branches consistently before flattening. The lesson: `Flatten` is not free of type discipline — it is where type discipline is enforced, sometimes late.

### 16. How do you route bad records to a dead-letter queue, and what is the mechanism?

The mechanism in Beam 2.77 is **`with_exception_handling()`** on a `ParDo` or `Map`. It returns a tuple of two PCollections: the good output and a dead-letter output whose elements are `(input, (exception_class, message, traceback))`.

```python
import apache_beam as beam


def parse_order(line):
    fields = line.split(",")
    if len(fields) != 9:
        raise ValueError(f"expected 9 fields, got {len(fields)}")
    return fields


with beam.Pipeline() as p:
    good, bad = (
        p
        | "Read" >> beam.io.ReadFromText("gs://bucket/orders.csv")
        | "Parse" >> beam.Map(parse_order).with_exception_handling()
    )
    _ = good | "Valid" >> beam.Filter(lambda row: row[6] == "complete")
    _ = bad | "WriteDlq" >> beam.Map(lambda item: f"{item[0]},{item[1][1]}")
```

Two alternatives, and why they are worse. The first is catching the exception inside your own function and returning a sentinel — that works, but the pipeline *succeeds*, so a total upstream failure looks like a successful run with zero rows. The second is `TaggedOutput` from a `ParDo`, which gives you finer control over *which* elements go where but requires you to write the try/except yourself.

`with_exception_handling()` has two parameters worth knowing: `threshold` caps the ratio of bad inputs before the pipeline aborts (default 1.0, meaning up to 100% bad and the job still succeeds — set it to something like 0.01 in production so a broken upstream does not silently produce an empty result), and `partial=False` buffers all outputs for an element until it processes successfully, so a partially-emitted element does not leak half-written rows.

The production failure story: a pipeline parsed CSV with a bare `try/except` that swallowed malformed rows and counted them in a metric. When the upstream producer changed its date format, *every* row became malformed, the pipeline exited 0, the metric showed 100% rejection — and the dashboard was empty for three days before anyone looked. The fix was `with_exception_handling()` with `threshold=0.01`, so the job fails loudly when the rejection rate is abnormal rather than producing a beautiful, empty, successful result.
