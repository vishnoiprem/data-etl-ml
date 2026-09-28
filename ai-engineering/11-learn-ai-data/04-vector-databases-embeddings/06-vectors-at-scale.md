# Lesson 6 — Vectors at Scale

> **Type:** Article · Module 4 · Vector Databases & Embeddings
> Sharding, replication, quantisation, freshness at billion-scale, and the cost math.

---

## The scaling curve

```
   <1M vectors     — easy, single-node HNSW, pgvector, Chroma
   1M–10M          — needs prod-grade engine: Qdrant, Weaviate, Pinecone
   10M–100M        — sharded, replicas, quantisation kicks in
   100M–1B         — serious engineering: IVF_PQ or HNSW+PQ, careful sharding
   1B+             — Milvus, Vespa, or major Pinecone spend
```

Each tier adds operational complexity and cost. **Pick the smallest engine that meets your needs today, with a clear migration path.**

---

## The memory math

```
   1M vectors × 1536 dim × 4 bytes (float32) = 6 GB raw vector data
                                          × 2-3 (index overhead) = 12-18 GB
   100M vectors × 1536 dim × 4 bytes          = 600 GB raw
                                              × 2-3 (index) = 1.2-1.8 TB
   1B vectors × 1536 dim × 4 bytes            = 6 TB raw
                                              × 2-3 (index) = 12-18 TB
```

**Quantisation:**
- **Scalar (int8):** 4× memory reduction. Recall drop ~1–2%.
- **PQ (product quantisation):** 16–64× reduction. Recall drop 3–10%. Needs training.
- **Matryoshka:** Variable dim; pick lower dim at inference. Few % recall drop.

At 1B vectors, scalar quantisation drops the memory to **3 TB → 750 GB**. PQ drops it to **100 GB**. The cost difference is staggering.

---

## The sharding strategy

Two main approaches:

### 1. Hash sharding (default)
- Each vector is hashed to a shard based on its ID or tenant.
- Each shard is independent; replicas per shard.
- **Pros:** Simple, even distribution.
- **Cons:** Cross-shard queries (rare in vector world) are expensive.

### 2. Tenant sharding (multi-tenant)
- Each tenant gets dedicated shards.
- **Pros:** Strict tenant isolation, predictable performance per tenant.
- **Cons:** Hot tenants (one tenant has 100× more vectors than others) get unbalanced.

Most production systems use **tenant sharding for the long tail** + **hash sharding within large tenants**.

```
   ┌─────────────┬─────────────┬─────────────┐
   │  Tenant A   │  Tenant B   │  Tenant C   │
   │  (large)    │  (medium)   │  (small)    │
   │             │             │             │
   │ shard-A0 ──┐│ shard-B0 ──┐│ shard-C0    │
   │ shard-A1   ││ shard-B1   ││             │
   │ shard-A2   ││             ││             │
   └─────────────┴─────────────┴─────────────┘
```

---

## The replication pattern

```
   WRITE                     READ
   ─────                     ────
   coordinator ──► shard 0 primary ──► replica 0a
                       │
                       └────────────► replica 0b
                       │
                       └────────────► replica 0c

   3 replicas per shard, quorum = 2 for writes.
   Reads from any replica; round-robin or latency-based.
```

For production, **3 replicas minimum**, spread across AZs. Pinecone, Qdrant Cloud, Milvus, Weaviate all handle this for you if you don't self-host.

---

## The freshness story at scale

```
   PROBLEM: 100M vectors, refreshing 10% per day = 10M upserts/day

   Realtime ingest:
     - 10M / 86400s = 115 upserts/second average
     - peaks can hit 1000/s
     - HNSW inserts are slow; IVF is faster
     - consider batched async ingest

   Strategies:
     1. async batched: every 5 min, batch upsert 10K vectors
     2. streaming: Kafka → embed → upsert (low latency, complex)
     3. dual-write: write to new index in background, swap when ready

   Most prod systems: async batched, 5-15 min lag acceptable.
```

---

## The "rebuild the index" plan

When you upgrade embedding models or change schema:

```
   ┌────────────────────────────────────────────────────────┐
   │  THE INDEX REBUILD WORKFLOW                            │
   │                                                        │
   │  1. New index, side-by-side with old                    │
   │  2. Backfill: re-embed all chunks into new index        │
   │     - batched, throttled, observed                      │
   │     - cost: ~$1 per 10M chunks at small embedder        │
   │  3. A/B test: 10% queries → new, 90% → old             │
   │  4. Compare recall, latency, cost                       │
   │  5. Cut over: 100% → new                                │
   │  6. Delete old index                                    │
   │  7. Update `embedding_model_version` in metadata        │
   └────────────────────────────────────────────────────────┘
```

Plan for this to take **1–2 weeks** at billion scale. Don't do it on a Friday.

---

## The cost math (illustrative, 2026)

For 100M vectors, 1536 dim, hosted:

| Option | Storage | Monthly cost |
|---|---|---|
| Pinecone serverless | managed | $5k–15k |
| Qdrant cloud | managed | $2k–6k |
| Milvus self-hosted on AWS | 2× r6i.4xlarge + 1 TB gp3 | $1.5k–3k + storage |
| pgvector on existing RDS | +500 GB storage, +small CPU | $200–500 |
| Milvus + scalar quantisation | 4× less memory | ~$1k–2k |
| Milvus + PQ | 16× less memory | ~$500–1k |

**Quantisation is the single biggest cost lever** at scale.

---

## The observability

What you monitor at scale:

```
   PER-SHARD:
   - vector count
   - index build time
   - memory usage
   - insert latency
   - query latency p50 / p95 / p99

   CLUSTER-WIDE:
   - recall (against held-out eval set, run nightly)
   - freshness lag (source change → vector available)
   - shard skew (max/min vector count across shards)
   - cost per million queries
   - error rate (per-shard and aggregate)

   ALERTS:
   - recall drop > 2% over 24 hours
   - p99 latency > SLA
   - freshness lag > SLO
   - shard skew > 1.5×
   - memory > 80% capacity
```

---

## What AI cannot do at scale

- **Capacity planning.** You size the cluster; AI tunes within it.
- **Index rebuild risk management.** You cut over; AI can't sign off.
- **Cost optimisation choices.** "Use PQ?" — that's a business call.
- **Tenant SLAs.** Different tenants pay different amounts.

AI helps with: query tuning, embedding quality eval, anomaly detection on recall, and metadata schema design.

---

## What Comes Next

> Lesson 7 — **Quiz: Vector Databases & Embeddings** — self-check on the six lessons of Module 4.
