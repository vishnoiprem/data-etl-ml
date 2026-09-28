# Lesson 2 — Vector DB Fundamentals

> **Type:** Article · Module 4 · Vector Databases & Embeddings
> What an ANN index actually does, how to choose one, and the tradeoffs.

---

## The naive approach (and why it doesn't work)

Naive: at query time, compute cosine similarity against **every** vector in the database. For 10 M vectors × 1536 dim, that's 15 billion floating-point ops per query. Latency: seconds. Doesn't scale.

```
   query vector  ──►  cosine similarity  ──►  top-k
                       against all N vectors
                       = O(N·d) per query
```

## The solution: Approximate Nearest Neighbours (ANN)

Trade a small amount of accuracy for **100–1000× speedup**. ANN indexes organise vectors so that "find me the closest 10" doesn't require scanning everything.

```
   query vector  ──►  ANN index  ──►  top-k candidates  ──►  exact rerank  ──►  top-k final
                       (fast, approximate)
```

Recall@10 might drop from 0.99 (exact) to 0.95 (approximate). For retrieval, this is usually invisible to the user.

---

## The three main ANN families

### 1. HNSW (Hierarchical Navigable Small Worlds)
- **Graph-based.** Each vector connects to its neighbours; layers allow "skipping" through the graph.
- **Strengths:** Very fast queries, high recall, no training step.
- **Weaknesses:** High memory, slow to insert, no compression of vectors.
- **Used by:** Pinecone (default), Qdrant, Weaviate (default), Milvus.

### 2. IVF (Inverted File Index)
- **Partition-based.** Cluster vectors into `k` partitions; at query time, search only the closest partitions.
- **Strengths:** Memory-efficient, fast bulk insert.
- **Weaknesses:** Lower recall at high speeds; needs training.
- **Used by:** Milvus (IVF_PQ), Faiss, pgvector (with `ivfflat`).

### 3. PQ / Scalar Quantisation
- **Compression-based.** Replace each vector with a compact code (e.g. 64 bytes instead of 6144).
- **Strengths:** Massive memory savings (10–30×).
- **Weaknesses:** Lower recall; sometimes re-ranking needed.
- **Used by:** Almost every vector DB, as a memory-saving layer on top of HNSW or IVF.

---

## The recall / latency / memory triangle

```
                       MEMORY
                         ▲
                         │
                         │        ╱
                         │       ╱
                         │      ╱  IVF_PQ
                         │     ╱
                         │    ╱────────────
                         │   ╱
                         │  ╱   HNSW (no quantisation)
                         │ ╱
                         │╱
                         └────────────────────► LATENCY

   "More recall" usually costs "more memory" or "more latency".
   Pick the corner that matters most for your workload.
```

| Workload | Pick |
|---|---|
| Production RAG with high recall | HNSW, no quantisation, rerank with exact |
| Billion-scale, cost-sensitive | IVF_PQ or HNSW + scalar quantisation |
| Real-time recommenders, low-latency | HNSW with small ef, kept hot in memory |
| Embeddings for analytics / clustering | IVF_PQ, recall less critical |

---

## The metadata filter problem

In production, **every query has filters** (tenant, date range, language, doc type). ANN indexes weren't designed for this.

```
   embedding:    ──► ANN top-k (over ALL vectors)
   metadata:     tenant_id = X
                 created_at > 2026-01-01
                 status = 'published'

   naive: ANN over all, then filter → may return <k after filter
   pre-filter: filter first, then ANN → may degrade index quality
   post-filter: ANN first, then filter → wastes work, low precision
   hybrid filter (per-engine): pre-filter with index awareness
```

**Per-engine support varies wildly.** Pinecone, Qdrant, and Weaviate support metadata filtering natively and efficiently. pgvector supports it but can be slow with high cardinality.

---

## The shard / replica story

For scale, vector DBs shard vectors across nodes:

```
   ┌────────────────────────────────────────────────────────┐
   │  VECTOR DB CLUSTER                                      │
   │                                                        │
   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
   │   │  Shard 0    │  │  Shard 1    │  │  Shard 2    │  │
   │   │  vectors    │  │  vectors    │  │  vectors    │  │
   │   │  0..3M       │  │  3M..6M     │  │  6M..9M     │  │
   │   └─────────────┘  └─────────────┘  └─────────────┘  │
   │         ▲                ▲                ▲           │
   │         └────────────────┴────────────────┘           │
   │                  coordinator                          │
   └────────────────────────────────────────────────────────┘
```

Each shard is replicated for HA. Reads scale with replicas; writes go through a quorum.

---

## The "what to look for" decision matrix

| Feature | Why it matters |
|---|---|
| **Recall vs. latency tunable** | You can dial it for your workload |
| **Metadata filtering** | Most production queries need it |
| **Hybrid search (BM25 + vector)** | Best retrieval quality (Lesson 5) |
| **Quantisation options** | Cost savings at scale |
| **Multi-tenant isolation** | If you serve many customers |
| **Replication + HA** | Production durability |
| **Real-time updates** | Ingest rate vs query latency |
| **Observability** | Recall metrics, slow-query logs |
| **On-disk vs in-memory** | Memory costs at scale |

---

## The "I don't need a vector DB" test

You might not need a vector DB if:
- <100K vectors → in-memory numpy / Faiss
- Already on Postgres / MySQL → pgvector, MySQL HeatWave
- Don't need ANN → exact search is fast enough
- One-shot batch → embed in Python, store in Parquet

You **do** need a vector DB if:
- >1M vectors
- Real-time queries
- Metadata filtering
- Production SLA (uptime, latency, recall)
- Multi-tenant

---

## What Comes Next

> Lesson 3 — **Vector DB Comparison** — Pinecone vs Weaviate vs Qdrant vs Milvus vs pgvector vs the cloud-managed services. The 2026 landscape.
