"""
Tests for the RAG pipeline
===========================
Run:  pytest tests/
"""

import os
import pytest
from rag import RAGPipeline, chunk_text, count_tokens


# =============================================================================
# UNIT TESTS (no API calls)
# =============================================================================

def test_count_tokens():
    assert count_tokens("Hello, world!") == 4
    assert count_tokens("") == 0
    assert count_tokens("The quick brown fox") > 0


def test_chunk_text_basic():
    text = " ".join(["word"] * 100)
    chunks = chunk_text(text, chunk_size=20, overlap=5)
    assert len(chunks) > 1
    # Each chunk should be smaller than chunk_size
    for c in chunks:
        assert count_tokens(c) <= 25  # some slack for overlap decode


def test_chunk_text_short():
    """Short text should fit in one chunk."""
    text = "This is a short text."
    chunks = chunk_text(text, chunk_size=100, overlap=10)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_overlap():
    """Consecutive chunks should have overlapping tokens."""
    text = " ".join([f"word{i}" for i in range(100)])
    chunks = chunk_text(text, chunk_size=30, overlap=10)
    assert len(chunks) >= 2
    # Last token of chunk 0 should appear in chunk 1
    assert chunks[0].split()[-1] in chunks[1]


# =============================================================================
# INTEGRATION TESTS (require API keys)
# =============================================================================

@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") or not os.getenv("PINECONE_API_KEY"),
    reason="API keys not set",
)
def test_rag_end_to_end():
    """End-to-end test: index, query, verify citation."""
    rag = RAGPipeline(
        openai_api_key=os.environ["OPENAI_API_KEY"],
        pinecone_api_key=os.environ["PINECONE_API_KEY"],
    )

    # Index a test document
    test_doc_id = "test-doc-001"
    rag.index_document(
        user_id="test-user",
        document_id=test_doc_id,
        title="Test Doc",
        pages=[
            "Refunds are processed within 5 business days. To request a refund, email support@example.com.",
            "We accept Visa, Mastercard, and PayPal. American Express is not supported.",
        ],
    )

    # Query
    result = rag.query(
        user_id="test-user",
        question="How long do refunds take?",
    )

    assert "answer" in result
    assert "citations" in result
    assert len(result["citations"]) > 0
    # The answer should mention 5 business days (from the source)
    assert "5" in result["answer"] or "five" in result["answer"].lower()
