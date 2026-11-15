"""End-to-end tests: the whole agent, offline, with no API key."""

from __future__ import annotations

import json

from src.trade_sourcing_ai.quotes import load_quotes


class TestDecisionFlow:
    def test_a_full_decision_runs_offline(self, service, primary_quote_dicts):
        result = service.compare_quotes(primary_quote_dicts)
        assert result["ok"] is True
        assert result["recommended"] is not None
        assert result["decision_id"]
        assert result["explanation"]
        assert result["value"]["cost"]["total_cost_usd"] >= 0

    def test_the_decision_is_recorded(self, service, primary_quote_dicts):
        result = service.compare_quotes(primary_quote_dicts)
        history = service.decision_history()
        assert len(history) == 1
        assert history[0]["decision_id"] == result["decision_id"]

    def test_the_recorded_decision_can_be_read_back(self, service, primary_quote_dicts):
        service.compare_quotes(primary_quote_dicts)
        events = service.audit.recent()
        assert events[0].payload["recommended"]["alibaba_id"] == "qytech_2014"
        assert events[0].payload["value"]["recommended_margin_usd"] > 0

    def test_recording_can_be_disabled(self, service, primary_quote_dicts):
        service.compare_quotes(primary_quote_dicts, record=False)
        assert service.decision_history() == []

    def test_history_summary_aggregates(self, service, primary_quote_dicts):
        service.compare_quotes(primary_quote_dicts)
        service.compare_quotes(primary_quote_dicts)
        summary = service.summarise_history()
        assert summary["decisions"] == 2
        assert summary["decisions_with_recommendation"] == 2

    def test_the_same_decision_is_reproducible(self, service, primary_quote_dicts):
        first = service.compare_quotes(primary_quote_dicts)
        second = service.compare_quotes(primary_quote_dicts)
        assert (
            first["recommended"]["alibaba_id"] == second["recommended"]["alibaba_id"]
        )
        assert first["confidence"] == second["confidence"]

    def test_an_invalid_quote_is_rejected_without_a_decision(self, service):
        result = service.compare_quotes([{"alibaba_id": "x"}])
        assert result["ok"] is False
        assert result["error"] == "invalid_quote"
        assert service.decision_history() == []

    def test_all_quotes_rejected_is_reported_honestly(self, service, unviable_quote_dicts):
        result = service.compare_quotes(unviable_quote_dicts)
        assert result["ok"] is True
        assert result["recommended"] is None
        assert result["confidence"] == 0.0
        assert any("disqualified" in line for line in result["rationale"])

    def test_bundled_fixture_loads_and_decides(self, service):
        quotes = load_quotes()
        primary = [q for q in quotes if q.product == "phone case silicone"]
        result = service.compare_quotes(
            [q.raw for q in primary], status_quo_alibaba_id="goldstar_2010"
        )
        assert result["recommended"]["alibaba_id"] == "qytech_2014"
        assert result["value"]["margin_captured_vs_status_quo_usd"] > 0


class TestRetrievalFlow:
    def test_search_works_end_to_end(self, service):
        result = service.search("fitness band supplier", top_k=3)
        assert result["hits"]
        assert result["total_latency_ms"] >= 0

    def test_search_hits_carry_provenance(self, service):
        result = service.search("supplier", top_k=3)
        for hit in result["hits"]:
            assert hit["source_path"]
            assert hit["source_line"] > 0

    def test_supplier_pool_is_ranked(self, service):
        suppliers = service.suppliers()
        assert len(suppliers) == 10
        scores = [s["composite_score"] for s in suppliers]
        assert scores == sorted(scores, reverse=True)

    def test_supplier_pool_filters_by_lead_time(self, service):
        suppliers = service.suppliers(max_lead_time_days=18)
        assert suppliers
        assert all(s["lead_time_days"] <= 18 for s in suppliers)


class TestHealth:
    def test_health_reports_the_corpus(self, service):
        health = service.health()
        assert health["status"] == "ok"
        assert health["documents"] > 100
        assert health["documents_by_type"]["supplier"] == 10

    def test_health_reports_the_router(self, service):
        assert service.health()["router"] == "stub"

    def test_health_lists_the_source_files(self, service):
        paths = service.health()["source_paths"]
        assert any("find_opportunities.py" in p for p in paths)
        assert any("verify_suppliers.py" in p for p in paths)


class TestSerialisability:
    def test_a_decision_is_json_serialisable(self, service, primary_quote_dicts):
        result = service.compare_quotes(primary_quote_dicts)
        json.dumps(result)

    def test_a_search_is_json_serialisable(self, service):
        json.dumps(service.search("supplier", top_k=3))

    def test_the_history_is_json_serialisable(self, service, primary_quote_dicts):
        service.compare_quotes(primary_quote_dicts)
        json.dumps(service.decision_history())
