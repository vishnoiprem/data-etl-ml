"""
Voice Activity Detection (VAD) using Silero.

Decides when a chunk of audio contains speech. Emits a stream of
speech-segment events with start/end timestamps. The downstream
transcriber only runs on speech segments, not silence.
"""
from __future__ import annotations
import time
from collections import deque
from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass
class SpeechSegment:
    start_ts: float
    end_ts: float
    samples: np.ndarray   # int16, 16kHz


class SileroVAD:
    """Toy VAD based on RMS energy. Real impl: Silero VAD model."""

    def __init__(self, sample_rate: int = 16000, frame_ms: int = 30,
                 energy_threshold: float = 0.01, min_speech_ms: int = 250):
        self.sample_rate = sample_rate
        self.frame_size = int(sample_rate * frame_ms / 1000)
        self.energy_threshold = energy_threshold
        self.min_speech_frames = int(min_speech_ms / frame_ms)
        self._is_speech = False
        self._speech_start: float | None = None
        self._buffer: list[np.ndarray] = []

    def _rms(self, frame: np.ndarray) -> float:
        return float(np.sqrt(np.mean(np.square(frame.astype(np.float32) / 32768.0))))

    def feed(self, pcm_chunk: np.ndarray, t0: float | None = None) -> list[SpeechSegment]:
        """Feed PCM (int16, 16kHz). Returns any completed segments."""
        t0 = t0 if t0 is not None else time.time()
        segments: list[SpeechSegment] = []
        i = 0
        while i + self.frame_size <= len(pcm_chunk):
            frame = pcm_chunk[i : i + self.frame_size]
            ts = t0 + i / self.sample_rate
            energy = self._rms(frame)
            is_speech = energy > self.energy_threshold
            if is_speech and not self._is_speech:
                self._is_speech = True
                self._speech_start = ts
                self._buffer = [frame]
            elif is_speech and self._is_speech:
                self._buffer.append(frame)
            elif not is_speech and self._is_speech:
                # End of speech segment
                self._is_speech = False
                if len(self._buffer) >= self.min_speech_frames:
                    segments.append(SpeechSegment(
                        start_ts=self._speech_start,
                        end_ts=ts,
                        samples=np.concatenate(self._buffer),
                    ))
                self._buffer = []
            i += self.frame_size
        return segments


if __name__ == "__main__":
    vad = SileroVAD()
    # 5s of fake audio: 2s of speech, 1s silence, 2s of speech
    pcm = np.zeros(16000 * 5, dtype=np.int16)
    pcm[0:16000*2] = (np.random.randn(16000*2) * 8000).astype(np.int16)  # "speech"
    pcm[16000*3:16000*5] = (np.random.randn(16000*2) * 8000).astype(np.int16)
    segs = vad.feed(pcm, t0=0.0)
    print(f"detected {len(segs)} segments: {[(round(s.start_ts,2), round(s.end_ts,2)) for s in segs]}")
