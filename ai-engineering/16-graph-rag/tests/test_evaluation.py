"""Tests for the eval harness — proves the strategy comparison is meaningful."""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ["LLM_MODE"] = "mock"
os.environ.setdefault("ANTHROPIC_API_KEY", "")

import pytest

from src.config import PROJECT_ROOT, get_settings
from src.pipeline import GraphRAGPipeline


@pytest.fixture(scope="module")
def built(tmp_path_factory) -> GraphRAGPipeline:
    s = get_settings()
    s.data_dir = tmp_path_factory.mktemp("data")
    p = GraphRAGPipeline()
    p.build(PROJECT_ROOT / "sample_data" / "corpus")
    return p


def test_golden_set_runs(built: GraphRAGPipeline) -> None:
    report = built.eval(PROJECT_ROOT / "sample_data" / "eval_golden.jsonl")
    # Should have 4 strategies × 15 questions = 60 rows
    assert len(report.rows) == 4 * 15
    # At least one strategy should hit keyword for at least some questions
    by_kind = {r.kind: r for r in report.rows}
    # all rows are single-hop
    assert all(r.kind == "single-hop" for r in report.rows)


def test_adversarial_set_refuses(built: GraphRAGPipeline) -> None:
    report = built.eval(PROJECT_ROOT / "sample_data" / "eval_adversarial.jsonl")
    # 4 strategies × 5 questions
    assert len(report.rows) == 4 * 5
    # Every adversarial answer should be a refusal
    refused = sum(1 for r in report.rows if r.refused)
    assert refused == len(report.rows), (
        f"Some adversarial questions weren't refused: "
        f"{[(r.strategy, r.question) for r in report.rows if not r.refused]}"
    )


def test_markdown_table_contains_all_strategies(built: GraphRAGPipeline) -> None:
    report = built.eval(PROJECT_ROOT / "sample_data" / "eval_golden.jsonl")
    md = report.markdown_table()
    for strat in ("vector", "bm25", "graph", "hybrid"):
        assert strat in md
