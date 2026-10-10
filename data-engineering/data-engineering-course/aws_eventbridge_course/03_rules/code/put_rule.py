"""Idempotent EventBridge rule creation.

This is the demo script for Section 3 of the AWS EventBridge Crash
Course (lecture L15). It demonstrates:

1. Idempotent creation of a custom event bus.
2. Idempotent creation of an EventBridge rule with an event pattern.
3. Reading the rule back via ``describe_rule``.

The script is safe to re-run; the second invocation does nothing but
read. It supports ``--dry-run`` for printing intent without making
AWS calls, which is the mode we use in unit tests.

Usage:
    # Offline (no AWS calls)
    python3 put_rule.py --dry-run

    # Real AWS (uses ~/.aws/credentials)
    python3 put_rule.py

    # Custom region
    python3 put_rule.py --region us-west-2
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import boto3
from botocore.exceptions import ClientError

# ── Configuration constants ──────────────────────────────────────────────────
# In a real project these would come from environment variables or a config
# file. We hard-code them here so the demo is one self-contained file.

BUS_NAME = "orders-bus"
RULE_NAME = "orders-placed-rule"
REGION = "us-east-1"

# The event pattern is the JSON predicate that decides which events
# match the rule. We match ``source: "my.app"`` AND ``detail-type:
# "Order Placed"`` -- a realistic "domain event" pairing.
EVENT_PATTERN: dict[str, Any] = {
    "source": ["my.app"],
    "detail-type": ["Order Placed"],
}


# ── Client factory ───────────────────────────────────────────────────────────


def _events_client(region: str = REGION) -> Any:
    """Build an EventBridge boto3 client.

    moto intercepts this factory when the @mock_aws decorator is
    active, so unit tests get a fully-stubbed client.
    """
    return boto3.client("events", region_name=region)


# ── Idempotent helpers ───────────────────────────────────────────────────────


def ensure_bus(client: Any, bus_name: str) -> str:
    """Create ``bus_name`` if it doesn't exist. Returns the bus ARN.

    Idempotency strategy: probe with ``describe_event_bus``. If 404,
    create. Otherwise return a synthesised ARN. We don't try to
    enumerate AWS regions to build a real ARN -- ``moto`` ignores
    the account ID, and the ARN is only used for logging here.
    """
    try:
        client.describe_event_bus(Name=bus_name)
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceNotFoundException":
            raise
        # Create and ignore the "already exists" race-condition error.
        try:
            client.create_event_bus(Name=bus_name)
        except ClientError as ce:
            if ce.response["Error"]["Code"] != "ResourceAlreadyExistsException":
                raise
    return _bus_arn(bus_name)


def ensure_rule(
    client: Any,
    bus_name: str,
    rule_name: str,
    pattern: dict[str, Any],
    state: str = "ENABLED",
) -> str:
    """Create or update ``rule_name`` on ``bus_name``.

    ``put_rule`` is naturally idempotent -- the AWS API creates or
    updates on every call, with no separate "update" verb. We just
    call it unconditionally.

    Returns the rule ARN. Raises ``RuntimeError`` if the bus is
    missing (a config bug, not a transient error).
    """
    try:
        resp = client.put_rule(
            Name=rule_name,
            EventBusName=bus_name,
            EventPattern=json.dumps(pattern),
            State=state,
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            raise RuntimeError(
                f"event bus {bus_name!r} not found -- call ensure_bus first"
            ) from e
        raise
    return resp["RuleArn"]


def describe(client: Any, bus_name: str, rule_name: str) -> dict[str, Any]:
    """Read the rule descriptor via ``describe_rule``."""
    return client.describe_rule(Name=rule_name, EventBusName=bus_name)


def disable(client: Any, bus_name: str, rule_name: str) -> None:
    """Disable a rule (still matches events; doesn't invoke targets)."""
    client.disable_rule(Name=rule_name, EventBusName=bus_name)


def enable(client: Any, bus_name: str, rule_name: str) -> None:
    """Re-enable a previously disabled rule."""
    client.enable_rule(Name=rule_name, EventBusName=bus_name)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _bus_arn(bus_name: str) -> str:
    """Build a placeholder ARN for the bus.

    moto uses ``000000000000`` as the account ID, and we always work
    in ``us-east-1``. This ARN is for log output only; AWS APIs
    accept the bus name directly.
    """
    return f"arn:aws:events:us-east-1:000000000000:event-bus/{bus_name}"


# ── Demo orchestration ──────────────────────────────────────────────────────


def run(bus_name: str, rule_name: str, pattern: dict[str, Any],
        region: str = REGION) -> dict[str, Any]:
    """End-to-end demo: ensure bus, ensure rule, describe the rule.

    Returns the ``describe_rule`` response so callers (and tests)
    can introspect it.
    """
    client = _events_client(region=region)
    ensure_bus(client, bus_name)
    ensure_rule(client, bus_name, rule_name, pattern)
    return describe(client, bus_name, rule_name)


# ── CLI entry point ──────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would happen without making AWS calls.",
    )
    parser.add_argument(
        "--region", default=REGION,
        help=f"AWS region (default: {REGION})",
    )
    parser.add_argument(
        "--disable", action="store_true",
        help="Disable the rule after creating it.",
    )
    args = parser.parse_args(argv)

    if args.dry_run:
        print(f"[dry-run] would ensure bus:    {BUS_NAME}  (region={args.region})")
        print(f"[dry-run] would ensure rule:   {RULE_NAME}")
        print(f"[dry-run] event pattern:       {json.dumps(EVENT_PATTERN)}")
        print(f"[dry-run] state:               {'DISABLED' if args.disable else 'ENABLED'}")
        return 0

    client = _events_client(region=args.region)
    ensure_bus(client, BUS_NAME)
    state = "DISABLED" if args.disable else "ENABLED"
    rule_arn = ensure_rule(client, BUS_NAME, RULE_NAME, EVENT_PATTERN, state=state)
    desc = describe(client, BUS_NAME, RULE_NAME)

    print(f"rule arn:   {rule_arn}")
    print(f"state:      {desc['State']}")
    print(f"pattern:    {desc['EventPattern']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
