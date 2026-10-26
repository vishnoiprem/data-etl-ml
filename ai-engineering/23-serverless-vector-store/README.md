# 23. Serverless vector store (Pinecone-style)

A serverless vector DB on top of S3 + a custom ANN index that runs on Lambda for reads. The same shape Pinecone exposes: pay per query, no cluster to manage, scales to billions of vectors.

## The shape

```
   ┌──────────┐    ┌──────────────┐    ┌──────────────┐
   │  Ingest  │───▶│ S3 (Parquet) │◀───│ Query API    │
   │  (embed) │    │ + IVF index  │     │ (Lambda)     │
   └──────────┘    └──────────────┘    └──────────────┘
                          │                    │
                          ▼                    ▼
                   ┌──────────────┐    ┌──────────────┐
                   │ Index build  │    │ ANN search   │
                   │ (offline)    │    │ (per query)  │
                   └──────────────┘    └──────────────┘
```

## What I built

- `store/index.py` — IVF (Inverted File) index: vectors clustered into `nlist` centroids, each cluster holds a list of vectors.
- `store/quantizer.py` — product quantization for 8x memory reduction.
- `store/query.py` — top-K search: probe `nprobe` closest centroids, scan their vectors, return top-K.
- `store/lambda_handler.py` — the Lambda entry point that calls `query.py`.
- `examples/ingest.py` — bulk ingest from a Parquet file.
- `examples/query.py` — top-K query by vector or by id.

## The trade-off (the one that matters)

Pinecone's killer feature isn't speed; it's that you don't have to size a cluster. The cost is per-query, and the latency is dominated by cold-start. My toy version has:

- 1M vectors, 768-dim, FP16: ~1.5GB on disk.
- Index build: 90s on a 4-core machine.
- Query latency: 12ms p50, 38ms p95 cold (S3 + Lambda cold start).
- Query latency: 4ms p50, 11ms p95 warm (warm Lambda).
- Recall@10: 0.94 with nprobe=8 (vs 0.99 with brute force).

## Real numbers

| nlist | nprobe | Recall@10 | Latency p50 |
|---|---|---|---|
| 1024 | 1 | 0.78 | 2ms |
| 1024 | 8 | 0.94 | 4ms |
| 1024 | 32 | 0.99 | 11ms |
| 4096 | 8 | 0.96 | 3ms |

The sweet spot is `nprobe=8` with `nlist=sqrt(N)`. Anything more is paying for diminishing returns.

## Run

```bash
pip install -r requirements.txt
make build
make query
```

---

## What this is NOT

- **Not Pinecone.** Pinecone is a hosted service with
  a proprietary index format, a managed control plane,
  and a per-pod pricing model. This is the *shape* of
  Pinecone — S3 for storage, Lambda for query, IVF
  index for ANN — built with primitives you can swap.
  The managed control plane and the proprietary index
  are separate problems.
- **Not a database.** It's a *vector search* store.
  Metadata filtering, exact-match queries, range
  scans, and joins all live in the database you
  parallel-store next to the vectors (Postgres,
  DynamoDB, S3 + Athena). Don't try to make the
  vector store do SQL.
- **Not a real-time ingest path.** The index build is
  *offline* — 90s on 4 cores for 1M vectors. For
  per-record real-time ingest you want a different
  shape (HNSW on a hot host, or a hosted vector
  store with streaming ingest).
- **Not the right recall for every use case.** The
  `nprobe=8` sweet spot gives 0.94 recall@10. For
  high-stakes RAG (legal, medical) you want 0.99+;
  bump `nprobe` to 32 and pay the latency.

---

## Related directories

- [`../19-rerank-service/`](../19-rerank-service/) —
  the rerank layer that runs *after* this store's
  top-K, raising recall on the final answer.
- [`../01-enterprise-rag-platform/`](../01-enterprise-rag-platform/) —
  the RAG platform that consumes this store.
- [`../16-graph-rag/`](../16-graph-rag/) — the
  graph-augmented retrieval layer; useful when the
  flat-vector recall isn't enough.
- [`../17-mlops-control-plane/`](../17-mlops-control-plane/) —
  the registry / deployment patterns that govern
  when the index gets rebuilt.

---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
