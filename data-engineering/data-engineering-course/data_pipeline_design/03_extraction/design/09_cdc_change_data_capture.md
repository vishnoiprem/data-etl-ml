# 09 — CDC (Change Data Capture)

> **Lesson 9 of 30 — Extraction**

The gold standard for extraction. CDC reads the database's
transaction log and emits INSERT/UPDATE/DELETE events in
real-time. It's complete, low-latency, and doesn't burden the
source. This lesson is *the* deep dive on CDC.

---

## 1. What CDC is

A typical OLTP database (Postgres, MySQL, Oracle) writes every
change to a transaction log before committing it. The log is the
source of truth for replication and recovery. CDC reads that log
and emits a stream of change events:

```
Postgres WAL → Debezium → Kafka topic "cdc.users"
                                  ↓
                                { "op": "c", "after": {"id": 1, ...} }
                                { "op": "u", "before": {...}, "after": {...} }
                                { "op": "d", "before": {...} }
```

The "op" field is one of:

- `c` (create / insert)
- `u` (update)
- `d` (delete)
- `r` (read / snapshot — initial load)

The downstream consumer receives every change, in order, with
before and after images. From there, the consumer can apply the
changes to its own store (the destination warehouse, a search
index, a cache, etc.).

---

## 2. Why CDC wins

Compared to polling (`SELECT * FROM users WHERE updated_at > ?`):

| Property | CDC | Polling |
|---|---|---|
| Latency | Sub-second | Polling interval (minutes to hours) |
| Completeness | Every change, including deletes | Only `updated_at`-tagged changes; deletes invisible |
| Source load | Read from log, no impact on DB | Repeated `SELECT` scans |
| Schema info | Full before/after images, schema | Whatever the SELECT returns |
| Ordering | Per-row, in commit order | Per-query, no commit ordering |

The only thing CDC loses to polling: it requires the source to
expose a transaction log. Postgres, MySQL, MongoDB, Cassandra all
do. Old Oracle, some SaaS APIs don't.

---

## 3. The Debezium architecture

Debezium is the open-source default for CDC. It runs as a
connector inside a Kafka Connect cluster:

```
                  ┌──────────────────────────┐
Postgres WAL ──►  │ Debezium Postgres source │  ──► Kafka topic
                  └──────────────────────────┘

                  ┌──────────────────────────┐
MySQL binlog ──►  │ Debezium MySQL source    │  ──► Kafka topic
                  └──────────────────────────┘

                  ┌──────────────────────────┐
MongoDB oplog ──► │ Debezium MongoDB source  │  ──► Kafka topic
                  └──────────────────────────┘
```

The Debezium source runs *inside* the database (it registers as a
replication slot in Postgres, for example). It streams every
change to Kafka. Downstream consumers read from Kafka with
exactly-once semantics.

---

## 4. The snapshot + streaming pattern

The first time a CDC connector starts, it doesn't have a "last
position" in the log. It needs to capture the *current state* of
the table before it can start streaming new changes. The pattern:

```
Phase 1 (snapshot): Read the full table, emit one "r" event per row.
Phase 2 (streaming): Read the transaction log from the snapshot's
                     start LSN, emit "c", "u", "d" events.
```

The two phases are atomic: the connector records the LSN (log
sequence number) where the snapshot started, so the streaming
phase doesn't miss any changes that happened *during* the snapshot.

This is exactly the pattern the `CDCPipeline` class in
`code/cdc.py` implements:

```python
from data_pipeline_design.03_extraction.code.cdc import CDCPipeline

pipeline = CDCPipeline(sink)
pipeline.run_once(current_state)  # snapshot + diff + emit events
```

---

## 5. The change event schema

A standard CDC event (Debezium-style):

```json
{
  "op": "u",
  "ts_ms": 1700000000000,
  "before": {"id": 1, "name": "Alice", "status": "active"},
  "after":  {"id": 1, "name": "Alice", "status": "inactive"},
  "source": {
    "table": "users",
    "lsn": 12345678
  }
}
```

The downstream consumer:

- For `c`: insert the `after` row.
- For `u`: replace the `before` row with the `after` row.
- For `d`: delete the `before` row.
- For `r`: insert the `after` row (snapshot row).

The events are *immutable* and *ordered per row*. The consumer
applies them in order, per primary key, and the destination is
always a faithful copy of the source at the latest consumed LSN.

---

## 6. The ordering problem

CDC events are ordered *within a row* (by commit time) but not
across rows. Two updates to the same row will arrive in the order
they committed. Two updates to different rows can arrive in any
order.

The senior move: **partition by primary key**. The consumer must
process events for a single primary key in order. Across keys,
ordering doesn't matter.

```python
# The partition-by-pk pattern
consumer.subscribe("cdc.users", partition_fn=lambda e: e["after"]["id"])
```

In Kafka, this is `KafkaProducer.send(key=pk)` and
`KafkaConsumer.poll(partition=...)`. The consumer group
rebalances when partitions move.

---

## 7. The initial-load gotcha

The first time you turn on CDC, you have to do a *full snapshot*
of every table. For a 1 TB table, this can take hours. During
those hours, the source is being written to. Debezium handles this
by:

1. Acquiring a lock on the table (Postgres `ACCESS SHARE`).
2. Reading the full table.
3. Recording the LSN.
4. Releasing the lock.
5. Starting the stream phase from that LSN.

The window between (1) and (4) is small. The window between (4)
and the consumer catching up can be large. The senior move: size
your consumer fleet to catch up in a reasonable time, or accept
the lag.

---

## 8. The failure modes

| Failure | Mitigation |
|---|---|
| Source DB down | Debezium retries; events queue in the WAL. |
| Kafka down | Debezium buffers; events wait until Kafka is back. |
| Consumer crashes | On restart, resume from last committed offset. |
| Schema change | Debezium emits a schema change event; downstream must handle. |
| Disk fills up | WAL disk full → source DB stops accepting writes. Page on disk usage. |

The senior move: name the disk-fills-up failure mode. "If the WAL
disk fills up, Postgres stops accepting writes. So the failure
propagates back to the source. This is why the CDC connector must
have its own alerting on lag."

---

## 9. CDC vs ELT in 2026

The 2026 consensus:

- **CDC is the default for OLTP sources.** It's lower-latency, more
  complete, and cheaper than polling.
- **Polling is the fallback** when CDC isn't available (old Oracle,
  SaaS APIs without webhooks).
- **The CDC stream lands in a Kafka topic or directly in a Delta
  Lake bronze table.** No intermediate warehouse.
- **dbt or Spark applies the events** to build silver and gold
  tables. The bronze table is the source of truth.

The senior framing: "I'd use Debezium for the CDC stream from
Postgres into Kafka, then either stream-process into the warehouse
or batch the Kafka topic into a Delta Lake bronze table."

---

## Try it

Sketch the CDC pipeline for a system you've worked on. What's the
source? What's the log format? What's the consumer? Where does the
gold table live? If you can't sketch it, that's the lesson to
study next.
