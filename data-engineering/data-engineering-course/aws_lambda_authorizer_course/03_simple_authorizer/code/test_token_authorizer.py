"""Offline tests for the token-based Lambda Authorizer.

Run with:  pytest test_token_authorizer.py -v
"""

from __future__ import annotations

import importlib.util
import os
import time
from pathlib import Path

import jwt
import pytest

# Load the authorizer module without making it a package.
_HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("token_authorizer", _HERE / "token_authorizer.py")
assert _spec and _spec.loader
authorizer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(authorizer)


# Shared test fixtures
SECRET = "unit-test-secret"
ISSUER = "https://auth.example.com"
AUDIENCE = "api.example.com"
METHOD_ARN = "arn:aws:execute-api:us-east-1:111:abcd/prod/GET/orders"


def _mint(claims: dict | None = None, *, exp_offset: int = 60,
          secret: str = SECRET) -> str:
    """Mint an HS256 JWT with the standard claims."""
    payload = {
        "sub": "user-1",
        "tenant": "acme",
        "scope": "read",
        "iss": ISSUER,
        "aud": AUDIENCE,
    }
    if claims:
        payload.update(claims)
    payload["iat"] = int(time.time())
    payload["exp"] = int(time.time()) + exp_offset
    return jwt.encode(payload, secret, algorithm="HS256")


def _event(token: str | None, method_arn: str = METHOD_ARN,
           *, with_bearer: bool = True) -> dict:
    """Wrap a token in an API Gateway TOKEN authorizer event."""
    if token is None:
        auth_value = ""
    elif with_bearer:
        auth_value = f"Bearer {token}"
    else:
        auth_value = token
    return {
        "type": "TOKEN",
        "authorizationToken": auth_value,
        "methodArn": method_arn,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_valid_token_returns_allow(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", SECRET)
    monkeypatch.setenv("JWT_ISSUER", ISSUER)
    monkeypatch.setenv("JWT_AUDIENCE", AUDIENCE)

    response = authorizer.lambda_handler(_event(_mint()), context=None)

    assert response["principalId"] == "user-1"
    stmt = response["policyDocument"]["Statement"][0]
    assert stmt["Effect"] == "Allow"


def test_invalid_token_returns_deny(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", SECRET)
    # Token was minted with a different secret; verification fails.
    bad_token = _mint(secret="a-different-secret")
    response = authorizer.lambda_handler(_event(bad_token), context=None)
    stmt = response["policyDocument"]["Statement"][0]
    assert stmt["Effect"] == "Deny"


def test_missing_token_returns_deny(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", SECRET)
    response = authorizer.lambda_handler(_event(None), context=None)
    stmt = response["policyDocument"]["Statement"][0]
    assert stmt["Effect"] == "Deny"


def test_policy_resource_matches_method_arn(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", SECRET)
    response = authorizer.lambda_handler(_event(_mint()), context=None)
    stmt = response["policyDocument"]["Statement"][0]
    assert stmt["Resource"] == METHOD_ARN


def test_policy_action_is_execute_api_invoke(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", SECRET)
    response = authorizer.lambda_handler(_event(_mint()), context=None)
    stmt = response["policyDocument"]["Statement"][0]
    assert stmt["Action"] == "execute-api:Invoke"


def test_principal_id_extracted_from_sub_claim(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", SECRET)
    monkeypatch.setenv("JWT_ISSUER", ISSUER)
    monkeypatch.setenv("JWT_AUDIENCE", AUDIENCE)
    token = _mint(claims={"sub": "user-42"})
    response = authorizer.lambda_handler(_event(token), context=None)
    assert response["principalId"] == "user-42"


def test_expired_token_returns_deny(monkeypatch):
    """Extra coverage: expired tokens must be rejected."""
    monkeypatch.setenv("JWT_SECRET", SECRET)
    monkeypatch.setenv("JWT_ISSUER", ISSUER)
    monkeypatch.setenv("JWT_AUDIENCE", AUDIENCE)
    expired = _mint(exp_offset=-10)
    response = authorizer.lambda_handler(_event(expired), context=None)
    stmt = response["policyDocument"]["Statement"][0]
    assert stmt["Effect"] == "Deny"


def test_context_flattens_claims(monkeypatch):
    """Extra coverage: the context map is flat and string-valued."""
    monkeypatch.setenv("JWT_SECRET", SECRET)
    monkeypatch.setenv("JWT_ISSUER", ISSUER)
    monkeypatch.setenv("JWT_AUDIENCE", AUDIENCE)
    token = _mint(claims={
        "sub": "u-1",
        "tenant": "acme",
        "scope": "read",
    })
    response = authorizer.lambda_handler(_event(token), context=None)
    ctx = response["context"]
    assert ctx["sub"] == "u-1"
    assert ctx["tenant"] == "acme"
    assert ctx["scope"] == "read"
    # Every value must be a string.
    assert all(isinstance(v, str) for v in ctx.values())