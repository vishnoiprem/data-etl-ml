# Scenario Lift — Phase 1 → Phase 2

> **The customer is the same. The AI tool is the same. What changes is the surface area.**

Phase 1 produced a Python CLI that Mei (the CS lead at PacificFreight Co.) runs on her laptop:

```bash
python3 04-first-ai-tool.py --shipment PF-1003
# → returns a drafted reply Mei copy-pastes into Gmail
```

Phase 2 lifts that CLI into a **service** that anyone at PacificFreight can call from any tool, with RAG that pulls the right shipment + the right policy when the customer doesn't include a shipment ID.

---

## What you learned in Phase 1

Phase 1 was the on-ramp. You finished it with three things in hand:

1. **A working CLI** — `technical/04-first-ai-tool.py` — runs without an API key (mock backend), handles a known shipment ID, returns a drafted reply.
2. **A 1-pager** — `consulting/04-framing-an-ai-use-case.md` — 8 sections, signed off by Sarah (the ops manager).
3. **A solution outline** — `consulting/05-solution-outline.md` — 6 sections, components, data flow, cost projection, build plan.

Phase 1 also gave you a **shared asset folder** — `shared/shipments.json`, `shared/sample-emails.md`, `shared/style-guide.md` — that Phase 2 reuses.

---

## What Phase 2 changes

The Phase 2 lift is three things:

### 1. CLI → service

| Phase 1 (CLI) | Phase 2 (service) |
|---|---|
| One CS person runs it on her laptop | Any internal tool (or browser) can call it over HTTP |
| No auth (it's on her laptop) | Service has a `/health` endpoint the deployment platform checks |
| Single shipment at a time | `/draft` accepts an email + optional shipment ID; if no ID, the service retrieves it |
| No tests | `pytest` covers the happy path + the failure paths |
| Runs as `python3 ...` | Runs as a Docker container, started by `docker compose up` |

### 2. Lookup → RAG

| Phase 1 | Phase 2 |
|---|---|
| CS person looks up the shipment in the PHP tracker (20 seconds) | Service retrieves the top-1 shipment from `shipments.json` based on the email |
| Style guide is the whole `style-guide.md` (~130 lines) in the system prompt | Style guide is **chunked** and **retrieved** — only the relevant section enters the prompt |
| Context is 1 shipment | Context is top-1 shipment + top-K policy chunks |
| No eval | 30-row eval set, 4 RAGAS-style metrics, regression baseline |

### 3. "Looks right" → "the eval says it's 0.83"

| Phase 1 | Phase 2 |
|---|---|
| Mei reads each draft and decides if it's good | `/eval` runs the 30-row set, produces a markdown report with 4 metrics |
| No baseline — every change is a guess | A `baseline.jsonl` saved at end of week 1; future runs check for regression |
| Failure mode = "Mei sends a bad draft" | Failure mode = "the eval score drops 0.05 week over week" — caught in CI, before customer sees |

---

## What Phase 2 does NOT change

The customer (PacificFreight Co.) and the personas (Mei, Sarah, the CS team) are unchanged. The Phase 1 1-pager is still the source of truth for *why* we're building this. The 4-week build plan from Phase 1's outline is still the schedule; Phase 2 just adds the documents that let the customer scale from 1 CS person using a CLI to a team using a service.

The PacificFreight budget hasn't changed: the customer ceiling is **USD 200/month** in LLM spend. Phase 2 stays well under that (the cost projection in the solution-design doc shows ~$3-5/month at projected volume).

---

## The deliverable contract

Per the Phase 2 brief, you produce **three deliverables**:

| Deliverable | Where it lives | What it is |
|---|---|---|
| **A deployable AI system** | `service/app.py` + `service/rag.py` + `service/eval.py` + `service/Dockerfile` + `service/tests/` | A FastAPI service that boots, runs, serves `/draft` + `/retrieve` + `/eval` + `/health`, passes pytest, builds in Docker |
| **An architecture view** | `consulting/02-prd-and-solution-design.md` (the worked example) + `consulting/pacificfreight-solution-design.md` (the learner's deliverable) | A solution-design document with system diagram + component choices + capacity model + cost model + failure modes, modeled on `course/capstone-starters/01-ai-doc-qa/ARCHITECTURE.md` |
| **A record of key design decisions** | `consulting/03-adrs-and-tradeoffs.md` (the worked examples) + `consulting/decisions/0001..3` (the learner's deliverables) | Three ADRs (FastAPI choice, mock-vs-real vector store, eval regression threshold) following the Michael Nygard template |

Together, those three artifacts are what you hand to PacificFreight's exec sponsor at the end of week 4 of the Phase 2 engagement, and what you hand to your own engineering team at the start of week 5.

---

## Where each Phase 2 lesson lands

```
phase-2-applications/
├── service/                  ← The deployable AI system
│   ├── app.py                  (FastAPI: /draft, /retrieve, /eval, /health)
│   ├── rag.py                  (MockVectorStore + retrieve() + build_rag_prompt())
│   ├── eval.py                 (4 RAGAS-style metrics + LLMJudge + regression check)
│   ├── Dockerfile              (deploys in a container)
│   ├── docker-compose.yml      (`docker compose up`)
│   ├── requirements.txt        (fastapi, uvicorn, pydantic, pytest, httpx)
│   └── tests/test_app.py       (4-5 pytest cases)
│
├── technical/                ← The lesson walkthroughs of the service code
│   ├── 01-llm-applications.md  (T1: wrap Phase 1 in FastAPI)
│   ├── 01-llm-applications.py  (the same FastAPI app, runnable as a script)
│   ├── 02-context-rag.md       (T2: RAG over shipments + policy)
│   ├── 02-context-rag.py       (the RAG module)
│   ├── 03-eval-reliability.md  (T3: eval harness + regression check)
│   └── 03-eval-reliability.py  (the eval CLI)
│
├── consulting/               ← The documents that justify the service
│   ├── 01-requirement-discovery.md   (C1: discovery deck)
│   ├── 02-prd-and-solution-design.md (C2: PRD + design doc)
│   └── 03-adrs-and-tradeoffs.md      (C3: 3 ADRs)
│
└── shared/                   ← The data the service runs on
    ├── eval_set.jsonl            (30 rows: email → expected)
    ├── build_policy_chunks.py    (one-time script: style-guide → policy_chunks.jsonl)
    └── policy_chunks.jsonl       (generated by build_policy_chunks.py)
```

---

**What's after the Phase 2 lift** — Phase 3 takes this service from "deployable" to "in production": streaming responses, hosted vector DB, real auth, observability, rate limiting. The Phase 2 service is the smallest end-to-end thing that proves the system survives a customer pilot; Phase 3 proves it survives a rollout.
