# code/lambda_authorizer

A token-based AWS Lambda Authorizer for API Gateway (REST API).

The function:

1. Reads `authorizationToken` from the API Gateway authorizer event.
2. Strips the `Bearer ` scheme if present.
3. Verifies the token as an HS256 JWT against `JWT_SECRET`.
4. Returns an `Allow` IAM policy with the `methodArn` as `Resource`
   and a small `context` (sub, tenant, scope) for the integration.
5. Returns a `Deny` policy on any verification failure.

## Layout

```
lambda_authorizer/
├── README.md
├── lambda_authorizer.py        # the function code
├── test_lambda_authorizer.py   # moto-free unit tests
├── attach_to_api.py            # boto3 helper to wire the authorizer
└── requirements.txt
```

## Run the tests

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

Expected output: `6 passed`.

## Deploy

```bash
pip install --target ./build pyjwt -q
cp lambda_authorizer.py ./build/
(cd ./build && zip -qr ../authorizer.zip .)

aws lambda create-function \
  --function-name demo-lambda-authorizer \
  --runtime python3.12 \
  --handler lambda_authorizer.lambda_handler \
  --role arn:aws:iam::123456789012:role/lambda-exec-role \
  --zip-file fileb://authorizer.zip \
  --environment 'Variables={JWT_SECRET=replace-me, JWT_ALG=HS256}' \
  --timeout 5 \
  --memory-size 256

aws lambda add-permission \
  --function-name demo-lambda-authorizer \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:123456789012:abcd/*"
```

## Wire onto an API method

```bash
export API_ID=abcd1234ef
export ITEMS_RESOURCE_ID=xyz789
export AUTHORIZER_LAMBDA_ARN=arn:aws:lambda:us-east-1:123456789012:function:demo-lambda-authorizer
python attach_to_api.py
```

## Test against a real API

See `../event_payloads/` for sample events, or use the L37 lecture
smoke test script to mint a JWT and call the API.
