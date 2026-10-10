#!/usr/bin/env python3
"""
archive_replay.py — idempotent demo of EventBridge Archive + Replay.

What it does:
  1. Creates a custom event bus `orders-bus`.
  2. Creates a dedicated replay bus `orders-replay-bus`.
  3. Creates a 30-day archive `orders-archive-30d` against the
     `orders-bus`.
  4. Sends 5 synthetic `Order Placed` events to the bus.
  5. Starts a `start_replay` for the last 1 hour, with the replay
     bus as the destination.

Run with --dry-run to print the boto3 payloads without making any
AWS calls. Without --dry-run, the script is idempotent for the
bus and archive creation; the replay itself is *not* idempotent
(start_replay with an existing name raises ResourceAlreadyExists).

NOTE on moto + archive/replay:
    `moto[events]` historically mocked `create_event_bus` and
    `put_events` but not the newer `create_archive` / `start_replay`
    APIs. As of `moto` 5.x, the unified `mock_aws` decorator
    registers an events backend that supports `create_event_bus`,
    `create_archive`, `list_archives`, `put_events`, `start_replay`,
    and `describe_replay` (with the caveat that `start_replay`
    requires both the source bus and the destination bus to exist
    in the mock). In pinned CI where the archive/replay support is
    partial, the pure-Python unit tests cover the timestamp-filter
    logic that the demo's `start_replay` payload depends on.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from typing import Any

import boto3

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

BUS_NAME = "orders-bus"
REPLAY_BUS_NAME = "orders-replay-bus"
ARCHIVE_NAME = "orders-archive-30d"
REPLAY_NAME = "orders-replay-last-hour"
RETENTION_DAYS = 30

# 1 hour = a smoke test. 24 hours = a daily backfill. 720 = full 30 days.
REPLAY_WINDOW_HOURS = 1

# How many synthetic events to seed in the archive.
SEED_EVENT_COUNT = 5


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def build_replay_time_range(window_hours: int) -> tuple[datetime, datetime]:
    """Return (EventStartTime, EventEndTime) as timezone-aware UTC datetimes."""
    if window_hours <= 0:
        raise ValueError(f"window_hours must be > 0, got {window_hours}")
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=window_hours)
    return start, end


def ensure_event_bus(client: Any, name: str, *, dry_run: bool) -> str:
    """Idempotently create an event bus. Returns the bus ARN."""
    if dry_run:
        print(f"[dry-run] would ensure event bus: {name!r}")
        return f"arn:aws:events:us-east-1:111122223333:event-bus/{name}"

    try:
        resp = client.create_event_bus(Name=name)
        print(f"[ok] created event bus: {name}")
        return resp["EventBusArn"]
    except client.exceptions.ResourceAlreadyExistsException:
        # describe_event_bus returns the ARN
        described = client.describe_event_bus(Name=name)
        print(f"[ok] event bus already exists: {name}")
        return described["Arn"]


def ensure_archive(
    client: Any,
    *,
    archive_name: str,
    bus_arn: str,
    retention_days: int,
    dry_run: bool,
) -> str:
    """Idempotently create an archive. Returns the archive ARN."""
    if dry_run:
        print(f"[dry-run] would create archive: {archive_name!r}")
        return f"arn:aws:events:us-east-1:111122223333:archive/{archive_name}"

    try:
        resp = client.create_archive(
            ArchiveName=archive_name,
            EventSourceArn=bus_arn,
            RetentionDays=retention_days,
            Description=(
                f"{retention_days}-day archive of every event on the "
                f"{BUS_NAME} bus (created by archive_replay.py)."
            ),
        )
        print(f"[ok] created archive: {archive_name}")
        return resp["ArchiveArn"]
    except client.exceptions.ResourceAlreadyExistsException:
        # `describe_archive` returns the existing ARN. We prefer
        # this over `list_archives` because some moto backends
        # return a different field shape on list (no ArchiveArn
        # in the summary), whereas describe_archive always
        # includes the ARN.
        described = client.describe_archive(ArchiveName=archive_name)
        print(f"[ok] archive already exists: {archive_name}")
        return described["ArchiveArn"]


def send_test_events(
    client: Any,
    *,
    bus_name: str,
    count: int,
    dry_run: bool,
) -> int:
    """Seed the archive with synthetic Order Placed events. Returns
    the number of events put."""
    entries = [
        {
            "Source": "demo.app",
            "DetailType": "Order Placed",
            "Detail": json.dumps(
                {"orderId": f"o-{i}", "total": 42, "currency": "USD"}
            ),
            "EventBusName": bus_name,
        }
        for i in range(count)
    ]
    if dry_run:
        print(f"[dry-run] would put {count} events on bus {bus_name!r}:")
        print(json.dumps(entries[:2], indent=2))
        if count > 2:
            print(f"  ... ({count - 2} more)")
        return count

    resp = client.put_events(Entries=entries)
    failed = resp.get("FailedEntryCount", 0)
    sent = len(resp.get("Entries", [])) - failed
    print(f"[ok] put_events: {sent} succeeded, {failed} failed")
    return sent


def start_replay_for_last_window(
    client: Any,
    *,
    replay_name: str,
    source_bus_arn: str,
    destination_bus_arn: str,
    window_hours: int,
    dry_run: bool,
) -> str:
    """Start a replay for the last `window_hours` of the archive.
    Returns the replay ARN."""
    start, end = build_replay_time_range(window_hours)
    params: dict[str, Any] = {
        "ReplayName": replay_name,
        "Description": (
            f"Replay of last {window_hours}h from "
            f"{start.isoformat()} to {end.isoformat()}"
        ),
        "EventSourceArn": source_bus_arn,
        "EventStartTime": start,
        "EventEndTime": end,
        "Destination": {"Arn": destination_bus_arn},
    }

    if dry_run:
        print(f"[dry-run] would start_replay:")
        print(json.dumps(
            {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in params.items()},
            indent=2,
            default=str,
        ))
        return f"arn:aws:events:us-east-1:111122223333:replay/{replay_name}"

    resp = client.start_replay(**params)
    print(f"[ok] started replay: {replay_name} -> {resp['ReplayArn']}")
    return resp["ReplayArn"]


def describe_replay_if_exists(client: Any, replay_name: str) -> dict[str, Any] | None:
    """Wrap describe_replay with a ResourceNotFoundException catch.
    Returns the response dict or None if the replay does not exist."""
    try:
        return client.describe_replay(ReplayName=replay_name)
    except client.exceptions.ResourceNotFoundException:
        return None


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Idempotent EventBridge Archive + Replay demo."
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
        "--window-hours",
        type=int,
        default=REPLAY_WINDOW_HOURS,
        help=f"Replay window in hours (default: {REPLAY_WINDOW_HOURS}).",
    )
    parser.add_argument(
        "--seed-count",
        type=int,
        default=SEED_EVENT_COUNT,
        help=f"Number of synthetic events to seed (default: {SEED_EVENT_COUNT}).",
    )
    parser.add_argument(
        "--replay-name",
        default=REPLAY_NAME,
        help=f"Replay name (default: {REPLAY_NAME}).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    print(
        f"[info] region={args.region}  dry_run={args.dry_run}  "
        f"window_hours={args.window_hours}  seed_count={args.seed_count}"
    )

    client = boto3.client("events", region_name=args.region)

    # 1. Source bus
    source_arn = ensure_event_bus(client, BUS_NAME, dry_run=args.dry_run)

    # 2. Replay bus (destination)
    dest_arn = ensure_event_bus(client, REPLAY_BUS_NAME, dry_run=args.dry_run)

    # 3. Archive against the source bus
    ensure_archive(
        client,
        archive_name=ARCHIVE_NAME,
        bus_arn=source_arn,
        retention_days=RETENTION_DAYS,
        dry_run=args.dry_run,
    )

    # 4. Seed the archive with synthetic events
    send_test_events(
        client,
        bus_name=BUS_NAME,
        count=args.seed_count,
        dry_run=args.dry_run,
    )

    # 5. Start a replay for the last window_hours
    start_replay_for_last_window(
        client,
        replay_name=args.replay_name,
        source_bus_arn=source_arn,
        destination_bus_arn=dest_arn,
        window_hours=args.window_hours,
        dry_run=args.dry_run,
    )

    print("[info] done")
    return 0


if __name__ == "__main__":
    sys.exit(main())