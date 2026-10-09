"""HTTP-level tests for the Weather service."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.app import create_app  # noqa: E402
from code.service import SimulatedProvider, WeatherService  # noqa: E402


class WeatherAppTests(unittest.TestCase):
    def setUp(self) -> None:
        # Use a deterministic single provider for stable tests.
        self.svc = WeatherService(providers=[
            SimulatedProvider("only", 0, fail_rate=0.0, seed=42),
        ])
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def test_weather(self) -> None:
        r = self.client.get("/api/weather?lat=40.0&lng=-70.0")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(body["provider"], "only")
        self.assertFalse(body["cache_hit"])

    def test_cache_hit(self) -> None:
        self.client.get("/api/weather?lat=40.0&lng=-70.0")
        r = self.client.get("/api/weather?lat=40.0&lng=-70.0")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["cache_hit"])

    def test_nocache(self) -> None:
        self.client.get("/api/weather?lat=40.0&lng=-70.0")
        r = self.client.get("/api/weather?lat=40.0&lng=-70.0&nocache=1")
        self.assertFalse(r.get_json()["cache_hit"])

    def test_invalid_lat(self) -> None:
        r = self.client.get("/api/weather?lat=200&lng=0")
        self.assertEqual(r.status_code, 400)

    def test_providers(self) -> None:
        r = self.client.get("/api/providers")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["providers"][0]["name"], "only")

    def test_health_and_metrics(self) -> None:
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        r = self.client.get("/metrics")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"weather_total", r.data)


if __name__ == "__main__":
    unittest.main()
