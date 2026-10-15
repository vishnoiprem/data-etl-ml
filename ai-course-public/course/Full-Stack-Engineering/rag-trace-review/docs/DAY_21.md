# Day 21 — Capstone Polish + Final Review
**Module 18 + everything** | Total: 90 min (10 + 20 + 30 + 20 + 20)

---

## 1. Simple explanation (10 min)

**Analogy for a 12-year-old:**
Today is **graduation day**. You built the project, you learned the theory, you practiced the interviews. Today you put a bow on it: polish, test, demo, and self-grade.

---

## 2. Technical concepts (20 min)

The full success-criteria checklist from the master prompt:

- [ ] Build a React + TypeScript frontend without copying blindly.
- [ ] Implement FastAPI endpoints and explain request validation.
- [ ] Implement cursor pagination correctly.
- [ ] Build a virtualized React table.
- [ ] Handle optimistic feedback and rollback.
- [ ] Debug frontend/backend issues independently.
- [ ] Write meaningful automated tests.
- [ ] Explain each design choice in a Meta L6 interview.
- [ ] Build and run the entire project locally.

---

## 3. Coding (30 min) — capstone polish

Run the 100-point review script and fix anything that fails.

```bash
bash /tmp/fix_review_100.sh
```

If anything is below 100, read the failure and fix the underlying issue.

### Capstone checklist
- [ ] `GET /traces?day=...&prompt_version=...` works.
- [ ] Cursor pagination.
- [ ] Virtualization.
- [ ] Optimistic feedback with rollback.
- [ ] Loading, empty, error states.
- [ ] 14+ backend tests pass.
- [ ] 100-point review ≥ 95.
- [ ] README explains how to run.

### Sample I/O
- `curl 'http://localhost:8000/traces?limit=1'` → 200 with one item.
- Click 👍 in the UI → instant emoji; backend down → emoji reverts.

### Line-by-line
Discuss your changes with a partner or rubber duck.

---

## 4. Debugging & tests (20 min)

### Final test runs
```bash
cd backend && source .venv/bin/activate && pytest -q
cd ../frontend && npm test
```

Both should be green. If not, fix the underlying issue, not the test.

### Final review
Run the 100-point script. Aim for 100/100.

### Manual smoke test
1. Open the app.
2. Filter by `v1.0`.
3. Click a row.
4. Click 👍.
5. Reload the page.
6. The 👍 is still there (persisted).

---

## 5. Mock interview practice (20 min) — 5-minute "demo and defend"

**5-minute script:**
1. Open the app. Show the trace table (10–15 sec).
2. Filter by `v1.0`. Notice latency jump (10–15 sec).
3. Click a row. Show the detail (30 sec).
4. Click 👍. Note instant feedback (10–15 sec).
5. Disconnect the backend (kill uvicorn). Click 👍 again. Note rollback (30 sec).
6. Restart backend. Click 👍. Now persists (30 sec).
7. Walk through the 100-point review script (60 sec).
8. Answer one Meta L6 question (60 sec).

### Final 5 Meta Q&As
1. **What is the hardest part of cursor pagination?**
   > Tie-breaker logic and combining with filters.

2. **Why is virtualization a frontend optimization, not backend?**
   > It reduces DOM cost; the payload is unchanged.

3. **When would you abandon optimistic UI?**
   > When the cost of being wrong is high (payments, deletes).

4. **Why FastAPI over Flask?**
   > Type-driven validation, async-first, OpenAPI for free.

5. **What's the difference between unit and integration tests?**
   > Scope of what runs.

---

## 6. Success criteria check (final)
- [ ] All success criteria from the master prompt ✅
- [ ] 14+ backend tests pass
- [ ] 100-point review ≥ 95
- [ ] I can demo the app in 5 minutes
- [ ] I can defend each design choice

## 7. Final grade yourself 0–10
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

**Pass mark:** ≥ 56/80 (≥ 70%).
**Distinction:** ≥ 64/80 (≥ 80%).

---

## 8. Coding assignment
**Add a `?sort=latency_desc` query param to the traces endpoint.**

### Rubric (0–10)
- 0: doesn't compile
- 4: sorts
- 6: accepts `latency_asc`
- 8: works with cursor
- 10: indexed + tested for ties

### Solution
```python
sort = Query("created_at_desc", regex="^(created_at_desc|latency_desc|latency_asc)$")
# then in handler:
if sort == "latency_desc":
    order_sql = "ORDER BY latency_ms DESC, trace_id DESC"
else:
    order_sql = "ORDER BY created_at DESC, trace_id DESC"
```

---

**Congratulations — you finished the 21-day course! 🎉**
**Time: 90 min**