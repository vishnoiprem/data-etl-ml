# Technical Track — AI FDE Phase 2

> **From a CLI to a deployable AI service.** Three lessons, ~3 hours total. All code runs without an API key (mock LLM backend by default).

This track teaches the **engineering craft** of taking an AI tool out of the terminal and into a service. Every lesson ends with runnable code you can demo to the customer on a video call.

---

## Lesson map

| # | Lesson | What you build | Time |
|---|---|---|---|
| 01 | [LLM applications and workflows](./technical/01-llm-applications.md) | A FastAPI app with `/draft`, `/health` — wraps the Phase 1 logic in a service | 40 min |
| 02 | [Context engineering and RAG foundations](./technical/02-context-rag.md) | A `/retrieve` endpoint backed by a mock vector store over `shipments.json` + `style-guide.md`; `/draft` now augments the prompt with retrieved context | 50 min |
| 03 | [Early evaluation, reliability, and application-layer patterns](./technical/03-eval-reliability.md) | A `/eval` endpoint + a CLI that grades drafts against the 30-row eval set, saves a baseline, and trips a regression check | 50 min |

After lesson 03, the service is **deployable**: Dockerfile, docker-compose, pytest, `/health` endpoint, full coverage of the happy path and the failure paths.

---

## What "Phase 2 technical" is NOT

- It is **not** async-first. Phase 2 keeps handlers sync; the `hardcode/level-3-streaming/` track is where you graduate to `asyncio` + SSE.
- It is **not** framework-heavy. No LangChain, no LlamaIndex, no Pinecone. Plain Python over a dict-of-lists. The frameworks are in `practice/level-4-rag/`.
- It is **not** Kubernetes. One container, one process, one port.
- It is **not** 1000-line systems. The whole service is ~600 lines across 3 files in `service/`, plus 3 lesson files in `technical/`.

---

## The shared scenario (the Phase 2 lift)

Read [`scenario-lift.md`](./scenario-lift.md). The short version:

> Phase 1 drafter works when the CS person **already knows** the shipment ID. Phase 2 lifts this: the service can answer "where is my parcel?" even when the customer doesn't include an ID, by retrieving the right shipment from the tracker and the right policy from the style guide.

Concretely, Phase 2 makes these changes to the Phase 1 tool:

| Layer | Phase 1 (CLI) | Phase 2 (service) |
|---|---|---|
| Interface | `python3 04-first-ai-tool.py --shipment PF-1003` | `curl -X POST localhost:8000/draft -d '{"email":"...", "shipment_id":"PF-1003"}'` |
| Retrieval | CS person looks up the shipment manually | Service retrieves the shipment from `shipments.json` + the right policy chunk from `style-guide.md` |
| Context | System prompt = persona + style guide | System prompt = persona + style guide + **retrieved policy chunks** + **top-N retrieved shipments** |
| Evaluation | Ad-hoc ("looks good to me") | A 30-row eval set + 4 RAGAS-style metrics + a regression baseline |
| Deployment | Runs on the CS person's laptop | Dockerfile + docker-compose + `/health` for the deployment platform to check |

---

## Code conventions (Phase 2)

- Python 3.11+
- FastAPI + uvicorn for the service
- Pydantic for request/response models
- `pytest` + `httpx` for the tests
- Mock LLM backend by default (the same `complete()` from Phase 1)
- Mock vector store by default (deterministic token-overlap retrieval — no embeddings API needed)
- All code in `service/*.py` and `technical/*.py`

### The reuse pattern

Every technical .py file in Phase 2 starts with this import to reach Phase 1's unified LLM client:

```python
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "pf_llm",
    Path(__file__).parent.parent / "phase-1-foundations" / "technical" / "03-modern-ai-tooling.py",
)
pf_llm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pf_llm)  # type: ignore
complete = pf_llm.complete
PRICING = pf_llm.PRICING
```

This is the same pattern Phase 1's `04-first-ai-tool.py` uses. The reason: Phase 2 should not duplicate Phase 1's pricing, retry, log, and mock code — it should reuse them.

---

## What's next

- The **Consulting Track** — the other half. The documents you'd hand the customer to justify this service.
- **`course/practice/level-4-rag/`** — when you want to graduate to LangChain / LlamaIndex / real embeddings.
- **`course/practice/level-6-production/`** — when you want to add observability, caching, async, and load testing.
- **`course/hardcode/level-8-evaluation-testing/`** — when you want a 1000-line production RAGAS / LLM-as-judge harness.
- **`course/hardcode/level-9-failure-handling/`** — when you want circuit breakers and hallucination detectors.
- **`course/capstone-starters/01-ai-doc-qa/`** — the production version of this service, with FastAPI + JWT + Postgres + Pinecone.
