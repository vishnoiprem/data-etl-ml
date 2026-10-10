---
lecture: L18
title: "Scopes, Groups & Fine-Grained Authorization"
duration: "16:00"
section: 4
prereqs:
  - L17
---

# L18 — Scopes, Groups & Fine-Grained Authorization

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 4 — API Gateway + Cognito Authorizer
> **Duration:** 16:00

## Prereqs

- Watched **L16 + L17** (REST + HTTP authorizer).

## Key terms

- **Scope** — a string the client requests at sign-in time and that
  appears in the access token's `scope` claim. Cognito scopes are
  namespaced: `<resource-server-id>/<scope-name>`.
- **Group** — a Cognito User Pool container of users. Members appear
  in the ID token's `cognito:groups` claim.
- **RBAC** — Role-Based Access Control. "If you're in group X, you
  can do Y." Cognito groups map to RBAC directly.
- **ABAC** — Attribute-Based Access Control. "If your `sub` matches
  this URL parameter, you can do Y." Cognito + Lambda authorizers
  enable ABAC.
- **Authorization scope** — the scope(s) API Gateway requires on a
  specific method. Requests with a token that doesn't have the scope
  are rejected with 403.
- **`scope` claim** — the space-separated list of scopes in the
  access token. e.g. `"openid email https://api.example.com/read:items"`.

## Lecture

Welcome back. In L16/L17 we wired an authorizer and saw that it
validates the token. Today we answer the harder question: **once the
token is valid, what is this user allowed to do?** This is where
most production APIs get authorization wrong. We'll show you the
two tools Cognito gives you — scopes and groups — and the right way
to combine them.

### Scopes vs Groups

| | Scope | Group |
|---|---|---|
| Defined in | Resource server (in the user pool) | User pool |
| Carried in | Access token (`scope` claim) | ID token (`cognito:groups` claim) |
| Granted at | Sign-in (user-consented) | Admin-group-membership (or user self-joins if configured) |
| Best for | What an **app** can do | What a **user** is |
| Example | `https://api.example.com/read:items` | `admins`, `readers`, `writers` |

A user can be in the `admins` group AND have the
`read:items` scope. The two are independent — and you can combine
them in your authorization rules.

### Defining a scope

You define a scope in a **resource server** on the User Pool:

```python
cognito.create_resource_server(
    UserPoolId=pool_id,
    Identifier="https://api.example.com",  # the resource server's URL/identifier
    Name="My API",
    Scopes=[
        {"ScopeName": "read:items",  "ScopeDescription": "Read items"},
        {"ScopeName": "write:items", "ScopeDescription": "Modify items"},
    ],
)
```

This creates the scopes `https://api.example.com/read:items` and
`https://api.example.com/write:items`. You then add them to the App
Client's `AllowedOAuthScopes`:

```python
cognito.update_user_pool_client(
    UserPoolId=pool_id,
    ClientId=client_id,
    AllowedOAuthScopes=[
        "openid",
        "email",
        "profile",
        "https://api.example.com/read:items",
        "https://api.example.com/write:items",
    ],
)
```

When the user signs in via the OAuth code flow (L09), they're shown
a consent screen with the scopes and they approve them. The access
token then carries the approved scopes in its `scope` claim.

### Requiring a scope on a route

REST API:

```python
apigw.put_method(
    restApiId=api_id,
    resourceId=items_id,
    httpMethod="GET",
    authorizationType="COGNITO_USER_POOLS",
    authorizerId=authorizer_id,
    authorizationScopes=["https://api.example.com/read:items"],  # ← require
)
```

HTTP API:

```python
apigwv2.create_route(
    ApiId=api_id,
    RouteKey="GET /items",
    Target=f"integrations/{integration_id}",
    AuthorizationType="JWT",
    AuthorizerId=authorizer_id,
    AuthorizationScopes=["https://api.example.com/read:items"],  # ← require
)
```

API Gateway extracts the scope from the access token's `scope`
claim, splits on whitespace, and checks for membership. If the
scope isn't present, API Gateway returns **403 Forbidden** with a
`x-amzn-ErrorType: ForbiddenException` payload.

### Defining a group

```python
cognito.create_group(
    GroupName="admins",
    UserPoolId=pool_id,
    Description="Administrators",
    # Optionally attach an IAM role — used when the group is also a
    # User Pool provider in an Identity Pool.
    RoleArn="arn:aws:iam::123456789012:role/AdminsRole",
)
cognito.admin_add_user_to_group(
    UserPoolId=pool_id,
    Username="alice@example.com",
    GroupName="admins",
)
```

After Alice signs in, her ID token's `cognito:groups` claim is
`["admins"]`. API Gateway forwards this to your Lambda:

```python
def handler(event, context):
    groups = event.request_context.authorizer.claims.get(
        "cognito:groups", ""
    )
    if isinstance(groups, str):
        groups = [g for g in groups.split(",") if g]
    if "admins" not in groups:
        return {"statusCode": 403, "body": "forbidden"}
    # ... do the admin thing ...
```

### The pattern: scopes + groups

For most APIs the right answer is:

- **Scopes** gate which **endpoints** a user can hit at all
  (coarse-grained).
- **Groups** gate which **rows** or **actions** a user can perform
  (fine-grained, in your Lambda).

For example:

| Endpoint | Scope required | Group required |
|---|---|---|
| `GET /items` | `read:items` | any signed-in user |
| `POST /items` | `write:items` | any signed-in user |
| `DELETE /items/{id}` | `write:items` | `admins` group |
| `GET /admin/audit-log` | `read:audit` | `admins` group |

The scope check is enforced by API Gateway. The group check is
enforced in your Lambda.

### ABAC for per-row authorization

For "user X can only read their own order":

```python
def get_order_handler(event, context):
    claims = event.request_context.authorizer.claims
    user_sub = claims["sub"]
    order_id = event.path_parameters["orderId"]

    order = orders_table.get_item(Key={"id": order_id})["Item"]

    if order["owner_sub"] != user_sub and "admins" not in claims.get(
        "cognito:groups", ""
    ).split(","):
        return {"statusCode": 403, "body": "not your order"}

    return {"statusCode": 200, "body": json.dumps(order)}
```

This is **ABAC** (attribute-based): the authorization decision
depends on the value of the `owner_sub` attribute on the row
**and** the value of the `sub` claim in the token. Cognito gives
you the `sub`; your code does the comparison.

### Common authorization bugs

1. **Relying on scope for row-level access.** Scopes are coarse.
   Use groups or ABAC for row-level.
2. **Forgetting to check the token's group claim in your Lambda.**
   The authorizer validates the token; your Lambda enforces
   authorization.
3. **Trusting a custom claim from the user.** Custom claims are
   signed by Cognito — they're trustworthy. **But never let the
   client send the claim as a header** — always read it from the
   validated token claims.
4. **Mixing up ID and access tokens for scope.** Scopes appear in
   **access tokens**, not ID tokens. If you put an ID token in
   `Authorization: Bearer ...` and require a scope, it'll always
   fail.

### What's coming

L19 — the JWT validation algorithm in depth. The lecture that
makes you dangerous enough to write a Lambda Authorizer from scratch.