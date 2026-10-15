# Day 4 — FastAPI

## 1. Analogy (10 min)
FastAPI is a **traffic controller at an airport**. Each request is a plane. The controller reads the flight plan (URL), checks the runway (function), and guides it to the gate (response). Pydantic is the security check that opens every bag.

## 2. Technical concept (20 min)
FastAPI is a Python framework built on **Starlette** (ASGI) and **Pydantic**. Routes are functions decorated with `@app.get/post/put/delete`. Path and query parameters are typed. Body is validated by Pydantic. OpenAPI docs are generated for free.

### Key features
- Type-driven validation
- Dependency injection via `Depends`
- Async-first (`async def`)
- Auto OpenAPI at `/docs`

## 3. Why this problem exists
Express and Flask needed 3rd-party libs to do type validation. FastAPI bakes it in.

## 4. Data flow
Client → ASGI → router → dependency resolution → Pydantic validation → handler → response model serialization → JSON → client

## 5. Complete example
**File: `backend/app/routes/calc.py`**
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

## 6. Line-by-line
- `BaseModel` defines the contract.
- `response_model=SumOut` validates and shapes the response.
- `HTTPException` short-circuits with a status code.

## 7. Sample I/O
- POST `/calc/sum` `{"a":2,"b":3}` → `{"total": 5}`
- GET `/calc/div/10/2` → `{"result": 5.0}`

## 8. Bugs
- Forgetting `response_model` leaks internal types.
- Using `def` instead of `async def` blocks the event loop on slow I/O.
- Returning a dict when `response_model` is a list — FastAPI coerces or errors.

## 9. Tests
```python
def test_sum(client):
    r = client.post("/calc/sum", json={"a":2,"b":3})
    assert r.status_code == 200 and r.json() == {"total": 5.0}

def test_div_zero(client):
    r = client.get("/calc/div/1/0")
    assert r.status_code == 400
```

## 10. Performance
- Pydantic v2 is written in Rust — fast.
- For huge responses, stream with `StreamingResponse`.
- Avoid `await sync_function()`; use `run_in_threadpool`.

## 11. Five Q&As
1. **What's the difference between `def` and `async def`?** `async def` is a coroutine; FastAPI can await it without blocking other requests.
2. **What is `Depends`?** A function whose return is injected into the route.
3. **What is the lifespan event?** Replaces `@on_event` for startup/shutdown.
4. **Why Pydantic over dataclasses?** Validation + OpenAPI.
5. **How do you version the API?** URL prefix `/v2/...`.

## 12. Coding assignment
Add a `POST /calc/mean` that takes `{"values": [1,2,3]}` and returns `{"mean": 2}`. Return 422 on empty list.

## 13. Solution + rubric
```python
class MeanIn(BaseModel):
    values: list[float] = Field(min_length=1)

class MeanOut(BaseModel):
    mean: float

@router.post("/mean", response_model=MeanOut)
def mean(body: MeanIn):
    return {"mean": sum(body.values) / len(body.values)}
```
- 0: doesn't compile
- 4: returns correct mean
- 6: validates non-empty (422)
- 8: returns correct type, declared model
- 10: handles overflow, uses `statistics.fmean`

**Time: 90 min**