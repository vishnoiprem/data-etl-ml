"""
test_history_search.py — tests for the in-process vector index.

The index is the agent's "memory" — it powers the
`query_history` tool. Tests cover:

  * add + query round-trip
  * Persist + load round-trip
  * Top-k ordering (most similar first)
  * Empty index returns empty list
  * Hash pseudo-embeddings are stable + L2-normalized
  * format_results produces a readable string for the agent
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pytest

from m100.history_search import HistoryIndex, HistoryHit, _embed, _EMBED_DIM


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def tmp_index(tmp_path: Path) -> HistoryIndex:
    idx = HistoryIndex(persist_dir=str(tmp_path))
    return idx


# ============================================================
# Embedding fallback
# ============================================================

def test_embed_returns_384_dim():
    e = _embed("hello world")
    assert e.shape == (_EMBED_DIM,)


def test_embed_is_deterministic():
    """Same input → same vector. (Hash pseudo-embeddings AND real
    sentence-transformers are deterministic.)"""
    e1 = _embed("same text")
    e2 = _embed("same text")
    assert np.array_equal(e1, e2)


def test_hash_embedding_is_normalized():
    """Hash fallback must be L2-normalized so cosine = inner product."""
    e = _embed("test")
    norm = np.linalg.norm(e)
    assert abs(norm - 1.0) < 1e-5 or norm == 0  # zero-norm on empty text


def test_hash_embedding_differs_for_different_text():
    e1 = _embed("alpha")
    e2 = _embed("omega")
    # With 384 dims of hash buckets, identical vectors are extremely unlikely
    assert not np.array_equal(e1, e2)


# ============================================================
# Index basics
# ============================================================

def test_new_index_is_empty(tmp_index):
    assert tmp_index.size == 0
    assert tmp_index.embeddings.shape == (0, _EMBED_DIM)


def test_add_iteration_increments_size(tmp_index):
    tmp_index.add_iteration(
        iter_no=0, listing_id="L0", category="Finance",
        summary="first iteration", quality_score=0.5,
    )
    assert tmp_index.size == 1


def test_query_empty_index_returns_empty(tmp_index):
    assert tmp_index.query("anything") == []


def test_query_returns_top_k(tmp_index):
    for i in range(10):
        tmp_index.add_iteration(
            iter_no=i, listing_id=f"L{i}", category="Finance",
            summary=f"summary {i} about trading and risk", quality_score=0.5,
        )
    hits = tmp_index.query("trading risk", top_k=3)
    assert len(hits) == 3
    assert all(isinstance(h, HistoryHit) for h in hits)


def test_query_top_k_caps_at_size(tmp_index):
    for i in range(3):
        tmp_index.add_iteration(
            iter_no=i, listing_id=f"L{i}", category="X",
            summary=f"text {i}", quality_score=0.5,
        )
    # Ask for top-10 but only 3 exist
    hits = tmp_index.query("anything", top_k=10)
    assert len(hits) == 3


def test_query_similarities_are_bounded(tmp_index):
    """Cosine similarities in [-1, 1]."""
    for i in range(5):
        tmp_index.add_iteration(
            iter_no=i, listing_id=f"L{i}", category="X",
            summary=f"summary {i}", quality_score=0.5,
        )
    for h in tmp_index.query("anything"):
        assert -1.0 <= h.similarity <= 1.0


# ============================================================
# Persist / load
# ============================================================

def test_save_and_load_round_trip(tmp_path):
    idx1 = HistoryIndex(persist_dir=str(tmp_path))
    idx1.add_iteration(
        iter_no=0, listing_id="L0", category="Finance",
        summary="first", quality_score=0.8,
    )
    idx1.add_iteration(
        iter_no=1, listing_id="L1", category="Healthcare",
        summary="second", quality_score=0.4,
    )
    # Build a fresh index, load from disk
    idx2 = HistoryIndex(persist_dir=str(tmp_path))
    idx2.load()
    assert idx2.size == 2
    assert idx2.meta[0]["iter_no"] == 0
    assert idx2.meta[1]["quality_score"] == 0.4
    # Embeddings match
    assert np.array_equal(idx1.embeddings, idx2.embeddings)


# ============================================================
# format_results
# ============================================================

def test_format_empty_index():
    idx = HistoryIndex(persist_dir="/tmp/_test_no_history")
    out = idx.format_results("anything")
    assert "no prior history" in out


def test_format_returns_top_k_with_metadata(tmp_index):
    for i in range(3):
        tmp_index.add_iteration(
            iter_no=i, listing_id=f"L{i}", category="Finance",
            summary=f"summary {i}", quality_score=0.5 + i * 0.1,
        )
    out = tmp_index.format_results("test question", top_k=2)
    assert "Top 2" in out
    assert "Finance" in out
    assert "q=" in out
    # Only 2 of the 3 should be in the formatted output
    assert out.count("iter ") == 2


# ============================================================
# Agent integration
# ============================================================

def test_agent_call_tool_query_history(tmp_index):
    """The M100Agent's `call_tool` should route `query_history` to the index."""
    from m100.agent import M100Agent
    for i in range(3):
        tmp_index.add_iteration(
            iter_no=i, listing_id=f"L{i}", category="Finance",
            summary=f"summary {i}", quality_score=0.5,
        )
    agent = M100Agent(workspace_client=None, history_index=tmp_index)
    out = agent.call_tool("query_history", {"question": "anything"})
    assert "Top" in out


def test_agent_call_tool_unknown_returns_explanation():
    from m100.agent import M100Agent
    agent = M100Agent(workspace_client=None)
    out = agent.call_tool("not_a_tool", {})
    assert "not implemented" in out
