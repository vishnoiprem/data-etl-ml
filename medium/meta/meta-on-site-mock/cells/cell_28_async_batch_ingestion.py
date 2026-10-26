"""
Cell 28: Async Batch Ingestion Pipeline — write-back queue, batch flush, backpressure

The interview question:
'You get 1M events/sec into your RAG ingestion pipeline. Embedding API rate limit
 is 10k RPM. How do you build the ingestion layer to never drop data, never
 duplicate, and backpressure when the consumer falls behind?'

L6 answer structure:
- Never call the embedding API inline with the request (block 200ms per chunk)
- Async write-back queue: producer -> buffer -> consumer pool
- Batch flush: 100 chunks/batch = 100x throughput, 100x cheaper
- Backpressure: bounded queue + 503 to producer when full
- Retry with exponential backoff: 1s, 2s, 4s, 8s, 16s, give up at 60s
- DLQ: poison messages get parked for human inspection
- Idempotency: (doc_id, chunk_hash, model_version) UNIQUE = free dedup
"""
import time
import random
import json
import hashlib
import threading
from queue import Queue, Empty
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Optional

# ════════════════════════════════════════════════════════════════
# THE NAIVE WAY (DON'T DO): inline embedding call
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("THE NAIVE WAY (DON'T DO): inline embedding call")
print("=" * 70)
print("""
def ingest_document(doc):
    chunks = chunker(doc)
    for chunk in chunks:
        embedding = openai.embed(chunk)   # 200ms API call, blocks thread
        qdrant.upsert(chunk, embedding)   # 50ms
    return 'ok'

Problems:
  - 200ms * 50 chunks = 10 seconds per doc
  - 100 concurrent docs = 1000 threads blocked
  - Rate limit: 10k RPM (OpenAI) vs 1M events/sec (your pipeline)
  - If API is down: 10 seconds of work lost, retry from scratch
  - No backpressure: every request gets accepted, then explodes
""")

# ════════════════════════════════════════════════════════════════
# THE L6 WAY: async write-back queue + batch flush
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("THE L6 WAY: async write-back queue + batch flush")
print("=" * 70)
print("""
ARCHITECTURE:

   HTTP request               async worker pool           Qdrant / ClickHouse
   ───────────                ────────────────            ──────────────────
       │                          │                            │
       ▼                          ▼                            │
  ┌─────────┐  enqueue    ┌─────────────────┐                  │
  │ Producer│────────────▶│  In-Mem Queue   │                  │
  │ (HTTP)  │  1ms ack    │  (bounded 10k)  │                  │
  └─────────┘             └─────────────────┘                  │
                                  │                            │
                                  │ batch of 100              │
                                  ▼                            │
                          ┌─────────────────┐                  │
                          │  Worker Thread  │                  │
                          │  (1 of 50)      │──────────────────┘
                          │  - embed batch  │   single bulk upsert
                          │  - flush        │   (100x faster)
                          └─────────────────┘

KEY INSIGHT: the HTTP request returns in 1ms with an event_id.
The expensive work (embedding, indexing) happens in the background.
Producer is decoupled from consumer.
""")

# ════════════════════════════════════════════════════════════════
# SIMULATION: the pipeline
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("SIMULATION: 100k events, naive vs L6 pipeline")
print("=" * 70)

@dataclass
class IngestEvent:
    event_id: str
    doc_id: str
    chunk_text: str
    chunk_hash: str
    model_version: str
    enqueued_at: float
    attempts: int = 0

class EmbeddingAPI:
    """Simulates OpenAI: 200ms per call, 10k RPM rate limit, 1% error rate."""
    def __init__(self):
        self.call_count = 0
        self.error_count = 0
        self.total_latency = 0.0
        self.rate_limit_lock = threading.Lock()
        self.minute_calls = 0
        self.minute_start = time.time()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch embed: 200ms for batch of N (amortized)."""
        # Rate limit check
        with self.rate_limit_lock:
            now = time.time()
            if now - self.minute_start > 60:
                self.minute_calls = 0
                self.minute_start = now
            if self.minute_calls + len(texts) > 10_000:
                raise Exception("Rate limit exceeded (10k RPM)")
            self.minute_calls += len(texts)

        # Simulate batch latency: 200ms + 1ms per item
        latency = 0.200 + 0.001 * len(texts)
        time.sleep(latency / 100)  # sped up for demo
        self.total_latency += latency

        # Simulate 1% error rate
        if random.random() < 0.01:
            self.error_count += 1
            raise Exception("API transient error")

        self.call_count += 1
        return [[random.random() for _ in range(8)] for _ in texts]  # 8-dim fake vec

class VectorDB:
    """Simulates Qdrant: bulk upsert is fast, single upsert is slow."""
    def __init__(self):
        self.upserted = []
        self.duplicates_skipped = 0
        # Idempotency: (doc_id, chunk_hash, model_version) -> vec
        self.idempotency_index = {}

    def bulk_upsert(self, events: List[IngestEvent], vectors: List[List[float]]):
        """Single bulk upsert = 100x faster than 100 individual upserts."""
        time.sleep(0.005)  # 5ms regardless of batch size (network + DB)
        for ev, vec in zip(events, vectors):
            key = (ev.doc_id, ev.chunk_hash, ev.model_version)
            if key in self.idempotency_index:
                self.duplicates_skipped += 1
                continue
            self.idempotency_index[key] = vec
            self.upserted.append((ev.event_id, ev.doc_id))

class AsyncIngestionPipeline:
    """The L6 pattern: bounded queue + worker pool + batch flush + backpressure."""

    def __init__(self, embedder, vdb, queue_size=10_000, batch_size=100,
                 num_workers=10, flush_interval_ms=100):
        self.queue = Queue(maxsize=queue_size)
        self.embedder = embedder
        self.vdb = vdb
        self.batch_size = batch_size
        self.flush_interval = flush_interval_ms / 1000
        self.num_workers = num_workers
        self.dlq = []
        self.metrics = defaultdict(int)
        self.workers_started = False

    def enqueue(self, event: IngestEvent) -> bool:
        """Non-blocking enqueue with backpressure."""
        try:
            self.queue.put_nowait(event)
            self.metrics['enqueued'] += 1
            return True
        except Exception:
            # Queue full: backpressure! Tell producer to slow down
            self.metrics['backpressure_503'] += 1
            return False

    def _worker(self):
        """Worker thread: batch, embed, flush, retry."""
        while True:
            batch = []
            try:
                # Block waiting for first item
                first = self.queue.get(timeout=1.0)
                batch.append(first)
            except Empty:
                if self.metrics.get('shutdown'):
                    return
                continue

            # Drain up to batch_size with timeout
            deadline = time.time() + self.flush_interval
            while len(batch) < self.batch_size and time.time() < deadline:
                try:
                    item = self.queue.get_nowait()
                    batch.append(item)
                except Empty:
                    time.sleep(0.005)
                    if time.time() > deadline:
                        break

            # Process batch with retry
            self._process_batch_with_retry(batch)

    def _process_batch_with_retry(self, batch: List[IngestEvent]):
        """Try to embed+upsert. Retry on failure with exponential backoff."""
        for attempt in range(5):
            try:
                vectors = self.embedder.embed_batch([e.chunk_text for e in batch])
                self.vdb.bulk_upsert(batch, vectors)
                self.metrics['flushed'] += len(batch)
                return
            except Exception as e:
                wait = 0.1 * (2 ** attempt)  # 0.1s, 0.2s, 0.4s, 0.8s, 1.6s
                if attempt == 4:
                    # Give up: park in DLQ
                    for ev in batch:
                        ev.attempts = attempt + 1
                        self.dlq.append(ev)
                    self.metrics['dlq'] += len(batch)
                    return
                time.sleep(wait / 100)  # sped up
                self.metrics['retries'] += 1

    def start(self):
        if self.workers_started:
            return
        self.workers_started = True
        self.workers = []
        for _ in range(self.num_workers):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            self.workers.append(t)

    def stop(self):
        self.metrics['shutdown'] = True
        for t in self.workers:
            t.join(timeout=2.0)

# Run simulation
print("\n--- Naive (inline, single-thread) ---")
api = EmbeddingAPI()
vdb_naive = VectorDB()
t0 = time.perf_counter()
# 200 events inline = 200 API calls
for i in range(200):
    ev = IngestEvent(
        event_id=f"ev_{i}", doc_id=f"doc_{i}",
        chunk_text=f"text_{i}", chunk_hash=f"hash_{i}",
        model_version="v1", enqueued_at=time.time()
    )
    try:
        vec = api.embed_batch([ev.chunk_text])[0]
        vdb_naive.bulk_upsert([ev], [vec])
    except Exception:
        pass
naive_time = time.perf_counter() - t0
naive_throughput = 200 / naive_time
print(f"  Time: {naive_time:.1f}s, throughput: {naive_throughput:.0f} events/sec")
print(f"  API calls: {api.call_count} (one per event)")

print("\n--- L6 (async, batched, 10 workers) ---")
api2 = EmbeddingAPI()
vdb_l6 = VectorDB()
pipeline = AsyncIngestionPipeline(api2, vdb_l6, queue_size=10_000,
                                   batch_size=100, num_workers=10, flush_interval_ms=50)
pipeline.start()

# 10k events (50x more)
t0 = time.perf_counter()
for i in range(10_000):
    ev = IngestEvent(
        event_id=f"ev_{i}", doc_id=f"doc_{i // 50}",  # 50 chunks per doc
        chunk_text=f"text_{i}", chunk_hash=f"hash_{i}",
        model_version="v1", enqueued_at=time.time()
    )
    pipeline.enqueue(ev)

# Wait for queue to drain
while not pipeline.queue.empty():
    time.sleep(0.1)
time.sleep(1.0)  # final flush
l6_time = time.perf_counter() - t0
pipeline.stop()
l6_throughput = 10_000 / l6_time
print(f"  Time: {l6_time:.1f}s, throughput: {l6_throughput:.0f} events/sec")
print(f"  API calls: {api2.call_count} (batched 100x)")
print(f"  Metrics: {dict(pipeline.metrics)}")
print(f"  DLQ depth: {len(pipeline.dlq)} (poison messages)")

print(f"\n--- COMPARISON ---")
print(f"  Naive: {naive_throughput:>8.0f} events/sec, {api.call_count} API calls")
print(f"  L6:    {l6_throughput:>8.0f} events/sec, {api2.call_count} API calls")
print(f"  Speedup: {l6_throughput / naive_throughput:.0f}x")
print(f"  API call reduction: {api.call_count / max(1, api2.call_count):.0f}x")

# ════════════════════════════════════════════════════════════════
# THE 5 CRITICAL CONCEPTS
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("THE 5 CRITICAL CONCEPTS (the L6 whiteboard)")
print("=" * 70)
print("""
1. BACKPRESSURE (the most-asked concept)
   Bounded queue (10k items). When full, return HTTP 503 to producer.
   Producer backs off (exponential retry) and retries.
   This is the ONLY way to prevent OOM when consumer is slow.
   Without backpressure: queue grows unbounded, OOM, total outage.
   With backpressure: producer slows down, system stays stable.

2. BATCH FLUSH (the throughput multiplier)
   100 chunks per batch = 1 API call instead of 100.
   - 100x fewer API calls (cost!)
   - 100x lower per-call overhead
   - 100x fewer Qdrant round-trips
   - 100x better network utilization
   Trade-off: latency goes from 50ms to 50ms + flush_interval (100ms typical).
   Total: 150ms vs 50ms, 3x worse latency, 100x better throughput.
   For ingestion (not serving), throughput wins.

3. IDEMPOTENCY (the dedup mechanism)
   Key: (doc_id, chunk_hash, model_version) UNIQUE in vector DB.
   Why 3-tuple: doc_id alone doesn't catch re-chunking.
                chunk_hash catches re-runs of the same chunk.
                model_version catches model upgrade replays.
   Implementation: ON CONFLICT DO NOTHING in Postgres / upsert with check in Qdrant.
   This makes at-least-once delivery safe (no duplicates ever).

4. RETRY WITH EXPONENTIAL BACKOFF (the reliability pattern)
   1s, 2s, 4s, 8s, 16s, give up at 60s. Add jitter (random 0-100ms) to avoid thundering herd.
   Max attempts: 5 (don't retry forever).
   Failed after max: send to DLQ, page on-call.
   Idempotency key ensures retries are safe.

5. DEAD LETTER QUEUE (the safety net)
   Park poison messages for human inspection.
   Alert when DLQ depth > 100 (something is structurally wrong).
   Replay button in admin tool: drain DLQ to main queue after fix.
   Common cause: schema change broke older messages.

THE 5 NEVER-DOs:
  - Never block the HTTP request on the embedding API (200ms is too slow)
  - Never use unbounded queue (OOM is guaranteed)
  - Never retry forever (poison messages block the queue)
  - Never skip idempotency (at-least-once = duplicates without dedup)
  - Never use enable.auto.commit in Kafka (the most common production bug)
""")

# ════════════════════════════════════════════════════════════════
# THE L6 MATH: capacity planning
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("THE L6 MATH: capacity planning")
print("=" * 70)
print("""
Inputs:
  - 1M events/sec peak
  - Embedding API: 10k RPM, 200ms per batch of 100
  - Qdrant: 5k upserts/sec per node, 3 nodes
  - Worker: embed batch of 100 in 200ms = 500 batches/sec/worker

Number of workers needed:
  Peak: 1M / 100 = 10k batches/sec
  Per worker: 500 batches/sec (1 batch per 2ms with batching)
  Workers needed: 10k / 500 = 20 workers
  With 2x headroom: 40 workers

Qdrant shards needed:
  Peak: 1M / (3 nodes * 5k upserts/sec) = 67 nodes? No.
  Actually: 1M events/sec with batch of 100 = 10k bulk upserts/sec
  Per node: 5k upserts/sec, so 2 nodes minimum, 6 with 3x headroom.
  3 nodes is fine if your batches are smaller (50 instead of 100).

Queue size:
  At 1M events/sec, queue can fill in 10ms if consumer dies.
  10k items = 10ms buffer. Want 60s buffer = 60M items.
  That's 60M * 1KB = 60GB. Too much in memory.
  Solution: use Kafka as the queue (persistent, 1B+ items, no OOM).
""")

# ════════════════════════════════════════════════════════════════
# L6 ANSWER
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("L6 ANSWER (when they ask 'how do you build the ingestion layer?')")
print("=" * 70)
print("""
Q: "1M events/sec, 10k RPM embedding API. How do you build the ingestion
    layer to never drop or duplicate?"

A: "5 components in order:

1. ASYNC WRITE-BACK QUEUE
   HTTP request enqueues an event and returns 202 Accepted in 1ms.
   The expensive work (embedding, indexing) happens in the background.
   Decouples producer from consumer.

2. BOUNDED QUEUE + BACKPRESSURE
   Queue size = 10k items. When full, return HTTP 503 to producer.
   Producer backs off (exponential retry). This prevents OOM when
   the consumer is slow. Unbounded queue = OOM = outage.

3. BATCH FLUSH (100x throughput)
   Workers accumulate 100 events OR 100ms, whichever first.
   Single API call for 100 chunks. 100x fewer calls.
   100x lower overhead. 100x better network utilization.
   Trade-off: 100ms added latency. For ingestion, throughput wins.

4. RETRY WITH EXPONENTIAL BACKOFF
   1s, 2s, 4s, 8s, 16s, give up at 60s. Add jitter.
   Max 5 attempts. After that, send to DLQ + alert on-call.
   Idempotency key (doc_id, chunk_hash, model_version) UNIQUE
   ensures retries are safe.

5. DEAD LETTER QUEUE
   Poison messages get parked for human inspection.
   Alert when DLQ depth > 100. Replay button in admin tool.

THE CARDINAL SIN: inline embedding API call in the request path.
  - 200ms per chunk * 50 chunks = 10s per doc
  - 100 concurrent docs = 1000 threads blocked
  - Rate limit: 10k RPM vs 1M events/sec = system collapses
  - No backpressure, no retry, no DLQ
  - If API is down: 10s of work lost

THE L6 MATH:
  1M events/sec / 100 batch = 10k batches/sec
  500 batches/sec/worker = 20 workers, 40 with 2x headroom
  Queue: Kafka (persistent, no OOM) for production
  Qdrant: 3-6 nodes, 5k upserts/sec each

The L6 default: NEVER block the request on the embedding API.
Always async, always batched, always idempotent, always with DLQ.
""")
