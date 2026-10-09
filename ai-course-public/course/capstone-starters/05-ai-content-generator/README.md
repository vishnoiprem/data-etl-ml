# AI Content Generator — Capstone Starter

> **Build an SEO blog generator in 8 weeks using this starter.**

This is the runnable starter for **Capstone Template 5** from [`../../projects/ai-engineer-capstone-guide.md`](../../projects/ai-engineer-capstone-guide.md). The starter gives you a complete working skeleton: enter a topic + target keyword, the agent researches top SERP results via Tavily, GPT-4o writes an SEO-optimized article, the optimizer scores keyword density, meta tags, and readability. Your job is to extend it to a production-grade, paid SaaS over 8 weeks.

---

## What you start with

A working AI Content Generator with:

- ✅ **Topic + keyword input** — the only inputs you need
- ✅ **SERP research** — Tavily fetches top 10 results for the keyword
- ✅ **SEO-optimized article** — 1500 words, H1/H2/H3 structure, internal links, FAQs
- ✅ **Meta generation** — title tag, meta description, OG tags
- ✅ **Keyword optimization** — density check, LSI keywords, heading coverage
- ✅ **Brand voice (optional)** — RAG over your past posts for tone matching
- ✅ **Backend** — FastAPI with `/generate`, `/articles`, `/article/:id` endpoints
- ✅ **Auth** — JWT-based auth (replace with Clerk/Auth0 in production)
- ✅ **Persistence** — Postgres for users, articles, research notes
- ✅ **Tests** — pytest suite covering the optimizer
- ✅ **Docker** — Dockerfile + docker-compose for local dev
- ✅ **Architecture doc** — [`ARCHITECTURE.md`](./ARCHITECTURE.md) with system diagram, cost model, capacity model

What you add in 8 weeks:

- [ ] Replace JWT with Clerk
- [ ] Add Stripe for payments ($39/mo)
- [ ] Add brand-voice RAG over your existing content
- [ ] Add one-click publish to WordPress / Medium / Ghost
- [ ] Add content calendar (plan 30 posts in advance)
- [ ] Add multi-language support (50+ languages)
- [ ] Add image generation (DALL-E 3 or Stable Diffusion) for hero + inline
- [ ] Add internal-link suggestions from your existing posts
- [ ] Add a "competitor gap" report (what's ranking that you're missing)
- [ ] Deploy to Railway / Render
- [ ] Get 10 paying users

---

## How to run locally

```bash
# 1. Install dependencies
cd 05-ai-content-generator
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
05-ai-content-generator/
├── README.md               # this file
├── ARCHITECTURE.md         # system design + cost model + capacity model
├── app.py                  # FastAPI entry point
├── researcher.py           # SERP research + outline generation
├── writer.py               # Article generation (GPT-4o)
├── optimizer.py            # SEO scoring + meta generation
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
| `POST` | `/generate` | Generate an article from a topic + keyword |
| `GET` | `/articles` | List user's past articles |
| `GET` | `/articles/:id` | Get a specific article + SEO report |
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

- **Real SERP research** — pulls top 10 results, extracts headings, finds the angle competitors miss
- **Outline-first generation** — better articles when you plan first, write second
- **SEO scoring** — keyword density, heading coverage, meta length, readability (Flesch)
- **Meta + OG generation** — title, description, og:title, og:description, og:image
- **JSON-LD schema** — Article, FAQPage, BreadcrumbList for rich results
- **Observability** — every LLM call + every Tavily call logged with latency + cost
- **Capacity model** — see ARCHITECTURE.md for the 1K/10K/100K user projections
- **Trade-offs documented** — Tavily vs Serper vs DataForSEO, outline-first vs freeform, RAG vs prompt

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for the full document.

---

## Paired learning resources

- **Lesson labs** — [`../../practice/level-3-prompt-engineering/`](../../practice/level-3-prompt-engineering/) covers the prompt patterns this starter uses
- **Codebook** — [`../../workbooks/ai-engineer-codebook.md`](../../workbooks/ai-engineer-codebook.md) § 3 covers CRAFT and outline patterns
- **Exercises** — [`../../workbooks/exercises/section-3-prompt-engineering-exercises.md`](../../workbooks/exercises/section-3-prompt-engineering-exercises.md) extends what you build here

---

## License

MIT — use freely in your own products.