# Module 5 — Project Deep Dives (the 45-minute presentation)

> **The project deep dive is the highest-leverage round.** You pick 1 project, you present it for 45 minutes, and the interviewer decides whether they trust you to do the work at their company. **The signal: a candidate who can talk about 1 project for 45 minutes — with depth on the technical decisions AND the customer-facing consequences — is showing they can own a system at scale.**

---

## The 4 sections (45 minutes, in this order)

### Section 1: Context (5 minutes)

- **The customer** (1-2 sentences): who they are, what they do, why they needed the system.
- **The problem** (2-3 sentences): what was broken, what was the cost of the broken-ness, what was the timeline.
- **The constraint** (1 sentence): the cost ceiling, the latency SLO, the compliance boundary.

**The signal:** a senior FDE names the customer, the problem, AND the constraint. The constraint is the operational boundary; it's the FDE signal.

**PacificFreight example:**

> "PacificFreight is a 12-person cross-border logistics SMB in Singapore. They process 150 customer emails/day through a 3-person CS team. By the time I joined, Mei (the CS lead) was spending 4 hours/day on the same 5 templates — refund status, ETA inquiry, address change, damaged package, lost package. The cost of the broken-ness: 4 hours/day × $30/hour × 3 CS reps = $360/day in wasted labor. The constraint: a $5/month LLM ceiling (PacificFreight's CFO said no to a higher line item). The timeline: 6 weeks to MVP, 4 months to production."

### Section 2: Approach (15 minutes)

- **The architecture** (5 minutes, with a diagram): the 4 services, the 3 data stores, the 2 LLM calls.
- **The eval set** (3 minutes): the 30-row eval set, the 4 metrics, the 0.05 threshold.
- **The cost model** (3 minutes): the $/month calculation, the cost ceiling, the SLM vs hosted decision.
- **The runbook** (2 minutes): the 8 sections, the on-call rotation, the RACI.
- **The handoff** (2 minutes): the 5-question test, the principal-level 10-question test.

**The signal:** a senior FDE has an architecture diagram AND an eval set AND a cost model AND a runbook. The 4 artifacts are the FDE signal.

**PacificFreight example:**

> "The architecture is 4 services: the retrieval service (BM25 + dense + RRF), the inference service (GPT-4o-mini or SLM), the feedback service (thumbs-up/down), the metrics service (Prometheus + JSONL). The 3 data stores are: in-process (the retrieval index), Postgres (the shipments + drafts + feedback), and Redis (the rate limiter, added in Phase 5). The eval set is 30 rows, stratified by shipment type + difficulty, with 4 metrics: faithfulness, ansrel, context_precision, context_recall. The 0.05 threshold is the contract between prompt engineer and customer — any regression above 0.05 blocks the PR. The cost model is $0.50/week at 150 emails/day, $4.09/month at 1500 emails/day (10× growth). The runbook is 24 pages, with 8 sections + the 4 Phase 5 sections. The handoff is the 5-question test (5/5 from 3 stakeholders at 30/60/90 days)."

### Section 3: Outcome (10 minutes)

- **The metrics** (3 minutes): the 35/35 tests, the eval set green, the cost under ceiling, the uptime.
- **The customer feedback** (3 minutes): Mei's quotes, Sarah's metrics, Daniel's sign-off.
- **The evolution** (4 minutes): the Phase 1→5 narrative, the 4 projects, the 5 case studies.

**The signal:** a senior FDE has metrics AND customer quotes AND an evolution narrative. The 3 are the FDE signal.

**PacificFreight example:**

> "By week 8: 35/35 tests pass, eval set green at 0.94 faithfulness (above the 0.90 threshold), $0.50/week under the $5/month ceiling, 99.5% uptime. Mei: 'The drafter saves me 3 hours/day. I trust it.' Sarah: 'The Monday iteration cadence is the best part of my week.' Daniel: 'The runbook is what I needed. I can own this.' By month 6: 100× growth (1500 emails/day), the cost ceiling held, 10/10 at the 90-day check, 3 next FDEs trained. The system is now a platform that 12 tenants use."

### Section 4: Tradeoffs + What I'd Do Differently (15 minutes)

- **The 3 tradeoffs** (5 minutes, named + defended): the LLM choice, the in-process state vs Redis, the monolith vs microservices.
- **The 5 things I'd do differently** (5 minutes, with specifics): the 5 lessons from the case studies.
- **The Q&A** (5 minutes, the interviewer asks follow-ups).

**The signal:** a senior FDE has 3 tradeoffs AND 5 lessons AND 5 minutes of Q&A. The 3+5+5 is the FDE signal.

**PacificFreight example:**

> "The 3 tradeoffs: (1) GPT-4o-mini over Qwen-1.5B for the MVP — the operational complexity of self-hosting was too high; we switched at 10× growth in Phase 4 P3. (2) In-process state over Redis for the MVP — we switched at 100× growth in Phase 5 P1. (3) Monolith over microservices — we still haven't switched; the team is 3 FDEs, not 30. The 5 things I'd do differently: (1) start with the eval set in week 1, not week 4; (2) set the cost ceiling at 50% of willingness-to-pay, not 100%; (3) pre-approve the multi-tenant YAML when the 2nd tenant signs; (4) add a 'growth event' detector; (5) make the cost ceiling a config, not a code change."

---

## The 5 deep-dive anti-patterns

1. **Spending 30 minutes on the architecture diagram.** The diagram is 5 minutes; the eval set + cost model + runbook + handoff are the other 10 minutes. The diagram is the easy part; the operational artifacts are the FDE signal.
2. **Skipping the customer quotes.** "Mei liked it" is not a customer quote. "Mei said: 'The drafter saves me 3 hours/day. I trust it.'" is a customer quote. The quote is the signal.
3. **Naming 1 tradeoff.** 3 tradeoffs, with defense. Always.
4. **Skipping the "what I'd do differently" section.** A senior FDE has 5 lessons. A junior FDE has none.
5. **Going over time.** 45 minutes is 45 minutes. Practice with a timer. Going over is a red flag; finishing 5 minutes early is a green flag.

---

## The 3 deep-dive formats

### Format 1: The "ship + scale" deep dive (default for PacificFreight)

- 5 min context, 15 min approach, 10 min outcome, 15 min tradeoffs
- The 45-minute PacificFreight drafter narrative
- Best for: senior FDE roles at Anthropic, OpenAI, AWS

### Format 2: The "build from scratch" deep dive (for greenfield projects)

- 5 min context, 20 min approach (the architecture is the bulk), 10 min outcome, 10 min tradeoffs
- The 45-minute greenfield narrative
- Best for: founding FDE roles at startups (Kepler, Contour)

### Format 3: The "rescue" deep dive (for engagements that started broken)

- 5 min context (the broken-ness is the headline), 15 min approach (the diagnosis), 10 min outcome (the fix), 15 min tradeoffs (the lessons)
- The 45-minute rescue narrative
- Best for: senior FDE roles at consulting firms, large enterprise

**Pick Format 1 by default.** Formats 2 and 3 are for specific stories; Format 1 fits 80% of FDE roles.

---

## The slide deck (12 slides, 45 minutes, 3-4 minutes per slide)

| Slide | Title | Content | Time |
|---|---|---|---|
| 1 | Title | Project name, customer, your role | 1 min |
| 2 | The customer | PacificFreight, Mei, Sarah, Daniel | 2 min |
| 3 | The problem | 4 hours/day × 3 CS reps = $360/day | 3 min |
| 4 | The constraint | $5/month LLM ceiling | 1 min |
| 5 | The architecture | 4 services, 3 data stores, 2 LLM calls (diagram) | 5 min |
| 6 | The eval set | 30 rows, 4 metrics, 0.05 threshold | 3 min |
| 7 | The cost model | $0.50/week at 150 emails/day | 3 min |
| 8 | The runbook | 8 sections + 4 Phase 5 sections, 24 pages | 2 min |
| 9 | The metrics | 35/35 tests, 0.94 faithfulness, $0.50/week, 99.5% uptime | 3 min |
| 10 | The customer feedback | Mei, Sarah, Daniel quotes | 3 min |
| 11 | The 3 tradeoffs | LLM, state, monolith | 5 min |
| 12 | The 5 lessons | The 5 things I'd do differently | 5 min |
| + Q&A | The interviewer's questions | (5-10 min) | |

**12 slides, 30-35 minutes of talking, 10-15 minutes of Q&A.** That's the 45-minute deep dive.

---

## How to use this module

1. **Pick your best project.** PacificFreight is the default; use another if you have one.
2. **Write the 4 sections** (context, approach, outcome, tradeoffs) in 1 page each.
3. **Build the 12-slide deck.** 3-4 minutes per slide.
4. **Rehearse out loud, timed.** 45 minutes total, 5 minutes Q&A.
5. **Rehearse with an AI assistant.** Have it score you on the 5 anti-patterns.
6. **Practice the 5 follow-up questions** (below). They're the most common Q&A.

---

## The 5 most common deep-dive follow-up questions

| Question | The FDE answer |
|---|---|
| 1. "What was the hardest part?" | "Convincing Daniel to externalize the rate limiter to Redis. He didn't want the operational complexity. I showed him the failover test — when the primary VM went down, the in-process state was lost. He signed off in 1 PR." |
| 2. "What would you do differently?" | "Start with the eval set in week 1, not week 4. The first 4 weeks of prompt engineering produced 3 prompts that all regressed the eval set. I should have built the eval set first." |
| 3. "How did you measure success?" | "The 5-question test. 3 stakeholders, 5 questions, 5/5 at 30/60/90 days. The metric is the test; the test is the contract." |
| 4. "What happened when it broke?" | "Engagement 3: the week 11 SEV-1. OpenAI had a 10-minute outage; the drafter hallucinated 4 wrong shipment statuses. Mei reverted 4 drafts in 5 minutes. I added the circuit breaker in week 12; we haven't had a SEV-1 since." |
| 5. "How did you hand it off?" | "Engagement 5 + 10. The 5-question test for the customer, the 10-question test for the next FDE. 6 weeks of structured KT, 2 weeks of shadow operation, 2 weeks of independent operation with the FDE on standby. 3 next FDEs, 10/10 at 90 days." |

**Memorize these 5.** They're the Q&A for 80% of project deep dives.
