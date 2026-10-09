# 07 — Distributed Message Queue (Kafka-like)

> **Lesson 7 of the System Design course — Event-Driven Systems**

A working design + implementation of a Kafka-style distributed message
queue: topics split into partitions, producers append to a partition
log, consumers in a *group* read with tracked offsets, at-least-once
delivery, persistent per-partition log backed by a `KeyValueStore`.

This is the first lesson in the **Event-Driven Systems** track — the
patterns here (partitioning, offsets, consumer groups, idempotent
producers) show up everywhere downstream: webhooks (lesson 8),
marketplace order state machines (lesson 9), and beyond.

---

## 1. Requirements

### Functional
- **Topics** — create, list, delete. A topic has a fixed number of
  partitions.
- **Produce** — append a record `{key, value, headers}` to a topic.
  Records with the same `key` go to the same partition (sticky
  hashing), so consumers can rely on per-key ordering.
- **Consume** — pull a batch of records from a topic, advancing a
  *per-group* offset. The same record may be returned to a different
  group, but never twice to the same group (after commit).
- **Consumer groups** — register a group, attach it to a topic, track
  its committed offset per partition. Manual `commit` advances the
  cursor; auto-commit on consume is the default.
- **At-least-once semantics** — a record is only acked after the
  partition log is durably written. A consumer that crashes before
  committing re-reads the same records on restart.
- **Offset reset** — `earliest` (start from the beginning) or `latest`
  (start from the new head) on a new group.

### Non-functional
- **Durability** — the partition log is persisted to the
  `KeyValueStore` JSON file on disk. A broker restart replays the
  log and resumes exactly where it left off.
- **Partitioning** — concurrency comes from partitions. A topic with
  `N` partitions can be read by up to `N` consumers in the same
  group; more consumers than partitions sit idle.
- **High write throughput** — append-only writes, no in-place edits.
  Reads do not block writes; writes do not block reads.
- **Observability** — per-topic produce / consume counters and
  end-to-end latency histograms surfaced at `/metrics`.

### Out of scope (for this lesson)
- Replication / ISR (in a real Kafka, each partition has 3 replicas
  and a leader-follower protocol — we model a single broker).
- Compaction (we keep an append-only log; no segment roll-off or
  tombstones).
- Exactly-once semantics (we promise at-least-once; the consumer
  must be idempotent).
- Authentication / authorization / quotas.

---

## 2. Capacity estimation

| Metric | Value |
|---|---|
| Topics | ~10 K |
| Partitions per topic | 12 (typical) — capped at 256 |
| Producers | ~1 K concurrent per topic |
| Consumers | 1–N per group, ≤ partitions |
| Record size | ~1 KB avg, 1 MB max |
| Write rate | ~100 K records/sec/broker (in-memory KV bottleneck) |
| Retention | until compacted (out of scope); default unlimited |
| Storage | bytes_on_disk = records × avg_size; per-partition append log |

The lesson: this design is throughput-bound by the in-memory
KV; the real bottleneck in a production broker is the page cache +
sequential disk I/O pattern. We model the in-memory log here so the
API surface is correct; swapping for a real disk-backed log is a
mechanical change.

---

## 3. High-level design

```
                 ┌──────────────────────────────────────────────┐
   producer ────►│                BROKER                        │
                 │                                               │
                 │   ┌─────────────┐ ┌─────────────┐            │
                 │   │ topic "X"   │ │ topic "Y"   │            │
                 │   │             │ │             │            │
                 │   │ P0  P1  P2  │ │ P0  P1  P2  │            │
                 │   │ │   │   │  │ │ │   │   │  │             │
                 │   │ ▼   ▼   ▼  │ │ ▼   ▼   ▼  │             │
                 │   │ log log log│ │ log log log│  ◄── append  │
                 │   └─────┬──────┘ └─────┬──────┘    only     │
                 │         │              │                    │
                 │         ▼              ▼                    │
                 │   ┌─────────────────────────────────────┐    │
                 │   │  KeyValueStore (JSON-persisted log) │    │
                 │   └─────────────────────────────────────┘    │
                 │                                              │
                 │  ┌───────────────┐  ┌───────────────┐        │
                 │  │  group "A"    │  │  group "B"    │        │
                 │  │  offsets:     │  │  offsets:     │        │
                 │  │  P0=42 P1=87  │  │  P0=10 P1=10  │        │
                 │  └───────────────┘  └───────────────┘        │
                 │                                              │
                 └──────────────────────────────────────────────┘
                          ▲                 ▲
                          │                 │
                       consumer          consumer
                       (group A)         (group B)
```

- **Broker**: the process that owns the topics and partition logs.
  Here, one process; in production, a cluster of brokers with the
  same replication factor.
- **Topic**: a named stream of records. Split into partitions for
  parallelism.
- **Partition**: an ordered, append-only log. The unit of
  distribution — each partition lives on one broker (here, this
  process). Records within a partition are totally ordered.
- **Producer**: chooses a partition by hashing the record key
  (sticky / consistent hashing) and appends. Optional acks=1 (broker
  only) or acks=all (would imply replicas — not modeled).
- **Consumer group**: a set of consumers that *cooperatively* read a
  topic. Each partition is read by exactly one consumer in the
  group. The group tracks a committed offset per partition.
- **Offset**: the 0-based record index within a partition. A
  consumer's "position" is its next-to-read offset; "commit" stores
  it durably.

---

## 4. API

| Method | Path | Body / Query | Returns |
|---|---|---|---|
| `POST` | `/api/topics` | `{"name": "...", "partitions": N}` | `{"name", "partitions", "created_at"}` |
| `GET`  | `/api/topics` | — | list of topics |
| `GET`  | `/api/topics/<name>` | — | topic metadata |
| `DELETE`| `/api/topics/<name>` | — | `{"ok": true}` |
| `POST` | `/api/topics/<name>/produce` | `{"key": "...", "value": "..."}` | `{"message_id", "partition", "offset"}` |
| `GET`  | `/api/topics/<name>/consume?group=&max=&reset=` | query | `{"records": [{message_id, partition, offset, key, value, ts}], "next_offset"}` |
| `POST` | `/api/groups` | `{"group": "..."}` | `{"group", "created_at"}` |
| `GET`  | `/api/groups` | — | list of groups |
| `GET`  | `/api/groups/<name>/offsets?topic=` | query | per-partition committed offsets |
| `POST` | `/api/groups/<name>/commit` | `{"topic": "...", "partition": 0, "offset": N}` | `{"committed": N}` |
| `GET`  | `/metrics` | — | counters + histograms |
| `GET`  | `/health` | — | `{"ok": true}` |
| `GET`  | `/` | — | service index |

Notes:
- `consume` auto-commits by default. Pass `?commit=false` to read
  without advancing the offset.
- `reset=earliest` or `reset=latest` is honored the *first* time a
  group attaches to a topic; subsequent calls resume from the
  committed offset.
- A single `consume` call returns records from *one* partition
  (round-robin across the group's assigned partitions); this keeps
  the response shape simple and matches a "fetch one batch per
  partition" Kafka client. Use repeated calls to drain.

---

## 5. Data model

### Record
```
record = {
  "message_id":  <snowflake int>,   # globally unique, time-sortable
  "key":         <str|None>,
  "value":       <str>,             # opaque payload (we don't decode)
  "headers":     <dict|None>,       # optional metadata
  "partition":   <int>,             # 0..N-1, decided by producer hash
  "offset":      <int>,             # position within the partition log
  "ts":          <float>,           # wall-clock at produce
}
```

### Partition log
```
log:<topic>:<partition> = [
  record, record, record, ...      # append-only list
]
```

The log lives in a single `KeyValueStore` value as a list. New
records are appended via `store.set(...)` with the full list. A real
broker uses segment files and an index; the list-of-records is the
conceptual equivalent for our scale.

### Topic
```
topic:<name> = {
  "name": str,
  "partitions": int,                # fixed at create time
  "created_at": float,
}
```

### Consumer group
```
group:<name> = {
  "name": str,
  "created_at": float,
  "offsets": {                       # persisted per (topic, partition)
    "<topic>:<partition>": int,
    ...
  },
  "reset": "earliest" | "latest",    # policy on first read of a new key
}
```

The same offset key (`<topic>:<partition>`) may be reused by
different groups — they each have their own `group:<name>` record.

### Hashing
Records with the same `key` go to the same partition:
```
partition = hash(key) % num_partitions
```
For `key=None`, we round-robin by append count (each partition
keeps roughly equal share of the no-key stream).

---

## 6. Write path: produce

`POST /api/topics/<name>/produce`:

```
1. Producer sends {key, value, headers}.
2. Broker hashes the key to pick a partition (round-robin if key=None).
3. Broker reads the current partition log from the KV store.
4. Broker assigns offset = len(log).
5. Broker appends a new record (message_id from Snowflake, ts=now).
6. Broker writes the updated log back to the KV store.
7. Broker returns {message_id, partition, offset}.
```

The whole operation is wrapped in a `KeyValueStore` write, so it's
atomic from the consumer's point of view. A real broker would
fsync before acking; here we rely on the JSON `os.replace` atomic
write, which gives us crash-consistent append-only semantics for
*whole* writes (a half-written log line is impossible to read back).

---

## 7. Read path: consume

`GET /api/topics/<name>/consume?group=g&max=10&reset=earliest`:

```
1. Group "g" is registered (POST /api/groups) or known.
2. For each partition in the topic, compute next_offset:
     if (topic:partition) in group.offsets:
         offset = group.offsets[(topic:partition)]
     else:
         offset = 0 if reset=="earliest" else log_len
         # record the resolved offset so subsequent reads advance from here
3. Round-robin to one partition per call (single-partition fetch).
4. Read records[next_offset : next_offset + max] from the log.
5. If commit=true (default), update group.offsets[(topic:partition)].
6. Return the records + the next offset.
```

Why single-partition fetch per call? Because the consumer is
expected to *batch-process* — fetch, do work, commit, fetch again.
Multiple partitions in one response force the client to track
per-partition positions, which is the Kafka client's job, not the
broker's.

---

## 8. Failure modes

| Failure | What happens | Mitigation |
|---|---|---|
| **Broker crash between append and ack** | Producer retry on idempotent message_id dedup; consumer sees no record (it wasn't persisted) or sees it on next fetch (it was). | At-least-once promise; consumers must be idempotent. |
| **Consumer crash before commit** | On restart, the group resumes from the *last committed* offset. Records between commit and crash are re-delivered. | This is the at-least-once contract — the consumer must dedup by `message_id`. |
| **Commit succeeds, processing fails** | Record is never re-delivered; gap in the offset. | Standard at-least-once: the *next* read advances past it. |
| **Topic deleted while consumers attached** | Subsequent `consume` returns 404. Consumers should re-resolve. | Documented; treat as a hard error. |
| **More consumers in a group than partitions** | Extra consumers get no records (no partition assigned). | Standard Kafka semantics; raise a warning, not an error. |
| **Log grows unbounded** | Memory + disk usage climbs. | Out-of-scope compaction; in production, segment roll + retention policy. |
| **Hot partition** (one key dominates) | All writes for that key land on one partition. The other partitions sit idle. | Hashing is unavoidable; solutions are application-side (split a hot key) or broker-side (virtual partitions). |

---

## 9. Tradeoffs

### Hash partitioning vs round-robin
- **Hash** (default, when `key` is set): guarantees per-key ordering,
  so a consumer can do stateful processing of a single key's stream
  without locking. The downside is *hot keys* — one very busy key
  saturates one partition.
- **Round-robin** (default, when `key` is None): maximizes write
  throughput, but consumers see a mix of keys per batch, so any
  per-key state must be kept in an external store.

We pick hash-with-round-robin-fallback. Producers should always set
`key` unless they really want maximum throughput and don't care
about ordering.

### Auto-commit vs manual commit
- **Auto-commit on consume** (default): simplest, but a consumer
  crash between fetch and process loses records.
- **Manual commit after process**: more code, but the consumer
  controls exactly when a record is "done".

We default to auto-commit (simple) and expose `?commit=false` for
manual control. A real Kafka client commits in a separate thread.

### Single broker vs replicated
- A single broker is a SPOF. A 3-replica setup needs a consensus
  protocol (ISR + leader election) and costs ~3x the storage.
- We pick single broker for the lesson; the code is structured so
  swapping in a `ReplicatedLog` (one log per replica + quorum
  writes) is a contained change.

### Append-only list vs segmented log
- **List-in-KV** (here): trivially correct, but every append
  rewrites the whole list — O(N) per write. Fine for the lesson.
- **Segmented log** (real Kafka): append to the active segment,
  roll when full, index by offset, drop old segments. O(1) append,
  O(1) lookup by offset.

### At-least-once vs exactly-once
- At-least-once: simpler, faster, but consumers must dedup. Standard
  in nearly every real pipeline.
- Exactly-once: requires idempotent producers + transactional
  writes. Doubles the engineering cost.

We pick at-least-once, document the requirement, and use Snowflake
`message_id` so dedup is straightforward.

---

## 10. Code map

```
07_message_queue/
├── design/README.md            # this file
├── code/
│   ├── __init__.py
│   ├── service.py              # MessageQueueService (pure logic)
│   └── app.py                  # Flask wrapper
└── tests/
    ├── __init__.py
    ├── test_service.py         # ≥6 unit tests
    └── test_app.py             # ≥4 HTTP tests
```

- `MessageQueueService` owns: topics, partition logs, consumer
  groups, offsets. Pure Python; takes a `KeyValueStore` and a
  `Snowflake` so tests are deterministic and persistence is
  swappable.
- `app.py` is the Flask wrapper. All endpoints are thin: parse,
  delegate, return JSON. Metrics collected at the HTTP layer.
- The service does *not* run a background thread — consume is
  request-driven, which keeps the API fully synchronous and
  testable.
