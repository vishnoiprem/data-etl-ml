"""Tests for burst detection.

The detector's job is to separate *accelerating* topics from *steady* ones.
Most of these tests are about that distinction.
"""

from __future__ import annotations

import pytest

from tech_trend_radar.burst import (
    BASELINE_PRIOR,
    attach_topics,
    burst_report,
    detect_bursts,
    platform_mentions,
    score_topic,
)


class TestDetection:
    def test_a_topic_with_mentions_is_detected(self, post_factory):
        posts = [post_factory(str(i), "Rust news") for i in range(3)]
        signals = detect_bursts(posts)
        assert "rust" in signals

    def test_the_recent_and_baseline_counts_are_separate(self, post_factory):
        posts = [
            post_factory(f"r{i}", "Rust news", hours_ago=2) for i in range(4)
        ] + [
            post_factory(f"b{i}", "Rust news", hours_ago=24 * 5) for i in range(2)
        ]
        signal = detect_bursts(posts)["rust"]
        assert signal.recent_mentions == 4
        assert signal.baseline_mentions == 2

    def test_a_post_older_than_the_baseline_window_counts_for_nothing(self, post_factory):
        posts = [post_factory("old", "Rust news", hours_ago=24 * 30)]
        signal = detect_bursts(posts)["rust"]
        assert signal.recent_mentions == 0
        assert signal.baseline_mentions == 0

    def test_the_platforms_are_recorded(self, post_factory):
        posts = [
            post_factory("a", "Rust news", platform="hackernews"),
            post_factory("b", "Rust news", platform="devto"),
            post_factory("c", "Rust news", platform="devto"),
        ]
        signal = detect_bursts(posts)["rust"]
        assert signal.platforms == {"hackernews", "devto"}

    def test_the_first_and_last_seen_timestamps_are_recorded(self, post_factory):
        posts = [
            post_factory("a", "Rust news", hours_ago=10),
            post_factory("b", "Rust news", hours_ago=1),
        ]
        signal = detect_bursts(posts)["rust"]
        assert signal.first_seen is not None
        assert signal.last_seen is not None
        assert signal.first_seen < signal.last_seen

    def test_the_headlines_are_collected(self, post_factory):
        posts = [
            post_factory(f"p{i}", f"Rust news number {i}", url=f"https://x.invalid/{i}")
            for i in range(3)
        ]
        signal = detect_bursts(posts)["rust"]
        assert len(signal.titles) == 3
        assert "https://x.invalid/0" in signal.urls

    def test_an_identical_title_is_not_collected_twice(self, post_factory):
        posts = [post_factory(f"p{i}", "Rust news") for i in range(3)]
        signal = detect_bursts(posts)["rust"]
        assert len(signal.titles) == 1


class TestRatio:
    def test_a_topic_with_no_baseline_has_a_finite_ratio(self, post_factory):
        posts = [post_factory(str(i), "Rust news") for i in range(3)]
        signal = detect_bursts(posts)["rust"]
        assert signal.ratio == pytest.approx(3 / BASELINE_PRIOR)

    def test_a_steady_topic_has_a_ratio_near_one(self, post_factory):
        posts = [post_factory(f"r{i}", "Rust news", hours_ago=2) for i in range(4)]
        posts += [post_factory(f"b{i}", "Rust news", hours_ago=24 * 5) for i in range(4)]
        signal = detect_bursts(posts)["rust"]
        assert signal.ratio == pytest.approx(4 / (4 + BASELINE_PRIOR), rel=0.01)


class TestScoring:
    def test_an_accelerating_topic_outranks_a_declining_one(
        self, accelerating_corpus, settings
    ):
        ranked = burst_report(accelerating_corpus, settings, limit=10)
        topics = [signal.topic for signal, _ in ranked]
        # `python` and `docker` are flat or declining, so they are not
        # trending at all and never reach the report. The accelerating
        # topics are what is left.
        assert "rust" in topics
        assert "kubernetes" in topics

    def test_a_declining_topic_is_absent_from_the_report(
        self, accelerating_corpus, settings
    ):
        ranked = burst_report(accelerating_corpus, settings, limit=10)
        topics = [signal.topic for signal, _ in ranked]
        assert "python" not in topics
        assert "docker" not in topics

    def test_both_accelerating_topics_come_first(self, accelerating_corpus, settings):
        ranked = burst_report(accelerating_corpus, settings, limit=10)
        topics = [signal.topic for signal, _ in ranked]
        assert set(topics[:2]) == {"rust", "kubernetes"}

    def test_a_topic_with_too_few_mentions_scores_zero(self, post_factory, settings):
        posts = [post_factory("a", "Rust news"), post_factory("b", "Rust news")]
        signal = detect_bursts(posts)["rust"]
        assert score_topic(signal, settings) == 0.0

    def test_a_declining_topic_scores_zero(self, post_factory, settings):
        # Many recent mentions but far more in the baseline: it is slowing
        # down, so it is not trending.
        posts = [post_factory(f"r{i}", "Rust news", hours_ago=2) for i in range(4)]
        posts += [post_factory(f"b{i}", "Rust news", hours_ago=24 * 5) for i in range(20)]
        signal = detect_bursts(posts)["rust"]
        assert score_topic(signal, settings) == 0.0

    def test_a_flat_topic_scores_zero(self, post_factory, settings):
        posts = [post_factory(f"r{i}", "Rust news", hours_ago=2) for i in range(4)]
        posts += [post_factory(f"b{i}", "Rust news", hours_ago=24 * 5) for i in range(4)]
        signal = detect_bursts(posts)["rust"]
        assert score_topic(signal, settings) == 0.0

    def test_a_cross_platform_topic_outscores_a_single_platform_one(
        self, post_factory, settings
    ):
        single = [post_factory(f"s{i}", "Rust news", platform="hackernews") for i in range(5)]
        multi = [
            post_factory(f"m{i}", "Rust news", platform=["hackernews", "devto", "stackoverflow"][i % 3])
            for i in range(5)
        ]
        single_score = score_topic(detect_bursts(single, settings)["rust"], settings)
        multi_score = score_topic(detect_bursts(multi, settings)["rust"], settings)
        assert multi_score > single_score


class TestAttachTopics:
    def test_each_post_gets_its_topics(self, post_factory):
        posts = [post_factory("a", "Rust 1.90 released")]
        drafts = attach_topics(posts)
        assert "rust" in drafts[0].topics

    def test_the_evidence_records_the_matched_text(self, post_factory):
        posts = [post_factory("a", "Rust 1.90 released")]
        drafts = attach_topics(posts)
        assert drafts[0].evidence.get("rust")

    def test_a_topic_is_not_repeated_within_one_post(self, post_factory):
        posts = [post_factory("a", "Rust and more Rust and Rust again")]
        drafts = attach_topics(posts)
        assert drafts[0].topics.count("rust") == 1


class TestPlatformMentions:
    def test_each_platform_is_counted(self, post_factory):
        posts = [
            post_factory("a", "Rust news", platform="hackernews"),
            post_factory("b", "Rust news", platform="hackernews"),
            post_factory("c", "Rust news", platform="devto"),
        ]
        counts = platform_mentions(posts)
        assert counts["hackernews"] == 2
        assert counts["devto"] == 1

    def test_very_old_posts_are_not_counted(self, post_factory):
        posts = [post_factory("a", "Rust news", hours_ago=24 * 60)]
        assert platform_mentions(posts)["hackernews"] == 0


class TestReport:
    def test_the_report_is_ordered_by_score(self, accelerating_corpus, settings):
        ranked = burst_report(accelerating_corpus, settings, limit=10)
        scores = [score for _, score in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_the_report_respects_the_limit(self, accelerating_corpus, settings):
        assert len(burst_report(accelerating_corpus, settings, limit=2)) == 2

    def test_only_eligible_topics_appear_in_the_report(self, post_factory, settings):
        posts = [post_factory("a", "Rust news")]
        ranked = burst_report(posts, settings, limit=10)
        assert ranked == []
