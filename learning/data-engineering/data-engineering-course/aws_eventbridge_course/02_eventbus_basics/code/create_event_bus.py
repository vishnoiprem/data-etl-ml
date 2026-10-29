"""Idempotently create a custom EventBridge bus, attach a resource
policy, and list every bus in the (account, region).

This is the working demo for the L09 lecture in section 2. The script
is **idempotent**: re-running it does not raise and does not create
duplicate resources. A `--dry-run` flag short-circuits before any
boto3 call so the script is safe to use in CI sanity checks.

Usage:
    export AWS_REGION=us-east-1
    python create_event_bus.py

    # override defaults
    python create_event_bus.py --name acme-billing --source-account 444455556666

    # see what it would do, but don't actually call AWS
    python create_event_bus.py --dry-run

Required IAM permissions (least-privilege):
    events:CreateEventBus
    events:DescribeEventBus
    events:PutPermission
    events:ListEventBuses
on resource arn:aws:events:<region>:<account>:event-bus/*.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from typing import Optional

import boto3
from botocore.exceptions import ClientError

LOG = logging.getLogger("eventbridge.eventbus")
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
)


# ── helpers ────────────────────────────────────────────────────────────
def make_client(region: str):
    """Build a boto3 events client. Kept as a function so tests can
    patch `boto3.client` and count invocations."""
    return boto3.client("events", region_name=region)


def describe_event_bus_arn(client, name: str) -> str:
    """Return the ARN of an existing bus by name, or raise."""
    resp = client.describe_event_bus(Name=name)
    return resp["Arn"]


def ensure_event_bus(client, name: str) -> str:
    """Create the bus if missing; return its ARN either way.

    Idempotency: a second call hits `ResourceAlreadyExistsException`,
    which we treat as success and re-fetch the ARN from
    `DescribeEventBus`.
    """
    try:
        resp = client.create_event_bus(Name=name)
        LOG.info("created custom bus name=%s arn=%s", name, resp["EventBusArn"])
        return resp["EventBusArn"]
    except ClientError as exc:
        code = exc.response["Error"]["Code"]
        if code == "ResourceAlreadyExistsException":
            arn = describe_event_bus_arn(client, name)
            LOG.info("bus %s already exists; reusing arn=%s", name, arn)
            return arn
        raise


def apply_resource_policy(
    client,
    name: str,
    *,
    source_account: str,
    principal_arn: Optional[str] = None,
) -> None:
    """Grant another AWS account the right to call `PutEvents` on
    this bus. The policy is stored on the bus itself (a *resource
    policy*, not an IAM policy)."""
    bus_arn = describe_event_bus_arn(client, name)
    if principal_arn is None:
        principal_arn = f"arn:aws:iam::{source_account}:root"

    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowCrossAccountPutEvents",
                "Effect": "Allow",
                "Principal": {"AWS": principal_arn},
                "Action": "events:PutEvents",
                "Resource": bus_arn,
            }
        ],
    }
    # `put_permission` takes a JSON *string*, not a dict.
    client.put_permission(EventBusName=name, Policy=json.dumps(policy))
    LOG.info("applied resource policy to bus=%s allowing principal=%s",
             name, principal_arn)


def list_buses(client) -> list[dict]:
    """Return [{'Name': ..., 'Arn': ...}, ...] for every bus in the
    (account, region). Manually paginated with `Limit` + `NextToken`
    because `list_event_buses` is not in the botocore paginator config.
    Important because a real account can have up to ~100 buses."""
    out: list[dict] = []
    next_token: Optional[str] = None
    while True:
        kwargs: dict = {"Limit": 100}
        if next_token is not None:
            kwargs["NextToken"] = next_token
        page = client.list_event_buses(**kwargs)
        for b in page.get("EventBuses", []):
            out.append({"Name": b["Name"], "Arn": b["Arn"]})
        next_token = page.get("NextToken")
        if not next_token:
            break
    return out


def delete_event_bus(client, name: str) -> None:
    """Delete a custom bus. The default bus cannot be deleted; AWS
    raises `ValidationException` if you try."""
    client.delete_event_bus(Name=name)
    LOG.info("deleted bus name=%s", name)


# ── main ───────────────────────────────────────────────────────────────
def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Idempotently create a custom EventBridge bus, "
                    "apply a cross-account resource policy, and list "
                    "all buses in the (account, region)."
    )
    parser.add_argument(
        "--name",
        default=os.environ.get("BUS_NAME", "acme-orders"),
        help="Name of the custom bus to create (default: acme-orders).",
    )
    parser.add_argument(
        "--region",
        default=os.environ.get("AWS_REGION", "us-east-1"),
        help="AWS region (default: us-east-1).",
    )
    parser.add_argument(
        "--source-account",
        default=os.environ.get("SOURCE_ACCOUNT", "444455556666"),
        help="AWS account ID that will be granted PutEvents on the bus.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would happen but make no AWS calls.",
    )

    args = parser.parse_args(argv)

    if args.dry_run:
        print(f"[dry-run] would create_event_bus Name={args.name!r} "
              f"region={args.region}")
        print(f"[dry-run] would put_permission on bus {args.name!r} "
              f"allowing account={args.source_account}")
        print(f"[dry-run] would list_event_buses region={args.region}")
        return 0

    client = make_client(args.region)

    bus_arn = ensure_event_bus(client, args.name)
    apply_resource_policy(
        client, args.name, source_account=args.source_account
    )
    buses = list_buses(client)

    print()
    print("=" * 64)
    print(f"BUS ARN     : {bus_arn}")
    print(f"REGION      : {args.region}")
    print(f"ALLOWED ACCT: {args.source_account}")
    print("=" * 64)
    print(f"Found {len(buses)} bus(es) in this region:")
    for b in buses:
        marker = "*" if b["Name"] == args.name else " "
        print(f"  {marker} {b['Name']:<32}  {b['Arn']}")
    print("=" * 64)
    print()
    print("Next step: attach a rule. See L10 (Rules 101) in section 3.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
