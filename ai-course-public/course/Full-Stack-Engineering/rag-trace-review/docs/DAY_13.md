# Day 13 — AI UI Features (Streaming)
**Module 13** | Total: 90 min (10 + 20 + 30 + 20 + 20)

---

## 1. Simple explanation (10 min)

**Analogy for a 12-year-old:**
Streaming tokens is **watching someone type** on the other side of a glass wall. The words appear as they're typed, not after the whole page is written.

A 10-second response that shows the first word in 200ms feels faster than a 2-second response that shows nothing for 1.9s.

---

## 2. Technical concepts (20 min)

### Transports
- **Server-Sent Events (SSE):** server pushes `text/event-stream` chunks. One-way, simple.
- **WebSockets:** full-duplex, more complex.

For LLM streaming, SSE is usually enough.

### SSE format
```
data: {"token":"hi"}\n\n
data: {"token":" "}\n\n
data: {"token":"world"}\n\n
```

### Cancellation
- `EventSource.close()` on the client.
- Server checks for disconnect.

### Time-to-first-token (TTFT)
The metric that matters. Most users perceive latency by TTFT, not total time.

---

## 3. Coding (30 min)

Add an SSE endpoint to `backend/app/routes/feedback.py` (or a new `routes/stream.py`):

```python
from fastapi.responses import StreamingResponse
import asyncio

@router.get("/stream/demo")
async def stream_demo():
    async def gen():
        for w in ["Hello", " ", "streaming", " ", "world"]:
            yield f"data: {w}\n\n"
            await asyncio.sleep(0.1)
    return StreamingResponse(gen(), media_type="text/event-stream")
```

Add a frontend `useStream` hook:

```ts
export function useStream(url: string) {
  const [text, setText] = useState('');
  useEffect(() => {
    const src = new EventSource(url);
    src.onmessage = (e) => setText(t => t + e.data);
    return () => src.close();
  }, [url]);
  return text;
}
```

### Sample I/O
- Page loads → text grows `"Hello"` → `"Hello "` → `"Hello streaming"` → `"Hello streaming "` → `"Hello streaming world"`.

### Line-by-line
- `data: <payload>\n\n` — SSE event format.
- `media_type="text/event-stream"` — tells the browser to keep the connection open.

---

## 4. Debugging & tests (20 min)

### Bug 1: events don't fire
**Cause:** forgot `\n\n`.
**Fix:** always end each event with two newlines.

### Bug 2: auto-reconnect loop
**Cause:** `EventSource` retries on disconnect.
**Fix:** set `retry: 0` or `src.close()` on unmount.

### Bug 3: state updates after unmount
**Cause:** SSE onmessage still firing.
**Fix:** close the source in cleanup.

### Bug 4: race with React 18 strict mode (double mount in dev)
**Fix:** use a ref to ensure single instance.

### Test
```ts
import { setupServer } from 'msw/node';
const server = setupServer();
test('appends tokens', async () => {
  server.listen();
  // mock SSE
  // assert text grows
});
```

---

## 5. Mock interview practice (20 min)

**Q1 — "SSE vs WebSocket?"**
> SSE for one-way, WS for two-way.

**Q2 — "What does `data: ` prefix mean?"**
> SSE protocol field.

**Q3 — "How do you cancel a stream?"**
> `EventSource.close()`.

**Q4 — "Why `text/event-stream`?"**
> Standard MIME type; browser keeps connection open.

**Q5 — "What if the connection drops?"**
> `EventSource` auto-reconnects unless we set `retry:`.

---

## 6. Success criteria check
- [ ] I can write a FastAPI SSE endpoint.
- [ ] I can write a React SSE consumer.
- [ ] I can cancel on unmount.
- [ ] I can test SSE with msw.

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
**Add a stop button that calls `EventSource.close()` and a retry button that re-opens.**

### Rubric (0–10)
- 0: doesn't compile
- 4: stop closes
- 6: start re-opens
- 8: cleanup on unmount
- 10: handles backpressure

### Solution
```tsx
const [src, setSrc] = useState<EventSource | null>(null);
const start = () => setSrc(new EventSource('/traces/stream/demo'));
const stop = () => { src?.close(); setSrc(null); };
useEffect(() => () => src?.close(), [src]);
```

**Time: 90 min**