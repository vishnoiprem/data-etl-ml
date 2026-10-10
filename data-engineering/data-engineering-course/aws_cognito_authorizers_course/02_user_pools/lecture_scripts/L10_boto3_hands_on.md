---
lecture: L10
title: "Hands-on: Create a User Pool with boto3 + moto"
duration: "15:00"
section: 2
prereqs:
  - L09
---

# L10 — Hands-on: Create a User Pool with boto3 + moto

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 2 — Cognito User Pools
> **Duration:** 15:00

## Prereqs

- Watched **L05–L09** (the entire section 2 theory).
- `pip install -r requirements.txt` from the course root.
- Optional: an AWS account if you want to run against real AWS.
  **The course does not require it** — every demo runs offline with
  `moto`.

## Key terms

- **`@mock_aws`** — the moto decorator that intercepts every boto3
  call in a test and routes it to a local fake. The replacement for
  the older `@mock_cognito-idp`.
- **Idempotent** — running the script multiple times yields the same
  result. Re-running `bootstrap()` does not raise `ResourceExistsException`
  — it finds the existing resource and reuses it.
- **`admin_set_user_password(Permanent=True)`** — sets the user's
  password and skips the `FORCE_CHANGE_PASSWORD` challenge on first
  sign-in. The recommended path for test users.
- **`MessageAction="SUPPRESS"`** — tells Cognito not to send a
  welcome email when `admin_create_user` runs. Required for the
  course because we don't have a real inbox.

## Lecture

Welcome to the hands-on climax of section 2. In the next 15 minutes
we'll walk through `02_user_pools/code/create_user_pool.py` line by
line, and then run the 6 moto tests that prove it works — all
without an AWS account.

### The goal

The script does four things, in order:

1. **Find or create** a User Pool named `demo-cognito-course-pool`.
2. **Find or create** an App Client inside the pool, with no client
   secret and `code` OAuth flow enabled.
3. **Find or create** a test user `alice@example.com`.
4. **Set a permanent password** on the test user so it can sign in
   immediately.

Re-running the script is a no-op (idempotent). The `--dry-run` flag
prints the plan without touching AWS.

### The structure

```
create_user_pool.py
├── Defaults                  constants (pool name, region, etc.)
├── UserPoolStack             dataclass returned by bootstrap()
├── _env()                    env-var helper (re-read every call)
├── _build_pool_kwargs()      kwargs for create_user_pool
├── _build_client_kwargs()    kwargs for create_user_pool_client
├── _find_existing_pool()     lookup helper (paginated)
├── _find_existing_client()   lookup helper (paginated)
├── _user_exists()            lookup helper (admin_get_user)
├── bootstrap()               the main function — creates everything
├── _print_dry_run()          pretty-prints the plan
└── main() / __main__         argparse + sys.exit
```

Each helper has **one job** and is testable in isolation. `bootstrap()`
is the orchestrator.

### Walkthrough

**The pool kwargs.** `_build_pool_kwargs()` returns a single dict
that's passed straight to `cognito.create_user_pool(...)`. The fields:

```python
{
    "PoolName": ...,
    "UsernameAttributes": ["email"],                     # email-as-username
    "AutoVerifiedAttributes": ["email"],                 # auto-verify on sign-up
    "Policies": {
        "PasswordPolicy": {
            "MinimumLength": 8,
            "RequireSymbols": True,                       # at least one symbol
            "TemporaryPasswordValidityDays": 7,
            # other complexity booleans False (per NIST 800-63B)
        },
    },
    "Schema": [
        {"Name": "email", "AttributeDataType": "String", "Required": True, "Mutable": True},
    ],
    "AccountRecoverySetting": {
        "RecoveryMechanisms": [{"Name": "verified_email", "Priority": 1}],
    },
    "EmailConfiguration": {"EmailSendingAccount": "COGNITO_DEFAULT"},
    "AdminCreateUserConfig": {"AllowAdminCreateUserOnly": True},
}
```

Two things to note:

- `AdminCreateUserConfig.AllowAdminCreateUserOnly: True` means **no
  self-sign-up** through the Hosted UI. For the course we want
  admin-only so we can script the test user creation.
- `EmailSendingAccount: "COGNITO_DEFAULT"` uses Cognito's built-in
  sandbox (50 emails/day, capped to verified addresses). In
  production you'd switch to Amazon SES and raise that limit.

**The app client kwargs.** `_build_client_kwargs()` returns:

```python
{
    "UserPoolId": ...,
    "ClientName": ...,
    "GenerateSecret": False,                              # safe for SPAs
    "AllowedOAuthFlows": ["code"],                        # auth-code flow
    "AllowedOAuthFlowsUserPoolClient": True,
    "AllowedOAuthScopes": ["openid", "email", "profile"],
    "SupportedIdentityProviders": ["COGNITO"],
    "AccessTokenValidity": 60,                            # minutes
    "IdTokenValidity": 60,                                # minutes
    "RefreshTokenValidity": 30,                           # days
    "TokenValidityUnits": {
        "AccessToken": "minutes",
        "IdToken": "minutes",
        "RefreshToken": "days",
    },
    "PreventUserExistenceErrors": "ENABLED",              # don't leak which users exist
}
```

**The user creation.** `bootstrap()` calls:

```python
cognito.admin_create_user(
    UserPoolId=pool_id,
    Username=username,                                    # "alice@example.com"
    UserAttributes=[
        {"Name": "email",          "Value": username},
        {"Name": "email_verified", "Value": "true"},
    ],
    MessageAction="SUPPRESS",                             # no welcome email
)
cognito.admin_set_user_password(
    UserPoolId=pool_id,
    Username=username,
    Password=password,                                    # "TempPass!2026"
    Permanent=True,                                       # skip FORCE_CHANGE_PASSWORD
)
```

**Idempotency.** Each "find or create" helper uses a paginator and
returns the existing resource's id if found, else calls the create
API. The result is that re-running `bootstrap()` is a no-op — the
tests prove this with `test_idempotent`.

### The dry-run path

`--dry-run` prints the API calls we *would* make, then exits 0:

```
[DRY-RUN] No AWS calls will be made. Plan:
  cognito-idp.create_user_pool({...})
  cognito-idp.create_user_pool_client({...})
  cognito-idp.admin_create_user('alice@example.com')
  cognito-idp.admin_set_user_password('alice@example.com', permanent=True)
  region: us-east-1
```

This is the same pattern we use in `aws_lambda_course/10_generative_ai_bedrock/.../create_api_key.py`:
no `--apply` is necessary because dry-run is the safe default and
real apply is the explicit opt-in.

### The 6 moto tests

`test_create_user_pool.py` has 6 tests, all wrapped in `@mock_aws`:

| Test | What it asserts |
|---|---|
| `test_creates_pool` | A pool with the expected name exists after `bootstrap()` |
| `test_idempotent` | Two `bootstrap()` calls yield the same IDs and create only one pool / one app client |
| `test_creates_app_client` | The app client has the expected name and no client secret |
| `test_creates_user` | The test user exists with `email_verified=true` |
| `test_password_set` | `initiate_auth(USER_PASSWORD_AUTH)` succeeds with the documented password |
| `test_dry_run` | `main(["--dry-run"])` prints the plan and creates nothing |

The password test is the most interesting one. It does a real
`initiate_auth(USER_PASSWORD_AUTH)` against the moto-mocked
Cognito and asserts the response contains a non-empty `IdToken`,
`AccessToken`, and `ExpiresIn`. moto has supported this since 5.0.12
(June 2023); if you see a "not implemented" error, upgrade.

### Running the tests

```bash
cd aws_cognito_authorizers_course
python3 -m pytest 02_user_pools/code/test_create_user_pool.py -v
```

Expected output:

```
02_user_pools/code/test_create_user_pool.py::test_creates_pool PASSED
02_user_pools/code/test_create_user_pool.py::test_idempotent PASSED
02_user_pools/code/test_create_user_pool.py::test_creates_app_client PASSED
02_user_pools/code/test_create_user_pool.py::test_creates_user PASSED
02_user_pools/code/test_create_user_pool.py::test_password_set PASSED
02_user_pools/code/test_create_user_pool.py::test_dry_run PASSED
============================== 6 passed in 2.23s ===============================
```

### Running against real AWS

If you have an AWS account and want to actually create the pool:

```bash
unset AWS_PROFILE          # or set your real profile
export AWS_REGION=us-east-1
python3 02_user_pools/code/create_user_pool.py
# → creates the pool + app client + test user
# → prints env-var lines you can copy-paste
```

Then in the console:

- Pool details → "User pool ID" — note the 26-char id
- App integration → "Domain name" — set a unique prefix
- Users → "alice@example.com" → "Enable TOTP" to enroll MFA

To clean up: Pool → "Delete user pool" (top right). The demo
resources cost nothing if you don't enable SMS MFA.

## Hands-on

You have two tasks:

1. **Run the tests.** From the course root:

```bash
python3 -m pytest 02_user_pools/code/test_create_user_pool.py -v
```

Confirm all 6 pass. If any fail, look at the trace — most likely
you have an old version of `moto`. Upgrade: `pip install -U 'moto[cognito-idp]>=5.0'`.

2. **Modify the script.** Pick **one** of the following and apply
   it. Re-run the tests; they should still pass.

   - Add a second test user (`bob@example.com`) and a `UserPoolGroup`
     called `admins`. Add Alice to the group, not Bob.
   - Change the password policy to `MinimumLength=12` and
     `RequireNumbers=True`.
   - Add a custom attribute `custom:tenant_id` and set it on Alice
     to `"acme-corp"`.

   The existing tests don't check the new behavior — you have to
   add new tests to assert it. That's the assignment (in
   `assignments/assignment_1_user_pool_api.md`).

## Quiz prep

For this lecture, focus on:

- The 4 steps of `bootstrap()` and the order they run in
- Why `MessageAction="SUPPRESS"` matters in tests
- Why `admin_set_user_password(Permanent=True)` is what makes
  `USER_PASSWORD_AUTH` work
- The 6 moto tests and what each one proves

## Further reading

- AWS docs — `admin_create_user`: <https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_AdminCreateUser.html>
- moto's Cognito support: <https://github.com/getmoto/moto/blob/master/moto/cognitoidp/models.py>
- `02_user_pools/code/create_user_pool.py` (read it top-to-bottom)

## What's next

Section 2 is done. Next stop: **Section 3 — Cognito Identity Pools**,
where we trade the JWT from this User Pool for **temporary AWS
credentials** via STS.