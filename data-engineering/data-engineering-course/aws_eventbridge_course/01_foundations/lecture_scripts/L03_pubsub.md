---
l_id: L03
title: "The Pub/Sub Pattern (and how it differs from a queue)"
duration: "6:00"
prereqs:
  - L02 (What is Event-Driven Architecture?)
---

# L03 — The Pub/Sub Pattern (and how it differs from a queue)

> **Section:** 1 — Foundations
> **Duration:** 6:00

## Prereqs

- L02 — What is Event-Driven Architecture?

## Key terms

- **Pub/Sub (publish/subscribe)** — a pattern where publishers send
  events to a *topic*, and any number of subscribers receive a copy.
  The publisher does not know the subscribers.
- **Topic** — the named destination publishers send to. EventBridge
  uses the term *event bus*; SNS calls it a *topic*; Kafka calls it a
  *topic*. Same idea.
- **Message queue** — a durable buffer where producers put messages
  and a *single* consumer (or one of a consumer group) processes each
  message exactly once.
- **Event stream** — an append-only log (Kafka, Kinesis) where
  consumers track their own offset. Multiple consumers can read the
  same record.
- **Fanout** — one event delivered to many subscribers. This is what
  pub/sub does natively.
- **Competing consumers** — many workers competing to drain one
  queue. This is what queues do natively.

## Lecture

Pub/sub, message queues, and event streams are three *cousins* in the
asynchronous messaging family. They look similar — JSON goes in, code
runs on the other side — but they make very different promises. Get
the choice wrong and you'll either lose messages, deliver them twice,
or block producers on a slow consumer.

### Pub/sub: "tell everyone who cares"

In a pub/sub system, a publisher writes to a topic. The broker is
responsible for delivering a copy of the message to *every
subscriber*. If a subscriber is offline, the broker buffers until it
comes back.

```text
                    ┌──────────────┐
                    │  SNS Topic   │
   Publisher ───►   │ "order-events"│
                    └──┬────┬───┬──┘
                       │    │   │
                       ▼    ▼   ▼
                   Email  SMS  Lambda
                   Sub    Sub  Sub
```

EventBridge behaves the same way: a rule is a "subscription" and
matching events are fanned out to every matching target. The fanout
is implicit; you don't enumerate subscribers in your publish call.

**Best for:** notifications, broadcasts, "anything that needs to know
about this fact", decoupling across teams.

### Message queue: "give this to one worker"

A queue has a different contract. The producer puts a message in; one
consumer (or exactly one of a *consumer group*) takes it out and
processes it. The queue is durable: a message stays until it's
acknowledged.

```text
   Producer ─► ┌──────────────┐ ─► Worker 1
               │  SQS Queue   │ ─► Worker 2  (only one wins)
               │ "orders"     │ ─► Worker 3
               └──────────────┘
```

If you put a message in SQS, you should not also rely on EventBridge
to fan that same message out to five different Lambdas — those are
different jobs. Use a queue when you need **work distribution with
back-pressure** and **at-least-once delivery to a single processor**.

**Best for:** job queues, background work, smoothing bursty load,
decoupling slow consumers from a fast producer.

### Event stream: "an ordered log everyone tails"

An event stream (Kafka, Kinesis Data Streams, DynamoDB Streams) is an
*append-only log*. Producers append records; consumers maintain their
own *position* (offset) in the log. New consumers can replay history
from any point. The stream does not delete records when a consumer
reads them.

```text
   Producer ─► ┌──────────────┐ ─► Consumer A  (offset = 100)
               │  Kinesis     │ ─► Consumer B  (offset = 50)
               │  Stream      │ ─► Consumer C  (offset = 200)
               └──────────────┘
```

**Best for:** analytics, multiple consumers needing different views,
time-travel / replay, ordered processing at high throughput.

### Side-by-side comparison

| Property | Pub/Sub (EventBridge, SNS) | Queue (SQS) | Stream (Kinesis) |
|---|---|---|---|
| Delivery semantics | Fanout to all subscribers | One consumer per message | All consumers read all records |
| Retention | None (or up to 24h with replay) | 4–14 days | 1–365 days |
| Ordering | Best-effort | FIFO optional | Ordered by partition key |
| Replay | EventBridge: yes, via Archive | No (delete-on-process) | Yes, by offset |
| Throughput per topic/queue | Tens of thousands of TPS | Hundreds of TPS per queue | Thousands per shard |
| Cost unit | Events published | Requests + message size | Shard hours + PUT payload |

### A concrete example: "order placed"

Picture an e-commerce site. The same `Order Placed` event needs to:

1. Charge the card (must succeed, exactly once) → **SQS FIFO → Lambda**
2. Send a confirmation email (fire-and-forget) → **SNS topic / EventBridge rule**
3. Update a real-time analytics dashboard (ordered, replayable) → **Kinesis → Lambda**
4. Audit-log to S3 (long retention) → **EventBridge → Firehose → S3**

Notice we use **all three patterns** for one event, because each
consumer has a different requirement. Pub/sub isn't a replacement
for queues; they are tools in the same toolbox.

### Where EventBridge sits in this picture

EventBridge is the **pub/sub** tier with three extras nobody else
has: SaaS partner integrations, archives & replay, and a schema
registry. It is **not** a queue — there is no "one consumer wins"
semantics — and it is **not** a stream — there is no per-consumer
offset. When you need those, attach SQS, Kinesis, or DynamoDB Streams
as *targets* on a rule, which is what we do in section 4.

## Hands-on

Nothing to do for this lecture — it is conceptual. In L04 we look at
how EventBridge evolved from CloudWatch Events and how it fits in
with the rest of AWS messaging.

## Quiz prep

- One line each: what does pub/sub promise, what does a queue promise,
  what does a stream promise?
- For a "send confirmation email" use case, which pattern fits?
- Why doesn't EventBridge replace SQS?

## Key takeaways

- **Pub/sub** = fanout, no retention, no ordering, no "one consumer
  wins" — best for notifications and decoupling.
- **Queue** = one consumer per message, durable, ordered (FIFO) or
  best-effort — best for work distribution and back-pressure.
- **Stream** = append-only log, all consumers read all records, replay
  by offset — best for analytics and ordered processing.
- EventBridge is **pub/sub with extras**: SaaS partners, archives,
  replay, schema registry.
- Real systems combine all three; pick the pattern by the *consumer's*
  requirements, not the producer's.

## Further reading

- _AWS Messaging Services_ decision guide (SQS vs SNS vs EventBridge vs Kinesis)
- _Apache Kafka_ documentation — for a deeper stream primer
- L04 — Why EventBridge? (and where CloudWatch Events fits)
- L18 — SQS + SNS Targets (queue + pub/sub fanout)
