# Day 23 — System Design: RAG at Scale
**Module 19** | Total: 90 min (10 + 20 + 30 + 20 + 20)

---

## 1. Simple explanation (10 min)

A RAG system is a **library with a librarian**. The librarian has read every book (vector DB). When you ask a question, the librarian finds the 5 most relevant paragraphs (retrieval), reads them, and writes an answer (generation).

The hard part: the librarian has to be **fast** (sub-2s), **accurate** (no hallucinations), and **cheap** (LLM calls cost money).

---

## 2. Technical concepts (20 min)

### Pipeline
1. **Ingest:** chunk documents → embed → store in vector DB.
2. **Query:** embed user question → top-k search → rerank → prompt LLM.
3. **Observe:** log traces, capture feedback (this project).

### Components
- **Chunker:** split docs into 200–500 token chunks with 20% overlap.
- **Embedder:** sentence-transformers / OpenAI `text-embedding-3-small`.
- **Vector DB:** Pinecone, Weaviate, Qdrant, pgvector.
- **Reranker:** cross-encoder (Cohere, BGE-reranker). Trades latency for accuracy.
- **LLM:** GPT-4, Claude, Llama-3. Mix and match.
- **Cache:** Redis for query embeddings and exact-match responses.

### Capacity
- 1M docs × 500 tokens × 1.5 KB/token = 750 GB embeddings.
- Top-k=10 search: ~50ms with HNSW index.
- LLM: 500ms–2s depending on model.

### Failure modes
- Vector DB down → fall back to BM25 (lexical search).
- LLM down → return top chunks only ("no answer available").
- Embedder down → use cached embeddings or BM25.
- Stale embeddings → nightly re-embed job.

### Cost
- Embedding: $0.02 / 1M tokens.
- GPT-4o: $5/M input, $15/M output.
- 1k QPS × 1k tokens in + 500 tokens out = $5 × 86400 = **$432k/day** at 1k QPS.

This is why **caching** is mandatory at scale.

---

## 3. Coding (30 min)

Add a vector search endpoint. For local dev, use **TF-IDF** as a stand-in for embeddings (no external API).

```python
# backend/app/routes/retrieval.py
"""Toy retriever using TF-IDF over the user_query column."""
import math
import re
from collections import Counter
from fastapi import APIRouter, Query
from ..database import db_cursor

router = APIRouter(prefix="/retrieval", tags=["retrieval"])


def tokenize(s: str) -> list[str]:
    return re.findall(r"\w+", s.lower())


_DOC_CACHE: list[dict] = []


def _load_corpus():
    global _DOC_CACHE
    if _DOC_CACHE:
        return _DOC_CACHE
    with db_cursor() as cur:
        rows = cur.execute(
            "SELECT trace_id, user_query, prompt_version FROM traces"
        ).fetchall()
    _DOC_CACHE = [dict(r) for r in rows]
    return _DOC_CACHE


@router.get("/search")
def search(q: str = Query(...), k: int = Query(5, ge=1, le=50)):
    docs = _load_corpus()
    q_tokens = Counter(tokenize(q))
    scores = []
    for d in docs:
        d_tokens = Counter(tokenize(d["user_query"]))
        # cosine similarity
        dot = sum(q_tokens[t] * d_tokens.get(t, 0) for t in q_tokens)
        norm = (sum(v * v for v in q_tokens.values()) ** 0.5) * (
            sum(v * v for v in d_tokens.values()) ** 0.5
        ) or 1
        scores.append((dot / norm, d))
    scores.sort(key=lambda x: -x[0])
    return [{"score": s, **d} for s, d in scores[:k]]
```

### Sample I/O
- GET `/retrieval/search?q=What%20is%20RAG&k=3` → 3 most similar user_queries with scores.

### Line-by-line
- `_DOC_CACHE` is a module-level cache (reload on app start).
- `Counter` is a dict with `.most_common()`.
- Cosine similarity: dot product / product of norms.

---

## 4. Debugging & tests (20 min)

### Bug 1: empty corpus
**Fix:** lazy-load on first request, not on import.

### Bug 2: cache stale
**Fix:** invalidate `_DOC_CACHE = []` after a write.

### Bug 3: irrelevant results
**Fix:** real embeddings beat TF-IDF. Use OpenAI or a local model.

### Bug 4: hot key in cache
**Fix:** shard Redis by hash of the query.

### Test
```python
def test_search_returns_results(client, seed):
    r = client.get("/retrieval/search?q=query")
    body = r.json()
    assert len(body) <= 5
    assert all("trace_id" in d for d in body)
```

---

## 5. Mock interview practice (20 min)

**Q1 — "How do you chunk a 100-page PDF?"**
> Recursive splitter: split by section → paragraph → sentence. 500 tokens per chunk, 50-token overlap. Preserve headings as metadata.

**Q2 — "How do you evaluate retrieval quality?"**
> Offline: a labeled set of (query, relevant_doc_id). Measure recall@10, MRR. Online: thumbs up/down on the final answer (this project!).

**Q3 — "When would you NOT use RAG?"**
> When the answer is in a single document. When the data is highly structured (use a SQL agent). When latency budget is < 100ms (cache the answer).

**Q4 — "How do you make it cheaper?"**
> Cache query embeddings. Use a smaller model for retrieval, larger for generation. Rerank only top-50. Batch embeddings during ingest.

**Q5 — "How do you detect drift?"**
> Compare embedding distribution week-over-week. Alert if KL divergence > threshold. Track retrieval recall on a held-out set.

---

## 6. Success criteria check
- [ ] I can describe the full RAG pipeline.
- [ ] I can estimate cost and latency.
- [ ] I can list 4 failure modes.
- [ ] I can explain the eval loop.

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
**Add a `/retrieval/search` cache: cache results in memory by query string for 5 minutes.**

### Rubric (0–10)
- 0: no cache
- 4: in-memory dict
- 6: TTL enforced
- 8: LRU eviction
- 10: cache hit metric

### Solution
```python
import time
_CACHE: dict[str, tuple[float, list]] = {}
TTL = 300

def cached_search(q: str, k: int):
    key = f"{q}:{k}"
    now = time.time()
    if key in _CACHE and now - _CACHE[key][0] < TTL:
        return _CACHE[key][1]
    result = search(q, k)
    _CACHE[key] = (now, result)
    return result
```

**Time: 90 min**