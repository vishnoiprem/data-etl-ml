"""BM25 index using rank-bm25. Same search signature as VectorIndex."""
from __future__ import annotations

import re
from dataclasses import dataclass

from rank_bm25 import BM25Okapi  # type: ignore

from .config import get_settings
from .ingestion import Doc, read_jsonl, write_jsonl


@dataclass
class BM25Hit:
    chunk_id: str
    doc_id: str
    text: str
    score: float


_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


class BM25Index:
    def __init__(self) -> None:
        self._bm25: BM25Okapi | None = None
        self._chunks: list[Doc] = []

    def build(self, chunks: list[Doc]) -> None:
        if not chunks:
            raise ValueError("No chunks to index.")
        self._chunks = chunks
        tokenized = [_tokenize(c.text) for c in chunks]
        self._bm25 = BM25Okapi(tokenized)

    def search(self, query: str, k: int | None = None) -> list[BM25Hit]:
        if self._bm25 is None:
            raise RuntimeError("BM25 index is empty — call build() first.")
        k = k or get_settings().top_k_bm25
        scores = self._bm25.get_scores(_tokenize(query))
        order = scores.argsort()[::-1][:k]
        return [
            BM25Hit(
                chunk_id=self._chunks[i].chunk_id,
                doc_id=self._chunks[i].doc_id,
                text=self._chunks[i].text,
                score=float(scores[i]),
            )
            for i in order
            if scores[i] > 0
        ]

    def save(self, prefix: str = "bm25") -> None:
        s = get_settings()
        write_jsonl(
            [{"doc_id": c.doc_id, "chunk_id": c.chunk_id, "text": c.text, "title": c.title} for c in self._chunks],
            s.chunks_path(prefix),
        )

    def load(self, prefix: str = "bm25") -> None:
        s = get_settings()
        path = s.chunks_path(prefix)
        if not path.exists():
            raise FileNotFoundError(f"Missing BM25 chunks at {path}")
        self._chunks = [Doc(doc_id=d["doc_id"], chunk_id=d["chunk_id"], text=d["text"], title=d.get("title", "")) for d in read_jsonl(path)]
        # Rebuild the BM25 object from the loaded chunks
        tokenized = [_tokenize(c.text) for c in self._chunks]
        self._bm25 = BM25Okapi(tokenized)
