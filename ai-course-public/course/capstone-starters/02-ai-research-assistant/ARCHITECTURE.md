# Architecture — AI Research Assistant

> **The design decisions behind the starter.** Read this before you change anything.

## System diagram

```
                        ┌─────────────────┐
                        │   React UI      │
                        │  (or HTML)      │
                        └────────┬────────┘
                                 │ HTTPS (SSE for streaming)
                                 ▼
                        ┌─────────────────┐
                        │   FastAPI       │
                        │   (uvicorn)     │
                        ├─────────────────┤
                        │ /research       │
                        │ /reports        │
                        │ /report/:id     │
                        │ /auth/*         │
                        └────┬──────┬─────┘
                             │      │
                  ┌──────────┘      └──────────┐
                  ▼                             ▼
         ┌─────────────────┐          ┌─────────────────┐
         │  PostgreSQL     │          │   LangGraph     │
         │  (Neon free)    │          │   State Machine │
         ├─────────────────┤          ├─────────────────┤
         │ - users         │          │ 1. Plan         │
         │ - research_jobs │          │ 2. Search       │
         │ - reports       │          │ 3. Synthesize   │
         │ - sources       │          │ 4. Critique     │
         └─────────────────┘          │ 5. Finalize     │
                                      └────┬──────┬─────┘
                                            │      │
                              ┌─────────────┘      └────────────┐
                              ▼                                  ▼
                     ┌─────────────────┐               ┌─────────────────┐
                     │   Tavily API    │               │   OpenAI API    │
                     │   (web search)  │               ├─────────────────┤
                     └────────┬────────┘               │ - gpt-4o        │
                              │                        │ - gpt-4o-mini   │
                              ▼                        └─────────────────┘
                     ┌─────────────────┐
                     │  Web Scraper    │
                     │  (httpx +       │
                     │   trafilatura)  │
                     └─────────────────┘
```

## Component choices

| Component | Choice | Alternative | Why we picked this |
|---|---|---|---|
| Agent framework | LangGraph | LangChain AgentExecutor, CrewAI | Explicit state graph, easier to debug, deterministic |
| Web search | Tavily | Serper, Bing, Google CSE | Tuned for AI agents, returns clean content, has free tier |
| LLM (planner) | GPT-4o | Claude 3.5 Sonnet, o1 | Strong planning, fast enough, well-priced |
| LLM (synthesizer) | GPT-4o-mini | GPT-4o, Claude Haiku | 30× cheaper, near-equal for synthesis |
| Web scraper | trafilatura + httpx | BeautifulSoup, Playwright | Fast, no browser overhead, robust to bad HTML |
| Backend | FastAPI | Flask, Django | Async-native, OpenAPI built-in, great for SSE |
| Database | Postgres (Neon) | MongoDB, SQLite | Relational data (jobs, sources, citations) + free tier |
| Streaming | SSE | WebSockets, polling | Simpler than WS, works behind CDN |
| Auth | JWT (in starter) → Clerk in prod | Auth0, Supabase | Clerk has 5-min setup, social logins, MFA |
| Hosting | Railway | Render, Fly.io, Vercel | $5/mo free tier, Postgres included, easy deploy |

## Agent state machine

```
[START]
   │
   ▼
[plan] ◀─────────────────────┐
   │                          │
   ▼                          │
[search] (loop until budget)  │
   │                          │
   ▼                          │
[scrape]                      │
   │                          │
   ▼                          │
[synthesize] ──── needs_more? │
   │                          │
   ▼                          │
[critique] ──────── retry ────┘
   │
   ▼
[finalize]
   │
   ▼
[END]
```

Each node writes to the shared state. The graph is fully checkpointed to Postgres so a crashed run can resume from the last node.

## Data flow: a research request

```
1. User POSTs /research with {question: "Compare Stripe and Adyen"}
2. FastAPI validates, creates research_job row, returns job_id
3. Background task starts the LangGraph run
4. [plan] node: GPT-4o decomposes into 6 sub-questions
5. [search] node: for each sub-question, call Tavily (3 results)
6. [scrape] node: for each unique URL, fetch + extract text (max 30 sources)
7. [synthesize] node: GPT-4o-mini writes a section per sub-question
8. [critique] node: GPT-4o checks for gaps, may add 1-2 more searches
9. [finalize] node: assemble into 1500-word report with [1], [2] citations
10. Report row written to Postgres with embedded sources
11. SSE event "report_ready" pushed to client
12. User GETs /report/:id to read
```

## Capacity model

| Users | Reports/day | Searches/day | Compute | Storage | Monthly cost |
|---|---|---|---|---|---|
| 10 | 30 | 300 | Railway free | Neon free | $0 |
| 100 | 300 | 3K | Railway $20 | Neon free | $20 |
| 1K | 3K | 30K | Railway $100, 4 workers | Neon $15 | $115 |
| 10K | 30K | 300K | Railway $500, autoscaling | Neon $50 | $550 |
| 100K | 300K | 3M | Railway $2K, dedicated workers | Neon $200 | $2,200 |

**Per report (avg):**
- 1 plan call (GPT-4o) = $0.05
- 6 sub-question searches × 3 results = 18 Tavily searches = $0.05
- 6 scrapes (httpx, mostly free)
- 6 synthesis calls (GPT-4o-mini) = $0.18
- 1 critique call (GPT-4o-mini) = $0.03
- 1 finalize call (GPT-4o) = $0.10
- **Total per report = ~$0.41**

**Scaling cliffs:**

- **100 users**: Need to add Redis for SSE pub/sub (single uvicorn is fine)
- **1K users**: Need to move long jobs to a queue (Celery + Redis or RQ)
- **10K users**: Need to add multi-region Tavily (latency), LLM response caching
- **100K users**: Need to consider fine-tuning a smaller planner (cut $0.05/report)

## Cost model (per 1K reports)

Assumes: avg 6 sub-questions, 18 searches, 8 LLM calls, 1500 words out.

| Component | Cost per 1K reports |
|---|---|
| GPT-4o (plan + finalize) | $150 |
| GPT-4o-mini (synthesize + critique) | $210 |
| Tavily search (18K searches) | $180 (Pro tier) |
| Web scraping (bandwidth) | $5 |
| Postgres writes (1K × 30 rows) | $1 |
| **Total per 1K reports** | **$546** |

At $49/mo per user with 30 reports/month = $49 / 30 = **$1.63 per report**. Cost $0.41. **75% margin.**

## Security checklist

- [x] JWT tokens with expiry (replace with Clerk for refresh tokens)
- [x] Per-user data isolation (user_id filter on every query)
- [x] Input validation (Pydantic)
- [ ] Rate limiting per user (add in week 4)
- [ ] SSRF protection on user-supplied URLs (scraping from arbitrary URLs is dangerous)
- [ ] Domain allowlist / denylist for scrapes (avoid scraping sensitive sites)
- [ ] PII redaction before sending scraped content to OpenAI
- [ ] HTTPS only (handled by hosting platform)
- [ ] CORS restricted to your domain
- [ ] Webhook signatures for Tavily callbacks (when used)

## Observability checklist

- [x] Structured logs (JSON, request_id, user_id, timing)
- [x] Every LLM call logged with token counts + cost
- [x] Every Tavily call logged with latency
- [x] Agent node transitions logged (so you can replay a run)
- [ ] Add LangSmith for end-to-end trace visualization (week 3)
- [ ] Add Sentry for error tracking (week 3)
- [ ] Add PostHog for product analytics (week 4)
- [ ] Add a "report quality" eval pipeline (week 5)
- [ ] Add uptime monitoring (week 4)

## Failure modes

| Failure | Detection | Recovery |
|---|---|---|
| Tavily rate limit | 429 response | Backoff 2x, max 3 retries, fall back to Serper |
| Tavily down | 5xx | Show "search temporarily unavailable" + retry queue |
| OpenAI rate limit | 429 | Backoff 2x, max 3 retries, then job fails with retryable error |
| OpenAI down | 5xx | Persist state, mark job `paused`, resume when API back |
| Scraper gets 403/blocked | status_code | Skip that source, log, continue with others |
| Scraper gets 1GB HTML | OOM | Reject responses > 5MB |
| User sends 1M-token question | OOM in planner | Truncate to 8K tokens before plan call |
| User has 1000s of concurrent jobs | DB CPU | Per-user concurrency limit (3 free, 30 paid) |
| LLM hallucinates sources | Eval set alerts | Cross-check every citation URL against scraped sources |
| Job runs > 10 min | Watchdog | Auto-pause, alert, save partial report |

## When to migrate off this stack

| Trigger | Migration |
|---|---|
| >$2K/mo in OpenAI | Add Claude Haiku + prompt caching; route plan to o1-mini for hard cases |
| >1K concurrent jobs | Move from per-request uvicorn workers to dedicated job workers (Celery) |
| >10K users | Move auth to Clerk, add team workspaces, add scheduled research |
| Users in EU | Move to EU region (OpenAI EU, Tavily has no EU — replace with EU provider) |
| Scraping gets blocked | Move from direct scraping to a proxy (Bright Data, ScraperAPI) |
| Need on-prem | Replace OpenAI with self-hosted Llama 3 70B (cut cost 80%, lose 20% quality) |

## Trade-off log (ADRs)

- **ADR-001**: LangGraph over LangChain AgentExecutor — LangGraph is deterministic, debuggable, and supports checkpointing. AgentExecutor is a black box.
- **ADR-002**: Tavily over Serper — Tavily returns clean text snippets, purpose-built for agents. Serper is closer to raw Google.
- **ADR-003**: GPT-4o for planner, GPT-4o-mini for synthesizer — planning needs reasoning, synthesis is mostly formatting. Saves 60% on LLM cost vs all-GPT-4o.
- **ADR-004**: SSE over WebSockets — SSE is one-way (server → client) which is all we need. WS adds reconnect/heartbeat complexity.
- **ADR-005**: Direct scraping over Playwright — Playwright is 50× heavier and most sources work with simple HTTP. Fall back to Playwright for JS-heavy sites.
- **ADR-006**: Postgres for everything — citations and sources are relational. Don't split into a separate store.

## Future work

- [ ] Add multi-modal research (image + text)
- [ ] Add PDF/document upload as a source
- [ ] Add custom research templates (legal, medical, due-diligence)
- [ ] Add PDF export of the final report
- [ ] Add team collaboration (share reports, comments)
- [ ] Add scheduled/recurring research (morning brief)
- [ ] Add Slack/Email delivery of finished reports
- [ ] Add Notion / Google Docs export
- [ ] Add a "trust score" for each source
- [ ] Add multi-language support
