# Module 1 — The FDE Interview Process

> **The FDE loop is 5-8 rounds over 4-6 weeks.** The order matters: resume screen → recruiter call → technical phone screen → 4-6 on-site rounds → references → offer. Each company tweaks the order, but the substance is the same: prove you can ship, prove you can talk to a customer, prove you can survive the room.

---

## 1. The 5-8 rounds (the canonical loop)

| # | Round | Length | What they test | What they want to see |
|---|---|---|---|---|
| 1 | Resume screen | 5 min | Background, signal | A working AI service you shipped, with metrics |
| 2 | Recruiter call | 30 min | Motivation, comp | A clear "why FDE, why this company" |
| 3 | Technical phone screen | 60 min | Coding + system design | Clean code, clear thinking, customer-aware tradeoffs |
| 4 | Decomposition question | 60 min | Open-ended system design | The 4-step framework (Clarify / Decompose / Design / Tradeoffs) |
| 5 | Practical coding round | 90 min | AI-assisted build / extend / debug | How you work with an AI assistant in production |
| 6 | Behavioral | 45 min | Customer interaction | STAR-format stories from real engagements |
| 7 | Project deep dive | 45 min | Your best project, end-to-end | The 1 project you can talk about for 45 minutes |
| 8 | Take-home + presentation | 4-8 hr + 60 min | Build + present | The "FDE in miniature" — build, ship, defend |

**Some companies combine rounds.** Anthropic and OpenAI often run a 4-round loop (decomposition + coding + behavioral + system design). Palantir runs the full 8. AWS FDE runs 5-6. Rippling runs 4-5.

---

## 2. Company-specific loops

| Company | FDE loop | Distinguishing round | Phase 6 prep focus |
|---|---|---|---|
| **Palantir** | 8 rounds, 4-6 weeks | Decomposition (60 min) + Foundry coding | `decomposition/` (the canonical round) |
| **Anthropic** | 4-5 rounds, 3 weeks | GenAI depth + project deep dive | `generative-ai/` + `project-deep-dives/` |
| **OpenAI** | 4-5 rounds, 3 weeks | Take-home (semantic search) + GenAI | `take-home/01-prototype.md` |
| **AWS FDE** | 5-6 rounds, 4 weeks | AWS-architecture + customer simulation | `system-design/01-read-heavy.md` + `behavioral/01-customer-interaction.md` |
| **Rippling** | 4-5 rounds, 2-3 weeks | Practical coding + behavioral | `practical-coding/` + `behavioral/` |
| **LangChain** | 4-5 rounds, 2 weeks | Agentic AI + GenAI | `system-design/09-agentic-ai.md` |
| **Kepler / Contour** (startups) | 3-4 rounds, 1-2 weeks | Founder interview + take-home | `take-home/` + `project-deep-dives/` |

**The signal:** the company that hires you tells you which round to focus on. If you can't decode the signal, ask the recruiter. "Which round is the highest-leverage for your team?" is a perfectly acceptable question.

---

## 3. The day-in-the-life (so you can answer "why FDE?")

| Time | Activity | % of week |
|---|---|---|
| 09:00 | Iteration review with the customer (PacificFreight's Monday cadence) | 10% |
| 10:00 | Implementation (writing code, debugging, deploying) | 40% |
| 13:00 | Customer calls (design review, sprint demo, incident review) | 20% |
| 15:00 | Code review + on-call handoff | 10% |
| 16:00 | Self-directed work (eval set tuning, runbook updates, case study) | 20% |

**The 80/20 of the FDE role:** 80% of your time is split between implementation and customer interaction. The other 20% is everything else (code review, on-call, self-directed work). **If you don't like one of those two, you won't like the FDE role.**

---

## 4. The 5 questions every FDE interview asks (in some form)

1. **"Tell me about a time you shipped a system that you didn't write alone."** → Engagement 1: the PacificFreight drafter; Mei owns the prompts, Daniel owns the VM, you own the glue.
2. **"Tell me about a time you disagreed with the customer."** → Engagement 2: the pivot; you walked away from a legal-tech engagement because the data wasn't RAG-ready.
3. **"Tell me about a time the spec was unclear."** → Engagement 1: the eval set as spec; you built the 30-row eval set before the prompt.
4. **"Tell me about a time something broke in production."** → Engagement 3 or 7: the postmortem; you wrote a public postmortem in 24 hours.
5. **"Tell me about a time you made yourself unnecessary."** → Engagement 5 or 10: the handoff; you trained 3 next FDEs, the system ran.

**These are the 5 Phase 1-5 case studies.** Every behavioral answer maps to one of them.

---

## 5. The 3 red flags (that get you rejected)

1. **"I built a system that does X"** with no mention of the customer, the eval set, the cost ceiling, or the handoff. **FDEs don't ship systems; they ship systems that survive the customer.**
2. **"I disagree with the customer"** with no resolution. **The FDE is in the room to find the resolution, not to be right.**
3. **"I worked on a project that uses LLMs"** with no production deployment, no eval set, no cost model. **Anyone can call an LLM. FDEs ship LLMs.**

**The fix for all 3:** name the artifact (eval set, runbook, cost model, case study) and the metric (35/35 tests, $4.09/mo, 10-question test).

---

## 6. The 3 green flags (that get you an offer)

1. **"I built the eval set first, then the prompt."** Shows you understand the spec comes before the implementation.
2. **"I have a runbook + a RACI + an on-call rotation."** Shows you understand the operational boundary.
3. **"I have 3 next FDEs who can answer the 10-question test."** Shows you understand the principal-level FDE.

**The green flags are the Phase 5 deliverables.** The portfolio is the answer.

---

## 7. How to use this module

1. **Read this file once.** It's the canonical loop. The 8 modules in this phase prep each round.
2. **Pick your target company.** The table in §2 tells you which module to focus on.
3. **Rehearse the 5 questions in §4.** They're the 5 case studies; you already have the answers.
4. **Avoid the 3 red flags in §5.** They're easy to slip into; rehearse with an AI assistant.
5. **Hit the 3 green flags in §6.** They're the Phase 1-5 portfolio; you already have the proof.

---

## 8. The signal-to-noise test

When you finish a practice answer, ask yourself: **"Could a senior FDE at the target company tell I built a system, talked to a customer, and made myself unnecessary?"** If yes, ship the answer. If no, add a Phase 1-5 artifact.

**The portfolio is the resume. The interview is the performance. Phase 6 is the rehearsal.**
