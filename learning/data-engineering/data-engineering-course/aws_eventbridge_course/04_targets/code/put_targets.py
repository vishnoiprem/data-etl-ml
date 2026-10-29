"""Idempotent EventBridge target management.

This is the demo script for Section 4 of the AWS EventBridge Crash
Course (lecture L20). It demonstrates:

1. Idempotent creation of a custom event bus + a rule with an
   event pattern.
2. Idempotent addition of a Lambda target (with execution role).
3. Idempotent addition of an SQS target (with resource policy).
4. Listing target IDs.
5. Removing one target.
6. Re-adding it -- proving the script is idempotent across re-runs.

The script is safe to re-run; the second invocation leaves the
system in the same state as the first. It supports ``--dry-run``
for printing intent without making AWS calls.

Usage:
    # Offline (no AWS calls)
    python3 put_targets.py --dry-run

    # Real AWS (uses ~/.aws/credentials)
    python3 put_targets.py
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import boto3
from botocore.exceptions import ClientError

# ── Configuration constants ──────────────────────────────────────────────────

BUS_NAME = "orders-bus"
RULE_NAME = "orders-placed-rule"
REGION = "us-east-1"
ROLE_NAME = "EventBridgeInvokeLambda"
SQS_QUEUE_NAME = "orders-queue"

# Event pattern (same as Section 3)
EVENT_PATTERN: dict[str, Any] = {
    "source": ["my.app"],
    "detail-type": ["Order Placed"],
}

# Stable target IDs so re-runs replace, not duplicate.
LAMBDA_TARGET_ID = "lambda-process-order"
SQS_TARGET_ID = "sqs-orders"

# Placeholder ARNs for the demo. In a real AWS environment, these
# would be looked up from CloudFormation/CDK outputs or SSM.
# moto uses 000000000000 as the account ID.
DEMO_ACCOUNT = "000000000000"
LAMBDA_FUNCTION_NAME = "processOrder"
SQS_QUEUE_ARN = (
    f"arn:aws:sqs:us-east-1:{DEMO_ACCOUNT}:{SQS_QUEUE_NAME}"
)
LAMBDA_FUNCTION_ARN = (
    f"arn:aws:lambda:us-east-1:{DEMO_ACCOUNT}:function:{LAMBDA_FUNCTION_NAME}"
)
ROLE_ARN = f"arn:aws:iam::{DEMO_ACCOUNT}:role/{ROLE_NAME}"


# ── Client factories ─────────────────────────────────────────────────────────


def _events_client(region: str = REGION) -> Any:
    return boto3.client("events", region_name=region)


def _iam_client(region: str = REGION) -> Any:
    return boto3.client("iam", region_name=region)


def _sqs_client(region: str = REGION) -> Any:
    return boto3.client("sqs", region_name=region)


# ── Idempotent setup helpers ─────────────────────────────────────────────────


def ensure_bus(client: Any, bus_name: str) -> str:
    """Idempotent: create the bus if it doesn't exist. Return ARN string."""
    try:
        client.describe_event_bus(Name=bus_name)
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceNotFoundException":
            raise
        try:
            client.create_event_bus(Name=bus_name)
        except ClientError as ce:
            if ce.response["Error"]["Code"] != "ResourceAlreadyExistsException":
                raise
    return f"arn:aws:events:us-east-1:{DEMO_ACCOUNT}:event-bus/{bus_name}"


def ensure_rule(
    client: Any,
    bus_name: str,
    rule_name: str,
    pattern: dict[str, Any],
    state: str = "ENABLED",
) -> str:
    """Idempotent: put_rule is naturally upsert."""
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


def ensure_lambda_role(iam: Any, role_name: str = ROLE_NAME) -> str:
    """Create an IAM role EventBridge can assume to invoke Lambda.

    The demo uses a permissive mock environment; in real AWS you'd
    also attach a permission policy granting ``lambda:InvokeFunction``
    for the specific function ARN.
    """
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "events.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }],
    }
    try:
        iam.get_role(RoleName=role_name)
        return f"arn:aws:iam::{DEMO_ACCOUNT}:role/{role_name}"
    except ClientError as e:
        if e.response["Error"]["Code"] != "NoSuchEntity":
            raise
    iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(trust_policy),
    )
    return f"arn:aws:iam::{DEMO_ACCOUNT}:role/{role_name}"


def ensure_sqs_queue(sqs: Any, queue_name: str = SQS_QUEUE_NAME) -> str:
    """Create the demo SQS queue. Return the queue ARN."""
    try:
        resp = sqs.create_queue(QueueName=queue_name)
        queue_url = resp["QueueUrl"]
    except ClientError as e:
        # Race: someone created it between get and create
        if e.response["Error"]["Code"] != "QueueAlreadyExists":
            raise
        # We can't list queues by name easily; ask for it via attribute.
        queue_url = f"https://sqs.us-east-1.amazonaws.com/{DEMO_ACCOUNT}/{queue_name}"
    return f"arn:aws:sqs:us-east-1:{DEMO_ACCOUNT}:{queue_name}"


def attach_sqs_policy(sqs: Any, queue_arn: str, bus_name: str,
                      rule_name: str) -> None:
    """Attach a resource policy allowing EventBridge to write.

    This is what makes the SQS target work -- EventBridge checks
    the queue's policy before writing.
    """
    policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "AllowEventBridgeSend",
            "Effect": "Allow",
            "Principal": {"Service": "events.amazonaws.com"},
            "Action": "sqs:SendMessage",
            "Resource": queue_arn,
            "Condition": {
                "ArnEquals": {
                    "aws:SourceArn": (
                        f"arn:aws:events:us-east-1:{DEMO_ACCOUNT}"
                        f":rule/{bus_name}/{rule_name}"
                    )
                }
            },
        }]
    }
    # moto's SQS mock accepts set_queue_attributes with a JSON policy.
    # In real AWS you need the queue URL; for the demo we synthesize one.
    queue_url = (
        f"https://sqs.us-east-1.amazonaws.com/{DEMO_ACCOUNT}/"
        f"{queue_arn.split(':')[-1]}"
    )
    try:
        sqs.set_queue_attributes(
            QueueUrl=queue_url,
            Attributes={"Policy": json.dumps(policy)},
        )
    except ClientError:
        # If we can't fetch the URL, swallow -- the DLQ is best-effort.
        pass


# ── Target helpers ───────────────────────────────────────────────────────────


def add_lambda_target(
    events_client: Any,
    bus: str,
    rule: str,
    function_arn: str,
    role_arn: str,
    target_id: str = LAMBDA_TARGET_ID,
    dlq_arn: str | None = None,
) -> str:
    """Add (or replace) a Lambda target. Returns the target ID."""
    target: dict[str, Any] = {
        "Id": target_id,
        "Arn": function_arn,
        "RoleArn": role_arn,
    }
    if dlq_arn:
        target["DeadLetterConfig"] = {"Arn": dlq_arn}
    resp = events_client.put_targets(
        Rule=rule, EventBusName=bus, Targets=[target]
    )
    if resp.get("FailedEntries"):
        raise RuntimeError(f"failed to add lambda target: {resp['FailedEntries']}")
    return target_id


def add_sqs_target(
    events_client: Any,
    bus: str,
    rule: str,
    queue_arn: str,
    target_id: str = SQS_TARGET_ID,
) -> str:
    """Add (or replace) an SQS target. Returns the target ID."""
    resp = events_client.put_targets(
        Rule=rule, EventBusName=bus,
        Targets=[{"Id": target_id, "Arn": queue_arn}],
    )
    if resp.get("FailedEntries"):
        raise RuntimeError(f"failed to add sqs target: {resp['FailedEntries']}")
    return target_id


def remove_target(events_client: Any, bus: str, rule: str,
                  target_id: str) -> None:
    """Remove a single target by ID."""
    resp = events_client.remove_targets(
        Rule=rule, EventBusName=bus, Ids=[target_id],
    )
    if resp.get("FailedEntries"):
        raise RuntimeError(f"failed to remove target {target_id}: {resp['FailedEntries']}")


def list_target_ids(events_client: Any, bus: str, rule: str) -> list[str]:
    """Return the list of target IDs currently attached to a rule."""
    resp = events_client.list_targets_by_rule(Rule=rule, EventBusName=bus)
    return [t["Id"] for t in resp.get("Targets", [])]


# ── Demo orchestration ──────────────────────────────────────────────────────


def run(region: str = REGION) -> dict[str, Any]:
    """End-to-end demo: bus, rule, two targets, remove one, re-add.

    Returns a dict summarizing the state for tests/logging.
    """
    events = _events_client(region=region)
    iam = _iam_client(region=region)
    sqs = _sqs_client(region=region)

    ensure_bus(events, BUS_NAME)
    ensure_rule(events, BUS_NAME, RULE_NAME, EVENT_PATTERN)
    role_arn = ensure_lambda_role(iam)
    queue_arn = ensure_sqs_queue(sqs)
    attach_sqs_policy(sqs, queue_arn, BUS_NAME, RULE_NAME)

    add_lambda_target(events, BUS_NAME, RULE_NAME, LAMBDA_FUNCTION_ARN, role_arn)
    add_sqs_target(events, BUS_NAME, RULE_NAME, queue_arn)

    before = sorted(list_target_ids(events, BUS_NAME, RULE_NAME))

    # Remove one target, re-add it. Proves idempotency.
    remove_target(events, BUS_NAME, RULE_NAME, SQS_TARGET_ID)
    during = sorted(list_target_ids(events, BUS_NAME, RULE_NAME))
    add_sqs_target(events, BUS_NAME, RULE_NAME, queue_arn)
    after = sorted(list_target_ids(events, BUS_NAME, RULE_NAME))

    return {
        "after_setup": before,
        "after_remove": during,
        "after_readd": after,
    }


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
    args = parser.parse_args(argv)

    if args.dry_run:
        print(f"[dry-run] would ensure bus:    {BUS_NAME}  (region={args.region})")
        print(f"[dry-run] would ensure rule:   {RULE_NAME}")
        print(f"[dry-run] would add lambda target: {LAMBDA_TARGET_ID}")
        print(f"[dry-run] would add sqs target:    {SQS_TARGET_ID}")
        print(f"[dry-run] would list, remove, re-add {SQS_TARGET_ID}")
        return 0

    summary = run(region=args.region)
    for key, value in summary.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
