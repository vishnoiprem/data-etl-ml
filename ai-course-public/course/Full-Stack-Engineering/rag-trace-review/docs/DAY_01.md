# Day 1 — How Full-Stack Applications Work
## RAG Trace Review Platform — Day 1 of 21

**Today's goal:** by the end of this lesson you can explain, draw, and build the bones of a full-stack app. We start with the smallest possible FastAPI server that returns JSON, then end with a working `GET /traces` endpoint.

**Time budget (90 min):**
- 10 min simple explanation
- 20 min technical concepts
- 30 min coding
- 20 min debugging & tests
- 20 min mock interview practice

---

## Part 1 — Simple explanation (10 min)

### Analogy for a 12-year-old

You walk into a restaurant.

- **The menu** is the website you see in your browser.
- **The waiter** is the API — it walks your question.
- **The kitchen** is the database — where the food (data) is stored.

The waiter doesn't cook. The kitchen doesn't take orders. The menu doesn't decide what's available. Each layer does one job, and they pass paper slips (JSON) between each other.

A "full-stack developer" is the person who can build any of them, and knows how the layers talk.

---

## Part 2 — Technical concepts (20 min)

### What is HTTP?

HTTP is a **request-response protocol**. The client (browser) sends a request, the server sends a response.

```
GET /traces HTTP/1.1
Host: localhost:8000
```

```
HTTP/1.1 200 OK
Content-Type: application/json

{"items": [...], "meta": {...}}
```

### Status codes you must know

| Code | Meaning | Example |
|---|---|---|
| 200 | OK | success |
| 201 | Created | POST succeeded |
| 204 | No Content | DELETE succeeded |
| 400 | Bad Request | malformed JSON |
| 404 | Not Found | unknown trace_id |
| 422 | Unprocessable Entity | JSON is fine but values are wrong |
| 500 | Server Error | bug in the API |

### What is JSON?

JSON is text that looks like a JavaScript object.

```json
{
  "trace_id": "trace_000001",
  "latency_ms": 245,
  "feedback": "up"
}
```

### What is REST?

REST is a *convention* for designing endpoints.
- **Nouns** are in the URL: `/traces`, `/traces/{id}`
- **Verbs** are the HTTP method: GET (read), POST (create), PUT (replace), PATCH (partial), DELETE (remove)

### Request lifecycle

1. User clicks a link in the browser.
2. Browser opens a TCP connection to the server.
3. Browser sends `GET /traces` over the wire.
4. Server (FastAPI) routes the URL to your function.
5. Your function talks to the database, builds JSON, returns it.
6. Server sends `200 OK` + JSON back.
7. Browser parses JSON, renders React components.

### Why this problem exists

Web developers needed a way for the *front* (what users see) and the *back* (where data lives) to communicate **without coupling**. JSON + REST is the lowest-common-denominator contract: any language on the client, any language on the server.

---

## Part 3 — Setup commands for Apple Silicon macOS

```bash
# 1. Open the project
cd /Users/pvishnoi/PycharmProjects/data-etl-ml/ai-course-public/course/Full-Stack-Engineering/rag-trace-review

# 2. Backend virtualenv + install
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Seed the database (creates rag_traces.db with 10,000 rows)
python seed.py

# 4. Start the API
uvicorn app.main:app --reload --port 8000
```

**Expected output (last lines):**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

Open **http://localhost:8000/docs** to see the auto-generated OpenAPI explorer.

---

## Part 4 — Code walkthrough: today's runnable files

### File 1: `app/database.py`

```python
"""SQLite connection management."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
import os

DB_PATH = os.environ.get("RAG_DB_PATH", str(Path(__file__).parent.parent / "rag_traces.db"))


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


@contextmanager
def db_cursor(commit: bool = False):
    conn = get_connection()
    try:
        cur = conn.cursor()
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with db_cursor(commit=True) as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS traces (
                trace_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                prompt_version TEXT NOT NULL,
                user_query TEXT NOT NULL,
                prompt TEXT NOT NULL,
                retrieved_chunks TEXT NOT NULL,
                model_response TEXT NOT NULL,
                citations TEXT NOT NULL,
                token_usage INTEGER NOT NULL,
                latency_ms INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'ok',
                feedback TEXT
            )
        """)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_traces_created_id "
            "ON traces(created_at DESC, trace_id DESC)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_traces_prompt_version "
            "ON traces(prompt_version)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_traces_latency "
            "ON traces(latency_ms)"
        )
        cur.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trace_id TEXT NOT NULL,
                rating TEXT NOT NULL CHECK (rating IN ('up','down')),
                note TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(trace_id),
                FOREIGN KEY(trace_id) REFERENCES traces(trace_id)
            )
        """)
```

**Line by line:**

- `DB_PATH = os.environ.get(...)` — env var override so tests can use a temp DB.
- `get_connection()` — opens a new connection. WAL mode lets readers and writers not block each other.
- `row_factory = sqlite3.Row` — rows become dict-like.
- `@contextmanager` + `with db_cursor()` — guarantees `close()` runs even on exceptions.
- `init_db()` — `CREATE TABLE IF NOT EXISTS` is idempotent; safe to call on every startup.
- The composite index `(created_at DESC, trace_id DESC)` matches our cursor pagination `ORDER BY`.

### File 2: `app/main.py`

```python
"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db
from .routes.traces import router as traces_router
from .routes.feedback import router as feedback_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="RAG Trace Review API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(traces_router)
app.include_router(feedback_router)


@app.get("/health")
def health():
    return {"status": "ok"}
```

**Line by line:**
- `lifespan` is the modern replacement for the deprecated `on_event("startup")`. The code before `yield` runs at startup; after `yield` runs at shutdown.
- `CORSMiddleware` lets the browser on `:5173` call the API on `:8000`. Without this, the browser blocks the request.
- `include_router` mounts our route modules under their prefixes.
- `/health` is for load balancers and uptime monitors.

### File 3: `app/routes/traces.py` — **the heart of Day 1**

```python
"""Cursor-paginated trace listing + detail endpoints."""
import base64
import os
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from ..database import db_cursor
from ..models import (
    TraceSummary, TraceDetail, RetrievedChunk, Citation,
    TracePage, PageMeta,
)

router = APIRouter(prefix="/traces", tags=["traces"])

PAGE_SIZE = int(os.environ.get("RAG_PAGE_SIZE", 50))
MAX_PAGE_SIZE = 200


def _encode_cursor(created_at: str, trace_id: str) -> str:
    raw = f"{created_at}|{trace_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _decode_cursor(cursor: str) -> tuple[str, str]:
    try:
        decoded = base64.urlsafe_b64decode(cursor.encode()).decode()
        created_at, trace_id = decoded.split("|", 1)
        return created_at, trace_id
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid cursor") from exc


@router.get("", response_model=TracePage)
def list_traces(
    day: Optional[str] = Query(None, description="YYYY-MM-DD"),
    prompt_version: Optional[str] = Query(None),
    min_latency: Optional[int] = Query(None, ge=0),
    max_latency: Optional[int] = Query(None, ge=0),
    cursor: Optional[str] = Query(None),
    limit: int = Query(PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
):
    where: list[str] = []
    params: list = []
    if day:
        where.append("substr(created_at, 1, 10) = ?")
        params.append(day)
    if prompt_version:
        where.append("prompt_version = ?")
        params.append(prompt_version)
    if min_latency is not None:
        where.append("latency_ms >= ?")
        params.append(min_latency)
    if max_latency is not None:
        where.append("latency_ms <= ?")
        params.append(max_latency)
    if cursor:
        c_at, c_id = _decode_cursor(cursor)
        where.append("(created_at < ? OR (created_at = ? AND trace_id < ?))")
        params.extend([c_at, c_at, c_id])

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    sql = f"""
        SELECT trace_id, created_at, prompt_version, user_query,
               token_usage, latency_ms, status, feedback
        FROM traces
        {where_sql}
        ORDER BY created_at DESC, trace_id DESC
        LIMIT ?
    """
    params.append(limit + 1)
    with db_cursor() as cur:
        rows = cur.execute(sql, params).fetchall()

    has_more = len(rows) > limit
    rows = rows[:limit]
    items = [TraceSummary(**dict(r)) for r in rows]
    next_cursor = None
    if has_more and rows:
        last = rows[-1]
        next_cursor = _encode_cursor(last["created_at"], last["trace_id"])
    return TracePage(items=items, meta=PageMeta(next_cursor=next_cursor, has_more=has_more))


@router.get("/{trace_id}", response_model=TraceDetail)
def get_trace(trace_id: str):
    with db_cursor() as cur:
        row = cur.execute("SELECT * FROM traces WHERE trace_id = ?", (trace_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Trace not found: {trace_id}")
    d = dict(row)
    import json
    d["retrieved_chunks"] = [RetrievedChunk(**c) for c in json.loads(d["retrieved_chunks"])]
    d["citations"] = [Citation(**c) for c in json.loads(d["citations"])]
    return TraceDetail(**d)
```

**Line by line:**
- `_encode_cursor` and `_decode_cursor` — opaque base64 of `"created_at|trace_id"`. Clients treat them as black boxes; we can change the format later.
- `Query(None, ge=0)` — FastAPI parses URL query params and validates them. `ge=0` enforces "≥ 0".
- The cursor's WHERE fragment `(created_at < ? OR (created_at = ? AND trace_id < ?))` is **the heart of keyset pagination**.
- `LIMIT ?` with `limit + 1` lets us know if there's another page without a second query.
- `has_more` and `next_cursor` together give you the full state machine for an infinite list.

---

## Part 5 — Sample input and expected output

### Input

```bash
curl "http://localhost:8000/traces?limit=2&prompt_version=v2.0"
```

### Expected output

```json
{
  "items": [
    {
      "trace_id": "trace_009842",
      "created_at": "2026-01-30T18:33:21+00:00",
      "prompt_version": "v2.0",
      "user_query": "How does RAG work?",
      "token_usage": 1820,
      "latency_ms": 540,
      "status": "ok",
      "feedback": "up"
    },
    {
      "trace_id": "trace_009120",
      "created_at": "2026-01-30T15:10:02+00:00",
      "prompt_version": "v2.0",
      "user_query": "What is chunking?",
      "token_usage": 980,
      "latency_ms": 220,
      "status": "ok",
      "feedback": null
    }
  ],
  "meta": {
    "next_cursor": "MjAyNi0wMS0zMFQxNToxMDowMiswMHx0cmFjZV8wMDkxMjA=",
    "has_more": true
  }
}
```

### Pagination — second request

```bash
curl "http://localhost:8000/traces?limit=2&prompt_version=v2.0&cursor=MjAyNi0wMS0zMFQxNToxMDowMiswMHx0cmFjZV8wMDkxMjA="
```

You get the *next* 2 rows. The cursor walks forward, deterministically.

---

## Part 6 — Common bugs and how to debug them

### Bug 1: `ModuleNotFoundError: No module named 'fastapi'`

**Cause:** venv not active, or you installed in a different venv.
**Fix:** `source .venv/bin/activate`, then `pip install -r requirements.txt`.

### Bug 2: `sqlite3.OperationalError: no such table: traces`

**Cause:** You didn't run `python seed.py` and the DB is brand-new with no tables.
**Fix:** `python seed.py`. The script calls `init_db()` and inserts rows.

### Bug 3: CORS error in browser console

```
Access to fetch at 'http://localhost:8000/traces' from origin 'http://localhost:5173'
has been blocked by CORS policy
```

**Cause:** Your browser is on `:5173` and our `allow_origins` doesn't include that port.
**Fix:** Check `app/main.py`. We already allow `http://localhost:5173`. If you used a different port, add it.

### Bug 4: `Invalid cursor` 400

**Cause:** Manually edited the cursor, or it expired (we don't expire them, but you might have hand-crafted one).
**Fix:** Drop the cursor and request the first page again.

### Bug 5: `uvicorn` not found

**Cause:** forgot to activate venv.
**Fix:** `source .venv/bin/activate`.

---

## Part 7 — Unit tests (today's tests)

The tests are in `backend/tests/test_traces.py`. We have **14 passing tests** that cover:

1. Health endpoint
2. List ordering (newest first)
4. Cursor pagination walks all rows
5. Invalid cursor → 400
6. Day filter
7. Prompt-version filter
8. Latency range filter
9. Trace detail
10. 404 on unknown trace
11. Feedback submit
12. Feedback idempotency (PUT twice)
13. Invalid rating → 422
14. 404 on feedback for unknown trace
15. Combined cursor + filter
16. Concurrent feedback upsert

**Run them:**
```bash
cd /Users/pvishnoi/PycharmProjects/data-etl-ml/ai-course-public/course/Full-Stack-Engineering/rag-trace-review/backend
source .venv/bin/activate
pytest -q
```

**Expected:**
```
14 passed in 0.15s
```

---

## Part 8 — Performance and maintainability tradeoffs

### Why keyset pagination?

| | OFFSET | Cursor (chosen) |
|---|---|---|
| Speed on 10k rows | Linear (slow) | Logarithmic (fast) |
| Stable under inserts | No | Yes (mostly) |
| Implementation | High (easy) | Medium (cursor logic) |
| Index requirement | None | Composite `(created_at DESC, trace_id DESC)` |
| Random access (jump to page 7) | High | Low (must chain) |

We chose cursor because the dataset is large, the user mostly scrolls forward, and rows can be inserted (new traces).

### Why SQLite?

- Zero-config.
- Single file you can `cp` to backup.
- Surprisingly fast for read-heavy workloads up to ~1M rows.
- No server process.

Tradeoff: doesn't scale to multiple machines. For multi-host, swap to Postgres later. The SQL we wrote is portable.

### Why Pydantic over dataclasses?

- Validates input automatically → 422 with clear errors.
- Generates OpenAPI docs.
- Serializes to JSON for free.

---

## Part 9 — Five Meta-style interview questions

### Q1 — "Walk me through what happens when a user opens our app."

> **Strong answer:** "The browser loads the React bundle. `main.tsx` mounts `App`. App hits `/traces` over the network. FastAPI's router resolves the URL, the route handler builds a SQL query with cursor + filters, SQLite returns rows, FastAPI serializes them into Pydantic models, returns JSON. React Query caches the result. The component renders rows through the virtualizer, which only mounts the visible ones. Total round-trip ~200ms; perceived load is faster because the virtualizer renders before all rows arrive."

### Q2 — "Why did you choose cursor pagination over OFFSET?"

> "Two reasons. First, performance: OFFSET makes the database scan and discard rows on every page request — at 10k rows it's already slow, at 1M it's unusable. Cursor uses the index directly and runs in O(log n). Second, stability: if a new row is inserted while the user scrolls, OFFSET skips or duplicates rows. Cursor continues from where it left off. The tradeoff is you can't jump to page 7 — you have to chain. That's acceptable for a trace viewer."

### Q3 — "How do you know if there's another page?"

> "I ask for `limit + 1` rows. If I get back `limit + 1`, there is a next page; I drop the extra and encode the *last* row's `(created_at, trace_id)` as the next cursor. If I get back `limit` or fewer, `has_more = False` and `next_cursor = None`. This avoids a second `SELECT count(*)` query, which would be expensive on a large table."

### Q4 — "What's the difference between 400 and 422?"

> "400 Bad Request means the request itself is malformed — say, the HTTP body isn't valid JSON, or the URL is broken. 422 Unprocessable Entity means the request is well-formed but semantically wrong — say, `{"rating": "meh"}` where we expected `"up"` or `"down"`. Pydantic gives us 422 for free when we declare `Field(pattern='^(up|down)$')`. We use 400 only for bad cursors because those aren't validated by a model."

### Q5 — "How would you test pagination boundaries? Be specific."

> "Three boundaries. First, **empty**: request with a filter that matches zero rows, expect `items=[]`, `has_more=false`, `next_cursor=null`. Second, **single page**: request with `limit` larger than total rows, expect all rows back, `has_more=false`. Third, **last page partial**: walk through pages with `limit=1` and confirm (a) every row is returned exactly once, (b) the order is deterministic, (c) the loop terminates after the expected number of pages. I'd add a test that inserts a row *between* page 1 and page 2 to confirm we don't see it twice."

---

## Part 10 — Coding assignment

> **Goal:** Add a `GET /traces/{id}/chunks` endpoint that returns just the retrieved chunks for a trace.

### Requirements

1. Returns `{ "chunks": [...] }` with HTTP 200 on success.
2. Returns 404 if the trace doesn't exist.
3. Include a unit test that asserts the response shape and the 404 path.

### Scoring rubric (0–10)

- 0: nothing runs
- 4: returns chunks for an existing trace
- 6: handles 404
- 8: tests pass; response model declared
- 10: Pydantic-typed response, included in OpenAPI, no N+1 query

### Solution

```python
# backend/app/routes/traces.py — add at the bottom
from fastapi import Response

@router.get("/{trace_id}/chunks")
def get_trace_chunks(trace_id: str):
    with db_cursor() as cur:
        row = cur.execute(
            "SELECT retrieved_chunks FROM traces WHERE trace_id = ?",
            (trace_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Trace not found: {trace_id}")
    import json
    chunks = json.loads(row["retrieved_chunks"])
    return {"chunks": chunks}
```

### Test

```python
def test_get_trace_chunks(client, seed):
    r = client.get("/traces/t001/chunks")
    assert r.status_code == 200
    assert "chunks" in r.json()


def test_get_trace_chunks_404(client, seed):
    r = client.get("/traces/nope/chunks")
    assert r.status_code == 404
```

---

## Part 11 — Day 1 wrap-up

✅ You can describe the request lifecycle end-to-end.
✅ You can run the backend and hit it.
✅ You understand cursor pagination at the SQL level.
✅ You have 14 passing tests.
✅ You answered (or attempted) 5 interview questions.

**Tomorrow (Day 2):** JavaScript and TypeScript — variables, async/await, generics, discriminated unions, and how TypeScript catches the bugs that JavaScript would let through.

**Time spent: ~90 min**
**Score for today: rate yourself 0–10 on the rubric in the master prompt.**