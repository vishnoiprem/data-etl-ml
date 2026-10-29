"""Tests for the EventBridge custom-bus setup script.

Uses `moto.mock_aws` to stub the EventBridge APIs entirely. We don't
exercise the AWS-issued ARN format (moto generates predictable ones),
only the orchestration logic — create, idempotent re-create, attach
resource policy, list, dry-run, delete.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import boto3
import pytest
from moto import mock_aws

HERE = Path(__file__).resolve().parent
SCRIPT_PATH = HERE / "create_event_bus.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("create_event_bus", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def script(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    if "create_event_bus" in sys.modules:
        del sys.modules["create_event_bus"]
    return _load_script()


# ── tests ──────────────────────────────────────────────────────────────
def test_creates_new_bus(script):
    """First call creates the bus and returns the new ARN."""
    with mock_aws():
        client = boto3.client("events", region_name="us-east-1")
        arn = script.ensure_event_bus(client, "acme-orders")
        assert arn.endswith(":event-bus/acme-orders")
        assert arn.startswith("arn:aws:events:us-east-1:")


def test_recreate_is_idempotent(script):
    """A second call must return the same ARN and must not raise."""
    with mock_aws():
        client = boto3.client("events", region_name="us-east-1")
        arn_1 = script.ensure_event_bus(client, "acme-orders")
        arn_2 = script.ensure_event_bus(client, "acme-orders")
        assert arn_1 == arn_2

        # And the bus list still shows exactly one.
        names = [b["Name"] for b in script.list_buses(client)]
        assert names.count("acme-orders") == 1


def test_apply_resource_policy(script):
    """The resource policy must be attached to the bus with the
    expected principal and action."""
    with mock_aws():
        client = boto3.client("events", region_name="us-east-1")
        script.ensure_event_bus(client, "acme-orders")
        script.apply_resource_policy(
            client, "acme-orders", source_account="444455556666"
        )

        # `describe_event_bus` returns the policy in `Policy`.
        desc = client.describe_event_bus(Name="acme-orders")
        policy = json.loads(desc["Policy"])
        stmt = policy["Statement"][0]
        assert stmt["Effect"] == "Allow"
        assert stmt["Action"] == "events:PutEvents"
        assert stmt["Principal"]["AWS"] == "arn:aws:iam::444455556666:root"
        assert stmt["Resource"].endswith(":event-bus/acme-orders")


def test_list_buses_includes_ours(script):
    """After creation, our custom bus must appear in `list_buses`."""
    with mock_aws():
        client = boto3.client("events", region_name="us-east-1")
        script.ensure_event_bus(client, "acme-orders")
        script.ensure_event_bus(client, "acme-billing")

        names = sorted(b["Name"] for b in script.list_buses(client))
        # The default bus is always present + our two custom buses.
        assert names == ["acme-billing", "acme-orders", "default"]


def test_dry_run_makes_no_calls(script):
    """`--dry-run` must short-circuit before any boto3 client is built.

    We patch `boto3.client` with a MagicMock so we can count how many
    times it is called (and inspect the calls if needed)."""
    with patch("create_event_bus.boto3.client") as mock_client:
        rc = script.main([
            "--dry-run",
            "--name", "acme-orders",
            "--source-account", "444455556666",
        ])
        assert rc == 0
        # No `boto3.client("events", ...)` was ever instantiated.
        mock_client.assert_not_called()


def test_dry_run_prints_intent(script, capsys):
    """Dry-run should print what *would* happen so a human reviewer
    can confirm the intent."""
    with patch("create_event_bus.boto3.client") as mock_client:
        rc = script.main([
            "--dry-run",
            "--name", "acme-orders",
            "--source-account", "444455556666",
        ])
        assert rc == 0
        out = capsys.readouterr().out
        assert "[dry-run]" in out
        assert "acme-orders" in out
        assert "444455556666" in out
        mock_client.assert_not_called()


def test_delete_bus_removes_from_list(script):
    """`delete_event_bus` must remove the bus; subsequent list excludes it."""
    with mock_aws():
        client = boto3.client("events", region_name="us-east-1")
        script.ensure_event_bus(client, "acme-orders")
        script.delete_event_bus(client, "acme-orders")
        names = [b["Name"] for b in script.list_buses(client)]
        assert "acme-orders" not in names
        # The default bus is still there.
        assert "default" in names


def test_main_creates_bus_and_prints_summary(script, capsys):
    """End-to-end: `main()` (without --dry-run) creates the bus,
    attaches the policy, and prints a summary including the ARN."""
    with mock_aws():
        rc = script.main([
            "--name", "acme-orders",
            "--source-account", "444455556666",
            "--region", "us-east-1",
        ])
        assert rc == 0
        out = capsys.readouterr().out
        assert "BUS ARN" in out
        assert "acme-orders" in out
        assert "ALLOWED ACCT" in out
        assert "default" in out  # the default bus is in the list

        # And the bus really was created.
        client = boto3.client("events", region_name="us-east-1")
        names = [b["Name"] for b in script.list_buses(client)]
        assert "acme-orders" in names


def test_ensure_bus_raises_unrelated_client_error(script):
    """A `ClientError` that is *not* `ResourceAlreadyExistsException`
    must propagate; we only swallow the duplicate-bus case."""
    fake_exc = Exception("boom")
    with mock_aws():
        client = MagicMock()
        client.create_event_bus.side_effect = fake_exc
        with pytest.raises(Exception, match="boom"):
            script.ensure_event_bus(client, "acme-orders")
