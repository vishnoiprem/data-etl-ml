# AI Research Assistant — Capstone Starter

> **Build an autonomous research agent in 8 weeks using this starter.**

This is the runnable starter for **Capstone Template 2** from [`../../projects/ai-engineer-capstone-guide.md`](../../projects/ai-engineer-capstone-guide.md). The starter gives you a complete working skeleton: input a research question, the agent searches the web (Tavily), scrapes top sources, synthesizes a cited report, and saves it. Your job is to extend it to a production-grade, paid SaaS over 8 weeks.

---

## What you start with

A working AI Research Assistant with:

- ✅ **ReAct agent** — Reason/Act loop using LangGraph with explicit state
- ✅ **Tool belt** — Tavily web search, web scraper (httpx + trafilatura), document loader (PDF)
- ✅ **Planning** — the agent decomposes a question into 5–10 sub-questions
- ✅ **Cited report** — every claim has a `[1]`, `[2]` source link
- ✅ **Streaming** — token-by-token report generation (SSE-ready)
- ✅ **Backend** — FastAPI with `/research`, `/reports`, `/report/:id` endpoints
- ✅ **Auth** — JWT-based auth (replace with Clerk/Auth0 in production)
- ✅ **Persistence** — Postgres for users, reports, citations
- ✅ **Tests** — pytest suite covering the agent loop
- ✅ **Docker** — Dockerfile + docker-compose for local dev
- ✅ **Architecture doc** — [`ARCHITECTURE.md`](./ARCHITECTURE.md) with system diagram, cost model, capacity model

What you add in 8 weeks:

- [ ] Replace JWT with Clerk
- [ ] Add Stripe for payments ($49/mo)
- [ ] Add custom research templates (legal, medical, due-diligence)
- [ ] Add PDF export of the final report
- [ ] Add team collaboration (share reports, comments)
- [ ] Add scheduled/recurring research (morning brief)
- [ ] Add Slack/Email delivery of finished reports
- [ ] Deploy to Railway / Render
- [ ] Get 10 paying users

---

## How to run locally

```bash
# 1. Install dependencies
cd 02-ai-research-assistant
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Set environment variables
cp .env.example .env
# Add OPENAI_API_KEY and TAVILY_API_KEY

# 3. Start the server
uvicorn app:app --reload

# 4. Open the UI
open http://localhost:8000
```

---

## Folder structure

```
02-ai-research-assistant/
├── README.md               # this file
├── ARCHITECTURE.md         # system design + cost model + capacity model
├── app.py                  # FastAPI entry point
├── agent.py                # the ReAct / LangGraph research agent
├── tools.py                # Tavily search, scrape, document load
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
| `POST` | `/research` | Start a research job, returns job_id |
| `GET` | `/research/:id/stream` | SSE stream of agent progress |
| `GET` | `/reports` | List user's past reports |
| `GET` | `/report/:id` | Get a specific report + sources |
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

- **LangGraph state machine** — explicit nodes for plan / search / synthesize / finalize
- **Tool budget enforcement** — max 30 searches per report (cost control)
- **Source diversity** — agent avoids using the same domain > 3 times
- **Observability** — every tool call logged with latency, every LLM call cost-tracked
- **Streaming** — SSE-ready so the user sees the report write itself
- **Capacity model** — see ARCHITECTURE.md for the 1K/10K/100K user projections
- **Trade-offs documented** — Tavily vs Serper vs Bing, ReAct vs plan-and-execute, GPT-4o vs Claude

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for the full document.

---

## Paired learning resources

- **Lesson labs** — [`../../practice/level-5-agents/`](../../practice/level-5-agents/) covers every agent technique this starter uses
- **Codebook** — [`../../workbooks/ai-engineer-codebook.md`](../../workbooks/ai-engineer-codebook.md) § 5 covers ReAct, plan-and-execute, LangGraph
- **Exercises** — [`../../workbooks/exercises/section-5-agents-exercises.md`](../../workbooks/exercises/exercises/section-5-agents-exercises.md) extends what you build here

---

## License

MIT — use freely in your own products.
