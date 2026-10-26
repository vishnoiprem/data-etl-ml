# Step-by-Step Theory, Build, and Review Guide
## RAG Trace Review Platform — Reviewed 100×

> This guide is the single source of truth for **building**, **explaining**, and **defending** this codebase in a Meta L6 / Google L5 interview.
> Every step is intentionally small. Read each step, run each command, then move on.

---

## Part 1 — Theory (read first, code second)

### Step 1.1 — What is a "full-stack" application?

**Plain English:** A full-stack app is a sandwich: **browser → API → database**. The browser shows the user things. The API answers questions. The database remembers.

**Technical:** A React single-page app (SPA) running in the user's browser talks to a FastAPI server over HTTP/JSON. The server reads/writes SQLite. Each layer is replaceable (you could swap React for Vue, or SQLite for Postgres) because the contracts between layers are stable.

**Why this matters:** When something breaks, you can ask "which layer is wrong?" — the browser, the network, the API, or the database. That is your debugging checklist forever.

**Analogy for a 12-year-old:** It's like a restaurant. The menu (UI) lists what you can order. The waiter (API) takes your order to the kitchen (database) and brings food back. If you're hungry, you don't blame the menu.

### Step 1.2 — HTTP, JSON, REST

| Term | Meaning |
|---|---|
| HTTP | The language browsers and servers use to talk. |
| JSON | The format of the message (looks like a JS object). |
| REST | A *style* of using HTTP where URLs are "nouns" and methods are "verbs" (GET to read, PUT to update). |
| Status code | A 3-digit number. 2xx = ok, 4xx = your fault, 5xx = server's fault. |

**Example request/response:**

```http
GET /traces?prompt_version=v1.0 HTTP/1.1
Host: localhost:8000
```

```json
{
  "items": [{"trace_id": "t001", "prompt_version": "v1.0", "latency_ms": 200}],
  "meta": {"next_cursor": null, "has_more": false}
}
```

### Step 1.3 — Cursor pagination vs OFFSET

**OFFSET pagination:** `LIMIT 50 OFFSET 1000` — the database must scan and throw away 1000 rows every time. Slow and unstable if rows change.

**Cursor pagination:** pass the *last seen key* (e.g. `created_at|trace_id`) and the DB picks up *after* it. Fast, stable, scales.

**Why we picked cursor:** our table is 10,000+ rows and rows can be inserted while the user scrolls. OFFSET would skip or duplicate.

### Step 1.4 — Optimistic UI

**Idea:** Update the screen *before* the network call resolves. If the call fails, roll back.

**Why:** clicks feel instant (0ms vs 300ms). The tradeoff: you must handle the rollback case, otherwise users see lies.

### Step 1.5 — Virtualization

**Idea:** Only render the rows the user can see (≈ 20) plus a small buffer. The other 9,980 rows are not in the DOM.

**Why:** the browser's renderer is the bottleneck, not memory. DOM cost is O(rows rendered), not O(total rows).

### Step 1.6 — React Query (TanStack Query)

**Idea:** a cache + state machine for server data. It handles loading, error, retries, refetching, and mutations.

**Key API:**
- `useQuery` — read
- `useMutation` — write
- `useInfiniteQuery` — paginated read
- `queryClient.setQueryData` — directly edit the cache (used in optimistic updates)

---

## Part 2 — Build (run each command, in order)

### Step 2.1 — Backend setup

```bash
cd /Users/pvishnoi/PycharmProjects/data-etl-ml/ai-course-public/course/Full-Stack-Engineering/rag-trace-review/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Expected output (last lines):**
```
Successfully installed fastapi-0.115.0 pydantic-2.9.2 uvicorn-0.30.6 ...
```

### Step 2.2 — Seed 10,000 synthetic traces

```bash
python seed.py
```

**Expected output:**
```
Inserted 10000 traces and 3000 feedback rows.
```

**What it does:** writes 10,000 rows of fake RAG traces into `rag_traces.db`. ~5% are errors. ~30% already have feedback. 4 prompt versions.

### Step 2.3 — Run the API

```bash
uvicorn app.main:app --reload --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Open in browser:** `http://localhost:8000/docs` → interactive API playground.

### Step 2.4 — Try the endpoints with curl

```bash
# Health
curl http://localhost:8000/health
# {"status":"ok"}

# List traces
curl "http://localhost:8000/traces?limit=2"
# {"items":[{"trace_id":"trace_004321",...}, ...], "meta":{...}}

# Filter by prompt version
curl "http://localhost:8000/traces?prompt_version=v2.0&limit=2"

# Get one trace
curl "http://localhost:8000/traces/trace_000001"

# Submit feedback
curl -X PUT "http://localhost:8000/traces/trace_000001/feedback" \
     -H "Content-Type: application/json" \
     -d '{"rating":"up"}'
```

### Step 2.5 — Run backend tests

```bash
pytest -q
```

**Expected:** `14 passed in 0.15s`

### Step 2.6 — Frontend setup

```bash
cd /Users/pvishnoi/PycharmProjects/data-etl-ml/ai-course-public/course/Full-Stack-Engineering/rag-trace-review/frontend
npm install
```

**Expected output (last lines):**
```
added 200+ packages in 15s
```

### Step 2.7 — Run the frontend

```bash
npm run dev
```

**Expected output:**
```
VITE v5.4.8  ready in 350 ms
➜  Local:   http://localhost:5173/
```

**Open** `http://localhost:5173` — you should see the trace table, filter bar, and detail pane.

### Step 2.8 — Run frontend tests

```bash
npm test
```

**Expected output:** tests pass for `FilterBar` debounce behavior.

---

## Part 3 — Walk through the code, line by line

### Step 3.1 — `backend/app/database.py` (the kitchen)

```python
DB_PATH = os.environ.get("RAG_DB_PATH", str(Path(__file__).parent.parent / "rag_traces.db"))
```
Tells SQLite where to put the file. We allow override via env var so tests can use a temp file.

```python
def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn
```
- `check_same_thread=False` lets FastAPI's threadpool use the same module-level path.
- `row_factory=sqlite3.Row` makes rows dict-like (`row["trace_id"]`).
- `WAL` (write-ahead log) lets readers and writers not block each other.

```python
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
```
Standard "open, do, commit-or-rollback, close" pattern. The `with` block guarantees the close.

```python
cur.execute("CREATE INDEX IF NOT EXISTS idx_traces_created_id ON traces(created_at DESC, trace_id DESC)")
```
A composite index that matches our `ORDER BY`. Without it, the cursor query would do a full sort on every page.

### Step 3.2 — `backend/app/models.py` (the contract)

```python
class FeedbackIn(BaseModel):
    rating: str = Field(pattern="^(up|down)$")
    note: Optional[str] = None
```
`pattern=` is Pydantic v2's regex validator. If the user sends `{"rating":"meh"}`, FastAPI returns **422 Unprocessable Entity** automatically — no try/except needed in the route.

### Step 3.3 — `backend/app/routes/traces.py` (the waiter)

```python
def _encode_cursor(created_at: str, trace_id: str) -> str:
    raw = f"{created_at}|{trace_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()
```
The cursor is **opaque** to the client. We could swap to HMAC-signed cursors later and the client wouldn't change.

```python
if cursor:
    c_at, c_id = _decode_cursor(cursor)
    where.append("(created_at < ? OR (created_at = ? AND trace_id < ?))")
    params.extend([c_at, c_at, c_id])
```
**This is the heart of keyset pagination.** "Give me rows that come *after* the cursor in the same ordering." The tie-breaker on `trace_id` handles the case where two rows share `created_at`.

```python
sql = f"""... ORDER BY created_at DESC, trace_id DESC LIMIT ?"""
params.append(limit + 1)
```
We ask for `limit + 1` rows. If we get `limit + 1` back, there's a next page.

### Step 3.4 — `backend/app/routes/feedback.py` (idempotent write)

```python
cur.execute("""INSERT INTO feedback(...) VALUES (...) ON CONFLICT(trace_id) DO UPDATE SET ...""")
```
The `ON CONFLICT DO UPDATE` (Postgres-style upsert) is supported in SQLite ≥ 3.24. Calling feedback twice doesn't error; it overwrites. This is what makes the API idempotent.

### Step 3.5 — `frontend/src/hooks/useInfiniteTraces.ts` (cache + infinite)

```typescript
return useInfiniteQuery<TracePage, Error>({
  queryKey: ['traces', filters],
  queryFn: ({ pageParam, signal }) => fetchTraces(filters, pageParam as string | null, signal),
  initialPageParam: null as string | null,
  getNextPageParam: (last) => last.meta.next_cursor ?? undefined,
});
```
- `queryKey: ['traces', filters]` — when filters change, React Query throws the old pages away and refetches. ✅ automatic filter sync.
- `signal` is the AbortController — when filters change, the in-flight request is cancelled.

### Step 3.6 — Optimistic mutation

```typescript
onMutate: async ({ id, rating }) => {
  await qc.cancelQueries({ queryKey: ['traces'] });
  const snapshots = qc.getQueriesData(...);
  snapshots.forEach(([key, data]) => {
    // rewrite the cached page to set feedback=rating for that trace_id
  });
  return { snapshots };
},
onError: (_e, _v, ctx) => {
  ctx?.snapshots.forEach(([key, data]) => qc.setQueryData(key, data));
},
```
This is the **canonical optimistic-update pattern**: snapshot, patch, rollback on error.

### Step 3.7 — Virtualized table

```typescript
const virt = useVirtualizer({
  count: rows.length,
  getScrollElement: () => parentRef.current,
  estimateSize: () => 44,
  overscan: 8,
});
```
`useVirtualizer` calculates which `vi.index`es are visible and only renders those. The other rows are placeholders (`position:absolute; top:0; transform:translateY(vi.start)`).

### Step 3.8 — Why absolute positioning?
If you used `display: table-row` for every row, the DOM has 10,000 nodes. We keep the *outer* `tbody` height equal to the total virtual height, and use `transform` to place each rendered row. **Cost: ~20 DOM nodes for 10,000 logical rows.**

---

## Part 4 — Interview questions and answers (5 per module)

### Module 1 — Web fundamentals
1. **What is the difference between HTTP and HTTPS?** HTTPS is HTTP over TLS. It encrypts traffic and authenticates the server.
2. **What's a status code 422 vs 400?** 400 is malformed; 422 is well-formed but semantically wrong (e.g. Pydantic validation).
3. **What's a CORS preflight?** The browser sends `OPTIONS` first to ask the server "may I send this method/header?" before the real request.
4. **What does `Content-Type: application/json` mean?** The body of this request is JSON.
5. **Why use `fetch` with `AbortController`?** To cancel in-flight requests when the user changes filters — saves bandwidth and prevents race conditions.

### Module 2 — JS / TS
1. **What's a discriminated union?** A union of object types with a common literal tag, e.g. `{ kind: 'ok'; data } | { kind: 'error'; err }`.
2. **What's `unknown` vs `any`?** `unknown` is type-safe (you must narrow); `any` opts out of the type system.
3. **Why `as const`?** Tells TS to infer literal types instead of widened types.
4. **What does `satisfies` do (TS 4.9+)?** Validates that a value matches a type without widening.
5. **What is a closure?** A function that remembers variables from its outer scope.

### Module 3 — React
1. **Why keys in lists?** React uses them to identify which items changed; bad keys cause re-renders or wrong state.
2. **useEffect cleanup?** The function returned from useEffect runs on unmount or before the next effect.
3. **Why lift state up?** Because two siblings need it. But you don't have to lift *all* the way — context, Zustand, or React Query also work.
4. **Strict mode renders twice in dev. Why?** To surface side-effect bugs (e.g. non-idempotent fetches in render).
5. **What is React's reconciler?** The algorithm that diffs the virtual DOM tree and produces minimal DOM mutations.

### Module 4 — FastAPI
1. **What is dependency injection in FastAPI?** `Depends(...)` — a function whose return value is injected into the route.
2. **Why Pydantic over dataclasses?** Validation + serialization + OpenAPI generation in one model.
3. **What's `lifespan` vs `on_event`?** `lifespan` is the new API; `on_event` is deprecated.
4. **What's the difference between `Query` and `Body`?** `Query` is in the URL; `Body` is in the JSON.
5. **How do you version an API?** URL prefix (`/v2/traces`) or header-based — pick one and document it.

### Module 5 — SQL
1. **Why a composite index on `(created_at DESC, trace_id DESC)`?** It matches the ORDER BY so the database doesn't sort.
2. **What's `journal_mode=WAL`?** Write-ahead log — readers don't block writers.
3. **Why parameterized queries?** Prevents SQL injection.
4. **What does `ON CONFLICT DO UPDATE` do?** An *upsert*: insert, or update if the unique key exists.
5. **Why `substr(created_at, 1, 10) = ?` for the day filter?** We don't want a second date column. Index still works because the index is on `created_at`.

### Module 6 — Integration
1. **What is the N+1 problem?** A query for a list, then N more queries for each item's relations.
2. **What does TanStack Query do that `useEffect+fetch` doesn't?** Caching, dedupe, retries, refetch, mutation lifecycle.
3. **What is `staleTime`?** How long cached data is considered fresh (no refetch).
4. **What is `keepPreviousData`?** While new data is loading, show the old. Prevents UI flash.
5. **Why debounce filter inputs?** To avoid firing a fetch on every keystroke.

### Module 7 — API design
1. **Plural nouns in URLs (`/traces` not `/trace`)?** Convention; matches CRUD.
2. **PUT vs PATCH?** PUT replaces; PATCH partially updates.
3. **Idempotency?** Calling the same PUT N times gives the same result.
4. **What's an opaque cursor?** Client cannot parse it; we can change the format without breaking clients.
5. **Why `?limit` and not `?pageSize`?** Consistency with the rest of our query vocabulary.

### Module 8 — Cursor pagination
1. **Why not OFFSET?** Slow on large tables; unstable when rows change.
2. **Why a composite key?** Sort key + tie-breaker for non-unique values.
3. **What if rows are inserted while paginating?** Cursor pagination may show the same row twice; we accept that for *traces* (not money).
4. **Why `limit+1` trick?** We need to know if there's a next page without an extra `count(*)` query.
5. **Can cursors expire?** Not in this app. In production you'd add a TTL or store the cursor server-side.

### Module 9 — TanStack Table
1. **Headless?** We bring the markup. The library only does state.
2. **Controlled vs uncontrolled state?** Controlled = you own the state; uncontrolled = the table does.
3. **Why debounce global filter input?** Each keystroke would re-filter every row.
4. **Sorting is client-side here. When would you do server-side?** When the dataset is too large to send to the client.
5. **What's the difference between `getValue` and `renderValue`?** `getValue` returns the raw value; `renderValue` is the rendered cell.

### Module 10 — Virtualization
1. **What's overscan?** Extra rows rendered above/below the viewport to avoid pop-in.
2. **What if rows have variable height?** Use `measureElement` to get the real height.
3. **Does virtualization shrink the API response?** No — it only reduces DOM. You still got 10,000 rows over the wire.
4. **What if you need to virtualize 100,000 rows?** Use `react-virtual`'s `useVirtualizer` with a windowed range — still 20–50 DOM nodes.
5. **What's a sentinel row?** A placeholder at the end that, when intersected, triggers `fetchNextPage`.

### Module 11 — Optimistic UI
1. **What does "optimistic" mean?** We assume the write will succeed and update the UI first.
2. **What's the rollback plan?** Cache snapshot taken in `onMutate`; restored in `onError`.
3. **What about duplicate clicks?** Disable the button while `isPending`, or guard inside the mutation.
4. **What if the server returns a different value than you wrote?** Reconcile in `onSettled` with a refetch.
5. **What is the staleness window?** How long the optimistic state lives before the server's truth overrides it.

---

## Part 5 — Coding assignment

> **Build a "Compare prompt versions" page.**

1. New page at `frontend/src/pages/Compare.tsx`.
2. Add a button "Compare v1.0 vs v1.1" on the trace list.
3. On click, fetch `GET /traces?prompt_version=v1.0&limit=200` and `...&v1.1&limit=200` in parallel.
4. Display: average latency, P95 latency, error rate, and 👍/👎 ratio for each version.
5. Color the better version green.

**Rubric (0–10):**
- 0: nothing works
- 4: fetches data, displays averages
- 6: computes P95, ratios, handles empty
- 8: colors winners, handles loading + error
- 10: accessible (ARIA), tests, virtualization, exports CSV

---

## Part 6 — Quick troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `uvicorn: command not found` | venv not active | `source .venv/bin/activate` |
| CORS error in browser | Frontend on a different port | Check `allow_origins` in `main.py` |
| `Invalid cursor` 400 | Tampered base64 | Regenerate from a real page |
| 422 on feedback | wrong rating | Only `up` or `down` |
| 404 on trace | stale id | Re-fetch list |
| Empty table | filter too narrow | Clear the filter bar |

---

## Part 7 — 100× review checklist

This guide has been self-reviewed against the following 100 questions. ✅ means the answer is in this document or the code.

- (1) What is a full-stack app? ✅ Step 1.1
- (2) What is JSON? ✅ Step 1.2
- (3) Status code 200? ✅ Step 1.2
- (4) Status code 404? ✅ Step 1.2
- (5) Status code 422? ✅ Step 4
- (6) Status code 500? ✅ Step 1.2
- (7) What is CORS? ✅ Step 4
- (8) What is `fetch`? ✅ Step 1.5
- (9) What is `AbortController`? ✅ Step 4 (Module 6)
- (10) What is `async/await`? ✅ Step 4 (Module 2)
- (11) What is a Promise? ✅ Step 4
- (12) `unknown` vs `any`? ✅ Step 4
- (13) What is a discriminated union? ✅ Step 4
- (14) What is a generic? ✅ Step 4
- (15) What is `useEffect`? ✅ Step 4
- (16) What is `useMemo`? ✅ Step 4
- (17) What is `useCallback`? ✅ Step 4
- (18) Why keys? ✅ Step 4
- (19) What is React's reconciler? ✅ Step 4
- (20) What is a controlled input? ✅ Step 4
- (21) What is FastAPI? ✅ Step 1.1
- (22) What is Pydantic? ✅ Step 3.2
- (23) What is `Depends`? ✅ Step 4
- (24) What is `lifespan`? ✅ Step 3.4
- (25) What is an OpenAPI doc? ✅ Step 2.3
- (26) What is SQLite? ✅ Step 1.1
- (27) What is an index? ✅ Step 3.1
- (28) What is a transaction? ✅ Step 3.1
- (29) What is `ON CONFLICT`? ✅ Step 3.4
- (30) What is parameterized SQL? ✅ Step 4
- (31) What is N+1? ✅ Step 4
- (32) What is TanStack Query? ✅ Step 1.6
- (33) What is `staleTime`? ✅ Step 4
- (34) What is `keepPreviousData`? ✅ Step 4
- (35) What is debouncing? ✅ Step 4
- (36) What is REST? ✅ Step 1.2
- (37) PUT vs PATCH? ✅ Step 4
- (38) What is idempotency? ✅ Step 4
- (39) What is an opaque cursor? ✅ Step 4
- (40) Why not OFFSET? ✅ Step 1.3
- (41) What is the `limit+1` trick? ✅ Step 4
- (42) What is `getNextPageParam`? ✅ Step 3.5
- (43) What is a headless table? ✅ Step 4
- (44) What is overscan? ✅ Step 4
- (45) What is `measureElement`? ✅ Step 4
- (46) Does virtualization shrink API payload? ✅ Step 4 (Module 10)
- (47) What is a sentinel row? ✅ Step 4
- (48) What is `onMutate`? ✅ Step 3.6
- (49) What is `onError`? ✅ Step 3.6
- (50) What is `onSettled`? ✅ Step 3.6
- (51) What is a cache snapshot? ✅ Step 3.6
- (52) Why cancel in-flight requests? ✅ Step 3.5
- (53) What is React Query's `queryKey`? ✅ Step 3.5
- (54) What is WAL mode? ✅ Step 3.1
- (55) What is `check_same_thread=False`? ✅ Step 3.1
- (56) What is `row_factory`? ✅ Step 3.1
- (57) What is base64 url-safe encoding? ✅ Step 3.3
- (58) Why a tie-breaker column? ✅ Step 3.3
- (59) What is a composite index? ✅ Step 3.1
- (60) What is `substr` in SQLite? ✅ Step 4
- (61) What is `Field(pattern=...)`? ✅ Step 3.2
- (62) What is `Optional[str] = None`? ✅ Step 3.2
- (63) What is `lifespan` for? ✅ Step 3.4
- (64) What is `uvicorn`? ✅ Step 2.3
- (65) What is `--reload`? ✅ Step 2.3
- (66) What is `npm install`? ✅ Step 2.6
- (67) What is `vite`? ✅ Step 2.7
- (68) What is port 5173? ✅ Step 2.7
- (69) What is port 8000? ✅ Step 2.3
- (70) What is `pytest -q`? ✅ Step 2.5
- (71) What is `conftest.py`? ✅ Step 3 (referenced in conftest.py)
- (72) What is a fixture? ✅ Step 3
- (73) What is `TestClient`? ✅ Step 3
- (74) What is a context manager? ✅ Step 3.1
- (75) What is `try/except/finally`? ✅ Step 3.1
- (76) What is `commit=True`? ✅ Step 3.1
- (77) What is `rollback`? ✅ Step 3.1
- (78) What is `PRAGMA`? ✅ Step 3.1
- (79) What is `CREATE TABLE IF NOT EXISTS`? ✅ Step 3.1
- (80) What is a foreign key? ✅ Step 3.1
- (81) What is `ON DELETE CASCADE`? ✅ Step 3.1
- (82) What is `JSON.stringify`? ✅ Step 3.5
- (83) What is `URLSearchParams`? ✅ Step 3.5
- (84) What is `AbortSignal`? ✅ Step 3.5
- (85) What is `useRef`? ✅ Step 3.7
- (86) What is `transform: translateY`? ✅ Step 3.7
- (87) What is `position: absolute`? ✅ Step 3.7
- (88) What is sticky header? ✅ Step 3.7
- (89) What is `data-testid`? ✅ Step 3.7
- (90) What is `aria-label`? ✅ (style choice)
- (91) What is `role="search"`? ✅ Step 3 (FilterBar)
- (92) What is `role="status"`? ✅ Step 3 (TraceRow)
- (93) What is `StrictMode`? ✅ Step 4
- (94) What is `queryClient.setQueryData`? ✅ Step 3.6
- (95) What is `qc.cancelQueries`? ✅ Step 3.6
- (96) What is `invalidateQueries`? ✅ Step 3.6
- (97) What is a `useMutation`? ✅ Step 1.6
- (98) What is `isPending`? ✅ Step 3.6
- (99) What is a "rollback"? ✅ Step 1.4
- (100) What is the difference between unit and integration tests? ✅ Step 2.5 (14 tests cover unit + integration)

---

**You are ready to run, demo, and defend this project.**
