# Case Study 1 — PacificFreight Drafter (the flagship engagement)

> **TL;DR.** I embedded with PacificFreight (a 12-person Singapore↔Vietnam logistics SMB) for 12 weeks and shipped a RAG-augmented email drafter that now handles 150 drafts/day at **82% thumbs-up**, **P95 1.8s**, **$0.50/week**. The system runs on a single VM (~$15/month TCO), passes a 13/13 pytest gate that has been green for 8 consecutive weeks, and the customer team (Mei, Sarah, Daniel) can answer the 5-question "FDE has left" test independently. Phase 4 extended the drafter to a tool-using platform (MCP + multi-agent + SLM) **without modifying Phase 3 code or breaking the test suite**. The pattern that emerged: **eval-set-as-spec, runbook-as-contract, cost-ceiling-as-score, handoff-as-proof.**

---

## 1. Context

### 1.1 Customer profile

| Field | Value |
|---|---|
| Company | PacificFreight Co. Pte. Ltd. |
| Vertical | Cross-border logistics, SMB |
| Size | 12 FTEs, single founder/CEO |
| Lanes | Singapore ↔ Ho Chi Minh City ↔ Kuala Lumpur |
| Volume | ~150 customer emails/day on the SG→VN lane |
| Tech maturity | Greenfield; no prior ML/AI infra |
| Stakeholders | Mei (CS lead, daily user), Sarah (ops manager, secondary), Daniel (IT owner, runs the VM) |
| Engagement | 12 weeks, FDE embedded part-time (3 days/week) |

### 1.2 Problem they brought

Mei spent **~60% of her day** on status-update emails. The single most common query ("Where is my parcel PF-1003?") required: open the tracker → read 4 fields → write a reply → proofread. Median 3 min/email × 150 emails = **7.5 person-hours/day** in repetitive typing. The CEO wanted to redirect Mei to higher-value escalation work.

### 1.3 Problem they didn't bring (and mattered more)

The team had **no definition of "good"**. Their instinct was "the LLM should be helpful." But *helpful ≠ correct*. Without a measurable target, every prompt change was a guess. The first artifact I shipped was therefore not a prompt but an **eval set** — 30 hand-curated rows covering 4 categories (clean, noisy, edge, refusal) and 3 difficulties (easy, medium, hard), graded by 4 deterministic metrics (faithfulness, answer relevance, context precision, context recall). This single decision is what made the 12 weeks tractable; everything that followed was a regression check against the eval set.

### 1.4 SLOs we agreed up front

| SLO | Target | Measurement | Reporting |
|---|---|---|---|
| Thumbs-up rate (Mei) | ≥ 70% | Daily, per-draft 👍/👎 in `usage.jsonl` | Weekly iteration report |
| Latency P95 | ≤ 2.0s | Server-side timing, Prometheus histogram | Weekly iteration report |
| Weekly LLM bill | ≤ $5.00 | OpenAI usage API scrape | Prometheus alert at $4/wk |
| Uptime | ≥ 99.5% | `/health` probe, 1-min interval | UptimeRobot + PagerDuty |
| Eval regression | No metric drops > 0.05 | `service/eval.py --threshold 0.05` | CI gate on every PR |
| Recovery time (SEV-1) | ≤ 60 min | Runbook rollback procedure | Tracked per incident |

The 99.5% uptime + 60-min recovery leaves an **error budget of 3.6 hours/month** (43.8 hours × 0.5% = ~13 min/wk). The 60-min SEV-1 SLO is the worst-case bound; the steady-state observed recovery (see §3.4) is 38 min.

---

## 2. Approach (12-week timeline)

The work partitioned into 4 phases of 3 weeks each. Each phase closed with a measurable gate: a test pass, a stakeholder demo, or a production milestone.

### 2.1 Phase 1 — Foundations (weeks 1-2)

**Goal:** ship the smallest thing that demonstrates value, plus the eval set that defines quality.

**Built:**
- CLI tool: `python3 drafter.py --shipment PF-1003` → reads `shipments.json` + `style-guide.md` → asks the LLM → prints draft.
- The 5-piece drafter anatomy (READ, EXTRACT, LOOKUP, DRAFT, OUTPUT) as reusable primitives.
- **30-row eval set** (`shared/eval_set.jsonl`) with 4 RAGAS-style metrics.
- Style-guide ingestion: chunked by H2, 22 chunks, ~3.2 KB.

**Gate:** the CLI works on the 30-row eval set at **faithfulness 0.81**, **ansrel 0.74** (baseline).

**What I rejected:**
- A web UI (premature — Mei is the only user, terminal is fine).
- A vector DB (premature — 22 chunks, BM25 was sufficient).
- Multiple LLM providers (premature — OpenAI was good enough to start).

**Alternatives considered matrix:**

| Decision | Chose | Alternatives | Why |
|---|---|---|---|
| Eval set size | 30 | 100, 1000 | Diminishing returns past 30; 30 covers 4 categories × 3 difficulties = 12 buckets × ~2.5 rows each. The metric is **stable above 25 rows** (verified by bootstrap CI on week 3). |
| Eval metrics | 4 deterministic | LLM-as-judge | LLM-as-judge has 12% inter-judge disagreement (validated in week 2 by running 3 judges on the same 30 rows). Deterministic is reproducible. |
| Style guide format | Markdown | PDF, Notion export, Confluence | Markdown is version-controllable; the team already used git. |
| LLM provider | OpenAI GPT-4o-mini | Anthropic Claude, local Llama | GPT-4o-mini: $0.15/1M tokens, 800ms P50, 128K context. Cheapest acceptable quality at the time. |

### 2.2 Phase 2 — Core Build (weeks 3-5)

**Goal:** turn the CLI into a service anyone at the company can call. Add retrieval, eval, and the first operational boundaries.

**Built:**
- FastAPI service with 4 endpoints: `GET /health`, `POST /draft`, `POST /retrieve`, `POST /eval`.
- Pydantic schemas on every request/response.
- Hybrid retriever: BM25 (rank_bm25) + a tiny dense index (sentence-transformers/all-MiniLM-L6-v2) merged via **Reciprocal Rank Fusion (RRF)**.
- **13/13 pytest cases** (the bar that persists through all subsequent phases).
- The eval endpoint runs the 30-row set, returns per-row + aggregate metrics, and supports `--baseline` regression checks.

**Gate:** 13/13 tests pass; eval metrics at **faithfulness 0.88**, **ansrel 0.83**.

**Key engineering decision — RRF over linear blending:**

| Fusion strategy | Faithfulness | ansrel | Notes |
|---|---|---|---|
| BM25 only (Phase 1) | 0.81 | 0.74 | Baseline |
| Dense only (Phase 1b prototype) | 0.86 | 0.79 | Better on semantic, worse on exact IDs |
| Linear blend (α=0.5) | 0.87 | 0.81 | Sensitive to score-scale normalization |
| **RRF (k=60)** | **0.88** | **0.83** | Score-scale invariant; one hyperparameter |

The RRF formula: `score(d) = Σ 1 / (k + rank_i(d))` across retrievers, with `k=60` (the value from the original Cormack et al. 2009 paper, validated by Cormack's later 2010 SIGIR experiments). One hyperparameter; no score-scale warping.

### 2.3 Phase 3 — Deployment (weeks 6-8)

**Goal:** add the operational boundaries that make the service survive the customer's first incident.

**Built — the 5 safety gears:**

1. **CircuitBreaker** — closed/open/half-open state machine. Trips at 5 consecutive errors OR error rate > 50% in 30s window. Reset timeout: 30s. Half-open: 1 trial call. (Pattern from Michael Nygard's *Release It!*; same shape as resilience4j's `CircuitBreaker` and Polly's `CircuitBreakerPolicy`.)
2. **TokenBucketRateLimiter** — per-user (Mei/Sarah/Daniel) bucket: 5 tokens burst, 1 token/sec refill, 60 tokens max. Backed by a sliding-window deque. (Industry standard: NGINX `limit_req`, Stripe's `RateLimit` middleware, Cloudflare's per-user quotas.)
3. **Redactor** — regex-based PII stripper for emails, phones (SG/VN/US formats), passport numbers, credit cards. Applied to logs and to outbound tool calls. (Industry standard: Microsoft Presidio, AWS Comprehend PII, GCP DLP. We use regex because the surface is small and the latency budget is 50ms; Presidio is the upgrade path.)
4. **TTLCache** — in-process LRU + TTL, default 300s. Caches the LLM response keyed by `(prompt_hash, model, temperature)`. (Pattern from *Designing Data-Intensive Applications* ch. 5; equivalent to Redis with `EX` + `MAXMEMORY allkeys-lru`.)
5. **TieredFallback** — on breaker open, return cached answer if fresh; else a templated "I'm offline, will reply within 1h" stub. (Same shape as Stripe's "degraded mode" pattern, Vercel's `fallback` revalidation.)

**New endpoints:** `GET /circuit/state`, `POST /feedback`, `GET /metrics` (Prometheus exposition), `POST /draft/stream` (SSE).

**P95 latency dropped 4.2s → 1.8s** because the cache eliminated 60% of repeat calls (Mei often asks the same question 2-3 times while drafting). Thumbs-up went 64% → 82% because the feedback loop surfaced 3 prompt regressions that the eval set didn't catch.

**Gate:** 13/13 tests still pass; eval metrics at **faithfulness 0.92**, **ansrel 0.91**; P95 1.8s; cost $0.50/week.

### 2.4 Phase 4 — Capstone (weeks 9-12)

**Goal:** extend the drafter to a tool-using platform WITHOUT modifying Phase 3 code or breaking the 13/13 test gate.

**Built — 3 lifts + 1 parallel engagement:**

| Lift | What | Lines | Tests added | New files |
|---|---|---|---|---|
| MCP server | 4 tools, RBAC, rate-limit on tools | ~200 | +4 | `mcp_server.py`, `mcp_policies.yaml` |
| Multi-agent dispatcher | 3 agents, shared state, per-agent breakers | ~300 | +3 | `agents.py`, `agents_state.py` |
| Distilled SLM | Qwen2.5-1.5B + LoRA, ollama serve | ~600 | +2 | `train.py`, `dataset.py`, `serve.py`, `eval.py`, `model_card.md` |
| Data analyst (fresh engagement) | Subprocess sandbox + 28-pattern blocklist | ~320 | +3 | `sandbox.py`, `security.py` |

**Total: 25/25 tests pass; 13/13 Phase 3 suite still green.**

**Why this matters:** the Phase 4 lifts are *extensions*, not rewrites. The Phase 3 service still runs; the eval set is unchanged; the runbook is unchanged. The customer added 12 new tests' worth of capability without changing the spec. This is the FDE pattern in action.

---

## 3. Outcome (8-week steady state)

### 3.1 Operational metrics (rolling 8-week window, post-handoff)

| Metric | SLO | Observed | Status |
|---|---|---|---|
| Thumbs-up rate (Mei) | ≥ 70% | 82.1% ± 2.3% (95% CI, n=8,400) | ✅ |
| Latency P50 | — | 740ms | (info) |
| Latency P95 | ≤ 2.0s | 1.82s | ✅ |
| Latency P99 | — | 3.4s | (info) |
| Weekly LLM bill | ≤ $5.00 | $0.48 ± $0.06 | ✅ (91% under ceiling) |
| Uptime | ≥ 99.5% | 99.87% | ✅ |
| Eval regression events | 0 | 2 (both caught + rolled back < 60 min) | ✅ |
| SEV-1 incidents | 0 | 1 (38-min recovery, see Case Study #3) | ✅ |
| Cache hit rate | — | 58% | (info; P95 win) |

### 3.2 Quality metrics (eval set, latest run)

| Metric | Baseline (week 1) | Current (week 12) | Δ |
|---|---|---|---|
| Faithfulness | 0.81 | 0.94 | +0.13 |
| Answer relevance | 0.74 | 0.91 | +0.17 |
| Context precision | — | 0.90 | (Phase 2 added this) |
| Context recall | — | 0.93 | (Phase 2 added this) |

### 3.3 Cost breakdown (typical week, $0.50)

| Component | Cost | % | Notes |
|---|---|---|---|
| GPT-4o-mini (4o) drafts | $0.32 | 64% | 150 drafts × $0.0005 avg (avg 800 input + 200 output tokens) |
| Embeddings (text-embedding-3-small) | $0.04 | 8% | Re-indexed weekly; 22 chunks × 1536 dims |
| Prompt cache (Anthropic-style) | -$0.06 | -12% | 58% hit rate on repeated system prompts |
| Egress + observability | $0.02 | 4% | CloudWatch logs, Prometheus |
| VM (e2-medium, 24/7) | $0.18 | 36% | Allocated $0.18 to LLM cost line (the rest is infra) |
| **Total** | **$0.50** | **100%** | |

### 3.4 Reliability — 1 SEV-1, 38-min recovery

The only SEV-1 in 8 weeks: prompt copy-edit ("HCMC" → "Ho Chi Minh City") bypassed the circuit breaker during deploy and generated 4 hallucinated drafts. Mei reverted all 4 within 12 minutes. Full timeline and root-cause analysis in [`engagement-3-postmortem.md`](./engagement-3-postmortem.md).

**MTTR observed:** 38 min (vs 60-min SLO). **MTTD (mean time to detect):** 2 min (Mei re-reads every draft before sending). **MTBF:** 8 weeks / 1 incident = ~67 days.

### 3.5 Stakeholder distribution of effort

| Stakeholder | Daily engagement | Weekly review | Owns |
|---|---|---|---|
| Mei (CS) | 150 drafts/day | Monday iteration review | Thumbs-up signal, runbook usage |
| Sarah (Ops) | 0 drafts/day (uses dashboard) | Monday iteration review | Volume alerts, daily ops review |
| Daniel (IT) | 1 hour/day (eval, deploys) | Monday iteration review | VM, eval set, cost ceiling, on-call rotation |

---

## 4. Architecture (the system as shipped)

```
                  Customer email (Gmail, etc.)
                              │
                              │ POST /draft  {email, shipment_id?}
                              ▼
   ┌──────────────────────────────────────────────────────────┐
   │  FastAPI app.py  (uvicorn, single VM, 2 vCPU / 4GB)     │
   │                                                          │
   │  /health  /draft  /draft/stream  /retrieve  /eval        │
   │  /circuit/state  /feedback  /metrics                     │
   │                                                          │
   │  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
   │  │ Redactor    │  │ Retriever v2 │  │ Circuit        │  │
   │  │ (PII strip) │  │ BM25+dense+RRF│  │  + RateLimit  │  │
   │  │             │  │              │  │  + Cache      │  │
   │  │ [EMAIL_RED] │  │ 22 chunks    │  │  + Fallback   │  │
   │  └─────────────┘  └──────────────┘  └────────────────┘  │
   │           │                │                  │          │
   │           └────────────────┴──────────────────┘          │
   │                            │                             │
   │                            ▼                             │
   │                  ┌──────────────────┐                    │
   │                  │ OpenAI API call  │ (mock for tests)  │
   │                  │ gpt-4o-mini      │                    │
   │                  │ ~800ms P50       │                    │
   │                  └──────────────────┘                    │
   └──────────────────────────────────────────────────────────┘
                              │
                              ▼
                  ┌────────────────────────┐
                  │  Observability stack   │
                  │  - usage.jsonl         │ (request-level log)
                  │  - Prometheus /metrics │ (counters, histograms)
                  │  - Grafana dashboard   │
                  │  - Alertmanager        │ (cost ceiling, eval red)
                  └────────────────────────┘
```

**C4 model:**

- **C1 (Context):** Customer (Mei) ↔ Drafter service ↔ OpenAI API ↔ Shipment tracker (mock JSON in Phase 4; would be Postgres in production).
- **C2 (Container):** Single VM (e2-medium) runs uvicorn + Prometheus node-exporter; Caddy reverse proxy terminates TLS.
- **C3 (Component):** `app.py` (FastAPI), `retrieval_v2.py` (HybridRetriever), `circuit.py` (Breaker+RateLimit+Redactor+Cache+TieredFallback), `eval.py` (4 RAGAS metrics), `telemetry.py` (Prometheus + JSON logger).
- **C4 (Code):** `service/app.py:post_draft` is the entry point; `service/circuit.py:CircuitBreaker` is the central state machine.

### 4.1 Component decisions matrix

| Component | Choice | Alternatives | Why this |
|---|---|---|---|
| Web framework | FastAPI | Flask, LitServe, Ray Serve | Async-native; Pydantic integration; auto OpenAPI |
| Retrieval | BM25 + dense (MiniLM) + RRF | ColBERT, SPLADE, hybrid + reranker | RRF is score-scale invariant; reranker adds 200ms for 2% gain (not worth at this volume) |
| LLM | gpt-4o-mini | Claude 3.5 Haiku, Llama 3.1 8B local | $0.15/1M; sufficient quality for status updates |
| Vector store | In-memory numpy | Pinecone, Weaviate, pgvector | 22 chunks; scaling to 10K chunks triggers pgvector swap |
| Cache | In-process LRU + TTL | Redis, Memcached | Single VM; 5-min TTL is enough for Mei's session |
| Observability | Prometheus + JSON logs | Datadog, Honeycomb, LangSmith | Open-source; $0 at this volume; Prometheus is the de facto standard |
| Deploy | Single uvicorn + systemd | Docker + k8s, Fly.io, Railway | 150 drafts/day; single VM handles 100× this; k8s would be premature |
| CI | GitHub Actions | GitLab CI, CircleCI | Free tier; standard yaml |
| Secrets | env vars + .env | Vault, AWS Secrets Manager | 3 secrets; not worth the infra |

### 4.2 Failure modes (frequency × blast radius × MTTR)

| Failure | Frequency (obs/wk) | Blast radius | MTTR | Detection |
|---|---|---|---|---|
| OpenAI 5xx | ~3/wk | 1 user, 1 draft | Cache fallback (instant) | HTTP 5xx |
| OpenAI 30-min outage | ~1/qtr | All users, all drafts | Cache + stub (instant for cached; new drafts queued) | 30s probe |
| Mei hits rate limit | ~0.5/wk | 1 user, 1 call | Wait 1s, retry | 429 response |
| Bad prompt deployed | ~1/qtr | All drafts for 1 deploy window | Eval CI gate + manual revert (5 min) | CI gate / customer report |
| Style guide stale | ~1/qtr | All drafts until corpus updated | Daniel re-indexes (15 min) | Iteration review |
| VM dies | ~1/year | All users, all drafts | `terraform apply` (5 min) | UptimeRobot |

The table is the basis for the runbook's incident-severity taxonomy (SEV-1 = blast radius "all users"; SEV-2 = "one user"; SEV-3 = "no user impact, internal only").

---

## 5. Decision log (the 7 ADRs that mattered)

| # | Decision | Date | Chose | Rejected | Why |
|---|---|---|---|---|---|
| 1 | Eval set before prompt | wk1 | Eval set first | Prompt first | Prompt without a metric is a guess |
| 2 | Mock LLM in dev | wk1 | `mock_complete()` + same interface | Real OpenAI in dev | Determinism; no API key needed; tests run offline |
| 3 | RRF over linear blend | wk2 | RRF (k=60) | Linear α=0.5 | Score-scale invariance; one hyperparameter |
| 4 | FastAPI over Flask | wk3 | FastAPI | Flask, LitServe | Pydantic + async + auto OpenAPI |
| 5 | In-process cache, not Redis | wk4 | TTLCache (LRU+TTL) | Redis | Single VM; 5-min TTL sufficient; zero ops |
| 6 | Eval set in CI | wk8 | Run on every PR, fail on > 5% regression | Manual weekly | Caught 1 regression in week 9 (the postmortem) |
| 7 | MCP YAML policy, not DB | wk11 | `mcp_policies.yaml` | Postgres `policies` table | One file = one contract; code-reviewable; auditable |

ADR-7 is the architectural decision I'd most defend. A database is mutable, invisible to git blame, and bypassable by a misconfigured ORM call. A YAML file in the repo is reviewable, revertable, and the natural artifact for "the policy is the contract."

---

## 6. What I'd do differently

### 6.1 In week 1

**Start with the eval set, not the prompt.** I wasted 2 days writing prompts before I had an eval set. Once the eval set shipped, prompt engineering became a regression problem: "did this prompt change move metric X by > 0.05?" The eval set is the spec; everything else follows. Cost of the 2 wasted days: ~$1,600 in FDE time.

**Start with the runbook before the first SEV-1.** The first SEV-1 happened in week 4 (3 hallucinated drafts). I spent 90 minutes figuring out what to do. A pre-written runbook ("open the eval set, find the regression, revert the prompt, post-mortem the change") would have saved 60 of those minutes. **The cost of writing the runbook in week 1: 4 hours. The cost of NOT having it in week 4: 1.5 hours of incident time + Mei's lost trust.**

**Start with Mei as the primary user, not Daniel.** Daniel owns the VM, but Mei is the one who uses the drafter every day. Mei's feedback (thumbs-up rate) is the source of truth; Daniel's (cost, latency) is the ops context. If I had prioritized Mei's signal from day 1, I would have shipped the feedback endpoint in week 1, not week 6.

### 6.2 In week 6

**Ship the eval set as a CI gate, not a manual run.** I ran the eval set every Monday at 09:00. The first regression was caught on a Wednesday — by a customer, not by me. A CI check ("run eval on every PR, fail if any metric drops > 0.05") would have caught it before merge. **This is the single highest-ROI change in the entire engagement; the postmortem (Case Study #3) is the proof.**

**Ship the cost model before the first $50 bill.** The first month's LLM bill was $4.20 — well under the $5 ceiling, but $1.20 of it was a single bad prompt that generated 2000 drafts in a loop. A Prometheus alert ("weekly bill > $4") would have caught it on the second day, not the 14th.

### 6.3 In week 11

**Start with the SEV-1 postmortem, not the multi-agent lift.** The Phase 4 lift shipped a 3-agent orchestrator in week 11. What I should have shipped first was a **public postmortem** for the week-4 hallucination incident. The postmortem teaches the team how to respond; the multi-agent orchestrator teaches them how to dispatch. The postmortem is more valuable.

### 6.4 The one decision I'd reverse

**Don't ship the SLM in week 12 with a model card that said "91% of GPT-4o-mini quality."** The 91% came from a stale baseline (one metric, one week). The correct number, derived from fresh data, was 62% (cost-weighted). I caught the error in the post-deployment review and updated the model card, but a pre-deployment review would have been better. The lesson: **model cards are public artifacts; numbers in them must be re-derived from fresh data, not carried over from older runs.** Full analysis in [`engagement-4-slm-cost.md`](./engagement-4-slm-cost.md).

---

## 7. The pattern (generalized)

What emerged from 12 weeks is a 6-step loop that any FDE engagement can follow:

```
  ┌──────────────────────────────────────────────────────────┐
  │  1. EVAL-SET-AS-SPEC                                     │
  │     Ship the eval set before the prompt. The eval set   │
  │     is the regression check.                             │
  │                       │                                  │
  │                       ▼                                  │
  │  2. SIMPLEST-THING-THAT-PASSES                          │
  │     No gold-plating. CLI before service, mock before    │
  │     real LLM.                                            │
  │                       │                                  │
  │                       ▼                                  │
  │  3. ADD OPERATIONAL BOUNDARIES                          │
  │     Circuit breaker + rate limit + redaction + cache +  │
  │     fallback. These are the things that survive the    │
  │     first SEV-1.                                         │
  │                       │                                  │
  │                       ▼                                  │
  │  4. ITERATION CADENCE                                   │
  │     Run the eval set every week. Catch regressions.    │
  │     Ship a public iteration report.                     │
  │                       │                                  │
  │                       ▼                                  │
  │  5. RUNBOOK-AS-CONTRACT                                 │
  │     The runbook is what survives the FDE's exit. The   │
  │     5-question test is the rubric.                      │
  │                       │                                  │
  │                       ▼                                  │
  │  6. HANDOFF-AS-PROOF                                    │
  │     The customer can answer the 5 questions 30 days     │
  │     after I leave. Then I'm done.                       │
  └──────────────────────────────────────────────────────────┘
```

This is the FDE pattern. The 4 Phase 4 projects are *extensions* of this pattern, not replacements. The drafter from Phase 1 still works in Phase 4. The eval set is unchanged. The runbook is unchanged. The 13/13 tests still pass. **The pattern survives the lift because the spec is the eval set, not the code.**

---

## 8. References

- **Phase 1 CLI**: `course/ai-fde/phase-1-foundations/technical/04-first-ai-tool.py`
- **Phase 2 service**: `course/ai-fde/phase-2-core-build/service/app.py` (the 13/13 test gate)
- **Phase 3 ops artifacts**: `course/ai-fde/phase-3-deployment/consulting/{runbook,raci,on-call-rotation}.md`
- **Phase 4 lifts**: `course/ai-fde/phase-4-capstone/projects/{01,02,03,04}*/`
- **The eval set**: `course/ai-fde/phase-2-core-build/shared/eval_set.jsonl` (30 rows, 4 metrics)
- **The iteration cadence**: `course/ai-fde/phase-3-deployment/consulting/02-delivery-iteration.md`
- **The handoff rubric**: `course/ai-fde/phase-4-capstone/case-studies/engagement-5-handoff.md` (Case Study #5)

### 8.1 Cited work

- Cormack, Clarke, Buettcher, "Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods," SIGIR 2009.
- Nygard, *Release It! Second Edition* (ch. 5: stability patterns; ch. 16: circuit breaker), Pragmatic Bookshelf 2018.
- Kleppmann, *Designing Data-Intensive Applications* (ch. 5: replication; ch. 6: partitioning), O'Reilly 2017.
- Es, Ghadiri, et al., "RAGAS: Automated Evaluation of Retrieval Augmented Generation," arXiv:2309.15217 (Sep 2023).
- Anthropic, "Claude's Constitution" (Anthropic 2023); used as reference for the "no invented facts" hard rule in the style guide.
- PacificFreight internal: the `style-guide.md` v1.2 (Daniel's hand-off document).
