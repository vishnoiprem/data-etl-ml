# Day 16 — Debugging and Performance

## 1. Analogy
Debugging is **detective work**. The bug is the criminal. Logs are witnesses. The profiler is the surveillance camera.

## 2. Technical concept
- **Browser DevTools:** network, performance, memory.
- **React Profiler:** measures render time per component.
- **Backend logs:** structured JSON with request id.
- **Slow queries:** `EXPLAIN QUERY PLAN`.
- **P95 latency:** 95th percentile — the realistic worst case.

## 3. Why
Most "slow" is in one place. Find that place, fix it, ship.

## 4. Data flow
User reports slowness → reproduce → DevTools network tab → identify slow request → backend logs → SQL plan → fix.

## 5. Example (structured logging)
```python
import logging, time
log = logging.getLogger("perf")
@app.middleware("http")
async def add_timing(request, call_next):
    t0 = time.perf_counter()
    r = await call_next(request)
    log.info("req", extra={"path": request.url.path, "ms": int((time.perf_counter()-t0)*1000)})
    return r
```

## 6. Line-by-line
- `time.perf_counter()` is monotonic.
- Middleware wraps every request.

## 7. I/O
- Log: `{"path":"/traces", "ms":42}`

## 8. Bugs
- **Render loops** — `setState` inside `useEffect` without a dep.
- **Memory leaks** — `addEventListener` without remove.
- **Stale state** — capturing the wrong closure.

## 9. Tests
- Use `Profiler` in tests and assert render count.
- Use `MSW` to simulate slow networks.

## 10. Performance
- P95 < 200ms for traces API.
- P95 < 16ms for table render.
- P95 < 1s for full page load.

## 11. Five Q&As
1. **What's P95?** The 95th percentile.
2. **What's a render loop?** `useEffect` that updates state it depends on.
3. **What's a memory leak?** Memory allocated but not freed.
4. **What's backpressure?** A slow consumer throttling a fast producer.
5. **What's request coalescing?** Merging duplicate in-flight requests.

## 12. Coding assignment
Add a `withTiming` wrapper that logs function duration.

## 13. Solution
```python
import time, logging
log = logging.getLogger("timing")
def withTiming(fn):
    def w(*a, **kw):
        t0 = time.perf_counter(); r = fn(*a, **kw)
        log.info(f"{fn.__name__} {int((time.perf_counter()-t0)*1000)}ms"); return r
    return w
```
- 0: doesn't run
- 4: prints duration
- 6: structured log
- 8: async support
- 10: thread-safe

**Time: 90 min**