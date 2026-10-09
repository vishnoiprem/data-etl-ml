# AI FDE — Phase 2: Core Build

> **From a CLI on your laptop to a deployable AI service.** Three lessons per track. ~2 weeks of study. All code runs without an API key.

An **AI FDE at the Phase 2 level** can take the Phase 1 CLI, wrap it in a service, add retrieval over the customer's knowledge, and stand up an eval harness that catches regressions before they ship. This phase is the bridge between "I wrote a tool" and "the tool is in front of customers."

---

## What you will produce by the end of Phase 2

1. **A deployable AI system** — a FastAPI service with `/draft`, `/retrieve`, `/eval`, `/health` endpoints, packaged in Docker, with pytest coverage.
2. **An architecture view** — a solution-design document (system diagram, component-choices table, capacity model, cost model, failure modes) modeled on the `capstone-starters/01-ai-doc-qa/ARCHITECTURE.md` template.
3. **A record of key design decisions** — three Architecture Decision Records (ADRs) for the choices that would otherwise live in someone's head.

That is it. Phase 2 is **not** Kubernetes, **not** LangChain, **not** a multi-tenant SaaS. It is the smallest end-to-end thing that proves the system survives a customer pilot.

---

## The scenario (continued from Phase 1)

Same customer — **PacificFreight Co.**, the 12-person cross-border logistics SMB — with one lift:

> The Phase 1 drafter works when the CS person **already knows** the shipment ID. Phase 2 lifts this: the service can answer "where is my parcel?" **even when the customer doesn't include an ID**, by retrieving the right shipment from the tracker and the right policy from the style guide.

Read the lift: [`scenario-lift.md`](./scenario-lift.md).
Read the Phase 1 brief that started it all: [`../phase-1-foundations/scenario-brief.md`](../phase-1-foundations/scenario-brief.md).

The same scenario is used in every lesson in both tracks. Phase 1 built the CLI; Phase 2 ships the service; Phase 3 (next) will add streaming, multi-tenancy, and the move to a hosted vector DB.

---

## Two parallel tracks

| Track | What you learn | What you produce | Files |
|---|---|---|---|
| **Technical** | FastAPI, RAG, retrieval, eval harnesses, application-layer reliability | A deployable AI system with tests + Dockerfile | [`technical/`](./technical/) + [`service/`](./service/) |
| **Consulting** | Requirement discovery, PRDs, solution-design docs, ADRs | A discovery deck, a PRD, a solution design doc, three ADRs | [`consulting/`](./consulting/) |

You can take the tracks in either order, but the **end-of-phase deliverable** is the same artifact seen from two sides: the **service** (technical) and the **documents that justify it** (consulting).

---

## The standard template (carried over from Phase 1)

### Technical lesson (.md + .py)

Each Phase 2 technical lesson is **two files**:

- **`technical/NN-name.md`** — the lesson narrative: 🎯 Outcome / 🧠 Mindset / 🛠️ Practice / 🏛️ FDE Lens / 🌙 Reflect.
- **`technical/NN-name.py`** — the runnable hands-on script. **The .py is the spec.** If the .py doesn't run, the lesson isn't done.

You can take the lessons in any order, but the recommended sequence is **T1 → T2 → T3**, because each builds on the last:

```
T1 (LLM apps & workflows)
   ↓ exposes the Phase 1 CLI as /draft
T2 (Context engineering & RAG)
   ↓ adds /retrieve, the drafter now grounds on retrieved context
T3 (Early eval, reliability)
   ↓ adds /eval, regression check, the drafter is now measured
```

### Consulting lesson (.md only)

Each Phase 2 consulting lesson is **one .md file**. It uses the same 5-section skeleton as the technical track, but the 🛠️ Practice section is a **written deliverable** (PRD, ADR, design doc), not runnable code.

```
C1 (Requirement discovery)
   ↓ produces a 10-question discovery deck
C2 (PRD & solution design)
   ↓ produces a PRD + a solution design doc
C3 (ADRs / trade-offs)
   ↓ produces 3 ADRs
```

The deliverables live **alongside** the lesson .md in `consulting/`. They're the artifacts the FDE hands to the customer.

---

## File layout

```
phase-2-core-build/
├── README.md                      ← you are here
├── scenario-lift.md               ← the Phase 1→2 narrative
├── technical/                     ← 3 lessons (.md + .py each)
│   ├── 01-llm-applications.{md,py}
│   ├── 02-context-rag.{md,py}
│   └── 03-eval-reliability.{md,py}
├── consulting/                    ← 3 lessons (.md each)
│   ├── 01-requirement-discovery.md
│   ├── 02-prd-and-solution-design.md
│   └── 03-adrs-and-tradeoffs.md
├── service/                       ← the FastAPI service (built across the 3 lessons)
│   ├── app.py
│   ├── retrieval.py
│   ├── eval.py
│   ├── tests/
│   └── Dockerfile
└── shared/                        ← Phase 1's style guide + tracker data
```

---

## How long does this take?

| Track | Time per lesson | Total |
|---|---|---|
| Technical | 40–50 min (read + run the .py) | ~2.5 hours |
| Consulting | 30–50 min (read + write the deliverable) | ~2 hours |
| **Both tracks** | — | **~5 hours** |

This is the smallest phase. **The hardest thing is not the code, it's resisting scope.** Phase 2 is **not** the place to add observability, auth, or a frontend. Those are Phase 3.

---

## What comes next

When you finish Phase 2 you have a service that passes pytest, has an eval harness, and is documented well enough that a new engineer can pick it up. **That's the bar.**

Phase 3 (in `../phase-2-core-build/`) lifts this to: hybrid retrieval (BM25 + dense + RRF), a circuit breaker, rate limiting, redaction, telemetry, a runbook + RACI + on-call rotation, and a GO/NO-GO gate. The service goes from "works on my laptop" to "runs in production with a team that owns it."

Phase 4 (in `../phase-4-capstone/`) takes the Phase 3 service and turns it into a **platform**: MCP for tool use, multi-agent for complex cases, a distilled SLM for cost, a fresh engagement for breadth, plus 5 case studies and a capstone presentation.

Read [`../phase-2-core-build/scenario-lift.md`](../phase-2-core-build/scenario-lift.md) for the Phase 3 lift.
