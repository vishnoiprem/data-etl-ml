# L39 — Securing APIs using AWS Cognito Authorizer — Hands On

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 09
> **Duration target:** 14:11
> **Lecture ID:** L39

## Status

Authored. Paired with `code/cognito_setup/`. Assumes the REST API from
section 8 is still deployed; if you tore it down, redeploy L31 first.

## Prereqs

- L38 watched/read end-to-end. You should know the difference between
  User Pool and Identity Pool and the claims API Gateway verifies.
- A deployed REST API with a `GET /items` method (or any method you
  want to protect).
- Python 3.11+, `boto3 >= 1.34`, `moto >= 5`, `requests`.
- IAM permissions to call `cognito-idp:CreateUserPool`,
  `cognito-idp:CreateUserPoolClient`, `cognito-idp:DescribeUserPoolClient`,
  `apigateway:CreateAuthorizer`, `apigateway:UpdateMethod`, and
  `apigateway:CreateDeployment`.

## Key terms

- **`client_credentials` flow** — OAuth 2.0 machine-to-machine flow
  where the client id + client secret are exchanged directly for an
  access token. No user interaction. Perfect for service-to-service.
- **`COGNITO_USER_POOLS`** — the `authorizationType` value for the
  method patch.
- **`USER_PASSWORD_AUTH`** — Cognito's older auth flow. We **do not**
  use it; it is on the deprecation track and SRP is the recommended
  replacement.
- **Hosted UI** — the pre-built Cognito login page. Out of scope for
  this lecture; useful for browser/mobile apps, not for service-to-
  service.

## Lecture

### 1. The plan

```mermaid
flowchart LR
    Client[curl / requests]
    CP[cognito-idp<br/>/oauth2/token]
    APIGW[API Gateway<br/>GET /items<br/>COGNITO_USER_POOLS]
    Int[Integration Lambda<br/>S3 list]
    S3[(items/ in S3)]

    Client -->|client_credentials grant| CP
    CP -->|access_token (JWT)| Client
    Client -->|Authorization: Bearer <jwt>| APIGW
    APIGW -->|verify sig, exp, iss, aud| APIGW
    APIGW -->|invoke + claims| Int
    Int -->|list_objects| S3
```

Steps in order:

1. Create a User Pool.
2. Create an App Client with `client_credentials` enabled and a custom
   scope `read:items`.
3. Attach a resource server to the User Pool so the scope is valid.
4. Wire the User Pool as a `COGNITO_USER_POOLS` authorizer on the API
   method.
5. Redeploy.
6. Mint an access token via the `client_credentials` flow.
7. Call the API with the token and read the claims from the
   integration response.

### 2. Create the User Pool and App Client

`code/cognito_setup/create_user_pool.py`:

```python
"""
Create a Cognito User Pool + App Client for the section 9 hands-on.

Idempotent: re-running with the same USER_POOL_NAME returns the
existing pool's id and client id.

Env vars:
    USER_POOL_NAME  name of the pool. Default: demo-section9-pool
    AWS_REGION      default: us-east-1
"""

from __future__ import annotations

import os
import sys

import boto3

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
    cognito = boto3.client("cognito-idp", region_name=REGION)

    pool_id = _find_existing_pool(cognito, POOL_NAME)
    if pool_id:
        print(f"Reusing existing User Pool: {pool_id}")
    else:
        resp = cognito.create_user_pool(
            PoolName=POOL_NAME,
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

    # Resource server defines the custom OAuth scope.
    cognito.create_resource_server(
        UserPoolId=pool_id,
        Identifier=POOL_NAME,
        Name=POOL_NAME,
        Scopes=[{"ScopeName": SCOPE_NAME, "ScopeDescription": "Read items"}],
    )

    client_id = _find_existing_client(cognito, pool_id)
    if client_id:
        print(f"Reusing existing App Client: {client_id}")
    else:
        resp = cognito.create_user_pool_client(
            UserPoolId=pool_id,
            ClientName=f"{POOL_NAME}-client",
            GenerateSecret=True,
            AllowedOAuthFlows=["client_credentials"],
            AllowedOAuthScopes=[f"{POOL_NAME}/{SCOPE_NAME}"],
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
```

Run it:

```bash
cd 09_api_security_lambda_cognito_auth/code/cognito_setup
pip install -r requirements.txt
python create_user_pool.py
```

It prints `USER_POOL_ID` and `APP_CLIENT_ID`. Save both.

### 3. Offline test (`moto`)

`code/cognito_setup/test_create_user_pool.py`:

```python
"""Offline test for the User Pool + App Client bootstrap."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import boto3
import pytest
from moto import mock_aws

_SPEC = importlib.util.spec_from_file_location(
    "create_user_pool", Path(__file__).parent / "create_user_pool.py"
)
assert _SPEC and _SPEC.loader
mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(mod)


@pytest.fixture
def aws_env(monkeypatch):
    with mock_aws():
        yield boto3.client("cognito-idp", region_name="us-east-1")


def test_creates_pool_and_client(aws_env, capsys, monkeypatch):
    monkeypatch.setenv("USER_POOL_NAME", "test-pool")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    rc = mod.main()
    assert rc == 0

    pools = aws_env.list_user_pools(MaxResults=10)["UserPools"]
    assert any(p["Name"] == "test-pool" for p in pools)

    pool_id = next(p["Id"] for p in pools if p["Name"] == "test-pool")
    clients = aws_env.list_user_pool_clients(UserPoolId=pool_id, MaxResults=10)[
        "UserPoolClients"
    ]
    assert any(c["ClientName"] == "test-pool-client" for c in clients)


def test_idempotent(aws_env, capsys, monkeypatch):
    monkeypatch.setenv("USER_POOL_NAME", "test-pool")
    mod.main()
    mod.main()  # second call must not raise

    pools = aws_env.list_user_pools(MaxResults=10)["UserPools"]
    assert sum(1 for p in pools if p["Name"] == "test-pool") == 1
```

Run:

```bash
pytest -q
```

### 4. Mint an access token (the `client_credentials` flow)

The token endpoint is:

```
POST https://<USER_POOL_DOMAIN>.auth.<region>.amazoncognito.com/oauth2/token
```

You need a domain on the User Pool. Set it up once:

```bash
aws cognito-idp create-user-pool-domain \
  --user-pool-id "$USER_POOL_ID" \
  --domain "demo-section9-$(date +%s)"
```

Then mint a token:

```python
"""Mint a client_credentials access token for the demo pool."""

import base64
import os
import requests

USER_POOL_ID = os.environ["USER_POOL_ID"]
APP_CLIENT_ID = os.environ["APP_CLIENT_ID"]
APP_CLIENT_SECRET = os.environ["APP_CLIENT_SECRET"]
DOMAIN = os.environ["COGNITO_DOMAIN"]  # e.g. demo-section9-1730000000

# Basic auth header.
basic = base64.b64encode(
    f"{APP_CLIENT_ID}:{APP_CLIENT_SECRET}".encode()
).decode()

resp = requests.post(
    f"https://{DOMAIN}.auth.us-east-1.amazoncognito.com/oauth2/token",
    headers={
        "Authorization": f"Basic {basic}",
        "Content-Type": "application/x-www-form-urlencoded",
    },
    data={
        "grant_type": "client_credentials",
        "scope": "demo-section9-pool/read:items",
    },
    timeout=10,
)
resp.raise_for_status()
token = resp.json()["access_token"]
print(token)
```

You can also peek at the JWT body to see the `client_id` and `scope`
claims:

```python
import base64, json
def _decode(jwt):
    body = jwt.split(".")[1]
    body += "=" * (-len(body) % 4)
    return json.loads(base64.urlsafe_b64decode(body))

print(_decode(token))
```

### 5. Wire the User Pool as a `COGNITO_USER_POOLS` authorizer

You can do this from the console, but boto3 is reproducible. Drop
this into a small script:

```python
import os, boto3
from botocore.config import Config

apigw = boto3.client("apigateway", region_name="us-east-1")
API_ID = os.environ["API_ID"]
ITEMS_RESOURCE_ID = os.environ["ITEMS_RESOURCE_ID"]
USER_POOL_ID = os.environ["USER_POOL_ID"]

auth = apigw.create_authorizer(
    restApiId=API_ID,
    name="cognito-pool-authorizer",
    type="COGNITO_USER_POOLS",
    providerARNs=[
        f"arn:aws:cognito-idp:us-east-1:123456789012:userpool/{USER_POOL_ID}"
    ],
    identitySource="method.request.header.Authorization",
    authorizerResultTtlInSeconds=300,
)
print("authorizer id:", auth["id"])

apigw.update_method(
    restApiId=API_ID,
    resourceId=ITEMS_RESOURCE_ID,
    httpMethod="GET",
    patchOperations=[
        {"op": "replace", "path": "/authorizationType", "value": "COGNITO_USER_POOLS"},
        {"op": "replace", "path": "/authorizerId", "value": auth["id"]},
    ],
)
apigw.create_deployment(restApiId=API_ID, stageName="prod")
print("deployed")
```

Replacing the Lambda Authorizer from L37 with this authorizer takes
two minutes — same `update_method` call, different `authorizerId`.

### 6. Call the API

```bash
export API_BASE=https://${API_ID}.execute-api.us-east-1.amazonaws.com/prod
TOKEN=$(python mint_token.py)

# no token
curl -i $API_BASE/items
# 401 Unauthorized

# with token
curl -i -H "Authorization: Bearer $TOKEN" $API_BASE/items
# 200 OK
# body includes a "caller" block echoed from event.requestContext.authorizer.claims
```

A successful response body from the integration Lambda should look
something like:

```json
{
  "items": ["a.txt", "b.txt"],
  "caller": {
    "sub": "<service-principal-uuid>",
    "client_id": "<APP_CLIENT_ID>",
    "scope": "demo-section9-pool/read:items",
    "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_xyz"
  }
}
```

### 7. Scope-down (optional advanced step)

If you want to require a specific scope on a method, switch the
authorizer type to `COGNITO_USER_POOLS` *with* a method-level scope
list. From the console: **Method Request → Settings → OAuth Scopes**.
From boto3: the `update_method` patch includes
`/authorizationScopes`. Concretely:

```python
apigw.update_method(
    restApiId=API_ID,
    resourceId=ITEMS_RESOURCE_ID,
    httpMethod="GET",
    patchOperations=[
        {"op": "add", "path": "/authorizationScopes", "value": "demo-section9-pool/read:items"},
    ],
)
```

Now a token with no `read:items` scope gets `403`, even if it is
otherwise valid.

### 8. Common failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `401 Unauthorized` on every call, including with a valid token | API Gateway cannot reach the JWKS endpoint | Confirm the User Pool has a domain and the `iss` claim matches `https://cognito-idp.<region>.amazonaws.com/<pool-id>` |
| `403 Forbidden` with a valid token | Required scope missing | Add the scope to the App Client's `AllowedOAuthScopes` **and** the method's `authorizationScopes` |
| `Invalid scope` in the token response | Scope name has typos or the resource server was not created | Re-check the `Identifier/ScopeName` pair; must match `<Identifier>/<ScopeName>` |
| Integration sees `claims` as empty | You used `COGNITO_USER_POOLS` for `type` but the `providerARNs` is wrong | The provider ARN is `arn:aws:cognito-idp:<region>:<account>:userpool/<id>` |
| Token works once, then `401` for 5 minutes | Cache hit on an older token; rotate by deploying a new stage or invalidating via the API Gateway console | Production: design with short TTL + refresh token flow |

### 9. Cleanup

```bash
aws cognito-idp delete-user-pool --user-pool-id "$USER_POOL_ID"
# authorizer detached by deleting the API stack, or explicitly:
aws apigateway delete-authorizer --rest-api-id "$API_ID" --authorizer-id "$AUTHORIZER_ID"
```

## Hands-on summary

You have now protected a REST API with both flavors of authorizer. The
mental model to keep:

- **Cognito User Pool Authorizer** = OIDC JWT validation, zero code,
  best when the IdP is Cognito.
- **Lambda Authorizer** = programmable policy generation, best when
  you need to call out to custom logic or use a non-OIDC token.

In production you will often see both: a Lambda authorizer chains on
top of Cognito to add per-tenant policy logic, or replaces Cognito
entirely to integrate with an enterprise IdP.

## Quiz prep

- What three claims does the Cognito User Pool Authorizer enforce on
  the incoming JWT?
- How do you scope a method to require a specific OAuth scope?
- What is the difference between `cognito:groups` and an OAuth scope
  for authorization purposes?
- Why is `client_credentials` appropriate for service-to-service
  calls but not for a logged-in user?

## Further reading

- AWS Docs — [Cognito User Pool app client](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-client-apps.html)
- AWS Docs — [OAuth 2.0 client credentials grant](https://docs.aws.amazon.com/cognito/latest/developerguide/token-endpoint.html)
- IETF — RFC 6749 §4.4 (Client Credentials Grant)
