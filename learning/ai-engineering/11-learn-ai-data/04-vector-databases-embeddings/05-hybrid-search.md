# Lesson 5 — Hybrid Search

> **Type:** Article · Module 4 · Vector Databases & Embeddings
> Combining BM25 (lexical) and ANN (semantic) for the highest-quality retrieval.

---

## Why hybrid

Pure semantic search is **bad at exact matches**. Pure lexical search is **bad at synonyms**. Hybrid search combines both.

```
   Query: "How do I refund a payment?"

   LEXICAL (BM25) finds:                       SEMANTIC (vector) finds:
   - "refund a payment" (exact)                - "return money to customer"
   - "refund policy"                            - "chargeback process"
   - "Stripe refund API"                        - "dispute resolution"
   (precise but narrow)                        (broad but noisy)

   HYBRID: both lists, merged by score → best of both worlds
```

In practice, hybrid search beats pure semantic on most retrieval evals by **5–15% on recall@10**.

---

## The architecture

```
                  query
                    │
            ┌───────┴────────┐
            ▼                ▼
      BM25 retriever    ANN retriever
            │                │
            ▼                ▼
       top-50 docs       top-50 docs
            │                │
            └───────┬────────┘
                    ▼
            ┌──────────────┐
            │  FUSION      │  (RRF, weighted, cross-encoder rerank)
            └──────┬───────┘
                   ▼
              top-10 docs
```

Two retrievers, one query, results fused by score.

---

## The fusion methods

### 1. Reciprocal Rank Fusion (RRF)

```python
def rrf(rankings: list[list[str]], k: int = 60) -> list[str]:
    """Reciprocal rank fusion: 1/(k + rank)."""
    scores = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
    return sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
```

Simple, robust, no score normalisation needed. Default choice.

### 2. Weighted score fusion

```python
score = alpha * bm25_score + (1 - alpha) * vector_score
```

Requires score normalisation (BM25 and cosine are on different scales). Use `alpha ≈ 0.5` to start.

### 3. Cross-encoder rerank

After fusion, **rerank the top-50 candidates with a cross-encoder model**:

```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
pairs = [(query, doc.text) for doc in candidates]
scores = reranker.predict(pairs)
reranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
```

**Cross-encoder reranking adds the most quality** for retrieval tasks. ~50 ms for top-50. Highest leverage per minute spent.

---

## The "weights" tuning

```python
# typical starting points
ALPHA = 0.5            # 50% lexical, 50% semantic
TOP_K_BM25 = 50
TOP_K_VECTOR = 50
TOP_K_FINAL = 10
RERANK_TOP = 50        # rerank before final cut
```

Tune on your eval set. Higher ALPHA when queries are exact-match heavy (product codes, error messages). Lower ALPHA when queries are conceptual ("how does the refund flow work?").

---

## The query rewriting layer

For conversational / ambiguous queries, rewrite first:

```
   USER: "How do I undo that?"
        │
        ▼
   ┌──────────────┐
   │  LLM rewrite │  "How do I refund a payment?"
   └──────┬───────┘
          ▼
       BM25 + ANN + rerank
```

This is the **query understanding** step. LLM-based rephrasing, expansion, and HyDE (Hypothetical Document Embeddings) all live here.

---

## The "metadata-aware retrieval"

Real production retrieval is rarely "find me the closest 10." It's:

```
   find me the closest 10 WHERE
     tenant_id = current_user.tenant_id
     AND created_at > last_180_days
     AND language = current_user.locale
     AND visibility IN ('public', current_user.org_id)
     AND doc_type IN user_allowed_doc_types
```

Every production search has metadata filters. **Design the vector DB schema for them from day one.**

---

## The eval for hybrid

Build an eval set with:

| Query type | Expected behaviour |
|---|---|
| Exact match ("error code E1234") | BM25 wins |
| Synonym ("how to return money") | Semantic wins |
| Conceptual ("how does auth work") | Hybrid + rerank wins |
| Multi-hop ("compare X to Y") | Hybrid + rerank + multi-query |
| Negative ("how to NOT do X") | Hard for all; needs careful rewrite |

Track recall@10 for each. Tune ALPHA, RRF k, reranker model.

---

## What Comes Next

> Lesson 6 — **Vectors at Scale** — sharding, replication, quantisation, freshness at billion-scale, and the cost math.
