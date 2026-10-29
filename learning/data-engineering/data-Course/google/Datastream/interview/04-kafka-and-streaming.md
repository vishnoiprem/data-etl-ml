# Module 4 — Kafka, Streaming & the Confluent Path

> **14 questions · Module 4 · Kafka, Streaming & the Confluent Path**

---

## Kafka fundamentals

### 1. What is Kafka's delivery guarantee, and what does that mean for a database write?

**At-least-once.** Records are delivered to exactly one consumer within a consumer group, and may be **redelivered** if the consumer fails before committing its offset.

For a database write, that means the same message can arrive twice, and the row can be written twice. The sequence is:

```text
  1. The function receives message M
  2. The function writes M to PostgreSQL   ← succeeds
  3. The function returns 200
  4. The response is lost in transit
  5. The connector never advances its offset
  6. The connector redelivers M
  7. The function writes M again              ← duplicate
```

Steps 2–4 are not a rare race. They are a normal consequence of a distributed system, and the rate is proportional to your message volume.

The conclusion: **the destination must enforce idempotency, not the application.** The application will be retried; the database constraint will not.

### 2. Why does the Kafka path differ from the Datastream path?

**The Datastream destination is stateful and converges. The Kafka destination is stateless and appends.**

| | Datastream → BigQuery | Kafka → Cloud Run → Cloud SQL |
|---|---|---|
| Semantics | Stateful — the table converges | Stateless — each message is a fact |
| Delivery | Exactly-once within the merge | At-least-once |
| Ordering | Preserved (source order) | Per-partition only |
| State kept | The full current table | None, unless you dedupe |

The consequence is concrete. A CDC destination converges: replay the whole stream and you get the same table. A Kafka destination does not: it is a growing log of whatever arrived, and the same message can arrive twice. So the Kafka path needs a uniqueness constraint that the Datastream path gets for free from its merge key.

### 3. What is a consumer group and why does it matter for ordering?

**A consumer group is a set of consumers that share a topic's partitions, where each partition is assigned to exactly one consumer in the group.**

Two consequences:

- **Load balancing.** Adding consumers to a group lets them share the partitions, so throughput scales with consumer count — up to the partition count.
- **Ordering guarantee.** Records within a partition are delivered in order, and because only one consumer in the group holds a partition, that order is preserved end to end. Records *across* partitions have no order relationship.

The trap: **if you produce messages for the same entity to different partitions, they can be consumed out of order.** So the partitioning key must be the entity's key.

And for a CDC fan-out through Kafka, the partitioning key must be the **merge key**. If it is not, updates for one row can arrive out of order and the merge converges on the wrong value. This is the requirement that makes a partitioned stream mergeable.

The failure story: a team partitioned by `customer_id` while the destination merged on `transaction_id`. Every customer had thousands of transactions, so each partition held them in order, but the merge looked each row up by a different key — and an update arriving before its insert created a duplicate row. Every night the deduplication job found a few hundred extra rows and deleted them. The pipeline was "self-healing" and nobody asked why it was not healing correctly.

### 4. Why must the Kafka partitioning key match the merge key?

**Because ordering and merging are only compatible if they agree.** The merge assumes it sees each key's changes in order; the partitioner is what guarantees an order. If they disagree, the merge sees updates before their inserts and creates duplicates.

Concretely: merging on `transaction_id` while partitioning by `customer_id` means all of one customer's transactions are ordered relative to each other, but a given transaction's insert and its update may land in different partitions and arrive in either order. The update arrives first, the merge does not find the row, and it inserts — then the real insert arrives and creates a duplicate.

The rule, stated for an interview: **when you fan a CDC stream out through Kafka, the partition key and the merge key must be the same value.** They are not two independent decisions; they are one decision expressed twice.

### 5. How does the Confluent Google Cloud Functions sink connector work?

It is a **Confluent-managed connector** that runs on Confluent's infrastructure. It polls the topic and POSTs each message to your Cloud Run function's HTTP endpoint.

```text
  Kafka topic
      │
      ▼
  Confluent GCF sink connector
      │  HTTP POST, one per message
      ▼
  Cloud Run Function (2nd gen)
      │  fetch secret → parse → insert
      ▼
  Cloud SQL for PostgreSQL
```

Three properties that determine how you write the function:

1. **The connector is stateless from your side.** It holds the offsets. If the function returns a **4xx**, the connector treats it as a permanent failure and skips the record. If it returns a **5xx**, it retries.
2. **The function must be idempotent**, because the connector will redeliver on a retry.
3. **The status code is your retry policy.** Getting it backwards means either dropping good data (returning 4xx for a transient database error) or retrying a poison message forever (returning 5xx for a malformed message).

### 6. Why does a Cloud Run function need `min-instances` for a streaming consumer?

**Because a cold start adds seconds of latency to the first message, and a stream consumer's SLA is usually measured in milliseconds.**

Cloud Run scales to zero when idle. The next request pays the container start, the runtime initialisation, and the import of your dependencies. For a Kafka consumer that is continuously receiving messages, that cold start lands on a real message, and the consumer's offset does not advance until the function returns — so the message's processing latency spikes.

Setting `min-instances` keeps N instances warm. It costs money continuously, which is why it is a deliberate trade: you are paying for warm capacity to meet a latency SLA.

The alternative is to accept the cold start and make the function's initialisation cheap. Caching the database connection and the secret in module scope — which the course's `cloud_function.py` does — helps, but it does not remove the container start itself.

### 7. What is the difference between Cloud Run and Cloud Functions for this use case?

**Cloud Run is the more flexible option and is what you would build today; Cloud Functions is what Confluent's connector targets.**

| | Cloud Functions (gen2) | Cloud Run |
|---|---|---|
| Trigger | Event-driven | Any — HTTP, background, scheduled |
| Concurrency | 1 per instance by default | Configurable, up to 1000 per instance |
| Cold start | Yes | Yes, but `min-instances` can remove it |
| Best for | Small, event-driven handlers | Longer requests, higher throughput |

The difference that matters in production is `min-instances`, and the concurrency setting. A Cloud Function processing one message per invocation at one request per instance cannot keep up with a high-throughput topic, because each invocation pays a full round trip. Cloud Run's concurrency lets one instance process many messages in flight.

If you are using the Confluent sink connector, Cloud Functions is the path of least resistance. If you are building from scratch, use Cloud Run.

## The Cloud Run function

### 8. What are the three stages of the function, and what does each one do?

**Fetch the secret → parse the message → insert the row.**

**Fetch the secret** resolves the database password from Secret Manager. It is cached in module scope, because Cloud Run reuses the instance across invocations, and fetching on every call adds a round trip to every message. The trade-off is that a rotated secret is not picked up until the instance restarts — acceptable for a database password, unacceptable for a short-lived token, which is why the two should be cached differently.

**Parse** validates and flattens the JSON payload. It raises on a missing field rather than inserting a NULL, because a transaction with no amount is not a transaction with a zero amount.

**Insert** writes the row, with a **parameterised** statement.

### 9. Why must the INSERT statement be parameterised?

**Because it is the difference between storing a string that contains a quote and executing that string.**

```python
# Vulnerable — the payload becomes SQL.
statement = f"INSERT INTO transactions VALUES ('{row['product_id']}', ...)"

# Correct — the payload is data.
statement = "INSERT INTO transactions (transaction_id, ...) VALUES (%s, ...)"
cursor.execute(statement, values)
```

This is not a style preference, and the test that proves it is a payload with a quote in it. A payload of `p0001'; DROP TABLE transactions; --` in a vulnerable implementation produces a statement containing `DROP TABLE`. In a parameterised implementation it produces a statement with `%s`, and the payload sits in the values tuple as a string literal.

The reason the vulnerable version survives testing is that **test data does not contain quotes**. Every functional test passes. The first production payload with an apostrophe in it is the one that finds the bug.

### 10. What is the right way to handle a duplicate in the Kafka path?

**Catch the unique-violation error and treat it as success.** The constraint does the work; the application recognises the outcome.

```sql
CREATE TABLE transactions (
    transaction_id TEXT PRIMARY KEY,
    ...
);
```

```python
try:
    with connection.cursor() as cursor:
        cursor.execute(statement, values)
    connection.commit()
except psycopg2.errors.UniqueViolation:
    connection.rollback()
    log.info("duplicate — already stored")
```

The Postgres-specific alternative avoids the exception entirely:

```sql
INSERT INTO transactions (transaction_id, customer_id, amount)
VALUES (%s, %s, %s)
ON CONFLICT (transaction_id) DO NOTHING;
```

The third option, an idempotency key table checked by the function, works but adds a read and a write per message and has its own failure modes. The database constraint is better because it is the last line of defence and nothing above it can be bypassed.

The keying question worth raising: the primary key must be the **business key** — `transaction_id`, not `customer_id`. Two legitimate transactions by the same customer are not duplicates, and keying on `customer_id` would silently drop half your data.

### 11. How does the Cloud Function handle a poison message?

**Return a 4xx, and make sure a dead-letter queue is configured.**

A poison message is one that will always fail — a malformed payload, a missing required field, a value that violates a constraint. The connector's retry policy is typically five attempts, after which the record goes to the dead-letter queue topic **if one is configured**.

Without a DLQ, the record is dropped without a trace. That is a silent data loss, and it is invisible unless you count the rejects.

The status code contract:

| Situation | Status | Connector behaviour |
|---|---|---|
| Malformed payload, validation failure | **4xx** | Skip (or route to the DLQ) |
| Database temporarily unreachable | **5xx** | Retry |
| Success | **200** | Commit the offset |
| Unexpected internal error | **5xx** | Retry |

The failure story: a function returned 500 for everything, including malformed payloads. The connector retried each five times and then dropped it. The team discovered six months later, during a data audit, that a customer segment had been missing for half a year. The DLQ was never configured, so the dropped records existed nowhere.

### 12. What is the cost of a Confluent Cloud topic, and what surprises people?

**Confluent Cloud bills on data stored and data transferred — not on message count, not on partitions, not on consumers.**

That is the surprise. A topic with 10 million small messages can cost more than one with 1 million large ones, and a topic with a high retention and a modest message rate can cost more than one with a huge rate and short retention.

Two consequences for a course project and for production:

**Set retention on every topic.** The default retention is unbounded, and an unbounded retention on a high-volume topic is an unbounded bill. A topic retaining seven days of a high-volume stream is a very different invoice from one retaining one hour.

**Watch the transfer cost, not just the storage cost.** Every message is transferred in from the producer and out to the consumer. A fan-out to three consumers triples the egress.

The practical numbers: a moderate pipeline moving a few gigabytes a day costs a few dollars a month with sensible retention. The same pipeline with unbounded retention on a high-volume topic costs hundreds, because the storage accumulates without limit.

### 13. How do you store the database password for a Cloud Run function?

**In Secret Manager, fetched at runtime, cached in memory, and never in the source, the environment variables, or the image.**

```bash
gcloud functions deploy ingest-transaction \
    --gen2 \
    --runtime python312 \
    --region us-central1 \
    --source . \
    --entry-point handle_event \
    --trigger-http \
    --no-allow-unauthenticated \
    --set-env-vars="INSTANCE_CONNECTION_NAME=project:region:instance" \
    --set-secrets="DB_PASSWORD=db-password:latest"
```

The `--set-secrets` flag mounts the secret as an environment variable **at runtime**, so the value is never baked into the container image. The function then reads it and, ideally, exchanges it for a short-lived access token.

Two rules that follow:

- **Never use `--set-env-vars` for the password itself.** That places it in the function's configuration, visible to anyone with IAM access to the function.
- **Never put it in the source or in a `Dockerfile` `ENV` line.** Both are baked into the image and persist in the registry.

The failure story: a team set the database password as a plain environment variable, "just for the first deploy". The container image was later published to a shared registry, and the password went with it. Rotating it was straightforward; the audit was not.

### 14. When would you use a Kafka-based CDC pipeline rather than Datastream?

**When you need to fan the change stream out to multiple consumers, or when the source is not a database.**

The specific reasons:

1. **Fan-out.** Datastream's BigQuery destination is one destination. If five teams need the change stream — a warehouse, a search index, a machine learning feature store, a fraud service, an audit log — Kafka lets all five subscribe independently. Each gets its own consumer group and its own offsets, and one slow consumer does not hold up the others.

2. **Non-database sources.** Kafka is the natural transport for application events, third-party feeds, and anything that is not a database with a binary log.

3. **Decoupling.** The producer does not know or care who consumes. With Datastream, the destination is coupled to the stream configuration.

The reasons *not* to: it is more infrastructure, it introduces at-least-once semantics you must handle yourself, and it loses the transactional guarantees that the log-based approach gives you. If you have one destination and it is BigQuery, Datastream is less work and fewer failure modes.

The honest comparison for an interview: **Datastream is the better tool for "replicate this database into the warehouse". Kafka is the better tool for "publish the change stream so anything can subscribe".** Choosing Kafka for the first case means re-implementing merge semantics, idempotency, and ordering guarantees that Datastream gives you for free — which is exactly what the `PRIMARY KEY` constraint in this course's Cloud SQL schema is compensating for.
