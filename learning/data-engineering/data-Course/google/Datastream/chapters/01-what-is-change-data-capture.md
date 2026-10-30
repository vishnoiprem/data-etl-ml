# 1.1 — What Is Change Data Capture?

> **Section 1 · Foundations & Mental Model · Lecture 1.1 · 25 min**

## 🎯 What you will learn

- What change data capture is, and the problem it solves that batch ETL cannot
- The three-layer architecture of a CDC pipeline: log, transport, sink
- The distinction that makes CDC different from everything else: **an
  immutable log of changes, applied to a mutable table**
- The four reasons teams adopt CDC — and the two that are usually the wrong
  reason
- How to tell whether CDC is worth it for your workload, using event
  amplification

---

## 🧠 Concept

### The problem CDC solves

A source database holds *current state*. A reporting table usually needs
*current state too* — but it needs it **fresh**, and the source is not
designed to be read continuously.

The traditional answer is **polling**: every fifteen minutes, run a query
that reads the rows changed since the last run and upsert them.

Polling works, and for a small table it is the right answer. It has three
problems, and each of them has a CDC answer.

| Polling's problem | What it costs | CDC's answer |
|---|---|---|
| **Latency** is the poll interval | 15 minutes of staleness, minimum | Read the log continuously — sub-second to a few seconds |
| **Every poll re-reads** | You read the whole changed set each time, even if nothing changed | The log contains exactly the changes |
| **Deletes are invisible** | A polling query that reads changed rows never sees a deleted row | The log contains an explicit delete event |

That third one is the real reason CDC exists, and it is the one people
forget. Polling based on `updated_at > last_run` **structurally cannot
detect a delete**. The row is gone. There is no timestamp to compare. So
either your polling logic keeps a tombstone table of its own — which is a
CDC implementation you wrote yourself, badly — or your pipeline never
deletes anything.

### The three layers

Every CDC pipeline has three layers, and knowing which one a problem lives
in is most of the debugging.

```text
  1. THE LOG                    2. THE TRANSPORT              3. THE SINK
  ┌──────────────────┐         ┌─────────────────┐          ┌──────────────────┐
  │ Source database  │         │ Change events   │          │ Destination       │
  │ binary log (WAL) │────────▶│ as they arrive │─────────▶│ table, maintained │
  │                  │  read   │                 │  merge   │ by a merge        │
  │ INSERT/UPDATE/  │         │ {op, before,    │          │                  │
  │ DELETE + images │         │  after, ts}     │          │                  │
  └──────────────────┘         └─────────────────┘          └──────────────────┘
     MySQL binlog                Kafka / Datastream          BigQuery / Postgres
     Postgres WAL                 Direct to BQ
```

**Layer 1 — the log.** The source database writes every change to a
durable log before acknowledging the transaction. MySQL calls it the
binary log; Postgres calls it the WAL; Oracle calls it the redo log. The
log is the source of truth for *what changed*, and it is why CDC does not
put load on the database's tables.

**Layer 2 — the transport.** Something reads the log and delivers change
events. This is where Datastream sits, and where Kafka sits. The transport
may buffer, retry, and replay. It is the component most likely to deliver
the same event twice.

**Layer 3 — the sink.** Something applies the events to a destination
table. This is a **merge** — a keyed upsert-and-delete. It is the layer
that holds the semantic contract, and the one this course spends most of
its time on.

### The one distinction that matters

> **The log is immutable and append-only. The table is mutable.**

This is the whole idea. A row that changes five times produces **five
events** in the log and **one row** in the table.

Everything good about CDC follows from this:

- **Auditability.** The log is the complete history. You can answer "what
  did this row look like at 3pm?" — the events are still there.
- **Replayability.** You can re-apply the log from the beginning and
  rebuild the table exactly. This is how you recover from a corrupted
  destination.
- **Idempotency.** Applying the same event twice has the same effect as
  applying it once, because the merge is keyed. This is what makes retries
  safe.
- **Statefulness in the wrong place.** The state lives in the destination
  table, not in the transport. The transport can be stateless, which means
  it can be scaled horizontally and restarted freely.

And the thing that catches people: **the log and the table answer different
questions.** If you count rows in the log you get 5. If you count rows in
the table you get 1. Both are correct. A dashboard built on the wrong one
will be wrong, and it will be wrong by a factor of your churn rate.

### Four reasons teams adopt CDC — and two that are usually wrong

**The right reasons:**

1. **Low latency.** Sub-second to a few seconds, versus a polling
   interval. For fraud detection, live pricing, or operational dashboards,
   this is the whole point.
2. **Delete detection.** Polling structurally cannot see deletes. CDC
   sees them explicitly.
3. **Lower load on the source.** Reading a log is sequential and cheap.
   Polling a table with an index on `updated_at` is a random-access
   workload, and it re-reads the same range on every poll.
4. **Consistent capture.** The log reflects exactly what was committed,
   including transactions that span many rows. A polling query sees a
   *partial* transaction — rows half-updated — and you cannot tell.

**The reasons that are usually wrong:**

1. **"It is more real-time."** CDC is not real-time. It is *low-latency*.
   The floor is set by the read consistency window, typically 5 seconds.
   If your SLA is "under a minute", polling every 30 seconds meets it at a
   fraction of the cost.
2. **"It is faster."** For a small table, polling is faster — CDC adds
   merge overhead, and the merge is the expensive part. CDC's advantage
   appears when the *changed* set is much smaller than the *scannable*
   set.

### Event amplification — the number that decides it

> **Event amplification** = (number of change events) ÷ (number of rows in
> the table).

This single ratio tells you whether CDC is worth the complexity.

| Amplification | What the table looks like | Recommendation |
|---|---|---|
| ~1.0x | Append-only. Rows are inserted and never change. | **Poll, or use a simple batch extract.** CDC buys you nothing. |
| 1.1–2x | Mostly append, some churn | CDC is defensible if latency matters |
| 5–20x | High churn — rows change constantly | **CDC wins.** Polling re-reads and re-writes constantly |
| 100x+ | A log table masquerading as a table | Consider whether you want a table at all — a log sink may be the right answer |

The reason CDC wins in the middle of that table is arithmetic. Consider a
table with 10 million rows where 1% changes per hour:

- **Polling** reads 10 million rows to find 100,000 changes, unless it has
  a reliable `updated_at` index — and even then, the index probe plus the
  row fetch is a random-access workload across 10 million rows.
- **CDC** reads 100,000 events from a sequential log and merges them into
  the table.

That is the difference between a job that scales with the *table* and one
that scales with the *changes*. It is the entire economic argument for CDC,
and it is worth being able to state in one sentence in an interview.

---

## 🛠️ Hands-On: The Model in Code

The course's `cdc.py` implements the sink layer — the merge — in pure
Python. It runs with no GCP account, no credentials and no bill.

### Set up

```bash
cd data-engineering/data-Course/google/Datastream

python3 -m venv .venv
source .venv/bin/activate
pip install -r project/requirements.txt
```

### The whole model, in twenty lines

```python
from cdc import CdcState

state = CdcState(merge_keys=["customer_id"])

customer = {
    "customer_id": "c000001",
    "first_name": "Ada",
    "region": "EMEA",
    "tier": "silver",
}

state.apply_event({"op": "INSERT", "after": customer})
state.apply_event({"op": "UPDATE", "before": customer,
                   "after": {**customer, "tier": "gold"}})
state.apply_event({"op": "DELETE", "before": {**customer, "tier": "gold"}})

print("events applied :", state.applied_count)
print("rows in table  :", state.row_count())
```

Three events applied. **Zero rows in the table** — because the last event
deleted the row. Change the order and you get one row.

### Watch the table converge

```python
from cdc import CdcState

state = CdcState(merge_keys=["customer_id"])

for tier in ["silver", "gold", "platinum", "bronze"]:
    state.apply_event({
        "op": "UPDATE",
        "after": {"customer_id": "c1", "tier": tier},
    })

print("events applied :", state.applied_count)
print("rows in table  :", state.row_count())
print("final tier     :", state.get({"customer_id": "c1"})["tier"])
```

Four events, one row, and the row holds the *last* value. That is
convergence: the table's content depends on the *set* of events applied,
not on how many there were.

### Measure the amplification

```bash
python resources/sample_data.py --output-dir ./sample_data
python project/cdc_pipeline.py \
    --input ./sample_data/changes.ndjson \
    --output ./out/customers \
    --merge-keys customer_id
```

```
CDC replay summary
----------------------------------------------------
  events read          : 377
  rows in table        : 186
  changes applied      : 374
  events skipped       : 8
  skip reasons:
    delete_of_absent_row      : 2
    duplicate_insert          : 5
    missing_merge_key         : 1
```

**377 events, 186 rows — an amplification of about 2.0×.** By the table
above, that is a table with real churn, where CDC is defensible.

Note the skipped events: duplicates, deletes of rows never inserted, and
one deliberately malformed event. **None of them are errors.** Section 2.3
covers exactly what each one means.

---

## 🛠️ Common Errors and Fixes

### `KeyError: 'customer_id'`

Your merge key is not in the row image. Either the source table has no such
column, or the row image is a `before`/`after` image that predates the
column being added.

```python
# wrong
key = row["customer_id"]

# right
key = row.get("customer_id")
if key is None:
    return  # the row predates the column; skip it
```

### The table looks right but the numbers are wrong

Almost always the merge key. See chapter 2.1 — the failure is silent, and
a row-count check will not catch it.

### `RuntimeError: no project id available`

A local run picked up the GCP code path. Either set `GOOGLE_CLOUD_PROJECT`
or use the local fallback:

```bash
export SECRET_VALUE=local-dev-password
```

### The pipeline applies events but the table stays empty

Check that the merge key matches the **destination** table's primary key,
not the source's. If the destination table is clustered on `id` and you
merged on `customer_id`, every event inserts a new row instead of updating
one.

### `FileNotFoundError: ./sample_data/changes.ndjson`

You have not generated the sample data:

```bash
python resources/sample_data.py --output-dir ./sample_data
```

---

## 💡 Production Notes

- **The merge is the contract.** Everything else — the log reader, the
  transport, the retries — is plumbing. When the data is wrong, the merge
  is where the bug is.
- **Never count rows to validate a CDC pipeline.** Compare *values*. A
  wrong merge key or a dropped event leaves the row count plausible.
- **Log the skips, always.** "Skipped: 8, reasons: {duplicate_insert: 5}".
  A rising skip count is the only early warning you get.
- **CDC is not real-time.** Your SLA floor is the read consistency window
  plus the merge time. Put that number in the SLA.
- **Test the merge, not the connector.** The connector is Google's
  problem. The merge is yours, and it is pure logic — so it should have
  80% unit tests and run in a millisecond.

---

## 🔑 Key Takeaways

- CDC is **an immutable log of changes, applied to a mutable table**.
- Three layers: **log → transport → sink**. The sink is the merge, and it
  holds the contract.
- Polling **structurally cannot detect deletes**. That is CDC's real
  reason to exist.
- **Event amplification** decides whether CDC is worth it. ~1.0x means poll
  instead.
- The log answers "what happened"; the table answers "what is true". Do
  not confuse them.
- The **merge key** makes the merge idempotent — which is what makes
  retries and replays safe.

---

## 📚 Practice Exercises

1. **Measure amplification yourself.** Generate the sample data with
   `--customers 2000` and compute the ratio of events to rows. At what
   customer count does amplification drop below 1.5x?

2. **Break the model.** Write a merge that appends instead of upserting.
   Replay the sample data. Show that the row count is now wrong, and that
   replaying the stream a second time makes it worse. This is the
   non-idempotent bug, reproduced.

3. **Model a polling pipeline.** Write a function that simulates polling:
   it reads rows where `updated_at > last_run` and upserts them. Show that
   it never deletes a row. Then show that a CDC stream does.

4. **Prove convergence.** Apply the same set of events in two different
   orders (swapping two adjacent events) and show that the final table is
   the same — *except* when one of them is a DELETE of a row the other
   inserts. Explain why that exception exists.

5. **Reflection.** Your CFO asks why you are building a CDC pipeline
   instead of a nightly batch export. Using the amplification number from
   exercise 1 and the latency requirement, make the case. Then make the
   case *against* it. What would change your answer?

---

## 📖 Further Reading

- Google Cloud Datastream overview — https://cloud.google.com/datastream/docs/overview
- Datastream's replication model — https://cloud.google.com/datastream/docs/replication-overview
- Debezium's documentation on logical decoding — https://debezium.io/documentation/reference/connectors/mysql.html
- *Designing Data-Intensive Applications*, Martin Kleppmann, Chapter 7
  ("Transactions and Isolation") and Chapter 11 ("Streaming Data")
