# 06 — Data Sources

> **Lesson 6 of 30 — Storage**

The left edge of every pipeline is a data source. The four source
types you'll meet in 90% of interviews are OLTP databases, APIs,
files, and event streams. Each has a different shape, a different
SLA, and a different reliability story. This lesson is the *when
to use which* decision tree.

---

## 1. The four source types

| Source type | Examples | Latency | Reliability story |
|---|---|---|---|
| **OLTP database** | Postgres, MySQL, Oracle | Seconds (CDC) to hours (polling) | Strong consistency, transactional. |
| **API** | Stripe, Salesforce, internal REST | Seconds to days (rate-limited) | Best-effort, paginated, rate-limited. |
| **File drop** | S3, GCS, NFS, FTP | Minutes to days | Eventually consistent, no schema. |
| **Event stream** | Kafka, Kinesis, Pub/Sub | Sub-second to seconds | At-least-once, ordered per partition. |

The "right" source type is dictated by the source system, not by
you. Stripe doesn't expose a binlog; you have to poll the API.
Postgres exposes a binlog; you should use CDC. The senior move is to
recognize the source type and pick the right extractor for it.

---

## 2. OLTP databases (CDC + polling)

OLTP databases (Postgres, MySQL, Oracle, SQL Server) are the
backbone of most enterprise pipelines. The source of truth lives in
a row-oriented store with strong consistency and transactional
semantics.

**Two ways to extract:**

- **Change Data Capture (CDC).** Read the database's transaction
  log (Postgres `pgoutput`, MySQL binlog, Oracle redo log). Emit
  INSERT/UPDATE/DELETE events. Debezium is the open-source default.
  Low latency, complete, doesn't burden the source DB. **The
  preferred pattern in 2026.**
- **Polling.** Run `SELECT * FROM table WHERE updated_at > last_run`
  on a schedule. Simpler to set up, but lossy (deletes are invisible
  unless soft-deleted), high load on the source DB, and latency is
  the polling interval.

**The trade-off.** CDC is the right answer when the source has a
binlog and you need low latency. Polling is the fallback when the
source is read-only, doesn't expose a binlog, or is a SaaS API
disguised as a database.

```sql
-- The polling pattern: incremental by updated_at
SELECT id, name, status, updated_at
FROM users
WHERE updated_at > :last_run_ts
ORDER BY updated_at
LIMIT 10000;
```

The query above is what every polling extractor eventually looks
like. Note the `ORDER BY updated_at` — without it, you can miss
rows that updated during the query. Note the `LIMIT` — without it,
a long-running query can starve the source.

---

## 3. APIs (paginated, rate-limited, best-effort)

APIs are the source of truth for SaaS systems: Stripe, Salesforce,
HubSpot, internal microservices. They are *not* databases. They are
eventually-consistent, rate-limited, paginated, and they change
their schema without warning.

**Three pagination patterns:**

- **Offset pagination** — `?page=1&page_size=100`. Simple, but
  unstable: a row inserted between page 1 and page 2 can shift all
  subsequent rows. Use only when the dataset is small and stable.
- **Cursor pagination** — `?after=cursor_xyz&page_size=100`. Stable
  under inserts. The cursor is opaque; you don't try to parse it.
  The default for modern APIs (Stripe, Slack, Notion).
- **Keyset pagination** — `?since_id=12345&page_size=100`. Stable,
  simple, but only works for monotonic keys. Common for internal
  APIs.

**Rate limits.** Most APIs return 429 with a `Retry-After` header.
The senior move: respect the header, back off exponentially, and
emit a metric so the on-call sees when you're rate-limited.

```python
# The rate-limit handling pattern
response = requests.get(url, headers=headers)
if response.status_code == 429:
    retry_after = int(response.headers.get("Retry-After", 60))
    time.sleep(retry_after)
    response = requests.get(url, headers=headers)
```

---

## 4. File drops (S3, GCS, FTP)

File drops are the oldest pattern: a producer writes a file
(CSV, Parquet, JSON) to a shared location, the pipeline reads it
on a schedule. Common for partner integrations, legacy systems, and
batch ML feature pipelines.

**The schema problem.** Files have no schema enforcement. The
producer can change a column name without telling you. The senior
move is a *schema contract*: a JSON file alongside the data that
describes the expected schema. The pipeline reads the contract,
validates the file, and rejects mismatches.

**The ordering problem.** Files are usually written in batches
(`part-0001.csv`, `part-0002.csv`). The pipeline must wait for
*all* parts before processing. The standard pattern is a
*marker file* (e.g. `_SUCCESS`) written last; the pipeline only
processes when the marker is present.

**The size problem.** A 100 GB CSV is unwieldy. The senior move
is Parquet, partitioned by date, with a metadata file. The 2026
default for file drops is Parquet + a schema file + a marker file.

---

## 5. Event streams (Kafka, Kinesis, Pub/Sub)

Event streams are the right source when the producer already
publishes events: app logs, clickstream, IoT telemetry, CDC
output. The producer owns the schema and the ordering guarantee;
the pipeline consumes from a topic.

**The three guarantees:**

| Guarantee | What it means |
|---|---|
| **At-most-once** | The event is delivered zero or one times. Loses events on failure. Rare in practice. |
| **At-least-once** | The event is delivered one or more times. Duplicates on retry. The default for Kafka. |
| **Exactly-once** | The event is delivered exactly one time. Expensive; usually achieved via idempotency keys. |

**The senior move** is to know that "exactly-once" is usually
"at-least-once + idempotency on the consumer side." The pipeline
must dedup on a stable event_id. Lesson 23 covers this in detail.

**The ordering problem.** Kafka guarantees order *within a
partition*. If you partition by `user_id`, all events for the same
user are ordered, but events across users are not. The senior
move is to choose the partition key deliberately: by user_id for
per-user state, by event_id for global ordering, by random for
throughput.

---

## 6. Choosing the right source type

```
Is the source a database you control?
  └─ Yes → CDC (binlog) if available, else polling on updated_at
  └─ No  → Is it a SaaS API?
              └─ Yes → API polling with cursor pagination
              └─ No  → Does the producer publish events?
                         └─ Yes → Subscribe to the event stream
                         └─ No  → File drop with a schema contract
                                  and a marker file
```

This is the decision tree you'll recite in the interview. The
right answer is rarely "I would build X." The right answer is
"Given that the source is Y, I would use Z for these reasons."

---

## 7. The reliability story per source

Every source has a different reliability story. The senior answer
includes this:

| Source | What breaks | Mitigation |
|---|---|---|
| **OLTP** | DB down, replication lag, schema migration | CDC checkpoint + retry; alert on replication lag > 5 min. |
| **API** | Rate limit (429), 5xx, schema change | Backoff + retry; schema contract tests; alert on 5xx rate. |
| **File** | Late file, missing parts, schema drift | Marker file + wait + alert; schema contract; daily count check. |
| **Stream** | Broker down, consumer lag, poison message | Lag-based alerting; DLQ for poison messages; idempotent consumer. |

If you can name the failure mode of each source type unprompted,
you have a senior answer.

---

## Try it

Pick the most recent pipeline you've worked on. Which source type
is it? What's the reliability story? Is there a failure mode the
pipeline doesn't handle? Sketch the answer on a whiteboard — this
is exactly what the interview will ask.
