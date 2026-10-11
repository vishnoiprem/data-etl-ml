"""Offline tests for the request-parameter Lambda Authorizer.

Run with:  pytest test_param_authorizer.py -v
"""

from __future__ import annotations

import importlib.util
import os
import time
from pathlib import Path

import pytest

# Load the authorizer module without making it a package.
_HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("param_authorizer", _HERE / "param_authorizer.py")
assert _spec and _spec.loader
param_authorizer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(param_authorizer)


METHOD_ARN = "arn:aws:execute-api:us-east-1:111:abcd/prod/GET/admin/reindex"


def _event(user: str | None = None, token: str | None = None,
           method_arn: str = METHOD_ARN) -> dict:
    qs: dict = {}
    if user is not None:
        qs["user"] = user
    if token is not None:
        qs["token"] = token
    return {
        "type": "REQUEST",
        "methodArn": method_arn,
        "resource": "/admin/reindex",
        "path": "/admin/reindex",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": qs,
        "pathParameters": None,
        "stageVariables": {},
        "requestContext": {},
        "body": None,
        "isBase64Encoded": False,
    }


def _reset_cache() -> None:
    """Clear the module-level cache between tests."""
    # Drop and recreate the cache.
    param_authorizer._POLICY_CACHE = param_authorizer.TTLCache(
        max_size=128, ttl_seconds=300,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_valid_params_return_allow():
    _reset_cache()
    response = param_authorizer.lambda_handler(
        _event(user="alice", token="valid-alice-token"), context=None,
    )
    stmt = response["policyDocument"]["Statement"][0]
    assert stmt["Effect"] == "Allow"
    assert stmt["Resource"] == METHOD_ARN
    assert response["principalId"] == "alice"


def test_missing_user_returns_deny():
    _reset_cache()
    response = param_authorizer.lambda_handler(
        _event(user=None, token="valid-alice-token"), context=None,
    )
    stmt = response["policyDocument"]["Statement"][0]
    assert stmt["Effect"] == "Deny"


def test_missing_token_returns_deny():
    _reset_cache()
    response = param_authorizer.lambda_handler(
        _event(user="alice", token=None), context=None,
    )
    stmt = response["policyDocument"]["Statement"][0]
    assert stmt["Effect"] == "Deny"


def test_wrong_token_returns_deny():
    _reset_cache()
    response = param_authorizer.lambda_handler(
        _event(user="alice", token="WRONG"), context=None,
    )
    stmt = response["policyDocument"]["Statement"][0]
    assert stmt["Effect"] == "Deny"


def test_cache_key_built_from_user_and_token():
    _reset_cache()
    cache = param_authorizer._POLICY_CACHE
    assert cache.get("alice|valid-alice-token") is None

    param_authorizer.lambda_handler(
        _event(user="alice", token="valid-alice-token"), context=None,
    )
    # The cache now contains an entry keyed by the (user, token) pair.
    cached = cache.get("alice|valid-alice-token")
    assert cached is not None
    stmt = cached["policyDocument"]["Statement"][0]
    assert stmt["Effect"] == "Allow"


def test_cache_hit_skips_verification(monkeypatch):
    """The second identical request hits the cache — verification
    is bypassed even if the underlying token map is wiped.
    """
    _reset_cache()
    e = _event(user="alice", token="valid-alice-token")
    param_authorizer.lambda_handler(e, context=None)

    # Wipe the expected tokens map. Verification would now fail.
    param_authorizer._EXPECTED_TOKENS = {}

    # Second request still returns Allow because the cache hit
    # short-circuits verification.
    response = param_authorizer.lambda_handler(e, context=None)
    stmt = response["policyDocument"]["Statement"][0]
    assert stmt["Effect"] == "Allow"


def test_ttl_applied_to_cached_policy():
    """A cached entry that exceeds the TTL is treated as missing."""
    cache = param_authorizer.TTLCache(max_size=128, ttl_seconds=1)
    cache.set("k", {"value": 1})
    assert cache.get("k") == {"value": 1}

    time.sleep(1.1)
    assert cache.get("k") is None


def test_lru_evicts_oldest_when_full():
    """Once full, the least-recently-used entry is dropped first."""
    cache = param_authorizer.TTLCache(max_size=2, ttl_seconds=300)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)  # evicts "a"
    assert cache.get("a") is None
    assert cache.get("b") == 2
    assert cache.get("c") == 3


def test_cache_is_thread_safe():
    """Smoke test: many threads can hammer the cache."""
    import threading
    cache = param_authorizer.TTLCache(max_size=64, ttl_seconds=300)

    def worker(i):
        for j in range(50):
            cache.set(f"k{i}", j)
            cache.get(f"k{i}")

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    # If anything crashed, the test failed already. Length is at most 64.
    assert len(cache) <= 64