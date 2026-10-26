"""Weather service with provider fanout, grid-cell cache, circuit breakers.

We simulate three providers with different reliability. The breaker state
machine is per provider: CLOSED -> OPEN -> HALF_OPEN -> CLOSED/OPEN.
"""

from __future__ import annotations

import random
import threading
import time
from typing import Callable, Optional

from common.cache import TTLCache
from common.storage import KeyValueStore

CACHE_TTL_S = 300.0
GRID_PRECISION = 1  # decimal places; ~11km
BREAKER_THRESHOLD = 3
BREAKER_COOLDOWN_S = 30.0

CLOSED = "closed"
OPEN = "open"
HALF_OPEN = "half_open"


def _now_ms() -> int:
    return int(time.time() * 1000)


def grid_key(lat: float, lng: float) -> str:
    return f"grid:{round(lat, GRID_PRECISION)}:{round(lng, GRID_PRECISION)}"


# ----------------------------------------------------------------------
# CircuitBreaker
# ----------------------------------------------------------------------


class CircuitBreaker:
    """A simple three-state breaker."""

    def __init__(
        self,
        name: str,
        threshold: int = BREAKER_THRESHOLD,
        cooldown_s: float = BREAKER_COOLDOWN_S,
    ):
        self.name = name
        self.threshold = threshold
        self.cooldown_s = cooldown_s
        self.state = CLOSED
        self.failures = 0
        self.successes = 0
        self.opened_at_ms = 0
        self._lock = threading.Lock()

    def allow(self) -> bool:
        with self._lock:
            if self.state == CLOSED:
                return True
            if self.state == OPEN:
                if (_now_ms() - self.opened_at_ms) / 1000.0 >= self.cooldown_s:
                    self.state = HALF_OPEN
                    return True
                return False
            # HALF_OPEN: allow one trial.
            return True

    def record_success(self) -> None:
        with self._lock:
            self.successes += 1
            self.failures = 0
            self.state = CLOSED
            self.opened_at_ms = 0

    def record_failure(self) -> None:
        with self._lock:
            self.failures += 1
            if self.state == HALF_OPEN:
                self.state = OPEN
                self.opened_at_ms = _now_ms()
            elif self.failures >= self.threshold:
                self.state = OPEN
                self.opened_at_ms = _now_ms()

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "name": self.name,
                "state": self.state,
                "failures": self.failures,
                "successes": self.successes,
                "opened_at_ms": self.opened_at_ms,
            }


# ----------------------------------------------------------------------
# SimulatedProvider
# ----------------------------------------------------------------------


class SimulatedProvider:
    """A stand-in upstream weather provider."""

    def __init__(
        self,
        name: str,
        priority: int,
        fail_rate: float = 0.0,
        latency_ms_range: tuple[int, int] = (5, 30),
        seed: Optional[int] = None,
    ):
        self.name = name
        self.priority = priority
        self.fail_rate = fail_rate
        self.latency_range = latency_ms_range
        self._rng = random.Random(seed) if seed is not None else random.Random()

    def fetch(self, lat: float, lng: float) -> dict:
        # Simulate latency. We don't actually sleep in tests, but the
        # hook is here for realism.
        lo, hi = self.latency_range
        time.sleep(self._rng.uniform(lo, hi) / 1000.0)
        if self._rng.random() < self.fail_rate:
            raise RuntimeError(f"{self.name} simulated failure")
        return {
            "provider": self.name,
            "lat": lat,
            "lng": lng,
            "temp_c": round(self._rng.uniform(-5, 35), 1),
            "conditions": self._rng.choice(["sunny", "cloudy", "rain", "snow"]),
            "wind_kph": round(self._rng.uniform(0, 50), 1),
            "fetched_at_ms": _now_ms(),
        }


# ----------------------------------------------------------------------
# WeatherService
# ----------------------------------------------------------------------


class WeatherService:
    def __init__(
        self,
        store: Optional[KeyValueStore] = None,
        providers: Optional[list[SimulatedProvider]] = None,
        cache_ttl_s: float = CACHE_TTL_S,
    ):
        self.store = store or KeyValueStore("weather", persist_path=None)
        self.cache = TTLCache(ttl_seconds=cache_ttl_s, max_entries=50_000)
        if providers is None:
            providers = [
                SimulatedProvider("provider_a", priority=0, fail_rate=0.0, seed=1),
                SimulatedProvider("provider_b", priority=1, fail_rate=0.3, seed=2),
                SimulatedProvider("provider_c", priority=2, fail_rate=0.5, seed=3),
            ]
        self.providers = sorted(providers, key=lambda p: p.priority)
        self.breakers: dict[str, CircuitBreaker] = {
            p.name: CircuitBreaker(p.name) for p in self.providers
        }
        self._lock = threading.Lock()

    # ---- public API ---------------------------------------------------

    def get_weather(self, lat: float, lng: float, nocache: bool = False) -> dict:
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            raise ValueError("lat/lng out of range")
        key = grid_key(lat, lng)
        if not nocache:
            cached = self.cache.get(key)
            if cached is not None:
                return {**cached, "cache_hit": True}

        last_error: Optional[Exception] = None
        tried: list[str] = []
        for prov in self.providers:
            br = self.breakers[prov.name]
            if not br.allow():
                tried.append(f"{prov.name}:open")
                continue
            tried.append(prov.name)
            try:
                payload = prov.fetch(lat, lng)
                br.record_success()
                self.cache.set(key, payload)
                return {**payload, "cache_hit": False, "tried": tried}
            except Exception as e:  # noqa: BLE001
                br.record_failure()
                last_error = e
                continue

        # All providers failed. If we have stale cache, return it.
        stale = self.store.get(key)
        if stale:
            return {**stale, "cache_hit": True, "stale": True, "tried": tried}
        raise RuntimeError(
            f"all providers failed (tried={tried}): {last_error}"
        )

    def provider_health(self) -> list[dict]:
        out = []
        for br in self.breakers.values():
            out.append(br.snapshot())
        return out

    def stats(self) -> dict:
        return {
            "cache": self.cache.stats(),
            "providers": [
                {"name": p.name, "priority": p.priority, "fail_rate": p.fail_rate}
                for p in self.providers
            ],
        }
