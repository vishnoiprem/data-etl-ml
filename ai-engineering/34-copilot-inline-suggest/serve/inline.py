"""GitHub Copilot-style inline suggestion engine: streaming + debounce + prefix cache.

The latency budget is the product. A few details that matter:
1. Debounce: don't generate while the user is still typing (200-400ms
   is the sweet spot).
2. Prefix cache: if the system prompt / recent file context is the
   same as the last suggestion, don't re-encode it.
3. Token-by-token streaming: the user sees "ghost text" the moment
   the first token is ready, not after the full completion.
"""
from __future__ import annotations
import time
from collections import deque
from dataclasses import dataclass, field


@dataclass
class SuggestionRequest:
    user_id: str
    prefix: str
    suffix: str = ""
    max_tokens: int = 64
    debounce_ms: int = 250


@dataclass
class SuggestionResult:
    text: str
    latency_first_token_ms: float
    latency_total_ms: float
    cache_hit: bool
    tokens: int = 0


class Debouncer:
    """Buffers keystrokes; flushes only after `settle_ms` of quiet."""

    def __init__(self, settle_ms: int = 250):
        self.settle_ms = settle_ms
        self._last_input_ts: float = 0.0

    def should_emit(self, now: float) -> bool:
        if (now - self._last_input_ts) * 1000 >= self.settle_ms:
            self._last_input_ts = now
            return True
        return False


class PrefixCache:
    """Tiny demo cache: keyed on (prefix_hash, suffix_hash) -> encoded token count."""

    def __init__(self, max_entries: int = 256):
        self._store: dict[tuple[int, int], int] = {}
        self._hits = 0
        self._misses = 0
        self.max_entries = max_entries

    def check(self, prefix: str, suffix: str) -> tuple[bool, int]:
        k = (hash(prefix), hash(suffix))
        if k in self._store:
            self._hits += 1
            return True, self._store[k]
        self._misses += 1
        return False, 0

    def store(self, prefix: str, suffix: str, token_count: int) -> None:
        if len(self._store) >= self.max_entries:
            self._store.pop(next(iter(self._store)))
        self._store[(hash(prefix), hash(suffix))] = token_count

    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return self._hits / total if total else 0.0


class CopilotEngine:
    def __init__(self, model_tokens_per_sec: float = 80.0):
        self.debouncer = Debouncer(settle_ms=250)
        self.cache = PrefixCache(max_entries=256)
        self.model_tokens_per_sec = model_tokens_per_sec

    def suggest(self, req: SuggestionRequest) -> SuggestionResult:
        t0 = time.time()
        if not self.debouncer.should_emit(t0):
            return SuggestionResult(text="", latency_first_token_ms=0, latency_total_ms=0, cache_hit=False)
        hit, cached_tokens = self.cache.check(req.prefix, req.suffix)
        # Simulate: cache hit saves the prefill cost (50ms)
        prefill_ms = 0 if hit else 50
        time.sleep(prefill_ms / 1000)
        # Simulate streaming: 1st token at 50ms, total = prefill + (n_tokens / tps) * 1000
        n_tokens = min(req.max_tokens, max(1, len(req.prefix) // 4))
        gen_ms = (n_tokens / self.model_tokens_per_sec) * 1000
        t1 = time.time()
        self.cache.store(req.prefix, req.suffix, n_tokens)
        return SuggestionResult(
            text=f"// suggestion for: {req.prefix[:30]}...",
            latency_first_token_ms=(t1 - t0) * 1000 + 50,
            latency_total_ms=(t1 - t0) * 1000 + prefill_ms + gen_ms,
            cache_hit=hit,
            tokens=n_tokens,
        )


if __name__ == "__main__":
    eng = CopilotEngine()
    # Simulate 5 keystrokes 100ms apart, then a stable period
    for i in range(5):
        r = SuggestionRequest(user_id="u1", prefix=f"def add_{i}(a, b):", max_tokens=32)
        result = eng.suggest(r)
        time.sleep(0.1)
    # Now a stable request (same prefix as last)
    r = SuggestionRequest(user_id="u1", prefix="def add_4(a, b):", max_tokens=32)
    result = eng.suggest(r)
    print(f"cache hit: {result.cache_hit}, total latency: {result.latency_total_ms:.1f}ms, "
          f"first token: {result.latency_first_token_ms:.1f}ms")
    print(f"cache hit rate: {eng.cache.hit_rate:.2%}")
