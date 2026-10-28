# Dataflow FAQ

> The questions students actually ask.

---

## Getting started

### Do I need a GCP project to follow the course?

**No.** Every chapter, every notebook and the whole project run on the
local Direct Runner with no credentials, no billing and no network. The
GCP sections (modules 4, 5 and parts of 8) are optional and are clearly
marked.

The reason the course is built this way is that a Dataflow job that
succeeds on your machine teaches you more than one that succeeds on GCP
after an hour of IAM debugging. The pipeline *logic* — which is the hard
part — is identical in both.

### Which runner should I use?

`BundleBasedDirectRunner` (the default). It is the classic pure-Python
runner, it supports the full trigger and windowing feature set, and it
behaves like Dataflow.

Beam 2.60+ also ships a Go-based runner called `DirectRunner` (the "Prism"
runner). It is genuinely faster — often 2–3× — but it does not yet
implement every trigger, and it panics on `AfterWatermark` and on the
`+inf` watermark evaluation that `TestPipeline` performs. Try it on the
batch pipeline with `--runner DirectRunner`; use the classic runner for
anything streaming.

### How long does the course take?

Roughly **35–40 hours** of focused work: about 14 hours of reading
(chapters), 10 hours in the notebooks, 8 hours on the project, and 6
hours on the interview questions. The modules are independent after
module 2, so you can reorder them.

### What Python version do I need?

**3.9–3.13.** The course was developed on **3.13**. If `pip install
apache-beam[gcp]` fails to build a wheel, install the plain
`apache-beam` first and add the extras afterwards.

### Do I need to know Java?

No. Everything in this course is Python. Java is mentioned in the
Dataflow comparisons because classic templates are JVM-based and the
Python SDK historically had a smaller feature set — but that gap has
narrowed considerably, and the flex template approach means your
production template can be Python too.

---

## The programming model

### What is the difference between `Map` and `FlatMap`?

`Map` is 1-to-0-or-1: one input element produces at most one output.
`FlatMap` is 1-to-N: one input element produces a list of outputs.

```python
beam.Map(lambda line: line.split(","))       # 1 line -> 1 list
beam.FlatMap(lambda line: line.split(","))    # 1 line -> N fields
```

If you are about to write `beam.Map(lambda x: [a, b])` and then have to
`FlatMap` it downstream, write the `FlatMap` instead.

### When should I use `CombinePerKey` instead of `GroupByKey`?

**Always.** `GroupByKey` buffers every element of every group in memory
before you touch it. `CombinePerKey` keeps a compact accumulator — a
running count, a running sum — and merges partial accumulators between
workers.

The difference is not incremental. A `GroupByKey` over 1 TB of data
fails; a `CombinePerKey` over the same data runs. The rule of thumb:
`GroupByKey` is for when you genuinely need the whole group (a sort, a
"take the top 10" that is not a combiner), and `CombinePerKey` is for
everything else.

### `CombinePerKey` and `GroupByKey` — what if my aggregation is not a simple sum?

Write a `CombineFn`. Four methods:

```python
class MyFn(beam.CombineFn):
    def create_accumulator(self): ...
    def add_input(self, acc, v): ...
    def merge_accumulators(self, accs): ...
    def extract_output(self, acc): ...
```

The critical property: **merging must be associative and
order-independent**. The runner merges partial accumulators from
different workers in an arbitrary order. If `merge(a, b) != merge(b, a)`,
your result depends on how the data happened to shard, and it will not be
reproducible between runs.

A good accumulator is a small summary (a count, a sum, a set of the top
k), never the full list.

### Why does `combiners.Sum` not exist?

There is no `beam.combiners.Sum`. Beam ships only the combiners that
need real machinery — `Count`, `Mean`, `Sum`, `Min`, `Max`... but the
actual API surface in Beam 2.77 has `Count`, `Mean`, `Min`, `Max`,
`Sample` and `Distinct`. For a plain sum, use Python's builtin:

```python
beam.CombinePerKey(sum)
```

The builtin works because `sum` is associative and commutative over
numbers, and Beam wraps it in a `CombineFn` for you. Note the key
convention: the values being summed must be the numbers themselves, so
key on the region and put the amount in the value.

### What is `CoGroupByKey` for?

Merging several keyed PCollections. It is the Beam equivalent of a
`FULL OUTER JOIN` on the key, done inside the runner:

```python
result = (
    {'counts': counts, 'sums': sums}
    | beam.CoGroupByKey()
)
```

Each output element is `(key, {'counts': [...], 'sums': [...]})`. Use it
when you would otherwise write two aggregations, dump them to BigQuery,
and join the two tables back together.

### What does the `>>` operator actually do?

`p | "Label" >> transform` applies `transform` to `p`. The label is
just a name — but it must be **unique within the pipeline**. Beam raises
`RuntimeError: Transform name is already used` otherwise, and the error
message does not say which labels collided.

The course linter catches this statically:

```bash
python resources/audit_course.py
```

### Why do my transform labels collide when I copy a block?

Because you copied it. The fix is to rename the labels. The course
linter flags duplicates **per function scope**, so two different test
methods may both use `"Create"` — they are two different pipelines.

### What is the difference between `beam.ParDo` and `beam.Map`?

`Map` is a `ParDo` with the function applied to each element. `ParDo` is
the general form: it can emit zero, one or many elements per input, and
it can access windowing and state parameters.

Use `Map` when you can. Use `ParDo` when you need `PaneInfo`, state,
timers, or multiple outputs.

### What is a `DoFn` "instance"?

The Python object your `DoFn` subclass is instantiated as. It is
**serialised to the workers** when the pipeline is submitted.

This is why a `DoFn` must not hold an open file handle, a database
connection or a `requests.Session` — those cannot be pickled, and the
job fails at submission time with a confusing error. Put that setup in
`setup()` instead, which runs on each worker.

---

## Windowing and streaming

### Why does `AfterWatermark` fail with "Unsafe trigger"?

```text
ValueError: Unsafe trigger: AfterWatermark() may lose data. Reason: MAY_FINISH
```

`AfterWatermark` fires when the watermark passes the window end. If
allowed lateness is non-zero, more data can still arrive for that
window, so Beam cannot prove the result is complete. Beam refuses the
combination unless you pass `--allow_unsafe_triggers`.

The course's streaming pipeline detects this and falls back to zero
allowed lateness with a warning, rather than failing.

### `AfterWatermark` with `ACCUMULATING` or `DISCARDING`?

`AfterWatermark` with `DISCARDING` is unusual — it fires once, at the
watermark, so there is nothing to discard. In practice `AfterWatermark`
is paired with `ACCUMULATING`, and the "discard" question is answered by
the allowed-lateness policy instead.

### What is the difference between accumulation modes again?

- `DISCARDING` — each firing emits only what arrived since the last
  firing. Use for deltas and alerts.
- `ACCUMULATING` — each firing emits the running total for the window.
  Use for running totals and checkpointing.

With `AfterCount(2)` over 5 elements:
- `ACCUMULATING` emits 2, 4, 5
- `DISCARDING` emits 2, 2, 1

### What is a watermark, precisely?

Beam's estimate of how far through the event-time timeline the pipeline
has processed. It is roughly **the minimum timestamp seen so far**, minus
the allowed lateness.

The consequence: a window closes not when wall-clock time passes it, but
when the *slowest* upstream source has moved past it. That is why
watermarks are the hard part of streaming and why the watermark
estimation in Dataflow is configurable — a single lagging source can
stall every downstream window.

### What is the difference between event time and processing time?

- **Event time** — when the event actually happened, as recorded in the
  data. This is what you window over.
- **Processing time** — when the runner saw it.

They differ exactly when the pipeline is behind. A pipeline that falls
behind by an hour still computes the correct hourly rollup, because the
window is defined on event time. If you window on processing time
instead, a backlog produces one giant window with all the data in it.

### How do I handle late data?

Three options, in increasing order of complexity:

1. **Set `allowed_lateness`** — the window stays open that long, and late
   elements are merged in. With `ACCUMULATING` the output is updated.
2. **Use a trigger that fires repeatedly** — `AfterCount` or
   `AfterProcessingTime` with `ACCUMULATING` gives you incremental
   output.
3. **Accept the data loss** — with `DISCARDING` and no lateness, late
   elements are dropped. This is a legitimate design choice for
   "approximate but fast" dashboards, provided you say so.

### Why does the streaming pipeline produce no output on the Direct Runner?

The Direct Runner processes a **bounded** file, so the watermark advances
to `+inf` and every window closes — but only after the input is
exhausted. With a file source, you get one final output per window, and
it appears at the end of the run.

For incremental output, use `--trigger-count N` (`AfterCount`) instead
of the default `AfterWatermark`. Then each window fires every N elements
and you see results as it goes.

### What is `use_global_window=False` and why does my assertion fail?

```python
assert_that(result, matcher, use_global_window=False)
```

With `use_global_window=False`, the elements are in non-global windows,
so Beam delivers them as `WindowedValue` objects rather than plain
tuples. Comparing them directly against a list of tuples fails.

Unwrap `.value` first:

```python
def _compare(actual):
    unwrapped = [item.value if hasattr(item, "value") else item for item in actual]
    return sorted(unwrapped) == sorted(expected)
```

---

## I/O and coders

### How do I choose a coder?

Let the type hints do it. If your function is annotated, Beam picks the
coder statically:

```python
def to_row(item: tuple[str, float]) -> dict[str, object]:
    ...
```

Without hints, Beam falls back to `FastPrimitivesCoder` and guesses at
runtime — which means the failure happens on a worker, not on your
machine.

Force one when you need to:

```python
beam.ParDo(ParseFn()).with_output_coder(FastPrimitivesCoder())
```

### What is the difference between a coder and an encoder?

A **coder** serialises a Python type the coder framework understands.
An **encoder** handles types the coder framework cannot represent
directly — `apache_beam.rows.Row`, protos, and other custom types.

### `WriteToText` writes one file per shard. How do I get one file?

You do not, and you should not try. `WriteToText` deliberately writes
multiple shards, because a single output file would serialise the
parallelism you just built.

To get one file, either concatenate afterwards, or use a sink that
handles the merge itself (`WriteToBigQuery` writes rows, not files).

### Why is my `WriteToText` output full of Python dict reprs?

Because `WriteToText` calls `str()` on each element. A dict becomes
`{'region': 'EMEA', 'order_count': 3}`.

Convert to a string first — the project uses `csv.writer` for exactly
this reason:

```python
| "Format" >> beam.Map(format_summary_csv)
```

### How do I read a CSV with a header?

`ReadFromText` gives you the raw lines, header included. Skip it:

```python
p | "Read" >> beam.io.ReadFromText(path)
     | "SkipHeader" >> beam.Filter(lambda line: not line.startswith("order_id"))
```

Or use `ReadFromCsv` with `skip_header_lines=1`:

```python
p | "Read" >> beam.io.ReadFromCsv(
    path,
    skip_header_lines=1,
    infer_schema=True,
)
```

### What is `with_sharding` doing in `WriteToText`?

It controls how output files are split. The default splits on **file
size** (roughly 128 MB per shard), not on row count. This is a common
misconception — a shard is not "the first 50,000 rows".

```python
beam.io.WriteToText(path, shard_name_template="", num_shards=1)
```

Setting `num_shards=1` forces a single output file at the cost of
parallelism.

---

## Dataflow and GCP

### What are the three service identities?

| Identity | Role |
|---|---|
| Your account | submits the job |
| Dataflow service agent | creates workers, accesses GCS |
| Worker service account | the identity the workers run as |

They need different roles and confusing them is the most common cause of
a job that fails to start. `roles/dataflow.serviceAgent` for the service
agent, `roles/dataflow.worker` for the worker SA, plus
`roles/storage.objectAdmin` on both.

### My job fails with a 403 on `storage.objects.get`

The Dataflow service agent is missing `roles/storage.objectAdmin`. The
subtle part: if you add the role **after** the service agent was
created, it does not take effect until you remove and re-add the
service agent, because Dataflow caches the policy at creation time.

### `DefaultCredentialsError: Could not automatically determine credentials`

You ran a `DataflowRunner` job without credentials:

```bash
gcloud auth application-default login
```

Or you meant to run locally — use `--runner BundleBasedDirectRunner`.

### Why does Dataflow reject my staging location?

Two concurrent jobs with the same staging location collide. The default
locations are shared, so **always** set them explicitly, and make them
unique per job.

### What is a flex template, and how is it different from a classic template?

A **flex template** is a Python file uploaded to GCS and run by its GCS
path. You can update the file and rerun without rebuilding anything.

A **classic template** is a packaged Java class (or Python wheel) invoked
by a fully-qualified class name. It is more rigid but was the only
option for years.

For a course project, flex templates are the better choice: no Java
toolchain, and the "template" is just a file you can read.

### How do I stop a streaming job?

```bash
gcloud dataflow jobs cancel JOB_ID
```

The job goes to `Cancelled` and its workers are reclaimed. This is the
normal way to apply a code change to a streaming pipeline — there is no
"update in place".

### Why is my streaming job using 100 workers for 10 MB of data?

Autoscaling starts workers based on observed throughput. On a fresh
project the first few minutes are spent scaling up and down. For a
small job, pin the worker count:

```bash
--num_workers=1 --autoscaling_algorithm=NONE
```

### How much does this cost?

Dataflow bills **vCPU-hour**, roughly $0.05–0.10 per vCPU-hour for
standard workers, plus per-GB charges for streaming. A 5,000-row batch
job on one `n1-standard-2` worker costs **under a cent**.

The number that surprises people is usually a streaming job left running
over a weekend: 100 workers × 72 hours × $0.06 = **$432**. Set a budget
alert.

---

## Performance and cost

### My pipeline is slow. Where do I look?

The Dataflow job graph, in order:

1. **Is the shuffle the bottleneck?** A `GroupByKey` or `CombinePerKey`
   shows up as a slow, wide stage. That is the shuffle.
2. **Is there a hot key?** One worker with a large share of the data is
   skew. Fix with `Reshuffle` or a hot key splitter.
3. **Is the source the bottleneck?** A `ReadFromText` stage that is slow
   and narrow means the input format is the problem — Avro and Parquet
   beat CSV, and splitting a huge CSV into many files helps.
4. **Is it fusion?** The runner fuses compatible transforms, which is
   usually good. `Reshuffle` breaks the fusion when you need it.

### What is skew and how do I fix it?

**Skew** is an uneven distribution of work — one key with 40% of the
data causes one worker to do 40% of the work while the rest idle.

Fixes, cheapest first:
1. **Filter or aggregate upstream** so the hot key never reaches the
   shuffle.
2. **`Reshuffle`** before the aggregation to redistribute.
3. **A hot key splitter** — split the hot key into `N` sub-keys before
   the shuffle and re-merge after. This is the correct fix when the
   aggregation must be exact.

### Should I use `GroupByKey` for "top 10 per group"?

Not directly. `GroupByKey` materialises every group.

The scalable pattern is `CombinePerKey` with a combiner that keeps a
bounded top-k heap — the accumulator is 10 elements, not 10 million.
That is exactly what `CombineFn` is for, and why
`combine_accumulators` must return a mergeable summary.

### How do I make the pipeline cheaper?

In order of impact:

1. **Fewer workers.** Autoscaling starts at 1. Most test jobs need 1.
2. **Filter before aggregating.** It can cut the shuffle by 10×.
3. **Use a smaller machine for the shuffle-heavy stage** and a bigger
   one for the CPU-heavy stage. Dataflow does not auto-size per stage.
4. **Replace `GroupByKey` with `CombinePerKey`.**
5. **Use Parquet or Avro instead of CSV** for the I/O stages — parsing
   is often 60% of a CSV pipeline's runtime.

---

## Testing

### How do I test a Beam pipeline?

```python
from apache_beam.testing.test_pipeline import TestPipeline
from apache_beam.testing.util import assert_that, equal_to

with TestPipeline(options=options) as p:
    result = p | beam.Create([1, 2, 3]) | beam.Map(lambda x: x * 2)
    assert_that(result, equal_to([2, 4, 6]))
```

`TestPipeline` runs the pipeline with the Direct Runner and collects the
output for assertion. It is the modern API — the older `PTest` style
is deprecated.

### How do I test a windowed pipeline?

Set `use_global_window=False` and use a matcher that unwraps the
`WindowedValue`:

```python
assert_that(result, my_matcher, use_global_window=False)
```

The course's `project/tests/test_pipelines.py` has a working example.

### Why does my test pass locally but fail on Dataflow?

Three usual reasons:

1. **Non-deterministic ordering.** `equal_to` is order-insensitive, but
   `assert_that` on a *list* preserves order. If the order differs
   between runners, sort before comparing.
2. **A combiner that is not order-independent.** If
   `merge(a, b) != merge(b, a)`, the result depends on the sharding,
   which differs between the local runner and Dataflow. This is a real
   bug in your combiner, and the cross-runner test is doing its job.
3. **Time-dependent logic.** A window boundary computed from
   `datetime.now()` behaves differently on a worker in another timezone.

### Do I need a GCP account to run the tests?

No. `project/tests/test_transforms.py` tests the pure logic and needs
**no** Beam at all. `project/tests/test_pipelines.py` needs Beam but not
credentials. Neither needs a network.

---

## Troubleshooting

### `RuntimeError: Transform name is already used`

Two transforms in the same pipeline share a label. Run the linter:

```bash
python resources/audit_course.py
```

### `ValueError: accumulation_mode must be provided for non-trivial triggers`

`AfterCount` and `AfterWatermark` need an explicit mode:

```python
accumulation_mode=AccumulationMode.ACCUMULATING
```

### `ValueError: Unsafe trigger: AfterCount(100) may lose data`

Beam will not run a trigger it cannot prove is safe without
`--allow_unsafe_triggers`. The course's streaming pipeline detects this
and falls back to zero allowed lateness with a warning.

### `panic in ElementManager.Bundles watermark evaluation goroutine`

The Prism runner and `AfterWatermark` do not mix. Use
`BundleBasedDirectRunner`.

### `AttributeError: module 'apache_beam.transforms.combiners' has no attribute 'Sum'`

There is no `combiners.Sum`. Use `beam.CombinePerKey(sum)`.

### `AttributeError: 'PipelineOptions' object has no attribute 'region'`

Dataflow-specific flags live on the `DataflowOptions` subclass:

```python
options.view_as(DataflowOptions).region = "us-central1"
```

### `TypeError: unhashable type: 'dict'`

The key you are grouping by is a dict. Use a tuple or a frozen
structure.

### `ModuleNotFoundError: No module named 'apache_beam'`

The wrong virtualenv. Check with `which python` and
`pip show apache-beam`.

### My pipeline produces no output and no error

The most common cause is a filter that removed everything, followed by
a `CombinePerKey` over an empty PCollection. Beam does not error on an
empty PCollection — it just produces nothing.

Print the count at each stage while debugging:

```python
| "Count" >> beam.combiners.Count.PerKey()
```

### The job hangs with no output

A streaming job waiting on a watermark that never advances. Check that
the source is actually producing data, and that `allowed_lateness` is
not larger than the gap between your events.

---

## Course mechanics

### Where is the sample data?

```bash
python resources/sample_data.py --output-dir ./sample_data
```

It is deterministic — the same bytes every run, so the expected outputs
in the chapters stay correct.

### The expected output in the README does not match what I got

Two things to check:
1. You generated the data with the default settings. `--hot-key-rate` and
   `--late-events` change the dataset.
2. You are running the same pipeline. The batch pipeline counts only
   `complete` orders and converts currency with the static rate table in
   `transforms.py`.

### How do I run everything at once?

```bash
# The pure logic — 51 tests, no Beam needed
python3 -m pytest project/tests/test_transforms.py -q

# Everything
python3 -m pytest project/tests/ -q

# The linter
python resources/audit_course.py

# The course structural tests
python resources/test_course.py
```

### What is the `.env` for?

The course reads configuration from the **repository root** `.env`, so one
file configures every project in the repo. In this repository that path
is a *virtualenv directory*, not a dotenv file — the loader detects that
and falls back to the process environment. Point it elsewhere with
`load_dotenv(path)`, or just export the variables in your shell.

### How do I contribute a fix?

The course ships with a linter and a test suite. If you change a
chapter, run:

```bash
python resources/audit_course.py && python resources/test_course.py
```

The linter checks that every Python snippet parses, that every
`beam.<attr>` actually exists in the installed SDK, that transform labels
are unique, and that every relative link resolves.
