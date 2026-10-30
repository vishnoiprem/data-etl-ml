# 4.1 — Apache Kafka & the Streaming Model

> **Section 4 · Streaming & Ingestion · Lecture 4.1 · 8:00**

## 🎯 What you will learn

- Batch versus streaming: the real distinction is *when the answer is computed*, not the tool you run
- Latency versus throughput as two independent axes, and why optimising one usually costs the other
- Event time versus processing time, and why every late-arriving row is a correctness bug you must design for
- The Kafka architecture: brokers, topics, partitions, leaders, followers, replication factor, ISR
- Why a partition is the unit of parallelism, ordering, and throughput — all three at once
- The consumer group and the partition-assignment problem, including rebalances and the "one slow consumer" problem
- Offsets and the three commit semantics: at-most-once, at-least-once, exactly-once
- The log-structured storage model, and why retention is a **disk-space** decision, not a data-lifecycle one
- Key-based ordering guarantees and their exact limits
- Schema Registry and Avro: why "just use JSON" fails in production
- Kafka versus Pub/Sub: when Kafka earns its operational cost and when it does not

---

## 🧠 Concept

### The streaming model

The batch/streaming distinction is usually taught as "batch processes all the data, streaming processes data as it arrives". That is a description of the *interface*, not the *semantics*. The semantics that actually matter are two questions:

1. **When is the answer computed?** Batch computes it when the job runs, over a closed, complete input. Streaming computes it as each element arrives, over an input that has no end.
2. **Can the answer change after it is emitted?** In batch, once the job completes, the answer is final — the input is frozen. In streaming, a result emitted at 14:00 can be invalidated at 14:03 by an event that arrives late.

Everything else — "real-time", "micro-batching", "fast" — is marketing around those two questions.

A **micro-batch** (Dataflow calls this a fixed window, Spark Structured Streaming calls it a trigger interval) is a hybrid: the pipeline wakes up every N seconds, processes everything that arrived in that interval, and emits. This is *not* a compromise that is somehow worse at both things. For most real workloads it is the correct choice, because:

- The source system (a Postgres binlog, an API) usually delivers in bursts, not at a smooth rate. A 1-second trigger on a bursty source just adds latency and overhead.
- Checkpointing and exactly-once semantics are dramatically simpler when the unit of work is a batch of records rather than a single record.
- Downstream sinks (BigQuery load jobs, file exports) are naturally batch-shaped. Loading one row at a time into BigQuery is absurd.

The course project's pipeline is exactly this shape. `ingest_events` consumes a set of lines and returns `(accepted, rejected)`. `aggregate_events` reduces the accepted set. `bucket_by_window` groups by event-time hour. The pure functions in `project/core/pipeline_logic.py` are the batch skeleton of a streaming pipeline, and the mapping to Dataflow is one-to-one.

```text
batch:    [read file] → [transform all] → [write all] → DONE
stream:   [read delta] → [transform delta] → [write delta] → never DONE
micro:    [read delta] → [transform delta] → [write delta] → sleep → repeat
```

### Latency versus throughput

These are independent axes and conflating them is the most common design error in streaming architectures.

- **Latency**: how long from "event happened" to "result available".
- **Throughput**: how many events per second the system sustains.

The naive intuition is that these trade off against each other. Sometimes they do. More importantly, in a stream processing engine, **per-event work is what costs you both**. Every event you touch costs CPU, and the more events you touch per unit time, the less wall-clock time you have for each.

The practical consequence: *the cheapest way to reduce streaming cost and latency is to touch fewer events*. Filter at the source. Project columns. Do not join in the streaming layer if you can denormalise upstream. This is why the pipeline design principle — push computation to where the data already is — dominates streaming cost optimisation.

There is a second, subtler latency that engineers routinely forget: **end-to-end latency is the sum of every stage's latency, and the slowest stage sets the floor**. Pub/Sub publish→subscribe is seconds. A Dataflow trigger interval of 60 seconds adds a minute. A BigQuery load job on a 500 GB partition takes minutes. If your SLA is "one minute", the Dataflow trigger interval alone blows it.

```python
# The latency budget, made explicit. Every number here is a real,
# tunable knob — and every one of them adds to the total.
LATENCY_BUDGET = {
    "ingest_poll_interval_s": 5,       # Pub/Sub pull / Kafka fetch.max.wait
    "trigger_interval_s": 60,          # Dataflow / Structured Streaming trigger
    "window_allowance_s": 300,         # how long to wait for late data
    "sink_commit_s": 30,               # BigQuery load job or GCS flush
}
# Total: 395 s ≈ 6.6 minutes, against a target of 300 s.
# The window allowance is the only one that is a semantic choice;
# the rest are engineering defaults. The trigger interval is usually
# the biggest lever and the one nobody tunes.
```
### Event time versus processing time

**Processing time** is when the engine handles the record. **Event time** is when the record says it happened.

The two differ whenever there is any latency between the two: network delay, a source that batches, a queue backlog, a retry, a partition that was temporarily unavailable. This is not an edge case; it is the normal condition of a distributed system.

If you aggregate by processing time, you answer the wrong question. "How many orders did we get in the last hour?" becomes "how many orders *arrived* at us in the last hour" — which, after an outage, answers "all of them" for one bucket and zero for the next. Your revenue dashboards spike and dip in ways that correlate with your own infrastructure health, not with your business.

The correct rule: **the timestamp you aggregate by must come from the data, never from the clock of the machine doing the aggregation.** In the project, `bucket_by_window` is explicit about this:

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import bucket_by_window, ingest_events

with open("sample_data/events.csv") as handle:
    accepted, rejected = ingest_events(handle)

windows = bucket_by_window(accepted, window_seconds=3600)
print(f"accepted={len(accepted)} rejected={len(rejected)}")
print(f"hourly windows={len(windows)}")
```

The docstring of `bucket_by_window` names the failure mode exactly, and it is worth reading twice:

> This is the pure equivalent of a Dataflow fixed window: the bucket is derived from the **event timestamp**, never from arrival time. Skip the re-stamping step and every event collapses into a single window — the totals stay right, which is exactly why the bug is so easy to miss.

That last clause is the killer. If you use processing time, your **totals** are usually still correct — you just put the rows in the wrong bucket. Nothing crashes, no alert fires, the daily revenue number is right, and the hourly chart is garbage. It takes a human noticing a spike to find it.

### Watermarks and lateness

Once you aggregate by event time, you must answer: *when is a window closed?* You cannot know. A record with a timestamp of 14:00 might arrive at 14:00:01 or at 14:59:59.

The industry solution is the **watermark**: the system's claim about how complete the data is, per partition. A watermark is "I have seen all events up to time T" (plus some allowance). When the watermark passes the end of a window, the window is closed and its result is emitted.

If a record arrives *after* the watermark passed its window, it is **late**. A late record is not a bug to be silently dropped — it is a design case. Your options:

1. **Drop it** and count it. Simple, lossy. Fine when late data is rare and a correction is acceptable.
2. **Buffer and correct.** Keep the window open until a bounded lateness allowance expires, then emit. This is the standard choice.
3. **Allow retraction.** Emit a correction (negative delta) that downstream subtracts. Correct but it makes every downstream consumer retraction-aware, which is expensive to build.

The operational requirement in all cases: **you must measure late data**, or you cannot claim your numbers are right. `watermark_lag` in the project is the shape of that metric.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import hours_spanned, ingest_events, watermark_lag

with open("sample_data/events.csv") as handle:
    accepted, rejected = ingest_events(handle)

lag = watermark_lag(accepted)
print(f"hours spanned: {hours_spanned(accepted)}")
print(f"watermark lag: {lag}")
```

### Kafka's architecture

Kafka is a **distributed, partitioned, replicated, append-only commit log**. Everything else follows from those five words.

- A **broker** is a server process. A production deployment is 3, 5, or more brokers, each a separate machine, each in a different zone.
- A **topic** is a logical name for a stream of records. It is not a container of data; it is a label.
- A **partition** is an ordered, append-only log. A topic with 12 partitions is 12 independent logs, each with its own leader.
- A **leader** is the broker currently accepting writes for a partition. A **follower** replicates the leader's log.
- The **replication factor (RF)** is how many brokers hold each partition's data. RF=3 means three copies.
- The **in-sync replica set (ISR)** is the set of followers that are caught up with the leader.

The write path:

```text

```

### The partition is the unit of everything

This is the single most important idea in Kafka, and it is worth stating bluntly: **a partition is simultaneously the unit of parallelism, the unit of ordering, and the unit of throughput.** You cannot tune them independently.

- **Parallelism**: each partition can be consumed by exactly one consumer in a group at a time. So *max consumers that read the whole topic = number of partitions*. Twelve partitions, twelve consumers, and each consumer handles one partition. A thirteenth consumer idles.
- **Ordering**: records within a partition are totally ordered. Records across partitions have **no** defined order relative to each other. Ever.
- **Throughput**: total topic throughput is roughly the sum of per-partition throughput, capped by the slowest partition. One hot key writing 80% of traffic to one partition makes that partition the bottleneck for the entire topic.

The consequence for capacity planning: **partition count is the ceiling on consumer parallelism, and you cannot decrease it later.** Kafka does not support reducing partition counts (it used to via a config flag; it is deprecated and dangerous). Under-partition and you cannot scale out. Over-partition and you pay per-partition overhead (each partition has a leader, replication, file handles, index files) and your hot partition problem gets worse.

Rule of thumb: partitions = (peak throughput ÷ per-partition throughput ceiling), rounded up with headroom. Measure the per-partition ceiling; do not guess.

### The consumer group and partition assignment

A **consumer group** is a set of consumers that collectively read a topic and each message is delivered to **exactly one** consumer in the group. Different groups are independent — each gets its own copy of every message. This is the fan-out mechanism: group A does fraud detection, group B does training data collection, group C powers a live dashboard.

The assignment problem: given N consumers and M partitions, assign each partition to at most one consumer, so that (a) every partition is consumed, and (b) load is balanced. Kafka's default assignor is **range** (each consumer gets a contiguous range of partitions), which is simple but has a well-known pathology: with 4 consumers and 6 partitions, the first consumer gets 2 and the rest get 1 each. Consumers with *different* throughput profiles make this much worse.

The **cooperative-sticky** assignor (Kafka 2.4+, the default in modern Kafka) solves the incremental-rebalance problem: instead of revoking everything and reassigning, consumers only give up the partitions they need to move.

The rebalance is the operational hazard. When a consumer joins, leaves, or times out, the group rebalances and **consumption pauses**. Under the eager (range/roundrobin) protocol, all partitions are revoked and reassigned — a stop-the-world pause. This is why:

- `session.timeout.ms` and `max.poll.interval.ms` are the two most-tuned Kafka settings.
- If your processing takes longer than `max.poll.interval.ms` (default 5 minutes) between polls, **the consumer is evicted** and its partitions reassigned, even though it is healthy — producing duplicate processing (at-least-once semantics in action) and rebalance churn.
- Long processing should be separated from the consumer thread, or you must call `poll()` more often.

The "slow consumer" problem in one sentence: **one slow partition drags down a whole consumer group**, because the group's throughput is bounded by its slowest member, and with range assignment the slowest partition often lands on the same consumer.

### Offsets and commit semantics

Each partition has a monotonically increasing **offset**. A consumer records its progress as "I have processed up to offset N for partition P" — that record is the **committed offset**, stored in an internal topic (`__consumer_offsets`).

The commit strategy determines the delivery guarantee:

| Semantics | When you commit | Possible outcome | Idempotency required? |
|---|---|---|---|
| **At-most-once** | Before processing | Messages can be **lost** on crash | No |
| **At-least-once** | After processing | Messages can be **duplicated** on crash | **Yes** |
| **Exactly-once** | Transactional (write + offset atomically) | Neither lost nor duplicated | Yes, plus a transactional sink |

**At-most-once**: commit the offset, then process. If the process dies between commit and processing, the message is gone forever. This is the default in some clients and it is almost never what you want for anything except pure metrics where loss is tolerable and duplicates are not.

**At-least-once**: process, then commit. If the process dies between processing and commit, the message is redelivered. This is the safe default and what most Kafka applications use. The cost is that your processor **must be idempotent**, because duplicates are guaranteed to happen eventually. Not "might happen" — will happen, on every deploy, every rebalance storm, every broker restart.

The standard idempotency pattern is an idempotent upsert keyed on a business key, exactly like `dedup_key` in the project:

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import dedup_key, deduplicate, partition_for_event

rows = [
    {"event_id": "e00000000", "event_dt": "2026-01-15T00:54:38+00:00"},
    {"event_id": "e00000001", "event_dt": "2026-01-15T03:09:55+00:00"},
    {"event_id": "e00000000", "event_dt": "2026-01-15T00:54:38+00:00"},  # redelivery
]
partition = partition_for_event(rows[0]["event_dt"])
print(f"partition={partition}")
print(f"in={len(rows)} out={len(deduplicate(rows, partition=partition))}")
print(f"key={dedup_key('e00000000', partition)}")
```
The critical rule, from the `dedup_key` docstring: **the identity must be derived from the data, never from arrival time.** A load-time timestamp would make a retry produce *different* rows rather than the same rows, which defeats deduplication entirely. So would a random UUID generated at publish time if you re-publish from a different run. Business key + partition, always.

**Exactly-once**: Kafka's transactional API makes "produce to topic T" and "advance offset for group G" a single atomic commit against the transaction coordinator, so both happen or neither does. Read-process-write is exactly-once only when the write is to a Kafka topic; writing to BigQuery or GCS breaks the transaction boundary. The realistic pattern is **Kafka EOS for the Kafka-to-Kafka hop, and idempotent writes for everything downstream.** Claiming "exactly-once end to end" across Kafka and BigQuery is a category error — BigQuery has no two-phase commit with Kafka.

### Log-structured storage and retention

Kafka stores records in **segment files** on disk. The log is append-only. Data is written to the end of the active segment; when a segment reaches `log.segment.bytes` (default 1 GB) it is rolled and closed. Closed segments are subject to retention.

This is why Kafka is a filesystem-backed system and not an in-memory system, and why throughput and latency are decoupled from the number of consumers: a consumer reading at its own pace does not slow the producer.

**Retention is a disk-space decision.** Kafka does not know what your data means. When it deletes a segment, the data is gone. Your recovery story depends entirely on a downstream consumer having persisted it elsewhere. Setting `retention.ms` to seven days means: "I need to be able to replay the last seven days of events into a new consumer group." If your real requirement is "I need to be able to re-run yesterday's job", seven days is right. If your requirement is "I need to recover from a botched backfill", it might be longer.

The three retention knobs:

- `retention.ms` — time-based. The default is 7 days.
- `retention.bytes` — size-based. Default is -1 (unlimited). When both are set, **whichever triggers first wins** — and this is a classic surprise: a size limit can silently delete data hours after a traffic spike, far inside the time window.
- `log.retention.checkpoint.interval.ms` and `log.retention.hourly.checkpoint.interval.ms` — how often the retention thread runs to actually delete. These are why deleted data can persist physically for hours after its logical expiry. Disks are not free until the segment is actually deleted.

`log.cleanup.policy=delete` (the default) deletes whole segments and discards the tombstones. `log.cleanup.policy=compact` keeps the log forever but removes records whose key has a newer record — it is a **key-value state store**, not an event log. Using compaction to "save space" on an event log is wrong: you lose the history, and if you need history for audit you have lost it.

**Never set an infinite retention on a Kafka topic and assume the broker is backing up your data.** Kafka is not a backup system. It is a transport buffer with a replay window.

### Key-based ordering and its limits

Kafka guarantees ordering **within a partition**. To get ordering for a given entity, all records for that entity must land in the same partition. The default partitioner hashes the record key:

```text
partition=20260115
in=3 out=2
key=20260115:e00000000
```

Two consequences that bite hard:

1. **The mapping is not stable across partition count changes.** If you increase partitions from 12 to 24, `hash(key) % 24` produces a completely different partition for most keys. After a partition expansion, a given key's records are split across two partitions, and **ordering for that key is broken**. This is why you cannot cleanly add partitions to an ordered topic, and why "we need to add partitions" is an architectural decision, not an operational tweak.

2. **Hot keys destroy throughput.** If one customer generates 30% of your traffic, their key maps to one partition, and that partition's throughput ceiling becomes your topic's ceiling. The fix is sub-keying — but then you have broken the ordering you wanted.

The precise guarantee you can make: *records with the same key, in the same partition, produced in order to the same partition leader, are consumed in order.* The "produced in order" part is your responsibility — if your producer has two threads publishing to the same key concurrently without a lock, Kafka does not serialise them for you.

### Schema Registry and Avro

Avro is a schema-based serialisation format. A Schema Registry stores versioned schemas and enforces compatibility rules on registration. Why this matters:

- **Self-describing JSON is not self-describing in practice.** Consumers end up with `data["user"]["id"]` assumptions baked into code, and a producer that starts sending a string where an int was expected breaks every downstream consumer at once, at 03:00.
- **Avro is compact.** Binary encoding is materially smaller than JSON, which directly reduces Kafka storage and, on Pub/Sub, the per-GB message charge.
- **Compatibility rules turn breakage into a rejected publish.** With `BACKWARD` compatibility, the producer cannot register a schema that would break existing consumers — the publish fails instead. The failure moves from "3 a.m. downstream" to "the producer's CI", which is the entire point.

Compatibility modes worth knowing:

| Mode | Rule | Use when |
|---|---|---|
| `NONE` | No checks | Rarely. Legacy or non-Avro |
| `BACKWARD` | New reader can read old data | Default. Safe for adding fields |
| `BACKWARD_TRANSITIVE` | New reader reads all previous versions | Stricter; default in recent Confluent |
| `FORWARD` | Old reader can read new data | Rarely |
| `FULL` | Both directions | Very strict |

You can also make a *field* optional (`["null", "string"]` union with default `null`) which is the correct way to evolve a schema without forcing every consumer to handle the new field — but only under BACKWARD compatibility, and only if you supply the default.

### Kafka versus Pub/Sub on GCP

Both are messaging. The differences are structural, and the decision is usually not close.

| Dimension | Pub/Sub | Kafka (Confluent Cloud on GCP) |
|---|---|---|
| Operations | Zero — fully managed, serverless | You choose and pay for the cluster |
| Message retention | 7 days default, 31 days max | Configurable; can be infinite with compaction |
| Replay | Only within retention; create a new subscription to replay | Native; any consumer can seek to any offset |
| Partitioning | Automatic, managed | Manual, fixed at creation, cannot be reduced |
| Ordering | Ordering key → per-key FIFO, managed | Record key → per-partition FIFO |
| Delivery | At-least-once default, exactly-once available | At-least-once default, EOS via transactions |
| Schema enforcement | Optional | Schema Registry is central |
| Throughput ceiling | High | Higher, tunable per partition |
| Cost shape | Per GB ingested + per GB delivered | Per GB ingested + per GB retained + per cluster-hour |
| Best for | GCP-native, event fan-out, serverless consumers | High-volume, long-replay, multi-team platform |

**When Kafka earns its cost:**

- You need a **replay window longer than 31 days**, or replay from an arbitrary offset rather than "recreate a subscription".
- You have **many consumer teams** sharing a stream and need governance over schemas across organisational boundaries.
- You need **higher sustained throughput** per dollar than the Pub/Sub model delivers, or you need fine control over partition layout and hot-key mitigation.
- You are running **Kafka Connect / Kafka Streams** and already have a Kafka-centred platform.
- You need **ordering with a guarantee that Pub/Sub's ordering keys cannot give** — or you need ordering per key with higher throughput than a single ordering key permits.

**When Pub/Sub is the right answer (most of the time on GCP):**

- Every consumer is on GCP and serverless (Dataflow, Cloud Run, GKE).
- You want **zero operational ownership**. Kafka is not free to run; Confluent Cloud reduces but does not eliminate that.
- You need **fan-out to independent consumers** where each wants its own delivery position — Pub/Sub subscriptions model this natively.
- Your **retention needs are bounded** (7 days default is usually plenty).
- Your **team does not already operate Kafka**. The operational tax of a broker fleet, partitions, ISR shrinking, and rebalance storms is real and continuous.

My opinionated take: **on GCP, default to Pub/Sub.** Choose Kafka when you have a specific, articulable requirement that Pub/Sub cannot meet — usually replay depth, schema governance across teams, or extreme throughput. "We might need it later" is not a requirement; adding a Kafka cluster later is a project, but adding one on a whim is a permanent tax.

---

## 🛠️ Hands-On

### Lab 1 — Model the streaming contract with the project pipeline

The project already implements the streaming semantics in pure Python. This lab walks the whole path: ingest (subscription pull), validate (DoFn), aggregate (CombinePerKey), publish, and idempotent load.

```python
import sys
sys.path.insert(0, "project/core")

from platform_sim import build_demo_project, format_pipeline_log

project = build_demo_project()
with open("sample_data/events.csv") as handle:
    lines = list(handle)

result = project.run_pipeline(lines)
print(format_pipeline_log(result))
print("summary csv:")
print(result.summary_csv)
```
Expected output:

```text
▶ Running pipeline

  ingest: 4800 accepted, 0 rejected
  aggregate: 4 regions, 4800 events
  publish: 4800 messages to events-normalised
  load: partition 20260115, 4800 rows
  dedup: 4800 -> 4800 rows (0 duplicates removed)

region,event_count,revenue_eur
AMER,1238,464848.02
APAC,1159,421049.85
EMEA,1176,432544.17
LATAM,1227,445554.36
summary csv:
region,event_count,revenue_eur
AMER,1238,464848.02
APAC,1159,421049.85
EMEA,1176,432544.17
LATAM,1227,445554.36
```

### Lab 2 — Build a Kafka partition-assignment simulator

Kafka's partition assignment is a small enough algorithm to simulate exactly. This is the clearest way to internalise why partition count caps consumer parallelism.

```python
from dataclasses import dataclass, field


@dataclass
class Consumer:
    name: str
    throughput: int  # messages per second this consumer can process
    partitions: list[int] = field(default_factory=list)


def range_assign(num_partitions: int, consumers: list[Consumer]) -> None:
    """Kafka's default range assignor: contiguous blocks per consumer."""
    per_consumer = num_partitions // len(consumers)
    extra = num_partitions % len(consumers)
    start = 0
    for index, consumer in enumerate(consumers):
        count = per_consumer + (1 if index < extra else 0)
        consumer.partitions = list(range(start, start + count))
        start += count


def group_throughput(consumers: list[Consumer]) -> int:
    """Group throughput is bounded by the slowest member."""
    return sum(c.throughput for c in consumers)


consumers = [Consumer(f"c{i}", throughput=1000) for i in range(4)]
range_assign(12, consumers)
for c in consumers:
    print(f"{c.name}: partitions={c.partitions}")
print(f"group throughput: {group_throughput(consumers)} msg/s")
```

Expected output:

```text
c0: partitions=[0, 1, 2]
c1: partitions=[3, 4, 5]
c2: partitions=[6, 7, 8]
c3: partitions=[9, 10, 11]
group throughput: 4000 msg/s
```

Now add a fifth consumer to a 12-partition topic and observe the idle consumer — the classic symptom of over- or under-partitioning:

```python
from dataclasses import dataclass, field


@dataclass
class Consumer:
    name: str
    throughput: int  # messages per second this consumer can process
    partitions: list[int] = field(default_factory=list)


def range_assign(num_partitions: int, consumers: list[Consumer]) -> None:
    """Kafka's default range assignor: contiguous blocks per consumer."""
    per_consumer = num_partitions // len(consumers)
    extra = num_partitions % len(consumers)
    start = 0
    for index, consumer in enumerate(consumers):
        count = per_consumer + (1 if index < extra else 0)
        consumer.partitions = list(range(start, start + count))
        start += count


consumers = [Consumer(f"c{i}", throughput=1000) for i in range(5)]
range_assign(12, consumers)
for c in consumers:
    status = "ACTIVE" if c.partitions else "IDLE"
    print(f"{c.name}: {status} partitions={c.partitions}")
```

Expected output:

```text
c0: ACTIVE partitions=[0, 1, 2]
c1: ACTIVE partitions=[3, 4, 5]
c2: ACTIVE partitions=[6, 7]
c3: ACTIVE partitions=[8, 9]
c4: ACTIVE partitions=[10, 11]
```

Note what actually happened: the range assignor gave the first two consumers three partitions each and the last three two each. **No consumer is idle — but the load is uneven.** With a fixed number of partitions, adding a consumer does not add throughput beyond the partition count; it just redistributes partitions. And because `range_assign` splits by *contiguous blocks* rather than by load, the consumer with the *slowest* hardware may end up holding the largest block. That is the range assignor's central weakness, and the reason the cooperative-sticky assignor exists.

### Lab 3 — Simulate at-least-once delivery and prove idempotency

This is the core correctness argument of the chapter, executed.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import deduplicate, partition_for_event

# A consumer processed two messages, then crashed BEFORE committing its
# offset. On restart, the broker redelivers from the last committed offset.
delivered = [
    {"event_id": "e00000000", "event_dt": "2026-01-15T00:54:38+00:00"},
    {"event_id": "e00000001", "event_dt": "2026-01-15T03:09:55+00:00"},
    # --- crash: offset not committed, broker replays from offset 0 ---
    {"event_id": "e00000000", "event_dt": "2026-01-15T00:54:38+00:00"},
    {"event_id": "e00000001", "event_dt": "2026-01-15T03:09:55+00:00"},
    {"event_id": "e00000002", "event_dt": "2026-01-15T06:12:01+00:00"},
]

partition = partition_for_event(delivered[0]["event_dt"])
unique = deduplicate(delivered, partition=partition)
print(f"delivered={len(delivered)} unique={len(unique)} duplicates={len(delivered) - len(unique)}")
print(f"partition={partition}")
```

Expected output:

```text
delivered=5 unique=3 duplicates=2
partition=20260115
```

The duplicates are removed *deterministically*, with no external state, because the identity is derived from the business key and the partition. This is what makes at-least-once safe.

### Lab 4 — Verify the event-time windowing contract

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import aggregate_by_window, bucket_by_window, ingest_events

with open("sample_data/events.csv") as handle:
    accepted, rejected = ingest_events(handle)

windows = bucket_by_window(accepted, window_seconds=3600)
by_window = aggregate_by_window(accepted, window_seconds=3600)

print(f"accepted={len(accepted)} rejected={len(rejected)}")
print(f"windows={len(windows)} rows={len(by_window)}")

first_key = sorted(windows)[0]
last_key = sorted(windows)[-1]
print(f"first window={first_key} events={len(windows[first_key])}")
print(f"last window={last_key} events={len(windows[last_key])}")
print(f"total in windows={sum(len(v) for v in windows.values())}")
```

Expected output:

```text
accepted=4800 rejected=0
windows=24 rows=96
first window=2026-01-15T00:00:00+00:00 events=203
last window=2026-01-15T23:00:00+00:00 events=179
total in windows=4800
```

`total in windows=4800` is the invariant that proves no event was lost or double-counted by the windowing. 24 windows × 4 regions = 96 aggregate rows.

### Lab 5 — Price the Kafka-versus-Pub/Sub decision

```python
import sys
sys.path.insert(0, "project/core")

from cost_model import estimate

# 10 GB/day of events, retained 7 days on Kafka, delivered to 3 consumer groups.
daily_gb = 10.0
monthly_gb = daily_gb * 30

pubsub = estimate("pubsub", pubsub_gb=monthly_gb, messages=0, apply_free_tier=False)
kafka_ingest = monthly_gb * 0.40
kafka_retained = monthly_gb * 7 * 0.0235  # ~$0.0235/GB-month retained

print(f"Pub/Sub ingest+storage (30d):   ${pubsub.total:,.2f}")
print(f"Kafka ingest (30d):             ${kafka_ingest:,.2f}")
print(f"Kafka retained (7d window):     ${kafka_retained:,.2f}")
print(f"Kafka total (no cluster fee):   ${kafka_ingest + kafka_retained:,.2f}")
```
The point of the exercise is not the absolute number — it is that Pub/Sub's cost is dominated by *delivery* (per GB delivered to each subscription), while Kafka's is dominated by *retention*. If you have 10 consumer groups, Pub/Sub's delivery cost dominates. If you need 30 days of replay, Kafka's retention cost dominates. The cost winner depends entirely on the shape of your fan-out and your replay requirement.

### Lab 6 — Inspect the catalog entries for the three streaming services

```python
import sys
sys.path.insert(0, "project/core")

from service_catalog import get_service, regions_for, services_by_category

for service_id in ("kafka", "pubsub", "datastream"):
    service = get_service(service_id)
    print(f"{service.id}: {service.name}")
    print(f"  role       : {service.data_role}")
    print(f"  pricing    : {service.pricing_model}")
    print(f"  resources  : {', '.join(service.key_resources)}")
    print(f"  regions    : {len(regions_for(service_id))}")
    print()

streaming = services_by_category("Streaming & Messaging")
print("streaming & messaging services:")
for service in streaming:
    print(f"  - {service.id}")
```

Expected: three services in `Streaming & Messaging` — `kafka`, `pubsub`, `datastream` — and the Kafka entry correctly lists `southamerica-east1` under `restricted`, matching the fact that Confluent Cloud has no São Paulo region.

---

## 🛠️ Common Errors and Fixes

### 1. `org.apache.kafka.common.errors.UnknownTopicOrPartitionException`

```text
Pub/Sub ingest+storage (30d):   $120.00
Kafka ingest (30d):             $120.00
Kafka retained (7d window):     $49.35
Kafka total (no cluster fee):   $169.35
```

**Cause:** the producer sent to a topic that does not exist, or the topic exists but the broker's metadata cache has not been refreshed. A common variant is a typo'd topic name that silently auto-creates a *new* topic with default settings — one partition, one replica — which then becomes a production hotspot forever.

**Fix:** create the topic explicitly with the partition and replication count you actually want, and never rely on auto-creation in production.

```bash
gcloud pubsub topics describe orders.v1          # Pub/Sub equivalent
kafka-topics.sh --bootstrap-server $BOOTSTRAP \
  --create --topic orders.v1 --partitions 12 \
  --replication-factor 3 \
  --config retention.ms=604800000 \
  --config min.insync.replicas=2
```

### 2. `KafkaTimeoutError: Timeout expired: 60000 ms since last operation` or consumer eviction

```text
WARN o.a.k.clients.consumer.internals.ConsumerCoordinator:
Commit of offset {orders.v1=1042,orders.v2=88} failed:
CommitFailedException: This means that the consumer is not part of an
active group for auto partition assignment, and it has been removed
by the group coordinator.
```

**Cause:** the consumer was evicted because it exceeded `max.poll.interval.ms` (default 5 minutes) between `poll()` calls, or exceeded `session.timeout.ms`. Processing a batch took longer than the interval allowed.

**Fix:** decouple processing from the poll loop, or raise the interval and reduce `max.poll.records`. Do **not** simply set `max.poll.interval.ms` to a huge value — that just converts a fast failure into a slow failure where the partition is silently unowned.

```properties
max.poll.records=500
max.poll.interval.ms=300000
session.timeout.ms=45000
```

```bash
# Inspect consumer lag and assignment directly
kafka-consumer-groups.sh --bootstrap-server $BOOTSTRAP \
  --describe --group orders-processors --all-groups
```

### 3. `LEADER_NOT_AVAILABLE` and constant rebalances after a broker dies

```text
WARN o.a.k.clients.consumer.internals.AbstractCoordinator:
Discovered group coordinator as broker-1
ERROR o.a.k.clients.consumer.internals.ConsumerCoordinator:
(Re-)joining group orders-processors
```

**Cause:** a broker failed and the ISR for some partitions shrank below `min.insync.replicas`, so the leader is unavailable and the group keeps re-electing. Often the root cause is RF=1 or RF=2 with `min.insync.replicas=2` — a configuration that cannot survive a single failure.

**Fix:** use RF=3 with `min.insync.replicas=2`. That combination tolerates one broker failure without losing availability, and still refuses writes when two brokers are down — which is the guarantee you want.

```bash
kafka-configs.sh --bootstrap-server $BOOTSTRAP --entity-type topics \
  --entity-name orders.v1 --alter \
  --add-config min.insync.replicas=2
```

### 4. `OutOfOrderSequenceException` / `ProducerFencedException`

```text
org.apache.kafka.common.errors.OutOfOrderSequenceException:
The broker received an out of order sequence number for topic
orders.v1 partition-3
```

**Cause:** two producer instances used the same `producer.id` (usually a duplicated config or a restarted instance with a stale transactional id), or a transaction was left open and then timed out.

**Fix:** give each producer instance a unique, stable `transactional.id`, and shut down producers cleanly so transactions are aborted rather than left dangling. `ProducerFencedException` means another producer has fenced this one — that is the mechanism working correctly; the fix is to stop using the old instance.

```properties
transactional.id=orders-producer-us-central1-01
enable.idempotence=true
acks=all
max.in.flight.requests.per.connection=5
```

### 5. Schema Registry rejects a compatible-looking change

```text
RESTException: Schema being registered is incompatible with an earlier schema:
Error message: Reader schema with field orders.v2.shipped_at of type
string is incompatible with writer schema of type int
```

**Cause:** the new schema changed an existing field's type. Adding a field with a default is `BACKWARD`-compatible; changing a type is not, and the registry correctly refuses.

**Fix:** never mutate an existing field's type in place. Add a new field (e.g. `shipped_at_v2`) with a default, backfill, and deprecate the old field in a later version. This is the schema-evolution discipline that Avro is designed to enforce.

```bash
curl -X POST http://schema-registry:8081/subjects/orders.v2/versions \
  -H 'Content-Type: application/vnd.schemaregistry.v1+json' \
  -d '{"schema":"{\"type\":\"record\",\"name\":\"Order\",\"fields\":[{\"name\":\"id\",\"type\":\"string\"},{\"name\":\"total\",\"type\":[\"null\",\"double\"],\"default\":null}]}","schemaType":"AVRO"}'
```

### 6. Duplicate processing that idempotency did not fix

**Symptom:** the same event appears twice in BigQuery after a routine deploy.

**Cause:** the deduplication key includes something non-deterministic. The classic bug is deriving the key from `ingest_timestamp` or a random UUID generated at write time — a retry then produces a *different* key, so it is not a duplicate by the key's definition.

**Fix:** derive the key from the business key and the partition, exactly as `dedup_key` does. Then verify with a duplicate-count query against the target table.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import dedup_key, partition_for_event

event = {"event_id": "e00000000", "event_dt": "2026-01-15T00:54:38+00:00"}
partition = partition_for_event(event["event_dt"])
print(dedup_key(event["event_id"], partition))
# 20260115:e00000000  <- deterministic; a retry produces the same key
```

---

## 💡 Production Notes

- **Partition count is the ceiling on consumer parallelism and it can only go up.** Size it for your peak throughput with headroom, never for today's average. Kafka cannot reduce partition count, and changing it breaks key-based ordering because `hash(key) % num_partitions` remaps.

- **Every Kafka consumer must be idempotent.** At-least-once is the default and redelivery on rebalance is guaranteed, not exceptional. Use a business key derived from the data — never from arrival time — exactly like `dedup_key(event_id, partition)`.

- **Size batches so processing finishes well inside `max.poll.interval.ms`.** Default is 5 minutes; target completion under 60 seconds so a single slow batch cannot evict the consumer and trigger a rebalance storm. Decouple the poll loop from processing if your work is heavy.

- **Retention is a disk-space decision, not a data-lifecycle decision.** Kafka deletes what you tell it to delete and knows nothing about business meaning. Set `retention.ms` to your actual replay requirement, and remember that `retention.bytes` can expire data far earlier than the time window under a traffic spike.

- **Kafka is not a backup system.** With infinite retention on a compacted topic you still lose the ability to rebuild a state you compacted away, and with time-based retention you lose the replay window entirely. Every topic must have a durable sink — BigQuery, GCS, or a warehouse — and the Kafka copy is a transport buffer.

- **Schema compatibility is enforced, not hoped for.** Register schemas with `BACKWARD` (or `BACKWARD_TRANSITIVE`) compatibility so a breaking producer change fails at publish time rather than breaking every downstream consumer simultaneously.

- **Watch consumer lag as a first-class SLI, and watch it per partition, not per group.** Aggregate lag can hide a single stuck partition, which is the failure that actually hurts. A healthy group has balanced lag across all its partitions.

- **On GCP, default to Pub/Sub.** Choose Kafka only for a specific articulable requirement — replay beyond 31 days, schema governance across organisational boundaries, or sustained throughput above what Pub/Sub delivers for your shape of workload. Every Kafka deployment carries a permanent operational tax.

---

## 🔑 Key Takeaways

- Streaming is defined by **when the answer is computed** and **whether it can be retracted**, not by how fast it is. Micro-batching is the correct default for most workloads.
- Latency is the sum of every stage; the slowest stage sets the floor. The trigger interval is usually the biggest lever and the least tuned.
- **Aggregate by event time, never by processing time.** Processing-time aggregation produces plausible totals in implausible buckets — a failure with no crash and no alert.
- Late data is a design case, not an error. Every streaming pipeline needs a lateness policy and a metric that measures how much late data actually arrives.
- A Kafka **partition** is simultaneously the unit of parallelism, ordering, and throughput. Partition count caps consumer parallelism, cannot be reduced, and changing it breaks key ordering.
- The **consumer group** guarantees exactly-once delivery *within* a group and full fan-out *across* groups. Rebalances pause consumption; `max.poll.interval.ms` is the setting that causes most surprises.
- **At-least-once is the practical default** and it requires idempotent processing. The dedup identity must come from the business key and partition, never from a timestamp.
- Kafka's log-structured storage decouples throughput from consumer speed and makes retention a **disk-space** decision. Never treat it as a backup.
- Ordering is guaranteed **per partition only**, and the key→partition mapping is unstable when the partition count changes.
- **Schema Registry + Avro** turns a 3 a.m. downstream break into a publish-time rejection in the producer's CI. JSON without a schema is a coordination protocol you have not written down.
- On GCP, **Pub/Sub by default**; Kafka for replay depth, cross-team schema governance, or extreme sustained throughput.

---

## 📚 Practice Exercises

1. **Latency budget.** Using the `LATENCY_BUDGET` dict from the Hands-On section, write a function that takes a list of stage latencies and returns the total, the slowest stage, and the headroom against a 300-second target. Then argue, in writing, which single stage you would cut first and why.

2. **Event-time vs processing-time.** Modify a copy of `bucket_by_window` so it buckets by processing time instead of event time (simulate arrival time as `event_dt + random offset`). Show that the totals are identical but the per-window distribution is completely different. Explain why this bug survives code review.

3. **Partition-count simulator.** Extend the Lab 2 range assignor to implement the round-robin and cooperative-sticky assignors. Show the partition distribution for 12 partitions across 4 consumers under each, and identify where a hot key lands in each scheme.

4. **Hot-key analysis.** Write a function that, given a list of `(key, count)` pairs and a partition count, computes the partition load distribution and reports the imbalance ratio (max partition load ÷ mean partition load). Use it to show why a single 30%-of-traffic key caps your topic throughput.

5. **Offset commit matrix.** Implement a `Consumer` class with `commit_before_processing` and `commit_after_processing` modes, then simulate a crash at each of three points (before read, after read, after process) and tabulate, for each mode, whether the message was lost, duplicated, or correct.

6. **At-least-once to exactly-once.** Using `pipeline_logic.deduplicate` and `dedup_key`, show that the project's pipeline is idempotent under redelivery. Write the BigQuery `MERGE` statement you would use to write the same rows idempotently into a partitioned table, and explain why a `MERGE` on `event_id` is equivalent to `deduplicate`.

7. **Schema evolution.** Write two Avro schemas — one adding a field with a default, one changing a field's type — and predict, for each, whether `BACKWARD` compatibility accepts it. Explain what a consumer would see at runtime if the registry were bypassed.

8. **Cost decision.** Extend the Lab 5 comparison to model 3 consumer groups on Pub/Sub (each group adds a delivery charge) and 30-day Kafka retention. Produce a table showing at what fan-out count and retention length the Kafka option becomes cheaper, and state your conclusion for a specific team.

---

## 📖 Further Reading

- [Apache Kafka Documentation: Introduction](https://kafka.apache.org/documentation/)
- [Confluent Cloud on Google Cloud Documentation](https://docs.confluent.io/cloud/current/gcp.html)
- [Cloud Pub/Sub Documentation — Delivery Types](https://docs.cloud.google.com/pubsub/docs/pull)
- [Apache Kafka: Designing Event-Driven Systems (O'Reilly)](https://www.oreilly.com/library/view/designing-event-driven-systems/9781492040352/)
- [Apache Kafka: The Definitive Guide, 2nd Edition](https://www.oreilly.com/library/view/apache-kafka-the-definitive/9781492043083/)
- [Streaming and Batch Processing: Dataflow Documentation](https://docs.cloud.google.com/dataflow/docs/overview)
- [GCP Data Engineer Certification Study Guide](https://cloud.google.com/certification/resources/data-engineer-study-guide)
