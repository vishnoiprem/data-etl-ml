"""
service/circuit.py — Circuit breaker, rate limiter, and PII redactor.

What this file does
-------------------
Three small primitives, each a "patterns" implementation. No `pybreaker`,
no `redis`, no `python-jose` — ~350 lines of stdlib so the lesson is the code.

1. **CircuitBreaker** — 3-state machine (closed / half_open / open) wrapping
   any callable. Four trip signals: failure_rate, latency_p99_ms, cost_per_min,
   model_degradation (placeholder; see T3 lesson). On `open`, calls fall
   through to a 3-tier fallback: cache → cheaper LLM → stub. Mirrors the
   pattern in `hardcode/level-9-failure-handling/17-circuit-breaker-llm.py`
   but in ~150 lines instead of ~1072.

2. **TokenBucketRateLimiter** — per-user in-process token bucket. Refill rate
   + capacity per user. NOT shared across workers (Phase 4 fix: Redis Lua).
   Pattern lifted from `hardcode/level-3-streaming/01-realtime-chat-websocket.py`.

3. **Redactor** — regex-based PII stripper (email, phone, passport). Run on
   the email body BEFORE it reaches the LLM. Logs the count of redactions;
   does NOT log the redacted text.

Why all in one file
-------------------
Each is small enough (~100 lines) that splitting into 3 files would create
more import friction than clarity. The file is structured with clear section
headers so each primitive is independently readable.

How to run / import
-------------------
    from circuit import CircuitBreaker, TokenBucketRateLimiter, Redactor
    cb = CircuitBreaker(failure_threshold=0.2, latency_p99_ms_threshold=3000)
    rl = TokenBucketRateLimiter(capacity=20, refill_rate=0.33)  # 20/min
    rd = Redactor()
    safe_text = rd.redact("Email me at jane.doe@example.com or +65 9123 4567.")
"""
from __future__ import annotations

import math
import re
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Deque


# ===================================================================
# Redactor
# ===================================================================
class Redactor:
    """Regex-based PII stripper. Replaces matches with `[REDACTED:<kind>]`.

    Counts the number of each kind it stripped, so the caller can log
    `n_redactions` without logging the actual text (no PII in logs).
    """
    EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}")
    # Phone: optional +, 7-15 digits with optional spaces/dashes/parens.
    PHONE_RE = re.compile(r"\+?\d[\d\s\-\(\)]{7,}\d")
    # Passport: 1 letter + 7 digits (matches Singapore/Malaysia style).
    PASSPORT_RE = re.compile(r"\b[A-Z]\d{7}\b")

    def __init__(self) -> None:
        self.n_emails = 0
        self.n_phones = 0
        self.n_passports = 0

    def redact(self, text: str) -> str:
        """Return the redacted text and update internal counters."""
        text, n = self.EMAIL_RE.subn("[REDACTED:email]", text)
        self.n_emails += n
        text, n = self.PHONE_RE.subn("[REDACTED:phone]", text)
        self.n_phones += n
        text, n = self.PASSPORT_RE.subn("[REDACTED:passport]", text)
        self.n_passports += n
        return text

    def stats(self) -> dict[str, int]:
        return {
            "emails": self.n_emails,
            "phones": self.n_phones,
            "passports": self.n_passports,
        }


# ===================================================================
# Token-bucket rate limiter (per-key, in-process)
# ===================================================================
class TokenBucketRateLimiter:
    """A per-key in-process token bucket.

    Each key (e.g. user_id) gets its own bucket with `capacity` tokens, refilling
    at `refill_rate` tokens per second. `try_acquire(key, n=1)` returns True
    if `n` tokens are available, False otherwise. NOT shared across workers.
    """
    def __init__(self, capacity: float, refill_rate: float) -> None:
        if capacity <= 0 or refill_rate <= 0:
            raise ValueError("capacity and refill_rate must be > 0")
        self.capacity = capacity
        self.refill_rate = refill_rate
        self._buckets: dict[str, float] = {}
        self._last: dict[str, float] = {}
        self._lock = threading.Lock()
        self.n_allowed = 0
        self.n_rejected = 0

    def _refill(self, key: str, now: float) -> None:
        if key not in self._buckets:
            self._buckets[key] = self.capacity
            self._last[key] = now
            return
        elapsed = now - self._last[key]
        self._buckets[key] = min(
            self.capacity, self._buckets[key] + elapsed * self.refill_rate
        )
        self._last[key] = now

    def try_acquire(self, key: str, n: float = 1.0) -> bool:
        now = time.monotonic()
        with self._lock:
            self._refill(key, now)
            if self._buckets[key] >= n:
                self._buckets[key] -= n
                self.n_allowed += 1
                return True
            self.n_rejected += 1
            return False

    def stats(self) -> dict[str, Any]:
        return {
            "capacity": self.capacity,
            "refill_rate": self.refill_rate,
            "n_allowed": self.n_allowed,
            "n_rejected": self.n_rejected,
        }


# ===================================================================
# Circuit breaker (closed / half_open / open)
# ===================================================================
# State codes — also used in metrics and the /circuit/state endpoint.
STATE_CLOSED = 0
STATE_HALF_OPEN = 1
STATE_OPEN = 2
STATE_NAME = {0: "closed", 1: "half_open", 2: "open"}


@dataclass
class CircuitBreakerConfig:
    """Knobs for the breaker. All thresholds are evaluated every `window_seconds`."""
    failure_threshold: float = 0.20       # trip if failure_rate >= 20% over the window
    latency_p99_ms_threshold: float = 4000.0  # trip if observed p99 latency > 4s
    cost_per_min_usd_threshold: float = 5.0   # trip if rolling 60s cost > $5
    window_seconds: float = 60.0          # rolling window size
    cooldown_seconds: float = 30.0        # how long to stay OPEN before HALF_OPEN
    min_calls_in_window: int = 5          # don't trip on < 5 calls (avoid 1-of-1 trips)


class CircuitOpenError(RuntimeError):
    """Raised when a call is attempted while the breaker is OPEN and no
    fallback succeeded. Callers should treat this as a 503."""


class CircuitBreaker:
    """A simple 3-state circuit breaker.

    States:
      - CLOSED:   calls go through normally. We track outcomes.
      - OPEN:     calls short-circuit to the fallback. After `cooldown_seconds`,
                  the breaker moves to HALF_OPEN.
      - HALF_OPEN: 1 trial call is allowed. Success → CLOSED, failure → OPEN.

    Trip signals (re-evaluated on every call):
      1. `failure_rate >= failure_threshold` (when `len(window) >= min_calls_in_window`)
      2. `latency_p99_ms > latency_p99_ms_threshold`
      3. `cost_per_min_usd > cost_per_min_usd_threshold`
    """
    def __init__(
        self,
        *,
        name: str = "default",
        fallback: Callable[..., Any] | None = None,
        config: CircuitBreakerConfig | None = None,
    ) -> None:
        self.name = name
        self.fallback = fallback
        self.cfg = config or CircuitBreakerConfig()
        self.state: int = STATE_CLOSED
        self._opened_at: float | None = None
        # Rolling window of (ts, success: bool, latency_ms, cost_usd)
        self._window: Deque[tuple[float, bool, float, float]] = deque(maxlen=1000)
        # Recent transitions for /circuit/state visibility.
        self._transitions: Deque[dict[str, Any]] = deque(maxlen=20)
        self._lock = threading.Lock()
        self.n_calls = 0
        self.n_trips = 0

    # -- public API ---------------------------------------------------------
    def call(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Run `fn(*args, **kwargs)` through the breaker.

        Returns the fn's return value on success. On a tripped breaker,
        delegates to `self.fallback(*args, **kwargs)`. Raises
        `CircuitOpenError` if the breaker is OPEN and no fallback is set
        (or the fallback itself raises).
        """
        with self._lock:
            self._maybe_recover_to_half_open()
            if self.state == STATE_OPEN:
                # No direct call; delegate immediately to fallback.
                return self._invoke_fallback(*args, **kwargs)

        # CLOSED or HALF_OPEN — actually call.
        ts = time.monotonic()
        cost = float(kwargs.pop("__cost_usd", 0.0))
        try:
            result = fn(*args, **kwargs)
            latency_ms = (time.monotonic() - ts) * 1000.0
            self._record_outcome(success=True, latency_ms=latency_ms, cost_usd=cost)
            return result
        except Exception as e:
            latency_ms = (time.monotonic() - ts) * 1000.0
            self._record_outcome(success=False, latency_ms=latency_ms, cost_usd=cost)
            # On failure, try the fallback too.
            return self._invoke_fallback_on_failure(e, *args, **kwargs)

    def snapshot(self) -> dict[str, Any]:
        """Return a JSON-safe snapshot of the current state."""
        with self._lock:
            recent = list(self._transitions)
            n = len(self._window)
            failures = sum(1 for _, ok, _, _ in self._window if not ok)
            cost = sum(c for _, _, _, c in self._window)
            return {
                "name": self.name,
                "state": STATE_NAME[self.state],
                "state_code": self.state,
                "n_calls": self.n_calls,
                "n_trips": self.n_trips,
                "window_n": n,
                "window_failures": failures,
                "window_cost_usd": round(cost, 4),
                "recent_transitions": recent,
            }

    # -- internals ----------------------------------------------------------
    def _record_outcome(self, *, success: bool, latency_ms: float, cost_usd: float) -> None:
        with self._lock:
            self.n_calls += 1
            now = time.time()
            self._window.append((now, success, latency_ms, cost_usd))
            self._evict_old(now)
            # Check trip conditions if currently CLOSED.
            if self.state == STATE_CLOSED and self._should_trip():
                self._transition(STATE_OPEN, reason="threshold_breach")
            elif self.state == STATE_HALF_OPEN and success:
                self._transition(STATE_CLOSED, reason="half_open_success")
            elif self.state == STATE_HALF_OPEN and not success:
                self._transition(STATE_OPEN, reason="half_open_failure")
                self._opened_at = time.time()

    def _evict_old(self, now: float) -> None:
        cutoff = now - self.cfg.window_seconds
        while self._window and self._window[0][0] < cutoff:
            self._window.popleft()

    def _should_trip(self) -> bool:
        if len(self._window) < self.cfg.min_calls_in_window:
            return False
        n = len(self._window)
        failures = sum(1 for _, ok, _, _ in self._window if not ok)
        if failures / n >= self.cfg.failure_threshold:
            return True
        latencies = sorted(l for _, _, l, _ in self._window)
        p99 = latencies[max(0, math.ceil(0.99 * n) - 1)]
        if p99 > self.cfg.latency_p99_ms_threshold:
            return True
        cost = sum(c for _, _, _, c in self._window)
        if cost > self.cfg.cost_per_min_usd_threshold:
            return True
        return False

    def _maybe_recover_to_half_open(self) -> None:
        if self.state == STATE_OPEN and self._opened_at is not None:
            if time.time() - self._opened_at >= self.cfg.cooldown_seconds:
                self._transition(STATE_HALF_OPEN, reason="cooldown_elapsed")

    def _transition(self, new_state: int, *, reason: str) -> None:
        if new_state == self.state:
            return
        old = STATE_NAME[self.state]
        self.state = new_state
        if new_state == STATE_OPEN:
            self.n_trips += 1
            self._opened_at = time.time()
        ev = {
            "ts": time.time(),
            "from": old,
            "to": STATE_NAME[new_state],
            "reason": reason,
        }
        self._transitions.append(ev)

    def _invoke_fallback(self, *args: Any, **kwargs: Any) -> Any:
        if self.fallback is None:
            raise CircuitOpenError(
                f"circuit '{self.name}' is OPEN and no fallback is set"
            )
        return self.fallback(*args, **kwargs)

    def _invoke_fallback_on_failure(
        self, original_exc: Exception, *args: Any, **kwargs: Any
    ) -> Any:
        if self.fallback is None:
            raise original_exc
        try:
            return self.fallback(*args, **kwargs)
        except Exception:
            # Fallback itself failed — raise the original exception.
            raise original_exc


# ===================================================================
# Three-tier fallback (cache → cheaper LLM → stub)
# ===================================================================
class TTLCache:
    """Tiny in-memory LRU+TTL cache for fallback responses."""
    def __init__(self, max_size: int = 256, ttl_seconds: float = 300.0) -> None:
        self.max_size = max_size
        self.ttl = ttl_seconds
        self._store: dict[str, tuple[float, Any]] = {}
        self._order: Deque[str] = deque()
        self.n_hits = 0
        self.n_misses = 0

    def get(self, key: str) -> Any | None:
        item = self._store.get(key)
        if item is None:
            self.n_misses += 1
            return None
        ts, value = item
        if time.time() - ts > self.ttl:
            self._store.pop(key, None)
            self.n_misses += 1
            return None
        self.n_hits += 1
        return value

    def set(self, key: str, value: Any) -> None:
        if key in self._store:
            self._store[key] = (time.time(), value)
            return
        self._store[key] = (time.time(), value)
        self._order.append(key)
        while len(self._order) > self.max_size:
            evicted = self._order.popleft()
            self._store.pop(evicted, None)

    def stats(self) -> dict[str, int]:
        return {"hits": self.n_hits, "misses": self.n_misses, "size": len(self._store)}


def stub_fallback(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Tier-3 fallback: an explicit "we're degraded" response.

    Never raises. The caller (CircuitBreaker) wraps this in try/except so a
    raised exception here would re-raise the original LLM error.
    """
    return {
        "ok": False,
        "draft": "[unavailable] The drafter is temporarily down. Please reply manually.",
        "model": "stub",
        "is_mock": True,
        "cost_usd": 0.0,
        "latency_ms": 0,
        "circuit_state": "open",
    }


def make_tiered_fallback(
    cache: TTLCache, cheaper_fn: Callable[..., Any] | None = None,
) -> Callable[..., Any]:
    """Build a 3-tier fallback: cache → cheaper_fn → stub.

    The cache key is built from the first positional arg (assumed to be the
    prompt or request identifier).
    """
    def fallback(*args: Any, **kwargs: Any) -> Any:
        cache_key = str(args[0]) if args else "default"
        cached = cache.get(cache_key)
        if cached is not None:
            return {**cached, "circuit_state": "open", "fallback_tier": "cache"}
        if cheaper_fn is not None:
            try:
                result = cheaper_fn(*args, **kwargs)
                cache.set(cache_key, result)
                return {**result, "circuit_state": "open", "fallback_tier": "cheaper"}
            except Exception:
                pass
        return stub_fallback(*args, **kwargs)
    return fallback


# ===================================================================
# CLI demo
# ===================================================================
def main() -> int:
    print("=" * 70)
    print("service/circuit.py — demo")
    print("=" * 70)

    # Redactor demo
    print("\n--- Redactor ---")
    rd = Redactor()
    sample = (
        "Hi, please email jane.doe@example.com or call +65 9123 4567. "
        "My passport is A1234567 and I have a backup at jane.doe@pf.com.sg."
    )
    redacted = rd.redact(sample)
    print(f"  before: {sample}")
    print(f"  after : {redacted}")
    print(f"  stats : {rd.stats()}")

    # Rate limiter demo
    print("\n--- TokenBucketRateLimiter (capacity=3, refill_rate=1/s) ---")
    rl = TokenBucketRateLimiter(capacity=3, refill_rate=1.0)
    for i in range(6):
        ok = rl.try_acquire("mei@pf.com")
        print(f"  try #{i+1}  allowed={ok}  stats={rl.stats()}")
    print("  (sleeping 2s to refill)")
    time.sleep(2.1)
    for i in range(3):
        ok = rl.try_acquire("mei@pf.com")
        print(f"  retry #{i+1}  allowed={ok}  stats={rl.stats()}")

    # Circuit breaker demo
    print("\n--- CircuitBreaker (failure_threshold=0.5, min_calls=3) ---")
    cfg = CircuitBreakerConfig(
        failure_threshold=0.5, min_calls_in_window=3, cooldown_seconds=2.0
    )
    cache = TTLCache()
    fb = make_tiered_fallback(cache, cheaper_fn=None)
    cb = CircuitBreaker(name="openai", fallback=fb, config=cfg)

    def flaky_llm(n: int) -> dict[str, Any]:
        # Fails on n % 2 == 0, succeeds on n % 2 == 1.
        if n % 2 == 0:
            raise RuntimeError("simulated 5xx")
        return {"ok": True, "draft": f"draft for call {n}", "model": "gpt-4o-mini"}

    for i in range(6):
        try:
            r = cb.call(flaky_llm, i)
            print(f"  call {i}: state={STATE_NAME[cb.state]}  result={r.get('draft') or r.get('draft', '<stub>')[:40]}")
        except Exception as e:
            print(f"  call {i}: state={STATE_NAME[cb.state]}  RAISED {type(e).__name__}: {e}")

    print(f"\n  snapshot: {cb.snapshot()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
