---
lecture: L01
title: "Course Intro — Why API Security Matters"
duration: "6:00"
section: 1
prereqs: []
downloads:
  - "../../downloads/jwt_cheat_sheet.pdf"
---

# L01 — Course Intro — Why API Security Matters

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 1 — Foundations
> **Duration:** 6:00

## Prereqs

None. This is the very first lecture. No AWS account, no Python install,
no prior auth experience needed.

## Key terms

- **Authentication (AuthN)** — *who is making the request?* Verifies an
  identity (a username, a JWT subject, a client certificate).
- **Authorization (AuthZ)** — *what is that identity allowed to do?*
  Decides whether the request should be allowed to hit the resource
  behind the API.
- **Lambda Authorizer** — a Lambda function that API Gateway invokes
  before the request reaches your backend, and that returns an IAM
  policy that says **Allow** or **Deny**.
- **IAM policy document** — the JSON document API Gateway expects as
  the response of a Lambda Authorizer. Has a `Version`, a list of
  `Statement`s, and either an `Effect: Allow` or `Effect: Deny`.
- **Principal** — the identity the policy is *for*. For a Lambda
  Authorizer this is the `principalId` you return; API Gateway maps
  it to a principal in the policy's `Resource` block.

## Lecture

Hi, I'm Prem Vishnoi — welcome to **AWS Lambda Authorizer — Crash
Course**. In the next six minutes I want to convince you that the
Lambda Authorizer is the most under-rated API Gateway feature, and
that after this course you'll reach for it every time you need
anything more nuanced than "is the request signed with an IAM key?"

### Why API security is hard

Three things have changed in the last decade that turned "we have a
WAF in front of our API" from a sufficient answer to a *non-answer*:

1. **Tokens replaced sessions.** Most public APIs are no longer
   consumed by browsers that hold a session cookie; they're consumed
   by mobile apps, by partner integrations, and by your own internal
   services. The shared secret is a JSON Web Token that the client
   carries in an `Authorization: Bearer …` header. Your API has to
   verify that token, not just look up a session.
2. **Tenants are not equal.** Even a "single-tenant" SaaS app usually
   has internal services, partner integrations, and admin tooling
   that all want different levels of access. The same endpoint might
   be `Allow` for an admin token and `Deny` for a regular user.
3. **Cryptography moves faster than ops can patch.** Algorithms get
   deprecated (RS256 → RS256-PSS), keys get rotated, signing
   identities move between providers. A hard-coded check in your
   backend Lambda is the wrong place to deal with this — the check
   needs to live in a place that's easy to update, easy to test, and
   easy to swap out.

A Lambda Authorizer is that place.

### What a Lambda Authorizer actually is

A Lambda Authorizer is **a small Lambda function that API Gateway
invokes before the request reaches your backend**. The function
receives the request (or a token from the request) and returns an
IAM policy document. API Gateway enforces that policy: if it says
`Allow`, the request continues; if it says `Deny`, API Gateway
returns 403 without ever invoking your backend.

The contract is **three fields**:

```json
{
  "principalId": "user-12345",
  "policyDocument": {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": "execute-api:Invoke",
        "Resource": "arn:aws:execute-api:us-east-1:111122223333:abcd1234/prod/GET/orders"
      }
    ]
  },
  "context": { "sub": "user-12345", "tenant": "acme" }
}
```

That's it. Everything else in this course — JWT verification, JWKS
rotation, policy caching, CloudFront at the edge — is a refinement of
this contract.

### What you'll build

The course is anchored by **three working demos**:

- **Section 2** — verify a JWT from first principles with `pyjwt`
  (signing, expiry, key rotation).
- **Section 3** — a TOKEN authorizer that turns a `Bearer` JWT into
  an `Allow` policy.
- **Section 4** — a REQUEST authorizer that pulls a token from the
  query string, caches the resulting policy for 5 minutes, and uses
  an in-process LRU.

Sections 1 and 5 are conceptual (request lifecycle, OIDC, Lambda@Edge,
trade-offs).

### The 4 downloads

You have **4 downloads** in `downloads/` (linked at the top of this
file):

| # | File | When you'll use it |
|---|---|---|
| 1 | `jwt_cheat_sheet.pdf` | Throughout — every claim, every algorithm, one page |
| 2 | `iam_policy_cheat_sheet.pdf` | L04 onwards — the policy contract |
| 3 | `api_gateway_event_shapes.pdf` | L12, L17 — TOKEN vs REQUEST event reference |
| 4 | `lambda_authorizer_template_pack.zip` | L15, L20 — SAM / CDK starter projects |

## Hands-on

This lecture is orientation only. Your only homework is to skim the
JWT cheat sheet.

```bash
open aws_lambda_authorizer_course/downloads/jwt_cheat_sheet.pdf
```

In L02 we'll walk through the request lifecycle and see exactly where
the authorizer fits.

## Quiz prep

- What's the difference between authentication and authorization?
- What three fields does API Gateway expect from a Lambda Authorizer?
- How many working demos does this course build? (3)

## Further reading

- Download: [`../../downloads/jwt_cheat_sheet.pdf`](../../downloads/jwt_cheat_sheet.pdf)
- `../../SYLLABUS.md` — full lecture map.
- `../../README.md` — repo layout.

## What's next

**L02 — Where the Lambda Authorizer Fits in the Request Lifecycle** —
we'll draw the full sequence from the client through API Gateway, the
authorizer, the IAM policy, and back to your backend.
