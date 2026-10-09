"""Typeahead service: dictionary loader + LRU-cached suggest API."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

from common.cache import LRUCache

from .trie import Trie


DEFAULT_DICT = Path(__file__).resolve().parent.parent.parent / "sample_data" / "dictionary.jsonl"


class TypeaheadService:
    """Loads a dictionary into a Trie and serves top-K suggestions.

    >>> s = TypeaheadService(k=5)
    >>> s.load_default()
    True
    >>> out = s.suggest("flas")
    >>> len(out) <= 5
    True
    """

    def __init__(self, k: int = 10, cache_size: int = 5_000):
        self.k = k
        self._trie = Trie(k=k)
        self._cache = LRUCache(max_entries=cache_size)

    def load_default(self) -> bool:
        return self.load_jsonl(DEFAULT_DICT)

    def load_jsonl(self, path: Path) -> bool:
        if not Path(path).exists():
            return False
        words = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                words.append((obj["word"], int(obj["freq"])))
        self._trie = Trie(k=self.k)
        self._trie.build_from(words)
        self._cache.clear()
        return True

    def suggest(self, prefix: str, k: Optional[int] = None) -> list[tuple[str, int]]:
        limit = k or self.k
        cache_key = (prefix, limit)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
        result = self._trie.suggest(prefix)[:limit]
        self._cache.set(cache_key, result)
        return result

    def has(self, word: str) -> bool:
        return self._trie.has(word)

    def stats(self) -> dict:
        return {
            "trie_nodes": self._trie.size(),
            "k": self.k,
            **self._cache.stats(),
        }
