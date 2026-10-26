---
lecture: L17
title: "The API Gateway REQUEST Event (headers, query, stage vars, body)"
duration: "18:00"
section: 4
prereqs: ["L16"]
---

# L17 — The API Gateway REQUEST Event

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 4 — Request-Parameter Authorizer & Policy Caching
> **Duration:** 18:00

## Prereqs

- L16 — section overview.

## Key terms

- **`type`** — `"REQUEST"` for this section.
- **`methodArn`** — the same as for TOKEN. The ARN of the method
  being invoked.
- **`resource` / `path`** — the path pattern (`/orders/{id}`) and
  the actual path (`/orders/123`).
- **`httpMethod`** — the HTTP verb (`GET`, `POST`, etc).
- **`headers`** — a flat dict of header name → header value. Names
  are lowercased. Multi-value headers are joined with commas.
- **`queryStringParameters`** — a flat dict of query string name →
  value. The values are NOT lists — if a query parameter appears
  twice, the values are joined with a comma.
- **`pathParameters`** — `{id: "123"}` for the path pattern
  `/orders/{id}`.
- **`stageVariables`** — the stage's variables (`stage`, `lambdaAlias`,
  etc).
- **`requestContext`** — the API Gateway request context. Includes
  `accountId`, `apiId`, `domainName`, `httpMethod`, `requestId`,
  `resourceId`, `resourcePath`, `stage`, `identity` (the AWS
  SigV4 identity if the request was signed), `authorizer` (the
  upstream authorizer's output if any).

## Lecture

The REQUEST event is bigger than the TOKEN event but the structure
is the same shape every API Gateway event has. Let's walk through
the fields that matter for an authorizer.

### A full event

```json
{
  "type": "REQUEST",
  "methodArn": "arn:aws:execute-api:us-east-1:111122223333:abcd1234/prod/GET/admin/reindex",
  "resource": "/admin/reindex",
  "path": "/admin/reindex",
  "httpMethod": "GET",
  "headers": {
    "X-Tenant": "acme",
    "X-Forwarded-For": "203.0.113.42",
    "CloudFront-Viewer-Country": "US"
  },
  "multiValueHeaders": {
    "X-Tenant": ["acme"],
    "X-Forwarded-For": ["203.0.113.42", "198.51.100.7"]
  },
  "queryStringParameters": {
    "user": "alice",
    "token": "xyz"
  },
  "multiValueQueryStringParameters": {
    "user": ["alice"],
    "token": ["xyz"]
  },
  "pathParameters": null,
  "stageVariables": {
    "stage": "prod"
  },
  "requestContext": {
    "accountId": "111122223333",
    "apiId": "abcd1234",
    "domainName": "abcd1234.execute-api.us-east-1.amazonaws.com",
    "httpMethod": "GET",
    "requestId": "5b2f…",
    "resourceId": "xyz789",
    "resourcePath": "/admin/reindex",
    "stage": "prod",
    "identity": { … }
  },
  "body": null,
  "isBase64Encoded": false
}
```

### Field-by-field

**`type`** — always `"REQUEST"`. If you see `"TOKEN"`, the
authorizer is misconfigured. Fail closed.

**`methodArn`** — the canonical `Resource` for the policy. Same as
in section 3.

**`resource` vs `path`** — `resource` is the *pattern*
(`/orders/{id}`), `path` is the *actual* path (`/orders/123`).
For an authorizer, `resource` is what you usually want; `path` is
useful for log lines.

**`headers` vs `multiValueHeaders`** — `headers` is the
single-value form (multi-value headers joined with commas).
`multiValueHeaders` keeps them as lists. The authorizer can use
either; for caching purposes, the single-value form is usually
sufficient.

Header names are **lowercased**. `event["headers"]["X-Tenant"]`
will never match; it's `event["headers"]["x-tenant"]`.

**`queryStringParameters` vs `multiValueQueryStringParameters`** —
same shape as headers, single-value vs multi-value. If a client
sends `?tag=a&tag=b`, the single-value form is `"tag": "a,b"`.

**`pathParameters`** — `null` for paths without placeholders.
For `/orders/{id}` it's `{"id": "123"}`. Useful for log lines;
almost never used as an `IdentitySource`.

**`stageVariables`** — the values of the API's stage variables.
`stage` is a built-in. Custom variables (`lambdaAlias`,
`signingKey`) are passed through.

**`requestContext.identity`** — if the request was signed with IAM
(SigV4), this contains the IAM identity. Most Lambda Authorizers
ignore it, but it's the right field to use if you're combining IAM
auth with a Lambda Authorizer.

**`body`** — `null` for `GET`/`DELETE`. The full request body for
`POST`/`PUT`. Almost never used as an `IdentitySource` because
bodies are large and variable; using the body in a cache key would
defeat the cache.

### What's missing

The REQUEST event **does not** include:

- The **TLS client cert** (for mTLS). If you need mTLS, look at
  API Gateway's mTLS support separately.
- The **raw HTTP request line** (you have `httpMethod` and `path`
  separately).
- The **raw `Authorization` header** in decoded form. The raw value
  is in `headers["authorization"]`; decoding JWTs is your job.

### Common gotchas

- **Header names are lowercased.** Always `headers.get("x-tenant")`,
  not `headers.get("X-Tenant")`.
- **`null` vs missing.** A field the client didn't send is
  `None` in `queryStringParameters` (not absent). Use
  `event.get("queryStringParameters", {}).get("user")` to handle
  both cases.
- **Multi-value headers are joined with commas.** If the value
  itself contains a comma, you can't recover the split. Use
  `multiValueHeaders` if it matters.
- **The body is base64-encoded** for binary content. Check
  `isBase64Encoded` and decode if so.

## Hands-on

The hands-on code is in L20. For now, build a small Python
function that takes a REQUEST event and prints a summary:

```python
def summarize(event):
    print("method:", event["httpMethod"], event["resource"])
    print("user  :", (event.get("queryStringParameters") or {}).get("user"))
    print("tenant:", (event.get("headers") or {}).get("x-tenant"))
    print("stage :", (event.get("stageVariables") or {}).get("stage"))
```

Use the sample event from the parent course's
`../aws_lambda_course/09_api_security_lambda_cognito_auth/code/event_payloads/request_authorizer_event.json`.

## Quiz prep

- Are header names case-sensitive in the event? (No — lowercased.)
- What's the difference between `queryStringParameters` and
  `multiValueQueryStringParameters`?
- Is the body included in the cache key? (No, and don't try.)

## Further reading

- AWS docs: [Input to a Lambda REQUEST authorizer](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-lambda-authorizer-input.html).
- Download: [`../../downloads/api_gateway_event_shapes.pdf`](../../downloads/api_gateway_event_shapes.pdf).

## What's next

**L18 — `IdentitySource`, Multi-Identity-Source & `ReauthorizeEvery`**
— how to pick the cache key and the cache duration.