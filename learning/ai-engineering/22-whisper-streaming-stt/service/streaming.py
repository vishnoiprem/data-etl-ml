"""
Streaming partial-emit + finalize state machine.

On every chunk, emit a partial that's stable for >= 300ms.
On VAD silence, finalize the last segment.
This is the layer that makes the UI feel smooth instead of flickering.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class PartialTranscript:
    text: str
    is_final: bool
    ts: float


class StreamingState:
    def __init__(self, stable_ms: int = 300, on_partial: Optional[Callable] = None):
        self.stable_ms = stable_ms
        self.on_partial = on_partial
        self._last_emit_ts: float = 0.0
        self._last_emit_text: str = ""
        self._finalized: list[str] = []

    def feed(self, new_text: str, is_final: bool = False) -> list[PartialTranscript]:
        """Returns any partials/finals to emit. Calls on_partial for each."""
        out: list[PartialTranscript] = []
        now = time.time()

        if is_final:
            self._finalized.append(new_text)
            out.append(PartialTranscript(text=new_text, is_final=True, ts=now))
        else:
            # Emit only the suffix that changed, and only if it's been stable.
            changed = new_text[len(self._last_emit_text):] if new_text.startswith(self._last_emit_text) else new_text
            stable_for_ms = (now - self._last_emit_ts) * 1000
            if changed and stable_for_ms >= self.stable_ms:
                out.append(PartialTranscript(text=new_text, is_final=False, ts=now))
                self._last_emit_text = new_text
                self._last_emit_ts = now

        if self.on_partial:
            for p in out:
                self.on_partial(p)
        return out


if __name__ == "__main__":
    state = StreamingState(stable_ms=200)
    # Simulate partial emissions
    for partial in ["I", "I want", "I want to", "I want to book", "I want to book a", "I want to book a flight"]:
        time.sleep(0.05)  # shorter than stable_ms for first few
        emitted = state.feed(partial)
        for e in emitted:
            print(f"  partial: {e.text!r}")
    # Finalize
    final = state.feed("I want to book a flight to Tokyo", is_final=True)
    for f in final:
        print(f"  final:   {f.text!r}")
