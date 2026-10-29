"""Readiness probe: pings each downstream with a hard timeout.

Returns 200 if every dep is reachable within the timeout, 503 if any
fails. Each check is independent — one dep being down doesn't take the
others with it. The /healthz endpoint is a static liveness check;
this is the readiness check (K8s rolls traffic here).
"""
from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable

import httpx

from .settings import Settings

logger = logging.getLogger("apex.readyz")


async def _ping(url: str, timeout_s: float) -> tuple[bool, str]:
    """GET a URL with a hard timeout. Returns (ok, detail)."""
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            r = await client.get(url)
        if r.status_code < 500:
            return True, f"{r.status_code}"
        return False, f"http {r.status_code}"
    except httpx.TimeoutException:
        return False, "timeout"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


async def check_dependencies(settings: Settings) -> dict[str, dict[str, str | bool]]:
    """Ping Qdrant and ES concurrently. Return a per-dep status map.

    Each entry has `ok: bool` and `detail: str`. The /readyz route uses
    this to decide 200 vs 503.
    """
    timeout_s = settings.readyz_timeout_ms / 1000.0
    qdrant_url = f"{settings.qdrant_url.rstrip('/')}/healthz"
    es_url = f"{settings.es_url.rstrip('/')}/_cluster/health"
    q_task = asyncio.create_task(_ping(qdrant_url, timeout_s))
    e_task = asyncio.create_task(_ping(es_url, timeout_s))
    q_ok, q_detail = await q_task
    e_ok, e_detail = await e_task
    return {
        "qdrant": {"ok": q_ok, "detail": q_detail},
        "es": {"ok": e_ok, "detail": e_detail},
    }


def is_ready(statuses: dict[str, dict[str, str | bool]]) -> bool:
    """All deps must report ok. Conservative — one red dep = not ready."""
    return all(v["ok"] for v in statuses.values())
