"""Request-parameter Lambda Authorizer for AWS API Gateway (REST API).

Companion to L20.

Validates ``?user=<u>&token=<t>`` from the query string and returns
an IAM policy that allows invocation of the ``methodArn`` from the
event. Policies are cached in an in-process LRU with TTL.

Environment variables:
    CACHE_TTL_SECONDS  per-entry TTL for the internal cache. Default 300.
    CACHE_MAX_SIZE     max number of entries in the internal cache. Default 1024.
    EXPECTED_TOKENS    JSON-encoded ``{"user": "token", …}`` map. In a
                       real deployment, replace with a JWKS-backed
                       RS256 verifier (see lecture L09).
"""

from __future__ import annotations

import json
import os
import time
from collections import OrderedDict
from threading import Lock
from typing import Any, Dict, Generic, Optional, Tuple, TypeVar

K = TypeVar("K")
V = TypeVar("V")


# ---------------------------------------------------------------------------
# TTLCache — thread-safe LRU with per-entry TTL.
# ---------------------------------------------------------------------------

class TTLCache(Generic[K, V]):
    """Thread-safe LRU cache with per-entry TTL."""

    def __init__(self, max_size: int = 1024, ttl_seconds: int = 300):
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._data: "OrderedDict[K, Tuple[float, V]]" = OrderedDict()
        self._lock = Lock()

    def get(self, key: K) -> Optional[V]:
        now = time.time()
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            created_at, value = entry
            if now - created_at > self._ttl:
                # Expired — drop and report miss.
                self._data.pop(key, None)
                return None
            # Touch — move to the end so it's the "most recent".
            self._data.move_to_end(key)
            return value

    def set(self, key: K, value: V) -> None:
        now = time.time()
        with self._lock:
            self._data[key] = (now, value)
            self._data.move_to_end(key)
            while len(self._data) > self._max_size:
                self._data.popitem(last=False)

    # -- observability ----------------------------------------------------
    def __len__(self) -> int:
        with self._lock:
            return len(self._data)


# ---------------------------------------------------------------------------
# Default test fixtures. Real deployments read these from a JWKS or DB.
# ---------------------------------------------------------------------------

DEFAULT_EXPECTED_TOKENS: Dict[str, str] = {
    "alice": "valid-alice-token",
    "bob":   "valid-bob-token",
}


def _load_expected_tokens() -> Dict[str, str]:
    raw = os.environ.get("EXPECTED_TOKENS")
    if not raw:
        return DEFAULT_EXPECTED_TOKENS
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


# ---------------------------------------------------------------------------
# Internal cache + expected-tokens map.
# ---------------------------------------------------------------------------

_POLICY_CACHE: TTLCache[str, Dict[str, Any]] = TTLCache(
    max_size=int(os.environ.get("CACHE_MAX_SIZE", "1024")),
    ttl_seconds=int(os.environ.get("CACHE_TTL_SECONDS", "300")),
)

_EXPECTED_TOKENS: Dict[str, str] = _load_expected_tokens()


# ---------------------------------------------------------------------------
# Policy builders
# ---------------------------------------------------------------------------

def _allow(method_arn: str, principal_id: str,
           context: Dict[str, str]) -> Dict[str, Any]:
    return {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "execute-api:Invoke",
                    "Resource": method_arn,
                }
            ],
        },
        "context": context,
    }


def _deny(method_arn: str) -> Dict[str, Any]:
    return {
        "principalId": "unauthorized",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Deny",
                    "Action": "execute-api:Invoke",
                    "Resource": method_arn,
                }
            ],
        },
    }


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def _verify_token(user: str, token: str) -> bool:
    """Constant-time-ish comparison against the expected token for ``user``.

    For the demo we look the token up in a dict. In production this
    would be a JWKS-backed RS256 verifier.
    """
    expected = _EXPECTED_TOKENS.get(user)
    if expected is None:
        return False
    # Constant-time-ish. Not a true constant-time compare, but
    # better than ``==`` for shared secrets of different length.
    if len(expected) != len(token):
        return False
    result = 0
    for a, b in zip(expected, token):
        result |= ord(a) ^ ord(b)
    return result == 0


def _build_cache_key(user: str, token: str) -> str:
    """The pipe character can't appear in either user or token in
    practice, so it's a safe separator.
    """
    return f"{user}|{token}"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """API Gateway REQUEST authorizer entry point.

    Reads ``user`` and ``token`` from the query string and returns
    an Allow / Deny IAM policy. Policies are cached in an
    in-process LRU keyed by ``(user, token)`` with TTL
    ``CACHE_TTL_SECONDS``.
    """
    method_arn = event.get("methodArn", "")
    qs = event.get("queryStringParameters") or {}
    user = qs.get("user", "")
    token = qs.get("token", "")

    if not user or not token:
        return _deny(method_arn)

    cache_key = _build_cache_key(user, token)
    cached = _POLICY_CACHE.get(cache_key)
    if cached is not None:
        return cached

    if not _verify_token(user, token):
        return _deny(method_arn)

    policy = _allow(method_arn, user, {"sub": user, "tenant": user})
    _POLICY_CACHE.set(cache_key, policy)
    return policy