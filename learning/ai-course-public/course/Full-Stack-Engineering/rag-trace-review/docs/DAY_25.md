# Day 25 — AI Domain: LLM Streaming, Function Calling, and Evals
**Module 20** | Total: 90 min (10 + 20 + 30 + 20 + 20)

---

## 1. Simple explanation (10 min)

Modern LLM APIs have three superpowers:
1. **Streaming** — see the answer as it's typed.
2. **Function calling** — let the model call your Python functions.
3. **Structured output** — force the answer into JSON matching a schema.

Plus one thing you must have: **evals** — measuring if the model is actually good.

---

## 2. Technical concepts (20 min)

### Streaming (SSE)
- Server sends `data: {"delta":"..."}\n\n` chunks.
- Client appends to UI.
- TTFT (time to first token) is the perceived latency.
- Use `EventSource` (browser) or `httpx.stream` (Python).

### Function calling
- You define a list of `{name, description, parameters}` schemas.
- The model returns `{name, arguments}` when it wants to call a function.
- You execute the function and return the result.
- The model then continues the conversation.

### Structured output
- `response_format={"type": "json_schema", "schema": {...}}` forces the model to return JSON matching your schema.
- OpenAI and Anthropic both support this.
- Alternative: use a library like `instructor` or `outlines`.

### Eval frameworks
- **Ragas:** RAG-specific (faithfulness, answer relevancy, context precision).
- **Braintrust / LangSmith:** generic LLM tracing + scoring.
- **Phoenix:** open-source observability.
- **Custom:** a set of (input, expected_output) pairs, scored by an LLM judge or exact match.

### Cost optimization
- **Prompt caching:** OpenAI caches common prefixes; reduces cost 10x.
- **Smaller models:** GPT-4o-mini is 30x cheaper than GPT-4o, often 90% as good.
- **Batching:** call the LLM with N requests at once.
- **Speculative decoding:** use a small model to draft, big model to verify.

---

## 3. Coding (30 min)

Add a **streaming chat** endpoint that uses **function calling** to fetch trace stats. `backend/app/routes/llm.py`:

```python
"""LLM endpoint with streaming + function calling. Uses a mock LLM (no API key)."""
import asyncio
import json
from typing import AsyncGenerator
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter(prefix="/llm", tags=["llm"])


class ChatIn(BaseModel):
    message: str


# Mock function definitions (in real life, pass to OpenAI/Anthropic)
FUNCTIONS = [
    {
        "name": "get_trace_stats",
        "description": "Get aggregated trace statistics by prompt version",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt_version": {"type": "string", "enum": ["v1.0", "v1.1", "v1.2", "v2.0"]}
            },
        },
    }
]


def mock_llm_stream(message: str) -> AsyncGenerator[str, None]:
    """A fake LLM that streams tokens."""
    response = f"Based on the data: you asked '{message}'. Calling get_trace_stats now."
    for word in response.split(" "):
        yield f"data: {json.dumps({'token': word + ' '})}\n\n"
        asyncio.sleep(0.05)
    # The model "decides" to call the function
    yield f"data: {json.dumps({'function_call': {'name': 'get_trace_stats', 'arguments': {'prompt_version': 'v2.0'}}})}\n\n"
    yield "data: [DONE]\n\n"


@router.post("/chat")
def chat(body: ChatIn):
    return StreamingResponse(mock_llm_stream(body.message), media_type="text/event-stream")
```

### Sample I/O
- POST `/llm/chat` `{"message":"how is v2.0 doing?"}` → SSE stream of tokens + a function call event.

### Line-by-line
- `AsyncGenerator` — async generator type.
- `data: ` prefix is the SSE protocol.
- `[DONE]` signals end of stream.

---

## 4. Debugging & tests (20 min)

### Bug 1: function call arguments malformed
**Fix:** validate against the JSON schema before calling your function.

### Bug 2: stream cuts off mid-token
**Fix:** check `Content-Length` and `Transfer-Encoding: chunked`; client should handle partial UTF-8.

### Bug 3: eval set is biased
**Fix:** include adversarial examples (typos, ambiguous queries, off-topic).

### Bug 4: LLM judge agrees with itself
**Fix:** use multiple judges, or human spot-checks on 10% of cases.

### Test
```python
def test_chat_streams(client):
    with client.stream("POST", "/llm/chat", json={"message": "hi"}) as r:
        chunks = list(r.iter_lines())
    assert any("data:" in c for c in chunks)
    assert chunks[-1] == "data: [DONE]"
```

---

## 5. Mock interview practice (20 min)

**Q1 — "How do you stream tokens to the browser?"**
> Server-Sent Events. Each `yield` is a `data: ...\n\n` chunk. Browser uses `EventSource` which auto-reconnects.

**Q2 — "How do you reduce LLM cost by 10x?"**
> Prompt caching (10x on common prefixes). Smaller models for routing/summarization. Batch offline jobs.

**Q3 — "How do you evaluate a RAG system?"**
> Offline eval set with (query, expected_answer, relevant_doc_ids). Metrics: faithfulness, answer relevancy, context recall. Use an LLM judge for open-ended answers.

**Q4 — "How do you handle function call errors?"**
> Wrap in try/except, return the error to the model as a tool result, let it decide what to do next.

**Q5 — "What's the TTFT budget?"**
> 500ms for chat. Long enough for a 50-token first chunk. If you can't hit 500ms, you need a smaller model or speculative decoding.

---

## 6. Success criteria check
- [ ] I can implement SSE streaming.
- [ ] I can describe function calling.
- [ ] I can list 3 eval metrics.
- [ ] I can name 3 cost optimizations.

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
**Add an `eval/run` endpoint that scores a (question, expected_answer) pair using a simple heuristic: substring match after lowercasing and stripping punctuation.**

### Rubric (0–10)
- 0: doesn't compile
- 4: returns score
- 6: normalized comparison
- 8: returns pass/fail + score
- 10: batch endpoint

### Solution
```python
import re
def normalize(s: str) -> set[str]:
    return set(re.findall(r"\w+", s.lower()))

def score(question, expected, actual):
    e, a = normalize(expected), normalize(actual)
    if not e: return 0.0
    return len(e & a) / len(e)
```

**Time: 90 min**