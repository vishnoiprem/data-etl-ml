# Datastream & CDC Glossary

> Every term used in this course, defined.

---

## A

**At-least-once delivery** — A transport guarantee that every message is
delivered one *or more* times. Kafka's guarantee. The same message can
arrive twice, so the destination must be idempotent.

**Auditability** — The property that the change log is a complete history,
so you can answer "what did this row look like at 3pm?".

---

## B

**Backfill** — Copying the *existing contents* of the source table into the
destination before the stream starts delivering changes. Datastream's modes:
`backfill-all`, `backfill-none`, `backfill-config`.

**Backlog** — The total amount of unprocessed change sitting between the
source's current position and the stream's position. Also called **lag**.

**Before image** — The row's contents *before* a change. Null for INSERT.
It is what tells a DELETE which row to remove, and it is what makes CDC
auditable.

**After image** — The row's contents *after* a change. Null for DELETE. It
is what makes an INSERT and an UPDATE produce a row.

**Binary log (binlog)** — MySQL's write-ahead log of row changes. The
source of truth for CDC on MySQL.

**BigQuery `MERGE`** — The DML statement that implements a keyed merge:
`WHEN NOT MATCHED BY TARGET THEN INSERT`, `WHEN MATCHED ... THEN UPDATE`,
`WHEN MATCHED AND __op__ = 'DELETE' THEN DELETE`.

**Backfill mode** — See *Backfill*.

---

## C

**CDC (Change Data Capture)** — Reading a database's write-ahead log and
applying the changes it contains to a destination table.

**Change event** — One entry in the log: the operation, the before image,
the after image, and two timestamps.

**Clustering (BigQuery)** — `CLUSTER BY col` physically sorts a table by
that column, letting BigQuery skip sorts and prune blocks. On a CDC
destination, cluster on the **merge key**.

**Commit order** — The order in which the source database committed
transactions. Datastream preserves it within a single source.

**Consumer group** — A set of Kafka consumers that share a topic's
partitions, where each partition is assigned to exactly one consumer in the
group.

**Confluent Cloud** — The managed Kafka platform. Billed on **bytes stored
and bytes transferred**, not on message count.

---

## D

**Datastream** — Google's managed change data capture service. Reads a
source database's log, preserves commit order, and applies the changes to a
BigQuery destination with a keyed merge.

**Dead-letter queue (DLQ)** — A topic where records are routed after the
sink connector exhausts its retries. Without one, poison messages are
dropped silently.

**Delete-of-absent-row** — A DELETE event for a key that is not in the
destination. A **no-op**, not an error.

**Duplicate insert** — An INSERT event for a key that already exists. The
merge converges — the row is unchanged.

---

## E

**Event amplification** — (Number of change events) ÷ (number of rows in
the table). The single metric that decides whether CDC is worth it. At
~1.0× the table is append-only and a scheduled poll is better.

**Exactly-once (misnomer)** — A term that usually means "exactly-once
*processing*", not exactly-once delivery. A keyed merge is idempotent, which
is what makes redelivery safe — but the transport can still deliver the
same event twice.

---

## F

**Failover** — The source database's primary changes. The new primary has a
different log position, so the stream must re-establish its position; this
can involve a re-backfill if the position is unrecoverable.

**Fan-out** — Publishing one change stream to many independent consumers.
The main reason to choose Kafka over a single Datastream destination.

---

## G

**GCF sink connector** — The Confluent-managed connector that polls a Kafka
topic and POSTs each message to a Cloud Run / Cloud Functions HTTP
endpoint. It holds the offsets.

**Graceful degradation** — A sink that keeps working when part of its
input is unusable, by routing the bad records elsewhere rather than
failing.

---

## H

**Heartbeat / slot activity** — Postgres replication slot liveness. An
inactive slot holds WAL on disk indefinitely and will eventually fill the
disk.

**Idempotency** — Applying the same event twice has the same effect as
applying it once. It falls out of the merge's shape: every clause is an
upsert or a delete by key, and none appends.

---

## J

**Job** — In BigQuery, a DML or query operation. A CDC merge generates many
jobs, and the per-table concurrent-DML quota is the limit that a
high-throughput stream hits.

---

## K

**Key** — The value a producer hashes to choose a partition. For a CDC
stream fanned out through Kafka, **the partition key must equal the merge
key**.

**Kafka** — A distributed, partitioned, append-only log. The natural
transport for publishing a change stream to many consumers.

**Kafka Connect** — The framework that runs connectors, including the
Confluent GCF sink connector.

---

## L

**Lag** — The total amount of unprocessed change between the source's
current position and the stream's position. Different from *latency*.

**Latency** — The delay for a single event — the time from the source's
commit to the merge completing.

**Log position** — The point in the binary log a reader has reached. A
stream can resume from a log position; it cannot resume from one that no
longer exists.

---

## M

**Merge key** — The column (or columns) used to match a change event to a
row in the destination. Must be **unique**, **immutable**, and **minimal**.
The rule of thumb: the source table's primary key, and nothing else.

**Merge** — The keyed upsert-and-delete that applies change events to a
destination table. Every clause is an upsert or a delete by key.

**Min-instances** — The number of Cloud Run instances kept warm so a cold
start does not land on a real request. A deliberate trade of money for
latency.

**MySQL `binlog_format`** — `ROW`, `STATEMENT`, or `MIXED`. CDC requires
`ROW`.

**MySQL `binlog_row_image`** — `FULL`, `MINIMAL`, or `NOBLOB`. CDC requires
`FULL`, because `MINIMAL` produces incomplete before-images.

---

## N

**Non-unique merge key** — The most dangerous configuration error. One
update matches several rows and overwrites all of them, and nothing errors.
The row count stays plausible.

---

## O

**Offset** — A position in a Kafka partition. The connector holds the
offset, not your function. If the function's response is lost, the offset
does not advance and the record is redelivered.

**Ordering key** — The Pub/Sub / Kafka equivalent of the merge key for
ordering purposes.

---

## P

**Partition (BigQuery)** — A time-bounded slice of a table, usually by
ingestion date (`_PARTITIONTIME`). Makes expiration cheap and keeps merges
from touching the whole history.

**Partition (Kafka)** — An ordered append-only sequence within a topic. The
unit of parallelism and the scope of the ordering guarantee.

**Partitioning key** — The value used to select a Kafka partition. **Must
equal the merge key** for a CDC fan-out.

**Poison message** — A record that will always fail — malformed, missing a
required field, violating a constraint. Must return a 4xx and be routed to
a DLQ.

**Postgres WAL** — Postgres's write-ahead log. `wal_level = logical` is
required for CDC.

**Primary key** — The merge key, in almost every case.

**Pub/Sub** — Google's messaging service. Not used as the CDC transport in
this course, but the at-least-once delivery semantics are the same.

---

## R

**Read consistency window** — How long Datastream waits after a transaction
commits before reading its changes, to guarantee commit-order delivery. It
is your latency floor. 5 seconds is the standard choice.

**Replication slot** — A Postgres object that prevents the WAL from being
truncated past a disconnected reader. Prevents data loss; holds WAL on disk
indefinitely if unmonitored.

**Replication user** — The database account Datastream uses. It can read
the entire binary log — a security concern worth raising.

**Retry** — The transport delivering the same event again. Safe only
because the destination is idempotent.

---

## S

**Secret Manager** — GCP's secret store. The database password lives here,
fetched at runtime and cached in memory — never in the source, the
environment variables, or the image.

**Schema evolution** — How a pipeline handles a source schema change. Three
responses: widen, version into a new column, or migrate to a new table.

**Sink** — The layer that applies change events to the destination. Holds
the semantic contract.

**Slot** — See *Replication slot*.

**Source config** — The Datastream object describing the source database:
host, port, credentials, and the tables to include.

**Synchronised merge** — A merge against a finite, complete snapshot. Adds
`WHEN NOT MATCHED BY SOURCE THEN DELETE`. The backfill mode.

**Streaming merge** — A merge against an unbounded stream of changes. Never
infers deletes from absence. The default.

---

## T

**Tombstone table** — A table of deleted rows maintained by a polling
pipeline so it can detect deletions. A CDC implementation you wrote badly.

**Transport** — The layer that reads the log and delivers change events:
Datastream, Debezium, Fivetran, Kafka Connect.

**Truncate (the log)** — The binary log being deleted or expired past the
reader's position. The stream cannot resume; a full re-backfill is needed.

---

## U

**Upsert** — An insert-or-update. What every non-delete clause of a keyed
merge does.

---

## V

**VPC peering** — The network path from Datastream to a source database,
established through a Datastream network config with a static IP from a
reserved range. The database's firewall must allow the **allocation's**
address.

---

## W

**WAL** — Write-ahead log. Postgres's `wal_level` must be `logical` for CDC.

**Write-ahead log** — The durable, ordered record of committed
transactions. The thing CDC reads.

---

## `__op__`

**`__op__`** — Datastream's synthetic column recording which operation each
change event represents (`INSERT`, `UPDATE`, `DELETE`). It is what lets one
`MERGE` handle all three. It is not a column in your source table.

---

## Related material

- The one-page reference — [CHEATSHEET.md](CHEATSHEET.md)
- The course README — [../README.md](../README.md)
