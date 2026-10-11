"""ElevenLabs-style voice synthesis + streaming: first-frame latency is the product.

The interesting engineering: TTFB (time-to-first-byte) is dominated by
the first-frame synthesis, not the streaming. If you can synthesize
the first 80ms of audio in parallel with the rest of the utterance,
your TTFB drops from 200ms to ~80ms.

The toy captures the streaming pipeline + the per-chunk latency budget.
Real TTS uses VITS / XTTS / Bark / StyleTTS2.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field


@dataclass
class AudioChunk:
    pcm_bytes: bytes
    sample_rate: int
    duration_ms: float


@dataclass
class TTSRequest:
    text: str
    voice_id: str
    stream: bool = True
    target_chunk_ms: float = 80.0   # first-frame budget


@dataclass
class TTSResult:
    chunks: list[AudioChunk] = field(default_factory=list)
    ttfb_ms: float = 0.0
    total_ms: float = 0.0


class StreamingTTS:
    """Toy streaming TTS that emits chunks at target_chunk_ms granularity."""

    def __init__(self, first_frame_ms: float = 80.0, chunk_ms: float = 80.0):
        self.first_frame_ms = first_frame_ms
        self.chunk_ms = chunk_ms

    def synthesize(self, req: TTSRequest) -> TTSResult:
        t0 = time.time()
        n_chunks = max(1, int(len(req.text) / 10))   # ~10 chars per chunk
        chunks: list[AudioChunk] = []
        for i in range(n_chunks):
            # First chunk takes first_frame_ms; rest are chunk_ms each
            chunk_dur = self.first_frame_ms if i == 0 else self.chunk_ms
            time.sleep(chunk_dur / 1000)
            chunks.append(AudioChunk(
                pcm_bytes=b"\x00\x00" * int(req.target_chunk_ms * 16),  # 16 kHz mono
                sample_rate=16_000,
                duration_ms=req.target_chunk_ms,
            ))
        t1 = time.time()
        return TTSResult(
            chunks=chunks,
            ttfb_ms=(t1 - t0) * 1000 - (n_chunks - 1) * self.chunk_ms,
            total_ms=(t1 - t0) * 1000,
        )


if __name__ == "__main__":
    tts = StreamingTTS(first_frame_ms=80.0, chunk_ms=80.0)
    req = TTSRequest(text="Hello, this is a streaming TTS test of about 60 characters.", voice_id="v1")
    result = tts.synthesize(req)
    print(f"text length: {len(req.text)} chars")
    print(f"chunks emitted: {len(result.chunks)}")
    print(f"TTFB: {result.ttfb_ms:.1f} ms")
    print(f"total: {result.total_ms:.1f} ms")
    print(f"per-chunk duration (audio): {result.chunks[0].duration_ms} ms")
    print(f"first chunk audio bytes: {len(result.chunks[0].pcm_bytes)}")
