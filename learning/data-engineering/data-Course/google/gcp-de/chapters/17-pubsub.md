# 4.2 — Pub/Sub

> **Section 4 · Streaming & Ingestion · Lecture 4.2 · 8:00**

## 🎯 What you will learn

- The Pub/Sub architecture: topics, subscriptions, publishers, subscribers, and the three-entity model
- The message lifecycle, from publish through acknowledgment, and why "acknowledge" is the only thing a subscriber controls
- The three **delivery types**: push, pull, and exactly-once — what each actually guarantees
- Pull vs push: how to choose, and why push is not "pull with a callback"
- **Ordering keys** and their exact throughput cost
- Message retention, the 7-day default, and the 31-day maximum
- **Schemas**: Avro, Protobuf, and JSON — and why an unenforced schema is a coordination failure waiting to happen
- **Dead-letter topics**: when they help, when they hide bugs, and the poison-pill trap
- At-least-once as the default, and how to achieve deduplication with `message_id` and `id_label`
- Pub/Sub Lite, and the throughput ceiling that justifies it
- The Pub/Sub cost model and the fan-out charge that surprises everyone

---

## 🧠 Concept

### The three-entity model

Pub/Sub has exactly three nouns, and everything else is configuration on them:

- A **topic** is a named stream of messages. Publishers write to it. A topic is a routing label, not storage.
- A **subscription** is an independent, durable cursor over a topic. Each subscription tracks its own delivery position, its own retry configuration, and its own dead-letter topic.
- A **publisher** writes messages to a topic. A **subscriber** reads from a subscription.

The model is a durable fan-out bus. Write once to the topic; every subscription sees every message, independently, at its own pace.

```text
                    ┌──────────────────────────────────────────┐
   publisher ──────▶│  TOPIC  orders.v1                       │
   (publish)        │  (no storage of its own; a routing      │
                    │   label for subscriptions)              │
                    └────┬───────────┬───────────┬───────────┘
                         │           │           │
              ┌──────────▼──┐ ┌──────▼─────┐ ┌───▼──────────┐
              │ SUB audit   │ │ SUB billing│ │ SUB realtime │
              │ own offset  │ │ own offset │ │ own offset  │
              │ own DLQ     │ │ own DLQ    │ │ own DLQ     │
              └──────┬──────┘ └──────┬─────┘ └──────┬──────┘
                     │               │              │
              BigQuery        Cloud Run        Realtime DB
```

The critical consequence of this design: **the topic holds no messages of its own.** Retention is a property of the *subscription*. Two subscriptions on the same topic can have entirely different retention periods, and deleting one subscription deletes its backlog.

This is the mental model that makes everything else fall out. When you ask "where are my messages?", the answer is "in the subscription backlog", and the question you should ask instead is "which subscription is behind?"

### The message lifecycle

```text
1. publish       Publisher sends a message (data + attributes + optional ordering key)
                        │
2. persist       The message is written to the subscription backlog
                        │
3. deliver       The subscriber receives it — via pull (StreamingPull) or push (HTTP POST)
                        │
4. process       The subscriber does its work
                        │
5. acknowledge   The subscriber ACKs the message
                        │
6. (on failure)  nack → the message is redelivered, up to the retry limit
                        │
7. (on exhaustion) the message goes to the dead-letter topic
```

Two properties of this lifecycle drive every design decision:

**The subscriber controls exactly one thing: when to acknowledge.** Pub/Sub does not know whether your processing succeeded. It only knows whether you sent an ACK. If you ACK before processing, you have chosen at-most-once. If you ACK after, you have chosen at-least-once. Everything else is downstream of that choice.

**At-least-once is the default, and duplicates are guaranteed.** Pub/Sub's guarantee is "a message is delivered at least once", and the practical consequence is that **a message can be delivered more than once**. This is not an edge case you mitigate in production; it is the design. Pub/Sub Lite does not guarantee ordering.

The standard advice from Google is: *acknowledge the message before processing if you want at-most-once; acknowledge after processing if you want at-least-once. Set the retry policy so that a failing message is redelivered, and give your subscriber a dead-letter topic.*

### Delivery types

This is the single most examined topic in the certification, and the distinction is sharper than most documentation makes it.

#### Pull delivery

The subscriber opens a long-lived streaming pull (`StreamingPull`) or a bounded synchronous pull (`Pull`) and receives messages. The subscriber explicitly acknowledges each message.

**Guarantees:**
- At-least-once delivery.
- The subscriber controls the rate of consumption — the service only sends as many messages as you ask for.
- **The ack deadline timer starts when the message is delivered to the subscriber.** You have a bounded window (default 10 s, max 600 s) to acknowledge before the message is redelivered.

**Why pull is the default for serverless:** the message is held in the subscription backlog until you ask for it. If your consumer is slow, the backlog grows — and backlog is exactly what you want, because it means no data loss during a consumer outage. With push, Pub/Sub must buffer the message somewhere during the outage, and that buffer is subject to the topic's retention window.

**The critical pull mistake:** acknowledging in a `finally` block or an unconditional path, which turns at-least-once into at-most-once by accident.

```python
# A miniature subscriber that shows the two ack strategies.
class Subscriber:
    def __init__(self, name: str, ack_in_finally: bool = False) -> None:
        self.name = name
        self.ack_in_finally = ack_in_finally
        self.acked: list[str] = []
        self.nacked: list[str] = []

    def ack(self, message_id: str) -> None:
        self.acked.append(message_id)

    def nack(self, message_id: str) -> None:
        self.nacked.append(message_id)

    def handle(self, message_id: str, fail: bool) -> None:
        try:
            if fail:
                raise ValueError("processing failed")
        except Exception:
            self.nack(message_id)
            if self.ack_in_finally:
                self.ack(message_id)  # BUG: the message is acked anyway
        else:
            self.ack(message_id)


buggy = Subscriber("ack-in-finally", ack_in_finally=True)
buggy.handle("m1", fail=True)
print(f"buggy  acked={buggy.acked} nacked={buggy.nacked}")

correct = Subscriber("ack-after-success")
correct.handle("m1", fail=True)
print(f"correct acked={correct.acked} nacked={correct.nacked}")
```

Expected output:

```text
buggy  acked=['m1'] nacked=['m1']
correct acked=[] nacked=['m1']
```

The buggy subscriber both nacks **and** acks the same message. The nack schedules a redelivery, but the ack has already told Pub/Sub to discard it — so the message is lost. That is how an accidental `ack()` in a `finally` block turns at-least-once into at-most-once without any error being raised.

The project models this distinction exactly. `ingest_events` takes a `reject` flag that switches between the two modes:

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events

with open("sample_data/malformed_events.csv") as handle:
    lines = list(handle)

# Mode 1: collect rejects for a dead-letter path (at-least-once friendly).
accepted, rejected = ingest_events(lines, reject=False)
print(f"accepted={len(accepted)} rejected={len(rejected)}")

# Mode 2: fail the whole batch on the first bad event.
try:
    ingest_events(lines, reject=True)
except Exception as exc:
    print(f"raised {type(exc).__name__}: {exc}")
```
Expected output:

```text
accepted=0 rejected=12
raised EventRejected: wrong_field_count: not-an-event,missing-fields,garbage
```

#### Push delivery

Pub/Sub delivers messages by making an HTTP POST to a **push endpoint** you configure on the subscription.

**Guarantees:**
- At-least-once delivery. The push endpoint must return a `2xx` to acknowledge.
- **A non-2xx response (or a timeout) causes redelivery** — with exponential backoff, up to the retry limit, then dead-letter.
- The endpoint must respond within the **ack deadline**. If it does not, the message is redelivered — possibly while your first request is still executing. This is the classic duplicate-processing trigger in push architectures.

**Push specifics that matter:**

- The endpoint must be publicly reachable, or use a push endpoint that Pub/Sub can reach (Cloud Run, GKE Ingress, an authenticated backend). Pub/Sub **supports OIDC authentication** for push endpoints, which you should always enable — an unauthenticated push endpoint on the public internet is a data-leak waiting to happen.
- Pub/Sub adds headers: `x-goog-version`, `x-goog-message-id`, `x-goog-pubsub-message-id`, `x-goog-pubsub-subscription-name`, `x-goog-pubsub-attributes`, `x-goog-pubsub-ordering-key`. The message ID header is what you use for deduplication.
- The `User-Agent` header contains `(Google Pub/Sub)` — filter on it if you have a shared endpoint.
- **Push is a webhook.** The request body is the message; your endpoint's response code is the ack. There is no client library involved on the receiving side.

**When push wins:** the subscriber is a webhook-shaped service, needs no long-lived connection, or is not on GCP at all (a partner system, an on-prem app that can be exposed). **When pull wins:** the consumer is long-running, is on GCP, or wants backpressure.

The practical nuance: Pub/Sub push has no built-in rate limiting, so a burst can overwhelm a fragile endpoint. You can mitigate with a push subscription + a subscriber that pulls, or with Cloud Run's concurrency limits, or with an API Gateway quota in front.

#### Exactly-once delivery

This is the newest and most misunderstood delivery type. It is **not** a general exactly-once guarantee for your processing.

**What it actually does:** Pub/Sub buffers messages server-side between the subscription and the publisher, in the publisher's project. If a message is not acknowledged within the ack deadline, and the *publisher* retries publishing the same message **with the same `message_id`**, Pub/Sub deduplicates it — the duplicate is dropped before it reaches your subscriber.

**What it does not do:**
- It does not make your processing exactly-once. If your subscriber receives a message, processes it, and then crashes *before* acknowledging, the message is redelivered and processed twice. Exactly-once delivery does not help there.
- It does not help if your publisher generates a new `message_id` on each retry.
- It requires the publisher and the subscription to be **in the same project and same region** for the deduplication window to apply.
- It requires the subscriber to acknowledge **within the ack deadline**.

The deduplication window is a finite buffer. The message is deduplicated if the retry arrives while the original is still within that buffer. If the original has already been acknowledged and aged out of the buffer, a later duplicate is delivered normally.

**The correct mental model:** exactly-once delivery protects against **publisher-side retries**. At-least-once with idempotent processing protects against **subscriber-side failures**. You need both, and they solve different problems.

### Ordering keys

Pub/Sub's ordering guarantee: messages published with the **same ordering key** are delivered to a subscription **in the order they were published**, provided all messages are published **to the same region** and use the **same ordering key**.

Without an ordering key, Pub/Sub may deliver messages in any order — including out of order. This is the default.

**The throughput cost, which is severe:**

> Enabling message ordering reduces the maximum throughput of a Pub/Sub topic to **1 MB per second per ordering key region**.

This is the number to remember. Ordering keys are not a hint; they are a hard throughput partition, exactly like a Kafka partition. A topic with ordering enabled and 100 ordering keys has a ceiling of 100 MB/s. A topic with a single ordering key — a very common mistake, using `user_id` as the ordering key where one user generates most of the traffic — has a ceiling of 1 MB/s.

The correct use: an ordering key should be a **low-cardinality-per-entity, high-cardinality-across-entities** value, and you should have many of them. Ordering by `customer_id` when you have a million customers is fine. Ordering by `user_id` when one user is 30% of traffic is a throughput incident waiting to happen.

The other ordering costs:

- **Ordering is only guaranteed within a region.** A topic in `us-central1` and a topic in `europe-west1` have no ordering relationship. Ordering keys do not work across regions.
- **Ordering requires a single active publisher per ordering key.** If two publishers publish to the same key concurrently, order is undefined.
- **Ordering increases redelivery risk.** If a message with an ordering key is not acknowledged within the ack deadline, it is redelivered — and while it is outstanding, **subsequent messages with the same key are held back**. One slow message stalls the whole key. Google explicitly warns that with ordering enabled, a stuck message can block the key indefinitely, and the recommended mitigation is to publish a "fresh" copy of the stuck message to break the block.

The mitigation pattern: keep a maximum ack deadline (600 s), and on a stuck message, re-publish it with the same ordering key and a new publish time, then ack the original. The redelivered copy and the fresh copy are the same logical message; your idempotent consumer handles the duplicate.

**Do you need ordering?** Almost never for analytics. Event streams feeding BigQuery do not need ordering — you are aggregating, and aggregation is order-independent. Ordering matters for stateful machine learning features, for maintaining a derived aggregate incrementally, and for sequence-sensitive domain logic. If your pipeline aggregates to hourly windows, ordering is pure cost.

### Message retention

**Subscription backlog retention** determines how long unacknowledged messages are kept for a subscriber. The default is **7 days**. The maximum is **31 days**.

- Once a message is acknowledged, it is gone from the backlog — permanently. Acknowledged messages are not retained.
- The retention clock starts when the message is **published**, not when it is delivered. A message published on day 1 and delivered on day 6 has 1 day of retention left, not 7.
- If a subscriber is down longer than the retention window, messages expire. **Expiration is silent** — the message is never delivered, no dead-letter entry is created, and the subscriber just sees fewer messages.
- Retention and ordering interact: **ordering keys require at least a 60-minute retention window.** Enabling ordering on a subscription with less than that fails.

The retention decision is a **recovery window** decision. How long do you need to be able to catch up after a consumer outage? Seven days covers a weekend. Thirty-one days covers a long holiday and an incident review. The cost of longer retention is storage, which is cheap; the cost of a missed outage window is missing data, which is not.

### Schemas

A Pub/Sub **schema** attaches a schema to a topic or subscription and enforces it on publish and/or delivery. Three types are supported:

- **Avro** — binary, schema-based, field-level defaults and evolution rules. The default choice.
- **Protocol Buffers** — binary, strong typing, excellent multi-language support, widely used with Dataflow.
- **JSON** — text, human-readable, weakest guarantees.

Why schemas matter, stated plainly: **without a schema, Pub/Sub transports bytes.** It will happily deliver a message where `amount` changed from a string to an integer, where a field was removed, or where the entire payload shape is different. Your consumer finds out at 03:00 with a `TypeError`, or worse, silently writes garbage into BigQuery.

A schema attached with `ENCODING_JSON` and `VALIDATION` enforcement gives you:

- **Publish-time rejection.** The publisher gets an error and can retry — with the producer knowing immediately.
- **Delivery-time validation.** The subscriber gets a `SchemaViolationError` and can route the message to the dead-letter topic.

The compatibility modes mirror what you would expect from Schema Registry:

| Mode | Meaning | Typical use |
|---|---|---|
| `RELAXED` | Backward or backward-transitive | Rapidly evolving data |
| `STRICT` | Full compatibility | Contracts with external consumers |

For the `STRICT` mode, the practical rules are: add new fields with defaults, never change a field's type in place, never remove a field, and use nested records for grouped changes.

**JSON vs Avro decision:** use Avro unless you have a specific reason. Avro is materially smaller (which directly reduces the per-GB message charge), it supports field defaults for evolution, and it is the format the Dataflow connectors handle most cleanly. Use JSON when a human needs to read the payloads in the console, or when an external system produces the messages and cannot emit Avro.

The `publish_topic` function in the project shows the right way to structure a published message:

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events, publish_topic

with open("sample_data/events.csv") as handle:
    accepted, rejected = ingest_events(handle)

messages = publish_topic(accepted[:2], topic="events-normalised")
for message in messages:
    print(f"topic   : {message['topic']}")
    print(f"attrs   : {message['attributes']}")
    print(f"payload : {message['data'][:100]}...")
    print()
```
The key design point: **the routing metadata goes in the attributes, not in the body.** Attributes are separately encoded from the data payload, so a subscriber can filter on `region` or `event_type` without decoding the body at all. On Pub/Sub, a filtered subscription does not even count the filtered messages as delivered — a real cost saving.

### Dead-letter topics

A **dead-letter topic** is a topic that receives messages that have exhausted their retry policy. The subscription's `dead_letter_policy` names it.

**How it works:**

1. The subscriber NACKs a message (or fails to ACK before the ack deadline).
2. Pub/Sub redelivers with exponential backoff, up to `max_delivery_attempts` (default 5).
3. When the attempts are exhausted, the message is **removed from the subscription backlog** and published to the dead-letter topic.
4. The dead-letter topic is a normal topic — it has its own subscriptions, its own retention, and it can be consumed by a remediation job.

**The poison-pill trap:** the failure mode is that a single poison message blocks your pipeline. But the more common failure is the opposite — **a dead-letter topic with 4 million messages and nobody looking at it.** The DLQ becomes a graveyard. Messages accumulate, retention expires them, and the underlying bug is never found because the alert was never wired.

The discipline that makes DLQs work:

- **The DLQ must have a subscription with a consumer.** An unsubscribed DLQ topic is a message black hole.
- **Alert on DLQ message count**, not on DLQ existence. A threshold of "more than 0 messages in an hour" catches problems early.
- **The DLQ message must carry the failure reason.** Pub/Sub does not add one automatically. Include the reason code in the message attributes when you republish, or use a wrapper.

This is exactly what the project's reject path produces — a stable, low-cardinality reason code, which is what makes the DLQ actionable:

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events, reject_counts

with open("sample_data/malformed_events.csv") as handle:
    accepted, rejected = ingest_events(handle)

counts = reject_counts(rejected)
print(f"total rejected: {len(rejected)}")
for reason, count in sorted(counts.items()):
    print(f"  {reason}: {count}")
```

Expected output:

```text
total rejected: 12
  bad_amount: 1
  bad_timestamp: 1
  missing_event_id: 1
  missing_user_id: 1
  negative_amount: 1
  unknown_channel: 1
  unknown_currency: 1
  unknown_event_type: 1
  unknown_region: 2
  wrong_field_count: 2
```

Note the design principle in the `validate_event` docstring: *"Each is stable and low-cardinality, because a reason code becomes a metric label."* Ten reason codes across 12 rejects. If the reason were the raw payload, you would have 12 distinct metric labels and a broken monitoring system.

### Deduplication with `message_id` and `id_label`

Pub/Sub's default is at-least-once. To make a pipeline effectively-once, you deduplicate.

The mechanism: the publisher sets a **deterministic `message_id`** on each message. The consumer keeps a record of the IDs it has already processed (in BigQuery, Redis, or a local set) and skips repeats.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import dedup_key, deduplicate, partition_for_event

# Simulate the same message delivered twice.
delivered = [
    {"event_id": "e00000000", "event_dt": "2026-01-15T00:54:38+00:00"},
    {"event_id": "e00000001", "event_dt": "2026-01-15T03:09:55+00:00"},
    {"event_id": "e00000000", "event_dt": "2026-01-15T00:54:38+00:00"},
]
partition = partition_for_event(delivered[0]["event_dt"])
unique = deduplicate(delivered, partition=partition)
print(f"delivered={len(delivered)} unique={len(unique)}")
```

Expected output:

```text
delivered=3 unique=2
```

**`message_id` versus `id_label`:** when you enable a Pub/Sub **exactly-once delivery subscription**, the subscription has an **`id_label`** — a field in the message payload that holds the deduplication key. The publisher does not set `message_id`; instead it embeds the key in the payload under the field named by `id_label`, and Pub/Sub uses that value for deduplication.

The distinction matters: `message_id` is a transport-level attribute you set on publish; `id_label` is a payload field that only exists on exactly-once subscriptions. If you configure `id_label` for a field that is not present in the message, the message is **rejected** — a very common configuration mistake.

**The rules for a correct dedup key:**

1. **Deterministic.** The same logical event must produce the same key every time, including across retries and across different publisher instances.
2. **Derived from the data, never from the clock.** A `uuid4()` at publish time, or a publish timestamp, makes every retry a new key and defeats the whole mechanism.
3. **Globally unique across the topic's lifetime.** A business key plus a partition does this — the project's `dedup_key` is exactly this pattern.

### Pub/Sub Lite

Pub/Sub Lite is a zonal, single-topic-at-a-time service with a much lower per-message cost, designed for **very high publish rates of small messages**.

**The tradeoff, precisely:**

| | Pub/Sub | Pub/Sub Lite |
|---|---|---|
| Regions | Regional / multi-regional | **Zonal** — one zone only |
| Throughput | Very high, unbounded per region | ~10 MB/s publish, ~10 MB/s consume, per zone |
| Per-GB ingest price | $0.40 | **$0.06** |
| Latency | ~100 ms typical | Lower (no cross-zone replication) |
| Ordering | Ordering keys | **No ordering guarantee** |
| Exactly-once | Supported | Not supported |
| Delivery types | Push, pull | **Pull only** |
| Schema enforcement | Yes | No |
| Snapshots / offsets | — | **Yes** — publish a snapshot for a consumer to resume from |

The 1 MB/s per ordering key limit that constrains standard Pub/Sub is *not* a limit on Lite, because Lite does not offer ordering at all.

**The trigger for Lite:** you are publishing millions of tiny messages per second (telemetry, IoT, clickstream at high volume) and the per-GB Pub/Sub price dominates your bill. At $0.06/GB versus $0.40/GB, that is roughly a 6.7× reduction on ingest.

**The costs of Lite:** zonal only (a zone outage stops your pipeline), pull-only, no ordering, no exactly-once, no schema enforcement, and a smaller regional footprint. Lite also has its own snapshot lifecycle to manage.

If your workload is "high volume of small events", Lite is genuinely valuable. If your workload is "business events needing ordering and schema governance", Lite is the wrong tool.

### The cost model

Pub/Sub charges:

- **$0.40 per GB of message data ingested.** Note: this is the *message data*, not attributes.
- **$0.40 per GB of message data delivered** to each subscription.
- **$0.08 per GB of message data retained** in the subscription backlog (after the 7-day free retention).
- **$0.05 per GB** of replayed data (seek/snapshot).

The **delivery charge is per subscription**, and this is the number that surprises people. A topic with 10 subscriptions costs 10× the delivery of a topic with one. Fan-out is not free.

The course's `cost_model.py` encodes this with `PUBSUB_PER_GB_INGEST = 0.40`. The free tier covers 10 GB per month.

```python
import sys
sys.path.insert(0, "project/core")

from cost_model import FREE_TIER, PUBSUB_PER_GB_INGEST, estimate

# 1 TB/month of events, three consumer groups.
monthly_gb = 1024.0
est = estimate("pubsub", pubsub_gb=monthly_gb, messages=0, apply_free_tier=False)
print(f"ingest:  ${est.total:,.2f}  ({monthly_gb} GB @ ${PUBSUB_PER_GB_INGEST}/GB)")

# Fan-out: each additional subscription adds a full delivery charge.
for groups in (1, 3, 10):
    delivery = monthly_gb * groups * PUBSUB_PER_GB_INGEST
    print(f"{groups:>2} subscription(s): ingest ${monthly_gb * PUBSUB_PER_GB_INGEST:,.2f} "
          f"+ delivery ${delivery:,.2f} = ${monthly_gb * PUBSUB_PER_GB_INGEST + delivery:,.2f}")

print(f"free tier: {FREE_TIER['pubsub_gb']} GB/month")
```
A 1 TB/month topic with 10 subscriptions costs about **$8,806/month**. With one subscription, about $880. That ratio is the single most important cost fact in Pub/Sub.

---

## 🛠️ Hands-On

### Lab 1 — Model the Pub/Sub topology

```python
import sys
sys.path.insert(0, "project/core")

from service_catalog import get_service, services_by_category

pubsub = get_service("pubsub")
print(f"name       : {pubsub.name}")
print(f"summary    : {pubsub.summary}")
print(f"pricing    : {pubsub.pricing_model}")
print(f"resources  : {', '.join(pubsub.key_resources)}")

print("\nstreaming & messaging category:")
for service in services_by_category("Streaming & Messaging"):
    print(f"  {service.id:<12} {service.pricing_model}")
```

Expected output:

```text
name       : Pub/Sub
summary    : Managed publish/subscribe messaging for event ingestion.
pricing    : Per GB of message data ingested, then per delivery.
resources  : Topic, Subscription, Schema, Dead-Letter Topic

streaming & messaging category:
  datastream   Per CDC row-change processed plus per-stream-hour.
  kafka        Per GB ingested, per GB retained, and per cluster-hour.
  pubsub       Per GB of message data ingested, then per delivery.
```

### Lab 2 — Build a subscription-fan-out cost model

```python
import sys
sys.path.insert(0, "project/core")

from cost_model import PUBSUB_PER_GB_INGEST

monthly_gb = 500.0
ingest = monthly_gb * PUBSUB_PER_GB_INGEST

print(f"monthly volume: {monthly_gb} GB")
print(f"ingest charge : ${ingest:,.2f}")
print()
print(f"{'subs':>5} {'delivery':>12} {'total':>12} {'x vs 1 sub':>12}")
baseline = ingest * 2
for subs in (1, 2, 5, 10, 25):
    delivery = monthly_gb * subs * PUBSUB_PER_GB_INGEST
    total = ingest + delivery
    print(f"{subs:>5} {delivery:>12,.2f} {total:>12,.2f} {total / baseline:>11.1f}x")
```
Expected output:

```text
monthly volume: 500.0 GB
ingest charge : $200.00

 subs     delivery        total   x vs 1 sub
    1       200.00       400.00         1.0x
    2       400.00       600.00         1.5x
    5     1,000.00     1,200.00         3.0x
   10     2,000.00     2,200.00         5.5x
   25     5,000.00     5,200.00        13.0x
```

Delivery cost scales linearly with subscription count. Fan-out is the dominant cost driver.

### Lab 3 — Simulate the delivery-type guarantees

```python
from dataclasses import dataclass, field


@dataclass
class Subscription:
    name: str
    delivery_type: str            # "pull" | "push" | "exactly-once"
    ack_deadline_s: int = 10
    max_delivery_attempts: int = 5
    delivered: list[str] = field(default_factory=list)
    acked: set[str] = field(default_factory=set)
    dlq: list[str] = field(default_factory=list)
    attempts: dict[str, int] = field(default_factory=dict)

    def deliver(self, message_id: str) -> None:
        if self.delivery_type == "exactly-once" and message_id in self.acked:
            return  # deduplicated by the server buffer
        self.delivered.append(message_id)
        self.attempts[message_id] = self.attempts.get(message_id, 0) + 1

    def ack(self, message_id: str) -> None:
        self.acked.add(message_id)

    def nack(self, message_id: str) -> None:
        if self.attempts.get(message_id, 0) >= self.max_delivery_attempts:
            self.dlq.append(message_id)


# --- Pull: subscriber crashes before acking -> redelivery ---
pull = Subscription("audit-pull", "pull")
pull.deliver("m1")
print(f"pull delivered: {pull.delivered} acked: {sorted(pull.acked)}")
pull.nack("m1")
pull.deliver("m1")   # broker redelivers
print(f"after nack+redeliver: {pull.delivered} attempts={pull.attempts}")

# --- Push: endpoint returns 500 -> Pub/Sub retries ---
push = Subscription("billing-push", "push")
push.deliver("m2")
push.nack("m2")
print(f"push delivered: {push.delivered} attempts={push.attempts}")

# --- Exactly-once: publisher retries with the same message_id ---
eo = Subscription("realtime-eo", "exactly-once")
eo.deliver("m3")
eo.ack("m3")
eo.deliver("m3")     # duplicate publish, same message_id
eo.deliver("m3")
print(f"exactly-once delivered: {eo.delivered} (deduplicated by server)")
```

Expected output:

```text
pull delivered: ['m1'] acked: []
after nack+redeliver: ['m1', 'm1'] attempts={'m1': 2}
push delivered: ['m2'] attempts={'m2': 1}
exactly-once delivered: ['m3'] (deduplicated by server)
```

### Lab 4 — Verify the at-least-once dedup contract end to end

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import dedup_key, deduplicate, partition_for_event

# A subscriber's delivery batch, with one message redelivered.
batch = [
    {"event_id": "e00000000", "event_dt": "2026-01-15T00:54:38+00:00"},
    {"event_id": "e00000001", "event_dt": "2026-01-15T03:09:55+00:00"},
    {"event_id": "e00000002", "event_dt": "2026-01-15T06:12:01+00:00"},
    {"event_id": "e00000000", "event_dt": "2026-01-15T00:54:38+00:00"},
]
partition = partition_for_event(batch[0]["event_dt"])
unique = deduplicate(batch, partition=partition)
print(f"received={len(batch)} unique={len(unique)} dropped={len(batch) - len(unique)}")
print(f"message_id for e00000000 -> {dedup_key('e00000000', partition)}")
```

Expected output:

```text
received=4 unique=3 dropped=1
message_id for e00000000 -> 20260115:e00000000
```

### Lab 5 — The DLQ reason-code contract

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events, reject_counts

with open("sample_data/malformed_events.csv") as handle:
    accepted, rejected = ingest_events(handle)

counts = reject_counts(rejected)
print(f"accepted={len(accepted)} rejected={len(rejected)}")
print(f"distinct reason codes: {len(counts)}")
print(f"max cardinality of a single code: {max(counts.values())}")
for reason, count in sorted(counts.items()):
    print(f"  {reason:<22} {count}")
```

Expected output:

```text
accepted=0 rejected=12
distinct reason codes: 10
max cardinality of a single code: 2
  bad_amount             1
  bad_timestamp          1
  missing_event_id       1
  missing_user_id        1
  negative_amount        1
  unknown_channel        1
  unknown_currency       1
  unknown_event_type     1
  unknown_region         2
  wrong_field_count      2
```

Ten stable reason codes across 12 rejects — usable directly as Cloud Monitoring metric labels.

### Lab 6 — Ordering key throughput planning

```python
# Pub/Sub: 1 MB/s per ordering key. Plan the key cardinality you need.
MESSAGE_SIZE_BYTES = 2_048
MAX_BYTES_PER_SEC_PER_KEY = 1_048_576

events_per_second = 50_000
bytes_per_second = events_per_second * MESSAGE_SIZE_BYTES
keys_needed = bytes_per_second / MAX_BYTES_PER_SEC_PER_KEY

print(f"ingest rate      : {events_per_second:,} events/s")
print(f"byte rate        : {bytes_per_second / 1_048_576:,.1f} MB/s")
print(f"ordering keys req: {keys_needed:,.0f}")
print()
print("If you key on user_id and one user generates 30% of traffic:")
hot_user_bytes = bytes_per_second * 0.30
print(f"  hot key rate   : {hot_user_bytes / 1_048_576:,.1f} MB/s")
print(f"  ceiling        : 1.0 MB/s")
print(f"  verdict        : {'VIOLATION - hot key exceeds the ceiling' if hot_user_bytes > MAX_BYTES_PER_SEC_PER_KEY else 'ok'}")
```

Expected output:

```text
ingest rate      : 50,000 events/s
byte rate        : 97.7 MB/s
ordering keys req: 98

If you key on user_id and one user generates 30% of traffic:
  hot key rate   : 29.3 MB/s
  ceiling        : 1.0 MB/s
  verdict        : VIOLATION - hot key exceeds the ceiling
```

---

## 🛠️ Common Errors and Fixes

### 1. `PERMISSION_DENIED` when a publisher or subscriber cannot access a topic

```text
google.api_core.exceptions.PermissionDenied:
Permission 'pubsub.topics.publish' denied on resource
'projects/my-project/topics/orders.v1' (or it may not exist).
```

**Cause:** the calling service account lacks the Pub/Sub IAM role. The role names are:
- `roles/pubsub.publisher` — publish to topics.
- `roles/pubsub.subscriber` — pull from subscriptions.
- `roles/pubsub.viewer` — list and get (no data access).
- `roles/pubsub.editor` — full management.

A very common variant: the account has `roles/pubsub.publisher` but is trying to **pull** from a subscription, which needs `roles/pubsub.subscriber`.

**Fix:** grant the narrowest role that matches the action.

```bash
gcloud pubsub topics add-iam-policy-binding orders.v1 \
  --member=serviceAccount:pipeline@my-project.iam.gserviceaccount.com \
  --role=roles/pubsub.publisher

gcloud pubsub subscriptions add-iam-policy-binding orders-sub \
  --member=serviceAccount:pipeline@my-project.iam.gserviceaccount.com \
  --role=roles/pubsub.subscriber
```

### 2. `404 Not Found: Subscription (project/xxx/subscriptions/xxx) not found` in a push subscription

```text
ERROR: Requested entity was not found.
gcloud pubsub subscriptions describe orders-sub
```

**Cause:** the subscription name is fully qualified as `projects/<project>/subscriptions/<name>`, but a bare name is interpreted in the *active* project. If the resource lives in another project or the active project is wrong, it is not found. A related cause: the topic auto-created by the first publish is in a different project than the subscription.

**Fix:** always fully qualify, or set the project explicitly.

```bash
gcloud pubsub subscriptions describe \
  projects/my-project/subscriptions/orders-sub

gcloud pubsub topics list --project=my-project
gcloud pubsub subscriptions list --project=my-project
```

### 3. `ResourceExhausted: Quota exceeded for quota metric 'Publish requests'`

```text
google.api_core.exceptions.ResourceExhausted:
Quota exceeded for quota metric 'Publish requests'
limit: 1000/s, used: 1000/s
```

**Cause:** you are publishing in a tight loop. The default publish quota is 1,000 messages per second per project.

**Fix:** batch your publishes using the `PublishRequest` with multiple messages, and use the **batching publisher** in the client library, which groups messages into `max_messages` / `max_bytes` batches automatically.

```python
from google.cloud import pubsub_v1

publisher = pubsub_v1.PublisherClient(
    batch_settings=pubsub_v1.types.BatchSettings(
        max_messages=1000,          # max messages per batch
        max_bytes=1024 * 1024,     # 1 MiB per batch
        max_latency=0.05,          # flush after 50 ms
    )
)
topic_path = publisher.topic_path("my-project", "orders.v1")
for order in orders:
    publisher.publish(topic_path, order["id"].encode(), origin=b"api")
```

### 4. `DeadlineExceeded` — the ack deadline expires before you acknowledge

```text
WARNING: Message with ack_id: 12, delivery attempt: 3 is nacked.
Reason: The subscriber's ack deadline expired before the message was acknowledged.
```

**Cause:** your processing took longer than the subscription's ack deadline (default 10 s). The message is redelivered, and if you are also processing the redelivered copy concurrently, you get duplicate side effects.

**Fix:** three options, in order of preference.

1. **Increase the ack deadline** (up to 600 s) if your processing genuinely needs it:
   ```bash
   gcloud pubsub subscriptions update orders-sub \
     --ack-deadline-seconds=120
   ```
2. **Ack early and use an idempotent downstream write** — ack as soon as the message is durably queued downstream, and make the downstream write idempotent.
3. **Offload the work**: ack immediately, push to a work queue (a second Pub/Sub topic), and process there. This trades ordering for throughput and is the standard pattern for heavy processing.

Note the interaction with ordering: with an ordering key enabled, an unacked message **blocks all later messages with the same key**. A 10-second ack deadline with 60-second processing means the key stalls for 60 seconds every time.

### 5. `ResourceExhausted: Ordering keys are enabled, but the message has no ordering key` (and the reverse)

```text
Value 'None' does not match the expected ordering key format
```

**Cause:** you enabled ordering on the subscription but published a message without an ordering key, or the ordering key contains characters outside the allowed set.

**Fix:** publish with an ordering key on every message once ordering is enabled. Also note that **ordering keys require at least a 60-minute retention period** on the subscription.

```bash
gcloud pubsub subscriptions update orders-sub \
  --enable-message-ordering \
  --message-retention-duration=60m
```

### 6. `SchemaViolationError` / `InvalidArgument: Schema violation`

```text
google.api_core.exceptions.InvalidArgument:
400 Schema violation for message subject: orders.v1, reason:
'ENUM' not found in ENUM 'OrderStatus'
```

**Cause:** the message payload does not conform to the schema attached to the topic or subscription. Common causes: the enum gained a value the producer does not know, a field was renamed, or a `null` was written to a non-nullable field.

**Fix:** check the attached schema and the producer's version. If the change was intentional, register a new schema version with `BACKWARD` compatibility. If it was a bug, fix the producer and replay from the dead-letter topic.

```bash
gcloud pubsub schemas describe orders-schema \
  --project=my-project --format="yaml"
gcloud pubsub subscriptions describe orders-sub \
  --format="value(deadLetterPolicy,messageRetentionDuration)"
```

### 7. Dead-letter topic receives nothing even though messages fail

**Symptom:** the DLQ is empty but the pipeline is clearly dropping data.

**Cause:** you NACK the message but the subscription's `max_delivery_attempts` is set high (or infinite), and the ack deadline keeps resetting, so the message never reaches the DLQ. Or the DLQ topic does not exist, so the publish silently fails.

**Fix:** configure an explicit, bounded retry policy and verify the DLQ topic exists.

```bash
gcloud pubsub subscriptions create orders-sub-dlq --topic=orders.v1

gcloud pubsub subscriptions update orders-sub \
  --dead-letter-topic=orders-sub-dlq \
  --max-delivery-attempts=5 \
  --ack-deadline-seconds=60
```

---

## 💡 Production Notes

- **Acknowledge after processing, and exactly once per delivery.** An ack in a `finally` block silently converts at-least-once into at-most-once. This is the most common and most damaging Pub/Sub bug, because nothing crashes and data simply vanishes.

- **Deduplicate at the sink, not at the broker.** At-least-once duplicates are guaranteed. Make the downstream write idempotent with a `MERGE` on the business key, or track processed `message_id`s. Derive the key from the data — never from a publish timestamp or a random UUID.

- **Fan-out is the dominant cost driver.** Each additional subscription adds a full $0.40/GB delivery charge. Ten subscriptions on a 1 TB/month topic is roughly 10× the cost of one. Audit your subscription count before you audit anything else.

- **Enforce schemas with `VALIDATION`.** Attach an Avro or Protobuf schema and set validation to reject at publish time. A producer break then fails in the producer's CI instead of corrupting the warehouse at 03:00.

- **Ordering is a throughput partition, not a feature flag.** The limit is 1 MB/s per ordering key, and a single hot key can stall its own key indefinitely. Enable ordering only where a downstream stateful consumer genuinely needs it, and set the ack deadline high enough to avoid blocking the key.

- **Every dead-letter topic needs a subscription, a consumer, and an alert on message count.** An unwatched DLQ is where data goes to be silently expired. Include a stable reason code in the DLQ attributes so the count is actionable — the project's `validate_event` reason codes are the model.

- **Monitor backlog age, not just backlog depth.** A subscription with 1,000 messages that are one second old is healthy; 1,000 messages that are six hours old means the consumer stopped six hours ago. `pubsub.googleapis.com/subscription/oldest_unacked_message_age` is the metric that catches this.

- **Treat `id_label` configuration as schema.** On exactly-once subscriptions, if the field named by `id_label` is missing from the message, the publish is rejected. Validate the producer payload against the subscription's `id_label` in CI.

---

## 🔑 Key Takeaways

- Pub/Sub has three nouns — **topic, subscription, publisher/subscriber** — and a topic holds no messages of its own. Retention belongs to the subscription.
- The subscriber controls exactly one thing: **when to acknowledge**. Ack-after-processing gives at-least-once; ack-before gives at-most-once.
- **Pull** gives you backpressure and backlog durability; **push** gives you webhook simplicity. Pull is the right default on GCP because the backlog absorbs consumer outages.
- **Exactly-once delivery protects against publisher-side retries only** — it deduplicates redelivered publishes with the same `message_id` within a finite server buffer. It does not make your subscriber's processing exactly-once.
- **Ordering keys cap throughput at 1 MB/s per key** and can stall a key indefinitely. Ordering also requires ≥60-minute retention and a single active publisher per key.
- Retention defaults to **7 days**, maxes at **31 days**, and starts at publish time. Expiration is silent — no delivery, no dead-letter entry.
- **Schemas turn breaking changes into rejected publishes.** Avro or Protobuf with `VALIDATION` is the difference between a producer CI failure and a warehouse corruption.
- A **dead-letter topic without a subscription, a consumer, and an alert** is a data graveyard. Reason codes must be stable and low-cardinality to be usable as metric labels.
- **At-least-once is the default and duplicates are guaranteed.** Deduplicate at the sink with a deterministic, data-derived key.
- **Pub/Sub Lite** is zonal, pull-only, unordered, and 6.7× cheaper per GB — the right choice only for very high publish rates of small messages.
- Cost is driven by **ingest + per-subscription delivery + retention**. Fan-out, not volume, is what usually surprises people.

---

## 📚 Practice Exercises

1. **Delivery-type decision matrix.** For each of these workloads, choose pull, push, or exactly-once and justify: (a) a Dataflow streaming job writing to BigQuery, (b) a partner system outside GCP calling your API, (c) a real-time feature store needing per-entity ordering, (d) a nightly batch loader. For each, state the ack deadline and the dedup strategy.

2. **Ordering key cardinality.** Extend the Lab 6 script to model a key distribution from a realistic Zipf-like distribution, then compute the minimum number of ordering keys needed to stay under the 1 MB/s ceiling. Show what happens with 1, 100, and 10,000 keys.

3. **Ack-deadline failure analysis.** Using the `Subscription` class from Lab 3, write a simulation where processing takes 30 s, the ack deadline is 10 s, and the consumer crashes after 15 s. Tabulate the number of deliveries of each message and explain the resulting duplicate side effects. Then model the fix using the ack-then-offload pattern.

4. **Cost of a fan-out topology.** Design a topology with 3 topics and 12 subscriptions totalling 2 TB/month of messages. Compute the monthly cost using `cost_model.estimate`, break out ingest vs delivery vs retention, and identify which two subscriptions to consolidate.

5. **Schema evolution.** Write an Avro schema for the course event shape. Then produce three revisions: adding a field with a default, adding a field without a default, and changing a field's type. For each, state whether `BACKWARD` compatibility accepts it and what a consumer would see at runtime.

6. **DLQ remediation loop.** Using `pipeline_logic.ingest_events` and `reject_counts`, write a remediation function that reads the reject reason codes, maps each to a concrete fix (a schema rule, a currency-table addition, a validation change), and asserts that the total matches `EXPECTED_REJECT_COUNTS` from `project/core/pipeline_logic.py`.

7. **Retention window sizing.** Given a consumer with a 4-hour average outage per week, compute the retention window needed so no message expires, including a safety factor. Explain why the answer is not "the default 7 days" and what the cost delta looks like in the `cost_model` framework.

8. **Pub/Sub Lite evaluation.** Take a workload of 200,000 events/second at 500 bytes each (≈95 GB/s... no: ≈9.5 MB/s) and design a Lite-based topology. State the zones required, the snapshot strategy for consumer recovery, and the two features you lose that you must re-implement.

---

## 📖 Further Reading

- [Pub/Sub Documentation — Overview](https://docs.cloud.google.com/pubsub/docs/overview)
- [Pub/Sub Documentation — Delivery Types](https://docs.cloud.google.com/pubsub/docs/pull)
- [Pub/Sub Documentation — Message Ordering](https://docs.cloud.google.com/pubsub/docs/ordering)
- [Pub/Sub Documentation — Schemas](https://docs.cloud.google.com/pubsub/docs/schemas)
- [Pub/Sub Documentation — Dead-Letter Topics](https://docs.cloud.google.com/pubsub/docs/dead-letter-topics)
- [Pub/Sub Documentation — Exactly-Once Delivery](https://docs.cloud.google.com/pubsub/docs/exactly-once-delivery)
- [Pub/Sub Lite Documentation](https://docs.cloud.google.com/pubsub/docs/pubsub-lite-documentation)
- [Pub/Sub Pricing](https://docs.cloud.google.com/pubsub/pricing)
