# M2 L2: Vector Mathematics and Similarity Search

> **Plain English:** A vector is a list of numbers. Similarity is a single number that tells you how close two lists are. KNN (K-Nearest Neighbors) is "show me the K most similar vectors." Every production vector DB (FAISS, Pinecone, Qdrant) is a fast, approximate version of this. Build the slow, exact version first.
> 90 min. Code: `python3 lessons/m02-vector-math/L2-vector-math-knn.py` (no API keys).

---

## 1. Concept (5 min)

**Distances** are not all the same. Pick the wrong one and retrieval ranking silently breaks.

| Metric | Formula | When to use |
|---|---|---|
| **L2 (Euclidean)** | `sqrt(sum((a_i - b_i)^2))` | Default for dense features; sensitive to magnitude |
| **L1 (Manhattan)** | `sum(abs(a_i - b_i))` | Sparse features, robust to outliers |
| **Inner product** | `sum(a_i * b_i)` | Pre-normalized embeddings; equivalent to cosine |
| **Cosine** | `(a·b) / (||a|| * ||b||)` | Text embeddings (default) — measures direction, not magnitude |

**The identity every vector DB exploits:** when all vectors are L2-normalized, `cosine(a, b) == inner_product(a, b)`. No sqrt, no divide. One matmul.

**Brute-force KNN** is O(N * dim). For 1M 768-dim vectors that's ~10^9 ops per query — too slow at scale. So production uses **ANN** (approximate) — HNSW, IVF-PQ, ScaNN. But the *exact* version is the ground truth: recall@K vs brute force is the standard eval.

---

## 2. Architecture (Mermaid)

```mermaid
flowchart LR
    A[query vector] --> B[Brute-force KNN<br/>O(N*d)]
    C[(N vectors<br/>in RAM)] --> B
    B --> D[sorted top-K]
    D --> E[production swap:<br/>FAISS / HNSW / Qdrant]
    E -.approx.-> F[top-K in O(log N)]
```

**Read as:** Start with brute force as ground truth. Replace with ANN when latency bites. Always measure recall@K of the ANN against the brute force.

---

## 3. Worked example (from the lesson code)

A 10-vector sample corpus with three clusters (HR, Finance, Ops). Query is an HR-shaped vector.

```
Section 3: KNN on the 10-doc sample (cosine, k=3)
  hr-001  dist=0.005
  hr-004  dist=0.005
  hr-002  dist=0.012
```

Top-3 are all HR — correct. Brute force is right.

**Metric sweep on 200 random unit vectors (k=5):**

| metric | latency | notes |
|---|---:|---|
| cosine | 2.52 ms | default; one sqrt per pair |
| l2 | 1.13 ms | no sqrt; faster but sensitive to magnitude |
| l1 | 0.92 ms | no multiply, just abs |
| ip | 0.21 ms | one matmul; assumes pre-normalized |

**ip is 12× faster** than cosine on the same data. The catch: it only ranks correctly when vectors are unit-length. That's why every production pipeline normalizes at ingest.

**Recall@10 vs numpy.argsort:** 10/10 (perfect). KNN gives the same answer as a hand-rolled sort.

---

## 4. Formulas (defined, every symbol)

```
L1(a, b)      = sum(|a_i - b_i|)                          (Manhattan)
L2(a, b)      = sqrt(sum((a_i - b_i)^2))                  (Euclidean)
inner(a, b)   = sum(a_i * b_i)                            (dot product)
cos(a, b)     = inner(a, b) / (||a|| * ||b||)             (cosine similarity)
              = inner(normalize(a), normalize(b))          (when unit-length)
||v||         = sqrt(sum(v_i^2))                          (L2 norm)
normalize(v)  = v / ||v||                                 (unit-length vector)
```

**Range notes:**
- L1, L2: in `[0, +inf)`, 0 = identical
- inner: in `(-inf, +inf)`, 0 = orthogonal
- cos: in `[-1, +1]`, 1 = identical direction, 0 = orthogonal, -1 = opposite

**KNN ranking equivalence:** under L2, "smallest distance" and "highest cosine" can rank differently. Under cosine, "smallest `1 - cos`" and "highest cos" are identical. Don't mix.

---

## 5. Code map (what's in `L2-vector-math-knn.py`)

| Section | Function | What it does |
|---|---|---|
| 1 | `l1_distance`, `l2_distance`, `inner_product`, `cosine_similarity` | The 4 metric primitives |
| 2 | `normalize`, `cos_via_inner_product` | The identity: cos == ip(norm, norm) |
| 3 | `knn` (dataclass `Neighbor`) | Exact KNN with 4 metric options |
| 4 | `TinyIndex` (dataclass) | Wraps `knn` for one-call retrieval |
| 5 | `SAMPLE_VECTORS`, `build_sample_index` | 10 hand-written 16-dim vectors in 3 clusters |
| 6 | `build_random_corpus` | N random unit vectors for the perf demo |
| 7 | `demo` | Runs all 7 sections top to bottom |
| 8 | 10 `test_*` functions | pytest-compatible unit tests |

---

## 6. Edge cases, failure modes, debugging

| Edge case | What breaks | What to do |
|---|---|---|
| Zero vector | `cosine(0, x) = NaN` (divide by 0) | Guard with `if norm == 0: return 0.0` (done) |
| Mixed metrics | "L2 says A is closer, cos says B is closer" — both correct | Pick one per index; never mix in one query |
| Non-normalized corpus | `ip` ranking is wrong | Normalize at ingest, not query time |
| Very high dim (>1000) | L2 and cosine lose contrast; curse of dimensionality | Use HNSW with PQ; or reduce dim with PCA |
| NaN in vectors | KNN propagates NaN, returns garbage | Validate at ingest: assert no NaN, finite only |
| Brute force on 10M+ | O(N*d) per query = seconds | Switch to HNSW (M4) |
| Same vector twice in corpus | Two identical distances; tie broken by index | That's fine; both are valid neighbors |

---

## 7. Scale-up: 100 → 1M → 100M → 1B vectors

| Scale | Method | Recall@10 | P50 latency | Memory |
|---|---|---:|---:|---|
| 100 | brute force | 1.00 | <1ms | 100 * 768 * 4B = 300KB |
| 1M | FAISS IVF (nlist=4096) | 0.95 | 5ms | ~3GB |
| 100M | HNSW (M=32) | 0.98 | 10ms | ~50GB |
| 1B | HNSW + PQ (m=64) | 0.95 | 20ms | ~30GB (compressed) |

(Back-of-envelope. Real numbers depend on dim, hardware, recall target.)

---

## 8. Alternatives and tradeoffs

| Index | Build time | Query P50 | Recall@10 | Memory | Pick when |
|---|---|---:|---:|---|---|
| Brute force | O(1) | O(N*d) | 1.00 | full | Ground truth, <100K vectors |
| FAISS IVF | minutes | 1-10ms | 0.90-0.95 | full | 1M-100M, batch queries |
| FAISS HNSW | hours | 1-5ms | 0.95-0.99 | 1.5x | 1M-50M, low latency |
| ScaNN (Google) | hours | 0.5-2ms | 0.95 | 1.0x | Google stack, best P99 |
| Pinecone | managed | 5-20ms | 0.95 | managed | Don't want to operate |
| pgvector | 0 | 20-100ms | 0.95 | full | Already on Postgres |

---

## 9. Mock interview

### 5 Meta L6 questions (with natural spoken answers)

**Q1: "Why is cosine the default for text embeddings and not L2?"**
> Because text embeddings from a transformer are L2-normalized as a side effect of training — the loss is usually a cosine-based contrastive loss. The magnitudes are roughly the same; the directions carry the meaning. If you use L2, you're weighting "longer" embeddings (which just have bigger numbers) as more important. Use cosine for text. Use L2 for raw features like pixel intensities.

**Q2: "How do you know your KNN implementation is correct before you trust the ANN?"**
> You build the brute force KNN first, build a golden set of 50 queries with hand-labeled relevant docs, and compute recall@K against the brute force. If the brute force doesn't recall 1.00, your distance function is wrong. If brute force is 1.00 and ANN is 0.90, your ANN is the problem. Never measure ANN recall against the answer — always against brute force.

**Q3: "Walk me through what happens when you query a 1M-vector HNSW index."**
> Entry point is a fixed node at the top of the graph. Greedy search: at the current node, look at all neighbors, jump to the closest one. Repeat until no neighbor is closer than the current node. That's the local minimum. HNSW also keeps a candidate list of the best K found so far, and uses the upper bound of the distance to unvisited nodes to skip whole layers. The two-level structure (entry layer, then narrow down) is what makes it O(log N).

**Q4: "You see recall@10 dropped from 0.95 to 0.80 after an index rebuild. What's your first hour?"**
> Check the build parameters first. Did the efConstruction change? Did the M change? Did the dimension change? Then check the data — is the new corpus a different distribution? Then check the metric — was the index built with inner product and queried with cosine, or vice versa? 80% of "ANN regressions" are build-parameter or metric-mismatch bugs, not the algorithm.

**Q5: "Why does HNSW use so much memory?"**
> Each node has M=16 to M=64 neighbors per layer. With 1M nodes and 32 layers times M=32, you have roughly 1B edges. Each edge is an int32 (4 bytes) plus the vector (768 floats = 3KB). The graph is the smaller cost; the vectors are the dominant cost. PQ compression reduces the vector cost 8-16× at a small recall hit. That's why production HNSW + PQ is the standard for >10M vectors.

### 3 Google-oriented questions (architecture + business)

**G1: "Design a 100M-doc similarity search system for a media company. Walk me through the major decisions."**
> Storage: HNSW + PQ on the vectors, metadata in Postgres (joined by doc_id). Build: incremental updates via a write-ahead log, batch rebuild weekly. Query: prefilter by metadata (language, date, ACL), then HNSW search on the filtered subset. Cost: 100M docs * 768 dim * 4B = 300GB raw, 50GB with PQ. The first decision is "do we need 100M in one index or can we shard by domain?" — for a media company, sharding by language is almost always right.

**G2: "Customer says the search is slow. Latency went from 10ms to 100ms. Triage."**
> Check the index first. Did the index size grow? Did the efSearch change? Did the M change? Then check the query — is it hitting a hot partition? Then check the hardware — disk IO? Memory pressure? Then check the application — is the query doing post-processing that scales with the candidate set? The cheapest fix is usually efSearch; the most expensive is a re-architecture. Measure first.

**G3: "You're the tech lead. A PM wants to add semantic search to the existing Postgres-only stack. Push back?"**
> Don't push back. Use pgvector. It's not the fastest, but it's already there, and "fast enough" beats "best in class" for most workloads. If the workload is <10M vectors, pgvector is fine. If it's >10M, then push for a dedicated vector DB, but only after measuring pgvector at production traffic. The wrong move is to build a vector DB stack for 100K vectors.

---

## 10. One-minute explanation

> A vector is a list of numbers. Similarity is a number that says how close two lists are. Cosine is the default for text because it measures direction, not magnitude. Brute force KNN is exact but slow — O of N times d per query. So production uses approximate indexes like HNSW that get 95 to 99 percent recall at 5 to 20 milliseconds for millions of vectors. The right way to ship this: build the exact version first as ground truth, measure the approximate version against it, and only ship the approximate version when the recall target is met.

## 11. 90-second interview script

> "Vector search is similarity over lists of numbers. Cosine similarity is the default for text embeddings because transformer training normalizes the magnitudes and the direction carries the meaning. Inner product is mathematically equivalent to cosine for unit-length vectors, and it's twelve times faster at query time because it's one matmul — that's why every production pipeline normalizes at ingest. Brute force KNN is O of N times d per query, which is fine for a hundred thousand vectors and untenable for a hundred million. The production answer is HNSW, a graph where each node keeps a small list of neighbors and the search is greedy descent to a local minimum, giving ninety-five to ninety-nine percent recall at single-digit milliseconds. The right way to validate an approximate index is to build a golden set of fifty queries, run brute force as ground truth, and measure recall at ten of the approximate index. If that number is below the target, you don't ship."

## 12. Assignment

### Build
1. Run the lesson code end-to-end: `python3 lessons/m02-vector-math/L2-vector-math-knn.py`
2. Run the 10 unit tests
3. Open the notebook and execute it top to bottom
4. Add a new metric "hamming" (for binary vectors) and a test
5. Replace the brute-force KNN with a vectorized NumPy implementation using `matrix @ query` and a single argsort

### Acceptance criteria
- [ ] All 10 unit tests pass
- [ ] Notebook executes in < 5 seconds
- [ ] `cos(a, a) == 1.0 ± 1e-5`
- [ ] `L1([1,0], [0,1]) == 2.0`
- [ ] KNN recall@10 == 1.0 on the 50-vector random test
- [ ] You can explain why `inner` is 12× faster than `cosine` on unit vectors

### Rubric (self-score 0-10 each)
- Math fluency: you can derive the cosine-via-inner-product identity
- Implementation: brute force KNN matches numpy.argsort (recall = 1.0)
- Tradeoff articulation: you can defend cosine vs L2 for text
- Production intuition: you know when to switch from brute force to HNSW
- Communication: the 90-second script is under 90 seconds

---

*Last updated: 2026-10-15*
*License: MIT*
