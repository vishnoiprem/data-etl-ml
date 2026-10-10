#!/usr/bin/env python3
"""
schedule_cron.py — idempotent demo of EventBridge Scheduler.

Creates (or updates) three schedules in a `default` schedule group:
- a `rate(5 minutes)` heartbeat
- a `cron(0 8 * * MON-FRI *)` in America/Los_Angeles with a flexible window
- an `at(2099-12-31T23:59:00)` one-off

Run with --dry-run to print the boto3 payloads without making any
AWS calls. Without --dry-run, the script is idempotent: every
schedule is created-or-updated, so re-running is safe.

NOTE on moto + the `scheduler` client:
    `moto[events]` historically mocked the `events` service but not
    the newer `scheduler` service. As of `moto` 5.x, the unified
    `mock_aws` decorator registers a scheduler backend that supports
    `create_schedule_group`, `create_schedule`, `update_schedule`,
    `get_schedule`, and `delete_schedule`. In pinned CI where the
    scheduler backend is partial, fall back to testing through the
    public `events` rule API (see test_schedule_cron.py). The
    production code below is unchanged — it always uses the
    `scheduler` client.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import boto3

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

SCHEDULE_GROUP = "default"

# Placeholder ARNs. Replace with your own Lambda + IAM role before
# running against a real AWS account.
LAMBDA_ARN = "arn:aws:lambda:us-east-1:111122223333:function:scheduler-demo"
SCHEDULER_ROLE_ARN = (
    "arn:aws:iam::111122223333:role/scheduler-invoke-lambda-demo"
)

# The three demo schedules. Each row exercises a different feature:
#   * rate(5 minutes)               -> L22
#   * cron with tz + flexible window -> L22 + L23
#   * at(...) one-off               -> L23
SCHEDULES: list[dict[str, Any]] = [
    {
        "name": "demo-rate-5min",
        "expression": "rate(5 minutes)",
        "expression_timezone": None,
        "flexible_window_minutes": 0,  # 0 == OFF (fire exactly on time)
        "input_payload": {"job": "heartbeat", "owner": "demo"},
        "description": "L22: rate(5 minutes) — fires every 5 minutes, UTC.",
    },
    {
        "name": "demo-cron-weekday-morning",
        "expression": "cron(0 8 * * MON-FRI *)",
        "expression_timezone": "America/Los_Angeles",
        "flexible_window_minutes": 10,  # 10-minute flexible window
        "input_payload": {"job": "morning-digest", "owner": "demo"},
        "description": "L22+L23: 8 AM Pacific on weekdays, flexible window.",
    },
    {
        "name": "demo-at-one-off",
        "expression": "at(2099-12-31T23:59:00)",
        "expression_timezone": None,
        "flexible_window_minutes": 0,
        "input_payload": {"job": "century-mark", "owner": "demo"},
        "description": "L23: one-off at-expression.",
    },
]


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def build_flexible_window(minutes: int) -> dict[str, Any]:
    """Turn an integer into the right `FlexibleTimeWindow` dict.

    0 means fire exactly on the minute (`Mode: OFF`). A positive
    integer is a `Mode: FLEXIBLE` window of that many minutes.
    """
    if minutes <= 0:
        return {"Mode": "OFF"}
    return {"Mode": "FLEXIBLE", "MaximumWindowInMinutes": minutes}


def build_schedule_params(
    spec: dict[str, Any], *, group: str, lambda_arn: str, role_arn: str
) -> dict[str, Any]:
    """Convert a `SCHEDULES` row into the kwargs for create/update_schedule."""
    params: dict[str, Any] = {
        "Name": spec["name"],
        "GroupName": group,
        "ScheduleExpression": spec["expression"],
        "FlexibleTimeWindow": build_flexible_window(
            spec["flexible_window_minutes"]
        ),
        "State": "ENABLED",
        "Description": spec.get("description", ""),
        "Target": {
            "Arn": lambda_arn,
            "RoleArn": role_arn,
            "Input": json.dumps(spec["input_payload"]),
        },
    }
    # Only include the timezone when it is set. (The API accepts the
    # field but it is cleaner to omit it when we mean UTC.)
    if spec.get("expression_timezone"):
        params["ScheduleExpressionTimezone"] = spec["expression_timezone"]
    return params


def ensure_schedule_group(client: Any, name: str, *, dry_run: bool) -> None:
    """Idempotently create a schedule group. No-op if it already exists."""
    if dry_run:
        print(f"[dry-run] would ensure schedule group: {name!r}")
        return
    try:
        client.create_schedule_group(Name=name)
        print(f"[ok] created schedule group: {name}")
    except client.exceptions.ConflictException:
        print(f"[ok] schedule group already exists: {name}")


def create_or_update_schedule(
    client: Any,
    spec: dict[str, Any],
    *,
    group: str,
    lambda_arn: str,
    role_arn: str,
    dry_run: bool,
) -> None:
    """Idempotently create-or-update a single schedule."""
    params = build_schedule_params(
        spec, group=group, lambda_arn=lambda_arn, role_arn=role_arn
    )
    if dry_run:
        print(
            f"[dry-run] {spec['name']}: would call create_schedule/update_schedule with:"
        )
        print(json.dumps(params, indent=2, default=str))
        return

    try:
        client.create_schedule(**params)
        print(f"[ok] created schedule: {spec['name']}")
    except client.exceptions.ConflictException:
        # update_schedule does not accept GroupName. Pull it out.
        update_params = {k: v for k, v in params.items() if k != "GroupName"}
        client.update_schedule(**update_params)
        print(f"[ok] updated schedule: {spec['name']}")


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Idempotent EventBridge Scheduler demo."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the boto3 payloads but do not call AWS.",
    )
    parser.add_argument(
        "--region",
        default="us-east-1",
        help="AWS region (default: us-east-1).",
    )
    parser.add_argument(
        "--lambda-arn",
        default=LAMBDA_ARN,
        help="Override the placeholder Lambda target ARN.",
    )
    parser.add_argument(
        "--role-arn",
        default=SCHEDULER_ROLE_ARN,
        help="Override the placeholder scheduler IAM role ARN.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    print(f"[info] region={args.region}  dry_run={args.dry_run}")

    client = boto3.client("scheduler", region_name=args.region)
    ensure_schedule_group(client, SCHEDULE_GROUP, dry_run=args.dry_run)

    for spec in SCHEDULES:
        create_or_update_schedule(
            client,
            spec,
            group=SCHEDULE_GROUP,
            lambda_arn=args.lambda_arn,
            role_arn=args.role_arn,
            dry_run=args.dry_run,
        )

    print("[info] done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
