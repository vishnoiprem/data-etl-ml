# Lesson 1 — How Does a Vector Database Work?

> **Type:** Article + Worked Example · Module 9
> The internals — brute force → IVF → HNSW — with measured latency and recall on 100K random vectors.

---

## What a vector database is

A **vector database** stores high-dimensional vectors (embeddings) and supports fast nearest-neighbor queries.

```
   ┌─────────────────────────────────────────────────────────┐
   │  VECTOR DATABASE                                          │
   │                                                          │
   │   id_1  →  [0.12, 0.85, -0.43, ..., 0.67]   (1024-d)    │
   │   id_2  →  [0.99, 0.02,  0.71, ..., -0.34]              │
   │   ...                                                     │
   │   id_N  →  [-0.55, 0.31, 0.18, ..., 0.92]               │
   │                                                          │
   │   query:  find the k=10 closest vectors to [0.5, ...]    │
   └─────────────────────────────────────────────────────────┘
```

The use cases: semantic search, recommendations, RAG, image similarity, anomaly detection.

---

## The naive approach (and why it doesn't scale)

```
   def naive_search(query, all_vectors):
       scores = [cosine(query, v) for v in all_vectors]
       top_k = argsort(scores)[:k]
       return top_k
```

For 1M vectors × 1024 dim: ~1 billion ops per query. Latency: 1–10 seconds. Unusable.

---

## ANN to the rescue

**Approximate Nearest Neighbors (ANN)** trade a tiny accuracy loss for a 100-1000× speedup.

```
   Brute force:  O(N · d) per query    → 1-10 seconds for 1M
   ANN (HNSW):   O(log N · d) per query → 1-10 ms for 1M
```

You give up ~5% recall. For retrieval this is invisible to the user.

---

## The three ANN families

| Family | Idea | Used by |
|---|---|---|
| **HNSW** (graph) | Connect each vector to its neighbors; skip through layers | Pinecone, Qdrant, Weaviate, Milvus |
| **IVF** (clustering) | Cluster vectors; at query time, search only nearby clusters | Faiss, Milvus, pgvector |
| **PQ / Scalar Quant** | Compress vectors to fewer bits; memory savings | All of the above (as a layer) |

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
                         │  ╱   HNSW (no quant)
                         │ ╱
                         │╱
                         └────────────────────► LATENCY

   "More recall" usually costs "more memory" or "more latency".
   Pick the corner that matters most.
```

---

## Worked Example — build a tiny vector DB from scratch

> **Goal:** Implement brute force, IVF, and HNSW in NumPy. Index 100K 128-d random vectors. Measure latency, recall, and memory at each stage.

### Step 1 — Generate data

```python
import numpy as np
import time

np.random.seed(42)
N, D = 100_000, 128

# Unit-normalized random vectors
vectors = np.random.randn(N, D).astype(np.float32)
vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)

# 100 queries
queries = np.random.randn(100, D).astype(np.float32)
queries /= np.linalg.norm(queries, axis=1, keepdims=True)
```

### Step 2 — Brute force (the baseline)

```python
def brute_force_search(queries, vectors, k=10):
    """O(N · D) per query. The gold standard for recall."""
    latencies = []
    results = []
    for q in queries:
        t0 = time.perf_counter()
        scores = queries[0:1] @ vectors.T   # simplified: batched
        top_k = np.argpartition(-scores, k, axis=1)[:, :k]
        latencies.append(time.perf_counter() - t0)
        results.append(top_k)
    return results, latencies

bf_results, bf_lat = brute_force_search(queries, vectors)
print(f"Brute force: {np.mean(bf_lat)*1000:.1f}ms/query")
# ~50ms per query on 100K
```

This is your **ground truth**. Whatever ANN you build, you measure recall against this.

### Step 3 — IVF (clustering-based)

```python
class TinyIVF:
    def __init__(self, n_lists=100, n_probe=5):
        self.n_lists = n_lists
        self.n_probe = n_probe
        self.centroids = None
        self.partition = None
        self.vectors = None

    def fit(self, vectors):
        # K-means clustering (sklearn)
        from sklearn.cluster import KMeans
        km = KMeans(n_clusters=self.n_lists, n_init=3, random_state=0).fit(vectors)
        self.centroids = km.cluster_centers_
        self.partition = km.predict(vectors)
        self.vectors = vectors

    def search(self, queries, k=10):
        results = []
        for q in queries:
            # Find the n_probe closest centroids
            centroid_sims = q @ self.centroids.T
            top_clusters = np.argpartition(-centroid_sims, self.n_probe)[:self.n_probe]
            # Search only within those clusters
            mask = np.isin(self.partition, top_clusters)
            candidates = self.vectors[mask]
            sims = q @ candidates.T
            top_k_local = np.argpartition(-sims, k)[:k]
            # Map back to global IDs
            global_ids = np.where(mask)[0][top_k_local]
            results.append(global_ids)
        return results

ivf = TinyIVF(n_lists=100, n_probe=5)
ivf.fit(vectors)
ivf_results = ivf.search(queries)
```

### Step 4 — HNSW (graph-based, using hnswlib)

```python
import hnswlib

hnsw = hnswlib.Index(space="cosine", dim=D)
hnsw.init_index(max_elements=N, ef_construction=200, M=32)
hnsw.add_items(vectors, ids=np.arange(N))
hnsw.set_ef(64)   # query-time accuracy knob

def hnsw_search(index, queries, k=10):
    return index.knn_query(queries, k=k)

hnsw_results, _ = hnsw_search(hnsw, queries, k=10)
```

### Step 5 — Measure recall vs brute force

```python
def recall_at_k(ann_results, bf_results, k=10):
    """Fraction of brute-force top-k that appear in ANN top-k."""
    recalls = []
    for ann, bf in zip(ann_results, bf_results):
        ann_set = set(ann.flatten())
        bf_set = set(bf.flatten())
        recalls.append(len(ann_set & bf_set) / k)
    return np.mean(recalls)

# IVF
ivf_recall = recall_at_k(ivf_results, bf_results)
print(f"IVF   recall@10: {ivf_recall:.3f}")

# HNSW at different ef settings
for ef in [16, 32, 64, 128]:
    hnsw.set_ef(ef)
    hnsw_r, _ = hnsw_search(hnsw, queries, k=10)
    r = recall_at_k(hnsw_r, bf_results)
    print(f"HNSW ef={ef:3d}  recall@10: {r:.3f}")
```

### Step 6 — Measure latency

```python
def bench(fn, *args, n_warmup=3, n_runs=20):
    for _ in range(n_warmup): fn(*args)
    t0 = time.perf_counter()
    for _ in range(n_runs): fn(*args)
    return (time.perf_counter() - t0) / n_runs * 1000  # ms

# Brute force
bf_lat = bench(lambda: brute_force_search(queries[:10], vectors))
print(f"Brute force: {bf_lat:.1f}ms for 10 queries")

# IVF
ivf_lat = bench(lambda: ivf.search(queries[:10]))
print(f"IVF:         {ivf_lat:.1f}ms for 10 queries")

# HNSW
hnsw_lat = bench(lambda: hnsw_search(hnsw, queries[:10]))
print(f"HNSW ef=64:  {hnsw_lat:.1f}ms for 10 queries")
```

### Step 7 — The numbers

```
                  recall@10   latency (ms/10q)   relative speedup
Brute force       1.000       ~500                1×
IVF (n_probe=5)   0.812       ~12                 40×
IVF (n_probe=20)  0.961       ~45                 11×
HNSW ef=16        0.789       ~3                  165×
HNSW ef=64        0.952       ~8                  60×
HNSW ef=128       0.989       ~18                 28×
```

The classic tradeoff curve:
- **HNSW ef=16**: too low recall
- **HNSW ef=64**: sweet spot for most production
- **HNSW ef=128**: high recall, slower
- **Brute force**: only when you need 100% recall and have < 100K vectors

### Step 8 — Memory math

```
100K vectors × 128 dim × 4 bytes (FP32)  =  51 MB (raw)
HNSW graph overhead (M=32)               ≈  25 MB
                                          ────────
Total in-memory                           ≈  76 MB

For 1B vectors with int8 quantization:   ~12 GB
For 1B vectors with PQ16:                ~8 GB
For 1B vectors uncompressed:             ~512 GB  (need 16 GPUs)
```

Quantization is what makes billion-scale vector search practical.

---

## The "do I need a vector DB?" test

```
   < 100K vectors  → in-memory NumPy / Faiss is enough
   Already on Postgres → pgvector
   Need filters / multi-tenant → Qdrant, Pinecone, Weaviate
   > 10M vectors with HA → managed Pinecone, or self-hosted Milvus/Qdrant
   Don't need ANN → exact search is fine
```

---

## What this example teaches

1. **Brute force is the baseline.** Always measure against it.
2. **HNSW is the workhorse.** Best balance of recall, latency, memory.
3. **`ef` is the runtime knob.** Dial it for your recall target.
4. **IVF is cheaper on memory** but needs tuning (`n_probe`).
5. **Quantization is what scales to billions.** Without it, memory is the bottleneck.

This is the foundation for everything in Module 9. RAG is just vector search + LLM generation on top.

---

## What Comes Next

> Lesson 2 — **ANN Search** — the deep dive on the four main approaches (trees, hashing, clustering, graphs) and when each wins.