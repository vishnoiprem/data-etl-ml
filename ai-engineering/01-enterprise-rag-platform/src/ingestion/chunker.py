"""Chunking strategies.

Two implementations:
- `RecursiveChunker` (default) — splits along structural boundaries (paragraphs,
  sentences) with token-aware sizing. Fast, deterministic, respects document
  structure.
- `SemanticChunker` — splits at semantic boundaries by clustering adjacent
  sentences with low embedding similarity. Slower but better for unstructured
  prose.

Both produce `Chunk` objects with stable IDs and back-pointer metadata.
"""
from __future__ import annotations

import hashlib
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterable

from loguru import logger

from src.ingestion.loader import Document


# Tokenizer used for measuring chunk size. Prefer tiktoken cl100k_base
# (gpt-style BPE) as a universal proxy across embedding models; fall back
# to a whitespace-based heuristic if the encoding can't be loaded
# (e.g. air-gapped or sandboxed environments).
_ENC = None
try:
    import tiktoken
    _ENC = tiktoken.get_encoding("cl100k_base")
except Exception as e:  # offline / restricted network
    logger.warning(f"tiktoken unavailable ({e}); using whitespace token approximation")


def count_tokens(text: str) -> int:
    if _ENC is not None:
        return len(_ENC.encode(text))
    # Heuristic: ~1.3 tokens per whitespace-separated word
    return max(1, int(len(text.split()) * 1.3))


def _encode_decode_fallback(text: str, n: int, op: str):
    """Minimal encode/decode used only when tiktoken is unavailable."""
    if op == "encode":
        return text.split()
    return " ".join(text)


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    text: str
    chunk_index: int
    total_chunks: int
    source: str
    title: str
    metadata: dict = field(default_factory=dict)

    @classmethod
    def from_text(cls, doc: Document, text: str, idx: int, total: int) -> "Chunk":
        chunk_id = hashlib.sha256(
            f"{doc.doc_id}::{idx}::{text[:50]}".encode()
        ).hexdigest()[:16]
        return cls(
            chunk_id=chunk_id,
            doc_id=doc.doc_id,
            text=text,
            chunk_index=idx,
            total_chunks=total,
            source=doc.source,
            title=doc.title,
            metadata=dict(doc.metadata),
        )


class Chunker(ABC):
    @abstractmethod
    def chunk(self, doc: Document) -> list[Chunk]:
        ...


class RecursiveChunker(Chunker):
    """Token-aware recursive splitting on hierarchical separators.

    Tries to split on the largest natural boundary first (double newlines,
    headings), falling back to smaller ones (single newline, sentence, word)
    until each piece fits the target size.
    """

    SEPARATORS = ["\n\n## ", "\n\n# ", "\n\n", "\n", ". ", " "]

    def __init__(self, chunk_size: int = 512, overlap: int = 64):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def _split_recursive(self, text: str, separators: list[str]) -> list[str]:
        """Recursive splitter — keeps splitting on smaller separators until pieces fit."""
        if count_tokens(text) <= self.chunk_size:
            return [text]
        if not separators:
            # Hard fall-through: split by token windows
            return self._token_window_split(text)

        sep, *rest = separators
        parts = text.split(sep)
        if len(parts) == 1:
            return self._split_recursive(text, rest)

        # Reattach the separator to keep semantic continuity
        parts = [parts[0]] + [sep + p for p in parts[1:]]
        result: list[str] = []
        for part in parts:
            if count_tokens(part) <= self.chunk_size:
                result.append(part)
            else:
                result.extend(self._split_recursive(part, rest))
        return result

    def _token_window_split(self, text: str) -> list[str]:
        if _ENC is not None:
            tokens = _ENC.encode(text)
            chunks = []
            step = max(1, self.chunk_size - self.overlap)
            for start in range(0, len(tokens), step):
                window = tokens[start:start + self.chunk_size]
                chunks.append(_ENC.decode(window))
                if start + self.chunk_size >= len(tokens):
                    break
            return chunks
        # Fallback: word-window split
        words = text.split()
        chunks = []
        step = max(1, self.chunk_size - self.overlap)
        for start in range(0, len(words), step):
            chunks.append(" ".join(words[start:start + self.chunk_size]))
            if start + self.chunk_size >= len(words):
                break
        return chunks

    def _merge_with_overlap(self, parts: list[str]) -> list[str]:
        """Greedily pack small parts into chunks of ~chunk_size with overlap.

        Overlap is implemented by carrying forward the last `overlap` tokens
        of the previous chunk into the next. This preserves context across
        chunk boundaries — important for retrieval recall.
        """
        merged: list[str] = []
        current = ""
        for part in parts:
            candidate = (current + part).strip()
            if count_tokens(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    merged.append(current)
                # Overlap: take last `overlap` tokens of `current` and prepend
                if current and self.overlap > 0:
                    if _ENC is not None:
                        tail_tokens = _ENC.encode(current)[-self.overlap:]
                        tail = _ENC.decode(tail_tokens)
                    else:
                        tail = " ".join(current.split()[-self.overlap:])
                    current = (tail + " " + part).strip()
                else:
                    current = part.strip()
        if current:
            merged.append(current)
        return merged

    def chunk(self, doc: Document) -> list[Chunk]:
        text = re.sub(r"\n{3,}", "\n\n", doc.text).strip()
        if not text:
            return []

        parts = self._split_recursive(text, self.SEPARATORS)
        merged = self._merge_with_overlap(parts)
        chunks = [Chunk.from_text(doc, t, i, len(merged)) for i, t in enumerate(merged)]
        logger.debug(f"Chunked '{doc.title}' into {len(chunks)} chunks")
        return chunks


class SemanticChunker(Chunker):
    """Splits at points where adjacent sentence embeddings diverge.

    Lazily imports sentence-transformers so projects that don't use this
    chunker don't pay the load time.
    """

    def __init__(
        self,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        breakpoint_percentile: float = 95.0,
        max_chunk_tokens: int = 512,
    ):
        self.embedding_model_name = embedding_model
        self.breakpoint_percentile = breakpoint_percentile
        self.max_chunk_tokens = max_chunk_tokens
        self._model = None

    def _model_lazy(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.embedding_model_name)
        return self._model

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        # Lightweight splitter; for production consider a real sentence segmenter.
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        return [s for s in sentences if s]

    def chunk(self, doc: Document) -> list[Chunk]:
        import numpy as np
        sentences = self._split_sentences(doc.text)
        if len(sentences) <= 1:
            return [Chunk.from_text(doc, doc.text, 0, 1)] if doc.text.strip() else []

        embeddings = self._model_lazy().encode(sentences, show_progress_bar=False)
        # Cosine distance between adjacent sentences
        distances = []
        for i in range(len(embeddings) - 1):
            a, b = embeddings[i], embeddings[i + 1]
            cos = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))
            distances.append(1.0 - cos)

        threshold = float(np.percentile(distances, self.breakpoint_percentile))
        breakpoints = [i + 1 for i, d in enumerate(distances) if d > threshold]

        chunks_text: list[str] = []
        start = 0
        for bp in breakpoints + [len(sentences)]:
            piece = " ".join(sentences[start:bp])
            if count_tokens(piece) > self.max_chunk_tokens:
                # Fall back to recursive within an overgrown piece
                rec = RecursiveChunker(self.max_chunk_tokens, 64)
                inner = rec.chunk(Document(doc_id=doc.doc_id, text=piece, source=doc.source, title=doc.title))
                chunks_text.extend(c.text for c in inner)
            elif piece.strip():
                chunks_text.append(piece)
            start = bp

        return [Chunk.from_text(doc, t, i, len(chunks_text)) for i, t in enumerate(chunks_text)]


def chunk_documents(docs: Iterable[Document], chunker: Chunker | None = None) -> list[Chunk]:
    chunker = chunker or RecursiveChunker()
    all_chunks: list[Chunk] = []
    for doc in docs:
        all_chunks.extend(chunker.chunk(doc))
    logger.info(f"Produced {len(all_chunks)} chunks")
    return all_chunks
