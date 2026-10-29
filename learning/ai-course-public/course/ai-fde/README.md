# AI FDE — the full course

> **A 7-phase course that teaches you to be an AI Forward-Deployed Engineer.** You build 12 things across 4 project phases, write 15 case studies, drill 11 interview round types, and rehearse against 100 company-specific interview loops.

An **AI FDE** is an engineer who lands inside a customer's company, builds them an AI service that works, deploys it in production, hands it off to the customer's team, and leaves. The whole job takes 9 weeks. This course teaches you how.

> **Want a deadline instead of a curriculum?** See
> [`90-day-plan.md`](./90-day-plan.md) — the same four phases scheduled
> against a 90-day window, plus the interview reps and customer-facing
> rehearsal this course deliberately doesn't teach.

---

## The journey (the picture first)

```
                         THE 7-PHASE JOURNEY
                         ══════════════════

   PHASE 1            PHASE 2            PHASE 3            PHASE 4         PHASE 5            PHASE 6            PHASE 7
   Foundations        Core Build         Deployment         Capstone        Advanced           Interview Prep     100-Company FDE
   ───────────        ──────────         ──────────         ────────       ──────────         ────────────      ───────────────
   "I wrote a         "the tool is a     "it runs 24/7      "the platform   "principal-grade    "you're a           "100 interview
    tool"              service"           for everyone"       the team        scale, multi-       candidate, not     reports: tier,
                                                          extends"        tenancy, DR,         a builder"         process, success,
                                                                          sandbox"                               rejection, reading

   ┌─────────┐        ┌──────────┐        ┌──────────┐        ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
   │ CLI     │  ───▶  │ FastAPI  │  ───▶  │ Hardened │  ───▶  │ 4        │    │ 4        │ ─▶ │ 9 modules│ ─▶ │ 100 files│
   │ tool    │        │ service  │        │ service  │        │ projects │    │ projects │    │ + 11     │    │ + index  │
   │ 1-pager │        │ + RAG    │        │ + breaker│        │ + 5 case │    │ + 5 case │    │ rounds   │    │          │
   │ 5 qs    │        │ + eval   │        │ + ops    │        │ studies  │    │ studies  │    │          │    │          │
   │ + brief │        │ + Docker │        │ + docs   │        │          │    │ + Redis  │    │          │    │          │
   └─────────┘        └──────────┘        └──────────┘        └──────────┘    └──────────┘    └──────────┘    └──────────┘

   TIME:  1 week         2 weeks            2 weeks            4 weeks         6 weeks            3 weeks            2-4 weeks
   ARTIFACT: 1-pager   Service + 3 docs   Hardened service  4 projects +    4 projects +       Mock-loop, 35/35   Tier-specific
                                                          5 case studies + 5 case studies      tests pass         rehearsal per
                                                          portfolio                                              target company
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

### Phase 5 — Advanced
- 4 projects: Redis state externalization, OAuth multi-tenant, gVisor sandbox, multi-region DR
- 5 scale-event postmortems: multi-tenant onboarding, region failover, cost ceiling breach, evals at scale, principal handoff
- 3 lessons: state externalization, auth and tenancy, sandbox hardening
- **35/35 tests** (adds 10 to the Phase 4 suite)

### Phase 6 — Interview Prep
- 9 modules mapped to 11 interview round types (decomposition, behavioral, system design, practical coding, SWE coding, take-home, project deep dive, customer simulation, company experiences, GenAI)
- The 4-step framework (Clarify / Decompose / Design / Tradeoffs) as reusable muscle memory
- 12 real interview reports + customer simulation scenarios

### Phase 7 — FDE 100-Company Interview Bank
- 100 per-company FDE/FDSE interview files (Palantir, Anthropic, OpenAI, Anthropic, AWS, Snowflake, Databricks, … )
- Each file: company snapshot, interview process, success stories, rejection stories, reading list
- Tiered: FDE-native / frontier lab / big-tech PS / growing

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
├── 90-day-plan.md                 ← the same course, scheduled against a deadline
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
├── phase-4-capstone/              ← 4 projects + 5 case studies + portfolio
│   ├── README.md
│   ├── scenario-brief.md
│   ├── projects/                  ← 4 self-contained projects
│   ├── case-studies/              ← 5 case studies + portfolio + presentation
│   └── technical/                 ← 3 lessons (.md each)
├── phase-5-advanced/              ← 4 projects: Redis, OAuth multi-tenant, gVisor, multi-region DR
│   ├── README.md
│   ├── scenario-brief.md
│   ├── projects/                  ← 01-redis-state, 02-oauth, 03-gvisor, 04-multi-region-dr
│   ├── technical/                 ← 3 lessons (state, auth/tenancy, sandbox)
│   └── case-studies/              ← 5 scale-event postmortems
├── phase-6-interview-prep/        ← 9 modules mapped to 11 interview round types
│   ├── README.md
│   ├── interview-process.md       ← the FDE loop, day-in-the-life
│   ├── decomposition/             ← 4-step: clarify / decompose / design / tradeoffs
│   ├── behavioral/                ← 3 question types + STAR
│   ├── system-design/             ← 9 system design patterns
│   ├── practical-coding/          ← AI-assisted coding rounds
│   ├── swe-coding/                ← classic SWE prep
│   ├── take-home/                 ← 3 take-home patterns
│   ├── project-deep-dives/        ← the 45-min presentation script
│   ├── customer-simulation/       ← highest-signal round
│   ├── company-experiences/       ← 12 real interview reports
│   └── generative-ai/             ← GenAI-specific + companion courses
└── phase-7-FDE-100-interview/     ← 100 company-specific FDE/FDSE interview files
    ├── 00-INDEX.md                ← tier map + how to use
    ├── 03-openai-fde.md           ← OpenAI: process, success/rejection, reading list
    ├── 01-palantir-fdse.md        ← Palantir FDSE (FDE-native tier)
    ├── 02-anthropic-fde.md        ← Anthropic (frontier-lab tier)
    └── …95 more companies…       ← tiered: FDE-native / frontier / big-tech PS
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

**Length:** Phases 1–4 ~9 weeks full-time; the full 7-phase track ~20 weeks full-time, ~34 weeks part-time
**Cost:** $0 (everything runs with the mock LLM backend, no API key needed); Phase 5 production mode adds ~$50/mo infra
**Goal:** You finish and you can put "AI FDE" on your LinkedIn.

---

**Last updated:** 2026-10-21
**License:** MIT — use freely in your own courses, prototypes, and products.  
