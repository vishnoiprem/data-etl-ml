# 03_simple_authorizer/code — TOKEN Lambda Authorizer

A reference implementation of a TOKEN-based AWS Lambda Authorizer
for API Gateway REST APIs.

The function:

1. Reads `authorizationToken` from the API Gateway authorizer event.
2. Strips the `Bearer ` scheme if present.
3. Verifies the token as an HS256 JWT against `JWT_SECRET`.
4. Returns an `Allow` IAM policy with the `methodArn` as `Resource`
   and a flat string-only `context` (flattened from the JWT claims).
5. Returns a `Deny` policy on any verification failure.

## Layout

```
03_simple_authorizer/code/
├── README.md
├── token_authorizer.py            ← the function code
├── test_token_authorizer.py       ← 6+ moto-free unit tests
└── requirements.txt
```

## Run the tests

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -v
```

Expected output: **6+ passed**.

## What the tests cover

| Test | Asserts |
|---|---|
| `test_valid_token_returns_allow` | sign + verify → `Effect: Allow` |
| `test_invalid_token_returns_deny` | wrong secret → `Effect: Deny` |
| `test_missing_token_returns_deny` | empty header → `Effect: Deny` |
| `test_policy_resource_matches_method_arn` | `Resource` is the `methodArn` |
| `test_policy_action_is_execute_api_invoke` | `Action` is exactly `execute-api:Invoke` |
| `test_principal_id_extracted_from_sub_claim` | `principalId` comes from the JWT `sub` |
| `test_expired_token_returns_deny` | expired token → `Effect: Deny` |
| `test_context_flattens_claims` | context is flat, all values are strings |

## Deploy

```bash
pip install --target ./build pyjwt -q
cp token_authorizer.py ./build/
(cd ./build && zip -qr ../authorizer.zip .)

aws lambda create-function \
  --function-name demo-lambda-authorizer \
  --runtime python3.12 \
  --handler token_authorizer.lambda_handler \
  --role arn:aws:iam::123456789012:role/lambda-exec-role \
  --zip-file fileb://authorizer.zip \
  --environment 'Variables={JWT_SECRET=replace-me,JWT_ISSUER=https://auth.example.com,JWT_AUDIENCE=api.example.com}' \
  --timeout 5 \
  --memory-size 256

aws lambda add-permission \
  --function-name demo-lambda-authorizer \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:123456789012:abcd/*"
```

## See also

- [`../lecture_scripts/L15_end_to_end.md`](../lecture_scripts/L15_end_to_end.md)
  — the lecture that walks through this code.
- `../../02_jwt_basics/code/jwt_verify.py` — the JWT primitives
  this handler wraps.