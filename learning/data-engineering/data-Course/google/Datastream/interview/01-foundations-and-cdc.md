# Module 1 — Foundations & Mental Model

> **14 questions · Module 1 · Foundations & Mental Model**

---

## The fundamentals

### 1. What is change data capture, and what problem does it solve that batch ETL cannot?

**Change data capture is reading a database's write-ahead log and applying the changes it contains to a destination table.** The batch ETL alternative is polling: periodically querying the source for rows modified since the last run.

The problem polling *structurally* cannot solve is **delete detection**. A polling query reads rows where `updated_at > last_run`. A deleted row is not in the table at all, so there is no timestamp to compare and no way to notice it happened. Either the polling pipeline maintains its own tombstone table — which is a CDC implementation you wrote badly — or deleted rows linger forever. CDC sees the delete as an explicit event in the log.

The second problem polling cannot solve is **transaction boundaries**. A 500-row transaction that is half-applied when the poll runs gives you a torn read — an order with some line items but no header. The log records the commit atomically, so the reader sees whole transactions.

The third is **cost scaling**. Polling reads the whole changed set on every poll, and if it must scan to find it, the work scales with the *table*. CDC reads the log sequentially, and the work scales with the *changes*.

The failure story: a retailer's nightly reconciliation kept showing a difference of roughly 0.4% of orders. The pipeline polled on `updated_at` and upserted. The difference was the deleted orders — cancelled and refunded rows the pipeline never removed. For two years nobody investigated, because "0.4% drift" read like a rounding error. It was 40,000 orders.

### 2. Walk me through the architecture of a CDC pipeline. What are the components and where do failures live?

Three layers: **the log**, **the transport**, and **the sink**.

**The log** is the source database's write-ahead log — MySQL's binlog, Postgres's WAL, Oracle's redo log. It is written by the database as part of committing a transaction, before the commit is acknowledged. Reading it is sequential and cheap, because the data is written anyway.

**The transport** is whatever reads the log and delivers change events: Datastream, Debezium, Fivetran, Kafka Connect. It buffers, retries, and may replay. This is the layer most likely to deliver the same event twice, and the layer most likely to have a network problem.

**The sink** applies the events to a destination table. It is a **keyed merge** — upsert-and-delete on a merge key. This layer holds the semantic contract.

Knowing which layer a problem lives in is most of the debugging. A connection error is layer 1 or 2. A table with wrong values but a healthy row count is layer 3, and specifically the merge key.

The failure story that organises this: a team debugged for two days because "Datastream was broken". The stream was fine, the connection was fine, and the source was producing changes the whole time. The merge key was `region` instead of `customer_id`, so every update was overwriting the wrong rows. Nothing was broken except a config field, and the symptom pointed at every layer except the one that was wrong.

### 3. What is the difference between the log and the table, and why does it matter?

**The log is immutable and append-only. The table is mutable.** A row that changes five times produces five events in the log and one row in the table.

Four properties follow, and they are the reason CDC is valuable:

- **Auditability.** The log is the complete history. You can answer "what did this row look like at 3pm?"
- **Replayability.** You can re-apply the log from the beginning and rebuild the table exactly. This is how you recover from a corrupted destination.
- **Idempotency.** Applying the same event twice has the same effect as applying it once, because the merge is keyed.
- **State lives in the destination, not the transport.** The transport can be stateless, scaled horizontally, and restarted freely.

What catches people: the log and the table answer different questions. Counting rows in the log gives you five; counting rows in the table gives you one. Both are correct. A dashboard built on the wrong one is wrong by a factor of the churn rate, and it will look plausible.

The production symptom: a team monitored their CDC pipeline by counting the rows in the change-event table. The count grew without bound and they paged themselves nightly for a month. The destination table was perfectly healthy. They were measuring the log, not the table.

### 4. When would you *not* use CDC?

When the workload does not need it. The decision metric is **event amplification** — the number of change events divided by the number of rows in the table.

At roughly 1.0x, the table is append-only: rows are inserted and never change. CDC buys you nothing, because there are no updates and no deletes to detect. A nightly batch extract is simpler and cheaper. CDC's only advantage is latency, and if your SLA is "within the hour", a 15-minute poll meets it at a fraction of the cost and complexity.

CDC also does not earn its keep when the changed set is nearly as large as the table. Polling at 95% amplification reads almost everything every poll. The economics that favour CDC — work scaling with changes rather than with the table — only appear when amplification is high and the table is large.

The third case is when you need *historical* correctness rather than current state. If the requirement is "what did the ledger look like on 30 June", you want a snapshot or an immutable history table, not a CDC destination. A CDC table gives you the current state; the log gives you the history, and usually in a different system.

The honest recommendation, which I give whenever anyone asks whether they need CDC: compute the amplification first. Below 2x, use a scheduled extract and spend the engineering time on the transforms that actually matter.

### 5. What is event amplification and how do you use it to decide?

**Event amplification = (number of change events) ÷ (number of rows in the table).** It measures how much a row churns, and it is the single number that decides whether CDC is worth it.

| Amplification | Table shape | Recommendation |
|---|---|---|
| ~1.0x | Append-only | Poll. CDC buys nothing. |
| 1.1–2x | Mostly append | CDC is defensible if latency matters |
| 5–20x | High churn | **CDC wins.** Polling re-reads and re-writes constantly. |
| 100x+ | A log table in disguise | Consider whether you want a table at all |

The mechanism behind it: consider a 10-million-row table where 1% changes per hour. Polling reads 10 million rows to find 100,000 changes, unless it has a reliable `updated_at` index — and even then it is a random-access probe across 10 million rows. CDC reads 100,000 events from a sequential log and merges them. That is the difference between a job that scales with the table and one that scales with the changes.

Compute it for your workload before you commit: instrument the source for a day, count the writes per table, and divide by the row count.

### 6. What is the read consistency window, and how do you choose it?

**The read consistency window is how long Datastream waits after a transaction commits before reading its changes, to guarantee it reads them in commit order.**

When transaction A commits at t=0 and transaction B commits at t=0.1, a reader with no window might read B's changes first and apply them before A's. The merge then converges on the wrong state. The window makes Datastream wait long enough that the ordering is guaranteed.

The trade-off is direct: **the window is your latency floor**. A 5-second window means a 5-second floor, plus the merge time. 1 second is usually fine for a single-writer database; 5 seconds is the standard choice because it has enormous headroom over normal write gaps; 10 seconds is for heavy concurrent write loads.

The window must exceed the worst-case gap between two commits that could be read out of order. Under normal load that gap is milliseconds, so 5 seconds is very safe. Under a write burst it can be closer.

The mistake to avoid: measuring latency during a quiet period and putting that number in the SLA. You will measure something like 300 milliseconds, quote sub-second replication, and then have a write burst push every event past the window and your latency to 5.3 seconds. **Set the SLA from the window, not from a measurement.**

### 7. Why does Datastream not delete rows that I removed from the source table?

It does — but it deletes them because the log contains an explicit delete event, not because it noticed the row was missing.

The mechanism: a streaming merge has three clauses — insert when the key is new, update when matched, delete when matched and the change is marked as a delete. There is no fourth clause, `WHEN NOT MATCHED BY SOURCE THEN DELETE`, and the reason is conceptual rather than a product limitation.

**In a stream there is no "the source" as a whole.** The stream contains changes. The absence of a change is not evidence of a deletion — a row that has not changed in an hour has simply not changed. A merge that deleted every unmatched row would empty the table continuously.

That fourth clause belongs to a **synchronised merge**, where the source is a finite, complete snapshot. There, "not in the snapshot" genuinely means "deleted". Datastream offers that as a backfill mode, and it is the right operator for a one-off sync.

The production symptom of getting this backwards: a team built their own CDC consumer and included `NOT MATCHED BY SOURCE`, reasoning that the destination should mirror the source. Their table emptied itself every time the stream went quiet for a few minutes, and refilled when the next batch of changes arrived. The fix was to remove the clause and rely on explicit delete events.

## The log

### 8. Why does CDC read the binary log instead of the tables?

Four reasons, and only the first is about performance.

**Performance.** The binary log is sequential. Reading tables is random access — an index probe, then a row fetch — against the hot data, and it competes with the application for buffer cache and I/O.

**Deletes.** The log contains delete events. A table read cannot see them.

**Transaction boundaries.** The log records the commit as a unit, so the reader sees whole transactions. A table read can catch one half-applied.

**Replayability.** The log is a durable history. A table read gives you only the current state. If the destination is corrupted, the log is what you rebuild from.

The load argument is the one people remember, and it is the least important. Even a small table with heavy churn is better served by CDC, because of the delete and transaction arguments.

### 9. What is the difference between `binlog_format=ROW` and `STATEMENT`, and why does CDC need ROW?

`STATEMENT` records the **SQL statement** that was executed. `ROW` records the **row images** — what each row looked like before and after.

CDC requires `ROW`, and it is not a preference. A statement-based log for a 500-row `INSERT` records one statement. To reconstruct what each row became, the reader must interpret the statement against the table's current state — which is not possible reliably, because the table may have changed since. Statement-based replication also has ambiguity: `UPDATE t SET x = x + 1` under `ROW` logs each row's old and new value; under `STATEMENT` it logs the expression, and the reader must evaluate it.

`MIXED` uses statement format except for unsafe statements, and should be avoided for CDC because you then have two event shapes to handle.

The Postgres equivalent is `wal_level`, which defaults to `replica` and **must** be changed to `logical`. Physical replication ships WAL files for a standby; logical replication ships the row changes. CDC needs the logical one.

### 10. What is `binlog_row_image`, and what breaks if you set it to `MINIMAL`?

`binlog_row_image` controls how much of each row is written to the binary log.

| Setting | Logged | Consequence |
|---|---|---|
| `FULL` | Every column, before and after | Complete images. Backfills and audits work. |
| `MINIMAL` | Only changed columns and the key | Smaller and faster, but **before images are incomplete** |
| `NOBLOB` | All except large blobs | A middle ground |

`MINIMAL` breaks two things. A `before` image that contains only the key means you cannot tell what the row used to contain — so you cannot reconstruct history, and a delete event cannot say what was deleted. It also means a `before` image and an `after` image have *different schemas*, which every consumer has to handle.

Use `FULL`. The volume argument for `MINIMAL` is real on wide tables, and the correctness argument is stronger. A CDC pipeline whose before images are incomplete is not an audit trail, and cannot be used to rebuild a table from scratch.

### 11. What does the replication user need, and why is it a security concern?

For MySQL: `SELECT`, `REPLICATION SLAVE`, and `REPLICATION CLIENT`. For Postgres: `REPLICATION` plus `pg_read_all_data` or table-level `SELECT` grants, and `USAGE` on the schema.

`REPLICATION SLAVE` (MySQL) or `REPLICATION` (Postgres) is what lets the reader read the binary log. `SELECT` is what lets it read the tables during a backfill. `REPLICATION CLIENT` lets it query the server's replication metadata.

The security concern is real and worth raising unprompted: **the replication user can read the entire binary log**, which contains every change to every table — including the contents of rows in tables you were not asked to capture. A password column that was changed is in the log in plaintext. A replication credential is therefore more sensitive than a normal application credential, and it belongs in Secret Manager with a rotation schedule, not in a Terraform variable or a YAML file.

Scope it as narrowly as the connector allows. On Postgres, `pg_read_all_data` can be replaced with per-table `SELECT` grants. On MySQL, `ON *.*` is the documented form, but a dedicated host and a restricted network path compensate.

### 12. How does the network path from Datastream to the source database work?

Through a **VPC peering** established by a Datastream network config, with a static IP allocated from a reserved range.

```text
  Datastream ──VPC peering──> your VPC ──> your database
       │
       └─ static IP from a reserved range, e.g. 10.0.0.2/28
```

Two steps: reserve a range (via Private Service Connect), then create the network config that references the peering and the IP allocation.

The database's firewall must allow the **IP allocation's** address, and that address is not the same as the Datastream service's outbound IP. This is the most common first-run failure: the connection profile has the right hostname and port, but the source's firewall has not been opened to the allocated IP, so the connection times out.

The diagnostic distinction worth memorising: a **timeout** is almost always a firewall or routing problem; a **connection refused** is a wrong host, a wrong port, or nothing listening. That one distinction splits the search space in half.

## Correctness

### 13. What is idempotency, and why does it matter so much here?

**Idempotency means applying the same event twice has the same effect as applying it once.** It is not a feature you configure in Datastream — it falls out of the merge's shape, because every clause is an upsert or a delete *by key*. There is no clause that appends.

It matters because four things happen routinely in a distributed system:

- **Retries.** A failed delivery is redelivered.
- **Replays.** You rebuild the table from the log.
- **Restarts.** The transport restarts mid-stream.
- **Multi-consumer.** Two consumers write to the same table.

Each of those is a corruption event without idempotency. The classic symptom is a customer table where every customer appears twice, and nobody can say when it started — because it started the first time a consumer retried.

The failure story: a pipeline's Kafka consumer wrote to BigQuery with `WriteDisposition.WRITE_APPEND` and no merge key. The first consumer restart duplicated 2% of the rows. Because the consumer partitioned by `customer_id` but the write was an append, the destination became a growing multiset. The fix was to switch to a keyed merge, and to make the sink idempotent by key rather than by arrival.

### 14. What is the difference between a streaming merge and a synchronised merge, and when would you use each?

A **streaming merge** applies an unbounded stream of changes. Three clauses: insert when the key is new, update when matched, delete when matched-and-deleted. It never infers deletions from absence.

A **synchronised merge** reconciles the target against a finite, complete snapshot. It adds `WHEN NOT MATCHED BY SOURCE THEN DELETE` — the rows in the target that are not in the snapshot are removed.

| | Streaming merge | Synchronised merge |
|---|---|---|
| Source | Unbounded stream of changes | Finite, complete snapshot |
| Infers deletes from absence | Never | Yes |
| Use | Live replication | Backfill, one-off sync |
| Datastream | The default | The backfill mode |

The distinction is conceptual, and it is worth being able to explain it in one sentence: **in a stream, the absence of a change is not evidence of a deletion**, because a row that has not changed in an hour has simply not changed.

Use the synchronised merge when you are doing a backfill into an empty table, or a periodic full reconciliation. Use the streaming merge for everything else. The mistake is reaching for the synchronised merge on a stream, which empties the table every time the stream goes quiet.
