# code/cognito_setup

Boto3 script that creates the Cognito User Pool, resource server, and
App Client used by L39. The script is idempotent — re-running it
returns the existing resources rather than creating duplicates.

## Layout

```
cognito_setup/
├── README.md
├── create_user_pool.py         # the bootstrap script
├── test_create_user_pool.py    # moto-based offline tests
├── mint_token.py               # client_credentials access token helper
└── requirements.txt
```

## Run the tests

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

Expected output: `2 passed`.

## Bootstrap a real User Pool

```bash
export USER_POOL_NAME=demo-section9-pool
export AWS_REGION=us-east-1
python create_user_pool.py
```

The script prints `USER_POOL_ID` and `APP_CLIENT_ID` — capture them.

## Mint an access token (client_credentials flow)

```bash
export USER_POOL_ID=us-east-1_xxxxxxxxx
export APP_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
export APP_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
export COGNITO_DOMAIN=demo-section9-1730000000

python mint_token.py
```

The script prints the access_token (a JWT). Decode it locally with
[jwt.io](https://jwt.io) to inspect the `scope`, `client_id`, `exp`,
and `iss` claims.

## Wire the User Pool as an API Gateway authorizer

See the L39 lecture script (`lecture_scripts/L39_cognito_authorizer_hands_on.md`)
section 5 for the boto3 snippet that creates the `COGNITO_USER_POOLS`
authorizer and patches the `GET /items` method.
