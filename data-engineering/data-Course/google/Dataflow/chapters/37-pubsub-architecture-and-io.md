# 7.1 — Pub/Sub Architecture & I/O

> **Section 7 · Streaming Pipelines · Lecture 7.1 · 6:30**

## 🎯 What you will learn

- How Pub/Sub's topic / subscription / snapshot / ack model actually works
- Why at-least-once delivery is the normal operating mode, not an error condition
- The ack deadline, the 10-minute maximum, and what happens when it expires
- Exactly-once delivery: what Pub/Sub offers, and why `ReadFromPubSub` does not use it
- The real `ReadFromPubSub` parameters — `topic`, `subscription`, `id_label`, `with_attributes`, `timestamp_attribute`
- How Beam's `id_label` deduplication works, and the window-scoped caveat that surprises people
- Subscription as a queue vs subscription as a log — and why two jobs on one subscription split messages
- The dead-letter topic pattern for messages that fail every retry
- `WriteToPubSub` and its `id_label` attribute
- The Pub/Sub cost model, and why it makes the "topic vs file" choice a cost decision too
- Why a `gs://` file source is a **bounded** stream and Pub/Sub is **unbounded**

---

## 🧠 Concept

### The vocabulary

Pub/Sub is Google Cloud's managed publish/subscribe messaging service. It is
the default way to get data *into* Dataflow, and it is deliberately boring
in the way good infrastructure is boring: you publish messages, you consume
them, and the service handles the rest.

Four nouns carry the whole model:

| Noun | What it is | Lifetime |
|---|---|---|
| **Topic** | the named stream you publish to | permanent |
| **Subscription** | a named cursor attached to a topic | permanent, until deleted |
| **Message** | an opaque byte payload plus attributes | up to 7 days retained |
| **Snapshot** | a saved position in a subscription's backlog | permanent, until deleted |

A topic is a mailbox. A subscription is a **cursor into that mailbox**. Two
subscriptions on the same topic each receive a full copy of every message.
This single sentence explains most of Pub/Sub's behaviour, including the
failure mode that costs people an afternoon: **two Dataflow jobs reading the
same subscription do not each get every message — they split the messages
between them.**

### The ack model

When a subscriber pulls a message, Pub/Sub does not delete it. It marks it
"in flight" and starts a countdown: the **ack deadline**. If the subscriber
calls `ack()`, the message is removed from the subscription's backlog
forever. If the subscriber does *not* ack within the deadline, the message is
**redelivered**.

The ack deadline is:

- **Default 10 seconds.** Short enough to fail fast, long enough for a
  normal processing step.
- **Maximum 10 minutes.** You cannot extend it beyond this. This is a hard
  limit in the Pub/Sub service, not a Beam limitation.
- **Automatically extended** while the subscriber is streaming messages, as
  long as the client library is alive and making progress. You do not have to
  renew it by hand in the common case.

The important consequence: **the ack deadline is a timeout on your whole
processing step, not on the network call.** If your `DoFn` takes 12 minutes,
you have already failed, and the message will be redelivered — possibly
while your first processing run is still finishing on another worker.

That is the single most common source of "why did I see this event three
times?" in production, and it is why the course pipeline parses and
aggregates rather than doing long per-message work.

### At-least-once delivery is normal, not an error

Pub/Sub's delivery guarantee is **at-least-once**. The service promises to
deliver every message *at least* one time. It makes no promise about
delivery *exactly* once.

Redelivery happens for ordinary reasons, none of which are bugs:

| Cause | What happens |
|---|---|
| Subscriber crashes before acking | Message is redelivered after the deadline |
| Worker is preempted (Dataflow autoscaling) | In-flight messages are redelivered |
| Network partition | Client cannot ack; message is redelivered |
| Ack deadline expires on a slow step | Message is redelivered |
| You stop a Dataflow job mid-bundle | Unacked messages return to the backlog |

So if you see the same message twice, **you have not lost data** — you have
used the at-least-once guarantee exactly as designed. The pipeline must be
**idempotent**: processing the same message twice must produce the same
result as processing it once.

For the course's clickstream events, idempotency is straightforward: the
event carries an `event_id`, and the aggregation is a sum. Adding the same
event twice is wrong, but the fix — dedup by `event_id` — is a business
decision, not a transport one. The `transforms.py` module gives you the key:

```python
from transforms import dedup_key

dedup_key({"event_id": "e00000123", "user_id": "u000456"})
# 'e00000123'
```

The docstring is worth repeating verbatim, because it is the rule:

> The deduplication key must be derived from the payload's own identity,
> never from arrival time.

### Exactly-once delivery — and why Beam does not use it

Pub/Sub *does* have an exactly-once delivery feature. It is real, and it is
useful. It works by combining two mechanisms:

1. **The publisher requests a deduplication key.** Pub/Sub rejects a publish
   whose key it has seen before, within a **5-minute deduplication window**.
2. **The subscriber uses a pull client with exactly-once enabled.** The
   client tracks in-flight message IDs and, on reconnect, tells the service
   exactly which messages it already received but never acked — so the
   service redelivers only the ones truly not yet processed.

The interaction is the point: exactly-once is not a property of the message
store alone. It requires **both** ends to participate. A publisher that
does not send a deduplication key gets at-least-once behaviour even if the
subscriber has exactly-once enabled.

Now the part that matters for this course:

**Beam's `ReadFromPubSub` uses the streaming pull API and is at-least-once.**
It does not enable Pub/Sub's exactly-once delivery. You cannot turn it on
from the `ReadFromPubSub` parameters. If you need exactly-once semantics,
you either implement idempotency downstream or use a different reader.

This is a deliberate design choice on Beam's part. Exactly-once delivery
requires the subscriber to persist its in-flight state durably, and Beam's
Dataflow runner already checkpoints its own window state. Adding a second,
independent exactly-once mechanism would mean two sources of truth about
what has been processed — and two ways to disagree.

So the practical rule is: **design for at-least-once, make the pipeline
idempotent, and use `id_label` to make Beam's own deduplication do the
heavy lifting.**

### The real `ReadFromPubSub` parameters

This is where guessing goes wrong. The actual signature in apache-beam
2.77 is:

```text
ReadFromPubSub(
    topic: Optional[str] = None,
    subscription: Optional[str] = None,
    id_label: Optional[str] = None,
    with_attributes: bool = False,
    timestamp_attribute: Optional[str] = None,
)
```

Verify it yourself against whatever version you have installed:

```bash
.venv/bin/python -c "
import inspect
from apache_beam.io.gcp.pubsub import ReadFromPubSub
print(inspect.signature(ReadFromPubSub.__init__))
"
```

Two things to note immediately, because both differ from what people
commonly assume:

- The timestamp parameter is **`timestamp_attribute`**, *not*
  `with_timestamp_attributes`. The `with_attributes` parameter is a
  separate boolean that controls whether elements come out as
  `PubsubMessage` objects (payload plus attributes) or as raw `bytes`.
- `topic` and `subscription` are **mutually exclusive**. Beam raises
  `ValueError` if you pass both, or neither:

```text
ValueError: Only one of topic or subscription should be provided.
ValueError: Either a topic or subscription must be provided.
```

| Parameter | Meaning |
|---|---|
| `topic` | `projects/<project>/topics/<topic>`. If given, `subscription` must be `None`. |
| `subscription` | `projects/<project>/subscriptions/<sub>`. If given, `topic` must be `None`. |
| `id_label` | The **Pub/Sub attribute name** to use as a unique record identifier for deduplication. |
| `with_attributes` | `True` → elements are `PubsubMessage`; `False` (default) → elements are `bytes`. |
| `timestamp_attribute` | The message attribute whose value becomes the element timestamp. `None` → the publish time. |

The `timestamp_attribute` value may be either:

- a number of **milliseconds since the Unix epoch**, or
- an **RFC 3339 string** in UTC, e.g. `2026-01-15T10:05:00Z`. The
  sub-second component is optional; digits below milliseconds are ignored.

### `id_label` — the deduplication detail people get wrong

Setting `id_label` tells Beam to use the value of the named Pub/Sub
**attribute** as the record's identity, and to deduplicate on that value.
The Beam documentation says:

> When specified, the value of this attribute (which can be any string that
> uniquely identifies the record) will be used for deduplication of messages.
> If not provided, we cannot guarantee that no duplicate data will be
> delivered on the Pub/Sub stream. In this case, deduplication of the
> stream will be strictly best effort.

The subtlety, and the reason this chapter spends a paragraph on it:
**Beam's deduplication is window-scoped.** The deduplication state is held
per window, and the window of a message is determined by the element's
timestamp. Two consequences follow:

1. The **same `id_label` value in two different windows is not a
   duplicate.** If your `id_label` is a per-day identifier and your windows
   are hourly, you get one copy per hour, not one copy ever.

2. Deduplication only works if the duplicate arrives **in the same window**.
   A redelivery that crosses a window boundary will be counted twice.

This is why `id_label` must point at an attribute that identifies the
*record*, not the *arrival*. If the producer sets `id_label` to a fresh
UUID on every publish attempt, dedup does nothing — every redelivery looks
unique.

In practice, `id_label` is most useful when it carries the **business key**
of the event: the `event_id` in the course's clickstream payload. The
producer must copy it into a Pub/Sub attribute at publish time.

### Subscription as a queue vs subscription as a log

This is the mental model that prevents the most expensive class of
Pub/Sub bug.

**As a queue.** A subscription is a queue with multiple consumers. Each
message goes to exactly one consumer. If you run two Dataflow jobs against
the same subscription, they **split the load** — job A gets some messages,
job B gets the others, and neither job sees the whole stream.

This is a feature, not a bug. It is how you scale a consumer horizontally.
If you run ten workers of the same Dataflow job, they share one subscription
and the messages are distributed across them — that is exactly what you
want.

**As a log.** If you want every consumer to see every message, you give
each consumer **its own subscription** on the same topic. Topic A with
subscription B and subscription C delivers each published message to both.

The mistake people make is expecting log semantics from a single shared
subscription. The failure is usually noticed as: *"the pipeline ran fine,
but the numbers are half of what they should be."* The pipeline is fine.
The two jobs are each correctly processing half the stream.

The rule to remember:

> **One subscription, one logical consumer group.** Scale by adding workers
> to the job, not by adding jobs.

If you genuinely need two independent consumers of the same data — say an
audit trail alongside a live dashboard — create two subscriptions and give
each its own job.

### The dead-letter topic

Pub/Sub has no built-in dead-letter queue. If a message cannot be
processed, the subscriber's only choices are to drop it or to keep retrying
it forever. Both are bad: the first loses data, the second blocks the
subscription's backlog.

The standard pattern is to build the dead-letter queue yourself, using
Pub/Sub's own primitives:

```text
                 ┌──────────────────────┐
  publish ──────▶│  main topic          │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │  main subscription   │
                 └──────────┬───────────┘
                            │
                     processing fails?
                       ┌────┴────┐
                     yes         no
                       │          │
                       ▼          ▼
             ┌─────────────────┐  ack → done
             │  dead-letter    │
             │  topic          │
             └────────┬────────┘
                      │
                      ▼
             ┌─────────────────┐
             │  dead-letter    │
             │  subscription   │
             └─────────────────┘
```

The mechanics are: **do not ack the message**. Instead, publish it to the
dead-letter topic, then ack the original. If the process dies between the
publish and the ack, the original is redelivered and the dead-letter topic
gets a second copy — which is why the dead-letter publish should be
idempotent, or the DLQ message should carry the original's `message_id` so
consumers can dedup.

The alternative is to **nack** the message (Pub/Sub's explicit "I did not
process this" signal). A nacked message is redelivered immediately, with no
deadline wait, and it counts against the subscription's redelivery budget.
That is right for a *transient* failure and wrong for a *permanent* one —
a malformed payload will never parse, and nacking it forever stalls the
subscription.

The rule: **nack for transient, dead-letter for permanent.** The course's
`streaming_pipeline.py` chooses a third option for its malformed-payload
case: log and drop.

```python
def parse_event(payload: bytes) -> dict:
    """Parse one Pub/Sub payload into an event dict.

    Malformed payloads are dropped rather than failing the bundle. A single
    bad message should not stop a streaming pipeline.
    """
    try:
        return parse_event_payload(payload)
    except ValueError as exc:
        log.warning("dropping malformed event: %s", exc)
        return None
```

That is defensible for a course, and it is what the streaming pipeline does.
In production you would normally route it to a dead-letter topic instead —
the pattern above — so the data is recoverable rather than merely logged.

### `WriteToPubSub` and `id_label` on the write side

`WriteToPubSub` publishes elements to a topic. Its signature in 2.77:

```text
WriteToPubSub(
    topic: str,
    with_attributes: bool = False,
    id_label: Optional[str] = None,
    timestamp_attribute: Optional[str] = None,
    publish_with_ordering_key: bool = False,
)
```

The `id_label` parameter here is the **dual** of the read-side one. The
documentation says:

> If set, will set an attribute for each Cloud Pub/Sub message with the
> given name and a unique value. This attribute can then be used in a
> `ReadFromPubSub` PTransform to deduplicate messages.

So the round trip is:

1. **Write** with `id_label="event_id"` — Beam sets an attribute named
   `event_id` on each outgoing message, whose value is unique per message.
2. **Read** with `id_label="event_id"` — Beam uses that attribute's value
   to deduplicate redeliveries.

The attribute name is the same string on both sides, but the *semantics* are
different: on write it is "put this value in an attribute"; on read it is
"read this attribute and dedup on it". Beam's write-side `id_label` does not
let you choose the value — it generates a unique one. If you need the
business key (not a random id) to be the dedup key, you must set the
attribute yourself using `with_attributes=True` and a `PubsubMessage`.

One practical caveat: `id_label` on the write side is **not supported by
the DirectRunner** for Pub/Sub writes — you will only exercise it against
Dataflow.

### The cost model

Pub/Sub pricing has two components, and both are worth knowing because
they change design decisions:

| Component | Unit price (US, list) | Notes |
|---|---|---|
| Volume | **$0.06 per GiB** of message data ingested | The dominant cost for large payloads |
| Throughput | **$0.05 per million operations** | Publish + subscribe are separate operations |

A "GB ingested" is measured on the **message payload**, not the wire size,
and it is charged per *delivery* — so a topic with three subscriptions
charges you three times for the same published data.

Put a number on it. A clickstream event with a 500-byte JSON payload:

- 1 million events ≈ 0.5 GiB ≈ **$0.03** of volume
- 1 million publishes + 1 million subscribes ≈ 2 million operations ≈ **$0.10**
- Total ≈ **$0.13 per million events**, at one subscription

At 100 million events per day across three subscriptions, that is roughly
**$39/day** in Pub/Sub charges alone — before Dataflow worker time, which
dominates once the pipeline does anything non-trivial.

Two cost facts that surprise people:

- **A subscription multiplies the volume charge.** If you attach a
  "just for debugging" subscription to a busy topic, you have doubled your
  Pub/Sub bill. Debug subscriptions should be attached and detached, not
  left running.
- **Dead-letter topics cost money too.** A poison-message loop that
  redelivers forever burns both Pub/Sub and Dataflow worker time. The
  dead-letter pattern above exists partly to cap that.

### `gs://` is bounded; Pub/Sub is unbounded

This distinction is the foundation of everything in Module 7, and it is
worth stating precisely because the two are so easy to conflate.

| | `gs://` file source | Pub/Sub topic |
|---|---|---|
| Cardinality | **Bounded** — finite, known set of files | **Unbounded** — no end |
| When it ends | When the last byte is read | When you cancel the job |
| Watermark | Advances to `+inf` at the end | Advances as data arrives |
| Window closure | Every window closes at the end | Windows close as the watermark passes them |
| Runner mode | Batch | Streaming |
| Output | One complete result | Incremental, partial results |
| Job termination | Automatic | Manual (or by a deadline) |

A `gs://` path is a **snapshot**. It has a beginning and an end, and Beam
knows it. When the source is exhausted, Beam advances the watermark to
`+inf`, which closes every window, which fires every trigger, which
produces the final output. The pipeline then exits successfully.

A Pub/Sub subscription is a **stream**. It never ends. The watermark advances
only as new data arrives, so windows close only when the stream has genuinely
moved past them. The job runs until you cancel it, and the output is a
series of partial results that get more complete over time.

This is why the course's `streaming_pipeline.py` treats them as
interchangeable in one code path: the *logic* is identical, and only the
source differs.

```text
events = pipeline | "ReadPubSub" >> ReadFromPubSub(
    topic=args.topic, subscription=args.subscription
)
...
events = pipeline | "ReadEvents" >> ReadFromText(args.input)
```

The windowing, the trigger, the aggregation, the output format — all the
same. What changes is whether the job terminates.

### One more thing about timestamps: `timestamp_attribute` vs re-stamping

`ReadFromPubSub` with `timestamp_attribute` set uses the named attribute as
the element timestamp. With it unset, the element timestamp is the
**message's publish time**.

Publish time is *not* event time. A mobile client that was offline for two
minutes publishes a click with an event time of two minutes ago, and Pub/Sub
stamps it with *now*. If you window on publish time, that click lands in
the wrong window. This is the subject of chapter 7.2, and the short version
is: **window on the event's own timestamp, and re-stamp explicitly if the
source did not carry it.**

---

## 🛠️ Hands-On

This hands-on runs entirely on your machine. It builds the same source
abstraction you would use against real Pub/Sub, but backs it with a local
file — and then shows what changes when you point it at a real topic.

### Step 1 — Generate the sample data

```bash
cd data-engineering/data-Course/google/Dataflow
python resources/sample_data.py --output-dir ./sample_data
```

This writes `sample_data/events.ndjson`, one JSON clickstream event per line.

### A note on the runner

Every command below builds its options with the course's own helper:

```python
from beam_options import build_options

options = build_options([])
```

`build_options` defaults to `BundleBasedDirectRunner` — the classic,
pure-Python runner — rather than Beam 2.60+'s newer Go-based
`DirectRunner` (the "Prism" runner). Prism does not yet support every
trigger and windowing combination: it panics on the `+inf` watermark
evaluation that happens at the end of a windowed batch run. The classic
runner supports the full feature set, which is what a course needs.

The `project/` directory has to be importable, so set `PYTHONPATH`:

```bash
export PYTHONPATH="$PWD/project"
```

### Step 2 — The source abstraction

The pattern is: a function that returns a `PCollection` of raw payloads,
chosen by environment. The rest of the pipeline cannot tell the difference.

```python
import os

import apache_beam as beam
from beam_options import build_options
from apache_beam.io.gcp.pubsub import ReadFromPubSub
from apache_beam.io.textio import ReadFromText


def build_source(pipeline):
    """Return a PCollection of raw event payloads.

    The environment decides where the bytes come from. Everything
    downstream is identical either way.
    """
    topic = os.environ.get("PUBSUB_TOPIC")
    subscription = os.environ.get("PUBSUB_SUBSCRIPTION")

    if topic:
        # A real topic. `id_label` names the Pub/Sub attribute that
        # carries the event's business key, so Beam can deduplicate
        # redeliveries.
        return pipeline | "ReadFromPubSub" >> ReadFromPubSub(
            topic=topic,
            subscription=subscription,
            id_label="event_id",
        )

    # A bounded local file. Same code path, finite input.
    return pipeline | "ReadFromText" >> ReadFromText(
        "./sample_data/events.ndjson"
    )
```

Run it against the file:

```bash
python -c "
import apache_beam as beam
from beam_options import build_options
from streaming_pipeline import build_source

with beam.Pipeline(options=build_options([])) as p:
    events = build_source(p)
    (
        events
        | 'Count' >> beam.combiners.Count.PerKey()
        | 'Print' >> beam.Map(lambda kv: kv[1])
    )
" 2>&1 | grep -v "INFO\|WARNING"
```

> **Note.** The `Count.PerKey()` above uses the *global* window, because
> `WindowInto` has not been applied. That is exactly what chapter 7.3 is
> about: `WindowInto` is not optional, and it must come before the
> aggregation.

### Step 3 — The same pipeline with a real Pub/Sub topic

If you have a GCP project, this is the whole path from nothing to a live
stream.

Create the topic and a subscription:

```bash
gcloud pubsub topics create YOUR_TOPIC --project YOUR_PROJECT_ID
gcloud pubsub subscriptions create YOUR_SUBSCRIPTION \
    --topic YOUR_TOPIC \
    --ack-deadline-seconds 30 \
    --project YOUR_PROJECT_ID
```

> **Always create the subscription explicitly.** If you point Beam at a
> topic with no subscription, Beam creates a temporary one and deletes it
> when the job ends. That works, but it means the backlog is empty when
> the job starts, and any messages published in the meantime are lost to
> you. A named subscription keeps the backlog.

Publish some messages:

```bash
gcloud pubsub topics publish YOUR_TOPIC \
    --message='{"event_id":"e1","user_id":"u1","event_ts":"2026-01-15T10:05:00+00:00","event_type":"click","product_id":"p1","region":"EMEA","value":10.0}' \
    --project YOUR_PROJECT_ID
```

Now run the same pipeline against it:

```bash
export PUBSUB_TOPIC="projects/YOUR_PROJECT_ID/topics/YOUR_TOPIC"
export PUBSUB_SUBSCRIPTION="projects/YOUR_PROJECT_ID/subscriptions/YOUR_SUBSCRIPTION"

python -c "
import apache_beam as beam
from beam_options import build_options
from streaming_pipeline import build_source

with beam.Pipeline(options=build_options([])) as p:
    events = build_source(p)
    (
        events
        | 'Print' >> beam.Map(lambda payload: payload[:60])
    )
" 2>&1 | grep -v "INFO\|WARNING"
```

The job now **does not exit**. It is waiting for more messages, because a
Pub/Sub source is unbounded. Ctrl-C stops it; the unacked message returns
to the backlog and will be redelivered next time.

### Step 4 — Publishing with a deduplication attribute

To make `id_label` useful, the producer must put the business key into a
Pub/Sub attribute. Here is a small publisher script:

```python
import json
from google.cloud import pubsub_v1

TOPIC = "projects/YOUR_PROJECT_ID/topics/YOUR_TOPIC"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(TOPIC)

payload = {
    "event_id": "e00000042",
    "user_id": "u000001",
    "event_ts": "2026-01-15T10:05:00+00:00",
    "event_type": "click",
    "product_id": "p0001",
    "region": "EMEA",
    "value": 42.0,
}

future = publisher.publish(
    topic_path,
    json.dumps(payload).encode("utf-8"),
    event_id="e00000042",
)
print(f"published {future.result()}")
```

Note `event_id="e00000042"` — that is the attribute. Now Beam's reader can
deduplicate on it:

```python
events = pipeline | "ReadFromPubSub" >> ReadFromPubSub(
    subscription="projects/YOUR_PROJECT_ID/subscriptions/YOUR_SUBSCRIPTION",
    id_label="event_id",
)
```

### Step 5 — Write back out to a topic

The other direction. `WriteToPubSub` publishes each element as a message.

```python
import apache_beam as beam
from beam_options import build_options
from apache_beam.io.gcp.pubsub import WriteToPubSub

with beam.Pipeline(options=build_options([])) as p:
    (
        p
        | "Read" >> beam.io.ReadFromText("./sample_data/events.ndjson")
        | "ExtractId" >> beam.Map(lambda line: line.split('"event_id":"')[1].split('"')[0])
        | "WriteToTopic" >> WriteToPubSub(
            topic="projects/YOUR_PROJECT_ID/topics/YOUR_TOPIC",
            id_label="event_id",
        )
    )
```

The `id_label` here sets an **attribute** named `event_id` on each outgoing
message. Note that this write-side `id_label` is not supported by the
DirectRunner — run this one on Dataflow.

### Step 6 — Use the course streaming pipeline

The real pipeline already wires the source selection for you:

```bash
python project/streaming_pipeline.py --input ./sample_data/events.ndjson
```

And with a topic:

```bash
python project/streaming_pipeline.py \
    --topic YOUR_TOPIC \
    --subscription YOUR_SUBSCRIPTION \
    --project YOUR_PROJECT_ID \
    --staging_location gs://YOUR_BUCKET/dataflow/staging \
    --temp_location gs://YOUR_BUCKET/dataflow/temp
```

Note the trigger-selection logic in `streaming_pipeline.py`. It has two
paths, and the choice is deliberate:

```python
if trigger_count:
    trigger = AfterCount(count=trigger_count)
    accumulation_mode = AccumulationMode.DISCARDING
else:
    trigger = AfterWatermark()
    accumulation_mode = AccumulationMode.ACCUMULATING
```

`AfterCount` is never safe — a window can close while elements are still
in flight — and so is any trigger combined with non-zero allowed lateness.
The pipeline therefore falls back to the safe `AfterWatermark` path unless
the caller explicitly opts in with `--allow_unsafe_triggers`. Chapter 7.4
covers why this matters.

---

## 🛠️ Common Errors and Fixes

### `ValueError: Only one of topic or subscription should be provided.`

You passed both `topic` and `subscription` to `ReadFromPubSub`. They are
mutually exclusive.

```python
# wrong
ReadFromPubSub(topic="projects/p/topics/t", subscription="projects/p/subscriptions/s")

# right — pick one
ReadFromPubSub(topic="projects/p/topics/t")
ReadFromPubSub(subscription="projects/p/subscriptions/s")
```

### `ValueError: Either a topic or subscription must be provided.`

You passed neither. If you meant to read a topic and let Beam create a
temporary subscription, pass the `topic` and leave `subscription=None`.

### `TypeError: ReadFromPubSub() got an unexpected keyword argument 'with_timestamp_attributes'`

The parameter does not exist. The real name is **`timestamp_attribute`**,
and it takes the *name of a message attribute*, not a boolean.

```python
# wrong
ReadFromPubSub(topic=t, with_timestamp_attributes=True)

# right
ReadFromPubSub(topic=t, timestamp_attribute="event_ts")
```

The `with_attributes` parameter does exist, but it is a different thing
entirely: it controls whether elements come out as `PubsubMessage` objects
or as raw `bytes`.

### `TypeError: 'bytes' object is not subscriptable` in your parsing code

You set `with_attributes=True` on the reader but still treat the element as
bytes — or the reverse. With `with_attributes=True`, elements are
`PubsubMessage` objects and you must read `element.data` for the payload:

```python
def extract_payload(element):
    data = element.data if hasattr(element, "data") else element
    return parse_event_payload(data)
```

### `RuntimeError: Transform name is already used`

Two transforms in the same pipeline share a label. In a source-selection
helper like `build_source`, give each branch a distinct label — "ReadFromPubSub"
and "ReadFromText" — because both branches are in the same pipeline scope
even though only one executes.

### `google.api_core.exceptions.NotFound: Could not find topic projects/.../topics/...`

The topic path is malformed. It must be the fully-qualified form:

```text
projects/<project-id>/topics/<topic-id>
```

Note the hyphen in `project-id`: it is a project **identifier**, not a
display name. `projects/My Project/topics/x` will not resolve.

### `google.api_core.exceptions.Forbidden: User ... does not have permission to perform pubsub.subscriptions.consume`

Your service account is missing the Pub/Sub subscriber role. The
`roles/pubsub.subscriber` role covers `consume` and `getSnapshot`. The
Dataflow service account needs it on both the topic and the subscription.

### The pipeline processes each message two or three times

This is Pub/Sub's at-least-once delivery working as designed, usually
because the processing step exceeded the ack deadline and the message was
redelivered. Three causes, in order of likelihood:

1. **The ack deadline is too short** for the work you are doing. Raise it
   with `gcloud pubsub subscriptions update YOUR_SUBSCRIPTION
   --ack-deadline-seconds 60`.
2. **The worker was preempted.** Dataflow preempted a worker mid-step.
3. **The pipeline is not idempotent.** Even with a correct ack deadline,
   a crash between "process" and "ack" will redeliver. Deduplicate on a
   business key.

If your aggregation is a sum, redelivery inflates it. Make the
aggregation idempotent — deduplicate by `event_id`, or use a set-based
accumulator rather than a plain sum.

### Two jobs, half the data each

You ran two Dataflow jobs against the same subscription. A subscription is a
**queue**: each message goes to exactly one consumer.

```bash
# Give each job its own subscription on the same topic.
gcloud pubsub subscriptions create YOUR_SUBSCRIPTION --topic YOUR_TOPIC
```

Give each job its own subscription if both need the full stream.

### The pipeline hangs and never produces output

If you are reading a Pub/Sub topic and the topic has no messages, the
pipeline is behaving correctly: an unbounded source has no "end", so the
job waits. Publish a message, or publish one *before* starting the job so
the backlog is non-empty.

```bash
gcloud pubsub topics publish YOUR_TOPIC --message='{"event_id":"e1"}' --project YOUR_PROJECT_ID
```

### `id_label` does not seem to deduplicate anything

Check three things in order:

1. **Is the attribute actually present on the message?** Publish with the
   attribute explicitly; `gcloud pubsub topics publish` will not set one
   for you.
2. **Are the duplicates landing in the same window?** Beam's dedup state
   is window-scoped. A duplicate that arrives after a window boundary is a
   new record as far as Beam is concerned.
3. **Does the attribute value identify the record?** If the producer
   generates a fresh UUID per publish, every redelivery looks unique.

---

## 💡 Production Notes

- **Design for at-least-once from day one.** Retrofitting idempotency into
  a pipeline that already counts things twice is a data-quality incident,
  not a refactor. Decide the dedup key before the first message flows.
- **Keep the ack deadline honest.** The deadline is a contract with
  Pub/Sub: "I will finish processing this message within N seconds, or
  send it to someone else." Set it to your real p99 processing latency
  plus a margin. Setting it to 10 minutes to be safe means a stuck
  message blocks the subscription for 10 minutes.
- **Never let a permanent failure nack forever.** A malformed payload that
  nacks will be redelivered immediately and indefinitely, growing the
  subscription's backlog and pinning worker capacity. Route it to a
  dead-letter topic and ack the original.
- **Budget for the redelivery rate.** For a healthy subscription, redelivery
  is well under 1% of messages. If you see 5%, the ack deadline is too
  short for your workload, or your pipeline is flapping. Both are worth an
  alert on: `subscription/num_undelivered_messages` climbing monotonically
  is the earliest signal that something is wrong.
- **Watch the subscription backlog, not just the pipeline.** The single
  most useful Pub/Sub metric is the undelivered message count. It rises
  when your pipeline is slower than your publishers, and it is the earliest
  warning before you start dropping or lagging.
- **One subscription per logical consumer.** Attach a debugging subscription
  only while you need it, and delete it when you are done — it bills for
  every message it receives.
- **Cost is dominated by volume × subscriptions.** At $0.06/GiB, a
  100 KiB message costs about $0.000006 per delivery. A million 100 KiB
  messages delivered to three subscriptions is roughly $0.18 in volume —
  small until you remember the Dataflow workers reading it are the
  expensive part.
- **Use message ordering keys only where you need them.** Ordering keys
  guarantee order *within a key* at the cost of throughput and head-of-line
  blocking. Ordering per user is reasonable; ordering the entire topic is
  usually a sign of a badly partitioned producer.
- **Dead-letter topics need their own alarm.** A DLQ with messages in it
  is a queue of problems nobody is solving. Alert on `num_undelivered_messages
  > 0` for the DLQ subscription.
- **Prefer `timestamp_attribute` over re-stamping when you can.** If the
  producer can put the event timestamp into a Pub/Sub attribute, the reader
  gets the right event time with zero pipeline work. Chapter 7.2 covers
  what to do when the producer cannot.

---

## 🔑 Key Takeaways

- Pub/Sub is **topic → subscription → message**, and the subscription is a
  **cursor**, not a copy. Two subscriptions on one topic each get every
  message; two jobs on **one** subscription split them.
- Delivery is **at-least-once**. Redelivery after a crash, a preemption, or
  an expired ack deadline is **normal operation**, not a bug. Design the
  pipeline to be idempotent.
- The ack deadline defaults to **10 seconds** and cannot exceed **10
  minutes**. It bounds your *whole* processing step, not just the network
  call.
- Pub/Sub's exactly-once delivery needs **both** ends to opt in, and Beam's
  `ReadFromPubSub` does **not** use it — the reader is at-least-once. Use
  `id_label` plus idempotent business logic instead.
- The real `ReadFromPubSub` parameters are `topic`, `subscription`,
  `id_label`, `with_attributes`, and **`timestamp_attribute`**. `topic` and
  `subscription` are mutually exclusive.
- Beam's `id_label` deduplication is **window-scoped**, so the duplicate
  must arrive in the same window, and the attribute must identify the
  *record*, not the arrival.
- A `gs://` source is **bounded** and closes every window at the end; a
  Pub/Sub source is **unbounded** and never finishes.
- Pub/Sub bills **per GiB ingested per delivery**, so every extra
  subscription multiplies the bill.

---

## 📚 Practice Exercises

1. **Prove the split.** Create two subscriptions on one topic, publish
   ten messages, then run two `ReadFromPubSub` pipelines concurrently and
   count how many messages each processed. Explain why the total is ten and
   not twenty. Then create a second subscription, attach a third pipeline,
   and show that the total is now twenty.

2. **Measure the redelivery rate.** Start a pipeline reading from
   `YOUR_SUBSCRIPTION`, publish 1,000 messages, then kill the job with
   Ctrl-C partway through. Restart it and count the total messages
   processed. The excess is your redelivery count — explain where each
   duplicate came from.

3. **Add a dead-letter topic.** Extend the `build_source` helper so that
   malformed payloads are published to a dead-letter topic instead of
   being logged and dropped. Use `WriteToPubSub` with `with_attributes=True`
   to carry the original `message_id` so the DLQ copy can be deduplicated.

4. **Benchmark the ack deadline.** Set the ack deadline to 10 seconds and
   to 60 seconds on two subscriptions. Run the same pipeline against each
   and compare the observed redelivery rate. Write down the p99 processing
   latency you measured and argue for the deadline you would actually set
   in production.

5. **Cost it.** Compute the monthly Pub/Sub bill for a pipeline ingesting
   200 million events per day at 600 bytes each, with two subscriptions.
   Then work out how much a third "debugging" subscription adds, and
   explain why you would attach and detach it rather than leave it running.

6. **Build the toggle.** Add a `--source` flag to `streaming_pipeline.py`
   that accepts `file`, `topic`, or `test`, and route to
   `ReadFromText`, `ReadFromPubSub`, or the `TestStream` builder
   accordingly. Keep the three labels distinct so no two branches collide.

---

## 📖 Further Reading

- Google Cloud Pub/Sub overview — https://cloud.google.com/pubsub/docs/overview
- Pub/Sub delivery guarantees — https://cloud.google.com/pubsub/docs/overview#delivery_guarantees
- Pub/Sub exactly-once delivery — https://cloud.google.com/pubsub/docs/exactly-once-delivery
- Pub/Sub subscription ack deadline — https://cloud.google.com/pubsub/docs/subscription-message-retention
- Beam's Pub/Sub I/O documentation — https://beam.apache.org/documentation/io/pubsub-io/
- Writing to Pub/Sub from Beam — https://beam.apache.org/documentation/io/pubsub-io/#write
