---
lecture: L14
title: "Returning Claims via the context Map"
duration: "14:00"
section: 3
prereqs: ["L13"]
---

# L14 — Returning Claims via the `context` Map

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 3 — Simple Token-Based Lambda Authorizer
> **Duration:** 14:00

## Prereqs

- L13 — building the Allow policy.

## Key terms

- **`context`** — the third top-level field of the authorizer
  response. A flat dict of strings that API Gateway forwards to the
  integration.
- **`requestContext.authorizer`** — the location in the integration
  event JSON where API Gateway puts the `context` map.
- **`X-Amzn-Apigateway-Authorizer-*`** — the request headers API
  Gateway sets on the integration for each `context` key.
- **Flattening** — the process of turning nested JSON into a flat
  dict. Required because `context` cannot contain nested objects.

## Lecture

The `context` map is how the authorizer passes identity information
to the backend. It's an optional third field on the response, but
almost always present in real systems because the backend needs to
know *who* the caller is.

### The contract

Two rules:

1. **Flat.** No nested objects, no lists. `{"a.b": "1"}` is allowed;
   `{"a": {"b": 1}}` is not.
2. **Strings.** Every value must be a string. `{"iat": 1700000000}`
   is required; `{"iat": 1700000000}` (int) is silently dropped.

API Gateway enforces both rules server-side. If you violate either,
the request fails with **500 Internal Server Error** and the only
error message is in CloudWatch Logs:

```
The context map must be a flat map of string-keyed, string-valued
entries.
```

This error is famously hard to debug because the response is just
500. The integration never runs, so the Lambda logs are empty.

### A correct context

```json
{
  "sub": "user-1",
  "tenant": "acme",
  "scope": "read",
  "exp": "1700000900"
}
```

Every value is a string. The map is flat. `exp` is the JWT's `exp`
claim cast to `str(...)`.

### A flattened helper

The JWT payload is *not* flat — `claims["address"]` might be a dict.
You need a helper:

```python
def _flatten(claims: dict, *, _prefix: str = "") -> dict:
    out: dict[str, str] = {}
    for key, value in claims.items():
        composite = f"{_prefix}{key}"
        if isinstance(value, dict):
            out.update(_flatten(value, _prefix=f"{composite}."))
        elif isinstance(value, list):
            # API Gateway can't carry lists; join with commas.
            out[composite] = ",".join(str(v) for v in value)
        else:
            out[composite] = str(value)
    return out
```

Now `_flatten({"sub": "u-1", "tenant": "acme", "iat": 1700000000})`
returns `{"sub": "u-1", "tenant": "acme", "iat": "1700000000"}`.

### What the integration sees

The backend Lambda's event includes:

```python
event["requestContext"]["authorizer"] = {
    "principalId": "user-1",
    "sub": "user-1",
    "tenant": "acme",
    "scope": "read",
    "exp": "1700000900",
}
```

And on the way in, API Gateway sets these headers on the
integration:

```
X-Amzn-Apigateway-Authorizer-Principal-Id: user-1
X-Amzn-Apigateway-Authorizer-Sub:           user-1
X-Amzn-Apigateway-Authorizer-Tenant:        acme
X-Amzn-Apigateway-Authorizer-Scope:         read
X-Amzn-Apigateway-Authorizer-Exp:           1700000900
```

`principalId` is special-cased: it's also in
`event.requestContext.authorizer.principalId`. Every other key is
only in the dict.

### Common keys

The keys you'll put in `context` are almost always a subset of:

- `sub` — the subject of the token (duplicated from `principalId`).
- `tenant` / `org` — multi-tenant systems need this to scope queries.
- `scope` — space-separated OAuth2 scopes.
- `exp` — the token's `exp` claim, as a string. Useful for the
  backend to log "this request will expire in 12 minutes".
- `user_agent` — if you want to pass through the client's
  `User-Agent` header.

What you should NOT put in `context`:

- Anything you wouldn't want logged. `context` appears in
  CloudWatch Logs for both the authorizer and the integration.
- Anything larger than a few hundred bytes. The whole point of
  `context` is to be cheap; if you're passing the entire JWT
  payload, you've misunderstood the use case.

### A full handler

```python
def lambda_handler(event, context):
    method_arn = event.get("methodArn", "")
    token = event.get("authorizationToken", "")
    if token.lower().startswith("bearer "):
        token = token[7:]

    try:
        claims = jwt.decode(token, SECRET, algorithms=["HS256"],
                            audience="api.example.com",
                            issuer="https://auth.example.com",
                            options={"require": ["exp", "iat", "iss",
                                                 "sub", "aud"]})
    except jwt.PyJWTError:
        return _deny(method_arn)

    principal_id = str(claims["sub"])
    flat_context = _flatten(claims)
    return _allow(method_arn, principal_id, flat_context)
```

## Hands-on

The hands-on demo is L15. For now, copy the `_flatten` helper into
a Python REPL and try it on a sample JWT payload:

```python
def _flatten(claims, *, _prefix=""):
    out = {}
    for k, v in claims.items():
        key = f"{_prefix}{k}"
        if isinstance(v, dict):
            out.update(_flatten(v, _prefix=f"{key}."))
        elif isinstance(v, list):
            out[key] = ",".join(str(x) for x in v)
        else:
            out[key] = str(v)
    return out

_flatten({"sub": "u-1", "tenant": "acme",
          "address": {"city": "sf"},
          "roles": ["admin", "ops"]})
# {'sub': 'u-1', 'tenant': 'acme',
#  'address.city': 'sf', 'roles': 'admin,ops'}
```

## Quiz prep

- What two rules apply to the `context` map?
- What does the integration see in the event JSON?
- How do you represent a list in `context`?

## Further reading

- AWS docs: [Output from a Lambda TOKEN authorizer](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-lambda-authorizer-output.html).
- Download: [`../../downloads/iam_policy_cheat_sheet.pdf`](../../downloads/iam_policy_cheat_sheet.pdf).

## What's next

**L15 — End-to-End: TOKEN Authorizer with HS256 JWT** — the
working demo. The full handler, six tests.