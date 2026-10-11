"""Mistral-style self-hosted LLM serving: prefix cache + token-budget guard.

The two features that make self-hosted Llama-class serving actually
usable: (1) a prefix cache so we don't re-encode the system prompt on
every request, (2) a token-budget guard so a 200K-context request
doesn't melt the cluster.
"""
from __future__ import annotations
from collections import OrderedDict
from dataclasses import dataclass, field


@dataclass
class CachedPrompt:
    prompt_hash: str
    token_count: int
    hits: int = 0


class PrefixCache:
    """LRU cache of (prompt_prefix_hash, token_count) -> was-in-cache."""

    def __init__(self, max_entries: int = 1024):
        self._cache: OrderedDict[str, CachedPrompt] = OrderedDict()
        self.max_entries = max_entries

    def check(self, prompt: str) -> tuple[bool, int]:
        h = hash(prompt)
        if h in self._cache:
            self._cache.move_to_end(h)
            self._cache[h].hits += 1
            return True, self._cache[h].token_count
        return False, 0

    def store(self, prompt: str, token_count: int) -> None:
        h = hash(prompt)
        self._cache[h] = CachedPrompt(prompt_hash=str(h), token_count=token_count)
        self._cache.move_to_end(h)
        if len(self._cache) > self.max_entries:
            self._cache.popitem(last=False)

    def stats(self) -> dict:
        total = sum(c.hits for c in self._cache.values())
        return {
            "entries": len(self._cache),
            "total_hits": total,
            "max_entries": self.max_entries,
        }


class TokenBudgetGuard:
    """Refuse requests whose (prompt + expected_output) > budget."""

    def __init__(self, max_total_tokens: int = 32_000):
        self.max_total_tokens = max_total_tokens

    def allow(self, prompt_tokens: int, max_output_tokens: int) -> tuple[bool, str]:
        total = prompt_tokens + max_output_tokens
        if total > self.max_total_tokens:
            return False, f"total {total} > budget {self.max_total_tokens}"
        return True, "ok"


if __name__ == "__main__":
    cache = PrefixCache(max_entries=3)
    guard = TokenBudgetGuard(max_total_tokens=10_000)

    # First request with a long system prompt: cache miss, ~1500 prompt tokens
    system = "You are a helpful assistant. " * 100  # ~1500 tokens
    miss, n = cache.check(system)
    print(f"first  call: cache_hit={miss}, prompt_tokens={n}")
    cache.store(system, 1500)

    # Second request with the same system prompt: cache hit
    miss, n = cache.check(system)
    print(f"second call: cache_hit={miss}, prompt_tokens={n} (re-encoded {n if not miss else 0})")

    # Now check the budget guard
    ok, msg = guard.allow(prompt_tokens=1500, max_output_tokens=500)
    print(f"normal request: allowed={ok} ({msg})")
    ok, msg = guard.allow(prompt_tokens=9500, max_output_tokens=2000)
    print(f"too-long request: allowed={ok} ({msg})")

    print(f"\ncache stats: {cache.stats()}")
