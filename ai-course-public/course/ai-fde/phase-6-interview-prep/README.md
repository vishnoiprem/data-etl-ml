# Phase 6 — FDE Interview Prep (the FDE is now the candidate)

> **Phases 1-5 made you an FDE. Phase 6 makes you a credible FDE candidate.** The 5-question test, the 35/35 pytest, and the runbook are the artifacts that get you past the resume screen. The interview prep is what gets you past the loop. This phase turns the Phase 1-5 portfolio into the answers to the 8 FDE interview rounds.

---

## Why Phase 6 exists

A senior FDE portfolio (PacificFreight drafter, MCP tools, multi-agent, SLM, multi-region DR, 5 PE-grade case studies) is the **proof** that you can do the work. The interview loop is the **performance** of doing the work. The two are different skills:

| What Phase 1-5 gave you | What the interview tests |
|---|---|
| A working service | Can you decompose a fuzzy problem into a system design? |
| 35/35 tests pass | Can you debug a codebase you didn't write, in 30 minutes, with an AI assistant? |
| A runbook + RACI | Can you answer "tell me about a time you disagreed with a customer"? |
| A 24-page case study | Can you deliver a 45-minute deep dive on your best project? |
| A multi-region DR plan | Can you whiteboard a read-heavy + write-heavy + async-job system under pressure? |
| A $4.09/mo cost ceiling | Can you explain why you chose Redis over Postgres for rate limiting? |

**Phase 6 is the bridge.** Every module in Phase 6 maps to a Phase 1-5 artifact and reframes it as an interview answer.

---

## The 11 modules (file layout)

The 8 rounds + 3 cross-cutting modules = 11 total.

| # | Round | What they test | Phase 6 module | Phase 1-5 artifact that backs it up |
|---|---|---|---|---|
| 1 | **FDE introduction** | "What is an FDE? How does the role differ across companies?" | `interview-process.md` | The 1-page Phase 1 README |
| 2 | **Decomposition questions** (Palantir-style) | "Design a system for X" — open-ended, no right answer | `decomposition/` | Phase 4 P2 (multi-agent) + Phase 5 P4 (multi-region) |
| 3 | **Practical coding interviews** | "Here's a codebase. Add a feature. Debug this." | `practical-coding/` | The 35/35 tests + the 4 Phase 5 projects |
| 4 | **Behavioral questions for FDEs** | "Tell me about a time you handled a difficult customer" | `behavioral/` | The 10 case studies (engagements 1-10) |
| 5 | **Project deep dive** | 45-minute presentation of your best project | `project-deep-dives/` | The PacificFreight drafter (Phase 2→5) |
| 6 | **Take-home assignment** | 4-8 hour build + 1-hour presentation | `take-home/` | The Phase 4 P1 MCP server (the pattern) |
| 7 | **System design** | "Design a read-heavy system / event-driven / async / etc." | `system-design/` | The Phase 4 + Phase 5 architecture docs |
| 8 | **Generative AI interviews** | "How do LLMs work in production? Where do they fail?" | `generative-ai/` | The Phase 4 P3 SLM + the Phase 4 P4 sandbox |
| 9 | **SWE coding** (classic LeetCode) | "Reverse a linked list / group anagrams / etc." | `swe-coding/` | The 8 SWE patterns + the 4 anti-patterns |
| 10 | **Customer simulation** (highest-signal) | "Your deployment slipped 3 weeks. I am the customer. Tell me." | `customer-simulation/` | Engagement 8 (cost ceiling breach) + Engagement 2 (the pivot) |
| 11 | **Real interview experiences** | "What did the loop actually look like at OpenAI / Palantir / AWS?" | `company-experiences/` | 12 real reports + the 13 signature round → company matrix |

**The 11 modules map to 11 interview round types.** The 8 rounds are the standard; the 3 cross-cutting modules (9, 10, 11) are the modules that compound across all 8.

---

## The 9 modules (file layout)

```
phase-6-interview-prep/
├── README.md                                    ← you are here
├── interview-process.md                         ← Module 1: the FDE loop, day-in-the-life
├── decomposition/                               ← Module 2: Palantir-style open-ended
│   ├── README.md                                ← the 4-step decomposition framework
│   ├── 01-clarify.md                           ← ask 5 questions before drawing
│   ├── 02-decompose.md                         ← break into entities, services, flows
│   ├── 03-design.md                             ← API contracts, data model, scale
│   └── 04-tradeoffs.md                         ← 3+ tradeoffs, not 1
├── behavioral/                                  ← Module 4: customer-facing questions
│   ├── README.md                                ← the 3 question types + STAR format
│   ├── 01-customer-interaction.md              ← "tell me about a difficult customer"
│   ├── 02-disagreement.md                      ← "tell me about a time you disagreed"
│   ├── 03-ambiguity.md                         ← "tell me about a time the spec was unclear"
│   └── 04-no-experience.md                     ← answering without customer-facing title
├── project-deep-dives/                          ← Module 5: 45-min presentation
│   ├── README.md                                ← how to pick + structure
│   └── pacificfreight-deep-dive.md             ← the canonical 45-min script
├── take-home/                                   ← Module 6: 4-8 hour build
│   ├── README.md                                ← the 3 take-home patterns
│   ├── 01-prototype.md                          ← OpenAI-style semantic search
│   ├── 02-pipeline.md                           ← Labelbox-style RLHF pipeline
│   └── 03-presentation.md                       ← how to present the take-home
├── system-design/                               ← Module 7: the 9 patterns
│   ├── README.md                                ← the 4-step system design framework
│   ├── 01-read-heavy.md                         ← Phase 5 P4 read replica
│   ├── 02-event-driven.md                       ← Phase 4 webhook + Phase 5 Redis pub/sub
│   ├── 03-async-jobs.md                         ← Phase 4 P2 multi-agent
│   ├── 04-distributed-storage.md                ← Phase 5 P1 Redis sharding
│   ├── 05-transactional.md                      ← Phase 4 circuit breaker
│   ├── 06-batch-processing.md                   ← Phase 4 P3 SLM eval
│   ├── 07-real-time-collaborative.md            ← Phase 5 P4 multi-region DR
│   ├── 08-media-streaming.md                   ← outside the FDE scope, but tested
│   └── 09-agentic-ai.md                         ← Phase 4 P1 MCP + P2 multi-agent
├── practical-coding/                            ← Module 3: AI-assisted coding rounds
│   ├── README.md                                ← the new round format
│   ├── 01-build-new-project.md                  ← greenfield AI-assisted build
│   ├── 02-extend-codebase.md                    ← add a feature to a new codebase
│   └── 03-debug.md                              ← find the bug in 30 min
├── customer-simulation/                         ← Module 10: the highest-signal round
│   └── README.md                                ← 5 scenarios, 12 Q&A, 5 anti-patterns
├── company-experiences/                         ← Module 11: real interview reports
│   ├── README.md                                ← 12 reports + signature round matrix
│   ├── openai-semantic-search.md
│   ├── palantir-fde-decomposition.md
│   ├── langchain-deployed-engineer.md
│   ├── anthropic-fde-customer-simulation.md
│   ├── aws-fde-customer-simulation.md
│   ├── sierra-ai-agent-engineer.md
│   ├── databricks-ai-fde.md
│   ├── scale-ai-fde.md
│   ├── meta-fde-ai-engineer.md
│   ├── google-ai-engineer.md
│   ├── microsoft-ai-engineer.md
│   ├── stripe-fde-payments.md
│   └── huggingface-fde-open-source.md
├── swe-coding/                                  ← Module 9: classic SWE prep
│   ├── README.md                                ← the 8 patterns
│   ├── 01-arrays.md
│   ├── 02-hash-tables.md
│   ├── 03-strings.md
│   ├── 04-trees-graphs.md
│   ├── 05-dynamic-programming.md
│   └── 06-recursion-backtracking.md
└── generative-ai/                               ← Module 8: GenAI-specific
    ├── README.md                                ← what AI companies test
    ├── 01-llm-fundamentals.md                   ← transformer, attention, decoding
    ├── 02-rag-patterns.md                       ← Phase 2 RAG + Phase 4 P3 SLM
    ├── 03-production-deployment.md              ← Phase 5 P1-4
    ├── 04-eval-and-safety.md                    ← Phase 4 eval set + Phase 5 P3 sandbox
    └── companion-courses/                       ← Phase 6 GenAI depth courses
        ├── README.md
        ├── ed-donner-ai-engineer-core-track.md
        └── intro-to-ai-agents.md
```

---

## The 4-step framework that ties every module together

Every FDE interview round — decomposition, system design, project deep dive, take-home, behavioral, GenAI — can be answered with the same 4-step framework:

### Step 1: Clarify (2-3 minutes)

- Ask 5 questions before drawing anything.
- What's the user? What's the scale? What's the constraint? What's the failure mode? What's the timeline?
- **The FDE signal:** the candidate who asks 5 questions before opening the whiteboard is showing they understand the customer, not just the system.

### Step 2: Decompose (5-7 minutes)

- List 3-5 entities (User, Content, Metadata, Event, Metric).
- List 3-5 services (one per entity, roughly).
- List 3-5 flows (User creates Content, Content triggers Event, Event updates Metric).
- **The FDE signal:** the candidate who can list entities + services + flows without naming a technology is showing they can think before they build.

### Step 3: Design (10-15 minutes)

- API contracts (3-5 endpoints, with request/response shape).
- Data model (3-5 tables/collections, with keys + indexes).
- Scale model (QPS, storage, bandwidth, cost).
- **The FDE signal:** the candidate who names the QPS AND the cost ceiling is showing they understand the operational boundary.

### Step 4: Tradeoffs (3-5 minutes)

- 3+ tradeoffs, not 1. ("We could use Postgres, but the read QPS would require sharding at 10× growth; Redis is simpler for the rate-limit case.")
- **The FDE signal:** the candidate who names a tradeoff, then defends the choice they made, is showing they understand the customer-facing consequence of the technical decision.

**This framework appears in every Phase 6 module.** It's the thread that ties the 8 rounds together.

---

## The 3 question types (for behavioral)

Every FDE behavioral question falls into one of 3 buckets:

1. **Customer interaction** — "Tell me about a time you handled a difficult customer." (Engagement 8: the cost ceiling breach — Sarah wanted to keep the bill under $5/mo; Daniel wanted to disable the SLM. I ran the 3-week fix and gave Sarah the YAML she could defend in front of her CFO.)
2. **Disagreement with a stakeholder** — "Tell me about a time you disagreed with your manager / the customer." (Engagement 2: the pivot — I told the legal-tech customer their data wasn't RAG-ready, and walked away. Better to lose 2 weeks than ship a system that fails at week 11.)
3. **Ambiguity / no spec** — "Tell me about a time the spec was unclear." (Engagement 1: PacificFreight's drafter had no eval set in week 1; I built the 30-row eval set before writing the prompt. The eval set is the spec.)

**Every behavioral answer uses the STAR format (Situation / Task / Action / Result) AND names a Phase 1-5 artifact.** "I built the eval set, which became the contract between prompt engineer and customer."

---

## How to use this phase

1. **Pick a target company first.** Palantir, Anthropic, OpenAI, AWS, Rippling, LangChain all have different FDE loops. The README in each module calls out company-specific patterns.
2. **Run the 4-step framework on every practice question.** The framework is the muscle memory; the artifacts are the examples.
3. **Use the Phase 1-5 case studies as your behavioral answers.** Engagement 8 = cost-ceiling story; engagement 7 = reliability story; engagement 2 = the pivot; engagement 5 = the handoff.
4. **Rehearse the 45-minute project deep dive.** It's the highest-leverage round. The script is in `project-deep-dives/pacificfreight-deep-dive.md`.
5. **Mock-interview with an AI assistant.** The "Practical Coding" module includes a meta-section on using Cursor / Claude / Copilot during the round. Yes, the AI-assisted round is now standard.

---

## The thesis

Phase 1-5 made you a builder. Phase 6 makes you a candidate. The 4-step framework (Clarify / Decompose / Design / Tradeoffs) is the muscle memory. The 10 case studies are the answers. The 35/35 tests are the proof. The runbook is the artifact you leave behind.

**You don't interview for an FDE role. You interview the role. The right company lets you do the work Phase 1-5 trained you for: ship a system, hand it off, and train the next 3 FDEs.**

---

**Last updated:** 2026-10-09
**Length:** ~3 weeks full-time prep (assuming Phase 1-5 portfolio is complete)
**Cost:** $0 (reuses the Phase 1-5 portfolio)
**Goal:** You can put "FDE @ Anthropic / OpenAI / Palantir" on your LinkedIn.
