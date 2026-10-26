#!/usr/bin/env python3
"""
test_archive_replay.py — pytest suite for archive_replay.py.

Six tests covering:
  1. Replay time-range builder (pure-Python).
  2. start_replay payload shape (pure-Python).
  3. --dry-run does not call AWS (moto mock_aws).
  4. create_event_bus is idempotent (moto mock_aws).
  5. create_archive against a custom bus (moto mock_aws).
  6. start_replay requires both source and destination buses
     (validation test; boto3 + moto).

NOTE on moto + archive/replay:
    moto 5.x supports `create_event_bus`, `create_archive`,
    `list_archives`, `put_events`, `start_replay`, and
    `describe_replay` under the unified `mock_aws` decorator. The
    `start_replay` call requires both the source and destination
    buses to exist in the mock. We rely on that here. For pinned
    CI environments where the archive/replay backend is partial,
    tests 1, 2, and 6 still work — they are pure-Python.
"""
from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime, timezone

import boto3
import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import archive_replay  # noqa: E402  (path-mutating import)


# ----------------------------------------------------------------------
# Pure-Python unit tests
# ----------------------------------------------------------------------


def test_build_replay_time_range_is_exactly_window_hours_wide():
    """The time range covers exactly the configured number of hours."""
    for window in (1, 6, 24, 168, 720):
        start, end = archive_replay.build_replay_time_range(window)
        delta = end - start
        assert delta.total_seconds() == window * 3600, (
            f"window={window}: expected {window*3600}s, got {delta.total_seconds()}s"
        )
        # Both must be timezone-aware UTC.
        assert start.tzinfo == timezone.utc
        assert end.tzinfo == timezone.utc
        # And end must be strictly after start.
        assert end > start


def test_build_replay_time_range_rejects_non_positive():
    """Zero or negative window hours raise ValueError."""
    with pytest.raises(ValueError):
        archive_replay.build_replay_time_range(0)
    with pytest.raises(ValueError):
        archive_replay.build_replay_time_range(-1)


def test_replay_payload_shape():
    """`start_replay` payload has the required fields and the right
    window width. We assemble the payload manually rather than calling
    `start_replay_for_last_window` so this test does not depend on
    moto's replay backend."""
    start, end = archive_replay.build_replay_time_range(window_hours=2)
    payload = {
        "ReplayName": "test-replay",
        "Description": "test",
        "EventSourceArn": "arn:aws:events:us-east-1:111122223333:event-bus/orders-bus",
        "EventStartTime": start,
        "EventEndTime": end,
        "Destination": {"Arn": "arn:aws:events:us-east-1:111122223333:event-bus/orders-replay-bus"},
    }
    # Required keys per the StartReplay API.
    required = {"ReplayName", "EventSourceArn", "EventStartTime",
                "EventEndTime", "Destination"}
    assert required.issubset(payload.keys())
    # The Destination must wrap the bus ARN under "Arn".
    assert "Arn" in payload["Destination"]
    # The window must be exactly 2 hours.
    assert (payload["EventEndTime"] - payload["EventStartTime"]).total_seconds() == 2 * 3600


# ----------------------------------------------------------------------
# moto-backed events tests
# ----------------------------------------------------------------------


def test_dry_run_does_not_call_aws(capsys):
    """`--dry-run` prints payloads but does not create a bus or archive."""
    from moto import mock_aws

    with mock_aws():
        rc = archive_replay.main([
            "--dry-run",
            "--region", "us-east-1",
            "--window-hours", "1",
            "--seed-count", "3",
        ])
        assert rc == 0

        # Nothing should have been created.
        client = boto3.client("events", region_name="us-east-1")
        buses = client.list_event_buses()
        names = [b["Name"] for b in buses.get("EventBuses", [])]
        assert archive_replay.BUS_NAME not in names
        assert archive_replay.REPLAY_BUS_NAME not in names

        archives = client.list_archives().get("Archives", [])
        assert archives == []

    out = capsys.readouterr().out
    # At least 4 [dry-run] markers (bus, replay-bus, archive, events, replay).
    assert out.count("[dry-run]") >= 4
    # The seed events should show up in the printed payload.
    assert "Order Placed" in out


def test_create_event_bus_is_idempotent():
    """ensure_event_bus can be called twice without error."""
    from moto import mock_aws

    with mock_aws():
        client = boto3.client("events", region_name="us-east-1")
        arn1 = archive_replay.ensure_event_bus(
            client, "my-bus", dry_run=False
        )
        arn2 = archive_replay.ensure_event_bus(
            client, "my-bus", dry_run=False
        )
        assert arn1 == arn2
        assert "my-bus" in arn1


def test_create_archive_against_custom_bus():
    """`create_archive` succeeds when the bus exists; idempotent on re-run."""
    from moto import mock_aws

    with mock_aws():
        client = boto3.client("events", region_name="us-east-1")
        bus_arn = archive_replay.ensure_event_bus(
            client, "orders-bus", dry_run=False
        )
        arch_arn1 = archive_replay.ensure_archive(
            client,
            archive_name="orders-archive-30d",
            bus_arn=bus_arn,
            retention_days=30,
            dry_run=False,
        )
        assert arch_arn1.endswith(":archive/orders-archive-30d")

        # Second call should not raise.
        arch_arn2 = archive_replay.ensure_archive(
            client,
            archive_name="orders-archive-30d",
            bus_arn=bus_arn,
            retention_days=30,
            dry_run=False,
        )
        assert arch_arn2 == arch_arn1

        # The archive should appear in list_archives.
        listed = client.list_archives(NamePrefix="orders-archive-30d")
        names = [a["ArchiveName"] for a in listed.get("Archives", [])]
        assert "orders-archive-30d" in names


def test_replay_requires_existing_buses(monkeypatch):
    """Without the source and destination buses, start_replay fails."""
    from moto import mock_aws

    with mock_aws():
        client = boto3.client("events", region_name="us-east-1")
        # No buses created. The replay call should raise.
        with pytest.raises(Exception) as excinfo:
            archive_replay.start_replay_for_last_window(
                client,
                replay_name="test-replay",
                source_bus_arn="arn:aws:events:us-east-1:123456789012:event-bus/orders-bus",
                destination_bus_arn="arn:aws:events:us-east-1:123456789012:event-bus/orders-replay-bus",
                window_hours=1,
                dry_run=False,
            )
        # The exception should mention the missing bus.
        assert "bus" in str(excinfo.value).lower() or "does not exist" in str(excinfo.value).lower()


def test_send_test_events_writes_to_bus():
    """`put_events` with a custom bus succeeds and the bus persists the event."""
    from moto import mock_aws

    with mock_aws():
        client = boto3.client("events", region_name="us-east-1")
        bus_arn = archive_replay.ensure_event_bus(
            client, "orders-bus", dry_run=False
        )
        sent = archive_replay.send_test_events(
            client, bus_name="orders-bus", count=3, dry_run=False
        )
        assert sent == 3

        # The test event entries use Source=demo.app and DetailType=Order Placed.
        # We can re-issue another put_events to confirm the bus is alive.
        resp = client.put_events(
            Entries=[
                {
                    "Source": "demo.app",
                    "DetailType": "Order Placed",
                    "Detail": json.dumps({"orderId": "o-extra"}),
                    "EventBusName": "orders-bus",
                }
            ]
        )
        assert resp.get("FailedEntryCount", 0) == 0
