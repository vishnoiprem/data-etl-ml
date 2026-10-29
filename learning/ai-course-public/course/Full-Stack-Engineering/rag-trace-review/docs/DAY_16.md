# Day 16 — Debugging and Performance
**Module 16** | Total: 90 min (10 + 20 + 30 + 20 + 20)

---

## 1. Simple explanation (10 min)

**Analogy for a 12-year-old:**
Debugging is **detective work**. The bug is the criminal. Logs are witnesses. The profiler is the surveillance camera. Most crimes are committed by the same few suspects — find them once, find them everywhere.

---

## 2. Technical concepts (20 min)

- **Browser DevTools:** network, performance, memory.
- **React Profiler:** measures render time per component.
- **Backend logs:** structured JSON with request id.
- **Slow queries:** `EXPLAIN QUERY PLAN`.
- **P95 latency:** 95th percentile — the realistic worst case.

### Common bug classes
1. **Render loops** — `setState` inside `useEffect` without a dep.
2. **Memory leaks** — `addEventListener` without remove.
3. **Stale state** — capturing the wrong closure.
4. **N+1** — looping a query for each row.
5. **Race conditions** — out-of-order responses.

### Performance budgets
- P95 < 200ms for traces API.
- P95 < 16ms for table render (60fps).
- P95 < 1s for full page load.

---

## 3. Coding (30 min)

Add a `withTiming` decorator in `backend/app/main.py`:

```python
import time
def withTiming(fn):
    def w(*a, **kw):
        t0 = time.perf_counter()
        r = fn(*a, **kw)
        log.info(f"{fn.__name__} {int((time.perf_counter()-t0)*1000)}ms")
        return r
    return w
```

Wrap `list_traces`:
```python
@router.get("", response_model=TracePage)
@withTiming
def list_traces(...):
    ...
```

Add a `<Profiler>` in `frontend/src/App.tsx` to log render time:

```tsx
import { Profiler } from 'react';
<Profiler id="App" onRender={(id, phase, actualDuration) => console.log(id, phase, actualDuration)}>
  <TraceList />
</Profiler>
```

### Sample I/O
- `list_traces 12ms` in backend log.
- `App mount 18.2ms` in browser console.

### Line-by-line
- `time.perf_counter()` is monotonic.
- `Profiler.onRender` receives the component id, phase (mount/update), and duration in ms.

---

## 4. Debugging & tests (20 min)

### Bug 1: render loop
**Symptom:** CPU pegs, "Maximum update depth" warning.
**Fix:** guard with a ref or `useMemo`.

### Bug 2: memory leak
**Fix:** cleanup `useEffect` removes event listeners.

### Bug 3: stale state in callback
**Fix:** use the functional setter: `setX(x => x + 1)`.

### Bug 4: N+1
**Fix:** `WHERE x IN (?, ?, ?)` or join.

### Test
```ts
test('does not re-render needlessly', () => {
  const spy = vi.fn();
  const Child = React.memo(() => { spy(); return null; });
  const { rerender } = render(<Parent><Child /></Parent>);
  rerender(<Parent><Child /></Parent>);
  expect(spy).toHaveBeenCalledTimes(1);
});
```

---

## 5. Mock interview practice (20 min)

**Q1 — "P95?"**
> 95th percentile.

**Q2 — "Render loop?"**
> `useEffect` that updates state it depends on, with no guard.

**Q3 — "Memory leak?"**
> Memory allocated but not freed.

**Q4 — "Backpressure?"**
> Slow consumer throttling a fast producer.

**Q5 — "Request coalescing?"**
> Merging duplicate in-flight requests.

---

## 6. Success criteria check
- [ ] I can read DevTools network and performance.
- [ ] I can use the React Profiler.
- [ ] I can read backend logs.
- [ ] I can `EXPLAIN QUERY PLAN`.

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
**Add a `/health/deep` endpoint that runs a sample query and returns the round-trip ms.**

### Rubric (0–10)
- 0: doesn't compile
- 4: returns 200
- 6: includes timing
- 8: typed response
- 10: includes DB file size + row count

### Solution
```python
@app.get("/health/deep")
def deep_health():
    t0 = time.perf_counter()
    with db_cursor() as cur:
        n = cur.execute("SELECT COUNT(*) AS c FROM traces").fetchone()["c"]
    return {"db_ms": int((time.perf_counter()-t0)*1000), "rows": n}
```

**Time: 90 min**