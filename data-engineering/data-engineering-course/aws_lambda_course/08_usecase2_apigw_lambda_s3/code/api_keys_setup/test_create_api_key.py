"""Tests for create_api_key.

Uses moto to stub API Gateway entirely. We don't test the AWS-issued
key value (moto generates random ones), only the idempotent orchestration
logic.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import boto3
import pytest
from moto import mock_aws

HERE = Path(__file__).resolve().parent
SCRIPT_PATH = HERE / "create_api_key.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("create_api_key", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def script(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    if "create_api_key" in sys.modules:
        del sys.modules["create_api_key"]
    return _load_script()


@pytest.fixture
def rest_api(script):
    """Create a REST API, a fake resource + method, and a 'prod' stage
    in moto-stubbed API Gateway."""
    with mock_aws():
        client = boto3.client("apigateway", region_name="us-east-1")
        api = client.create_rest_api(name="ServerlessCRUD")
        api_id = api["id"]

        # Create a resource + method so a deployment is valid in moto
        resources = client.get_resources(restApiId=api_id)
        root_id = resources["items"][0]["id"]
        resource = client.create_resource(
            restApiId=api_id, parentId=root_id, pathPart="{proxy+}"
        )
        # Put a no-op GET method + a MOCK integration so a deployment
        # is valid in moto
        client.put_method(
            restApiId=api_id,
            resourceId=resource["id"],
            httpMethod="GET",
            authorizationType="NONE",
        )
        client.put_integration(
            restApiId=api_id,
            resourceId=resource["id"],
            httpMethod="GET",
            type="MOCK",
            requestTemplates={"application/json": '{"statusCode": 200}'},
        )
        client.create_deployment(restApiId=api_id, stageName="prod")
        yield api_id


# ── helpers ────────────────────────────────────────────────────────────
def _get_key_value(client, key_id: str) -> str:
    return client.get_api_key(apiKey=key_id, includeValue=True)["value"]


# ── tests ──────────────────────────────────────────────────────────────
def test_ensure_api_key_creates_then_reuses(script, rest_api):
    client = boto3.client("apigateway", region_name="us-east-1")
    api_id = rest_api

    # First call → creates
    key_id_1 = script.ensure_api_key(client, "k1")
    assert _get_key_value(client, key_id_1)

    # Second call → reuses the same id
    key_id_2 = script.ensure_api_key(client, "k1")
    assert key_id_1 == key_id_2


def test_ensure_usage_plan_creates_then_updates(script, rest_api):
    client = boto3.client("apigateway", region_name="us-east-1")
    api_id = rest_api

    plan_id_1 = script.ensure_usage_plan(
        client,
        "p1",
        rate_limit=10.0,
        burst_limit=20,
        quota_limit=1000,
        quota_period="DAY",
        stages=[{"apiId": api_id, "stage": "prod"}],
    )
    plan = client.get_usage_plan(usagePlanId=plan_id_1)
    assert plan["throttle"]["rateLimit"] == 10.0

    # Update
    plan_id_2 = script.ensure_usage_plan(
        client,
        "p1",
        rate_limit=200.0,
        burst_limit=400,
        quota_limit=1_000_000,
        quota_period="MONTH",
        stages=[{"apiId": api_id, "stage": "prod"}],
    )
    assert plan_id_1 == plan_id_2
    plan = client.get_usage_plan(usagePlanId=plan_id_2)
    assert plan["throttle"]["rateLimit"] == 200.0
    assert plan["quota"]["limit"] == 1_000_000
    assert plan["quota"]["period"] == "MONTH"


def test_attach_key_to_plan_is_idempotent(script, rest_api):
    client = boto3.client("apigateway", region_name="us-east-1")
    api_id = rest_api

    key_id = script.ensure_api_key(client, "k1")
    plan_id = script.ensure_usage_plan(
        client,
        "p1",
        rate_limit=10.0,
        burst_limit=20,
        quota_limit=1000,
        quota_period="DAY",
        stages=[{"apiId": api_id, "stage": "prod"}],
    )

    script.attach_key_to_plan(client, plan_id, key_id)
    keys = client.get_usage_plan_keys(usagePlanId=plan_id)["items"]
    assert len(keys) == 1

    # Second attach is a no-op
    script.attach_key_to_plan(client, plan_id, key_id)
    keys = client.get_usage_plan_keys(usagePlanId=plan_id)["items"]
    assert len(keys) == 1


def test_find_rest_api_id_raises_when_missing(script):
    with mock_aws():
        client = boto3.client("apigateway", region_name="us-east-1")
        with pytest.raises(RuntimeError, match="not found"):
            script.find_rest_api_id(client, "nope")


def test_find_rest_api_id_finds_it(script, rest_api):
    client = boto3.client("apigateway", region_name="us-east-1")
    assert script.find_rest_api_id(client, "ServerlessCRUD") == rest_api
