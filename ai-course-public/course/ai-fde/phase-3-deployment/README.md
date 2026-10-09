# AI FDE — Phase 2: Applications

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

See:
- [TECHNICAL-TRACK.md](./TECHNICAL-TRACK.md) — the 3-lesson map
- [CONSULTING-TRACK.md](./CONSULTING-TRACK.md) — the 3-lesson map

---

## The standard template (carried over from Phase 1)

### Technical lesson (.md + .py)

```markdown
# Lesson N: <Title>
## 🎯 You will build
## 🧠 Concept (5 min)
## 🛠️ Build It (30-50 min)
## 🏛️ FDE Lens
   — the one question to ask the client before you start coding
## 🌙 Reflect
   — what to write down + "What's next" pointer
```

### Consulting lesson (.md only)

```markdown
# Lesson N: <Title>
## 🎯 Outcome
   — the artifact you produce (a doc, a 1-pager, an ADR)
## 🧠 Mindset
   — the principle
## 🛠️ Practice
   — the exercise, with a worked example
## 🏛️ FDE Lens
   — the technical reality underneath
## 🌙 Reflect
   — what to write down + "What's next" pointer
```

---

## Shared assets (used by both tracks)

- [`shared/eval_set.jsonl`](./shared/eval_set.jsonl) — 30 eval rows: (email, expected_intent, expected_shipment_id, expected_mentions). 10 clean, 10 messy, 10 edge.
- [`shared/policy_chunks.jsonl`](./shared/policy_chunks.jsonl) — pre-chunked style guide, one chunk per H2 section. Backed by `shared/build_policy_chunks.py`, regenerated from Phase 1's `../phase-1-foundations/shared/style-guide.md`.
- **Reused from Phase 1**:
  - [`../phase-1-foundations/shared/shipments.json`](../phase-1-foundations/shared/shipments.json) — 15 mock shipments. Read-only.
  - [`../phase-1-foundations/shared/sample-emails.md`](../phase-1-foundations/shared/sample-emails.md) — the 10 Phase 1 inbound emails; 10 of them are reused in `eval_set.jsonl`.

---

## The service (the deliverable)

[`service/app.py`](./service/app.py) is the Phase 2 deliverable. Boot it:

```bash
cd service
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

Then:

```bash
curl localhost:8000/health
curl -X POST localhost:8000/draft -H 'Content-Type: application/json' \
     -d '{"email":"Where is PF-1003?", "shipment_id":"PF-1003"}'
curl 'localhost:8000/retrieve?q=customs%20duty'
curl -X POST localhost:8000/eval -H 'Content-Type: application/json' \
     -d '{"set":"../shared/eval_set.jsonl"}'
```

The service runs the **mock LLM backend** by default — no API key needed. Set `PF_LLM_PROVIDER=openai` with `PF_OPENAI_API_KEY=sk-...` to run against real OpenAI.

Run the tests:

```bash
cd service
pytest tests/ -v
```

Run in Docker:

```bash
docker build -t pf-phase2 .
docker run --rm -p 8000:8000 pf-phase2
```

---

## How to use this phase

1. **Read `scenario-lift.md` first** (5 min). It tells you what changes from Phase 1.
2. **Pick a track.** Most people go Technical first (it's tangible).
3. **Do one lesson per session.** Each is 30-50 min of build time + 5-10 min of reflection.
4. **After T1, the service is runnable.** After T2, it does RAG. After T3, it grades itself.
5. **Run the consulting track in parallel.** C1-C3 produce the documents you'd hand a customer.

---

## What's after Phase 2

Phase 2 is the "deployable service" phase. After it, you can go to:

- **Phase 3 (next)** — Streaming responses, real vector DB (Pinecone / Qdrant), auth, rate limiting, observability with LangSmith or Helicone.
- **`course/practice/level-4-rag/`** — when you want LangChain / LlamaIndex / Self-RAG / GraphRAG (the framework versions of T2).
- **`course/hardcode/level-8-evaluation-testing/`** — when you want a 1000-line RAGAS / LLM-as-judge harness (the prod version of T3).
- **`course/hardcode/level-9-failure-handling/`** — when you want circuit breakers and hallucination detectors (the reliability half of T3).
- **`course/capstone-starters/01-ai-doc-qa/`** — the full document-Q&A RAG capstone this phase's service is the teaching version of.

---

**Last updated:** 2026-10-09
**Tone:** hands-on, FDE-style, with practical code in every lesson
**Goal:** You finish Phase 2 and you can put the service in front of a paying customer.
