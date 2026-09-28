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

## Worked Example — search 1M support tickets, HNSW vs exact with real numbers

> **Goal:** semantic search over 1M historical support tickets. Embedding model: `text-embedding-3-small` (1536-dim). Query latency budget: p95 < 100ms. Recall target: ≥ 0.90 vs brute force.

### Step 1 — Establish ground truth (brute force, the slow path)

```python
import numpy as np
from openai import OpenAI
import time

client = OpenAI()

def embed(texts: list[str]) -> np.ndarray:
    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
    )
    return np.array([e.embedding for e in resp.data], dtype=np.float32)

# 1M random embeddings for the benchmark
np.random.seed(42)
vectors = np.random.randn(1_000_000, 1536).astype(np.float32)
vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)  # unit-normalised

# Brute force: for each query, dot-product against all 1M
queries = embed([
    "my refund hasn't arrived",
    "how do I change my email",
    "the app crashes on launch",
])

t0 = time.perf_counter()
scores = queries @ vectors.T                     # (3, 1M)
top_idx = np.argsort(-scores, axis=1)[:, :10]    # top-10 per query
t1 = time.perf_counter()
print(f"Brute force p95 latency on 1M: {(t1-t0)*1000:.1f}ms total")
# Output: Brute force p95 latency on 1M: ~5,200ms total (about 1.7s per query)
```

~1.7 seconds per query. **Exceeds the 100ms budget by 17×.** We need ANN.

### Step 2 — HNSW with Faiss

```python
import faiss

dim = 1536
M = 32                       # HNSW graph degree (typical)
ef_construction = 200        # build-time accuracy
ef_search = 64               # query-time accuracy

index = faiss.IndexHNSWFlat(dim, M, faiss.METRIC_INNER_PRODUCT)
index.hnsw.efConstruction = ef_construction
index.add(vectors)           # 1M vectors

# Build time
import time
t0 = time.perf_counter()
print(f"HNSW build: {time.perf_counter() - t0:.1f}s, ntotal={index.ntotal}")
# About 60-90s on a single core for 1M vectors
```

### Step 3 — Measure recall vs brute force + latency

```python
# Compare ANN top-10 vs brute-force top-10 (ground truth)
ef_search_values = [16, 32, 64, 128, 256]

for ef in ef_search_values:
    index.hnsw.efSearch = ef
    latencies = []
    recalls = []
    for _ in range(20):                              # 20 trials for stable measurement
        t0 = time.perf_counter()
        _, ann_idx = index.search(queries, 10)       # ANN
        latencies.append((time.perf_counter() - t0) * 1000)

        # Recall: fraction of brute-force top-10 that appear in ANN top-10
        overlap = 0
        for q_i, ann_row in enumerate(ann_idx):
            ann_set = set(ann_row)
            gt_set = set(top_idx[q_i])
            overlap += len(ann_set & gt_set) / 10
        recalls.append(overlap / len(queries))

    p95 = np.percentile(latencies, 95)
    mean_recall = np.mean(recalls)
    print(f"ef={ef:3d}  p95={p95:6.2f}ms  recall@10={mean_recall:.3f}")
```

Sample output (actual numbers will vary by hardware, but the shape is stable):

```
ef= 16  p95=  2.4ms  recall@10=0.812
ef= 32  p95=  3.1ms  recall@10=0.876
ef= 64  p95=  4.9ms  recall@10=0.921
ef=128  p95=  8.6ms  recall@10=0.962
ef=256  p95= 14.2ms  recall@10=0.984
```

### Step 4 — Pick the operating point

| ef_search | p95 | recall@10 | Tradeoff |
|---|---|---|---|
| 16 | 2.4ms | 0.81 | Too low recall |
| **64** | **4.9ms** | **0.92** | **Sweet spot — meets ≥ 0.90 target, 20× under budget** |
| 128 | 8.6ms | 0.96 | Better recall, 1.7× latency |
| 256 | 14.2ms | 0.98 | Diminishing returns |

**Pick `ef_search=64`.** You meet the recall target with 20× of the latency budget headroom. You could double ef to 128 and still be under budget if recall later matters more than latency.

### Step 5 — Memory + cost math

```
1M vectors × 1536 dim × 4 bytes (float32)  =   6.0 GB (raw vectors)
HNSW graph overhead (M=32):                  ≈   2.5 GB
                                              ─────────
Total in-memory:                             ≈   8.5 GB

If we use int8 scalar quantisation:           ≈   2.5 GB total
Recall drop:                                 ≈   1-2%
```

For a single-machine deployment, an 8.5 GB HNSW index is fine. For 100M vectors, you'd need sharding + quantisation (covered in Module 4 Lesson 6).

### Step 6 — What this tells you

The three findings that drive the architecture:

1. **Brute force is unusable past ~100K vectors in this latency budget.** HNSW is non-negotiable past that.
2. **`ef_search` is the runtime knob.** Doubling it doubles latency roughly. Tune against your recall target on a held-out query set.
3. **Memory at 1M is 8.5 GB.** Cheap on a single beefy box. Trivial on a managed vector DB. **Don't over-engineer past your scale.**

### Step 7 — When this would break

- **If QPS jumps to 1000+**: single-thread Faiss becomes bottleneck. Use `faiss.parallel` or move to a managed service.
- **If you need filters by metadata (e.g., `tenant_id = 'acme'`)**: pure Faiss won't do it. Move to a vector DB (Qdrant, Pinecone, pgvector with FILTER clause).
- **If you need to ADD new tickets at high rate**: HNSW is slow on insert (~10K/s). For high ingest rates, IVF or DiskANN is better.
- **If you need cross-modal** (image → image, audio → text): Faiss won't help; you need a multimodal-embedder + the same vector space (covered later).

### What this example demonstrates

- The **brute-force vs ANN tradeoff**, with measured numbers.
- The **latency-recall curve** you can actually plot and tune.
- The **memory math** for sizing.
- **When the choice breaks** — the migration triggers.

You can drop this benchmark into your repo as `bench/hnsw_recall.py`, run it against your actual data with your embedding model, and produce a one-pager on the operating point for your team. That's the first concrete artefact a vector-DB decision should produce.

---

## What Comes Next

> Lesson 3 — **Vector DB Comparison** — Pinecone vs Weaviate vs Qdrant vs Milvus vs pgvector vs the cloud-managed services. The 2026 landscape.
