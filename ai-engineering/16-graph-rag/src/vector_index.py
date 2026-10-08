"""FAISS inner-product index over L2-normalised embeddings + parallel text store."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .config import get_settings
from .embeddings import embed
from .ingestion import Doc, read_jsonl, write_jsonl


@dataclass
class Hit:
    chunk_id: str
    doc_id: str
    text: str
    score: float


class VectorIndex:
    """Wraps a FAISS index plus a parallel JSONL chunk store."""

    def __init__(self) -> None:
        self._index = None
        self._chunks: list[Doc] = []
        self._dim: int | None = None

    # ---- build ---------------------------------------------------------

    def build(self, chunks: list[Doc]) -> None:
        from faiss import IndexFlatIP  # type: ignore

        if not chunks:
            raise ValueError("No chunks to index.")
        self._chunks = chunks
        texts = [c.text for c in chunks]
        vecs = embed(texts)
        self._dim = vecs.shape[1]
        self._index = IndexFlatIP(self._dim)
        self._index.add(vecs)

    # ---- search --------------------------------------------------------

    def search(self, query: str, k: int | None = None) -> list[Hit]:
        from faiss import IndexFlatIP  # type: ignore

        if self._index is None:
            raise RuntimeError("Vector index is empty — call build() first.")
        k = k or get_settings().top_k_vector
        q = embed([query])
        scores, ids = self._index.search(q, min(k, len(self._chunks)))
        out: list[Hit] = []
        for score, idx in zip(scores[0].tolist(), ids[0].tolist()):
            if idx < 0:
                continue
            c = self._chunks[idx]
            out.append(Hit(chunk_id=c.chunk_id, doc_id=c.doc_id, text=c.text, score=float(score)))
        return out

    # ---- persist -------------------------------------------------------

    def save(self, prefix: str = "vector") -> None:
        import faiss  # type: ignore

        s = get_settings()
        idx_path = s.index_path(prefix)
        chunks_path = s.chunks_path(prefix)
        faiss.write_index(self._index, str(idx_path))
        write_jsonl(
            [{"doc_id": c.doc_id, "chunk_id": c.chunk_id, "text": c.text, "title": c.title} for c in self._chunks],
            chunks_path,
        )

    def load(self, prefix: str = "vector") -> None:
        import faiss  # type: ignore

        s = get_settings()
        idx_path = s.index_path(prefix)
        chunks_path = s.chunks_path(prefix)
        if not idx_path.exists() or not chunks_path.exists():
            raise FileNotFoundError(f"Missing index or chunks file for {prefix}")
        self._index = faiss.read_index(str(idx_path))
        self._chunks = [Doc(doc_id=d["doc_id"], chunk_id=d["chunk_id"], text=d["text"], title=d.get("title", "")) for d in read_jsonl(chunks_path)]
        self._dim = self._index.d
