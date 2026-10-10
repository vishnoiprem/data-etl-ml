"""put_metric_data.py — publish 5 latency datapoints + read back stats.

Companion to L08/L09. Idempotent: re-running produces the same metric
state because CloudWatch metrics are upserted.

Required IAM permissions (real AWS):
    cloudwatch:PutMetricData
    cloudwatch:GetMetricStatistics
    cloudwatch:ListMetrics
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import sys
import time
from datetime import datetime, timedelta, timezone

import boto3
from botocore.config import Config

LOG = logging.getLogger("put_metric_data")
LOG.setLevel(logging.INFO)

NAMESPACE = "MyApp"
METRIC_NAME = "LatencyMs"
DIMENSIONS = [
    {"Name": "Endpoint", "Value": "/checkout"},
    {"Name": "Region",   "Value": "us-east-1"},
]

# 5 synthetic datapoints, each one minute apart. We use a realistic
# latency range so the p99 demonstration in the lecture makes sense.
BASE_LATENCY = 87.4
JITTER = 25.0  # ±25ms


def _client(region: str = "us-east-1"):
    return boto3.client(
        "cloudwatch",
        region_name=region,
        config=Config(retries={"max_attempts": 3, "mode": "standard"}),
    )


def publish_metrics(cw, *, dry_run: bool = False) -> list[dict]:
    """Publish 5 latency datapoints to the custom MyApp namespace."""
    metric_data = []
    now = datetime.now(timezone.utc)
    for i in range(5):
        value = BASE_LATENCY + random.uniform(-JITTER, JITTER)
        dp = {
            "MetricName": METRIC_NAME,
            "Value": round(value, 2),
            "Unit": "Milliseconds",
            "Timestamp": now - timedelta(minutes=5 - i),
            "Dimensions": DIMENSIONS,
        }
        metric_data.append(dp)

    LOG.info("publishing %d datapoints to namespace=%s", len(metric_data), NAMESPACE)
    if dry_run:
        LOG.info("[DRY-RUN] put_metric_data payload:\n%s",
                 json.dumps({"Namespace": NAMESPACE, "MetricData": metric_data},
                            default=str, indent=2))
        return metric_data

    cw.put_metric_data(Namespace=NAMESPACE, MetricData=metric_data)
    return metric_data


def get_statistics(cw, *, dry_run: bool = False) -> dict:
    """Read Average + p99 over the last 5 minutes."""
    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=5)
    params = dict(
        Namespace=NAMESPACE,
        MetricName=METRIC_NAME,
        Dimensions=DIMENSIONS,
        StartTime=start,
        EndTime=end,
        Period=60,
        Statistics=["Average", "Sum", "SampleCount"],
        ExtendedStatistics=["p99", "p95"],
    )
    if dry_run:
        LOG.info("[DRY-RUN] get_metric_statistics params:\n%s",
                 json.dumps(params, default=str, indent=2))
        return {"Datapoints": [], "dry_run": True}
    return cw.get_metric_statistics(**params)


def list_namespaced_metrics(cw, *, dry_run: bool = False) -> list[dict]:
    """List all metrics in the MyApp namespace; confirm dimensions exist."""
    if dry_run:
        LOG.info("[DRY-RUN] list_metrics Namespace=%s", NAMESPACE)
        return []
    paginator = cw.get_paginator("list_metrics")
    page_iter = paginator.paginate(Namespace=NAMESPACE)
    metrics: list[dict] = []
    for page in page_iter:
        metrics.extend(page["Metrics"])
    return metrics


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--dry-run", action="store_true",
                        help="Print API call payloads without making them.")
    parser.add_argument("--region", default=os.environ.get("AWS_REGION", "us-east-1"))
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")

    cw = _client(args.region)

    published = publish_metrics(cw, dry_run=args.dry_run)
    print(f"\n[1/3] Published {len(published)} datapoints to {NAMESPACE}")

    if not args.dry_run:
        # CloudWatch aggregates the publish; the first query can return
        # a partial result. A tiny sleep makes the read-back deterministic
        # for the demo. Skip in --dry-run.
        time.sleep(1)

    stats = get_statistics(cw, dry_run=args.dry_run)
    print(f"[2/3] get_metric_statistics returned {len(stats.get('Datapoints', []))} "
          f"datapoints")
    for dp in stats.get("Datapoints", []):
        print(f"   ts={dp['Timestamp']} avg={dp.get('Average')} "
              f"p99={dp.get('p99')} samples={dp.get('SampleCount')}")

    metrics = list_namespaced_metrics(cw, dry_run=args.dry_run)
    print(f"[3/3] list_metrics found {len(metrics)} series in {NAMESPACE}")
    for m in metrics[:5]:
        dims = {d["Name"]: d["Value"] for d in m.get("Dimensions", [])}
        print(f"   {m['MetricName']:>14}  dims={dims}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
