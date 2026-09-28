# Building Data Pipelines with Kafka — CTO / Principal Study Plan

**Source course:** Data Vidhya — *Building Data Pipelines with Kafka*
by Darshil Parmar.
**Course URL:** https://datavidhya.com/learn/ (Python + Kafka course)
**Coverage:** 3 modules • 20 lessons
**Audience:** Data engineers targeting **Staff → Principal → Director →
VP/CTO** track with hands-on Python Kafka producer/consumer + Avro
+ Schema Registry skills.

> **How to use this file.** Each lesson has four lenses:
>
> 1. **Theory** — mental model and the Python-Kafka primitive.
> 2. **Practical Example** — concrete code, configs, decisions.
> 3. **AI Use Case** — where GenAI / ML slots in or on top of this lesson.
> 4. **CTO / Principal Motivation** — career reason; what decisions
>    you're trusted with at senior levels.
>
> This is the **hands-on companion** to the Stream Processing &
> Production course: that one covers the operational and strategic
> layer; this one covers the **code-level mechanics** — every
> `confluent-kafka-python` and `kafka-python` parameter you'll
> touch in production, every Avro/Schema Registry pattern, and the
> Citi Bikes project that ties them together.
>
> The Principal-level Python Kafka engineer can write a
> production-grade producer (idempotent, EOS, schema-validated) and
> consumer (manual commit, backpressure-aware, exactly-once into a
> sink) in 30 minutes, and can defend every parameter in a code
> review.

---

# Module 1 · Python Programming (10 lessons)

## Lesson 1 — Python Kafka Setup

### Theory

Setting up a Python Kafka development environment. Mental model:

- **Library choice:**
  - `kafka-python` — pure-Python, no librdkafka, slower.
  - `confluent-kafka-python` — wraps `librdkafka`, faster, the
    production standard. **Default for any serious work.**
  - `aiokafka` — async wrapper around `kafka-python`, for asyncio
    codebases.
- **Docker Compose** — local single-broker Kafka + Schema Registry +
  Control Center for development.
- **Dependencies** — `pip install confluent-kafka[avro] fastavro`.

### Practical Example

A minimal `docker-compose.yml` for local dev:

```yaml
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.6.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
  kafka:
    image: confluentinc/cp-kafka:7.6.0
    depends_on: [zookeeper]
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
  schema-registry:
    image: confluentinc/cp-schema-registry:7.6.0
    depends_on: [kafka]
    environment:
      SCHEMA_REGISTRY_HOST_NAME: schema-registry
      SCHEMA_REGISTRY_KAFKASTORE_BOOTSTRAP_SERVERS: kafka:9092
```

Python install:

```bash
pip install confluent-kafka[avro] fastavro requests
```

### AI Use Case

**AI-generated docker-compose.** Describe your local stack → AI
generates the compose file. The Principal's edge: 5× faster
environment setup.

### CTO / Principal Motivation

Standardizing the dev environment is **the lowest-cost productivity
win** a Principal can deliver. One docker-compose.yml replaces 20
"works on my machine" tickets per quarter. CTOs see this as **cycle
time reduction** — a measurable engineering metric.

---

## Lesson 2 — Python — Producer and Consumer (Video)

### Theory

The two endpoints of Kafka in Python. Mental model:

- **Producer** — `Producer(conf)` → `produce(topic, value, key)` →
  `flush()` to send.
- **Consumer** — `Consumer(conf)` → `subscribe([topics])` →
  `poll(timeout)` to receive.
- **Delivery callback** — invoked per message (success or failure).
- **Consumer loop** — call `poll()` in a loop until done.

### Practical Example

A minimal producer + consumer pair:

```python
# producer.py
from confluent_kafka import Producer

p = Producer({"bootstrap.servers": "localhost:9092"})

def delivery(err, msg):
    if err:
        print(f"FAILED: {err}")
    else:
        print(f"Sent: topic={msg.topic()} partition={msg.partition()} offset={msg.offset()}")

p.produce("events", key="u1", value=b'{"event":"click"}', callback=delivery)
p.flush()
```

```python
# consumer.py
from confluent_kafka import Consumer

c = Consumer({
    "bootstrap.servers": "localhost:9092",
    "group.id": "my-group",
    "auto.offset.reset": "earliest"
})
c.subscribe(["events"])

while True:
    msg = c.poll(1.0)
    if msg is None: continue
    if msg.error(): print(f"ERROR: {msg.error()}"); continue
    print(f"Received: {msg.value().decode()}")
```

### AI Use Case

**AI-generated producer/consumer skeletons.** "Python producer with
idempotence and Schema Registry" → AI generates a working template.
The Principal's edge: 3× faster pipeline onboarding.

### CTO / Principal Motivation

Producer/consumer code patterns are the **first thing to standardize
across teams**. Without a shared library, every team writes their
own producer with subtle bugs (no flush, no callback, no retry).
The Principal's deliverable: an internal `kafka-python-utils`
package that wraps `confluent-kafka` with team defaults.

---

## Lesson 3 — Producers In-Depth (Part 1)

### Theory

Producer internals Part 1 — the **send path**. Mental model:

- **`produce()`** — appends to internal queue (non-blocking).
- **`poll()` / `flush()`** — drains the queue (blocking).
- **Accumulator** — batches records by partition (default 32 KB
  threshold or `linger.ms`).
- **Sender thread** — sends batches to brokers.
- **Serializer** — converts key/value to bytes (string, json,
  AvroSerializer).

### Practical Example

Producer with batching:

```python
p = Producer({
    "bootstrap.servers": "localhost:9092",
    "linger.ms": 50,           # wait up to 50ms to fill a batch
    "batch.size": 65536,       # 64 KB batch threshold
    "compression.type": "lz4", # compress the batch
    "acks": "all",             # wait for all replicas
})
```

At 10K msgs/sec × 1 KB with `linger.ms=50`, you get ~50 ms p99 latency
and 100+ MB/sec throughput per producer.

### AI Use Case

**AI-tuned producer config.** AI watches producer metrics
(batch size, queue time, throughput) and recommends parameter
changes. The Principal's edge: 2× throughput from AI tuning.

### CTO / Principal Motivation

Producer tuning is **the most underestimated lever** in Kafka
deploys. A 2× producer throughput improvement saves 50% of broker
count. The Principal owns the **tuning playbook**; the CTO sees the
**Kafka cost** decline.

---

## Lesson 4 — Producers In-Depth (Part 2)

### Theory

Producer internals Part 2 — **reliability and EOS**. Mental model:

- **`acks`** — 0 (fire-and-forget), 1 (leader), all (replicated).
- **`enable.idempotence=true`** — dedupe retries within a session
  via producer ID + sequence number.
- **`transactional.id`** — enables transactions across multiple
  topics/partitions.
- **`max.in.flight.requests.per.connection`** — capped at 5 for
  idempotent producers.
- **Retries** — `retries=10`, `retry.backoff.ms=100` default.

### Practical Example

An idempotent, transactional producer:

```python
p = Producer({
    "bootstrap.servers": "localhost:9092",
    "enable.idempotence": True,
    "acks": "all",
    "max.in.flight.requests.per.connection": 5,
    "retries": 10,
    "transactional.id": "my-tx-id",
})

p.init_transactions()
p.begin_transaction()
p.produce("events", value=b'...')
p.produce("audit", value=b'...')
p.commit_transaction()  # atomic across both topics
```

This gives **exactly-once** semantics between two Kafka topics.
Combined with `read_committed` consumers, end-to-end EOS.

### AI Use Case

**AI-driven idempotence audit.** AI scans producer configs for
missing `enable.idempotence` and flags duplicates risk. The
Principal's edge: zero data corruption incidents.

### CTO / Principal Motivation

Idempotent producers are **the no-brainer default** for production
pipelines. The Principal's standard: "every producer in our fleet
has `enable.idempotence=true`." CTOs approve because the alternative
is silent data corruption.

---

## Lesson 5 — Producers in Python (Article)

### Theory

The complete producer reference. Mental model — the `confluent-kafka`
Producer API surface:

- **`Producer(conf)`** — create with config dict.
- **`produce(topic, value=..., key=..., timestamp=..., headers=...,
  partition=..., callback=...)`** — enqueue.
- **`flush(timeout=...)`** — block until queue drained.
- **`poll(timeout=...)`** — non-blocking flush, also services delivery
  callbacks.
- **Per-message config**: `on_delivery` callback; `headers` (key-value
  list).

### Practical Example

A robust producer with error handling and headers:

```python
from confluent_kafka import Producer
import json

p = Producer({
    "bootstrap.servers": "localhost:9092",
    "enable.idempotence": True,
    "acks": "all",
    "compression.type": "zstd",
    "linger.ms": 20,
    "client.id": "orders-service",
})

def send_order(order: dict):
    headers = [
        ("trace-id", order["trace_id"].encode()),
        ("schema-version", b"2"),
    ]
    p.produce(
        topic="orders",
        key=order["order_id"].encode(),
        value=json.dumps(order).encode(),
        headers=headers,
        on_delivery=lambda err, msg: log_failure(err, msg)
    )
    p.poll(0)  # service callbacks

def log_failure(err, msg):
    if err:
        logger.error(f"delivery failed: {err}, topic={msg.topic()}, key={msg.key()}")

# At shutdown
p.flush(10)
```

### AI Use Case

**AI-generated producer wrappers.** "Wrap confluent-kafka with our
team's conventions (idempotence, structured logging, headers,
metrics)" → AI produces a `TeamProducer` class. The Principal's
edge: standards adoption in days, not months.

### CTO / Principal Motivation

The producer wrapper class is **the most leveraged internal library**
in a Kafka organization. One good wrapper eliminates 100 bug
reports. The Principal's deliverable: a published, versioned
internal package.

---

## Lesson 6 — Part 1 — Consumer & Consumer Groups

### Theory

Consumer fundamentals. Mental model:

- **Consumer group** — N consumers sharing the partitions of a topic.
  Each partition goes to exactly one consumer in the group.
- **`group.id`** — the consumer's group identity.
- **Auto-assignment** — Kafka rebalances when consumers join/leave.
- **`subscribe([topics])`** — declarative subscription (group-based).
- **`assign([TopicPartition(...)])`** — imperative assignment (no group).

### Practical Example

Consumer with explicit partition assignment (no rebalance):

```python
from confluent_kafka import Consumer, TopicPartition

c = Consumer({
    "bootstrap.servers": "localhost:9092",
    "group.id": "etl-1",
    "enable.auto.commit": False
})

# Manually assign specific partitions
c.assign([TopicPartition("events", 0, offset=0),
          TopicPartition("events", 1, offset=0)])

while True:
    msg = c.poll(1.0)
    if msg is None: continue
    process(msg)
    c.commit(message=msg, asynchronous=False)
```

### AI Use Case

**AI-driven rebalance avoidance.** AI watches consumer rebalances
and recommends session timeouts / static membership. The Principal's
edge: zero rebalance downtime.

### CTO / Principal Motivation

Rebalances cause **consumer lag spikes** that customers notice.
Static membership (`group.instance.id`) is the 2026 fix. The
Principal's standard: "every consumer uses static membership in
prod." CTOs see this as **reliability improvement**.

---

## Lesson 7 — Part 2 — Hands-On Consumer & Parameters

### Theory

Consumer parameters in depth. Mental model:

- **`auto.offset.reset`** — earliest (replay from start) vs latest
  (only new messages).
- **`enable.auto.commit`** — true (default) commits offsets every
  5s; false (manual) is safer.
- **`max.poll.interval.ms`** — max time between `poll()` calls before
  Kafka assumes the consumer is dead.
- **`session.timeout.ms`** — heartbeat-based liveness; default 45s.
- **`fetch.min.bytes` / `fetch.wait.max.ms`** — fetch batching.
- **`partition.assignment.strategy`** — range, roundrobin, sticky,
  cooperative-sticky.

### Practical Example

A tuned consumer for low-latency processing:

```python
c = Consumer({
    "bootstrap.servers": "localhost:9092",
    "group.id": "fraud-detector",
    "auto.offset.reset": "earliest",
    "enable.auto.commit": False,
    "max.poll.interval.ms": 300000,        # 5 min processing window
    "session.timeout.ms": 60000,           # 60s heartbeat
    "fetch.min.bytes": 1024,
    "fetch.wait.max.ms": 100,
    "partition.assignment.strategy": "cooperative-sticky",
})
```

### AI Use Case

**AI-tuned consumer config.** AI watches consumer lag, processing
time, rebalance frequency and recommends parameters. The Principal's
edge: lowest latency at lowest cost.

### CTO / Principal Motivation

Consumer parameters are **the difference between a working consumer
and a production consumer**. The Principal's deliverable: a
**tuned config template** per use-case class (real-time fraud vs
batch ETL).

---

## Lesson 8 — Part 3 — Consumer Commit and Offset

### Theory

Offset management. Mental model:

- **`__consumer_offsets`** — internal Kafka topic storing committed
  offsets per group/partition.
- **Auto-commit** — periodic; risk: process crashes between commit
  and processing → duplicate.
- **Manual commit** — `commit(message=msg)` or `commit(offsets=[...])`.
- **Sync vs async commit** — sync blocks until commit succeeds.
- **Commit strategies** — at-least-once (commit after process),
  exactly-once (commit in transaction).

### Practical Example

At-least-once consumer with manual commit:

```python
def process_with_commit(c):
    while True:
        msg = c.poll(1.0)
        if msg is None: continue
        try:
            result = process(msg)  # may take seconds
            db_write(result)        # write to downstream
            c.commit(message=msg, asynchronous=False)  # commit only on success
        except Exception as e:
            logger.error(f"processing failed: {e}")
            # don't commit; will retry
            time.sleep(5)
```

### AI Use Case

**AI-driven commit-strategy advisor.** AI watches offset patterns
and recommends at-least-once vs exactly-once per pipeline. The
Principal's edge: lower duplicate rate.

### CTO / Principal Motivation

Commit strategy is **the dedup boundary**. The Principal's standard:
"every consumer uses manual commit after processing." CTOs see this
as **data correctness improvement**.

---

## Lesson 9 — Consumers in Python (Article)

### Theory

Complete consumer reference. Mental model — the API surface:

- **`Consumer(conf)`** — create with config dict.
- **`subscribe([topics], on_assign=..., on_revoke=...)`** — join group.
- **`assign([TopicPartition(...])`** — manual assignment.
- **`poll(timeout)`** — returns `Message` or `None`.
- **`commit(...)`** — explicit offset commit.
- **`seek(TopicPartition(...))`** — jump to specific offset.
- **`close()`** — leave group cleanly.

### Practical Example

A consumer with rebalance callbacks for clean drain:

```python
def on_assign(c, partitions):
    # Custom logic on partition assignment
    for tp in partitions:
        tp.offset = OFFSET_BEGINNING if fresh_start else OFFSET_STORED
    c.assign(partitions)

def on_revoke(c, partitions):
    # Drain in-flight messages before losing partitions
    c.commit(asynchronous=False)
    close_resources()

c.subscribe(["events"], on_assign=on_assign, on_revoke=on_revoke)
```

### AI Use Case

**AI-generated consumer wrappers.** AI produces a `TeamConsumer`
class with our team's rebalance handling, error retry, metric
emission. The Principal's edge: 5× faster consumer onboarding.

### CTO / Principal Motivation

The consumer wrapper class is the **mirror of the producer wrapper**
— same leverage, same standards. Together they form the
**internal Kafka SDK**. CTOs see this as **engineering velocity**.

---

## Lesson 10 — Quiz: Python Programming

### Theory

Validate: producer/consumer API fluency, parameter knowledge,
commit-strategy choices, error-handling patterns.

### Practical Example

The 10-question drill:

1. Idempotent producer requirements?
2. Cooperative-sticky vs range assignment?
3. When to use manual commit?
4. EOS between two topics — what config?
5. Session timeout vs max poll interval?

### AI Use Case

AI-generated flashcards + code-completion drills.

### CTO / Principal Motivation

Python Kafka fluency is the **prerequisite for hands-on system
design**.

---

# Module 2 · Project: Citi Bikes (2 lessons)

## Lesson 1 — Citi Bikes Streaming Project (Video)

### Theory

A full end-to-end streaming pipeline using NYC Citi Bikes public data
(real GBFS feed). Mental model:

- **Source** — Citi Bikes GBFS API (`https://gbfs.citibikenyc.com/gbfs/en/station_status.json`).
- **Producer** — Python script polls every 30s, writes to Kafka.
- **Consumer** — Python script reads, processes, writes to Postgres.
- **Schema** — Avro with Schema Registry.
- **Topic** — `citibike.station_status`.

### Practical Example

```python
# producer: poll GBFS, write to Kafka
import requests, json, time
from confluent_kafka import Producer

p = Producer({"bootstrap.servers": "localhost:9092",
              "enable.idempotence": True})

while True:
    data = requests.get(
        "https://gbfs.citibikenyc.com/gbfs/en/station_status.json"
    ).json()
    for station in data["data"]["stations"]:
        p.produce("citibike.station_status",
                  key=station["station_id"].encode(),
                  value=json.dumps(station).encode())
    p.flush()
    time.sleep(30)
```

```python
# consumer: read Kafka, write to Postgres
from confluent_kafka import Consumer
import psycopg2

c = Consumer({"bootstrap.servers": "localhost:9092",
              "group.id": "citibike-writer",
              "enable.auto.commit": False})
c.subscribe(["citibike.station_status"])

conn = psycopg2.connect("dbname=citibike")
while True:
    msg = c.poll(1.0)
    if msg is None: continue
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO station_status VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
            (msg.key().decode(), msg.value()["num_bikes_available"],
             msg.value()["num_docks_available"], msg.timestamp())
        )
        conn.commit()
    c.commit(message=msg)
```

### AI Use Case

**AI-driven project templates.** "Build me a streaming pipeline
that polls X API and writes to Y database" → AI generates
producer + consumer skeleton. The Principal's edge: faster project
kickoff.

### CTO / Principal Motivation

End-to-end projects are **the interview gold standard**. The
candidate who can talk through a complete pipeline (source →
producer → topic → consumer → sink → monitoring) demonstrates
the seniority the job requires. CTOs hire on this.

---

## Lesson 2 — Quiz: Project: Citi Bikes

### Theory

Validate: complete pipeline design, error handling, schema choice,
monitoring, scaling.

### Practical Example

The 5-question project drill:

1. How would you handle GBFS API downtime?
2. Schema evolution if GBFS adds a field?
3. How would you scale to 100 cities?
4. How would you detect data quality issues?
5. How would you replay the past 30 days?

### AI Use Case

AI mock project review with feedback.

### CTO / Principal Motivation

Project-style drills are the **highest signal in interviews**.
Principals who've built 5 end-to-end pipelines interview at a
different level than those who've only read.

---

# Module 3 · Data Schema & Apache Avro (8 lessons)

## Lesson 1 — Data Schema Handling in Kafka (Video)

### Theory

Why Kafka needs explicit schemas. Mental model:

- **Default Kafka** — bytes only; consumers must guess structure.
- **Schema required** when: multiple teams consume the same topic,
  schema evolves over time, regulatory audit requires structure.
- **Schema formats** — JSON Schema, Avro, Protobuf. Avro is the
  Kafka default (compact binary + schema registry).
- **Schema Registry** — central service for schema versions; enforces
  compatibility.

### Practical Example

The three schema formats compared:

| Format | Size | Speed | Tooling |
|--------|------|-------|---------|
| JSON | Large (verbose) | Slow parse | Universal |
| Avro | Small (binary) | Fast | Schema Registry |
| Protobuf | Small (binary) | Fastest | Various |

A 1 KB JSON event → 200 bytes Avro → 250 bytes Protobuf.

### AI Use Case

**AI-generated schema from samples.** "Generate an Avro schema
for these 100 JSON events" → AI produces a `.avsc` file. The
Principal's edge: 10× faster schema authoring.

### CTO / Principal Motivation

Schema standardization is **the prerequisite for cross-team
Kafka**. Without schemas, every consumer duplicates parsing logic.
The Principal's deliverable: a **schema registry standard** with
mandatory enforcement at producer-side.

---

## Lesson 2 — Schemas & Serialization (Article)

### Theory

Serialization in depth. Mental model:

- **Serializer** — Python object → bytes for Kafka.
- **Deserializer** — bytes → Python object on consumer.
- **Built-in serializers** in `confluent-kafka`:
  - `StringSerializer`, `StringDeserializer`
  - `IntegerSerializer`, `IntegerDeserializer`
  - `JSONSerializer`, `JSONDeserializer`
  - `AvroSerializer`, `AvroDeserializer` (require Schema Registry)
  - `ProtobufSerializer`, `ProtobufDeserializer`

### Practical Example

A JSON producer/consumer:

```python
from confluent_kafka import Producer, Consumer
from confluent_kafka.serialization import (
    StringSerializer, JSONSerializer, SerializationContext, MessageField
)

serializer = JSONSerializer(lambda obj: obj, StringSerializer("utf_8"))
producer = Producer({"bootstrap.servers": "localhost:9092"})

event = {"user_id": "u1", "action": "click", "ts": 1234567890}
producer.produce(
    "events",
    key=event["user_id"],
    value=event,
    on_delivery=lambda err, msg: print(f"delivered: {err or 'ok'}")
)
producer.flush()
```

### AI Use Case

**AI-generated serializers.** AI produces typed serializers for
common event types. The Principal's edge: typed pipelines without
manual boilerplate.

### CTO / Principal Motivation

Serializer standardization is **the typed-API equivalent** of the
Kafka producer/consumer wrappers. Together they form the **internal
Kafka SDK**.

---

## Lesson 3 — Apache Avro Introduction (Video)

### Theory

Avro in 60 seconds. Mental model:

- **Schema-first** — `.avsc` JSON file defines structure.
- **Compact binary** — 2-4× smaller than JSON.
- **Self-describing** — schema travels with data (in the header
  when using Schema Registry).
- **Fast** — no parsing, just byte slicing.
- **Schema evolution** — backward, forward, full compatibility.

### Practical Example

An Avro schema:

```json
{
  "type": "record",
  "name": "ClickEvent",
  "namespace": "com.example.events",
  "fields": [
    {"name": "user_id", "type": "string"},
    {"name": "url", "type": "string"},
    {"name": "ts", "type": "long", "logicalType": "timestamp-millis"},
    {"name": "country", "type": ["null", "string"], "default": null}
  ]
}
```

### AI Use Case

**AI-generated Avro schemas.** "Avro schema for a clickstream
event with user, URL, timestamp, country" → AI produces `.avsc`.
The Principal's edge: 5× faster schema authoring.

### CTO / Principal Motivation

Avro adoption is the **data-governance accelerator**. With Avro +
Schema Registry, you get schema evolution, audit trail, and
typed APIs for free. The Principal's standard: "all topics use
Avro + Schema Registry."

---

## Lesson 4 — Avro Complex Data Types (Video)

### Theory

Avro's complex types. Mental model:

- **records** — named struct.
- **enums** — fixed string set.
- **arrays** — ordered list of same type.
- **maps** — string → value.
- **unions** — multiple types in one field (often `["null",
  "actual_type"]` for nullable).
- **nested records** — record inside record.

### Practical Example

A nested event schema:

```json
{
  "type": "record",
  "name": "OrderEvent",
  "fields": [
    {"name": "order_id", "type": "string"},
    {"name": "user", "type": {
        "type": "record",
        "name": "User",
        "fields": [
          {"name": "id", "type": "string"},
          {"name": "email", "type": "string"}
        ]
    }},
    {"name": "items", "type": {
        "type": "array",
        "items": {
          "type": "record",
          "name": "Item",
          "fields": [
            {"name": "sku", "type": "string"},
            {"name": "qty", "type": "int"},
            {"name": "price", "type": "double"}
          ]
        }
    }}
  ]
}
```

### AI Use Case

**AI-driven schema refactoring.** AI normalizes nested schemas to
canonical form. The Principal's edge: consistent schema design.

### CTO / Principal Motivation

Complex Avro types are the **price of admission** for modeling
real-world events. The Principal's deliverable: a **schema style
guide** with examples per use-case.

---

## Lesson 5 — Avro & Schema Evolution (Article)

### Theory

Schema evolution rules. Mental model — the four compatibilities:

| Compatibility | Rule |
|---------------|------|
| **Backward** | New schema can read old data (consumer upgrading first). |
| **Forward** | Old schema can read new data (producer upgrading first). |
| **Full** | Both directions. |
| **None** | No checks. |

The most common evolution patterns:

- **Add optional field** — backward + forward compatible.
- **Remove field** — backward only (default value required).
- **Rename field** — NOT compatible (use aliases).

### Practical Example

Backward-compatible evolution:

```json
// v1
{"name": "user_id", "type": "string"}

// v2 — add optional country
{"name": "user_id", "type": "string"},
{"name": "country", "type": ["null", "string"], "default": null}
```

A v1 consumer can read v2 data (country is null). A v2 consumer
can read v1 data (defaults applied). **Backward + forward
compatible.**

### AI Use Case

**AI-driven compatibility checker.** AI simulates both old and new
schema reading each other's data. The Principal's edge: catch
incompatible schemas before deploy.

### CTO / Principal Motivation

Schema evolution is **the long-term reliability lever**. A schema
registry without proper compatibility settings is a time bomb.
The Principal's standard: "every topic is configured with
backward compatibility; breaking changes require new topic."

---

## Lesson 6 — Schema Registry in Kafka (Video)

### Theory

Schema Registry in depth. Mental model:

- **Service** — REST API (`POST /subjects/{name}/versions`).
- **Storage** — internal `_schemas` topic (or MySQL/Postgres).
- **Compatibility** — global or per-subject setting.
- **Subject naming** — default `<topic>-value` and `<topic>-key`.
- **Schema IDs** — each version has a numeric ID; serialized data
  includes the ID for lookup.

### Practical Example

Register and use a schema:

```bash
# Register schema
curl -X POST http://schema-registry:8081/subjects/events-value/versions \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d '{"schema": "{\"type\":\"record\",\"name\":\"Event\",\"fields\":[{\"name\":\"id\",\"type\":\"string\"}]}"}'
```

```python
# Producer with Schema Registry
from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer

sr = SchemaRegistryClient({"url": "http://schema-registry:8081"})
avro_ser = AvroSerializer(sr, schema_str)

p = Producer({"bootstrap.servers": "localhost:9092"})
p.produce("events", value={"id": "abc"}, serializer=avro_ser)
p.flush()
```

### AI Use Case

**AI-driven schema registration.** AI registers schemas from
`.avsc` files, checks compatibility, flags breaking changes. The
Principal's edge: zero-touch schema deployment.

### CTO / Principal Motivation

Schema Registry is **the most leveraged single service** in a
Kafka org. One registry replaces 100 email threads about
"what does this field mean." CTOs fund it because it enables
data contracts.

---

## Lesson 7 — Schema Registry (Article)

### Theory

Schema Registry article — advanced topics. Mental model:

- **Compatibility levels** — `BACKWARD`, `FORWARD`, `FULL`, `NONE`,
  `BACKWARD_TRANSITIVE`, etc.
- **Per-subject override** — some topics can be `FULL`, others
  `BACKWARD`.
- **Schema normalization** — map, decimal logical types, default
  values normalization.
- **Exporters** — replicate schemas across regions.
- **Custom modes** — Confluent has `READ`/`WRITE` mode.

### Practical Example

Set compatibility per subject:

```bash
# Set per-subject compatibility
curl -X PUT http://schema-registry:8081/config/orders-value \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d '{"compatibility": "FULL"}'

# Check compatibility before deploy
curl -X POST http://schema-registry:8081/compatibility/subjects/orders-value/versions/latest \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d '{"schema": "..."}'
```

### AI Use Case

**AI-driven compatibility policy.** AI analyzes schema evolution
history and recommends compatibility level per topic. The
Principal's edge: safer evolution by default.

### CTO / Principal Motivation

Per-subject compatibility policies are **the safety net** for
multi-team Kafka. The Principal's deliverable: a **compatibility
matrix** — which topics are FULL, which are BACKWARD, and why.

---

## Lesson 8 — Quiz: Data Schema & Apache Avro

### Theory

Validate: Avro schema authoring, complex types, evolution rules,
Schema Registry usage, compatibility levels.

### Practical Example

The 10-question drill:

1. Schema evolution rule for adding required field?
2. Difference between BACKWARD and FORWARD?
3. Avro schema for nullable field?
4. Why use Schema Registry vs schema in code?
5. What's the schema ID used for in serialized data?

### AI Use Case

AI-generated schema-drill exercises.

### CTO / Principal Motivation

Schema fluency is **the prerequisite for production-grade
Kafka**. Without schema discipline, every team has data-quality
fires.

---

# Closing Notes

## The Promotion Path from this Course

| Level        | Skill unlocked by this course | Compensation signal |
|--------------|-------------------------------|---------------------|
| Senior DE    | Writes Python producer/consumer for new pipelines | $150-200k |
| Staff DE     | Designs end-to-end pipelines; reviews schemas; sets Kafka standards | $200-280k |
| Principal DE | Owns the internal Kafka SDK; sets schema evolution policy; runs the registry | $280-400k |
| Director / VP | Owns the streaming platform budget; sets cross-team Kafka standards | $350-500k+ |
| CTO          | Makes Confluent vs MSK vs self-hosted strategic call; signs off on schema contracts | $400-700k+ |

## The Python Kafka Principal's Strategic Toolkit

Six decisions a Principal owns:

1. **`confluent-kafka` vs `kafka-python` vs `aiokafka`** — default
   `confluent-kafka` for performance; `aiokafka` only for asyncio
   stacks.
2. **Idempotent producer as default** — every new producer in the
   fleet has `enable.idempotence=true`.
3. **Manual commit as default** — every consumer has
   `enable.auto.commit=false`.
4. **Cooperative-sticky rebalance** — every consumer uses it to
   minimize rebalance downtime.
5. **Avro + Schema Registry as default** — JSON only for legacy;
   all new topics use Avro.
6. **Backward-compat schema policy** — every topic is BACKWARD; new
   topics for breaking changes.

## The CTO Pitch (Python Kafka flavor)

When the CTO walks into a board meeting, the streaming platform
story is: "we ship 10× faster than our competitors because our
internal Kafka SDK + schema registry means a new pipeline is 50
lines of Python, not 5000 lines of glue code." That's the leverage
this course unlocks.

## Cross-References

- **Kafka Fundamentals** — `07_kafka_fundamentals.md` (the
  prerequisite course).
- **Kafka Stream Processing & Production CTO plan** —
  `kafka_stream_processing_cto_learning_plan.md` (the operational
  layer; this is the code-level companion).
- **AWS DE CTO plan** — `aws_de_cto_learning_plan.md` (Kinesis vs
  MSK decision tree).
