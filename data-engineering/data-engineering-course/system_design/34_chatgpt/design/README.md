# 34 — Design ChatGPT (Conversational AI with Streaming)

> **Module 2 of 6 — Agentic AI Systems**

A complete, runnable design + implementation of a ChatGPT-style
conversational chat service. The core engineering problems we model:

* **Conversation memory** — a thread of `system / user / assistant`
  messages, persisted and replayable.
* **Context window** — only the last N messages are sent on every call.
* **Streaming** — tokens (here, words) are emitted to the client as
  soon as they're produced, via Server-Sent Events.
* **Per-conversation model selection** — different models for different
  conversations; the model name is part of the cache key.

The LLM is a deterministic mock. Streaming, context windowing, and
persistence are real and runnable.

---

## 1. Requirements

### Functional
- Create a conversation with a `user_id` and `model`.
- Append a message (`role`, `content`) to a conversation.
- Stream a model reply one token at a time (SSE).
- List/get conversations; per-user filtering.
- Track approximate token counts for observability.

### Non-functional
- **Low first-token latency** — streaming means the user sees text
  within ~50–100 ms.
- **Bounded context** — context window is enforced server-side so we
  don't blow up token cost.
- **Cached completions** — repeated identical prompts reuse replies.

### Out of scope
- Tool use (covered in module 37).
- Multi-modal input.
- Real LLM API calls.

---

## 2. Capacity estimation

| Metric | Value |
|---|---|
| Active conversations | 1 M concurrent |
| Messages / conversation | ~30 |
| Avg context window | 8 messages ≈ 2 K tokens |
| Streaming chunks / response | ~50–200 |
| Storage / conversation | ~30 × 200 B = 6 KB |

Streaming is the dominant engineering cost. Each open stream is a
long-lived HTTP connection; we cap server threads and put a hard
timeout on streams.

---

## 3. High-level design

```
            ┌────────────────────┐
  client ──►│  Flask / app tier  │──┐
            └────────────────────┘  │
                      │              ▼
                      │       ┌─────────────┐
                      │       │  conv store │ (per-thread message log)
                      │       └─────────────┘
                      │              │
                      ▼              ▼
              ┌─────────────────────────┐
              │  context window builder │  (last N msgs + system)
              └────────────┬────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │   mock LLM      │  (canned, deterministic)
                  └────────┬────────┘
                           │ token stream
                           ▼
                  ┌─────────────────┐
                  │ SSE producer    │  data: <chunk>\\n\\n
                  └─────────────────┘
```

In production the "mock LLM" is replaced by an HTTP/2 stream from
OpenAI / Anthropic / vLLM, but the *interface* is the same: a token
generator.

---

## 4. API

| Method | Path | Body | Returns |
|---|---|---|---|
| `POST` | `/api/conversations` | `{user_id, model, system_prompt?}` | `Conversation` |
| `GET`  | `/api/conversations?user_id=` | — | `Conversation[]` |
| `GET`  | `/api/conversations/<id>` | — | `Conversation` |
| `POST` | `/api/conversations/<id>/messages` | `{role, content}` | `Message` |
| `POST` | `/api/conversations/<id>/complete` | — | full assistant `Message` |
| `POST` | `/api/conversations/<id>/stream` | — | SSE: token stream |
| `GET`  | `/metrics`, `/health` | — | metrics / health |

---

## 5. Data model

### Conversation

```json
{
  "conversation_id": 7,
  "user_id": "u-123",
  "model": "mock-fast",
  "system_prompt": "You are a helpful, concise assistant.",
  "created_at": 1700000000.0,
  "messages": [
    {"role": "system",    "content": "...", "tokens": 12},
    {"role": "user",      "content": "...", "tokens": 7},
    {"role": "assistant", "content": "...", "tokens": 35}
  ]
}
```

### KV layout

`conv:<id>` → JSON. The system prompt is the first message so we can
re-render the entire context from one record.

---

## 6. Read path deep dive: streaming

`POST /api/conversations/<id>/stream`:

1. Load the conversation, build the context window (system + last N).
2. Call the mock LLM to produce the full text.
3. Walk the text in token-sized chunks (`\S+\s*`).
4. For each chunk, emit a `data: <json>\n\n` SSE event.
5. Sleep 20 ms between chunks to simulate network latency.
6. Persist the final accumulated message on the conversation.
7. Send a sentinel `data: [DONE]\n\n` event.

The same code path becomes a real LLM stream in production — we just
swap `_mock_complete` + `stream_tokens` for a `requests` (or gRPC)
streaming call.

---

## 7. Write path deep dive: message append

`POST /api/conversations/<id>/messages`:

1. Validate `role` ∈ {user, assistant, system}.
2. Trim `content` to `MAX_MESSAGE_CHARS` to bound the context.
3. Estimate tokens (≈ words × 1.34).
4. Append + persist the whole conversation record.

Appending the whole record is fine for a single-process design; in a
sharded production system you'd write a per-message event to a
Kafka-style log and project to a read store.

---

## 8. Failure modes

| Failure | Mitigation |
|---|---|
| LLM stream stalls | Hard timeout per chunk; partial reply persisted. |
| LLM returns nothing | Treat as empty assistant message; surface in UI. |
| Token explosion | `MAX_MESSAGE_CHARS` caps individual messages; `context_window` caps the prompt. |
| Network drops mid-stream | Client re-issues; we return full reply on retry. |
| Cache poisoning | Per-model + per-context key; identical prompts reuse identical replies. |

---

## 9. Tradeoffs

- **SSE vs WebSocket**: SSE is one-way (server→client) and HTTP/1.1
  friendly — perfect for chat. WebSockets win when you also need
  typing indicators and bi-directional commands.
- **Whole-record write vs message log**: we re-serialize the whole
  conversation per message. A real system writes to an append-only log
  and projects to a doc store.
- **Context window by message vs token**: by message is simple and
  predictable. By token is more accurate for cost; production systems
  use tiktoken / equivalent to count tokens precisely.
- **Per-conversation cache vs global cache**: we cache `(model, ctx)`
  so the same prompt in different conversations reuses a reply. This
  is fine for a deterministic mock; for a real LLM you'd typically
  skip the cache to get diverse outputs.

---

## 10. Code map

| File | Role |
|---|---|
| `code/service.py` | `ChatService` — conversations, messages, context window, mock LLM, stream. |
| `code/app.py` | Flask HTTP service; SSE streaming for `/api/conversations/<id>/stream`. |
| `tests/test_service.py` | Service-level tests (tokenization, validation, completion, streaming). |
| `tests/test_app.py` | HTTP-level tests using Flask's test client. |
