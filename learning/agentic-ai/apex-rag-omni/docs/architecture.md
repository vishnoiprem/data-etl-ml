# apex-rag-omni — Architecture

## System overview

```
                  ┌─────────────────────────────────────────────┐
                  │     apex-rag-omni  (Sovereign RAG)          │
                  └─────────────────────────────────────────────┘
                                     │
            ┌────────────────────────┼────────────────────────┐
            │                        │                        │
            ▼                        ▼                        ▼
   ┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
   │  Next.js        │    │  Omni API        │    │  Eval harness    │
   │  Frontend       │    │  (FastAPI)       │    │  (Recall, nDCG,  │
   │  (virtualized   │◄──►│                  │◄──►│   LLM-as-judge)  │
   │   1k trace)     │    │  /v1/retrieve    │    │                  │
   └─────────────────┘    │  /v1/answer      │    └──────────────────┘
                          └──────────────────┘
                                     │
            ┌────────────────────────┼────────────────────────┐
            │                        │                        │
            ▼                        ▼                        ▼
   ┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
   │  Qdrant cluster │    │  Elasticsearch   │    │  Postgres + WAL  │
   │  10 shards      │    │  (BM25)          │    │  (source of      │
   │  + shadow index │    │                  │    │   truth)         │
   └─────────────────┘    └──────────────────┘    └──────────────────┘
            ▲                                                 │
            │                                                 ▼
            │                                       ┌──────────────────┐
            │                                       │  Flink CDC       │
            │                                       │  5-min freshness │
            │                                       │  WAL → Kafka     │
            │                                       └──────────────────┘
            │                                                 │
            └────────────── indexer ◄────────────────────────┘
```

## Why these choices

### 10-shard Qdrant (not 1 big collection)
- **Latency**: 10x smaller collections = 10x faster ANN search.
- **Failure isolation**: a single shard going down only loses 10% of the
  index, not 100%.
- **Rebalancing**: stable hashing (sha256 mod n) means rebalancing is
  a copy + alias swap, not a re-shuffle of the whole keyspace.

### Hybrid BM25 + vector (RRF)
- Vector-only misses exact-match queries ("Section 12.3(b) of the
  agreement").
- BM25-only misses semantic queries ("revenue growth similar to Q3 last
  year").
- RRF combines both without needing score normalization — robust to
  different score scales from different backends.

### 5-min freshness via Flink CDC
- Tailing the Postgres WAL is the only way to hit 5-min freshness at
  100M docs without hammering the DB with change-detection queries.
- Debezium → Kafka → indexer is the standard production pattern.

### Shadow index for embedding model upgrades
- When the embedding model changes (e.g., text-embedding-3-small →
  text-embedding-3-large), the vector dimension changes too. A naive
  cutover loses retrieval quality for the duration of the reindex.
- Dual-write to both old + new indexes, query new, atomic alias swap.
  Zero-downtime upgrade.

### Omni layer: 1 API, 3 domains
- Three separate APIs means three separate code paths, three separate
  prompt templates, three separate eval sets. Drift guaranteed.
- One API with a `domain` parameter means one code path, one place to
  audit, one eval set to maintain. Per-domain customization is
  data-driven (prompts/<domain>.yaml) not code-driven.

### `evidence_json` to prevent hallucination
- The LLM prompt is forced to cite `[doc_N]` for every claim.
- If coverage < 50% of retrieved docs cited, the answer is refused.
- `evidence_json` is the structured artifact returned to the client —
  no claims without citations.

### Eval harness: 3 metrics, 3 views
- **Recall@8** is binary, deterministic, fast. The "is the answer in
  the top-8?" question.
- **nDCG@10** is graded, position-aware. The "is the most relevant
  doc near the top?" question.
- **LLM-as-judge** catches groundedness + hallucination, which the
  automated metrics can't. A doc can be retrieved but cited wrongly;
  only a judge catches that.

## Acceptance bar

| Metric | Threshold |
|---|---|
| Recall@8 | ≥ 0.85 |
| nDCG@10 | ≥ 0.78 |
| Judge groundedness | ≥ 4.0 / 5 |
| Judge hallucination | ≤ 2 / 5 |
| P50 retrieval latency | ≤ 80 ms |
| P95 retrieval latency | ≤ 200 ms |
| Freshness P95 | ≤ 5 min |

## What this is NOT

- Not a LangChain demo. No `from langchain import ...`.
- Not a Jupyter notebook. Production code only.
- Not a tutorial. Every line is a deliberate trade-off.
- Not a vector-store-only system. BM25 is mandatory for exact-match.
- Not a single-domain system. Three domains share one API; per-domain
  customization is data-driven.
