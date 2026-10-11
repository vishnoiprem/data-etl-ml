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
