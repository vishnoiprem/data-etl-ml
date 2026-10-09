"""Retry decorator with exponential backoff and optional jitter.

Wraps a function so that, on exception, it's retried with
exponential backoff. The last exception is re-raised if all
attempts are exhausted.

Usage::

    @retry(max_attempts=3, backoff=1.0, jitter=True)
    def flaky():
        ...

    @retry(max_attempts=5, backoff=0.5, jitter=False,
           retry_on=(ValueError,))
    def pickier():
        ...

Author: Prem Vishnoi <prem.vishnoi.example.com>
"""

from __future__ import annotations

import functools
import random
import time
from typing import Any, Callable, Optional, Tuple, Type, Union


def retry(
    max_attempts: int = 3,
    backoff: float = 1.0,
    jitter: bool = True,
    retry_on: Optional[Tuple[Type[BaseException], ...]] = None,
    sleep: Callable[[float], None] = time.sleep,
) -> Callable:
    """Decorator: retry ``fn`` with exponential backoff on failure.

    Parameters
    ----------
    max_attempts:
        Total attempts (including the first). Must be >= 1.
    backoff:
        Base wait time in seconds. The wait for attempt N is
        ``backoff * 2 ** (N - 1)``.
    jitter:
        If True, multiply the wait by a random factor in
        [0.5, 1.5) to spread retries.
    retry_on:
        Tuple of exception types to retry. ``None`` means
        retry on any exception.
    sleep:
        Sleep function. Defaults to ``time.sleep``. Tests
        inject a no-op.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")
    if backoff < 0:
        raise ValueError("backoff must be >= 0")

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_err: Optional[BaseException] = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:  # noqa: BLE001
                    if retry_on is not None and not isinstance(exc, retry_on):
                        raise
                    last_err = exc
                    if attempt == max_attempts:
                        break
                    wait = backoff * (2 ** (attempt - 1))
                    if jitter:
                        wait *= 0.5 + random.random()
                    sleep(wait)
            assert last_err is not None  # for type-checkers
            raise last_err

        return wrapper

    return decorator
