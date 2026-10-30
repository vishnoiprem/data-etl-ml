"""
Problem 06: Retry with exponential backoff for transient errors
Meta flavor: "Calling Meta Marketing API or Graph API: rate limits (HTTP 429),
gateway timeouts (504), and connection resets happen often. A naive retry loop
that bombs on a 400 will melt the API and your job. Distinguish transient from
permanent, retry only the transient, and log loudly."

How to Think:
- Two error classes:
  - TRANSIENT: 5xx, 429, network resets. Worth retrying.
  - PERMANENT: 4xx other than 429 (auth, validation). Never retry; surface up.
- Exponential backoff with jitter: sleep `base * 2^attempt + random`.
- Set a hard cap on attempts so the job cannot loop forever.
- Backoff must NOT break idempotency at the data layer -- use idempotency
  tokens where the API supports them (e.g. Graph dedup hash).

How to Remember:
- Retry only what would succeed if you tried again in a moment.

AI Use Cases
- Calling Meta Marketing/Graph APIs during ETL with predictable throttling.
- Polling cloud object stores for newly written partition files.
"""
from __future__ import annotations
import random
import time
from dataclasses import dataclass
from typing import Callable, TypeVar


T = TypeVar("T")


class PermanentError(Exception):
    """Do not retry."""


class TransientError(Exception):
    """Retry with backoff."""


@dataclass
class RetryPolicy:
    max_attempts: int = 5
    base_seconds: float = 0.5
    max_seconds: float = 30.0

    def sleep_for(self, attempt: int) -> float:
        # exponential with full jitter, capped
        exp = min(self.base_seconds * (2 ** attempt), self.max_seconds)
        return random.uniform(0, exp)


def call_with_retry(fn: Callable[[], T], policy: RetryPolicy = RetryPolicy()) -> T:
    last: Exception | None = None
    for attempt in range(policy.max_attempts):
        try:
            return fn()
        except PermanentError:
            raise
        except TransientError as e:
            last = e
            if attempt == policy.max_attempts - 1:
                break
            time.sleep(policy.sleep_for(attempt))
    raise last  # type: ignore[misc]


if __name__ == "__main__":
    attempts = {"n": 0}

    def flaky() -> str:
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise TransientError("gateway 504")
        return "ok"

    # monkey patch sleep to be instant for demo
    RetryPolicy.sleep_for = lambda self, attempt: 0  # type: ignore
    print("result:", call_with_retry(flaky))
    print("attempts:", attempts["n"])

    def bad() -> str:
        raise PermanentError("invalid token")

    try:
        call_with_retry(bad)
    except PermanentError as e:
        print("permanent surfaced, no retry:", e)
