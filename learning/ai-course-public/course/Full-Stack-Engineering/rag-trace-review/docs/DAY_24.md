# Day 24 — AI Domain: Vector Databases + Embeddings
**Module 20** | Total: 90 min (10 + 20 + 30 + 20 + 20)

---

## 1. Simple explanation (10 min)

An **embedding** is a list of numbers that represents the *meaning* of text. "Dog" and "puppy" get similar numbers; "dog" and "democracy" get very different numbers.

A **vector database** is a search engine for embeddings. You give it a query, it gives you the K nearest neighbors (KNN) in meaning-space.

---

## 2. Technical concepts (20 min)

### Embeddings
- A function `text → ℝ^n` (typically n = 384, 768, 1024, 1536, 3072).
- Cosine similarity measures "how similar" two embeddings are.
- Models: `text-embedding-3-small` (OpenAI), `all-MiniLM-L6-v2` (local), `bge-large-en` (local, high quality).

### Vector search
- **Exact KNN:** O(n) per query. Slow at 1M+.
- **ANN (approximate nearest neighbor):** HNSW, IVF, ScaNN. O(log n) with ~99% recall.
- **HNSW:** graph-based, fast queries, big memory footprint.
- **IVF:** cluster-based, smaller memory, slower recall.

### Vector DBs
| Name | Type | Notes |
|---|---|---|
| Pinecone | Managed | Easy, expensive at scale |
| Weaviate | Self-host or cloud | Open source, modules for hybrid |
| Qdrant | Self-host or cloud | Rust, fast |
| pgvector | Postgres extension | Good for small scale |
| Chroma | Embedded | Good for prototyping |
| FAISS | Library | No server, you build the rest |

### Distance metrics
- Cosine: most common for text. Normalized vectors.
- Dot product: faster, equivalent to cosine on normalized vectors.
- Euclidean: for image embeddings.

### Tradeoffs
- **Recall vs latency:** HNSW with `ef` parameter. Higher = better recall, slower.
- **Memory vs recall:** larger index = better recall.
- **Indexing time vs query time:** re-index when corpus changes.

---

## 3. Coding (30 min)

Add a **semantic search** endpoint using a **real embedding model** that runs locally — `sentence-transformers`. First, add to `requirements.txt`:

```
sentence-transformers==3.0.1
```

Then write `backend/app/routes/embeddings.py`:

```python
"""Local semantic search using sentence-transformers + numpy."""
import os
import numpy as np
from fastapi import APIRouter, Query
from ..database import db_cursor

router = APIRouter(prefix="/embeddings", tags=["embeddings"])

# Lazy-load the model (saves ~5s on import)
_model = None


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


_CACHE: dict[str, np.ndarray] = {}


@router.get("/semantic-search")
def semantic_search(q: str = Query(...), k: int = Query(5, ge=1, le=50)):
    if q in _CACHE:
        q_emb = _CACHE[q]
    else:
        q_emb = get_model().encode(q)
        _CACHE[q] = q_emb

    with db_cursor() as cur:
        rows = cur.execute(
            "SELECT trace_id, user_query FROM traces LIMIT 1000"
        ).fetchall()

    corpus = [r["user_query"] for r in rows]
    corpus_emb = get_model().encode(corpus, show_progress_bar=False)

    # cosine similarity
    q_norm = q_emb / (np.linalg.norm(q_emb) + 1e-9)
    c_norm = corpus_emb / (np.linalg.norm(corpus_emb, axis=1, keepdims=True) + 1e-9)
    scores = (c_norm @ q_norm).flatten()

    top_k_idx = np.argsort(-scores)[:k]
    return [
        {"trace_id": rows[i]["trace_id"], "user_query": rows[i]["user_query"], "score": float(scores[i])}
        for i in top_k_idx
    ]
```

### Sample I/O
- GET `/embeddings/semantic-search?q=vector%20databases&k=3` → top 3 traces by meaning.

### Line-by-line
- `SentenceTransformer("all-MiniLM-L6-v2")` — 80MB model, 384-dim embeddings, runs on CPU.
- `np.linalg.norm` — vector magnitude.
- `c_norm @ q_norm` — matrix-vector product = cosine similarities for all docs.

---

## 4. Debugging & tests (20 min)

### Bug 1: model load is slow
**Fix:** load on first request (we already do), or pre-warm in `lifespan`.

### Bug 2: OOM on large corpus
**Fix:** encode in batches of 32; don't hold the full corpus in memory if > 100k.

### Bug 3: low recall
**Fix:** increase `k` for retrieval, add a reranker, use a bigger model.

### Bug 4: cache grows unbounded
**Fix:** LRU cache with max size.

### Test
```python
def test_semantic_search(client, seed):
    r = client.get("/embeddings/semantic-search?q=q1&k=2")
    body = r.json()
    assert len(body) <= 2
    assert all("score" in d for d in body)
```

---

## 5. Mock interview practice (20 min)

**Q1 — "Why not just use Postgres full-text search?"**
> FTS is lexical (matches words). Embeddings are semantic (matches meaning). "How do I fix my car?" matches "automotive repair guide" via embeddings, not FTS.

**Q2 — "How do you keep the index fresh?"**
> Upsert on every write. For 1M+ docs, batch updates every 5 min. HNSW supports incremental inserts.

**Q3 — "What is HNSW?"**
> Hierarchical Navigable Small World. Multi-layer graph. Top layer has long jumps; bottom layer has short jumps. Average query is O(log n).

**Q4 — "How do you measure semantic search quality?"**
> Labeled set: (query, relevant_doc_id). Recall@k = (# retrieved relevant) / (# relevant). Target 0.9+ at k=10.

**Q5 — "Why normalize vectors?"**
> Cosine similarity = dot product of unit vectors. Normalizing once at insert time makes queries a single matmul.

---

## 6. Success criteria check
- [ ] I can explain what an embedding is.
- [ ] I can name 3 vector DBs and their tradeoffs.
- [ ] I can describe HNSW in 2 sentences.
- [ ] I can run semantic search end-to-end.

## 7. Grade yourself 0–10
| Area | Score |
|---|---|
| Correctness | /10 |
| Code quality | /10 |
| Debugging | /10 |
| API design | /10 |
| Frontend implementation | /10 |
| Performance | /10 |
| Testing | /10 |
| Communication | /10 |
| **Total** | **/80** |

## 8. Coding assignment
**Add a `pgvector`-style in-memory HNSW index using `hnswlib` instead of brute-force search.**

### Rubric (0–10)
- 0: doesn't compile
- 4: hnswlib imported
- 6: index built
- 8: 10x faster than brute force
- 10: persisted to disk

### Solution
```python
import hnswlib
import numpy as np

def build_hnsw(vectors: np.ndarray, ids: list[str]):
    idx = hnswlib.Index(space="cosine", dim=vectors.shape[1])
    idx.init_index(max_elements=len(ids))
    idx.add_items(vectors, list(range(len(ids))))
    return idx
```

**Time: 90 min**