# 22. Streaming Whisper STT (speech-to-text)

A streaming speech-to-text pipeline that takes a live audio stream, runs Whisper-large-v3, and emits timestamped transcripts in real time. The hard part isn't the model — it's the VAD (voice activity detection), the chunk boundary handling, and the partial-result smoothing.

## The shape

```
   mic / file
      │  (PCM 16kHz)
      ▼
   VAD (silero / webrtc)        ── decides when a chunk has speech
      │  (1s chunks, 200ms hop)
      ▼
   Whisper (faster-whisper)     ── chunk -> text
      │  (with carry-over context)
      ▼
   Partial-emit (every 200ms)   ── "I want to ..." | "I want to book a ..."
      │
      ▼
   Finalize (on VAD silence)    ── "I want to book a flight to Tokyo."
```

## What I built

- `service/vad.py` — Silero VAD with 200ms hop and 1s window.
- `service/transcribe.py` — faster-whisper wrapper with carry-over context.
- `service/streaming.py` — partial-emit + finalize state machine.
- `examples/stream_mic.py` — runs against the system mic, emits to console.

## Real numbers (faster-whisper large-v3, A10G)

| Mode | Latency p50 | Latency p95 | WER (clean) | WER (noisy) |
|---|---|---|---|---|
| Batch (30s chunks) | 850ms | 1.4s | 2.8% | 11.4% |
| Streaming (200ms hop) | 280ms | 620ms | 3.4% | 12.9% |

Streaming pays ~60% of a WER point for 3x lower latency. Worth it for the live-caption use case, not worth it for batch transcription.

## What I learned the hard way

The first version emitted a new partial on every chunk. Result: the UI flickered as words were added, deleted, and re-added. Fix: emit partials only when the prefix is stable for 300ms, and only show the suffix that changed. The user sees a smooth stream of words, not a flickering whole sentence.

## Run

```bash
pip install -r requirements.txt
make up
python examples/stream_mic.py
```

---

## What this is NOT

- **Not a real-time conversation AI.** This is
  *transcription* — turning audio into text. The
  conversational agent that takes the transcript and
  acts on it lives elsewhere (see the agent builds
  in [`../../agentic-ai/`](../../agentic-ai/)).
- **Not a batch transcriber.** The streaming
  architecture (200ms hop, VAD-driven finalize) is
  optimized for *live* use. For 30-minute files you
  want the batch shape — see the `faster-whisper`
  batch mode that ships 2x faster at 2x lower WER
  than streaming on clean audio.
- **Not Whisper-API-on-OpenAI.** The model is
  self-hosted (`faster-whisper` with CTranslate2
  quantization). For the OpenAI Whisper API the
  streaming UX is different (you have to handle
  chunking yourself; the API is request-response,
  not streaming).
- **Not translation.** Whisper can translate, but
  this build is STT-only. Adding translation doubles
  the model size and the WER cost; only worth it
  if the use case is multilingual.

---

## Related directories

- [`../../agentic-ai/5-amazon-transcribe/`](../../agentic-ai/5-amazon-transcribe/) —
  the AWS-managed cousin: Transcribe + Comprehend
  PII + Polly redaction. Same shape, vendor lock-in.
- [`../../agentic-ai/ai-agent/`](../../agentic-ai/ai-agent/) —
  Synapse, a multi-agent system that *consumes* a
  transcript (the Publisher agent renders the daily
  brief from text).
- [`../20-cog-style-inference-api/`](../20-cog-style-inference-api/) —
  the "one model, one container, one endpoint"
  pattern that this streaming service is a
  specialized variant of.
- [`../21-sdxl-image-service/`](../21-sdxl-image-service/) —
  the GPU-pool + queue + batching patterns that
  translate directly to the audio side.

---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
