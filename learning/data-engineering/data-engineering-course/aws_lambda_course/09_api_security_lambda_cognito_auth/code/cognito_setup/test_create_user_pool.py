"""Offline tests for the Cognito User Pool + App Client bootstrap."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import boto3
import pytest
from moto import mock_aws

_SPEC = importlib.util.spec_from_file_location(
    "create_user_pool", Path(__file__).parent / "create_user_pool.py"
)
assert _SPEC and _SPEC.loader
mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(mod)


@pytest.fixture
def aws_env(monkeypatch):
    with mock_aws():
        yield boto3.client("cognito-idp", region_name="us-east-1")


def test_creates_pool_and_client(aws_env, monkeypatch):
    monkeypatch.setenv("USER_POOL_NAME", "test-pool")
    monkeypatch.setenv("AWS_REGION", "us-east-1")

    rc = mod.main()
    assert rc == 0

    pools = aws_env.list_user_pools(MaxResults=10)["UserPools"]
    assert any(p["Name"] == "test-pool" for p in pools)

    pool_id = next(p["Id"] for p in pools if p["Name"] == "test-pool")
    clients = aws_env.list_user_pool_clients(UserPoolId=pool_id, MaxResults=10)[
        "UserPoolClients"
    ]
    assert any(c["ClientName"] == "test-pool-client" for c in clients)

    servers = aws_env.list_resource_servers(UserPoolId=pool_id, MaxResults=10)[
        "ResourceServers"
    ]
    assert any(s["Identifier"] == "test-pool" for s in servers)


def test_idempotent(aws_env, monkeypatch):
    monkeypatch.setenv("USER_POOL_NAME", "test-pool")
    mod.main()
    mod.main()  # second call must not raise

    pools = aws_env.list_user_pools(MaxResults=10)["UserPools"]
    matching = [p for p in pools if p["Name"] == "test-pool"]
    assert len(matching) == 1
