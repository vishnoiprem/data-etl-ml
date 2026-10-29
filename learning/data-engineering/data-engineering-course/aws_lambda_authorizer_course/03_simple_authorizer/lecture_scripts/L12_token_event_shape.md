---
lecture: L12
title: "The API Gateway TOKEN Event (authorizationToken, methodArn, type)"
duration: "14:00"
section: 3
prereqs: ["L11"]
---

# L12 — The API Gateway TOKEN Event

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 3 — Simple Token-Based Lambda Authorizer
> **Duration:** 14:00

## Prereqs

- L11 — section overview.

## Key terms

- **`type`** — `"TOKEN"` for this section. `"REQUEST"` for section 4.
- **`authorizationToken`** — the raw value of the `Authorization`
  header. API Gateway does NOT strip the `Bearer ` scheme for you.
- **`methodArn`** — the ARN of the method being invoked. Format:
  `arn:aws:execute-api:<region>:<account>:<api-id>/<stage>/<METHOD>/<resource-path>`.
- **Cache key** — by default, the `methodArn` is used to key the
  policy cache. So two requests to the *same* method share a cached
  policy if the authorizer returns one. See section 4 for caveats.
- **Stale-token problem** — if a token is valid when the authorizer
  runs but the cache TTL outlasts the token, the cached Allow policy
  may let through a token whose `exp` has since passed. Mitigated by
  short TTLs.

## Lecture

The TOKEN event is small. Three fields, two of which you'll use 99%
of the time:

```json
{
  "type": "TOKEN",
  "authorizationToken": "Bearer eyJhbGciOi…",
  "methodArn": "arn:aws:execute-api:us-east-1:111122223333:abcd1234/prod/GET/orders"
}
```

### `type`

Always `"TOKEN"` for this authorizer type. You can use it as a
sanity check:

```python
if event.get("type") != "TOKEN":
    return _deny(event.get("methodArn", ""))
```

If you see `"REQUEST"` instead, you attached a REQUEST authorizer
to a method that's actually configured as TOKEN, or vice versa. It's
a configuration bug — fail closed.

### `authorizationToken`

The raw value of the `Authorization` header. API Gateway does *not*
strip the `Bearer ` prefix for you. A well-behaved authorizer does:

```python
raw = event.get("authorizationToken", "")
if raw.lower().startswith("bearer "):
    raw = raw[7:]  # drop the scheme
```

If the client sends no `Authorization` header at all, this field is
the empty string. If the client sends `Authorization: Basic …`, the
value is `"Basic …"` — your authorizer should reject both.

### `methodArn`

The full ARN of the method being invoked. Format:

```
arn:aws:execute-api:<region>:<account>:<api-id>/<stage>/<METHOD>/<resource-path>
```

Example:

```
arn:aws:execute-api:us-east-1:111122223333:abcd1234/prod/GET/orders
```

This is the canonical `Resource` for the Allow policy:

```python
def lambda_handler(event, context):
    method_arn = event.get("methodArn", "")
    token = event.get("authorizationToken", "")
    # ... verify token ...
    return _allow(method_arn, principal_id, claims)
```

A common variant is to use a **wildcard segment** to allow multiple
methods at once:

```python
# Allow GET /orders and POST /orders
arn_prefix = method_arn.rsplit("/", 1)[0]
resource = f"{arn_prefix}/*"
```

But for the first version of any authorizer, just echo the
`methodArn` back unchanged. Expanding the `Resource` is a
refinement.

### What the integration sees

When the request is allowed, the integration (your backend Lambda)
receives the authorizer's `context` in the event JSON:

```json
{
  "requestContext": {
    "authorizer": {
      "principalId": "user-1",
      "sub": "user-1",
      "tenant": "acme",
      "scope": "read"
    }
  }
}
```

And as request headers:

```
X-Amzn-Apigateway-Authorizer-Principal-Id: user-1
X-Amzn-Apigateway-Authorizer-Sub:           user-1
X-Amzn-Apigateway-Authorizer-Tenant:        acme
X-Amzn-Apigateway-Authorizer-Scope:         read
```

The integration can read either form. Most teams use the event JSON
because it's strongly typed.

### What CloudWatch shows

The authorizer's logs are visible in
`/aws/lambda/<authorizer-function-name>`. A successful invocation
looks like:

```text
START RequestId: 5b2f… Version: $LATEST
[INFO] 2025-01-01T00:00:00.000Z 5b2f… verified sub=user-1 tenant=acme
END RequestId: 5b2f…
REPORT RequestId: 5b2f…  Duration: 12.34 ms  Billed Duration: 13 ms  Memory Size: 128 MB
```

The Duration is the most important metric — authorizer latency adds
to every API call. The first time the function warms up you'll see
~200 ms (cold start); subsequent calls should be under 20 ms.

## Hands-on

No code yet. The hands-on demo is L15. For now, eyeball the
`event_payloads/token_authorizer_event.json` file in the parent
course if you want to see a real event.

## Quiz prep

- Does API Gateway strip the `Bearer ` prefix from
  `authorizationToken`? (No.)
- What does the `methodArn` look like?
- Where do you read the authorizer's `context` in the backend
  Lambda? (`event.requestContext.authorizer` and as
  `X-Amzn-Apigateway-Authorizer-*` headers.)

## Further reading

- AWS docs: [Input to a Lambda TOKEN authorizer](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-lambda-authorizer-input.html).

## What's next

**L13 — Building the Allow Policy** — the `policyDocument` line by
line. Why the `Action` is always `execute-api:Invoke` and why the
`Resource` is almost always the `methodArn`.