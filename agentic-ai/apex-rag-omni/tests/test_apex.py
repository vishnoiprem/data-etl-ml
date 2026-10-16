"""Tests for the apex-rag-omni platform.

Each test class covers one component:
- test_router: domain classification + prompt template loading
- test_retriever: RRF fusion + shard routing
- test_answerer: grounding enforcement + citation extraction
- test_qdrant: stable shard hashing + dual-write semantics
- test_cdc: freshness stats over a window
- test_eval: Recall@8, nDCG@10, acceptance bar
"""
from __future__ import annotations

import math

import pytest

from agent.router import Domain, classify_domain, build_evidence_json
from agent.retriever import RetrievedDoc, rrf_fuse, top_k, shard_for
from agent.answerer import extract_citations, enforce_grounding, make_answer
from tools.qdrant import stable_shard_id, dual_write
from tools.cdc import freshness_report, CDCEvent
from eval.harness import (recall_at_k, ndcg_at_k, score_query,
                          run_harness, check_acceptance, EvalReport,
                          ACCEPTANCE)


class TestRouter:
    def test_classify_finance(self):
        assert classify_domain("What was Q3 revenue vs EBITDA?") == Domain.FINANCE

    def test_classify_legal(self):
        assert classify_domain("Show me the indemnity clause") == Domain.LEGAL

    def test_classify_medical(self):
        assert classify_domain("Patient shows symptoms of ICD-10 diagnosis") == Domain.MEDICAL

    def test_classify_default(self):
        assert classify_domain("hello world") == Domain.FINANCE

    def test_hint_overrides(self):
        assert classify_domain("x", hint=Domain.LEGAL) == Domain.LEGAL

    def test_evidence_no_spans_refused(self):
        ej = build_evidence_json("q", Domain.FINANCE, "ans", spans=[])
        assert ej.refused is True
        assert ej.refusal_reason is not None

    def test_evidence_with_spans_ok(self):
        from agent.router import EvidenceSpan
        spans = [EvidenceSpan(doc_id="0x1", offset=0, text="t", score=0.9)]
        ej = build_evidence_json("q", Domain.FINANCE, "ans", spans=spans)
        assert ej.refused is False
        assert len(ej.spans) == 1


class TestRetriever:
    def _doc(self, doc_id, v=0.0, b=0.0, rv=0, rb=0, score=0.0):
        return RetrievedDoc(
            doc_id=doc_id, text=f"text {doc_id}", vector_score=v,
            bm25_score=b, rrf_score=score, rank_vector=rv, rank_bm25=rb,
        )

    def test_rrf_fuse_basic(self):
        v = [self._doc("a", rv=1), self._doc("b", rv=2)]
        b = [self._doc("b", rb=1), self._doc("c", rb=2)]
        fused = rrf_fuse(v, b)
        assert fused[0].doc_id == "b"  # b is in both
        assert len(fused) == 3

    def test_rrf_score_math(self):
        # 1/(k+1) + 1/(k+1) when in both at rank 1
        v = [self._doc("a", rv=1)]
        b = [self._doc("a", rb=1)]
        fused = rrf_fuse(v, b)
        expected = 1.0 / 61 + 1.0 / 61
        assert abs(fused[0].rrf_score - expected) < 1e-9

    def test_top_k(self):
        v = [self._doc(str(i), rv=i) for i in range(1, 11)]
        b = []
        fused = rrf_fuse(v, b)
        assert len(top_k(fused, 5)) == 5

    def test_shard_stable(self):
        assert stable_shard_id("0x1234") == stable_shard_id("0x1234")
        # different doc_ids can land in different shards
        shards = {stable_shard_id(f"0x{i:064x}") for i in range(100)}
        assert len(shards) > 1  # hash distributes


class TestAnswerer:
    def _doc(self, doc_id, score=0.9):
        return RetrievedDoc(
            doc_id=doc_id, text=f"text {doc_id}", rrf_score=score,
        )

    def test_extract_citations(self):
        ans = "Revenue grew [doc_1] but margins shrank [doc_2]."
        assert extract_citations(ans) == [1, 2]

    def test_enforce_grounded(self):
        ans = "Cited [doc_1] and [doc_2] and [doc_3] and [doc_4] and [doc_5]."
        retrieved = [self._doc(str(i)) for i in range(1, 6)]
        ok, _ = enforce_grounding(ans, retrieved, type("T", (), {"citation_marker": "[doc_{i}]"})())
        assert ok is True

    def test_enforce_not_grounded(self):
        ans = "I think the answer is 42, no citations."
        retrieved = [self._doc(str(i)) for i in range(1, 6)]
        ok, reason = enforce_grounding(ans, retrieved, type("T", (), {"citation_marker": "[doc_{i}]"})())
        assert ok is False
        assert "citations" in reason.lower() or "coverage" in reason.lower()

    def test_make_answer_refused(self):
        retrieved = [self._doc("a"), self._doc("b")]
        ej, trace = make_answer("q", Domain.FINANCE, retrieved, "no citations")
        assert ej.refused is True
        assert trace.refused is True

    def test_make_answer_grounded(self):
        retrieved = [self._doc("a"), self._doc("b"), self._doc("c"), self._doc("d")]
        ans = "Answer [doc_1] [doc_2] [doc_3] [doc_4] covers everything."
        ej, trace = make_answer("q", Domain.FINANCE, retrieved, ans)
        assert ej.refused is False
        assert len(ej.spans) == 4


class TestQdrant:
    def test_stable_shard_distribution(self):
        # 1000 doc_ids should hit at least 2 of 10 shards
        shards = {stable_shard_id(f"0x{i:064x}") for i in range(1000)}
        assert len(shards) >= 2
        assert all(0 <= s < 10 for s in shards)

    def test_dual_write_consistent(self):
        docs = [(f"0x{i:064x}", [0.1] * 1536, f"text {i}") for i in range(100)]
        result = dual_write(docs, embed_model_version="v2")
        assert result.main_written == 100
        assert result.shadow_written == 100
        assert result.consistent is True


class TestCDC:
    def test_freshness_no_violations(self):
        from datetime import timedelta
        now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        samples = [(now - timedelta(seconds=30), now) for _ in range(100)]
        report = freshness_report(samples)
        assert report.sla_violations == 0
        assert report.p50_lag_seconds < 60

    def test_freshness_violations(self):
        from datetime import timedelta
        now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        samples = [(now - timedelta(seconds=600), now) for _ in range(100)]
        report = freshness_report(samples)
        assert report.sla_violations == 100


class TestEval:
    def test_recall_at_k_hit(self):
        assert recall_at_k(["a", "b", "c"], ["c", "x"], k=8) == 1.0

    def test_recall_at_k_miss(self):
        assert recall_at_k(["a", "b", "c"], ["x", "y"], k=8) == 0.0

    def test_ndcg_perfect(self):
        rel = {"a": 3, "b": 2, "c": 1}
        assert ndcg_at_k(["a", "b", "c"], rel, k=3) == pytest.approx(1.0)

    def test_ndcg_zero(self):
        assert ndcg_at_k(["a", "b"], {"x": 3, "y": 2}, k=2) == 0.0

    def test_acceptance_pass(self):
        r = EvalReport(
            timestamp="2026-10-16T00:00:00Z", n_samples=100,
            recall_at_8=0.90, ndcg_at_10=0.85,
            judge_groundedness=4.5, judge_completeness=4.0,
            judge_hallucination=1.0,
        )
        ok, failures = check_acceptance(r)
        assert ok is True
        assert failures == []

    def test_acceptance_fail_recall(self):
        r = EvalReport(
            timestamp="2026-10-16T00:00:00Z", n_samples=100,
            recall_at_8=0.70, ndcg_at_10=0.85,
            judge_groundedness=4.5, judge_completeness=4.0,
            judge_hallucination=1.0,
        )
        ok, failures = check_acceptance(r)
        assert ok is False
        assert any("Recall@8" in f for f in failures)


class TestEndToEnd:
    def test_run_harness_with_dummy_retrieve(self):
        from eval.harness import GoldItem

        def retrieve(q):
            return ["0xa", "0xb", "0xc"]

        def judge(q, r):
            return {"groundedness": 4.0, "completeness": 4.0, "hallucination": 1.0}

        gold = [GoldItem(
            query_id=f"q{i}", query=f"query {i}",
            gold_doc_ids=["0xa"], graded_relevance={"0xa": 3, "0xb": 1},
        ) for i in range(10)]
        report = run_harness(gold, retrieve, judge, out_path=None)
        assert report.n_samples == 10
        assert report.recall_at_8 == 1.0
