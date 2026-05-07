"""BM25 sparse retrieval for the LOCAL backend.

In AWS mode this is unused — OpenSearch's `match` query does BM25 natively
and the hybrid module fuses it with k-NN in a single request.

For LOCAL mode we use rank_bm25 with a simple whitespace + lowercase
tokenizer. Fine for demos; for production text quality, use a proper
analyzer (stop words, stemming).
"""
from __future__ import annotations

import pickle
import re
from pathlib import Path
from typing import Sequence

from loguru import logger
from rank_bm25 import BM25Okapi

from src.config import settings
from src.ingestion.chunker import Chunk


_TOKEN_RE = re.compile(r"\b[\w']+\b")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class BM25Retriever:
    INDEX_FILE = "bm25.pkl"

    def __init__(self, index_dir: Path | None = None):
        self.index_dir = Path(index_dir or settings.INDEX_DIR)
        self.bm25: BM25Okapi | None = None
        self.chunks: list[Chunk] = []
        self._load()

    def _load(self):
        path = self.index_dir / self.INDEX_FILE
        if path.exists():
            data = pickle.loads(path.read_bytes())
            self.bm25 = data["bm25"]
            self.chunks = data["chunks"]
            logger.info(f"Loaded BM25 index with {len(self.chunks)} chunks")

    def _persist(self):
        path = self.index_dir / self.INDEX_FILE
        path.write_bytes(pickle.dumps({"bm25": self.bm25, "chunks": self.chunks}))

    def fit(self, chunks: Sequence[Chunk]) -> None:
        self.chunks = list(chunks)
        tokenized = [_tokenize(c.text) for c in self.chunks]
        self.bm25 = BM25Okapi(tokenized)
        self._persist()
        logger.info(f"BM25 fit on {len(self.chunks)} chunks")

    def search(self, query: str, k: int = 50, filters: dict | None = None) -> list[tuple[Chunk, float]]:
        if not self.bm25 or not self.chunks:
            return []
        scores = self.bm25.get_scores(_tokenize(query))
        # Sort all, then filter then trim — small enough for in-process scoring
        indexed = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        out: list[tuple[Chunk, float]] = []
        for i, s in indexed:
            chunk = self.chunks[i]
            if filters and not self._matches(chunk, filters):
                continue
            if s <= 0:
                continue
            out.append((chunk, float(s)))
            if len(out) >= k:
                break
        return out

    @staticmethod
    def _matches(chunk: Chunk, filters: dict) -> bool:
        for key, expected in filters.items():
            actual = getattr(chunk, key, None) or chunk.metadata.get(key)
            if isinstance(expected, (list, tuple, set)):
                if actual not in expected:
                    return False
            elif actual != expected:
                return False
        return True
