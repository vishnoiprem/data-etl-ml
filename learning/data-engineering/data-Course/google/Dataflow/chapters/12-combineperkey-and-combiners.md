# 2.7 — CombinePerKey & combiners.Count.PerKey

> **Section 2 · SDK & Core Transforms · Lecture 2.7 · 6:30**

## 🎯 What you will learn

- Why `beam.GroupByKey` does not scale, and what it costs at 10^9 elements
- The accumulator concept: the idea that makes Beam aggregations distributed
- `beam.CombinePerKey(sum)` and why it is the idiomatic way to sum
- `beam.combiners.Count.PerKey()` and the full list of built-in combiners in
  apache-beam 2.77 — including the one that does not exist
- The `CombineFn` four-method interface
- Associativity and commutativity, and why they determine whether your results
  are reproducible across runners
- `CombineFn` instance versus a plain callable
- `beam.CombineGlobally`, `beam.combiners.Top`, `beam.Distinct`
- A worked example of how partial accumulators from different workers merge
- The project's `RevenueByRegionFn` as the canonical combiner
- How to cross-validate a `CombinePerKey` against a pure Python function

---

## 🧠 Concept

### The problem `GroupByKey` creates

`beam.GroupByKey` takes KV pairs and produces, for each key, an iterable of
all the values under that key.

```python
import apache_beam as beam

with beam.Pipeline() as p:
    kv = p | "Create" >> beam.Create([("a", 1), ("a", 2), ("b", 3)])

    grouped = kv | "Group" >> beam.GroupByKey()

    (
        grouped
        | "Count" >> beam.Map(lambda kv: (kv[0], len(list(kv[1]))))
        | "Print" >> beam.Map(print)
    )
```

The output is `(key, iterable_of_values)`. The problem is not the shape —
it is what happens between the shuffle and the output.

`GroupByKey` must, for each key, **materialise every value under that key**,
because it does not know which value will arrive last. It reads them all
into memory, groups them, and hands the whole group downstream. If one key
has 50 million values, one worker must hold 50 million values in memory.

This is the scaling wall. The shuffle distributes *keys* across workers,
which is the right thing to do, but then the entire group lands on one
worker. `GroupByKey` is O(total elements) in network transfer and O(largest
group) in peak memory. It is fine for 1,000 elements and hopeless for
10^9.

### The accumulator idea

`CombinePerKey` solves this with a three-step idea.

**Step 1: summarise, don't collect.** Instead of gathering all the values
under a key, each worker computes a *partial summary* of the values it
happens to see. For a sum, the summary is a number. For a count, a number.
For "the largest three", a three-element list.

**Step 2: merge summaries.** The summaries are shuffled — and this is the
crucial part — **the summaries are small, and the shuffle is over summaries,
not over values.**

**Step 3: extract.** The final summary is converted to the output value.

```text
GroupByKey:                       CombinePerKey:

(a,1) (a,2) (a,3)  ──▶ [1,2,3]    (a,1) (a,2) (a,3)  ──▶ 6
                                    ──▶ partial sums: 1+2=3, 3
                                       ──▶ merge: 3+3=6
                                       ──▶ extract: 6
```

The network transfer in the `CombinePerKey` case is proportional to the
number of *keys*, not the number of *elements*. If you have 10^9 elements
and 10^4 keys, `CombinePerKey` transfers roughly 10^4 values plus whatever
the partial-combining step needs, while `GroupByKey` transfers 10^9 values
and holds the largest group in memory.

The partial-combining step — the one that turns many values into few
summaries *before* the shuffle — is the real win. On Dataflow this is a
pre-shuffle combine, and it is why `CombinePerKey` is dramatically cheaper
than `GroupByKey`.

### `beam.CombinePerKey` with a callable

The simplest form of `CombinePerKey` takes a callable that reduces an
iterable to a value:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    kv = p | "Create" >> beam.Create([("a", 1), ("a", 2), ("b", 3)])

    (
        kv
        | "Sum" >> beam.CombinePerKey(sum)
        | "Print" >> beam.Map(print)
    )
```

Output:

```text
('a', 3)
('b', 3)
```

`sum` is a Python builtin that takes an iterable and returns its total.
`CombinePerKey` applies it to the values under each key.

There is a naming trap here that trips up nearly everyone:

> **There is no `beam.combiners.Sum`.**

The `combiners` module has no `Sum` member. If you write
`beam.combiners.Sum.PerKey()`, you get:

```text
AttributeError: type object 'Sum' has no attribute 'PerKey'
```

—or, at the `combiners` level:

```text
AttributeError: module 'apache_beam.transforms.combiners' has no attribute 'Sum'
```

The correct forms are:

```python
beam.CombinePerKey(sum)                       # the builtin
beam.combiners.Count.PerKey()                 # count
beam.combiners.Mean.PerKey()                  # mean
```

### The complete list of built-in combiners in apache-beam 2.77

This is worth having in front of you, because the combiners module is bigger
and smaller than most people expect. Here is the verified list of public
members of `beam.combiners`, and how each one is actually applied:

| Combiner | Class | How to use it |
|---|---|---|
| Count | `combiners.Count` | `Count.PerKey()` / `Count.Globally()` |
| — | `combiners.Count.PerElement` | `Count.PerElement()` |
| Mean | `combiners.Mean` | `Mean.PerKey()` / `Mean.Globally()` |
| Top | `combiners.Top` | `Top.PerKey(n, key=...)` / `Top.Of(n, key=...)` |
| — | `combiners.Top.LargestPerKey(n, key=...)` | per key, largest |
| — | `combiners.Top.SmallestPerKey(n)` | per key, smallest |
| Largest | `combiners.Largest(n, key=None, reverse=False)` | global, largest |
| Smallest | `combiners.Smallest(n)` | global, smallest |
| Sample | `combiners.Sample` | `Sample.FixedSizePerKey(n)` / `Sample.FixedSizeGlobally(n)` |
| Latest | `combiners.Latest` | `Latest.PerKey()` / `Latest.Globally()` |
| ToList | `combiners.ToList` | `ToList()` — a **transform**, applied directly |
| ToSet | `combiners.ToSet` | `ToSet()` — a **transform**, applied directly |
| ToDict | `combiners.ToDict` | `ToDict()` — a **transform**, applied directly |
| Iterable | `combiners.Iterable` | `Iterable()` — a **transform**, applied directly |
| Any | `combiners.Any` | `Any()` — a **transform**, applied directly |
| Timestamp | `combiners.Timestamp` | `Timestamp()` — a **transform**, applied directly |
| Duration | `combiners.Duration` | `Duration()` — a **transform**, applied directly |

The last five rows deserve a note. `ToList`, `ToSet`, `ToDict`, `Iterable`,
`Any`, `Timestamp` and `Duration` are **not** combiners in the
`Count.PerKey()` sense — they are `PTransform`s that you apply directly
to a KV PCollection:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    kv = p | "Create" >> beam.Create([("a", 1), ("a", 2), ("b", 3)])

    (
        kv
        | "ToList" >> beam.combiners.ToList()
        | "Print" >> beam.Map(print)
    )
```

Trying to use one inside `CombinePerKey` fails, because it is not a
`CombineFn` and not a callable:

```text
TypeError: Expected a CombineFn or callable, got <ToList(PTransform) label=[ToList] at 0x11cf641a0>
```

**There is no `combiners.Sum`, no `combiners.Min`, and no
`combiners.Max`.** Sums use `CombinePerKey(sum)`; minima and maxima use
`combiners.Top.SmallestPerKey` / `combiners.Top.LargestPerKey`, or
`combiners.Largest` / `combiners.Smallest` globally.

You can check this yourself:

```bash
python -c "
import apache_beam as beam
print([c for c in dir(beam.combiners) if not c.startswith('_')])
"
```

The `Top` API deserves particular care, because its exact signature
matters:

```text
beam.combiners.Top.Of(n, key=None, reverse=False)   # global
beam.combiners.Top.PerKey(n, key=None, reverse=False)  # per key
beam.combiners.Top.LargestPerKey(n, key=None)        # per key, largest
beam.combiners.Top.SmallestPerKey(n)                # per key, smallest
beam.combiners.Largest(n, key=None, reverse=False)   # global
beam.combiners.Smallest(n)                          # global
```

Two things to get right:

**1. The `key` function receives the *value*, not the KV pair.** This is
the mistake almost everyone makes first:

```python
# WRONG: the key function gets the value, not the (key, value) pair
beam.combiners.Top.LargestPerKey(1, key=lambda kv: kv[1])

# RIGHT
beam.combiners.Top.LargestPerKey(1, key=lambda v: v)
```

**2. The per-key form outputs `(key, [values])` — a list, not a scalar.**

```python
import apache_beam as beam

with beam.Pipeline() as p:
    kv = p | "Create" >> beam.Create([("a", 1), ("b", 5), ("c", 3)])

    (
        kv
        | "Top" >> beam.combiners.Top.LargestPerKey(1, key=lambda v: v)
        | "Print" >> beam.Map(print)
    )
```

Output:

```text
('a', [1])
('b', [5])
('c', [3])
```

And the global form outputs a single element containing a list:

```python
with beam.Pipeline() as p:
    values = p | "Create" >> beam.Create([1, 5, 3, 9])

    (
        values
        | "Top" >> beam.combiners.Top.Largest(2, key=lambda v: v)
        | "Print" >> beam.Map(print)
    )
```

Output:

```text
[[9, 5]]
```

Note the double brackets: one element, which is a list.

### The `CombineFn` four-method interface

When a callable is not enough, you write a `CombineFn`. It has exactly four
methods, and the contract for each is precise:

```python
class RevenueByRegionFn(beam.CombineFn):
    """Aggregate order count and revenue per region."""

    def create_accumulator(self) -> dict[str, float]:
        """Create an empty accumulator."""
        return {"order_count": 0.0, "revenue_eur": 0.0}

    def add_input(self, accumulator, order) -> dict[str, float]:
        """Add one order to the accumulator."""
        accumulator["order_count"] += 1
        accumulator["revenue_eur"] += normalise_currency(
            float(order["amount"]), order["currency"]
        )
        return accumulator

    def merge_accumulators(self, accumulators) -> dict[str, float]:
        """Merge partial accumulators from different workers."""
        total = self.create_accumulator()
        for partial in accumulators:
            total["order_count"] += partial["order_count"]
            total["revenue_eur"] += partial["revenue_eur"]
        return total

    def extract_output(self, accumulator) -> dict[str, float]:
        """Produce the final output from the accumulator."""
        return {
            "order_count": int(accumulator["order_count"]),
            "revenue_eur": round(accumulator["revenue_eur"], 2),
        }
```

| Method | Called | Contract |
|---|---|---|
| `create_accumulator()` | once per accumulator | return the identity element |
| `add_input(acc, element)` | per element | return the updated accumulator |
| `merge_accumulators(accs)` | per merge | combine several accumulators into one |
| `extract_output(acc)` | at the end | convert the accumulator to the output |

Three rules that people get wrong:

**1. `create_accumulator` must return the identity element.** For a sum,
that is `0`. For a max, it is `-inf`. For a list, `[]`. If your accumulator
starts at a non-identity value, your answer is wrong by that amount.

**2. `add_input` and `merge_accumulators` must be consistent.** Merging two
accumulators must give the same result as adding the inputs to one
accumulator directly. This is the property the test
`test_merge_is_order_independent` in `project/tests/test_pipelines.py`
checks:

```python
def test_merge_is_order_independent(self):
    """The combiner gives the same answer however the inputs are merged."""
    orders = [
        {"amount": 10.0, "currency": "EUR"},
        {"amount": 20.0, "currency": "EUR"},
        {"amount": 30.0, "currency": "EUR"},
    ]
    combiner = RevenueByRegionFn()

    left = combiner.create_accumulator()
    for order in orders[:2]:
        left = combiner.add_input(left, order)

    right = combiner.create_accumulator()
    for order in reversed(orders[2:]):
        right = combiner.add_input(right, order)

    merged = combiner.merge_accumulators([left, right])
    assert combiner.extract_output(merged) == {
        "order_count": 3,
        "revenue_eur": 60.0,
    }
```

Note that the two halves are accumulated in *opposite* orders — the first
half forwards, the second half backwards — and the merged result is still
exactly right. That is associativity and commutativity, tested.

**3. `extract_output` must not mutate the accumulator.** It is a
projection. The accumulator may be reused. Mutating it in
`extract_output` produces wrong results on some runners and right results
on others.

**A note on mutating vs returning.** The `RevenueByRegionFn` above mutates
the accumulator in place *and* returns it. That is allowed. But the
returned value is what Beam uses, so always return it — even if you mutated
in place. A `DoFn`-style implementation that mutates without returning
silently loses data.

### Associativity and commutativity: why they matter

This is the theoretical heart of the chapter, and it is worth understanding
rather than memorising.

**Commutative** means `merge(A, B) == merge(B, A)`.

**Associative** means `merge(merge(A, B), C) == merge(A, merge(B, C))`.

Why does Beam care? Because the runner is free to:

- process elements in **any order** within a bundle;
- process bundles in **any order** across workers;
- merge accumulators in **any grouping** — a worker might merge 3 partials
  at a time, another might merge 17 at a time, and the tree shapes will
  differ;
- retry a bundle, producing a different merge tree on the second attempt.

If your combiner is associative and commutative, all of those produce the
same answer. If it is not, your answer depends on the execution plan — which
means:

| Property | Consequence if violated |
|---|---|
| Not associative | The result depends on the merge tree. Different runners, different worker counts, different bundle sizes give different numbers. |
| Not commutative | The result depends on the order elements are processed. |
| Neither | The result is non-deterministic and irreproducible. |

Concretely, for floating-point revenue sums, this is not academic. Adding
`0.1 + 0.2 + 0.3` in different orders gives different results at the 17th
significant digit. If you sum raw floats across a distributed merge, the
answer depends on the execution plan.

This is why `RevenueByRegionFn` rounds in `extract_output` rather than
accumulating rounded values. `add_input` accumulates the *unrounded* total,
and the rounding happens once, at the end:

```python
def extract_output(self, accumulator):
    return {
        "order_count": int(accumulator["order_count"]),
        "revenue_eur": round(accumulator["revenue_eur"], 2),
    }
```

Rounding per-element would be non-associative: `round(round(a+b) + c)` is
not `round(a + b + c)`. This is a genuinely important detail, and it is the
kind of thing that makes a combiner "correct" rather than "approximately
correct".

### A concrete worked example of the merge

Let us trace `RevenueByRegionFn` over four orders across three workers.

**The input** (keyed by region):

```text
EMEA  EUR 100.00
EMEA  USD 200.00     (USD → EUR = 0.92, so 184.00)
AMER  EUR  50.00
EMEA  GBP 100.00     (GBP → EUR = 1.17, so 117.00)
```

**Worker A** receives the first two EMEA orders. Its accumulator:

```text
create_accumulator()  →  {"order_count": 0.0, "revenue_eur": 0.0}
add_input(acc, EMEA/EUR/100.00)
    → {"order_count": 1.0, "revenue_eur": 100.00}
add_input(acc, EMEA/USD/200.00)
    → {"order_count": 2.0, "revenue_eur": 284.00}
```

**Worker B** receives the AMER order:

```python
{"order_count": 1.0, "revenue_eur": 50.00}
```

**Worker C** receives the EMEA/GBP order:

```python
{"order_count": 1.0, "revenue_eur": 117.00}
```

**The shuffle.** The three accumulators are keyed by region and routed to
the worker handling EMEA and AMER.

**The merge for EMEA** — two partial accumulators:

```text
merge_accumulators([
    {"order_count": 2.0, "revenue_eur": 284.00},   # from A
    {"order_count": 1.0, "revenue_eur": 117.00},   # from C
])
→ total = create_accumulator()                      # {"order_count": 0.0, "revenue_eur": 0.0}
→ total["order_count"] += 2.0                      # 2.0
→ total["revenue_eur"] += 284.00                   # 284.00
→ total["order_count"] += 1.0                      # 3.0
→ total["revenue_eur"] += 117.00                   # 401.00
→ {"order_count": 3.0, "revenue_eur": 401.00}
```

**The extract:**

```text
extract_output({"order_count": 3.0, "revenue_eur": 401.00})
→ {"order_count": 3, "revenue_eur": 401.0}
```

**The output:**

```text
EMEA  3  401.0
AMER  1  50.0
```

Now: what if the merge order were reversed, or the worker boundaries
different? The result is identical, because addition is associative and
commutative, and the rounding happens once at the end. That is the
property that makes the answer reproducible whether you run on the Direct
Runner, on Dataflow with 10 workers, or on Dataflow with 500.

**Compare with the non-associative version.** If `add_input` had rounded
each time:

```text
Worker A:  0.00 + 100.00 = 100.00
            100.00 + 184.00 = 284.00
Worker C:  0.00 + 117.00 = 117.00
Merge:     284.00 + 117.00 = 401.00
```

That happens to agree. But consider amounts of 0.005 and 0.015:

```text
Rounded per element:  round(0.005) = 0.01 (banker's rounding: 0.01)
                       round(0.015) = 0.01
                       total = 0.02
Unrounded, then rounded: round(0.005 + 0.015) = round(0.02) = 0.02
```

The divergence shows up when a single element crosses a rounding boundary
and the partial sums land differently. The rule stands: **round once, at
the end.**

### `CombineFn` instance versus a callable

`CombinePerKey` accepts either:

```python
# A callable: applied to the whole iterable of values for a key
beam.CombinePerKey(sum)

# A CombineFn instance: the four-method protocol
beam.CombinePerKey(RevenueByRegionFn())
```

There is a third form worth knowing: a `CombineFn` can be lifted to a
per-key combiner with `LiftedCombinePerKey`:

```python
beam.CombinePerKey(beam.combiners.LiftedCombinePerKey(RevenueByRegionFn()))
```

...but `CombinePerKey` already does that lifting for you when you pass a
`CombineFn` instance. The explicit lift exists for the cases where you want
to combine the *lifted* form with other operations.

When to use which:

| Form | Use when | Cost |
|---|---|---|
| Callable (`sum`) | the reduction is a one-liner | the runner must materialise the values to call it — no incremental combining |
| `CombineFn` | you need a custom summary, or incremental combining | the runner can combine incrementally, before the shuffle |

This is a real performance difference. `beam.CombinePerKey(sum)` cannot
pre-combine, because `sum` needs the whole iterable. `CombinePerKey(
RevenueByRegionFn())` can: each worker reduces its values to a dict, and
only the dicts are shuffled. For a hot key with 50 million values, that is
the difference between shuffling 50 million values and shuffling 200
dicts.

### `beam.CombineGlobally`

`CombineGlobally` applies a combiner to the entire PCollection, with no
key:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    values = p | "Create" >> beam.Create([1, 2, 3])

    (
        values
        | "Sum" >> beam.CombineGlobally(sum)
        | "Print" >> beam.Map(print)
    )
```

Output:

```text
[6]
```

Note the shape: the output is a **single element** containing the reduced
value, not a bare scalar. This trips people up regularly. If you want a
scalar, map it:

```text
| "Sum" >> beam.CombineGlobally(sum)
| "Unwrap" >> beam.Map(lambda vs: list(vs)[0])
```

`CombineGlobally` is a shuffle. It is the right tool for "one number for
the whole dataset" — total revenue, distinct users, overall error rate.
It is the wrong tool for "one number per region", which is
`CombinePerKey`.

### `beam.Distinct` and per-key distinct

`beam.Distinct` removes duplicates from a PCollection:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    values = p | "Create" >> beam.Create([1, 1, 2, 2, 3])

    (
        values
        | "Distinct" >> beam.Distinct()
        | "Print" >> beam.Map(print)
    )
```

Output:

```text
1
2
3
```

`Distinct` is a shuffle under the hood — it needs to see all the values to
know which are unique.

Per-key distinct — "the distinct products per region" — has two forms.
The explicit one uses `CombinePerKey` with a set-returning combiner:

```python
class DistinctPerKeyFn(beam.CombineFn):
    """Collect the distinct values seen under each key."""

    def create_accumulator(self):
        return set()

    def add_input(self, accumulator, element):
        accumulator.add(element)
        return accumulator

    def merge_accumulators(self, accumulators):
        merged = set()
        for acc in accumulators:
            merged |= acc
        return merged

    def extract_output(self, accumulator):
        return sorted(accumulator)
```

Used like this:

```python
(
    kv
    | "DistinctPerKey" >> beam.CombinePerKey(DistinctPerKeyFn())
    | "Print" >> beam.Map(print)
)
```

The built-in `combiners.ToSet()` is *not* a per-key combiner — it is a
**global** transform that collects every element of a flat PCollection into
one set. For the global case, use it directly:

```python
(
    flat
    | "Distinct" >> beam.combiners.ToSet()
    | "Print" >> beam.Map(print)
)
```

Note that `merge_accumulators` uses `|=` — set union — which is
associative and commutative. Good.

There is also `beam.GroupBy`, which is a higher-level alternative to
`GroupByKey` that builds named rows:

```python
(
    kv
    | "GroupBy" >> beam.GroupBy(lambda row: row[0]).aggregate_field(
        "v", sum, "total"
    )
)
```

`GroupBy` requires the input to have *named fields* — a namedtuple or a
`Row` — not a bare tuple, which is why it is less convenient for the
KV-pair style used throughout this course. `GroupBy` is worth knowing about
but `CombinePerKey` is the right default for KV work.

### The project's `RevenueByRegionFn`

The combiner in `project/transforms.py` is the reference example for this
chapter, and it is worth reading in full:

```python
class RevenueByRegionFn(beam.CombineFn):
    """Aggregate order count and revenue per region.

    A `CombineFn` must be *associative* and *commutative*, because Beam
    merges partial accumulators from different workers in an arbitrary
    order. `add_input` accumulates one order, `merge_accumulators` merges
    two partial sums, and the merge must produce the same result as
    adding the inputs in any other order.
    """

    def create_accumulator(self) -> dict[str, float]:
        return {"order_count": 0.0, "revenue_eur": 0.0}

    def add_input(self, accumulator, order):
        accumulator["order_count"] += 1
        accumulator["revenue_eur"] += normalise_currency(
            float(order["amount"]), order["currency"]
        )
        return accumulator

    def merge_accumulators(self, accumulators):
        total = self.create_accumulator()
        for partial in accumulators:
            total["order_count"] += partial["order_count"]
            total["revenue_eur"] += partial["revenue_eur"]
        return total

    def extract_output(self, accumulator):
        return {
            "order_count": int(accumulator["order_count"]),
            "revenue_eur": round(accumulator["revenue_eur"], 2),
        }
```

Note three design decisions:

1. **The accumulator is a plain `dict` of floats.** Small, picklable, and
   cheap to merge. It is not a dataclass, not a namedtuple — because this
   accumulator is shuffled and merged many times, and dict access is fast.
2. **`merge_accumulators` builds a fresh accumulator** rather than mutating
   the first one in the list. Safer, and it means the method does not care
   whether the list is empty.
3. **Rounding happens in `extract_output`, once.** As discussed above.

### The full picture

```text
   KV pairs
      │
      ▼
  ┌──────────────────────────────────────────┐
  │ pre-shuffle combine (per worker)         │
  │   add_input × N  →  one accumulator      │
  └──────────────────────────────────────────┘
      │  (shuffle: accumulators, not elements)
      ▼
  ┌──────────────────────────────────────────┐
  │ merge_accumulators × N                   │
  │   → one accumulator per key              │
  └──────────────────────────────────────────┘
      │
      ▼
  extract_output  →  the final value
```

---

## 🛠️ Hands-On: Cross-Validating a Combiner Against Pure Python

The most valuable thing you can do with a combiner is prove it agrees with
a reference implementation. This is the discipline that catches
non-associative bugs before they reach production.

### Step 1 — the pure reference

`build_revenue_summary` in `project/transforms.py` is the pure twin of
`RevenueByRegionFn`. The two must agree exactly.

```python
from project.transforms import build_revenue_summary, try_parse_order_line

rows = [r for r in (try_parse_order_line(l) for l in LINES) if r]
pure = build_revenue_summary(rows, statuses=("complete",))
```

### Step 2 — the Beam result

```python
import apache_beam as beam
from apache_beam.io.textio import ReadFromText

with beam.Pipeline() as p:
    lines = p | "Read" >> ReadFromText("./sample_data/orders.csv")
    orders = lines | "Parse" >> beam.ParDo(ParseOrderFn())
    completed = orders | "KeepComplete" >> beam.Filter(
        lambda o: o["status"] == "complete"
    )
    keyed = completed | "Key" >> beam.Map(lambda o: (o["region"], o))
    summary = keyed | "Revenue" >> beam.CombinePerKey(RevenueByRegionFn())
```

### Step 3 — the cross-validation harness

Create `hands_on_combine.py`:

```python
"""Cross-validate a CombinePerKey result against the pure build_revenue_summary."""
import apache_beam as beam
from apache_beam.io.textio import ReadFromText, WriteToText

from project.transforms import (
    ParseOrderFn,
    RevenueByRegionFn,
    build_revenue_summary,
    try_parse_order_line,
)

INPUT = "./sample_data/orders.csv"
OUTPUT = "./out/hands_on/summary"


def beam_summary(pipeline, input_path, output_path):
    """Run the combiner and write the result as CSV."""
    lines = pipeline | "ReadOrders" >> ReadFromText(input_path)
    orders = lines | "ParseOrders" >> beam.ParDo(ParseOrderFn())
    completed = orders | "KeepCompleted" >> beam.Filter(
        lambda o: o["status"] == "complete"
    )
    keyed = completed | "KeyByRegion" >> beam.Map(lambda o: (o["region"], o))
    summary = keyed | "RevenueByRegion" >> beam.CombinePerKey(RevenueByRegionFn())

    (
        summary
        | "Format" >> beam.Map(
            lambda kv: f"{kv[0]},{kv[1]['order_count']},{kv[1]['revenue_eur']}"
        )
        | "Write" >> WriteToText(output_path, num_shards=1, shard_name_template="")
    )
    return summary


def pure_summary(input_path):
    """Run the pure reference implementation over the same file."""
    with open(input_path, encoding="utf-8") as handle:
        lines = handle.read().splitlines()

    rows = []
    for line in lines:
        row = try_parse_order_line(line)
        if row is not None:
            rows.append(row)

    return build_revenue_summary(rows, statuses=("complete",))


def main():
    with beam.Pipeline() as pipeline:
        beam_summary(pipeline, INPUT, OUTPUT)

    expected = pure_summary(INPUT)
    print("pure reference:")
    for region in sorted(expected):
        bucket = expected[region]
        # `build_revenue_summary` accumulates the count as a float; the
        # combiner's `extract_output` casts it to an int. Compare them
        # numerically, not as strings.
        print(f"  {region},{int(bucket['order_count'])},{bucket['revenue_eur']}")

    print()
    print("beam output:")
    # `shard_name_template=""` means the runner writes the file at the exact
    # prefix, with no `00000of00001` suffix. Read it with a glob if you
    # have not pinned the shard name template.
    with open(OUTPUT, encoding="utf-8") as handle:
        for line in handle.read().splitlines():
            print(f"  {line}")


if __name__ == "__main__":
    main()
```

Run it:

```bash
python hands_on_combine.py
```

The two lists must agree — same regions, same counts, same revenue, to the
cent. Then check them mechanically:

```bash
python hands_on_combine.py > /tmp/combine_report.txt
grep -A100 "beam output" /tmp/combine_report.txt | tail -n +2 | sort > /tmp/beam.txt
grep -A100 "pure reference" /tmp/combine_report.txt | tail -n +2 | sort > /tmp/pure.txt
diff /tmp/beam.txt /tmp/pure.txt && echo "MATCH"
```

If `diff` reports a difference, the combiner is wrong — not the reference.
The reference is nine lines of plain Python with no distributed
execution to hide behind.

### Step 4 — prove associativity and commutativity directly

The property that makes the combiner safe is testable without a runner:

```python
import itertools

from project.transforms import RevenueByRegionFn

orders = [
    {"amount": 10.0, "currency": "EUR"},
    {"amount": 20.0, "currency": "EUR"},
    {"amount": 30.0, "currency": "EUR"},
    {"amount": 40.0, "currency": "EUR"},
]

combiner = RevenueByRegionFn()

# Every possible order of the four orders must give the same answer.
results = set()
for permutation in itertools.permutations(orders):
    acc = combiner.create_accumulator()
    for order in permutation:
        acc = combiner.add_input(acc, order)
    results.add(tuple(sorted(combiner.extract_output(acc).items())))

print("distinct results across all 24 orderings:", len(results))
assert len(results) == 1
```

One distinct result across all 24 permutations. That is commutativity and
associativity, demonstrated rather than asserted.

Now do the same for the *merge* path, which is what the runner actually
uses:

```python
# Split into two halves, merge in both orders.
left = combiner.create_accumulator()
for order in orders[:2]:
    left = combiner.add_input(left, order)

right = combiner.create_accumulator()
for order in orders[2:]:
    right = combiner.add_input(right, order)

forward = combiner.merge_accumulators([left, right])
backward = combiner.merge_accumulators([right, left])

assert combiner.extract_output(forward) == combiner.extract_output(backward)
print("merge is order-independent")
```

### Step 5 — break it, and watch it break

Now make the combiner non-associative and see the cross-validation fail.
Change `add_input` to round as it goes:

```python
class BadRevenueByRegionFn(beam.CombineFn):
    """A deliberately broken combiner: rounds on every add."""

    def create_accumulator(self):
        return {"order_count": 0.0, "revenue_eur": 0.0}

    def add_input(self, accumulator, order):
        accumulator["order_count"] += 1
        accumulator["revenue_eur"] = round(
            accumulator["revenue_eur"] + float(order["amount"]), 2
        )
        return accumulator

    def merge_accumulators(self, accumulators):
        total = self.create_accumulator()
        for partial in accumulators:
            total["order_count"] += partial["order_count"]
            total["revenue_eur"] = round(total["revenue_eur"] + partial["revenue_eur"], 2)
        return total

    def extract_output(self, accumulator):
        return {
            "order_count": int(accumulator["order_count"]),
            "revenue_eur": round(accumulator["revenue_eur"], 2),
        }
```

The cross-validation against `build_revenue_summary` will now fail on at
least one region — the pure function accumulates unrounded and rounds once
at the end, and the two disagree by a cent. That single cent is the visible
symptom of a class of bug that, at scale, turns into irreproducible
financial reports.

This is the whole argument for the cross-validation harness in one
experiment.

### Step 6 — compare the combiners

```python
import apache_beam as beam

with beam.Pipeline() as p:
    kv = p | "Create" >> beam.Create(
        [("EMEA", 100.0), ("EMEA", 200.0), ("AMER", 50.0), ("AMER", 25.0)]
    )
    flat = p | "CreateFlat" >> beam.Create(
        [100.0, 200.0, 50.0, 25.0]
    )

    counted = kv | "Count" >> beam.combiners.Count.PerKey()
    summed = kv | "Sum" >> beam.CombinePerKey(sum)
    meaned = kv | "Mean" >> beam.combiners.Mean.PerKey()
    topped = kv | "Top" >> beam.combiners.Top.LargestPerKey(1, key=lambda v: v)

    # `ToList()` and `ToSet()` are global: they take a *flat* PCollection
    # and collect every element into one list, not a list per key.
    listed = flat | "ToList" >> beam.combiners.ToList()

    for name, coll in (
        ("count", counted),
        ("sum", summed),
        ("mean", meaned),
        ("top", topped),
        ("list", listed),
    ):
        (
            coll
            | f"Print{name}" >> beam.Map(lambda kv, n=name: (n, kv))
            | f"Show{name}" >> beam.Map(print)
        )
```

Output:

```text
('count', ('EMEA', 2))
('count', ('AMER', 2))
('sum', ('EMEA', 300.0))
('sum', ('AMER', 75.0))
('mean', ('EMEA', 150.0))
('mean', ('AMER', 37.5))
('top', ('EMEA', [200.0]))
('top', ('AMER', [50.0]))
('list', [100.0, 200.0, 50.0, 25.0])
```

Note the shapes: `Count.PerKey` gives a scalar, `Top.LargestPerKey` gives
a **one-element list**, not a scalar, and `ToList()` gives a single
flat list of every element. That last one catches people out regularly —
`ToList()` is global, so it needs a non-keyed input, and it does **not**
give you a list per key.

---

## 🛠️ Common Errors and Fixes

### `AttributeError: module 'apache_beam.transforms.combiners' has no attribute 'Sum'`

```text
AttributeError: module 'apache_beam.transforms.combiners' has no attribute 'Sum'
```

There is no `combiners.Sum`. Use the builtin:

```python
beam.CombinePerKey(sum)
```

### `AttributeError: type object 'Count' has no attribute 'Sum'`

A typo — `Count` is the count combiner, not a namespace for other
combiners. Each combiner is its own class in `beam.combiners`.

### `TypeError: 'LargestPerKey' object is not callable` / `TypeError: '<lambda>' object is not subscriptable`

```text
TypeError: '<lambda>' object is not subscriptable
```

Your `key` function is subscripting the value as if it were a KV pair. The
`key` function receives the **value**:

```python
# WRONG
beam.combiners.Top.LargestPerKey(1, key=lambda kv: kv[1])

# RIGHT
beam.combiners.Top.LargestPerKey(1, key=lambda v: v)
```

### The `Top` output is `('a', [5])` and you expected `('a', 5)`

The per-key `Top` combiners output a **list**. The global ones output a
single element containing a list. Unwrap explicitly:

```text
| "Top" >> beam.combiners.Top.LargestPerKey(1, key=lambda v: v)
| "Unwrap" >> beam.Map(lambda kv: (kv[0], kv[1][0]))
```

### `TypeError: 'CombineFn' object is not callable`

```text
TypeError: 'CombineFn' object is not callable
```

You passed the **class** rather than an instance. `CombineFn` needs to be
instantiated:

```python
# WRONG
beam.CombinePerKey(RevenueByRegionFn)

# RIGHT
beam.CombinePerKey(RevenueByRegionFn())
```

### `TypeError: unhashable type: 'dict'` in `CombinePerKey`

Your input to `CombinePerKey` is not KV pairs. The transform requires
`(key, value)` tuples. Add a `Map` to key it first.

### `ValueError: Type of ... is not assignable to type hint KV[...]`

The key or the value type does not match the hint. Drop the explicit
`with_output_types` and let Beam infer, or fix the keying `Map`.

### `CombineGlobally` output is `[[6]]` and you expected `6`

`CombineGlobally` produces **one element** containing the reduced value.
That is a single element whose value is a list of one value. Unwrap it:

```text
| "Sum" >> beam.CombineGlobally(sum)
| "Unwrap" >> beam.Map(lambda vs: list(vs)[0])
```

### `ValueError: Cannot combine ... with itself` or a merge that produces the wrong total

Your `merge_accumulators` is not summing all the partials. Check that it
iterates over *all* the accumulators, and that it starts from
`create_accumulator()` rather than from the first element of the list:

```python
def merge_accumulators(self, accumulators):
    total = self.create_accumulator()      # not accumulators[0]
    for partial in accumulators:
        total["revenue_eur"] += partial["revenue_eur"]
    return total
```

### The combiner's numbers differ from the pure function by a cent

You are rounding inside `add_input` or `merge_accumulators`. Move the
rounding to `extract_output`, where it happens exactly once.

### `BeamAssertException: Failed assert` on a `CombinePerKey` result

Usually a floating-point comparison, or an ordering assumption. Beam's
`equal_to` compares multisets of elements, so order within a group is not
the issue — but `round(x, 2) == round(y, 2)` on floats is. Compare
rounded values, or compare the dict fields individually.

---

## 💡 Production Notes

- **Choose `CombinePerKey` over `GroupByKey` by default, always.** The
  cost difference is not incremental, it is a different order of
  magnitude. `GroupByKey` on a hot key with 50 million values OOMs a
  worker; `CombinePerKey` on the same data moves a few hundred kilobytes
  across the network. `GroupByKey` is for when you genuinely need the
  values, not a summary of them.
- **A `CombineFn` that cannot pre-combine is a `GroupByKey` in disguise.**
  If your `add_input` just appends to a list, and your `extract_output`
  does the real work, you have written `GroupByKey` with extra steps and
  no benefit. The whole point of the accumulator is that it is *small* and
  *mergeable*.
- **Watch the accumulator size, not the input size.** A `CombiningValueStateSpec`
  that accumulates a set per key is a `GroupByKey` again. The accumulator
  should be O(1) in the number of elements, or O(k) for a fixed small k
  (`Top` with `n=10` is fine; `n=10,000,000` is not).
- **Float sums are not reproducible across runners without care.** If your
  output must match bit-for-bit across runs, accumulate in integer minor
  units (cents) rather than floats, or use `decimal.Decimal` with a fixed
  context. `RevenueByRegionFn` rounds once at the end, which is the
  pragmatic 95% solution.
- **The `count` combiner is not free of the "extract" cost, but it is
  cheap.** `beam.combiners.Count.PerKey()` is the fastest possible
  per-key aggregation and is a good default when you need cardinality.
  For distinct *values* rather than distinct *elements*, use
  `combiners.ToSet()` and remember that the accumulator is the
  set — which does not scale.
- **A combiner that is not associative produces irreproducible financial
  reports.** This is the failure mode you cannot detect in a smoke test
  with 100 rows, and cannot reproduce from the job logs, because the
  result depends on the execution plan. Cross-validate against a pure
  reference on a realistic sample, as the hands-on does.
- **The `merge_accumulators` path is rarely exercised by small tests.** On
  the Direct Runner with 100 elements there may be one worker and one
  merge. On Dataflow with 500 workers there are hundreds of merges with
  different tree shapes. **Test the merge path explicitly**, as
  `test_merge_is_order_independent` does.
- **`CombinePerKey` still shuffles.** It is cheaper than `GroupByKey`, not
  free. If the number of keys is small — a few hundred regions — the
  shuffle is not the bottleneck; the pre-shuffle combine is. If one key is
  hot, the pre-shuffle combine on the hot key's worker is the bottleneck,
  and the fix is salt-bucketing the key before the combine, or
  `Reshuffle` plus a re-key.
- **A combiner that is a Python callable cannot pre-combine.** If
  `CombinePerKey(sum)` is your hot path and the values are large, the
  runner materialises the iterable to call `sum` on it. Writing a
  `CombineFn` with an integer accumulator moves that work to the
  pre-shuffle phase.
- **Prefer `CombinePerKey` over `GroupByKey` + `Map` + `Reduce` even for
  one-off joins.** If you find yourself writing
  `GroupByKey → Map(len) → CombinePerKey(sum)`, the middle two steps
  collapse into a single `CombinePerKey` with a counting combiner, and
  the shuffle count drops from two to one.
- **The accumulator is shipped to workers with the `DoFn`.** Keep it small.
  A `CombineFn` whose accumulator holds the full list of values is a
  memory leak with extra steps.

---

## 🔑 Key Takeaways

- `GroupByKey` materialises every group and is O(largest group) in memory.
  `CombinePerKey` ships *summaries* across the shuffle and is O(number of
  keys) in network transfer. Prefer `CombinePerKey` unless you truly need
  the values.
- The accumulator idea: summarise locally → shuffle summaries → merge →
  extract. The pre-shuffle combine is where the savings come from.
- **There is no `beam.combiners.Sum`.** Use `beam.CombinePerKey(sum)`. The
  per-key combiners are `Count`, `Mean`, `Top`, `Largest`, `Smallest`,
  `Sample` and `Latest`. `ToList`, `ToSet`, `ToDict`, `Iterable`, `Any`,
  `Timestamp` and `Duration` are **global transforms applied directly**,
  not combiners with a `.PerKey()` method.
- `beam.combiners.Count.PerKey()` outputs `(key, int)`, one integer per
  key. `Count.Globally()` outputs a single element.
- A `CombineFn` has exactly four methods: `create_accumulator`,
  `add_input`, `merge_accumulators`, `extract_output`. `CombinePerKey`
  takes a callable or a `CombineFn` *instance*; only the instance can
  pre-combine before the shuffle.
- **Associativity and commutativity are what make the result
  reproducible** across runners, worker counts, bundle sizes and retries.
  A non-associative combiner gives different numbers on different runs.
- `create_accumulator` must return the identity element; `add_input` and
  `merge_accumulators` must agree; `extract_output` must not mutate.
  Round once, in `extract_output` — rounding inside `add_input` is
  non-associative and produces off-by-a-cent errors.
- `Top`'s `key` function receives the **value**, and the per-key form
  outputs `(key, [values])` — a list, not a scalar.

---

## 📚 Practice Exercises

1. **Write a `MedianPerKey` combiner.** A `CombineFn` that computes the
   median of the values under each key. *Hint:* the accumulator must be
   the full list, which means it does not scale — write it, then explain
   why a median is fundamentally harder to compute in a distributed setting
   than a mean, and what `combiners.Sample` gives you instead.

2. **Write a `MaxPerKeyFn` `CombineFn`.** Implement it with an accumulator
   that is a single float initialised to `-inf`. Then verify associativity
   by merging partials in both orders, as the hands-on does for revenue.

3. **Cross-validate `combiners.Count.PerKey()`.** Extend the hands-on
   harness so the pure reference computes the count per region and compare
   it with the `Count.PerKey()` output. *Expected:* exact match on every
   region.

4. **Compare `ToList()` and `ToSet()`.** Run both over the same flat input
   with a duplicated value. *Expected:* the list keeps the duplicate, the
   set does not. Then write a `DistinctPerKeyFn` `CombineFn` and show that
   it gives a set *per key* — which neither built-in does. Explain which
   of the three is a `GroupByKey` in disguise, and what that means for its
   memory profile.

5. **Demonstrate the float-rounding bug.** Write a `CombineFn` that
   rounds inside `add_input`, and show that the cross-validation against
   `build_revenue_summary` fails by a cent on at least one region. Then
   fix it by moving the rounding into `extract_output` and re-run.
   *Expected:* the diff disappears.

6. **Reflection.** A pipeline sums revenue per region over a hot key that
   receives 60% of all orders. Explain, in terms of the pre-shuffle
   combine and the shuffle, where the time goes, and propose two changes
   that would reduce it without changing the final numbers.

---

## 📖 Further Reading

- Apache Beam: Combining keyed values — https://beam.apache.org/documentation/programming-guide/#combining
- Apache Beam Python API: `beam.combiners` — https://beam.apache.org/documentation/sdks/python/apache_beam.combiners.html
- Apache Beam Python API: `apache_beam.CombineFn` — https://beam.apache.org/documentation/sdks/python/apache_beam.transforms.combinefn.html
- Apache Beam: Combination functions and commutativity — https://beam.apache.org/documentation/basic-topics/#combining
- Google Cloud Dataflow: Optimise aggregation with CombinePerKey — https://cloud.google.com/dataflow/docs/optimize-aggregates
- Google Cloud Dataflow: Handling skewed data — https://cloud.google.com/dataflow/docs/guides/skewed-data-processing-guide
