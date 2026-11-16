"""Tests for the evaluation harness and the CLI.

The evaluation harness is a gate, not a report: `make eval` exits non-zero
when it fails, so the numbers it computes have to mean something.
"""

from __future__ import annotations

import pytest

from tech_trend_radar.cli import build_parser, main
from tech_trend_radar.evaluation import (
    ACCEPTANCE,
    build_burst_fixture,
    check_acceptance,
    eval_burst_detection,
    mrr,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)


class TestRankingMetrics:
    def test_precision_counts_the_hits_in_the_top_k(self):
        assert precision_at_k(["a", "b", "c"], {"a"}, 3) == pytest.approx(1 / 3)

    def test_precision_is_one_when_every_hit_is_correct(self):
        assert precision_at_k(["a", "b"], {"a", "b"}, 2) == 1.0

    def test_precision_is_zero_when_nothing_is_correct(self):
        assert precision_at_k(["x", "y"], {"a"}, 2) == 0.0

    def test_recall_is_the_fraction_of_the_gold_set_found(self):
        assert recall_at_k(["a", "x"], {"a", "b"}, 2) == pytest.approx(0.5)

    def test_recall_is_zero_for_an_empty_gold_set(self):
        assert recall_at_k(["a"], set(), 3) == 0.0

    def test_mrr_is_the_reciprocal_of_the_first_hit(self):
        assert mrr(["x", "y", "a"], {"a"}) == pytest.approx(1 / 3)

    def test_mrr_is_zero_when_nothing_hits(self):
        assert mrr(["x"], {"a"}) == 0.0

    def test_mrr_is_one_when_the_first_answer_is_right(self):
        assert mrr(["a", "x"], {"a"}) == 1.0

    def test_ndcg_rewards_an_early_hit_more(self):
        early = ndcg_at_k(["a", "x", "y"], {"a"}, 3)
        late = ndcg_at_k(["x", "y", "a"], {"a"}, 3)
        assert early > late

    def test_ndcg_is_one_for_a_perfect_ranking(self):
        assert ndcg_at_k(["a", "b"], {"a", "b"}, 2) == pytest.approx(1.0)

    def test_ndcg_is_zero_for_an_empty_gold_set(self):
        assert ndcg_at_k(["a"], set(), 3) == 0.0


class TestBurstFixture:
    def test_the_fixture_contains_the_accelerating_topics(self):
        posts, gold = build_burst_fixture(
            __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        )
        assert gold == {"rust", "kubernetes", "postgres", "wasm"}
        assert len(posts) > 0

    def test_the_accelerating_topics_have_many_more_recent_mentions(self, now):
        from tech_trend_radar.burst import detect_bursts

        posts, _ = build_burst_fixture(now)
        signals = detect_bursts(posts, now=now)
        assert signals["rust"].recent_mentions > signals["rust"].baseline_mentions
        assert signals["python"].recent_mentions == signals["python"].baseline_mentions


class TestBurstEvaluation:
    def test_the_burst_evaluation_passes(self, settings):
        result = eval_burst_detection(settings)
        assert result.passed
        assert result.metrics["accuracy"] >= ACCEPTANCE["min_burst_accuracy"]

    def test_the_accelerating_topics_are_the_ones_found(self, settings):
        result = eval_burst_detection(settings)
        ranked = result.metrics["ranked"]
        assert "rust" in ranked[:4]
        assert "kubernetes" in ranked[:4]

    def test_the_steady_topics_are_not_in_the_top_four(self, settings):
        result = eval_burst_detection(settings)
        assert "python" not in result.metrics["ranked"][:4]
        assert "docker" not in result.metrics["ranked"][:4]


class TestAcceptance:
    def test_a_passing_run_passes(self, settings):
        from tech_trend_radar.evaluation import EvalResult

        results = [
            EvalResult("burst_detection", True),
            EvalResult("ranking", True),
            EvalResult("coverage", True),
        ]
        assert check_acceptance(results)

    def test_a_failing_run_fails(self, settings):
        from tech_trend_radar.evaluation import EvalResult

        results = [
            EvalResult("burst_detection", True),
            EvalResult("coverage", False),
        ]
        assert not check_acceptance(results)

    def test_the_ranking_evaluation_is_not_gated(self, settings):
        from tech_trend_radar.evaluation import EvalResult

        results = [EvalResult("ranking", False), EvalResult("coverage", True)]
        assert check_acceptance(results)

    def test_a_skipped_evaluation_does_not_fail_the_gate(self, settings):
        from tech_trend_radar.evaluation import EvalResult

        # A missing snapshot is a missing input, not a failure. The gate
        # has to stay usable before the first `make fetch`.
        results = [
            EvalResult("burst_detection", True),
            EvalResult("coverage", True, skipped=True),
        ]
        assert check_acceptance(results)

    def test_a_missing_snapshot_skips_coverage_rather_than_failing_it(self, settings):
        from tech_trend_radar.evaluation import eval_coverage

        result = eval_coverage(None, settings)
        assert result.skipped
        assert result.passed
        assert "no snapshot" in result.detail

    def test_a_missing_snapshot_skips_the_ranking_evaluation(self, settings):
        from tech_trend_radar.evaluation import eval_ranking

        result = eval_ranking(None, settings)
        assert result.skipped

    def test_a_snapshot_that_is_present_but_under_covered_still_fails(self, settings):
        from tech_trend_radar.collector import Snapshot
        from tech_trend_radar.evaluation import eval_coverage

        snapshot = Snapshot(fetched_at=__import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ), results=[])
        result = eval_coverage(snapshot, settings)
        assert not result.skipped
        assert not result.passed


class TestCLI:
    def test_the_parser_builds(self):
        parser = build_parser()
        assert parser is not None

    def test_the_trends_command_parses(self):
        args = build_parser().parse_args(["trends", "--limit", "5"])
        assert args.limit == 5
        assert args.command == "trends"

    def test_the_topics_command_parses(self):
        args = build_parser().parse_args(["topics", "rust"])
        assert args.topic == "rust"

    def test_no_command_prints_help(self, capsys):
        assert main([]) == 0
        assert "trending technology topics" in capsys.readouterr().out

    def test_an_unknown_topic_exits_non_zero(self, tmp_path, monkeypatch, capsys):
        # Point the snapshot directory at an empty place so the CLI has
        # nothing to report on.
        from tech_trend_radar.config import Settings

        settings = Settings(snapshot_dir=tmp_path)
        monkeypatch.setattr("tech_trend_radar.cli.load_settings", lambda: settings)
        assert main(["--offline", "topics", "rust"]) == 1

    def test_the_report_command_writes_a_file(self, tmp_path, monkeypatch, accelerating_corpus):
        from tech_trend_radar.collector import Snapshot
        from tech_trend_radar.config import Settings

        snapshot = Snapshot(fetched_at=accelerating_corpus[0].published, results=[])
        snapshot_path = tmp_path / "snapshot_test.json"
        snapshot.save(snapshot_path)

        settings = Settings(snapshot_dir=tmp_path)
        monkeypatch.setattr("tech_trend_radar.cli.load_settings", lambda: settings)

        out = tmp_path / "report.md"
        assert main(["--offline", "report", "--out", str(out)]) == 0
        assert out.exists()
        assert "Tech Trend Radar" in out.read_text()

    def test_the_trends_command_reports_the_semantic_state(
        self, tmp_path, monkeypatch, accelerating_corpus, capsys
    ):
        from tech_trend_radar.collector import Snapshot
        from tech_trend_radar.config import Settings

        snapshot = Snapshot(fetched_at=accelerating_corpus[0].published, results=[])
        snapshot.save(tmp_path / "snapshot_test.json")

        settings = Settings(snapshot_dir=tmp_path)
        monkeypatch.setattr("tech_trend_radar.cli.load_settings", lambda: settings)

        assert main(["--offline", "trends"]) == 0
        out = capsys.readouterr().out
        assert "Semantic matching:" in out

    def test_the_semantic_layer_can_be_turned_off_by_the_environment(
        self, tmp_path, monkeypatch, accelerating_corpus, capsys
    ):
        from tech_trend_radar.collector import Snapshot
        from tech_trend_radar.config import Settings

        snapshot = Snapshot(fetched_at=accelerating_corpus[0].published, results=[])
        snapshot.save(tmp_path / "snapshot_test.json")

        settings = Settings(snapshot_dir=tmp_path)
        monkeypatch.setattr("tech_trend_radar.cli.load_settings", lambda: settings)
        monkeypatch.setenv("TREND_RADAR_NO_SEMANTIC", "1")

        assert main(["--offline", "trends"]) == 0
        assert "lexical only" in capsys.readouterr().out
