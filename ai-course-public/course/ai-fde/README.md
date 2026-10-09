# AI FDE — the full course

> **A 9-week course that teaches you to be an AI Forward-Deployed Engineer.** You build 4 things, write 5 case studies, and demo a capstone system live.

An **AI FDE** is an engineer who lands inside a customer's company, builds them an AI service that works, deploys it in production, hands it off to the customer's team, and leaves. The whole job takes 9 weeks. This course teaches you how.

---

## The journey (the picture first)

```
                         THE 4-PHASE JOURNEY
                         ══════════════════

   PHASE 1            PHASE 2            PHASE 3            PHASE 4
   Foundations        Core Build         Deployment         Capstone
   ───────────        ──────────         ──────────         ────────
   "I wrote a         "the tool is a     "it runs 24/7      "it's a platform
    tool"              service"           for everyone"       the team extends"

   ┌─────────┐        ┌──────────┐        ┌──────────┐        ┌──────────┐
   │ CLI     │  ───▶  │ FastAPI  │  ───▶  │ Hardened │  ───▶  │ Platform │
   │ tool    │        │ service  │        │ service  │        │ + 4      │
   │ 1-pager │        │ + RAG    │        │ + breaker│        │ projects │
   │ 5 qs    │        │ + eval   │        │ + ops    │        │ + case   │
   │ + brief │        │ + Docker │        │   docs   │        │   studies│
   └─────────┘        └──────────┘        └──────────┘        └──────────┘
        │                  │                   │                   │
        ▼                  ▼                   ▼                   ▼
   Mei's laptop      Daniel's VM        Production          The team's
                                           24/7               platform

   TIME:  1 week         2 weeks            2 weeks            4 weeks
   LINES: ~300           ~600               ~1500              ~3000
   ARTIFACT: 1-pager   Service + 3 docs   Hardened service  4 projects +
                                                          5 case studies +
                                                          portfolio
```

**Read it left to right.** Each phase is the previous phase *evolved*. Phase 1's CLI is the seed. Phase 4's platform is what you grow it into.

---

## Why this course exists

Most AI projects die at "Who owns this?" — and most AI courses stop at "the demo works." This course teaches you to ship, deploy, hand off, and leave. The customer can fire you the day after you finish and the system keeps running. **That is the FDE's job.**

```
    MOST AI PROJECTS:                       THIS COURSE:

    Demo works ✓                            Demo works ✓
        │                                       │
        ▼                                       ▼
    Pilot works ✓                           Pilot works ✓
        │                                       │
        ▼                                       ▼
    "Who owns this?"                        Prod-grade service ✓
        │                                       │
        ▼                                       ▼
    (no one knows)                          Runbook + RACI + on-call ✓
        │                                       │
        ▼                                       ▼
    (system dies)                           5-question "FDE has left" test
                                                │
                                                ▼
                                            FDE exits; system runs
```

---

## What you produce

### Phase 1 — Foundations
- A CLI tool that drafts replies to customer emails (Mei's terminal)
- A 1-pager that explains the use case to the customer
- A 5-question framework for AI use-case discovery

### Phase 2 — Core Build
- A FastAPI service with `/draft`, `/retrieve`, `/eval`, `/health` endpoints
- 13/13 pytest cases pass
- A discovery deck, a PRD, a solution design doc, and 3 ADRs

### Phase 3 — Deployment
- The Phase 2 service hardened with: hybrid retrieval, circuit breaker, rate limiter, redactor, telemetry, streaming `/draft/stream`, `/feedback`, `/metrics`
- A Caddy reverse proxy in front
- A stakeholder map, an iteration cadence, a runbook, a RACI, an on-call rotation
- 13/13 pytest cases still pass
- 3-loop Mon daily/weekly/monthly cadence

### Phase 4 — Capstone
- 4 projects: MCP drafter, multi-agent dispatcher, distilled SLM, AI data analyst
- 5 case studies: PF drafter, PIVOT, postmortem, SLM cost, handoff
- A portfolio narrative
- A capstone presentation (7 slides, 10 minutes)

---

## How to use this course

1. **Start with Phase 1.** Read the README. Read the scenario brief. Do the 1-pager.
2. **Pick a phase, do it end-to-end.** Each phase is self-contained; you can take a break between them.
3. **Run the tests at the end of each phase.** The pytest count is the bar:
   - End of Phase 2: 13/13
   - End of Phase 3: 13/13 (the same suite, now against the hardened service)
   - End of Phase 4: 25/25 (13 Phase 3 + 4 MCP + 3 multi-agent + 2 SLM + 3 sandbox)
4. **Write the artifacts.** Each phase has at least one written deliverable. The artifacts are what survive the FDE's exit.

---

## File layout

```
course/ai-fde/
├── README.md                      ← you are here
├── phase-1-foundations/           ← CLI tool + 1-pager + 5-question framework
│   ├── README.md
│   ├── scenario-brief.md
│   ├── technical/                 ← 3 lessons (.md + .py each)
│   ├── consulting/                ← 3 lessons (.md each)
│   └── shared/                    ← style guide, tracker data
├── phase-2-core-build/            ← FastAPI service + RAG + eval
│   ├── README.md
│   ├── scenario-lift.md           ← Phase 1→2 narrative
│   ├── diagrams.md                ← flow diagrams (this file's cousin)
│   ├── technical/                 ← 3 lessons
│   ├── consulting/                ← 3 lessons
│   ├── service/                   ← the FastAPI service
│   └── shared/                    ← eval set, policy chunks
├── phase-3-deployment/            ← hardened service + ops artifacts
│   ├── README.md
│   ├── scenario-lift.md           ← Phase 2→3 narrative
│   ├── TECHNICAL-TRACK.md
│   ├── CONSULTING-TRACK.md
│   ├── technical/                 ← 3 lessons
│   └── consulting/                ← 3 lessons + 3 ops artifacts (runbook, RACI, on-call)
└── phase-4-capstone/              ← 4 projects + 5 case studies + portfolio
    ├── README.md
    ├── scenario-brief.md
    ├── projects/                  ← 4 self-contained projects
    ├── case-studies/              ← 5 case studies + portfolio + presentation
    └── technical/                 ← 3 lessons (.md each)
```

---

## The 5-question "FDE has left" test

By the end of the course you should be able to answer YES to all 5:

1. Can a new FDE, on day 1, name the 3 + 1 stakeholder audiences and what each one decides?
2. Can they run the eval suite and explain the 4 RAGAS metrics to the customer?
3. Can they trip the circuit breaker, drain the rate limiter, and read the runbook at 2am?
4. Can they answer "where is the eval set?" / "who owns the drafter?" / "what's the cost ceiling?" without asking the FDE?
5. Can they demo the capstone (PF drafter + MCP + multi-agent + SLM + data analyst) in 10 minutes?

If you answered NO to any of those, you haven't finished your job. Go back to the phase that teaches it.

---

**Last updated:** 2026-10-09
**Length:** ~9 weeks full-time, ~16 weeks part-time
**Cost:** $0 (everything runs with the mock LLM backend, no API key needed)
**Goal:** You finish and you can put "AI FDE" on your LinkedIn.
