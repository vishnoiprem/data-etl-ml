"""Flip API Key Required to true on both /public/{proxy+} and /internal/{proxy+}.

Reuses the resource ids that API Gateway already has. We do not need
to redeploy anything except the stage.

Env vars:
    API_ID    the REST API id (printed by api_setup.py)
    AWS_REGION default: us-east-1
"""

from __future__ import annotations

import os

import boto3


REGION = os.environ.get("AWS_REGION", "us-east-1")
API_ID = os.environ["API_ID"]


def _client():
    return boto3.client("apigateway", region_name=REGION)


def _resource_id_by_path(path: str) -> str:
    apigw = _client()
    for r in apigw.get_resources(restApiId=API_ID)["items"]:
        if r.get("path") == path:
            return r["id"]
    raise RuntimeError(f"resource {path!r} not found")


def _set_key_required(resource_id: str, method: str) -> None:
    apigw = _client()
    apigw.update_method(
        restApiId=API_ID,
        resourceId=resource_id,
        httpMethod=method,
        patchOperations=[
            {"op": "replace", "path": "/apiKeyRequired", "value": "true"},
        ],
    )


def main() -> int:
    apigw = _client()
    public_proxy = _resource_id_by_path("/public/{proxy+}")
    internal_proxy = _resource_id_by_path("/internal/{proxy+}")
    for rid in (public_proxy, internal_proxy):
        for method in ("GET", "PUT"):
            _set_key_required(rid, method)
            print(f"apiKeyRequired=true on {rid} {method}")

    apigw.create_deployment(restApiId=API_ID, stageName="prod")
    print("redeployed prod")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
