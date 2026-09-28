# Kafka Stream Processing & Production — CTO / Principal Study Plan

**Source course:** Data Vidhya — *Kafka Stream Processing & Production*
by Darshil Parmar.
**Course URL:** https://datavidhya.com/learn/ (intermediate Kafka course)
**Coverage:** 4 modules • 16 lessons
**Audience:** Data engineers targeting **Staff → Principal → Director →
VP/CTO** track with deep Kafka + Kafka Streams + Kafka Connect + ksqlDB
expertise.

> **How to use this file.** Each lesson has four lenses:
>
> 1. **Theory** — mental model and the Kafka primitive.
> 2. **Practical Example** — concrete numbers, code, decisions.
> 3. **AI Use Case** — where GenAI / ML slots in or on top of this lesson.
> 4. **CTO / Principal Motivation** — career reason; what decisions
>    you're trusted with at senior levels.
>
> Kafka is the **default streaming backbone** for data engineering in
> 2026. This course extends the Kafka Fundamentals course by drilling
> the **operational layer**: Kafka Connect (300+ pre-built connectors),
> Kafka Streams (stateful stream processing library), ksqlDB (SQL on
> streams), and the production / monitoring / security layer.
>
> The Principal-level Kafka engineer can operate a 100-broker cluster,
> tune producer/consumer for sub-second p99, debug a hot-partition
> incident at 2 AM, and explain to a CTO why we're spending $X/month
> on MSK vs Confluent Cloud.

---

# Module 1 · Kafka Connect (6 lessons)

## Lesson 1 — Kafka Connect Introduction (Video)

### Theory

Kafka Connect is the **integration framework for Kafka**. Mental model:

- **Source connector** — pulls data from external systems into Kafka.
- **Sink connector** — pushes data from Kafka into external systems.
- **Worker** — JVM process that runs connectors.
- **Connector plugin** — the actual integration code (JDBC, Debezium,
  S3, Elasticsearch, etc.).
- **300+ certified connectors** in the Confluent Hub cover almost every
  common source/sink.

Why Connect exists: instead of writing 500 producers/consumers
custom-coded for each system, you configure a connector. One
config file replaces a multi-week engineering project.

### Practical Example

Three connectors cover 80% of pipelines:

| Connector | Use case | Frequency |
|-----------|----------|-----------|
| Debezium PostgreSQL | OLTP → Kafka (CDC) | Real-time |
| JDBC Source | SQL → Kafka (poll) | Hourly/daily |
| S3 Sink | Kafka → S3 | Real-time |
| Elasticsearch Sink | Kafka → search | Real-time |
| Snowflake Sink | Kafka → warehouse | Real-time |

```bash
# Start a JDBC source connector
curl -X POST http://connect:8083/connectors \
  -H "Content-Type: application/json" \
  -d '{
    "name": "postgres-source",
    "config": {
      "connector.class": "io.confluent.connect.jdbc.JdbcSourceConnector",
      "connection.url": "jdbc:postgresql://db:5432/orders",
      "connection.user": "kafka",
      "connection.password": "...",
      "table.whitelist": "orders,order_items",
      "mode": "incrementing",
      "incrementing.column.name": "id",
      "topic.prefix": "pg-"
    }
  }'
```

### AI Use Case

**AI-driven connector configuration.** "Connect my Postgres DB to
Kafka with CDC, partition by tenant, write to topic pg-orders" →
AI generates the full connector config. The Principal's edge:
3× faster connector onboarding.

### CTO / Principal Motivation

Connect is **the first thing a Principal standardizes**. Without a
Connect platform, every team writes custom producers/consumers and
the company's Kafka spend grows linearly with headcount. With
Connect, you add a team and the connector cost is $0. The CTO's
narrative: "we ship 10× faster because the integration layer is
already built."

---

## Lesson 2 — Kafka Connect Guide (Article)

### Theory

The Connect framework's deep architecture. Mental model:

- **Standalone vs Distributed mode** — Standalone is for development;
  Distributed is for production (horizontal scaling, fault tolerance).
- **Tasks** — units of parallelism within a connector. A source
  connector reading 10 tables can run 10 tasks in parallel.
- **Offset commit** — Connect commits Kafka offsets via an internal
  topic (`__consumer_offsets`).
- **Dead letter queue (DLQ)** — failed records go to `<topic>.dlq`
  instead of blocking the connector.
- **Transforms (SMTs)** — Single Message Transforms modify records
  in-flight: insert header, mask field, route to topic.

### Practical Example

A S3 sink with partitioning and DLQ:

```json
{
  "name": "s3-sink",
  "config": {
    "connector.class": "io.confluent.connect.s3.S3SinkConnector",
    "s3.bucket.name": "data-lake-raw",
    "topics.dir": "events",
    "flush.size": 1000,
    "rotate.interval.ms": 60000,
    "partition.duration.ms": 3600000,
    "path.format": "'year'=YYYY/'month'=MM/'day'=dd/'hour'=HH",
    "format.class": "io.confluent.connect.s3.format.parquet.ParquetFormat",
    "partitioner.class": "io.confluent.connect.storage.partitioner.TimeBasedPartitioner",
    "errors.deadletterqueue.topic.name": "events.dlq",
    "errors.tolerance": "all"
  }
}
```

This writes Parquet to S3 partitioned by date, with DLQ for bad
records — production-ready in 30 lines of config.

### AI Use Case

**AI-driven schema drift handling.** AI watches SMT outputs, detects
schema evolution, generates new SMT chains. The Principal's edge:
zero-downtime schema evolution.

### CTO / Principal Motivation

The Connect Guide is the **Standard Operating Procedure** for any
data integration. The Principal owns the **connector library**; the
CTO owns the **vendor consolidation narrative** ("we use 5 connectors
instead of 50 custom integrations").

---

## Lesson 3 — Database Connect in Kafka (Video)

### Theory

Two patterns for getting database changes into Kafka:

| Pattern | Tool | Latency | Cost | Use case |
|---------|------|---------|------|----------|
| **Log-based CDC** | Debezium | Sub-second | $$$ | Real-time, full fidelity |
| **Poll-based** | JDBC Source | Seconds-minutes | $ | Batch, query-driven |
| **Trigger-based** | Custom | Seconds | $$ | Custom transforms |

The decision rule: **use Debezium unless you can't**. Log-based CDC
captures inserts/updates/deletes with full before/after rows; poll-based
catches inserts/updates only.

### Practical Example

Debezium for PostgreSQL:

```bash
curl -X POST http://debezium:8083/connectors \
  -d '{
    "name": "pg-cdc",
    "config": {
      "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
      "database.hostname": "postgres",
      "database.port": "5432",
      "database.dbname": "app",
      "database.user": "debezium",
      "database.password": "...",
      "plugin.name": "pgoutput",
      "publication.autocreate.mode": "filtered",
      "table.include.list": "public.orders",
      "tombstones.on.delete": "false",
      "decimal.handling.mode": "double"
    }
  }'
```

Cost: 1 connector instance per Postgres database = $50/month
compute + Kafka storage cost (~$0.10/GB-month).

### AI Use Case

**AI-driven CDC schema evolution.** AI watches Debezium schema
changes and auto-updates downstream Iceberg schema. The Principal's
edge: zero-downtime schema changes.

### CTO / Principal Motivation

CDC is **the foundation for replication, audit, and real-time
analytics**. The Principal owns the **CDC tool selection**; the
CTO owns the **data replication strategy**.

---

## Lesson 4 — Debezium CDC (Article)

### Theory

Debezium in depth. Mental model:

- **Connector** runs inside Kafka Connect (or Debezium Server).
- **Logical Decoding** (Postgres) / **Binlog** (MySQL) — reads database
  transaction log.
- **Snapshot mode** — initial full read before streaming changes
  (initial, schema_only, never).
- **Tombstone events** — DELETE emits a null record after the delete
  event (for Kafka log compaction).
- **Schema history topic** — Kafka topic storing all schema changes.

### Practical Example

Snapshot + streaming for Postgres:

```json
{
  "snapshot.mode": "initial",
  "snapshot.locking.mode": "minimal",
  "max.queue.size": 8192,
  "max.batch.size": 2048,
  "poll.interval.ms": 100
}
```

The connector takes an initial snapshot of all rows, then streams
changes. Kafka topic receives: INSERT → full row, UPDATE → before/after
envelope, DELETE → null (tombstone).

### AI Use Case

**AI-driven anomaly detection on CDC events.** AI watches the CDC
stream for unusual patterns (mass updates, mass deletes) and alerts.
The Principal's edge: catch data corruption early.

### CTO / Principal Motivation

Debezium is the **most production-proven CDC tool** in 2026.
The Principal owns the **CDC platform**; the CTO owns the
**data freshness narrative**.

---

## Lesson 5 — Handle Kafka Via REST Proxy (Video)

### Theory

The **REST Proxy** lets non-JVM clients (Python, JavaScript, Go) talk
to Kafka over HTTP. Mental model:

- **Confluent REST Proxy** — official; production-grade.
- **Endpoints** — produce, consume, list topics, get metadata.
- **Use case** — when you can't install librdkafka, or you need a
  simple webhook ingestion endpoint.

### Practical Example

A Python webhook producer:

```python
import requests
requests.post(
    "http://rest-proxy:8082/topics/events",
    headers={"Content-Type": "application/vnd.kafka.json.v2+json"},
    json={
        "records": [
            {"value": {"user_id": "u1", "event": "click"}}
        ]
    }
)
```

Cost: REST Proxy is a thin layer — same Kafka cost underneath, plus
$0.10/million HTTP requests.

### AI Use Case

**AI-augmented REST endpoints.** AI watches HTTP traffic, detects
unusual patterns, auto-throttles abusive clients. The Principal's
edge: production-grade public-facing Kafka.

### CTO / Principal Motivation

REST Proxy is **the bridge between SaaS and Kafka**. The Principal
owns the **public ingestion layer**; the CTO owns the **SaaS
integration strategy**.

---

## Lesson 6 — Quiz: Kafka Connect

### Theory

The quiz validates: connector selection, mode (standalone vs
distributed), task parallelism, DLQ handling, SMT knowledge.

### Practical Example

The 5-question mental check before designing any Connect pipeline:

1. Source vs Sink?
2. Standalone vs Distributed?
3. How many tasks?
4. DLQ enabled?
5. SMT chain?

### AI Use Case

AI-generated flashcards from connector docs.

### CTO / Principal Motivation

Connect mastery is the **prerequisite for Kafka production**. If
you can't design a connector, you can't run a Kafka pipeline at
scale.

---

# Module 2 · Streaming Fundamentals (5 lessons)

## Lesson 1 — Stream Processing Fundamentals

### Theory

Stream processing = **continuous computation on unbounded data**.
Mental model:

- **Event time** vs **processing time** — always process on event time.
- **State** — what the operator remembers between events.
- **Windowing** — bounding a stream into finite slices.
- **Watermarks** — event-time progress markers.
- **Triggers** — when to emit results.
- **Exactly-once semantics** — guarantees on duplicates.

### Practical Example

The three stream-processing paradigms:

| Paradigm | Tools | Use case |
|----------|-------|----------|
| **Native streams** | Kafka Streams, Flink | Stateful, event-time, low latency |
| **Micro-batch** | Spark Structured Streaming | Throughput, ease of use |
| **SQL on streams** | ksqlDB, Materialize | Simple transforms, SQL skills |

### AI Use Case

**AI-optimized stream windows.** AI watches query patterns, suggests
window sizes. The Principal's edge: lower latency, lower compute.

### CTO / Principal Motivation

Stream-processing paradigm choice is **the CTO's strategic decision**.
The Principal owns the **decision framework** (native vs micro-batch
vs SQL); the CTO owns the **stream-processing platform** narrative.

---

## Lesson 2 — Window Function in Data Streaming (Video)

### Theory

Windowing bounds unbounded streams into finite groups. Mental model:

- **Tumbling window** — fixed-size, non-overlapping (e.g., 5-minute
  buckets).
- **Sliding window** — fixed-size, overlapping (e.g., last 10 minutes,
  emit every 1 minute).
- **Session window** — dynamic, gap-based (e.g., 30-minute inactivity
  ends a session).
- **Global window** — no time bound (entire stream).

### Practical Example

Tumbling count per user in 5-minute windows with Kafka Streams:

```java
KStream<String, Event> events = builder.stream("events");
KTable<Windowed<String>, Long> counts = events
    .groupByKey()
    .windowedBy(TimeWindows.ofSizeWithNoGrace(Duration.ofMinutes(5)))
    .count();
counts.toStream()
      .foreach((windowedKey, count) ->
          System.out.println(windowedKey.key() + "@" + windowedKey.window() +
                             " = " + count));
```

### AI Use Case

**AI-driven window sizing.** AI watches user activity patterns and
recommends session-window gaps. The Principal's edge: better
sessionization accuracy.

### CTO / Principal Motivation

Windowing choices affect **business KPIs directly** (active users,
session duration, conversion). The Principal owns the **windowing
standard**; the CTO owns the **metric definition** narrative.

---

## Lesson 3 — KSQL Masterclass (Video)

### Theory

KSQL (legacy) / ksqlDB (current) is **SQL on Kafka streams**. Mental
model:

- **STREAM** — unbounded, append-only.
- **TABLE** — bounded by key, latest value per key (changelog-like).
- **CREATE STREAM AS SELECT** — continuous query.
- **CREATE TABLE AS SELECT** — materialized aggregate.
- **Push queries** — emit as new events arrive.
- **Pull queries** — point lookup (TABLE only).

### Practical Example

Real-time count of clicks per URL:

```sql
CREATE STREAM clicks (url STRING, user_id STRING)
  WITH (KAFKA_TOPIC='clicks', VALUE_FORMAT='JSON');

CREATE TABLE clicks_per_url AS
  SELECT url, COUNT(*) AS clicks
  FROM clicks
  WINDOW TUMBLING (SIZE 5 MINUTE)
  GROUP BY url
  EMIT CHANGES;
```

This creates a continuous query that emits URL-click-count updates
every 5 minutes.

### AI Use Case

**AI-generated ksqlDB queries.** AI translates business logic
("show me active users per minute") into ksqlDB SQL. The Principal's
edge: 5× faster stream app development.

### CTO / Principal Motivation

ksqlDB is **the lowest-friction entry to stream processing**. The
Principal owns the **SQL-on-streams standard**; the CTO owns the
**democratization of streaming** narrative.

---

## Lesson 4 — ksqlDB (Article)

### Theory

ksqlDB in depth. Mental model:

- **Server** — runs the ksqlDB cluster.
- **CLI** — interactive SQL shell.
- **Connectors** — integrate with Kafka Connect under the hood.
- **UDF / UDAF** — user-defined functions (Java).
- **State stores** — RocksDB-backed, replicated via Kafka log.

### Practical Example

A complete analytics pipeline in ksqlDB:

```sql
-- Source streams
CREATE STREAM raw_events (
  user_id STRING,
  event_type STRING,
  ts BIGINT
) WITH (KAFKA_TOPIC='events', VALUE_FORMAT='JSON', TIMESTAMP='ts');

-- Filter + project
CREATE STREAM clicks AS
  SELECT user_id, ts FROM raw_events
  WHERE event_type = 'click';

-- Windowed aggregation
CREATE TABLE clicks_per_user_per_minute AS
  SELECT user_id, COUNT(*) AS clicks
  FROM clicks
  WINDOW TUMBLING (SIZE 1 MINUTE)
  GROUP BY user_id
  EMIT CHANGES;
```

This creates a real-time "clicks per user per minute" table — queryable
via pull query, pushable to downstream streams.

### AI Use Case

**AI-driven ksqlDB migration.** AI converts Spark/Flink jobs to
ksqlDB queries where possible. The Principal's edge: lower compute
cost.

### CTO / Principal Motivation

ksqlDB is **the SQL skill-multiplier on streams**. The Principal
owns the **ksqlDB adoption**; the CTO owns the **team productivity**
narrative.

---

## Lesson 5 — Quiz: Streaming Fundamentals

### Theory

The quiz validates: paradigm selection (native vs micro-batch vs
SQL), window choice (tumbling vs sliding vs session), ksqlDB
fluency, state management.

### Practical Example

The 5-question mental check:

1. Tumbling vs sliding window?
2. When to use ksqlDB vs Kafka Streams vs Flink?
3. How to handle late-arriving events?
4. How to scale state stores?
5. How to guarantee exactly-once?

### AI Use Case

AI-generated flashcards and stream-app drilling exercises.

### CTO / Principal Motivation

Streaming fundamentals are the **prerequisite for any real-time
system design**.

---

# Module 3 · Production & Operations (3 lessons)

## Lesson 1 — Performance & Monitoring

### Theory

Production Kafka performance and monitoring. Mental model:

- **Producer tuning:**
  - `linger.ms` — batch window (5-100 ms).
  - `batch.size` — bytes per batch (16 KB - 1 MB).
  - `compression.type` — snappy, lz4, zstd.
  - `acks` — 0 (fire-and-forget), 1 (leader), all (replicated).
- **Consumer tuning:**
  - `fetch.min.bytes` — minimum fetch size (1 KB - 1 MB).
  - `max.poll.records` — max records per poll.
  - `isolation.level` — read_committed (with EOS) vs read_uncommitted.
- **Broker tuning:**
  - `num.network.threads`, `num.io.threads` — CPU-bound.
  - `log.segment.bytes` — segment size (default 1 GB).
  - `num.partitions` — parallelism.

### Practical Example

Producer config for high throughput:

```yaml
# producer.yaml
bootstrap.servers: broker:9092
acks: all
compression.type: zstd
linger.ms: 50
batch.size: 65536
buffer.memory: 67108864
retries: 10
enable.idempotence: true
max.in.flight.requests.per.connection: 5
```

At 10K msgs/sec × 1 KB, this config delivers ~100 MB/sec per producer
with exactly-once semantics.

**Monitoring metrics:**

- `kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec`
- `kafka.server:type=ReplicaFetcherManager,name=MaxLag`
- `kafka.consumer:type=consumer-fetch-manager-metrics,name=records-lag-max`

### AI Use Case

**AI-driven Kafka tuning.** AI watches producer/consumer metrics and
recommends config changes (increase batch size, switch compression).
The Principal's edge: 2× throughput from AI tuning.

### CTO / Principal Motivation

Performance tuning is **the difference between a $5K/month Kafka
bill and a $50K/month one**. The Principal owns the **tuning
playbook**; the CTO owns the **Kafka cost** narrative.

---

## Lesson 2 — Running Kafka in Production

### Theory

The production Kafka stack. Mental model:

- **Zookeeper vs KRaft** — KRaft (Kafka 3.3+) removes Zookeeper
  dependency; now the default.
- **Replication factor** — typically 3 for production.
- **min.insync.replicas** — 2 (always confirm 2 replicas written).
- **Tiered storage** — Kafka 3.6+ offloads cold segments to S3.
- **Multi-region** — MirrorMaker 2 (MM2), Confluent Cluster Linking.
- **Self-hosted vs MSK vs Confluent Cloud** — the build-vs-buy call.

### Practical Example

A 5-broker production cluster:

```yaml
# server.properties
broker.id: 0
listeners: PLAINTEXT://broker:9092
log.dirs: /var/kafka/data
num.partitions: 12
default.replication.factor: 3
min.insync.replicas: 2
unclean.leader.election.enable: false
compression.type: zstd
log.retention.hours: 168
log.segment.bytes: 1073741824
```

Cost: 5 × `kafka.m5.2xlarge` on AWS = $5k/month for the cluster,
plus EBS storage (~$0.10/GB-month), plus data transfer.

### AI Use Case

**AI-driven capacity planning.** AI watches disk usage, partition
count, broker CPU and recommends: add broker, increase partition
count, enable tiered storage. The Principal's edge: predictable
scaling.

### CTO / Principal Motivation

The "self-hosted vs managed" decision is **the CTO's strategic call**.
At <50 GB/day, self-hosted is fine. Above 500 GB/day, MSK Serverless
or Confluent Cloud wins on operational cost. Above 5 TB/day, on-prem
can win if you have the team. The Principal owns the **runbook**;
the CTO owns the **TCO model**.

---

## Lesson 3 — Quiz: Production & Operations

### Theory

The quiz validates: producer/consumer tuning, broker sizing,
replication strategy, monitoring setup, runbook fluency.

### Practical Example

The 10-question on-call drill:

1. Broker disk full — what do you do?
2. Consumer lag growing — root causes?
3. Hot partition detected — how to fix?
4. Leader election storm — what now?
5. KRaft vs ZK — which to choose?

### AI Use Case

AI-driven incident simulator. Generate scenarios, drill response.

### CTO / Principal Motivation

Production mastery is **the difference between a Senior and Staff
Kafka engineer**. The Principal owns the **runbook**; the CTO owns
the **incident narrative**.

---

# Module 4 · Interview Prep (2 lessons)

## Lesson 1 — Kafka Interview Questions

### Theory

The 30+ Kafka interview questions every Principal can answer cold.
Mental model — group by category:

- **Fundamentals (1-10):** What is Kafka? Topic vs partition? Consumer
  group vs individual consumer?
- **Producer/Consumer (11-15):** Idempotent producer? Exactly-once?
  Consumer offset commit?
- **Architecture (16-22):** Leader election? ISR? Replication?
  Hot partition? Backpressure?
- **Operations (23-28):** Kafka monitoring? KRaft vs ZK? Capacity
  planning? Tiered storage?
- **Advanced (29-32):** MirrorMaker 2 vs Cluster Linking? Kafka
  Streams vs Flink? ksqlDB internals?

### Practical Example

The "explain exactly-once semantics" answer (Principal-level):

> Exactly-once in Kafka has three layers: (1) idempotent producer
> uses producer ID + sequence number to dedupe retries within a
> session. (2) Transactional producer uses `initTransactions()` +
> `beginTransaction()` + `commit()` to atomically write to multiple
> topics including `__consumer_offsets`. (3) Read-isolation
> `read_committed` ensures consumers only see committed records.
> Combined, this gives end-to-end exactly-once between Kafka topics.
> For Kafka-to-sink exactly-once, use Kafka Connect with the
> sink connector's EOS support.

### AI Use Case

**AI mock interviewer.** Practice 50 Kafka interview questions
with AI scoring. The Principal's edge: drill before the interview.

### CTO / Principal Motivation

Interview questions are **the language of evaluation**. The
Principal who can explain KRaft, EOS, and MM2 in 3 minutes each
demonstrates Staff-level depth. The CTO who interviews candidates
uses these questions to calibrate.

---

## Lesson 2 — Quiz: Interview Prep

### Theory

The capstone quiz validates: 30-question mastery, whiteboarding a
Kafka design, on-call simulation.

### Practical Example

Whiteboard drills:

- "Design a clickstream pipeline for 1M events/sec."
- "Design a CDC pipeline from Postgres to Snowflake."
- "Diagnose a Kafka cluster with 30-second consumer lag."

### AI Use Case

AI-generated whiteboarding scenarios with grading rubric.

### CTO / Principal Motivation

The interview-prep module is **the final-mile artifact**. The
Principal's deliverable: 30 questions answered in 3 minutes each,
3 whiteboarding drills rehearsed, 5 on-call scenarios simulated.

---

# Closing Notes

## The Promotion Path from this Course

| Level        | Skill unlocked by this course | Compensation signal |
|--------------|-------------------------------|---------------------|
| Senior DE    | Connects Kafka to systems; writes basic Kafka Streams jobs | $150-200k |
| Staff DE     | Operates production Kafka clusters; tunes for throughput; debugs incidents | $200-280k |
| Principal DE | Designs org-wide Kafka standards; leads vendor selection (Confluent vs MSK); sets security baseline | $280-400k |
| Director / VP | Owns streaming platform budget; manages on-call rotation; platform-level FinOps | $350-500k+ |
| CTO          | Kafka vs Pulsar vs Redpanda vs Kinesis strategy; multi-region DR strategy | $400-700k+ |

## The Kafka Principal's Strategic Toolkit

Six decisions a Principal owns:

1. **Self-hosted vs MSK vs Confluent Cloud** — the build-vs-buy call.
   Decision tree: <50 GB/day → self-hosted fine; 50-500 → MSK Serverless;
   500+ → Confluent Cloud. (These thresholds shift as prices change.)
2. **KRaft vs Zookeeper** — KRaft for new clusters in 2026+; never
   deploy Zookeeper for greenfield.
3. **Tiered storage** — enable for clusters with >1 PB retention need;
   saves 60-80% on storage cost.
4. **Schema registry** — mandatory for any org with >3 Kafka producers.
5. **MirrorMaker 2 vs Cluster Linking** — MM2 for OSS, Cluster Linking
   for Confluent Cloud.
6. **EOS vs at-least-once** — default to EOS for new pipelines; at-
   least-once only when EOS overhead is unacceptable.

## The Two CTO Pillars (Kafka-flavored)

This course is the **technical pillar** for streaming-platform CTOs.
The **other pillar** is the build-vs-buy narrative — why we run our
own Kafka vs paying Confluent for managed. CTOs who have both
pillars close deals 5× faster.

## Cross-References

- **AWS DE CTO plan** — `aws_de_cto_learning_plan.md` (Kinesis vs
  MSK decision tree).
- **Azure DE CTO plan** — `azure_de_cto_learning_plan.md` (Event Hubs
  vs Kafka).
- **DE System Design CTO plan** — `de_system_design_cto_learning_plan.md`
  (Kafka in the architecture pattern).
- **Kafka Fundamentals** — `07_kafka_fundamentals.md` (the prerequisite
  course this builds on).
