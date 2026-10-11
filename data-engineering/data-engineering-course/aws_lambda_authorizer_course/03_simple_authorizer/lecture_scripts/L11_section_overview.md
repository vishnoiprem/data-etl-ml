---
lecture: L11
title: "Section Overview — TOKEN Authorizer Event Shape"
duration: "6:00"
section: 3
prereqs: ["L10"]
---

# L11 — Section Overview — TOKEN Authorizer Event Shape

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 3 — Simple Token-Based Lambda Authorizer
> **Duration:** 6:00

## Prereqs

- L10 — JWT verification in Python.

## Key terms

- **TOKEN authorizer** — the API Gateway authorizer type that is
  handed a single string (the value of the `Authorization` header)
  and is expected to return an Allow/Deny policy.
- **REQUEST authorizer** — the richer authorizer type that gets the
  full HTTP request. We cover that in section 4.
- **Authorization header** — the standard HTTP header used to carry
  the bearer token. `Authorization: Bearer eyJ…`.
- **`methodArn`** — the ARN of the method being invoked. The
  canonical resource to allow in the policy.
- **`lambda_handler`** — the entry point API Gateway invokes. Same
  shape as any other Lambda: `(event, context) -> response`.

## Lecture

A TOKEN authorizer is the simplest of the two authorizer types. The
event you receive has only three fields that matter:

```json
{
  "type": "TOKEN",
  "authorizationToken": "Bearer eyJ…",
  "methodArn": "arn:aws:execute-api:us-east-1:111:abcd/prod/GET/orders"
}
```

The handler must return either an Allow or a Deny policy:

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
  },
  "context": { "sub": "user-1", "tenant": "acme", "scope": "read" }
}
```

The next four lectures unpack each piece.

### Lecture roadmap

- **L12 — The TOKEN event in detail.** `type`, `authorizationToken`,
  `methodArn` — what they are, what they look like in CloudWatch,
  what to do if any of them is missing.
- **L13 — Building the Allow policy.** Walking through the
  `policyDocument` line by line. Why `Action: execute-api:Invoke`
  is the only action. Why `Resource` should almost always be the
  `methodArn` from the event.
- **L14 — The `context` map.** How to surface JWT claims to the
  integration. The two rules (must be flat, must be strings) and
  why they exist.
- **L15 — End-to-end.** Wire it all together: a real
  `lambda_handler`, a real event, six tests.

By the end of L15 you have a working authorizer you could deploy
in front of any API Gateway REST API in `us-east-1`.

## Hands-on

No code yet. Just make sure you have the libraries from L10:

```bash
pip install 'pyjwt>=2.8.0' 'cryptography>=42.0'
```

## Quiz prep

- How many fields are in a TOKEN authorizer event? (3 — `type`,
  `authorizationToken`, `methodArn`.)
- What action does an Allow policy always set? (`execute-api:Invoke`.)
- What two rules apply to the `context` map? (Flat, strings only.)

## Further reading

- AWS docs: [Input to a Lambda TOKEN authorizer](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-lambda-authorizer-input.html).
- Download: [`../../downloads/api_gateway_event_shapes.pdf`](../../downloads/api_gateway_event_shapes.pdf).

## What's next

**L12 — The API Gateway TOKEN Event** — the event in detail, field
by field.