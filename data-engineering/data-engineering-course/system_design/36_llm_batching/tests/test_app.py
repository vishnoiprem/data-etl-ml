"""HTTP-level tests for the LLM batching service."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.app import create_app  # noqa: E402
from code.service import BatchingService  # noqa: E402


class BatchingAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = BatchingService(batch_size=4, window_ms=20.0)
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        self.svc.shutdown()

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["ok"])

    def test_submit_returns_query_id(self):
        r = self.client.post("/api/queries", json={"prompt": "hello"})
        self.assertEqual(r.status_code, 202)
        self.assertIn("query_id", r.get_json())

    def test_submit_rejects_empty(self):
        r = self.client.post("/api/queries", json={"prompt": ""})
        self.assertEqual(r.status_code, 400)

    def test_get_with_wait_blocks_until_done(self):
        r = self.client.post("/api/queries", json={"prompt": "hello"})
        qid = r.get_json()["query_id"]
        # wait=1 with a generous timeout — should resolve done.
        r2 = self.client.get(f"/api/queries/{qid}?wait=1&timeout=2.0")
        self.assertEqual(r2.status_code, 200)
        body = r2.get_json()
        self.assertEqual(body["status"], "done")
        self.assertIsNotNone(body["response"])
        self.assertIsNotNone(body["batch_id"])

    def test_flush_endpoint(self):
        self.client.post("/api/queries", json={"prompt": "a"})
        self.client.post("/api/queries", json={"prompt": "b"})
        r = self.client.post("/api/queries/flush")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["flushed"], 2)

    def test_stats_endpoint(self):
        ids = []
        for i in range(4):
            r = self.client.post("/api/queries", json={"prompt": f"p-{i}"})
            ids.append(r.get_json()["query_id"])
        for qid in ids:
            self.client.get(f"/api/queries/{qid}?wait=1&timeout=1.0")
        r = self.client.get("/stats")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertGreaterEqual(body["batches"], 1)
        self.assertEqual(body["queries_in_batches"], 4)
        self.assertGreater(body["throughput_x"], 1.0)

    def test_metrics_endpoint(self):
        r = self.client.get("/metrics")
        self.assertEqual(r.status_code, 200)
        self.assertIn("queries_submitted_total", r.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
