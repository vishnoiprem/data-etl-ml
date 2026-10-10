---
lecture: L13
title: "Building the Allow Policy (Resource = methodArn, Action = execute-api:Invoke)"
duration: "16:00"
section: 3
prereqs: ["L12"]
---

# L13 — Building the Allow Policy

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 3 — Simple Token-Based Lambda Authorizer
> **Duration:** 16:00

## Prereqs

- L12 — TOKEN event shape.

## Key terms

- **`Statement[].Action`** — `"execute-api:Invoke"` is the only valid
  action for an API Gateway authorizer policy. Any other action
  will be silently ignored or, worse, accepted as a syntax error
  that breaks every request.
- **`Statement[].Resource`** — the ARN(s) the policy applies to.
  Can be a single string or a list. Wildcards are allowed.
- **`Statement[].Effect`** — `"Allow"` or `"Deny"`. A Deny always
  wins over an Allow.
- **`Version`** — the IAM policy language version. API Gateway only
  accepts `"2012-10-17"`. (The other valid value,
  `"2008-10-17"`, is for IAM users, not API Gateway.)
- **Wildcard expansion** — granting access to more than the caller
  asked for. Useful for scope-based authorization.

## Lecture

This lecture is the cookbook entry for the Allow policy. We'll
build it up from the minimum valid response to the production-grade
version with wildcard resource expansion.

### The minimum valid Allow

```json
{
  "principalId": "user-1",
  "policyDocument": {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": "execute-api:Invoke",
        "Resource": "arn:aws:execute-api:us-east-1:111:abcd/prod/GET/orders"
      }
    ]
  }
}
```

That's it. API Gateway will allow the request.

### The Python that produces it

```python
def _allow(method_arn: str, principal_id: str, context: dict) -> dict:
    return {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "execute-api:Invoke",
                    "Resource": method_arn,
                }
            ],
        },
        "context": context,
    }
```

The helper takes three arguments — the `methodArn`, the
`principalId` (from the JWT `sub`), and the `context` map (from the
JWT claims) — and returns the response dict.

### Wildcard resource expansion

If the JWT carries a `scope: admin` claim, you can grant access to
*all* methods under the same API + stage:

```python
def _allow_with_scope(method_arn: str, principal_id: str, claims: dict) -> dict:
    scope = claims.get("scope", "")

    # Admin scope: allow the whole stage.
    if "admin" in scope.split():
        arn_prefix = method_arn.rsplit("/", 2)[0]  # strip /METHOD/resource
        resource = f"{arn_prefix}/*"
    else:
        resource = method_arn

    return {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "execute-api:Invoke",
                    "Resource": resource,
                }
            ],
        },
        "context": _flatten(claims),
    }
```

This is the canonical pattern for **scope-based authorization**:
the JWT carries the scope, the authorizer maps scope to a
wildcarded resource list.

### Multiple resources

You can also allow a list of resources:

```python
"Resource": [
    "arn:aws:execute-api:us-east-1:111:abcd/prod/GET/orders",
    "arn:aws:execute-api:us-east-1:111:abcd/prod/POST/orders",
]
```

This is useful when a single JWT grants access to a fixed set of
methods (e.g. an integration account that has read access to
`/orders` and `/customers` but nothing else).

### The Deny policy

For completeness:

```python
def _deny(method_arn: str) -> dict:
    return {
        "principalId": "unauthorized",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Deny",
                    "Action": "execute-api:Invoke",
                    "Resource": method_arn,
                }
            ],
        },
    }
```

API Gateway doesn't actually use `principalId` on a Deny, but it's
clearer in CloudWatch if you set it. `"unauthorized"` is the
convention.

### What you should NOT do

- **Don't put `*` for the `Action`.** Only `execute-api:Invoke` is
  valid; the policy language accepts other strings but API Gateway
  will reject them with a 500.
- **Don't use `Version: "2008-10-17"`.** API Gateway rejects it.
- **Don't omit `principalId` from an Allow.** It's optional per the
  AWS docs but CloudWatch metrics will be broken without it.
- **Don't return both an Allow and a Deny statement.** API Gateway
  uses the *first* statement; whichever order you put them in is
  the order they're evaluated. If you Allow first then Deny, the
  Allow wins. If you Deny first then Allow, the Deny wins. The
  cleanest pattern is one statement per response.

### Edge cases

- **Empty `methodArn`.** If the event arrives without a `methodArn`
  (rare, but it happens when API Gateway is misconfigured), your
  Allow policy with `Resource: ""` will silently match nothing.
  Return Deny instead.
- **Multi-region APIs.** If your API is deployed in multiple regions
  and you want one authorizer to handle them all, the `Resource` in
  the policy must include the region from the `methodArn`, not a
  wildcard. The safest pattern is to echo the `methodArn`
  unchanged.

## Hands-on

Open `03_simple_authorizer/code/token_authorizer.py` (L15) and
look at the `_allow()` and `_deny()` helpers. They implement
exactly the patterns from this lecture.

## Quiz prep

- What is the only valid `Action` for an API Gateway authorizer?
- What happens if you put `*` for `Action`?
- What's the safest default for `Resource`?

## Further reading

- AWS docs: [Output from a Lambda TOKEN authorizer](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-lambda-authorizer-output.html).

## What's next

**L14 — Returning Claims via the `context` Map** — how to surface
JWT claims to the integration. The two rules (flat, strings only)
and why they exist.