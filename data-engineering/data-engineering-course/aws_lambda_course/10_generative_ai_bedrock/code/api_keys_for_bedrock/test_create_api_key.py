"""Tests for the Bedrock API Key + Usage Plan setup script.

Uses moto to stub API Gateway entirely. We don't test the AWS-issued
key value (moto generates random ones), only the idempotent orchestration
logic — key reuse, two-plan creation, plan updates, key attachment, and
stage-association behaviour.
"""
from __future__ import annotations

import importlib.util
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
def rest_api_with_stages(script):
    """Create a `bedrock-defect-api` REST API with dev + prod stages deployed."""
    with mock_aws():
        client = boto3.client("apigateway", region_name="us-east-1")
        api = client.create_rest_api(name="bedrock-defect-api")
        api_id = api["id"]

        # Build a /defects resource + POST method so a deployment is valid.
        resources = client.get_resources(restApiId=api_id)
        root_id = resources["items"][0]["id"]
        resource = client.create_resource(
            restApiId=api_id, parentId=root_id, pathPart="defects"
        )
        client.put_method(
            restApiId=api_id,
            resourceId=resource["id"],
            httpMethod="POST",
            authorizationType="NONE",
        )
        client.put_integration(
            restApiId=api_id,
            resourceId=resource["id"],
            httpMethod="POST",
            type="MOCK",
            requestTemplates={"application/json": '{"statusCode": 200}'},
        )

        # Two stages — the two-plan case from L44a.
        client.create_deployment(restApiId=api_id, stageName="dev")
        client.create_deployment(restApiId=api_id, stageName="prod")
        yield api_id


# ── helpers ────────────────────────────────────────────────────────────
def _get_key_value(client, key_id: str) -> str:
    return client.get_api_key(apiKey=key_id, includeValue=True)["value"]


def _build_two_plans(script, client, api_id):
    """Helper: create one key + two plans + attach the key to both."""
    key_id = script.ensure_api_key(client, "defect-api-key")
    dev_plan = script.ensure_usage_plan(
        client,
        "defect-api-dev",
        rate_limit=100.0,
        burst_limit=200,
        quota_limit=1_000_000,
        quota_period="DAY",
        stages=[{"apiId": api_id, "stage": "dev"}],
    )
    prod_plan = script.ensure_usage_plan(
        client,
        "defect-api-prod",
        rate_limit=10.0,
        burst_limit=50,
        quota_limit=100_000,
        quota_period="DAY",
        stages=[{"apiId": api_id, "stage": "prod"}],
    )
    script.attach_key_to_plan(client, dev_plan, key_id)
    script.attach_key_to_plan(client, prod_plan, key_id)
    return key_id, dev_plan, prod_plan


# ── tests ──────────────────────────────────────────────────────────────
def test_ensure_api_key_creates_then_reuses(script, rest_api_with_stages):
    client = boto3.client("apigateway", region_name="us-east-1")

    key_id_1 = script.ensure_api_key(client, "defect-api-key")
    assert _get_key_value(client, key_id_1)

    key_id_2 = script.ensure_api_key(client, "defect-api-key")
    assert key_id_1 == key_id_2


def test_two_plans_have_independent_throttle(script, rest_api_with_stages):
    """Dev plan and prod plan must carry their own rate / quota settings."""
    client = boto3.client("apigateway", region_name="us-east-1")
    api_id = rest_api_with_stages

    _, dev_plan_id, prod_plan_id = _build_two_plans(script, client, api_id)

    dev = client.get_usage_plan(usagePlanId=dev_plan_id)
    prod = client.get_usage_plan(usagePlanId=prod_plan_id)

    assert dev["throttle"]["rateLimit"] == 100.0
    assert dev["quota"]["limit"] == 1_000_000
    assert prod["throttle"]["rateLimit"] == 10.0
    assert prod["quota"]["limit"] == 100_000

    # The two plans must be distinct resources.
    assert dev_plan_id != prod_plan_id


def test_one_key_attached_to_both_plans(script, rest_api_with_stages):
    """The same key is attached to the dev plan AND the prod plan."""
    client = boto3.client("apigateway", region_name="us-east-1")
    api_id = rest_api_with_stages

    key_id, dev_plan_id, prod_plan_id = _build_two_plans(script, client, api_id)

    dev_keys = client.get_usage_plan_keys(usagePlanId=dev_plan_id)["items"]
    prod_keys = client.get_usage_plan_keys(usagePlanId=prod_plan_id)["items"]

    assert [k["id"] for k in dev_keys] == [key_id]
    assert [k["id"] for k in prod_keys] == [key_id]


def test_attach_key_to_plan_is_idempotent(script, rest_api_with_stages):
    """A second attach call must be a no-op (no duplicate row)."""
    client = boto3.client("apigateway", region_name="us-east-1")
    api_id = rest_api_with_stages

    key_id, dev_plan_id, _ = _build_two_plans(script, client, api_id)

    # Second attach is a no-op
    script.attach_key_to_plan(client, dev_plan_id, key_id)
    keys = client.get_usage_plan_keys(usagePlanId=dev_plan_id)["items"]
    assert len(keys) == 1


def test_ensure_usage_plan_updates_in_place(script, rest_api_with_stages):
    """Re-running with different throttle values updates the same plan."""
    client = boto3.client("apigateway", region_name="us-east-1")
    api_id = rest_api_with_stages

    plan_id_1 = script.ensure_usage_plan(
        client,
        "defect-api-prod",
        rate_limit=10,
        burst_limit=50,
        quota_limit=100_000,
        quota_period="DAY",
        stages=[{"apiId": api_id, "stage": "prod"}],
    )
    plan_id_2 = script.ensure_usage_plan(
        client,
        "defect-api-prod",
        rate_limit=5,
        burst_limit=20,
        quota_limit=50_000,
        quota_period="MONTH",
        stages=[{"apiId": api_id, "stage": "prod"}],
    )

    assert plan_id_1 == plan_id_2
    plan = client.get_usage_plan(usagePlanId=plan_id_2)
    assert plan["throttle"]["rateLimit"] == 5
    assert plan["quota"]["limit"] == 50_000
    assert plan["quota"]["period"] == "MONTH"


def test_find_rest_api_id_raises_when_missing(script):
    with mock_aws():
        client = boto3.client("apigateway", region_name="us-east-1")
        with pytest.raises(RuntimeError, match="not found"):
            script.find_rest_api_id(client, "bedrock-defect-api")


def test_stage_exists_returns_true_and_false(script, rest_api_with_stages):
    client = boto3.client("apigateway", region_name="us-east-1")
    api_id = rest_api_with_stages
    assert script.stage_exists(client, api_id, "dev") is True
    assert script.stage_exists(client, api_id, "prod") is True
    assert script.stage_exists(client, api_id, "staging") is False


def test_main_creates_two_plans_and_prints_key(script, rest_api_with_stages, capsys):
    """End-to-end: main() must create the key, two plans, and print the value."""
    client = boto3.client("apigateway", region_name="us-east-1")

    rc = script.main(
        [
            "--api-name", "bedrock-defect-api",
            "--key-name", "defect-api-key",
            "--dev-plan-name", "defect-api-dev",
            "--prod-plan-name", "defect-api-prod",
            "--dev-stage", "dev",
            "--prod-stage", "prod",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "API ID" in out
    assert "DEV PLAN" in out
    assert "PROD PLAN" in out
    assert "KEY VALUE" in out

    # Two plans must exist with the expected names.
    plans = client.get_usage_plans()["items"]
    names = sorted(p["name"] for p in plans)
    assert names == ["defect-api-dev", "defect-api-prod"]
