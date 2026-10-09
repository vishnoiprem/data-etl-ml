"""HTTP-level tests for the Metrics + Logging service."""

from __future__ import annotations

import os
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.app import create_app  # noqa: E402
from code.service import MetricsLoggingService  # noqa: E402


class MetricsLoggingAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = MetricsLoggingService()
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def test_ingest_and_query(self) -> None:
        now = int(time.time())
        for i in range(3):
            r = self.client.post("/api/metrics", json={
                "name": "requests",
                "value": float(i),
                "labels": {"path": "/"},
                "ts": now + i,
            })
            self.assertEqual(r.status_code, 201)
        r = self.client.get(
            f"/api/query?metric=requests&from={now-5}&to={now+10}"
            f"&step=60&agg=sum"
        )
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertGreaterEqual(len(body["points"]), 1)

    def test_ingest_batch(self) -> None:
        r = self.client.post("/api/metrics", json=[
            {"name": "n", "value": 1.0},
            {"name": "n", "value": 2.0},
            {"name": "n", "value": 3.0},
        ])
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["ingested"], 3)

    def test_log_ingest_and_search(self) -> None:
        r = self.client.post("/api/logs", json={"msg": "hello", "level": "info"})
        self.assertEqual(r.status_code, 201)
        r = self.client.post("/api/logs", json={"msg": "world error", "level": "error"})
        self.assertEqual(r.status_code, 201)
        r = self.client.get("/api/logs?q=error")
        self.assertEqual(r.status_code, 200)
        results = r.get_json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["msg"], "world error")

    def test_health(self) -> None:
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertTrue(body["ok"])
        self.assertIn("stats", body)

    def test_metrics_endpoint(self) -> None:
        r = self.client.get("/metrics")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"ingest_total", r.data)


if __name__ == "__main__":
    unittest.main()
