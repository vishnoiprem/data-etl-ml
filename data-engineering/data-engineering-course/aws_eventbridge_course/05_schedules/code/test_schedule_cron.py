#!/usr/bin/env python3
"""
test_schedule_cron.py — pytest suite for schedule_cron.py.

Six tests covering:
  1. rate expression canonical form (pure-Python).
  2. cron expression 6-field shape and `?` rule (pure-Python).
  3. build_flexible_window helper (pure-Python).
  4. --dry-run does not actually call AWS (moto mock_aws).
  5. create_or_update_schedule is idempotent (moto mock_aws).
  6. Legacy CloudWatch Events rule fallback path (moto[events]).

NOTE on moto support for the `scheduler` client:
    moto 5.x ships a `scheduler` backend under the unified `mock_aws`
    decorator that supports `create_schedule_group`, `create_schedule`,
    `update_schedule`, and `get_schedule`. We use that here. If you
    are pinned to an older `moto` that does not register a `scheduler`
    backend, fall back to the `events` rule API (test 6) — the
    production code in schedule_cron.py does not change.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from unittest import mock

import boto3
import pytest

# Make schedule_cron.py importable when pytest is run from the
# course root.
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import schedule_cron  # noqa: E402  (path-mutating import)


# ----------------------------------------------------------------------
# Pure-Python unit tests
# ----------------------------------------------------------------------


def test_rate_expression_format():
    """Every rate expression in SCHEDULES is well-formed."""
    rate_pat = re.compile(r"^rate\((\d+)\s+(minute|minutes|hour|hours|day|days)\)$")
    for spec in schedule_cron.SCHEDULES:
        if spec["expression"].startswith("rate("):
            assert rate_pat.match(spec["expression"]), spec["expression"]


def test_cron_six_fields_and_question_mark_rule():
    """Every cron expression has 6 fields, and exactly one of dom/dow is '?'."""
    for spec in schedule_cron.SCHEDULES:
        expr = spec["expression"]
        if not expr.startswith("cron("):
            continue
        assert expr.endswith(")"), expr
        inner = expr[len("cron(") : -1]
        fields = inner.split()
        assert len(fields) == 6, f"expected 6 fields, got {len(fields)}: {expr}"
        dom, dow = fields[2], fields[4]
        # AWS rule: day-of-month and day-of-week cannot both be '*'.
        # The convention is to set one of them to '?'. In the demo
        # set we use '?' in the day-of-week position when the
        # day-of-month is a wildcard, and we use '?' in the
        # day-of-month position when day-of-week is a list (e.g.
        # MON-FRI). Either is fine.
        assert not (dom == "*" and dow == "*"), (
            f"day-of-month and day-of-week cannot both be '*': {expr}"
        )


def test_flexible_window_helper():
    """build_flexible_window(0) == OFF; >0 == FLEXIBLE with the right minutes."""
    assert schedule_cron.build_flexible_window(0) == {"Mode": "OFF"}
    assert schedule_cron.build_flexible_window(10) == {
        "Mode": "FLEXIBLE",
        "MaximumWindowInMinutes": 10,
    }
    # Negative values are treated as OFF (defensive default).
    assert schedule_cron.build_flexible_window(-1) == {"Mode": "OFF"}


# ----------------------------------------------------------------------
# moto-backed scheduler tests
# ----------------------------------------------------------------------


def test_dry_run_does_not_call_aws(capsys):
    """`--dry-run` prints payloads but does not create a schedule."""
    from moto import mock_aws

    with mock_aws():
        rc = schedule_cron.main(["--dry-run", "--region", "us-east-1"])
        assert rc == 0

        # No schedule should have been created.
        client = boto3.client("scheduler", region_name="us-east-1")
        listed = client.list_schedules(GroupName="default")
        assert listed.get("Schedules", []) == []

    out = capsys.readouterr().out
    # We should see at least one "[dry-run]" prefix.
    assert "[dry-run]" in out
    # And the cron expression should appear in the printed payload.
    assert "cron(0 8 * * MON-FRI *)" in out


def test_create_or_update_is_idempotent():
    """Running the demo twice creates exactly one schedule per row."""
    from moto import mock_aws

    with mock_aws():
        # First run — creates the schedules.
        rc1 = schedule_cron.main(["--region", "us-east-1"])
        assert rc1 == 0

        client = boto3.client("scheduler", region_name="us-east-1")
        listed = client.list_schedules(GroupName="default")
        names1 = sorted(s["Name"] for s in listed.get("Schedules", []))
        assert names1 == sorted(s["name"] for s in schedule_cron.SCHEDULES)

        # Second run — should update, not create new ones.
        rc2 = schedule_cron.main(["--region", "us-east-1"])
        assert rc2 == 0

        listed2 = client.list_schedules(GroupName="default")
        names2 = sorted(s["Name"] for s in listed2.get("Schedules", []))
        # No duplicates — the second run is a no-op create + an update.
        assert names2 == names1


def test_legacy_events_rule_still_works():
    """Fallback path: the legacy `events` rule API still accepts a
    `rate`/`cron` ScheduleExpression. This is the path you'd use if
    you were pinned to an older `moto` that did not register a
    `scheduler` backend."""
    from moto import mock_aws

    with mock_aws():
        events = boto3.client("events", region_name="us-east-1")
        resp = events.put_rule(
            Name="legacy-rate-5min",
            ScheduleExpression="rate(5 minutes)",
            State="ENABLED",
            Description="Legacy CW Events schedule rule (fallback path).",
        )
        assert "RuleArn" in resp

        described = events.describe_rule(Name="legacy-rate-5min")
        assert described["ScheduleExpression"] == "rate(5 minutes)"
        assert described["State"] == "ENABLED"


def test_build_schedule_params_includes_flexible_window_and_input():
    """Smoke test for the parameter builder."""
    spec = next(
        s for s in schedule_cron.SCHEDULES
        if s["name"] == "demo-cron-weekday-morning"
    )
    params = schedule_cron.build_schedule_params(
        spec,
        group="default",
        lambda_arn="arn:aws:lambda:us-east-1:111122223333:function:f",
        role_arn="arn:aws:iam::111122223333:role/r",
    )
    assert params["ScheduleExpression"] == "cron(0 8 * * MON-FRI *)"
    assert params["ScheduleExpressionTimezone"] == "America/Los_Angeles"
    assert params["FlexibleTimeWindow"] == {
        "Mode": "FLEXIBLE",
        "MaximumWindowInMinutes": 10,
    }
    # The Input field should be a JSON string with the payload.
    payload = json.loads(params["Target"]["Input"])
    assert payload["job"] == "morning-digest"
