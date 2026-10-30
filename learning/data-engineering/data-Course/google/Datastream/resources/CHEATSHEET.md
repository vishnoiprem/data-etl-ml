# Datastream & CDC Cheat Sheet

> One page per topic. Keep it open in a tab.

---

## The pipeline in one picture

```text
   MySQL / Postgres
        │
        │  binlog (ROW)  /  WAL (logical)
        ▼
   ┌─────────────────┐
   │  Datastream     │  reads the log, preserves order,
   │  (read only)    │  applies a read consistency window
   └─────────────────┘
        │  change events: {op, before, after, sourceTimestamp, serverTimestamp}
        ▼
   ┌─────────────────┐
   │  BigQuery       │  MERGE on the merge key
   │  destination    │  NOT MATCHED → INSERT
   │                 │  MATCHED + op≠DELETE → UPDATE
   │                 │  MATCHED + op=DELETE → DELETE
   └─────────────────┘
```

---

## The merge, in full

```sql
MERGE `PROJECT.dataset.customers` AS target
USING `PROJECT.dataset.customers_stream` AS source
    ON target.customer_id = source.customer_id
WHEN NOT MATCHED BY TARGET THEN
    INSERT (customer_id) VALUES (source.customer_id)
WHEN MATCHED AND source.__op__ != 'DELETE' THEN
    UPDATE SET target.customer_id = source.customer_id
WHEN MATCHED AND source.__op__ = 'DELETE' THEN
    DELETE
```

### The four clauses and what each one does

| Situation | Clause | Result |
|---|---|---|
| Key not in target | `WHEN NOT MATCHED BY TARGET` | INSERT |
| Key in target, not a delete | `WHEN MATCHED AND __op__ != 'DELETE'` | UPDATE |
| Key in target, a delete | `WHEN MATCHED AND __op__ = 'DELETE'` | DELETE |
| Key in target, key is null | — | SKIP (count it) |

### The clause that must NOT be there

```sql
-- NEVER in a streaming merge.
WHEN NOT MATCHED BY SOURCE THEN DELETE
```

**In a stream, the absence of a change is not evidence of a deletion.** A
row that has not changed in an hour has simply not changed. This clause
belongs to a *synchronised* merge, where the source is a finite, complete
snapshot — i.e. a backfill.

---

## The merge key rules

| Property | Why | What breaks without it |
|---|---|---|
| **Unique** | A merge must match exactly one row | One update overwrites several rows — silently |
| **Immutable** | The merge looks rows up by key | A changed key orphans the row and creates a duplicate |
| **Minimal** | Fewer columns, fewer chances to be wrong | A nullable key component fails to match |

> **The rule:** the source table's **primary key**, and nothing else.
> Never an email, a username, a slug, a phone number.

---

## Merge behaviour, decision table

| Event | Key present? | Result | Skip reason |
|---|---|---|---|
| INSERT | no | INSERT | — |
| INSERT | yes | converge (no-op) | `duplicate_insert` |
| UPDATE | no | INSERT the after-image | `update_of_absent_row` |
| UPDATE | yes | UPDATE | — |
| DELETE | no | no-op | `delete_of_absent_row` |
| DELETE | yes | DELETE | — |
| any | key is null | skip | `missing_merge_key` |
| any | no before/after image | skip | `no_row_image` |

This table is implemented in `project/cdc.py` → `CdcState.apply()`. It is
the semantic contract every CDC tool reimplements.

---

## Source configuration

### MySQL

```sql
-- The three settings that matter.
SHOW VARIABLES LIKE 'binlog_format';       -- must be ROW
SHOW VARIABLES LIKE 'binlog_row_image';    -- must be FULL
SHOW VARIABLES LIKE 'binlog_expire_logs_seconds';

-- The three grants the replication user needs.
SELECT, REPLICATION SLAVE, REPLICATION CLIENT
```

| Setting | Value | Why |
|---|---|---|
| `binlog_format` | `ROW` | Statement logs cannot be replayed against a changed table |
| `binlog_row_image` | `FULL` | `MINIMAL` gives incomplete before-images — no audit, no rebuild |
| `binlog_expire_logs_seconds` | `604800` (7d) | Bounds the log, and bounds how long a disconnected reader can survive |

### Postgres

```sql
SHOW wal_level;                     -- must be logical (default is replica)
SHOW wal_keep_size;
SELECT slot_name, active, wal_status FROM pg_replication_slots;
```

| Setting | Value | Why |
|---|---|---|
| `wal_level` | `logical` | Physical WAL ships files; logical ships row changes |
| Replication slot | per-consumer | Prevents WAL truncation past a disconnected reader — **and** holds WAL on disk indefinitely if unmonitored |

---

## The read consistency window

**How long Datastream waits after a commit before reading its changes, to
guarantee commit-order delivery.**

| Window | Use when | Latency floor |
|---|---|---|
| 1 second | Single-writer, low contention | 1s + merge time |
| **5 seconds** | **The default choice** | **5s + merge time** |
| 10 seconds | Heavy concurrent write load | 10s + merge time |

> **Set the SLA from the window, not from a measurement.** A quiet-period
> measurement of 300ms will become 5.3s after the first write burst.

---

## Backfill modes

| Mode | Behaviour | When |
|---|---|---|
| `backfill-all` | Copy contents, then stream changes | **The default choice** |
| `backfill-none` | Stream changes only, from now | The destination already has the data |
| `backfill-config` | Copy contents, with a filter and column mapping | The source has columns you do not want |

### The recovery procedure

```text
  1. Pause the stream.        (so nothing new arrives mid-rebuild)
  2. DROP the destination table.
  3. RECREATE it with the same schema, partitioned and clustered.
  4. Update the stream with --backfill-all.
  5. Resume the stream.
```

The destination **must** be empty before a backfill. The merge has no
version information, so it cannot resolve a conflict between the snapshot
and an existing row.

---

## BigQuery destination setup

```sql
CREATE TABLE `PROJECT.dataset.customers` (
    customer_id STRING NOT NULL,
    first_name  STRING,
    last_name   STRING,
    email       STRING,
    region      STRING,
    tier        STRING
)
PARTITION BY _PARTITIONTIME
CLUSTER BY customer_id;
```

| Choice | Reason |
|---|---|
| `CLUSTER BY customer_id` | The merge sorts on the merge key — clustering skips the sort and prunes blocks |
| `PARTITION BY _PARTITIONTIME` | Partition expiration is cheap; the merge only touches recent partitions |
| `NOT NULL` on the merge key | A null key cannot match, and a silent null is a data quality lie |

---

## The four metrics that matter

| Metric | What it tells you | Alert on |
|---|---|---|
| **Latency** | How far behind is the destination? | p95 > SLA |
| **Throughput** | Events per second | vs source write rate |
| **Error rate** | Are events being rejected? | any sustained > 0 |
| **Lag** | How much unprocessed change is there? | **growth rate**, not size |

### What does NOT matter

- **The row count.** It goes up and down with churn and says nothing about health.
- **The stream state being `READY`.** It means the stream has not *failed*,
  not that events are *flowing*.

### The arithmetic test

```text
  backlog growth = source write rate − pipeline processing rate

  > 0   → permanently behind; waiting will not fix it
  = 0   → keeping up
  < 0   → catching up
```

---

## Kafka side

| Concept | Meaning |
|---|---|
| **Topic** | The log of messages. Partitioned. |
| **Partition** | An ordered append-only sequence. The unit of parallelism. |
| **Partition key** | The value the producer hashes to choose a partition. **Must equal the merge key.** |
| **Consumer group** | A set of consumers sharing the partitions. Each partition → exactly one consumer. |
| **Offset** | A position in a partition. The connector holds it, not you. |

### Delivery semantics

| | Datastream → BigQuery | Kafka → Cloud Run → Cloud SQL |
|---|---|---|
| Semantics | Stateful — converges | Stateless — appends |
| Delivery | Exactly-once within the merge | At-least-once |
| Ordering | Preserved (source order) | Per-partition only |
| Idempotency | Free (keyed merge) | **You must enforce it** — `PRIMARY KEY` |

### The status code contract

| Situation | Status | Connector behaviour |
|---|---|---|
| Malformed payload, validation failure | **4xx** | Skip (or route to the DLQ) |
| Database temporarily unreachable | **5xx** | Retry |
| Success | **200** | Commit the offset |
| Unexpected internal error | **5xx** | Retry |

Getting it backwards means either dropping good data (4xx for a transient
database error) or retrying a poison message forever (5xx for a malformed
message).

---

## Handling duplicates in the Kafka path

```sql
-- The constraint does the work.
CREATE TABLE transactions (
    transaction_id TEXT PRIMARY KEY,
    customer_id    TEXT NOT NULL,
    amount         NUMERIC(12,2) NOT NULL,
    currency       TEXT NOT NULL,
    product_id     TEXT,
    channel        TEXT,
    occurred_at    TIMESTAMPTZ NOT NULL
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

```sql
-- Or avoid the exception entirely.
INSERT INTO transactions (transaction_id, customer_id, amount)
VALUES (%s, %s, %s)
ON CONFLICT (transaction_id) DO NOTHING;
```

> **The key must be the business key** — `transaction_id`, not
> `customer_id`. Two legitimate transactions by the same customer are not
> duplicates.

---

## The gcloud commands you actually need

```bash
# Source config
gcloud datastream source-configs describe mysql-source \
    --location=us-central1 \
    --format="value(mysqlSourceConfig.includeTables)"

# Network / IP allocation
gcloud datastream network-configs ip-pools list \
    --location=us-central1 --network-config=network-config

# Stream state
gcloud datastream streams describe my-stream --location=us-central1

# Pause / resume
gcloud datastream streams pause  my-stream --location=us-central1
gcloud datastream streams resume my-stream --location=us-central1

# Trigger a backfill
gcloud datastream streams update my-stream --location=us-central1 \
    --backfill-all

# Deploy the ingest function
gcloud functions deploy ingest-transaction \
    --gen2 --runtime python312 --region us-central1 --source . \
    --entry-point handle_event --trigger-http --no-allow-unauthenticated \
    --set-env-vars="INSTANCE_CONNECTION_NAME=project:region:instance" \
    --set-secrets="DB_PASSWORD=db-password:latest"
```

---

## The reconciliation query

```sql
-- Compare VALUES, never counts.
WITH source AS (SELECT * FROM `PROJECT.reconciliation.customers_source_snapshot`),
     destination AS (SELECT * FROM `PROJECT.datastream.customers`)

SELECT 'MISSING' AS discrepancy, s.customer_id
FROM source s LEFT JOIN destination d USING (customer_id)
WHERE d.customer_id IS NULL

UNION ALL

SELECT 'EXTRA', d.customer_id
FROM destination d LEFT JOIN source s USING (customer_id)
WHERE s.customer_id IS NULL

UNION ALL

SELECT 'VALUE_MISMATCH', s.customer_id
FROM source s JOIN destination d USING (customer_id)
WHERE s.tier IS DISTINCT FROM d.tier
   OR s.region IS DISTINCT FROM d.region;
```

| Discrepancy | Root cause |
|---|---|
| `MISSING` | Inserts dropped, or the backfill did not cover the table |
| `EXTRA` | Deletes not applied |
| `VALUE_MISMATCH` | Wrong merge key, or a dropped update |

> **Reconcile against the source, not against the stream.** Comparing the
> destination to a reconstruction from the stream only proves the *merge*
> works. Comparing it to the source proves the *pipeline* works.

---

## Cost levers, in order of impact

1. **Capture less** — exclude high-churn tables at the source. One line of
   config, and it can remove 99% of the processing volume.
2. **Cluster and partition the destination** — an unclustered destination's
   merge cost grows with the table.
3. **Set retention** — `binlog_expire_logs_seconds` on the source, partition
   expiration on the destination, topic retention on Kafka.

| Service | Billed on |
|---|---|
| Datastream | GB of change data processed |
| BigQuery | Storage, queries, DML generated by the merge |
| Confluent Cloud | Bytes stored + bytes transferred (not message count) |
| Cloud Run / Cloud Functions | Instance time (with `min-instances`, always) |

---

## The five mistakes that cost the most

1. **Merging on a mutable attribute** (email, username) → orphaned rows and
   duplicates, silently.
2. **`NOT MATCHED BY SOURCE THEN DELETE` in a streaming merge** → the table
   empties itself every time the stream goes quiet.
3. **Comparing row counts instead of values** → passes with a wrong merge key.
4. **Returning 500 for a malformed payload** → infinite retries, then silent
   data loss with no DLQ.
5. **Partitioning by something other than the merge key in Kafka** → updates
   arrive before inserts and the destination duplicates.
