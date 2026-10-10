"""Tests for ``put_rule.py`` -- Section 3 demo.

Six tests covering:
    1. Bus creation + idempotent re-create.
    2. Rule creation returns ARN.
    3. Event pattern matches the expected source/detail-type pair.
    4. Event pattern does NOT match a different source.
    5. Rule can be disabled and re-enabled.
    6. CLI ``--dry-run`` flag makes no AWS calls.

All tests run against ``moto`` -- no AWS credentials required.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

# Make the module under test importable when pytest is run from the
# course root (e.g. ``python3 -m pytest 03_rules/code/test_put_rule.py``).
THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import put_rule  # noqa: E402  (intentional path mutation for test import)


REGION = "us-east-1"


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def client():
    """An EventBridge client with moto active."""
    return put_rule._events_client(region=REGION)


@pytest.fixture
def bus_rule(client):
    """Pre-create the bus + rule pair. Returned as a tuple."""
    put_rule.ensure_bus(client, put_rule.BUS_NAME)
    put_rule.ensure_rule(client, put_rule.BUS_NAME, put_rule.RULE_NAME, put_rule.EVENT_PATTERN)
    return client, put_rule.BUS_NAME, put_rule.RULE_NAME


# ── 1. Bus creation + idempotent re-create ───────────────────────────────────


@mock_aws
def test_ensure_bus_creates_then_idempotent():
    """First call creates the bus; second call is a no-op (no error)."""
    client = put_rule._events_client(region=REGION)
    put_rule.ensure_bus(client, "test-bus-1")

    # Bus exists now.
    desc = client.describe_event_bus(Name="test-bus-1")
    assert desc["Name"] == "test-bus-1"

    # Re-run -- should not raise (idempotent).
    put_rule.ensure_bus(client, "test-bus-1")
    desc2 = client.describe_event_bus(Name="test-bus-1")
    assert desc2["Name"] == "test-bus-1"


# ── 2. Rule creation returns the ARN ────────────────────────────────────────


@mock_aws
def test_ensure_rule_returns_arn_and_state_is_enabled():
    """The rule exists after ensure_rule; state is ENABLED."""
    client = put_rule._events_client(region=REGION)
    put_rule.ensure_bus(client, put_rule.BUS_NAME)
    arn = put_rule.ensure_rule(
        client, put_rule.BUS_NAME, put_rule.RULE_NAME, put_rule.EVENT_PATTERN
    )

    assert arn.endswith(put_rule.RULE_NAME)
    assert ":rule/" in arn

    desc = client.describe_rule(Name=put_rule.RULE_NAME, EventBusName=put_rule.BUS_NAME)
    assert desc["State"] == "ENABLED"
    assert json.loads(desc["EventPattern"]) == put_rule.EVENT_PATTERN


# ── 3. Event pattern matches ────────────────────────────────────────────────


def test_event_pattern_matches_expected_source_and_detail_type():
    """The pattern matches events with source=my.app + detail-type=Order Placed."""
    pattern = put_rule.EVENT_PATTERN
    event = {
        "source": "my.app",
        "detail-type": "Order Placed",
        "detail": {"orderId": "O-1001"},
    }
    # AND over keys, OR inside arrays -- pattern semantics.
    assert event["source"] in pattern["source"]
    assert event["detail-type"] in pattern["detail-type"]


# ── 4. Event pattern does NOT match a different source ──────────────────────


def test_event_pattern_does_not_match_different_source():
    """An event with source=other.app does not satisfy the pattern."""
    pattern = put_rule.EVENT_PATTERN
    other_event = {"source": "other.app", "detail-type": "Order Placed"}
    assert other_event["source"] not in pattern["source"]


# ── 5. Rule can be disabled and re-enabled ───────────────────────────────────


@mock_aws
def test_disable_rule_changes_state_to_disabled():
    """After disable_rule, describe_rule returns State=DISABLED."""
    client = put_rule._events_client(region=REGION)
    put_rule.ensure_bus(client, put_rule.BUS_NAME)
    put_rule.ensure_rule(client, put_rule.BUS_NAME, put_rule.RULE_NAME, put_rule.EVENT_PATTERN)

    put_rule.disable(client, put_rule.BUS_NAME, put_rule.RULE_NAME)

    desc = client.describe_rule(Name=put_rule.RULE_NAME, EventBusName=put_rule.BUS_NAME)
    assert desc["State"] == "DISABLED"

    # Re-enable and check.
    put_rule.enable(client, put_rule.BUS_NAME, put_rule.RULE_NAME)
    desc2 = client.describe_rule(Name=put_rule.RULE_NAME, EventBusName=put_rule.BUS_NAME)
    assert desc2["State"] == "ENABLED"


# ── 6. Dry-run makes no AWS calls ────────────────────────────────────────────


@mock_aws
def test_dry_run_does_not_create_resources():
    """Running the script with --dry-run leaves the bus count at zero."""
    # moto is active; we explicitly check that no bus was created
    # by listing all buses.
    client = put_rule._events_client(region=REGION)

    # Run the script as a subprocess so we hit the actual CLI entry point.
    result = subprocess.run(
        [sys.executable, str(THIS_DIR / "put_rule.py"), "--dry-run"],
        capture_output=True, text=True, check=False,
    )

    assert result.returncode == 0
    assert "[dry-run]" in result.stdout

    # No bus should have been created -- describe_event_bus should 404.
    with pytest.raises(ClientError) as excinfo:
        client.describe_event_bus(Name=put_rule.BUS_NAME)
    assert excinfo.value.response["Error"]["Code"] == "ResourceNotFoundException"


# ── Bonus: ensure_rule fails loudly when the bus is missing ─────────────────


@mock_aws
def test_ensure_rule_raises_when_bus_missing():
    """ensure_rule raises RuntimeError if the bus doesn't exist."""
    client = put_rule._events_client(region=REGION)

    with pytest.raises(RuntimeError, match="not found"):
        put_rule.ensure_rule(
            client, "nonexistent-bus", "any-rule", put_rule.EVENT_PATTERN
        )
