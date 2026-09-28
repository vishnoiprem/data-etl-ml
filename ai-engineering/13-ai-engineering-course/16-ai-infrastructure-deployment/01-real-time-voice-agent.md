# Lesson 1 — Real-Time Voice Agent Architecture

> **Type:** Article + Worked Example · Module 16
> STT → LLM → TTS over WebSocket, with measured latency budgets, interruption handling, and the cost model.

---

## Why voice is the hardest production AI problem

Voice combines everything hard: real-time latency, streaming audio, interruption handling, multi-modal sync, cost. A 200ms delay feels "laggy" on the phone. 500ms feels broken.

```
   LATENCY BUDGET (human conversation): ~500ms round-trip
   
   TEXT CHAT                         VOICE AGENT
   ────────                          ───────────
   User types → submit               User speaks → STT (50ms)
   LLM (1-3s OK)                     LLM first token (200ms)
   Stream response                   TTS first audio (150ms)
                                     Stream audio out
                                     Total: ~400ms
                                     
   3 seconds OK                      500ms or it's broken
```

The component budget for a voice agent:

```
   USER SPEAKS                                              AGENT SPEAKS
   ──────────                                              ────────────
   |STT     |LLM think  |TTS      |  TOTAL
   |50-100ms|150-300ms  |100-200ms|  = 300-600ms
   
   Each stage must stream — you can't wait for the full output before
   starting playback. TTFT (time to first audio) is the key metric.
```

---

## The architecture

```
   ┌────────┐  audio   ┌──────┐  text   ┌──────┐  text   ┌──────┐  audio   ┌────────┐
   │ User   │ ──────► │ STT  │ ──────► │ LLM  │ ──────► │ TTS  │ ──────► │ User   │
   │ mic    │  WebRTC │ Whisper│        │stream│        │stream│  WebRTC │ speaker│
   └────────┘         └──────┘         └──────┘         └──────┘         └────────┘
                          │                │                 │
                          ▼                ▼                 ▼
                     [turn detect]   [interruption]    [audio buffer]
                     VAD silence     user started      queue chunks
                     detection       speaking?
```

Three concurrent streams, all over a single WebSocket or WebRTC connection.

---

## Worked Example — build a voice agent with measured latency

> **Goal:** Wire up Deepgram (STT) → GPT-4o-mini (LLM) → ElevenLabs (TTS) over WebSocket. Measure end-to-end latency, TTFT, audio glitch rate. Add interruption handling.

### Step 1 — The WebSocket server

```python
import asyncio
import websockets
import json

async def voice_session(ws):
    """One WebSocket = one conversation."""
    transcript_buffer = []
    
    async for message in ws:
        if isinstance(message, bytes):
            # Audio chunk from the user → forward to STT
            await stt_stream.feed(message)
        else:
            data = json.loads(message)
            if data["type"] == "stt_final":
                # User finished a turn; pass to LLM
                user_text = data["text"]
                await handle_turn(ws, user_text)

async def handle_turn(ws, user_text):
    """Run STT→LLM→TTS pipeline for one user turn."""
    t0 = time.perf_counter()
    
    # LLM streaming
    full_response = ""
    first_token_at = None
    async for chunk in llm.astream(user_text):
        if first_token_at is None:
            first_token_at = time.perf_counter()
        full_response += chunk
        # Buffer text for TTS
        await tts_buffer.feed(chunk)
    
    # TTS streams audio as soon as a sentence boundary is detected
    # The first audio chunk is sent to the user ASAP
    
    print(f"TTFT (first LLM token): {(first_token_at - t0)*1000:.0f}ms")
    print(f"Total turn: {(time.perf_counter() - t0)*1000:.0f}ms")
```

### Step 2 — Stream STT (Deepgram)

```python
from deepgram import DeepgramClient

dg = DeepgramClient()

async def transcribe_stream(audio_queue):
    """Consume audio chunks, yield transcripts."""
    connection = dg.listen.live.v("1")
    
    async def keep_alive():
        while True:
            await connection.keep_alive()
            await asyncio.sleep(3)
    
    asyncio.create_task(keep_alive())
    
    # Set up transcript handler
    transcripts = asyncio.Queue()
    
    def on_message(result, **kwargs):
        sentence = result.channel.alternatives[0].transcript
        if sentence and result.is_final:
            transcripts.put_nowait(sentence)
    
    connection.on("Results", on_message)
    await connection.start()
    
    while True:
        audio = await audio_queue.get()
        await connection.send(audio)
        try:
            yield await asyncio.wait_for(transcripts.get(), timeout=0.1)
        except asyncio.TimeoutError:
            continue
```

### Step 3 — Stream LLM with sentence buffering

```python
async def stream_llm_to_tts(user_text: str, tts_input):
    """Send LLM tokens to TTS in sentence-sized chunks."""
    buffer = ""
    SENTENCE_END = {".", "!", "?", "\n"}
    
    async for chunk in client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": user_text}],
        stream=True,
    ):
        delta = chunk.choices[0].delta.content or ""
        buffer += delta
        # Emit the longest prefix ending in sentence punctuation
        while any(buffer.endswith(p) for p in SENTENCE_END):
            for p in SENTENCE_END:
                if buffer.endswith(p):
                    sentence = buffer
                    buffer = ""
                    await tts_input.put(sentence)
                    break
```

**Why sentence buffering?** TTS sounds choppy if you feed it 3-token chunks. A full sentence gives natural prosody.

### Step 4 — Stream TTS (ElevenLabs)

```python
import elevenlabs

async def tts_to_websocket(text_queue, ws):
    """Consume sentences, stream audio back to the user."""
    while True:
        sentence = await text_queue.get()
        
        # Streaming TTS — first chunk arrives in ~150ms
        audio_stream = elevenlabs.generate(
            text=sentence,
            voice="Rachel",
            stream=True,
        )
        
        async for audio_chunk in audio_stream:
            await ws.send(audio_chunk)   # WebSocket binary message → user speaker
```

### Step 5 — Interruption handling

The hardest part. If the user starts speaking while the agent is talking, the agent must stop talking within ~200ms.

```python
# VAD (Voice Activity Detection) runs in parallel with everything
async def interruption_monitor(audio_queue, tts_cancel_event):
    """Detect user speech during agent speech → cancel TTS."""
    vad = SileroVAD()
    while True:
        audio = await audio_queue.get()
        is_speaking = vad.is_speech(audio)
        
        if is_speaking and tts.is_currently_speaking():
            print("User interrupted — cancelling TTS")
            tts_cancel_event.set()
            await ws.send({"type": "agent_stopped"})
            # Clear pending sentences
            while not tts_input.empty():
                tts_input.get_nowait()

async def stream_llm_to_tts(user_text, tts_input, tts_cancel_event):
    buffer = ""
    async for chunk in client.chat.completions.create(...):
        if tts_cancel_event.is_set():
            return  # bail out
        # ... same as before
```

The trick: every streaming call checks the cancel event before doing work. Cancellation propagates in ~100ms.

### Step 6 — Measure the latency

```python
LATENCY_LOG = []

async def instrumented_session(ws):
    timings = {"stt_end": None, "llm_first_token": None, "tts_first_audio": None, "user_heard": None}
    
    # STT...
    timings["stt_end"] = time.perf_counter()
    
    # LLM first token
    timings["llm_first_token"] = time.perf_counter()
    
    # TTS first audio (sent to user)
    timings["tts_first_audio"] = time.perf_counter()
    
    # User "heard" first audio = send time + network RTT
    timings["user_heard"] = time.perf_counter()
    
    LATENCY_LOG.append({
        "stt_to_llm": (timings["llm_first_token"] - timings["stt_end"]) * 1000,
        "llm_to_tts": (timings["tts_first_audio"] - timings["llm_first_token"]) * 1000,
        "tts_to_user": (timings["user_heard"] - timings["tts_first_audio"]) * 1000,
        "total": (timings["user_heard"] - timings["stt_end"]) * 1000,
    })

import statistics
print(f"Median total latency: {statistics.median(l['total'] for l in LATENCY_LOG):.0f}ms")
print(f"P95 total latency:    {sorted(l['total'] for l in LATENCY_LOG)[int(len(LATENCY_LOG)*0.95)]:.0f}ms")
# Median ~600ms, P95 ~1100ms
```

### Step 7 — The latency budget

```
   COMPONENT           TARGET    P95
   ─────────           ─────    ───
   STT (per chunk)     50ms     80ms
   LLM TTFT            200ms    350ms
   TTS TTFA            150ms    300ms
   Network (RTT)       50ms     100ms
   Total (user → user) 450ms    830ms

   At P95 > 1s, conversation feels laggy.
   At P95 > 2s, users hang up.
```

### Step 8 — The cost model

```
   Per minute of conversation:
   STT (Deepgram):    $0.0043
   LLM  (GPT-4o-mini, 500 in + 500 out tokens):  $0.0009
   TTS  (ElevenLabs):  $0.018
   ────────────────────────────────────────────
   Total:              $0.023 / minute

   At 10K minutes/day: $230/day = $7K/month
   Per-user at 10 min/day, 100K users: $230K/day
   
   The TTS is 80% of the cost. STT is cheap. LLM is cheap.
   → Optimize TTS first (use a smaller model, batch sentences).
```

### Step 9 — The infrastructure pattern

```
   ┌─────────────────────────────────────────────────────────────┐
   │  DEPLOYMENT                                                 │
   │                                                             │
   │  - Single WebSocket per session (or WebRTC for lower RTT)   │
   │  - STT and TTS as managed APIs (Deepgram, ElevenLabs)       │
   │  - LLM streaming via API or self-hosted (vLLM for cost)     │
   │  - VAD on every audio frame (model runs on edge server)     │
   │  - Audio buffer (ring buffer, 200ms chunks)                 │
   │  - Cancel event propagates through STT/LLM/TTS              │
   │                                                             │
   │  Failure modes to handle:                                   │
   │  - STT API down → fall back to browser Web Speech API       │
   │  - LLM slow → start TTS on partial response                 │
   │  - TTS fails → fall back to text + browser TTS              │
   │  - User disconnects → flush all state, log for review       │
   └─────────────────────────────────────────────────────────────┘
```

---

## Voice agent optimizations

| Optimization | Latency saved | Cost |
|---|---|---|
| Speculative TTS (start TTS on partial LLM output) | 100-200ms | extra TTS calls (sometimes wasted) |
| Smaller TTS model (Flash vs HD) | 50-100ms | quality drop |
| Quantized LLM (INT4) | 50-100ms TTFT | small quality loss |
| WebRTC instead of WebSocket | 30-50ms RTT | complexity |
| Edge STT (browser-based) | 30-50ms | privacy win |
| Sentence-level pipelining | parallel stages | more memory |

---

## Cost roll-up

```
   Voice agent at 10K conversations/day, 5 min each:
   STT:   $215/month
   LLM:   $45/month
   TTS:   $900/month
   ────────────────
   Total: $1,160/month
   Per-call: $0.004
   
   Compare to human call center: $5-15/call
   AI voice is 1000-3000× cheaper, available 24/7, scales infinitely.
```

---

## What this example teaches

1. **Streaming everything is non-negotiable.** STT, LLM, TTS all stream. No waiting for full output.
2. **TTFT (time to first audio) is the metric.** Target < 500ms.
3. **Interruption handling is the UX.** Cancel propagates in < 200ms or it feels broken.
4. **TTS dominates cost.** Optimize there first.
5. **WebRTC > WebSocket** for real-time, but harder to deploy.

Read this and you understand why every conversational AI startup in 2026 ships a voice agent.

---

## What Comes Next

> Lesson 2 — **GPU Economics & Self-Hosting** — when to rent APIs vs own GPUs. The break-even math for fine-tuning and inference at scale.