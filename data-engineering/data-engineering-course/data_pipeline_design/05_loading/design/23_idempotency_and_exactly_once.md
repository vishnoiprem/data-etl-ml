# 23 — Idempotency and Exactly-Once Semantics

> **Lesson 23 of 30 — Loading**

The hardest problem in data engineering. The pipeline must
produce the same result whether it runs once or ten times. This
lesson is the *why* and the *how* — the patterns that turn a
flaky retry into a safe one.

---

## 1. The problem

A pipeline runs. Halfway through, the worker crashes. The
orchestrator retries. The destination now has *some* of the
rows from the first run and *all* of the rows from the second.
Result: duplicates, inflated metrics, angry analysts.

The fix: **idempotency**. Running the pipeline N times produces
the same result as running it once.

The senior move: "Every production pipeline is idempotent. If
yours isn't, it's a matter of time before it produces wrong
data."

---

## 2. The three levels of guarantee

| Level | What it means | Cost |
|---|---|---|
| **At-most-once** | The operation may not happen | Cheap, but data loss |
| **At-least-once** | The operation may happen more than once | Cheap, but duplicates |
| **Exactly-once** | The operation happens exactly once | Expensive, often impossible |

The senior framing: "True exactly-once is rarely achievable.
The practical answer is at-least-once with idempotency on the
consumer side."

---

## 3. Idempotency keys

The standard pattern: every event / row has a unique *idempotency
key*. The destination tracks which keys have been processed;
duplicates are dropped.

```
Producer:
  emit event { id: "evt-abc-123", data: {...} }

Consumer:
  if "evt-abc-123" already in processed_set:
    skip
  else:
    process(data)
    add "evt-abc-123" to processed_set
```

The processed set is durable (a database table, a KV store
with TTL). The senior move: "I'd use the event ID as the
idempotency key. The dedup table has a TTL of 7 days — long
enough to absorb retries, short enough to keep the table small."

---

## 4. The pattern: write-then-commit

The classic write-then-commit pattern for batch loads:

```python
def load(rows):
    # Stage 1: write to a staging table.
    stage_table = f"{target_table}_staging_{run_id}"
    write_to_table(stage_table, rows)
    # Stage 2: atomic swap.
    swap_tables(target_table, stage_table)
    # Stage 3: commit the run id.
    mark_run_complete(run_id)
```

If the worker crashes between stage 1 and stage 2, the retry
sees an incomplete `stage_table` and starts over. If the
worker crashes between stage 2 and stage 3, the retry sees a
completed `target_table` and skips.

The senior move: "I'd use the staging-table pattern for any
batch load. The atomic swap makes the load crash-safe."

---

## 5. The pattern: idempotent upsert

The simplest idempotent write: `MERGE INTO` on a primary key.

```sql
MERGE INTO target.users t
USING staging.users s
ON t.id = s.id
WHEN MATCHED THEN UPDATE ...
WHEN NOT MATCHED THEN INSERT ...;
```

Running this twice with the same data produces the same
result. The primary key is the idempotency anchor.

The senior move: "For upsert pipelines I'd use `MERGE INTO`
on the natural primary key. The semantics are inherently
idempotent."

---

## 6. The pattern: Kafka exactly-once

Kafka *does* support exactly-once via transactional
producers and read-committed consumers:

```python
producer = KafkaProducer(
    transactional_id="my-producer",
    enable_idempotence=True,
)
producer.begin_transaction()
producer.send("events", value=row)
producer.commit_transaction()
```

This makes the producer's writes atomic: either all of them
land in the topic, or none. The senior move: "Kafka's
exactly-once is the right answer when the pipeline is
Kafka-only. It doesn't help with cross-system boundaries
(like a Kafka-to-warehouse load)."

---

## 7. The pattern: idempotency at the warehouse

The warehouse-side pattern: every load has a *load_id*. The
warehouse records which `load_id`s have been applied. A retry
with the same `load_id` is a no-op.

```sql
CREATE TABLE load_log (
  load_id TEXT PRIMARY KEY,
  target_table TEXT,
  row_count INTEGER,
  loaded_at TIMESTAMP
);

-- The idempotent load
INSERT INTO load_log (load_id, target_table, row_count)
VALUES (:load_id, 'orders', :row_count)
ON CONFLICT (load_id) DO NOTHING;

-- If the insert affected 0 rows, this load_id is a duplicate.
```

The senior move: "I'd use load IDs for any pipeline that
writes to a warehouse. The load_log table is the source of
truth for what has been applied."

---

## 8. The pattern: dedup by event_id

For event streams, the simplest idempotency: dedup by event_id.

```sql
-- The dedup pattern
INSERT INTO target.events (event_id, payload, event_time)
SELECT event_id, payload, event_time
FROM staging.events s
WHERE NOT EXISTS (
  SELECT 1 FROM target.events t
  WHERE t.event_id = s.event_id
);
```

The `NOT EXISTS` makes the insert idempotent: re-running it
with the same data inserts nothing. The senior move: "For
event streams I'd dedup by event_id in the staging-to-target
step. The dedup is the idempotency anchor."

---

## 9. The interview answer

> "Every production pipeline is idempotent. The pattern depends
> on the load type: for upserts I'd use `MERGE INTO` on the
> natural primary key; for batch loads I'd use the
> staging-table + atomic-swap pattern; for event streams I'd
> dedup by event_id; for Kafka I'd use transactional
> producers. True exactly-once is rarely achievable across
> systems; the practical answer is at-least-once with
> idempotency on the consumer side."

That single paragraph covers: the principle, four patterns
by load type, the at-least-once + idempotency framing.
Senior answer in 30 seconds.

---

## Try it

Look at the most recent pipeline you've worked on. Is it
idempotent? Can you re-run it without producing duplicates?
What happens on a partial failure? If you can't answer
"yes" to all three, the pipeline is one bad run away from
wrong data.
