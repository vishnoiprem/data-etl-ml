"""Idempotently create / update an API Key and a Usage Plan for Use Case 2.

The script can be run any number of times. On re-run it:
  * looks up the REST API by name,
  * reuses the existing API Key (if any) and updates the enabled flag,
  * reuses the existing Usage Plan (if any) and updates the throttle /
    quota values,
  * attaches the key to the plan only if not already attached.

Usage:
    export AWS_REGION=us-east-1
    export API_NAME=ServerlessCRUD
    export STAGE_NAME=prod
    python create_api_key.py
    # or with explicit overrides:
    python create_api_key.py --rate 200 --burst 400 --quota 100000 --quota-period MONTH
"""
from __future__ import annotations

import argparse
import logging
import os
from typing import Optional

import boto3
from botocore.exceptions import ClientError

LOG = logging.getLogger("usecase2.api_keys")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


# ── helpers ────────────────────────────────────────────────────────────
def find_rest_api_id(client, name: str) -> str:
    """Return the API ID of the REST API with the given name, or raise."""
    paginator = client.get_paginator("get_rest_apis")
    for page in paginator.paginate():
        for api in page["items"]:
            if api["name"] == name:
                return api["id"]
    raise RuntimeError(f"REST API named {name!r} not found")


def ensure_api_key(
    client,
    name: str,
    value: Optional[str] = None,
    *,
    enabled: bool = True,
) -> str:
    """Return the API Key ID. Reuses an existing key with the same name."""
    paginator = client.get_paginator("get_api_keys")
    for page in paginator.paginate(includeValues=True):
        for k in page["items"]:
            if k["name"] == name:
                client.update_api_key(
                    apiKey=k["id"],
                    patchOperations=[
                        {"op": "replace", "path": "/enabled",
                         "value": str(enabled).lower()},
                    ],
                )
                LOG.info("reusing existing API Key id=%s name=%s", k["id"], name)
                return k["id"]

    params: dict = {"name": name, "enabled": enabled}
    if value:
        params["value"] = value
    resp = client.create_api_key(**params)
    LOG.info("created new API Key id=%s name=%s", resp["id"], name)
    return resp["id"]


def ensure_usage_plan(
    client,
    name: str,
    *,
    rate_limit: float,
    burst_limit: int,
    quota_limit: int,
    quota_period: str,
    stages: list[dict],
) -> str:
    """Create or update a Usage Plan with the given throttle / quota."""
    paginator = client.get_paginator("get_usage_plans")
    existing = None
    for page in paginator.paginate():
        for p in page["items"]:
            if p["name"] == name:
                existing = p
                break
        if existing:
            break

    if existing:
        plan_id = existing["id"]
        # update_usage_plan only takes int values in its patchOperations.
        # Round to an int if a whole number, else cast to int (AWS API
        # itself takes a float; we use int in the patch to match boto3
        # validation for update_usage_plan specifically).
        rate_str = str(int(rate_limit)) if rate_limit == int(rate_limit) else str(rate_limit)
        client.update_usage_plan(
            usagePlanId=plan_id,
            patchOperations=[
                {"op": "replace", "path": "/throttle/rateLimit",
                 "value": rate_str},
                {"op": "replace", "path": "/throttle/burstLimit",
                 "value": str(burst_limit)},
                {"op": "replace", "path": "/quota/limit",
                 "value": str(quota_limit)},
                {"op": "replace", "path": "/quota/period",
                 "value": quota_period},
            ],
        )
        LOG.info("updated existing Usage Plan id=%s name=%s", plan_id, name)
    else:
        resp = client.create_usage_plan(
            name=name,
            throttle={"rateLimit": rate_limit, "burstLimit": burst_limit},
            quota={"limit": quota_limit, "period": quota_period},
            apiStages=stages,
        )
        plan_id = resp["id"]
        LOG.info("created new Usage Plan id=%s name=%s", plan_id, name)
    return plan_id


def attach_key_to_plan(client, plan_id: str, key_id: str) -> None:
    """No-op if the key is already attached to the plan."""
    resp = client.get_usage_plan_keys(usagePlanId=plan_id)
    if any(k["id"] == key_id for k in resp.get("items", [])):
        LOG.info("key %s already attached to plan %s", key_id, plan_id)
        return
    client.create_usage_plan_key(
        usagePlanId=plan_id, keyId=key_id, keyType="API_KEY"
    )
    LOG.info("attached key %s to plan %s", key_id, plan_id)


# ── main ───────────────────────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-name", default=os.environ.get("API_NAME", "ServerlessCRUD"))
    parser.add_argument("--stage", default=os.environ.get("STAGE_NAME", "prod"))
    parser.add_argument("--key-name", default=os.environ.get("API_KEY_NAME", "usecase2-demo-key"))
    parser.add_argument("--plan-name", default=os.environ.get("USAGE_PLAN_NAME", "usecase2-demo-plan"))
    parser.add_argument("--rate", type=float, default=50.0, help="requests / sec")
    parser.add_argument("--burst", type=int, default=100, help="burst capacity")
    parser.add_argument("--quota", type=int, default=10_000, help="requests / period")
    parser.add_argument("--quota-period", default="DAY",
                        choices=["DAY", "WEEK", "MONTH"])
    parser.add_argument("--region", default=os.environ.get("AWS_REGION", "us-east-1"))
    args = parser.parse_args()

    client = boto3.client("apigateway", region_name=args.region)

    api_id = find_rest_api_id(client, args.api_name)
    LOG.info("found REST API id=%s", api_id)

    key_id = ensure_api_key(client, args.key_name, enabled=True)
    plan_id = ensure_usage_plan(
        client,
        args.plan_name,
        rate_limit=args.rate,
        burst_limit=args.burst,
        quota_limit=args.quota,
        quota_period=args.quota_period,
        stages=[{"apiId": api_id, "stage": args.stage}],
    )
    attach_key_to_plan(client, plan_id, key_id)

    # Surface the key value so the operator can copy it
    key_resp = client.get_api_key(apiKey=key_id, includeValue=True)
    print()
    print("=" * 60)
    print(f"API ID    : {api_id}")
    print(f"STAGE     : {args.stage}")
    print(f"PLAN ID   : {plan_id}")
    print(f"KEY ID    : {key_id}")
    print(f"KEY VALUE : {key_resp['value']}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
