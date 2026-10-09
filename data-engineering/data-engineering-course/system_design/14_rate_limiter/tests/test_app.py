"""HTTP-level tests for the rate limiter (Flask test client)."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.app import create_app  # noqa: E402
from code.service import RateLimiter  # noqa: E402


class RateLimiterAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rl = RateLimiter(capacity=1_000)
        self.app = create_app(self.rl)
        self.client = self.app.test_client()

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["ok"])

    def test_strategies_endpoint(self):
        r = self.client.get("/api/strategies")
        self.assertEqual(r.status_code, 200)
        self.assertIn("token_bucket", r.get_json()["available"])

    def test_check_allows_then_denies(self):
        # Token bucket: limit 3, fill up.
        for _ in range(3):
            r = self.client.post("/api/check", json={
                "key": "alpha", "limit": 3, "window_seconds": 60,
                "strategy": "token_bucket",
            })
            self.assertEqual(r.status_code, 200)
            self.assertTrue(r.get_json()["allowed"])
        r = self.client.post("/api/check", json={
            "key": "alpha", "limit": 3, "window_seconds": 60,
            "strategy": "token_bucket",
        })
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.get_json()["allowed"])
        self.assertIn("reset_in", r.get_json())

    def test_missing_params(self):
        r = self.client.post("/api/check", json={"key": "k"})
        self.assertEqual(r.status_code, 400)

    def test_invalid_strategy(self):
        r = self.client.post("/api/check", json={
            "key": "k", "limit": 1, "window_seconds": 60, "strategy": "nope",
        })
        self.assertEqual(r.status_code, 400)

    def test_reset_key(self):
        for _ in range(3):
            self.client.post("/api/check", json={
                "key": "x", "limit": 3, "window_seconds": 60,
                "strategy": "token_bucket",
            })
        r = self.client.delete("/api/keys/x")
        self.assertEqual(r.status_code, 200)
        r = self.client.post("/api/check", json={
            "key": "x", "limit": 3, "window_seconds": 60,
            "strategy": "token_bucket",
        })
        self.assertTrue(r.get_json()["allowed"])

    def test_metrics_endpoint(self):
        self.client.post("/api/check", json={
            "key": "k", "limit": 5, "window_seconds": 60,
        })
        r = self.client.get("/metrics")
        self.assertEqual(r.status_code, 200)
        self.assertIn("allow_total", r.get_data(as_text=True))

    def test_inspect(self):
        self.client.post("/api/check", json={
            "key": "y", "limit": 5, "window_seconds": 60,
            "strategy": "token_bucket",
        })
        r = self.client.get("/api/keys/y?strategy=token_bucket")
        self.assertEqual(r.status_code, 200)
        self.assertIn("state", r.get_json())


if __name__ == "__main__":
    unittest.main()
