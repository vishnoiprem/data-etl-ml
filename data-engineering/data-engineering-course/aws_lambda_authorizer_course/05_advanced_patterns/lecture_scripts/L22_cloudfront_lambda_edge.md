---
lecture: L22
title: "CloudFront Lambda@Edge — Viewer-Request Authentication"
duration: "18:00"
section: 5
prereqs: ["L21"]
---

# L22 — CloudFront Lambda@Edge — Viewer-Request Authentication

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 5 — Advanced Patterns
> **Duration:** 18:00

## Prereqs

- L21 — section overview.

## Key terms

- **Lambda@Edge** — a Lambda function that runs in a CloudFront
  edge location, close to the user. Reached via the
  `cloudfront-lambda` event source.
- **Origin-request vs viewer-request** — the two events Lambda@Edge
  can subscribe to. Viewer-request runs *before* the request
  reaches origin; origin-request runs after CloudFront has decided
  to forward to origin.
- **Edge constraints** — Lambda@Edge functions have a smaller
  memory / timeout envelope than regular Lambda. No environment
  variables (you have to bake config into the deployment package).
- **Geographic distribution** — Lambda@Edge runs in ~13 AWS regions
  globally; regular Lambda runs in 1.

## Lecture

If your API is fronted by CloudFront (which is the case for most
public APIs), you have a choice: authenticate at the edge (with
Lambda@Edge) or at origin (with API Gateway + Lambda Authorizer).
This lecture walks through when to pick which.

### When to authenticate at the edge

Authenticate at the edge when:

- You want to **block bad traffic early**, before CloudFront calls
  origin. This is the most common reason.
- Your API has a global user base and you want to validate tokens
  in the AWS region closest to the user.
- You're caching content at CloudFront and you need to key the
  cache by identity (e.g. per-tenant caching).

Authenticate at API Gateway (origin) when:

- The API is regional (not global). Lambda@Edge adds latency
  penalty for going edge → origin.
- The token verification is expensive (e.g. requires a database
  lookup that you want to run close to your data).
- You don't have CloudFront in front of API Gateway.

### The viewer-request event

A Lambda@Edge viewer-request handler receives:

```json
{
  "Records": [
    {
      "cf": {
        "config": {
          "distributionId": "EDFDVBD6EXAMPLE",
          "eventType": "viewer-request",
          "requestId": "..."
        },
        "request": {
          "clientIp": "203.0.113.42",
          "headers": { … },
          "method": "GET",
          "querystring": "user=alice&token=xyz",
          "uri": "/orders"
        }
      }
    }
  ]
}
```

The handler returns either:

- a **modified request** (allow, with optional rewrites), or
- a **response** (reject, e.g. 401 / 403).

### A reference implementation

```python
import base64
import json


def handler(event, context):
    request = event["Records"][0]["cf"]["request"]
    qs = request.get("querystring", "")
    token = _extract_token(qs)
    if not token:
        return _reject(401, "missing token")

    if not _verify_jwt(token):
        return _reject(403, "invalid token")

    return request  # allow


def _reject(status: int, body: str) -> dict:
    return {
        "status": status,
        "statusDescription": "Unauthorized",
        "headers": {
            "content-type": [{"key": "Content-Type", "value": "text/plain"}],
        },
        "body": body,
    }
```

### Constraints to remember

- **No environment variables.** Bundle config into the deployment
  package or fetch at cold start.
- **No layers.** Same.
- **Smaller memory / timeout envelope.** 128 MB–3 GB, 5 s–30 s
  (depending on event type).
- **Read-only file system.** You can write to `/tmp` but the
  changes don't persist.
- **No VPC.** Lambda@Edge doesn't run in a VPC.

### Cost

Lambda@Edge is **$0.60 per 1M invocations** plus
**$0.0000500025 per GB-second** of compute time. Roughly 3× the
cost of a regular Lambda invocation, but you save the API Gateway
→ Lambda round trip on rejected traffic (which is the
expensive part of an API).

### Debugging

Lambda@Edge logs go to CloudWatch in **us-east-1**, regardless
of where the function actually ran. Set up a CloudWatch dashboard
in `us-east-1` before you deploy.

X-Ray is supported but the UI is harder to navigate because the
trace crosses regions.

## Hands-on

There's no code in this lecture — Lambda@Edge functions deploy
through CloudFront, not API Gateway, and require a multi-region
distribution to test end-to-end. The walk-through in the lecture
video covers the deployment step by step.

## Quiz prep

- What's the difference between viewer-request and origin-request?
- Why can't Lambda@Edge use environment variables?
- What's the cost difference between Lambda@Edge and a regular
  Lambda invocation?

## Further reading

- AWS docs: [Using Lambda@Edge](https://docs.aws.amazon.com/lambda/latest/dg/lambda-edge.html).

## What's next

**L23 — Custom Auth Challenges for WebSocket APIs**.