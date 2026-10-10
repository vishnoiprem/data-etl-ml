---
lecture: L16
title: "Section Overview — Why a Request Authorizer"
duration: "6:00"
section: 4
prereqs: ["L15"]
---

# L16 — Section Overview — Why a Request Authorizer

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 4 — Request-Parameter Authorizer & Policy Caching
> **Duration:** 6:00

## Prereqs

- L15 — end-to-end TOKEN authorizer.

## Key terms

- **REQUEST authorizer** — the richer API Gateway authorizer type
  that receives the **full** request event, not just the
  `Authorization` header.
- **`IdentitySource`** — the list of expressions that identify *this*
  request. Each expression is a reference to a header, a query
  parameter, a stage variable, or a context variable.
- **Cache key** — the string API Gateway derives from the
  `IdentitySource` values for a given request. Two requests with
  the same cache key share a cached policy.
- **`ReauthorizeEvery`** — how long API Gateway keeps a cached
  policy before invoking the authorizer again. Default 5 minutes,
  max 1 hour.
- **LRU cache** — a least-recently-used cache. Bounded by size
  (number of entries) and time (per-entry TTL). The reference
  implementation in this section.

## Lecture

A TOKEN authorizer is fine for "the client sends a JWT in the
Authorization header and that's the whole story." But what if:

- the client is a JavaScript widget that **can't** set custom
  headers (because CORS)?
- the identity is in **multiple** fields (a username in the query
  string *and* a token in a header)?
- the identity depends on a **stage variable** (a different
  signing key per stage)?

These are the use cases for a **REQUEST** authorizer. It gets the
full event:

```json
{
  "type": "REQUEST",
  "methodArn": "arn:aws:execute-api:us-east-1:111:abcd/prod/GET/admin/reindex",
  "resource": "/admin/reindex",
  "path": "/admin/reindex",
  "httpMethod": "GET",
  "headers": { "X-Tenant": "acme", … },
  "queryStringParameters": { "user": "alice", "token": "xyz" },
  "pathParameters": {},
  "stageVariables": { "stage": "prod" },
  "requestContext": { … }
}
```

And — critically — you tell API Gateway *which* parts of the
request make up the **cache key**:

```bash
aws apigateway create-authorizer \
  --rest-api-id abcd \
  --name param-authorizer \
  --type REQUEST \
  --authorizer-uri "arn:aws:lambda:…:function:my-authorizer" \
  --identity-source "method.request.querystring.user,method.request.querystring.token" \
  --authorizer-result-ttl-in-seconds 300
```

For a request `GET /admin/reindex?user=alice&token=xyz`, the cache
key is the concatenation `alice,xyz`. A subsequent request with the
same `user` and `token` shares the cached policy; a request with a
different `user` or `token` gets a fresh authorizer invocation.

### The next four lectures

- **L17 — REQUEST event shape.** Every field in the event, what it
  contains, and the common gotchas (`null` vs missing, case
  sensitivity, multi-value headers).
- **L18 — `IdentitySource` and `ReauthorizeEvery`.** How to pick the
  cache key, how long to cache, and the trade-offs.
- **L19 — LRU + TTL.** A thread-safe Python implementation of the
  cache, with eviction, TTL, and observability.
- **L20 — End-to-end.** The working code. A query-string-based
  authorizer (`?user=alice&token=…`) that verifies the token and
  caches the policy for 5 minutes.

By the end of L20 you'll have an authorizer you can drop in front
of a real API Gateway endpoint.

## Hands-on

No code yet. Make sure you have the libraries:

```bash
pip install 'pyjwt>=2.8.0' 'cryptography>=42.0'
```

## Quiz prep

- What's the difference between a TOKEN and a REQUEST authorizer?
- What is the cache key derived from?
- What's the default `ReauthorizeEvery`? (5 minutes)

## Further reading

- AWS docs: [Input to a Lambda REQUEST authorizer](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-lambda-authorizer-input.html).

## What's next

**L17 — The API Gateway REQUEST Event** — every field, every
gotcha.