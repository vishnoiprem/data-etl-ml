"""API key auth for the 4 data endpoints.

X-API-Key header is required for /traces, /query, /feedback, /eval.
The /healthz and /readyz probes stay open (K8s needs them).
The /docs and /openapi.json stay open (dev experience).

Key lookup is constant-time against a set built from settings.api_keys_list.
The key is never logged in full — only a 6-char prefix.
"""
from __future__ import annotations

import hmac

from fastapi import Depends, Header, HTTPException, status

from .settings import Settings, get_settings

_API_KEY_HEADER = "X-API-Key"


def _key_prefix(key: str) -> str:
    """Return a 6-char prefix for safe logging. Never the full key."""
    return key[:6] + "…" if len(key) > 6 else key


async def verify_api_key(
    x_api_key: str | None = Header(default=None, alias=_API_KEY_HEADER),
    settings: Settings = Depends(get_settings),
) -> str:
    """FastAPI dep. Returns the verified key, or raises 403.

    The returned string is the raw key — callers can use it as an actor id
    in audit events without re-checking. We do NOT echo the key in any
    response; the prefix is the only thing observable.
    """
    valid = settings.api_keys_list
    if not valid:
        # No keys configured = the server is not yet ready to serve traffic.
        # Fail closed. This is louder than a 403 with a key mismatch.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Server is not configured with any API keys. "
                   "Set APEX_API_KEYS in .env.",
        )
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing {_API_KEY_HEADER} header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    # Constant-time comparison: avoid timing oracles.
    # Compare against EVERY key (no early exit) with hmac.compare_digest;
    # `in set` is a hash lookup, not constant-time.
    ok = False
    for k in valid:
        ok |= hmac.compare_digest(x_api_key.encode(), k.encode())
    if not ok:
        # We don't differentiate "wrong key" from "unknown key" — both 403.
        # We don't log the candidate here, just the prefix of the request.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return x_api_key


def safe_key_for_log(key: str | None) -> str:
    """Logging helper. Returns the 6-char prefix or '<none>'."""
    if not key:
        return "<none>"
    return _key_prefix(key)
