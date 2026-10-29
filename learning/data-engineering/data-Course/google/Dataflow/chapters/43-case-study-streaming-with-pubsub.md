# 7.7 — Case Study 3 — Streaming with Pub/Sub

> **Section 7 · Streaming Pipelines · Lecture 7.7 · 6:30**

## 🎯 What you will learn

- A complete, worked streaming case study built on the course's own `project/streaming_pipeline.py`
- How to read a streaming pipeline's requirements and turn them into a specific transform graph
- Why the key is `(region, value)` and not `region`, and how `CoGroupByKey` merges the two aggregations back together
- How trigger selection and the `allowed_lateness` guard interact
- The three input modes — bounded file, `TestStream`, and real Pub/Sub — and when to use each
- The local verification numbers, and why they are what they are
- How the `TestWindowing` tests pin down the windowing behaviour
- The deployment path via a Dataflow streaming flex template
- The honest limitations, and what I would change in production

---

## 🧠 Concept

### The business problem

A digital commerce team wants a live view of clickstream revenue, broken
down by region, hour by hour.

Concretely, the requirements are:

- Every clickstream event carries a `value` (the revenue attributable to
  that interaction) and a `region`.
- The leadership team wants a running total per region per hour, updated
  as the hour progresses, not at midnight.
- The numbers must be correct — this feeds a revenue dashboard that the
  CFO sees.
- The pipeline must not require a GCP account to develop and test.

That last requirement is what shapes the whole project. A streaming
pipeline is much easier to trust when you can run it on your laptop
against a file, see exactly what it produced, and then promote the *same
code* to a real topic.

### The requirements, stated precisely

| Requirement | Implication | How it is met |
|---|---|---|
| Unbounded source | The pipeline must be a real streaming pipeline, not a batch | `ReadFromPubSub` for production; `ReadFromText` and `TestStream` for local work |
| Bounded state | The pipeline must not accumulate unboundedly | Fixed windows; the state is released when the window closes |
| At-least-once safe | The same event may arrive twice | `dedup_key` in `project/transforms.py` derives the dedup key from the payload's own `event_id` |
| No GCP for local demo | The reader must be able to run everything offline | `ReadFromText` over `./sample_data/events.ndjson`, with a local runner by default |

"At-least-once safe" deserves a note. Pub/Sub delivers each message **at
least once**, so the same event can arrive twice — after a worker
reschedule, a subscription redelivery, or a checkpoint rollback. A naive
counting pipeline will double-count. The fix is to deduplicate *before*
the window, keyed on something that comes from the payload rather than
from arrival time:

```python
def dedup_key(event: dict) -> str:
    """Return the deduplication key for an event."""
    return str(event.get("event_id") or event.get("user_id", ""))
```

The course project exposes this helper; the streaming pipeline's role is to
apply it upstream of the windowing, where a duplicate would otherwise be
counted twice.

### The design — the exact graph

The pipeline in `project/streaming_pipeline.py` is this graph:

```text
                        ┌──────────────┐
   events (PCollection) │  ParseEvents │  beam.Map(parse_event)
                        └──────┬───────┘
                               │
                        ┌──────▼────────────┐
                        │   ApplyWindow     │  beam.WindowInto(
                        │                    │      FixedWindows(3600),
                        │                    │      trigger=AfterWatermark(),
                        │                    │      accumulation_mode=ACCUMULATING,
                        │                    │      allowed_lateness=<n>)
                        └──────┬────────────┘
                               │
                        ┌──────▼────────────┐
                        │   KeyByRegion     │  beam.Map((region, value))
                        └──────┬────────────┘
                               │
                   ┌───────────┴───────────┐
                   │                       │
            ┌──────▼────────┐      ┌───────▼────────┐
            │  CountEvents  │      │   SumValues    │
            │ Count.PerKey()│      │ CombinePerKey()│
            └──────┬────────┘      └───────┬────────┘
                   │                       │
            ┌──────▼────────┐      ┌───────▼────────┐
            │   TagCounts   │      │    TagSums     │
            └──────┬────────┘      └───────┬────────┘
                   │                       │
                   └───────────┬───────────┘
                               │
                        ┌──────▼────────────┐
                        │    GroupBoth      │  beam.CoGroupByKey()
                        └──────┬────────────┘
                               │
                        ┌──────▼────────────┐
                        │ MergeAggregations │  beam.Map(_merge)
                        └──────┬────────────┘
                               │
                        ┌──────▼────────────┐
                        │    FormatCsv      │  beam.Map(to_window_row)
                        └──────┬────────────┘
                               │
                        ┌──────▼────────────┐
                        │   WriteOutput     │  WriteToText
                        └───────────────────┘
```

Read that graph carefully — every stage exists for a reason, and two of
the design decisions are worth arguing about.

### The key design decision: why `(region, value)` and not `region`

This is the decision that most often trips people up when they first read
the pipeline, because the code comment says something slightly confusing:

```python
# The key is (region, value). The window is carried by Beam itself —
# after `WindowInto`, each element belongs to a window, and the
# combiner runs per (key, window) pair. So the key only needs the
# region, and the value needs to be something both `Count` and `sum`
# can consume.
keyed = windowed | "KeyByRegion" >> beam.Map(
    lambda event: (event["region"], event["value"])
)
```

Here is what is actually happening, and it is worth being precise because
the comment's phrasing can read as though the key is `(region, value)` in
the sense of a two-field key.

**Beam's grouping key is not just what your `Map` produces.** After
`WindowInto`, every element belongs to a window. When a grouping transform
runs, it groups by the **pair** `(key, window)`. So the effective grouping
key is `(region, window_start..window_end)` — the window is added
automatically, and you do not put it in your `Map`.

What your `Map` produces is the **user-defined key** (here, `region`) and
the **value** (here, the event's numeric `value`). The tuple
`(region, value)` is the standard Beam `KV` pair: key first, value second.

Now, why does the value need to be a number rather than the whole event
dict?

Because **the same keyed PCollection is consumed by two different
combiners**, and each combiner needs a different value shape:

- `beam.combiners.Count.PerKey()` does not look at the value at all. It
  counts elements. Any value works.
- `beam.CombinePerKey(sum)` needs a numeric value it can add.

So the value must be a number that `sum` can consume. If you passed the
whole event dict, `sum` would fail with a `TypeError` the first time the
combiner merged two accumulators.

And why do we need two aggregations at all, rather than one combiner that
produces both count and sum?

Because `CombinePerKey` takes **one** `CombineFn` and produces **one**
output value per key. You want two outputs (a count and a sum) from one
pass over the data, so you run two combiners over the same keyed
PCollection. Beam handles that efficiently: the two grouping stages share
the shuffle.

The `CoGroupByKey` then merges the two results back together, because
there is no built-in "join two PCollections" transform that preserves the
windowed key. `CoGroupByKey` is exactly that transform:

```python
tagged_counts = counts | "TagCounts" >> beam.Map(_tag, tag="count")
tagged_sums = sums | "TagSums" >> beam.Map(_tag, tag="sum")

grouped = (tagged_counts, tagged_sums) | "GroupBoth" >> beam.CoGroupByKey()
```

`CoGroupByKey` takes a tuple of keyed PCollections and, for each key,
produces a tuple of iterables — one per input. The tagging step is there
so you can tell the inputs apart when you unpack them.

A note on a common misconception: there is **no `beam.combiners.Sum`**.
The FAQ in this course records the error verbatim:

```text
AttributeError: module 'apache_beam.transforms.combiners' has no attribute 'Sum'
```

A sum is the builtin `sum` function, wrapped by Beam:

```python
sums = keyed | "SumValues" >> beam.CombinePerKey(sum)
```

### Trigger selection logic

The pipeline picks its trigger from `--trigger-count`:

```python
if trigger_count:
    trigger = AfterCount(count=trigger_count)
    accumulation_mode = AccumulationMode.DISCARDING
else:
    trigger = AfterWatermark()
    accumulation_mode = AccumulationMode.ACCUMULATING
```

| `--trigger-count` | Trigger | Accumulation | Behaviour |
|---|---|---|---|
| `0` (default) | `AfterWatermark()` | `ACCUMULATING` | Fires once when the watermark passes the window end. Exact, complete, final. |
| `N > 0` | `AfterCount(N)` | `DISCARDING` | Fires every N elements per window. Partial results throughout; the tail of the window is lost. |

Why `ACCUMULATING` for `AfterWatermark` and `DISCARDING` for `AfterCount`?

- `AfterWatermark` fires **once**. There is nothing to discard — the whole
  window arrives in one pane. `ACCUMULATING` is the honest description of
  that, and if the window ever fires a second time (because lateness was
  enabled), `ACCUMULATING` merges the late data into the total.
- `AfterCount` fires **repeatedly**. `DISCARDING` means each firing emits
  only the elements that arrived since the last firing — the deltas. That
  is what you want for a live dashboard: each update is an increment, not
  a repeated total. (`ACCUMULATING` would also work, but it would repeat
  the entire total every time, which is more data over the wire for the
  same information.)

### The `allowed_lateness` guard

The pipeline's guard is the subject of chapter 7.5, and it is worth
re-reading in context:

```python
unsafe = bool(getattr(options, "allow_unsafe_triggers", False)) if options else False

# With allowed lateness, the trigger becomes unsafe unless the caller
# opts in. Fall back to a zero-lateness window so the default run is
# always safe and always succeeds.
effective_lateness = allowed_lateness_seconds
if effective_lateness and not unsafe:
    log.warning(
        "allowed_lateness=%ds requires --allow_unsafe_triggers; "
        "falling back to 0s so the pipeline stays safe",
        effective_lateness,
    )
    effective_lateness = 0
```

Three things to note:

1. The check is on **`options`**, not on a command-line flag parsed by
   `argparse`. `allow_unsafe_triggers` lives on Beam's `TypeOptions`, so
   it is resolved through `build_options` in `project/beam_options.py`.
2. The fallback is **loud** — a `WARNING` on stderr. A silent downgrade
   would be worse than a failure.
3. The fallback only touches the **lateness**. The `--trigger-count` path
   is separate: asking for `AfterCount` without the flag still fails at
   the `GroupByKey` stage with Beam's own error.

### The three input modes

The pipeline supports exactly three sources, and choosing between them is
a large part of knowing how to test streaming code.

| Mode | Flag | Source | Needs GCP? | Use it for |
|---|---|---|---|---|
| Bounded file | *(default)* | `ReadFromText` | no | End-to-end verification of the numbers |
| Test stream | `--use-test-stream` | `beam.testing.test_stream.TestStream` | no | Deterministic watermark and re-trigger tests |
| Real Pub/Sub | `--topic YOUR_TOPIC` | `ReadFromPubSub` | yes | The production job |

**The bounded file mode** is the workhorse. `ReadFromText` over
`./sample_data/events.ndjson` exercises every streaming transform —
windowing, triggers, the combiners, the `CoGroupByKey` — without a
single GCP dependency. The one thing it does *not* exercise is late data,
because a bounded source advances the watermark to `+inf` at the end,
which makes every element on time.

**The `TestStream` mode** is the deterministic testing tool. `TestStream`
lets you advance the watermark explicitly, which is how you construct a
controlled event-time scenario:

```python
from apache_beam.testing.test_stream import TestStream
from apache_beam.transforms.window import TimestampedValue
from apache_beam.utils.timestamp import Timestamp

stream = TestStream()
stream.add_elements([TimestampedValue(("EMEA", 10.0), Timestamp(BASE + 0))])
stream.advance_watermark_to(Timestamp(BASE + 120))
stream.add_elements([TimestampedValue(("EMEA", 5.0), Timestamp(BASE + 5))])
```

Note the argument order of `TimestampedValue`: **value first, timestamp
second**. It is `TimestampedValue(value, timestamp)`, not
`TimestampedValue(timestamp, value)`. Getting this backwards produces a
`TypeError: Cannot interpret (...) as Timestamp` that is genuinely hard to
read the first time.

> **A caveat on `TestStream` and late data.** The snippet above *looks*
> like it constructs a late-data scenario, and it is tempting to read the
> result as evidence about `allowed_lateness`. It is not. The
> `DirectRunner`'s `TestStream` does not reliably deliver a genuinely late
> arrival — an element that arrives after the watermark has passed the
> window end — so the same totals come out whether the lateness budget is
> 300 seconds or 0. Use `TestStream` for what it is good at: deterministic
> control of watermark advancement and trigger timing. To assert on
> late-data handling specifically, drive the trigger driver directly (see
> chapter 7.5) or test against a real streaming source.

> **A note on the current project state.** The `--use-test-stream` path in
> `project/streaming_pipeline.py` does not currently work. Its
> `_build_test_stream()` helper returns a `TestStream` *PTransform* rather
> than a `PCollection`, and the pipeline then tries to feed that transform
> into `CoGroupByKey`, which fails with
> `TypeError: '_ChainedPTransform' object is not iterable`. The fix is to
> build the `TestStream` with its events configured *before* applying it
> to the pipeline, and to pass the resulting PCollection into
> `build_streaming_pipeline` as the `events` argument — the same shape the
> chapter's own example uses. The local verification in this chapter uses
> the bounded-file mode, which works correctly today.

**The Pub/Sub mode** is the production path. `ReadFromPubSub` takes either
a topic or a subscription:

```python
events = pipeline | "ReadPubSub" >> ReadFromPubSub(
    topic=args.topic, subscription=args.subscription
)
```

Two operational notes that matter in production:

- **Prefer a subscription over a topic.** A topic creates a fresh
  subscription for each job, so two concurrent jobs on the same topic
  each see *all* the messages. A named subscription distributes the
  messages between them.
- **Pub/Sub has no ordering guarantee across messages.** The event time
  in the payload is the only thing that makes windowing meaningful, which
  is exactly why `event_timestamp` in the project reads the event's own
  `event_ts` rather than using arrival time:

```python
def event_timestamp(event: dict):
    """Return the event's timestamp as a Beam timestamp.

    Using the event's own timestamp rather than arrival time is what makes
    windowing meaningful. Arrival-time windowing in a pipeline that sees
    out-of-order data produces silently wrong results.
    """
```

### The local verification

Run the pipeline against the generated sample data:

```bash
python resources/sample_data.py --output-dir ./sample_data
python project/streaming_pipeline.py \
    --input ./sample_data/events.ndjson \
    --output ./out/streaming \
    --window-seconds 3600
```

The expected output is:

```csv
region,event_count,total_value
APAC,4885,291314.62
EMEA,5099,302548.0
LATAM,4979,299522.51
AMER,5037,302651.93
```

| Region | Event count | Total value |
|---|---|---|
| APAC | 4,885 | 291,314.62 |
| EMEA | 5,099 | 302,548.00 |
| LATAM | 4,979 | 299,522.51 |
| AMER | 5,037 | 302,651.93 |

The counts sum to 20,000 — the exact number of events the generator
produces. That is the first correctness check, and it is a meaningful one:
it confirms no event was double-counted and none was dropped.

The second check is that the totals sum to the sum of every event's
`value`:

```bash
python -c "
import json
total = 0.0
count = 0
with open('./sample_data/events.ndjson') as fh:
    for line in fh:
        event = json.loads(line)
        total += float(event['value'])
        count += 1
print(f'events={count} total_value={round(total, 2)}')
"
```

```text
events=20000 total_value=1196037.06
```

And the four region totals sum to 291314.62 + 302548.0 + 299522.51 +
302651.93 = 1,196,037.06. They agree.

A note on the `WriteToText` output shape. The sink writes a header line
and one shard file, and the region order is not guaranteed — the runner
may process the keys in any order. Sort before comparing:

```bash
cat ./out/streaming* | sort
```

Do not write a test that depends on the row order.

### The testing strategy

The course's `project/tests/test_pipelines.py` pins down the windowing
behaviour with the `TestWindowing` class. Three tests, each targeting one
specific property:

**`test_fixed_window_groups_by_time`** — the foundational test. Three
events, two of them in the same hour, produce two groups of different
sizes:

```python
def test_fixed_window_groups_by_time(self):
    """Events in different windows produce different groups."""
    events = [
        ("2026-01-15T10:05:00+00:00", 10.0),
        ("2026-01-15T10:55:00+00:00", 20.0),
        ("2026-01-15T11:05:00+00:00", 30.0),
    ]

    with TestPipeline(options=beam_test_options()) as pipeline:
        result = (
            pipeline
            | "Create" >> beam.Create(events)
            | "WithTimestamps" >> beam.Map(
                lambda pair: (
                    beam.window.Timestamp(_to_epoch(pair[0])),
                    pair[1],
                )
            )
            | "Window" >> beam.WindowInto(FixedWindows(3600))
            | "KeyByRegion" >> beam.Map(lambda pair: ("all", pair[1]))
            | "Count" >> beam.combiners.Count.PerKey()
        )
        assert_that(
            result,
            _windowed_values([("all", 2), ("all", 1)]),
            use_global_window=False,
        )
```

**`test_accumulating_mode_emits_running_total`** — five elements with
`AfterCount(2)` and `ACCUMULATING` produce the counts `2, 4, 5`. The
running total, not the deltas.

**`test_discarding_mode_emits_running_total`** — the same five elements
with `DISCARDING` produce `2, 2, 1`. The deltas.

Those two tests together are the clearest possible demonstration of the
difference between the accumulation modes, and they are worth running
before you write any production windowing code:

```bash
python -m pytest project/tests/test_pipelines.py::TestWindowing -v
```

Two details in the test harness are worth copying into your own tests.

The first is `use_global_window=False`. With a real window, elements
arrive as `WindowedValue` objects carrying a start, an end, and a
timestamp. Comparing them against plain tuples fails. The
`_windowed_values` helper unwraps the value and compares only the
payload:

```python
def _compare(actual):
    unwrapped = [
        item.value if hasattr(item, "value") else item for item in actual
    ]
    return sorted(unwrapped, key=repr) == sorted(expected, key=repr)
```

The second is that the test harness sets `allow_unsafe_triggers`, because
`AfterCount` is by definition unsafe:

```python
flags = [f"--runner={TEST_RUNNER}", "--allow_unsafe_triggers"]
flags.extend(f"--{name}={value}" for name, value in extra.items())

options = PipelineOptions(flags)
options.view_as(TypeOptions).allow_unsafe_triggers = True
```

That is exactly the pattern the streaming pipeline uses to decide whether
to honour `--allowed-lateness-seconds`. Reading the two together shows
the project making the same safety decision in two places.

### The deployment path

The production deployment uses a **Dataflow streaming flex template**. The
template lives at `project/templates/streaming_template.py` and reads from
Pub/Sub, windows, and writes to Cloud Storage and optionally BigQuery.

Two steps:

**Build the template image:**

```bash
gcloud dataflow flex-template build streaming_template.py \
    --project YOUR_PROJECT_ID \
    --region us-central1 \
    --image gcr.io/YOUR_PROJECT_ID/dataflow/streaming-template:latest \
    --temp-location gs://YOUR_BUCKET/tmp
```

**Launch the streaming job:**

```bash
gcloud dataflow jobs run dataflow-streaming-template \
    --project YOUR_PROJECT_ID \
    --region us-central1 \
    --streaming \
    --image gcr.io/YOUR_PROJECT_ID/dataflow/streaming-template:latest \
    --temp-location gs://YOUR_BUCKET/tmp \
    --topic YOUR_PROJECT_ID.YOUR_TOPIC \
    --output gs://YOUR_BUCKET/streaming \
    --window-seconds 3600
```

The `--streaming` flag is **not optional**. Without it, Dataflow launches
the job as a batch job, and a batch job over an unbounded Pub/Sub source
never terminates. This is the most common deployment mistake with
streaming flex templates.

The `--staging_location` and `--temp_location` flags must be distinct
per concurrent job. `project/beam_options.py` derives them from the bucket
so they do not collide:

```python
base = bucket.rstrip("/")
if not getattr(options, "staging_location", None):
    options.staging_location = f"{base}/dataflow/staging"
if not getattr(options, "temp_location", None):
    options.temp_location = f"{base}/dataflow/temp"
```

### The honest limitations

Every course project has limits, and a case study that hides them teaches
the wrong lesson. These are the real ones in this pipeline.

**No watermark hold-back per source.** The pipeline has one source, so
the multi-source watermark stall described in chapter 7.5 does not arise
here. If you add a second source, you must add a per-source hold-back and
a `TimestampCombiner.OUTPUT_AT_EOW`, or every window will stall.

**No per-key state.** The pipeline is a `CombinePerKey` over a fixed
window. It does not track a user across windows, so it cannot compute
per-user metrics, detect sessions, or deduplicate across windows. The
deduplication key exists in `project/transforms.py` but is not applied in
the streaming pipeline's graph — a real gap, because Pub/Sub is
at-least-once and duplicates will inflate the counts.

**Static currency assumptions.** The batch pipeline converts to EUR using a
static rate table in `project/transforms.py`. The streaming pipeline does
no currency conversion at all — it sums the raw `value` field, which is
whatever currency the event producer used. A production version would
either require all producers to emit a single currency, or read a
periodically-refreshed rate table and join it in.

**`WriteToText` is an awkward sink for a streaming pipeline.** This is the
biggest structural limitation. `WriteToText` is a *file* sink: it writes
shard files at the end of the job. For a streaming job that never ends,
the files are only finalised when the job is cancelled. Worse, with
`ACCUMULATING` and non-zero allowed lateness, a window can fire more than
once, and `WriteToText` will happily write two rows for the same window.

In production you would write to **BigQuery**, with a schema keyed on
`(region, window_start)` and a write disposition that upserts rather than
appends. The template already has the shape of this:

```python
if bigquery_table:
    rows | "WriteBigQuery" >> beam.io.WriteToBigQuery(
        bigquery_table,
        write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
        create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
    )
```

BigQuery's streaming buffer accepts rows continuously, and a
`MERGE`-style upsert handles re-firing windows correctly.

**A window can fire more than once.** With `ACCUMULATING` and a non-zero
lateness budget, the same window produces multiple output rows. Any
downstream consumer must be idempotent.

**The `--use-test-stream` mode does not currently work.** As described
above, the helper returns a PTransform rather than a PCollection.

### What I would change in production

Six changes, in priority order.

**1. Deduplicate upstream of the window.** Apply `dedup_key` before the
windowing, and keep a bounded set of recently-seen keys per worker (a
`SetStateSpec` with a TTL, or a `BagStateSpec` trimmed on a timer). Without
this, the counts are wrong whenever Pub/Sub redelivers — which is
constantly, not occasionally.

**2. Write to BigQuery with an upsert disposition.** Replace `WriteToText`
with `beam.io.WriteToBigQuery` against a table keyed on `(region,
window_start)`. Use `WRITE_APPEND` with a partition on `window_start`, or
a `MERGE` if you need exactly-once semantics per window. This fixes the
"streaming into a file sink" problem and the "duplicate row on re-fire"
problem at once.

**3. Add a per-source watermark hold-back** as soon as a second source
appears, with `TimestampCombiner.OUTPUT_AT_EOW` on the merged window.
Also: set the Pub/Sub source's own watermark hold-back so a quiet topic
does not stall the pipeline.

**4. Replace the static currency table** with a periodically-refreshed
side input — a rates table in BigQuery, read once per window, joined in
with `beam.pvalue.AsDict`. A side input is re-read on each window if you
use a `DoFn` with `setup()` and a `SetupContext`; the simpler version is
to re-read it on a timer.

**5. Emit the window boundaries in the output.** The current `to_window_row`
emits `region,event_count,total_value` — with no indication of *which*
hour the numbers describe. That is a real usability bug for a dashboard.
Add the window start and end. In a `DoFn` you get them from
`beam.DoFn.WindowParam`; with a `Map` you can read them from the
`WindowedValue` that arrives when `use_global_window=False`.

**6. Add the metrics that tell you the job is healthy.** At minimum:

- watermark age, per stage — the single most useful streaming metric, and
  the only one that catches a stalled pipeline;
- the count of late elements received and dropped;
- the number of open windows and the bundled data size;
- the input element count, per source, so you can spot a redelivery storm.

### Putting it together: the whole pipeline in one page

```python
import apache_beam as beam
from apache_beam.io.textio import ReadFromText, WriteToText
from apache_beam.transforms.window import FixedWindows
from apache_beam.transforms.trigger import AccumulationMode, AfterWatermark

with beam.Pipeline() as p:
    events = p | "ReadEvents" >> ReadFromText("./sample_data/events.ndjson")

    parsed = events | "ParseEvents" >> beam.Map(parse_event)

    windowed = parsed | "ApplyWindow" >> beam.WindowInto(
        FixedWindows(size=3600),
        trigger=AfterWatermark(),
        accumulation_mode=AccumulationMode.ACCUMULATING,
        allowed_lateness=0,
    )

    keyed = windowed | "KeyByRegion" >> beam.Map(
        lambda event: (event["region"], event["value"])
    )

    counts = keyed | "CountEvents" >> beam.combiners.Count.PerKey()
    sums = keyed | "SumValues" >> beam.CombinePerKey(sum)

    combined = _combine_counts_and_sums(counts, sums)

    combined | "FormatCsv" >> beam.Map(to_window_row) | "WriteOutput" >> WriteToText(
        "./out/streaming",
        header="region,event_count,total_value",
        num_shards=1,
        shard_name_template="",
    )
```

Seven lines of graph. Everything else in this chapter is about *why* each
of those lines is what it is.

---

## 🛠️ Hands-On

### Step 1 — Generate the sample data

```bash
python resources/sample_data.py --output-dir ./sample_data
```

```bash
cat ./sample_data/summary.json
```

```json
{
  "orders": 5000,
  "events": 20000,
  "malformed_rows": 5,
  "reference_rows": 50,
  "target_date": "2026-01-15"
}
```

### Step 2 — Run the streaming pipeline

```bash
python project/streaming_pipeline.py \
    --input ./sample_data/events.ndjson \
    --output ./out/streaming \
    --window-seconds 3600
```

Watch for the fallback warning — the default `--allowed-lateness-seconds`
is 300, and without the opt-in flag it is downgraded to 0:

```text
WARNING __main__: allowed_lateness=300s requires --allow_unsafe_triggers; falling back to 0s so the pipeline stays safe
```

### Step 3 — Verify the output

```bash
cat ./out/streaming* | sort
```

```csv
region,event_count,total_value
AMER,5037,302651.93
APAC,4885,291314.62
EMEA,5099,302548.0
LATAM,4979,299522.51
```

### Step 4 — Check the invariants

```bash
python -c "
import csv, glob

rows = list(csv.DictReader(open(glob.glob('./out/streaming*')[0])))
rows = [r for r in rows if r.get('region')]

total_count = sum(int(r['event_count']) for r in rows)
total_value = round(sum(float(r['total_value']) for r in rows), 2)

print('regions       :', len(rows))
print('total events  :', total_count)
print('total value   :', total_value)
assert total_count == 20000, 'event count does not match the generator'
print('OK: every event was counted exactly once')
"
```

```text
regions       : 4
total events  : 20000
total value   : 1196037.06
OK: every event was counted exactly once
```

### Step 5 — Verify against the raw data independently

```bash
python -c "
import json
from collections import Counter

counts = Counter()
totals = Counter()
with open('./sample_data/events.ndjson') as fh:
    for line in fh:
        e = json.loads(line)
        counts[e['region']] += 1
        totals[e['region']] = round(totals[e['region']] + e['value'], 2)

for region in sorted(counts):
    print(f'{region},{counts[region]},{totals[region]}')
"
```

```csv
AMER,5037,302651.93
APAC,4885,291314.62
EMEA,5099,302548.0
LATAM,4979,299522.51
```

The Beam output matches a plain-Python reference implementation computed
from the raw file. That is the strongest form of the check: two independent
implementations, same answer.

### Step 6 — Change the window size

```bash
python project/streaming_pipeline.py \
    --input ./sample_data/events.ndjson \
    --output ./out/streaming_6h \
    --window-seconds 21600
```

```bash
cat ./out/streaming_6h* | sort
```

With a six-hour window the counts per region are unchanged — because the
events all fall within the same day — but each row now summarises six
hours rather than one. The counts are identical; the *meaning* of each
row is different. That is a good illustration of what windowing actually
controls.

### Step 7 — Try the `AfterCount` path

```bash
python project/streaming_pipeline.py \
    --input ./sample_data/events.ndjson \
    --output ./out/streaming_count \
    --window-seconds 3600 \
    --trigger-count 1000 \
    --allow_unsafe_triggers \
    2>&1 | grep -i "unsafe"
```

```text
WARNING apache_beam.transforms.core: GroupByKey: Unsafe trigger `AfterCount(1000)` detected (reason: MAY_FINISH). This is being allowed because --allow_unsafe_triggers is set. This could lead to missing or incomplete groups.
```

With `DISCARDING`, the window fires every 1000 elements and emits deltas.
The final total is the same, but the output is a stream of partial rows
rather than one row per region.

### Step 8 — Run the windowing tests

```bash
python -m pytest project/tests/test_pipelines.py::TestWindowing -v
```

```text
platform darwin -- Python 3.13.16, pytest-9.2.0
collected 3 items

test_accumulating_mode_emits_running_total PASSED
test_discarding_mode_emits_running_total PASSED
test_fixed_window_groups_by_time PASSED

3 passed
```

### Step 9 — Read the graph

```python
import apache_beam as beam
from apache_beam.io.textio import ReadFromText
from apache_beam.transforms.window import FixedWindows
from apache_beam.transforms.trigger import AccumulationMode, AfterWatermark

p = beam.Pipeline()
(
    p
    | "Read" >> ReadFromText("./sample_data/events.ndjson")
    | "Window"
    >> beam.WindowInto(
        FixedWindows(3600),
        trigger=AfterWatermark(),
        accumulation_mode=AccumulationMode.ACCUMULATING,
    )
)
print(p)
```

```text
<pipeline [
  Read[None],
  Window[None]>] at 0x...>
```

### Step 10 — Inspect the effective windowing

```python
import apache_beam as beam
from apache_beam.transforms.window import FixedWindows
from apache_beam.transforms.trigger import AccumulationMode, AfterWatermark

with beam.Pipeline() as p:
    windowed = (
        p
        | "Create" >> beam.Create([1, 2, 3])
        | "Window"
        >> beam.WindowInto(
            FixedWindows(3600),
            trigger=AfterWatermark(),
            accumulation_mode=AccumulationMode.ACCUMULATING,
        )
    )
    print(windowed.windowing)
```

The output includes the trigger, the accumulation mode, the window function
and the allowed lateness — the complete windowing specification in one
object.

---

## 🛠️ Common Errors and Fixes

### `AttributeError: module 'apache_beam.transforms.combiners' has no attribute 'Sum'`

There is no `combiners.Sum`. Use the builtin:

```python
sums = keyed | "SumValues" >> beam.CombinePerKey(sum)
```

### `TypeError: '_ChainedPTransform' object is not iterable`

This is what the `--use-test-stream` mode currently produces. The helper
returns a `TestStream` PTransform instead of a PCollection, and
`CoGroupByKey` cannot consume a transform.

The fix is to configure the `TestStream` and then apply it to the
pipeline, passing the resulting PCollection as `events`:

```python
stream = TestStream()
stream.add_elements([TimestampedValue(("EMEA", 10.0), Timestamp(BASE + 0))])
stream.advance_watermark_to(Timestamp(BASE + 120))
stream.add_elements([TimestampedValue(("EMEA", 5.0), Timestamp(BASE + 5))])

events = pipeline | "ReadTestStream" >> stream
```

### `TypeError: Cannot interpret ('EMEA', 10.0) <class 'tuple'> as Timestamp`

The `TimestampedValue` constructor takes **value first, timestamp second**:

```python
TimestampedValue(value, timestamp)
```

not `TimestampedValue(timestamp, value)`.

### `ValueError: GroupByKey: Unsafe trigger: \`AfterWatermark()\` may lose data. Reason: MAY_FINISH`

You asked for allowed lateness without the opt-in. Either pass
`--allow_unsafe_triggers`, or let the project fall back to zero. See
chapter 7.5.

### `WARNING __main__: allowed_lateness=300s requires --allow_unsafe_triggers; falling back to 0s so the pipeline stays safe`

This is the guard working as designed, not an error. It means your
requested lateness was **not** applied. If you meant it, add the flag.

### The output is empty

Four likely causes:

1. **The input file does not exist.** Run
   `python resources/sample_data.py --output-dir ./sample_data` first.
2. **You filtered everything out.** Check that the events have the fields
   `parse_event_payload` requires: `event_id`, `user_id`, `event_ts`,
   `event_type`, `product_id`, `region`, `value`.
3. **The sink wrote a shard with a different name.** `WriteToText` writes
   `streaming00000of00001`. Use `cat ./out/streaming*`.
4. **You forgot the sink.** A PCollection with no consumer does no work.

### The region rows are in a different order each run

That is expected. The runner does not guarantee key order. Sort before
comparing, and never write a test that depends on the order.

### The output has more than four rows

You probably ran the pipeline twice into the same output prefix. The sink
appends; it does not overwrite. Delete the old files first, or use a fresh
prefix.

### `panic in ElementManager.Bundles watermark evaluation goroutine`

The Prism runner (`--runner DirectRunner` in Beam 2.60+) does not support
`AfterWatermark`. Use `BundleBasedDirectRunner`, which is the project
default.

### The Pub/Sub job starts and produces nothing

Check, in order:

1. Is `--streaming` on the `gcloud dataflow jobs run` command? Without it
   the job launches in batch mode and never finishes.
2. Is the topic actually receiving messages? Publish one and check the
   subscription's backlog.
3. Are the messages in the format `parse_event_payload` expects? A
   malformed payload is logged and dropped, not fatal.

---

## 💡 Production Notes

- **The count is the number people check.** Revenue totals drift slowly and
  are easy to explain away; an event count that is off by 3% is obvious and
  alarming. Build the count invariant into a test — sum the per-region
  counts and assert it equals the input count. If you add deduplication,
  the invariant becomes "the deduplicated count", which you compute
  independently.

- **At-least-once means your counts are wrong until you deduplicate.**
  Pub/Sub redelivers after a worker reschedule, a subscription ack
  timeout, and a checkpoint rollback. In a job with one-minute windows and
  frequent rescheduling, expect a low-single-digit percentage of
  duplicates. On a revenue dashboard that is unacceptable, and it is
  invisible without an independent check like the one in Step 4.

- **File sinks and streaming jobs do not mix.** `WriteToText` finalises
  shards when the job ends. A streaming job that runs for a month
  finalises its shards when you cancel it — after a month. Anything
  downstream of the pipeline sees nothing for the whole time. Write to
  BigQuery, Pub/Sub, or Kafka, not to files.

- **The window boundaries belong in the output.** A row saying
  `EMEA,5099,302548.0` is useless to a consumer six months later. Include
  `window_start` and `window_end` as ISO-8601 timestamps. This is a
  two-line change and it saves a great deal of confusion.

- **One region per key is a small cardinality. That will change.** The
  current key is `region`, giving four keys and no skew. A production
  version keyed by `(region, product_id)` gives twenty thousand keys and
  a long tail. Watch the hot-key behaviour — the batch chapter covers
  skew, and the same problem applies here with the added cost of
  per-window state.

- **Watch the watermark age metric from day one.** It is the earliest
  signal that something is wrong. A watermark age that grows without bound
  means the pipeline is not closing windows, and the dashboard is stale
  even though nothing is failing. Set the alert at the level where the
  business would notice — for an hourly revenue dashboard, a watermark age
  above two hours is a page.

- **The `--allow_unsafe_triggers` decision belongs in the launch
  configuration, reviewed and documented.** In the flex-template
  deployment, it would be an explicit argument in the `gcloud dataflow
  jobs run` command with a comment explaining what late-data risk the team
  has accepted and why.

- **Cost: the window size and the lateness budget are the two dials.**
  Halving the window doubles the number of open windows and roughly
  doubles the state. A lateness budget of 24 hours multiplies the state by
  25. Both are cheap in a batch job and expensive in a streaming job that
  runs for a month. Model the state before you deploy, not after.

---

## 🔑 Key Takeaways

- The pipeline graph is **read → parse → validate → window → key →
  count + sum → `CoGroupByKey` → format → write**.
- The key is **`(region, value)`** — a standard Beam KV pair. The *window*
  is added by Beam automatically, so the effective grouping key is
  `(region, window)`.
- The value must be **numeric** because `Count.PerKey()` ignores it but
  `CombinePerKey(sum)` needs to add it. There is **no `beam.combiners.Sum`**.
- Two aggregations over one keyed PCollection are merged with
  **`CoGroupByKey`**, which preserves the windowed key.
- **Trigger selection**: `--trigger-count 0` → `AfterWatermark` with
  `ACCUMULATING` (exact, final); `--trigger-count N` → `AfterCount` with
  `DISCARDING` (partial, deltas).
- The **`allowed_lateness` guard** falls back to zero with a warning
  unless `--allow_unsafe_triggers` is set.
- **Three input modes**: bounded file (no GCP), `TestStream`
  (deterministic watermark control), and real Pub/Sub (production).
- The verified local output is **APAC 4885/291314.62, EMEA 5099/302548.0,
  LATAM 4979/299522.51, AMER 5037/302651.93** — the counts sum to 20,000,
  matching the generator exactly.
- Deployment is a **Dataflow streaming flex template**, and `--streaming`
  is mandatory on the `gcloud dataflow jobs run` command.
- Honest limits: no watermark hold-back, no deduplication in the graph,
  static currency assumptions, and `WriteToText` is the wrong sink for a
  streaming job.

---

## 📚 Practice Exercises

1. **Add the window boundaries to the output.** Change `to_window_row` to
   emit `window_start,window_end,region,event_count,total_value`. You
   will need the window, so use a `DoFn` with `beam.DoFn.WindowParam`
   rather than a `Map`. Verify the output still passes the invariant check
   from Step 4.

2. **Add deduplication.** Apply `dedup_key` from `project/transforms.py`
   upstream of the windowing, using a `SetStateSpec` to remember recently
   seen `event_id`s. Then publish a duplicate message into a Pub/Sub
   topic and confirm the count does **not** increase. Note the
   unbounded-state problem this introduces and how you would bound it.

3. **Compare the two aggregations.** Build a second pipeline that uses a
   single `CombineFn` producing `{"event_count": n, "total_value": sum}`
   instead of two combiners plus `CoGroupByKey`. Compare the outputs and
   the number of shuffle stages in the job graph. Which is better, and
   under what circumstances?

4. **Prove the `CoGroupByKey` merge.** Write a test that produces a count
   stream and a sum stream with *different* key sets, and shows what
   `CoGroupByKey` does when one side is empty. Then explain why the
   merge function in the project initialises both totals to zero rather
   than assuming both sides are present.

5. **Measure the cost of a lateness budget.** Run the pipeline with
   `--allowed-lateness-seconds 86400 --allow_unsafe_triggers` and compare
   the bundled data size and the wall-clock runtime against the zero-
   lateness run. Explain the relationship to the live-state multiplier
   from chapter 7.5.

6. **Design the production sink.** Write the BigQuery DDL for the
   production table, including the partition on `window_start` and the
   clustering columns. Then write the `beam.io.WriteToBigQuery` call with
   the disposition that makes re-firing windows correct, and explain why
   `WRITE_APPEND` alone is not sufficient.

---

## 📖 Further Reading

- Apache Beam: A Tour of Windowing — https://beam.apache.org/documentation/programming-guide/#windowing
- Apache Beam: CoGroupByKey — https://beam.apache.org/documentation/programming-guide/#combine
- Apache Beam Python SDK: `CoGroupByKey` API reference — https://beam.apache.org/releases/pydoc/current/apache_beam.transforms.core.html#apache_beam.transforms.core.CoGroupByKey
- Google Cloud Dataflow: Pub/Sub to BigQuery streaming patterns — https://cloud.google.com/dataflow/docs/guides/streaming/pubsub-to-bigquery
- Google Cloud Dataflow: Building a streaming pipeline — https://cloud.google.com/dataflow/docs/guides/streaming/creating-a-streaming-pipeline
- Google Cloud Dataflow: Dataflow flex templates — https://cloud.google.com/dataflow/docs/guides/templates/overview
- Google Cloud Pub/Sub: Message delivery and ordering — https://cloud.google.com/pubsub/docs/overview#delivery
