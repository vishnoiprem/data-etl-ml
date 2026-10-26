# Your 90-Day Roadmap: Principal Forward Deployed Engineer at OpenAI

**October 21, 2026 – January 19, 2027**

> **A 90-day execution plan, not a curriculum.** The curriculum already
> exists in this folder. This document tells you *which* phase to run on
> *which* day, for *which* deliverable, and what "done" means.

Targeting **Senior / Principal FDE** roles at leading AI companies —
OpenAI first. OpenAI's careers listings include a Forward Deployed
Engineer position in **Singapore**, which makes it a directly relevant
target.

---

## What you already have (and don't rebuild)

Three strengths are already in place. The 90 days are spent
*converting* them into FDE-legible evidence, not re-learning them:

| Strength you have | Where it's already evidenced | What the 90 days add |
|---|---|---|
| Enterprise architecture | `data-engineering/` (18 projects), `Portfolio-Head-of-AI/` | Frame it in FDE vocabulary: requirements → architecture → ROI |
| Production data engineering | Same repos, live pipelines | Show it wired to an LLM system, not adjacent to one |
| Technical leadership | `Portfolio-Head-of-AI/` (6 chapters, 20 docs) | Make it *customer-facing* — the FDE gap, not the engineering gap |

**The gap is not knowledge. It's translation.** The engineering is
already there; what it needs is a customer problem on the front of it.

---

## The four development priorities

These drive the whole schedule:

1. **Hands-on AI engineering** — production-grade agents, RAG,
   enterprise integrations.
2. **Python and SQL interviews** — problem interpretation, coding
   confidence, solving under pressure.
3. **AI system design** — architecture, scalability, security,
   reliability, tradeoffs, explained independently.
4. **Customer-facing engineering** — turning ambiguous business
   problems into deployed AI solutions.

Priority 4 is the one that costs the most and matters most for FDE
specifically. It's also the one that can't be scheduled by putting in
hours. It gets scheduled by *rehearsing* it.

---

## Month 1: Build your technical foundation

**October 21 – November 20**

Focus: Python, SQL, LLM fundamentals, RAG.

### Daily schedule (2 hours)

| Time | Activity | Why this slot |
|---|---|---|
| 30 min | Python + SQL interview practice | Needs to be first — it's the highest-friction task when tired |
| 30 min | LLM APIs, tool calling, structured outputs, embeddings | Conceptual load; better before the build block |
| 45 min | Build the RAG application | The long block; needs the most context |
| 15 min | Explain your architecture aloud | The most-skipped slot, and the highest-leverage |

### Project 1 — Enterprise Document Intelligence

Build a RAG application with document ingestion, hybrid retrieval,
reranking, citations, and evaluation.

**Stack:** Python, FastAPI, PostgreSQL + pgvector, an LLM API.

**Deliverable:** a working application with automated tests,
measurable retrieval quality, and a clear architecture diagram.

### Month 1 maps onto existing course artifacts

You do not build this from scratch. Run the existing phases:

| Week | Days | Run this | Produces |
|---|---|---|---|
| 1 | Oct 21–27 | [`phase-1-foundations/`](./phase-1-foundations/) | CLI tool + 1-pager + 5-question discovery framework |
| 2 | Oct 28–Nov 3 | [`phase-2-core-build/`](./phase-2-core-build/) | FastAPI service + RAG + eval (13/13 tests) |
| 3 | Nov 4–10 | [`phase-2-core-build/`](./phase-2-core-build/) continued | Eval set, policy chunks, diagrams |
| 4 | Nov 11–20 | `phase-2` hybrid retrieval + Phase 1 Python/SQL practice | Measurable retrieval quality + architecture diagram |

**What you add that the course doesn't have:**

- **Python/SQL interview reps** — the course teaches building; the
  interviews test *problem interpretation*. Practice separately.
- **The architecture diagram as a customer artifact** — not an
  internal diagram. The audience is a stakeholder who decides budget.
- **Citations as a first-class feature** — Phase 2 covers retrieval;
  verify citation accuracy is explicitly measured.

---

## Month 2: Become an AI agent engineer

**November 21 – December 20**

Focus: agentic AI, MCP, orchestration, production reliability.

### Project 2 — Enterprise Operations AI Agent

An agent that can:

- Query business databases through controlled tools.
- Retrieve company policies and documentation.
- Call APIs to complete approved actions.
- Request human approval for sensitive operations.
- Record traces, tool calls, errors, and costs.

Concrete scenario: **investigate a delayed order → check inventory →
retrieve relevant policies → recommend the next action.**

**Stack:** Python, FastAPI, an agent orchestration framework where
useful, MCP-compatible integrations.

**Add:** authentication, authorization, timeouts, retries,
evaluation tests, human approval.

**Deliverable:** a working end-to-end agent with a demonstration and
measurable reliability.

### Month 2 maps onto existing course artifacts

This is the richest month for reuse — the capstone projects already
*are* the agent patterns:

| Week | Days | Run this | Produces |
|---|---|---|---|
| 5 | Nov 21–27 | [`phase-3-deployment/`](./phase-3-deployment/) | Hardened service: circuit breaker, rate limiter, redactor, telemetry |
| 6 | Nov 28–Dec 4 | [`phase-4-capstone/projects/01-mcp-drafter/`](./phase-4-capstone/projects/01-mcp-drafter/) | MCP server + client |
| 7 | Dec 5–11 | [`phase-4-capstone/projects/02-multi-agent-dispatcher/`](./phase-4-capstone/projects/02-multi-agent-dispatcher/) | Multi-agent with verifier |
| 8 | Dec 12–20 | `02-multi-agent-dispatcher` + auth/human-approval layer | End-to-end ops agent with approval gates |

**Reference material (skim, don't run end-to-end):**

- [`phase-5-advanced/projects/02-oauth-multi-tenant/`](./phase-5-advanced/projects/02-oauth-multi-tenant/) — the JWT/tenant pattern that Project 2 needs.
- [`phase-5-advanced/case-studies/engagement-8-cost-ceiling-breach.md`](./phase-5-advanced/case-studies/engagement-8-cost-ceiling-breach.md) — the postmortem that becomes a behavioral STAR story for Phase 6.

**What you add that the course doesn't have:**

- **A real customer-shaped scenario.** The course uses PacificFreight
  Co. Change the scenario to *delayed order + inventory + policy* so
  the agent does multi-tool work, not single-tool drafting.
- **Authentication and authorization.** The capstone assumes a trusted
  operator. FDE customers do not. Add authn/authz and show the
  difference.
- **Cost recording per trace.** `agentic-ai/16-autonomous-loop/` has
  the budget-gate pattern — port the idea into the agent's trace.

---

## Month 3: Prepare specifically for FDE interviews

**December 21 – January 19**

Focus: customer-facing architecture, live coding, deployment.

### Project 3 — Production AI Customer Deployment

Take **one** of the previous projects and package it as a
customer-ready AI solution.

**Include:**

- A live demo.
- Deployment instructions.
- A monitoring dashboard.
- An evaluation report.
- A five-minute business presentation.

### Scenarios to practice (all four, end to end)

Each scenario gets practiced across all six dimensions, not just
architecture:

| Scenario | What it tests |
|---|---|
| A bank wants to automate customer support using AI | Regulated-industry constraints, audit trail, risk tiering |
| A retailer wants an AI agent for inventory operations | Multi-system integration, operational reliability |
| A company wants to deploy secure RAG across millions of documents | Scale, security, cost model, index strategy |
| An enterprise wants to integrate AI agents with legacy systems | Integration debt, change management, realistic timelines |

For each: **requirements gathering → architecture → coding →
deployment → security → ROI.**

### Month 3 maps onto existing course artifacts

| Week | Days | Run this | Produces |
|---|---|---|---|
| 9 | Dec 21–27 | [`phase-6-interview-prep/`](./phase-6-interview-prep/) decomposition + system-design modules | The 4-step framework (Clarify / Decompose / Design / Tradeoffs) drilled on all 4 scenarios |
| 10 | Dec 28–Jan 3 | [`phase-6-interview-prep/behavioral/`](./phase-6-interview-prep/behavioral/) + [`customer-simulation/`](./phase-6-interview-prep/customer-simulation/) | 3 STAR stories drawn from your own case studies + the slipped-deployment simulation |
| 11 | Jan 4–10 | [`phase-7-FDE-100-interview/00-INDEX.md`](./phase-7-FDE-100-interview/00-INDEX.md) → [`03-openai-fde.md`](./phase-7-FDE-100-interview/03-openai-fde.md) + 2 more targets | Company-specific process, success/rejection stories, reading list |
| 12 | Jan 11–19 | [`phase-4-capstone/case-studies/REHEARSAL-CHECKLIST.md`](./phase-4-capstone/case-studies/REHEARSAL-CHECKLIST.md) + 5 mock interviews | Recorded mock FDE interviews, rehearsed against the phase-7 scripts |

### Month 3 is where phase-7 earns its keep

[`phase-7-FDE-100-interview/`](./phase-7-FDE-100-interview/)
holds 100 company-specific FDE interview files. Each one carries a
company snapshot, the actual interview process, success *and*
rejection stories with reasoning, and a reading list.

**How to use it in the final two weeks:**

1. **Pick 3–5 target companies** from the tier map in
   [`00-INDEX.md`](./phase-7-FDE-100-interview/00-INDEX.md). For an
   OpenAI-primary plan: OpenAI, Anthropic, Palantir, Scale AI, and
   one big-tech PS shop (AWS ProServe or Google CE).
2. **Read each file end-to-end** — snapshot → process → success →
   rejection → reading list.
3. **For every success-story Q, practice answering out loud** for
   60–90 seconds. Then compare against the recorded mock.
4. **For every rejection story, write the better answer in your own
   words**, then say it. The rejection files are the highest-value
   part of the directory — they show the near-misses.
5. **Drill the reading-list items in the final week** before each loop.

**Why this matters:** the success stories are answers that *worked*
at a specific company. Copying them verbatim reads as rehearsed;
re-deriving the reasoning from your own artifacts reads as senior.
The rejection files are where that distinction is most visible.

### The 5 system design exercises

Practice these as written exercises, each answered in 45 minutes:

1. Design a customer-support RAG for a regulated bank.
2. Design an agent that takes approved actions in an ERP.
3. Design a multi-tenant AI platform with per-tenant cost isolation.
4. Design the migration path from a vendor API to self-hosted serving.
5. Design an eval system for a system where labels cost $50/hour.

Exercise 5 is the hardest and the most valuable. It is also the one
that separates an FDE from a backend engineer.

All five map to the 9 patterns in
[`phase-6-interview-prep/system-design/`](./phase-6-interview-prep/system-design/)
— exercises 1 and 3 to `01-read-heavy` + `04-distributed-storage`,
exercise 2 to `09-agentic-ai`, exercise 4 to `05-transactional`.

### The 5 mock interviews

| # | Focus | Format | Drill against |
|---|---|---|---|
| 1 | Coding under pressure (Python) | 45 min, no AI assistant | `phase-7-FDE-100-interview/03-openai-fde.md` Round 2 story → practice as `phase-6-interview-prep/swe-coding/` pattern 1 |
| 2 | System design (scenario 1) | 60 min, whiteboarding | `phase-7-FDE-100-interview/03-openai-fde.md` Round 3 story → practice as `phase-6-interview-prep/system-design/01-read-heavy.md` |
| 3 | Customer discovery → architecture (ambiguous brief) | 60 min, role-play | `phase-7-FDE-100-interview/01-palantir-fdse.md` + `phase-6-interview-prep/customer-simulation/README.md` |
| 4 | Debugging a production incident you didn't build | 45 min | Cross-reference failure stories from any `phase-7-FDE-100-interview/*.md` rejection section |
| 5 | Business case + ROI (Project 3 presentation) | 30 min | `phase-5-advanced/case-studies/engagement-8-cost-ceiling-breach.md` + `phase-6-interview-prep/project-deep-dives/pacificfreight-deep-dive.md` |

**Record every one.** The recording is the artifact; the interview
is just the input. The row shows both source material (phase-7) and
the framework it gets drilled against (phase-6), so each interview
practice uses a real Q paired with the four-step Clarify/Decompose/
Design/Tradeoffs framework.

---

## Weekend cadence (2–3 hours)

| Activity | Hours | When |
|---|---|---|
| Project polish | 1.5 | Saturday |
| Mock interview (recorded) | 1.0 | Saturday |
| Week review + next-week plan | 0.5 | Sunday |

The Sunday review is 30 minutes and it is what makes the other 60
days of the plan work. Without it, Month 3 quietly doesn't happen.

---

## What OpenAI's FDE roles actually ask for

From their published job descriptions, the emphasis is consistent
across roles:

| Requirement | Where the 90 days evidence it |
|---|---|
| Production-grade Python or JavaScript | Project 1 + Project 2, running, tested |
| End-to-end AI deployments | Project 3, deployed with instructions |
| Customer-facing technical ownership | 5 mock interviews + scenario rehearsals |
| Model evaluations | Eval reports from all three projects |
| Measurable business impact | ROI exercise + 5-min presentation |

**Note on job postings:** FDE requirements shift between postings
and between quarters. Verify against the live listing before each
application round. The four rows above have been stable across
postings; specific tool requirements have not.

---

## Targets by January 19, 2027

| Target | Where it's produced |
|---|---|
| Two working AI applications with documented architecture and tests | Projects 1, 2 |
| One customer-ready deployment demonstration | Project 3 |
| ≥50 Python and SQL problems completed independently | Daily 30-min block, Months 1–2 |
| 10 AI system design exercises | Months 2–3 (5 detailed here + 5 self-generated) |
| 5 mock FDE interviews | Month 3, all recorded |
| Updated CV emphasizing production AI, enterprise architecture, customer outcomes | Final week |

These are **preparation targets, not guarantees of interview
readiness or employment.** They make you credible in the room.
They don't decide the room.

---

## The one discipline that matters most

Your Meta interview taught the lesson that generalizes to every FDE
interview: **the gap is problem interpretation under pressure, not
technical knowledge.**

Apply this sequence to every coding exercise:

```
Clarify the problem  →  Explain your approach  →  Write the code  →  Test edge cases
```

**Do not let an AI coding assistant solve interview exercises before
you have attempted them independently.** Not as a fallback. Not as a
check. First. The entire point of the exercise is the four-step
sequence, and a correct answer produced without the sequence teaches
you nothing that the interview tests.

The same sequence applies to system design, where it maps to:

```
Clarify the business problem  →  Explain the architecture  →  Draw it  →  Attack it with failure cases
```

---

## Start today

Two things, in this order:

1. **One Python problem**, done without an assistant, using the
   four-step sequence out loud.
2. **The architecture for Project 1** — one page, ASCII diagram,
   naming the retrieval strategy, the eval metric, and the cost
   ceiling.

That is the day. Everything after it is repetition of the same two
moves.

---

## How this plan relates to the rest of the course

```
   90-day plan          Course phases           Portfolio
   (this file)          (7 phases)              (the evidence)

   Month 1        ───▶  phase-1, phase-2   ───▶  Project 1 artifact
   Month 2        ───▶  phase-3, 01, 02    ───▶  Project 2 artifact
                                  (+ phase-5 patterns)
   Month 3        ───▶  phase-4 (03), cases ──▶  Project 3 artifact
                       phase-6 (interview)       +
                       phase-7 (100 companies)  Portfolio-Head-of-AI/
                                                   (the judgment docs)
```

The course teaches seven phases. This plan schedules the load-bearing
ones against a deadline and adds the two things the course
deliberately doesn't teach: **timed interview reps** and
**customer-facing rehearsal**.

Phases 5 (advanced scale) and 7 (the 100-company bank) are treated
here as *reference material* rather than sequential work — phase 5's
Redis/OAuth/sandbox/DR patterns inform Project 2's production-readiness,
and phase 7's company files are the drilling material for Month 3.

---

**Length:** 90 days, ~2 hours/day + 2–3 hours/weekend (~270 hours)
**Cost:** $0 — everything runs with the mock LLM backend; no API key needed
**Goal:** By January 19, you can demonstrate you build AI systems, operate them reliably, and explain their business value.
**Last updated:** 2026-10-21
**License:** MIT