"""Offline tests for the token-based Lambda Authorizer."""

from __future__ import annotations

import importlib.util
import os
import time
from pathlib import Path

import jwt
import pytest

# Load the authorizer module without making it a package.
_AUTHORIZER_PATH = Path(__file__).parent / "lambda_authorizer.py"
_spec = importlib.util.spec_from_file_location("lambda_authorizer", _AUTHORIZER_PATH)
assert _spec and _spec.loader
authorizer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(authorizer)


SECRET = "unit-test-secret"
METHOD_ARN = "arn:aws:execute-api:us-east-1:123:abcd/prod/GET/items"


def _mint(claims: dict | None = None, *, exp_offset: int = 60, secret: str = SECRET) -> str:
    payload = {"sub": "user-1", "tenant": "acme", "scope": "read"}
    if claims:
        payload.update(claims)
    payload["exp"] = int(time.time()) + exp_offset
    return jwt.encode(payload, secret, algorithm="HS256")


def _event(
    token: str | None,
    method_arn: str = METHOD_ARN,
    *,
    with_bearer: bool = True,
) -> dict:
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


def test_allow_valid_token(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", SECRET)
    response = authorizer.lambda_handler(_event(_mint()), context=None)

    assert response["principalId"] == "user-1"
    stmt = response["policyDocument"]["Statement"][0]
    assert stmt["Effect"] == "Allow"
    assert stmt["Action"] == "execute-api:Invoke"
    assert stmt["Resource"] == METHOD_ARN
    assert response["context"]["tenant"] == "acme"
    assert response["context"]["scope"] == "read"


def test_allow_token_without_bearer_scheme(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", SECRET)
    response = authorizer.lambda_handler(_event(_mint(), with_bearer=False), context=None)
    assert response["policyDocument"]["Statement"][0]["Effect"] == "Allow"


def test_deny_expired_token(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", SECRET)
    response = authorizer.lambda_handler(_event(_mint(exp_offset=-10)), context=None)
    assert response["policyDocument"]["Statement"][0]["Effect"] == "Deny"


def test_deny_bad_signature(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", SECRET)
    response = authorizer.lambda_handler(
        _event(_mint(secret="different-secret")), context=None
    )
    assert response["policyDocument"]["Statement"][0]["Effect"] == "Deny"


def test_deny_missing_token(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", SECRET)
    response = authorizer.lambda_handler(_event(None), context=None)
    assert response["policyDocument"]["Statement"][0]["Effect"] == "Deny"


def test_deny_when_secret_misconfigured(monkeypatch):
    # Real deploy without JWT_SECRET should still deny — it just falls
    # back to the test default, which does not match a real token's
    # signature.
    monkeypatch.delenv("JWT_SECRET", raising=False)
    real_token = _mint(secret=SECRET)
    response = authorizer.lambda_handler(_event(real_token), context=None)
    assert response["policyDocument"]["Statement"][0]["Effect"] == "Deny"
