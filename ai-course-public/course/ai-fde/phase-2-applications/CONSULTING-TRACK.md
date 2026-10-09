# Consulting Track — AI FDE Phase 2

> **From "what does the customer want?" to "here are the documents that justify the build."** Three lessons, ~2 hours total.

This track teaches the **documents** the FDE writes when an engagement leaves Phase 1 and enters Phase 2. Where Phase 1's consulting lessons produced the 1-pager and the solution outline, Phase 2's consulting lessons produce the **discovery deck**, the **PRD**, the **solution-design document**, and a **set of ADRs**. These are the documents that travel: from FDE to engineering team, from engineering team to the customer, from the customer to their exec team.

---

## Lesson map

| # | Lesson | What you produce | Time |
|---|---|---|---|
| 01 | [Requirement discovery](./consulting/01-requirement-discovery.md) | A `discovery-deck.md` — Phase 2 lift of the 5-question framework with RAG-readiness questions appended | 35 min |
| 02 | [PRDs and solution design documents](./consulting/02-prd-and-solution-design.md) | A `pacificfreight-prd.md` (functional + non-functional requirements, acceptance criteria) + a `pacificfreight-solution-design.md` (system diagram, component choices, capacity model, failure modes) | 50 min |
| 03 | [Communicating scope, choices, and trade-offs (ADRs)](./consulting/03-adrs-and-tradeoffs.md) | Three ADRs (`0001-fastapi.md`, `0002-mock-vector-store.md`, `0003-eval-regression-threshold.md`) — the decisions that would otherwise live in someone's head | 35 min |

After C3, the consulting-track deliverable is the trio of documents that any customer engagement needs to scale: the **discovery deck** (what we heard), the **PRD + design doc** (what we're building), and the **ADRs** (why we built it this way and not another way).

---

## What "Phase 2 consulting" is NOT

- It is **not** a sales process. The customer has signed the Phase 1 1-pager; we're already inside the engagement.
- It is **not** a project plan. The 4-week build plan lives in the Phase 1 outline; Phase 2 tracks decisions, not dates.
- It is **not** legal. Contracts are a different document with a different audience.
- It is **not** re-doing Phase 1. Each Phase 2 lesson **extends** a Phase 1 artifact: C1 extends the 5-question framework; C2 extends the 1-pager and the outline; C3 introduces a new artifact (the ADR).

---

## The shared scenario (the Phase 2 lift)

The customer has signed the Phase 1 1-pager. The CLI works in the CS person's terminal. Now the customer is asking "how do we get this in front of more people, and what does it cost to scale?" That's the Phase 2 question — and the consulting track teaches you to answer it in documents the customer's exec team can read.

---

## How Phase 2 consulting builds on Phase 1 consulting

| Phase 1 artifact | Extended by Phase 2 |
|---|---|
| `02-asking-better-questions.md` — the 5-question framework | **C1** adds 5 more questions for RAG-readiness (where does the knowledge live? who owns updates? what's the data-privacy posture?) |
| `04-framing-an-ai-use-case.md` — the 1-pager | **C2** turns the 1-pager into a full PRD (user personas, FRs with acceptance criteria, NFRs) |
| `05-solution-outline.md` — the build plan | **C2** turns the outline into a solution-design doc (system diagram, component choices, capacity model, cost model, failure modes) — modeled on `capstone-starters/01-ai-doc-qa/ARCHITECTURE.md` |
| (none) | **C3** introduces the ADR — the artifact that records *why*, not *what* |

---

## Code conventions (Phase 2 consulting)

None. Phase 2 consulting produces **markdown documents**, not code. Each consulting lesson:

1. States the **outcome** — the artifact the learner produces
2. Gives the **mindset** — the principle behind the artifact
3. Walks through the **practice** — a worked example for PacificFreight
4. Connects to the **FDE lens** — how the document maps to a technical decision
5. Closes with **reflect** questions and a "What's next" pointer

---

## What's next

- The **Technical Track** — the FastAPI service that the design document describes.
- **`course/practice/level-4-rag/`** — the RAG technical lessons, for the learner who wants to understand what's inside the "retrieval" box on the solution-design diagram.
- **`course/capstone-starters/01-ai-doc-qa/ARCHITECTURE.md`** — the production exemplar of the solution-design doc this track teaches you to write.
- **Phase 3** — where these documents get tested against a real production rollout (streaming, multi-tenancy, auth, observability).
