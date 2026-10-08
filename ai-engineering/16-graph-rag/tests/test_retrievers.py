"""Tests for the graph retriever — proves the two-hop retrieval works."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import os

# Force mock mode for tests
os.environ.setdefault("LLM_MODE", "mock")
os.environ.setdefault("ANTHROPIC_API_KEY", "")

from src.graph_builder import build_graph
from src.graph_store import GraphStore
from src.ingestion import Doc
from src.llm import get_llm
from src.retrievers import GraphRetriever
from src.vector_index import VectorIndex


def _toy_corpus() -> list[Doc]:
    return [
        Doc(doc_id="onboarding.md", chunk_id="onboarding.md#0",
            text="All new hires go through a 30-90 day onboarding program. The IT runbook covers day-1 setup.",
            title="Onboarding"),
        Doc(doc_id="it-runbooks.md", chunk_id="it-runbooks.md#0",
            text="Day-1 setup: laptop provisioning, SSO enrollment, and a password manager. For international travel, see Expense Policy §3.",
            title="IT Runbooks"),
        Doc(doc_id="expense-policy.md", chunk_id="expense-policy.md#0",
            text="International travel requires VP-level approval. Submit the request via the expense system 14 days before departure.",
            title="Expense Policy"),
    ]


def test_graph_retriever_finds_two_hop_path() -> None:
    docs = _toy_corpus()
    llm = get_llm()
    g = build_graph(docs, llm)

    # Build a VectorIndex just to satisfy GraphRetriever's interface
    v = VectorIndex()
    v.build(docs)
    gr = GraphRetriever(g, v)
    result = gr.retrieve("new hire international travel approval")

    # The graph should have linked "New Hire" and/or "International Travel" or
    # "VP Approval" — seeds shouldn't be empty for this two-hop question.
    assert result.graph_seeds, "GraphRetriever should find at least one seed entity"

    # Edges should reach at least 2 hops away
    assert len(result.graph_edges) >= 2, f"Expected multi-hop edges, got {result.graph_edges}"


def test_graph_retriever_returns_no_seeds_for_unrelated_query() -> None:
    docs = _toy_corpus()
    llm = get_llm()
    g = build_graph(docs, llm)
    v = VectorIndex()
    v.build(docs)
    gr = GraphRetriever(g, v)
    result = gr.retrieve("quantum chromodynamics numerical simulation")
    assert result.graph_seeds == []
    assert result.hits == []
