# Day 7 — API Design
**Module 7** | Total: 90 min (10 + 20 + 30 + 20 + 20)

---

## 1. Simple explanation (10 min)

**Analogy for a 12-year-old:**
A well-designed API is a **good vending machine**: clear buttons, expected snacks, change returned. A bad API is a phone tree from 2003 — you press 1, then 2, then wait for silence.

The contract — "here's what I take, here's what I give back" — is the whole job. Everything else is decoration.

---

## 2. Technical concepts (20 min)

- **Resource-oriented:** nouns in URLs (`/traces`, `/traces/{id}`).
- **Idempotent:** GET, PUT, DELETE can be called N times with the same effect.
- **Stateless:** each request carries everything the server needs.
- **Versioned:** prefix `/v1/`.
- **Documented:** OpenAPI.

### Status codes
200 ok · 201 created · 204 no content · 400 bad request · 404 not found · 422 unprocessable · 500 server error.

### Error response shape (be consistent)
```json
{"detail": "Trace not found: trace_9999"}
```
or for validation:
```json
{"detail": [{"loc": ["body", "rating"], "msg": "string does not match regex", "type": "value_error.str.regex"}]}
```

### Plural nouns
`/traces` not `/trace`.

---

## 3. Coding (30 min)

Open `backend/app/routes/traces.py` and `feedback.py`. Add a `DELETE /traces/{id}/feedback`:

```python
@router.delete("/{trace_id}/feedback", status_code=204)
def delete_feedback(trace_id: str):
    with db_cursor(commit=True) as cur:
        cur.execute("DELETE FROM feedback WHERE trace_id = ?", (trace_id,))
        cur.execute("UPDATE traces SET feedback=NULL WHERE trace_id=?", (trace_id,))
    return Response(status_code=204)
```

Add a test:
```python
def test_delete_feedback(client, seed):
    client.put("/traces/t001/feedback", json={"rating": "up"})
    r = client.delete("/traces/t001/feedback")
    assert r.status_code == 204
    assert client.get("/traces/t001").json()["feedback"] is None
```

### Sample I/O
- PUT `{"rating":"up"}` → 200.
- DELETE → 204 (no body).
- GET → `{"feedback": null, ...}`.

### Line-by-line
- `status_code=204` tells FastAPI to return 204 with no body.
- `Response` is the empty-body response.

---

## 4. Debugging & tests (20 min)

### Bug 1: 200 on error
**Symptom:** the client thinks everything succeeded even when it didn't.
**Fix:** raise `HTTPException` with the right code.

### Bug 2: mixing PUT and POST
PUT is idempotent; POST creates a new resource. Pick one.

### Bug 3: undocumented 4xx
**Fix:** document every error code in OpenAPI by raising `HTTPException` with a `detail` string.

### Bug 4: 500 on validation
If you're seeing 500, your handler is throwing before FastAPI can validate. Wrap and re-raise.

---

## 5. Mock interview practice (20 min)

**Q1 — "PUT vs POST?"**
> PUT is idempotent; POST creates new resources.

**Q2 — "PATCH vs PUT?"**
> PATCH partial; PUT replaces.

**Q3 — "What makes a good URL?"**
> Nouns, not verbs. `/traces/42/feedback`, not `/getTraceFeedback?id=42`.

**Q4 — "What is a contract test?"**
> A test that verifies your API matches the spec. The consumer is the spec.

**Q5 — "What is content negotiation?"**
> `Accept: application/json` lets the client request a format. The server picks the best match.

---

## 6. Success criteria check
- [ ] I can list 5 status codes and what triggers them.
- [ ] I can write a resource-oriented URL.
- [ ] I can write an idempotent PUT.
- [ ] I can document errors in OpenAPI.
- [ ] I can test 200, 204, 404, 422.

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
**Add `GET /traces/{id}/chunks/count` returning the number of retrieved chunks.**

### Rubric (0–10)
- 0: doesn't run
- 4: returns count
- 6: 404 on missing trace
- 8: Pydantic response model + test
- 10: handles malformed JSON in `retrieved_chunks` (returns 0 instead of 500)

### Solution
```python
@router.get("/{trace_id}/chunks/count")
def chunk_count(trace_id: str):
    with db_cursor() as cur:
        row = cur.execute("SELECT retrieved_chunks FROM traces WHERE trace_id=?", (trace_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Trace not found: {trace_id}")
    import json
    try:
        return {"count": len(json.loads(row["retrieved_chunks"]))}
    except Exception:
        return {"count": 0}
```

**Time: 90 min**