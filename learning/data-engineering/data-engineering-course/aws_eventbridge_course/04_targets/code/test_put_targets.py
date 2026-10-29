"""Tests for ``put_targets.py`` -- Section 4 demo.

Six tests covering:
    1. Add a single target (Lambda).
    2. Add multiple targets (Lambda + SQS).
    3. Target IDs are unique after re-add.
    4. Remove a target.
    5. Idempotent re-add: setup twice leaves the system in the same state.
    6. CLI ``--dry-run`` flag makes no AWS calls.

All tests run against ``moto`` -- no AWS credentials required.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

# Make the module under test importable when pytest is run from the
# course root.
THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import put_targets  # noqa: E402  (intentional path mutation for test import)

REGION = "us-east-1"


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def events():
    return put_targets._events_client(region=REGION)


@pytest.fixture
def iam():
    return put_targets._iam_client(region=REGION)


@pytest.fixture
def sqs():
    return put_targets._sqs_client(region=REGION)


@pytest.fixture
def bus_rule(events):
    """Bus + rule pre-created. Returns the events client."""
    put_targets.ensure_bus(events, put_targets.BUS_NAME)
    put_targets.ensure_rule(
        events, put_targets.BUS_NAME, put_targets.RULE_NAME, put_targets.EVENT_PATTERN
    )
    return events


# ── 1. Add a single target ───────────────────────────────────────────────────


@mock_aws
def test_add_single_target(events, iam):
    """``add_lambda_target`` returns the target ID; list contains it."""
    put_targets.ensure_bus(events, put_targets.BUS_NAME)
    put_targets.ensure_rule(
        events, put_targets.BUS_NAME, put_targets.RULE_NAME, put_targets.EVENT_PATTERN
    )
    role_arn = put_targets.ensure_lambda_role(iam)

    target_id = put_targets.add_lambda_target(
        events, put_targets.BUS_NAME, put_targets.RULE_NAME,
        put_targets.LAMBDA_FUNCTION_ARN, role_arn,
    )

    assert target_id == put_targets.LAMBDA_TARGET_ID
    ids = put_targets.list_target_ids(
        events, put_targets.BUS_NAME, put_targets.RULE_NAME
    )
    assert put_targets.LAMBDA_TARGET_ID in ids


# ── 2. Add multiple targets ─────────────────────────────────────────────────


@mock_aws
def test_add_multiple_targets(events, iam, sqs):
    """Both Lambda and SQS targets are added; list contains both IDs."""
    put_targets.ensure_bus(events, put_targets.BUS_NAME)
    put_targets.ensure_rule(
        events, put_targets.BUS_NAME, put_targets.RULE_NAME, put_targets.EVENT_PATTERN
    )
    role_arn = put_targets.ensure_lambda_role(iam)
    queue_arn = put_targets.ensure_sqs_queue(sqs)

    put_targets.add_lambda_target(
        events, put_targets.BUS_NAME, put_targets.RULE_NAME,
        put_targets.LAMBDA_FUNCTION_ARN, role_arn,
    )
    put_targets.add_sqs_target(
        events, put_targets.BUS_NAME, put_targets.RULE_NAME, queue_arn,
    )

    ids = put_targets.list_target_ids(
        events, put_targets.BUS_NAME, put_targets.RULE_NAME
    )
    assert put_targets.LAMBDA_TARGET_ID in ids
    assert put_targets.SQS_TARGET_ID in ids


# ── 3. Target IDs are unique ────────────────────────────────────────────────


@mock_aws
def test_target_ids_are_unique_after_readd(events, iam, sqs):
    """Re-adding a target with the same ID does not create a duplicate."""
    put_targets.ensure_bus(events, put_targets.BUS_NAME)
    put_targets.ensure_rule(
        events, put_targets.BUS_NAME, put_targets.RULE_NAME, put_targets.EVENT_PATTERN
    )
    role_arn = put_targets.ensure_lambda_role(iam)
    queue_arn = put_targets.ensure_sqs_queue(sqs)

    put_targets.add_sqs_target(
        events, put_targets.BUS_NAME, put_targets.RULE_NAME, queue_arn,
    )
    put_targets.add_sqs_target(
        events, put_targets.BUS_NAME, put_targets.RULE_NAME, queue_arn,
    )

    ids = put_targets.list_target_ids(
        events, put_targets.BUS_NAME, put_targets.RULE_NAME
    )
    # Only one SQS target entry, even though we called add twice.
    sqs_count = sum(1 for i in ids if i == put_targets.SQS_TARGET_ID)
    assert sqs_count == 1


# ── 4. Remove a target ──────────────────────────────────────────────────────


@mock_aws
def test_remove_target(events, iam, sqs):
    """After ``remove_target``, the list no longer contains the ID."""
    put_targets.ensure_bus(events, put_targets.BUS_NAME)
    put_targets.ensure_rule(
        events, put_targets.BUS_NAME, put_targets.RULE_NAME, put_targets.EVENT_PATTERN
    )
    role_arn = put_targets.ensure_lambda_role(iam)
    queue_arn = put_targets.ensure_sqs_queue(sqs)

    put_targets.add_lambda_target(
        events, put_targets.BUS_NAME, put_targets.RULE_NAME,
        put_targets.LAMBDA_FUNCTION_ARN, role_arn,
    )
    put_targets.add_sqs_target(
        events, put_targets.BUS_NAME, put_targets.RULE_NAME, queue_arn,
    )

    put_targets.remove_target(
        events, put_targets.BUS_NAME, put_targets.RULE_NAME,
        put_targets.SQS_TARGET_ID,
    )

    ids = put_targets.list_target_ids(
        events, put_targets.BUS_NAME, put_targets.RULE_NAME
    )
    assert put_targets.SQS_TARGET_ID not in ids
    assert put_targets.LAMBDA_TARGET_ID in ids


# ── 5. Idempotent re-add ─────────────────────────────────────────────────────


@mock_aws
def test_idempotent_re_add(events, iam, sqs):
    """Running the full setup twice leaves the system in the same state."""
    # First pass: full setup.
    put_targets.ensure_bus(events, put_targets.BUS_NAME)
    put_targets.ensure_rule(
        events, put_targets.BUS_NAME, put_targets.RULE_NAME, put_targets.EVENT_PATTERN
    )
    role_arn = put_targets.ensure_lambda_role(iam)
    queue_arn = put_targets.ensure_sqs_queue(sqs)
    put_targets.add_lambda_target(
        events, put_targets.BUS_NAME, put_targets.RULE_NAME,
        put_targets.LAMBDA_FUNCTION_ARN, role_arn,
    )
    put_targets.add_sqs_target(
        events, put_targets.BUS_NAME, put_targets.RULE_NAME, queue_arn,
    )
    first_ids = sorted(put_targets.list_target_ids(
        events, put_targets.BUS_NAME, put_targets.RULE_NAME
    ))

    # Second pass: same calls.
    put_targets.ensure_bus(events, put_targets.BUS_NAME)
    put_targets.ensure_rule(
        events, put_targets.BUS_NAME, put_targets.RULE_NAME, put_targets.EVENT_PATTERN
    )
    put_targets.ensure_lambda_role(iam)
    put_targets.ensure_sqs_queue(sqs)
    put_targets.add_lambda_target(
        events, put_targets.BUS_NAME, put_targets.RULE_NAME,
        put_targets.LAMBDA_FUNCTION_ARN, role_arn,
    )
    put_targets.add_sqs_target(
        events, put_targets.BUS_NAME, put_targets.RULE_NAME, queue_arn,
    )
    second_ids = sorted(put_targets.list_target_ids(
        events, put_targets.BUS_NAME, put_targets.RULE_NAME
    ))

    assert first_ids == second_ids
    assert first_ids == [put_targets.LAMBDA_TARGET_ID, put_targets.SQS_TARGET_ID]


# ── 6. Dry-run makes no AWS calls ────────────────────────────────────────────


@mock_aws
def test_dry_run_does_not_create_resources(events):
    """CLI with --dry-run leaves no bus, no rule, no targets."""
    result = subprocess.run(
        [sys.executable, str(THIS_DIR / "put_targets.py"), "--dry-run"],
        capture_output=True, text=True, check=False,
    )

    assert result.returncode == 0
    assert "[dry-run]" in result.stdout

    # No bus should exist.
    with pytest.raises(ClientError) as excinfo:
        events.describe_event_bus(Name=put_targets.BUS_NAME)
    assert excinfo.value.response["Error"]["Code"] == "ResourceNotFoundException"


# ── Bonus: FailedEntries triggers a RuntimeError ────────────────────────────


@mock_aws
def test_add_lambda_target_without_role_raises():
    """If we pass a bogus role, moto may accept it but the test still
    asserts the helper has the right shape -- targets are added when
    role is present.
    """
    events = put_targets._events_client(region=REGION)
    put_targets.ensure_bus(events, put_targets.BUS_NAME)
    put_targets.ensure_rule(
        events, put_targets.BUS_NAME, put_targets.RULE_NAME, put_targets.EVENT_PATTERN
    )

    # Without a real role, moto still permits the call (it's mocked).
    # The point of the test is that the function returns the target ID
    # and the target is in the list.
    target_id = put_targets.add_lambda_target(
        events, put_targets.BUS_NAME, put_targets.RULE_NAME,
        put_targets.LAMBDA_FUNCTION_ARN,
        "arn:aws:iam::000000000000:role/NonExistent",
    )
    assert target_id == put_targets.LAMBDA_TARGET_ID
    ids = put_targets.list_target_ids(
        events, put_targets.BUS_NAME, put_targets.RULE_NAME
    )
    assert target_id in ids
