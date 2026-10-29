"""Stand up the secured Use Case 2 REST API end-to-end.

The script:

1. Creates (or reuses) a REST API named API_NAME.
2. Creates (or reuses) a /public and /internal parent resource.
3. Creates (or reuses) a /public/{proxy+} and /internal/{proxy+}
   child resource under each.
4. Attaches a Lambda Authorizer to /internal/{proxy+}.
5. Attaches a Cognito User Pool Authorizer to /public/{proxy+}.
6. Wires both routes to the same integration Lambda
   (usecase2_with_auth.lambda_handler).
7. Deploys the API to STAGE_NAME.

Idempotent: re-running with the same API_NAME returns the existing
ids and reuses them. Safe to run from CI.

Env vars:
    API_NAME          default: usecase2-secure
    STAGE_NAME        default: prod
    BUCKET_NAME       default: usecase2-objects
    LAMBDA_ARN        the integration Lambda ARN (required)
    AUTHORIZER_ARN    the Lambda Authorizer function ARN (required)
    USER_POOL_ARN     the Cognito User Pool ARN (required)
    AWS_REGION        default: us-east-1
"""

from __future__ import annotations

import os
from typing import Dict, Optional

import boto3
from botocore.exceptions import ClientError


REGION = os.environ.get("AWS_REGION", "us-east-1")
API_NAME = os.environ.get("API_NAME", "usecase2-secure")
STAGE_NAME = os.environ.get("STAGE_NAME", "prod")


# ── small helpers ──────────────────────────────────────────────────────
def _client():
    return boto3.client("apigateway", region_name=REGION)


def _find_or_create_api() -> str:
    apigw = _client()
    paginator = apigw.get_paginator("get_rest_apis")
    for page in paginator.paginate():
        for api in page["items"]:
            if api["name"] == API_NAME:
                return api["id"]
    return apigw.create_rest_api(
        name=API_NAME, endpointConfiguration={"types": ["REGIONAL"]},
    )["id"]


def _get_root(api_id: str) -> str:
    apigw = _client()
    for r in apigw.get_resources(restApiId=api_id)["items"]:
        if r.get("path") == "/" and r.get("parentId") is None:
            return r["id"]
    raise RuntimeError("root resource not found")


def _find_child(api_id: str, parent_id: str, path_part: str) -> Optional[str]:
    apigw = _client()
    paginator = apigw.get_paginator("get_resources")
    for page in paginator.paginate(restApiId=api_id):
        for r in page["items"]:
            if r.get("pathPart") == path_part and r.get("parentId") == parent_id:
                return r["id"]
    return None


def _ensure_resource(api_id: str, parent_id: str, path_part: str) -> str:
    apigw = _client()
    existing = _find_child(api_id, parent_id, path_part)
    if existing:
        return existing
    return apigw.create_resource(
        restApiId=api_id, parentId=parent_id, pathPart=path_part,
    )["id"]


def _ensure_proxy_child(api_id: str, parent_id: str) -> str:
    return _ensure_resource(api_id, parent_id, "{proxy+}")


def _lambda_uri(function_arn: str) -> str:
    return (
        f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31"
        f"/functions/{function_arn}/invocations"
    )


def _ensure_method(
    api_id: str, resource_id: str, method: str, lambda_uri: str,
    authorizer_id: Optional[str] = None,
    api_key_required: bool = False,
) -> None:
    apigw = _client()
    kwargs: Dict[str, object] = {
        "restApiId": api_id,
        "resourceId": resource_id,
        "httpMethod": method,
        "authorizationType": "CUSTOM" if authorizer_id else "NONE",
        "apiKeyRequired": api_key_required,
    }
    if authorizer_id:
        kwargs["authorizerId"] = authorizer_id
    try:
        apigw.put_method(**kwargs)
    except ClientError as exc:
        if exc.response["Error"]["Code"] != "ConflictException":
            raise


def _ensure_integration(
    api_id: str, resource_id: str, method: str, lambda_uri: str,
) -> None:
    apigw = _client()
    try:
        apigw.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=method,
            type="AWS_PROXY",
            integrationHttpMethod="POST",
            uri=lambda_uri,
        )
    except ClientError as exc:
        if exc.response["Error"]["Code"] != "ConflictException":
            raise


def _ensure_lambda_authorizer(
    api_id: str, function_arn: str, name: str = "usecase2-token-authorizer",
) -> str:
    apigw = _client()
    paginator = apigw.get_paginator("get_authorizers")
    for page in paginator.paginate(restApiId=api_id):
        for a in page["items"]:
            if a["name"] == name:
                return a["id"]
    return apigw.create_authorizer(
        restApiId=api_id,
        name=name,
        type="TOKEN",
        authorizerUri=_lambda_uri(function_arn),
        identitySource="method.request.header.Authorization",
        authorizerResultTtlInSeconds=300,
    )["id"]


def _ensure_cognito_authorizer(
    api_id: str, user_pool_arn: str, name: str = "usecase2-cognito-authorizer",
) -> str:
    apigw = _client()
    paginator = apigw.get_paginator("get_authorizers")
    for page in paginator.paginate(restApiId=api_id):
        for a in page["items"]:
            if a["name"] == name:
                return a["id"]
    return apigw.create_authorizer(
        restApiId=api_id,
        name=name,
        type="COGNITO_USER_POOLS",
        providerARNs=[user_pool_arn],
        identitySource="method.request.header.Authorization",
        authorizerResultTtlInSeconds=300,
    )["id"]


# ── main ───────────────────────────────────────────────────────────────
def main() -> int:
    apigw = _client()
    api_id = _find_or_create_api()
    print(f"API: {api_id}")

    root_id = _get_root(api_id)
    public_id = _ensure_resource(api_id, root_id, "public")
    internal_id = _ensure_resource(api_id, root_id, "internal")
    public_proxy_id = _ensure_proxy_child(api_id, public_id)
    internal_proxy_id = _ensure_proxy_child(api_id, internal_id)

    lambda_arn = os.environ["LAMBDA_ARN"]
    lambda_uri = _lambda_uri(lambda_arn)

    # Internal route — Lambda Authorizer.
    lambda_auth_id = _ensure_lambda_authorizer(
        api_id, os.environ["AUTHORIZER_ARN"],
    )
    for method in ("GET", "PUT"):
        _ensure_method(
            api_id, internal_proxy_id, method, lambda_uri, lambda_auth_id,
        )
        _ensure_integration(api_id, internal_proxy_id, method, lambda_uri)
    print(f"Lambda authorizer on /internal/*: {lambda_auth_id}")

    # Public route — Cognito User Pool Authorizer.
    cognito_auth_id = _ensure_cognito_authorizer(
        api_id, os.environ["USER_POOL_ARN"],
    )
    for method in ("GET", "PUT"):
        _ensure_method(
            api_id, public_proxy_id, method, lambda_uri, cognito_auth_id,
        )
        _ensure_integration(api_id, public_proxy_id, method, lambda_uri)
    print(f"Cognito authorizer on /public/*: {cognito_auth_id}")

    apigw.create_deployment(restApiId=api_id, stageName=STAGE_NAME)
    print(f"Deployed to {STAGE_NAME}")

    print()
    print("=" * 60)
    print(f"API_ID              : {api_id}")
    print(f"PUBLIC_PROXY_ID     : {public_proxy_id}")
    print(f"INTERNAL_PROXY_ID   : {internal_proxy_id}")
    print(f"LAMBDA_AUTH_ID      : {lambda_auth_id}")
    print(f"COGNITO_AUTH_ID     : {cognito_auth_id}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
