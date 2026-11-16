"""The FastAPI app — the read-only endpoints."""

from __future__ import annotations

import pytest

fastapi = pytest.importorskip("fastapi")
import app as app_module  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app_module.app)


class TestHealth:
    def test_it_reports_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_it_reports_the_rate_card_region(self, client):
        assert response_region(client) == "us-east-1"

    def test_it_says_it_is_read_only(self, client):
        assert client.get("/health").json()["read_only"] is True

    def test_it_reports_the_router(self, client):
        assert client.get("/health").json()["router"] in {"stub", "ollama"}


def response_region(client) -> str:
    return client.get("/health").json()["rate_card_region"]


class TestFindings:
    def test_it_returns_the_findings(self, client):
        payload = client.get("/findings").json()
        assert payload["finding_count"] > 0
        assert len(payload["findings"]) == payload["finding_count"]

    def test_every_finding_carries_its_basis(self, client):
        payload = client.get("/findings").json()
        for finding in payload["findings"]:
            assert finding["cost_impact_basis"] in {
                "measured",
                "modelled",
                "upper_bound",
            }

    def test_every_finding_carries_its_summary(self, client):
        payload = client.get("/findings").json()
        for finding in payload["findings"]:
            assert finding["summary"].strip()

    def test_it_can_be_filtered_by_detector(self, client):
        payload = client.get("/findings?detector=growth").json()
        for finding in payload["findings"]:
            assert finding["detector"] == "growth"

    def test_it_can_be_filtered_by_severity(self, client):
        payload = client.get("/findings?severity=high").json()
        for finding in payload["findings"]:
            assert finding["severity"] == "high"

    def test_an_unknown_detector_returns_nothing_rather_than_everything(self, client):
        payload = client.get("/findings?detector=nonsense").json()
        assert payload["finding_count"] == 0

    def test_the_totals_are_kept_apart_by_basis(self, client):
        payload = client.get("/findings").json()
        totals = payload["totals_by_basis"]
        assert set(totals) <= {"measured", "modelled", "upper_bound"}


class TestReport:
    def test_it_returns_the_text(self, client):
        payload = client.get("/report").json()
        assert "AWS Cost Analyzer" in payload["text"]

    def test_the_text_names_the_region(self, client):
        payload = client.get("/report").json()
        assert "ap-southeast-1" in payload["text"] or "us-east-1" in payload["text"]

    def test_it_says_the_model_cannot_change_a_finding(self, client):
        payload = client.get("/report").json()
        assert "cannot change a finding" in payload["text"]


class TestDetectors:
    def test_it_lists_the_four_detectors(self, client):
        payload = client.get("/detectors").json()
        names = {d["name"] for d in payload["detectors"]}
        assert names == {"growth", "access", "lifecycle", "allocation"}

    def test_each_detector_says_what_it_needs(self, client):
        payload = client.get("/detectors").json()
        for detector in payload["detectors"]:
            assert detector["needs"].strip()


class TestReadOnly:
    def test_there_is_no_write_endpoint(self, client):
        paths = {route.path for route in app_module.app.routes}
        for path in paths:
            assert "snapshot" not in path or path == "/health"

    def test_a_post_is_not_allowed(self, client):
        assert client.post("/findings").status_code == 405

    def test_a_delete_is_not_allowed(self, client):
        assert client.delete("/findings").status_code == 405
