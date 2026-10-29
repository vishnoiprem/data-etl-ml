# Architecture — AI Content Generator

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
                        │ /generate       │
                        │ /articles       │
                        │ /article/:id    │
                        └────┬──────┬─────┘
                             │      │
                  ┌──────────┘      └──────────┐
                  ▼                             ▼
         ┌─────────────────┐          ┌─────────────────┐
         │  PostgreSQL     │          │  Researcher     │
         │  (Neon free)    │          │  (Tavily +      │
         ├─────────────────┤          │   GPT-4o-mini)  │
         │ - users         │          └────────┬────────┘
         │ - articles      │                   │
         │ - seo_reports   │                   ▼
         │ - brand_voice   │          ┌─────────────────┐
         └─────────────────┘          │   Tavily API    │
                                      │  (SERP data)    │
                                      └────────┬────────┘
                                               │
                                               ▼
                                      ┌─────────────────┐
                                      │   Writer        │
                                      │  (GPT-4o)       │
                                      │  outline-first  │
                                      └────────┬────────┘
                                               │
                                               ▼
                                      ┌─────────────────┐
                                      │   Optimizer     │
                                      │  (keyword, meta, │
                                      │   readability)   │
                                      └─────────────────┘
```

## Component choices

| Component | Choice | Alternative | Why we picked this |
|---|---|---|---|
| SERP research | Tavily | Serper, DataForSEO, manual | Tuned for AI, returns clean content, has free tier |
| Outline LLM | GPT-4o-mini | GPT-4o, Claude Haiku | Cheap, fast, good enough for outlines |
| Article LLM | GPT-4o | Claude 3.5 Sonnet | Best long-form, strong instruction following |
| SEO scoring | Custom (Python) | Surfer SEO API, Clearscope | Free, good enough for MVP |
| Brand voice (optional) | RAG over past posts | Fine-tuned model | Cheaper, no training pipeline |
| Backend | FastAPI | Flask, Django | Async, OpenAPI, Pydantic |
| Database | Postgres (Neon) | MongoDB, SQLite | Relational + free tier |
| Auth | JWT → Clerk | Auth0, Supabase | Clerk has 5-min setup, social logins, MFA |
| Hosting | Railway | Render, Fly.io | $5/mo free tier, Postgres included |

## The generation pipeline (5 stages)

```
1. INPUT     - topic + target keyword
2. RESEARCH  - Tavily fetches top 10 SERP results, extracts H1/H2, summary
3. OUTLINE   - GPT-4o-mini generates an outline (8-12 sections, FAQs)
4. WRITE     - GPT-4o writes the article section by section, citing research
5. OPTIMIZE  - keyword density, meta, JSON-LD, readability scoring
```

**Why outline-first?** Empirically, outline-first articles are 30-50% better than freeform generation. The outline forces structure, ensures topic coverage, and gives the writer per-section context.

## Data flow: generate an article

```
1. User POSTs /generate with {topic, keyword, length_words, tone}
2. researcher.research(keyword)
   - Tavily top 10 SERP results
   - For each, extract H1/H2 + 100-word summary
   - GPT-4o-mini: identify the "angle" competitors miss
3. writer.outline(topic, research, length_words)
   - GPT-4o-mini: 8-12 section outline with target keywords per section
4. writer.write(outline, research)
   - For each section, GPT-4o writes 100-200 words
   - Stream tokens if requested
5. optimizer.score(article, keyword)
   - Keyword density (target 1-2%)
   - Flesch reading ease
   - Heading structure (H1/H2/H3 hierarchy)
   - Meta title (50-60 chars), meta description (150-160 chars)
6. optimizer.generate_meta(article, keyword)
   - GPT-4o-mini: 5 candidate meta titles + 5 meta descriptions
   - Pick the best
7. Save to articles + seo_reports tables
8. Return article + SEO report
```

## Capacity model

| Users | Articles/day | Searches/day | Compute | Storage | Monthly cost |
|---|---|---|---|---|---|
| 10 | 50 | 500 | Railway free | Neon free | $0 |
| 100 | 500 | 5K | Railway $20 | Neon free | $20 |
| 1K | 5K | 50K | Railway $100, 4 workers | Neon $15 | $115 |
| 10K | 50K | 500K | Railway $500, autoscaling | Neon $50 | $550 |
| 100K | 500K | 5M | Railway $2K, dedicated workers | Neon $200 | $2,200 |

**Per article (avg, 1500 words):**
- 10 Tavily searches = $0.025
- 1 outline call (GPT-4o-mini, 2K+500) = $0.0006
- 1 research-summary call (GPT-4o-mini, 3K+1K) = $0.0011
- 1 article write call (GPT-4o, 8K+2K) = $0.04
- 1 SEO scoring call (GPT-4o-mini, 2K+500) = $0.0006
- 1 meta-gen call (GPT-4o-mini, 1.5K+500) = $0.0005
- **Total per article = ~$0.07**

**Scaling cliffs:**

- **100 users**: Need to add Redis for article cache (same topic + keyword → same article)
- **1K users**: Need to move long jobs to a queue (article gen takes 30-60s)
- **10K users**: Need to add per-user concurrency limits (5 free, 50 paid)
- **100K users**: Need to consider fine-tuning a smaller model on your brand voice

## Cost model (per 1K articles)

Assumes: avg 1500-word article.

| Component | Cost per 1K articles |
|---|---|
| Tavily SERP research | $25 |
| GPT-4o-mini (outline + research + scoring + meta) | $2 |
| GPT-4o article write | $40 |
| Postgres writes | $1 |
| **Total per 1K articles** | **$68** |

At $39/mo per user with 50 articles/month = $0.78 per article. Cost $0.07. **91% margin.**

## SEO scoring rubric

| Metric | Target | Implementation |
|---|---|---|
| Keyword in title | yes | string match |
| Keyword in H1 | yes | parse first H1 |
| Keyword in first 100 words | yes | substring match |
| Keyword density | 1-2% | kw_count / total_words |
| H2/H3 hierarchy | balanced | parse all headings |
| Word count | meets target | len(words) |
| Flesch reading ease | 60-70 | textstat |
| Sentence length | < 20 words avg | split on `.` |
| Paragraph length | < 100 words | quality parens |
| Internal links | >= 3 | count `](` substrings |
| Meta title length | 50-60 chars | len |
| Meta description length | 150-160 chars | len |

Each metric contributes to a 0-100 SEO score. Color-code: < 50 red, 50-75 yellow, 75+ green.

## Security checklist

- [x] JWT tokens with expiry (replace with Clerk for refresh tokens)
- [x] Per-user data isolation (user_id filter on every query)
- [x] Input validation (Pydantic, length caps)
- [ ] Rate limiting per user (add in week 4)
- [ ] Plagiarism check before publishing (Copyscape API or local check)
- [ ] Brand-voice RAG: redact PII from training data
- [ ] HTTPS only (handled by hosting platform)
- [ ] CORS restricted to your domain
- [ ] Watermark AI-generated content (Google's AI label requirements)

## Observability checklist

- [x] Structured logs (JSON, request_id, user_id, timing)
- [x] Every LLM call logged with token counts + cost
- [x] Every Tavily call logged with latency
- [x] Per-stage timing (research → write → optimize)
- [x] SEO score distribution logged
- [ ] Add LangSmith for end-to-end trace (week 3)
- [ ] Add Sentry for error tracking (week 3)
- [ ] Add PostHog for product analytics (week 4)
- [ ] Add an eval pipeline: held-out set of (topic, expected keywords) (week 5)
- [ ] Add uptime monitoring (week 4)

## Failure modes

| Failure | Detection | Recovery |
|---|---|---|
| Tavily rate limit | 429 | Backoff 2x, max 3 retries, fall back to Serper |
| Tavily down | 5xx | Skip research, generate from outline + general knowledge |
| OpenAI rate limit | 429 | Backoff 2x, max 3 retries, then job fails |
| OpenAI down | 5xx | Persist state, mark job `paused`, resume when API back |
| Article has no keyword in H1 | SEO score | Auto-add H1 with keyword, regenerate |
| Article too short | SEO score | Loop: ask LLM to "expand to N words" |
| Meta title too long | SEO score | Trim to 60 chars |
| User asks 1000 articles/day | rate limit | Per-user concurrency limit |
| Duplicate content (same topic/keyword twice) | (cost) | Cache + return cached article |
| LLM hallucinates statistics | eval set | Cross-check every [n] against SERP research |

## When to migrate off this stack

| Trigger | Migration |
|---|---|
| >$2K/mo in OpenAI | Add Claude Haiku as fallback, use prompt caching for the system prompt |
| >10K users | Move auth to Clerk, add team workspaces, add content calendar |
| EU users | Move to EU region (OpenAI EU, Tavily has no EU — replace with EU provider) |
| Need brand voice | Add RAG over past posts (FAISS / Pinecone) |
| Need on-prem | Replace OpenAI with self-hosted Llama 3 70B (cut cost 80%) |
| Need direct publish | Add WordPress/Medium/Ghost integrations |

## Trade-off log (ADRs)

- **ADR-001**: Outline-first over freeform generation — better articles, lower total cost (shorter prompts per section).
- **ADR-002**: Tavily over DataForSEO — Tavily is 10× cheaper and tuned for AI. DataForSEO gives richer SERP data (volume, difficulty) but overkill for MVP.
- **ADR-003**: GPT-4o for write, GPT-4o-mini for everything else — writing is the only thing that needs the best model. Outline / research / scoring are easy enough for mini.
- **ADR-004**: Custom SEO scoring over Surfer SEO API — Surfer is $69/mo, ours is free and good enough. Migrate to Surfer if customers want keyword volume data.
- **ADR-005**: RAG over fine-tuning — RAG is cheaper, faster to update, and doesn't require training infra. Fine-tune only at >10K articles / month.

## Future work

- [ ] Add brand-voice RAG over your existing content
- [ ] Add one-click publish to WordPress / Medium / Ghost
- [ ] Add content calendar (plan 30 posts in advance)
- [ ] Add multi-language support (50+ languages)
- [ ] Add image generation (DALL-E 3 or Stable Diffusion) for hero + inline
- [ ] Add internal-link suggestions from your existing posts
- [ ] Add a "competitor gap" report (what's ranking that you're missing)
- [ ] Add a "headline A/B" generator (10 variants + CTR prediction)
- [ ] Add social-post generation (Twitter thread, LinkedIn post from the same article)
- [ ] Add an SEO score history chart per article
- [ ] Add team workspaces (shared brand voice)
- [ ] Add a Notion-style editor for post-generation tweaks