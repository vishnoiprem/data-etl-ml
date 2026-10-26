# Decision brief: which `ai-engineering/` project to pin to the GitHub About

**Question.** Of the 40+ projects under `ai-engineering/`, which one
should we anchor the GitHub repo's "About" section on?

**Answer (TL;DR).** **`40-ai-side-hustle/`**. The four-stream AI
revenue factory — SEO content, micro-SaaS scaffolding, digital
products, print-on-demand merch — is the most directly sellable
project in the repo. The repo description should lead with it.

---

## Criteria

A "pinned" project must:

1. **Be understandable in 10 seconds** to a non-technical visitor
   (recruiter, client, GitHub searcher).
2. **Map to a real revenue path** — not just "look what I built."
3. **Have working code** (not just a README describing code that
   doesn't exist).
4. **Be a credible lead magnet** — a visitor who reads the README
   should be able to imagine hiring the author for a paid engagement.

## The 4 candidates from the ROI audit

| # | Project | 10-sec pitch | Revenue path | Working code? | Lead-magnet? |
|---|---|---|---|---|---|
| 1 | `20-cog-style-inference-api` | "A FastAPI inference server that wraps any open-weights model behind a single endpoint" | Yes (you can sell inference hours) | Yes | Weak — a client sees infra, not a service |
| 2 | `24-vertex-style-platform` | "A multi-backend ML platform with feature store, training, serving" | Yes (enterprise infra) | Yes | Weak — too big, sounds like Google |
| 3 | `38-multi-tenant-inference` | "An OpenAI-style gateway with per-tenant rate limits and cost attribution" | Yes (sell the gateway) | Yes | OK — clear "I'd pay for this" |
| 4 | **`40-ai-side-hustle`** | **"A self-contained side-hustle factory: 4 AI revenue streams, one dashboard, $0 to start"** | **Yes (the project itself is the demo)** | **Yes — and the most code in any candidate (router + 4 streams + dashboard + ledger + projections + publisher + simulator)** | **Strong — the *headline* is the product** |

## Why `40-ai-side-hustle` wins

1. **The name does the work.** "AI Side Hustle" reads as "money,"
   not "infrastructure." A non-technical GitHub visitor scans the
   repo list, sees `40-ai-side-hustle`, and clicks.
2. **It's a complete system, not a component.** The other 3 are
   *infrastructure you'd embed* in someone else's product. This
   one is a *product you can describe to a client and demo in
   10 minutes*: "I built a 4-stream revenue factory. The SEO
   stream writes 30 articles/month. The digital-product stream
   produces 10 Gumroad listings/week. Want me to set one up for
   you?"
3. **The code is real.** 7 source files in `src/` (router, ledger,
   projector, publisher, 4 stream modules), 2 scripts
   (`run_factory.py`, `publish_checklist.py`), a `tests/` dir,
   `Makefile`, `docs/`, `output/`, `sample_data/`. Other repos
   in the portfolio have fewer files.
4. **The README leads with the value.** Compare:
   - `20-cog-style-inference-api/README.md` opens with
     "Inference server wrapped in FastAPI" — infra talk
   - `40-ai-side-hustle/README.md` opens with
     "Make money with AI on day one. No audience required."
     — outcome talk

   Same engineering quality, different first impression.
5. **It's self-contained with stub mode.** A client can clone
   and run it without an API key. The `simulator.py` produces
   realistic-looking output. This is the *demo* advantage.
6. **It maps to the 4-1-1 rule of portfolio marketing.** Every
   portfolio has 1 project that's the "headline." This should
   be it.

## What changes in the GitHub About

The previous About was a topic dump:

> Production-style data engineering, ML, LLM & agentic-AI
> projects. Spark · Kafka · Flink · Airflow · AWS Bedrock ·
> LangGraph · RAG · multi-agent.

That description reads as "I dabble." A visitor doesn't know
which project to click. The new description leads with the
anchor project:

> An AI side-hustle factory (40-ai-side-hustle) plus the data
> engineering, ML, RAG, and multi-agent infrastructure behind it.
> 40+ production-style projects. Spark · Kafka · Flink ·
> LangGraph · AWS Bedrock.

Notice: the breadth is preserved (still Spark, Kafka, Flink,
LangGraph, Bedrock), but the *first sentence* names a specific
project and what it does. The non-technical visitor has an
entry point; the technical visitor sees the breadth.

## Risks of pinning `40-ai-side-hustle`

- **It's not the most "serious" project.** A staff-aug client
  looking for an inference engineer might prefer `20-cog-style-
  inference-api` as the headline. The fix: keep the breadth in
  the topics list (`ai-agents`, `mlops`, `llm`, `rag`,
  `langgraph`, `inference`); the description change only adds
  one anchor.
- **The 4 streams are aspirational.** `40-ai-side-hustle` has
  the *scaffolding* for 4 streams but not 4 production-deployed
  streams pulling real revenue. The README is honest about
  "offline-stub mode by default" — that honesty is the point.
  Don't claim revenue that isn't there.
- **A recruiter might find it too "indie."** The fix is the
  secondary projects visible in the repo list. The headline
  gets the click; the breadth keeps the credibility.

## What I'd do (3 actions, ordered by ROI)

1. **Update `.github/REPO_ABOUT.md`** with the new description
   and a topics list that adds `ai-side-hustle`, `revenue`,
   `ai-tools` (so the new project is searchable on its own
   terms) while keeping the existing breadth topics.
2. **Pin the repo** (GitHub → About → "Pinned repositories"
   on the user profile) so visitors see `40-ai-side-hustle` as
   the top item. This is a user action in the GitHub UI, not
   something we can do from code.
3. **Add a 1-line banner** in the root `README.md` that links
   to `ai-engineering/40-ai-side-hustle/`, so visitors who
   open the repo get the anchor without searching.

## What this is NOT

- **Not the only project worth selling.** All 40 projects in
  `ai-engineering/` are useful in a conversation. The pin is
  the *headline*, not the only pitch.
- **Not a code change.** Pinning a project is a UI action on
  GitHub. The repo-side change is a single `REPO_ABOUT.md`
  update + a 1-line `README.md` banner.
- **Not a permanent choice.** If a new project becomes the
  clear income leader in 6 months (e.g. `36-together-gpu-cloud`
  if you start a GPU rental business, or `38-multi-tenant-
  inference` if you productize the gateway), re-pin then.

---

**Last updated:** 2026-10-13  
**License:** MIT — use freely in your own courses, prototypes, and products.  
