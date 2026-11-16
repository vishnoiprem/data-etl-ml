"""Tests for hybrid retrieval."""

from __future__ import annotations

from src.trade_sourcing_ai.retrieval import (
    BM25Index,
    Filters,
    HybridRetriever,
    reciprocal_rank_fusion,
    tokenize,
)


class TestTokenizer:
    def test_lowercases_and_splits(self):
        assert tokenize("Smart Watch fitness band") == ["smart", "watch", "fitness", "band"]

    def test_drops_stopwords(self):
        assert "the" not in tokenize("the supplier of the band")

    def test_keeps_numbers(self):
        assert "500" in tokenize("500 units")

    def test_handles_punctuation(self):
        assert tokenize("FOB: $8.50 (500u)") == ["fob", "8", "50", "500u"]


class TestBM25:
    def test_scores_are_non_negative(self, documents):
        index = BM25Index(documents)
        for score in index.score("fitness band supplier"):
            assert score >= 0

    def test_matching_document_outranks_non_matching(self, documents):
        index = BM25Index(documents)
        results = index.search("reusable water bottle", top_k=3)
        assert results
        assert "water bottle" in results[0][0].title.lower()

    def test_empty_query_returns_nothing(self, documents):
        index = BM25Index(documents)
        assert index.search("", top_k=5) == []

    def test_stopword_only_query_returns_nothing(self, documents):
        index = BM25Index(documents)
        assert index.search("the of and", top_k=5) == []

    def test_results_are_ordered_by_score(self, documents):
        index = BM25Index(documents)
        results = index.search("supplier risk level lead time", top_k=10)
        scores = [score for _, score in results]
        assert scores == sorted(scores, reverse=True)

    def test_rare_terms_carry_more_weight(self, documents):
        index = BM25Index(documents)
        results = index.search("qiyang", top_k=1)
        assert results
        assert "qiyang" in results[0][0].title.lower()


class TestReciprocalRankFusion:
    def test_merges_two_rankings(self, documents):
        by_id = {d.doc_id: d for d in documents}
        a = by_id["supplier:goldstar_2010"]
        b = by_id["supplier:ocom_2007"]
        fused = reciprocal_rank_fusion([[a], [b]])
        assert len(fused) == 2
        assert all(isinstance(score, float) for _, score in fused)

    def test_document_in_both_lists_scores_higher(self, documents):
        by_id = {d.doc_id: d for d in documents}
        a = by_id["supplier:goldstar_2010"]
        b = by_id["supplier:ocom_2007"]
        fused = reciprocal_rank_fusion([[a, b], [b]])
        scores = {doc.doc_id: score for doc, score in fused}
        assert scores[b.doc_id] > scores[a.doc_id]

    def test_empty_input_returns_empty(self):
        assert reciprocal_rank_fusion([]) == []


class TestFilters:
    def test_destination_filter_excludes_other_routes(self, documents):
        filters = Filters(dest_country="IN")
        for doc in documents:
            if doc.doc_type == "product":
                assert filters.allows(doc) == (doc.metadata["dest_country"] == "IN")

    def test_supplier_docs_survive_destination_filter(self, documents):
        filters = Filters(dest_country="IN")
        suppliers = [d for d in documents if d.doc_type == "supplier"]
        assert suppliers
        assert all(filters.allows(d) for d in suppliers)

    def test_min_margin_filter(self, documents):
        filters = Filters(min_margin=0.30)
        for doc in documents:
            if doc.doc_type == "product" and doc.metadata.get("margin_pct") is not None:
                assert filters.allows(doc) == (doc.metadata["margin_pct"] >= 0.30)

    def test_lead_time_filter(self, documents):
        filters = Filters(max_lead_time_days=18)
        for doc in documents:
            if doc.doc_type == "supplier":
                assert filters.allows(doc) == (doc.metadata["lead_time_days"] <= 18)

    def test_doc_type_filter(self, documents):
        filters = Filters(doc_types=("supplier",))
        for doc in documents:
            assert filters.allows(doc) == (doc.doc_type == "supplier")


class TestHybridRetriever:
    def test_search_returns_hits(self, retriever):
        result = retriever.search("fitness band supplier", top_k=5)
        assert result["hits"]
        assert len(result["hits"]) <= 5

    def test_ranks_are_sequential(self, retriever):
        result = retriever.search("supplier lead time", top_k=5)
        assert [h.rank for h in result["hits"]] == list(range(1, len(result["hits"]) + 1))

    def test_dense_disabled_is_reported(self, retriever):
        result = retriever.search("supplier", top_k=3)
        assert result["dense_enabled"] is False

    def test_stages_are_reported(self, retriever):
        result = retriever.search("supplier", top_k=3)
        names = [s["name"] for s in result["stages"]]
        assert names == ["bm25", "dense", "fusion"]

    def test_stage_latencies_are_present(self, retriever):
        result = retriever.search("supplier", top_k=3)
        for stage in result["stages"]:
            assert stage["latency_ms"] >= 0
            assert stage["status"] in {"success", "empty", "skipped", "failed"}

    def test_filters_are_applied(self, retriever):
        result = retriever.search(
            "supplier", top_k=10, filters=Filters(dest_country="IN")
        )
        for hit in result["hits"]:
            if hit.doc.doc_type == "product":
                assert hit.doc.metadata["dest_country"] == "IN"

    def test_filters_are_echoed(self, retriever):
        result = retriever.search("supplier", top_k=3, filters=Filters(dest_country="IN"))
        assert result["filters_applied"]["dest_country"] == "IN"

    def test_hit_serialises_with_provenance(self, retriever):
        result = retriever.search("supplier", top_k=1)
        payload = result["hits"][0].to_dict()
        assert payload["source_path"]
        assert payload["source_line"] > 0
        assert payload["doc_id"]

    def test_search_is_deterministic(self, documents):
        first = HybridRetriever(documents, use_dense=False).search("supplier", top_k=5)
        second = HybridRetriever(documents, use_dense=False).search("supplier", top_k=5)
        assert [h.doc.doc_id for h in first["hits"]] == [
            h.doc.doc_id for h in second["hits"]
        ]

    def test_queries_with_no_match_return_nothing(self, retriever):
        result = retriever.search("zzzzqqqq nonexistent term", top_k=5)
        assert result["hits"] == []


class TestDenseDegradation:
    def test_missing_model_degrades_to_lexical(self, documents):
        retriever = HybridRetriever(
            documents, use_dense=True, model_name="nonexistent/model-that-does-not-exist"
        )
        result = retriever.search("supplier", top_k=3)
        assert result["dense_enabled"] is False
        assert result["dense_reason"]
        assert result["hits"]

    def test_search_still_works_without_dense(self, documents):
        retriever = HybridRetriever(
            documents, use_dense=True, model_name="nonexistent/model-that-does-not-exist"
        )
        result = retriever.search("fitness band", top_k=3)
        assert result["hits"]
