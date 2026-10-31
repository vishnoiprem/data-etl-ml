# Week 4 — Modern Data Architecture and AI Engineering

> **Week 4 · 5 lessons · 1 case study**
> **Objective:** Be able to design and defend the architecture of a secure, scalable, AI-ready enterprise data platform.

## The single principle

> **Architecture is the answer to "how do we deliver the strategy at scale, with reliability, on budget, and with the right security posture?"**

Week 2 was the *what* (strategy, AI portfolio, 3-year plan, 90-day plan). Week 3 was the *how much* (ROI, budget, prioritization). This week is the *how* — the technical architecture that makes the strategy real.

The CDO interview will probe architecture at three levels:

1. **Strategic architecture** — lakehouse vs. warehouse vs. mesh, cloud vs. on-prem, build vs. buy.
2. **Operational architecture** — ingestion, transformation, semantic layer, observability, FinOps.
3. **AI architecture** — feature store, model serving, RAG, agent platform, evaluation, guardrails.

You must be able to draw the boxes, name the trade-offs, and defend the choices. The interviewer is not asking you to be the engineer who built it. They are asking you to be the executive who decided it.

## Daily structure (90 min)

| Day | Lesson | Deliverable |
|---|---|---|
| Day 16 | Data platform architecture | The 5 layers of a modern data platform |
| Day 17 | Cloud migration and multi-cloud | A migration playbook with phases and risk |
| Day 18 | Reliability and scalability | SLAs, SLOs, error budgets, observability |
| Day 19 | ML architecture | Feature store, training, serving, monitoring |
| Day 20 | GenAI architecture | RAG, agents, evaluation, guardrails |

**Case study (90 min, weekend):** Design a secure, scalable enterprise data & AI platform for a 10M-customer retailer. Present in 30 minutes.

## The deliverable for the week

A **Data & AI Platform Architecture** — a 1-page diagram + 5-page narrative with:

1. The 5 layers (ingestion, storage, transformation, semantic, consumption)
2. The 3 cloud choices (with rationale)
3. The 4 SLAs (ingestion latency, query latency, model freshness, uptime)
4. The 5 security controls (IAM, encryption, lineage, audit, key mgmt)
5. The 3 AI platform components (feature store, RAG, agent runtime)
6. The build-vs-buy choices with rationale
7. The 3-year cost trajectory

## Scoring for Week 4 (out of 100)

| Competency | Weight | What "great" looks like |
|---|---|---|
| Technical judgment and architecture | 50% | The architecture has a story; the trade-offs are named |
| Strategic and business thinking | 20% | The architecture supports the business strategy |
| Commercial and financial understanding | 15% | The build-vs-buy and cost trajectory are credible |
| Governance and risk | 10% | The security and compliance controls are in the design |
| Communication and structure | 5% | The diagram is clear; the narrative is short |

A score below 90 means Week 4 is not done. Re-record.

## Production checklist

- [ ] Day 16 — I can draw the 5 layers of a modern data platform
- [ ] Day 17 — I can name the 6 R's of migration (rehost, replatform, refactor, etc.)
- [ ] Day 18 — I can name the SLAs, SLOs, and error budget for each layer
- [ ] Day 19 — I can draw the ML lifecycle architecture (feature → train → serve → monitor)
- [ ] Day 20 — I can draw the GenAI architecture (RAG → agent → eval → guardrail)
- [ ] Case study 04 — I can present the architecture in 30 minutes

---

**Next:** Week 5 — Data Governance, Security and Responsible AI.