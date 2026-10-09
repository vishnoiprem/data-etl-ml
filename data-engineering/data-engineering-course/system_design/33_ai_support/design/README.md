# 33 — AI-Powered Customer Support (RAG over a Knowledge Base)

> **Module 1 of 6 — Agentic AI Systems**

A complete, runnable design + implementation of a customer-support system
backed by retrieval-augmented generation (RAG). Customers open tickets;
the system retrieves the top-K knowledge-base articles and has a (mock)
LLM compose a grounded, cited reply.

---

## 1. Requirements

### Functional
- Ingest knowledge-base articles (title, body, tags).
- Open a support ticket (`user_id`, `subject`, `body`).
- Auto-reply to a ticket by retrieving relevant articles and composing a
  reply with citations.
- Human agent and end-user follow-up messages.
- Persist all state (articles, tickets, messages).

### Non-functional
- **Citation-grounded**: every reply must list which articles informed it.
- **Cheap retrieval**: top-K should respond in <50 ms on the in-memory
  inverted index. Real systems use a vector DB (FAISS, Pinecone).
- **Deterministic in tests**: same query + same articles → same reply.
- **Idempotent ingest**: re-ingesting the same article is safe.

### Out of scope
- Real LLM calls (we use a deterministic mock that templates replies).
- Auth, billing, multi-tenancy.

---

## 2. Capacity estimation

| Metric | Value |
|---|---|
| Tickets / day | 100 K |
| Articles in KB | 50 K (avg 1 KB) → 50 MB |
| Avg top-K retrieval | 5 articles × 1 KB = 5 KB / query |
| LLM prompt | ~2 K tokens (system + retrieved + user) |
| LLM response | ~200 tokens |

The expensive step is the LLM call. The cheap step (retrieval) is what
we should optimize first — that's why we cache retrieval results.

---

## 3. High-level design

```
            ┌──────────────────┐
customer ──►│  API / app tier  │──┐
            └──────────────────┘  │  write/read
                                  ▼
                           ┌─────────────┐
                           │ article KB  │  ◄── ingest
                           │  (KV store) │
                           └──────┬──────┘
                                  │ tokenize + index
                                  ▼
                           ┌─────────────┐
                           │ inverted    │  (in-process here,
                           │ index + TTL │   vector DB in prod)
                           │ cache       │
                           └──────┬──────┘
                                  │ top-K
                                  ▼
   ┌─────────────┐         ┌─────────────┐
   │  mock LLM   │◄────────┤ prompt build│
   │ (canned     │         │ context+user│
   │  templates) │         │             │
   └──────┬──────┘         └─────────────┘
          │ reply + citations
          ▼
   ┌─────────────┐
   │  ticket DB  │  append message, set status=auto_replied
   └─────────────┘
```

---

## 4. API

| Method | Path | Body | Returns |
|---|---|---|---|
| `POST` | `/api/articles` | `{title, body, tags[]}` | `Article` |
| `GET`  | `/api/articles` | — | `Article[]` |
| `GET`  | `/api/articles/<id>` | — | `Article` |
| `POST` | `/api/retrieve` | `{query, top_k}` | `{results: [{article, score}]}` |
| `POST` | `/api/tickets` | `{user_id, subject, body}` | `Ticket` |
| `GET`  | `/api/tickets` | — | `Ticket[]` |
| `GET`  | `/api/tickets/<id>` | — | `Ticket` |
| `POST` | `/api/tickets/<id>/reply` | `{}` (auto) / `{role, body}` (follow-up) | `{reply: Message}` |
| `GET`  | `/metrics`, `/health` | — | metrics / health |

---

## 5. Data model

### Article

```json
{
  "article_id": 42,
  "title": "Reset password",
  "body": "Click Forgot Password on the login page.",
  "tags": ["login"],
  "created_at": 1700000000.0
}
```

### Ticket

```json
{
  "ticket_id": 1,
  "user_id": "u-123",
  "subject": "Can't log in",
  "status": "auto_replied",
  "messages": [
    {"role": "user",      "content": "...", "citations": []},
    {"role": "assistant", "content": "...", "citations": [42, 17]}
  ],
  "citation_count": 2
}
```

### Inverted index

`idx:<token>:<article_id> = 1`. Cheap, in-process; in production we'd
embed each article and store vectors in FAISS / Pinecone / pgvector.

---

## 6. Read path deep dive: auto-reply

`POST /api/tickets/<id>/reply` (no body → auto-reply):

1. **Load ticket** + take the last user message.
2. **Build query**: `subject + last_user_message`. Tokenize, drop stopwords.
3. **Retrieve top-K** from the inverted index. Score = Σ term frequency
   with a +2 boost when the term appears in the title. (Real systems
   would use BM25 or cosine similarity of embeddings.)
4. **Build prompt**: a system prompt + the top-K article bodies + the
   user message. The mock LLM skips actual tokenization and just
   composes a reply based on the dominant tag of the top article.
5. **Append reply** with citations and flip `status` to `auto_replied`.
6. **Cache retrieval** result for `CACHE_TTL` (60 s) so repeated questions
   are free.

---

## 7. Write path deep dive: ingest

`POST /api/articles`:

1. Validate `title` and `body`.
2. Lowercase + tokenize once.
3. Persist `article:<id>` to KV.
4. For each unique token, write `idx:<token>:<id> = 1` (inverted index).

In production you'd: chunk the body, embed each chunk with a model,
upsert into a vector DB with metadata, and keep a relational copy of
the article for re-rendering.

---

## 8. Failure modes

| Failure | Mitigation |
|---|---|
| LLM rate-limited | Circuit-break; fall back to "we'll get back to you" + queue |
| Empty retrieval | Use a "general" template; ask user for more detail |
| Cache miss storm | Per-query TTL keeps it bounded; cold queries are cheap |
| Article drift (KB updated) | Re-index asynchronously; bump `version` on the article |
| Hallucination | Strict citation requirement; mock LLM always cites |

---

## 9. Tradeoffs

- **Mock LLM vs real LLM**: we use a deterministic mock. A real system
  would call OpenAI/Anthropic; the only change is one function
  (`_compose_reply`).
- **TF retrieval vs embeddings**: TF is fast and dependency-free but
  misses paraphrases. Embeddings (sentence-transformers, OpenAI
  `text-embedding-3`) are the production choice; the API and the
  rest of the pipeline are unchanged.
- **Per-ticket auto-reply vs batch**: high-volume systems batch tickets
  per topic and emit a single answer; we keep it per-ticket for clarity.
- **Mock citations vs real ones**: the mock always cites the retrieved
  articles. A real LLM is given the articles and instructed to cite.

---

## 10. Code map

| File | Role |
|---|---|
| `code/service.py` | `SupportService` — articles, retrieval, tickets, mock LLM, RAG flow. |
| `code/app.py` | Flask HTTP service exposing the API, /metrics, /health. |
| `tests/test_service.py` | Service-level tests (10 tests covering ingest, retrieval, auto-reply, follow-ups). |
| `tests/test_app.py` | HTTP-level tests using Flask's test client. |
