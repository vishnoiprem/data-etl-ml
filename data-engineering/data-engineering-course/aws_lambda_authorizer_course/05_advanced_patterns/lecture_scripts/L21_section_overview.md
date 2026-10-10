---
lecture: L21
title: "Section Overview — Beyond REST APIs"
duration: "4:00"
section: 5
prereqs: ["L20"]
---

# L21 — Section Overview — Beyond REST APIs

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 5 — Advanced Patterns
> **Duration:** 4:00

## Prereqs

- L20 — end-to-end REQUEST authorizer.

## Key terms

- **CloudFront Lambda@Edge** — a Lambda function attached to a
  CloudFront distribution that runs at the edge, near the user, on
  every request.
- **WebSocket API** — the API Gateway WebSocket protocol, which
  keeps a persistent connection open between the client and the
  server.
- **OIDC (OpenID Connect)** — an identity layer on top of OAuth2
  that defines how an IdP issues ID tokens (JWTs) to clients.
- **Trade-off matrix** — the four-axis decision tree (latency,
  cost, complexity, security) that tells you when a Lambda
  Authorizer is the right choice.

## Lecture

You now have a working TOKEN and a working REQUEST authorizer. In
this section we cover the four scenarios that take you beyond the
basics:

### L22 — CloudFront Lambda@Edge

If your API is fronted by a CloudFront distribution (which it
often is for global caching), you can attach a Lambda to the
viewer-request event. The Lambda runs at the edge, *before* the
request reaches API Gateway. It can:

- Reject unauthenticated requests (403) without ever touching
  origin.
- Rewrite the URL or headers before they reach API Gateway.
- Inject identity headers for downstream services.

This is the right pattern when:

- your API has a global user base and you want to authenticate
  close to the user;
- you want to **block bad traffic at the edge** rather than
  paying for an API Gateway → Lambda round trip for every 403.

### L23 — WebSocket auth challenges

API Gateway WebSocket APIs have a different auth model from REST
APIs: the client connects first (with no auth) and then sends
messages, some of which contain auth tokens.

A common pattern: reject the initial `$connect` if the URL has no
token, and reject any message that doesn't include a fresh token.

A Lambda Authorizer is the standard tool for the `$connect`
decision. For the per-message decision, you typically put the
check inside the integration Lambda (the Lambda that handles the
WebSocket messages).

### L24 — OIDC integration

If your IdP is Auth0, Okta, or Cognito, the tokens they issue are
OIDC-compliant JWTs. Your Lambda Authorizer just has to:

1. Fetch the JWKS endpoint at
   `https://<idp-host>/.well-known/jwks.json`.
2. Cache it (TTL ~1 h).
3. Verify the token's signature against the right key (looked up
   by `kid`).
4. Check `iss`, `aud`, `exp` per L07.

The pattern is identical to the one we walked through in L09; the
only difference is the URL of the JWKS endpoint.

### L25 — When **not** to use a Lambda Authorizer

Not every API needs a Lambda Authorizer. The trade-off matrix:

| Concern | Lambda Authorizer | Alternative |
|---|---|---|
| Latency | Adds 5–50 ms per request | IAM auth = 0 ms; Cognito User Pool = 1–2 ms |
| Cost | $0.20/M invocations + 128 MB | $0 for IAM; Cognito = $0.15/M MAU |
| Code you own | Yes | None (for IAM / Cognito native) |
| Custom tokens | Yes (any format) | No (Cognito is locked to Cognito) |
| Token rotation | Manual (you write it) | Built-in (Cognito rotates for you) |

Reach for a Lambda Authorizer when you need **a custom token
format** or **custom authorization logic**. Otherwise, use the
managed option.

## Hands-on

No code in this section. The hands-on is the **assignment 1**,
which combines sections 2, 3, and 4.

## Quiz prep

- What's the difference between Lambda@Edge and a Lambda Authorizer?
- When should you authenticate at the edge vs at API Gateway?
- What's the trade-off between Lambda Authorizer latency and
  Cognito User Pool auth?

## Further reading

- AWS docs: [Using CloudFront Lambda@Edge](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/lambda-edge-how-it-works.html).

## What's next

**L22 — CloudFront Lambda@Edge — Viewer-Request Authentication**.