# Architecture — AI Document Q&A

> **The design decisions behind the starter.** Read this before you change anything.

## System diagram

```
                        ┌─────────────────┐
                        │   React UI      │
                        │  (or HTML)      │
                        └────────┬────────┘
                                 │ HTTPS
                                 ▼
                        ┌─────────────────┐
                        │   FastAPI       │
                        │   (uvicorn)     │
                        ├─────────────────┤
                        │ /upload         │
                        │ /chat           │
                        │ /documents      │
                        │ /auth/*         │
                        └────┬──────┬─────┘
                             │      │
                  ┌──────────┘      └──────────┐
                  ▼                             ▼
         ┌─────────────────┐          ┌─────────────────┐
         │  PostgreSQL     │          │   Pinecone      │
         │  (Neon free)    │          │   (vector DB)   │
         ├─────────────────┤          ├─────────────────┤
         │ - users         │          │ - chunks        │
         │ - documents     │          │ - embeddings    │
         │ - queries       │          │ - metadata      │
         │ - citations     │          │   (doc_id, pg)  │
         └─────────────────┘          └────────┬────────┘
                                               │
                                               ▼
                                      ┌─────────────────┐
                                      │  OpenAI API     │
                                      ├─────────────────┤
                                      │ - text-embed-3  │
                                      │ - gpt-4o-mini   │
                                      └─────────────────┘
```

## Component choices

| Component | Choice | Alternative | Why we picked this |
|---|---|---|---|
| Backend | FastAPI | Flask, Django | Async-native, OpenAPI built-in, Pydantic validation |
| Vector DB | Pinecone | Weaviate, Qdrant, pgvector | Free tier, fast, well-documented. Migrate to Qdrant at 1M+ chunks. |
| LLM | GPT-4o-mini | GPT-4o, Claude Haiku | 5× cheaper than GPT-4o, near-equal quality for RAG |
| Embedding | text-embedding-3-small | ada-002, Cohere, Voyage | 5× cheaper than ada-002, same dimensions |
| Database | Postgres (Neon) | MongoDB, MySQL | Relational data (users, queries, citations) + free tier |
| Auth | JWT (in starter) → Clerk in prod | Auth0, Supabase | Clerk has 5-min setup, social logins, MFA |
| Payments | (Add in week 4) Stripe | LemonSqueezy, Paddle | Industry standard, easy SaaS billing |
| File storage | (Add in week 4) S3 | Cloudflare R2 | S3 is the standard, R2 is cheaper |
| Hosting | Railway | Render, Fly.io, Vercel | $5/mo free tier, Postgres included, easy deploy |

## Data flow: upload a document

```
1. User uploads PDF via /upload
2. FastAPI validates file (size, type, virus scan in prod)
3. PyPDF2 extracts text per page
4. Text is chunked: 1000 tokens, 200 overlap
5. Each chunk embedded via text-embedding-3-small
6. Embeddings stored in Pinecone with metadata: {doc_id, page, user_id}
7. Document record saved in Postgres (status: "indexed")
8. Return doc_id to user
```

## Data flow: ask a question

```
1. User asks question via /chat
2. Question embedded via text-embedding-3-small
3. Pinecone returns top-5 chunks for (question, user_id)
4. Chunks formatted as context for LLM
5. GPT-4o-mini called with system prompt: "Answer using only this context. Cite sources as [1], [2]."
6. Response parsed: extract citations [1], [2] → look up source chunks
7. Save query + response + citations to Postgres (for history + analytics)
8. Return {answer, citations: [{chunk_id, doc_title, page, score}]} to user
```

## Capacity model

| Users | Docs | Queries/day | Compute | Storage | Monthly cost |
|---|---|---|---|---|---|
| 10 | 100 | 100 | Railway free | Pinecone free, Neon free | $0 |
| 100 | 1K | 1K | Railway $5 | Pinecone free, Neon free | $5 |
| 1K | 10K | 10K | Railway $20 | Pinecone $70, Neon $15 | $105 |
| 10K | 100K | 100K | Railway $100, 2 workers | Pinecone $200, Neon $50 | $350 |
| 100K | 1M | 1M | Railway $500, autoscaling | Pinecone $700, Neon $200 | $1,400 |

**Scaling cliffs:**

- **1K users**: Need to add Redis for query caching
- **10K users**: Need to add queue (Celery + Redis) for async document processing
- **100K users**: Need to switch from Pinecone to Qdrant self-hosted (cheaper at scale)
- **1M users**: Need to add CDN, rate limiting per tier, multi-region

## Cost model (per 1K queries)

Assumes: avg 5 chunks retrieved, 800 input tokens, 200 output tokens.

| Component | Cost per 1K queries |
|---|---|
| Embedding (query, 50 tokens) | $0.001 |
| Pinecone search | $0 (within free tier up to 100K queries) |
| GPT-4o-mini (800 input + 200 output) | $0.18 |
| Neon Postgres (1K writes) | $0 |
| **Total per 1K queries** | **$0.18** |

At $19/mo per user with 100 queries/day = 3K queries/month = $0.55 in LLM cost. **97% margin.**

## Security checklist

- [x] JWT tokens with expiry (replace with Clerk for refresh tokens)
- [x] Per-user data isolation (user_id filter on every query)
- [x] Input validation (Pydantic)
- [ ] Rate limiting per user (add in week 4)
- [ ] File virus scanning (add in production)
- [ ] PII redaction before sending to OpenAI (add if handling sensitive data)
- [ ] HTTPS only (handled by hosting platform)
- [ ] CORS restricted to your domain

## Observability checklist

- [x] Structured logs (JSON, request_id, user_id, timing)
- [x] Every LLM call logged with token counts + cost
- [x] Every Pinecone call logged with latency
- [ ] Add LangSmith or Helicone for LLM tracing (week 3)
- [ ] Add Sentry for error tracking (week 3)
- [ ] Add PostHog for product analytics (week 4)
- [ ] Add uptime monitoring (week 4)

## Failure modes

| Failure | Detection | Recovery |
|---|---|---|
| OpenAI rate limit | 429 response | Retry with exponential backoff (3x) |
| OpenAI down | 5xx response | Fall back to cached response |
| Pinecone down | Connection error | Show "search temporarily unavailable" |
| User uploads 1GB PDF | OOM | Reject >50MB uploads |
| User uploads 1000 docs | Slow queries | Per-user document limit (100 free, unlimited paid) |
| User sends prompt injection | Prompt guard | Sanitize inputs, log attempts |
| LLM hallucinates | Eval set alerts | RAGAS eval on every prompt change |

## When to migrate off this stack

| Trigger | Migration |
|---|---|
| >1M chunks in Pinecone | Move to Qdrant self-hosted (cheaper) |
| >$500/mo in OpenAI | Add Claude Haiku as fallback, use prompt caching |
| >10K users | Move auth to Clerk, add team workspaces |
| Users in EU | Move to EU region (Pinecone EU, OpenAI EU) |
| Need on-prem | Replace OpenAI with self-hosted Llama 3 70B |

## Trade-off log (ADRs)

- **ADR-001**: Pinecone over pgvector — Pinecone has better DX and free tier. Migrate to pgvector if cost > $200/mo.
- **ADR-002**: GPT-4o-mini over GPT-4o — 30× cheaper, near-equal quality for RAG. Switch to GPT-4o only for complex reasoning tasks.
- **ADR-003**: JWT in starter, Clerk in prod — Starter avoids external dependencies. Clerk is faster to set up than rolling our own auth.
- **ADR-004**: Pinecone over Weaviate — Pinecone has zero ops, better free tier. Weaviate is better for self-hosted.

## Future work

- [ ] Add streaming responses (SSE) to /chat
- [ ] Add conversation memory (multi-turn)
- [ ] Add image understanding (Claude/GPT-4V) for docs with figures
- [ ] Add team workspaces
- [ ] Add Slack/Notion integrations
- [ ] Add OCR for scanned PDFs
- [ ] Add multi-language support
- [ ] Add mobile app (React Native)
