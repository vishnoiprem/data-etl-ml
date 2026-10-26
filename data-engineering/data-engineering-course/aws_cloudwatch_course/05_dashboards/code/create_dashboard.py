"""create_dashboard.py — build a 3-widget CloudWatch dashboard.

Companion to L23/L24. Idempotent: re-running replaces the dashboard
body with the same content.

Required IAM permissions (real AWS):
    cloudwatch:PutDashboard
    cloudwatch:GetDashboard
    cloudwatch:ListDashboards
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys

import boto3
from botocore.config import Config

LOG = logging.getLogger("create_dashboard")
LOG.setLevel(logging.INFO)

DASHBOARD_NAME = "checkout-overview"
REGION = "us-east-1"


def _client(region: str = REGION):
    return boto3.client(
        "cloudwatch",
        region_name=region,
        config=Config(retries={"max_attempts": 3, "mode": "standard"}),
    )


def build_body() -> dict:
    """Build a 3-widget dashboard body."""
    return {
        "widgets": [
            # 1) Metric: p99 API latency
            {"type": "metric",
             "x": 0, "y": 0, "width": 24, "height": 6,
             "properties": {
                 "metrics": [[
                     "AWS/ApiGateway", "Latency",
                     "ApiName", "checkout",
                     {"stat": "p99"},
                 ]],
                 "view": "timeSeries",
                 "stacked": False,
                 "region": REGION,
                 "title": "Checkout p99 Latency (ms)",
                 "period": 300,
             }},
            # 2) Logs Insights: top 20 ERRORs
            {"type": "log",
             "x": 0, "y": 6, "width": 16, "height": 8,
             "properties": {
                 "query": (
                     "SOURCE '/aws/lambda/checkout' "
                     "| filter @message like /ERROR/ "
                     "| fields @timestamp, @message "
                     "| sort @timestamp desc "
                     "| limit 20"
                 ),
                 "region": REGION,
                 "title": "Recent 20 ERRORs",
             }},
            # 3) Text: runbook
            {"type": "text",
             "x": 16, "y": 6, "width": 8, "height": 8,
             "properties": {
                 "markdown": (
                     "# Runbook\n\n"
                     "- **Wiki:** wiki/runbooks/checkout\n"
                     "- **PagerDuty:** pd.com/team\n"
                     "- **Slack:** #checkout-help\n"
                 ),
                 "background": "solid",
             }},
        ],
    }


def upsert_dashboard(cw, name: str, body: dict, *,
                     dry_run: bool = False) -> dict:
    """put_dashboard; return validation messages (always present, may be empty)."""
    payload = json.dumps(body)
    if dry_run:
        LOG.info("[DRY-RUN] put_dashboard Name=%s body length=%d chars",
                 name, len(payload))
        LOG.info("[DRY-RUN] body:\n%s", json.dumps(body, indent=2))
        return {"DashboardValidationMessages": []}
    resp = cw.put_dashboard(DashboardName=name, DashboardBody=payload)
    LOG.info("put_dashboard Name=%s validation messages=%d",
             name, len(resp.get("DashboardValidationMessages", [])))
    return resp


def get_dashboard(cw, name: str, *, dry_run: bool = False) -> dict | None:
    if dry_run:
        LOG.info("[DRY-RUN] get_dashboard Name=%s", name)
        return None
    try:
        resp = cw.get_dashboard(DashboardName=name)
    except cw.exceptions.ResourceNotFound:
        return None
    return json.loads(resp["DashboardBody"])


def list_dashboards(cw, *, dry_run: bool = False) -> list[str]:
    if dry_run:
        return []
    paginator = cw.get_paginator("list_dashboards")
    names: list[str] = []
    for page in paginator.paginate():
        names.extend(d["DashboardName"] for d in page["DashboardEntries"])
    return names


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--region", default=os.environ.get("AWS_REGION", REGION))
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")

    cw = _client(args.region)
    body = build_body()
    print(f"[1/3] put_dashboard Name={DASHBOARD_NAME} (3 widgets)")
    upsert_dashboard(cw, DASHBOARD_NAME, body, dry_run=args.dry_run)
    print("[2/3] get_dashboard")
    got = get_dashboard(cw, DASHBOARD_NAME, dry_run=args.dry_run)
    if got:
        for w in got["widgets"]:
            print(f"      {w['type']:>7}  ({w['x']},{w['y']}) "
                  f"{w['width']}x{w['height']}  title={w['properties'].get('title', '-')}")
    print("[3/3] list_dashboards")
    names = list_dashboards(cw, dry_run=args.dry_run)
    for n in names:
        print(f"      {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
