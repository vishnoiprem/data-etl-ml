# 20 — Streaming Loading (Kafka, Kinesis, Pub/Sub)

> **Lesson 20 of 30 — Loading**

The right pattern when latency matters. Events flow through a
broker (Kafka, Kinesis, Pub/Sub) and are loaded into the
warehouse in small batches. This lesson is the streaming-load
playbook: producer, broker, consumer, and the failure modes.

---

## 1. The streaming pattern

```
Producer ──► Kafka topic ──► Consumer group
                                  ↓
                          Batch (e.g. 1000 rows)
                                  ↓
                          COPY INTO warehouse
```

The producer writes events to a *topic*. The topic is a
partitioned, append-only log. The consumer group reads from
the topic, batches rows, and bulk-loads them into the
warehouse.

The latency: 1-5 seconds end-to-end. The throughput: 100K-1M
events/sec per topic.

---

## 2. The three brokers

| Broker | Strengths | Weaknesses |
|---|---|---|
| **Kafka** | Highest throughput, mature, exactly-once capable | Operational complexity (ZooKeeper / KRaft) |
| **Kinesis** | AWS-native, managed | Lower throughput than Kafka, higher cost at scale |
| **Pub/Sub** | GCP-native, managed, simple | Less feature-rich than Kafka |

The senior move: "For new pipelines I'd default to Kafka (or
Managed Kafka / MSK on AWS). For AWS-only shops Kinesis is
fine. For GCP-only shops Pub/Sub is the choice."

---

## 3. The producer pattern

A Kafka producer is a small client that buffers and sends:

```python
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers="broker:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    key_serializer=lambda k: k.encode("utf-8") if k else None,
    acks="all",  # wait for all in-sync replicas
    retries=3,
    linger_ms=20,  # batch up to 20ms
    compression_type="lz4",
)
producer.send("events", key="user-123", value={"event": "click"})
```

The senior move: name the four producer settings that matter:
`acks="all"`, `retries=3`, `linger_ms=20`, `compression_type="lz4"`.

---

## 4. The consumer pattern

A Kafka consumer reads from a topic in batches:

```python
from kafka import KafkaConsumer

consumer = KafkaConsumer(
    "events",
    bootstrap_servers="broker:9092",
    group_id="warehouse_loader",
    auto_offset_reset="earliest",
    enable_auto_commit=False,
    max_poll_records=1000,
)
for message in consumer:
    process(message.value)
    # commit manually after the load succeeds
    consumer.commit()
```

The senior move: name the four consumer settings that matter:
`group_id`, `auto_offset_reset`, `enable_auto_commit=False`,
`max_poll_records`.

---

## 5. The batching sweet spot

The consumer buffers rows until it has a batch, then writes:

```
batch_size = 1000       # 1000 rows
linger_ms = 5000        # or 5 seconds, whichever first
```

The trade-off:
- Small batches: low latency, more warehouse round-trips.
- Large batches: high throughput, higher latency.

The senior default: 1000-10000 rows per batch, 1-5 second
linger. Tune for the SLA.

---

## 6. The consumer group pattern

A consumer group is a set of consumers that share the work of
reading a topic. Each partition is read by exactly one consumer
in the group.

```
Topic "events" with 4 partitions:

Consumer 1 (group "loader"): reads partition 0
Consumer 2 (group "loader"): reads partition 1
Consumer 3 (group "loader"): reads partition 2
Consumer 4 (group "loader"): reads partition 3
```

The senior move: "The number of consumers in a group must be
≤ the number of partitions. If you have 4 partitions and 4
consumers, you have full parallelism. If you have 8 consumers,
4 are idle."

---

## 7. The failure modes

| Failure | Mitigation |
|---|---|
| Broker down | Producer retries; consumer reconnects. |
| Consumer crashes mid-batch | Manual commit; restart from last committed offset. |
| Slow warehouse | Backpressure: pause the consumer (`consumer.pause()`). |
| Poison message | DLQ: send to a dead-letter topic for human review. |
| Skewed partition | Rebalance: increase partitions, hash by key. |

The senior move: name the poison-message failure mode. "If a
malformed event makes the consumer crash, I send it to a
DLQ topic and continue. A poison message should not stop the
pipeline."

---

## 8. The exactly-once problem

Kafka *can* do exactly-once via transactional producers and
read-committed consumers, but it's complex. The practical
pattern:

- Producer: idempotent producer (`enable.idempotence=true`).
- Consumer: manual commit after successful load.
- Load: idempotent on the warehouse side (Lesson 23).

The senior move: "I treat 'exactly-once' as 'at-least-once
plus idempotency on the consumer side.' True exactly-once is
expensive; at-least-once with dedup is the practical answer."

---

## 9. The interview answer

> "For streaming I'd use Kafka (or Kinesis / Pub/Sub if
> cloud-native). The producer has `acks=all`, retries, and
> compression. The consumer buffers up to 1000 rows or 5
> seconds, then bulk-loads into the warehouse. The consumer
> commits the offset manually after the load succeeds. The
> number of consumers equals the number of partitions. The
> reliability story: poison messages go to a DLQ, the consumer
> is idempotent on the warehouse side, and backpressure is
> applied if the warehouse slows down."

That single paragraph covers: broker choice, producer settings,
consumer settings, batching, parallelism, failure handling.
Senior answer in 30 seconds.

---

## Try it

Look at the most recent streaming pipeline you've worked on.
What's the batch size? What's the linger time? Is the consumer
group sized to the partitions? Is there a DLQ? If any answer
is "I don't know," the pipeline is under-instrumented.
