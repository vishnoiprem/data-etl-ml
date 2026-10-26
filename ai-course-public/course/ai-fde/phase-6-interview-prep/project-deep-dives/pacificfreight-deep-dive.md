# The PacificFreight Deep Dive (the canonical 45-minute script)

> **This is the script.** It's the 12-slide deck, the 4 sections, and the 5 follow-up Q&A answers. Use it as-is, or adapt it to your own project. **The signal: a candidate who can deliver this script without notes, in 45 minutes, is showing they can own a system at scale.**

---

## Slide 1: Title (1 min)

> "Today I'm going to walk you through the PacificFreight drafter — a customer-facing AI service I built and handed off over 6 months. PacificFreight is a 12-person cross-border logistics SMB in Singapore. I was the FDE; Mei was the CS lead, Sarah was the ops lead, Daniel was the IT owner. The drafter went from 0 to 15,000 emails/day across 12 tenants, with a $4.09/month cost ceiling, 35/35 tests, and 10/10 at the 90-day handoff check."

**Cue:** 1 minute. Don't go over.

---

## Slide 2: The customer (2 min)

> "PacificFreight has 3 CS reps in Singapore and 9 ops people split between Singapore and Vietnam. They process 150 customer emails/day, mostly in English and Vietnamese. Mei leads the CS team; she's been with PacificFreight for 6 years. Sarah runs ops; she joined 2 years ago from DHL. Daniel is the IT owner; he's a one-person IT shop. The customer-facing metric is thumbs-up rate on the drafts. The ops metric is cost per draft. The IT metric is uptime + on-call burden."

**The signal:** 3 stakeholders, 3 metrics, 3 roles. A senior FDE names all 3.

---

## Slide 3: The problem (3 min)

> "By week 0, Mei was spending 4 hours/day on the same 5 templates: refund status, ETA inquiry, address change, damaged package, lost package. That's 12 hours/day of template work for a 3-person team. At $30/hour fully loaded, that's $360/day in wasted labor — $130k/year. The CFO had tried 3 off-the-shelf tools; none of them worked because the shipment tracking data is in a custom internal API. The constraint: a $5/month LLM ceiling. The CFO said no to a higher line item."

**The signal:** the cost of the broken-ness, the 3 failed attempts, the constraint. A senior FDE quantifies the problem.

---

## Slide 4: The constraint (1 min)

> "The $5/month LLM ceiling is the operational boundary. At 150 emails/day, with GPT-4o-mini at $0.15/1M tokens, the bill is $0.50/week = $2.17/month. Under the ceiling. At 10× growth (1500 emails/day), the bill is $21.70/month. Over the ceiling. So the constraint forces a Phase 4 P3 decision: either switch to a self-hosted SLM, or set a higher ceiling, or rate-limit aggressively. We did all 3, eventually."

**The signal:** the constraint, the calculation, the 3 options. A senior FDE names the math.

---

## Slide 5: The architecture (5 min, with diagram)

```
[Customer Email]
      ↓
[Retrieval Service: BM25 + dense + RRF]
      ↓
[Inference Service: GPT-4o-mini or Qwen-1.5B + LoRA]
      ↓
[Draft Service: Postgres + Redis rate limiter]
      ↓
[Feedback Service: thumbs-up/down]
      ↓
[Metrics Service: Prometheus + JSONL usage log]
```

> "4 services, 3 data stores, 2 LLM calls. The retrieval service is hybrid — BM25 for the policy corpus (which doesn't change often), dense embeddings for the shipment data (which changes daily), and RRF to fuse them. The inference service routes to GPT-4o-mini by default, and to Qwen-1.5B + LoRA when the cost ceiling is at 80%. The draft service persists the draft + citations + the request_id. The feedback service logs thumbs-up/down with the user_id + timestamp. The metrics service emits Prometheus counters and writes to a JSONL usage log for the Monday iteration review."

**The signal:** 4 services, 3 data stores, 2 LLM calls. A senior FDE has a diagram AND the 1-line description per box.

---

## Slide 6: The eval set (3 min)

> "The eval set is 30 rows, stratified by shipment type (5 types × 6 rows) and difficulty (easy/medium/hard × 10 rows each). 4 metrics: faithfulness (does the draft match the retrieved context?), ansrel (is the draft relevant to the email?), context_precision (did we retrieve the right chunks?), context_recall (did we retrieve all the relevant chunks?). The threshold is 0.05 — any regression above 0.05 blocks the PR. The eval set is the contract between prompt engineer and customer; the prompt is the implementation."

**The signal:** 30 rows, 4 metrics, 0.05 threshold, the contract framing. A senior FDE knows the eval set is the spec.

---

## Slide 7: The cost model (3 min)

> "Cost breakdown: $0.50/week at 150 emails/day. LLM: $0.30/week (GPT-4o-mini at $0.15/1M tokens × 1.5M tokens/week). Infra: $0.10/week (1 VM, 4 vCPU, 8GB RAM). Storage: $0.10/week (10GB Postgres + 1GB JSONL logs). Total: $2.17/month at 1× growth, $21.70/month at 10× growth. The ceiling is $5/month. So at 10× growth, the cost ceiling is breached — and the fix is the SLM (Qwen-1.5B + LoRA at $0.001/1M tokens) or the multi-tenant split (so the 2nd tenant pays for their own usage). We did both in Phase 4 P3 + Phase 5 P2."

**The signal:** the $/month calculation, the ceiling, the 2 fixes. A senior FDE names the math AND the 2 options.

---

## Slide 8: The runbook (2 min)

> "The runbook is 24 pages, 8 sections: (1) System overview, (2) On-call rotation, (3) Incident response, (4) Eval set maintenance, (5) Cost monitoring, (6) Customer feedback, (7) Deployment, (8) Handoff. Plus 4 Phase 5 sections: Redis, OAuth + multi-tenant, gVisor, multi-region DR. Daniel owns it; he re-reads it quarterly. The on-call rotation is a 3-FDE rotation; SEV-1 pages the on-call, SEV-2 emails the FDE shadow. The runbook is what survives the FDE's exit."

**The signal:** 24 pages, 8 sections, the on-call rotation, the handoff framing. A senior FDE has a runbook.

---

## Slide 9: The metrics (3 min)

> "By week 8: 35/35 tests pass. Eval set green at 0.94 faithfulness (above the 0.90 threshold). $0.50/week under the $5/month ceiling. 99.5% uptime. Mei's thumbs-up rate: 79%+. Sarah's Monday iteration review: 12 weeks, 0 SEV-1s. Daniel's on-call burden: 0 pages. By month 6: 100× growth (1500 emails/day), 12 tenants, 2 regions, the cost ceiling held at $4.09/month, 10/10 at the 90-day check, 3 next FDEs trained."

**The signal:** 35/35, 0.94, $0.50, 99.5%, 79%+, 10/10. A senior FDE has 5+ metrics, all named.

---

## Slide 10: The customer feedback (3 min)

> "Mei: 'The drafter saves me 3 hours/day. I trust it. The thumbs-up rate is the only metric I check.' Sarah: 'The Monday iteration cadence is the best part of my week. I see the cost, the eval set, the customer feedback — all in 30 minutes.' Daniel: 'The runbook is what I needed. I can own this. The 5-question test is the rubric.' All 3 stakeholders answered 5/5 at the 30/60/90-day checks. The system ran after I exited."

**The signal:** 3 customer quotes, with the metric they each care about. A senior FDE has the customer's words.

---

## Slide 11: The 3 tradeoffs (5 min)

> "Three tradeoffs I made. (1) GPT-4o-mini over Qwen-1.5B for the MVP — the operational complexity of self-hosting was too high for a 1-person IT shop; we switched at 10× growth in Phase 4 P3. (2) In-process state over Redis for the MVP — we switched at 100× growth in Phase 5 P1; the trigger was a failover test that lost 60 seconds of rate-limit state. (3) Monolith over microservices — we still haven't switched; the team is 3 FDEs, not 30. The tradeoffs are reversible; the operational complexity is the constraint."

**The signal:** 3 tradeoffs, named + defended + the trigger for revisiting. A senior FDE has 3 tradeoffs memorized.

---

## Slide 12: The 5 lessons (5 min)

> "Five things I'd do differently. (1) Start with the eval set in week 1, not week 4. The first 4 weeks of prompt engineering produced 3 prompts that all regressed the eval set. (2) Set the cost ceiling at 50% of willingness-to-pay, not 100%. The 100× growth breached the $5/month ceiling; the alert gave 1 week of warning instead of 5. (3) Pre-approve the multi-tenant YAML when the 2nd tenant signs the contract, not when they ask for it. (4) Add a 'growth event' detector — when Mei's team grows from 12 to 120, the system should proactively propose the multi-tenant split. (5) Make the cost ceiling a config, not a code change. The ceiling is in app.py today; it should be in a per-tenant YAML."

**The signal:** 5 lessons, with specifics. A senior FDE has 5 lessons, not 1.

---

## Q&A (5-10 min)

The 5 most common follow-up questions, with the FDE answers:

1. **"What was the hardest part?"** → "Convincing Daniel to externalize the rate limiter to Redis. He didn't want the operational complexity. I showed him the failover test — when the primary VM went down, the in-process state was lost. He signed off in 1 PR."

2. **"What would you do differently?"** → "Start with the eval set in week 1, not week 4. The first 4 weeks of prompt engineering produced 3 prompts that all regressed the eval set. I should have built the eval set first."

3. **"How did you measure success?"** → "The 5-question test. 3 stakeholders, 5 questions, 5/5 at 30/60/90 days. The metric is the test; the test is the contract."

4. **"What happened when it broke?"** → "Engagement 3: the week 11 SEV-1. OpenAI had a 10-minute outage; the drafter hallucinated 4 wrong shipment statuses. Mei reverted 4 drafts in 5 minutes. I added the circuit breaker in week 12; we haven't had a SEV-1 since."

5. **"How did you hand it off?"** → "The 5-question test for the customer, the 10-question test for the next FDE. 6 weeks of structured KT, 2 weeks of shadow operation, 2 weeks of independent operation with the FDE on standby. 3 next FDEs, 10/10 at 90 days."

---

## How to use this script

1. **Read it 3 times.** Internalize the flow.
2. **Rehearse out loud, timed.** 45 minutes total, 5-10 minutes Q&A. The total is 50-55 minutes; budget accordingly.
3. **Cut slides 7-8 if you're over time.** They're the "nice to have" slides; slides 1-6, 9-12 are the "must have."
4. **Rehearse the 5 Q&A answers.** They're 80% of the follow-ups.
5. **Adapt to your project.** If your project is greenfield, use Format 2 from `../README.md`; if it's a rescue, use Format 3.
