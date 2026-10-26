# 13 — Extraction at Scale: Backpressure, Batching, Parallelism

> **Lesson 13 of 30 — Extraction**

The single-source pipeline works at 1K rows/sec. At 1M rows/sec
it falls over. This lesson is what to do when the source
out-produces the pipeline.

---

## 1. The three problems of scale

When the source produces more than the pipeline can consume, three
things break:

1. **Memory:** the pipeline buffers rows in memory; if the source
   is faster, the buffer grows until OOM.
2. **Latency:** the destination sees rows minutes (or hours) after
   they were produced.
3. **Backpressure:** the source notices (e.g. Kafka consumer lag
   grows; Postgres WAL fills up) and the failure propagates back.

The senior move is to design for backpressure from day one. The
pipeline must be able to say "slow down" to the source — or, more
commonly, must be sized to handle the peak.

---

## 2. Batching

The simplest backpressure mechanism: *batch* writes. Instead of
one INSERT per row, batch 1000 rows per INSERT. This reduces
per-row overhead by 100-1000x.

```python
def batched_extract(source, batch_size=1000):
    batch = []
    for row in source:
        batch.append(row)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch
```

The trade-off: latency. A batch of 1000 rows means the destination
sees the first row 1000-rows-worth of time after the source
produced it. For high-throughput, low-latency systems, batching is
the wrong answer; for high-throughput, high-latency-tolerance
systems, batching is the right answer.

---

## 3. Parallelism

The next lever: *parallelism*. Run N extractors in parallel, each
on a subset of the data. The subsets must be *disjoint* — no two
extractors reading the same row.

The three ways to partition:

| Partitioning | Use case |
|---|---|
| **By primary key range** | `WHERE id BETWEEN 1 AND 10000`, `WHERE id BETWEEN 10001 AND 20000`, ... |
| **By hash of key** | `WHERE hash(id) % 4 = 0`, `WHERE hash(id) % 4 = 1`, ... |
| **By date** | `WHERE event_date = '2024-01-15'`, `WHERE event_date = '2024-01-16'`, ... |

The senior move: key-range or date partitioning when the
distribution is uniform; hash partitioning when it's skewed.

---

## 4. The Kafka consumer-group pattern

Kafka's consumer group is the canonical example of partition-based
parallelism. A topic has N partitions; a consumer group has up to
N consumers. Each consumer reads one partition, exclusively.

```
Topic "events" with 12 partitions:

Consumer 1: reads partition 0
Consumer 2: reads partition 1
...
Consumer 12: reads partition 11
```

The scaling rule: number of consumers ≤ number of partitions. If
you have 12 partitions and 24 consumers, 12 are idle. The senior
move: size partitions to your peak throughput (12 is the Kafka
default; real production topics often have 100+).

---

## 5. The Spark partition pattern

Spark parallelizes the same way: a DataFrame is split into N
partitions, each partition is processed by one task. The number
of partitions is the parallelism.

```python
df = spark.read.parquet("s3://data/events/")
# Repartition to control parallelism:
df = df.repartition(200, "user_id")
df.write.parquet("s3://data/events_by_user/")
```

The senior move: `spark.sql.shuffle.partitions = 200` is a common
default; tune it to the cluster size and the data volume. Too few
partitions = idle workers; too many = task overhead.

---

## 6. The backpressure pattern

Backpressure is the pipeline's ability to *slow down the source*
when the destination can't keep up. Three patterns:

**Pattern 1: bounded queue.** The extractor pulls rows from the
source into a bounded queue (e.g. 10K rows). When the queue is
full, the extractor *blocks* — the source sees backpressure.

**Pattern 2: credit-based.** The consumer tells the source "I can
accept N more rows." The source sends at most N. Kafka uses a
variant of this with `max.poll.records`.

**Pattern 3: pause / resume.** The consumer sends a "pause" signal
to the source (Kafka: `consumer.pause(partitions)`). The source
stops sending until "resume." This is the cleanest pattern.

The senior move: name the pattern. "I'd use bounded queues with
pause/resume to apply backpressure. The queue size is 2x the batch
size, so we always have one batch in flight and one queued."

---

## 7. The batching + parallelism pattern

The two compose: *batch within a partition*.

```
Topic with 12 partitions
  → 12 consumers, each reads its partition
    → each consumer buffers 1000 rows
      → when buffer is full, writes to destination
```

The math: 12 partitions × 1000 rows/batch = 12K rows in flight at
any time. If the source produces at 1M rows/sec, the destination
must sink at 1M rows/sec, or the buffers grow. The senior move:
size the parallelism to the peak throughput, and have an alert
on buffer depth.

---

## 8. The failure modes at scale

| Failure | Mitigation |
|---|---|
| Consumer crashes mid-batch | Idempotent writes (Lesson 23). |
| Slow destination | Backpressure: pause the source, alert. |
| Skewed partition (one key is hot) | Hash by `key % N`; accept skew; alert on lag. |
| Disk fills up (unbounded buffer) | Bounded buffer + alert on depth. |
| Worker OOM | Increase heap or decrease batch size. |

The senior move: name the skewed-partition failure mode. "If
partitioning is by `user_id` and one user produces 50% of events,
that partition is the bottleneck. I'd alert on per-partition lag
and add a salt (e.g. `user_id + bucket`) to spread the load."

---

## 9. The interview answer

> "For a 1M rows/sec source I'd batch in 1000-row chunks, run 12
> parallel consumers, and apply backpressure with bounded queues.
> The destination writes are idempotent on a `(source, id)` key, so
> a consumer crash doesn't duplicate data. The metric I watch is
> per-partition lag; if any partition is more than 30s behind, I
> page on-call. The hot path is the destination write — that's
> where I'd spend the deep-dive time."

That single paragraph covers: batching, parallelism, backpressure,
idempotency, monitoring, deep-dive choice. Senior answer in 30
seconds.

---

## Try it

Estimate the peak throughput of the most recent pipeline you've
worked on. How many rows/sec? How many partitions? How big is the
buffer? What's the per-partition lag? If any of those is "I don't
know," the pipeline is under-instrumented.
