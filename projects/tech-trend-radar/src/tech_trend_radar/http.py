"""One HTTP client, shared by every adapter.

Timeouts and the user agent are configured in exactly one place. Adapters
never build their own client — a source that hangs must not be able to hang
the whole run.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from .config import Settings, utcnow

#: Status codes worth retrying: the server asked us to slow down, or the
#: request hit a transient gateway error.
RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})


class HttpClient:
    """A thin wrapper over `httpx.Client` with the project's shared policy.

    Retries are limited to rate limits and transient server errors, with a
    growing delay between attempts. Several of the free APIs here
    (dev.to, GitHub's unauthenticated search) rate-limit aggressively, and a
    retry loop turns a spurious "source failed" into a normal run.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self._client = httpx.Client(
            timeout=self.settings.timeout_seconds,
            follow_redirects=True,
            headers={"User-Agent": self.settings.user_agent},
        )

    def _get(self, url: str, **kwargs: Any) -> httpx.Response:
        """GET with a bounded retry on rate limits and transient errors."""
        attempts = self.settings.max_retries + 1
        last_error: Exception | None = None

        for attempt in range(attempts):
            try:
                response = self._client.get(url, **kwargs)
            except httpx.TransportError as exc:
                last_error = exc
                if attempt == attempts - 1:
                    raise
                time.sleep(self._backoff(attempt))
                continue

            if response.status_code in RETRY_STATUSES and attempt < attempts - 1:
                time.sleep(self._backoff(attempt))
                continue

            response.raise_for_status()
            return response

        raise last_error or httpx.HTTPError(f"GET {url} failed")

    @staticmethod
    def _backoff(attempt: int) -> float:
        """Exponential-ish backoff, capped so a run never hangs long."""
        return min(0.5 * (2**attempt), 4.0)

    def get_json(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        response = self._get(url, params=params, headers=headers)
        return response.json()

    def get_text(self, url: str, headers: dict[str, str] | None = None) -> str:
        response = self._get(url, headers=headers)
        return response.text

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> HttpClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def normalise_engagement(raw: float, platform_weight: float) -> float:
    """Squash a platform's raw engagement counter onto one comparable scale.

    Raw counters are not comparable across platforms: 500 Hacker News points
    is a large event, 500 dev.to reactions is a mild one, and GitHub stars
    accumulate indefinitely. A log squashes the long tail, then the platform
    weight expresses how much a unit of that platform's engagement is worth
    relative to the others.

    `log1p` rather than `log` so zero engagement stays zero instead of
    becoming negative infinity.
    """
    import math

    if raw <= 0:
        return 0.0
    scaled = math.log1p(raw) / math.log1p(100.0)
    return scaled * platform_weight


def now() -> object:
    return utcnow()
