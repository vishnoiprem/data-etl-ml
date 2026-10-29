---
lecture: L25
title: "When NOT to Use a Lambda Authorizer — Design Trade-offs"
duration: "16:00"
section: 5
prereqs: ["L24"]
---

# L25 — When NOT to Use a Lambda Authorizer — Design Trade-offs

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 5 — Advanced Patterns
> **Duration:** 16:00

## Prereqs

- L24 — OIDC integration.

## Key terms

- **Latency budget** — the maximum time you can afford to add to a
  request before user experience degrades. Typically 100–200 ms
  for a public API.
- **Cost ceiling** — the maximum $ / month you're willing to spend
  on auth. For a small API, even $5/month is noticeable.
- **Code surface area** — the amount of code you have to write,
  test, and audit. Lambda Authorizers add ~100 lines + tests.
- **Threat model** — what attacks are you actually defending
  against? Drives whether the simpler options are sufficient.

## Lecture

The closing lecture. We've covered the design, the implementation,
and the advanced patterns. Now we step back and ask: **when is a
Lambda Authorizer the wrong choice?**

### The trade-off matrix

| Concern | Lambda Authorizer | IAM | Cognito User Pool | API Key |
|---|---|---|---|---|
| Latency per request | 5–50 ms | 0 ms | 1–2 ms | 1 ms |
| Cost | $0.20/M + compute | $0 | $0.15/M MAU | $0 |
| Code you own | ~100 lines + tests | 0 | 0 | 0 |
| Custom token formats | Yes | No | No | No |
| Authorization logic | Anything you can code | IAM policy | Groups + post-auth Lambda | Throttle + quota |
| Token rotation | Manual | Built-in | Built-in | N/A |
| Operational burden | High | Low | Medium | Low |

### When to skip the Lambda Authorizer

**Skip when you only have IAM-style auth needs.** If your API is
called only by other Lambdas in your AWS account, IAM (SigV4) is
zero-config and zero-cost. Adding a Lambda Authorizer on top is
ceremony.

**Skip when Cognito User Pool is sufficient.** If your end users
log in with username/password and you don't need a custom token
format, Cognito User Pool Authorizer is built-in, audited by AWS,
and rotates keys for you. A Lambda Authorizer that mints and
verifies its own JWTs is strictly worse.

**Skip when API Keys are the right tool.** If you need *metering*
and *throttling*, not authentication, an API Key + Usage Plan is
the answer. Don't roll your own metering in a Lambda Authorizer.

**Skip when the latency budget is too tight.** A Lambda Authorizer
that does a JWKS fetch on every cache miss will add 20–50 ms
above the API Gateway baseline. For a public-facing API on the
edge, that may be more than you can afford.

### When the Lambda Authorizer is the right choice

**Choose when you need a custom token format.** Your partner
already issues JWTs signed with RS256, or you have a legacy
internal system that issues opaque tokens you need to verify
against an internal database. Cognito can't help.

**Choose when you need custom authorization logic.** The token
contains a `scope: admin` claim and you want admin requests to
inherit a wildcard resource. Cognito can do *some* of this through
groups, but it's awkward and a Lambda Authorizer is simpler.

**Choose when the cost of Cognito is too high.** Cognito charges
$0.15 per MAU above the free tier (50k MAU). For a high-volume
internal API this adds up fast; rolling your own JWT verification
in a Lambda Authorizer costs almost nothing.

**Choose when you need to integrate with an external IdP you
don't control.** You're a B2B partner that needs to verify tokens
issued by your customer's IdP (Auth0, Okta, Azure AD). Lambda
Authorizer + JWKS is the standard pattern.

### A decision tree

```
Is the client in your AWS account?
├── Yes → IAM (SigV4). Done.
└── No
    ├── Do you have a managed user directory?
    │   ├── Yes → Cognito User Pool. Done.
    │   └── No
    │       ├── Does your client have a custom token format?
    │       │   ├── Yes → Lambda Authorizer  (this course)
    │       │   └── No
    │       │       ├── Just need throttling?
    │       │       │   ├── Yes → API Key + Usage Plan
    │       │       │   └── No → Cognito User Pool
    │       └── …?
    └── Good day of API building.
```

### The bottom line

A Lambda Authorizer is the **right** answer for ~20% of APIs. For
the other 80%, the managed options are faster, cheaper, and
safer. This course exists so that you can pick the 20% with
confidence.

## Hands-on

There's no code. The hands-on is the **assignment 1** which
combines sections 2–4 into a single working stack.

## Quiz prep

- What's the cost difference between a Lambda Authorizer and Cognito
  User Pool at 1M MAU?
- When would you choose IAM auth over a Lambda Authorizer?
- When would you choose a Lambda Authorizer over Cognito?

## Further reading

- AWS Well-Architected Framework: [Security pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html).
- `../../assignments/assignment_1_lambda_authorizer.md` — the
  graded extension.

## What's next

This is the last lecture. The next thing to do is **assignment 1**,
which ties sections 2–4 together into a single working API.