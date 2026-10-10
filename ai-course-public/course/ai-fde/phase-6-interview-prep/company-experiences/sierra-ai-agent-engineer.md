# Sierra AI Agent Engineer — Build + Demo + Customer Simulation (the customer-agent specialist)

> **Source:** Synthesized from the Exponent Sierra AI Agent Engineer interview experience (`tryexponent.com/courses/ai-company-interview-experiences/sierra-ai-agent-engineer-may-2025`), the Sierra AI-specific patterns in the FDE roadmap GitHub repo, and the LangChain-overlap patterns from the LangChain Deployed Engineer guide. **Sierra AI is the customer-agent specialist — the company is built around "the customer-facing AI agent" as a product, and their loop is the most take-home-heavy of the major FDE loops.** The signature round is the **take-home demo + customer simulation**, where the candidate must demo a working agent and then defend it under a customer-simulation pressure test.

---

## 1. What was the loop?

The Sierra AI Agent Engineer loop is **4-5 stages over ~3-4 weeks**. The loop is **take-home-first**: the take-home is the centerpiece (typically 1 week), and the customer simulation is a separate round that follows. The signature pattern is "build the agent, demo it, then defend it under pressure."

| Stage | Length | What they tested | What they wanted |
|---|---|---|---|
| 1. Recruiter screen | 30 min | Background, motivation, why Sierra, customer-agent experience | Cross-functional potential (dev + customer + product) |
| 2. **Take-home: build a customer-support agent** | **1 week** | A working agent + a written case study + a demo video | End-to-end shipping: discovery, design, build, eval, deploy, demo |
| 3. **Take-home demo walkthrough** | **60 min** | The candidate demos the agent; the interviewers have already run the code | "Demo was actually briefer than expected; Interviewers had already run the code" — they want to see how you handle "wait, why did you choose X?" |
| 4. **Customer simulation** | **45-60 min** | Push back on the agent's design under pressure, scope a follow-up engagement, hold the line | The same signals as AWS/Anthropic customer simulation, but the artifact is the agent you built |
| 5. Hiring manager | 60 min | Motivation, past failures, depth of ownership | Mission conviction under follow-up; specific metrics + trade-offs from past work |

**The candidate's framing (per the Exponent report):** "First half: Demo the agent you built in take-home. Demo was actually briefer than expected; Interviewers had already run the code."

**The Sierra-specific signal:** the interviewers **run the candidate's code before the demo**. This means: (1) the code must actually work end-to-end (no "TODO: deploy this"), (2) the candidate must be ready to explain every design decision, and (3) the demo should be brief because the substantive conversation is about choices, not features.

**The compensation (per the FDE definitive guide):** mid-level (3-5 yrs) $200K-$350K; senior (5+ yrs) $300K-$450K+; top-tier $600K+. Sierra is a high-paying AI startup with the standard 25-40% premium over traditional SWEs.

---

## 2. The take-home (the centerpiece, 1 week)

**The time budget:** 1 week (the candidate's time, asynchronous).

**The format:** build a customer-support agent for a fictional customer (typically an outdoor gear company, a streaming service, or an e-commerce store). The customer data is provided: products, customer records, purchase history, refund/returns data.

**The 3 typical customer scenarios (per the Exponent reports + the FDE roadmap):**

1. **"Build your own customer service AI agent for a hypothetical outdoors company."** — The outdoor gear customer. The agent handles product recommendations, order status, returns, and shipping questions.
2. **"Design an AI agent for a streaming service."** — The streaming customer. The agent handles subscription management, content recommendations, billing questions, and device troubleshooting.
3. **"Build a customer service agent using LangGraph."** — The framework-specific variant. The agent is built on LangGraph (or a comparable orchestrator), with multi-step workflows and human-in-the-loop handoffs.

**The deliverables (per the FDE roadmap + the Exponent reports):**

- A scoped problem statement and discovery notes
- A design doc with tradeoffs, rollout plan, and success metrics
- Working code with tests
- Deployment artifacts and runbooks
- A short demo video and a written case study focused on outcomes
- **An eval set** — the differentiator

**The 4 most common failure modes (per the FDE roadmap):**

1. **Over-scoped solution** — the candidate builds the universe instead of an MVP. The outdoor gear agent doesn't need 20 tools; it needs 5.
2. **No eval set** — the candidate ships without a way to measure success. The customer can't tell if the agent is good or bad.
3. **No rollback path** — the candidate assumes the first deploy is the only deploy. What happens when the agent hallucinates a refund?
4. **No production-readiness artifacts** — the candidate submits code without runbooks, monitoring, or incident playbooks.

**The guide's actual advice:** "Have a clean personal project template ready. A well-documented 70% solution beats an undocumented 100% solution."

**The Phase 6 prep:** This is `../take-home/01-prototype.md` + `../take-home/02-pipeline.md` (the take-home module) + the Phase 4 capstone's PacificFreight drafter as the reference implementation. The eval set is the differentiator.

---

## 3. The take-home demo walkthrough (the signature round, 60 min)

**Length:** 60 min.

**The format:** the candidate demos the agent. The interviewers have **already run the code** before the meeting. The demo is brief (5-10 min) because the substantive conversation is about choices.

**The 4 things they test:**

1. **Demo discipline** — Can you demo in 5-10 minutes? A 30-minute demo is a fail.
2. **Design rationale** — Can you explain every design decision? "Why did you choose tool X?" "Why is the eval set structured this way?" "Why did you scope to 5 tools instead of 20?"
3. **Receptiveness to feedback** — When the interviewer pushes back on a design decision, do you update in real time or defend?
4. **Trade-off reasoning** — Can you explain the trade-offs of every choice? Memory vs latency, eval coverage vs eval cost, multi-step vs single-step.

**The candidate's framing (per the Exponent report):** "Demo was actually briefer than expected; Interviewers had already run the code." The candidate who treats the demo as a 30-minute product pitch loses; the candidate who treats it as a 5-minute preview + a 50-minute design conversation wins.

**The 5 common demo questions (inferred from the Exponent reports + the FDE roadmap):**

1. **"Walk us through the agent's flow. Why did you structure it this way?"**
2. **"What's the eval set, and how did you choose the metrics?"**
3. **"What happens when the agent hallucinates a refund? What's the rollback path?"**
4. **"Why did you choose this framework / tool / model?"**
5. **"If you had 2 more weeks, what would you build next?"**

**The Phase 6 prep:** This is `../take-home/01-prototype.md` (the demo script) + the project-deep-dives module (the 45-min presentation pattern). The candidate who has a 5-minute demo script + 10 design decisions pre-articulated is signaling the FDE signal.

---

## 4. The customer simulation (the second signature round, 45-60 min)

**Length:** 45-60 min role play.

**The format:** the interviewer plays a **frustrated customer** (the same customer from the take-home, typically). The scenario tests whether the candidate can defend their agent under pressure, scope a follow-up engagement, and know when to say no.

**The 3 typical scenarios:**

1. **"Your agent just hallucinated a $500 refund. What do you do?"** — Test of incident response + customer trust.
2. **"The customer's success team wants to add 10 more tools to the agent. How do you scope?"** — Test of pushback + scoping.
3. **"The customer's eval is below threshold. They want to ship anyway. What do you do?"** — Test of no overpromising + trade-off explanation.

**The 4 things they test:**

1. **Calm under pressure** — Do you escalate your own emotional state when the customer escalates?
2. **No overpromising** — Do you agree to ship a below-threshold agent to keep the customer happy?
3. **Trade-off explanation** — Can you explain "we can ship faster if we accept a 3% hallucination rate, but here's the failure mode" in plain English?
4. **Knowing when to say no** — Do you have the conviction to walk away from a bad scope?

**The Phase 6 prep:** This is `../customer-simulation/README.md` (the discovery + scoping + pushback module, if present) + the behavioral module for the "no" pattern. The PacificFreight drafter's "we said no to Mei's refund tool" decision (Phase 4 cap-stone engagement) is the strongest signal you can bring.

---

## 5. The recruiter call (round 1)

**Length:** 30 min.

**The 4 things they test:**

1. **Why Sierra, why customer-agent work** — The candidate must articulate why Sierra specifically, not "I want to do AI agent work."
2. **Customer-facing experience** — Sierra is built around customer agents; the candidate must have cross-functional potential.
3. **Comp realism** — The candidate should bring a real target comp number, not "I'm flexible."
4. **Energy** — Customer-agent work is intense. The recruiter is looking for sustained energy.

**The guide's actual advice:** "Bring a tight 60-second answer to 'why FDE' and a separate 60-second answer to 'why Sierra,' plus a real target comp number."

**The 2 sample questions:**

1. "What are you looking for in your next role, and what do you want to work on?"
2. "Why Sierra, and what specifically draws you to the customer-agent work?"

**The Phase 6 prep:** This is `../interview-process.md` (the FDE loop, day-in-the-life) + `../behavioral/README.md` (the 60-second answers). The candidate who has a 60-second "why FDE" answer + a 60-second "why Sierra" answer pre-prepared is signaling the FDE signal.

---

## 6. The hiring manager round (round 5)

**Length:** 60 min.

**The 4 things they test:**

1. **Resolved doubts** — Whether the candidate closes the gap on whatever the onsite panel flagged as weaker.
2. **Depth of ownership** — How specifically the candidate can speak to the metrics and trade-offs behind their past work.
3. **Self-reflection** — How openly the candidate discusses failures and what they took from them.
4. **Mission conviction** — Whether the candidate's reasons for joining Sierra hold up under follow-up.

**The 4 sample questions:**

1. "Why Sierra, and why this team?"
2. "Tell me about a time you pushed back on a customer request."
3. "Tell me about your biggest failure."
4. "Walk me through the specific metrics and trade-offs from a project you owned."

**The guide's actual advice:** "Treat questions about past failures as a test of self-awareness, and answer with a specific example and what you changed afterward."

**The Phase 6 prep:** This is `../behavioral/README.md` (the 3 question types) + `../project-deep-dives/README.md` (the 45-min presentation).

---

## 7. What's the Phase 6 module that preps each round?

| Round | Phase 6 module |
|---|---|
| 1. Recruiter screen | `../interview-process.md` (the FDE loop, day-in-the-life) + `../behavioral/README.md` (the 60-second answers) |
| 2. Take-home (1 week) | `../take-home/01-prototype.md` + `../take-home/02-pipeline.md` (the take-home module) |
| 3. **Demo walkthrough** | `../take-home/01-prototype.md` (the demo script) + `../project-deep-dives/README.md` (the 45-min presentation) |
| 4. **Customer simulation** | `../customer-simulation/README.md` (the 3 scenarios + the "no" pattern) + the behavioral module |
| 5. Hiring manager | `../behavioral/README.md` (the 3 question types) + `../project-deep-dives/README.md` (the 45-min presentation) |

**The candidate's pre-Phase-6 prep time would have been:** ~4 weeks full-time, weighted 35% on the take-home (the centerpiece) + 25% on the demo walkthrough + 20% on the customer simulation + 10% on behavioral + 10% on the recruiter screen.

---

## 8. The 5-pattern cheat sheet for Sierra AI Agent Engineer prep

Based on this guide + the Phase 1-5 portfolio:

1. **Build a take-home with a real eval set.** The eval set is the differentiator. The candidate who ships a working agent with no eval set will fail.
2. **Demo in 5-10 minutes, then defend the choices.** A 30-minute demo is a fail. The substantive conversation is about choices, not features.
3. **Practice the customer simulation out loud.** The interviewers will push back on the agent's design. The signal is calm under pressure + receptiveness to feedback.
4. **Rehearse 5 design decisions.** "Why this framework?" "Why this eval set?" "Why this scope?" The candidate who can't defend their choices in 60 seconds fails.
5. **Prepare a specific answer to "Why Sierra?"** Generic enthusiasm is a disqualifier. Name specific Sierra products, specific operational challenges, and specific customer outcomes.

---

## 9. The 5 most common Sierra AI follow-up questions (inferred from this guide)

| Question | The FDE answer |
|---|---|
| 1. "Why Sierra?" | "I've spent the last 6 months building a customer-facing AI service for PacificFreight, and the work that resonates most is the same work Sierra does: build production customer-support agents, deliver technical artifacts, codify deployment patterns. The operational challenge I want to own is the multi-tenant data isolation + the eval-set-as-spec pattern at scale. Sierra's customer-agent focus gives me a structured way to deepen the customer-facing FDE work I want to do." |
| 2. "Walk us through the agent's flow. Why did you structure it this way?" | "The agent has 5 tools: tracker.lookup, refund.create, translate.to, escalate.to_human, and recommend.product. The flow is: classify the customer intent (3 categories: status, refund, recommendation), route to the right tool, validate the tool output (eval check), then send the response. The trade-offs: I chose 5 tools instead of 20 because the eval coverage drops as the tool count rises; I chose a classifier instead of an LLM router because the classifier is 10x faster and 50x cheaper; I chose a refund-amount validator because hallucinated refunds are the highest-cost failure mode." |
| 3. "What's the eval set, and how did you choose the metrics?" | "The eval set is 50 hand-labeled customer queries across the 3 intent categories. The metrics: (1) intent classification accuracy (target 95%), (2) tool selection accuracy (target 90%), (3) response faithfulness (target 85%, measured against retrieved context), (4) hallucination rate (target < 5%, measured by a second LLM judge), (5) latency P95 (target < 2s). I chose these metrics because they map to the customer's success criteria: 'the agent should never hallucinate a refund' is the highest-priority signal." |
| 4. "What happens when the agent hallucinates a refund?" | "The agent has a refund-amount validator that checks the requested amount against the order history. If the amount is > 110% of the order total, the agent escalates to a human before processing. The eval set includes 5 hallucinated-refund test cases; the agent catches 4 of 5 (the 5th is a near-miss that the eval set didn't catch — that's a known limitation, and I'd add it to the eval set in week 2). The rollback path: a 1-click refund reversal in the admin dashboard, with an audit log of every refund + reversal." |
| 5. "Tell me about your biggest failure." | "Engagement 2 of my FDE portfolio: I told a legal-tech customer their data wasn't RAG-ready and walked away after 2 weeks. I lost 2 weeks of work. The lesson: I should have run the data audit in week 1, not week 2. I now run a 'data-readiness check' as the first deliverable of every engagement — 30 rows of sample data, 4 quality metrics, a go/no-go decision before any prompt engineering. Better to lose 2 weeks than ship a system that fails at week 11." |

**Memorize these 5.** They're the most common Sierra AI Agent Engineer follow-ups based on this guide.

---

## 10. Sierra-specific prep tips (the 5 from the guide)

1. **Build a take-home with a real eval set.** The eval set is the differentiator. The candidate who ships a working agent with no eval set will fail.
2. **Demo in 5-10 minutes, then defend the choices.** A 30-minute demo is a fail. The substantive conversation is about choices, not features.
3. **Practice the customer simulation out loud.** The interviewers will push back on the agent's design. The signal is calm under pressure + receptiveness to feedback.
4. **Rehearse 5 design decisions.** "Why this framework?" "Why this eval set?" "Why this scope?" The candidate who can't defend their choices in 60 seconds fails.
5. **Prepare a specific answer to "Why Sierra?"** Generic enthusiasm is a disqualifier. Name specific Sierra products, specific operational challenges, and specific customer outcomes.

---

## 11. How to use this report

1. **Read it once.** Internalize the 5 stages + the take-home-first pattern + the demo + customer-simulation dynamic.
2. **Build a take-home with a real eval set.** The eval set is the spec.
3. **Rehearse the 5-minute demo.** The interviewers have already run the code; the demo is a preview, not a pitch.
4. **Rehearse 5 design decisions.** "Why this framework?" "Why this eval set?" "Why this scope?"
5. **Practice the customer simulation out loud.** Pair with a friend. The signal is calm under pressure + receptiveness to feedback.
6. **Prepare for the "Why Sierra?" question.** Specifics (specific Sierra products, operational challenges, customer outcomes) are required.
7. **Bring a Phase 1-5 case study as your "real customer" example.** PacificFreight is the default. Connect the circuit breaker to the eval-set-as-spec pattern.

---

## 12. Sierra AI compensation (FYI, for context)

- **Mid-level (3-5 yrs):** $200K-$350K
- **Senior (5+ yrs):** $300K-$450K+
- **Top-tier:** $600K+

Compensation combines base + equity + bonus. Sierra is a high-paying AI startup with the standard 25-40% premium over traditional SWEs. (Source: Sundeep Teki 2026 FDE guide, per Levels.fyi.)

---

## 13. The thesis

Sierra AI's Agent Engineer loop is the **most take-home-heavy of the major FDE loops**, with the 1-week take-home as the centerpiece. The 5 stages test the same 7 signals: customer-agent focus, end-to-end shipping, demo discipline, design rationale, customer-simulation calm, no overpromising, and trade-off reasoning. **The take-home eval set + the 5-minute demo + the customer-simulation pushback are the differentiators** — most engineers never prepare for the "interviewers have already run the code" pattern, and it filters more candidates than any other round. The customer-simulation under pressure is the disqualifier — the candidate who capitulates to the customer's bad scope loses.

**General FDE prep gets you past the resume screen. Sierra-specific prep gets you past the take-home demo + customer simulation.**
