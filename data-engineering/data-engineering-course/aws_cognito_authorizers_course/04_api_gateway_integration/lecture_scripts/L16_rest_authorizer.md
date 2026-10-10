---
lecture: L16
title: "Cognito User Pool Authorizer on REST APIs"
duration: "18:00"
section: 4
prereqs:
  - L15
---

# L16 — Cognito User Pool Authorizer on REST APIs

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 4 — API Gateway + Cognito Authorizer
> **Duration:** 18:00

## Prereqs

- Watched **L15 — Section Overview**.
- A working User Pool from L10. You need `USER_POOL_ID` and
  `APP_CLIENT_ID`.

## Key terms

- **`COGNITO_USER_POOLS` authorizer** — the REST API's built-in
  authorizer for Cognito-issued JWTs. Created with
  `create_authorizer(Type="COGNITO_USER_POOLS", ...)`.
- **Identity source** — the request field the authorizer reads the
  token from. Default: `method.request.header.Authorization`.
- **Authorizer result TTL** — how long API Gateway caches the
  authorizer's decision (in seconds). Default: 300 (5 min).
- **Method setting `AuthorizationType`** — set to `COGNITO_USER_POOLS`
  to require the authorizer on a specific method.
- **`x-amzn-oidc-*` headers** — the headers API Gateway forwards to
  your Lambda on the way to the backend. They contain the claims.

## Lecture

Welcome back. Today we wire a Cognito User Pool Authorizer to a REST
API with boto3. By the end of this lecture you'll have a working
recipe that you can adapt to any REST API.

### The 5-step recipe

1. **Create the REST API.**
2. **Create the authorizer** (`Type="COGNITO_USER_POOLS"`,
   `IdentitySource="method.request.header.Authorization"`).
3. **Create a resource and method.**
4. **Set the method's `AuthorizationType`** to `COGNITO_USER_POOLS`
   and pick the authorizer.
5. **Deploy to a stage.**

Let's walk through each step.

### Step 1 — Create the REST API

```python
apigw = boto3.client("apigateway", region_name="us-east-1")
api = apigw.create_rest_api(
    Name="cognito-demo",
    Description="Demo REST API secured by Cognito",
    EndpointConfiguration={"Types": ["REGIONAL"]},
)
api_id = api["id"]
# Get the root resource id (always "/" with id matching the API id)
resources = apigw.get_resources(restApiId=api_id)
root_id = next(r["id"] for r in resources["items"] if r["path"] == "/")
```

### Step 2 — Create the authorizer

```python
authorizer = apigw.create_authorizer(
    restApiId=api_id,
    name="cognito-user-pool-authorizer",
    Type="COGNITO_USER_POOLS",
    ProviderARNs=[f"arn:aws:cognito-idp:us-east-1:123456789012:userpool/{user_pool_id}"],
    IdentitySource="method.request.header.Authorization",
    # Caching is optional but recommended in production
    AuthorizerResultTtlInSeconds=300,
)
authorizer_id = authorizer["id"]
```

`ProviderARNs` accepts one or more user pool ARNs. If you have a
single User Pool, this is a one-element list.

### Step 3 — Create a resource and method

```python
# Create /items resource
resource = apigw.create_resource(
    restApiId=api_id,
    parentId=root_id,
    pathPart="items",
)
items_id = resource["id"]

# Mock integration that returns {"items": ["alpha", "beta"]}
apigw.put_method(
    restApiId=api_id,
    resourceId=items_id,
    httpMethod="GET",
    authorizationType="COGNITO_USER_POOLS",  # ← require the authorizer
    authorizerId=authorizer_id,
)
apigw.put_integration(
    restApiId=api_id,
    resourceId=items_id,
    httpMethod="GET",
    type="MOCK",
    requestTemplates={
        "application/json": '{"statusCode": 200}'
    },
)
apigw.put_method_response(
    restApiId=api_id,
    resourceId=items_id,
    httpMethod="GET",
    statusCode="200",
)
apigw.put_integration_response(
    restApiId=api_id,
    resourceId=items_id,
    httpMethod="GET",
    statusCode="200",
    responseTemplates={
        "application/json": '{"items": ["alpha", "beta"]}'
    },
)
```

The mock integration is a stand-in for a Lambda or HTTP backend. In
the course we use it so we can test the authorizer without a real
backend. In production you'd swap `type="MOCK"` for
`type="AWS_PROXY"` + a Lambda URI.

### Step 4 — Deploy

```python
deployment = apigw.create_deployment(
    restApiId=api_id,
    stageName="v1",
)
invoke_url = f"https://{api_id}.execute-api.us-east-1.amazonaws.com/v1"
```

### Step 5 — Test

Three test cases, all with curl:

```bash
# 1. No token → 401 Unauthorized
curl -i https://$API_ID.execute-api.us-east-1.amazonaws.com/v1/items

# 2. Bad token → 401 Unauthorized
curl -i -H "Authorization: Bearer not-a-jwt" \
    https://$API_ID.execute-api.us-east-1.amazonaws.com/v1/items

# 3. Good token → 200 OK with body
TOKEN=$(python3 -c "
import boto3, json
c = boto3.client('cognito-idp', region_name='us-east-1')
r = c.initiate_auth(
    AuthFlow='USER_PASSWORD_AUTH',
    ClientId='$APP_CLIENT_ID',
    AuthParameters={'USERNAME':'alice@example.com','PASSWORD':'TempPass!2026'},
)
print(r['AuthenticationResult']['AccessToken'])
")
curl -i -H "Authorization: Bearer $TOKEN" \
    https://$API_ID.execute-api.us-east-1.amazonaws.com/v1/items
```

The first two should return 401 with a `WWW-Authenticate: Bearer`
header. The third should return 200 with `{"items": ["alpha", "beta"]}`.

### What API Gateway puts in the request context

On a successful authorization, API Gateway forwards these headers
to your backend Lambda:

| Header | Value |
|---|---|
| `x-amzn-oidc-acct` | The account ID |
| `x-amzn-oidc-sub` | The user's `sub` (Cognito user UUID) |
| `x-amzn-oidc-iss` | The issuer URL |
| `x-amzn-oidc-client_id` | The App Client ID |
| `x-amzn-oidc-token_use` | `id` or `access` |
| `x-amzn-oidc-auth_time` | The last auth time, epoch seconds |
| `x-amzn-oidc-exp` | Token expiry, epoch seconds |
| `x-amzn-oidc-email` | Email claim (if present) |
| `x-amzn-oidc-cognito_groups` | Comma-separated groups (REST) |
| `x-amzn-oidc-custom_<name>` | Custom claims prefixed with `custom_` |

In your Lambda:

```python
def handler(event, context):
    claims = event.request_context.authorizer.claims
    sub = claims["sub"]
    email = claims.get("email")
    groups = claims.get("cognito:groups", "")
    # ... do your AuthZ check ...
```

For HTTP APIs the shape is slightly different:
`event.request_context.authorizer.jwt.claims` is where the claims
live.

### Caching

By default API Gateway caches the authorizer's decision for **5
minutes**. If you revoke a user's session, the cache still considers
them authorized for up to 5 minutes. For sensitive endpoints, set
`AuthorizerResultTtlInSeconds=0` to disable caching.

For a public API where thousands of users hit the same endpoint per
minute, **leave the default**. The performance win is significant.

### The "no scope yet" gotcha

A REST API authorizer with `Type="COGNITO_USER_POOLS"` validates the
JWT but does **not** enforce scopes. To require a scope (e.g.
`openid`) on a method, set `AuthorizationScopes=["openid"]` on
`put_method`. API Gateway will then reject any request whose token
doesn't have the scope.

We cover this in detail in L18.

### What's coming

L17 — the same pattern on HTTP APIs. L18 — scopes and groups.
L19 — the JWT validation algorithm in depth.