"""Tests for the value measurement and the audit ledger."""

from __future__ import annotations

import json

import pytest

from src.trade_sourcing_ai.audit import AuditLog
from src.trade_sourcing_ai.config import ValueConfig
from src.trade_sourcing_ai.quote_agent import recommend
from src.trade_sourcing_ai.quotes import parse_quote
from src.trade_sourcing_ai.value import (
    build_value_report,
    compute_cost,
    summarise_reports,
)


@pytest.fixture
def recommendation(primary_quote_dicts):
    quotes = [parse_quote(q) for q in primary_quote_dicts]
    return recommend(quotes, min_margin_pct=0.15)


@pytest.fixture
def config():
    return ValueConfig()


class TestComputeCost:
    def test_local_mode_costs_nothing_per_token(self, config):
        cost = compute_cost(compute_seconds=1.0, tokens_used=100_000, config=config)
        assert cost.model_cost_usd == 0.0

    def test_compute_time_is_priced(self, config):
        cost = compute_cost(compute_seconds=3600.0, tokens_used=0, config=config)
        assert cost.compute_cost_usd == pytest.approx(config.operator_hourly_usd)

    def test_total_is_the_sum(self, config):
        cost = compute_cost(compute_seconds=10.0, tokens_used=0, config=config)
        assert cost.total_cost_usd == pytest.approx(
            cost.compute_cost_usd + cost.model_cost_usd
        )

    def test_serialises(self, config):
        cost = compute_cost(compute_seconds=0.5, tokens_used=0, config=config)
        assert set(cost.to_dict()) == {
            "compute_seconds",
            "compute_cost_usd",
            "model_cost_usd",
            "total_cost_usd",
        }


class TestValueReport:
    def test_recommendation_is_named(self, recommendation, config):
        report = build_value_report(recommendation, config=config)
        assert report.recommended_supplier == "Shenzhen Qiyang Technology Co., Ltd."

    def test_margin_is_measured_per_order(self, recommendation, config):
        report = build_value_report(recommendation, config=config)
        assert report.recommended_margin_usd == pytest.approx(0.81, abs=0.01)

    def test_time_saved_is_capped_at_the_manual_baseline(self, recommendation, config):
        report = build_value_report(recommendation, config=config, agent_seconds=0.0)
        assert report.time_saved_minutes == pytest.approx(
            config.manual_minutes_per_decision
        )

    def test_time_saved_is_zero_when_the_agent_is_slower(self, recommendation, config):
        report = build_value_report(
            recommendation, config=config, agent_seconds=10000.0
        )
        assert report.time_saved_minutes == 0.0

    def test_manual_cost_is_reported(self, recommendation, config):
        report = build_value_report(recommendation, config=config)
        assert report.manual_cost_usd == pytest.approx(
            config.manual_minutes_per_decision / 60 * config.operator_hourly_usd
        )

    def test_margin_versus_status_quo_is_computed(self, recommendation, config):
        report = build_value_report(
            recommendation, config=config, status_quo_alibaba_id="goldstar_2010"
        )
        assert report.margin_captured_vs_status_quo_usd > 0

    def test_margin_versus_naive_is_zero_when_the_agent_picks_cheapest(
        self, recommendation, config
    ):
        report = build_value_report(recommendation, config=config)
        assert report.margin_captured_vs_naive_usd == pytest.approx(0.0, abs=0.01)

    def test_assumptions_are_carried(self, recommendation, config):
        report = build_value_report(recommendation, config=config)
        assert report.assumptions["operator_hourly_usd"] == config.operator_hourly_usd
        assert "assumption" in report.assumptions["notes"]

    def test_three_scenarios_are_produced(self, recommendation, config):
        report = build_value_report(recommendation, config=config)
        names = [s["name"] for s in report.scenarios]
        assert names == ["pessimistic", "base", "optimistic"]

    def test_scenarios_are_ordered(self, recommendation, config):
        report = build_value_report(recommendation, config=config)
        captures = [s["margin_captured_usd"] for s in report.scenarios]
        assert captures[0] <= captures[1] <= captures[2]

    def test_each_scenario_states_its_assumption(self, recommendation, config):
        report = build_value_report(recommendation, config=config)
        assert all(s["assumption"] for s in report.scenarios)

    def test_scenarios_use_the_stronger_baseline(self, recommendation, config):
        """The agent picked the cheapest quote, so the naive baseline captures
        nothing. The scenarios must use the status-quo comparison instead of
        reporting a flat zero."""
        report = build_value_report(
            recommendation, config=config, status_quo_alibaba_id="goldstar_2010"
        )
        assert report.margin_captured_vs_naive_usd == pytest.approx(0.0, abs=0.01)
        assert report.margin_captured_vs_status_quo_usd > 0
        base = next(s for s in report.scenarios if s["name"] == "base")
        assert base["margin_captured_usd"] == pytest.approx(
            report.margin_captured_vs_status_quo_usd, abs=0.01
        )
        assert base["measured_against"] == "status quo shortlist"

    def test_payback_uses_the_stronger_baseline(self, recommendation, config):
        report = build_value_report(
            recommendation, config=config, status_quo_alibaba_id="goldstar_2010"
        )
        assert report.payback_decisions is not None

    def test_serialises_to_json(self, recommendation, config):
        report = build_value_report(recommendation, config=config)
        json.dumps(report.to_dict())


class TestSummarise:
    def test_empty_input(self):
        assert summarise_reports([]) == {"decisions": 0}

    def test_aggregates(self, recommendation, config):
        report = build_value_report(recommendation, config=config)
        summary = summarise_reports([report, report])
        assert summary["decisions"] == 2
        assert summary["decisions_with_recommendation"] == 2
        assert summary["total_cost_usd"] >= 0


class TestAuditLog:
    def test_emits_and_reads_back(self, tmp_path):
        log = AuditLog(tmp_path / "decisions.jsonl")
        identifier = log.emit("quote_decision", {"product": "smart watch"})
        events = log.recent()
        assert len(events) == 1
        assert events[0].decision_id == identifier
        assert events[0].payload["product"] == "smart watch"

    def test_appends_rather_than_overwrites(self, tmp_path):
        log = AuditLog(tmp_path / "decisions.jsonl")
        log.emit("quote_decision", {"n": 1})
        log.emit("quote_decision", {"n": 2})
        assert len(log.recent()) == 2

    def test_filters_by_event_type(self, tmp_path):
        log = AuditLog(tmp_path / "decisions.jsonl")
        log.emit("quote_decision", {"n": 1})
        log.emit("something_else", {"n": 2})
        assert len(log.recent(event_type="quote_decision")) == 1

    def test_respects_the_limit(self, tmp_path):
        log = AuditLog(tmp_path / "decisions.jsonl")
        for i in range(10):
            log.emit("quote_decision", {"n": i})
        assert len(log.recent(limit=3)) == 3

    def test_finds_one_by_id(self, tmp_path):
        log = AuditLog(tmp_path / "decisions.jsonl")
        identifier = log.emit("quote_decision", {"n": 1})
        event = log.get(identifier)
        assert event is not None
        assert event.payload["n"] == 1

    def test_unknown_id_returns_none(self, tmp_path):
        log = AuditLog(tmp_path / "decisions.jsonl")
        assert log.get("nope") is None

    def test_missing_file_reads_as_empty(self, tmp_path):
        log = AuditLog(tmp_path / "missing.jsonl")
        assert log.recent() == []

    def test_each_line_is_valid_json(self, tmp_path):
        path = tmp_path / "decisions.jsonl"
        log = AuditLog(path)
        log.emit("quote_decision", {"n": 1, "text": "a \"quoted\" value"})
        for line in path.read_text(encoding="utf-8").splitlines():
            json.loads(line)

    def test_corrupt_lines_are_skipped(self, tmp_path):
        path = tmp_path / "decisions.jsonl"
        path.write_text("not json\n{\"event_type\": \"x\", \"decision_id\": \"1\", "
                        "\"ts\": \"t\", \"payload\": {}}\n", encoding="utf-8")
        log = AuditLog(path)
        assert len(log.recent()) == 1

    def test_clear_removes_the_ledger(self, tmp_path):
        log = AuditLog(tmp_path / "decisions.jsonl")
        log.emit("quote_decision", {"n": 1})
        log.clear()
        assert log.recent() == []
