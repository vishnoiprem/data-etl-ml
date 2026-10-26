---
lecture: L04
title: "Anatomy of an IAM Policy Document (Allow, Deny, principalId, context)"
duration: "8:00"
section: 1
prereqs: ["L03"]
---

# L04 — Anatomy of an IAM Policy Document

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 1 — Foundations
> **Duration:** 8:00

## Prereqs

- L03 — the four auth patterns.

## Key terms

- **`Version: "2012-10-17"`** — the IAM policy language version. It's
  the only value API Gateway accepts; don't use `"2008-10-17"`.
- **`Statement[].Effect`** — `"Allow"` or `"Deny"`. A `Deny` always
  wins over an `Allow` (explicit deny trumps).
- **`Statement[].Action`** — for an API Gateway authorizer, this is
  almost always `"execute-api:Invoke"`.
- **`Statement[].Resource`** — the ARN(s) the policy applies to. The
  canonical value is the `methodArn` from the event.
- **`principalId`** — the identity the policy is *for*. API Gateway
  forwards it as the integration's `event.requestContext.authorizer.principalId`
  and uses it for CloudWatch metrics.
- **`context`** — a flat dict of strings API Gateway forwards to the
  integration as `X-Amzn-Apigateway-…` headers and as
  `event.requestContext.authorizer` JSON. **Must be flat** (no nested
  objects) and **values must be strings**.

## Lecture

The IAM policy document is the contract between your authorizer and
API Gateway. Get it wrong and you either accidentally allow
everything (a security incident) or accidentally deny everything (a
site reliability incident). Let's walk through every field.

### The minimum valid Allow

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
  }
}
```

That is **the entire response** API Gateway needs to let the request
through. `principalId` becomes the principal in the integration's
event.

### Wildcards

You can use `*` in `Resource` to allow multiple methods at once:

```json
"Resource": [
  "arn:aws:execute-api:us-east-1:111122223333:abcd1234/prod/GET/orders",
  "arn:aws:execute-api:us-east-1:111122223333:abcd1234/prod/POST/orders"
]
```

or with a wildcard segment:

```json
"Resource": "arn:aws:execute-api:us-east-1:111122223333:abcd1234/prod/GET/orders/*"
```

The safest pattern is to echo back the `methodArn` from the event
unchanged. If you want to allow **more** than the caller asked for
(say, the JWT contains a `scope: admin` claim and you want to grant
access to all paths), you can expand the `Resource` list. If you
want to allow **less** than the caller asked for, return a `Deny`.

### The minimum valid Deny

```json
{
  "principalId": "unauthorized",
  "policyDocument": {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Deny",
        "Action": "execute-api:Invoke",
        "Resource": "arn:aws:execute-api:us-east-1:111122223333:abcd1234/prod/GET/orders"
      }
    ]
  }
}
```

You can omit `principalId` in a Deny (API Gateway will substitute
`"unauthorized"`), but it's clearer to set it.

### The `context` map

The third top-level field is optional but it's where you pass
**identity information** to the integration:

```json
{
  "principalId": "user-12345",
  "policyDocument": { … },
  "context": {
    "sub": "user-12345",
    "tenant": "acme",
    "scope": "read"
  }
}
```

The `context` becomes:

- `event.requestContext.authorizer.{sub,tenant,scope}` in the
  backend Lambda's event JSON.
- `X-Amzn-Apigateway-Authorizer-Sub`, `X-Amzn-Apigateway-Authorizer-Tenant`,
  `X-Amzn-Apigateway-Authorizer-Scope` request headers on the way
  to the integration.

**Two hard rules:**

1. The dict must be **flat**. No nested objects, no lists.
2. All values must be **strings**. If your JWT has a numeric `iat`,
   convert it: `str(claims["iat"])`.

Violate either rule and API Gateway returns 500 to the client
without invoking your backend — and the error is **very** hard to
debug because it shows up only in CloudWatch.

### Putting it all together

The full happy-path response:

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
  "context": {
    "sub": "user-12345",
    "tenant": "acme",
    "scope": "read"
  }
}
```

That's the contract. Memorize it.

## Hands-on

In `03_simple_authorizer/code/token_authorizer.py` (L15) we'll
implement the `_allow()` and `_deny()` helpers in Python. For now,
write the policy out by hand for a hypothetical JWT with claims
`{"sub": "u-1", "tenant": "acme", "scope": "admin"}` and the
`methodArn` `arn:aws:execute-api:us-east-1:111:abcd/prod/POST/admin/reindex`.

## Quiz prep

- What's the only valid `Version` string?
- Can `context` contain a nested dict? (No.)
- What happens if you return a `Deny` with `principalId: "user-1"`?

## Further reading

- Download: [`../../downloads/iam_policy_cheat_sheet.pdf`](../../downloads/iam_policy_cheat_sheet.pdf)
- AWS docs: [IAM JSON policy reference](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_grammar.html)

## What's next

**Section 2 — JWT Basics (L05–L10)**: we take a deep dive into JSON Web
Tokens. The authorizer can't validate a token if it doesn't know what
a token is.
