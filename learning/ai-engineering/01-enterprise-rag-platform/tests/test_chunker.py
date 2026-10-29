"""Smoke tests for the RAG pipeline."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from src.ingestion.chunker import RecursiveChunker, count_tokens
from src.ingestion.loader import Document


def test_chunker_respects_size():
    long_text = "Hello world. " * 500
    doc = Document(doc_id="t1", text=long_text, source="test", title="test")
    chunker = RecursiveChunker(chunk_size=128, overlap=16)
    chunks = chunker.chunk(doc)
    assert len(chunks) >= 2
    for c in chunks:
        # Allow small overshoot for boundary handling
        assert count_tokens(c.text) <= 200, f"chunk too big: {count_tokens(c.text)}"


def test_chunker_preserves_content():
    text = "## Section A\nFirst paragraph.\n\n## Section B\nSecond paragraph."
    doc = Document(doc_id="t1", text=text, source="test", title="test")
    chunks = RecursiveChunker(chunk_size=512).chunk(doc)
    joined = " ".join(c.text for c in chunks)
    assert "First paragraph" in joined
    assert "Second paragraph" in joined


def test_chunk_ids_stable():
    text = "Some sample text content."
    doc = Document(doc_id="t1", text=text, source="test", title="test")
    a = RecursiveChunker().chunk(doc)
    b = RecursiveChunker().chunk(doc)
    assert [c.chunk_id for c in a] == [c.chunk_id for c in b]
