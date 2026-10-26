# 19. Rerank service (Cohere-style)

Rerank is the cheapest accuracy boost in RAG. A cross-encoder takes (query, candidate_chunk) pairs and returns a relevance score that's much better than the cosine distance the retriever used. The pattern here: a small FastAPI service that takes a query + top-K chunks, returns re-ordered chunks, and exposes the score distribution so the caller can pick a threshold that matches its recall/precision budget.

## The pattern

```python
# Tiny cross-encoder rerank service.
# Real impl: ms-marco-MiniLM, BGE-reranker, or Cohere's API.
@app.post("/rerank")
def rerank(req: RerankRequest):
    pairs = [(req.query, c.text) for c in req.candidates]
    scores = cross_encoder.predict(pairs)        # list[float]
    scored = sorted(zip(req.candidates, scores), key=lambda x: -x[1])
    return {"ranked": scored, "score_dist": stats(scores)}
```

## What I built

- `service/app.py` — FastAPI rerank service with cross-encoder scoring.
- `service/calibration.py` — exposes the score distribution (mean, p10, p50, p90) so callers can pick thresholds.
- `service/threshold.py` — a small CLI that finds the score threshold that gives you 90% recall on a labeled set.
- `examples/with_rag.py` — wires it into the existing RAG platform.
- `tests/test_rerank.py` — checks ordering on a small labeled set.

## Real numbers

On a 5K-query eval set from our legal-Q&A pilot:
- Retriever alone (vector + BM25 hybrid): 78% recall@10, 0.41 precision@5.
- After rerank: 91% recall@10, 0.63 precision@5.
- Latency: +35ms p95 per query.
- Cost: 1 cross-encoder call per 10 candidates = ~$0.0003 / query.

That's the deal. +13 points of recall for 35ms and a tenth of a cent.

## Why it works

The retriever's job is to be fast and recall-friendly. The reranker's job is to be slow and precise. Splitting them means each can use a different model size. A 22M-param cross-encoder is plenty for reranking; using the same model for retrieval would be 100x more expensive and only marginally better.

## Run

```bash
pip install -r requirements.txt
make up
python examples/with_rag.py
```

---

## What this is NOT

- **Not a retrieval model.** The retriever (vector
  search + BM25 hybrid) does the recall job; the
  reranker does the precision job on the top-K the
  retriever returned. Swap the retriever, keep the
  reranker. Swap the reranker, keep the retriever.
  They are independent.
- **Not a generator.** The rerank service returns
  *reordered chunks with scores* — not a final
  answer. The generator (LLM call with the top chunks
  in context) lives in the RAG platform that calls
  this service.
- **Not a free lunch.** The +35ms p95 and
  $0.0003/query are real, but the *latency* cost is
  paid per query. If the retriever is already at
  90%+ recall, the reranker's value is small. The
  pattern is highest-leverage when the retriever's
  recall is < 85%.
- **Not a Cohere-API replacement.** The default
  cross-encoder here is `ms-marco-MiniLM` or
  `BGE-reranker`, both open-source. You can swap to
  Cohere's `rerank-english-v3.0` API for a better
  baseline, at $2 / 1K searches.

---

## Related directories

- [`../01-enterprise-rag-platform/`](../01-enterprise-rag-platform/) —
  the RAG platform that calls this service as a
  post-retrieval step.
- [`../16-graph-rag/`](../16-graph-rag/) — the
  graph-augmented retrieval layer; rerank still
  applies, but the input candidates are graph
  neighborhoods, not flat chunks.
- [`../32-llm-eval-harness/`](../32-llm-eval-harness/) —
  the eval framework that measures whether the
  reranker is actually helping the end-to-end
  answer quality.
- [`../23-serverless-vector-store/`](../23-serverless-vector-store/) —
  the vector store that produces the top-K the
  reranker re-orders.

---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
