# AI Document Q&A — Capstone Starter

> **Build a "ChatGPT for your PDFs" in 8 weeks using this starter.**

This is the runnable starter for **Capstone Template 1** from [`../../projects/ai-engineer-capstone-guide.md`](../../projects/ai-engineer-capstone-guide.md). The starter gives you a complete working skeleton: upload PDFs, auto-chunk + embed, search bar, answers with citations. Your job is to extend it to a production-grade, paid SaaS over 8 weeks.

---

## What you start with

A working AI Document Q&A product with:

- ✅ **Backend** — FastAPI with `/upload`, `/search`, `/chat` endpoints
- ✅ **RAG pipeline** — chunk PDFs, embed with `text-embedding-3-small`, store in Pinecone
- ✅ **Generation** — GPT-4o-mini answers questions using retrieved chunks
- ✅ **Citations** — every answer includes the source document + page number
- ✅ **Frontend** — minimal React UI (or use the included HTML)
- ✅ **Auth** — JWT-based auth (replace with Clerk/Auth0 in production)
- ✅ **Tests** — pytest suite covering the RAG pipeline
- ✅ **Docker** — Dockerfile + docker-compose for local dev
- ✅ **Architecture doc** — [`ARCHITECTURE.md`](./ARCHITECTURE.md) with system diagram, cost model, capacity model

What you add in 8 weeks:

- [ ] Replace JWT with Clerk (or Auth0/Supabase)
- [ ] Add Stripe for payments
- [ ] Add team workspaces
- [ ] Add OCR for scanned PDFs (Tesseract or AWS Textract)
- [ ] Add multi-language support
- [ ] Add Slack/Notion integrations
- [ ] Deploy to Railway / Render
- [ ] Get 10 paying users

---

## How to run locally

```bash
# 1. Install dependencies
cd 01-ai-doc-qa
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Set environment variables
cp .env.example .env
# Add your OPENAI_API_KEY and PINECONE_API_KEY

# 3. Start the server
uvicorn app:app --reload

# 4. Open the UI
open http://localhost:8000
```

---

## Folder structure

```
01-ai-doc-qa/
├── README.md               # this file
├── ARCHITECTURE.md         # system design + cost model + capacity model
├── app.py                  # FastAPI entry point
├── rag.py                  # the RAG pipeline (200 lines, no frameworks)
├── auth.py                 # JWT auth (replace with Clerk in week 3)
├── db.py                   # SQLAlchemy models for users, documents, queries
├── frontend/
│   └── index.html          # minimal UI (replace with React in week 5)
├── tests/
│   └── test_rag.py         # pytest suite
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/auth/signup` | Create account, returns JWT |
| `POST` | `/auth/login` | Login, returns JWT |
| `POST` | `/upload` | Upload a PDF, returns doc_id |
| `GET` | `/documents` | List user's documents |
| `POST` | `/chat` | Ask a question, returns answer + citations |
| `GET` | `/health` | Health check (no auth) |

See `app.py` for the OpenAPI spec.

---

## The 8-week build path

| Week | Goal | Deliverable |
|---|---|---|
| 1 | Pick idea, validate, set up repo | 5 user interviews, 1-page PRD |
| 2 | Use this starter end-to-end | Working MVP on localhost |
| 3 | Add real auth (Clerk) + database | Multi-user login |
| 4 | Add Stripe + admin dashboard | Payment flow works |
| 5 | Replace frontend with React | Polished UI |
| 6 | Get first 10 users | Soft launch |
| 7 | Polish + blog post | Portfolio-ready |
| 8 | Demo day + iterate | Public launch |

For week-by-week tasks and common mistakes, see [`../../projects/ai-engineer-capstone-guide.md`](../../projects/ai-engineer-capstone-guide.md).

---

## What makes this starter "architect-grade"

This isn't a 200-line hackathon project. It includes:

- **Production-grade error handling** — every LLM call has retry + circuit breaker
- **Observability** — structured logs, request IDs, timing
- **Cost tracking** — every query logs estimated cost
- **Security** — input validation, rate limiting per user, JWT expiry
- **Capacity model** — see ARCHITECTURE.md for the 1K/10K/100K user projections
- **Trade-offs documented** — Pinecone vs pgvector vs Weaviate (and when to migrate)

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for the full document.

---

## Paired learning resources

- **Lesson labs** — [`../../practice/level-4-rag/`](../../practice/level-4-rag/) covers every RAG technique this starter uses
- **Codebook** — [`../../workbooks/ai-engineer-codebook.md`](../../workbooks/ai-engineer-codebook.md) § 4 covers RAG patterns in detail
- **Exercises** — [`../../workbooks/exercises/section-1-llm-apis-exercises.md`](../../workbooks/exercises/section-1-llm-apis-exercises.md) extends what you build here

---

## License

MIT — use freely in your own products.
