"""Exact-match cache + crude semantic cache."""
from __future__ import annotations

import hashlib
import re
from collections import OrderedDict
from dataclasses import dataclass


@dataclass
class CacheEntry:
    response: str
    model_key: str
    in_tokens: int
    out_tokens: int


class ExactCache:
    """Bounded LRU keyed on hash(prompt + model + temperature)."""

    def __init__(self, max_size: int = 10_000):
        self._store: "OrderedDict[str, CacheEntry]" = OrderedDict()
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    @staticmethod
    def _key(prompt: str, model_key: str, temperature: float = 0.0) -> str:
        h = hashlib.sha256(f"{prompt}|{model_key}|{temperature:.3f}".encode()).hexdigest()
        return h[:32]

    def get(self, prompt: str, model_key: str, temperature: float = 0.0) -> CacheEntry | None:
        k = self._key(prompt, model_key, temperature)
        if k in self._store:
            self.hits += 1
            self._store.move_to_end(k)
            return self._store[k]
        self.misses += 1
        return None

    def put(self, prompt: str, model_key: str, entry: CacheEntry, temperature: float = 0.0):
        k = self._key(prompt, model_key, temperature)
        self._store[k] = entry
        self._store.move_to_end(k)
        if len(self._store) > self.max_size:
            self._store.popitem(last=False)


def normalize_for_semantic(prompt: str) -> str:
    """Crude semantic-cache normalization — lowercase, strip punctuation, trim."""
    s = prompt.lower().strip()
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


class SemanticCache(ExactCache):
    """Stand-in for semantic cache — normalizes the prompt before hashing.

    In production this is replaced by an embedding lookup against
    Redis-VS or pgvector with a similarity threshold (~0.95).
    """

    def get(self, prompt: str, model_key: str, temperature: float = 0.0):
        return super().get(normalize_for_semantic(prompt), model_key, temperature)

    def put(self, prompt: str, model_key: str, entry: "CacheEntry", temperature: float = 0.0):
        super().put(normalize_for_semantic(prompt), model_key, entry, temperature)
