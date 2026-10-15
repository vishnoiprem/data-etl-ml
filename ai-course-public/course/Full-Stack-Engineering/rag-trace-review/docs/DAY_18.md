# Day 18 — Mock Interview Practice

## Format
5 timed exercises. For each: 5 min think → 5 min code → 5 min discuss.

## Exercise 1 — Implement `GET /traces/stats`
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

## Exercise 2 — Add a `compare` query param
`GET /traces?compare=v1.0,v1.1` returns side-by-side metrics.

## Exercise 3 — Build a debounced search
Frontend input → 300ms debounce → fetch.

## Exercise 4 — Debug: "Filter changes don't update the table"
Likely cause: `queryKey` doesn't include filters, or the API ignores them.

## Exercise 5 — Explain optimistic UI to a PM
"It's like pressing 'send' on an email and seeing the recipient's 'read' instantly — even if their server is slow, we show the best case and correct it if we were wrong."

---

## Five Q&As
1. **Why is `useState` async?** It batches updates and re-renders on the next tick.
2. **What's a render boundary?** A component that owns its own state.
3. **What's a controlled input?** A form input whose value is React state.
4. **What is `useId`?** Stable unique id for accessibility.
5. **What's `Suspense`?** A boundary that shows a fallback while children load.

## Coding assignment
Add a "Recent activity" sidebar that polls `/traces?limit=5` every 30s.

## Solution
```tsx
const { data } = useQuery({
  queryKey: ['recent'],
  queryFn: () => fetchTraces({}, null),
  refetchInterval: 30_000,
});
```
- 0: doesn't render
- 4: shows data
- 6: polls
- 8: pauses when tab hidden
- 10: exponential backoff on error

**Time: 90 min**