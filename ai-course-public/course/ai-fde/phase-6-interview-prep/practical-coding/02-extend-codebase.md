# Practical Coding Sub-Lesson 2 — Extend a Codebase (brownfield, 90 min, AI-assisted)

> **This is the second most common practical-coding sub-round.** The format: 90 minutes, a realistic codebase you've never seen, "add a feature." You can use an AI assistant. **The signal: a candidate who reads the codebase first, uses the AI to ask "where is X implemented?", and adds a feature that fits the existing patterns — is showing they can ship in a brownfield environment.**

---

## Why this sub-round is the FDE signal

The 4 things the interviewer is testing:

1. **Can you read a codebase?** Brownfield is the FDE's daily work. The candidate who reads the README + the architecture doc + the tests in the first 20 minutes is signaling they can navigate.
2. **Can you use the AI to explore?** The AI is a codebase explorer, not a thinking partner. The candidate who uses the AI to ask "where is the rate limiter implemented?" is showing they can ramp up fast.
3. **Can you match the existing patterns?** The new feature should look like it was always there. The candidate who writes 200 lines of new code in a different style is signaling they can't ship in a brownfield environment.
4. **Can you ship without breaking the existing system?** The 5 tests should pass. The 5 new tests should pass. Total: 10/10 tests pass.

**The FDE pattern:** explore first, plan second, code third, test fourth. Same as the take-home, with a brownfield twist.

---

## The prompt template (the most common format)

> "Here's a codebase you've never seen. Add a feature. You have 90 minutes. You can use any tools you want, including an AI assistant."

**The feature is one of:**

- **New endpoint:** add a `/users` endpoint to a FastAPI service.
- **New tool:** add a `lookup_user` tool to an MCP server.
- **New metric:** add a `latency_p99` metric to a Prometheus exporter.
- **New test:** add a regression test for a known bug.

**The 5 deliverables (always):**

1. **The feature code** (1-2 files, ~50-200 lines).
2. **The tests** (3-5 tests).
3. **The README update** (1-2 paragraphs).
4. **The regression check** (existing tests still pass).
5. **The handoff note** (1 paragraph: what you changed, what the next engineer should know).

---

## The 3-phase plan (90 minutes)

### Phase 1: Explore the Codebase (20 minutes)

**Goal:** build a 1-page mental model of the codebase.

**The 5 sub-tasks:**

1. **Read the README.** 5 minutes. What does the codebase do? What's the architecture?
2. **Read the architecture doc.** 5 minutes. What's the system diagram? What's the data flow?
3. **Skim the tests.** 5 minutes. What are the existing test patterns? How are they structured?
4. **Use the AI to ask questions.** 5 minutes. "Where is the rate limiter implemented?" "How does the circuit breaker work?" "What's the data flow for the /draft endpoint?"
5. **Build the mental model.** 1-page diagram: input → processing → output. Note the 3-5 key abstractions (e.g., CircuitBreaker, TokenBucketRateLimiter, HybridRetriever).

**The 3 deliverables for Phase 1:**

- A 1-page mental model (could be a comment in the code)
- A list of 3-5 key abstractions (e.g., CircuitBreaker, RateLimiter, Retriever)
- A list of 3-5 patterns to match (e.g., "all endpoints have a request_id middleware", "all errors are logged as JSON")

### Phase 2: Implement the Feature (50 minutes)

**Goal:** ship the feature with the 5 deliverables.

**The 4 sub-tasks:**

1. **Plan the feature.** 1-page design: API contract, data model, error handling, tests.
2. **Write the code.** Match the existing patterns. Use the same imports, the same naming conventions, the same error handling.
3. **Write the tests.** 3-5 tests. Use the same test framework, the same fixtures, the same assertion style.
4. **Run the existing tests.** All 5 existing tests should still pass. If they don't, debug.

**The 5 deliverables for Phase 2:**

- The feature code (1-2 files, ~50-200 lines)
- The tests (3-5 tests)
- The README update (1-2 paragraphs)
- The regression check (existing tests still pass)
- The handoff note (1 paragraph: what you changed, what the next engineer should know)

### Phase 3: Tests + Polish (20 minutes)

**Goal:** make the feature operable by someone who isn't you.

**The 4 sub-tasks:**

1. **Add edge cases.** Empty input, missing field, malformed JSON, etc.
2. **Run the full test suite.** `pytest` should pass on the first run. If it doesn't, debug.
3. **Update the README.** The README should mention the new feature.
4. **Write the handoff note.** 1 paragraph: what you changed, what the next engineer should know.

**The 3 anti-patterns to avoid in Phase 3:**

1. **Skipping the regression check.** The existing tests should pass. If they don't, you broke something.
2. **Skipping the handoff note.** The handoff is the FDE signal.
3. **Going over time.** 90 minutes is 90 minutes. Practice with a timer.

---

## The worked example: "Add a `/users` endpoint to a FastAPI service"

### Phase 1: Explore the Codebase (20 minutes)

**The codebase (hypothetical):**

```
service/
├── app.py              # FastAPI app with 5 endpoints
├── circuit.py          # CircuitBreaker + RateLimiter
├── retrieval.py        # HybridRetriever (BM25 + dense + RRF)
├── eval.py             # 4 RAGAS metrics
├── telemetry.py        # Prometheus + JSON logger
└── tests/
    └── test_app.py     # 5 tests
```

**The 1-page mental model:**

- **API:** FastAPI with 5 endpoints, all with request_id middleware.
- **Circuit:** CircuitBreaker + RateLimiter + Redactor + TTLCache.
- **Retrieval:** HybridRetriever (BM25 + dense + RRF).
- **Eval:** 4 RAGAS metrics (faithfulness, ansrel, context_precision, context_recall).
- **Telemetry:** Prometheus + JSON logger.

**The 3-5 key abstractions:**

- `CircuitBreaker` — wraps external API calls
- `TokenBucketRateLimiter` — limits requests per user
- `HybridRetriever` — retrieves from BM25 + dense
- `MetricsRegistry` — exports Prometheus metrics
- `JsonLogger` — structured JSON logging

**The 3-5 patterns to match:**

- All endpoints have `request_id` in the response
- All errors are logged as JSON with `error_type`, `error_message`, `request_id`
- All external calls go through the circuit breaker
- All rate-limit checks happen before the LLM call
- All tests use `pytest` with the `client` fixture

### Phase 2: Implement the Feature (50 minutes)

**The feature code (`service/users.py`):**

```python
"""User management endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .circuit import RateLimiter
from .telemetry import MetricsRegistry, JsonLogger

router = APIRouter()
rate_limiter = RateLimiter(per_user_per_min=10)
metrics = MetricsRegistry()
logger = JsonLogger()

class UserRequest(BaseModel):
    email: str
    name: str

class UserResponse(BaseModel):
    user_id: str
    email: str
    name: str

@router.post("/users", response_model=UserResponse)
def create_user(req: UserRequest, request_id: str):
    """Create a new user. Rate limit: 10 req/min per user."""
    if not rate_limiter.allow(req.email):
        metrics.increment("users.rate_limited")
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # ... create user in DB ...
    user_id = "user_123"
    metrics.increment("users.created")
    logger.info({"event": "user_created", "user_id": user_id, "request_id": request_id})

    return UserResponse(user_id=user_id, email=req.email, name=req.name)
```

**The test (`tests/test_users.py`):**

```python
import pytest
from fastapi.testclient import TestClient
from service.app import app

client = TestClient(app)

def test_create_user():
    response = client.post("/users", json={"email": "alice@example.com", "name": "Alice"})
    assert response.status_code == 200
    assert response.json()["email"] == "alice@example.com"

def test_create_user_rate_limited():
    for _ in range(10):
        client.post("/users", json={"email": "alice@example.com", "name": "Alice"})
    response = client.post("/users", json={"email": "alice@example.com", "name": "Alice"})
    assert response.status_code == 429

def test_create_user_missing_email():
    response = client.post("/users", json={"name": "Alice"})
    assert response.status_code == 422

def test_create_user_empty_name():
    response = client.post("/users", json={"email": "alice@example.com", "name": ""})
    assert response.status_code == 422
```

**The README update:**

```markdown
## New: `/users` endpoint (added 2026-10-10)

- `POST /users` creates a new user. Rate limit: 10 req/min per user.
- Request: `{"email": "alice@example.com", "name": "Alice"}`
- Response: `{"user_id": "user_123", "email": "alice@example.com", "name": "Alice"}`
- Errors: 422 (missing field), 429 (rate limit exceeded).
```

**The handoff note:**

```markdown
## Handoff note: `/users` endpoint

- Added `service/users.py` with the `POST /users` endpoint.
- Added `tests/test_users.py` with 4 tests.
- The endpoint uses the existing `RateLimiter` and `MetricsRegistry`.
- The endpoint matches the existing patterns: `request_id` in response, JSON logging, rate-limit before LLM call.
- The next engineer should add the `GET /users/{user_id}` endpoint + the `DELETE /users/{user_id}` endpoint using the same patterns.
```

### Phase 3: Tests + Polish (20 minutes)

**The 3 things to add:**

1. **Edge case: handle duplicate email.** Add a check in the code: if the email already exists, return 409 Conflict.
2. **Edge case: handle long name.** Add a max length check on the name field.
3. **Edge case: handle special characters in email.** Add a regex check on the email field.

**The final review:**

- Run `pytest` → 9/9 passing (5 existing + 4 new).
- Read the README out loud → 60 seconds.
- Walk through the handoff note → 30 seconds.

---

## The 3 AI assistant patterns for brownfield

### Pattern 1: "AI as a codebase explorer"

You're in a new codebase. You use the AI to ask "what does this function do?" and "where is the rate limiter implemented?" You build a mental model.

**The risk:** the AI hallucinates the codebase structure. Verify by reading the actual code.

**The example prompts:**

- "What does the `HybridRetriever` class do?"
- "Where is the rate limiter implemented?"
- "How does the circuit breaker work?"
- "What's the data flow for the `/draft` endpoint?"

### Pattern 2: "AI as a code reviewer"

You write the feature. You use the AI to review the code: "Does this match the existing patterns?" "Are there any bugs?" "What's the time complexity?"

**The risk:** the AI proposes changes that don't match the existing patterns. Verify by reading the existing code.

**The example prompts:**

- "Does this endpoint match the existing patterns?"
- "Are there any edge cases I'm missing?"
- "What's the time complexity of this function?"

### Pattern 3: "AI as a test generator"

You write the feature. You use the AI to generate test cases: "What are the edge cases for this function?" "What are the failure modes?"

**The risk:** the AI generates tests that don't match the existing test patterns. Verify by reading the existing tests.

**The example prompts:**

- "What are the edge cases for this function?"
- "What are the failure modes?"
- "Generate 3 test cases for this endpoint."

---

## The 5 anti-patterns

1. **Skipping the exploration phase.** "I'll just start coding" is a junior answer. The mental model is the FDE signal.
2. **Trusting the AI's code without verification.** The AI generates code that looks right. The bug is in the line you didn't read.
3. **Writing code in a different style.** The new code should match the existing patterns. If it doesn't, the next engineer will be confused.
4. **Skipping the regression check.** The existing tests should pass. If they don't, you broke something.
5. **Going over time.** 90 minutes is 90 minutes. Practice with a timer.

---

## The cross-reference: how this maps to Phase 6

| Phase | The FDE skill it proves |
|---|---|
| `../take-home/01-prototype.md` | The 4-hour build plan (the same pattern, compressed) |
| `../swe-coding/README.md` | The 8 SWE patterns (the foundation for the code) |
| `../practical-coding/01-build-new-project.md` | The 5 deliverables (the same list) |

---

## The thesis

**Extend a codebase is the second most common practical-coding sub-round.** The candidate who reads the codebase first, uses the AI to explore, and adds a feature that matches the existing patterns — is showing they can ship in a brownfield environment.

**The 3-phase plan (20 min explore + 50 min implement + 20 min polish) is the muscle memory.** The 5 deliverables (feature + tests + README + regression + handoff) are the FDE signal. The 3 AI patterns (explorer + reviewer + test generator) are the meta-signal.

**General prep gets you past the resume screen. Practical-coding prep gets you past the centerpiece round at Meta, Anthropic, and OpenAI.**