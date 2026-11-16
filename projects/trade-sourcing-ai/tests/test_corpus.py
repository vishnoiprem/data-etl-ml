"""Tests for the corpus module.

These assert the corpus is built from the real trade-finder data and that
every document can be traced back to a source file.
"""

from __future__ import annotations

from pathlib import Path

from src.trade_sourcing_ai.corpus import (
    build_corpus,
    build_product_documents,
    build_reputation_documents,
    build_supplier_documents,
    corpus_summary,
    trade_finder_modules,
)


class TestTradeFinderModules:
    def test_modules_import(self):
        modules = trade_finder_modules()
        assert set(modules) == {"find_opportunities", "verify_suppliers", "demand_in"}

    def test_modules_are_cached(self):
        assert trade_finder_modules() is trade_finder_modules()

    def test_suppliers_are_real(self):
        modules = trade_finder_modules()
        assert len(modules["verify_suppliers"].SUPPLIERS) == 10

    def test_products_are_real(self):
        modules = trade_finder_modules()
        assert len(modules["find_opportunities"].PRODUCTS) == 36


class TestProductDocuments:
    def test_builds_documents(self):
        docs = build_product_documents()
        assert len(docs) > 0

    def test_all_documents_have_provenance(self):
        for doc in build_product_documents():
            assert doc.source_path
            assert doc.source_path.endswith("find_opportunities.py")
            assert doc.source_line > 0

    def test_source_path_is_repo_relative(self):
        for doc in build_product_documents():
            assert doc.source_path.startswith("projects/realtime-stock-pipeline/")

    def test_margin_is_computed(self):
        for doc in build_product_documents():
            assert doc.metadata["margin_pct"] >= 0.05
            assert doc.metadata["landed_cost_usd"] > 0

    def test_only_real_destinations(self):
        for doc in build_product_documents():
            assert doc.metadata["dest_country"] in {"IN", "UK", "US"}
            assert doc.metadata["source_country"] in {"CN", "VN"}

    def test_product_is_in_trade_finder_universe(self):
        modules = trade_finder_modules()
        names = {p["name"] for p in modules["find_opportunities"].PRODUCTS}
        for doc in build_product_documents():
            assert doc.metadata["product"] in names

    def test_india_demand_is_attached_when_available(self):
        modules = trade_finder_modules()
        demand = {row.product: row for row in modules["demand_in"].get_demand_table()}
        with_demand = [
            d for d in build_product_documents() if d.metadata.get("demand_score") is not None
        ]
        assert with_demand
        for doc in with_demand:
            expected = demand[doc.metadata["product"]].demand_score
            assert doc.metadata["demand_score"] == expected


class TestSupplierDocuments:
    def test_builds_one_per_supplier(self):
        docs = build_supplier_documents()
        assert len(docs) == 10

    def test_scores_are_present(self):
        for doc in build_supplier_documents():
            assert doc.metadata["composite_score"] > 0
            assert doc.metadata["risk_level"] in {"LOW", "MEDIUM", "HIGH"}

    def test_alibaba_ids_are_unique(self):
        ids = [d.metadata["alibaba_id"] for d in build_supplier_documents()]
        assert len(ids) == len(set(ids))

    def test_every_supplier_in_the_pool_is_covered(self):
        modules = trade_finder_modules()
        expected = {s["alibaba_id"] for s in modules["verify_suppliers"].SUPPLIERS}
        actual = {d.metadata["alibaba_id"] for d in build_supplier_documents()}
        assert actual == expected

    def test_scores_are_deterministic(self):
        first = [d.metadata["composite_score"] for d in build_supplier_documents()]
        second = [d.metadata["composite_score"] for d in build_supplier_documents()]
        assert first == second


class TestReputationDocuments:
    def test_parses_shortlist(self):
        docs = build_reputation_documents()
        assert len(docs) == 3

    def test_cites_the_report(self):
        for doc in build_reputation_documents():
            assert doc.source_path.endswith("supplier_shortlist.md")
            assert doc.source_line > 0

    def test_extracts_cycle_stats(self):
        docs = build_reputation_documents()
        assert all(d.metadata["avg_rank"] is not None for d in docs)
        assert all(d.metadata["composite_score"] is not None for d in docs)


class TestCorpusAssembly:
    def test_corpus_has_all_three_types(self):
        summary = corpus_summary(build_corpus())
        assert summary["by_type"]["product"] > 0
        assert summary["by_type"]["supplier"] == 10
        assert summary["by_type"]["reputation"] == 3

    def test_doc_ids_are_unique(self):
        docs = build_corpus()
        ids = [d.doc_id for d in docs]
        assert len(ids) == len(set(ids))

    def test_every_source_file_exists_on_disk(self):
        repo_root = Path(__file__).resolve().parents[3]
        for doc in build_corpus():
            assert (repo_root / doc.source_path).exists(), doc.source_path

    def test_document_serialises(self):
        doc = build_corpus()[0]
        payload = doc.to_dict()
        assert set(payload) == {
            "doc_id",
            "doc_type",
            "title",
            "text",
            "source_path",
            "source_line",
            "metadata",
        }
