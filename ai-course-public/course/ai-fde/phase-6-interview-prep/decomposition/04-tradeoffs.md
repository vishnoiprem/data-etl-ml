# Step 4 — Tradeoffs (3+ tradeoffs, not 1)

> **The tradeoff step is the FDE's signature.** A senior FDE names 3 tradeoffs, defends the choice, and explains the customer-facing consequence. A junior FDE names 1 tradeoff and says "I picked X because it's faster." **The signal: a candidate who names 3 tradeoffs is showing they understand the system has consequences.**

---

## The 3-tradeoff rule (always)

Every design decision has at least 3 alternatives. Naming 1 is a junior answer. Naming 3 is a senior FDE answer.

### The structure

For each design decision:

1. **Decision:** What did you pick?
2. **Alternative 1:** What else could you have picked?
3. **Alternative 2:** What else could you have picked?
4. **Alternative 3:** What else could you have picked?
5. **Why this one:** What was the customer-facing consequence that drove the choice?
6. **What you'd revisit:** Under what conditions would you change your mind?

**Example: the LLM choice**

| | Option | Cost | Quality | Latency | Operational complexity |
|---|---|---|---|---|---|
| 1 | **GPT-4o-mini (hosted)** | $0.15/1M tokens | 0.94 faithfulness | 1.5s P95 | Low (API call) |
| 2 | **Qwen-1.5B + LoRA (self-hosted)** | $0.001/1M tokens | 0.91 faithfulness | 0.8s P95 | High (GPU/serve) |
| 3 | **Claude Sonnet (hosted)** | $3/1M tokens | 0.97 faithfulness | 2.0s P95 | Low (API call) |
| 4 | **Rule-based + LLM fallback** | $0.05/1M tokens | 0.85 faithfulness | 0.3s P95 | Medium (rules + API) |

**The senior FDE answer:** "We picked GPT-4o-mini for the MVP. The cost ($0.15/1M tokens) is below the $5/month ceiling at 10k emails/day; the quality (0.94 faithfulness) is above the 0.90 threshold; the operational complexity is low (no GPU). The tradeoff: if the cost ceiling drops to $1/month, we'd switch to Qwen-1.5B + LoRA — that's the Phase 4 P3 SLM. If the quality threshold rises to 0.97, we'd switch to Claude Sonnet. The 4th option (rule-based) is for the case where latency matters more than quality."

**The signal:** 4 alternatives, named, with cost + quality + latency + complexity, AND a "what you'd revisit" condition. That's the FDE answer.

---

## The 5 tradeoff anti-patterns

1. **Naming 1 alternative.** "I picked X because Y" is 1 alternative. "I picked X over Y and Z because W, and the cost is V" is 3 alternatives with defense.
2. **Naming alternatives without comparison.** "We could have used Postgres or MongoDB" is naming. "We picked Postgres over MongoDB because ACID matters for the refund flow; the cost is sharding at 10× growth, which we accept because the cost ceiling is per-tenant, not per-shard" is comparison.
3. **Skipping the customer-facing consequence.** The FDE role is customer-facing. Every tradeoff has a customer-facing consequence. If you don't name it, the interviewer assumes you haven't shipped.
4. **Defending the choice without the cost.** "We picked X" without "the cost is Y" is incomplete. The cost is the signal.
5. **Not naming a "what you'd revisit" condition.** A senior FDE knows when their choice is wrong. A junior FDE defends forever.

---

## The 5 most common FDE tradeoffs (the cheat sheet)

### 1. Hosted LLM vs self-hosted SLM

| | Hosted LLM (GPT-4o-mini) | Self-hosted SLM (Qwen-1.5B + LoRA) |
|---|---|---|
| Cost | $0.15/1M tokens | $0.001/1M tokens |
| Quality | 0.94 faithfulness | 0.91 faithfulness |
| Latency | 1.5s P95 | 0.8s P95 (local) |
| Operational complexity | Low (API) | High (GPU + serve) |
| When to switch | (default) | When cost ceiling drops 10× |

**The FDE answer:** "We start with hosted; we switch to self-hosted when the cost ceiling is the binding constraint."

### 2. In-process state vs Redis

| | In-process (dict) | Redis |
|---|---|---|
| Cost | $0 | $10/month |
| Cross-worker consistency | No | Yes (atomic Lua) |
| Operational complexity | Low (no extra service) | Medium (Redis + Sentinel) |
| When to switch | (default for MVP) | When 2+ workers, or state must survive restart |

**The FDE answer:** "We start in-process; we switch to Redis when the system needs to scale horizontally. PacificFreight hit this at 100× growth (Phase 5 P1)."

### 3. Monolith vs microservices

| | Monolith (single service) | Microservices (5+ services) |
|---|---|---|
| Cost | $20/month | $200/month |
| Operational complexity | Low (1 deploy) | High (5 deploys, 5 on-calls) |
| Velocity | High (1 PR) | Medium (cross-service PR) |
| When to switch | (default) | When 5+ engineers, or services need different SLOs |

**The FDE answer:** "We start monolithic; we split when the team size or the SLO differentiation justifies the operational cost."

### 4. SQL vs NoSQL

| | SQL (Postgres) | NoSQL (MongoDB, DynamoDB) |
|---|---|---|
| ACID | Yes | No (or limited) |
| Schema flexibility | Low (migrations) | High (schemaless) |
| Query power | High (joins, aggregations) | Medium (denormalized) |
| When to pick | When ACID matters (refunds, payments) | When schema is fluid (user-generated content) |

**The FDE answer:** "We pick SQL for transactional flows (refund.create); we pick NoSQL for content (drafts, feedback) where schema is fluid."

### 5. Webhook vs polling

| | Webhook (push) | Polling (pull) |
|---|---|---|
| Freshness | Real-time | 5-min lag |
| Operational complexity | High (carrier reliability) | Low (we control the cadence) |
| Cost | $0 (carrier pushes) | $0 (we pull) |
| When to pick | When freshness matters, AND carrier supports it | When freshness can lag, OR carrier is unreliable |

**The FDE answer:** "We pick webhooks for the carriers that support them (FedEx, UPS); we pick polling for the ones that don't (regional carriers)."

---

## The "what you'd revisit" cheat sheet

| If this changes | Revisit |
|---|---|
| Cost ceiling drops 10× | Switch from hosted LLM to SLM |
| Team grows past 5 engineers | Split the monolith |
| QPS grows past 10k | Add read replicas, then multi-region |
| Latency SLO tightens to < 500ms | Add edge cache, switch to SLM (faster) |
| Compliance requires HIPAA | Add per-record encryption, audit log, no LLM with PII |
| 2nd tenant signs up | Multi-tenant (OAuth + per-tenant YAML) |

**The cheat sheet is the FDE's "I know when I'm wrong" signal.** A senior FDE has these 6 conditions memorized and applies them in the tradeoff step.

---

## How to use this file

1. **Memorize the 3-tradeoff rule.** Every design decision has 3 alternatives.
2. **Memorize the 5 most common tradeoffs.** They're the cheat sheet for 80% of FDE interviews.
3. **Memorize the "what you'd revisit" cheat sheet.** The 6 conditions cover 80% of the "when would you change your mind" follow-up.
4. **Practice on the 5 sample questions in `../README.md`.** Time yourself: 5-7 minutes for the tradeoffs.
5. **Rehearse with an AI assistant.** Have it score you on the 5 anti-patterns.
6. **Close with the "what you'd revisit" line.** "If the cost ceiling drops 10×, we'd switch to SLM. If the team grows past 5 engineers, we'd split the monolith." That's the FDE answer.
