"""subscription_filter.py — forward ERRORs from a log group to Kinesis.

Companion to L25/L29. Idempotent: existing groups / streams / filters
are not duplicated.

Required IAM permissions (real AWS):
    logs:CreateLogGroup
    logs:PutSubscriptionFilter
    logs:DescribeSubscriptionFilters
    kinesis:CreateStream
    kinesis:DescribeStream
    iam:PassRole
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time

import boto3
from botocore.config import Config

LOG = logging.getLogger("subscription_filter")
LOG.setLevel(logging.INFO)

LOG_GROUP = "/myapp/api"
STREAM_NAME = "cw-demo-logs-stream"
FILTER_NAME = "errors-to-kinesis"
FILTER_PATTERN = "ERROR"

# A real run needs an IAM role with CWL → Kinesis permissions.
ROLE_ARN = "arn:aws:iam::111122223333:role/CWLtoKinesisRole"
ACCOUNT_ID = "111122223333"


def _client(service: str, region: str = "us-east-1"):
    return boto3.client(
        service,
        region_name=region,
        config=Config(retries={"max_attempts": 3, "mode": "standard"}),
    )


def ensure_log_group(logs, *, dry_run: bool = False) -> None:
    if dry_run:
        LOG.info("[DRY-RUN] create_log_group logGroupName=%s", LOG_GROUP)
        return
    try:
        logs.create_log_group(logGroupName=LOG_GROUP)
        LOG.info("created log group %s", LOG_GROUP)
    except logs.exceptions.ResourceAlreadyExistsException:
        LOG.info("log group %s already exists", LOG_GROUP)


def ensure_stream(kinesis, *, dry_run: bool = False) -> str:
    if dry_run:
        LOG.info("[DRY-RUN] create_stream StreamName=%s ShardCount=1", STREAM_NAME)
        return f"arn:aws:kinesis:us-east-1:{ACCOUNT_ID}:stream/{STREAM_NAME}"
    try:
        kinesis.create_stream(StreamName=STREAM_NAME, ShardCount=1)
        LOG.info("created stream %s", STREAM_NAME)
    except kinesis.exceptions.ResourceInUseException:
        LOG.info("stream %s already exists", STREAM_NAME)
    # Wait for stream to be ACTIVE (real AWS only; moto is immediate).
    waiter = kinesis.get_waiter("stream_exists")
    try:
        waiter.wait(StreamName=STREAM_NAME, WaiterConfig={"Delay": 2, "MaxAttempts": 10})
    except Exception:
        pass
    desc = kinesis.describe_stream(StreamName=STREAM_NAME)
    return desc["StreamDescription"]["StreamARN"]


def ensure_subscription_filter(logs, destination_arn: str, *,
                              dry_run: bool = False) -> None:
    if dry_run:
        LOG.info("[DRY-RUN] put_subscription_filter:\n%s",
                 json.dumps({
                     "logGroupName": LOG_GROUP,
                     "filterName": FILTER_NAME,
                     "filterPattern": FILTER_PATTERN,
                     "destinationArn": destination_arn,
                     "roleArn": ROLE_ARN,
                 }, indent=2))
        return
    logs.put_subscription_filter(
        logGroupName=LOG_GROUP,
        filterName=FILTER_NAME,
        filterPattern=FILTER_PATTERN,
        destinationArn=destination_arn,
        roleArn=ROLE_ARN,
    )
    LOG.info("created subscription filter %s", FILTER_NAME)


def describe_filters(logs, *, dry_run: bool = False) -> list[dict]:
    if dry_run:
        return []
    resp = logs.describe_subscription_filters(logGroupName=LOG_GROUP)
    return resp.get("subscriptionFilters", [])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--region", default=os.environ.get("AWS_REGION", "us-east-1"))
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")

    logs = _client("logs", args.region)
    kinesis = _client("kinesis", args.region)

    print(f"[1/4] ensure_log_group ({LOG_GROUP})")
    ensure_log_group(logs, dry_run=args.dry_run)
    print(f"[2/4] ensure_stream ({STREAM_NAME})")
    stream_arn = ensure_stream(kinesis, dry_run=args.dry_run)
    print(f"      stream_arn = {stream_arn}")
    print(f"[3/4] ensure_subscription_filter ({FILTER_NAME})")
    ensure_subscription_filter(logs, stream_arn, dry_run=args.dry_run)
    print("[4/4] describe_subscription_filters")
    filters = describe_filters(logs, dry_run=args.dry_run)
    for f in filters:
        print(f"      name={f['filterName']:>22}  pattern={f['filterPattern']:>10}  "
              f"dest={f['destinationArn']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
