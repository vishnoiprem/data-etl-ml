---
lecture: L18
title: "IdentitySource, Multi-Identity-Source & ReauthorizeEvery"
duration: "20:00"
section: 4
prereqs: ["L17"]
---

# L18 — IdentitySource, Multi-Identity-Source & ReauthorizeEvery

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 4 — Request-Parameter Authorizer & Policy Caching
> **Duration:** 20:00

## Prereqs

- L17 — REQUEST event shape.

## Key terms

- **`IdentitySource`** — the comma-separated list of expressions
  that make up the cache key. Each expression is one of:
  - `method.request.header.<name>`
  - `method.request.querystring.<name>`
  - `method.request.path.<name>`
  - `method.request.context.<name>`
  - `stageVariables.<name>`
- **`ReauthorizeEvery`** — how long API Gateway keeps a cached
  policy. Default 300 s (5 min), max 3600 s (1 h).
- **Cache scope** — per-API, per-stage. A cache entry created by
  one Lambda Authorizer is shared by all methods that use the same
  authorizer in the same stage.
- **Cache miss** — when no cached policy exists for the cache key.
  API Gateway invokes the authorizer Lambda. (The authorizer's
  internal LRU cache is *separate* — see L19.)
- **Stale-token exposure** — the maximum time a token can remain
  accepted after the IdP has revoked it. Bounded by
  `ReauthorizeEvery` + the authorizer's internal LRU TTL.

## Lecture

The `IdentitySource` is the most important configuration on a
REQUEST authorizer. It defines *which* part of the request makes
up the cache key. Pick the wrong one and you either (a) blow the
cache by being too granular, or (b) under-cache by being too
coarse and letting the wrong user inherit someone else's policy.

### The identity-source grammar

Each expression is a path into the request. The full grammar is:

```
method.request.header.<name>          # header value
method.request.multivalueheader.<name>  # multi-value header as list
method.request.querystring.<name>     # query string value
method.request.multivaluequerystring.<name>  # multi-value query
method.request.path.<name>            # path parameter
stageVariables.<name>                 # stage variable
context.<name>                        # request context field
```

The list is comma-separated; the values for a request are
concatenated with commas. So an `IdentitySource` of
`method.request.querystring.user,method.request.querystring.token`
with a request `?user=alice&token=xyz` produces a cache key
`alice,xyz`.

### Picking the right identity sources

The rule of thumb: **include every field that affects the policy
decision**, and **exclude every field that doesn't**.

- ✅ `method.request.header.Authorization` — if the token is in
  a header.
- ✅ `method.request.querystring.token` — if the token is in the
  query string.
- ✅ `stageVariables.signingKey` — if different stages have
  different keys.
- ❌ `method.request.header.User-Agent` — the policy shouldn't
  depend on the UA.
- ❌ `method.request.querystring.cache_buster` — random noise that
  would defeat the cache.
- ❌ The full body — bodies are big and unique; including them
  makes the cache useless.

### Multi-Identity-Source

A common pattern: identify the caller by *both* their username
*and* their token:

```
method.request.querystring.user,method.request.querystring.token
```

The cache key is `user,token`. A request with `?user=alice&token=t1`
is cached separately from `?user=alice&token=t2`. A request with
`?user=bob&token=t1` is a separate cache entry.

This is the right pattern when the same user has multiple
concurrent tokens (e.g. one token per device).

### Single-Identity-Source (token only)

If you cache on the token alone, the same token is treated as
the same principal regardless of other request fields:

```
method.request.querystring.token
```

This is the pattern for a pure-token API. It is simpler to reason
about but it means a cached Allow policy for `?token=xyz` will
match *any* request that includes `token=xyz`, even if the path
or method differs. In practice, API Gateway scopes the cache per
method, so this is usually fine.

### `ReauthorizeEvery`

The cache duration. Default 300 s, max 3600 s. The trade-off:

- **Shorter TTL** → more authorizer invocations → more AWS bill,
  more latency, but shorter stale-token exposure.
- **Longer TTL** → fewer invocations → lower bill, lower latency,
  but longer stale-token exposure.

For a typical access-token-based system, **5 minutes (300 s)** is
the sweet spot. It matches most access-token TTLs (15 min to 1 h)
closely enough that the worst-case stale-token window is the
cache TTL itself, not the access-token TTL.

For a system that issues very short-lived tokens (1–5 min) the
cache TTL doesn't matter much — the access token itself will
expire before the cache does. For a system that issues long-lived
tokens (24 h) the cache TTL matters a lot — an attacker who
captures a token has 24 h to use it *or* until the cache
revalidates, whichever is shorter.

### Stale-token exposure

This is the **most important** number to compute for your
authorizer. It's the maximum time between:

1. the IdP revoking a token (e.g. user logs out), and
2. your authorizer noticing the revocation.

It is bounded by:

```
stale_token_exposure = min(
    access_token_ttl,                # the IdP's clock
    reauthorize_every,               # API Gateway's clock
    authorizer_internal_cache_ttl,   # your LRU's clock
)
```

If your access tokens live 1 h and your cache TTL is 5 min, a
revoked token is honored for at most 5 min. If your access tokens
live 5 min and your cache TTL is 1 h, a revoked token is honored
for at most 5 min. Either way, the bottleneck is the *shortest*
of the three.

### Common pitfalls

- **Not using `stageVariables` for stage-specific keys.** If you
  have `prod` and `staging` deployments with different signing
  keys, the cache key must include the stage. Otherwise, a token
  signed for `staging` is honored on `prod`.
- **Including the body in the cache key.** Defeats the cache.
- **Including PII (email, phone) in the cache key.** Bakes PII
  into CloudWatch logs and into the cache for up to 1 h.
- **Setting `ReauthorizeEvery` to 0.** The API Gateway docs
  explicitly forbid this; the minimum is 0 (which means "no
  cache") and the maximum is 3600.

## Hands-on

No code yet. The hands-on is L20. For now, sketch out the
`IdentitySource` and `ReauthorizeEvery` for the *assignment 1*
endpoints:

| Method + Path | `IdentitySource` | `ReauthorizeEvery` |
|---|---|---|
| `GET /orders` | `method.request.header.Authorization` | 300 |
| `GET /admin/reindex` | `method.request.querystring.user,method.request.querystring.token` | 300 |

## Quiz prep

- What's the max value of `ReauthorizeEvery`? (3600 s.)
- Why should you include `stageVariables` in the cache key when
  you have stage-specific secrets?
- What three numbers bound the stale-token exposure?

## Further reading

- AWS docs: [Identity sources for a Lambda authorizer](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-lambda-authorizer-input.html).

## What's next

**L19 — Building an LRU Cache with TTL** — the in-process cache
that lives inside the authorizer Lambda itself.