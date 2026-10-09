# 38 — Real-Time Voice AI (STT → LLM → TTS Pipeline)

> **Module 6 of 6 — Agentic AI Systems**

A complete, runnable design + implementation of a real-time voice
assistant pipeline, à la OpenAI Realtime API, Amazon Lex, or
Google Dialogflow CX. The engineering problem is wiring together
three independent stages and streaming audio in both directions.

The three stages:

```
   audio_in ──► STT ──► text_in ──► LLM ──► text_out ──► TTS ──► audio_out
```

Each stage is a deterministic mock; the pipeline state machine and
the data flow are real and runnable.

---

## 1. Requirements

### Functional
- Create a session per user.
- Push inbound audio chunks (binary).
- Run the full STT → LLM → TTS pipeline on each push.
- Stream outbound audio chunk metadata to the client (SSE).
- Maintain a per-session transcript (user + assistant).
- Clear the outbox after the client has played the audio.

### Non-functional
- **Low first-byte latency** — each stage should return promptly.
  (In production, all three stages run in parallel; we model the
  sequential case for clarity.)
- **Bounded chunk size** — 32 KB per inbound audio chunk.
- **State observable** — `state` is one of
  `idle | stt | llm | tts | playing | done | error`.
- **Recoverable errors** — a stage failure sets `state=error` with a
  human-readable message; the client can recover.

### Out of scope
- Real STT (Whisper) / TTS (ElevenLabs) / LLM.
- Voice activity detection (VAD).
- Bidirectional streaming (we run the pipeline per inbound chunk).

---

## 2. Capacity estimation

| Metric | Value |
|---|---|
| Audio bitrate | 16 kHz × 16-bit mono = 32 KB/sec |
| Inbound chunk size | 32 KB → 1 second of audio |
| STT latency (Whisper-small) | ~100 ms / 1-sec chunk |
| LLM first-token latency | ~150–300 ms |
| TTS first-byte latency | ~80 ms |
| Total time-to-first-audio | ~400–600 ms |
| Outbound audio | ~24 KB/sec (Opus @ 24 kbps) |

Real-time voice is the hardest latency budget in the AI stack.

---

## 3. High-level design

```
                              ┌──────────────────────┐
   client ── audio_in ──►    │       server         │
                              │                      │
                              │  ┌─────────┐         │
                              │  │  STT    │  text   │
                              │  └────┬────┘         │
                              │       ▼              │
                              │  ┌─────────┐ reply  │
                              │  │  LLM    │ text   │
                              │  └────┬────┘         │
                              │       ▼              │
                              │  ┌─────────┐ chunks │
                              │  │  TTS    │         │
                              │  └────┬────┘         │
                              │       ▼              │
                              │   outbox (FIFO)      │── audio_out ──► client
                              │                      │   (SSE metadata)
                              └──────────────────────┘
```

State machine per session:

```
        ┌─────────┐  audio_in
        │  idle   │──────────────┐
        └────┬────┘              ▼
             │              ┌─────────┐
             │              │  stt    │
             │              └────┬────┘
             │                   ▼
             │              ┌─────────┐
             │              │  llm    │
             │              └────┬────┘
             │                   ▼
             │              ┌─────────┐
             │              │  tts    │
             │              └────┬────┘
             │                   ▼
             │              ┌─────────┐
             │              │ playing │── clear ──► idle
             │              └─────────┘
             │                   │
             │ any error        ▼
             │              ┌─────────┐
             └──────────────│  error  │
                            └─────────┘
```

---

## 4. API

| Method | Path | Body | Returns |
|---|---|---|---|
| `POST` | `/api/sessions` | `{user_id}` | `Session` |
| `GET`  | `/api/sessions` | — | `Session[]` |
| `GET`  | `/api/sessions/<id>` | — | `Session` |
| `POST` | `/api/sessions/<id>/audio` | raw bytes | `{state, audio_chunks[]}` |
| `GET`  | `/api/sessions/<id>/transcript` | — | `transcript[]` |
| `GET`  | `/api/sessions/<id>/audio/outbox` | — | `outbox[]` |
| `GET`  | `/api/sessions/<id>/audio/stream` | — | SSE of `audio_chunks` |
| `POST` | `/api/sessions/<id>/outbox/clear` | — | `{cleared: N}` |
| `GET`  | `/metrics`, `/health` | — | metrics / health |

---

## 5. Data model

### Session

```json
{
  "session_id": 7,
  "user_id": "u-123",
  "state": "playing",
  "last_text": "Sure! It looks like it'll be partly cloudy…",
  "audio_in_bytes": 32000,
  "audio_out_bytes": 2048,
  "turn_count": 1,
  "error_message": null,
  "transcript": [
    {"role": "user",      "text": "what's the weather", "audio_ms": 1000.0},
    {"role": "assistant", "text": "Sure! It looks like…", "audio_ms": 0.0}
  ],
  "outbox": [
    {"chunk_id": 1234, "text": "Sure! …", "is_final": false, "size": 256, "sha256": "…"}
  ]
}
```

### Outbox

The outbox is a FIFO queue of `AudioChunk` records. Clients drain it
via `outbox/clear` (after playing) or stream it via SSE.

---

## 6. Read path deep dive: SSE audio stream

`GET /api/sessions/<id>/audio/stream`:

1. Walk the session's outbox.
2. For each chunk, emit `data: <json>\n\n`.
3. End with `data: [DONE]\n\n`.

Clients use this to drive a Web Audio player. The actual audio bytes
are small (256 B per chunk in the mock) so a real system can either:
- Embed them in the SSE event (base64), or
- Use a separate binary WebSocket.

---

## 7. Write path deep dive: push_audio

`POST /api/sessions/<id>/audio` (raw bytes):

1. Validate the chunk size (≤ 32 KB) and the session state.
2. Increment `audio_in_bytes`.
3. **STT stage** (`_mock_stt`):
   - Deterministic canned phrase from the audio hash.
   - Set `state = "stt"`, persist, then `state = "llm"`.
4. **Transcript**: append `{role: "user", text, audio_ms}`.
5. **LLM stage** (`_mock_llm`):
   - Template reply based on the transcript.
6. **Transcript**: append `{role: "assistant", text}`.
7. **TTS stage** (`_mock_tts_synth`):
   - Split the reply into word-sized synthetic byte chunks.
8. **Outbox**: append each `AudioChunk`. Increment `audio_out_bytes`.
9. Set `state = "playing"`, persist, return the chunks.

If any stage raises, `state = "error"` and `error_message` is set; the
client sees the error on the next call.

---

## 8. Failure modes

| Failure | Mitigation |
|---|---|
| Network drop on `audio_in` | Client retries; STT is deterministic on the same bytes. |
| STT returns empty | `state` returns to `idle`; no transcript / no outbox. |
| LLM rate-limited | Set `state = "error"` with the message; client backs off. |
| TTS fails | Same as above. |
| Outbox grows unbounded | Client calls `outbox/clear` after playback. |
| Bad session id | 404 from the session lookup. |
| Oversize audio | Reject with 400. |

---

## 9. Tradeoffs

- **Sequential vs streaming pipeline**: real systems run STT, LLM, and
  TTS in parallel with overlapping windows (Whisper streaming + LLM
  token streaming + TTS chunk streaming). We model the simpler
  per-chunk sequential pipeline.
- **Push vs WebSocket**: a push API works for the course. Real voice
  apps prefer a WebSocket (or WebRTC) for true bidirectional streaming.
- **Mock STT vs Whisper**: Whisper takes ~100 ms for a 1-second chunk
  on a GPU; the mock returns instantly. The interface is identical.
- **Server-side outbox vs client pull**: we expose both. SSE for live
  updates; `outbox` + `clear` for explicit drain.

---

## 10. Code map

| File | Role |
|---|---|
| `code/service.py` | `VoiceService` — session, pipeline, outbox, transcript. |
| `code/app.py` | Flask HTTP service with SSE audio stream. |
| `tests/test_service.py` | Service-level tests (mock STT/LLM/TTS, full pipeline, transcript, outbox). |
| `tests/test_app.py` | HTTP-level tests using Flask's test client. |
