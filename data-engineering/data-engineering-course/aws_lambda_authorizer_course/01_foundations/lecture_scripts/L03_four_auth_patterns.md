---
lecture: L03
title: "The Four Auth Patterns in API Gateway (IAM, Cognito, Lambda, API Keys)"
duration: "10:00"
section: 1
prereqs: ["L02"]
---

# L03 — The Four Auth Patterns in API Gateway

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 1 — Foundations
> **Duration:** 10:00

## Prereqs

- L02 — request lifecycle.

## Key terms

- **IAM auth** — `AWS Signature V4` signing. The client has long-lived
  IAM credentials (access key + secret) and signs every request.
- **Cognito User Pool authorizer** — built-in. Verifies a JWT minted
  by a Cognito User Pool. No code to write.
- **Lambda Authorizer** — custom. Your code, your logic, your choice
  of token format.
- **API Key** — a static secret tied to a **Usage Plan**. Throttles
  and meters; doesn't authenticate (on its own).
- **Mutual TLS** — client certificates verified at the load balancer.
  Out of scope for this course, but mention it to your security team.

## Lecture

API Gateway offers four built-in auth patterns. Picking the right one
is the single biggest decision you'll make for your API. Here's the
cheat sheet:

| Pattern | AuthN | AuthZ | Where to use |
|---|---|---|---|
| **IAM (SigV4)** | AWS access key | IAM policies | Service-to-service inside AWS |
| **Cognito User Pool** | Cognito-issued JWT | Cognito groups + Lambda authorizer post-auth | Mobile / web end users |
| **Lambda Authorizer** | Anything you can code | Anything you can code | Partner integrations, OIDC, internal SSO, custom tokens |
| **API Key + Usage Plan** | None (just a shared secret) | Throttle / quota | Metering, soft throttling for B2B |

### IAM (SigV4)

Every AWS SDK signs requests by default. If your client is *another
Lambda in the same account*, IAM auth is almost always the right
answer: zero new infra, zero new code, fine-grained policies with
`Resource` and `Action` already wired up. The downside is that the
client has to hold long-lived AWS credentials, which is a non-starter
for browser and mobile clients.

### Cognito User Pool

If your end users log in with a username and password through a
managed UI, Cognito User Pool is the path of least resistance. The
JWT is signed by Cognito; the JWKS endpoint is at
`https://cognito-idp.<region>.amazonaws.com/<userpool-id>/.well-known/jwks.json`;
API Gateway verifies it with zero custom code. The downside is
that you're locked into Cognito's user model and you can only
customize the post-auth step through a *second* Lambda Authorizer.

### Lambda Authorizer

The most flexible. You can verify any token you like, pull identity
out of headers, query strings, stage variables, or even call out to
an external IdP. The downside is that you **own the code** — and
every bug in that code is a security bug.

This is the pattern this course is about. By the end of the course
you'll be able to reach for it confidently.

### API Key

A static, opaque string the client sends in an `x-api-key` header.
API Gateway checks the key against a **Usage Plan** and applies the
plan's throttle and quota. **API Keys are not authentication** —
they're a metering and soft-throttling mechanism. Don't rely on them
as your only line of defense.

### The decision tree

```
                 ┌── Is the client in your AWS account?
                 │      YES → IAM (SigV4)
                 │      NO  ──┐
                 │            │
                 │            ├── Are end users logging in with username/password?
                 │            │      YES → Cognito User Pool
                 │            │      NO  ──┐
                 │            │            │
                 │            │            ├── Do you need a custom token format, an
                 │            │            │   external IdP, or claim-based policies?
                 │            │            │      YES → Lambda Authorizer  ← this course
                 │            │            │      NO  → Cognito + API Gateway native
                 │            │            │
                 │            │            └── Do you need metering / quota only?
                 │            │                   YES → API Key on top of the above
```

### A real example

For the public-facing API in the parent `aws_lambda_course` we use:

- **Cognito User Pool** for browser / mobile end users (so they can
  sign up, reset their password, get a JWT).
- **Lambda Authorizer** for service-to-service calls from a partner
  integration that already issues its own JWTs signed with RS256.
- **API Key** layered on top, so we can meter and throttle specific
  high-volume partners.
- **IAM (SigV4)** for calls from other AWS Lambdas in the same
  account (so internal services don't need to mint a JWT).

Four auth patterns, four different consumers, all on the same API.

## Hands-on

There's no code, but sketch the decision tree for *your* API. What
patterns apply? Where do they overlap?

## Quiz prep

- Which auth pattern is *not* authentication? (API Key)
- What's the difference between a Cognito User Pool and a Lambda
  Authorizer when both are validating a JWT?
- Can you layer more than one auth pattern on the same method? (Yes.)

## Further reading

- AWS docs: [Choose between auth types](https://docs.aws.amazon.com/apigateway/latest/developerguide/choose-auth-type.html)
- The companion `../aws_lambda_course/09_api_security_lambda_cognito_auth/`
  section (a deeper walk-through of the same four patterns in context).

## What's next

**L04 — Anatomy of an IAM Policy Document** — the JSON shape API
Gateway requires as the response of a Lambda Authorizer, in detail.
