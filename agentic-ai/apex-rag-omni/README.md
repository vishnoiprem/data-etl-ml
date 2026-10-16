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
| Document upload | **Working**: txt/md/csv/pdf → passages → searchable + citable, dedupe, per-collection, delete, PII/injection warnings. |
| Docker + HTTPS deploy | **Working** (Caddy + web + api, login, key injection). Verified locally with Docker. |
| Hallucination gate | **Working**: every answer is checked claim-by-claim (citations resolve, numbers match the source, lexical support); failures are refused. Word/number based, not an LLM judge. |
| Sanitization | **Working**: input normalisation + prompt-injection refusal (pattern list), PII masked before audit/logs, markup stripped from output. |
| Auth, CORS, audit queue, cursor-paginated traces | **Working**, tested (time-ordered trace ids, constant-time key check). |
| Flink CDC freshness, shadow-index dual-write, 100M-doc scale, embedding cost | **Design only.** |
| Eval metrics | Harness exists; quote only numbers from a real `make eval` run. |

## Upload your own documents

Out of the box each collection has a small demo corpus. Add your real documents and they become searchable and citable immediately.

**In the UI:** pick a collection in the sidebar → **⬆ Upload documents** → choose one or more files. Ask a question; answers cite your file by name (e.g. `remote-work.txt (1/2)`). Open **▸ N uploaded** to see or remove files.

**Via the API:**
```bash
curl -X POST http://localhost:8000/documents \
  -H "X-API-Key: $KEY" -F collection=hr_policies -F file=@remote-work.pdf
curl "http://localhost:8000/documents?collection=hr_policies" -H "X-API-Key: $KEY"        # list
curl -X DELETE "http://localhost:8000/documents/<doc_id>?collection=hr_policies" -H "X-API-Key: $KEY"
```

| | |
|---|---|
| Formats | `.txt` `.md` `.csv` `.pdf` (text PDFs; scanned/image PDFs need OCR first - not supported) |
| Size | 5 MB per file (`APEX_MAX_UPLOAD_BYTES`) |
| Processing | extract → strip control chars → split into ~500-char passages on paragraph/sentence boundaries → index. Each passage is one citable `[doc_N]` source |
| Duplicates | SHA-256 of the cleaned text; re-uploading the same content returns `409` |
| Scope | a document belongs to one collection; other collections never see it |
| Safety | Upload response lists `pii_detected` (emails, cards, phones, IDs) and `injection_like` so you can decide whether to keep a file. Markup is stripped from anything returned to the UI |
| Storage | `APEX_DATA_DIR` (default `./data`, gitignored; `/data` volume in Docker). **Back it up** - it is your knowledge base |

Tips for good answers: use clear headings and short paragraphs; one topic per file; put numbers and policy names in the text (answers are copied verbatim from your passages, never invented).

## Host it and make it live

The production stack is three containers behind Caddy: **proxy** (automatic HTTPS + login + injects the API key) → **web** (Next.js) + **api** (FastAPI). The API key never reaches the browser. Tested end to end (login, streaming, upload, restart persistence).

**You need:** a Linux server or VM (1 vCPU / 1 GB is enough for the built-in index), Docker with the Compose plugin, a domain name, ports 80 and 443 open.

```bash
# 1. DNS: point rag.example.com (A/AAAA record) at the server's IP.

# 2. On the server:
git clone <your-repo> && cd data-etl-ml/agentic-ai/apex-rag-omni
cp .env.prod.example .env.prod

# 3. Fill in .env.prod
python3 -c "import secrets;print(secrets.token_urlsafe(32))"                      # -> APEX_PROXY_KEY
docker run --rm caddy:2 caddy hash-password --plaintext 'a-strong-password'      # -> APEX_BASIC_HASH
#    (in .env.prod escape every $ in the hash as $$ ; set DOMAIN and APEX_BASIC_USER)

# 4. Go live
docker compose -f infra/docker-compose.app.yml --env-file .env.prod up -d --build

# 5. Check
docker compose -f infra/docker-compose.app.yml --env-file .env.prod ps     # api shows (healthy)
curl -u admin:'a-strong-password' https://rag.example.com/api/healthz      # {"status":"ok"}
```
Open `https://rag.example.com`, log in, upload documents, ask questions. Caddy obtains and renews the TLS certificate by itself.

**Try it locally first:** set `DOMAIN=http://localhost` in `.env.prod` and use `http://localhost`.

**Operate**
```bash
# update to a new version
git pull && docker compose -f infra/docker-compose.app.yml --env-file .env.prod up -d --build

# logs
docker compose -f infra/docker-compose.app.yml --env-file .env.prod logs -f api

# back up uploaded documents (do this on a schedule)
docker run --rm -v apex-rag-omni_apex-data:/d -v "$PWD":/b alpine tar czf /b/apex-data-$(date +%F).tgz -C /d .

# rotate the key: change APEX_PROXY_KEY in .env.prod, then `up -d` again
```
Health endpoints for your monitor: `/api/healthz` (liveness). `/api/readyz` reports 503 until Qdrant/ES are configured; that is expected for the built-in index.

**Other hosts:** any VM works (AWS Lightsail/EC2, Azure VM, DigitalOcean, Hetzner). For a managed platform (Cloud Run, ECS, Azure Container Apps) deploy the `api` and `web` images, mount a persistent volume at `/data`, and terminate TLS + login at the platform's gateway; keep `NEXT_PUBLIC_API_BASE=/api` and route `/api/*` to the API.

**Know the limits before you expose it**
- One shared login (HTTP basic auth). Everyone who can log in can upload, delete and read every collection. For per-user access put it behind your SSO (oauth2-proxy/Azure AD in front of Caddy) instead.
- Single node, local index: fine for thousands of documents; the Qdrant/ES/Flink design in `docs/architecture.md` is **not** deployed by this stack.
- Answers are extractive (verbatim cited sentences), not a chat model. No per-key rate limiting yet (backlog B3).
- Don't upload secrets or regulated personal data unless your policy allows it; the upload warning is advisory.

## Run (local development)

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
