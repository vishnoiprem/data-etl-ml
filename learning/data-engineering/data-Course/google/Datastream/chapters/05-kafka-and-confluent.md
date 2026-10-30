# 5.1 — Kafka, Confluent & the GCP Path

> **Section 5 · The Confluent Kafka Path · Lecture 5.1 · 30 min**

## 🎯 What you will learn

- How a Confluent Kafka cluster is structured, and what you are actually
  paying for
- The **Confluent Cloud** model — clusters, topics, and the API keys
- How the **Google Cloud Functions sink connector** wires Kafka to Cloud Run
- Why the Kafka path and the Datastream path have **different semantics**,
  and what that means for your table
- The idempotency problem, and the three ways to fix it

---

## 🧠 Concept

### The two paths, side by side

This course covers two pipeline shapes. They look similar — Kafka in, a
database out — but they are different problems.

| | Datastream → BigQuery | Kafka → Cloud Run → Cloud SQL |
|---|---|---|
| **Source** | A database's binary log | A Kafka topic |
| **Semantics** | **Stateful** — the table converges | **Stateless** — each message is a fact |
| **Delivery** | Exactly-once within the merge | **At-least-once** |
| **Ordering** | Preserved (single source order) | Per-partition only |
| **Storage** | BigQuery (columnar) | PostgreSQL (row-based) |
| **Typical latency** | Seconds | Milliseconds |
| **State kept** | The full current table | None, unless you dedupe |

The row that matters is **state**. The Datastream destination converges:
replay the whole stream and you get the same table. The Cloud SQL
destination does not: it is a growing append of whatever arrives, and
the same message can arrive twice.

### How Kafka is structured

```text
  Producer ──▶ Topic ──▶ Partition 0 ──▶ Consumer group A ──▶ consumer
                    ├──▶ Partition 1 ──▶ Consumer group B ──▶ consumer
                    └──▶ Partition 2 ──▶ (each partition is ordered)
```

**A topic** is a named stream of records. **A partition** is an ordered
sub-stream within the topic. Records within a partition are ordered;
records across partitions are **not**.

**A consumer group** is a set of consumers that share the partitions of a
topic. Each partition is assigned to exactly one consumer in the group, so
each record is delivered to exactly one consumer in the group — but
records may be **redelivered** if the consumer crashes before committing
its offset.

That is the whole of Kafka's delivery guarantee:

> **At-least-once.** Records are delivered to one consumer in the group,
> and may be redelivered if the consumer fails before committing the
> offset.

### Confluent Cloud

Confluent Cloud is the managed Kafka service. The objects you create:

| Object | What it is | Notes |
|---|---|---|
| **Cluster** | The Kafka brokers | Billed on what you store and what you transfer |
| **Topic** | A named stream | Partitioned; you choose the partition count |
| **API key** | A credential | Can be scoped to specific clusters and topics |
| **Connector** | A managed source or sink | Runs on Confluent's infrastructure |

Billing is worth understanding because it is the most common surprise:

> Confluent Cloud bills on **data stored** (bytes retained per hour) and
> **data transferred** (bytes in and out). Not on messages, not on
> partitions, not on consumers.

A topic with 10 million small messages can cost more than one with 1
million large ones. Message *count* is not the metric.

**The API key is the security boundary.** A key can be scoped to specific
clusters and topics, and it can be given separate `API key` and `Cloud
key` roles. The `API key` is what a client uses to connect; the `Cloud
key` is what the Confluent API uses to manage the cluster. You should
never use a `Cloud key` in an application.

### The Google Cloud Functions sink connector

Confluent's **Google Cloud Functions sink connector** is what wires Kafka
to a Cloud Run Function. It is a Confluent-managed connector, so the
connector itself runs on Confluent's infrastructure — it polls the topic
and POSTs each message to your function's URL.

```text
  Kafka topic
      │
      ▼
  Confluent GCF sink connector
      │  HTTP POST, one per message
      ▼
  Cloud Run Function (2nd gen)
      │  parse, validate
      ▼
  Cloud SQL for PostgreSQL
```

Three properties of this shape that matter:

1. **The connector is stateless from your side.** It holds offsets. If the
   function returns a 4xx, the connector treats it as a permanent failure
   and skips the record; a 5xx, it retries.
2. **The function must be idempotent**, because the connector will
   redeliver on a retry.
3. **The function should return 4xx for a permanently bad message** and
   5xx for a transient failure. Getting this backwards means either
   dropping good data or retrying a poison message forever.

### The idempotency problem, concretely

```text
  1. The function receives message M
  2. The function writes M to PostgreSQL  ← succeeds
  3. The function returns 200
  4. The response is lost in transit
  5. The connector never advances its offset
  6. The connector redelivers M
  7. The function writes M again     ← the row is duplicated
```

Steps 2–4 are not a rare race. They are a normal consequence of a
distributed system, and they will happen at a rate proportional to your
message volume.

### The three fixes

**1. A unique constraint on the business key.** The best fix, and you want
it regardless:

```sql
CREATE TABLE transactions (
    transaction_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    amount NUMERIC NOT NULL,
    ...
);
```

With the constraint, the duplicate insert raises a duplicate-key error.
Catch it and treat it as success:

```python
try:
    with connection.cursor() as cursor:
        cursor.execute(statement, values)
    connection.commit()
except psycopg2.errors.UniqueViolation:
    connection.rollback()
    log.info("duplicate transaction %s — already stored", row["transaction_id"])
```

**2. `INSERT ... ON CONFLICT DO NOTHING`.** Postgres-specific, and it
avoids the exception entirely:

```sql
INSERT INTO transactions (transaction_id, customer_id, amount)
VALUES (%s, %s, %s)
ON CONFLICT (transaction_id) DO NOTHING;
```

**3. An idempotency key table.** The function checks whether it has seen
the key before. Works, but it adds a read and a write per message, and it
has its own failure modes.

### The general rule

> The **database** is the last line of defence. Enforce uniqueness where
> the data lives, not only in the application that writes it. The
> application will be retried; the constraint will not.

### Ordering and partitioning — the rule people get wrong

Kafka guarantees ordering **within a partition** and nothing across
partitions. If you produce messages for the same entity to different
partitions, they can be consumed out of order.

So the partitioning key must be the entity key:

| Path | Partition by | Why |
|---|---|---|
| Transactions | `transaction_id` or `customer_id` | All events for one customer stay ordered |
| CDC → Kafka | The **merge key** | Ordering must match the merge's keying |

That last row is the important one, and it is a genuine constraint: **if
you fan a CDC stream out through Kafka, the Kafka partitioning key must be
the same key you merge on.** Otherwise the merge sees the updates for one
row out of order, and the row converges to the wrong value.

---

## 🛠️ Hands-On: The Function

### The three stages

The course ships `project/kafka_to_gcp.py` with the three functions the
course builds, and `project/cloud_function.py` with the deployable handler.

### Stage one — fetch the secret

```python
import os
os.environ.setdefault("SECRET_VALUE", "local-dev-password")

from kafka_to_gcp import fetch_secret

print("fetched:", fetch_secret("db-password"))
```

In production this reads from Secret Manager. The function caches the
value in module scope, because Cloud Run reuses the instance across
invocations.

### Stage two — parse

```python
import json
from kafka_to_gcp import parse_transaction

message = {
    "transaction_id": "t00000001",
    "customer_id": "c000001",
    "amount": 42.50,
    "currency": "EUR",
    "product_id": "p0001",
    "channel": "web",
    "timestamp": "2026-01-15T10:30:00Z",
}

row = parse_transaction(json.dumps(message))
print(json.dumps(row, indent=2))
```

### Stage three — write, parameterised

```python
from kafka_to_gcp import build_insert_sql

print(build_insert_sql())
```

```
INSERT INTO transactions (transaction_id, customer_id, amount, currency, product_id, channel, timestamp, ingested_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
```

Eight placeholders. No value is ever formatted into the string.

### Prove it with an attack

```python
from kafka_to_gcp import parse_transaction, ingest_transaction

message["product_id"] = "p0001'; DROP TABLE transactions; --"
row = parse_transaction(json.dumps(message))

class RecordingCursor:
    def __init__(self, sink):
        self.sink = sink

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, statement, values=None):
        self.sink.append((statement, values))


class RecordingConnection:
    def __init__(self):
        self.statements = []
        self.commits = 0

    def cursor(self):
        return RecordingCursor(self.statements)

    def commit(self):
        self.commits += 1


connection = RecordingConnection()
ingest_transaction(row, connection=connection)

statement, values = connection.statements[0]
print("statement contains 'DROP TABLE'? ", "DROP TABLE" in statement)
print("the payload is in the VALUES?      ", any("DROP TABLE" in str(v) for v in values))
```

```text
statement contains 'DROP TABLE'?  False
the payload is in the VALUES?       True
```

### Replay a recorded message log

```bash
python resources/sample_data.py --output-dir ./sample_data

python project/kafka_to_gcp.py \
    --messages ./sample_data/transactions.ndjson \
    --dry-run
```

```
Kafka → GCP replay summary
----------------------------------------------------
  messages read    : 500
  ingested         : 500
  rejected         : 0
```

### The idempotency demonstration

```python
import json
from kafka_to_gcp import parse_transaction, ingest_transaction

message = {
    "transaction_id": "t00000001",
    "customer_id": "c000001",
    "amount": 42.50,
    "currency": "EUR",
    "product_id": "p0001",
    "channel": "web",
    "timestamp": "2026-01-15T10:30:00Z",
}
body = json.dumps(message)

connection = RecordingConnection()
for _ in range(2):
    ingest_transaction(parse_transaction(body), connection=connection)

print("rows written:", len(connection.statements))
print("-> the same transaction was written twice.")
```

This is exactly what the `PRIMARY KEY` constraint prevents.

### The Cloud SQL schema

```sql
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    customer_id    TEXT NOT NULL,
    amount         NUMERIC NOT NULL,
    currency       TEXT NOT NULL,
    product_id     TEXT NOT NULL,
    channel        TEXT NOT NULL,
    timestamp      TIMESTAMPTZ NOT NULL,
    ingested_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transactions_customer
    ON transactions (customer_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_transactions_timestamp
    ON transactions (timestamp DESC);
```

The `PRIMARY KEY` is the idempotency guarantee. The indexes are for the
queries the dashboard runs — and on Cloud SQL, a missing index on a
growing table is a latency problem that gets worse every week.

---

## 🛠️ Common Errors and Fixes

### `psycopg2.errors.UniqueViolation`

The duplicate the constraint was designed to catch. Catch it and treat it
as success:

```python
try:
    with connection.cursor() as cursor:
        cursor.execute(statement, values)
    connection.commit()
except psycopg2.errors.UniqueViolation:
    connection.rollback()
    log.info("duplicate — already stored")
```

### The function returns 500 and the connector retries forever

A poison message that always fails. The connector's retry limit is
usually 5 attempts; after that it moves to the dead-letter queue topic —
**if you have configured one**. Without a DLQ, the record is dropped and
you lose it silently.

### `SSL error: certificate verify failed`

The Cloud SQL server certificate is not trusted by the function's runtime.
Use the Cloud SQL Auth Proxy, or install the CA bundle:

```bash
gcloud sql connect instance-name --user=postgres
```

### The connector cannot reach the function

A Cloud Run function created with `--no-allow-unauthenticated` rejects
unauthenticated requests — and the Confluent connector does not sign its
requests by default. Either allow the connector's service account through
IAM, or front the function with an authenticated endpoint and use the
connector's OAuth support.

### Messages arrive out of order

The partitioning key does not match the entity key. Check the producer's
partitioning configuration — the key must be the entity's key, and for a
CDC fan-out it must be the merge key.

### `could not translate host name` from Cloud Run

Cloud Run cannot resolve a Cloud SQL instance name directly. Use the
**instance connection name** (`project:region:instance`) with the
connector, or the Auth Proxy.

---

## 💡 Production Notes

- **Put a `PRIMARY KEY` on every table a stream writes to.** It is the
  cheapest correctness guarantee available, and it costs nothing at write
  time that matters.
- **Return 4xx for permanent failures and 5xx for transient ones.** The
  connector uses the status code to decide between skipping and retrying.
- **Configure a dead-letter queue topic.** Without one, a poison message
  is dropped without a trace.
- **Confluent Cloud bills on bytes stored and bytes transferred**, not on
  message count. Set retention on every topic — an unbounded retention
  policy on a high-volume topic is an unbounded bill.
- **Scope your API keys.** A key scoped to one cluster and one topic is
  far better than an org-wide key.
- **Keep the partition count stable.** Increasing it on a topic
  re-partitions the keyspace, and in-flight records can be reordered.
- **Do not use the `Cloud key` in an application.** It manages the
  cluster; the `API key` connects to it.

---

## 🔑 Key Takeaways

- Kafka guarantees ordering **within a partition** and at-least-once
  delivery.
- The **partitioning key must be the merge key** when you fan a CDC
  stream out through Kafka.
- Confluent Cloud bills on **bytes stored and transferred**, not on
  message count.
- The Confluent GCF sink connector POSTs each message to a Cloud Run
  function. The function must be **idempotent**.
- The duplicate-write race is normal, not exceptional. Design for it.
- The fix that scales best is a **`PRIMARY KEY` on the business key**, with
  the duplicate-key error treated as success.

---

## 📚 Practice Exercises

1. **Write the DDL.** Design a `transactions` table for the Kafka path,
   with the constraints and indexes the dashboard's queries need. Explain
   each index.

2. **Prove the ordering constraint.** Argue why the Kafka partition key
   must equal the merge key, using a concrete example of an update
   arriving before its insert.

3. **Measure the duplicate rate.** Assume 500 messages per second and a
   0.1% redelivery rate. Calculate the duplicates per hour, and size the
   `PRIMARY KEY` index for that table's row count.

4. **Design the DLQ.** Specify the shape of a dead-letter topic: the
   original payload, the failure reason, the timestamp, and the attempt
   count. Write the function's code that sends a message to it.

5. **Reflection.** Your team wants to write to BigQuery instead of Cloud
   SQL, using the Kafka path rather than Datastream. Give the two best
   reasons for that, and the one reason it is worse than just using
   Datastream.

---

## 📖 Further Reading

- Confluent Cloud documentation — https://docs.confluent.io/cloud/current/
- Confluent's Google Cloud Functions sink connector — https://docs.confluent.io/kafka-connectors/google-cloud-functions-sink-converter/
- Kafka delivery semantics — https://kafka.apache.org/documentation/#semantics
- Cloud SQL for PostgreSQL — https://cloud.google.com/sql/docs/postgres
