---
lecture: L20
title: "End-to-End: REQUEST Authorizer with Policy Cache"
duration: "20:00"
section: 4
prereqs: ["L19"]
---

# L20 — End-to-End: REQUEST Authorizer with Policy Cache

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 4 — Request-Parameter Authorizer & Policy Caching
> **Duration:** 20:00

## Prereqs

- L19 — LRU + TTL.

## Key terms

- **`IdentitySource`** — `method.request.querystring.user,method.request.querystring.token`
- **`ReauthorizeEvery`** — 300 (5 min).
- **Internal cache** — `TTLCache(max_size=1024, ttl_seconds=300)`.
- **Cache key** — `f"{user}|{token}"`.

## Lecture

This is the end-to-end lecture for the REQUEST authorizer. The
working code is in `04_policy_cache/code/param_authorizer.py` and
the tests are in `test_param_authorizer.py`.

### The handler

The handler:

1. Reads `user` and `token` from `queryStringParameters`.
2. Builds a cache key `f"{user}|{token}"`.
3. Returns the cached policy if present.
4. Otherwise verifies the token, builds an Allow policy, caches
   it, and returns it.

```python
def lambda_handler(event, context):
    method_arn = event.get("methodArn", "")
    qs = event.get("queryStringParameters") or {}
    user = qs.get("user", "")
    token = qs.get("token", "")

    if not user or not token:
        return _deny(method_arn)

    cache_key = f"{user}|{token}"
    cached = _POLICY_CACHE.get(cache_key)
    if cached is not None:
        return cached

    if not _verify_token(user, token):
        return _deny(method_arn)

    policy = _allow(method_arn, user, {"sub": user, "tenant": user})
    _POLICY_CACHE.set(cache_key, policy)
    return policy
```

The token verification, for the demo, just checks that the token
equals the expected value in `EXPECTED_TOKENS[user]`. In a real
system, replace `_verify_token` with a JWKS-backed RS256 check.

### The cache

A single module-level instance:

```python
_POLICY_CACHE: TTLCache[str, dict] = TTLCache(
    max_size=1024,
    ttl_seconds=int(os.environ.get("CACHE_TTL_SECONDS", "300")),
)
```

The TTL is environment-driven so you can tune it without
redeploying. The default is 300 s (5 min), matching API Gateway's
default `ReauthorizeEvery`.

### The tests

`test_param_authorizer.py` ships four tests:

1. **`test_valid_params_return_allow`** — `?user=alice&token=valid`
   returns Allow with the correct methodArn and principalId.
2. **`test_missing_user_returns_deny`** — no `user` query param
   returns Deny.
3. **`test_cache_key_built_from_user_and_token`** — two events
   with the same `user` and `token` share a cache entry.
4. **`test_ttl_applied_to_cached_policy`** — a stale entry is
   not returned; the second call re-runs verification.

Plus a small unit test for the cache itself:

5. **`test_cache_expires_after_ttl`** — manually advance `time.time()`
   and confirm the entry is treated as missing.

### Running

```bash
cd /Users/vishnoiprem/PycharmProjects/data-etl-ml/data-engineering/data-engineering-course/aws_lambda_authorizer_course/04_policy_cache/code
pip install -r requirements.txt
pytest -v
```

Expected: **4+ passed**.

### The deployment difference vs section 3

The create-authorizer call for a REQUEST authorizer is slightly
different from a TOKEN authorizer:

```bash
aws apigateway create-authorizer \
  --rest-api-id abcd \
  --name param-authorizer \
  --type REQUEST \
  --authorizer-uri "arn:aws:lambda:us-east-1:123456789012:function:my-param-authorizer" \
  --identity-source "method.request.querystring.user,method.request.querystring.token" \
  --authorizer-result-ttl-in-seconds 300
```

The two key differences:

- `--type REQUEST` (not `TOKEN`).
- `--identity-source` (not implicit from the `Authorization` header).

The `ReauthorizeEvery` (300 s) is `--authorizer-result-ttl-in-seconds`.

### What this handler doesn't (yet) handle

- **JWKS-backed RS256 verification.** For the demo, the token
  check is a dict lookup. In production, replace with the
  PyJWKClient pattern from L09.
- **Token revocation.** The internal cache can hold a stale entry
  for up to 5 min after the IdP revokes the token. For faster
  revocation, add a `jti` denylist backed by a Redis set.
- **Cache hit observability.** Add an EMF metric for hits vs
  misses (L19).

## Hands-on

```bash
cd /Users/vishnoiprem/PycharmProjects/data-etl-ml/data-engineering/data-engineering-course/aws_lambda_authorizer_course/04_policy_cache/code
python3 -m pip install -r requirements.txt
pytest -v
```

Expected: **4+ passed**.

## Quiz prep

- What's the cache key for a request with `?user=alice&token=xyz`?
- What's the default TTL of the internal cache?
- How do you tune the TTL at deploy time without changing code?

## Further reading

- [`../code/param_authorizer.py`](../code/param_authorizer.py) — the handler.
- [`../code/test_param_authorizer.py`](../code/test_param_authorizer.py) — the tests.
- AWS docs: [Use API Gateway Lambda authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-use-lambda-authorizer.html).

## What's next

**Section 5 — Advanced Patterns (L21–L25).** CloudFront Lambda@Edge,
WebSocket auth challenges, OIDC integration, and the design
trade-offs that tell you when **not** to use a Lambda Authorizer.