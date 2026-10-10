"""create_log_group.py — create a log group + stream + events + filtered read.

Companion to L12/L14. Idempotent: safe to re-run; existing groups and
streams are not duplicated.

Required IAM permissions (real AWS):
    logs:CreateLogGroup
    logs:CreateLogStream
    logs:PutLogEvents
    logs:PutRetentionPolicy
    logs:FilterLogEvents
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import boto3
from botocore.config import Config

LOG = logging.getLogger("create_log_group")
LOG.setLevel(logging.INFO)

LOG_GROUP = "/myapp/api"
LOG_STREAM = "demo-stream"
RETENTION_DAYS = 30

# Three events at 60-s intervals, ending ~now-2min so the time-filter
# demo (window = last 5 min) only returns the last 2 events.
NOW = datetime.now(timezone.utc)


def _client(region: str = "us-east-1"):
    return boto3.client(
        "logs",
        region_name=region,
        config=Config(retries={"max_attempts": 3, "mode": "standard"}),
    )


def ensure_log_group(logs, *, dry_run: bool = False) -> None:
    """Create the log group (idempotent)."""
    if dry_run:
        LOG.info("[DRY-RUN] create_log_group logGroupName=%s", LOG_GROUP)
        return
    try:
        logs.create_log_group(logGroupName=LOG_GROUP)
        LOG.info("created log group %s", LOG_GROUP)
    except logs.exceptions.ResourceAlreadyExistsException:
        LOG.info("log group %s already exists", LOG_GROUP)


def set_retention(logs, days: int, *, dry_run: bool = False) -> None:
    if dry_run:
        LOG.info("[DRY-RUN] put_retention_policy days=%d", days)
        return
    logs.put_retention_policy(logGroupName=LOG_GROUP, retentionInDays=days)


def ensure_log_stream(logs, *, dry_run: bool = False) -> None:
    if dry_run:
        LOG.info("[DRY-RUN] create_log_stream stream=%s", LOG_STREAM)
        return
    try:
        logs.create_log_stream(logGroupName=LOG_GROUP, logStreamName=LOG_STREAM)
        LOG.info("created log stream %s", LOG_STREAM)
    except logs.exceptions.ResourceAlreadyExistsException:
        LOG.info("log stream %s already exists", LOG_STREAM)


def _build_events() -> list[dict]:
    """Build 3 structured JSON events at NOW-5m, NOW-4m, NOW-3m."""
    events = []
    for i, label in enumerate(["login", "view-cart", "checkout"]):
        ts_ms = int((NOW - timedelta(minutes=5 - i)).timestamp() * 1000)
        events.append({
            "timestamp": ts_ms,
            "message": json.dumps({
                "level": "INFO",
                "event": label,
                "user_id": 42 + i,
            }),
        })
    return events


def put_events(logs, *, dry_run: bool = False) -> list[dict]:
    events = _build_events()
    if dry_run:
        LOG.info("[DRY-RUN] put_log_events stream=%s count=%d",
                 LOG_STREAM, len(events))
        return events
    resp = logs.put_log_events(
        logGroupName=LOG_GROUP,
        logStreamName=LOG_STREAM,
        logEvents=events,
    )
    LOG.info("put %d events, nextSequenceToken=%s",
             len(events), resp.get("nextSequenceToken"))
    return events


def filter_events(logs, *, dry_run: bool = False) -> list[dict]:
    """Filter events in the last 5 minutes."""
    end_ms = int(NOW.timestamp() * 1000)
    start_ms = int((NOW - timedelta(minutes=5)).timestamp() * 1000)
    if dry_run:
        LOG.info("[DRY-RUN] filter_log_events window=[%d, %d]", start_ms, end_ms)
        return []
    resp = logs.filter_log_events(
        logGroupName=LOG_GROUP,
        startTime=start_ms,
        endTime=end_ms,
        interleaved=True,
    )
    return resp.get("events", [])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--region", default=os.environ.get("AWS_REGION", "us-east-1"))
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")

    logs = _client(args.region)

    print(f"[1/5] ensure_log_group ({LOG_GROUP})")
    ensure_log_group(logs, dry_run=args.dry_run)
    set_retention(logs, RETENTION_DAYS, dry_run=args.dry_run)
    print(f"[2/5] ensure_log_stream ({LOG_STREAM})")
    ensure_log_stream(logs, dry_run=args.dry_run)
    print("[3/5] put_log_events (3 structured events)")
    published = put_events(logs, dry_run=args.dry_run)
    print(f"      wrote {len(published)} events")
    print("[4/5] filter_log_events (last 5 minutes)")
    if not args.dry_run:
        # CloudWatch takes a moment to make the events queryable.
        time.sleep(1)
    events = filter_events(logs, dry_run=args.dry_run)
    print(f"      filter returned {len(events)} events")
    for e in events:
        print(f"      ts={e['timestamp']} msg={e['message']}")
    print("[5/5] describe_log_groups")
    if not args.dry_run:
        resp = logs.describe_log_groups(logGroupNamePrefix=LOG_GROUP)
        for g in resp["logGroups"]:
            print(f"      {g['logGroupName']:>40}  retention={g.get('retentionInDays', 'never')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
