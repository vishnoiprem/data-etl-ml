# Anthropic FDE — Customer Simulation + Constitutional AI (the safety-first loop)

> **Source:** Synthesized from 3 industry sources: (1) the Anthropic-specific patterns in the Sundeep Teki 2026 FDE definitive guide (`sundeepteki.org/advice/the-definitive-guide-to-forward-deployed-engineer-interviews-in-2026`); (2) the Sundeep Teki AI Research Engineer interview guide (`sundeepteki.org/advice/the-ultimate-ai-research-engineer-interview-guide-cracking-openai-anthropic-google-deepmind-top-ai-labs`); (3) the FDE roadmap GitHub repo (`github.com/thecoder8890/forward-deployed-engineer-roadmap`). **Anthropic's FDE loop is the only major FDE loop where the customer simulation round is the highest-signal stage — and where Constitutional AI / Responsible Scaling Policy is a testable interview topic.**

---

## 1. What was the loop?

The Anthropic FDE loop is **5 stages over ~20 days**, faster than the Palantir 28-35 day loop but more concentrated on safety + ethics. The signature round is the **customer simulation** (the "highest-signal stage of the loop" per the FDE-interviews synthesis), which is structurally different from the decomposition round at Palantir.

| Stage | Length | What they tested | What they wanted |
|---|---|---|---|
| 1. Recruiter screen | 30 min | Background, motivation, why FDE, why Anthropic | Mission alignment with safety + AGI responsibility |
| 2. Technical screen | 60 min | Coding (with their usual AI tools allowed) | How you plan, prompt, and verify — not just the final answer |
| 3. **Customer simulation** | **45-60 min** | Stay calm with a frustrated executive, scope live, push back without damaging the relationship, know when to say no | "Whether they stay calm with a frustrated executive, avoid overpromising, and explain trade-offs" |
| 4. System design + take-home | 60 min + 1 week | Design + build a customer deployment; show the rollout plan + evals | A working deployment artifact that demonstrates the full FDE skillset (build + deploy + measure) |
| 5. Hiring manager | 60 min | Motivation, past failures, depth of ownership | Mission conviction under follow-up; specific metrics + trade-offs from past work |

**The Anthropic-specific signal:** Anthropic "conducts rigorous reference checks *during* the interview cycle" (per the AI Research Engineer guide). Your references will be called while you're in process, not after the offer.

**The candidate's framing (per the FDE roadmap):** "Build production apps inside customer systems, deliver technical artifacts, codify deployment patterns. Travel 25-50%. Focus on safety and reliability."

**The compensation:** Anthropic Applied AI Engineer pays $350K-$550K; FDE compensation tracks similarly. The 2025-2026 range for FDE-style roles: senior $300K-$450K+, top-tier $600K+.

---

## 2. The customer simulation round (the signature round)

**Length:** 45-60 min role play.

**The format:** the interviewer plays a **frustrated executive** (often a CIO, VP of Engineering, or head of compliance at a regulated-industry customer). You are the FDE in the room. The scenario typically:

- Starts with a vague or escalating problem ("our pilot is failing," "legal won't sign off," "the eval is below the threshold")
- Includes a hostile or impatient stakeholder who wants a quick answer
- Requires you to scope live, push back without damaging the relationship, and know when to say no
- Tests for overpromising (the most common failure mode)

**The opening line pattern (per the FDE-interviews synthesis):** "The verbatim opener from Anthropic's customer-simulation round, reported as the highest-signal stage of the loop. The customer is mid-pilot, the eval is below threshold, and legal has blocked deployment pending a hallucination incident last week."

**The 5 common scenarios (per the FDE roadmap + Beon.tech synthesis):**

1. **"A client demanding a chatbot in two weeks"** — Test of scoping + pushing back. The candidate must say "no" or "2-week MVP with limited scope" without losing the deal.
2. **"A hostile internal engineering team"** — Test of cross-functional empathy. The candidate must navigate the "I don't trust your AI" objection.
3. **"Scope quietly expanding mid-project"** — Test of ownership + saying no. The candidate must hold the line.
4. **"A bank wants AI to summarize customer support tickets"** — Test of compliance + scoping. The candidate must ask the right discovery questions (PII, audit, retention).
5. **"A hospital wants an AI assistant for doctors, but legal is worried about hallucinations"** — Test of safety + trade-offs. The candidate must propose mitigations (confidence thresholds, human-in-the-loop) without dismissing the concern.

**The 4 things they test:**

1. **Calm under pressure** — Do you escalate your own emotional state when the stakeholder escalates?
2. **No overpromising** — Do you agree to deadlines you can't hit? Do you promise accuracy numbers you can't deliver?
3. **Trade-off explanation** — Can you explain "we can ship 2 weeks faster if we drop the eval threshold, but here's the failure mode" in plain English?
4. **Knowing when to say no** — Do you have the conviction to walk away from a bad scope, or do you capitulate?

**The guide's actual advice:** "The candidate must stay anchored to the customer outcome. The technical artifact matters less than the customer's confidence that the FDE can hold the scope and ship the result."

**The Phase 6 prep:** This is `../customer-simulation/README.md` (the discovery + scoping + pushback module, if present) + the behavioral module for the "no" pattern. The PacificFreight drafter's "we said no to Mei's refund tool" decision (Phase 4 cap-stone engagement) is the strongest signal you can bring.

---

## 3. The take-home / case study (system design + build)

**The format (per the FDE roadmap):** a 1-week take-home. The candidate is given a customer scenario + a deployment constraint + a stack constraint, and is asked to build a working deployment.

**The 3 typical prompts:**

1. **"Design a RAG system for an enterprise knowledge base with strict permissions."** — The permissions-aware RAG pattern. The candidate must show row-level access control, an audit log, and a per-team rate limit.
2. **"Design an AI agent that updates CRM records but requires human approval."** — The human-in-the-loop pattern. The candidate must show the approval flow, the rollback path, and the failure mode if the human is unavailable.
3. **"Build an agent workflow, define evals, harden."** — The end-to-end pattern. The candidate must show the agent's tool calls, the eval set, the guardrails, and the production rollout plan.

**The deliverables (per the FDE roadmap):**

- A scoped problem statement and discovery notes
- A design doc with tradeoffs, rollout plan, and success metrics
- Working code with tests
- Deployment artifacts and runbooks
- A short demo video and a written case study focused on outcomes

**The 4 most common failure modes (per the FDE roadmap):**

1. **Over-scoped solution** — the candidate builds the universe instead of an MVP
2. **No eval set** — the candidate ships without a way to measure success
3. **No rollback path** — the candidate assumes the first deploy is the only deploy
4. **No production-readiness artifacts** — the candidate submits code without runbooks, monitoring, or incident playbooks

**The Phase 6 prep:** This is `../take-home/01-prototype.md` + `../take-home/02-pipeline.md` (the take-home module) + the Phase 4 capstone's PacificFreight drafter as the reference implementation. The eval set is the differentiator; the candidate who ships a working agent with no evals will fail.

---

## 4. The Constitutional AI / Responsible Scaling Policy round (the safety depth signal)

**The format:** a 30-60 min deep-dive round embedded in either the customer simulation or the system design round. Tested via **ethical dilemmas and downside-risk scenarios**.

**The 5 topics (per the AI Research Engineer guide):**

1. **Constitutional AI** — Anthropic's method for shaping Claude's behavior from public perspectives. The candidate must explain how it works and what its limitations are.
2. **RLHF (Reinforcement Learning from Human Feedback)** — the candidate must explain how it shapes model behavior, what its failure modes are, and how you'd evaluate it.
3. **Responsible Scaling Policy** — Anthropic's framework for capability-based safety commitments. The candidate must explain the ASL (AI Safety Level) framework and when each level is triggered.
4. **Alignment** — the candidate must reason about how a deployed agent's behavior could drift from its intended behavior, and what mitigations are available.
5. **Red teaming + adversarial robustness** — the candidate must explain how you'd red-team a customer-facing agent and what attack vectors you'd test for.

**The framing (per the AI Research Engineer guide):** "A candidate who is technically brilliant but dismissive of safety concerns is a 'Type I Error' for Anthropic — a hire they must avoid at all costs."

**The 4 most common mistakes (per the guide):**

1. **Dismissive answers** — "I don't think safety is a real concern" or "that's overblown." This is the disqualifier.
2. **Paralysis** — refusing to make a deployment decision because of hypothetical risks. The candidate must reason about trade-offs, not hide behind "I don't know."
3. **Generic RLHF explanations** — saying "we collect human feedback and train on it" without discussing the failure modes.
4. **Ignoring the customer outcome** — the safety answer must be grounded in the customer outcome, not abstract.

**The 4 sample questions (per the AI Research Engineer guide):**

1. "How would you design an eval set for a customer-facing agent that handles PII?"
2. "A customer's eval shows a 5% hallucination rate. Legal wants 0%. What do you do?"
3. "Explain the trade-offs between a confidence-threshold guardrail and a human-in-the-loop guardrail for a customer-support agent."
4. "How would you red-team a customer-facing agent before deployment?"

**The Phase 6 prep:** This is the Phase 1-5 case study on the in-process redaction (Phase 2 Module 4) + the circuit breaker pattern (Phase 2 Module 5). The candidate who can connect the PacificFreight circuit breaker to a Constitutional AI principle is signaling the FDE + safety intersection that Anthropic values.

---

## 5. The recruiter call (the 4 things they look for)

| # | Signal | What they test |
|---|---|---|
| 1 | Mission alignment with safety | Whether the candidate can articulate *why* safety matters at Anthropic specifically |
| 2 | Long-term fit | Signs of staying and growing, not "stepping stone" |
| 3 | Project self-awareness | How clearly the candidate reflects on what they've enjoyed and struggled with |
| 4 | Reference-check readiness | Whether the candidate's references will confirm the recruiter's read |

**The Anthropic-specific signal:** "Anthropic conducts rigorous reference checks *during* the interview cycle." The recruiter will ask for references in the first call, and those references will be called in week 2. Be ready.

**The 2 sample questions:**

1. "What are you looking for in your next role, and what do you want to work on?"
2. "Why Anthropic, and what specifically draws you to the mission?" — **The guide's advice: "Your reason needs to hold up under detail. Name a specific product (Claude Code, the API, the constitutional AI work) and a specific operational challenge you'd want to own."**

**The Phase 6 prep:** This is `../interview-process.md` (the FDE loop, day-in-the-life) + `../behavioral/README.md` (the 3 question types: customer interaction, disagreement, ambiguity) + a specific answer to "Why Anthropic?" grounded in Claude Code or Constitutional AI.

---

## 6. The hiring manager round (the 4 things they look for)

| # | Signal | What they test |
|---|---|---|
| 1 | Resolved doubts | Whether you close the gap on whatever the onsite panel flagged as weaker |
| 2 | Depth of ownership | How specifically you can speak to the metrics and trade-offs behind your past work |
| 3 | Self-reflection | How openly you discuss failures and what you took from them |
| 4 | Mission conviction | Whether your reasons for joining Anthropic hold up under follow-up |

**The 4 sample questions:**

1. "Why Anthropic, and why this team?"
2. "Tell me about a time you pushed back on a customer request."
3. "Tell me about your biggest failure."
4. "Walk me through the specific metrics and trade-offs from a project you owned."

**The guide's actual advice:** "Treat questions about past failures as a test of self-awareness, and answer with a specific example and what you changed afterward."

**The Phase 6 prep:** This is `../behavioral/README.md` (the 3 question types + the 5-question cheat sheet mapped to Phase 1-5 case studies) + `../project-deep-dives/README.md` (the 45-min presentation, because the HM will dig into specific metrics + trade-offs).

---

## 7. What did they test? (the consolidated signals)

### The 7 signals (across all 5 stages)

1. **"Stay calm with a frustrated executive."** → Customer simulation. The Anthropic-specific signal.
2. **"Avoid overpromising and explain trade-offs."** → Customer simulation. The scoping signal.
3. **"How you plan, prompt, and verify."** → Technical screen. The AI-tooling signal.
4. **"Mission alignment with safety + AGI responsibility."** → Recruiter + HM. The Anthropic-specific signal.
5. **"A candidate who is technically brilliant but dismissive of safety concerns is a Type I Error."** → Constitutional AI round. The disqualifier signal.
6. **"How you weigh the customer outcome against the safety risk."** → System design + customer sim. The trade-off signal.
7. **"References called during the interview cycle."** → Recruiter. The reference-check signal.

### The 4 anti-patterns (per the guide)

1. **Dismissive safety answers.** The Anthropic-specific disqualifier.
2. **Generic RLHF / Constitutional AI explanations.** The depth-of-knowledge signal.
3. **Overpromising in the customer simulation.** The scoping signal.
4. **Walking into the interview with no specific answer to "Why Anthropic?"** The motivation signal.

---

## 8. What's the Phase 6 module that preps each stage?

| Stage | Phase 6 module |
|---|---|
| 1. Recruiter call | `../interview-process.md` (the FDE loop, day-in-the-life) + `../behavioral/README.md` (the 3 question types) |
| 2. Technical screen | `../practical-coding/README.md` + `../swe-coding/README.md` (with AI tools allowed at Anthropic) |
| 3. **Customer simulation** | `../customer-simulation/README.md` (the 5 scenarios + the "no" pattern) + the behavioral module |
| 4. Take-home + system design | `../take-home/01-prototype.md` + `../take-home/02-pipeline.md` + `../system-design/README.md` |
| 5. Constitutional AI / safety depth | Phase 1-5 case studies (the in-process redaction, the circuit breaker, the eval-set-as-spec) |
| 6. Hiring manager | `../behavioral/README.md` (the 3 question types) + `../project-deep-dives/README.md` (the 45-min presentation) |

**The candidate's pre-Phase-6 prep time would have been:** ~4 weeks full-time, weighted 30% on customer simulation (the signature round) + 25% on Constitutional AI (the safety depth signal) + 20% on system design + 15% on take-home + 10% on behavioral.

---

## 9. The 5-pattern cheat sheet for Anthropic FDE prep

Based on this guide + the Phase 1-5 portfolio:

1. **Master the customer simulation.** Practice staying calm with a frustrated executive, scoping live, pushing back without damaging the relationship, and knowing when to say no. **This is the highest-signal round.**
2. **Read the Constitutional AI paper and the Responsible Scaling Policy.** Both are public. The candidate who can quote specific ASL levels + specific Constitutional AI principles is signaling the depth Anthropic values.
3. **Build a take-home with a real eval set.** The eval set is the differentiator. The candidate who ships a working agent with no eval set will fail.
4. **Prepare a specific answer to "Why Anthropic?"** Generic enthusiasm is a disqualifier. Name Claude Code, the API, Constitutional AI, or a specific operational challenge you'd want to own.
5. **Run mock customer simulations.** Pair with a friend who plays the frustrated executive. The signal is calm under pressure, not technical depth.

---

## 10. The 5 most common Anthropic FDE follow-up questions (inferred from this guide)

| Question | The FDE answer |
|---|---|
| 1. "Why Anthropic?" | "I've spent the last 6 months building a customer-facing AI service for PacificFreight, and the work that resonates most is the safety + reliability work Anthropic does on Claude Code: build production apps inside customer systems, deliver technical artifacts, codify deployment patterns. The operational challenge I want to own is the customer-facing safety surface — the in-process redaction, the eval-set-as-spec pattern, the circuit breaker that fails closed. Anthropic's FDE role is the only one I've seen that combines the build-it-and-ship-it FDE work with the safety + responsibility I care about." |
| 2. "A bank wants AI to summarize customer support tickets. How would you scope the first deployment?" | "Clarify first: the customer is a bank; the constraint is PII + audit + retention; the failure mode is a leak; the timeline is pilot in 2 weeks. Decompose: the PII redaction layer, the audit log, the eval set, the per-tenant rate limit. Design: a redaction-first RAG pipeline (PII redaction before the embedding step), append-only audit log, an eval set of 50 customer-support tickets with ground-truth summaries. Tradeoffs: redact at the embedding step (we chose this for downstream safety, accepted the latency cost) vs redact at the output step (faster but riskier). Data: the bank's ticket corpus, anonymized; the eval set is hand-labeled. Cost: $200/month for the redaction pipeline + $50/month for the eval harness." |
| 3. "A hospital wants an AI assistant for doctors, but legal is worried about hallucinations. What do you do?" | "I'd propose a confidence-threshold guardrail + a human-in-the-loop review for low-confidence outputs. The trade-off: we accept higher latency for safety. The eval set: 50 doctor queries with ground-truth answers, and we measure hallucination rate as the primary metric. The pilot scope: 1 department, 4 weeks, with a red-team pass at week 2. I'd refuse to ship without the confidence-threshold guardrail — the failure mode is a misdiagnosis, not a failed eval." |
| 4. "How would you design an eval set for a customer-facing agent that handles PII?" | "Three layers. (1) Functional: 50 hand-labeled queries with ground-truth answers, measuring exact match + semantic match. (2) Safety: 20 adversarial queries (PII extraction attempts, prompt injection), measuring refusal rate + no-leak rate. (3) Operational: latency (P95 < 2s), cost (per-query dollar cost), uptime (99.9% target). The eval set is the spec — if the eval set doesn't cover a failure mode, the deployment will fail at that failure mode." |
| 5. "Tell me about your biggest failure." | "Engagement 2 of my FDE portfolio: I told a legal-tech customer their data wasn't RAG-ready and walked away after 2 weeks. I lost 2 weeks of work. The lesson: I should have run the data audit in week 1, not week 2. I now run a 'data-readiness check' as the first deliverable of every engagement — 30 rows of sample data, 4 quality metrics, a go/no-go decision before any prompt engineering. Better to lose 2 weeks than ship a system that fails at week 11." |

**Memorize these 5.** They're the most common Anthropic FDE follow-ups based on this guide.

---

## 11. Anthropic-specific prep tips (the 5 from the guide)

1. **Master the customer simulation.** Practice staying calm with a frustrated executive, scoping live, pushing back without damaging the relationship, and knowing when to say no. **The guide's verdict: "This round filters the most candidates, and most engineers rarely prepare for it."**
2. **Read the Constitutional AI paper and the Responsible Scaling Policy.** Both are public. The candidate who can quote specific ASL levels + specific Constitutional AI principles is signaling the depth Anthropic values.
3. **Build a take-home with a real eval set.** The eval set is the differentiator. The candidate who ships a working agent with no eval set will fail.
4. **Prepare a specific answer to "Why Anthropic?"** Generic enthusiasm is a disqualifier. Name Claude Code, the API, Constitutional AI, or a specific operational challenge you'd want to own.
5. **Run mock customer simulations.** Pair with a friend who plays the frustrated executive. The signal is calm under pressure, not technical depth.

---

## 12. How to use this report

1. **Read it once.** Internalize the 5 stages + the customer simulation pattern + the Constitutional AI depth signal.
2. **Practice the customer simulation out loud.** Pair with a friend. The signal is calm under pressure, not technical depth.
3. **Read the Constitutional AI paper + the Responsible Scaling Policy.** Both are public.
4. **Build a take-home with a real eval set.** The eval set is the spec.
5. **Prepare for the "Why Anthropic?" question.** Specifics (Claude Code, Constitutional AI, the operational challenge) are required.
6. **Bring a Phase 1-5 case study as your "real customer" example.** PacificFreight is the default. Connect the circuit breaker to Constitutional AI.
7. **Be ready for reference checks during the cycle.** Have 3 references pre-briefed.

---

## 13. Anthropic compensation (FYI, for context)

- **Anthropic Applied AI Engineer:** $350K-$550K (per the FDE vs Applied AI Engineer guide)
- **Anthropic FDE (per the FDE definitive guide):** senior $300K-$450K+, top-tier $600K+

Compensation combines base + equity + bonus. Packages vary by experience and location. (Source: FDE-Academy, per the guide.)

---

## 14. The thesis

Anthropic's FDE loop is the only major FDE loop where the **customer simulation is the highest-signal stage** and the **Constitutional AI depth is a testable interview topic**. The 5 stages test the same 7 signals: customer simulation calm, no overpromising, AI-tool fluency, mission alignment with safety, technical depth + safety trade-off reasoning, customer outcome vs safety risk, and reference-check readiness. **The customer simulation is the differentiator** — most engineers never prepare for it, and it filters more candidates than any other round. The Constitutional AI depth is the disqualifier — a dismissive safety answer is a Type I Error for Anthropic.

**General FDE prep gets you past the resume screen. Anthropic-specific prep gets you past the customer simulation round.**
