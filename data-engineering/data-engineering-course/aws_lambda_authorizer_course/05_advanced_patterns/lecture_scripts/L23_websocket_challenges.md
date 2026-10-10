---
lecture: L23
title: "Custom Auth Challenges for WebSocket APIs"
duration: "14:00"
section: 5
prereqs: ["L22"]
---

# L23 — Custom Auth Challenges for WebSocket APIs

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 5 — Advanced Patterns
> **Duration:** 14:00

## Prereqs

- L22 — Lambda@Edge.

## Key terms

- **WebSocket API** — the API Gateway protocol that keeps a
  persistent connection between the client and the server.
- **`$connect`** — the routing key for the initial WebSocket
  handshake. The first message every client sends.
- **`$disconnect`** — the routing key for the teardown.
- **`$default`** — the fallback routing key for any non-handler
  message.
- **IAM auth (WebSocket)** — the built-in way to authenticate
  WebSocket connections using AWS Signature V4. Less common for
  WebSocket than REST because long-lived connections don't play
  well with rotated credentials.
- **`identitySource` for WebSocket** — the same as for REST REQUEST
  authorizers: header / query / stage variable / context.

## Lecture

A WebSocket API has a different auth model from a REST API: the
client connects first (with no auth) and then sends messages.
There are two distinct auth decisions:

1. **`$connect`** — should this connection be allowed at all?
2. **Per-message** — should each message from this connection be
   processed?

The standard tool for `$connect` is a Lambda Authorizer.
The standard tool for per-message is to do the check inside the
integration Lambda (the Lambda that handles the WebSocket).

### A Lambda Authorizer for `$connect`

The authorizer sees a REQUEST-style event:

```json
{
  "type": "REQUEST",
  "methodArn": "arn:aws:execute-api:us-east-1:111:abcd/prod/$connect",
  "identitySource": ["user=alice", "token=xyz"],
  …
}
```

The `methodArn` ends in `/$connect` rather than a method path. The
policy you return follows the same shape as for REST:

```python
def lambda_handler(event, context):
    qs = event.get("queryStringParameters") or {}
    user = qs.get("user", "")
    token = qs.get("token", "")
    if not _verify(user, token):
        return _deny(event["methodArn"])
    return _allow(event["methodArn"], user, {"sub": user})
```

### Attach to a WebSocket API

```bash
aws apigatewayv2 create-authorizer \
  --api-id abcd \
  --name websocket-authorizer \
  --authorizer-type REQUEST \
  --identity-source "route.request.querystring.user,route.request.querystring.token" \
  --authorizer-uri "arn:aws:lambda:us-east-1:123:function:ws-authorizer" \
  --authorizer-result-ttl-in-seconds 300
```

Note the **`route.request.querystring.*`** prefix — for
WebSocket APIs the path is `route.request`, not `method.request`.
This is a small but important difference from REST.

Then attach the authorizer to the `$connect` route:

```bash
aws apigatewayv2 update-route \
  --api-id abcd \
  --route-id $CONNECT \
  --target-operations "integrations/$CONNECT" \
  --authorizer-id abc123 \
  --authorization-type CUSTOM
```

### Per-message auth

The `$connect` authorizer doesn't run on every message. If you
need to re-validate on each message, do it in the integration:

```python
def message_handler(event, context):
    connection_id = event["requestContext"]["connectionId"]
    body = json.loads(event["body"])
    token = body.get("token")
    if not _verify_token(token):
        # Use the management API to disconnect.
        apigatewaymanagement = boto3.client("apigatewaymanagementapi",
                                            endpoint_url=…)
        apigatewaymanagement.delete_connection(ConnectionId=connection_id)
        return {"statusCode": 401}
    # Otherwise process the message.
    return {"statusCode": 200}
```

The `apigatewaymanagementapi` API is the management plane for
WebSocket APIs — you use it to send messages *to* the client and
to forcibly disconnect.

### Common pitfalls

- **`$connect` doesn't run on every reconnect.** Once the
  connection is established, the same Lambda Authorizer policy is
  cached for the duration of the connection (up to 2 hours). If
  the token is revoked, the existing connection is still allowed.
- **`$default` doesn't run auth.** Any message that doesn't match
  a routing key goes to `$default`; if you've attached the
  authorizer only to `$connect`, all messages are processed.
- **`identitySource` for WebSocket is `route.request.*`, not
  `method.request.*`.** Small but constant source of bugs.

## Hands-on

There's no code in this lecture. The lecture video walks through
the deployment. For a code-only walk-through, see the parent
course's section 7 (REST → WebSocket).

## Quiz prep

- What's the difference between `$connect` auth and per-message
  auth?
- What's the right `IdentitySource` prefix for a WebSocket API?
- How do you forcibly disconnect a WebSocket client?

## Further reading

- AWS docs: [WebSocket APIs in API Gateway](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-websocket-api.html).

## What's next

**L24 — OIDC Integration** — wiring Auth0, Okta, or Cognito as the
IdP behind a Lambda Authorizer.