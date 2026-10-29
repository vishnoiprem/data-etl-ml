# Datastream & CDC FAQ

> The questions students actually ask.

---

## Getting started

### Do I need a GCP project to follow the course?

**No.** Every chapter, every notebook and the whole project run on your
machine with no credentials, no billing and no network. The GCP sections
(modules 4, 5 and 6) are optional and are clearly marked.

The reason the course is built this way is that a CDC pipeline that
succeeds on your machine teaches you more than one that succeeds on GCP
after an hour of IAM debugging. The *merge semantics* — which is the hard
part — are identical in both.

### How long does the course take?

Roughly **30–35 hours** of focused work: about 12 hours of reading
(chapters), 8 hours in the notebooks, 8 hours on the project, and 6 hours
on the interview questions. The chapters are independent after module 3, so
you can reorder them.

### What Python version do I need?

**3.10–3.13.** The course was developed and tested on **Python 3.13**.

### Do I need to know Kafka?

No. Modules 1–4 are pure CDC and need only SQL and Python. Module 5
introduces Kafka from the consumer side — topics, partitions, consumer
groups, offsets — and assumes nothing more than that.

---

## The core model

### What is the difference between CDC and batch ETL?

CDC reads the database's write-ahead log and applies the changes it
contains. Batch ETL polls the source for rows modified since the last run.

The thing polling **structurally cannot** do is detect a delete: a deleted
row is not in the table, so there is no timestamp to compare. Polling
pipelines solve this by maintaining their own tombstone table — which is a
CDC implementation you wrote badly.

### What is event amplification?

**(Number of change events) ÷ (number of rows in the table).**

It measures churn, and it is the single number that decides whether CDC is
worth it. At ~1.0× the table is append-only and CDC buys you nothing. At
5–20× CDC clearly wins. The course's own sample data sits at ~1.9×.

### Why not just read the tables directly?

Four reasons, and only the first is about performance:

1. **Performance** — the log is sequential; a table read is random access.
2. **Deletes** — the log contains delete events; a table read cannot see them.
3. **Transaction boundaries** — the log records the commit as a unit.
4. **Replayability** — the log is a durable history; a table read gives only current state.

### What is the read consistency window?

How long Datastream waits after a transaction commits before reading its
changes, to guarantee it reads them in commit order. It is your **latency
floor**: a 5-second window means a 5-second floor. Set the SLA from the
window, not from a quiet-period measurement.

### Why is idempotency not something I configure?

Because it falls out of the merge's shape. Every clause of the merge is an
upsert or a delete *by key*; there is no clause that appends. Applying an
event twice therefore has the same effect as applying it once.

---

## The merge

### Why must the merge key be unique?

Because a merge must match **exactly one** row. If it matches several, one
update overwrites all of them, and **nothing errors**. The row count stays
plausible, the columns are populated, and the table is silently wrong.

This is the worst failure mode in CDC, and the only reliable detection is a
**value-level** comparison — a row-count check passes.

### Why must the merge key be immutable?

Because the merge looks rows up by key. If an update changes the key value,
the merge looks up the *new* key, does not find the row, and inserts — while
the old row remains, still keyed on the old value. Two rows, one entity.

Never merge on an email, a username, a slug, or a phone number.

### What happens on an UPDATE for a row that is not in the destination?

**It is inserted.** The `after` image *is* the current state of that row, so
inserting it produces a correct row, and dropping it would lose data
whenever a stream starts mid-history.

### What happens on a DELETE for a row that is not in the destination?

**Nothing — a no-op, not an error.** A stream that starts mid-history will
contain deletes for rows it never saw inserted, and crashing on that would
be a bug.

### Why is there no `WHEN NOT MATCHED BY SOURCE THEN DELETE`?

Because **in a stream, the absence of a change is not evidence of a
deletion.** A row that has not changed in an hour has simply not changed; a
merge that deleted every unmatched row would empty the table continuously.

That clause belongs to a *synchronised* merge, where the source is a finite,
complete snapshot — i.e. a backfill.

### What is `__op__`?

Datastream's synthetic column recording which operation each event
represents. It is not a column in your source table, and it is what lets one
`MERGE` statement handle INSERT, UPDATE and DELETE.

If your source table has a column called `__op__`, rename it.

### Should I use `INSERT ... ON CONFLICT DO NOTHING` instead of catching the error?

Both work. `ON CONFLICT (key) DO NOTHING` avoids the exception and is
Postgres-specific and cleaner. Catching `UniqueViolation` is portable and
lets you log the duplicate, which is useful for counting rejects.

Either way, **the constraint does the work** — it is the last line of
defence and nothing above it can be bypassed.

---

## Schema and backfills

### What happens when I add a column to the source?

The destination gains the column and older rows have `NULL`. That is
correct — those rows genuinely predate the column, and inventing a value
would be a lie that propagates into every downstream average.

### What happens when I change a column's type?

The stream contains a mix of representations, and a consumer with a fixed
schema will either reject the new events or silently coerce them. Neither
is acceptable, because neither is a decision anyone made.

The three defensible responses: **widen** the destination column (free, when
the types are compatible); **a new column, keeping the old** (when the
semantics changed); or **a new table** with a migration window (when the
change is breaking).

The rule for a consumer: **treat every row image as a partial record.**
Coerce explicitly and *count* what you could not read.

### Do I have to drop the destination table before a backfill?

**Yes.** The backfill's snapshot and the existing rows will conflict, and
the merge cannot resolve it — it has no version information and no timestamp
comparison. The result is persistent duplicates, and the only fix is to
drop, recreate, and backfill again.

### What if the binary log was truncated?

The stream cannot resume from a log position that no longer exists, so you
need a full re-backfill. This usually happens because the reader was
disconnected for longer than the log retention period. On Postgres, a
**replication slot** prevents this — and holds WAL on disk indefinitely
while the reader is down, so an unmonitored slot can fill the disk and take
Postgres down.

---

## Operations

### How do I tell a lagging stream from a broken one?

**A broken stream has an error message and a non-READY state. A lagging
stream is READY and delivering, just not fast enough.**

The test is arithmetic: `backlog growth = source write rate − processing
rate`. If it is positive, the pipeline is permanently behind and no amount
of waiting fixes it.

### The stream is `READY` but the table is not updating. Where do I look?

Cheapest checks first:

1. Is the source producing changes at all? `SHOW MASTER STATUS;`
2. Are the privileges still correct? `SHOW GRANTS FOR 'datastream_user'@'%';`
3. Is the binary log configured right? `SHOW VARIABLES LIKE 'binlog_format';`
4. Is the firewall open to the **IP allocation**? A timeout points here.
5. Is the source config capturing the tables you expect?

A password expiry on the replication user presents exactly like this: the
stream stays `READY`, the connection profile is valid, and nothing arrives.

### What is the difference between latency and lag?

**Latency** is the delay for a single event. **Lag** is the total
unprocessed change. A pipeline can have low latency and high lag (fast per
event, not fast enough in aggregate), or high latency and low lag (caught
up, but one slow merge batch).

You need both because they have different causes and different fixes, and
because a dashboard showing only recent latency values will show 2 seconds
while the backlog is four hours old.

### How do I verify the pipeline is delivering *correct* data?

Reconcile the destination against the source, **comparing values**. Three
categories: `MISSING` (inserts dropped), `EXTRA` (deletes not applied),
`VALUE_MISMATCH` (wrong merge key or dropped update).

The subtlety: **reconcile against the source, not against the stream.**
Reconstructing the expected table from the same events you fed the
destination only proves the merge works — a pipeline that captured the
wrong table entirely will reconcile perfectly.

### What causes "too many table update operations"?

The merge is generating more DML statements per second than BigQuery's
per-table quota allows. The real fix is **batching** — a merge of 1,000
changes costs far less than 1,000 merges of one change. Clustering on the
merge key helps too, by shortening the time each merge holds its quota slot.

Raising the quota treats the symptom, and pushes you into a *different*
limit.

### Which four metrics should I alert on?

**Latency, throughput, error rate, lag.** Alert on the *growth rate* of
the lag, not its size — a shrinking backlog is healthy, and one growing at
200 events per second is not, even while it is still small.

Do **not** alert on the row count (it churns) or on the stream state being
`READY` (it means "not failed", not "delivering").

---

## The Kafka path

### When should I use Kafka instead of Datastream?

**When you need to fan the change stream out to multiple consumers, or when
the source is not a database.**

If five teams need the change stream — a warehouse, a search index, an ML
feature store, a fraud service, an audit log — Kafka lets all five
subscribe independently, each with its own consumer group and offsets, and
one slow consumer does not hold up the others.

The honest comparison: **Datastream is the better tool for "replicate this
database into the warehouse". Kafka is the better tool for "publish the
change stream so anything can subscribe".**

### Why must the Kafka partitioning key match the merge key?

Because ordering and merging are only compatible if they agree. The merge
assumes it sees each key's changes in order; the partitioner is what
guarantees an order.

They are not two independent decisions — they are **one decision expressed
twice**.

### Kafka delivers at-least-once. What does that mean for my database?

The same message can arrive twice, so the destination must enforce
idempotency. The application will be retried; the database constraint will
not.

```text
  1. The function receives message M
  2. The function writes M to PostgreSQL   ← succeeds
  3. The function returns 200
  4. The response is lost in transit
  5. The connector never advances its offset
  6. The connector redelivers M
  7. The function writes M again              ← duplicate
```

Steps 2–4 are not a rare race. They are a normal consequence of a
distributed system, and the rate is proportional to your message volume.

### What status code should the function return?

| Situation | Status |
|---|---|
| Malformed payload, validation failure | **4xx** |
| Database temporarily unreachable | **5xx** |
| Success | **200** |
| Unexpected internal error | **5xx** |

Getting it backwards means either dropping good data or retrying a poison
message forever.

### What is a dead-letter queue and do I need one?

A topic where records go after the connector exhausts its retries. **You
need one**, because without it the record is dropped without a trace — a
silent data loss that is invisible unless you count the rejects.

### Why does the function need `min-instances`?

Because a cold start adds seconds of latency to the first message, and a
stream consumer's SLA is usually in milliseconds. Cloud Run scales to zero
when idle, and that cold start lands on a real message.

It costs money continuously, and it is a deliberate trade: warm capacity
bought with a monthly bill.

### Cloud Run or Cloud Functions?

**Cloud Run** is the more flexible option and is what you would build today
— configurable concurrency, up to 1000 requests per instance. **Cloud
Functions** is what Confluent's sink connector targets, so if you are using
that connector, it is the path of least resistance.

### Where does Confluent Cloud's cost surprise people?

It bills on **bytes stored and bytes transferred** — not message count, not
partitions, not consumers. A topic with 10 million small messages can cost
more than one with 1 million large ones.

Set retention on every topic. The default is unbounded, and unbounded
retention on a high-volume topic is an unbounded bill.

---

## Security

### Where do I put the database password?

In **Secret Manager**, fetched at runtime, cached in memory, and never in the
source, the environment variables, or the image.

```bash
gcloud functions deploy ingest-transaction \
    --gen2 --runtime python312 --region us-central1 --source . \
    --entry-point handle_event --trigger-http --no-allow-unauthenticated \
    --set-secrets="DB_PASSWORD=db-password:latest"
```

`--set-secrets` mounts the secret at runtime. `--set-env-vars` writes it
into the function's configuration, where anyone with IAM access can read
it.

### Is the replication user dangerous?

**Yes, and it is worth raising in an interview.** The replication user can
read the entire binary log, which contains every change to every table —
including the contents of rows in tables you were not asked to capture. A
changed password is in the log in plaintext.

Scope it as narrowly as the connector allows, and rotate it.

### Do I need to worry about SQL injection in the CDC function?

**The parameterisation question, yes.** Not because CDC payloads are
adversarial, but because they are arbitrary strings from a source system:

```python
# Vulnerable — the payload becomes SQL.
statement = f"INSERT INTO transactions VALUES ('{row['product_id']}', ...)"

# Correct — the payload is data.
cursor.execute("INSERT INTO transactions (...) VALUES (%s, ...)", values)
```

The reason a vulnerable version survives testing is that **test data does
not contain quotes**. The first production payload with an apostrophe finds
the bug.

---

## Miscellaneous

### Can I use Datastream with Postgres?

**Yes.** Postgres needs `wal_level = logical` (the default is `replica`),
a replication user with the `REPLICATION` attribute, and — ideally — a
**replication slot** so the WAL is not truncated past a disconnected
reader.

### Does the course require a Confluent account?

**No.** Module 5 explains the semantics and the contract; the code runs
against a local JSONL file in replay mode. You need an account only to
deploy for real.

### Where do I go if I want to compare this with Debezium or Fivetran?

Read the merge semantics in `project/cdc.py` and compare. Every CDC tool —
open source or commercial — has to implement the same four merge
behaviours: insert when new, update when matched, delete when
matched-and-deleted, and the upsert-on-unknown-update. If a tool's
behaviour differs from that table, that difference is the interesting part.

### What is the single most useful thing to remember from this course?

**The merge key, and the fact that the destination must enforce
idempotency.**

Everything else — the log format, the window, the transport, the billing —
varies by tool and by environment. But the destination always has to be
keyed on something unique and immutable, and it always has to tolerate
seeing the same event twice. Get those two right and most of the failures
in this course cannot happen.

---

## Where to go next

- The chapters — [../chapters/](../chapters/)
- The interview bank — [../interview/](../interview/)
- The one-page reference — [CHEATSHEET.md](CHEATSHEET.md)
- The setup guide — [SETUP.md](SETUP.md)
