# code/event_payloads

Example API Gateway authorizer events you can use to drive the
authorizer Lambda locally, without going through API Gateway at all.

| File | Authorizer type | Use with |
|---|---|---|
| `token_authorizer_event.json` | TOKEN | `lambda_authorizer.py` |
| `request_authorizer_event.json` | REQUEST | `lambda_authorizer.py` (requires changing `type` to `REQUEST` and updating the handler to read `headers` instead of `authorizationToken`) |

## Why these exist

You can invoke the authorizer Lambda directly via:

```bash
aws lambda invoke \
  --function-name demo-lambda-authorizer \
  --payload fileb://token_authorizer_event.json \
  --cli-binary-format raw-in-base64-out \
  out.json
cat out.json | jq .
```

This is the fastest way to iterate on the authorizer's logic while
you are writing it. The signatures in the sample tokens are not real —
they will fail verification until you mint a fresh token with PyJWT,
or set `JWT_SECRET=test-secret-do-not-use-in-prod` to fall back to
the default test secret.

## Minting a token that matches the sample payload

```python
import jwt, time, json
token = jwt.encode(
    {"sub": "user-1", "tenant": "acme", "scope": "read", "exp": int(time.time()) + 3600},
    "test-secret-do-not-use-in-prod",
    algorithm="HS256",
)
print(json.dumps({"authorizationToken": f"Bearer {token}"}))
```