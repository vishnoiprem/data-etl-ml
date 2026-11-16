"""Tests for the ranking and its explanations.

The rationale is the product. If a claim in it cannot be traced back to a
number, it is not a claim the radar should be making.
"""

from __future__ import annotations

import pytest

from tech_trend_radar.ranking import (
    build_trends,
    explain,
    score_all,
)


class TestBuildTrends:
    def test_the_accelerating_topics_are_ranked_first(self, accelerating_corpus, settings):
        trends = build_trends(accelerating_corpus, settings)
        assert trends[0].topic in {"rust", "kubernetes"}

    def test_the_ranks_are_sequential_from_one(self, accelerating_corpus, settings):
        trends = build_trends(accelerating_corpus, settings)
        assert [t.rank for t in trends] == list(range(1, len(trends) + 1))

    def test_a_topic_with_no_signal_does_not_appear(self, post_factory, settings):
        posts = [post_factory("a", "Rust news")]
        assert build_trends(posts, settings) == []

    def test_the_limit_is_respected(self, accelerating_corpus, settings):
        assert len(build_trends(accelerating_corpus, settings, limit=1)) == 1


class TestRationale:
    def test_the_summary_mentions_the_topic(self, accelerating_corpus, settings):
        trend = build_trends(accelerating_corpus, settings)[0]
        assert trend.topic in trend.summary

    def test_the_rationale_states_the_counts(self, accelerating_corpus, settings):
        trend = build_trends(accelerating_corpus, settings)[0]
        assert any(
            str(trend.recent_mentions) in reason for reason in trend.rationale
        )

    def test_a_cross_platform_topic_is_confirmed(self, accelerating_corpus, settings):
        trends = build_trends(accelerating_corpus, settings)
        rust = next(t for t in trends if t.topic == "rust")
        assert rust.corroborated
        assert rust.confidence in {"high", "medium"}

    def test_a_single_platform_topic_is_not_confirmed(self, post_factory, settings):
        posts = [post_factory(f"p{i}", "Rust news", platform="hackernews") for i in range(4)]
        trend = build_trends(posts, settings)[0]
        assert not trend.corroborated
        assert "Single platform only" in " ".join(trend.rationale)

    def test_the_rationale_warns_when_the_evidence_is_thin(self, post_factory, settings):
        posts = [post_factory(f"p{i}", "Rust news", platform="hackernews") for i in range(4)]
        trend = build_trends(posts, settings)[0]
        assert any("may be local" in reason for reason in trend.rationale)

    def test_a_real_post_is_quoted_as_the_example(self, accelerating_corpus, settings):
        trend = build_trends(accelerating_corpus, settings)[0]
        assert any("Example:" in reason for reason in trend.rationale)
        assert trend.headlines

    def test_the_example_matches_a_real_title(self, accelerating_corpus, settings):
        trend = build_trends(accelerating_corpus, settings)[0]
        titles = [p.title for p in accelerating_corpus]
        assert trend.headlines[0]["title"] in titles

    def test_the_evidence_names_the_platforms(self, accelerating_corpus, settings):
        trend = build_trends(accelerating_corpus, settings)[0]
        platform_evidence = [e for e in trend.evidence if e.kind == "platform"]
        assert platform_evidence


class TestBreakdown:
    def test_the_breakdown_sums_to_the_score(self, accelerating_corpus, settings):
        for trend in build_trends(accelerating_corpus, settings):
            b = trend.breakdown
            assert b["acceleration"] + b["volume"] + b["corroboration"] == pytest.approx(
                b["total"], abs=0.001
            )

    def test_the_breakdown_total_matches_the_score(self, accelerating_corpus, settings):
        for trend in build_trends(accelerating_corpus, settings):
            assert trend.breakdown["total"] == pytest.approx(trend.score, abs=0.001)

    def test_the_corroboration_term_is_positive_for_a_cross_platform_topic(
        self, accelerating_corpus, settings
    ):
        trends = build_trends(accelerating_corpus, settings)
        rust = next(t for t in trends if t.topic == "rust")
        assert rust.breakdown["corroboration"] > 0


class TestExplain:
    def test_the_explanation_includes_the_rank_and_the_topic(self, accelerating_corpus, settings):
        trend = build_trends(accelerating_corpus, settings)[0]
        text = explain(trend)
        assert str(trend.rank) in text
        assert trend.topic in text

    def test_the_explanation_includes_the_reasons(self, accelerating_corpus, settings):
        trend = build_trends(accelerating_corpus, settings)[0]
        text = explain(trend)
        for reason in trend.rationale:
            assert reason in text


class TestScoreAll:
    def test_every_topic_gets_a_score(self, accelerating_corpus, settings):
        scores = score_all(accelerating_corpus, settings)
        assert "rust" in scores
        assert "python" in scores

    def test_a_declining_topic_scores_zero(self, post_factory, settings):
        posts = [post_factory(f"r{i}", "Rust news", hours_ago=2) for i in range(3)]
        posts += [post_factory(f"b{i}", "Rust news", hours_ago=24 * 5) for i in range(10)]
        assert score_all(posts, settings)["rust"] == 0.0


class TestSerialization:
    def test_a_trend_round_trips_to_a_dict(self, accelerating_corpus, settings):
        trend = build_trends(accelerating_corpus, settings)[0]
        data = trend.to_dict()
        assert data["topic"] == trend.topic
        assert data["rank"] == trend.rank
        assert isinstance(data["rationale"], list)
        assert isinstance(data["breakdown"], dict)

    def test_the_dict_has_the_keys_the_api_returns(self, accelerating_corpus, settings):
        data = build_trends(accelerating_corpus, settings)[0].to_dict()
        for key in (
            "rank",
            "topic",
            "score",
            "recent_mentions",
            "baseline_mentions",
            "ratio",
            "platforms",
            "corroborated",
            "confidence",
            "summary",
            "rationale",
            "evidence",
            "headlines",
        ):
            assert key in data
