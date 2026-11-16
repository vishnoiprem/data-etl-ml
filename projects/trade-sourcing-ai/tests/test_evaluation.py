"""Tests for the eval harness.

The harness asserts its own thresholds, so this is the module that would
fail if retrieval or the decision logic regressed.
"""

from __future__ import annotations

import pytest

from src.trade_sourcing_ai.evaluation import (
    ACCEPTANCE,
    build_gold_decisions,
    build_gold_queries,
    check_acceptance,
    mrr,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    run_harness,
)


class TestMetrics:
    def test_recall_at_k(self):
        assert recall_at_k(["a", "b", "c"], ["a"], k=3) == 1.0
        assert recall_at_k(["x", "y", "z"], ["a"], k=3) == 0.0

    def test_recall_respects_k(self):
        assert recall_at_k(["x", "a"], ["a"], k=1) == 0.0
        assert recall_at_k(["x", "a"], ["a"], k=2) == 1.0

    def test_recall_with_no_gold_is_zero(self):
        assert recall_at_k(["a"], [], k=1) == 0.0

    def test_precision_divides_by_k_not_by_hits(self):
        """Returning fewer results must not inflate precision."""
        assert precision_at_k(["a"], ["a"], k=5) == pytest.approx(0.2)
        assert precision_at_k(["a", "b", "c"], ["a"], k=5) == pytest.approx(0.2)

    def test_precision_with_no_results(self):
        assert precision_at_k([], ["a"], k=5) == 0.0

    def test_mrr(self):
        assert mrr(["x", "a", "b"], ["a"]) == pytest.approx(0.5)
        assert mrr(["x"], ["a"]) == 0.0

    def test_ndcg(self):
        assert ndcg_at_k(["a", "b"], ["a", "b"], k=2) == pytest.approx(1.0)
        assert ndcg_at_k(["x"], ["a"], k=2) == 0.0

    def test_ndcg_rewards_relevant_items_early(self):
        """With binary relevance, nDCG rewards putting a relevant document
        first over burying it below an irrelevant one."""
        assert ndcg_at_k(["a", "x"], ["a"], k=2) > ndcg_at_k(["x", "a"], ["a"], k=2)

    def test_ndcg_penalises_a_relevant_item_buried_below_relevant_ones(self):
        """Two relevant items, one retrieved first: better than the reverse."""
        assert ndcg_at_k(["a", "b", "x"], ["a", "b"], k=3) > ndcg_at_k(
            ["x", "a", "b"], ["a", "b"], k=3
        )


class TestGoldSets:
    def test_every_gold_document_exists(self):
        from src.trade_sourcing_ai.corpus import build_corpus

        known = {doc.doc_id for doc in build_corpus()}
        for gold in build_gold_queries():
            for doc_id in gold.gold_doc_ids:
                assert doc_id in known, f"{gold.query!r} points at {doc_id}"

    def test_gold_queries_have_notes(self):
        for gold in build_gold_queries():
            assert gold.note

    def test_gold_decisions_cover_both_outcomes(self, all_quote_dicts):
        decisions = build_gold_decisions(all_quote_dicts)
        assert any(d.expect_rejection for d in decisions)
        assert any(not d.expect_rejection for d in decisions)

    def test_gold_decisions_reference_real_quotes(self, all_quote_dicts):
        decisions = build_gold_decisions(all_quote_dicts)
        for decision in decisions:
            for quote in decision.quotes:
                assert quote["alibaba_id"]
                assert quote["fob_usd"] > 0


class TestHarness:
    @pytest.fixture(scope="class")
    @staticmethod
    def report():
        return run_harness(use_dense=False)

    def test_report_produces_metrics(self, report):
        assert report.n_queries > 0
        assert report.n_decisions > 0
        assert 0.0 <= report.recall_at_5 <= 1.0
        assert 0.0 <= report.ndcg_at_5 <= 1.0

    def test_decisions_are_all_correct(self, report):
        assert report.decision_accuracy == 1.0

    def test_acceptance_thresholds_are_met(self, report):
        passed, failures = check_acceptance(report)
        assert passed, failures

    def test_summary_renders(self, report):
        text = report.summary()
        assert "Retrieval" in text
        assert "Decisions" in text
        assert "Acceptance" in text

    def test_report_serialises(self, report):
        import json

        json.dumps(report.to_dict())

    def test_thresholds_are_defined(self):
        assert set(ACCEPTANCE) == {
            "recall_at_5",
            "ndcg_at_5",
            "mrr",
            "decision_accuracy",
        }
