# Top 50 — Google Cloud Datastream & Change Data Capture

> **50 questions · The highest-yield subset · Read this the night before**

These fifty questions were selected from the full bank by five criteria:
**high decision impact** (the answer changes what you build), **cross-layer**
(the answer connects the log to the merge to the operations), **quantifiable**
(a number is attached), **contested** (reasonable senior engineers disagree),
and **common misconception** (the wrong answer is what a lot of people say).

Every answer is written the way a senior engineer who has actually run this in
production would say it out loud: the direct answer first, then the mechanism,
then when the obvious alternative wins, then the failure you have seen, and
the numbers.

---

## The model

### 1. What is change data capture, and what does it give you that polling cannot?

CDC reads the database's write-ahead log and applies the changes it contains
to a destination table. The batch alternative polls the source for rows
modified since the last run.

The thing polling **structurally cannot** do is detect a delete. A polling
query reads `WHERE updated_at > last_run`; a deleted row is not in the table
at all, so there is no timestamp to compare and no way to notice it happened.
Either the pipeline maintains its own tombstone table — which is a CDC
implementation you wrote badly — or deleted rows linger forever.

The second thing polling cannot do is respect transaction boundaries. A
500-row transaction that is half-applied when the poll runs gives you a torn
read. The log records the commit atomically, so the reader sees whole
transactions.

**Failure story:** a retailer's nightly reconciliation kept showing a
difference of roughly 0.4% of orders. The pipeline polled on `updated_at`
and upserted. The difference was the deleted orders — cancelled and refunded
rows the pipeline never removed. For two years nobody investigated, because
"0.4% drift" read like a rounding error. It was 40,000 orders.

### 2. Walk me through the architecture of a CDC pipeline. Where do failures live?

Three layers: **the log**, **the transport**, and **the sink**.

The log is the source's WAL — MySQL binlog, Postgres WAL, Oracle redo —
written as part of committing a transaction, before the commit is
acknowledged. Reading it is sequential and cheap because the data is written
anyway.

The transport is whatever reads the log and delivers events: Datastream,
Debezium, Fivetran, Kafka Connect. It buffers, retries, may replay. This is
the layer most likely to deliver the same event twice.

The sink applies the events with a **keyed merge** — upsert-and-delete on a
merge key. This layer holds the semantic contract.

Knowing which layer a problem lives in is most of the debugging. A connection
error is layer 1 or 2. A table with wrong values but a healthy row count is
layer 3, and specifically the merge key.

**Failure story:** a team debugged for two days because "Datastream was
broken". The stream was fine, the connection was fine, the source was
producing changes the whole time. The merge key was `region` instead of
`customer_id`, so every update overwrote the wrong rows. Nothing was broken
except a config field, and the symptom pointed at every layer except the one
that was wrong.

### 3. What is the difference between the log and the table, and why does it matter?

The log is immutable and append-only. The table is mutable. A row that
changes five times produces five events in the log and one row in the table.

Four properties follow: **auditability** (the log is the complete history —
"what did this row look like at 3pm?"), **replayability** (re-apply the log
and rebuild the table exactly), **idempotency** (applying an event twice
has the same effect as applying it once, because the merge is keyed), and
**state lives in the destination, not the transport** (the transport can be
stateless, scaled horizontally, restarted freely).

**What catches people:** the log and the table answer different questions.
Counting rows in the log gives you five; counting rows in the table gives
you one. Both are correct. A dashboard built on the wrong one is wrong by a
factor of the churn rate, and it will look plausible.

### 4. What is event amplification, and how do you decide whether you need CDC?

**Event amplification = (number of change events) ÷ (number of rows in the
table).** It measures churn, and it is the single number that decides whether
CDC is worth it.

| Amplification | Table shape | Recommendation |
|---|---|---|
| ~1.0x | Append-only | Poll. CDC buys nothing. |
| 1.1–2x | Mostly append | CDC is defensible if latency matters |
| 5–20x | High churn | **CDC wins.** |
| 100x+ | A log table in disguise | Do you want a table at all? |

The mechanism: consider a 10-million-row table where 1% changes per hour.
Polling reads 10 million rows to find 100,000 changes, unless it has a
reliable `updated_at` index — and even then it is a random-access probe
across 10 million rows. CDC reads 100,000 events from a sequential log. That
is the difference between a job that scales with the table and one that
scales with the changes.

The course's own sample data sits at **~2.0×** — 377 change events over 200
customers — which is the low end of defensible.

### 5. Why must the destination table be empty before a backfill?

**Because the backfill's snapshot and the existing rows will conflict, and
the merge cannot resolve it.** The merge has no version information and no
timestamp comparison, so it has no way to know which copy of a row is
correct.

The result is duplicates that persist, and the only fix is to drop and
recreate the table and backfill again. This is the one procedure with no
shortcut, and it is worth stating plainly in an interview, because "can we
just backfill into the existing table?" is a question that always gets asked.

### 6. What is idempotency, and why does it matter so much here?

**Applying the same event twice has the same effect as applying it once.**
It is not a feature you configure in Datastream — it falls out of the
merge's shape, because every clause is an upsert or a delete *by key*. There
is no clause that appends.

It matters because four things happen routinely in a distributed system:
retries (a failed delivery is redelivered), replays (you rebuild the table
from the log), restarts (the transport restarts mid-stream), and
multi-consumer (two consumers write to the same table). Each of those is a
corruption event without idempotency.

The classic symptom is a customer table where every customer appears twice,
and nobody can say when it started — because it started the first time a
consumer retried.

### 7. What is the difference between a streaming merge and a synchronised merge?

A **streaming merge** applies an unbounded stream of changes: insert when the
key is new, update when matched, delete when matched-and-deleted. It never
infers deletions from absence.

A **synchronised merge** reconciles the target against a finite, complete
snapshot. It adds `WHEN NOT MATCHED BY SOURCE THEN DELETE`.

| | Streaming merge | Synchronised merge |
|---|---|---|
| Source | Unbounded stream of changes | Finite, complete snapshot |
| Infers deletes from absence | Never | Yes |
| Use | Live replication | Backfill, one-off sync |
| Datastream | The default | The backfill mode |

The distinction is conceptual and worth being able to state in one sentence:
**in a stream, the absence of a change is not evidence of a deletion**,
because a row that has not changed in an hour has simply not changed.

**Failure story:** a team built their own CDC consumer and included `NOT
MATCHED BY SOURCE`, reasoning that the destination should mirror the source.
Their table emptied itself every time the stream went quiet for a few
minutes, and refilled when the next batch of changes arrived.

---

## The merge

### 8. What exactly does Datastream do on the BigQuery side?

It applies the change events to the destination table with a **keyed merge** —
an upsert-and-delete on a configured merge key.

The distinction that matters to an interviewer: **Datastream does not "write
events to a table". It maintains a table.** The destination is a projection
of the stream's current state, and the merge is the projection function.

**Failure story:** a team believed the destination table contained the change
history and built an audit report on it. It contained the current state.
Every row appeared once with the latest values. The report was wrong for
every historical question it was asked, and nobody had a way to answer
historical questions from the destination — because the history was in the
log, in a different system, which they had not retained.

### 9. What does the merge key have to be, and why?

**The smallest set of columns that uniquely identifies a row in the source
table.** Usually the primary key, usually one column. It may be composite —
a tenant id plus an id, in a multi-tenant system.

| Property | Why | What breaks without it |
|---|---|---|
| **Unique** | A merge must match exactly one row | One update overwrites several rows |
| **Immutable** | The merge looks rows up by key | A changed key orphans the row |
| **Minimal** | Fewer columns, fewer chances to be wrong | A nullable key component fails to match |

The rule of thumb for the interview: **the source table's primary key**, and
nothing else. If the source has no primary key, that is a problem to fix in
the source, not something to work around in the merge key.

### 10. What happens if the merge key is not unique?

**One update matches several rows and overwrites all of them. Nothing
errors.**

This is the worst failure mode in CDC, because it is silent. The row count
does not change. The columns are populated. The table is wrong.

The detection that works is a **value-level comparison**, not a count:

```python
# Useless — passes with a wrong merge key.
assert len(destination_rows) == len(expected_rows)

# This one catches it.
assert destination_rows == expected_rows
```

**Failure story:** a pipeline merged on `email`, because email was in every
dashboard. A customer changed their email address, which orphaned their old
row, and the destination ended up with two rows for one customer. The row
count *grew*, so the count check passed. It took a customer complaint — a
customer appearing twice in a loyalty calculation — to surface it.

### 11. What happens if the merge key changes value?

**The row is orphaned and a duplicate is created.** The merge looks up the
row by the *new* key, does not find it, and inserts; the old row remains,
still keyed on the old value.

The fix is to merge on an immutable key — the primary key or a surrogate key.
Never on an email, a username, a slug, or any other attribute a user can
change.

### 12. What happens on an UPDATE for a row that is not in the destination table?

**Datastream inserts it**, rather than dropping it.

There are two possible behaviours and the choice matters. If the update were
dropped, data would be lost whenever a stream started mid-history and
received an update for a row it never saw inserted. Inserting it produces a
correct row, because the `after` image *is* the current state of that row.

The cost is that the destination can contain rows the source no longer has,
if a delete arrived before the insert and you applied them out of order. That
is why stream order matters.

**Failure story:** a consumer implemented the strict reading and dropped
updates for unknown keys. The pipeline looked healthy — no errors, no
rejects — and the destination was missing every row that had been updated
before the consumer started. The team did not notice for six weeks, because
the missing rows were exactly the recently-active customers, and the
dashboard they were watching was a monthly report.

### 13. What happens on a DELETE for a row that is not in the destination table?

**Nothing — it is a no-op, not an error.**

This is deliberate and it matters. A stream that starts mid-history will
contain deletes for rows it never saw inserted. If the merge treated that as
an error, the pipeline would crash on a completely normal situation.

The interesting detail is *why* a delete can identify a row at all: it carries
the **before** image. There is no "after" state for a row that no longer
exists, so the before image is what tells the merge which key to remove.

This is also why `binlog_row_image = FULL` matters. With `MINIMAL`, the
before image contains only the key columns — enough to delete, but not
enough to tell you *what* was deleted, which breaks audit and backfill.

### 14. What is `__op__` and why does it matter?

**It is Datastream's synthetic column recording which operation each change
event represents**, and it is what lets a single `MERGE` handle all three
operations.

```sql
WHEN MATCHED AND source.__op__ != 'DELETE' THEN UPDATE ...
WHEN MATCHED AND source.__op__ = 'DELETE'   THEN DELETE ...
```

It is not a column in your source table. If your source happens to have a
column called `__op__`, that is a name collision and you should rename it.

**Failure story:** a custom consumer did not use `__op__` and instead
inferred the operation from which image was null. That works for `INSERT` and
`DELETE`, but it cannot distinguish an `UPDATE` from an `INSERT` — both have
a non-null `after` image. Every update was applied as an insert, and the
destination table became a growing multiset.

### 15. Why should the BigQuery destination table be clustered on the merge key?

Because the merge sorts on the merge key before matching, and clustering lets
BigQuery **skip the sort and prune blocks**. For a CDC destination this is
the single most effective BigQuery optimisation available.

The mechanism: the merge's `ON` clause matches on `customer_id`. With
`CLUSTER BY customer_id`, the rows are physically sorted by that column, so
BigQuery can restrict the scan to the blocks containing the keys being
matched. Without clustering, every merge operation reads the whole table.

The practical effect: an unclustered CDC destination gets progressively more
expensive as it grows, because each merge touches more rows. A clustered one
stays roughly constant.

**Numbers:** an unclustered destination on a 50-million-row table saw merge
costs climb steadily over six months until the pipeline was the largest line
item on the BigQuery bill. Adding `CLUSTER BY customer_id` and partitioning
by ingestion date cut the merge cost by roughly an order of magnitude and
made it flat.

### 16. Should a CDC destination table be partitioned?

**Yes — partition by the ingestion date.** Two independent reasons.

First, cost. BigQuery storage is priced per byte, and partitioning lets you
expire old partitions with `ALTER TABLE ... DROP PARTITION` rather than a
`DELETE` that scans and rewrites.

Second, and more importantly, **merge cost**. A `MERGE` on a partitioned table
only touches the partitions it needs.

The caveat worth knowing: if you partition by ingestion date and the merge
matches on a row ingested a year ago, the merge must touch that old
partition. Some teams partition by the *source's* update timestamp instead,
so a row's partition changes as it is updated — but that requires the
`WHEN NOT MATCHED` clause to remove the old row, which the streaming merge
does not do. Partitioning by ingestion date is the simpler, safer choice.

---

## Configuration

### 17. What is `binlog_format=ROW`, and why does CDC need it?

`STATEMENT` records the **SQL statement** that was executed. `ROW` records
the **row images** — what each row looked like before and after.

CDC requires `ROW`, and it is not a preference. A statement-based log for a
500-row `INSERT` records one statement. To reconstruct what each row became,
the reader must interpret the statement against the table's current state —
which is not possible reliably, because the table may have changed since.
Statement-based replication also has ambiguity: `UPDATE t SET x = x + 1`
under `ROW` logs each row's old and new value; under `STATEMENT` it logs the
expression, and the reader must evaluate it.

The Postgres equivalent is `wal_level`, which defaults to `replica` and
**must** be changed to `logical`. Physical replication ships WAL files for a
standby; logical replication ships the row changes. CDC needs the logical one.

### 18. What is `binlog_row_image`, and what breaks if you set it to `MINIMAL`?

It controls how much of each row is written to the binary log.

| Setting | Logged | Consequence |
|---|---|---|
| `FULL` | Every column, before and after | Complete images. Backfills and audits work. |
| `MINIMAL` | Only changed columns and the key | Smaller and faster, but **before images are incomplete** |
| `NOBLOB` | All except large blobs | A middle ground |

`MINIMAL` breaks two things. A `before` image that contains only the key
means you cannot tell what the row used to contain — so you cannot
reconstruct history, and a delete event cannot say what was deleted. It also
means a `before` image and an `after` image have *different schemas*, which
every consumer has to handle.

Use `FULL`. The volume argument for `MINIMAL` is real on wide tables, and
the correctness argument is stronger.

### 19. What does the replication user need, and why is it a security concern?

For MySQL: `SELECT`, `REPLICATION SLAVE`, and `REPLICATION CLIENT`. For
Postgres: `REPLICATION` plus `pg_read_all_data` or table-level `SELECT`
grants, and `USAGE` on the schema.

`REPLICATION SLAVE` (MySQL) or `REPLICATION` (Postgres) is what lets the
reader read the binary log. `SELECT` is what lets it read the tables during
a backfill. `REPLICATION CLIENT` lets it query the server's replication
metadata.

The security concern is real and worth raising unprompted: **the replication
user can read the entire binary log**, which contains every change to every
table — including the contents of rows in tables you were not asked to
capture. A password column that was changed is in the log in plaintext. A
replication credential is therefore more sensitive than a normal application
credential, and it belongs in Secret Manager with a rotation schedule.

Scope it as narrowly as the connector allows. On Postgres, `pg_read_all_data`
can be replaced with per-table `SELECT` grants.

### 20. How does the network path from Datastream to the source database work?

Through a **VPC peering** established by a Datastream network config, with a
static IP allocated from a reserved range.

```text
  Datastream ──VPC peering──> your VPC ──> your database
       │
       └─ static IP from a reserved range, e.g. 10.0.0.2/28
```

The database's firewall must allow the **IP allocation's** address, and
that address is not the same as the Datastream service's outbound IP. This
is the most common first-run failure: the connection profile has the right
hostname and port, but the source's firewall has not been opened to the
allocated IP, so the connection times out.

The diagnostic distinction worth memorising: a **timeout** is almost always
a firewall or routing problem; a **connection refused** is a wrong host, a
wrong port, or nothing listening. That one distinction splits the search
space in half.

### 21. What is the read consistency window, and how do you choose it?

**How long Datastream waits after a transaction commits before reading its
changes, to guarantee it reads them in commit order.**

When transaction A commits at t=0 and transaction B commits at t=0.1, a
reader with no window might read B's changes first and apply them before A's.
The merge then converges on the wrong state.

The trade-off is direct: **the window is your latency floor**. A 5-second
window means a 5-second floor, plus the merge time. 1 second is usually
fine for a single-writer database; 5 seconds is the standard choice because
it has enormous headroom over normal write gaps; 10 seconds is for heavy
concurrent write loads.

The mistake to avoid: measuring latency during a quiet period and putting
that number in the SLA. You will measure something like 300 milliseconds,
quote sub-second replication, and then have a write burst push every event
past the window and your latency to 5.3 seconds. **Set the SLA from the
window, not from a measurement.**

### 22. How do you handle a source schema change that breaks the pipeline?

In order:

**1. Decide, before touching the pipeline, which of the three responses
applies** — widen, version, or migrate. The pipeline must not decide.

**2. Widen the destination column** if the change is compatible.

**3. If the change is breaking, create a new column or a new table** and let
the old one stay for historical queries.

**4. Update the destination config** with the new column mapping if the
column set genuinely changed.

**5. Add a migration window.** If the change is breaking and you cannot
migrate atomically, run the old and new streams into two tables, backfill
the new one, cut over the reads, and drop the old one later.

**Failure story:** a team added a `status` column as a string in the source,
then changed it to an integer. The pipeline coerced the values, because the
destination column was `STRING` and the consumer called `str()`. For six
months the destination held `"1"`, `"2"`, `"3"` as strings, and every numeric
aggregation silently returned zero. It surfaced when a finance report showed
revenue of 0 for a category that had never been zero.

### 23. What is the danger of a changed column type mid-stream?

**The stream contains a mix of representations, and a consumer with a fixed
schema will either reject the new events or silently coerce them.** Neither
is acceptable, because neither is a decision anyone made.

The three defensible responses, with their costs: **widen** the destination
column (free, correct when the new type is compatible); **new column, keep
the old** (correct when the semantics changed and you want both histories);
or **a new stream or table** (correct when the change is breaking and you
need a migration window).

The rule for a consumer: **treat every row image as a partial record.**
Coerce explicitly, and *count* what you could not read. A rejected value
that is counted is a data quality signal. One that raises is an outage. One
that is silently dropped is a lie you find in a quarter-end report.

---

## Operations and recovery

### 24. How do you tell a lagging stream from a broken one?

**A broken stream has an error message and a non-READY state. A lagging
stream is READY and delivering, just not fast enough.** They need completely
different responses, and the mistake is treating a lag problem as a
connectivity problem.

The test is arithmetic, not observational:

```text
  backlog growth = source write rate − pipeline processing rate
```

If the growth rate is positive, the pipeline is permanently behind — no
amount of waiting fixes it. A pipeline running 4% below the source's rate
falls behind forever.

**Failure story:** a team treated a lag problem as a connectivity problem for
a week. They were restarting the stream, checking the firewall, re-granting
privileges, and rebuilding the destination. None of it helped, because the
pipeline was working perfectly — it was just configured with a merge key
that made each operation take ten times longer than necessary. The fix was
one config change.

### 25. The stream is `READY` but the destination table is not updating. What do you check?

Work down the source side, cheapest checks first.

**1. Is the source producing changes at all?**

```sql
SHOW BINARY LOGS;
SHOW MASTER STATUS;
```

**2. Are the privileges still correct?**

```sql
SHOW GRANTS FOR 'datastream_user'@'%';
```

A password expiry on the replication user presents exactly like this: the
stream stays `READY`, the connection profile is valid, and nothing arrives.

**3. Is the binary log configured correctly?**

```sql
SHOW VARIABLES LIKE 'binlog_format';
SHOW VARIABLES LIKE 'binlog_row_image';
```

**4. Is the firewall open to the Datastream IP allocation?** A timeout
rather than a refusal points here.

**5. Is the source config capturing the tables you expect?** Then, if the
source is definitely producing changes and they are definitely not arriving,
check the destination side: the merge key, the service account's BigQuery
IAM, and the project's BigQuery quotas.

### 26. What does the `RUNNING` state mean, and is it a problem?

**The stream is up but has not yet reached a consistent state with the
source.** It is normal during the initial backfill and after a source
failover, and it is a problem if it persists.

The concerning case is `RUNNING` with no backfill in progress, which usually
means the read consistency window cannot keep up with the write load, or the
source has a networking problem that prevents the consistency check from
completing.

### 27. What is the difference between latency and lag, and why do you need both?

**Latency** is the delay for a single event — the time from the source's
commit to the merge completing. **Lag** is the total amount of unprocessed
change sitting between the source's current position and the stream's
position.

A pipeline can have low latency and high lag: it processes each event
quickly but not fast enough to catch up, and the backlog grows while every
individual event looks fine. A pipeline can have high latency and low lag: it
is caught up, but each event took a long time.

You need both because they have different causes and different fixes. High
latency with low lag is a merge performance problem. Low latency with
growing lag is a throughput problem. And a dashboard showing only recent
latency values will show 2 seconds while the backlog is four hours old.

### 28. How do you know the pipeline is delivering *correct* data, not just data?

**Reconcile the destination against the source, comparing values.** The
comparison is the whole point — a count check passes with a wrong merge key.

Three categories, each mapping to a distinct root cause: **MISSING** means
inserts were dropped or the backfill did not cover the table. **EXTRA**
means deletes were not applied. **VALUE_MISMATCH** means a wrong merge key or
a dropped update.

Run it on a **sample** nightly. A full comparison on a large table is
expensive; a random 10,000-row sample catches a systematic problem
immediately and a rare one eventually.

The most important subtlety: **reconcile against the source, not against the
stream.** Comparing the destination to a reconstruction from the stream only
proves the merge works. Comparing it to the source proves the *pipeline*
works.

### 29. The destination table is corrupted. How do you recover?

**Replay the log.** The binary log is the source of truth for what changed,
so a corrupted destination is always rebuildable.

```text
  1. Pause the stream.        (so nothing new arrives mid-rebuild)
  2. DROP the destination table.
  3. RECREATE it with the same schema.
  4. Update the stream with --backfill-all.
  5. Resume the stream.
```

The window while the stream is paused is safe — changes during it are in the
log and the stream resumes from where it left off.

### 30. The source's binary log was truncated. What now?

**A full re-backfill**, exactly as above. The stream cannot resume from a
log position that no longer exists.

This is a real risk and it has a specific cause: the reader was disconnected
for longer than the log retention period. On MySQL,
`binlog_expire_logs_seconds` bounds retention. On Postgres, the equivalent
protection is a **replication slot**, which prevents the WAL from being
truncated past a disconnected reader.

The Postgres slot is a double-edged tool: it prevents data loss, but it also
holds WAL on disk indefinitely while the reader is down. A common operational
finding is a slot that has been inactive for weeks, holding several gigabytes
of WAL for a consumer that no longer exists.

### 31. What causes a BigQuery "too many table update operations" error?

**The merge is generating more DML statements per second than BigQuery's
per-table update quota allows.** A high-throughput CDC stream can exceed it.

The fixes, in order of preference:

**1. Batch the changes.** Group the events into fewer, larger merge statements
rather than one per event. This is the real fix — a merge of 1,000 changes
costs far less than 1,000 merges of one change.

**2. Cluster on the merge key.** A clustered table lets BigQuery prune blocks
and skip the sort, which reduces the time each merge holds its quota slot.

**3. Raise the quota.** Available on some projects, and it treats the
symptom.

**4. Partition by ingestion date.** A merge that only touches recent
partitions is faster and holds its slot for less time.

**Failure story:** a pipeline moving 8,000 events per second hit the quota
constantly, and the standard advice was to raise the quota. Raising it made
the pipeline faster and it hit a *different* limit — BigQuery's DML statement
rate — which manifested as a much harder-to-diagnose partial-failure pattern
where some events were applied and others silently dropped by the merge's
own error handling. The actual fix was batching, which reduced the DML rate
by three orders of magnitude.

### 32. How do you monitor a CDC pipeline? What are the metrics that matter?

Four signals, and nothing else:

| Signal | What it tells you |
|---|---|
| **Latency** | How far behind is the destination? |
| **Throughput** | How many events per second are flowing? |
| **Error rate** | Are events being rejected? |
| **Lag** | How much unprocessed change is there? |

What does **not** matter: the row count (it goes up and down with churn and
says nothing about health), and the stream state being `READY` (it means the
stream has not failed, not that events are flowing).

The alert worth writing is on the **backlog growth rate**, not its size. A
backlog that is shrinking is healthy. One growing at 200 events per second
is not, even while it is still small.

### 33. How do you cost a CDC pipeline, and what are the levers?

Three cost sources: **Datastream processing**, **BigQuery**, and **the
source**. Datastream charges per GB of change data processed. BigQuery
charges for storage, queries, and the DML the merge generates. The source's
cost is the binary log volume it generates.

Three levers, in order of impact:

**1. Capture less.** Datastream processes the change data for every table in
the source config, including tables you will filter out downstream.
Excluding one high-churn audit table at the source can remove 99% of the
processing volume. This is the biggest lever and it costs one line of
configuration.

**2. Cluster and partition the destination.** An unclustered destination's
merge cost grows with the table. Clustering on the merge key makes it
roughly flat.

**3. Set retention.** On the source side, `binlog_expire_logs_seconds`
bounds how much log is retained. On the destination, partition expiration
bounds how much is stored.

**Failure story:** a team replicated eight tables and found the bill was
fifteen times their estimate. Seven of the tables were audit and history
tables that nobody queried. Excluding them at the source cut the cost by
98%. The lesson was not about cost estimation — it was that the destination
config should list the tables you *use*, not the tables you *have*.

### 34. Does Datastream preserve the order of changes?

**Yes — within a single source, Datastream delivers changes in the order the
source committed them.** That is why the merge converges: an update always
arrives after its insert, and a delete after the update that preceded it.

The ordering guarantee comes from reading the log sequentially, and it is
what makes the keyed merge sufficient.

The exception is when you fan a CDC stream out through Kafka. **Kafka
guarantees ordering within a partition and nothing across partitions.** So
the Kafka partitioning key must be the same key you merge on.

### 35. What does the merge do with a DELETE that arrives before its INSERT?

**Delete-then-insert leaves the row. Insert-then-delete removes it.**

The merge is order-sensitive for the delete/insert pair on the same key, and
it must be: these are genuinely different outcomes, and there is no merge
that could treat them the same without being wrong.

In a well-behaved CDC stream this does not happen, because the log preserves
commit order. But it happens in three real situations: a stream that starts
mid-history; a Kafka fan-out where the partitioning key does not match the
merge key; and multiple source databases feeding one destination, where
there is no global order at all.

---

## Kafka and streaming

### 36. What does Kafka actually guarantee, and what does that mean for a database write?

**At-least-once.** Records are delivered to exactly one consumer within a
consumer group, and may be **redelivered** if the consumer fails before
committing its offset.

For a database write, the same message can arrive twice:

```text
  1. The function receives message M
  2. The function writes M to PostgreSQL   ← succeeds
  3. The function returns 200
  4. The response is lost in transit
  5. The connector never advances its offset
  6. The connector redelivers M
  7. The function writes M again              ← duplicate
```

The conclusion: **the destination must enforce idempotency, not the
application.** The application will be retried; the database constraint will
not.

### 37. Why does the Kafka path differ from the Datastream path?

**The Datastream destination is stateful and converges. The Kafka
destination is stateless and appends.**

| | Datastream → BigQuery | Kafka → Cloud Run → Cloud SQL |
|---|---|---|
| Semantics | Stateful — the table converges | Stateless — each message is a fact |
| Delivery | Exactly-once within the merge | At-least-once |
| Ordering | Preserved (source order) | Per-partition only |
| State kept | The full current table | None, unless you dedupe |

A CDC destination converges: replay the whole stream and you get the same
table. A Kafka destination does not — it is a growing log of whatever
arrived, and the same message can arrive twice. So the Kafka path needs a
uniqueness constraint that the Datastream path gets for free from its merge
key.

### 38. What is a consumer group, and why does it matter for ordering?

**A set of consumers that share a topic's partitions, where each partition is
assigned to exactly one consumer in the group.**

Two consequences: **load balancing** (adding consumers lets them share the
partitions, so throughput scales with consumer count — up to the partition
count) and **ordering** (records within a partition are delivered in order,
and because only one consumer in the group holds a partition, that order is
preserved end to end; records *across* partitions have no order relationship).

The trap: **if you produce messages for the same entity to different
partitions, they can be consumed out of order.**

### 39. Why must the Kafka partitioning key match the merge key?

**Because ordering and merging are only compatible if they agree.** The merge
assumes it sees each key's changes in order; the partitioner is what
guarantees an order. If they disagree, the merge sees updates before their
inserts and creates duplicates.

Concretely: merging on `transaction_id` while partitioning by `customer_id`
means a given transaction's insert and its update may land in different
partitions and arrive in either order. The update arrives first, the merge
does not find the row, and it inserts — then the real insert arrives and
creates a duplicate.

The rule, stated for an interview: **when you fan a CDC stream out through
Kafka, the partition key and the merge key must be the same value.** They are
not two independent decisions; they are one decision expressed twice.

**Failure story:** a team partitioned by `customer_id` while the destination
merged on `transaction_id`. Every customer had thousands of transactions, so
each partition held them in order, but the merge looked each row up by a
different key — and an update arriving before its insert created a duplicate
row. Every night the deduplication job found a few hundred extra rows and
deleted them. The pipeline was "self-healing" and nobody asked why it was not
healing correctly.

### 40. How does the Confluent Google Cloud Functions sink connector work?

It is a **Confluent-managed connector** that runs on Confluent's
infrastructure. It polls the topic and POSTs each message to your Cloud Run
function's HTTP endpoint.

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

1. **The connector is stateless from your side.** It holds the offsets. If
   the function returns a **4xx**, the connector treats it as a permanent
   failure and skips the record. If it returns a **5xx**, it retries.
2. **The function must be idempotent**, because the connector will redeliver
   on a retry.
3. **The status code is your retry policy.** Getting it backwards means
   either dropping good data (4xx for a transient database error) or
   retrying a poison message forever (5xx for a malformed message).

### 41. How should a Cloud Run function handle a poison message?

**Return a 4xx, and make sure a dead-letter queue is configured.**

A poison message is one that will always fail — a malformed payload, a
missing required field, a value that violates a constraint. The connector's
retry policy is typically five attempts, after which the record goes to the
dead-letter queue topic **if one is configured**.

| Situation | Status | Connector behaviour |
|---|---|---|
| Malformed payload, validation failure | **4xx** | Skip (or route to the DLQ) |
| Database temporarily unreachable | **5xx** | Retry |
| Success | **200** | Commit the offset |
| Unexpected internal error | **5xx** | Retry |

Without a DLQ, the record is dropped without a trace. That is a silent data
loss, and it is invisible unless you count the rejects.

**Failure story:** a function returned 500 for everything, including
malformed payloads. The connector retried each five times and then dropped
it. The team discovered six months later, during a data audit, that a
customer segment had been missing for half a year. The DLQ was never
configured, so the dropped records existed nowhere.

### 42. Why must the INSERT statement in the function be parameterised?

**Because it is the difference between storing a string that contains a quote
and executing that string.**

```python
# Vulnerable — the payload becomes SQL.
statement = f"INSERT INTO transactions VALUES ('{row['product_id']}', ...)"

# Correct — the payload is data.
statement = "INSERT INTO transactions (transaction_id, ...) VALUES (%s, ...)"
cursor.execute(statement, values)
```

This is not a style preference, and the test that proves it is a payload
with a quote in it. A payload of `p0001'; DROP TABLE transactions; --` in a
vulnerable implementation produces a statement containing `DROP TABLE`. In a
parameterised implementation it produces a statement with `%s`, and the
payload sits in the values tuple as a string literal.

The reason the vulnerable version survives testing is that **test data does
not contain quotes**. Every functional test passes. The first production
payload with an apostrophe in it is the one that finds the bug.

### 43. What is the right way to handle a duplicate in the Kafka path?

**Catch the unique-violation error and treat it as success.** The constraint
does the work; the application recognises the outcome.

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

The keying question worth raising: the primary key must be the **business
key** — `transaction_id`, not `customer_id`. Two legitimate transactions by
the same customer are not duplicates, and keying on `customer_id` would
silently drop half your data.

### 44. Why does a Cloud Run function need `min-instances` for a streaming consumer?

**Because a cold start adds seconds of latency to the first message, and a
stream consumer's SLA is usually measured in milliseconds.**

Cloud Run scales to zero when idle. The next request pays the container
start, the runtime initialisation, and the import of your dependencies. For
a Kafka consumer that is continuously receiving messages, that cold start
lands on a real message, and the consumer's offset does not advance until
the function returns — so the message's processing latency spikes.

Setting `min-instances` keeps N instances warm. It costs money continuously,
which is why it is a deliberate trade: you are paying for warm capacity to
meet a latency SLA.

The alternative is to accept the cold start and make the function's
initialisation cheap. Caching the database connection and the secret in
module scope — which the course's `cloud_function.py` does — helps, but it
does not remove the container start itself.

### 45. How do you store the database password for a Cloud Run function?

**In Secret Manager, fetched at runtime, cached in memory, and never in the
source, the environment variables, or the image.**

```bash
gcloud functions deploy ingest-transaction \
    --gen2 --runtime python312 --region us-central1 --source . \
    --entry-point handle_event --trigger-http --no-allow-unauthenticated \
    --set-env-vars="INSTANCE_CONNECTION_NAME=project:region:instance" \
    --set-secrets="DB_PASSWORD=db-password:latest"
```

The `--set-secrets` flag mounts the secret as an environment variable **at
runtime**, so the value is never baked into the container image.

Two rules that follow: **never use `--set-env-vars` for the password
itself** (that places it in the function's configuration, visible to anyone
with IAM access), and **never put it in the source or in a `Dockerfile` `ENV`
line** (both are baked into the image and persist in the registry).

**Failure story:** a team set the database password as a plain environment
variable, "just for the first deploy". The container image was later
published to a shared registry, and the password went with it. Rotating it
was straightforward; the audit was not.

### 46. What does Confluent Cloud actually bill you for?

**Data stored and data transferred — not message count, not partitions, not
consumers.**

That is the surprise. A topic with 10 million small messages can cost more
than one with 1 million large ones, and a topic with a high retention and a
modest message rate can cost more than one with a huge rate and short
retention.

Two consequences: **set retention on every topic** (the default is unbounded,
and unbounded retention on a high-volume topic is an unbounded bill), and
**watch the transfer cost, not just the storage cost** (every message is
transferred in from the producer and out to the consumer, so a fan-out to
three consumers triples the egress).

The practical numbers: a moderate pipeline moving a few gigabytes a day
costs a few dollars a month with sensible retention. The same pipeline with
unbounded retention on a high-volume topic costs hundreds, because the
storage accumulates without limit.

---

## Design and trade-offs

### 47. When would you use a Kafka-based CDC pipeline rather than Datastream?

**When you need to fan the change stream out to multiple consumers, or when
the source is not a database.**

1. **Fan-out.** Datastream's BigQuery destination is one destination. If five
   teams need the change stream — a warehouse, a search index, an ML feature
   store, a fraud service, an audit log — Kafka lets all five subscribe
   independently. Each gets its own consumer group and its own offsets, and
   one slow consumer does not hold up the others.

2. **Non-database sources.** Kafka is the natural transport for application
   events, third-party feeds, and anything that is not a database with a
   binary log.

3. **Decoupling.** The producer does not know or care who consumes.

The reasons *not* to: it is more infrastructure, it introduces at-least-once
semantics you must handle yourself, and it loses the transactional guarantees
that the log-based approach gives you. If you have one destination and it is
BigQuery, Datastream is less work and fewer failure modes.

The honest comparison for an interview: **Datastream is the better tool for
"replicate this database into the warehouse". Kafka is the better tool for
"publish the change stream so anything can subscribe".**

### 48. What is the difference between Cloud Run and Cloud Functions for this use case?

**Cloud Run is the more flexible option and is what you would build today;
Cloud Functions is what Confluent's connector targets.**

| | Cloud Functions (gen2) | Cloud Run |
|---|---|---|
| Trigger | Event-driven | Any — HTTP, background, scheduled |
| Concurrency | 1 per instance by default | Configurable, up to 1000 per instance |
| Cold start | Yes | Yes, but `min-instances` can remove it |
| Best for | Small, event-driven handlers | Longer requests, higher throughput |

The difference that matters in production is `min-instances`, and the
concurrency setting. A Cloud Function processing one message per invocation
at one request per instance cannot keep up with a high-throughput topic,
because each invocation pays a full round trip. Cloud Run's concurrency lets
one instance process many messages in flight.

If you are using the Confluent sink connector, Cloud Functions is the path of
least resistance. If you are building from scratch, use Cloud Run.

### 49. When should you *not* use CDC?

When the workload does not need it. The decision metric is event
amplification.

At roughly 1.0x, the table is append-only: rows are inserted and never
change. CDC buys you nothing, because there are no updates and no deletes to
detect. A nightly batch extract is simpler and cheaper. CDC's only advantage
is latency, and if your SLA is "within the hour", a 15-minute poll meets it
at a fraction of the cost and complexity.

CDC also does not earn its keep when the changed set is nearly as large as
the table. Polling at 95% amplification reads almost everything every poll.

The third case is when you need *historical* correctness rather than current
state. If the requirement is "what did the ledger look like on 30 June",
you want a snapshot or an immutable history table, not a CDC destination. A
CDC table gives you the current state; the log gives you the history, and
usually in a different system.

### 50. What is the single most common mistake in a CDC interview answer?

Answering with a **tool name** instead of a **mechanism and a number**. "Use
a merge key" is a non-answer. "The merge key must be the source's primary
key, because it has to be unique — one update overwriting several rows is
silent, the row count stays plausible, and only a value-level reconciliation
catches it" is an answer: mechanism, failure, boundary condition.

The second most common is claiming a guarantee Datastream does not make.
"Datastream is exactly-once" is the trap. Datastream's merge is idempotent,
so the destination converges — but the *transport* can deliver the same
event twice, and the reason that is safe is the merge, not a delivery
guarantee. The third is treating a lag problem as a connectivity problem.

**Why this matters:** a senior interviewer is not checking whether you know
the API. They are checking whether you can predict what your pipeline will do
at 100× the data volume, on a source you do not control, when something fails
at 3 a.m. Every answer here is structured to give that signal: the mechanism,
the trade-off, the failure, the number.

---

## Where to go next

- The full module-by-module bank lives alongside this file — start with
  [README.md](README.md) for the study plan and the question index.
- For the foundational reading behind questions 1–16, see
  [01-what-is-change-data-capture.md](../chapters/01-what-is-change-data-capture.md).
- The one-page reference for merge rules, config and flags is
  [CHEATSHEET.md](../resources/CHEATSHEET.md).
