"""Idempotently create an API Key and two Usage Plans for the Bedrock API.

This script wires up the L44a lecture: one API key attached to two
usage plans (one for the `dev` stage, one for the `prod` stage) of
the `bedrock-defect-api` REST API from L45. Run it once and the
key + plans are in place; run it again and the existing resources
are updated in place.

Usage:
    export AWS_REGION=us-east-1
    python create_api_key.py

Override defaults with flags, e.g.
    python create_api_key.py --prod-rate 5 --prod-quota 50000

Required IAM permissions (least-privilege):
    apigateway:GET
    apigateway:POST
    apigateway:PATCH
on resource arn:aws:apigateway:*::/*.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import Optional

import boto3
from botocore.exceptions import ClientError

LOG = logging.getLogger("bedrock.apikeys")
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


def stage_exists(client, api_id: str, stage_name: str) -> bool:
    """Return True if the stage has been deployed to the API."""
    try:
        client.get_stage(restApiId=api_id, stageName=stage_name)
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "NotFoundException":
            return False
        raise
    return True


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
                        {
                            "op": "replace",
                            "path": "/enabled",
                            "value": str(enabled).lower(),
                        }
                    ],
                )
                LOG.info("reusing existing API Key id=%s name=%s", k["id"], name)
                return k["id"]

    params = {"name": name, "enabled": enabled}
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
        client.update_usage_plan(
            usagePlanId=plan_id,
            patchOperations=[
                {"op": "replace", "path": "/throttle/rateLimit", "value": str(rate_limit)},
                {"op": "replace", "path": "/throttle/burstLimit", "value": str(burst_limit)},
                {"op": "replace", "path": "/quota/limit", "value": str(quota_limit)},
                {"op": "replace", "path": "/quota/period", "value": quota_period},
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
    """No-op if the key is already attached."""
    resp = client.get_usage_plan_keys(usagePlanId=plan_id)
    if any(k["id"] == key_id for k in resp.get("items", [])):
        LOG.info("key %s already attached to plan %s", key_id, plan_id)
        return
    client.create_usage_plan_key(
        usagePlanId=plan_id, keyId=key_id, keyType="API_KEY"
    )
    LOG.info("attached key %s to plan %s", key_id, plan_id)


# ── main ───────────────────────────────────────────────────────────────
def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create / update the API Key + dev & prod Usage Plans "
                    "for the Bedrock defect-summarizer REST API."
    )
    parser.add_argument("--api-name", default=os.environ.get("API_NAME", "bedrock-defect-api"))
    parser.add_argument("--key-name", default=os.environ.get("API_KEY_NAME", "defect-api-key"))
    parser.add_argument(
        "--dev-plan-name",
        default=os.environ.get("DEV_PLAN_NAME", "defect-api-dev"),
    )
    parser.add_argument(
        "--prod-plan-name",
        default=os.environ.get("PROD_PLAN_NAME", "defect-api-prod"),
    )
    parser.add_argument("--dev-stage", default=os.environ.get("DEV_STAGE", "dev"))
    parser.add_argument("--prod-stage", default=os.environ.get("PROD_STAGE", "prod"))

    # dev defaults: loose limits for CI / load tests
    parser.add_argument("--dev-rate", type=float, default=100.0, help="dev: requests / sec")
    parser.add_argument("--dev-burst", type=int, default=200, help="dev: burst capacity")
    parser.add_argument("--dev-quota", type=int, default=1_000_000, help="dev: requests / period")
    parser.add_argument("--dev-quota-period", default="DAY", choices=["DAY", "WEEK", "MONTH"])

    # prod defaults: tight limits to bound Bedrock cost
    parser.add_argument("--prod-rate", type=float, default=10.0, help="prod: requests / sec")
    parser.add_argument("--prod-burst", type=int, default=50, help="prod: burst capacity")
    parser.add_argument("--prod-quota", type=int, default=100_000, help="prod: requests / period")
    parser.add_argument("--prod-quota-period", default="DAY", choices=["DAY", "WEEK", "MONTH"])

    args = parser.parse_args(argv)

    region = os.environ.get("AWS_REGION", "us-east-1")
    client = boto3.client("apigateway", region_name=region)

    api_id = find_rest_api_id(client, args.api_name)
    LOG.info("found REST API id=%s name=%s", api_id, args.api_name)

    # We allow either or both stages to be missing — the script still
    # creates the plans and the key; the operator can deploy later.
    dev_deployed = stage_exists(client, api_id, args.dev_stage)
    prod_deployed = stage_exists(client, api_id, args.prod_stage)
    LOG.info(
        "stages: %s=%s %s=%s",
        args.dev_stage, "deployed" if dev_deployed else "missing",
        args.prod_stage, "deployed" if prod_deployed else "missing",
    )
    if not dev_deployed and not prod_deployed:
        LOG.warning(
            "neither stage is deployed; the plans will exist but no "
            "throttling will be active until a deploy happens."
        )

    dev_stages = [{"apiId": api_id, "stage": args.dev_stage}] if dev_deployed else []
    prod_stages = [{"apiId": api_id, "stage": args.prod_stage}] if prod_deployed else []

    key_id = ensure_api_key(client, args.key_name, enabled=True)

    dev_plan_id = ensure_usage_plan(
        client,
        args.dev_plan_name,
        rate_limit=args.dev_rate,
        burst_limit=args.dev_burst,
        quota_limit=args.dev_quota,
        quota_period=args.dev_quota_period,
        stages=dev_stages,
    )
    prod_plan_id = ensure_usage_plan(
        client,
        args.prod_plan_name,
        rate_limit=args.prod_rate,
        burst_limit=args.prod_burst,
        quota_limit=args.prod_quota,
        quota_period=args.prod_quota_period,
        stages=prod_stages,
    )

    if dev_deployed:
        attach_key_to_plan(client, dev_plan_id, key_id)
    if prod_deployed:
        attach_key_to_plan(client, prod_plan_id, key_id)

    key_resp = client.get_api_key(apiKey=key_id, includeValue=True)

    print()
    print("=" * 64)
    print(f"API ID      : {api_id}")
    print(f"DEV PLAN    : {dev_plan_id}  ({args.dev_rate} rps, {args.dev_quota} / {args.dev_quota_period})")
    print(f"PROD PLAN   : {prod_plan_id}  ({args.prod_rate} rps, {args.prod_quota} / {args.prod_quota_period})")
    print(f"KEY ID      : {key_id}")
    print(f"KEY VALUE   : {key_resp['value']}")
    print("=" * 64)
    print()
    print("Next step: in the API Gateway console set 'API Key Required = true'")
    print("on the POST /defects method and redeploy the prod stage.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
