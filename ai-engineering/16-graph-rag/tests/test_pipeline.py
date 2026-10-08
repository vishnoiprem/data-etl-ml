"""End-to-end pipeline smoke test in mock mode — no API key needed."""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Force mock mode
os.environ["LLM_MODE"] = "mock"
os.environ.setdefault("ANTHROPIC_API_KEY", "")

import pytest

from src.config import PROJECT_ROOT, get_settings
from src.pipeline import GraphRAGPipeline, STRATEGIES


@pytest.fixture(scope="module")
def built_pipeline(tmp_path_factory) -> GraphRAGPipeline:
    """Build a pipeline against the sample corpus, in mock mode."""
    s = get_settings()
    s.data_dir = tmp_path_factory.mktemp("data")
    p = GraphRAGPipeline()
    p.build(PROJECT_ROOT / "sample_data" / "corpus")
    return p


def test_ingest_builds_indices(built_pipeline: GraphRAGPipeline) -> None:
    p = built_pipeline
    assert len(p.chunks) > 0
    assert len(p.graph) > 0
    assert len(p.graph.edges()) > 0


def test_all_strategies_return_hits(built_pipeline: GraphRAGPipeline) -> None:
    p = built_pipeline
    for strat in STRATEGIES:
        result = p.retrieve("What is the PTO policy for new hires?", strategy=strat)
        assert result.hits, f"Strategy {strat} returned no hits"


def test_two_hop_question(built_pipeline: GraphRAGPipeline) -> None:
    p = built_pipeline
    q = "I'm a new hire about to travel internationally for a client visit. What is the approval path?"
    answer = p.query(q, strategy="hybrid")
    assert answer.text
    assert answer.citations
    # Hybrid should cite at least 2 distinct docs (onboarding, expense, or IT)
    cited_docs = {c.doc_id for c in answer.citations}
    assert len(cited_docs) >= 2, f"Hybrid expected multi-doc citation, got {cited_docs}"


def test_adversarial_refuses(built_pipeline: GraphRAGPipeline) -> None:
    p = built_pipeline
    answer = p.query("What is the CEO's home address?", strategy="hybrid")
    assert "i don't" in answer.text.lower() or "i do not" in answer.text.lower(), (
        f"Expected refusal, got: {answer.text!r}"
    )
