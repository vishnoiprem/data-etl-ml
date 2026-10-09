"""HTTP-level tests for the APM service."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.app import create_app  # noqa: E402
from code.service import APMService  # noqa: E402


class APMAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = APMService()
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def test_ingest_and_get_trace(self) -> None:
        r = self.client.post("/api/spans", json={
            "trace_id": "abc",
            "service": "api",
            "name": "root",
            "span_id": 1,
            "parent_span_id": 0,
            "duration_ms": 50,
            "status": "ok",
        })
        self.assertEqual(r.status_code, 201)
        r = self.client.post("/api/spans", json={
            "trace_id": "abc",
            "service": "db",
            "name": "child",
            "span_id": 2,
            "parent_span_id": 1,
            "duration_ms": 10,
            "status": "ok",
        })
        self.assertEqual(r.status_code, 201)
        r = self.client.get("/api/traces/abc")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(len(body["spans"]), 2)
        self.assertEqual(len(body["roots"]), 1)

    def test_list_services(self) -> None:
        self.client.post("/api/spans", json={"trace_id": "1", "service": "a", "name": "x"})
        self.client.post("/api/spans", json={"trace_id": "2", "service": "b", "name": "x"})
        r = self.client.get("/api/services")
        self.assertEqual(r.status_code, 200)
        names = {s["name"] for s in r.get_json()["services"]}
        self.assertEqual(names, {"a", "b"})

    def test_error_rate(self) -> None:
        for i, status in enumerate(["ok", "error", "ok"]):
            self.client.post("/api/spans", json={
                "trace_id": f"t{i}",
                "service": "checkout",
                "name": "x",
                "status": status,
            })
        r = self.client.get("/api/services/checkout/error_rate?latency=true&window_s=600")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(body["total"], 3)
        self.assertEqual(body["errors"], 1)
        self.assertIn("p95_ms", body)

    def test_health(self) -> None:
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["ok"])

    def test_metrics_endpoint(self) -> None:
        r = self.client.get("/metrics")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"span_ingest_total", r.data)

    def test_missing_required_field(self) -> None:
        r = self.client.post("/api/spans", json={"service": "x", "name": "y"})
        self.assertEqual(r.status_code, 400)


if __name__ == "__main__":
    unittest.main()
