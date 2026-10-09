# AI Data Analyst — Capstone Starter

> **Build "ChatGPT for your spreadsheets" in 8 weeks using this starter.**

This is the runnable starter for **Capstone Template 4** from [`../../projects/ai-engineer-capstone-guide.md`](../../projects/ai-engineer-capstone-guide.md). The starter gives you a complete working skeleton: upload a CSV, ask a question in plain English, GPT-4o writes pandas code, the code runs in a sandboxed subprocess, the result is returned as a table + chart. Your job is to extend it to a production-grade, paid SaaS over 8 weeks.

---

## What you start with

A working AI Data Analyst with:

- ✅ **CSV upload** — up to 100MB, automatic schema detection
- ✅ **Natural language questions** — "What's the average revenue by region?"
- ✅ **Code interpreter** — GPT-4o writes Python (pandas + plotly); sandboxed subprocess runs it
- ✅ **Auto-visualization** — chart auto-generated for any result with numeric columns
- ✅ **Insight extraction** — plain-English summary of the result
- ✅ **Backend** — FastAPI with `/datasets`, `/analyze`, `/chart` endpoints
- ✅ **Auth** — JWT-based auth (replace with Clerk/Auth0 in production)
- ✅ **Persistence** — Postgres for users, datasets, query history
- ✅ **Tests** — pytest suite covering the dataframe ops
- ✅ **Docker** — Dockerfile + docker-compose for local dev
- ✅ **Architecture doc** — [`ARCHITECTURE.md`](./ARCHITECTURE.md) with system diagram, cost model, capacity model

What you add in 8 weeks:

- [ ] Replace JWT with Clerk
- [ ] Add Stripe for payments ($29/mo)
- [ ] Add multi-file analysis (join across CSVs)
- [ ] Add database connections (Postgres, MySQL, BigQuery)
- [ ] Add scheduled reports (weekly email digest)
- [ ] Add team workspaces (shared datasets)
- [ ] Add an "analyst agent" that can run multi-step analyses
- [ ] Add PDF export of analysis reports
- [ ] Add Saved queries / query library
- [ ] Deploy to Railway / Render
- [ ] Get 10 paying users

---

## How to run locally

```bash
# 1. Install dependencies
cd 04-ai-data-analyst
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Set environment variables
cp .env.example .env
# Add OPENAI_API_KEY

# 3. Start the server
uvicorn app:app --reload

# 4. Open the UI
open http://localhost:8000
```

---

## Folder structure

```
04-ai-data-analyst/
├── README.md               # this file
├── ARCHITECTURE.md         # system design + cost model + capacity model
├── app.py                  # FastAPI entry point
├── code_executor.py        # sandboxed Python subprocess execution
├── dataframe_ops.py        # pandas operations + schema detection
├── visualizer.py           # chart generation (Plotly)
├── frontend/
│   └── index.html          # minimal UI (replace with React in week 5)
├── tests/
│   └── test_agent.py       # pytest suite
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
| `POST` | `/datasets/upload` | Upload a CSV, returns dataset_id |
| `GET` | `/datasets` | List user's datasets |
| `GET` | `/datasets/:id/schema` | Get inferred column types + sample |
| `POST` | `/analyze` | Ask a question, returns answer + code + chart |
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

- **Sandboxed code execution** — subprocess with timeout, restricted globals, no network
- **Schema-aware prompting** — column types + samples passed to GPT-4o, so it knows the data
- **Auto-visualization** — every result with 1-2 numeric columns auto-plots
- **Pandas safety** — no `eval`, no shell expansion, code is parsed before execution
- **Observability** — every LLM call + every code execution logged with latency + cost
- **Capacity model** — see ARCHITECTURE.md for the 1K/10K/100K user projections
- **Trade-offs documented** — subprocess vs Pyodide, GPT-4o vs Llama for code, local files vs S3

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for the full document.

---

## Paired learning resources

- **Lesson labs** — [`../../practice/level-4-rag/`](../../practice/level-4-rag/) covers the data-side patterns this starter uses
- **Codebook** — [`../../workbooks/ai-engineer-codebook.md`](../../workbooks/ai-engineer-codebook.md) § 9 covers file loaders and queues
- **Exercises** — [`../../workbooks/exercises/section-9-utilities-exercises.md`](../../workbooks/exercises/section-9-utilities-exercises.md) extends what you build here

---

## License

MIT — use freely in your own products.
