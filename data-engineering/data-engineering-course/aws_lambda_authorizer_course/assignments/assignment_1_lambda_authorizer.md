# Assignment 1 — Build a Complete Lambda Authorizer Stack

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Time estimate:** 6–8 hours
> **Difficulty:** Intermediate
> **Builds on:** Sections 2 (JWT basics), 3 (TOKEN authorizer), 4 (REQUEST authorizer + cache)

## Goal

Build a single **multi-tenant** REST API in API Gateway with **two
authorizers** layered on top of the same set of routes. The same Lambda
function behind the API serves both authenticated and unauthenticated
paths, but the path the request takes is determined by which authorizer
fires.

| Method + Path | Authorizer | Required claims |
|---|---|---|
| `GET /public/health` | none (open) | — |
| `GET /public/version` | none (open) | — |
| `GET /orders` | `token-auth` (HS256) | `sub`, `tenant` |
| `GET /orders/{id}` | `token-auth` (HS256) | `sub`, `tenant` |
| `POST /admin/reindex` | `param-auth` (RS256 + JWKS) | `scope=admin` |

The `param-auth` authorizer pulls `user` and `token` out of the **query
string** (`?user=…&token=…`) and caches the resulting policy for 5
minutes per `(user, token)` pair.

## What you deliver

1. A working REST API in `us-east-1` (use `moto` mocks for CI; deploy
   with `sam` for the real-AWS run).
2. The `token-authorizer` Lambda function (HS256 JWT).
3. The `param-authorizer` Lambda function (RS256, JWKS-cached, with an
   in-memory LRU policy cache with TTL).
4. The downstream `orders` Lambda (returns a hard-coded list of orders
   for the tenant in the `context` map).
5. A `tests/test_*.py` suite — at least 12 `moto` tests — that exercises
   each authorizer end-to-end against a mocked API Gateway.
6. A `README.md` that documents:
   - the policy for rotating the RS256 signing key
   - the cache key + TTL you chose, and why
   - the failure modes each authorizer handles
   - the CloudWatch metric you would emit per request

## Acceptance criteria

- [ ] All 12+ `moto` tests pass with `pytest -q`.
- [ ] `python scripts/run_all_tests.py -v` exits 0.
- [ ] `sam local start-api` returns 200 from `/public/health` and 401
      from `/orders` with no `Authorization` header.
- [ ] `/orders` with a valid HS256 token returns a 200 and the response
      body echoes the `tenant` claim.
- [ ] `/orders` with an expired token returns 401.
- [ ] `/admin/reindex` with a valid RS256 + `scope=admin` token returns
      202; with a token missing `scope=admin`, returns 403.
- [ ] The `param-auth` authorizer runs the **validator exactly once**
      for two consecutive identical requests inside the TTL, and runs it
      again after the TTL elapses (write a test for this).
- [ ] The authorizer Lambda is **idempotent** — running the same event
      twice returns the same `principalId` and the same `policyDocument`.

## Stretch goals

- Wire a **Cognito User Pool** authorizer in addition to the two custom
  authorizers, and have it protect a `GET /me` route.
- Add a **CloudWatch alarm** that fires when the `Deny` count in the
  authorizer's log group exceeds 100 in 5 minutes.
- Switch the in-process LRU cache for a **DAX-fronted DynamoDB cache**
  so the policy survives a cold start.

## Submission

A zip of the assignment directory (without `.venv/`) plus the
`pytest -v` output. Tag the git commit `assignment-1-submission`.

Good luck — and remember: a Lambda Authorizer is **the only** place
where a human-shaped credential crosses into your infrastructure, so the
quality of the code in those 100 lines matters more than almost any
other Lambda in the system.
