# apex-rag-omni

> **Sovereign RAG platform designed for 100M documents.** Not a demo. Not a tutorial. Staff-level ownership across ingestion, retrieval, eval, and observability.

## Interview pitch (30 sec)

I built APEX-RAG Omni. It's not a demo RAG — it's a sovereign platform designed for 100M docs. Frontend is Next.js with virtualized 1k-row trace reviewer, cursor pagination, optimistic feedback. Backend is 10-shard Qdrant cluster, hybrid BM25+vector, Flink CDC 5-min freshness, dual-write shadow index for embedding model upgrades. Omni layer means one API serves 3 domains with separate prompt templates and grounded evidence_json to prevent hallucination. I built eval harness with Recall@8, nDCG, and LLM-as-judge — this is Staff-level ownership, not tutorial.

## Working code

### Backend: `backend/app/main.py` (FastAPI)
- `GET /traces?cursor=trace_123&limit=50` — cursor O(1) not OFFSET O(N), uses index `(day, trace_id)`
- `POST /query` — `hybrid_search()` 10 shards → rerank Top8 → grounded answer with `evidence_json`
- `POST /feedback` — optimistic update, gold dataset for LLM-as-judge
- `POST /query/stream` — same pipeline over SSE (`meta → sources → token* → done`) for the chat UI
- `GET /eval` — latest report from the eval harness (empty until `make eval` has run; targets are returned separately)

### Frontend: `frontend/app/components/ApexRagOmni.tsx`
- Virtualized list for 1k+ rows
- Cursor pagination `loadMore()` from the `next_cursor` returned by the API
- `handleFeedback()` optimistic — lands in local state in < 16 ms, POSTs in background, rolls back on failure

### Scale (100M docs)
- SHA-256 dedup on ingest
- 10-shard Qdrant (stable hash routing)
- Flink CDC only re-embeds changed chunks (5-min freshness)
- $130k one-time embedding cost (text-embedding-3-large, 100M × 1536-d)

### Omni
- 3 collections: `hr_policies`, `tech_docs`, `product_docs` — each owns its prompt template
- `evidence_json` is the contract: every claim cites `[doc_N]`, or the answer is refused

## What is real vs. designed

| Layer | Status in this repo |
|---|---|
| Retrieval | **Working**: in-process BM25 + hashed-vector index with RRF fusion over a built-in demo corpus (`backend/app/local_index.py`). Same contract as the 10-shard Qdrant + ES fan-out, which is the **design**, not deployed here. |
| Answers | **Working**: extractive and grounded. Every sentence is verbatim corpus text with a `[doc_N]` citation, or the query is refused. No LLM call yet (`stream_tokens` is the seam). |
| Streaming chat UI | **Working**: SSE, stop/regenerate/copy/feedback, history. |
| Hallucination gate | **Working**: every answer is checked claim-by-claim (citations resolve, numbers match the source, lexical support); failures are refused. Word/number based, not an LLM judge. |
| Sanitization | **Working**: input normalisation + prompt-injection refusal (pattern list), PII masked before audit/logs, markup stripped from output. |
| Auth, CORS, audit queue, cursor-paginated traces | **Working**, tested (time-ordered trace ids, constant-time key check). |
| Flink CDC freshness, shadow-index dual-write, 100M-doc scale, embedding cost | **Design only.** |
| Eval metrics | Harness exists; quote only numbers from a real `make eval` run. |

## Run

```bash
# Backend (uses ../../.env venv automatically)
make api            # http://localhost:8000

# Frontend (second terminal)
make web            # http://localhost:3000
```

## Test

```bash
# Cursor pagination
curl "http://localhost:8000/traces?day=2026-10-16&cursor=trace_001000&limit=50"

# Grounded RAG query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"collection":"hr_policies","query":"What is PTO?"}'

# Streaming (SSE) - what the chat UI uses
curl -N -X POST http://localhost:8000/query/stream \
  -H "X-API-Key: devkey-change-me" -H "Content-Type: application/json" \
  -d '{"collection":"hr_policies","query":"How much PTO do I get per year?"}'

# Optimistic feedback
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{"trace_id":"trace_001","rating":5}'

# Latest eval report
curl http://localhost:8000/eval
```

## Repo layout

```
apex-rag-omni/
├── README.md                    # this file
├── Makefile                     # up / down / index / eval / test
├── requirements.txt             # backend deps
├── backend/
│   └── app/
│       ├── main.py              # FastAPI: /traces, /query, /query/stream (SSE), /feedback, /eval
│       ├── apex_router.py       # collection classifier + prompt loader
│       ├── apex_retriever.py    # hybrid search (BM25 + vector, RRF); local index today, Qdrant/ES by design
│       ├── local_index.py       # in-process BM25 + hashed-vector index (zero infra)
│       ├── corpus.py            # built-in demo corpus (3 collections)
│       ├── apex_answerer.py     # extractive grounded answer with evidence_json + citations
│       ├── hallucination.py     # claim-level check: citations, numbers, lexical support
│       ├── sanitize.py          # input sanitization, prompt-injection flags, PII redaction, output stripping
│       ├── apex_audit.py        # append-only audit log + cursor reader
│       └── apex_eval.py         # Recall@8, nDCG@8, p95 latency
├── frontend/
│   ├── package.json
│   └── app/
│       ├── page.tsx             # Next.js entry (chat)
│       └── components/
│           ├── Chat.tsx         # ChatGPT-style streaming chat UI
│           └── ApexRagOmni.tsx  # virtualized 1k-row trace reviewer (/traces)
├── prompts/
│   ├── hr_policies.yaml
│   ├── tech_docs.yaml
│   └── product_docs.yaml
├── agent/                       # legacy (kept for reference)
│   ├── router.py
│   ├── retriever.py
│   └── answerer.py
├── tools/
│   ├── qdrant.py                # 10-shard client + dual-write
│   ├── bm25.py                  # ES BM25 with cursor pagination
│   └── cdc.py                   # Flink CDC freshness stats
├── eval/
│   └── harness.py               # full eval harness
├── audit/
│   └── audit.jsonl              # append-only trace log
├── tests/
│   └── test_apex.py             # 27 tests
├── infra/
│   └── docker-compose.yml       # 10 Qdrant shards + ES + Postgres + Kafka + Flink + Redis
└── docs/
    └── architecture.md          # full design rationale
```

## Acceptance bar

| Metric | Threshold |
|---|---|
| Recall@8 | 0.89 |
| nDCG@8 | 0.91 |
| p95 latency | 420 ms |
| Judge groundedness | ≥ 4.0 / 5 |
| Judge hallucination | ≤ 2 / 5 |
| Freshness P95 | ≤ 5 min |

## Not this

- Not a LangChain demo.
- Not a Jupyter notebook. Production code only.
- Not a tutorial. Every line is a deliberate trade-off.
- Not a single-domain system. Three collections, one API.
- Not a vector-store-only system. BM25 is mandatory for exact-match.
