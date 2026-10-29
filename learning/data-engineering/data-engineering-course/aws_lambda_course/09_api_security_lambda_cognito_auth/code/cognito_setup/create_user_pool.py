"""
Create a Cognito User Pool + App Client for the section 9 hands-on.

Idempotent: re-running with the same USER_POOL_NAME returns the
existing pool's id and client id.

Env vars:
    USER_POOL_NAME   name of the pool. Default: demo-section9-pool
    AWS_REGION       default: us-east-1
"""

from __future__ import annotations

import os
import sys

import boto3
from botocore.exceptions import ClientError

REGION = os.environ.get("AWS_REGION", "us-east-1")
POOL_NAME = os.environ.get("USER_POOL_NAME", "demo-section9-pool")
SCOPE_NAME = "read:items"


def _find_existing_pool(cognito, name: str) -> str | None:
    paginator = cognito.get_paginator("list_user_pools")
    for page in paginator.paginate(MaxResults=60):
        for pool in page["UserPools"]:
            if pool["Name"] == name:
                return pool["Id"]
    return None


def _find_existing_client(cognito, pool_id: str) -> str | None:
    paginator = cognito.get_paginator("list_user_pool_clients")
    for page in paginator.paginate(UserPoolId=pool_id, MaxResults=60):
        for client in page["UserPoolClients"]:
            if client["ClientName"] == f"{POOL_NAME}-client":
                return client["ClientId"]
    return None


def main() -> int:
    # Re-read env on every call so tests can override USER_POOL_NAME via
    # monkeypatch.setenv() between invocations.
    region = os.environ.get("AWS_REGION", "us-east-1")
    pool_name = os.environ.get("USER_POOL_NAME", "demo-section9-pool")
    cognito = boto3.client("cognito-idp", region_name=region)

    pool_id = _find_existing_pool(cognito, pool_name)
    if pool_id:
        print(f"Reusing existing User Pool: {pool_id}")
    else:
        resp = cognito.create_user_pool(
            PoolName=pool_name,
            AutoVerifiedAttributes=["email"],
            UsernameAttributes=["email"],
            Policies={
                "PasswordPolicy": {
                    "MinimumLength": 8,
                    "RequireUppercase": False,
                    "RequireLowercase": False,
                    "RequireNumbers": False,
                    "RequireSymbols": False,
                }
            },
        )
        pool_id = resp["UserPool"]["Id"]
        print(f"Created User Pool: {pool_id}")

    # Resource server defines the custom OAuth scope. Idempotent:
    # if it already exists, the call raises and we swallow it. The exact
    # exception class varies by botocore version (some emit
    # `ResourceExistsException`, others `InvalidParameterException` for a
    # duplicate identifier, and moto historically returns nothing at all),
    # so we catch a broad ClientError and look at the error code.
    try:
        cognito.create_resource_server(
            UserPoolId=pool_id,
            Identifier=pool_name,
            Name=pool_name,
            Scopes=[{"ScopeName": SCOPE_NAME, "ScopeDescription": "Read items"}],
        )
        print("Created resource server.")
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in {"ResourceExistsException", "InvalidParameterException"}:
            print(f"Resource server already exists (code={code}).")
        else:
            raise

    client_id = _find_existing_client(cognito, pool_id)
    if client_id:
        print(f"Reusing existing App Client: {client_id}")
    else:
        resp = cognito.create_user_pool_client(
            UserPoolId=pool_id,
            ClientName=f"{pool_name}-client",
            GenerateSecret=True,
            AllowedOAuthFlows=["client_credentials"],
            AllowedOAuthScopes=[f"{pool_name}/{SCOPE_NAME}"],
            AllowedOAuthFlowsUserPoolClient=True,
            SupportedIdentityProviders=["COGNITO"],
        )
        client_id = resp["UserPoolClient"]["ClientId"]
        print(f"Created App Client: {client_id}")

    print("\nSet these as environment variables for the next steps:")
    print(f"  export USER_POOL_ID={pool_id}")
    print(f"  export APP_CLIENT_ID={client_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
