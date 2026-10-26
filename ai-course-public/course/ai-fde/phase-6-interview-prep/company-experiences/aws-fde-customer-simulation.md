# AWS FDE — Customer Simulation + Well-Architected Framework (the 6-round loop)

> **Source:** Synthesized from the Medium "Forward Deployed Engineer Interview Has Six Rounds" article (`medium.com/@shivanathd/the-forward-deployed-engineer-interview-has-six-rounds-365df0544e2c`), the Sundeep Teki 2026 FDE definitive guide, and the FDE roadmap GitHub repo. **AWS FDE is the canonical "6-round" FDE loop — and the only major FDE loop where the customer simulation round is explicit in the round structure (not embedded in another round).** The Well-Architected Framework (security / reliability / cost / performance / operational excellence / sustainability) is the testable depth signal.

---

## 1. What was the loop?

The AWS FDE loop is **6 rounds over ~4 weeks**. It's the most structured of the major FDE loops: each round has a stated purpose, a stated signal, and a stated format. The signature round is the **customer scenario interview** (round 6), which is the highest-signal stage.

| Round | Length | What they tested | What they wanted |
|---|---|---|---|
| 1. Recruiter screen | 30 min | Why FDE, why AWS, travel willingness, comp realism, energy | "Bring a tight 60-second answer to 'why FDE' and a separate 60-second answer to 'why this company,' plus a real target comp number" |
| 2. Technical phone screen | 45-60 min | Talk fluently about past work, reason about systems out loud, defend everything on the resume | A weak answer signals you can't explain a technical decision to someone without an engineering background |
| 3. Take-home or work sample | 4-8 hr | Shipping something end-to-end without supervision; sensible tradeoffs under time pressure | "A well-documented 70% solution beats an undocumented 100% solution" |
| 4. Coding interview | 60 min | Practical coding, not algorithmic; handling ambiguity matters as much as whether the code runs | Restate the problem, ask clarifying questions, propose an approach, then code while narrating decisions. **Silence is a red flag.** |
| 5. Systems and architecture interview | 60 min | Decision-making under explicit constraints (budget, sensitive data, read/write ratio) | Defend the simplest design that meets constraints when pushed for more complexity |
| 6. **Customer scenario interview** | **60-90 min** | Staying calm with a frustrated client, pushing back without damaging the relationship, scoping live, knowing when to say no | **"This round filters the most candidates, and most engineers rarely prepare for it."** |

**The candidate's framing (per the Medium article):** "The Forward Deployed Engineer Interview Has Six Rounds. A field guide to the skills, the loop, and the portfolio project that gets you hired. The six rounds no one tells you about upfront."

**The AWS-specific signal:** the customer scenario interview (round 6) is **explicit and separate** — it's not embedded in a technical round (unlike Palantir) and it's not the only round (unlike LangChain's take-home). The candidate who treats it as "just another behavioral" will fail.

**The compensation (per the FDE definitive guide):** mid-level (3-5 yrs) $200K-$350K; senior (5+ yrs) $300K-$450K+; top-tier $600K+. AWS FDEs earn the standard 25-40% premium over traditional SWEs.

---

## 2. The customer scenario interview (the signature round)

**Length:** 60-90 min role play.

**The format:** the interviewer plays a **frustrated client** (typically a CIO, VP of Engineering, or head of compliance at an enterprise customer). You are the FDE in the room. The scenario typically:

- Starts with a vague or escalating problem ("our pilot is failing," "the bill is 3x what we expected," "compliance wants an audit trail we don't have")
- Includes a hostile or impatient stakeholder who wants a quick answer
- Requires you to scope live, push back without damaging the relationship, and know when to say no
- Tests for overpromising (the most common failure mode)

**The 3 typical scenarios (per the Medium article):**

1. **"A client demanding a chatbot in two weeks."** — Test of scoping + pushing back. The candidate must say "no" or "2-week MVP with limited scope" without losing the deal.
2. **"A hostile internal engineering team."** — Test of cross-functional empathy. The candidate must navigate the "I don't trust your cloud" objection.
3. **"Scope quietly expanding mid-project."** — Test of ownership + saying no. The candidate must hold the line.

**The 4 things they test:**

1. **Calm under pressure** — Do you escalate your own emotional state when the stakeholder escalates?
2. **No overpromising** — Do you agree to deadlines you can't hit? Do you promise cost numbers you can't deliver?
3. **Trade-off explanation** — Can you explain "we can ship 2 weeks faster if we accept a 3x cost increase, but here's the failure mode" in plain English?
4. **Knowing when to say no** — Do you have the conviction to walk away from a bad scope, or do you capitulate?

**The guide's actual advice:** "A client demanding a chatbot in two weeks" is the most common scenario. The candidate who says "yes, we can do that" loses; the candidate who says "we can do an MVP in 2 weeks with this limited scope, and a full build in 6 weeks" wins.

**The Phase 6 prep:** This is `../customer-simulation/README.md` (the discovery + scoping + pushback module, if present) + the behavioral module for the "no" pattern. The PacificFreight drafter's "we said no to Mei's refund tool" decision (Phase 4 cap-stone engagement) is the strongest signal you can bring.

---

## 3. The take-home / work sample (round 3)

**The time budget:** 4-8 hr (the candidate's time, asynchronous).

**The format:** build something end-to-end without supervision. The deliverable is a working artifact + a written case study focused on outcomes.

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

**The guide's actual advice:** "A well-documented 70% solution beats an undocumented 100% solution." Have a clean personal project template ready.

**The 3 sample prompts (per the FDE roadmap + devopsschool):**

1. **"A bank wants to use AI to summarize customer support tickets. How would you scope the first deployment?"** — The compliance-aware RAG pattern.
2. **"Design a RAG system for an enterprise knowledge base with strict permissions."** — The permissions-aware RAG pattern.
3. **"Build an agent workflow, define evals, harden."** — The end-to-end pattern.

**The Phase 6 prep:** This is `../take-home/01-prototype.md` + `../take-home/02-pipeline.md` (the take-home module) + the Phase 4 capstone's PacificFreight drafter as the reference implementation.

---

## 4. The technical phone screen (round 2)

**Length:** 45-60 min.

**The format:** a live conversation with a senior engineer or hiring manager. The candidate is expected to talk fluently about past work, reason about systems out loud, and defend everything on the resume.

**The 4 things they test:**

1. **Past-work fluency** — Can you describe a past project at the right level of detail for a non-engineering audience?
2. **System reasoning out loud** — Can you walk through how a system works while being interrupted with questions?
3. **Resume defense** — Can you defend every bullet on your resume with a specific metric, trade-off, and outcome?
4. **Translation to non-technical audience** — Can you explain a technical decision to someone without an engineering background?

**The guide's actual advice:** "A weak answer often signals you can't explain a technical decision to someone without an engineering background." This is the disqualifier round.

**The 3 sample questions:**

1. "Walk me through a past project where you had to make a hard trade-off. What did you decide, and why?"
2. "How would you explain a circuit breaker to a non-technical executive?"
3. "Tell me about a time you pushed back on a customer request."

**The Phase 6 prep:** This is the behavioral module (the STAR format) + the project-deep-dives module (the 45-min presentation). The candidate who can defend every Phase 1-5 project with a specific metric + trade-off + outcome is signaling the FDE signal.

---

## 5. The coding interview (round 4)

**Length:** 60 min.

**The format:** practical coding, not algorithmic. The prompt is contextualized in a customer scenario, not an abstract puzzle.

**The 4 things they test:**

1. **Handling ambiguity** — Can you restate the problem and ask clarifying questions?
2. **Practical coding** — Can you write working, tested code under time pressure?
3. **Trade-off reasoning** — Can you discuss time/space complexity and where you'd optimize?
4. **Communication** — Can you narrate your decisions while coding?

**The guide's actual advice:** "Restate the problem, ask clarifying questions, propose an approach, then code while narrating decisions. **Silence is a red flag.**"

**The 3 sample questions (per the FDE roadmap):**

1. **"Implement a service endpoint plus tests, then extend it."** — The standard pair-coding prompt.
2. **"Build an API that ingests documents and returns searchable chunks."** — The RAG-adjacent prompt.
3. **"Write a function to evaluate model responses against expected answers."** — The eval-set prompt.

**The Phase 6 prep:** This is `../practical-coding/README.md` (the 3 sub-rounds) + `../swe-coding/README.md` (the 8 patterns). **Note: AI tools are typically allowed at AWS for the coding round, but not for the customer scenario.**

---

## 6. The systems and architecture interview (round 5)

**Length:** 60 min.

**The format:** industry-standard system design with the AWS-specific lens — the **Well-Architected Framework** pillars (security / reliability / cost / performance / operational excellence / sustainability) are the testable depth signal.

**The 4 things they test:**

1. **Decision-making under explicit constraints** — Budget, sensitive data, read/write ratio are all in scope.
2. **Simplest design that meets constraints** — Defend simplicity when pushed for complexity.
3. **Trade-off reasoning** — Databases, scaling, reliability, cost.
4. **End-user orientation** — Design decisions map to real usage and client needs.

**The Well-Architected Framework pillars (the AWS-specific depth signal):**

1. **Security** — least-privilege IAM, encryption at rest + in transit, audit logging
2. **Reliability** — multi-AZ, multi-region, automated recovery, circuit breakers
3. **Cost** — right-sizing, reserved capacity, cost allocation tags, lifecycle policies
4. **Performance** — caching, partitioning, async processing, CDN
5. **Operational excellence** — IaC, CI/CD, observability, runbooks, incident response
6. **Sustainability** — right-sized workloads, efficient data transfer, sustainable regions

**The guide's actual advice:** "Defend the simplest design that meets constraints when pushed for more complexity." The candidate who over-engineers the system design (e.g., multi-region active/active when the customer is a single-region SMB) fails.

**The 3 sample questions (per the FDE roadmap + devopsschool):**

1. **"Architect the components, data flow, and APIs for a real-world operational challenge, then walk through the trade-offs."** — The standard system design prompt.
2. **"Design a pipeline that ingests terabytes of sensor data in mixed formats like JSON, CSV, and XML, then surfaces failure predictions to a non-technical end-user."** — The data-pipeline prompt.
3. **"Design a system that lets multiple teams query a shared dataset without exposing the underlying raw data."** — The multi-tenant prompt.

**The Phase 6 prep:** This is `../system-design/README.md` (the 9 patterns) + the Well-Architected Framework reading. The candidate who can name all 6 pillars + apply them to a customer scenario is signaling the AWS-specific depth.

---

## 7. The recruiter call (round 1)

**Length:** 30 min.

**The 4 things they test:**

1. **Why FDE, why AWS** — Treated as a formality by most candidates, which is the first mistake.
2. **Travel willingness** — AWS FDEs travel 25-50% ("like a startup CTO"). The candidate who can't commit is filtered out early.
3. **Comp realism** — The candidate should bring a real target comp number, not "I'm flexible."
4. **Energy** — FDE work is intense. The recruiter is looking for sustained energy, not enthusiasm.

**The guide's actual advice:** "Bring a tight 60-second answer to 'why FDE' and a separate 60-second answer to 'why this company,' plus a real target comp number."

**The 2 sample questions:**

1. "What are you looking for in your next role, and what do you want to work on?"
2. "Why AWS, and what specifically draws you to the mission?"

**The Phase 6 prep:** This is `../interview-process.md` (the FDE loop, day-in-the-life) + `../behavioral/README.md` (the 3 question types). The candidate who has a 60-second "why FDE" answer + a 60-second "why AWS" answer pre-prepared is signaling the FDE signal.

---

## 8. What's the Phase 6 module that preps each round?

| Round | Phase 6 module |
|---|---|
| 1. Recruiter screen | `../interview-process.md` (the FDE loop, day-in-the-life) + `../behavioral/README.md` (the 60-second answers) |
| 2. Technical phone screen | `../behavioral/README.md` (the STAR format) + `../project-deep-dives/README.md` (the 45-min presentation) |
| 3. Take-home / work sample | `../take-home/01-prototype.md` + `../take-home/02-pipeline.md` (the take-home module) |
| 4. Coding interview | `../practical-coding/README.md` + `../swe-coding/README.md` (the 8 patterns, with AI tools allowed) |
| 5. Systems and architecture | `../system-design/README.md` (the 9 patterns) + the Well-Architected Framework reading |
| 6. **Customer scenario** | `../customer-simulation/README.md` (the 3 scenarios + the "no" pattern) + the behavioral module |

**The candidate's pre-Phase-6 prep time would have been:** ~4-5 weeks full-time, weighted 30% on the customer scenario (round 6) + 20% on the take-home (round 3) + 20% on system design (round 5) + 15% on coding (round 4) + 15% on behavioral.

---

## 9. The 5-pattern cheat sheet for AWS FDE prep

Based on this guide + the Phase 1-5 portfolio:

1. **Master the customer scenario.** Practice staying calm with a frustrated executive, scoping live, pushing back without damaging the relationship, and knowing when to say no. **The guide's verdict: "This round filters the most candidates, and most engineers rarely prepare for it."**
2. **Read the Well-Architected Framework.** All 6 pillars are testable. The candidate who can apply them to a customer scenario is signaling the AWS-specific depth.
3. **Build a take-home with a real eval set.** The eval set is the differentiator. The candidate who ships a working agent with no eval set will fail.
4. **Prepare 60-second answers to "why FDE" and "why AWS."** Generic enthusiasm is a disqualifier. Name specific AWS services, specific operational challenges, and specific customer outcomes.
5. **Run mock customer scenarios.** Pair with a friend who plays the frustrated executive. The signal is calm under pressure, not technical depth.

---

## 10. The 5 most common AWS FDE follow-up questions (inferred from this guide)

| Question | The FDE answer |
|---|---|
| 1. "Why AWS FDE?" | "I've spent the last 6 months building a customer-facing AI service for PacificFreight, and the work that resonates most is the same work AWS FDEs do: build production apps inside customer systems, deliver technical artifacts, codify deployment patterns. The operational challenge I want to own is the multi-tenant data isolation + the eval-set-as-spec pattern at scale. AWS's Well-Architected Framework gives me a structured way to reason about the 6 pillars, and the customer-scenario focus of the loop matches the FDE work I want to do." |
| 2. "Design a RAG system for an enterprise knowledge base with strict permissions." | "4-step framework. Clarify: the user is a data analyst on a downstream team; the constraint is row-level access control + a query budget per team; the failure mode is a leak of PII; the timeline is MVP in 2 weeks. Decompose: the redaction layer, the embedding pipeline, the per-team ACL, the audit log, the per-team rate limit. Design: a redaction-first RAG pipeline (PII redaction before the embedding step), per-team IAM roles, append-only audit log, per-team token bucket. Tradeoffs: redact at the embedding step (we chose this for downstream safety, accepted the latency cost) vs redact at the output step (faster but riskier). Well-Architected: Security (least-privilege IAM), Reliability (multi-AZ), Cost (right-sized embeddings), Performance (caching for hot queries), Operational excellence (runbooks + dashboards), Sustainability (right-sized regions)." |
| 3. "A client demanding a chatbot in two weeks." | "I'd push back. The 2-week timeline is a recipe for failure: no eval set, no production-readiness artifacts, no rollback path. I'd propose: 2-week MVP with limited scope (FAQ-only, 20% of customer queries, with a 'talk to a human' handoff for the rest), 6-week full build with eval set + production artifacts. The trade-off: we ship a smaller, safer product in 2 weeks; the customer's success team sees value; the full build follows. If the client insists on 2-week full build, I'd say no. Better to lose the deal than ship a system that fails at week 11." |
| 4. "Walk me through a past project where you had to make a hard trade-off." | "Engagement 1 of my FDE portfolio: I had to choose between a smaller, faster LLM (Qwen2.5-1.5B) and a larger, more expensive one (GPT-4o-mini) for the PacificFreight drafter. I chose the SLM for cost ceiling scalability. The trade-off: 91% of GPT-4o-mini's quality at 0.5% of the cost. The metric: the eval set showed no regression on the customer's primary use case (CS email drafting). The lesson: cost ceiling scalability is a feature, not a bug. The customer can take the cost reduction to their CFO." |
| 5. "How would you handle a hostile internal engineering team?" | "I'd listen first. The 'I don't trust your cloud' objection is usually about a past failure — a security incident, a billing surprise, a vendor lock-in. I'd ask: 'Tell me about the last time a cloud provider let you down.' Then I'd map their specific concerns to the Well-Architected pillars: security (least-privilege IAM, encryption at rest + in transit), reliability (multi-AZ, automated recovery), cost (cost allocation tags, lifecycle policies). I'd offer a 4-week pilot with explicit exit criteria: if the pilot doesn't meet these 3 metrics, we walk away with no obligation. The trade-off: we accept a smaller initial scope in exchange for trust." |

**Memorize these 5.** They're the most common AWS FDE follow-ups based on this guide.

---

## 11. AWS-specific prep tips (the 5 from the guide)

1. **Master the customer scenario.** Practice staying calm with a frustrated executive, scoping live, pushing back without damaging the relationship, and knowing when to say no. **The guide's verdict: "This round filters the most candidates, and most engineers rarely prepare for it."**
2. **Read the Well-Architected Framework.** All 6 pillars are testable. The candidate who can apply them to a customer scenario is signaling the AWS-specific depth.
3. **Build a take-home with a real eval set.** The eval set is the differentiator. The candidate who ships a working agent with no eval set will fail.
4. **Prepare 60-second answers to "why FDE" and "why AWS."** Generic enthusiasm is a disqualifier. Name specific AWS services, specific operational challenges, and specific customer outcomes.
5. **Run mock customer scenarios.** Pair with a friend who plays the frustrated executive. The signal is calm under pressure, not technical depth.

---

## 12. How to use this report

1. **Read it once.** Internalize the 6 rounds + the customer scenario pattern + the Well-Architected Framework depth signal.
2. **Practice the customer scenario out loud.** Pair with a friend. The signal is calm under pressure, not technical depth.
3. **Read the Well-Architected Framework.** All 6 pillars are testable.
4. **Build a take-home with a real eval set.** The eval set is the spec.
5. **Prepare for the "Why AWS?" question.** Specifics (specific services, operational challenges, customer outcomes) are required.
6. **Bring a Phase 1-5 case study as your "real customer" example.** PacificFreight is the default. Connect the circuit breaker to the Reliability pillar.

---

## 13. AWS FDE compensation (FYI, for context)

- **Mid-level (3-5 yrs):** $200K-$350K
- **Senior (5+ yrs):** $300K-$450K+
- **Top-tier:** $600K+

Compensation combines base + equity + bonus. FDEs earn a 25-40% premium over traditional SWEs. (Source: Sundeep Teki 2026 FDE guide, per Levels.fyi.)

---

## 14. The thesis

AWS's FDE loop is the **only major 6-round FDE loop** with an explicit, separate customer scenario round. The 6 rounds test the same 7 signals: why FDE/why AWS, past-work fluency, end-to-end shipping, practical coding, system design with explicit constraints, customer scenario calm, and the Well-Architected depth. **The customer scenario is the differentiator** — most engineers never prepare for it, and it filters more candidates than any other round. The Well-Architected Framework is the AWS-specific depth signal — the candidate who can apply all 6 pillars to a customer scenario is signaling the AWS-specific competency.

**General FDE prep gets you past the resume screen. AWS-specific prep gets you past the customer scenario round.**
