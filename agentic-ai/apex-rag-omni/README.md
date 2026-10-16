# apex-rag-omni

> **Sovereign RAG platform designed for 100M documents.** Not a demo. Not a tutorial. Staff-level ownership across ingestion, retrieval, eval, and observability.

```
   ┌──────────────────────────────────────────────────────────────────────┐
   │                       APEX-RAG OMNI PLATFORM                        │
   └──────────────────────────────────────────────────────────────────────┘
   Frontend (Next.js)
     │
     │  virtualized 1k-row trace reviewer
     │  cursor pagination
     │  optimistic feedback
     ▼
   Omni API Gateway  (1 API, 3 domains)
     │  - domain A prompt template
     │  - domain B prompt template
     │  - domain C prompt template
     │  - grounded evidence_json (anti-hallucination)
     ▼
   Hybrid Retriever (BM25 + vector)
     │
     ├──►  Qdrant cluster (10 shards)
     │       - shadow index for embedding upgrades
     │       - dual-write during model swap
     │
     └──►  BM25 inverted index
              - 5-min freshness via Flink CDC
              - Kafka topic for live docs
   ▼
   Eval Harness  (Recall@8, nDCG, LLM-as-judge)
     │
     └──►  reports/eval_<ts>.json + dashboard
```

## The shape

### 1. Frontend (Next.js)
- **Trace reviewer**: virtualized table that handles 1000+ retrieval traces without breaking a sweat.
- **Cursor pagination**: scroll-based load, never "page 1 of N" — works at any scale.
- **Optimistic feedback**: user ratings land instantly, reconcile in background.

### 2. Backend: 10-shard Qdrant cluster
- **Sharding**: documents hashed into 10 Qdrant collections by `tenant_id % 10`.
- **Hybrid retrieval**: BM25 (Elasticsearch/OpenSearch) + dense vector (Qdrant), fused with reciprocal-rank fusion.
- **5-min freshness**: Flink CDC pipeline tails Postgres WAL → Kafka → indexer. End-to-end P95 ≤ 5 min.
- **Shadow index for embedding upgrades**: when we swap embedding models (e.g., 1536-d → 3072-d), we dual-write to both old + new indexes, query new, then cut over atomically.

### 3. Omni layer (one API, three domains)
- `POST /v1/retrieve` and `POST /v1/answer` accept `{query, domain, top_k, filters}`.
- Domain-specific prompt templates (finance / legal / medical) live in `prompts/<domain>.yaml`.
- `evidence_json` is a structured artifact returned to the client — every claim is tied to a doc ID + offset. The LLM prompt is forced to cite `[doc_N]` or refuse.

### 4. Eval harness (Recall@8, nDCG, LLM-as-judge)
- **Recall@8**: at least 1 gold doc in top-8 (binary, deterministic).
- **nDCG@10**: graded relevance with position-discount.
- **LLM-as-judge**: GPT-4-class judge scoring groundedness / completeness / hallucination on a 1-5 scale.
- Reports land in `reports/eval_<timestamp>.json` and feed a dashboard.

## What I built

- `agent/router.py` — domain classifier + prompt-template loader.
- `agent/retriever.py` — hybrid BM25+vector fusion + shadow index.
- `agent/answerer.py` — grounded answer generator with `evidence_json` enforcement.
- `tools/qdrant.py` — 10-shard client + dual-write helper.
- `tools/bm25.py` — Elasticsearch client with cursor pagination.
- `tools/cdc.py` — Flink CDC pipeline starter.
- `audit/log.py` — every retrieval, every answer, every eval — append-only.

## Run it

```bash
make up        # bring up qdrant (10 shards), es, kafka, flink, postgres, redis
make index     # load 100M synthetic docs into all shards
make eval      # run the eval harness, write report
make down      # tear down
```

## Acceptance bar

- P50 retrieval latency ≤ 80 ms (P95 ≤ 200 ms) at 100M docs.
- 5-min freshness P95 ≤ 5 min.
- Recall@8 ≥ 0.85 on held-out set.
- nDCG@10 ≥ 0.78 on graded set.
- LLM-as-judge groundedness ≥ 4.0 / 5.
- Hallucination rate ≤ 2% (judge + spot check).

## Not this

- This is **not** a LangChain demo. No `from langchain import ...`.
- This is **not** a Jupyter notebook. Production code only.
- This is **not** a tutorial. Every line is a deliberate trade-off.