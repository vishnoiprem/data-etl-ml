---
lecture: L17
title: "Cognito User Pool Authorizer on HTTP APIs (JWT)"
duration: "18:00"
section: 4
prereqs:
  - L16
---

# L17 — Cognito User Pool Authorizer on HTTP APIs (JWT)

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 4 — API Gateway + Cognito Authorizer
> **Duration:** 18:00

## Prereqs

- Watched **L16 — REST API authorizer**.

## Key terms

- **HTTP API** — the newer, faster, cheaper API Gateway flavor.
  Optimized for the common case; missing some REST API features.
- **JWT Authorizer** — HTTP API's name for a token-validation
  authorizer. Equivalent to REST API's Cognito User Pool Authorizer,
  but **accepts tokens issued by any OIDC provider** (not just
  Cognito).
- **`jwt.AuthorizerConfiguration`** — the boto3 argument that
  configures a JWT authorizer. Includes `JwtConfiguration` (issuer,
  audience) and `IdentitySource` (header name).
- **Audience** — the value API Gateway checks in the token's `aud`
  claim. For Cognito, this is the App Client ID.
- **`AuthorizerPayloadFormatVersion`** — `2.0` for JWT authorizers.

## Lecture

HTTP APIs are the newer, faster, cheaper cousin of REST APIs. They
don't have a "Cognito User Pool Authorizer" per se — they have a
**JWT Authorizer** that accepts tokens from **any** OIDC provider
(including Cognito). By the end of this lecture you'll be able to
stand up a JWT-protected HTTP API in a few lines of boto3.

### The 4-step recipe

1. **Create the HTTP API.**
2. **Create the JWT authorizer.**
3. **Create a route and integration.**
4. **Deploy (automatic for HTTP APIs).**

### Step 1 — Create the HTTP API

```python
apigwv2 = boto3.client("apigatewayv2", region_name="us-east-1")
api = apigwv2.create_api(
    Name="cognito-demo-http",
    ProtocolType="HTTP",
    Description="Demo HTTP API secured by Cognito",
)
api_id = api["ApiId"]
```

`apigatewayv2` is the boto3 client for HTTP APIs and WebSocket APIs.
REST APIs use the `apigateway` client. The two are separate.

### Step 2 — Create the JWT authorizer

```python
issuer = f"https://cognito-idp.us-east-1.amazonaws.com/{user_pool_id}"

authorizer = apigwv2.create_authorizer(
    ApiId=api_id,
    AuthorizerType="JWT",
    Name="cognito-jwt-authorizer",
    IdentitySource=["$request.header.Authorization"],
    JwtConfiguration={
        "Issuer": issuer,
        "Audience": [app_client_id],  # the App Client ID, not the pool ID
    },
    AuthorizerPayloadFormatVersion="2.0",
)
authorizer_id = authorizer["AuthorizerId"]
```

Two important details:

- **`Audience`** is the App Client ID, not the pool ID.
- **`Issuer`** is the **exact** issuer URL the pool uses. Get it from
  the OIDC discovery document at
  `https://cognito-idp.<region>.amazonaws.com/<pool-id>/.well-known/openid-configuration`.

### Step 3 — Create a route and integration

```python
# Lambda integration (or use a mock integration by creating
# an HTTP integration pointing at a fixed URL)
integration = apigwv2.create_integration(
    ApiId=api_id,
    IntegrationType="AWS_PROXY",
    IntegrationUri=f"arn:aws:lambda:us-east-1:123456789012:function:my-backend",
    PayloadFormatVersion="2.0",
)

apigwv2.create_route(
    ApiId=api_id,
    RouteKey="GET /items",
    Target=f"integrations/{integration['IntegrationId']}",
    AuthorizationType="JWT",          # ← require the JWT authorizer
    AuthorizerId=authorizer_id,
)
```

Note the difference: HTTP APIs use `AuthorizationType="JWT"` (not
`COGNITO_USER_POOLS`).

### Step 4 — Auto-deploy

HTTP APIs auto-deploy by default. You just need a stage:

```python
apigwv2.create_stage(
    ApiId=api_id,
    StageName="$default",
    AutoDeploy=True,
)
invoke_url = f"https://{api_id}.execute-api.us-east-1.amazonaws.com"
```

### The request context in HTTP APIs

On a successful authorization, your Lambda receives:

```json
{
  "requestContext": {
    "authorizer": {
      "jwt": {
        "claims": {
          "sub": "505c1bfa-...",
          "email": "alice@example.com",
          "cognito:groups": ["admins"]
        },
        "scopes": ["openid", "email"]
      }
    }
  }
}
```

Note: `cognito:groups` is **a single string with a comma-separated
list**, not a JSON array, in HTTP APIs. REST APIs put it in
`x-amzn-oidc-cognito_groups` as a comma-separated string. The shape
is the same; just the path through the event is different.

### Scope enforcement

To require a specific scope (e.g. `https://api.example.com/read:items`)
on an HTTP API route, set `AuthorizationScopes` on `create_route`:

```python
apigwv2.create_route(
    ApiId=api_id,
    RouteKey="GET /items",
    Target=f"integrations/{integration['IntegrationId']}",
    AuthorizationType="JWT",
    AuthorizerId=authorizer_id,
    AuthorizationScopes=["https://api.example.com/read:items"],  # ← require scope
)
```

API Gateway rejects any request whose token doesn't have that scope
in its `scope` claim.

### REST vs HTTP — quick comparison

| | REST API | HTTP API |
|---|---|---|
| Client namespace | `boto3.client("apigateway")` | `boto3.client("apigatewayv2")` |
| Authorizer type string | `COGNITO_USER_POOLS` | `JWT` |
| Audience field | Set in the authorizer config | Set in `JwtConfiguration.Audience` |
| Scopes | `AuthorizationScopes` on `put_method` | `AuthorizationScopes` on `create_route` |
| Claims in Lambda event | `requestContext.authorizer.claims` | `requestContext.authorizer.jwt.claims` |
| Latency | ~30ms | ~10ms |
| Cost per million | $3.50 | $1.00 |

If you're starting fresh, **start with HTTP APIs**. Switch to REST
only if you need a feature HTTP doesn't have (request validation,
usage plans, OpenAPI export of authorizer config).

### What's coming

L18 — scopes and groups, in detail. The most important lecture for
production authorization.