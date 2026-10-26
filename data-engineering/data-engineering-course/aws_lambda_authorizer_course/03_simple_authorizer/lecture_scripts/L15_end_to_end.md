---
lecture: L15
title: "End-to-End: TOKEN Authorizer with HS256 JWT"
duration: "34:00"
section: 3
prereqs: ["L14"]
---

# L15 — End-to-End: TOKEN Authorizer with HS256 JWT

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 3 — Simple Token-Based Lambda Authorizer
> **Duration:** 34:00

## Prereqs

- L14 — `context` map.

## Key terms

- **Reference handler** — a complete, deployable Lambda Authorizer.
  The one in `03_simple_authorizer/code/token_authorizer.py`.
- **Environment-driven config** — the authorizer reads `JWT_SECRET`,
  `JWT_ISSUER`, `JWT_AUDIENCE` from the function's environment.
  Production secrets come from AWS Secrets Manager.
- **Flat context helper** — `_flatten()` turns nested JWT claims
  into the flat string-only dict API Gateway requires.

## Lecture

This is the **end-to-end** lecture. We wire together L11–L14 into
one ~100-line module and write six tests.

The module is `03_simple_authorizer/code/token_authorizer.py`. Open
it (it's short) and follow along.

### The shape

```python
def lambda_handler(event, context):
    method_arn = event.get("methodArn", "")
    raw_token = event.get("authorizationToken", "")
    if raw_token.lower().startswith("bearer "):
        raw_token = raw_token[7:]
    if not method_arn:
        return _deny("")

    secret = os.environ.get("JWT_SECRET", _DEFAULT_TEST_SECRET)
    issuer = os.environ.get("JWT_ISSUER")
    audience = os.environ.get("JWT_AUDIENCE")

    decode_kwargs = {"algorithms": ["HS256"],
                     "options": {"require": ["exp", "iat", "iss",
                                              "sub", "aud"]}}
    if issuer:
        decode_kwargs["issuer"] = issuer
    if audience:
        decode_kwargs["audience"] = audience

    try:
        claims = jwt.decode(raw_token, secret, **decode_kwargs)
    except jwt.PyJWTError:
        return _deny(method_arn)

    principal_id = str(claims.get("sub", "anonymous"))
    return _allow(method_arn, principal_id, _flatten(claims))
```

That's the whole handler.

### The tests

`test_token_authorizer.py` ships six tests:

1. **`test_valid_token_returns_allow`** — sign a token, call the
   handler, assert `Effect: Allow`, `Resource` matches `methodArn`,
   `principalId` matches `sub`.
2. **`test_invalid_token_returns_deny`** — sign with one secret,
   call with a different `JWT_SECRET`, assert `Effect: Deny`.
3. **`test_missing_token_returns_deny`** — call with empty
   `authorizationToken`, assert `Effect: Deny`.
4. **`test_policy_resource_matches_method_arn`** — verify that the
   Allow policy's `Resource` is the `methodArn` from the event.
5. **`test_policy_action_is_execute_api_invoke`** — verify that the
   Allow policy's `Action` is exactly `execute-api:Invoke`.
6. **`test_principal_id_extracted_from_sub_claim`** — sign with
   `sub: "u-42"`, verify the response's `principalId` is `"u-42"`.

Plus a helper `_mint(claims)` that signs an HS256 JWT with the
correct standard claims, and `_event(token)` that wraps the token
in an API Gateway authorizer event.

### Running it

```bash
cd /Users/vishnoiprem/PycharmProjects/data-etl-ml/data-engineering/data-engineering-course/aws_lambda_authorizer_course/03_simple_authorizer/code
pip install -r requirements.txt
pytest -v
```

Expected output ends with `6 passed`.

### Deploying it (real AWS)

If you want to run this on real AWS:

```bash
# 1. Create a deployment package
pip install --target ./build pyjwt -q
cp token_authorizer.py ./build/
(cd ./build && zip -qr ../authorizer.zip .)

# 2. Create the Lambda
aws lambda create-function \
  --function-name demo-token-authorizer \
  --runtime python3.12 \
  --handler token_authorizer.lambda_handler \
  --role arn:aws:iam::123456789012:role/lambda-exec-role \
  --zip-file fileb://authorizer.zip \
  --environment 'Variables={JWT_SECRET=replace-me,JWT_ISSUER=https://auth.example.com,JWT_AUDIENCE=api.example.com}' \
  --timeout 5 \
  --memory-size 256

# 3. Grant API Gateway permission to invoke it
aws lambda add-permission \
  --function-name demo-token-authorizer \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:123456789012:abcd/*"
```

Then attach the authorizer to your API method via
`create-authorizer` + `update-method`:

```bash
aws apigateway create-authorizer \
  --rest-api-id abcd \
  --name token-authorizer \
  --type TOKEN \
  --authorizer-uri "arn:aws:lambda:us-east-1:123456789012:function:demo-token-authorizer" \
  --identity-source "method.request.header.Authorization" \
  --authorizer-result-ttl-in-seconds 300

aws apigateway update-method \
  --rest-api-id abcd \
  --resource-id xyz789 \
  --http-method GET \
  --patch-operations op=replace,path=/authorizationType,value=CUSTOM \
                   op=replace,path=/authorizerId,value=abcd123
```

For a step-by-step screenshot walkthrough, watch the lecture video.

### What this handler doesn't (yet) handle

- **JWKS-based key rotation.** A production authorizer signed with
  RS256 should fetch the JWKS endpoint and cache it. That's the
  section 4 demo.
- **Policy caching with a custom cache key.** The default cache
  key is `methodArn`. Section 4 shows how to build a multi-key
  cache (e.g. `(methodArn, tenant)`).
- **Custom auth challenges** for WebSocket APIs. That's L23.
- **Lambda@Edge** invocation. That's L22.

If your needs are simple, this handler is the entire answer. If
not, the next two sections extend it.

## Hands-on

```bash
cd /Users/vishnoiprem/PycharmProjects/data-etl-ml/data-engineering/data-engineering-course/aws_lambda_authorizer_course/03_simple_authorizer/code
python3 -m pip install -r requirements.txt
pytest -v
```

Expected: **6 passed**.

## Quiz prep

- What three environment variables does the handler read?
- What does `_flatten()` do and why is it needed?
- What happens if `JWT_SECRET` is unset? (Falls back to a test
  default that won't match a real token — fails closed.)

## Further reading

- [`../code/token_authorizer.py`](../code/token_authorizer.py) — the full handler.
- [`../code/test_token_authorizer.py`](../code/test_token_authorizer.py) — the tests.
- AWS docs: [Use API Gateway Lambda authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-use-lambda-authorizer.html).

## What's next

**Section 4 — Request-Parameter Authorizer & Policy Caching (L16–L20).**
The richer authorizer type, with a multi-IdentitySource cache key
and an in-process LRU with TTL.