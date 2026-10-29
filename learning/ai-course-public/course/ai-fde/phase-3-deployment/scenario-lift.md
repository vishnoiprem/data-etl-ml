# Phase 2 → Phase 3 — Scenario Lift

> **The drafter works. Now make it survive the customer.**

---

## Where Phase 2 left us

End of Phase 2 state, PacificFreight Co.:

- The drafter service runs in Docker on Daniel's VM. `/health` returns 200. `/draft` answers 150 emails/day in mock mode. `/retrieve` returns the top-3 chunks from the style guide. `/eval` grades the drafter on the 30-row eval set and saves a baseline.
- 13/13 pytest cases pass.
- Mei (CS lead) uses the drafter daily. She reports 3-4 drafts/day that are "good enough to send as-is" out of ~25 she processes. That's the 14% thumbs-up rate. The other 86% she edits and sends.
- Sarah (ops manager) sees the drafter in the weekly metrics but doesn't have a stakeholder map. She asks "should we sign off on the pilot?" and the FDE realizes **nobody agreed on the criteria**.
- Daniel (IT) owns the VM. He has no runbook, no on-call rotation, no rate limits. The 1 OpenAI outage last month took the drafter down for 10 minutes; Mei had to revert to her old manual workflow for that period.
- The customer asks for a Week-4 GO/NO-GO decision. The FDE panics because the criteria don't exist.

**This is exactly the moment Phase 3 is for.**

---

## The Phase 3 lift

Phase 3 takes the Phase 2 service — which works in mock mode on Daniel's laptop — and turns it into a **production system with a team that owns it.** Five concrete lifts:

### 1. Hybrid retrieval (replaces the mock store)

**Before (Phase 2):** The retriever is a deterministic token-overlap scorer over 22 chunks. It works for the eval set but fails on real customer emails with typos, multi-language phrases, and the PF-1003 style of "where is my parcel?"

**After (Phase 3, T1):** The retriever is a **hybrid** of BM25 (keyword recall) + a dense embedding (semantic recall) + Reciprocal Rank Fusion (RRF) to merge the two rankings. The retriever now catches queries the mock store missed. Eval set goes from 0.78 → 0.91 context_precision.

```
T1 file: course/ai-fde/phase-2-core-build/service/retrieval_v2.py (~250 lines)
        Course/ai-fde/phase-3-deployment/technical/01-advanced-retrieval.{md,py}
```

### 2. Streaming + feedback + telemetry (the live loop)

**Before (Phase 2):** `/draft` returns a single JSON response. There's no way to see partial output. There's no way for Mei to record which drafts she accepted.

**After (Phase 3, T2):**
- `/draft/stream` returns Server-Sent Events, chunk by chunk, so Mei sees the first sentence in 200ms instead of waiting 1.8s for the whole thing.
- `/feedback` accepts `{"draft_id": "...", "rating": "up"|"down", "edited_draft": "..."}`. The feedback is appended to `usage.jsonl` and shows up in the next Monday's iteration report.
- `/metrics` exposes Prometheus counters: `drafts_total`, `feedback_total{type=up|down}`, `eval_score{metric=...}`, `circuit_state{name=...}`.
- A `render_iteration_report.py` reads the last 7 days of `usage.jsonl` and produces a markdown report Mei can read in 5 minutes.

```
T2 file: course/ai-fde/phase-2-core-build/service/app.py  (new /draft/stream + /feedback + /metrics)
        course/ai-fde/phase-2-core-build/service/eval.py  (new render_iteration_report)
        course/ai-fde/phase-3-deployment/technical/02-eval-monitoring-iteration.{md,py}
```

### 3. Circuit breaker + rate limiter + redactor (reliability)

**Before (Phase 2):** When OpenAI goes down (Week 7's 10-min outage), the drafter hangs. When Mei's email contains her customer's email address (PII), it ends up in logs. When the system is overloaded, the LLM call just slows down — there's no back-pressure.

**After (Phase 3, T3):**
- A `CircuitBreaker` wraps the LLM call. After 5 consecutive failures or 30s of latency, the circuit opens and returns a 503 + the cached last-good-response. Mei sees "the drafter is offline, here's what it said last time" instead of a hung spinner.
- A `TokenBucketRateLimiter` caps the LLM call at 60 requests/min/user. Mei can't accidentally loop the drafter and burn $50 in 10 minutes.
- A `Redactor` strips emails, phone numbers, and PF-XXXX shipment IDs from log lines *before* they're written. Logs are now safe to grep.
- A `TTLCache` caches LLM responses for 5 minutes. Mei's repeated re-renders of the same email don't re-bill OpenAI.
- A `make_tiered_fallback` chain: primary LLM → cached response → static template. Three levels of degradation.
- A `Caddy` reverse proxy terminates TLS and rate-limits at the edge.

```
T3 file: course/ai-fde/phase-2-core-build/service/circuit.py  (~400 lines)
        course/ai-fde/phase-2-core-build/service/telemetry.py  (~300 lines)
        course/ai-fde/phase-2-core-build/service/Caddyfile
        course/ai-fde/phase-3-deployment/technical/03-scale-reliability-security.{md,py}
```

### 4. The 3-loop iteration cadence (C2)

**Before (Phase 2):** Prompt changes happen ad-hoc. There's no rhythm. Mei asks for a change and the FDE ships it the same day if they have time.

**After (Phase 3, C2):** A Monday 3-loop cadence:
- **Daily:** Mei runs the drafter. She rates drafts. `/feedback` logs the ratings.
- **Weekly (Monday 9am):** The FDE + Sarah review the iteration report. They identify the 3 worst-rated drafts and write 1 prompt change or 1 retrieval change. They ship it before lunch.
- **Monthly (first Monday):** The FDE + Daniel + Sarah review the cost model, the circuit trip rate, the eval score trend. They decide if the model choice (GPT-4o-mini) still holds.

```
C2 file: course/ai-fde/phase-3-deployment/consulting/02-delivery-iteration.md
```

### 5. The 3 ops artifacts (C3)

**Before (Phase 2):** The FDE is the only person who knows how to deploy, debug, or change the drafter. The runbook is "ask the FDE." The on-call rotation is "the FDE." The RACI is "everyone agrees the FDE does it."

**After (Phase 3, C3):**
- `consulting/runbook.md` — Daniel owns. A 5-page doc that lists every alert + every SEV + the response procedure. The new FDE reads it on day 1 and knows what to do at 2am.
- `consulting/raci.md` — Sarah owns. A 1-pager that names the responsible/approver/consulted/informed for every decision (prompt change, model swap, capacity expansion, SEV-1 response).
- `consulting/on-call-rotation.md` — Daniel owns. A 1-pager that says who's on call this week, the escalation chain, and the "I'm going dark" handoff.

Plus the 5-question "FDE has left" test (C3 closes with this): can a new FDE, on day 1, answer all 5 questions correctly? If yes, the FDE is replaceable. If no, the FDE has not finished their job.

```
C3 files: course/ai-fde/phase-3-deployment/consulting/{runbook,raci,on-call-rotation}.md
         course/ai-fde/phase-3-deployment/consulting/03-ownership-handoff.md
```

---

## What the FDE delivers at the end of Phase 3

```
course/ai-fde/phase-3-deployment/
├── README.md                          ← the 3-track map (you are not here)
├── scenario-lift.md                   ← this file
├── TECHNICAL-TRACK.md                 ← T1 → T2 → T3 sequence
├── CONSULTING-TRACK.md                ← C1 → C2 → C3 sequence
├── technical/
│   ├── 01-advanced-retrieval.{md,py}       T1: hybrid retriever
│   ├── 02-eval-monitoring-iteration.{md,py} T2: streaming + feedback + metrics
│   └── 03-scale-reliability-security.{md,py} T3: circuit + rate-limit + redactor
└── consulting/
    ├── 01-stakeholder-alignment.md    C1: stakeholder map + GO/NO-GO
    ├── 02-delivery-iteration.md       C2: 3-loop cadence
    ├── 03-ownership-handoff.md        C3: 5-question handoff test
    ├── runbook.md                     ops artifact (Daniel)
    ├── raci.md                        ops artifact (Sarah)
    └── on-call-rotation.md            ops artifact (Daniel)
```

The service code (the deliverable of Phase 2) is hardened in place at:
- `course/ai-fde/phase-2-core-build/service/app.py` — added /draft/stream, /feedback, /metrics
- `course/ai-fde/phase-2-core-build/service/circuit.py` — NEW (400 lines: breaker + limiter + redactor + cache + tiered fallback)
- `course/ai-fde/phase-2-core-build/service/retrieval_v2.py` — NEW (replaces the mock store with hybrid retrieval)
- `course/ai-fde/phase-2-core-build/service/eval.py` — added render_iteration_report
- `course/ai-fde/phase-2-core-build/service/telemetry.py` — NEW (Prometheus + JSON logger)
- `course/ai-fde/phase-2-core-build/service/Caddyfile` — NEW (TLS termination, edge rate limit)

13/13 pytest cases pass end-to-end against the hardened service.

---

## What's after Phase 3

Phase 4 (in `../phase-4-capstone/`) takes the Phase 3 service and turns it into a **platform**: MCP for tool use, multi-agent for complex cases, a distilled SLM for cost, a fresh engagement for breadth, plus 5 case studies and a capstone presentation.

See `../phase-4-capstone/scenario-brief.md` for the week-by-week Phase 4 plan.
