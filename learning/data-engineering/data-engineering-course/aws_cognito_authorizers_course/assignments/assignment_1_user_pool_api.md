# Assignment 1 — Secure a REST API End-to-End with Cognito

> **Sections:** 2 (User Pools) + 4 (API Gateway + Cognito Authorizer)
> **Estimated time:** 4 hours
> **Deliverable:** a working end-to-end stack: `02_user_pools/code/create_user_pool.py` + a new `04_api_gateway_integration/code/e2e_protected_api.py` and matching `moto` tests.
> **Author:** Prem Vishnoi <pvishnoi@avilx.com>

## Learning objectives

By the end of this assignment you will be able to:

1. Stand up a Cognito User Pool + App Client + test user **idempotently**
   with boto3, and verify the result with `moto`.
2. Wire the User Pool as a **Cognito User Pool Authorizer** on a
   boto3-created API Gateway REST API.
3. Sign a user in via `initiate_auth(USER_PASSWORD_AUTH)`, extract the
   **ID token**, and call the protected API with `Authorization: Bearer
   <id-token>`.
4. Reject calls that have no token, an expired token, or the wrong
   `aud`/`iss`.
5. Write a **pytest + moto** suite that exercises the whole flow
   without any AWS credentials.

## Background

In section 2 (L05–L10) you built the `create_user_pool.py` script that
stands up a User Pool, an App Client, and a test user. In section 4
(L15–L20) you learned how to attach a Cognito User Pool Authorizer to
API Gateway. This assignment ties the two halves together: build a
single CLI tool that, given a fresh AWS account, creates the entire
stack and then proves it works by signing in and calling the protected
endpoint with `requests`.

## Step-by-step tasks

### Step 1 — Re-use the User Pool bootstrap

You already have `02_user_pools/code/create_user_pool.py`. Refactor it
so that `main()` returns a dataclass:

```python
@dataclass
class UserPoolStack:
    user_pool_id: str
    app_client_id: str
    test_username: str
    test_password: str
    region: str
```

This is what the rest of the assignment will consume. Add a small
`if __name__ == "__main__": ...` that, when invoked with `--dry-run`,
just prints the `UserPoolStack` and exits without touching AWS.

### Step 2 — Create the protected API

Create a new file `04_api_gateway_integration/code/e2e_protected_api.py`
that takes a `UserPoolStack` and:

1. Creates a REST API named `cognito-protected-demo` (or looks one up
   by name).
2. Creates a resource `/items` with a `GET` method.
3. Sets up a **Cognito User Pool Authorizer** pointing at the
   `user_pool_id` from step 1, with `IdentitySource` =
   `method.request.header.Authorization`.
4. Configures the `GET /items` method to require that authorizer.
5. Wires the method to a **mock integration** (so we don't need a
   real Lambda). The integration returns `200` with body
   `{"items": ["alpha", "beta"]}`.
6. Deploys the API to a stage called `v1`.
7. Returns a `ProtectedApi` dataclass:

```python
@dataclass
class ProtectedApi:
    api_id: str
    invoke_url: str           # https://<api_id>.execute-api.<region>.amazonaws.com/v1
    authorizer_id: str
    user_pool_id: str
    app_client_id: str
```

The file must also support a `--dry-run` flag.

### Step 3 — Sign a user in and call the protected API

In the same file, add a function `sign_in_and_call(stack: UserPoolStack,
api: ProtectedApi) -> requests.Response`:

```python
def sign_in_and_call(stack, api):
    cognito = boto3.client("cognito-idp", region_name=stack.region)
    auth = cognito.initiate_auth(
        AuthFlow="USER_PASSWORD_AUTH",
        ClientId=stack.app_client_id,
        AuthParameters={
            "USERNAME": stack.test_username,
            "PASSWORD": stack.test_password,
        },
    )
    id_token = auth["AuthenticationResult"]["IdToken"]
    return requests.get(
        f"{api.invoke_url}/items",
        headers={"Authorization": f"Bearer {id_token}"},
        timeout=5,
    )
```

You can test it locally with `requests-mock` (no real HTTP). With
`moto`'s `mock_aws`, `initiate_auth` is fully implemented; you can mint
a real-looking ID token and verify the rest of the pipeline (header
parsing, scope checks) using `pyjwt` directly.

### Step 4 — Validate the JWT manually (offline)

Implement a `validate_id_token(id_token: str, *, user_pool_id: str,
region: str, app_client_id: str) -> dict` helper that:

- Splits the JWT, decodes the header to find `kid`.
- Returns the **payload** as a dict if the standard claims are valid
  (`iss`, `aud`, `exp`, `token_use`).
- Raises `InvalidTokenError` (a custom exception you define) otherwise.

You do **not** need to verify the RSA signature in this assignment —
moto signs with a known fake key. Add a `validate_signature=False` knob
and document the trade-off in a code comment. Real-world code must
**always** verify signatures (L19).

### Step 5 — Write `moto` tests

`04_api_gateway_integration/code/test_e2e_protected_api.py` must have
at least these tests, all under `@mock_aws`:

| Test | Asserts |
|---|---|
| `test_stack_creates_idempotently` | Calling `UserPoolStack.bootstrap()` twice yields the same `user_pool_id` + `app_client_id`. |
| `test_api_creates_with_authorizer` | After `ProtectedApi.bootstrap(stack)`, the API has a `COGNITO_USER_POOLS` authorizer attached. |
| `test_sign_in_returns_id_token` | `initiate_auth` returns an `AuthenticationResult` with a non-empty `IdToken`. |
| `test_valid_id_token_passes_validation` | `validate_id_token` returns the payload for a freshly minted token. |
| `test_expired_id_token_fails` | Patch `time.time` so the token looks expired; assert `InvalidTokenError`. |
| `test_wrong_audience_fails` | Decode a token with `aud` set to a different client; assert `InvalidTokenError`. |
| `test_wrong_issuer_fails` | Decode a token with `iss` set to a different user pool; assert `InvalidTokenError`. |
| `test_protected_get_requires_token` | Stub a requests call without `Authorization`; assert 401 / missing token. |
| `test_protected_get_with_token_succeeds` | Stub a requests call *with* the ID token; assert 200 and the expected JSON. |

## Deliverables

- [ ] `02_user_pools/code/create_user_pool.py` refactored so `main()` returns a `UserPoolStack`.
- [ ] New file `04_api_gateway_integration/code/e2e_protected_api.py` (~150 lines, fully type-hinted).
- [ ] New file `04_api_gateway_integration/code/test_e2e_protected_api.py` (≥ 9 tests, all green under `moto`).
- [ ] `04_api_gateway_integration/code/README.md` with install / run / test instructions.
- [ ] Output of `pytest -v` pasted into the PR description (text, not screenshot).

## Grading rubric (100 points)

| Category | Points | What we look for |
|---|---|---|
| `UserPoolStack` idempotency | 15 | Re-running yields same IDs; no `ResourceExistsException` leak. |
| `ProtectedApi` setup | 20 | Authorizer type = `COGNITO_USER_POOLS`, identity source = Authorization header, mock integration wired, deployed to `v1`. |
| `sign_in_and_call` | 15 | Uses `USER_PASSWORD_AUTH`, returns `requests.Response`, includes Bearer header. |
| `validate_id_token` | 20 | Checks `iss`, `aud`, `exp`, `token_use`. Raises a typed exception on failure. |
| Tests | 20 | 9+ tests, all green, all use `moto`, asserts on **behavior** not on log strings. |
| Code quality | 10 | Type hints, no print in pure functions, logging configured once. |

Deductions:

- `-10` if `validate_id_token` is ever callable with `verify_signature=False` in production code.
- `-5` per missing test from the table above.
- `-5` if the authorizer is `TOKEN` (Lambda Authorizer) instead of `COGNITO_USER_POOLS`.

## Stretch goals (optional, +10 each, capped at +20)

- Add a `--groups` flag to `create_user_pool.py` that creates a Cognito
  group and adds the test user to it. Then assert the `cognito:groups`
  claim appears in the ID token.
- Replace the mock integration with a real Lambda Authorizer (L36) that
  checks the `cognito:groups` claim and returns `Allow` or `Deny`.
- Add a `--region` flag that defaults to `us-east-1` and a `--profile`
  flag for the boto3 session.

## Hints

- `moto` 5.x implements `initiate_auth(USER_PASSWORD_AUTH)` since 5.0.12.
  If you see a "not yet implemented" error, upgrade: `pip install -U
  'moto[cognito-idp]>=5.0'`.
- API Gateway authorizer type strings are case-sensitive:
  `COGNITO_USER_POOLS` is correct; `cognito_user_pools` is not.
- For the `--dry-run` path, you don't need `moto` at all — but the rest
  of the test suite does, so factor your code so `main()` can run with
  or without the mock.
- To inspect the JWT payload in tests, use `jwt.decode(token,
  options={"verify_signature": False})` — the assignment explicitly
  permits no-signature verification in test code only.
