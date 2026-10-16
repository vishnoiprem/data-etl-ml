"""Zero-infra hybrid index: BM25 (lexical) + hashed n-gram vectors (dense proxy).

Not Qdrant/Elasticsearch — it is an honest in-process stand-in with the same
contract, so the whole app (retrieve -> fuse -> ground -> cite) runs for real
on a laptop. The "dense" side is a feature-hashed char-3gram/word vector with
cosine similarity: it catches morphology/typos that BM25 misses
("authenticate" ~ "authentication"), but it is NOT a semantic embedding model.
"""
from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from dataclasses import dataclass

from .corpus import CORPUS
from .document_store import passages

DIM = 1024
_WORD = re.compile(r"[a-z0-9]+")
STOP = frozenset(
    "a an the of to in on for and or is are was were be do does did how what when where which who i my me we our "
    "you your it its this that with at by from as can should will about get s t much many".split()
)


def stem(w: str) -> str:
    for suf in ("ations", "ation", "ings", "ing", "ies", "ed", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: -len(suf)]
    return w


def tokens(text: str) -> list[str]:
    return [stem(w) for w in _WORD.findall(text.lower()) if w not in STOP]


def _h(s: str) -> int:
    return int.from_bytes(hashlib.blake2b(s.encode(), digest_size=8).digest(), "big")


def embed(text: str) -> list[float]:
    v = [0.0] * DIM
    for w in tokens(text):
        v[_h("w:" + w) % DIM] += 1.0
        g = f"^{w}$"
        for i in range(len(g) - 2):
            v[_h("g:" + g[i : i + 3]) % DIM] += 0.5
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


@dataclass
class Doc:
    doc_id: str
    title: str
    text: str
    toks: Counter
    length: int
    vec: list[float]


class LocalIndex:
    def __init__(self, docs: list[tuple[str, str, str]]):
        self.docs: list[Doc] = []
        for doc_id, title, text in docs:
            tk = tokens(f"{title} {text}")
            self.docs.append(Doc(doc_id, title, text, Counter(tk), len(tk), embed(f"{title} {text}")))
        self.avgdl = sum(d.length for d in self.docs) / max(1, len(self.docs))
        df: Counter = Counter()
        for d in self.docs:
            df.update(d.toks.keys())
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    def bm25(self, query: str, k1: float = 1.5, b: float = 0.75) -> list[tuple[Doc, float]]:
        q = tokens(query)
        out = []
        for d in self.docs:
            s = 0.0
            for t in q:
                f = d.toks.get(t, 0)
                if f:
                    s += self.idf.get(t, 0.0) * f * (k1 + 1) / (f + k1 * (1 - b + b * d.length / self.avgdl))
            if s > 0:
                out.append((d, s))
        return sorted(out, key=lambda x: x[1], reverse=True)

    def vector(self, query: str) -> list[tuple[Doc, float]]:
        qv = embed(query)
        out = [(d, sum(a * b for a, b in zip(qv, d.vec))) for d in self.docs]
        return sorted([x for x in out if x[1] > 0.05], key=lambda x: x[1], reverse=True)


_INDEXES: dict[str, LocalIndex] = {}


def get_index(collection: str) -> LocalIndex:
    """Built-in demo corpus + user uploads, cached until invalidate()."""
    if collection not in _INDEXES:
        _INDEXES[collection] = LocalIndex(CORPUS[collection] + passages(collection))
    return _INDEXES[collection]


def invalidate(collection: str) -> None:
    _INDEXES.pop(collection, None)
