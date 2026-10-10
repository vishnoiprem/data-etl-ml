# event_payloads

Sample API Gateway **proxy event** JSON payloads. These are exactly
the shape AWS sends to a Lambda handler when you choose
**Lambda Proxy Integration**.

## Files

- `lambda_proxy_event_get.json` — `GET /orders/123` (key from path +
  query string).
- `lambda_proxy_event_post.json` — `POST /orders/123` with a JSON body.
- `lambda_proxy_event_post_binary.json` — `POST /uploads/photo.bin` with
  a base64 binary body (`isBase64Encoded: true`).

## Using these in tests

The Lambda test files in `../api_get_object/` and `../api_put_object/`
construct events inline. If you want to feed these JSON files into a
test verbatim, use this pattern:

```python
import json
from pathlib import Path

PAYLOADS = Path(__file__).resolve().parent / "event_payloads"

def load(name: str) -> dict:
    return json.loads((PAYLOADS / name).read_text())

get_event = load("lambda_proxy_event_get.json")
post_event = load("lambda_proxy_event_post.json")
```

## Why proxy integration?

In proxy integration, the **entire** HTTP request is forwarded as a
JSON event. The handler returns a JSON object with `statusCode`,
`headers`, and `body`, and API Gateway serializes it back to HTTP.

The alternative ("non-proxy" with a mapping template) is covered in
L32.
