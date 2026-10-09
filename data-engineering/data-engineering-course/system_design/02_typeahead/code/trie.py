"""A simple trie with a precomputed top-K per node.

We precompute and freeze the top-K at build time so queries are O(p)
walk + O(1) slice. K is small (default 10), so the per-node storage
cost is acceptable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class TrieNode:
    children: dict[str, "TrieNode"] = field(default_factory=dict)
    top_k: list[tuple[str, int]] = field(default_factory=list)  # (word, freq), sorted desc
    is_word: bool = False


class Trie:
    """A prefix tree with precomputed top-K suggestions per node.

    >>> t = Trie()
    >>> t.insert("flask", 1000)
    >>> t.insert("flash", 800)
    >>> t.insert("flat", 600)
    >>> t.insert("apple", 500)
    >>> [w for w, _ in t.suggest("fla")]
    ['flask', 'flash', 'flat']
    """

    def __init__(self, k: int = 10):
        self.k = k
        self.root = TrieNode()

    # ---- build --------------------------------------------------------

    def insert(self, word: str, freq: int) -> None:
        word = word.lower()
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
            # Maintain a sorted top-k at this node, descending by freq,
            # with word as a tiebreaker for determinism.
            entry = (word, freq)
            inserted = False
            for i, existing in enumerate(node.top_k):
                if freq > existing[1] or (freq == existing[1] and word < existing[0]):
                    node.top_k.insert(i, entry)
                    inserted = True
                    break
            if not inserted:
                node.top_k.append(entry)
            if len(node.top_k) > self.k:
                node.top_k.pop()
        node.is_word = True

    def build_from(self, words: Iterable[tuple[str, int]]) -> int:
        """Insert all (word, freq) pairs; return count inserted."""
        n = 0
        for word, freq in words:
            self.insert(word, freq)
            n += 1
        return n

    # ---- query --------------------------------------------------------

    def suggest(self, prefix: str) -> list[tuple[str, int]]:
        prefix = (prefix or "").lower()
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return []
            node = node.children[ch]
        return list(node.top_k)

    def has(self, word: str) -> bool:
        word = word.lower()
        node = self.root
        for ch in word:
            if ch not in node.children:
                return False
            node = node.children[ch]
        return node.is_word

    def size(self) -> int:
        # Approximate node count.
        n = 0
        stack = [self.root]
        while stack:
            n += 1
            cur = stack.pop()
            stack.extend(cur.children.values())
        return n
