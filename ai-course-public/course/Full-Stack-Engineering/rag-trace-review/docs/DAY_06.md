# Day 6 — Frontend/Backend Integration

## 1. Analogy
The browser and server are two people on a phone call. They take turns speaking. `fetch` is the act of asking a question. The response is the answer. `AbortController` is hanging up.

## 2. Technical concept
The browser issues a `fetch(url, options)`. The promise resolves with a `Response`. You call `.json()` to parse the body. You can pass a `signal` to cancel.

```ts
const ctrl = new AbortController();
fetch('/traces', { signal: ctrl.signal }).then(r => r.json());
// later: ctrl.abort();
```

### CORS
The browser blocks cross-origin requests by default. The server must respond with `Access-Control-Allow-Origin`.

## 3. Why this problem exists
The browser is sandboxed for security. Cross-origin requests need explicit permission.

## 4. Data flow
User changes filter → React state updates → useEffect/useQuery fires fetch → server returns JSON → React Query caches → component renders.

## 5. Example
**File: `frontend/src/api/client.ts`**
```ts
export async function fetchTraces(filters, cursor, signal) {
  const r = await fetch(`${BASE}/traces?...`, { signal });
  if (!r.ok) throw new Error(`${r.status}`);
  return r.json();
}
```

## 6. Line-by-line
- `signal` lets us cancel mid-flight.
- `r.ok` is true for 2xx.
- Throwing on non-2xx lets TanStack Query catch and retry.

## 7. I/O
- Request: `GET /traces?limit=50`
- Response: `{"items":[...], "meta":{...}}`

## 8. Bugs
- **Stale closures** when state changes mid-request.
- **No cancellation** → race conditions.
- **CORS not configured** → silent failure.

## 9. Tests
```ts
import { rest } from 'msw';
import { setupServer } from 'msw/node';
const server = setupServer(rest.get('/traces', (req, res, ctx) => res(ctx.json({items:[], meta:{}}))));
```

## 10. Performance
- Cancel on filter change.
- Debounce text input.
- Cache aggressively with staleTime.

## 11. Five Q&As
1. **What is CORS preflight?** An OPTIONS request before the real one.
2. **What does `credentials: 'include'` do?** Sends cookies cross-origin.
3. **What's a same-origin policy?** Browsers block reading responses from other origins.
4. **What's the difference between fetch and axios?** axios has interceptors and JSON parsing built in; fetch doesn't.
5. **What's `AbortController`?** A signal you pass to fetch to cancel it.

## 12. Coding assignment
Add a `useDebouncedValue<T>(value, ms)` hook.

## 13. Solution
```ts
export function useDebouncedValue<T>(value: T, ms: number) {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return v;
}
```
- 0: doesn't compile
- 4: returns value after delay
- 6: cleans up timeout
- 8: typed
- 10: leading + trailing edge

**Time: 90 min**