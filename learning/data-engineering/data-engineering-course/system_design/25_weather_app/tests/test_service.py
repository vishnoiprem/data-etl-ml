"""Service-level tests for the Weather service."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.service import (  # noqa: E402
    CLOSED, HALF_OPEN, OPEN, CircuitBreaker, SimulatedProvider, WeatherService,
)


class CircuitBreakerTests(unittest.TestCase):
    def test_starts_closed_and_allows(self) -> None:
        br = CircuitBreaker("t")
        self.assertEqual(br.state, CLOSED)
        self.assertTrue(br.allow())

    def test_opens_after_threshold(self) -> None:
        br = CircuitBreaker("t", threshold=2, cooldown_s=10)
        br.record_failure()
        self.assertEqual(br.state, CLOSED)
        br.record_failure()
        self.assertEqual(br.state, OPEN)
        self.assertFalse(br.allow())

    def test_half_open_after_cooldown(self) -> None:
        br = CircuitBreaker("t", threshold=1, cooldown_s=0.0)
        br.record_failure()
        # Cooldown is 0 — allow should immediately move to HALF_OPEN.
        self.assertTrue(br.allow())
        self.assertEqual(br.state, HALF_OPEN)

    def test_half_open_success_closes(self) -> None:
        br = CircuitBreaker("t", threshold=1, cooldown_s=0.0)
        br.record_failure()
        self.assertTrue(br.allow())
        br.record_success()
        self.assertEqual(br.state, CLOSED)

    def test_half_open_failure_reopens(self) -> None:
        br = CircuitBreaker("t", threshold=1, cooldown_s=0.0)
        br.record_failure()
        self.assertTrue(br.allow())  # -> HALF_OPEN
        br.record_failure()
        self.assertEqual(br.state, OPEN)


class WeatherServiceTests(unittest.TestCase):
    def test_returns_weather(self) -> None:
        svc = WeatherService(providers=[
            SimulatedProvider("a", 0, fail_rate=0.0, seed=1),
        ])
        r = svc.get_weather(40.0, -70.0)
        self.assertEqual(r["provider"], "a")
        self.assertIn("temp_c", r)

    def test_cache_hit_on_second_call(self) -> None:
        svc = WeatherService(providers=[
            SimulatedProvider("a", 0, fail_rate=0.0, seed=1),
        ])
        r1 = svc.get_weather(40.0, -70.0)
        r2 = svc.get_weather(40.0, -70.0)
        self.assertFalse(r1["cache_hit"])
        self.assertTrue(r2["cache_hit"])

    def test_nocache_bypasses(self) -> None:
        svc = WeatherService(providers=[
            SimulatedProvider("a", 0, fail_rate=0.0, seed=1),
        ])
        svc.get_weather(40.0, -70.0)
        r = svc.get_weather(40.0, -70.0, nocache=True)
        self.assertFalse(r["cache_hit"])

    def test_falls_back_to_secondary_provider(self) -> None:
        # Provider A always fails, B succeeds.
        svc = WeatherService(providers=[
            SimulatedProvider("a", 0, fail_rate=1.0, seed=1),
            SimulatedProvider("b", 1, fail_rate=0.0, seed=2),
        ])
        r = svc.get_weather(40.0, -70.0)
        self.assertEqual(r["provider"], "b")

    def test_breaker_opens_after_failures(self) -> None:
        svc = WeatherService(providers=[
            SimulatedProvider("a", 0, fail_rate=1.0, seed=1),
        ])
        for _ in range(3):
            try:
                svc.get_weather(40.0, -70.0, nocache=True)
            except RuntimeError:
                pass
        snap = svc.provider_health()[0]
        self.assertEqual(snap["name"], "a")
        self.assertEqual(snap["state"], OPEN)

    def test_all_providers_fail_raises(self) -> None:
        svc = WeatherService(providers=[
            SimulatedProvider("a", 0, fail_rate=1.0, seed=1),
            SimulatedProvider("b", 1, fail_rate=1.0, seed=2),
        ])
        with self.assertRaises(RuntimeError):
            svc.get_weather(40.0, -70.0)

    def test_grid_key_groups_nearby(self) -> None:
        from code.service import grid_key
        self.assertEqual(grid_key(40.123, -70.456), grid_key(40.1, -70.5))

    def test_provider_health_lists_all(self) -> None:
        svc = WeatherService()
        snap = svc.provider_health()
        names = {s["name"] for s in snap}
        self.assertEqual(names, {"provider_a", "provider_b", "provider_c"})

    def test_validates_lat_lng(self) -> None:
        svc = WeatherService()
        with self.assertRaises(ValueError):
            svc.get_weather(200, 0)


if __name__ == "__main__":
    unittest.main()
