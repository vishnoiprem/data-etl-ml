# Lesson 01 — LLM Applications and Workflows

> **Wrap the Phase 1 CLI in a service.** 40 minutes. Hands-on, runnable.

By the end of this lesson you can take a working CLI and expose it as a **FastAPI service** with `/health` and `/draft` endpoints, Pydantic request/response models, and the same mock LLM backend as Phase 1. You have a `Dockerfile`, a `docker-compose.yml`, and a pytest that confirms the service is alive.

This is the smallest possible step from "runs on Mei's laptop" to "Mei's whole team can use it." T2 adds RAG. T3 adds the eval harness.

---

## 🎯 You will build

A FastAPI service that:
- Exposes `GET /health` (liveness probe)
- Exposes `POST /draft` (the same draft endpoint as Phase 1, but over HTTP)
- Reuses Phase 1's `complete()` via `importlib` (zero code duplication)
- Boots in mock mode by default (no API key needed)
- Has a Dockerfile + docker-compose + a `pytest` test that passes

You finish with a service you can `docker compose up` and call from any HTTP client.

## 🧠 Concept (5 min)

The Phase 1 CLI is a tool. The Phase 2 service is a tool **other tools can call**. The difference is just an HTTP layer — but the impact is huge:

| Phase 1 (CLI) | Phase 2 (service) |
|---|---|
| Mei runs it on her terminal | Anyone in the company can call it |
| No auth (it's on her laptop) | `/health` for the deployment platform to check |
| One CS person benefits | The whole CS team benefits |
| No metrics | `usage.jsonl` already logs every call |
| Fails silently if Mei's terminal crashes | Returns 500 → alerting fires |

**FastAPI** is the right choice for LLM applications because it is:
- **Async-native** (Phase 2 handlers are sync, but you can `await` an LLM in T3+ without rewriting the service)
- **OpenAPI built-in** (visit `/docs` in a browser and you get Swagger UI for free — the FDE shows this to the customer in the demo)
- **Pydantic-validated** (every request and response is typed; bad input returns 422 with a clear error, not a 500 stack trace)

**Pydantic** is the request/response layer. It turns a typed Python class into:
- A JSON schema (which becomes the OpenAPI spec)
- A validator (FastAPI rejects bad requests before your code runs)
- A serializer (your function returns a dataclass, the response is JSON)

You write:
```python
class DraftRequest(BaseModel):
    email: str
    shipment_id: Optional[str] = None
```

FastAPI gives you:
- `POST /draft` with this body
- 422 if `email` is missing
- The OpenAPI spec at `/docs`
- Auto-generated client SDKs in 20+ languages

## 🛠️ Build It (35 min)

### Step 1 — read the Phase 1 code (5 min)

Re-read these two files:
- `../phase-1-foundations/technical/03-modern-ai-tooling.py` — the `complete()` function and the `PRICING` dict
- `../phase-1-foundations/technical/04-first-ai-tool.py` — the Phase 1 CLI

The pattern you'll mirror: Phase 1's `04-first-ai-tool.py` already does `importlib.import_module("03-modern-ai-tooling")` to reuse `complete()`. You do the same thing, but in a service.

### Step 2 — write the Pydantic models (5 min)

Open [`../service/app.py`](../service/app.py) and look at lines 86-110. Three models:

```python
class DraftRequest(BaseModel):
    email: str
    shipment_id: Optional[str] = None
    rep: Optional[str] = None

class ContextSnippet(BaseModel):
    id: str; source: str; score: float; text: str; metadata: dict

class DraftResponse(BaseModel):
    ok: bool
    draft: str
    shipment_id: Optional[str]
    contexts: list[ContextSnippet]
    model: str; provider: str; is_mock: bool
    cost_usd: float; latency_ms: int
```

> **FDE tip:** the response includes `cost_usd` and `latency_ms` because the customer will ask "how much does each call cost?" and "how fast is it?" in the first 10 minutes of the demo. Bake the answer into the response so the FDE doesn't have to scramble.

### Step 3 — write the pipeline (10 min)

Look at `_draft_pipeline(req)` in `app.py` (lines 175-220). Five steps:

1. **Extract the shipment ID** — either from `req.shipment_id` or by regex over the email
2. **Look it up** in `shipments.json` (reuse Phase 1's tracker)
3. **Build a system prompt** — persona + style summary
4. **Build a user prompt** — the email + "Shipment in tracker: - ID: PF-XXXX" (the Phase 1 mock backend looks for this exact line to return a canned reply)
5. **Call `complete()`** — Phase 1's mock by default, real OpenAI if `PF_LLM_PROVIDER=openai` + `PF_OPENAI_API_KEY` is set

> **FDE tip:** the system/user split mirrors Phase 1's lessons 03-04. The Phase 2 lift is that the system prompt now also gets the **retrieved policy chunks** (T2) and the user prompt gets the **explicit shipment** in a Phase-1-compatible format so the mock works.

### Step 4 — wire the endpoints (5 min)

```python
app = FastAPI(title="PacificFreight Phase 2 — AI Drafter", version="0.2.0")

@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "pf-phase2", "n_chunks_loaded": 22}

@app.post("/draft", response_model=DraftResponse)
def draft(req: DraftRequest) -> DraftResponse:
    return _draft_pipeline(req)
```

That's it. The service is done. Boot it:

```bash
cd service
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

Then:
```bash
curl localhost:8000/health
# → {"ok":true,"service":"pf-phase2","n_chunks_loaded":22}

curl -X POST localhost:8000/draft -H 'Content-Type: application/json' \
     -d '{"email":"Where is PF-1003?", "shipment_id":"PF-1003"}'
# → {"ok":true,"draft":"Hi Mei Lin, ...","shipment_id":"PF-1003",...}
```

### Step 5 — Dockerize it (5 min)

The Dockerfile is 15 lines:
- `FROM python:3.11-slim` — small, no build tools
- `COPY requirements.txt .` + `pip install` — cached layer
- `COPY . /app/service/` + `COPY ../shared /app/shared/` — the code + the data
- `HEALTHCHECK` — the deployment platform uses this to know if the service is alive
- `CMD ["uvicorn", "app:app", ...]` — boot

Build and run:
```bash
cd service
docker build -t pf-phase2 .
docker run --rm -p 8000:8000 pf-phase2
# → Same /health response, but in a container.
```

> **FDE tip:** the HEALTHCHECK line is the most-skipped line in a Dockerfile. It is the line that tells Railway / Fly / Render "this container is alive." Without it, the platform will not restart the container on a silent crash. With it, you get free self-healing.

### Step 6 — write the test (5 min)

[`../service/tests/test_app.py`](../service/tests/test_app.py) is 100 lines, 8 tests. The first three are the lesson-01 ones:

```python
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True

def test_draft_known_shipment():
    r = client.post("/draft", json={
        "email": "Hi, can you check on my shipment PF-1003?",
        "shipment_id": "PF-1003",
    })
    assert r.status_code == 200
    body = r.json()
    assert "PF-1003" in body["draft"]
    assert "customs" in body["draft"].lower()
```

Run them:
```bash
cd service
pytest tests/ -v
# → 8 passed in 1.13s
```

## 🏛️ FDE Lens

> **What to ask the customer before you ship this service.**

Three questions, asked in week 4 of Phase 2 (right before deployment):

1. **"Where will this run?"** — Mei's laptop (Phase 1), a shared VM, a Docker container on Railway, a Kubernetes pod on AWS? Each has different `/health` requirements and different cost.
2. **"Who can call it?"** — Just the CS team, or every internal tool? This decides whether you need auth (Phase 3 lifts this).
3. **"What happens when it's down?"** — The CS team needs a fallback. Phase 1's CLI is the fallback. Document it in the runbook.

The FDE who asks these three questions in week 4 is the FDE who doesn't get a 2 AM page in week 5.

## 🌙 Reflect

Write 3-5 sentences:

1. Phase 1's CLI is `python3 04-first-ai-tool.py --shipment PF-1003`. Phase 2's service is `POST /draft {"shipment_id":"PF-1003"}`. What is the **operational** difference, beyond the obvious interface one?
2. The `/health` endpoint returns `n_chunks_loaded: 22`. What does this tell the deployment platform that "200 OK" alone does not?
3. The Dockerfile has a `HEALTHCHECK` line that calls `/health`. If you removed it, what would break in production?
4. The Pydantic `DraftRequest` has `shipment_id: Optional[str] = None`. The `_extract_id` regex runs only when `shipment_id` is None. Why is the order (use-given-then-extract) the right one?
5. The service uses Phase 1's `complete()` via `importlib.util.spec_from_file_location`. Why not `from phase1 import complete`? (Hint: read the import block at the top of `app.py`.)

**What's next** — T2 adds the `/retrieve` endpoint and a RAG layer that pulls the right policy chunk from the style guide. The drafter stops being "the CS person's instructions" and becomes "the CS person's instructions + the relevant slice of the style guide." That's the Phase 2 lift the customer actually pays for.
