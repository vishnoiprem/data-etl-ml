# LOOP 4: Real-time + Streaming + Low Latency

**Theme:** Flink 5-sec freshness + backpressure
**Total Duration:** 3 hours 15 min
**Difficulty:** Hard (streaming is interview-killer)

---

## Architecture Diagram (Master)

```
┌────────────────────────────────────────────────────────────────────┐
│         REAL-TIME RAG - 5-SEC FRESHNESS, 1M events/sec             │
└────────────────────────────────────────────────────────────────────┘

INGEST (CDC)                    PROCESS (FLINK)
─────────────                   ───────────────

┌────────────┐  WAL    ┌──────────┐    ┌─────────────────────┐
│ Postgres   │────────▶│ Debezium │───▶│ Kafka (1000 parts)  │
│ primary    │         │ CDC      │    │ commit_event topic  │
└────────────┘         └──────────┘    └──────────┬──────────┘
                                                 │
                                                 ▼
┌────────────┐                          ┌─────────────────────┐
│ Other DBs  │─────────────────────────▶│ Flink Job           │
│ MySQL,etc  │                          │ - watermark 5 sec   │
└────────────┘                          │ - at-least-once     │
                                        │ - backpressure      │
                                        │ - checkpoint 60s    │
                                        └──────────┬──────────┘
                                                   │
                                ┌──────────────────┼──────────────────┐
                                ▼                  ▼                  ▼
                        ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
                        │ Embed API    │   │ Embed API    │   │ Embed API    │
                        │ (rate-limit  │   │ (with back-  │   │ (retry exp.  │
                        │  5k RPS)     │   │  pressure)   │   │  backoff)    │
                        └──────┬───────┘   └──────┬───────┘   └──────┬───────┘
                               │                  │                  │
                               └──────────────────┼──────────────────┘
                                                  ▼
                                        ┌─────────────────────┐
                                        │ Qdrant (20 shards)  │
                                        │ 50M docs / shard    │
                                        └─────────────────────┘

QUERY PATH
──────────

User Query ──▶ Embed (50ms) ──▶ Qdrant search (150ms)
                                        │
                                        ▼
                              Top 8 chunks (200ms)
                                        │
                                        ▼
                              LLM answer (200ms) ──▶ User
                                        │
                                  Total: ~450ms p95
```

---

## Greet (15 min)

### Q1: What is hardest part of real-time vs batch?

**L6 Answer (60 sec):**

> "Three things make real-time fundamentally harder than batch:
>
> 1. **Backpressure** — if downstream is slow, upstream blocks. Batch just queues to disk. In Flink, this means checkpoint barriers stall, lag accumulates.
>
> 2. **Exactly-once semantics** — duplicate events corrupt state (e.g., double-charge). Batch is idempotent by nature because you re-read the whole file.
>
> 3. **Debugging** — 1M events/sec, you can't sample. You need distributed tracing per event with trace_id propagated through Kafka → Flink → sink.
>
> Real-time costs ~10x more than batch. It's only worth it when the SLA demands it (e.g., 'new doc must be searchable within 5 minutes')."

**L6 Keywords:** backpressure, idempotent sink, 10x cost, SLA-driven, trace_id.

---

### Q2: How do you handle backpressure in streaming?

**L6 Answer (60 sec):**

> "Three mechanisms, in order of preference:
>
> 1. **Bounded buffer + drop oldest** — if queue is full, drop the oldest event. Good for telemetry where losing 0.1% is OK.
>
> 2. **Flow control** — Kafka consumer with `fetch.max.bytes=1MB` and `fetch.min.bytes` to tune fetch size for throughput vs latency. `max.poll.interval.ms` bounds liveness; `max.in.flight.requests.per.connection` with `enable.idempotence=true` on the producer side throttles in-flight writes when the broker signals pressure.
>
> 3. **Adaptive concurrency** — Flink checkpointing, if checkpoint duration > 60s, reduce parallelism. Auto-scales back when load drops.
>
> For my APEX-RAG real-time path, I used #2 + #3. Buffer 10k events, then start applying backpressure to the Kafka consumer."

**L6 Keywords:** bounded buffer, drop oldest, flow control, adaptive concurrency, Kafka.

---

## AI-Native DE Full Stack (60 min)

### Q1 Data Model (15 min)

```
┌──────────────────────────────────────────────────────────────┐
│        REAL-TIME TRACES - 1-SEC GRANULARITY                  │
└──────────────────────────────────────────────────────────────┘

traces_realtime                     flink_checkpoints
┌────────────────────────┐          ┌──────────────────────────┐
│ trace_id        PK     │          │ checkpoint_id    PK      │
│ user_id                │          │ job_id                   │
│ query            TEXT  │          │ state_size_mb   BIGINT   │
│ embedding_model_ver    │          │ duration_ms     INT      │
│ shard_id          INT  │          │ status  completed/failed │
│ prompt_version    STR  │          │ created_at  TIMESTAMP    │
│ latency_ms        INT  │          └──────────────────────────┘
│ timestamp  TIMESTAMP   │
│ event_time  TIMESTAMP  │ ◀── WATERMARK (Flink)
│ ingestion_time        │
│ WATERMARK FOR ts      │
└────────────────────────┘
  PARTITIONED BY (DATE(timestamp), HOUR(timestamp))
```

**SQL schema:**

```sql
CREATE TABLE traces_realtime (
  trace_id              BIGINT PRIMARY KEY,
  user_id               BIGINT,
  query                 STRING,
  embedding_model_ver   STRING,
  shard_id              INT,
  prompt_version        STRING,
  latency_ms            INT,
  `timestamp`           TIMESTAMP,
  event_time            TIMESTAMP,
  ingestion_time        TIMESTAMP,
  WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
) PARTITIONED BY (DATE(`timestamp`), HOUR(`timestamp`));

CREATE TABLE flink_checkpoints (
  checkpoint_id  BIGINT PRIMARY KEY,
  job_id         STRING,
  state_size_mb  BIGINT,
  duration_ms    INT,
  status         STRING,
  created_at     TIMESTAMP
);
```

**Why WATERMARK:** handles late-arriving events up to 5 seconds late. After watermark passes, late events are dropped (or sent to side output).

---

### Q2 Pipeline (15 min) - Flink CDC with Backpressure

```
┌─────────────────────────────────────────────────────────────────┐
│         FLINK CDC PIPELINE - BACKPRESSURE HANDLING              │
└─────────────────────────────────────────────────────────────────┘

Postgres WAL ──▶ Debezium ──▶ Kafka (1000 partitions)
                                      │
                                      ▼
                            ┌──────────────────────┐
                            │ Flink Source         │
                            │ - 100 parallelism     │
                            │ - watermark 5 sec     │
                            │ - at-least-once       │
                            │   (idempotent sink)   │
                            └──────────┬───────────┘
                                       │
                                       ▼
                            ┌──────────────────────┐
                            │ Embedding Operator   │
                            │ - batch 100 events   │
                            │ - semaphore 50       │
                            │ - rate-limit 5k RPS  │
                            └──────────┬───────────┘
                                       │ 429?
                                       ▼
                            ┌──────────────────────┐
                            │ Backpressure Handler │
                            │ - sleep + retry      │
                            │ - exponential backoff│
                            │ - max 3 retries      │
                            └──────────┬───────────┘
                                       │
                                       ▼
                            ┌──────────────────────┐
                            │ Qdrant Sink          │
                            │ - async write        │
                            │ - checkpoint aligned │
                            └──────────────────────┘
```

**Pipeline code (PyFlink):**

```python
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.common import WatermarkStrategy, Duration

env = StreamExecutionEnvironment.get_execution_environment()
env.enable_checkpointing(60_000)  # checkpoint every 60s
env.get_checkpoint_config().set_min_pause_between_checkpoints(30_000)

# Source: Kafka — at-least-once with idempotent sink (Qdrant upsert by doc_id)
# Note: true EOS in Flink requires KafkaSource with offset+partition metadata;
# set_value_only_deserializer throws that away, so we don't claim exactly-once here.
kafka_source = KafkaSource.builder() \
    .set_bootstrap_servers("kafka:9092") \
    .set_group_id("rag_ingest") \
    .set_topics("commit_event") \
    .set_starting_offsets(KafkaSourceOffsetsInitializer.committed_offsets()) \
    .set_boundedness(Boundedness.CONTINUOUS_UNBOUNDED) \
    .set_value_only_deserializer(SimpleStringSchema()) \
    .build()

# Watermark: 5-second out-of-order tolerance
watermark_strategy = WatermarkStrategy \
    .for_bounded_out_of_orderness(Duration.of_seconds(5)) \
    .with_timestamp_assigner(lambda event, ts: event.commit_ts)

# Process
stream = env.from_source(kafka_source, watermark_strategy, "Kafka Source")
    .key_by(lambda e: e.shard_id) \
    .map(embed_with_rate_limit) \
    .add_sink(qdrant_sink)

env.execute("rag_realtime_ingest")
```

**Backpressure handling (the rate-limit-aware embedder):**

```python
import time
from threading import Semaphore
from openai import OpenAI

# Layered defense:
# - api_semaphore caps concurrent in-flight requests (cost control: at most 50 parallel calls).
# - min_interval enforces the upstream 5k RPS QPS contract regardless of concurrency.
api_semaphore = Semaphore(50)
last_call_time = [0.0]
min_interval = 1.0 / 5000  # 0.0002 sec between calls

client = OpenAI()


def rate_limited_embed(text: str, max_retries: int = 3) -> list:
    for attempt in range(max_retries):
        try:
            with api_semaphore:
                # Enforce minimum interval between calls (QPS contract)
                now = time.time()
                elapsed = now - last_call_time[0]
                if elapsed < min_interval:
                    time.sleep(min_interval - elapsed)
                last_call_time[0] = time.time()

                response = client.embeddings.create(
                    model="text-embedding-3-large",
                    input=text,
                )
                return response.data[0].embedding

        except openai.RateLimitError:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # 1s, 2s, 4s
```

---

### Q3 SQL (15 min) - p95 Latency Spike Detection

```sql
-- 1-min tumbling window, p95 latency, alert if > 600ms
SELECT
  TUMBLE_START(event_time, INTERVAL '1' MINUTE) AS window_start,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) AS p95_latency,
  PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY latency_ms) AS p50_latency,
  PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY latency_ms) AS p99_latency,
  COUNT(*)                                          AS query_count,
  COUNT(DISTINCT shard_id)                          AS active_shards
FROM traces_realtime
WHERE event_time > NOW() - INTERVAL '1' HOUR
GROUP BY TUMBLE(event_time, INTERVAL '1' MINUTE)
HAVING PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) > 600
ORDER BY window_start DESC;
```

**Output:**
| window_start         | p95_latency | p50 | p99 | query_count | active_shards |
|----------------------|-------------|-----|-----|-------------|---------------|
| 2026-10-18 14:32:00  | 720ms       | 380 | 950 | 12,500      | 18/20         |
| 2026-10-18 14:28:00  | 680ms       | 360 | 880 | 11,800      | 20/20         |

**Alert rule:** p95 > 600ms for 3 consecutive 1-min windows → page oncall.

---

### Q4 Coding (15 min) - Rate Limiter + Flink Watermark

```python
import time
from collections import deque
from typing import Optional


class TokenBucketRateLimiter:
    """
    Token bucket: 5000 tokens/sec, burst capacity 10000.
    Used to limit embedding API calls to 5k RPS.
    """
    def __init__(self, rate: int = 5000, capacity: int = 10000):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.monotonic()

    def acquire(self, tokens: int = 1, blocking: bool = True) -> bool:
        while True:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_refill = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            if not blocking:
                return False

            # Sleep until enough tokens available
            sleep_time = (tokens - self.tokens) / self.rate
            time.sleep(sleep_time)


def retry_with_exponential_backoff(fn, max_retries: int = 3, base_delay: float = 1.0):
    """Retry fn() with exponential backoff: 1s, 2s, 4s."""
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            if "rate limit" in str(e).lower() or "429" in str(e):
                time.sleep(base_delay * (2 ** attempt))
            else:
                raise


# Flink Watermark (Java-style pseudocode)
"""
DataStream<Event> stream = env
    .addSource(kafkaSource)
    .assignTimestampsAndWatermarks(
        WatermarkStrategy
            .<Event>forBoundedOutOfOrderness(Duration.ofSeconds(5))
            .withTimestampAssigner((event, ts) -> event.getCommitTimestamp())
    )
    .keyBy(Event::getShardId)
    .window(TumblingEventTimeWindows.of(Time.minutes(1)))
    .aggregate(new LatencyAggregator());
"""
```

---

## Sr Tech Design (60 min) - Real-time Incident Search

```
┌────────────────────────────────────────────────────────────────────┐
│      REAL-TIME INCIDENT SEARCH - 1B LOGS, <500ms                    │
└────────────────────────────────────────────────────────────────────┘

INGEST PATH
───────────

App logs ──▶ Fluent Bit ──▶ Kafka (1000 partitions) ──▶ Flink
                                                              │
                                                              ├──▶ Elasticsearch (recent 7d, hot)
                                                              ├──▶ ClickHouse (90d, time-travel)
                                                              └──▶ Qdrant (semantic search)

QUERY PATH (p95 < 500ms)
────────────────────────

"Find errors in payment service after 3pm"
        │
        ▼
   Embed query (50ms)
        │
        ▼
   ┌─────────────────────────────────────┐
   │ Parallel search (max of 3):         │
   │  - ES keyword (180ms)               │
   │  - Qdrant semantic (150ms)          │
   │  - ClickHouse time-travel (180ms)   │
   └────────────────┬────────────────────┘
                    │ Top 50 each
                    ▼
            ┌──────────────┐
            │ Dedup + Merge│ (40ms)
            └──────┬───────┘
                   │ Top 30
                   ▼
            ┌──────────────┐
            │ Cohere Rerank│ (50ms)
            └──────┬───────┘
                   │ Top 10
                   ▼
            ┌──────────────────────────────────┐
            │ LLM with evidence_json           │
            │ (skipped if pure keyword match)  │ (200ms)
            └──────────────┬───────────────────┘
                           │
                           ▼
                   Total: ~450ms p95
                   (30ms embed + 200ms search + 50ms rerank + 200ms LLM)
                   Grounded to log line + trace ID + doc chunk
```

**Key design decisions:**

1. **Three storage backends** for different needs:
   - **ES** for hot recent logs (last 7d), fast keyword search
   - **ClickHouse** for time-travel (any point in 90d), columnar
   - **Qdrant** for semantic ("weird error pattern")

2. **Parallel fan-out** then merge — single search would be 600ms, parallel is 200ms (max of 3)

3. **Skip LLM** for simple keyword matches — pure log search doesn't need explanation

4. **Grounded generation** with `evidence_json` containing log line + trace ID + doc chunk

5. **1M logs/sec ingest** = 86B/day. 1000 Kafka partitions, 100 Flink parallelism, batch 1000 per write.

---

## Sr Ownership (30 min)

### Q1: Streaming job lagged 2 hours — how did you own?

**L6 STAR:**

**S:** Flink job lag hit 2 hours, alerting fired. 1M events queued, downstream Qdrant slow.

**T:** Restore freshness, root cause, prevent recurrence.

**A:**
1. **Immediate:** Restarted Flink with parallelism 20→100, caught up in 30 min
2. **Root cause:** One Qdrant shard (shard 7) was slow, backpressure cascaded
3. **Fix:** Per-shard health check, auto-isolate slow shard, route to hot spare
4. **Prevent:** Lag alert > 30 min page oncall, parallel backfill job, runbook with 4 scenarios

**R:** Lag 2h → 5min within 1 hour. Runbook used 4 times since. MTTR 2h → 30min.

---

### Q2: Time you chose freshness vs cost

**L6 STAR:**

**S:** PM wanted 1-second freshness for 100M docs. Cost estimate: $130k/month.

**T:** Decide based on actual use case, not PM request.

**A:**
1. Built cost model: 1M events/sec × 30 days = $130k/month
2. Showed PM: 95% of queries don't need 1-sec, 24-hr batch covers it
3. Proposed: batch v1 (24h, $12k/month) + premium tier Flink CDC (5-sec, 1% users)
4. PM agreed, shipped

**R:** Saved $118k/year. Premium tier grew 5x in 6 months (real revenue). PM thanked me later — there wasn't a business case to justify 10x cost for v1.

**Lesson:** data > opinion, even with PMs.

---

## Full Stack (60 min) - Real-time Latency Dashboard

```tsx
import { useEffect, useState } from "react";

const RealTimeLatencyDashboard = () => {
  const [p95, setP95] = useState(0);
  const [p50, setP50] = useState(0);
  const [p99, setP99] = useState(0);
  const [shards, setShards] = useState([]);
  const [paused, setPaused] = useState(false);
  const [alert, setAlert] = useState(null);

  useEffect(() => {
    const ws = new WebSocket("wss://api/latency-stream");
    ws.onmessage = (event) => {
      if (paused) return;
      const data = JSON.parse(event.data);

      setP95(data.p95);
      setP50(data.p50);
      setP99(data.p99);
      setShards(data.shards);

      // Alert if hot shard or p95 spike
      const hotShards = data.shards.filter(s => s.docs > 12_000_000);
      if (data.p95 > 600 || hotShards.length > 0) {
        setAlert({
          type: data.p95 > 600 ? "p95" : "shard",
          message: data.p95 > 600
            ? `p95 spike: ${data.p95}ms`
            : `Hot shard: ${hotShards[0].id} has ${hotShards[0].docs.toLocaleString()} docs`
        });
      } else {
        setAlert(null);
      }
    };
    return () => ws.close();
  }, [paused]);

  const maxDocs = Math.max(...shards.map(s => s.docs), 1);

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header with controls */}
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Real-time Latency</h1>
        <button
          onClick={() => setPaused(!paused)}
          className={`px-4 py-2 rounded ${paused ? "bg-green-500" : "bg-yellow-500"}`}
        >
          {paused ? "▶ Resume" : "⏸ Pause"}
        </button>
      </div>

      {/* Alert banner */}
      {alert && (
        <div className={`p-3 mb-4 rounded ${alert.type === "p95" ? "bg-red-100" : "bg-orange-100"}`}>
          ⚠ {alert.message}
        </div>
      )}

      {/* Latency metrics */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <MetricCard label="p50" value={p50} unit="ms" color="green" />
        <MetricCard label="p95" value={p95} unit="ms" color={p95 > 600 ? "red" : "blue"} />
        <MetricCard label="p99" value={p99} unit="ms" color="orange" />
      </div>

      {/* Shard skew bar chart */}
      <h2 className="text-lg font-semibold mb-2">Shard Distribution ({shards.length} shards)</h2>
      <div className="space-y-1">
        {shards.map(s => (
          <div key={s.id} className="flex items-center gap-2">
            <span className="w-16 text-sm">shard {s.id}</span>
            <div className="flex-1 bg-gray-200 rounded h-6 relative">
              <div
                className={`h-full rounded ${s.docs > 12_000_000 ? "bg-red-500" : "bg-blue-500"}`}
                style={{ width: `${(s.docs / maxDocs) * 100}%` }}
              />
            </div>
            <span className={`w-24 text-right text-sm ${s.docs > 12_000_000 ? "text-red-600 font-bold" : ""}`}>
              {s.docs.toLocaleString()} docs
            </span>
          </div>
        ))}
      </div>

      <p className="text-xs text-gray-500 mt-4">
        Updates every 5 seconds via WebSocket. Red = hot shard &gt; 12M docs.
      </p>
    </div>
  );
};

const MetricCard = ({ label, value, unit, color }) => (
  <div className={`p-4 rounded border-l-4 border-${color}-500 bg-${color}-50`}>
    <div className="text-sm text-gray-600">{label}</div>
    <div className="text-3xl font-bold">{value}{unit}</div>
  </div>
);
```

---

## Day 2 Checkpoint

Before moving on, can you:
- [ ] Explain **3 backpressure mechanisms** (buffer, flow control, adaptive)?
- [ ] Compute **p95 latency SQL** with `TUMBLE` + `PERCENTILE_CONT`?
- [ ] Code a **token bucket rate limiter** in Python?
- [ ] Draw **real-time incident search** with 3 storage backends?
- [ ] State the **freshness vs cost tradeoff** with $130k example?

If yes to all 5, you're ready for Loop 5. If not, re-read the relevant section.
