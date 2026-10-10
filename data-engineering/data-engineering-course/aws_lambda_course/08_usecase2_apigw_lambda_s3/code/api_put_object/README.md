# api_put_object

Lambda that writes the request body to S3 at a key derived from the
`{proxy+}` path. Honors binary uploads (base64) and propagates the
client's `Content-Type` header to the S3 object.

## Files

- `lambda_function.py` — handler.
- `test_lambda_function.py` — `moto.mock_aws`-backed pytest suite.

## Run the tests

```bash
cd code/api_put_object
python -m pytest -v
```

## Environment

| Name | Required | Example |
|---|---|---|
| `BUCKET_NAME`  | yes | `usecase2-objects-prem` |
| `CONTENT_TYPE` | no  | `application/octet-stream` (default) |

## IAM

```json
{
  "Action": ["s3:PutObject"],
  "Resource": "arn:aws:s3:::<BUCKET_NAME>/*",
  "Effect": "Allow"
}
```

## API Gateway wiring

- Resource: `/{proxy+}`.
- Method: `POST` → Lambda Proxy Integration → this function.

## Try it

```bash
INVOKE="https://abc123.execute-api.us-east-1.amazonaws.com/prod"
curl -X POST "$INVOKE/hello.txt" \
     -H "Content-Type: text/plain" \
     -d "hello world"

# Round-trip
curl "$INVOKE/hello.txt"
```
