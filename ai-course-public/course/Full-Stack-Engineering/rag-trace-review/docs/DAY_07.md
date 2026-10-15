# Day 7 — API Design

## 1. Analogy
A well-designed API is a **good vending machine**: clear buttons, expected snacks, change returned. A bad API is a phone tree from 2003.

## 2. Technical concept
- **Resource-oriented**: nouns in URLs.
- **Idempotent**: PUT/DELETE/GET can be called N times with the same effect.
- **Stateless**: each request carries everything the server needs.
- **Versioned**: prefix `/v1/`.
- **Documented**: OpenAPI.

## 3. Why
Internal teams adopt APIs faster when they're predictable. External devs need contracts they can read.

## 4. Data flow
Client → `GET /traces` → list. `GET /traces/{id}` → detail. `PUT /traces/{id}/feedback` → upsert.

## 5. Example
Already in the project: see `routes/traces.py` and `routes/feedback.py`.

## 6. Line-by-line
- Status codes: 200 ok, 201 created, 204 no content, 400 bad request, 404 not found, 422 unprocessable.
- Use plural nouns: `/traces`, not `/trace`.

## 7. I/O
- `PUT /traces/abc/feedback {"rating":"up"}` → 200 `{"trace_id":"abc", "rating":"up", "note":null, "created_at":"..."}`

## 8. Bugs
- Returning 200 on errors.
- Mixing PUT and POST semantics.
- Not documenting 4xx codes.

## 9. Tests
See `tests/test_traces.py` for status code coverage.

## 10. Performance
- O(1) lookups by primary key.
- Cursor pagination on lists.
- `Cache-Control` headers for static-ish data.

## 11. Five Q&As
1. **PUT vs POST?** PUT is idempotent; POST creates new resources.
2. **PATCH vs PUT?** PATCH partial; PUT replaces.
3. **What makes a good URL?** Nouns, not verbs.
4. **What is a contract test?** A test that verifies your API matches the spec.
5. **What is content negotiation?** `Accept: application/json` lets the client request a format.

## 12. Coding assignment
Add `DELETE /traces/{id}/feedback` that removes feedback (204).

## 13. Solution
```python
@router.delete("/{trace_id}/feedback", status_code=204)
def delete_feedback(trace_id: str):
    with db_cursor(commit=True) as cur:
        cur.execute("DELETE FROM feedback WHERE trace_id = ?", (trace_id,))
        cur.execute("UPDATE traces SET feedback=NULL WHERE trace_id=?", (trace_id,))
```
- 0: doesn't compile
- 4: deletes
- 6: 204 status
- 8: also clears traces.feedback
- 10: handles unknown trace_id (404)

**Time: 90 min**