"""Offline tests for create_user_pool.py — run with `pytest`.

All tests are wrapped in ``mock_aws`` so no real AWS calls are made.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import boto3
import pytest
from moto import mock_aws

# Load the module under test without going through a package import —
# matches the convention used in ``../aws_lambda_course/09_api_security_*/``.
import sys as _sys

_SPEC = importlib.util.spec_from_file_location(
    "create_user_pool", Path(__file__).parent / "create_user_pool.py"
)
assert _SPEC and _SPEC.loader
mod = importlib.util.module_from_spec(_SPEC)
_sys.modules["create_user_pool"] = mod
_SPEC.loader.exec_module(mod)


@pytest.fixture
def aws_env(monkeypatch):
    """Wrap each test in ``mock_aws`` and yield a real cognito-idp client."""
    monkeypatch.setenv("USER_POOL_NAME", "test-pool")
    monkeypatch.setenv("APP_CLIENT_NAME", "test-pool-client")
    monkeypatch.setenv("TEST_USERNAME", "alice@example.com")
    monkeypatch.setenv("TEST_PASSWORD", "TempPass!2026")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    with mock_aws():
        yield boto3.client("cognito-idp", region_name="us-east-1")


def _pool_id(cognito, name: str = "test-pool") -> str:
    pools = cognito.list_user_pools(MaxResults=10)["UserPools"]
    return next(p["Id"] for p in pools if p["Name"] == name)


def test_creates_pool(aws_env):
    """bootstrap() creates a User Pool with the expected name."""
    stack = mod.bootstrap()
    assert stack.user_pool_id

    pools = aws_env.list_user_pools(MaxResults=10)["UserPools"]
    matching = [p for p in pools if p["Name"] == "test-pool"]
    assert len(matching) == 1
    assert matching[0]["Id"] == stack.user_pool_id


def test_idempotent(aws_env):
    """Calling bootstrap() twice yields the same user_pool_id + app_client_id."""
    s1 = mod.bootstrap()
    s2 = mod.bootstrap()
    assert s1.user_pool_id == s2.user_pool_id
    assert s1.app_client_id == s2.app_client_id

    pools = aws_env.list_user_pools(MaxResults=10)["UserPools"]
    assert sum(1 for p in pools if p["Name"] == "test-pool") == 1

    clients = aws_env.list_user_pool_clients(
        UserPoolId=s1.user_pool_id, MaxResults=10
    )["UserPoolClients"]
    assert sum(1 for c in clients if c["ClientName"] == "test-pool-client") == 1


def test_creates_app_client(aws_env):
    """bootstrap() creates an App Client with the right name and no secret."""
    stack = mod.bootstrap()
    desc = aws_env.describe_user_pool_client(
        UserPoolId=stack.user_pool_id, ClientId=stack.app_client_id
    )["UserPoolClient"]
    assert desc["ClientName"] == "test-pool-client"
    # No client secret: ``ClientSecret`` is either absent or ``None``.
    # Real AWS returns the field with value ``None``; moto may omit it
    # entirely. Either way: there must be no actual secret value.
    secret = desc.get("ClientSecret")
    assert secret in (None, "")


def test_creates_user(aws_env):
    """bootstrap() creates the test user and marks email_verified=True."""
    stack = mod.bootstrap()
    user = aws_env.admin_get_user(
        UserPoolId=stack.user_pool_id, Username="alice@example.com"
    )
    attrs = {a["Name"]: a["Value"] for a in user["UserAttributes"]}
    assert attrs["email"] == "alice@example.com"
    assert attrs["email_verified"] == "true"


def test_password_set(aws_env):
    """The test user can sign in with the documented password."""
    stack = mod.bootstrap()
    # ``initiate_auth(USER_PASSWORD_AUTH)`` should succeed without
    # forcing a password change (because we set a permanent password).
    auth = aws_env.initiate_auth(
        AuthFlow="USER_PASSWORD_AUTH",
        ClientId=stack.app_client_id,
        AuthParameters={
            "USERNAME": "alice@example.com",
            "PASSWORD": "TempPass!2026",
        },
    )
    assert "AuthenticationResult" in auth
    result = auth["AuthenticationResult"]
    assert result["IdToken"]
    assert result["AccessToken"]
    assert result.get("ExpiresIn", 0) > 0


def test_dry_run(aws_env, monkeypatch, capsys):
    """``--dry-run`` prints the plan and exits without touching AWS."""
    # If ``--dry-run`` accidentally created resources, this assertion
    # would fail because the list would not be empty.
    rc = mod.main(["--dry-run"])
    assert rc == 0

    captured = capsys.readouterr()
    assert "[DRY-RUN]" in captured.out
    assert "create_user_pool" in captured.out

    pools = aws_env.list_user_pools(MaxResults=10)["UserPools"]
    assert pools == []  # no resource was created