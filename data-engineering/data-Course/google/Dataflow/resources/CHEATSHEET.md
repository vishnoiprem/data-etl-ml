# Dataflow & Beam Cheat Sheet

> One page per topic. Keep it open in a tab.

---

## The pipeline skeleton

```python
import apache_beam as beam

with beam.Pipeline(options=options) as p:
    lines = (
        p
        | "Read" >> beam.io.ReadFromText("gs://bucket/orders.csv")
        | "Parse" >> beam.Map(parse_order_line)
        | "Valid" >> beam.Filter(lambda o: o["status"] == "complete")
        | "Key" >> beam.Map(lambda o: (o["region"], o["amount_eur"]))
    )
    revenue = lines | "Sum" >> beam.CombinePerKey(sum)
    _ = revenue | "Write" >> beam.io.WriteToText("gs://bucket/summary")
```

### The rules that never change

1. **A transform label is the left operand of `>>`**: `p | "Label" >> T`.
2. **Labels are unique within a pipeline.** Reusing one raises
   `RuntimeError: Transform name is already used`.
3. **A `DoFn` is the unit of work.** Put one `ParDo` per logical step so
   you can see where the time went.
4. **Everything is lazy until `run()`.** Building the graph does no I/O.
5. **Reuse the pipeline, not the data.** A `PCollection` is immutable and
   can be consumed by many downstream transforms.

---

## Beam transforms ↔ SQL

| Beam | SQL equivalent | Notes |
|---|---|---|
| `beam.Map(f)` | `SELECT f(col)` | 1 row → 0 or 1 row |
| `beam.FlatMap(f)` | `SELECT ... FROM UNNEST(f(col))` | 1 row → N rows |
| `beam.Filter(p)` | `WHERE p` | keeps matching rows |
| `beam.Flatten([a, b])` | `UNION ALL` | merges PCollections |
| `beam.CombinePerKey(f)` | `GROUP BY k` with `f` | **the scalable one** |
| `beam.GroupByKey()` | `GROUP BY k` | materialises every group |
| `beam.CoGroupByKey()` | `FULL OUTER JOIN` on the key | merges N keyed streams |
| `beam.ParDo(fn)` | a `CASE`/`UNNEST` expression | the general escape hatch |
| `beam.Reshuffle()` | a shuffle barrier | breaks fusion, spreads skew |
| `beam.WindowInto(w)` | `GROUP BY k, window` | streaming grouping |
| `beam.combiners.Count.PerKey()` | `COUNT(*)` | built-in, no DoFn needed |
| `beam.CombinePerKey(sum)` | `SUM(x)` | Python's builtin `sum` works |
| `beam.Map(lambda kv: kv[0])` | `SELECT k` | unwrap a keyed pair |

### Which one should I use?

- **`CombinePerKey` over `GroupByKey`**, always. `GroupByKey` buffers an
  entire group in memory; `CombinePerKey` keeps a compact accumulator and
  merges partial results. This is the difference between a pipeline that
  scales and one that dies at 2 TB.
- **`CoGroupByKey` over "run two aggregations and join the output".**
  It does the join inside the runner, with no shuffle round-trip through
  BigQuery.
- **`FlatMap` over `Map` + `Filter`** when the filter is a selection.

---

## Choosing a combiner

```python
# The three ways, in increasing order of work
beam.GroupByKey()                              # materialise everything
beam.CombinePerKey(lambda vs: sum(vs))        # a lambda combiner
class MyFn(beam.CombineFn):                   # a proper CombineFn
    def create_accumulator(self): ...
    def add_input(self, acc, v): ...
    def merge_accumulators(self, accs): ...
    def extract_output(self, acc): ...
```

A `CombineFn` must satisfy one property: **merging is order-independent
and associative**. If `merge(a, b) != merge(b, a)`, the result depends on
how the runner happened to shard the work, and your numbers will not be
reproducible.

```python
# Correct — a scalar accumulator
class SumFn(beam.CombineFn):
    def create_accumulator(self): return 0.0
    def add_input(self, acc, v): return acc + v
    def merge_accumulators(self, accs): return sum(accs)
    def extract_output(self, acc): return acc
```

---

## Windows and triggers

```python
from apache_beam.transforms.window import (
    FixedWindows, SlidingWindows, SessionWindows,
    TimestampCombiner,
)
from apache_beam.transforms.trigger import (
    AfterCount, AfterProcessingTime, AfterWatermark,
    AccumulationMode, Never,
)

beam.WindowInto(
    FixedWindows(60),                       # 60-second tumbling window
    trigger=AfterCount(10),                 # fire every 10 elements
    accumulation_mode=AccumulationMode.ACCUMULATING,
    allowed_lateness=30,                    # seconds
)
```

| Window | Shape | Use |
|---|---|---|
| `FixedWindows(n)` | tumbling, non-overlapping | hourly/daily rollups |
| `SlidingWindows(n, s)` | overlapping | rolling averages |
| `SessionWindows(gap)` | gap-delimited | user sessions |
| `GlobalWindows()` | one window | unbounded global aggregation |

### The trigger rules

| Trigger | Fires | Safe? | Accumulation |
|---|---|---|---|
| `DefaultTrigger` | when the window closes | yes | n/a |
| `AfterCount(n)` | every `n` elements | **no** — may lose data | `DISCARDING` |
| `AfterProcessingTime(d)` | `d` after processing time | **no** | `DISCARDING` |
| `AfterWatermark()` | when the watermark passes the window end | **only with zero allowed lateness** | `ACCUMULATING` |
| `Never()` | only when the pipeline ends | yes | n/a |

> **`AfterWatermark` + allowed lateness is an error.**
> `ValueError: Unsafe trigger: AfterWatermark may lose data. Reason:
> MAY_FINISH`. Beam will not run it unless you pass
> `--allow_unsafe_triggers`. With `ACCUMULATING` the late data is
> merged into the same output element; with `DISCARDING` it is dropped.

### Accumulation modes

| Mode | Emits | Use |
|---|---|---|
| `DISCARDING` | only what arrived since the last firing | deltas, alerts |
| `ACCUMULATING` | the running total every time | running totals, checkpoints |

---

## Side inputs

```python
rates = p | "ReadRates" >> beam.io.ReadFromText("gs://bucket/rates.csv")
lookup = rates | beam.Map(lambda line: tuple(line.split(","))) | beam.pvalue.AsDict()

result = lines | "Enrich" >> beam.Map(
    lambda o: {**o, "rate": lookup[o["currency"]]},
    lookup,
)
```

- A side input is **broadcast to every worker**. It must be small — the
  whole point is that it fits in memory everywhere.
- Beam 2.53+ prefers `AsDict`/`AsIter`/`AsList` over the deprecated
  `AsSingleton` for anything but a single value.
- `AsSingleton` on an empty PCollection raises at pipeline construction
  time, not at run time.

---

## `DoFn` and `PaneInfo`

```python
class ParseFn(beam.DoFn):
    def process(self, element, timestamp=beam.DoFn.TimestampParam,
                window=beam.DoFn.WindowParam,
                pane_info=beam.DoFn.PaneInfoParam):
        if pane_info.is_last:
            yield ...
```

| Param | Type | Use |
|---|---|---|
| `timestamp` | `Timestamp` | the element's event time |
| `window` | `BoundedWindow` | the window the element is in |
| `pane_info` | `PaneInfo` | `index`, `n`, `is_first`, `is_last` |
| `element` | `KV[K, V]` | only for `ParDo` over a keyed input |
| `windowed_value` | `WindowedValue` | timestamp + window together |

`PaneInfo` is what makes stateful `DoFn`s possible — `is_last` tells you
when a bundle is final.

---

## Coders and type hints

```python
from apache_beam.coders import FastPrimitivesCoder, AvroCoder, RowCoder

class MyFn(beam.DoFn):
    def process(self, element):
        yield beam.window.TimestampedValue(
            element,
            timestamp=...,   # re-stamp the event time
        )

# Force a coder on a specific output
beam.ParDo(ParseFn()).with_output_coder(FastPrimitivesCoder())
```

| Coder | Use |
|---|---|
| `FastPrimitivesCoder` | tuples, dicts of primitives — the default |
| `StrUtf8Coder` | plain strings |
| `AvroCoder` | Avro schemas |
| `RowCoder` | `apache_beam.rows.Row` — for BigQuery |
| `TupleCoder` | tuples with heterogeneous fields |

**Type hints matter.** Without them Beam falls back to `FastPrimitivesCoder`
and guesses at runtime. With them Beam picks the coder statically and
fails fast if the types do not match.

```python
def to_row(item: tuple[str, float]) -> dict[str, object]:
    ...
```

---

## `PipelineOptions`

```python
from apache_beam.options.pipeline_options import (
    PipelineOptions, StandardOptions, TypeOptions, GoogleCloudOptions,
)
from apache_beam.options.dataflow_options import DataflowOptions

options = PipelineOptions(["--runner=DataflowRunner", "--project=my-proj"])
options.view_as(StandardOptions).streaming = True
options.view_as(TypeOptions).allow_unsafe_triggers = True
```

| Subclass | Flags |
|---|---|
| `StandardOptions` | `--runner`, `--streaming`, `--temp_location` |
| `TypeOptions` | `--type_check`, `--allow_unsafe_triggers` |
| `DataflowOptions` | `--project`, `--region`, `--staging_location`, `--service_account_email`, `--network`, `--subnetwork`, `--machine_type`, `--max_workers`, `--autoscaling_algorithm` |
| `GoogleCloudOptions` | `--project`, `--region`, `--temp_location`, `--staging_location` |

> **`runner` is read-only.** `options.runner = "DataflowRunner"` raises.
> Pass `--runner=...` on the command line and Beam parses it.

---

## `gcloud dataflow`

```bash
# Jobs
gcloud dataflow jobs list --project=YOUR_PROJECT_ID --format="table(name,state,createTime)"
gcloud dataflow jobs describe JOB_ID --project=YOUR_PROJECT_ID
gcloud dataflow jobs describe JOB_ID --format='value(status)'
gcloud dataflow jobs cancel JOB_ID
gcloud dataflow jobs messages describe JOB_ID --format=json

# Metrics
gcloud dataflow jobs describe JOB_ID --format='value(metrics)'
gcloud dataflow jobs graph show JOB_ID --format=json

# Flex templates
gcloud dataflow flex-template build JOB_NAME \
    --template-file-gcs-path=gs://bucket/templates/worker.py \
    --temp-location=gs://bucket/dataflow/temp \
    --staging-location=gs://bucket/dataflow/staging

gcloud dataflow flex-template run JOB_NAME \
    --template=gs://bucket/templates/worker.py \
    --temp-location=gs://bucket/dataflow/temp \
    --staging-location=gs://bucket/dataflow/staging \
    --region=us-central1 \
    --project=YOUR_PROJECT_ID \
    --service-account=dataflow-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Worker logs
gcloud logging read \
    "resource.type=cloud_dataflow_job AND resource.labels.job_id=JOB_ID" \
    --project=YOUR_PROJECT_ID --limit=200
```

---

## `gcloud pubsub` and `gcloud storage`

```bash
# Pub/Sub
gcloud pubsub topics create events-topic --project=YOUR_PROJECT_ID
gcloud pubsub topics list
gcloud pubsub subscriptions create events-sub --topic=events-topic
gcloud pubsub subscriptions list
gcloud pubsub topics publish events-sub --message='{"region":"EMEA"}'

# Storage
gcloud storage ls gs://YOUR_BUCKET
gcloud storage cp ./local.csv gs://YOUR_BUCKET/data/
gcloud storage rsync ./out gs://YOUR_BUCKET/results/
gcloud storage cat gs://YOUR_BUCKET/file.csv | head
```

---

## Dataflow flex templates

A flex template is a **Python file uploaded to GCS**, then run by name.

```bash
# 1. Build
gcloud dataflow flex-template build orders-etl \
    --template-file-gcs-path=gs://YOUR_BUCKET/templates/orders.py \
    --temp-location=gs://YOUR_BUCKET/dataflow/temp \
    --staging-location=gs://YOUR_BUCKET/dataflow/staging

# 2. Run
gcloud dataflow flex-template run orders-etl \
    --template=gs://YOUR_BUCKET/templates/orders.py \
    --temp-location=gs://YOUR_BUCKET/dataflow/temp \
    --staging-location=gs://YOUR_BUCKET/dataflow/staging \
    --project=YOUR_PROJECT_ID --region=us-central1 \
    --service-account=dataflow-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --parameters="input=gs://YOUR_BUCKET/orders.csv,output=gs://YOUR_BUCKET/summary"

# 3. Stop a running streaming job
gcloud dataflow jobs cancel JOB_ID
```

> **Staging and temp locations must be unique per concurrent job.** The
> default locations collide, and the second job fails with a confusing
> "job already exists" error.

---

## Testing Beam pipelines

```python
from apache_beam.testing.test_pipeline import TestPipeline
from apache_beam.testing.util import assert_that, equal_to

with TestPipeline(options=options) as p:
    result = p | beam.Create([1, 2, 3]) | beam.Map(lambda x: x * 2)
    assert_that(result, equal_to([2, 4, 6]))
```

```python
# Windowed assertions need a window-aware matcher
assert_that(result, my_matcher, use_global_window=False)
```

> **`use_global_window=False` changes the element type.** Elements arrive
> as `WindowedValue` objects, not plain tuples. Comparing them directly
> fails with a confusing error. Unwrap `.value` first.

| Want | Use |
|---|---|
| assert on values | `assert_that(pcoll, equal_to([...]))` |
| assert on values in windows | `assert_that(pcoll, matcher, use_global_window=False)` |
| assert a count | `beam.testing.util.assert_that(pcoll, equal_to(N))` |
| pipeline should succeed | `assert_that(pcoll, empty())` for a DLQ |

---

## Testing options that matter

| Option | Why |
|---|---|
| `--runner=BundleBasedDirectRunner` | the default; supports all triggers |
| `--allow_unsafe_triggers` | required for `AfterCount` / `AfterProcessingTime` |
| `options.view_as(TypeOptions).allow_unsafe_triggers = True` | the programmatic form |

---

## Cost model

Dataflow bills **vCPU-hour**, not bytes.

| Item | Approximate cost |
|---|---|
| Dataflow worker | ~$0.05–0.10 per vCPU-hour |
| Dataflow streaming | ~$0.01–0.02 per GB processed |
| Dataflow batch | ~$0.02–0.05 per vCPU-hour |
| BigQuery | separate — you are billed for the writes |

**Levers that actually move the number:**

1. **Reduce the worker count** — autoscaling starts at 1 worker. A
   10 MB input does not need 100 workers.
2. **Use `machine_type` matching the work** — `n1-standard-2` for CPU-bound
   work, `n1-standard-4` for I/O-bound.
3. **Avoid `GroupByKey`** — it buffers.
4. **Turn off autoscaling for predictable batch jobs** with
   `--num_workers=1` when the input is small.
5. **Filter early** — a `Filter` before a `CombinePerKey` can cut the
   shuffle by an order of magnitude.

---

## Common error messages → cause

| Message | Cause |
|---|---|
| `RuntimeError: Transform name is already used` | duplicate transform label |
| `ValueError: accumulation_mode must be provided` | `AfterCount`/`AfterWatermark` without a mode |
| `ValueError: Unsafe trigger ... may lose data` | unsafe trigger without `--allow_unsafe_triggers` |
| `ValueError: Key ... not in ...` | a `GroupByKey` on a non-`KV` element |
| `AttributeError: module 'apache_beam.transforms.combiners' has no attribute 'Sum'` | there is no `combiners.Sum`; use `CombinePerKey(sum)` |
| `AttributeError: 'PipelineOptions' object has no attribute 'region'` | use `view_as(DataflowOptions)` |
| `RuntimeError: Transform name is already used` after adding a step | you forgot a unique label |
| `TypeError: unhashable type: 'dict'` | the key is a dict; use a tuple |
| `panic in ElementManager.Bundles watermark evaluation` | Prism runner + `AfterWatermark` |
| `ModuleNotFoundError: No module named 'apache_beam'` | wrong virtualenv |
