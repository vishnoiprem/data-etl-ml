"""Context packing with a hard token budget.

Greedy by score, with explicit drop reporting. Never silently truncates.
"""
from __future__ import annotations

from dataclasses import dataclass, field


def approx_tokens(text: str) -> int:
    """Cheap token estimate: ~1.3 tokens per whitespace-separated word."""
    return max(1, int(len(text.split()) * 1.3))


@dataclass
class Chunk:
    chunk_id: str
    text: str
    score: float
    title: str = ""

    @property
    def token_count(self) -> int:
        return approx_tokens(self.text)


@dataclass
class PackResult:
    included: list[Chunk] = field(default_factory=list)
    dropped: list[tuple[Chunk, str]] = field(default_factory=list)   # (chunk, reason)
    used_tokens: int = 0
    budget: int = 0

    @property
    def utilization(self) -> float:
        return self.used_tokens / self.budget if self.budget else 0.0


def pack_context(
    chunks: list[Chunk],
    budget_tokens: int,
    reserved_tokens: int = 0,
) -> PackResult:
    """Greedy pack by descending score. Returns explicit included + dropped lists."""
    available = max(0, budget_tokens - reserved_tokens)
    result = PackResult(budget=available)
    sorted_chunks = sorted(chunks, key=lambda c: -c.score)
    for c in sorted_chunks:
        if result.used_tokens + c.token_count <= available:
            result.included.append(c)
            result.used_tokens += c.token_count
        else:
            result.dropped.append((c, f"would exceed budget by {result.used_tokens + c.token_count - available} tokens"))
    return result
