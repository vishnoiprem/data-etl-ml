# Day 18 — Mock Interview Day 1
**Module 18** | Total: 90 min (10 + 20 + 30 + 20 + 20)

---

## 1. Simple explanation (10 min)

**Analogy for a 12-year-old:**
A mock interview is **practice for the big game**. You don't play the championship for the first time on the day. You play it 50 times in practice, then you play it for real.

Today: 5 timed exercises. For each: 5 min think → 5 min code → 5 min discuss.

---

## 2. Technical concepts (20 min)

Format reminders:
- **Think out loud** — narrate your reasoning.
- **State assumptions** — even if the prompt is vague.
- **Drive** — be the one to ask clarifying questions.
- **Time-box** — don't disappear into a rabbit hole.

Topics covered so far (Modules 1–8):
- Web fundamentals, JS/TS, React, FastAPI, SQL, integration, API design, cursor pagination.

---

## 3. Coding (30 min)

### Exercise 1 — Implement `GET /traces/stats`
Returns average and P95 latency grouped by `prompt_version`.

```python
@router.get("/stats")
def stats():
    with db_cursor() as cur:
        rows = cur.execute("SELECT prompt_version, latency_ms FROM traces").fetchall()
    by = {}
    for r in rows:
        by.setdefault(r["prompt_version"], []).append(r["latency_ms"])
    out = []
    for pv, vals in by.items():
        vals.sort()
        p95 = vals[int(0.95 * (len(vals) - 1))]
        out.append({"prompt_version": pv, "count": len(vals), "avg": sum(vals)/len(vals), "p95": p95})
    return out
```

### Exercise 2 — Add a `compare` query param
`GET /traces?compare=v1.0,v1.1` returns side-by-side metrics.

### Exercise 3 — Build a debounced search (frontend)
Input → 300ms debounce → fetch.

### Exercise 4 — Debug
"Filter changes don't update the table." Likely cause: `queryKey` doesn't include filters.

### Exercise 5 — Explain optimistic UI to a PM
"It's like pressing 'send' on email and seeing the recipient's 'read' instantly — even if their server is slow, we show the best case and correct it if we were wrong."

### Sample I/O
See exercises above.

### Line-by-line
Discuss with a partner or out loud to a rubber duck.

---

## 4. Debugging & tests (20 min)

For each exercise, ask:
- What test would catch a regression?
- What happens at the boundary (empty, single, max)?
- What's the worst-case Big-O?

Add a test for Exercise 1:

```python
def test_stats(client, seed):
    r = client.get("/traces/stats")
    body = r.json()
    assert {b["prompt_version"] for b in body} == {"v1.0", "v1.1", "v1.2"}
    assert all("avg" in b and "p95" in b for b in body)
```

---

## 5. Mock interview practice (20 min)

**Q1 — "Why is `useState` async?"**
> It batches updates and re-renders on the next tick.

**Q2 — "What is a render boundary?"**
> A component that owns its own state.

**Q3 — "Controlled input?"**
> Form input whose value is React state.

**Q4 — "What is `useId`?"**
> Stable unique id for accessibility.

**Q5 — "What is `Suspense`?"**
> A boundary that shows a fallback while children load.

---

## 6. Success criteria check
- [ ] I can think out loud for 5 minutes on a hard problem.
- [ ] I can write a stats endpoint in 5 minutes.
- [ ] I can find a bug in 5 minutes.
- [ ] I can explain a concept to a non-engineer.

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
**Add a "Recent activity" sidebar that polls `/traces?limit=5` every 30s.**

### Rubric (0–10)
- 0: doesn't render
- 4: shows data
- 6: polls
- 8: pauses when tab hidden
- 10: exponential backoff on error

### Solution
```tsx
const { data } = useQuery({
  queryKey: ['recent'],
  queryFn: () => fetchTraces({}, null),
  refetchInterval: 30_000,
});
```

**Time: 90 min**