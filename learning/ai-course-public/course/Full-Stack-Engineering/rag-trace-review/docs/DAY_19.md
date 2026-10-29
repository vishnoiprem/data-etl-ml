# Day 19 — Mock Interview Day 2
**Module 18** | Total: 90 min (10 + 20 + 30 + 20 + 20)

---

## 1. Simple explanation (10 min)

**Analogy for a 12-year-old:**
Today is **game day, take two**. Same format as Day 18 but harder. Five minutes to think, five to code, five to discuss. Repeat.

---

## 2. Technical concepts (20 min)

Topics covered so far (Modules 9–13):
- TanStack Table, virtualization, optimistic UI, trace inspection, streaming.

### Common meta-skill: rubber-duck
Explain your code to a rubber duck. If you can't, you don't understand it.

---

## 3. Coding (30 min)

### Exercise 1 — Trace count endpoint
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

### Exercise 2 — Bulk feedback
`PUT /traces/feedback/bulk` accepts `{"items":[{"id":"...", "rating":"up"}, ...]}`.

### Exercise 3 — Fix a bug
The trace list shows duplicates after a feedback update.
Likely cause: optimistic update doesn't account for the same trace appearing in multiple cached pages.

### Exercise 4 — Component composition
Re-design `TraceDetail` to accept a render prop for the chunks section.

### Exercise 5 — Explain cursor pagination
Same as Day 8.

### Sample I/O
See above.

### Line-by-line
Discuss with a partner or write the explanation as comments.

---

## 4. Debugging & tests (20 min)

For each exercise, ask:
- What's the test that would catch a regression?
- What's the empty/single/many case?
- What's the index strategy?

Add a test for Exercise 1:

```python
def test_count(client, seed):
    r = client.get("/traces/count?prompt_version=v1.0")
    assert r.json() == {"count": 1}
```

---

## 5. Mock interview practice (20 min)

**Q1 — "Tree-shaking?"**
> Removing unused exports at build time.

**Q2 — "Code-splitting?"**
> Lazy-loading routes.

**Q3 — "Hydration?"**
> Server-rendered HTML being claimed by React.

**Q4 — "Server components?"**
> React components that run only on the server.

**Q5 — "ISR?"**
> Incremental Static Regeneration.

---

## 6. Success criteria check
- [ ] I can write a count endpoint in 5 minutes.
- [ ] I can design a bulk endpoint in 5 minutes.
- [ ] I can debug a duplicate-row bug in 5 minutes.
- [ ] I can describe a render prop.

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
**Implement a "Refresh" button that invalidates the traces query and refetches.**

### Rubric (0–10)
- 0: no refresh
- 4: refetches
- 6: shows loading
- 8: shows new data
- 10: also refetches the detail query

### Solution
```tsx
const qc = useQueryClient();
<button onClick={() => qc.invalidateQueries({ queryKey: ['traces'] })}>Refresh</button>
```

**Time: 90 min**