"""Tests for the HTTP API.

The app is imported once and its service is replaced with a service built
from a synthetic corpus, so the tests never touch the network and always
see the same trends.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as radar_app  # noqa: E402
from tech_trend_radar.collector import Snapshot  # noqa: E402
from tech_trend_radar.models import FetchResult  # noqa: E402


@pytest.fixture
def client(accelerating_corpus, settings) -> TestClient:
    """A client whose service holds the synthetic corpus."""
    snapshot = Snapshot(
        fetched_at=accelerating_corpus[0].published,
        results=[
            FetchResult(
                platform="hackernews",
                posts=[p for p in accelerating_corpus if p.platform == "hackernews"],
                ok=True,
            ),
            FetchResult(
                platform="devto",
                posts=[p for p in accelerating_corpus if p.platform == "devto"],
                ok=True,
            ),
            FetchResult(
                platform="stackoverflow",
                posts=[p for p in accelerating_corpus if p.platform == "stackoverflow"],
                ok=True,
            ),
        ],
    )
    service = radar_app.RadarService.__new__(radar_app.RadarService)
    service.settings = settings
    service.snapshot = snapshot
    service.collected_at = snapshot.fetched_at
    service.trends = []
    service.recompute()

    original = radar_app.service
    radar_app.service = service
    try:
        yield TestClient(radar_app.app)
    finally:
        radar_app.service = original


class TestHealth:
    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_health_reports_the_post_count(self, client):
        # Two accelerating topics with 10 posts each, two steady ones
        # with 8 each.
        assert client.get("/health").json()["post_count"] == 36

    def test_health_reports_the_live_sources(self, client):
        sources = client.get("/health").json()["sources"]
        assert set(sources["live"]) == {"hackernews", "devto", "stackoverflow"}

    def test_health_reports_the_windows(self, client):
        windows = client.get("/health").json()["windows"]
        assert windows["recent_hours"] > 0
        assert windows["baseline_hours"] > 0

    def test_health_reports_the_semantic_layer_state(self, client):
        # The radar runs with or without the embedding model, so /health
        # has to say which mode it is in — otherwise a silently-degraded
        # service looks identical to a fully-working one.
        semantic = client.get("/health").json()["semantic"]
        assert "enabled" in semantic
        assert "model" in semantic
        assert "threshold" in semantic


class TestSources:
    def test_sources_lists_the_results(self, client):
        response = client.get("/sources")
        assert response.status_code == 200
        assert len(response.json()["results"]) == 3

    def test_each_result_reports_its_post_count(self, client):
        for result in client.get("/sources").json()["results"]:
            assert "post_count" in result
            assert "ok" in result


class TestTrends:
    def test_trends_are_returned(self, client):
        response = client.get("/trends")
        assert response.status_code == 200
        assert response.json()["count"] > 0

    def test_the_trends_are_ranked(self, client):
        trends = client.get("/trends").json()["trends"]
        assert [t["rank"] for t in trends] == list(range(1, len(trends) + 1))

    def test_the_limit_is_respected(self, client):
        assert client.get("/trends?limit=1").json()["count"] == 1

    def test_the_limit_must_be_positive(self, client):
        assert client.get("/trends?limit=0").status_code == 422

    def test_the_trends_can_be_filtered_by_platform(self, client):
        response = client.get("/trends?platform=hackernews")
        for trend in response.json()["trends"]:
            assert "hackernews" in trend["platforms"]

    def test_the_trends_can_be_filtered_by_minimum_score(self, client):
        response = client.get("/trends?min_score=2.0")
        for trend in response.json()["trends"]:
            assert trend["score"] >= 2.0

    def test_each_trend_carries_its_rationale(self, client):
        for trend in client.get("/trends").json()["trends"]:
            assert trend["rationale"]
            assert trend["summary"]

    def test_each_trend_carries_its_evidence(self, client):
        for trend in client.get("/trends").json()["trends"]:
            assert trend["evidence"]
            assert trend["headlines"]


class TestTopicDetail:
    def test_a_known_topic_is_returned(self, client):
        response = client.get("/topics/rust")
        assert response.status_code == 200
        assert response.json()["topic"]["topic"] == "rust"

    def test_the_topic_includes_the_posts_that_support_it(self, client):
        response = client.get("/topics/rust")
        assert response.json()["post_count"] > 0
        assert response.json()["posts"]

    def test_an_unknown_topic_is_a_404(self, client):
        response = client.get("/topics/definitelynotarealtopic")
        assert response.status_code == 404

    def test_the_topic_lookup_is_case_insensitive(self, client):
        assert client.get("/topics/RUST").status_code == 200


class TestReport:
    def test_the_report_is_markdown(self, client):
        response = client.get("/report")
        assert response.status_code == 200
        assert response.json()["markdown"].startswith("# Tech Trend Radar")

    def test_the_report_contains_the_trends(self, client):
        markdown = client.get("/report").json()["markdown"]
        assert "rust" in markdown


class TestOpenApi:
    def test_the_schema_is_generated(self, client):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        paths = response.json()["paths"]
        for path in ("/health", "/trends", "/topics/{topic}", "/sources", "/report"):
            assert path in paths
