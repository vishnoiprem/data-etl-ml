# System Design Primer for Meta L6 / Google L5
## What every full-stack engineer must know in 60 minutes

This primer is the minimum vocabulary and framework you need to survive a 45-minute system design round. It does not replace Hello Interview, Alex Xu, or *DDIA*, but it gives you the scaffolding so those resources make sense.

---

## 0. The framework every interviewer expects

When the interviewer says "Design X", they expect this structure:

1. **Clarify requirements (2–3 min).** Users, scale, core features. Write them down.
2. **Estimate scale (2 min).** QPS, storage, bandwidth. Round numbers.
3. **High-level design (5 min).** Boxes and arrows. Client → API → services → storage.
4. **Deep dive (20 min).** Pick 1–2 bottlenecks. Schema, indexing, caching, sharding.
5. **Wrap up (5 min).** Monitoring, failure modes, future work.

**Always say "let me clarify the requirements" first.** Interviewers will not start the clock until you do.

---

## 1. Capacity estimation (the cheat sheet)

When you need a number, use these rules of thumb:

| Quantity | Rule |
|---|---|
| Daily active users (DAU) | 10–30% of monthly |
| Reads : Writes | Most apps 100:1, social 10:1, chat 1:1 |
| QPS from DAU | DAU × actions_per_day / 86_400 / 2 (peak ÷ 2) |
| Storage per record | 1 KB for text, 10 KB for media |
| Bandwidth per request | ~10 KB average JSON |

### Worked example: "Design a URL shortener"
- 100M URLs shortened per month
- 100M / 30 / 86_400 ≈ 40 QPS average
- Peak ≈ 100 QPS
- Storage: 100M × 500 bytes = 50 GB
- Read:write = 10:1 → 1000 read QPS peak

### Worked example: "Design a RAG trace viewer" (this project)
- 10k traces/day, 1000 engineers
- 100k QPS at peak
- Storage: 10k × 5 KB = 50 MB/day = 18 GB/year
- Bandwidth: 100k × 5 KB = 500 MB/s

**The numbers don't have to be exact. They have to be in the right order of magnitude.**

---

## 2. The 12 boxes every design uses

| Box | What it does | When to use |
|---|---|---|
| Client | Browser, mobile | Always |
| CDN | Cache static assets | Static images, JS bundles |
| Load balancer | Distribute traffic | > 1 backend server |
| API server | HTTP → JSON | Always |
| Cache | Hot data in memory | Read-heavy, slow DB |
| Queue | Async work | Emails, video processing |
| Worker | Consume queue | Heavy CPU work |
| Database | Source of truth | Always |
| Search index | Full-text / vector | Search, ranking |
| Object store | Blobs (S3) | Images, videos, models |
| Pub/sub | Fanout | Real-time updates |
| Analytics | Logs/metrics pipeline | Always |

You won't use all 12. Most designs use 5–7.

---

## 3. The 6 things every interviewer asks

### Q1 — "How do you scale the database?"
- **Vertical:** bigger machine. Stops working around 10 TB.
- **Read replicas:** easy, eventually consistent.
- **Sharding:** split rows by `shard_key`. Hard to do well.
- **Denormalization:** duplicate data to avoid joins.

For Meta L6: know sharding strategies (hash, range, geo), rebalancing, and the join problem.

### Q2 — "How do you handle cache invalidation?"
- **TTL:** simple, stale.
- **Write-through:** cache updated on every write. Consistent, slow.
- **Cache-aside (lazy):** app reads from cache, falls back to DB, writes back. Industry default.
- **Write-behind:** write to cache, async to DB. Fast, lossy.

**The two hard things in CS:** cache invalidation, naming things, off-by-one errors.

### Q3 — "How do you handle failures?"
- **Retries with exponential backoff + jitter.**
- **Circuit breaker:** stop calling a failing service.
- **Idempotency keys:** retries don't double-charge.
- **Bulkhead:** isolate pools so one slow dependency doesn't take down the system.
- **Dead letter queue:** store failed messages for later.

### Q4 — "How do you make it consistent?"
- **Strong:** every read sees the latest write. Slow.
- **Eventual:** reads see stale data briefly. Fast.
- **Causal:** related events are ordered.

For L6: know the difference between "read-your-writes", "monotonic reads", and "linearizability".

### Q5 — "How do you monitor it?"
- **The four golden signals:** latency, traffic, errors, saturation.
- **Logs:** structured JSON with request id.
- **Metrics:** counters, gauges, histograms.
- **Traces:** distributed tracing (OpenTelemetry, Jaeger).
- **P50 / P95 / P99:** percentiles, not averages.

### Q6 — "What are the tradeoffs?"
**Every choice has a tradeoff. If you say "we use X" without saying "instead of Y because Z", you lose points.**

Examples:
- "We use Postgres instead of MongoDB because our data is relational and we need ACID."
- "We use Redis instead of Memcached because we need pub/sub and sorted sets."
- "We use eventual consistency instead of strong because the user can tolerate seeing a 1-second-old like count."

---

## 4. The 5 designs you must know cold

| Design | Key concepts |
|---|---|
| **URL shortener** | Base62, hashing, caching, sharding |
| **Twitter timeline** | Fanout-on-write vs fanout-on-read, cache, queue |
| **Rate limiter** | Token bucket, sliding window, Redis Lua |
| **Chat (WhatsApp)** | WebSockets, presence, message ordering, push notifications |
| **RAG system** | Vector DB, embeddings, chunking, retrieval, evaluation |

You should be able to draw each in 10 minutes.

---

## 5. Sharding strategies

### Hash sharding
`shard_id = hash(key) % N`
- Pro: even distribution.
- Con: rebalancing is expensive (all keys move when N changes).

### Consistent hashing
Keys and nodes are placed on a ring. Adding a node only moves ~1/N of keys.
- Pro: cheap rebalancing.
- Con: harder to reason about.

### Range sharding
`shard_id = key ∈ [a, b)`
- Pro: range queries are fast.
- Con: hotspots (today's date always hits the latest shard).

### Geo sharding
`shard_id = user's region`
- Pro: low latency.
- Con: cross-region queries are slow.

---

## 6. CAP theorem

You can have at most 2 of:
- **C**onsistency (every read sees the latest write)
- **A**vailability (every request gets a response)
- **P**artition tolerance (works despite network failures)

Since P is required in distributed systems, you choose **CP** (e.g., HBase) or **AP** (e.g., Cassandra).

For L6: know which databases make which trade and why.

---

## 7. Common pitfalls

1. **"We use NoSQL because it's faster."** No. SQL is fast when indexed. NoSQL is for specific shapes.
2. **"We don't need caching."** You do. Always.
3. **"We can just add more servers."** State (DB, sessions, uploads) is the bottleneck, not stateless servers.
4. **"The system is fully consistent."** Prove it. Most aren't.
5. **"We have a microservices architecture."** Why? Each service is a network call. Monoliths scale further than you think.
6. **"We'll use Kafka for everything."** Do you need ordering? Replay? If not, you don't need Kafka.

---

## 8. The 5-min "design a RAG system" walkthrough

1. **Requirements:** 1M docs, 100k engineers, 1k QPS, sub-2-second end-to-end.
2. **Storage:** S3 for raw docs, vector DB (Pinecone / pgvector) for embeddings, Postgres for metadata.
3. **Ingestion:** chunker → embedder (OpenAI / open source) → upsert to vector DB.
4. **Query:** user query → embedder → top-k vector search → reranker → LLM with retrieved chunks.
5. **Cache:** cache embeddings of common queries in Redis.
6. **Eval:** offline evals (Ragas, Braintrust), online evals (thumbs up/down — this project!).
7. **Failure modes:** vector DB down → fall back to BM25. LLM down → return chunks only.
8. **Cost:** embedding $0.02/1M tokens, GPT-4 $10/1M output tokens. 1k QPS × 1k tokens = $10k/day.

This is exactly the system you're building the **trace viewer** for. The viewer is the **observability** layer; the **retrieval + generation** is upstream.

---

## 9. Resources (in order of value)

| Resource | Time | Why |
|---|---|---|
| *System Design Interview* (Alex Xu) Vol 1+2 | 2 weeks | 20+ walkthroughs |
| *Designing Data-Intensive Applications* (Kleppmann) | 4 weeks | The deep book |
| Hello Interview (YouTube) | ongoing | 50+ free walkthroughs |
| System Design Primer (GitHub, donnemartin) | 3 days | Free, community |
| Mock interviews (pramp.com, interviewing.io) | weekly | Practice out loud |

---

## 10. The single most important rule

**Always state the tradeoff.** "We use X instead of Y because Z."

If you do nothing else, do this. It's the difference between L4 and L6.
