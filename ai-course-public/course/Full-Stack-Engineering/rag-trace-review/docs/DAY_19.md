# Day 19 — Mock Interview Day 2

## Exercise 1 — Trace count endpoint
`GET /traces/count?prompt_version=v1.0` returns `{count: 42}`.

```python
@router.get("/count")
def count(prompt_version: Optional[str] = None):
    sql = "SELECT COUNT(*) AS c FROM traces"
    params = []
    if prompt_version:
        sql += " WHERE prompt_version = ?"; params.append(prompt_version)
    with db_cursor() as cur:
        return {"count": cur.execute(sql, params).fetchone()["c"]}
```

## Exercise 2 — Bulk feedback
`PUT /traces/feedback/bulk` accepts `{"items":[{"id":"...", "rating":"up"}, ...]}`.

## Exercise 3 — Fix a bug
The trace list shows duplicates after a feedback update. Likely cause: optimistic update doesn't account for the same trace appearing in multiple cached pages.

## Exercise 4 — Component composition
Re-design `TraceDetail` to accept a render prop for the chunks section.

## Exercise 5 — Explain cursor pagination
Same as Day 8.

## Five Q&As
1. **What's tree-shaking?** Removing unused exports at build time.
2. **What's code-splitting?** Lazy-loading routes.
3. **What is hydration?** Server-rendered HTML being claimed by React.
4. **What is server components?** React components that run only on the server.
5. **What is ISR?** Incremental Static Regeneration.

## Coding assignment
Implement a "Refresh" button that invalidates the traces query and refetches.

## Solution
```tsx
const qc = useQueryClient();
<button onClick={() => qc.invalidateQueries({queryKey:['traces']})}>Refresh</button>
```
- 0: no refresh
- 4: refetches
- 6: shows loading
- 8: shows new data
- 10: also refetches the detail query

**Time: 90 min**