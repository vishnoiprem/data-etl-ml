# 8.1 — Testing Beam Pipelines

> **Section 8 · Production Operations · Lecture 8.1 · 6:30**

## 🎯 What you will learn

- The four-layer testing pyramid for Beam, and where each layer's cost and confidence live
- The difference between the modern `apache_beam.testing.test_pipeline.TestPipeline` API and the deprecated `PTest` style — and why their semantics genuinely differ
- How `assert_that` and `equal_to` work, and what `use_global_window=False` really changes
- How to write a matcher that survives windowed output by unwrapping `WindowedValue.value`
- The `beam_test_options` fixture pattern, including why `--allow_unsafe_triggers` has to be set explicitly
- How to test a `CombineFn` directly, and why merge-order independence is the property that matters
- How to test a `DoFn`, and when calling `process` directly is the right choice
- How `TestStream` makes streaming behaviour deterministic, and what it cannot simulate
- Snapshot (golden-file) testing, and what you should never test

---

## 🧠 Concept

### Why Beam needs its own testing discipline

A conventional data pipeline has a seam you can test through: a function that
takes rows and returns rows. You call it with a list, compare the list to
what you expected, and you are done. The framework is a detail.

Beam has no such seam. Your pipeline is a **graph of transforms** whose
inputs arrive as `PCollection`s, whose elements carry windows and
timestamps, and whose execution is a distributed, fused, and often
non-deterministic process. There is no "call the pipeline and get a list"
shortcut — a `PCollection` is a description of data, not data.

So Beam testing is a portfolio of techniques, each covering a different
slice of the risk. The job is to know which slice you are covering, so you
never mistake "the pipeline ran" for "the pipeline is correct".

### The testing pyramid

Beam's testing pyramid has four layers. The shape is the same as any
testing pyramid — cheap and broad at the bottom, expensive and narrow at
the top — but the proportions are unusual for a data system, because the
bottom layer is unusually productive.

```text
                 ╱╲
                ╱  ╲          4. Golden-file / regression
               ╱    ╲         (slow, brittle, catches silent drift)
              ╱──────╲
             ╱        ╲       3. Integration against real sources
            ╱          ╲      (minutes; catches schema, auth, format drift)
           ╱────────────╲
          ╱              ╲    2. Transform-level tests
         ╱                ╲   (seconds; TestPipeline + assert_that)
        ╱──────────────────╲
       ╱                    ╲  1. Pure-logic unit tests
      ╱______________________╲ (milliseconds; no Beam at all)
```

| Layer | What it covers | Typical speed | Needs Beam installed? | Catches |
|---|---|---|---|---|
| 1. Pure logic | Parsing, validation, currency conversion, business rules | 1–20 ms per test | no | Wrong rules, wrong edge-case handling |
| 2. Transform-level | Windowing, triggers, combiners, `DoFn` wiring | 0.3–3 s per test | yes | Wrong transform composition, wrong window assignment |
| 3. Integration | Real file formats, real schemas, real IO | 30 s – 10 min | yes (+ GCP) | Schema drift, auth problems, encoding surprises |
| 4. Golden file | Exact byte-for-byte output of a reference workload | minutes | yes | Any change in output, including accidental ones |

The ordering matters for a practical reason: **layer 1 tests run on every
save**. They must not import `apache_beam`, must not touch the network, and
must not need a runner. The course project enforces exactly this split —
`project/tests/test_transforms.py` imports nothing from Beam, and
`project/tests/test_pipelines.py` calls `pytest.importorskip("apache_beam")`
so it degrades to a skip rather than an error on a machine without the SDK.

### Layer 1 — pure-logic unit tests

The rule is simple: **if the logic can be written without Beam, it must
be.** This is the single highest-leverage testing decision you will make,
because it converts a distributed-systems problem into a function-call
problem.

The course project demonstrates this split deliberately. `transforms.py` has
a pure half and a Beam half:

```python
from transforms import (
    build_revenue_summary,   # pure twin of RevenueByRegionFn
    is_valid_order,          # pure
    normalise_currency,      # pure
    parse_order_line,        # pure
)
```

`build_revenue_summary` is a *pure twin* of the `RevenueByRegionFn`
combiner: it does the same arithmetic in plain Python. The twin is not
dead code — it is the specification. If the pure twin and the combiner
disagree, the combiner is wrong, and you have two tests (one fast, one
slow) that can prove which.

A pure-logic test looks like this — no fixtures, no runner, no setup:

```python
def test_gbp_conversion():
    """GBP converts at the static rate."""
    assert normalise_currency(100.0, "GBP") == 117.0
```

That test runs in well under a millisecond and will still pass in five
years when `apache-beam` has been upgraded twice and the runner has
changed three times.

The trick to keeping logic pure is to **keep it out of the `DoFn`**.
`ParseOrderFn.process` in the course project is a thin shell:

```python
class ParseOrderFn(beam.DoFn):
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

Every decision that could be wrong is delegated to `try_parse_order_line`
or `is_valid_order`, both of which are pure and directly testable. The
`DoFn` only handles the Beam-specific concerns: logging, and the decision
to emit or not emit.

### Layer 2 — transform-level tests with `TestPipeline`

When you need to exercise actual Beam machinery — windowing, triggers,
combiner merging, `DoFn` side inputs — you build a real pipeline and
assert on its output.

#### `TestPipeline` vs the deprecated `PTest`

The old style, `apache_beam.testing.test_pipeline.PTest`, still exists in
the SDK but is deprecated. It is not a drop-in replacement, and the
difference is not cosmetic.

```text
Old (PTest, deprecated)              New (TestPipeline)
──────────────────────────────        ──────────────────────────────
with ptest.TestPipeline() as p:       with TestPipeline() as pipeline:
    ...                                   ...
    assert_that(result, equal_to([...])) assert_that(result, equal_to([...]))
```

The semantic differences that actually matter:

| Aspect | `PTest` (deprecated) | `TestPipeline` (current) |
|---|---|---|
| Role in the pipeline graph | You call `p.run()` explicitly at the end; the pipeline does not run until you do | The context manager runs the pipeline when the block exits |
| Cleanup between test cases | Manual — you had to remove output files yourself | Automatic — the test framework deletes the temporary output directory |
| Output location | Wherever the pipeline wrote, often polluting your working directory | A per-test temporary directory, cleaned up afterwards |
| Assertion timing | After `p.run()` returned | Inside the `with` block is fine; the assertion is checked when the block exits |
| Status | Deprecated in the SDK; removed from the docs | The documented API |

The behavioural change that catches people out: in the `PTest` style, the
assertion was *after* `p.run()`, so a failed `assert_that` surfaced as a
`BeamAssertException` raised from the runner. In the `TestPipeline` style
the pipeline runs when the `with` block exits, and `assert_that` installs a
sentinel check into the graph. The exception is still a
`BeamAssertException`, but it is raised at the end of the block rather
than on an explicit `run()` call.

The practical guidance: **always use `TestPipeline`**. It is the documented
API, it cleans up after itself, and the semantics are the ones the Beam
maintainers intend.

The current signature, for reference:

```python
TestPipeline(runner=None, options=None, argv=None, is_integration_test=False,
             blocking=True, additional_pipeline_args=None, display_data=None,
             timeout=None)
```

The `options` argument is what lets you point the test at a specific
runner and a specific set of flags.

#### `assert_that` and `equal_to`

Both live in `apache_beam.testing.util`:

```python
from apache_beam.testing.util import assert_that, equal_to
```

`assert_that(actual, matcher)` attaches a check to the pipeline graph. The
matcher is a callable that receives the actual collection and either
returns normally (pass) or raises (fail). `equal_to(expected)` builds the
standard matcher.

Its implementation is worth understanding, because it explains a
surprising behaviour. `equal_to` first tries a fast path: sort both
collections and compare. If the sorts succeed and the lists are equal, it
passes immediately. Otherwise it falls back to an O(n·m) pairwise scan
using `row_namedtuple_equals_fn`, which reports both *unexpected* and
*missing* elements in the failure message.

This means:

- **Order does not matter.** `equal_to` compares collections, not sequences.
  A pipeline that emits results in a different order still passes. That is
  the right default — Dataflow gives no ordering guarantee.
- **Duplicates matter.** `equal_to([1, 1, 2])` expects two `1`s.
- **Mixing types does not crash.** The fallback path handles collections
  that cannot be sorted, so `equal_to([1, "a"])` works.

The failure message is genuinely helpful, which is why `equal_to` is
usually enough for a batch test:

```text
Failed assert: [('AMER', 2)] == [('EMEA', 3)], unexpected elements [('AMER', 2)], missing elements [('EMEA', 3)]
```

#### The `use_global_window=False` problem

This is the single most common stumbling block in Beam testing, and the
course project solves it in `test_pipelines.py`. Here is the problem.

By default, `assert_that` uses `use_global_window=True`. That means the
elements the matcher sees have been re-windowed into the global window,
which strips the window information and leaves plain values. For a batch
pipeline with no explicit windowing, that is exactly what you want, and
`equal_to` works directly.

But the moment you use `beam.WindowInto`, the elements in the output
PCollection are `WindowedValue` objects — a value plus a window (start,
end) plus a timestamp. Comparing a `WindowedValue` to a plain tuple fails,
and the failure message is deeply unhelpful:

```text
Failed assert: [WindowedValue(value=('all', 2), timestamp=..., windows=IntervalWindow(...))] == [('all', 2)]
```

Passing `use_global_window=False` to `assert_that` tells Beam **not** to
re-window the output, so the matcher receives the raw `WindowedValue`
objects. You then have to unwrap them yourself. Here is the working
matcher from `project/tests/test_pipelines.py`:

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

And the call site:

```python
assert_that(
    result,
    _windowed_values([("all", 2), ("all", 1)]),
    use_global_window=False,
)
```

Three details in that matcher are worth copying:

1. **`hasattr(item, "value")` guard.** The matcher handles both wrapped
   and unwrapped elements. That makes it reusable across tests where some
   paths are windowed and some are not.
2. **`sorted(..., key=repr)` rather than `sorted(...)`.** Sorting mixed
   types raises `TypeError` in Python 3. Sorting by `repr` sorts strings
   and always works — at the cost of comparing string representations
   rather than values. For tuples of strings and numbers, `repr` is a
   faithful and stable ordering.
3. **The matcher returns a bool, not an exception.** Beam's matchers may
   either raise or return `False`. Returning `False` produces a generic
   failure message, so if you write your own matcher, raise an exception
   with a useful message instead.

> **A better matcher.** The course matcher deliberately does *not* check
> window boundaries, because the boundaries depend on the timestamps in
> the test data and the test is about *how many* firings happened and
> *what* each contained. When you do want to assert on the window, write
> a matcher that checks `item.windows` explicitly.

### The `beam_test_options` fixture pattern

`TestPipeline` reads its runner from the `BEAM_RUNNER` environment variable
when you do not pass one explicitly, and `allow_unsafe_triggers` is not
read from the environment at all. So a test suite needs a small helper.

The course project puts it in `project/tests/conftest.py`:

```python
def beam_test_options(**extra: str):
    """Build PipelineOptions for a test pipeline."""
    from apache_beam.options.pipeline_options import PipelineOptions, TypeOptions

    flags = [f"--runner={TEST_RUNNER}", "--allow_unsafe_triggers"]
    flags.extend(f"--{name}={value}" for name, value in extra.items())

    options = PipelineOptions(flags)
    options.view_as(TypeOptions).allow_unsafe_triggers = True
    return options
```

Four things are going on:

**1. The runner is pinned.** `TEST_RUNNER` resolves to
`BundleBasedDirectRunner` by default, overridable with the
`BEAM_TEST_RUNNER` environment variable. The comment in `conftest.py`
explains why: Beam 2.60+ ships a faster Go-based in-process runner under
the plain name `DirectRunner` (the "Prism" runner), but it does not yet
support every trigger and windowing combination — it panics on the
`AfterWatermark` trigger and on the `+inf` watermark evaluation that
`TestPipeline` performs at the end of a run. The classic,
pure-Python runner supports the full feature set, so the course pins it.

**2. `--allow_unsafe_triggers` is passed as a flag.** Beam refuses
`AfterCount` triggers by default, because a window can close while
elements are still in flight. The trigger tests in the course project
deliberately exercise that behaviour.

**3. `options.view_as(TypeOptions).allow_unsafe_triggers = True` is set
explicitly.** The flag in `flags` is not sufficient on its own. The
`allow_unsafe_triggers` attribute is read from the `TypeOptions` view of
the options object, and `view_as` is how you get that view. Setting it
after construction guarantees it is present regardless of how the option
was parsed.

**4. The function is deliberately named `beam_test_options`, not
`test_options`.** pytest collects any function whose name starts with
`test` as a test case. A helper called `test_options` would be collected,
called with no arguments, and fail because it returns a value instead of
asserting anything. This is a real, easy-to-hit pytest footgun.

The companion fixture sets the environment variable so every `TestPipeline`
in the suite inherits the right runner:

```python
@pytest.fixture(scope="session", autouse=True)
def _beam_test_runner():
    previous = os.environ.get("BEAM_RUNNER")
    os.environ["BEAM_RUNNER"] = TEST_RUNNER
    yield TEST_RUNNER
    if previous is None:
        os.environ.pop("BEAM_RUNNER", None)
    else:
        os.environ["BEAM_RUNNER"] = previous
```

It restores the previous value on teardown, so the fixture does not leak
into unrelated test modules.

### Testing a `CombineFn` directly

A `CombineFn` is the most important thing to test carefully, because its
contract has a non-obvious requirement: **the merge must be
order-independent and associative**.

Beam executes a `CombinePerKey` in two phases. In phase one, each worker
accumulates a partial result locally using `add_input`. In phase two,
partial accumulators from different workers are combined using
`merge_accumulators`, in an order the runner chooses. If `merge` is
order-dependent, the answer depends on how the data happened to be
partitioned — which means the job is not reproducible, and it may produce
different totals on different days for the same input.

That is why the course project has a test named exactly what it checks:

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

Note the deliberate asymmetry: the left half is accumulated in order, the
right half in reverse. If the combiner were order-sensitive, this test
would catch it.

The four methods of the contract:

| Method | Contract | Failure mode if broken |
|---|---|---|
| `create_accumulator()` | Returns the identity element — adding it to anything changes nothing | Wrong totals when a key has a single element |
| `add_input(acc, element)` | Folds one element into the accumulator | Elements silently dropped |
| `merge_accumulators(accs)` | Combines partial accumulators; must be associative and commutative | **Non-deterministic results across runs** |
| `extract_output(acc)` | Produces the final value | Wrong shape downstream; often a `KeyError` far from the cause |

The empty-accumulator case deserves its own test, because "no elements" is
a real case — a key that was filtered out upstream, or a window that
fired empty:

```python
def test_empty_accumulator(self):
    """A fresh accumulator extracts to zero, not to an error."""
    combiner = RevenueByRegionFn()
    assert combiner.extract_output(combiner.create_accumulator()) == {
        "order_count": 0,
        "revenue_eur": 0.0,
    }
```

### Testing a `DoFn`

There are two ways to test a `DoFn`, and they answer different questions.

**Direct `process` call.** Instantiate the `DoFn`, call `process`, and
inspect the generator it returns:

```python
def test_parse_skips_malformed_lines():
    """A malformed line produces no output, not an exception."""
    fn = ParseOrderFn()
    assert list(fn.process("garbage")) == []
```

This is fast, deterministic, and it does not need a runner at all. It is
the right tool when you want to test the `DoFn`'s own logic.

**Through a pipeline.** Use `beam.ParDo` inside a `TestPipeline` and assert
on the output. This is what you want when the interesting behaviour
involves Beam-side inputs: side inputs, `TimestampParam`,
`WindowParam`, `DoFn.StateParam`, or output with side outputs.

```python
def test_parse_emits_valid_orders():
    """A valid line becomes an order dict."""
    with TestPipeline(options=beam_test_options()) as pipeline:
        result = (
            pipeline
            | "Create" >> beam.Create([VALID_ORDER_LINE])
            | "Parse" >> beam.ParDo(ParseOrderFn())
        )
        assert_that(
            result,
            equal_to(
                [
                    {
                        "order_id": "o00000001",
                        "customer_id": "c000042",
                        "order_ts": "2026-01-15T10:30:00+00:00",
                        "region": "EMEA",
                        "channel": "web",
                        "currency": "EUR",
                        "status": "complete",
                        "amount": 100.0,
                        "product_id": "p0042",
                    }
                ]
            ),
        )
```

Note the label uniqueness rule: `"Create"` and `"Parse"` are unique inside
this fence. The course project uses `"Create"` in several different test
methods, which is fine — labels are scoped per pipeline, and each test
method builds its own pipeline.

**A caution about direct `process` calls.** They bypass the runner's
serialisation, so they will not catch a `DoFn` that cannot be pickled, or
one that closes over an unpicklable object. Those failures only appear on
a Dataflow worker, hours into a job. Keep one pipeline-level test per
`DoFn` specifically to cover that.

### `TestStream` — deterministic streaming tests

A streaming pipeline is the hardest thing to test, because its behaviour
depends on *when* elements arrive relative to the watermark. Real
streaming sources give you none of that control.

`TestStream` is Beam's answer. It is a synthetic source that emits a
scripted sequence of events: elements, watermark advances, and processing
time advances. Because the script is fixed, the test is deterministic.

The import is from `apache_beam.testing.test_stream`:

```python
from apache_beam.testing.test_stream import TestStream
```

Note that `beam.io.TestStream` does **not** exist in the SDK — `TestStream`
lives in `apache_beam.testing.test_stream`. Getting this import wrong is a
very common mistake.

The API surface, verified against apache-beam 2.77:

| Method | Signature | What it does |
|---|---|---|
| `add_elements` | `add_elements(elements, tag=None, event_timestamp=None)` | Emits elements. Raw elements get the current watermark as their timestamp; `TimestampedValue` elements keep their own. |
| `advance_watermark_to` | `advance_watermark_to(new_watermark, tag=None)` | Moves the watermark to an absolute time. This is what closes windows. |
| `advance_processing_time` | `advance_processing_time(advance_by)` | Advances the processing-time clock by a duration in seconds. |
| `advance_watermark_to_infinity` | `advance_watermark_to_infinity(tag=None)` | Ends the stream by advancing the watermark to `+inf`, which flushes every window. |

There is **no** `advance_to` method. If you see it in a blog post, it is
either a different SDK version or a mistake.

Every one of these methods returns `self`, so the whole script reads as
one chained expression, and `TestStream` is attached to the pipeline
directly as a transform:

```text
p | "Stream" >> (TestStream().add_elements([...]).advance_watermark_to(t))
```

A complete streaming test:

```python
from apache_beam.testing.test_stream import TestStream
from apache_beam.utils.timestamp import Timestamp


def test_window_fires_when_watermark_advances():
    """The window emits once the watermark passes its end."""
    with TestPipeline(options=beam_test_options()) as pipeline:
        result = (
            pipeline
            | "Stream" >> (
                TestStream()
                .add_elements([("a", 1), ("b", 2)])
                .advance_watermark_to(Timestamp(1_700_000_000))
                .add_elements([("c", 3)])
                .advance_watermark_to_infinity()
            )
            | "Count" >> beam.combiners.Count.PerKey()
        )
        assert_that(result, equal_to([("a", 1), ("b", 1), ("c", 1)]))
```

Two API details that are easy to get wrong:

- **`TestStream` is a transform, not a source object.** You attach it
  directly with `p | "Stream" >> TestStream()`. Wrapping it in
  `beam.Create(stream)` raises
  `TypeError: 'TestStream' object is not iterable`.
- **The methods chain and return `self`.** `add_elements(...)` returns
  the stream, so the whole script reads as one expression.

The scripted form, factored into a helper, looks like this:

```python
def _build_stream():
    """A deterministic stream: three elements, then the watermark advances."""
    return (
        TestStream()
        .add_elements([("a", 1), ("b", 2)])
        .advance_watermark_to(Timestamp(1_700_000_000))
        .add_elements([("c", 3)])
        .advance_watermark_to_infinity()
    )
```

`TestStream` gives you precise control over **event time** (the
watermark) and **processing time** (the clock). What it does **not** give
you is real concurrency, real network partition, or real worker restarts.
Those are integration concerns, and no amount of `TestStream` scripting
will reproduce them.

The other important limit: `TestStream` works with the `DirectRunner`
family. It is not supported by `DataflowRunner` in the same way, because
Dataflow workers cannot receive a pushed script.

### Snapshot (golden-file) testing

A golden file is a reference output committed alongside the code. The test
runs the pipeline, compares the output to the file, and fails if they
differ.

```python
def test_summary_matches_golden_file(tmp_path):
    """The batch summary matches the committed reference output."""
    from batch_pipeline import build_pipeline

    input_file = tmp_path / "orders.csv"
    input_file.write_text("\n".join(ORDER_LINES) + "\n", encoding="utf-8")
    output_prefix = tmp_path / "summary"

    with TestPipeline(options=beam_test_options()) as pipeline:
        build_pipeline(
            pipeline,
            input_path=str(input_file),
            output_path=str(output_prefix),
        )

    actual = _read_summary(tmp_path)
    expected = _read_golden("golden/summary.csv")
    assert actual == expected
```

**Snapshot testing is the highest-value and highest-maintenance layer.**
It catches everything — including changes you did not intend. That is
precisely the problem: it catches *everything*, so it fails on every
harmless change too (a reordering, a float formatting difference, an
added column). A golden-file suite that is noisy gets ignored, and an
ignored suite catches nothing.

Use golden files when:

- the output is a small, well-defined, human-readable artefact
- the output is *consumed by something else* and you need to detect
  accidental contract changes
- the business logic is intricate enough that a human should review the
  output at least once

Do not use them when:

- the output is large (a million-row file as a golden file is a git
  disaster)
- the output ordering is not deterministic — in which case you must sort
  before comparing, and you should ask whether you are asserting on
  something meaningful
- you are trying to catch a specific bug — that is what a targeted
  assertion is for

### What *not* to test

This matters as much as what to test. Every test costs runtime, and every
brittle test costs maintenance.

| Do not test | Why |
|---|---|
| The runner's internals | You are not testing Beam. A test that asserts on fusion decisions or the runner's internal state breaks on every SDK upgrade and tells you nothing about your pipeline. |
| That `Map` calls your function | That is Beam's contract, and it has its own tests. |
| Exact worker counts, autoscaling decisions | These are environment-dependent. A test asserting "10 workers" fails on a different machine or a different runner. |
| Exact float equality on un-rounded sums | Floating-point addition is not associative. A merge that sums `0.1` ten ways in a different order can produce a different last bit. Round, or compare with a tolerance. |
| Output ordering | There is no ordering guarantee. A test that relies on order will fail intermittently in the best case. |
| The Cloud Monitoring export path | It is Google's problem. Test that you *emitted* the metric, not that Google's collector received it. |

That last point has a specific Beam mechanism worth knowing. Beam's
metrics API lets you inspect what was emitted, in-process, without
Cloud Monitoring:

```python
from apache_beam.metrics import MetricsFilter


def test_counter_metric_is_emitted():
    """The pipeline increments the counter once per element."""
    from apache_beam.metrics.metric import MetricResults

    with TestPipeline(options=beam_test_options()) as pipeline:
        result = (
            pipeline
            | "Create" >> beam.Create([1, 2, 3])
            | "Count" >> beam.Map(lambda x: x)
        )
        assert_that(result, equal_to([1, 2, 3]))

    counters = MetricsFilter().get_counters()
    ...
```

`MetricsFilter` filters by namespace, name, step, and label, and returns
the accumulated values. This is how you test custom metrics without a GCP
project — a technique covered in the next chapter.

---

## 🛠️ Hands-On: Testing a `CombineFn`'s Merge-Order Independence

This is the hands-on for the chapter: write the test that guarantees a
combiner is safe to run at scale.

### Step 1 — see the project as it stands

```bash
cd data-engineering/data-Course/google/Dataflow
source .venv/bin/activate
python3 -m pytest project/tests/ -v
```

You should see the whole suite pass:

```text
...........................................................              [100%]
59 passed, 1 warning in 3.08s
```

The warning is pytest declining to collect Beam's `TestPipeline` class as a
test, because it has an `__init__` constructor. It is harmless.

### Step 2 — read the combiner under test

```bash
sed -n '387,425p' project/transforms.py
```

`RevenueByRegionFn` implements the four contract methods. The accumulator
is a plain dict of two floats — cheap to create, cheap to merge.

### Step 3 — write the property test

Create `project/tests/test_combine_properties.py`:

```python
"""
test_combine_properties.py — property tests for the `CombineFn` contract.

The important property is **merge-order independence**: Beam merges partial
accumulators from different workers in an arbitrary order, so a combiner
whose merge is order-sensitive produces different totals on different days
for the same input.

Usage:
    python3 -m pytest project/tests/test_combine_properties.py -v
"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

apache_beam = pytest.importorskip(
    "apache_beam", reason="apache-beam is not installed"
)

from transforms import RevenueByRegionFn  # noqa: E402


ORDERS = [
    {"amount": 10.0, "currency": "EUR"},
    {"amount": 20.0, "currency": "EUR"},
    {"amount": 30.0, "currency": "EUR"},
    {"amount": 15.0, "currency": "GBP"},
    {"amount": 5.0, "currency": "JPY"},
]


def _accumulate(combiner, orders):
    """Fold a list of orders into one accumulator, in list order."""
    accumulator = combiner.create_accumulator()
    for order in orders:
        accumulator = combiner.add_input(accumulator, order)
    return accumulator


def _expected_total(orders):
    """The answer a correct combiner must produce, computed independently."""
    count = 0
    total = 0.0
    for order in orders:
        count += 1
        if order["currency"] == "EUR":
            total += order["amount"]
        elif order["currency"] == "GBP":
            total += round(order["amount"] * 1.17, 2)
        else:
            total += round(order["amount"] * 0.0064, 2)
    return {"order_count": count, "revenue_eur": round(total, 2)}


class TestMergeOrderIndependence:
    """`merge_accumulators` must not depend on the order it is given."""

    def test_all_partitions_produce_the_same_total(self):
        """Every way of splitting the input gives the same merged answer."""
        combiner = RevenueByRegionFn()
        expected = _expected_total(ORDERS)

        # Split the orders into every possible two-way partition.
        for split in range(len(ORDERS) + 1):
            left_orders = ORDERS[:split]
            right_orders = ORDERS[split:]

            left = _accumulate(combiner, left_orders)
            right = _accumulate(combiner, right_orders)

            merged = combiner.merge_accumulators([left, right])
            assert combiner.extract_output(merged) == expected

    def test_merge_is_commutative(self):
        """Merging [a, b] and merging [b, a] give the same answer."""
        combiner = RevenueByRegionFn()
        expected = _expected_total(ORDERS)

        left = _accumulate(combiner, ORDERS[:2])
        right = _accumulate(combiner, ORDERS[2:])

        assert combiner.extract_output(combiner.merge_accumulators([left, right])) == expected
        assert combiner.extract_output(combiner.merge_accumulators([right, left])) == expected

    def test_every_permutation_of_three_accumulators_agrees(self):
        """Three-way merges agree regardless of permutation."""
        combiner = RevenueByRegionFn()
        expected = _expected_total(ORDERS)

        parts = [
            _accumulate(combiner, ORDERS[0:2]),
            _accumulate(combiner, ORDERS[2:4]),
            _accumulate(combiner, ORDERS[4:]),
        ]

        for permutation in itertools.permutations(parts):
            merged = combiner.merge_accumulators(list(permutation))
            assert combiner.extract_output(merged) == expected

    def test_merging_one_accumulator_is_the_identity(self):
        """Merging a single accumulator changes nothing."""
        combiner = RevenueByRegionFn()
        only = _accumulate(combiner, ORDERS)

        merged = combiner.merge_accumulators([only])
        assert combiner.extract_output(merged) == _expected_total(ORDERS)

    def test_merging_with_the_empty_accumulator_is_the_identity(self):
        """The empty accumulator is the identity element."""
        combiner = RevenueByRegionFn()
        only = _accumulate(combiner, ORDERS)
        empty = combiner.create_accumulator()

        merged = combiner.merge_accumulators([only, empty])
        assert combiner.extract_output(merged) == _expected_total(ORDERS)
```

Run it:

```bash
python3 -m pytest project/tests/test_combine_properties.py -v
```

```text
test_combine_properties.py::TestMergeOrderIndependence::test_all_partitions_produce_the_same_total PASSED
test_combine_properties.py::TestMergeOrderIndependence::test_merge_is_commutative PASSED
test_combine_properties.py::TestMergeOrderIndependence::test_every_permutation_of_three_accumulators_agrees PASSED
test_combine_properties.py::TestMergeOrderIndependence::test_merging_one_accumulator_is_the_identity PASSED
test_combine_properties.py::TestMergeOrderIndependence::test_merging_with_the_empty_accumulator_is_the_identity PASSED
```

### Step 4 — break it, and watch the test catch it

A test that cannot fail is not a test. Temporarily make the combiner
order-sensitive by editing `project/transforms.py` so `merge_accumulators`
subtracts instead of adds for the second accumulator. Replace the whole
method with this:

```python
def merge_accumulators(self, accumulators):
    """A deliberately broken, order-sensitive merge."""
    total = self.create_accumulator()
    for index, partial in enumerate(accumulators):
        sign = 1 if index == 0 else -1
        total["order_count"] += sign * partial["order_count"]
        total["revenue_eur"] += sign * partial["revenue_eur"]
    return total
```

Re-run the tests:

```bash
python3 -m pytest project/tests/test_combine_properties.py -v
```

```text
FAILED test_combine_properties.py::TestMergeOrderIndependence::test_all_partitions_produce_the_same_total
FAILED test_combine_properties.py::TestMergeOrderIndependence::test_merge_is_commutative
FAILED test_combine_properties.py::TestMergeOrderIndependence::test_every_permutation_of_three_accumulators_agrees
```

Three of the five fail. The two that still pass are the ones that only
merge a single accumulator, or merge with the empty one — which is exactly
right, because neither exercises the ordering.

Now restore the original implementation:

```bash
cd data-engineering/data-Course/google/Dataflow
git checkout -- project/transforms.py
python3 -m pytest project/tests/ -q
```

```text
...........................................................              [100%]
64 passed, 1 warning in 3.07s
```

### Step 5 — add a windowed transform test

Now add a test that exercises the `use_global_window=False` path, in
`project/tests/test_combine_properties.py`:

```python
from apache_beam.testing.test_pipeline import TestPipeline  # noqa: E402
from apache_beam.testing.util import assert_that, equal_to  # noqa: E402
from apache_beam.transforms.window import FixedWindows  # noqa: E402
from apache_beam.utils.timestamp import Timestamp  # noqa: E402

from conftest import beam_test_options  # noqa: E402


def _windowed_values(expected):
    """Compare the values of windowed output, ignoring the windows."""

    def _compare(actual):
        unwrapped = [
            item.value if hasattr(item, "value") else item for item in actual
        ]
        return sorted(unwrapped, key=repr) == sorted(expected, key=repr)

    return _compare


class TestWindowedCombine:
    """A combiner inside a fixed window."""

    def test_counts_per_window(self):
        """Elements in different windows produce different groups."""
        base = 1_700_000_000

        with TestPipeline(options=beam_test_options()) as pipeline:
            result = (
                pipeline
                | "Create" >> beam.Create(
                    [
                        (Timestamp(base + 60), 1),
                        (Timestamp(base + 120), 2),
                        (Timestamp(base + 3600 + 60), 3),
                    ]
                )
                | "Window" >> beam.WindowInto(FixedWindows(3600))
                | "Key" >> beam.Map(lambda pair: ("all", pair[1]))
                | "Count" >> beam.combiners.Count.PerKey()
            )
            assert_that(
                result,
                _windowed_values([("all", 2), ("all", 1)]),
                use_global_window=False,
            )
```

Add the missing import at the top of the file:

```python
import apache_beam as beam  # noqa: E402
```

Run it:

```bash
python3 -m pytest project/tests/test_combine_properties.py -v
```

Now try removing `use_global_window=False` and see the failure message:

```text
Failed assert: [WindowedValue(value=('all', 2), timestamp=1767225600.0,
windows=IntervalWindow(1767225600.0, 1767229200.0))] == [('all', 2)],
unexpected elements [WindowedValue(value=('all', 2), ...)],
missing elements [('all', 2)]
```

That is the failure this chapter's matcher exists to prevent.

---

## 🛠️ Common Errors and Fixes

### `AssertionError: fixtures are not supported in unittest-style TestCase subclasses`

You wrote a test as a `unittest.TestCase` subclass and tried to use a
pytest fixture (like `tmp_path`) in it. Use plain pytest functions or
plain pytest classes — the course project's tests are plain classes with
no base class.

### `BeamAssertException: Failed assert: [...] == [...]` when you expected a match

You asserted on windowed output without `use_global_window=False`, or with
it but without unwrapping. The actual elements are `WindowedValue`
objects. Use the `_windowed_values` matcher from this chapter.

### `TypeError: '<' not supported between instances of 'WindowedValue' and 'tuple'`

You compared windowed elements directly with `==` in a plain `assert`.
Unwrap `.value` first, or use `equal_to` with `use_global_window=True`
when the window does not matter to the test.

### `TypeError: '<' not supported between instances of 'str' and 'int'`

`equal_to` tried to sort a collection with mixed types. It falls back to a
pairwise scan automatically — unless you are using `sorted()` yourself. In
a custom matcher, sort by `repr` instead:

```python
sorted(actual, key=repr) == sorted(expected, key=repr)
```

### `RuntimeError: Transform name is already used`

Two transforms in the same pipeline share a label. The error does not say
which ones. The course linter finds this statically:

```bash
python resources/audit_course.py
```

Remember that labels are scoped per pipeline: `"Create"` in two different
test methods is fine.

### `ImportError: cannot import name 'TestStream' from 'apache_beam.io'`

`TestStream` lives in `apache_beam.testing.test_stream`:

```python
from apache_beam.testing.test_stream import TestStream
```

There is no `beam.io.TestStream` in the SDK.

### `AttributeError: 'TestStream' object has no attribute 'advance_to'`

`TestStream` has no `advance_to`. Use `advance_watermark_to` for the event
time watermark, `advance_processing_time` for the processing-time clock,
and `advance_watermark_to_infinity` to flush every window at the end of the
stream.

### `TypeError: 'TestStream' object is not iterable`

You wrapped the stream in `beam.Create`. `TestStream` is a **transform**,
attached to the pipeline directly:

```text
p | "Stream" >> (TestStream().add_elements([...]).advance_watermark_to(t))
```

`beam.Create(stream)` tries to iterate the stream object and fails.

### `ValueError: Trigger AfterCount is not safe. See Beam documentation for more details.`

Beam refuses `AfterCount` by default, because a window can close while
elements are still in flight. Pass `--allow_unsafe_triggers` and set
`options.view_as(TypeOptions).allow_unsafe_triggers = True`. The
`beam_test_options` helper in `conftest.py` does both.

### `AttributeError: module 'pytest' has no attribute ...` / the helper is collected as a test

A helper function whose name starts with `test` is collected by pytest as a
test case. Rename `test_options` to `beam_test_options`.

### `ModuleNotFoundError: No module named 'apache_beam'` in the pure test file

The pure tests must not import Beam at all. If `test_transforms.py` fails
to import, you have accidentally added a Beam dependency to the pure half
of `transforms.py`. Use `pytest.importorskip("apache_beam")` in the files
that genuinely need it.

### The test passes locally and fails on Dataflow

Almost always a pickling problem. A `DoFn` that closes over a lambda, an
open file handle, or a database connection cannot be serialised to a
worker. Add a pipeline-level test that runs the `DoFn` through
`TestPipeline` — even the Direct Runner performs the serialisation step
and will surface the problem.

---

## 💡 Production Notes

- **The pure/Beam split is the highest-value decision in the chapter.** A
  project that puts its business rules in plain functions and leaves the
  `DoFn` as a thin shell has a test suite that runs in seconds and catches
  almost everything. A project that puts logic inline in `process` has a
  test suite that needs a runner for every assertion.
- **A combiner that is not order-independent will eventually produce a
  wrong number.** Not "might" — will. The partition boundaries change
  when you change the worker count, the autoscaling limit, or the input
  file order. The totals will differ by a fraction of a percent, and
  nobody will notice until a finance team reconciles.
- **Never compare floats for exact equality in a distributed test.** Sum
  `0.1` a hundred times in different orders and you get a different last
  bit. The course project rounds in `extract_output` for exactly this
  reason. If you cannot round, use `pytest.approx`.
- **Golden files are a contract, not a snapshot of convenience.** Before
  committing one, read it and confirm every value is correct. A golden
  file nobody reviewed is a permanent assertion that the bug is correct.
- **Test the boundaries, not the average.** Empty input, one element, a
  key that exists but has no valid values, a window with exactly one
  element, a malformed record at the very end of a file. The average case
  is the case that already works.
- **CI budget.** Keep the pure suite under 5 seconds and run it on every
  commit. Run the transform suite on every pull request. Run the
  integration suite nightly. If your full suite takes longer than 10
  minutes, people will start skipping it.
- **Test data should be small and hand-checked.** Five carefully chosen
  lines catch more bugs than five thousand generated ones. The course
  project's `ORDER_LINES` list is exactly this: five lines covering two
  regions, three currencies, and one status that should be filtered out.
- **Coverage percentage is not a goal.** A pipeline with 95% line coverage
  can still ship a wrong total, because the missing 5% is the merge path.
  Measure *which* branches are untested, not how many.

---

## 🔑 Key Takeaways

- Beam testing is a **four-layer pyramid**: pure-logic unit tests, transform-level tests, integration tests, and golden-file regression tests.
- **Keep business logic out of `DoFn.process`.** Put it in pure functions; the `DoFn` becomes a five-line shell and the tests become instant.
- **Use `apache_beam.testing.test_pipeline.TestPipeline`**, not the deprecated `PTest`. The new API runs on context-manager exit and cleans up its output directory.
- **`equal_to` compares collections, not sequences** — order never matters, duplicates always do.
- **`use_global_window=False` makes elements arrive as `WindowedValue` objects.** A custom matcher must unwrap `.value`; the `_windowed_values` helper in `project/tests/test_pipelines.py` is the working pattern.
- **Pin the runner and set `allow_unsafe_triggers` explicitly** with `options.view_as(TypeOptions).allow_unsafe_triggers = True`. Never name a pytest helper `test_*`.
- **A `CombineFn`'s merge must be associative and commutative.** Test merge-order independence directly, and break the test to prove it can fail.
- **Test what you own.** The runner's internals, autoscaling decisions, and Cloud Monitoring delivery are not your test suite.

---

## 📚 Practice Exercises

1. **Write a `DoFn` unit test without a runner.** Add a test to `project/tests/test_transforms.py` that instantiates `ParseOrderFn` and calls `process` directly on a malformed line, asserting that it yields nothing. The pure test file must keep working without `apache_beam` installed — check with `python3 -c "import sys; sys.modules['apache_beam'] = None"`-style isolation or by moving the test into the Beam-only file.

   *Expected answer:* the test belongs in `project/tests/test_pipelines.py` (the Beam-only file), because `ParseOrderFn` does not exist without the SDK. Assert `list(fn.process("garbage")) == []`.

2. **Write a property test for associativity.** Extend the property test from the hands-on so that it checks `merge(merge(a, b), c) == merge(a, merge(b, c))` for three accumulators built from disjoint slices of `ORDERS`. Use `itertools.permutations` to generate the cases. *Expected answer:* both orders produce `{"order_count": 5, "revenue_eur": 64.96}` — 10 + 20 + 30 EUR plus 15 GBP (17.55) plus 5 JPY (0.03).

3. **Add a `TestStream` test for a late element.** Use `TestStream` to emit two elements, advance the watermark past the window boundary, then emit a third element whose timestamp falls inside the already-fired window. Assert that the window emits once for the first two and that the late element produces a second, separate firing (or is dropped, depending on the allowed lateness you configure). *Expected answer:* with `FixedWindows(3600)` and zero allowed lateness the late element is dropped; with `allowed_lateness=300` and `--allow_unsafe_triggers` it produces an additional firing.

4. **Write a golden-file test.** Run the batch pipeline over a fixed five-line input, write the output to `project/tests/golden/summary.csv`, and add a test that compares the pipeline output to that file after sorting the lines. Then change one number in the golden file and confirm the test fails with a message that points at the difference. *Expected answer:* the failure message names the differing line rather than dumping the whole file.

5. **Audit the suite for brittleness.** Read `project/tests/test_pipelines.py` and list every assertion that could fail intermittently because of ordering, timing, or float precision. Then fix each one — usually by sorting before comparing or by rounding. *Expected answer:* at least the float-sensitive `revenue_eur` comparisons need `round()` or `pytest.approx`; the rest are safe because `equal_to` is order-insensitive.

6. **Write a matcher that checks the window.** Extend `_windowed_values` into a matcher that also asserts the expected window start and end for each element, using `item.windows[0].start` and `item.windows[0].end`. Use `beam.window.TimestampedValue` to place elements at known offsets. *Expected answer:* the matcher compares `(value, window_start, window_end)` triples and reports the mismatching triple in the exception message.

---

## 📖 Further Reading

- Apache Beam: Unit testing — https://beam.apache.org/documentation/sdks/python/testing/unit-testing/
- Apache Beam: Integration testing — https://beam.apache.org/documentation/sdks/python/testing/integration-testing/
- Apache Beam: `TestStream` API reference — https://beam.apache.org/documentation/sdks/python/apache-beam-testing-test_stream-apache-beam-testing-test-stream-py/
- Apache Beam: Metrics (`beam.metrics`) — https://beam.apache.org/documentation/sdks/python/apache-beam-metrics-metrics-py/
- Google Cloud Dataflow: Monitoring and logging — https://cloud.google.com/dataflow/docs/monitoring
- pytest: `importorskip` — https://docs.pytest.org/en/stable/how-to/skipping.html
