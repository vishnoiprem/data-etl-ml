# Architect Challenges — 10 Cross-Cutting System Design Problems

> **The questions that separate a senior engineer from a staff engineer.**
> Each challenge here has been asked in a real interview, in a real design review, or in a real production incident. Your job is to design the system — with numbers, trade-offs, and ADRs.

These challenges are not tied to a specific codebook section. They pull from **everything** you've learned: LLM APIs, production patterns, RAG, agents, vector DBs, deployment, observability, and the cheatsheets.

For each challenge, write a 1-2 page design doc. Include: capacity model, cost model, ADRs (key trade-offs), failure modes, and a "what would I monitor" section.

---

## How to use these

1. **Read the challenge once**
2. **Time-box yourself** — 60-90 min per challenge, max
3. **Write the design doc** with these sections:
   - System diagram
   - Capacity model (1K, 10K, 100K, 1M users)
   - Cost model (per-request, per-user, per-month at scale)
   - 3-5 key trade-offs (with ADRs explaining the choice)
   - 3-5 failure modes (with detection + recovery)
   - What you'd monitor (3-5 metrics + alerts)
4. **Then go back and find your blind spots** — what did you miss?

**Time per challenge:** 60-90 min.
**Total time for all 10:** 12-15 hours.

---

## Challenge 1: Design ChatGPT's Backend

**Brief:** Design the backend for a ChatGPT-class consumer chatbot. 100M MAU, 1B queries/day, average 500-token input + 300-token output.

### What to design

- The API layer (auth, rate limiting, request validation)
- The LLM inference path (caching, routing, fallback)
- The conversation memory (per-user history, KV cache reuse)
- The infrastructure (servers, regions, autoscaling)
- The cost model at 1B queries/day (this is the killer)

### Numbers to nail

- p50 / p95 / p99 latency target (you choose, defend it)
- Tokens/second you need to serve (back-compute from queries/day)
- Cost per query (LLM, infra, bandwidth, storage)
- Monthly bill at 100M MAU (will be eye-watering)

### Trade-offs to make

- Single huge model vs MoE vs router across many small models
- In-house GPU cluster vs API
- Per-region vs global
- Streaming or not (ChatGPT streams; what does that cost?)

### Failure modes to address

- OpenAI / Anthropic outage (you probably use them)
- 10x traffic spike (viral tweet)
- Prompt injection at scale
- Cost overrun from a user running a long conversation

---

## Challenge 2: Scale an RAG System to 1M Users

**Brief:** You're building a "ChatGPT for your company's documents" product. Start at 1K users, scale to 1M. Each user has ~100 docs, ~10K chunks total. Average 50 queries/day.

### What to design

- Document upload + indexing pipeline
- Embedding + chunking strategy at scale
- Vector DB choice (and when to migrate)
- Query path (embed → search → rerank → generate)
- Per-user isolation
- The cost model

### Numbers to nail

- Storage at 1M users (chunks × dimension × 4 bytes)
- Queries per second (back-compute from 1M × 50/day)
- Embedding cost at 1M users (one-time + delta)
- Vector DB cost at each scale (Pinecone vs Weaviate vs Qdrant vs pgvector)

### Trade-offs to make

- Pinecone managed vs Qdrant self-host
- 1000-token vs 500-token chunks
- Top-5 vs top-20 + rerank
- Per-user namespace vs metadata filter
- Caching (exact vs semantic)

### Failure modes to address

- Pinecone down → fall back to Postgres
- OpenAI rate-limited → return cached
- User uploads 1GB PDF
- User has 10K docs (slow)
- Bad embeddings (model change, reindex)

---

## Challenge 3: Real-Time AI Sales Coach on a Live Call

**Brief:** A BDR is on a live sales call. The system listens in (Zoom API), transcribes in real-time, and pops coaching suggestions ("they just objected on price, here's a response") with < 2s latency.

### What to design

- Audio capture (Zoom RTMS or similar)
- Streaming transcription (Whisper streaming)
- Real-time LLM inference (the LLM is reading the live transcript)
- Suggestion delivery (UI overlay on the call)
- Privacy + consent model

### Numbers to nail

- End-to-end latency budget (audio → suggestion)
- Tokens processed per second of call
- LLM cost per hour of call
- Concurrent calls supported per server

### Trade-offs to make

- Run LLM on every utterance vs batch every 5s
- One big LLM vs small classifier per suggestion type
- Pre-generated suggestions vs on-the-fly
- Where to host the LLM (latency vs cost)

### Failure modes to address

- Audio drop
- Whisper makes a mistake (and the LLM is wrong too)
- LLM is too slow (> 2s)
- User disables feature mid-call
- Compliance recording issue

---

## Challenge 4: AI Code Reviewer for 10K Engineers

**Brief:** GitHub Copilot-class code review. Engineer pushes PR, AI comments on the diff within 30s. 10K engineers, 20 PRs/engineer/month = 200K PRs/month.

### What to design

- The diff ingestion (GitHub webhook → process)
- The context assembly (the diff + relevant files + repo conventions)
- The LLM call (reviewer prompt)
- The comment posting (back to GitHub)
- The fine-tuning / RAG strategy (your repo's style)

### Numbers to nail

- Tokens per PR (diff + context)
- Cost per PR review
- Monthly cost at 200K PRs
- Latency target (30s end-to-end)

### Trade-offs to make

- LLM (general) vs fine-tuned (your code)
- Whole file vs RAG over repo
- Quick (line-by-line) vs thorough (whole-PR)
- Async review vs blocking

### Failure modes to address

- Massive PR (10K lines)
- LLM hallucinates an issue that doesn't exist
- Engineer rage-quits on bad feedback
- LLM says "looks good" on a broken PR

---

## Challenge 5: Multi-Tenant SaaS with Per-Tenant Customization

**Brief:** You're building an AI tool where each tenant (company) wants a custom assistant trained on their docs and tone. 500 tenants, 1000 users/tenant avg.

### What to design

- The onboarding flow (tenant uploads docs, custom assistant is built)
- The per-tenant RAG index (isolation)
- The per-tenant config (model, system prompt, temperature)
- The auth + RBAC (tenant → users → roles)
- The billing (per-tenant usage tracking)

### Numbers to nail

- Storage at 500 tenants × 10K docs × 10 chunks
- Cost per tenant (compute + storage)
- Onboarding time (from "tenant signs up" to "first answer")
- Cold-start time when a new tenant is created

### Trade-offs to make

- Per-tenant index vs shared index with metadata filter
- Per-tenant fine-tune vs per-tenant RAG
- Pre-built vs lazy-loaded
- Region pinning (EU tenant → EU data)

### Failure modes to address

- Tenant A's data leaks to Tenant B
- Tenant uploads 100K docs (onboarding takes 24h)
- Tenant goes viral (10x usage spike)
- Tenant leaves (hard delete all their data, GDPR)

---

## Challenge 6: Build an AI Search Engine (Perplexity-class)

**Brief:** Perplexity-style search: query → 10+ sources → synthesized answer with citations. 10M queries/day, average 5 sources per query.

### What to design

- The search pipeline (Tavily + direct scraping + YouTube transcription)
- The synthesis (ReAct agent or pipeline)
- The citation system (every claim linked to a source)
- The cost model
- The streaming UX

### Numbers to nail

- Searches per query (back-compute)
- LLM tokens per query (plan + synthesize + critique)
- Tavily/Serper cost per query
- End-to-end latency target
- Monthly cost at 10M queries/day

### Trade-offs to make

- Tavily vs Serper vs DataForSEO
- 5 sources vs 10 vs 20
- Outline-first vs freeform
- Streaming vs wait-for-full-answer
- Citation enforcement (LLM may lie about sources)

### Failure modes to address

- Tavily down → fall back to Serper
- Source URL 404s
- Source contradicts another source
- LLM cites a source that doesn't actually say what it claims
- Plagiarism risk

---

## Challenge 7: AI Tutor for 1M Students

**Brief:** Khan Academy-class AI tutor. Each student asks questions, gets explanations, does practice problems. 1M students, 50 interactions/student/week = 50M interactions/week.

### What to design

- The tutoring agent (Socratic method, not just "give the answer")
- The student model (what they know, what they're struggling with)
- The content (textbook-aligned)
- The practice problem generator
- The progress tracking

### Numbers to nail

- Cost per interaction
- Cost per student per month
- Storage for student models (1M students × what?)
- Latency target (educational = patient, but not slow)

### Trade-offs to make

- One model for all ages vs per-grade models
- Real-time generation vs curated question bank
- Free-form chat vs structured lessons
- Voice (kids) vs text

### Failure modes to address

- Student tries to get the AI to do their homework
- Model gives wrong math answer
- Student gets stuck in a loop
- Privacy (kids, COPPA, FERPA)

---

## Challenge 8: Cost-Optimized AI at $0.001 per Request

**Brief:** You need to serve 10M requests/day at $0.001/req = $10K/day. Pick the architecture that hits the cost target while staying useful.

### What to design

- The model choice (cheap models, fast models, self-hosted)
- The caching strategy (aggressive, semantic)
- The routing (when to use which model)
- The fallback chain
- The cost monitoring (alert on per-request cost)

### Numbers to nail

- Token budget per request (cap at 1500 in + 500 out)
- Model cost per request (must fit budget)
- Cache hit rate (target 50%+)
- Infrastructure cost per request

### Trade-offs to make

- Quality vs cost (every 0.1 cent matters)
- Latency vs cost (cheaper = slower?)
- Self-hosting vs API (volume threshold)
- Caching vs freshness

### Failure modes to address

- Cache miss storm (everyone asks new questions)
- Model price increase (OpenAI raises rates)
- Vendor outage
- Cost overrun alert (a single request blows past $1)

---

## Challenge 9: Migrating from OpenAI to Self-Hosted Llama

**Brief:** You're spending $50K/month on OpenAI. You estimate Llama 3 70B self-hosted could do 80% of the work at $5K/month. Plan the migration.

### What to design

- The infrastructure (GPU choice, hosting, autoscaling)
- The model serving stack (vLLM, TGI, Triton)
- The evaluation (is Llama 3 70B really 80% as good?)
- The gradual migration (which features first?)
- The rollback plan (when self-host fails, fall back to OpenAI)

### Numbers to nail

- GPU cost (A100 vs H100 vs L40S)
- Tokens/second per GPU
- Cost per million tokens (amortized)
- Time to migrate (months)
- Risk-adjusted savings (some features will stay on OpenAI)

### Trade-offs to make

- Llama 3 70B vs 8B (cost vs quality)
- Single big model vs MoE
- Self-host on AWS vs Lambda Labs vs CoreWeave
- Continuous batching vs on-demand

### Failure modes to address

- GPU supply shortage
- Inference slower than expected
- Quality regression
- Your ops team doesn't know GPU ops
- Vendor lock-in to a GPU cloud

---

## Challenge 10: Build an AI Feature Flag System

**Brief:** You ship 5 prompt changes per day. You need to test each on 1% of traffic, measure the impact, and roll out or roll back — all in <1 hour per change.

### What to design

- The flag system (per-prompt flags, traffic allocation)
- The evaluation (which metric matters? quality? latency? cost?)
- The statistical significance (how long to run an A/B test)
- The auto-rollback (when metrics tank, roll back)
- The audit log (who changed what when)

### Numbers to nail

- Sample size per arm (per-day traffic × target %)
- Time to significance (days, not weeks)
- Decision threshold (when to roll out vs roll back)
- Maximum concurrent experiments (don't break orthogonality)

### Trade-offs to make

- 1% → 10% → 50% → 100% vs continuous ramp
- LLM-as-judge vs human eval vs proxy metric
- Auto-rollback (fast but risky) vs human approval (slow but safe)
- Hash-based assignment (stable) vs random (re-shuffles on reload)

### Failure modes to address

- Bad prompt ships to 50% before detection
- Evaluation is gamed (LLM-as-judge picks the wrong winner)
- Traffic correlation (test A and test B interact)
- Silent regression (latency goes up 100ms, no alert)

---

## Cross-cutting design review checklist

For every challenge, ask yourself:

- [ ] Did I include actual numbers (not "a lot" or "lots of users")?
- [ ] Did I back-compute from a top-line target (1M users, $10/day)?
- [ ] Did I show the cost at 1K, 10K, 100K, 1M scale?
- [ ] Did I name specific technologies, not categories?
- [ ] Did I include 3+ ADRs (Architecture Decision Records)?
- [ ] Did I list 3+ failure modes with detection + recovery?
- [ ] Did I include what to monitor (3+ metrics + alerts)?
- [ ] Did I address the boring stuff (auth, rate limits, secrets, observability)?
- [ ] Did I make a cost-aware decision (not just "use the best model")?
- [ ] Did I make a latency-aware decision (not just "stream it")?

---

## The single most important lesson

Every system design question has the same answer at the end:

> **"It depends."**

The job is not to find the "right" answer. The job is to:
1. Make a reasonable choice
2. Defend it with numbers
3. Name the trade-offs you accepted
4. Define when you'll revisit the decision

A senior engineer finds the right answer for now. A staff engineer finds the right answer for the next 18 months, with a plan to migrate.

---

## What's next

- Pick the 2-3 challenges most relevant to your capstone
- Write a design doc for each
- Use the design doc as your ARCHITECTURE.md (or compare yours to it)
- Discuss with your cohort / on Twitter / in interviews

These are the questions that get asked in staff / principal interviews at AI companies. Practice them until you can answer in 30 minutes with confidence.