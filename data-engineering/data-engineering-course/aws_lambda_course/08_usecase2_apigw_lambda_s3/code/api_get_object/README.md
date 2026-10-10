# api_get_object

Lambda that reads an S3 object whose key is supplied either in the
`?key=` query string or the `{proxy+}` path. Returns the content plus
S3 metadata as JSON.

## Files

- `lambda_function.py` — handler.
- `test_lambda_function.py` — `moto.mock_aws`-backed pytest suite.

## Run the tests

```bash
cd code/api_get_object
python -m pytest -v
```

All five tests should pass without an AWS account.

## Deploy

The handler expects the following environment variable:

| Name | Required | Example |
|---|---|---|
| `BUCKET_NAME` | yes | `usecase2-objects-prem` |

The Lambda's execution role needs:

```json
{
  "Action": ["s3:GetObject"],
  "Resource": "arn:aws:s3:::<BUCKET_NAME>/*",
  "Effect": "Allow"
}
```

## API Gateway wiring

- Resource: `/{proxy+}`.
- Method: `GET` → Lambda Proxy Integration → this function.
- Optional mapping template to inject a default `?version=v1` (see L32).

## Try it locally

After deploying:

```bash
INVOKE="https://abc123.execute-api.us-east-1.amazonaws.com/prod"
curl "$INVOKE/test-object"
curl "$INVOKE/search?key=test-object"
```
