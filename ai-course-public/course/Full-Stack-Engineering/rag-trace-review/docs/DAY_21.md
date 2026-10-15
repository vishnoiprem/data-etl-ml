# Day 21 — Capstone Polish + Final Review

## Today's goals
1. Re-run the 100-point review.
2. Run the full test suite.
3. Polish documentation.
4. Practice the 5-minute "demo and defend".

## 5-minute demo script
1. Open the app. Show the trace table.
2. Filter by `v1.0`. Notice latency jump.
3. Click a row. Show the detail.
4. Click 👍. Note instant feedback.
5. Disconnect the backend (kill uvicorn). Click 👍 again. Note rollback.
6. Restart backend. Click 👍. Now persists.

## Capstone checklist
- [ ] `GET /traces?day=...&prompt_version=...` works
- [ ] Cursor pagination
- [ ] Virtualization
- [ ] Optimistic feedback with rollback
- [ ] Loading, empty, error states
- [ ] 14+ backend tests pass
- [ ] 100-point review ≥ 95
- [ ] README explains how to run

## Rubric self-grade (0–10)
- Correctness
- Code quality
- Debugging
- API design
- Frontend implementation
- Performance
- Testing
- Communication

## Final 5 Meta Q&As
1. **What is the hardest part of cursor pagination?** Tie-breaker logic and combining with filters.
2. **Why is virtualization a frontend optimization, not backend?** It reduces DOM cost; the payload is unchanged.
3. **When would you abandon optimistic UI?** When the cost of being wrong is high (payments, deletes, etc.).
4. **Why FastAPI over Flask?** Type-driven validation, async-first, OpenAPI for free.
5. **What's the difference between unit and integration tests?** Scope of what runs.

## Coding assignment
Add a `?sort=latency_desc` query param.

## Solution
```python
sort_sql = "ORDER BY latency_ms DESC, trace_id DESC"
# append to base SQL
```
- 0: doesn't compile
- 4: sorts
- 6: accepts `latency_asc`
- 8: indexed
- 10: combined with cursor

**Time: 90 min**