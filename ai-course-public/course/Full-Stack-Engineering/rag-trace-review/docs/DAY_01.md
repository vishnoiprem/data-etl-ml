# Day 1 — How Full-Stack Applications Work
**Module 1** | Total: 90 min (10 + 20 + 30 + 20 + 20)

---

## 1. Simple explanation (10 min)

**Analogy for a 12-year-old:**
You walk into a restaurant.
- The **menu** in your hand is the browser.
- The **waiter** is the API.
- The **kitchen** is the database.

The waiter doesn't cook. The kitchen doesn't take orders. Each layer does one job. They pass paper slips (JSON) between each other. A "full-stack developer" is the person who can build any of those layers and knows how they talk.

**Three sentences to remember:**
1. The browser shows things.
2. The API answers questions.
3. The database remembers.

---

## 2. Technical concepts (20 min)

| Term | Meaning |
|---|---|
| Browser | Renders HTML/CSS/JS for the user |
| Frontend | JavaScript/TypeScript that runs in the browser |
| Backend | Server code that handles requests and talks to a DB |
| Database | Persistent storage (SQLite, Postgres, etc.) |
| HTTP | Request-response protocol between client and server |
| HTTPS | HTTP encrypted with TLS |
| JSON | Text format that looks like a JS object |
| REST | Convention: nouns in URLs, verbs are HTTP methods |
| Request lifecycle | Browser → DNS → TCP → HTTP → server → response |
| Status codes | 2xx ok, 3xx redirect, 4xx client error, 5xx server error |

**Status codes you MUST know cold:**

| Code | Meaning | Example |
|---|---|---|
| 200 | OK | success |
| 201 | Created | POST succeeded |
| 204 | No Content | DELETE succeeded |
| 400 | Bad Request | malformed JSON |
| 404 | Not Found | unknown id |
| 422 | Unprocessable Entity | well-formed but semantically wrong |
| 500 | Server Error | unhandled exception |

**Client/server architecture:** the server is a long-running process listening on a port. Each request is independent. The server is stateless between requests unless it stores state (session, DB).

---

## 3. Coding (30 min)

### Goal: smallest possible FastAPI server returning JSON.

**Setup (Apple Silicon macOS):**
```bash
cd /Users/pvishnoi/PycharmProjects/data-etl-ml/ai-course-public/course/Full-Stack-Engineering/rag-trace-review/backend
source .venv/bin/activate
python seed.py          # creates rag_traces.db with 10,000 rows
uvicorn app.main:app --reload --port 8000
```

**Expected output (last lines):**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

Open **http://localhost:8000/docs** to see auto-generated OpenAPI.

**Try with curl:**
```bash
curl http://localhost:8000/health
# {"status":"ok"}

curl "http://localhost:8000/traces?limit=2"
# {"items":[...], "meta":{"next_cursor":"...","has_more":true}}
```

### Sample input
```bash
curl "http://localhost:8000/traces?limit=2&prompt_version=v1.0"
```

### Expected output
```json
{
  "items": [
    {"trace_id":"trace_000123","created_at":"2026-01-12T08:11:00+00:00",
     "prompt_version":"v1.0","user_query":"What is RAG?",
     "token_usage":1200,"latency_ms":180,"status":"ok","feedback":"up"},
    {"trace_id":"trace_000124", "...":"..."}
  ],
  "meta": {"next_cursor": "MjAyNi0wMS0xMnQwODoxMT...=", "has_more": true}
}
```

### Line-by-line walkthrough of `app/main.py`
- `lifespan` — runs `init_db()` once at startup.
- `CORSMiddleware` — lets the React app on `:5173` call the API on `:8000`.
- `include_router` — mounts each route module.
- `@app.get("/health")` — load balancer probe.

---

## 4. Debugging & tests (20 min)

### Bug 1: `ModuleNotFoundError: No module named 'fastapi'`
**Cause:** venv not active.
**Fix:** `source .venv/bin/activate`, then `pip install -r requirements.txt`.

### Bug 2: `sqlite3.OperationalError: no such table: traces`
**Cause:** DB is brand-new, no tables yet.
**Fix:** run `python seed.py` (it calls `init_db()`).

### Bug 3: CORS error in browser console
**Symptom:** `Access to fetch ... has been blocked by CORS policy`.
**Fix:** add your origin to `allow_origins` in `app/main.py`.

### Bug 4: 404 on a known trace
**Cause:** stale id from a previous DB.
**Fix:** re-seed: `python seed.py`.

### Run the tests
```bash
cd /Users/pvishnoi/PycharmProjects/data-etl-ml/ai-course-public/course/Full-Stack-Engineering/rag-trace-review/backend
source .venv/bin/activate
pytest -q
```

**Expected:** `14 passed in 0.15s`

---

## 5. Mock interview practice (20 min)

**Q1 — "Walk me through what happens when a user opens our app."**
> The browser loads the React bundle, mounts `App`, which calls `/traces`. FastAPI routes the URL, runs the cursor query, returns JSON. React Query caches it. The virtualizer renders only visible rows. Round-trip ~200ms; perceived faster because the virtualizer paints before all rows arrive.

**Q2 — "Why is the API on a different port from the frontend?"**
> They're independent processes. The browser uses CORS to allow the cross-origin request. In production a reverse proxy (Nginx) terminates both on the same domain.

**Q3 — "What's the difference between authentication and authorization?"**
> Authentication is "who are you?"; authorization is "what are you allowed to do?". We have neither yet (Day 14).

**Q4 — "What is a status code 422?"**
> Well-formed request, semantically wrong. Pydantic raises it automatically when validation fails. We use 400 only for invalid cursors.

**Q5 — "How do you know if a request is idempotent?"**
> Calling it N times gives the same observable effect as calling it once. GET, PUT, DELETE are idempotent. POST is not.

---

## 6. Success criteria check (Day 1)

By end of today you can:
- [ ] Describe the request lifecycle end-to-end
- [ ] Run the backend and `curl` every endpoint
- [ ] Open the OpenAPI explorer
- [ ] Explain the 3 status code families
- [ ] Run `pytest -q` and see 14/14 pass

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

**Pass mark:** ≥ 56/80. Aim for ≥ 64/80.

---

## 8. Coding assignment (graded)

**Add `GET /traces/{id}/chunks` returning `{"chunks": [...]}`.** Return 404 if missing. Add tests for the 200 and 404 paths.

### Rubric (0–10)
- 0: doesn't run
- 4: returns chunks
- 6: handles 404
- 8: Pydantic response model + test
- 10: Pydantic-typed, no N+1, OpenAPI visible, edge case test

### Solution
```python
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
    return {"chunks": json.loads(row["retrieved_chunks"])}
```

---

**Time: 90 min — finish the assignment before Day 2.**
