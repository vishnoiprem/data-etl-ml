# Lesson 02 — PRDs and Solution Design Documents

> **The 1-pager turns into a PRD. The outline turns into a design doc.** 50 minutes. No new code.

By the end of this lesson you can take a Phase 1 1-pager and produce **two** Phase 2 documents:

- A **PRD** (Product Requirements Document) — what the engineering team builds, with functional requirements, acceptance criteria, and non-functional requirements
- A **solution design doc** — how the engineering team builds it, with system diagram, component choices, capacity model, cost model, and failure modes

The PRD is for the engineering team. The design doc is for the customer's exec sponsor. Both are derived from the Phase 1 1-pager + the Phase 2 discovery deck (C1).

---

## 🎯 Outcome

You produce **two artifacts**:

1. `pacificfreight-prd.md` — a 2-3 page PRD with: user personas, functional requirements (FRs) with acceptance criteria, non-functional requirements (NFRs), out-of-scope, milestones
2. `pacificfreight-solution-design.md` — a 2-3 page solution design doc with: system diagram, component-choices table, capacity model, cost model, failure modes — modeled on `course/capstone-starters/01-ai-doc-qa/ARCHITECTURE.md`

When you finish, an engineer who has never met the customer can read the PRD and start coding. An exec sponsor who has never seen the codebase can read the design doc and approve the rollout.

## 🧠 Mindset

The 1-pager is **for the customer**. The PRD is **for the builder**. The design doc is **for the customer's exec sponsor**. Three documents, three audiences, three lengths.

| Document | Audience | Length | What it answers |
|---|---|---|---|
| **1-pager** (Phase 1) | Customer | 1 page | "Did we agree on the right problem?" |
| **Discovery deck** (C1) | FDE + customer | 1-2 pages | "What did we learn that changes the build?" |
| **PRD** (this lesson) | Engineering team | 2-3 pages | "What am I building?" |
| **Design doc** (this lesson) | Customer's exec sponsor | 2-3 pages | "How will it be built, and what does it cost?" |

The traps:

1. **The PRD is not the design doc.** A PRD says *what* the system does (FRs + NFRs). A design doc says *how* the system is built (components + choices + cost). A common mistake is to merge them; the result is a 10-page doc nobody reads.
2. **The design doc is not a sales deck.** No "we are excited to partner." No "world-class AI." The exec sponsor's job is to **approve the rollout**; the design doc's job is to give them enough information to do that.
3. **The PRD is not a wish list.** Every FR has an acceptance criterion. "The system shall retrieve the right shipment" is not an FR; "given an email with a PF-1003 reference, the system returns a draft that mentions 'customs' within 2 seconds" is.

> **FDE rule:** every FR in the PRD has a test. If the engineering team can't write a test for it, it's not an FR — it's a wish.

## 🛠️ Practice — the PRD

### Section 1 — User personas (3 short blocks)

The 1-pager had one user (Mei). The PRD enumerates all the roles:

> **Primary user: Mei (CS lead) and her 2-person CS team.** Drafts ~150 "where is my parcel?" replies/day. Uses the service via the existing internal tools (Gmail plugin or web UI in Phase 3; CLI in Phase 1; HTTP calls in Phase 2 testing).
>
> **Secondary user: Sarah (ops manager).** Approves the rollout, monitors the success metric, owns the style guide.
>
> **System owner: Daniel (IT).** Owns the VM, the AWS budget, the security patches, the pager.
>
> **Not the user: the end customer.** Always human-in-the-loop. The drafter never sends.

### Section 2 — Functional requirements (with acceptance criteria)

Each FR is one *behavior the system exhibits*, with a test the engineering team can write:

> **FR-1: Extract shipment ID from inbound email.**
> - Given: an email body containing one or more `PF-XXXX` references.
> - When: the service receives `POST /draft` with `{"email": "..."}`.
> - Then: the response `shipment_id` is the most recent `PF-XXXX` reference in the email.
> - Test: 5 emails with 1 PF ID + 3 emails with 2+ PF IDs + 2 emails with no PF ID. 100% pass.
>
> **FR-2: Look up shipment status.**
> - Given: a `shipment_id` that exists in the tracker.
> - When: the service processes the request.
> - Then: the response draft includes the shipment's `last_event` and `status` in plain English.
> - Test: for each of the 15 shipments in `shipments.json`, the draft contains the shipment's `last_event` substring.
>
> **FR-3: Augment the prompt with retrieved policy.**
> - Given: an email about customs.
> - When: the service processes the request.
> - Then: the system prompt includes the `Tone rules` and `Hard rules` policy chunks (in that order).
> - Test: grep the captured system prompt for both chunk IDs.
>
> **FR-4: Return a draft in the customer's language.**
> - Given: an email in Vietnamese / English / Tagalog.
> - When: the service processes the request.
> - Then: the draft is in the same language as the email.
> - Test: 3 emails × 3 languages = 9 test cases. Manual review of the draft.
>
> **FR-5: Never invent a status.**
> - Given: an email that asks about a shipment NOT in the tracker.
> - When: the service processes the request.
> - Then: the draft says "I cannot find that shipment, please reply with the correct ID."
> - Test: 2 emails with PF IDs not in the tracker.
>
> **FR-6: Refuse to send a draft about a refund or escalation.**
> - Given: an email that mentions "refund" / "money back" / "speak to your manager."
> - When: the service processes the request.
> - Then: the draft is a 2-line holding reply, with `[ESCALATE]` in the response.
> - Test: 5 emails with escalation keywords. The response always includes `[ESCALATE]`.

### Section 3 — Non-functional requirements (NFRs)

NFRs are the **quality attributes** the system must have. Each is measurable:

> **NFR-1: Latency.** P50 draft latency < 1.5s, P95 < 4s. Measured over 100 requests. (Driven by Mei's flow — she copy-pastes and sends; a 4s wait is the upper bound of patience.)
>
> **NFR-2: Cost.** LLM cost < $5/month at 150 emails/day. Measured via the `usage.jsonl` log. (Driven by the customer's $200/month ceiling.)
>
> **NFR-3: Availability.** Service uptime > 99% during business hours (SG time, 9am-6pm). Measured by the platform's `/health` check. (Driven by the CS team's working hours.)
>
> **NFR-4: PII handling.** Email body is never sent to the LLM. Only the extracted shipment ID + the looked-up status fields. Verified by a unit test that intercepts the LLM call and asserts the body is absent.
>
> **NFR-5: Observability.** Every `/draft` call writes one JSON line to `usage.jsonl` with: timestamp, model, provider, input_tokens, output_tokens, cost_usd, latency_ms, is_mock. (Driven by the customer's ops team's need to audit costs.)
>
> **NFR-6: Eval coverage.** A 30-row eval set runs in CI on every PR. A 5pp drop on any of the 4 metrics blocks the deploy. (Driven by the FDE's discipline — see C3 ADR-0003.)

### Section 4 — Out of scope (Phase 2)

> - Auto-send (sending without human review) — Phase 3+
> - Multi-shipment emails (2+ PF IDs in the same email) — Phase 2.5
> - Auto-language detection (the drafter defaults to English unless the email is in another language) — Phase 2.5
> - Refund / credit decisions — **never** (manager-only, off the table per Phase 1 1-pager)
> - Replacing the PHP tracker — separate engagement

### Section 5 — Milestones

> **Week 1:** Discovery deck signed. (C1 deliverable.)
> **Week 2:** v0 service in Mei's terminal (HTTP, not CLI). 3 FRs implemented.
> **Week 3:** Pilot with Mei only. 30-row eval set running nightly. All 6 FRs implemented.
> **Week 4:** Pilot with full CS team. Eval-driven regression check in CI. End-of-week go/no-go for Phase 3.

---

## 🛠️ Practice — the Solution Design Document

This is the design doc, modeled on `course/capstone-starters/01-ai-doc-qa/ARCHITECTURE.md`. Same structure: system diagram, component-choices table, data flow, capacity model, cost model, failure modes, migration triggers, ADR log.

### Section 1 — System diagram

```
                        ┌──────────────────┐
                        │   CS Tool        │
                        │  (Gmail plugin   │
                        │   in Phase 3)    │
                        └────────┬─────────┘
                                 │ HTTPS POST /draft
                                 ▼
                        ┌──────────────────┐
                        │   FastAPI        │
                        │   pf-phase2      │
                        ├──────────────────┤
                        │ /health          │
                        │ /draft           │
                        │ /retrieve        │
                        │ /eval            │
                        └────┬──────┬──────┘
                             │      │
                  ┌──────────┘      └──────────┐
                  ▼                             ▼
         ┌─────────────────┐          ┌─────────────────┐
         │  MockVectorStore│          │   OpenAI API    │
         │  (Phase 2)      │          │   (or self-     │
         │                 │          │   hosted in 3)  │
         │ - policy_chunks │          ├─────────────────┤
         │ - shipments     │          │ - gpt-4o-mini   │
         └────────┬────────┘          │ - text-embed-3  │
                  │                   │   (Phase 3)     │
                  ▼                   └─────────────────┘
         ┌─────────────────┐
         │  shipments.json │
         │  (daily export) │
         └─────────────────┘
```

### Section 2 — Component choices

| Component | Choice | Alternative | Why |
|---|---|---|---|
| Backend | FastAPI | Flask, Django | Async-native, OpenAPI built-in, Pydantic validation |
| Vector store | In-process mock (Phase 2) | Pinecone, pgvector | Mock is deterministic, free, ships in 1 day. Migrate to Pinecone at 10K+ chunks. (See ADR-0002.) |
| LLM | gpt-4o-mini | gpt-4o, claude-3-5-haiku | 30x cheaper than gpt-4o, near-equal for this task |
| Embedding | (Phase 3) text-embedding-3-small | ada-002, Cohere | TBD in Phase 3 |
| Tracker | shipments.json (file) | MySQL API, PHP API | Daily export is the only option today (Daniel's API is Phase 3) |
| Auth | None (Phase 2) | JWT, Clerk | Internal service, behind VPN. Add auth in Phase 3 when exposed. |
| Deployment | Single VM (AWS SG) | Fargate, K8s | $5/mo, Daniel manages it. Migrate to Fargate at multi-region. |

### Section 3 — Capacity model

| Volume | Compute | Storage | Monthly cost |
|---|---|---|---|
| 150 emails/day (today) | VM t3.small | <1 GB | $5/mo VM + $1-3/mo LLM = **~$7/mo** |
| 1,500 emails/day (10x) | VM t3.medium | <1 GB | $15/mo VM + $10-30/mo LLM = **~$35/mo** |
| 15,000 emails/day (100x) | Fargate x2 | Pinecone free tier | $50/mo Fargate + $50/mo Pinecone + $100-300/mo LLM = **~$400/mo** |

**Scaling cliffs:**
- 1,500 emails/day: add Redis for query caching, move LLM calls to async
- 15,000 emails/day: add queue (Celery + Redis), move embeddings to Pinecone, add rate limiting
- 150,000 emails/day: multi-region, CDN, dedicated inference endpoint

### Section 4 — Cost model (per 1K drafts)

| Component | Cost per 1K drafts |
|---|---|
| Embedding (Phase 3, 50 tokens) | $0.001 |
| LLM input (350 tokens system + 200 user) | $0.083 |
| LLM output (150 tokens) | $0.090 |
| VM (allocated) | $0.17 |
| **Total per 1K drafts** | **$0.35** |

At 150 emails/day × 22 days = 3,300 drafts/month = **$1.15/month in LLM**. Customer ceiling is $200/month. **Headroom: 174x.**

### Section 5 — Failure modes

| Failure | Detection | Recovery |
|---|---|---|
| OpenAI rate limit | 429 response | Retry with exponential backoff (3x) — already in Phase 1's complete() |
| OpenAI down | 5xx response | Fall back to canned replies (Phase 1's MOCK_RESPONSES) |
| shipments.json stale | `last_event_at` older than 36h | Log a warning; continue (the 24h lag is expected) |
| Email body too long | LLM call exceeds token limit | Truncate to 2,000 chars, log a warning |
| Eval regression | CI fails on `any_regressed=true` | Block the deploy; revert the prompt change |
| Daniel's VM crashes | Platform health check fails | Auto-restart; Mei's Slack channel is paged |

### Section 6 — ADR log (links to C3)

- [ADR-0001: FastAPI over Flask](./decisions/0001-fastapi.md)
- [ADR-0002: Mock vector store over Pinecone for Phase 2](./decisions/0002-mock-vector-store.md)
- [ADR-0003: Eval regression threshold 0.05](./decisions/0003-eval-regression-threshold.md)

### Section 7 — When to migrate off this stack

| Trigger | Migration |
|---|---|
| > 10K chunks in the mock | Switch to Pinecone or pgvector (real embeddings) |
| > $50/mo in OpenAI | Add Claude Haiku as fallback, enable prompt caching |
| > 5 CS users | Add JWT auth, rate limiting per user |
| Customer in EU | Move to OpenAI EU region |
| Mei needs the drafter on mobile | Add a web UI (Gmail plugin → web app) |

---

## 🏛️ FDE Lens — the technical reality underneath

The PRD's FRs map directly to the technical lessons:

| FR | Lesson that teaches it |
|---|---|
| FR-1 (extract ID) | T1 (`_extract_id` regex) |
| FR-2 (look up status) | T1 (`_find_shipment` against `shipments.json`) |
| FR-3 (augment with retrieved policy) | T2 (`build_rag_prompt` + `MockVectorStore.retrieve`) |
| FR-4 (reply in customer's language) | T1 (`complete()` with the email as user prompt) |
| FR-5 (never invent a status) | T1 (style-guide rule, enforced by the prompt) |
| FR-6 (escalate on refund/anger) | T2 (intent detection in retrieved chunks) |

The design doc's component choices map to the 8 service files in `service/`:

| Design-doc component | Service file |
|---|---|
| FastAPI service | `service/app.py` |
| Mock vector store | `service/rag.py` |
| RAG prompt builder | `service/rag.py::build_rag_prompt` |
| Eval harness | `service/eval.py` |
| LLM client | Reused from Phase 1's `03-modern-ai-tooling.py` |
| Daily tracker | `phase-1-foundations/shared/shipments.json` |
| Style guide | `phase-1-foundations/shared/style-guide.md` (chunked by `shared/build_policy_chunks.py`) |
| Tests | `service/tests/test_app.py` |

The PRD tells the engineer *what* to build. The design doc tells the exec *how* it will be built and what it costs. Both are derivable from the 1-pager + the discovery deck. **You cannot write the design doc without the discovery deck answers** — every component choice traces back to a Q6-Q10 answer.

## 🌙 Reflect

Write 3-5 sentences:

1. The PRD has 6 FRs. Each has an acceptance criterion. The customer asks "why so few?" — what do you say?
2. The design doc's capacity model says "$7/mo at 150 emails/day." The customer asks "what if we 10x?" What's the cost, and what's the migration trigger?
3. The design doc lists 6 failure modes. The customer asks "what if the eval is wrong?" What's the recovery?
4. The PRD says "FR-6: Refuse to send a draft about a refund." The customer asks "can we add 'refund' to the drafter in Phase 3?" What's the FDE's response?
5. The PRD + design doc are 5 pages. The customer's exec sponsor asks for a 1-page summary. What do you cut?

**What's next** — C3 introduces the **ADR** (Architecture Decision Record), the artifact that records *why* a design choice was made. The design doc lists the choices; the ADRs record the reasoning. Together, they're the consulting track's deliverable: discovery deck (what we heard) + PRD (what we're building) + design doc (how we'll build it) + ADRs (why we built it this way).
