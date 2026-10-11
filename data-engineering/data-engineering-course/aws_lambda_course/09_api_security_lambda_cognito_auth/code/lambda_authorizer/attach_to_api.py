"""Attach the demo-lambda-authorizer to GET /items on the demo REST API.

Required env vars:
    API_ID                 REST API id
    ITEMS_RESOURCE_ID      resource id for the /items path
    AUTHORIZER_LAMBDA_ARN  full ARN of the authorizer Lambda function
    AWS_REGION             default us-east-1
"""

from __future__ import annotations

import os
import sys

import boto3

REGION = os.environ.get("AWS_REGION", "us-east-1")
API_ID = os.environ["API_ID"]
ITEMS_RESOURCE_ID = os.environ["ITEMS_RESOURCE_ID"]
AUTHORIZER_LAMBDA_ARN = os.environ["AUTHORIZER_LAMBDA_ARN"]
AUTHORIZER_NAME = os.environ.get("AUTHORIZER_NAME", "demo-token-authorizer")


def main() -> int:
    apigw = boto3.client("apigateway", region_name=REGION)

    authorizer_uri = (
        f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/"
        f"functions/{AUTHORIZER_LAMBDA_ARN}/invocations"
    )

    auth = apigw.create_authorizer(
        restApiId=API_ID,
        name=AUTHORIZER_NAME,
        type="TOKEN",
        authorizerUri=authorizer_uri,
        identitySource="method.request.header.Authorization",
        authorizerResultTtlInSeconds=300,
    )
    authorizer_id = auth["id"]
    print(f"Authorizer created: {authorizer_id}")

    apigw.update_method(
        restApiId=API_ID,
        resourceId=ITEMS_RESOURCE_ID,
        httpMethod="GET",
        patchOperations=[
            {"op": "replace", "path": "/authorizationType", "value": "CUSTOM"},
            {"op": "replace", "path": "/authorizerId", "value": authorizer_id},
        ],
    )
    print("GET /items now requires the authorizer.")

    apigw.create_deployment(restApiId=API_ID, stageName="prod")
    print("Deployed to prod.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
