# Module 2 — Decomposition Questions (Palantir-style open-ended)

> **Decomposition questions are the FDE's signature round.** Pioneered at Palantir, now standard at Anthropic, OpenAI, AWS FDE, and LangChain. The format: 60 minutes, open-ended, no right answer. The interviewer gives you a fuzzy problem ("Design a system for X") and watches how you think. **The signal: do you clarify, decompose, design, and defend tradeoffs — or do you jump to a technology?**

---

## The 4-step framework (the same one for every round)

### Step 1: Clarify (5-7 minutes, not 2)

Ask 5 questions before drawing anything. The questions are the signal. The questions a senior FDE asks are:

1. **Who is the user?** (CS team, ops team, IT, end customer?)
2. **What's the scale?** (QPS, storage, growth rate?)
3. **What's the constraint?** (Cost ceiling, latency SLO, regulatory?)
4. **What's the failure mode?** (Worst-case if the system is down?)
5. **What's the timeline?** (MVP in 2 weeks, production in 2 months?)

**The 5 questions are the FDE signal.** The candidate who asks them is showing they understand the customer. The candidate who doesn't is showing they understand the technology (which is the wrong signal for an FDE role).

**Example:** "Design a system for processing 10,000 customer emails per day."
- **Junior answer:** "We'd use an LLM with a RAG pipeline, store embeddings in Pinecone, and serve via FastAPI."
- **Senior FDE answer:** "Before I draw, can I ask 5 questions? Who writes the emails — the customer or the CS team? Is the 10,000/day steady or bursty? What's the cost ceiling? What's the latency budget? And what's the failure mode if the LLM hallucinates a wrong shipment status?"

The senior FDE just bought 5 minutes of thinking time AND showed the customer-facing mindset.

### Step 2: Decompose (10-12 minutes)

After the 5 questions, list:

- **3-5 entities** (User, Email, Shipment, Response, Metric)
- **3-5 services** (one per entity, roughly; some entities share a service)
- **3-5 flows** (User creates Email, Email triggers Retrieval, Retrieval feeds LLM, LLM produces Response, Response is sent to User)

**The signal:** the candidate who can list entities + services + flows without naming a technology is showing they can think before they build. **The technology comes in step 3.**

**Example:** "So we have Users (CS team, ~50 people), Emails (~10k/day inbound), Shipments (the data we look up), Drafts (the LLM output), and Metrics (thumbs-up rate, cost per draft). The flow is: Email arrives → Retrieval fetches Shipment data → LLM produces Draft → User approves or edits → Metric is logged."

### Step 3: Design (15-20 minutes)

Now the technology. Pick the simplest design that satisfies the constraints:

- **API contracts** (3-5 endpoints with request/response shape)
- **Data model** (3-5 tables/collections with keys + indexes)
- **Scale model** (QPS, storage, bandwidth, cost)
- **Failure modes** (what happens when X is down)

**The signal:** the candidate who names the QPS AND the cost ceiling AND the failure mode is showing they understand the operational boundary.

**Example:** "API: POST /draft (in: email_id; out: draft_text, citations, request_id). Data: shipments table (PK shipment_id, B-tree on customer_id for lookup), emails table (PK email_id), drafts table (PK draft_id, FK email_id). Scale: 10k emails/day = 0.12 QPS average, 1.2 QPS peak. Cost ceiling: $5/month for LLM, $20/month for infra. Failure: if LLM is down, return a templated draft ('We're looking into this — we'll get back to you in 24 hours')."

### Step 4: Tradeoffs (5-7 minutes)

Name 3+ tradeoffs, defend the choice. Not "I picked Redis because it's fast" — but "I picked Redis over Postgres for the rate limiter because (a) we need sub-millisecond reads, (b) we don't need ACID, (c) Redis's TTL primitive saves us from writing a cleanup job. The tradeoff is durability — if Redis goes down, we lose 60 seconds of rate-limit state, which is acceptable for our use case."

**The signal:** the candidate who names 3 tradeoffs (not 1) and defends the choice is showing they understand the customer-facing consequence of the technical decision.

---

## The 5 most common decomposition questions (with the framework applied)

### 1. "Design a system for processing 10,000 customer emails per day."

(Answer template in §1 above. Phase 2 PacificFreight drafter is the artifact.)

### 2. "Design a system for tracking shipments across multiple carriers."

- **Clarify:** Who queries? (CS team, end customer, ops?) What's the latency budget? (real-time, or batched every 5 min?) What's the failure mode? (wrong status, missed update?)
- **Decompose:** Carriers (FedEx, UPS, DHL), Shipments (the entity), Webhooks (the inbound events), Status (the cached state), Users (CS team, end customer).
- **Design:** 1 webhook endpoint per carrier (3 endpoints); 1 status cache (Redis with 5-min TTL); 1 query endpoint (GET /shipment/{id} → cache hit/miss → carrier API). QPS: 1k webhooks/min peak. Cost: $0 cache + $0 carrier API + $0 storage.
- **Tradeoffs:** Polling vs webhooks (we chose webhooks for freshness, accepted the carrier-side complexity). Single-region vs multi-region (we chose single-region for the MVP, multi-region is Phase 5 P4). Carrier API direct vs aggregator (we chose direct for cost, accepted the per-carrier integration work).

### 3. "Design a system for a CS team to use AI to draft replies to customer emails."

This is the PacificFreight drafter. **The answer is the Phase 2 + Phase 4 + Phase 5 architecture.** The framework:

- **Clarify:** Same as Q1.
- **Decompose:** Same as Q1, plus the Eval Set, the Runbook, the Cost Ceiling, the On-Call Rotation (the operational entities).
- **Design:** Same as Q1, plus the eval-set-as-spec, the runbook-as-contract, the cost-ceiling-as-score, the handoff-as-proof. The technology is FastAPI + Redis + Postgres + an LLM. The artifact is the runbook + the eval set.
- **Tradeoffs:** Same as Q1, plus the FDE-specific tradeoffs: do we use a hosted LLM (we did, GPT-4o-mini at $0.15/1M tokens) or fine-tune our own (Phase 4 P3 SLM, at 0.5% of the cost at 91% of the quality). Do we use a vector DB (we did, in-process for MVP, Pinecone for scale) or just BM25 (we did, for the policy corpus, because the policy doesn't change often).

### 4. "Design a system for a 10-person team to share documents with external collaborators."

- **Clarify:** What's the doc type? (text, PDFs, slides?) Who are the external collaborators? (customers, vendors, partners?) What's the permission model? (per-doc, per-team, per-org?) What's the compliance boundary? (HIPAA, SOC 2, GDPR?)
- **Decompose:** Users (internal + external), Documents (the entity), Permissions (the access control), Audit (the log of who saw what), Notifications (the email/Slack alerts).
- **Design:** 1 doc storage (S3 with per-doc encryption key); 1 permission store (Postgres with row-level security); 1 audit log (append-only, 7-year retention); 1 share endpoint (POST /share with email + permission + expiry). QPS: 100 shares/day, 1k reads/day. Cost: $10/month S3 + $5/month Postgres.
- **Tradeoffs:** Per-doc encryption (we chose yes for HIPAA, accepted the key management overhead) vs bucket-level (simpler but no per-doc revocation). Audit log destination (we chose Postgres for queryability, accepted the 7-year storage cost) vs S3 (cheaper but harder to query). Expiring shares (we chose yes for least-privilege, accepted the cron job to clean up expired shares).

### 5. "Design a system for a company to deploy AI models in production with cost ceilings."

This is the Phase 5 cost-ceiling breach case study. **The answer is the Phase 5 P1-4 architecture.**

- **Clarify:** What's the cost ceiling? (per-customer, per-tenant, per-month?) What's the scale? (1 customer or 100?) What's the failure mode? (over-budget, latency spike, hallucination?)
- **Decompose:** Customers (the tenants), Drafts (the LLM output), Cost Meter (the running bill), Circuit Breaker (the kill switch), Cost Alert (the page on-call).
- **Design:** 1 LLM router (per-tenant model choice + per-tenant cost ceiling); 1 cost meter (Prometheus counter, scraped every 10s); 1 circuit breaker (kill switch at 80% of ceiling); 1 alert (Prometheus alertmanager at $X/wk). QPS: 10k drafts/day. Cost: $4.09/month per tenant at 10× growth.
- **Tradeoffs:** Per-tenant rate limit (we chose Redis token bucket for cross-worker atomicity, accepted the Redis dependency) vs per-worker (simpler but doesn't scale past 1 process). Cost ceiling as config (we chose YAML for code-reviewability, accepted the 1-PR-to-change) vs in code (simpler but no per-tenant override). Auto-failover on cost breach (we chose manual, accepted the on-call burden) vs automatic (less burden but risk of false positives).

---

## The 4 anti-patterns (what NOT to do)

1. **Naming a technology before step 1.** "We'd use Redis, Postgres, and an LLM" is a junior answer. The technology comes in step 3.
2. **Skipping the failure mode.** Every system has a failure mode. If you don't name it, the interviewer assumes you haven't shipped one.
3. **Picking one tradeoff.** A senior FDE names 3 tradeoffs and defends the choice. "I picked X because Y" is one tradeoff. "I picked X over Y because Z, but the cost is W" is one tradeoff with defense. "I picked X over Y and Z, and the cost is W and V" is three.
4. **Asking only technical questions.** "What's the QPS?" is a technical question. "Who is the user?" is a customer question. The FDE signal is the customer question.

---

## How to use this module

1. **Read `01-clarify.md` → `04-tradeoffs.md` in order.** Each file is one step of the framework.
2. **Pick a decomposition question from the 5 examples.** Run the framework on it, timed. 60 minutes total.
3. **Rehearse with an AI assistant.** Give it the question, run the framework out loud, have it score you on the 4 anti-patterns.
4. **Use the Phase 1-5 case studies as your "real-world example" answer.** When the interviewer asks "have you ever designed a system like this?" — yes, PacificFreight, here's the architecture doc.

---

## The 5-question Palantir-specific test

Palantir's decomposition round has 5 sub-rounds (called "the 5 questions"). They test:

1. **"How would you design a system for X?"** (decomposition)
2. **"What's the data model?"** (entities + relationships)
3. **"How would you scale this 10x?"** (bottleneck identification)
4. **"What would you do differently if you had 2 months instead of 2 weeks?"** (tradeoffs + MVP thinking)
5. **"Tell me about a time you shipped a system like this."** (Phase 1-5 case studies)

**The 5 sub-rounds are the 4-step framework + the behavioral answer.** Same prep, same artifacts, same STAR format.
