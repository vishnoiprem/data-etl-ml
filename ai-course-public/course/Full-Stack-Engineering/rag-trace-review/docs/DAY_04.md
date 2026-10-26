# Day 4 — FastAPI
**Module 4** | Total: 90 min (10 + 20 + 30 + 20 + 20)

---

## 1. Simple explanation (10 min)

**Analogy for a 12-year-old:**
FastAPI is a **traffic controller at an airport**.
- Each request is a plane.
- The controller reads the flight plan (URL).
- The controller checks the runway (function) and guides the plane to the gate (response).
- Pydantic is the security check that opens every bag before boarding.

---

## 2. Technical concepts (20 min)

FastAPI is a Python framework built on **Starlette** (ASGI) and **Pydantic**.
- Routes are functions decorated with `@app.get/post/put/delete`.
- Path and query parameters are typed.
- Bodies are validated by Pydantic.
- OpenAPI is auto-generated at `/docs`.

### Key features
- Type-driven validation
- Dependency injection via `Depends`
- Async-first (`async def`)
- Free OpenAPI

### Request validation flow
URL hits router → dependency resolution → Pydantic parses body / query → handler runs → response model serializes → JSON.

---

## 3. Coding (30 min)

Add `backend/app/routes/calc.py` with two endpoints.

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/calc", tags=["calc"])


class SumIn(BaseModel):
    a: float
    b: float


class SumOut(BaseModel):
    total: float


@router.post("/sum", response_model=SumOut)
def add(body: SumIn):
    return {"total": body.a + body.b}


@router.get("/div/{a}/{b}")
def div(a: float, b: float):
    if b == 0:
        raise HTTPException(status_code=400, detail="division by zero")
    return {"result": a / b}
```

Mount it in `app/main.py`:
```python
from .routes.calc import router as calc_router
app.include_router(calc_router)
```

### Sample I/O
- POST `/calc/sum` `{"a":2,"b":3}` → `{"total": 5.0}`
- GET `/calc/div/10/2` → `{"result": 5.0}`

### Line-by-line
- `BaseModel` defines the contract.
- `response_model=SumOut` validates and shapes the response.
- `HTTPException` short-circuits with the right status.

---

## 4. Debugging & tests (20 min)

### Bug 1: 422 on every request
**Cause:** Pydantic type mismatch.
**Fix:** check your body matches the model. Look at the `detail` array in the response.

### Bug 2: blocking the event loop
`def handler` with a slow DB call blocks every other request. Fix: `async def` + `await` or use a threadpool.

### Bug 3: dict leak
Returning a `dict` with extra fields when `response_model` is set strips them silently. Use `response_model_exclude_none=True` if needed.

### Tests
```python
def test_sum(client):
    r = client.post("/calc/sum", json={"a": 2, "b": 3})
    assert r.status_code == 200 and r.json() == {"total": 5.0}

def test_div_zero(client):
    r = client.get("/calc/div/1/0")
    assert r.status_code == 400
```

---

## 5. Mock interview practice (20 min)

**Q1 — "Difference between `def` and `async def`?"**
> `async def` is a coroutine; FastAPI awaits it. Long blocking calls inside `async def` block the event loop — use `run_in_threadpool` for them.

**Q2 — "What is `Depends`?"**
> A function whose return is injected. Example: `db = Depends(get_db)`.

**Q3 — "What is the lifespan event?"**
> Replaces `@app.on_event` for startup/shutdown. Code before `yield` runs on startup.

**Q4 — "Why Pydantic over dataclasses?"**
> Validation + OpenAPI generation + serialization in one place.

**Q5 — "How do you version an API?"**
> URL prefix `/v1/...` is simplest. Header-based works too. Pick one and document.

---

## 6. Success criteria check
- [ ] I can write a route with body, query, path params.
- [ ] I can write a Pydantic model.
- [ ] I can raise HTTPException with a specific code.
- [ ] I can mount a router.
- [ ] I can write a test for 200 and 400.

## 7. Grade yourself 0–10
| Area | Score |
|---|---|
| Correctness | /10 |
| Code quality | /10 |
| Debugging | /10 |
| API design | /10 |
| Frontend implementation | /10 |
| Performance | /10 |
| Testing | /10 |
| Communication | /10 |
| **Total** | **/80** |

## 8. Coding assignment
**Add `POST /calc/mean` taking `{"values":[1,2,3]}` returning `{"mean":2}`. Return 422 on empty list.**

### Rubric (0–10)
- 0: doesn't compile
- 4: correct mean
- 6: 422 on empty
- 8: typed model
- 10: handles overflow + uses `statistics.fmean`

### Solution
```python
class MeanIn(BaseModel):
    values: list[float] = Field(min_length=1)
class MeanOut(BaseModel):
    mean: float
@router.post("/mean", response_model=MeanOut)
def mean(body: MeanIn):
    return {"mean": sum(body.values) / len(body.values)}
```

**Time: 90 min**