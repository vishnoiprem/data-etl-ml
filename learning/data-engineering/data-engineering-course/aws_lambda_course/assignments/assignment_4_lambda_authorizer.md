# Assignment 4 — Lambda Authorizer: Token + Request Modes, Caching

> **Section:** 9 (API Security — Lambda Authorizer & Cognito Authorizer)
> **Estimated time:** 4 hours
> **Deliverable:** Use Case 2 API from assignment 3, re-protected by a Lambda Authorizer that you can flip between `TOKEN` and `REQUEST` modes without code changes outside the handler itself.
> **Author:** Prem Vishnoi <pvishnoi@avilx.com>

## Learning objectives

By the end of this assignment you will be able to:

1. Author a Lambda Authorizer that validates a **JWT** (or a simpler `Bearer` token) and returns a properly scoped `iam_policy` document.
2. Distinguish the **token-based** (`identitySource` is a header) and **request-based** (`identitySource` is a multi-source policy) authorizer configurations.
3. Configure **`identity_source`** and **`TTLDurationSeconds`** (caching) on the authorizer resource.
4. Re-wire the API from assignment 3 to use the Lambda Authorizer instead of Cognito, while keeping the `/health` endpoint public.
5. Verify caching via the CloudWatch `AuthorizerCache*` metrics.

## Background

Section 9 lectures L36–L37 walk through the Lambda Authorizer pattern. The authorizer is itself a Lambda. When API Gateway receives a request, it synchronously invokes the authorizer Lambda; the authorizer returns either `Allow` or `Deny` (and, when `Allow`, an `iam_policy` document). API Gateway then enforces that policy for the duration in `TTLDurationSeconds`.

This assignment asks you to **integrate** that pattern onto the API from assignment 3, and to make the authorizer mode toggleable without redeploying the API.

## Architecture

```
Client ──Authorization: Bearer <jwt>──▶ API Gateway ──Lambda Authorizer──▶ Items Lambda ──▶ S3
                  │                            │
                  │                            ├─ mode=TOKEN    (header only)
                  │                            └─ mode=REQUEST  (header + query + context)
                  │
                  └─TTL=300 s cache keyed by identitySource
```

## Step-by-step tasks

### Step 1 — Start from assignment 3

Reuse the SAM template (or CDK stack) from assignment 3. Delete the Cognito resources. Keep the `/health` endpoint, the CRUD Lambda, and the S3 bucket.

### Step 2 — Build the authorizer Lambda

`authorizer/app.py`:

```python
import json
import logging
import os
from typing import Any

import jwt  # PyJWT

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

JWT_SECRET = os.environ["JWT_SECRET"]            # HMAC HS256
JWT_ALG = "HS256"
EXPECTED_AUDIENCE = os.environ.get("JWT_AUDIENCE", "usecase2-api")
TOKEN_HEADER = "Authorization"                   # also configurable

def lambda_handler(event: dict[str, Any], _ctx: Any) -> dict[str, Any]:
    LOG.info("authorizer event: %s", json.dumps(event))

    # Token mode: identitySource is a single string (the raw header value).
    # Request mode: identitySource is a dict mapping each source to its value(s).
    token = _extract_token(event)
    try:
        claims = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG], audience=EXPECTED_AUDIENCE)
    except jwt.PyJWTError as exc:
        LOG.warning("jwt decode failed: %s", exc)
        return _deny("Unauthorized", f"Invalid token: {exc}")

    method_arn = event["methodArn"]
    _, _, region, acct, api_id, stage, method, resource = _arn_parts(method_arn)

    policy = _allow(acct, api_id, region, stage, method, resource, claims)
    return {
        "principalId": claims.get("sub", "anonymous"),
        "policyDocument": policy,
        "context": {
            "scope": " ".join(claims.get("scope", "").split()),
            "email": claims.get("email", ""),
        },
        "usageIdentifierKey": claims.get("client_id", claims.get("sub", "anon")),
    }
```

Two helper modules:

- `_arn_parts(arn)` splits `arn:aws:execute-api:us-east-1:111:abc/prod/GET/items/{id}` into a 7-tuple.
- `_allow(...)` builds the IAM policy document. It must set `Resource` to `arn:aws:execute-api:<region>:<acct>:<api>/<stage>/*/*` (or tighter — see Step 5).

### Step 3 — Support both `TOKEN` and `REQUEST` modes

The authorizer must work in either mode without code changes. The difference is in how API Gateway calls it:

- `TOKEN`: `event["identitySource"] = "Bearer eyJ..."` (single string).
- `REQUEST`: `event["identitySource"] = {"Authorization": ["Bearer eyJ..."], "querystring": {"scope": ["read"]}}` (multi-source map).

`_extract_token(event)` must handle both:

```python
def _extract_token(event: dict[str, Any]) -> str:
    src = event.get("identitySource", "")
    if isinstance(src, dict):
        for header, values in src.items():
            if header.lower() == TOKEN_HEADER.lower():
                v = values[0] if values else ""
                return v.removeprefix("Bearer ").strip()
        raise ValueError("No Authorization header in identitySource")
    if isinstance(src, str):
        return src.removeprefix("Bearer ").strip()
    raise ValueError(f"Unexpected identitySource type: {type(src).__name__}")
```

The **client SDK call to API Gateway** is identical in both modes — only the `Authorizer` config in your SAM/CDK changes.

### Step 4 — Wire the authorizer into SAM

```yaml
  ItemsApi:
    Type: AWS::Serverless::Api
    Properties:
      StageName: prod
      Auth:
        DefaultAuthorizer: LambdaRequestAuth   # flip to LambdaTokenAuth to test mode
        Authorizers:
          LambdaTokenAuth:
            FunctionArn: !GetAtt AuthorizerFunction.Arn
            FunctionPayloadType: TOKEN
            Identity:
              Header: Authorization
              ReauthorizeEvery: 300
            AuthorizerResultTtlInSeconds: 300
          LambdaRequestAuth:
            FunctionArn: !GetAtt AuthorizerFunction.Arn
            FunctionPayloadType: REQUEST
            Identity:
              Headers:
                - Authorization
              QueryStrings:
                - scope
              ReauthorizeEvery: 300
            AuthorizerResultTtlInSeconds: 300
```

Keep the `/health` event with `Auth: Authorizer: NONE`.

### Step 5 — Scope the IAM policy

The authorizer's returned policy document scopes which API resources the principal can call. Make it explicit and tight:

```python
def _allow(acct, api_id, region, stage, method, resource, claims):
    scopes = set(claims.get("scope", "").split())
    actions = []
    if "read" in scopes:
        actions.append("execute-api:Invoke")
    resource_arn = f"arn:aws:execute-api:{region}:{acct}:{api_id}/{stage}/GET/*"
    if "write" in scopes and method in {"POST", "PUT", "DELETE"}:
        actions.append("execute-api:Invoke")
    if not actions:
        return _policy("Deny", resource_arn, [])
    return _policy("Allow", resource_arn, actions)
```

This means a token with `scope: read` cannot `POST`. Verify it.

### Step 6 — Local test with `moto` (optional but recommended)

`moto` 5.x supports API Gateway including custom authorizers. Write a quick test:

```python
@mock_aws
def test_token_authorizer_allows_with_valid_jwt():
    # arrange: create authorizer Lambda, REST API, deployment, stage
    # act: mint a JWT, call the deployed URL
    # assert: 200
```

> Note: `moto`'s custom-authorizer simulation is best-effort. If a particular assertion fails, document it in your PR and proceed with manual testing against the deployed API.

### Step 7 — End-to-end test (deployed)

```bash
TOKEN=$(python -c "import jwt, time; print(jwt.encode({'sub':'u1','aud':'usecase2-api','scope':'read write','exp':int(time.time())+3600}, 'shhh', algorithm='HS256'))")
curl -i -H "Authorization: Bearer $TOKEN" "$API_URL/items"
curl -i -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"id":"sku-2","name":"gadget"}' "$API_URL/items"
curl -i "$API_URL/items/sku-2"                  # 401
```

### Step 8 — Verify caching

Hit the same endpoint ten times with the same token. The authorizer CloudWatch metrics should show:

- `InvokeCount` ≈ 10
- `AuthorizerCache*` metrics should appear when TTL > 0

In the CloudWatch console, observe the `AuthorizerCount` and `AuthorizerCacheCount` metrics for the `AWS/ApiGateway` namespace.

### Step 9 — Flip the mode

Change the SAM template's `DefaultAuthorizer` from `LambdaTokenAuth` to `LambdaRequestAuth`. Redeploy. Verify that the same client request still works (the handler doesn't care). Document the difference in the README.

## Deliverables

- [ ] Updated `template.yaml` with both `LambdaTokenAuth` and `LambdaRequestAuth` authorizers.
- [ ] `authorizer/app.py` with mode-agnostic token extraction.
- [ ] `README.md` (Architecture, Prereqs, Deploy, Mint token, Test caching, Flip mode, Cleanup).
- [ ] `curl` transcripts for both modes.
- [ ] CloudWatch metric screenshot or `get-metric-statistics` JSON for cache effectiveness.
- [ ] A `scope=read` token that gets 200 on GET and 403 on POST.

## Grading rubric (100 points)

| Category | Points | What we look for |
|---|---|---|
| Authorizer handler correctness | 25 | Validates JWT, scopes by `scope` claim, returns well-formed policy doc. |
| Mode-agnostic token parsing | 20 | Same handler works for `TOKEN` and `REQUEST` modes. |
| IAM policy scoping | 15 | Read-only tokens cannot write. |
| Caching | 15 | `TTLDurationSeconds` set; CloudWatch cache metrics show non-zero hits. |
| `/health` still public | 5 | Returns 200 with no token. |
| Flip-mode deploy | 10 | Re-deploying with the other mode requires zero code change. |
| README | 10 | All sections, with mint-token snippet. |

Deductions:

- `-15` if the authorizer crashes when `identitySource` is a dict (REQUEST mode).
- `-10` if the policy document's `Resource` is `*`.
- `-10` if `JWT_SECRET` is checked into git.

## Stretch goals (optional, +10 each, capped at +20)

- Use **asymmetric** (RS256) signing with a public key fetched from a JWKS URL (cached with `requests-cache`).
- Add a **deny-by-default** mode that returns 403 for any `scope` that is not in an env-var allowlist.
- Add a CloudWatch **metric filter** on the authorizer log group that counts `Result=Allow` vs `Result=Deny`.