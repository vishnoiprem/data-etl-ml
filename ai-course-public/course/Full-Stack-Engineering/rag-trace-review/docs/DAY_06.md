# Day 6 — Frontend/Backend Integration
**Module 6** | Total: 90 min (10 + 20 + 30 + 20 + 20)

---

## 1. Simple explanation (10 min)

**Analogy for a 12-year-old:**
The browser and server are two people on a phone call. They take turns speaking.
- `fetch` = asking a question.
- The response = the answer.
- `AbortController` = hanging up mid-call.

If you don't hang up and ask a new question, you can mix up who said what. Always cancel the old call before making a new one.

---

## 2. Technical concepts (20 min)

The browser issues `fetch(url, options)`. The promise resolves with a `Response`. You call `.json()` to parse the body. You can pass a `signal` to cancel.

```ts
const ctrl = new AbortController();
fetch('/traces', { signal: ctrl.signal }).then(r => r.json());
// later
ctrl.abort();
```

### CORS
The browser blocks cross-origin requests by default. The server must respond with `Access-Control-Allow-Origin`.

### JSON parsing
`await r.json()` parses the body. Errors throw and TanStack Query catches and retries.

### React Query handles
- Loading state
- Error state
- Retries
- Caching
- Refetching
- Mutation lifecycle

### Loading / empty / error states
- **Loading:** skeleton or "Loading…".
- **Empty:** "No traces match the current filters."
- **Error:** "Failed to load: 500."

---

## 3. Coding (30 min)

Open `frontend/src/api/client.ts` and `frontend/src/hooks/useInfiniteTraces.ts`. Add a `useDebouncedValue` hook in `frontend/src/hooks/useDebouncedValue.ts`:

```ts
import { useEffect, useState } from 'react';
export function useDebouncedValue<T>(value: T, ms: number): T {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return v;
}
```

Use it in `FilterBar.tsx` to debounce the date and latency inputs.

### Sample I/O
- Type `1` in min_latency → state changes immediately → after 300ms the debounced value updates → fetch fires.
- Cancel the in-flight fetch by passing `signal` to `useInfiniteTraces`.

### Line-by-line
- `useState(value)` — initial value.
- `setTimeout(() => setV(value), ms)` — schedule update.
- `return () => clearTimeout(t)` — cleanup on dep change.

---

## 4. Debugging & tests (20 min)

### Bug 1: stale closure
Fetching with state that was captured before the change. Fix: include state in `queryKey` so React Query refetches.

### Bug 2: no cancellation
User changes filter → previous request still in flight → second request returns first → wrong data shown.
**Fix:** pass `signal` to `fetch`, use `cancelQueries` in `onMutate`.

### Bug 3: CORS not configured
**Symptom:** `Access to fetch ... has been blocked by CORS policy`.
**Fix:** add origin to `allow_origins` in `app/main.py`.

### Bug 4: 304 vs 200
Browsers send conditional requests; we always return 200. Add `Cache-Control` headers if you want CDN caching.

### Test
```ts
import { renderHook, act } from '@testing-library/react';
import { useDebouncedValue } from './useDebouncedValue';
test('debounces', () => {
  const { result, rerender } = renderHook(({ v }) => useDebouncedValue(v, 100), { initialProps: { v: 1 } });
  rerender({ v: 2 });
  expect(result.current).toBe(1);
  act(() => vi.advanceTimersByTime(150));
  expect(result.current).toBe(2);
});
```

---

## 5. Mock interview practice (20 min)

**Q1 — "What is CORS preflight?"**
> An `OPTIONS` request before the real one. The browser asks "may I send this method/header?" first.

**Q2 — "What does `credentials: 'include'` do?"**
> Sends cookies cross-origin.

**Q3 — "What is the same-origin policy?"**
> Browsers block reading responses from other origins.

**Q4 — "fetch vs axios?"**
> axios has interceptors and JSON parsing built in; fetch doesn't.

**Q5 — "What is `AbortController`?"**
> A signal you pass to `fetch` to cancel mid-flight.

---

## 6. Success criteria check
- [ ] I can write a typed fetch wrapper.
- [ ] I can cancel in-flight requests.
- [ ] I can debounce a value.
- [ ] I can configure CORS.
- [ ] I can render loading/empty/error states.

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
**Wrap `fetchTraces` with a 15s timeout using `AbortController`.** Add a test that asserts it rejects on timeout.

### Rubric (0–10)
- 0: doesn't compile
- 4: throws on timeout
- 6: rejects with clear error
- 8: typed return
- 10: cleanup on unmount

### Solution
```ts
export async function fetchTraces(filters, cursor, signal) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 15_000);
  try {
    const r = await fetch(`${BASE}/traces?...`, { signal: ctrl.signal });
    return await r.json();
  } finally {
    clearTimeout(t);
  }
}
```

**Time: 90 min**