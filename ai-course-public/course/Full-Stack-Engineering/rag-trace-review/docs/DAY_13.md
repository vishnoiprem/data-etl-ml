# Day 13 — AI UI Features (Streaming)

## 1. Analogy
Streaming tokens is like **watching someone type** on the other side of a glass wall. The words appear as they're typed, not after the whole page is written.

## 2. Technical concept
Two main transports:
- **Server-Sent Events (SSE):** server pushes text/event-stream chunks. One-way, simple.
- **WebSockets:** full-duplex, more complex.

For LLM streaming, SSE is usually enough.

## 3. Why
Time-to-first-token is the perceived latency. A 10-second response that shows the first word in 200ms feels faster than a 2-second response that shows nothing for 1.9s.

## 4. Data flow
Client opens EventSource → server sends `data: {"token":"hi"}\n\n` chunks → client appends to UI.

## 5. Example (SSE)
**Server (FastAPI):**
```python
from fastapi.responses import StreamingResponse
import asyncio

@router.get("/stream")
async def stream():
    async def gen():
        for word in ["hello", " ", "world"]:
            yield f"data: {word}\n\n"
            await asyncio.sleep(0.1)
    return StreamingResponse(gen(), media_type="text/event-stream")
```
**Client:**
```ts
const src = new EventSource('/stream');
src.onmessage = (e) => setText(t => t + e.data);
```

## 6. Line-by-line
- `yield "data: ...\n\n"` — SSE event format.
- `media_type="text/event-stream"` — tells the browser to keep the connection open.

## 7. I/O
- Server: emits 3 events.
- Client: text grows `""` → `"hello"` → `"hello "` → `"hello world"`.

## 8. Bugs
- Forgetting `\n\n` → events don't fire.
- Auto-reconnect loops when the user navigates away.
- Race conditions on cancellation.

## 9. Tests
Mock the SSE endpoint with `msw` and assert incremental state.

## 10. Performance
- Use HTTP/1.1 keep-alive.
- Buffer small tokens; flush on word boundaries.

## 11. Five Q&As
1. **SSE vs WebSocket?** SSE for one-way, WS for two-way.
2. **What does `data: ` prefix mean?** It's the SSE protocol field.
3. **How do you cancel a stream?** `EventSource.close()`.
4. **Why `text/event-stream`?** Standard MIME type; browser knows to keep the connection open.
5. **What if the connection drops?** EventSource auto-reconnects with `retry:` field.

## 12. Coding assignment
Add a stop button that calls `EventSource.close()` and a retry button that re-opens.

## 13. Solution
```tsx
const [src, setSrc] = useState<EventSource | null>(null);
const start = () => setSrc(new EventSource('/stream'));
const stop = () => { src?.close(); setSrc(null); };
```
- 0: doesn't compile
- 4: stop closes
- 6: start re-opens
- 8: cleanup on unmount
- 10: handles backpressure

**Time: 90 min**