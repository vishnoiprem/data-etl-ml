# api_keys_setup

Idempotent boto3 script that:

1. Finds the `ServerlessCRUD` REST API by name.
2. Creates (or reuses) an API Key.
3. Creates (or updates) a Usage Plan with the requested throttle and
   quota.
4. Attaches the key to the plan.

Re-runnable: every call looks up the existing resources first.

## Files

- `create_api_key.py` — script.
- `test_create_api_key.py` — `moto.mock_aws`-backed pytest suite.

## Run the tests

```bash
cd code/api_keys_setup
python -m pytest -v
```

## Run the script against your AWS account

```bash
export AWS_REGION=us-east-1
export API_NAME=ServerlessCRUD
export STAGE_NAME=prod

# Defaults: 50 rps / burst 100 / 10k per day
python create_api_key.py

# Custom throttling
python create_api_key.py --rate 200 --burst 400 --quota 1000000 --quota-period MONTH
```

The script prints the key value at the end. Put it in your
`x-api-key` header:

```bash
curl -H "x-api-key: $KEY" "$INVOKE_URL/test-object"
```

## IAM required

```json
{
  "Action": [
    "apigateway:GET",
    "apigateway:PATCH",
    "apigateway:POST"
  ],
  "Resource": "arn:aws:apigateway:*::/*",
  "Effect": "Allow"
}
```
