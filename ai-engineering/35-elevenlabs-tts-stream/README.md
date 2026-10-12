# ElevenLabs-style voice synthesis + streaming

Sub-200ms TTFB streaming TTS. The latency budget is dominated by the first-frame synthesis, not the streaming. The trick: synthesize the first 80ms of audio as a separate, parallel stage and stream it the moment it's ready.

## Shape

```
                text
                 │
                 ▼
        ┌──────────────────┐
        │ StreamingTTS     │
        │ synthesize()     │
        └────┬─────────────┘
             │
   ┌─────────┼─────────┐
   ▼         ▼         ▼
  chunk 0   chunk 1   chunk 2 ...     <-- 80ms each, first one is the TTFB
  (TTFB)    (stream)  (stream)
   │
   ▼
  client starts playback
  while rest of the chunks are still being synthesized
```

## What I built

- `serve/streaming.py` — `AudioChunk` + `TTSRequest` + `TTSResult` + `StreamingTTS.synthesize()`.
- The toy simulates per-chunk latency: first chunk = `first_frame_ms` (the TTFB), rest = `chunk_ms` each.
- `TTSResult.ttfb_ms` and `total_ms` let you measure the budget.
- Smoke test: a 60-char utterance, ~6 chunks at 80ms each, prints TTFB and total.

## Real numbers

- ElevenLabs Turbo v2.5: TTFB ~120ms, real-time factor 0.3 (1s of audio in 300ms).
- Target TTFB: < 200ms p50; > 300ms feels laggy in conversation.
- Chunk size: 80ms is the standard (12.5 chunks/sec at 16 kHz).
- Voice cloning: works from 30-60s of clean reference audio; below that, identity drift.
- Emotion control: pitch + energy + duration features; most open-weights models don't expose this.

## What I learned the hard way

- **TTFB is the product metric.** Total latency matters less; the user hears the first frame and judges from there.
- **Chunk boundaries should be at silent-ish spots.** If you cut mid-word, you get a click. Most codecs force chunk alignment to phoneme boundaries.
- **The first frame should be parallel to the rest.** Synthesize chunk 0 in parallel with chunks 1..N; emit chunk 0 the moment it's ready.
- **Streaming without backpressure is a memory leak.** If the client is slow, you fill the buffer. Use a bounded queue + drop policy.
- **Voice cloning is fragile.** Background noise, reverb, multiple speakers in the reference — all of these silently degrade the clone quality. Clean reference audio is the single biggest lever.

## When to use

- Conversational agents (chatbots, IVR, voice assistants).
- Audiobook narration where the user can pause/resume.
- Real-time translation overlays.

## When NOT to use

- Pre-rendered audio (just batch-synthesize; streaming is wasted).
- Languages with no good open-weights TTS model.
- Latency budgets under 100ms TTFB (impossible with current models).

## Run

```bash
pip install -r requirements.txt
make smoke
```
---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
