"""Offline tests for identity_pool_demo.py — run with `pytest`.

All tests are wrapped in ``mock_aws`` so no real AWS calls are made.

.. note::

    **What we can and cannot test with moto.** ``moto`` 5.x implements
    ``cognito-identity:CreateIdentityPool``, ``DescribeIdentityPool``
    and ``ListIdentityPools``. It does **not** implement
    ``SetIdentityPoolRoles`` (raises ``NotImplementedError``) or the
    federated ``GetCredentialsForIdentity`` / ``GetId`` flows. These
    tests therefore cover pool creation, idempotency, provider
    configuration, and IAM role creation. The role <-> pool
    attachment is documented in ``identity_pool_demo._attach_roles_to_pool``
    and is verified by code review in production.
"""

from __future__ import annotations

import importlib.util
import json
import sys as _sys
from pathlib import Path

import boto3
import pytest
from moto import mock_aws

# Load the module under test
_SPEC = importlib.util.spec_from_file_location(
    "identity_pool_demo", Path(__file__).parent / "identity_pool_demo.py"
)
assert _SPEC and _SPEC.loader
mod = importlib.util.module_from_spec(_SPEC)
_sys.modules["identity_pool_demo"] = mod
_SPEC.loader.exec_module(mod)


# A reasonable fake "user pool" + "app client" id shape.
FAKE_USER_POOL_ID = "us-east-1_FakePoolId"
FAKE_APP_CLIENT_ID = "7a1b2c3d4e5f6g7h8i9j"


@pytest.fixture
def aws_env(monkeypatch):
    """Wrap each test in ``mock_aws`` and yield both boto3 clients."""
    monkeypatch.setenv("USER_POOL_ID", FAKE_USER_POOL_ID)
    monkeypatch.setenv("APP_CLIENT_ID", FAKE_APP_CLIENT_ID)
    monkeypatch.setenv("IDENTITY_POOL_NAME", "test-idpool")
    monkeypatch.setenv("AUTH_ROLE_NAME", "test-idpool-auth-role")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    with mock_aws():
        identity = boto3.client("cognito-identity", region_name="us-east-1")
        iam = boto3.client("iam")
        yield {"identity": identity, "iam": iam}


def _provider_name() -> str:
    return f"cognito-idp.us-east-1.amazonaws.com/{FAKE_USER_POOL_ID}"


def test_creates_identity_pool(aws_env):
    """bootstrap() creates an Identity Pool with the expected name."""
    stack = mod.bootstrap(
        identity=aws_env["identity"], iam=aws_env["iam"],
    )
    assert stack.identity_pool_id

    pools = aws_env["identity"].list_identity_pools(MaxResults=10)["IdentityPools"]
    names = [p["IdentityPoolName"] for p in pools]
    assert "test-idpool" in names


def test_sets_cognito_user_pool_as_provider(aws_env):
    """The Identity Pool has the User Pool listed as a Cognito provider."""
    stack = mod.bootstrap(
        identity=aws_env["identity"], iam=aws_env["iam"],
    )
    desc = aws_env["identity"].describe_identity_pool(
        IdentityPoolId=stack.identity_pool_id
    )
    providers = desc.get("CognitoIdentityProviders", [])
    assert any(
        p["ProviderName"] == _provider_name() and p["ClientId"] == FAKE_APP_CLIENT_ID
        for p in providers
    ), f"User pool not in providers: {providers}"


def test_role_has_correct_trust_policy(aws_env):
    """The auth role allows cognito-identity.amazonaws.com to assume it."""
    stack = mod.bootstrap(
        identity=aws_env["identity"], iam=aws_env["iam"],
    )
    role = aws_env["iam"].get_role(RoleName="test-idpool-auth-role")["Role"]
    trust = role["AssumeRolePolicyDocument"]
    # Decode the policy (it's a string here)
    policy = trust if isinstance(trust, dict) else json.loads(trust)
    principal = (
        policy["Statement"][0]["Principal"]["Federated"]
    )
    assert principal == "cognito-identity.amazonaws.com"
    assert "sts:AssumeRoleWithWebIdentity" in policy["Statement"][0]["Action"]
    # The auth role ARN should be on the returned stack
    assert stack.auth_role_arn.endswith(":role/test-idpool-auth-role")


def test_dry_run(aws_env, monkeypatch, capsys):
    """``--dry-run`` prints the plan and exits without touching AWS."""
    rc = mod.main(["--dry-run"])
    assert rc == 0

    captured = capsys.readouterr()
    assert "[DRY-RUN]" in captured.out
    assert "create_identity_pool" in captured.out
    assert "create_role" in captured.out

    # No resources were created
    pools = aws_env["identity"].list_identity_pools(MaxResults=10)["IdentityPools"]
    assert pools == []


def test_idempotent(aws_env):
    """Calling bootstrap() twice yields the same identity_pool_id and role ARN."""
    s1 = mod.bootstrap(identity=aws_env["identity"], iam=aws_env["iam"])
    s2 = mod.bootstrap(identity=aws_env["identity"], iam=aws_env["iam"])
    assert s1.identity_pool_id == s2.identity_pool_id
    assert s1.auth_role_arn == s2.auth_role_arn

    # Only one pool with our name
    pools = aws_env["identity"].list_identity_pools(MaxResults=10)["IdentityPools"]
    assert sum(1 for p in pools if p["IdentityPoolName"] == "test-idpool") == 1
