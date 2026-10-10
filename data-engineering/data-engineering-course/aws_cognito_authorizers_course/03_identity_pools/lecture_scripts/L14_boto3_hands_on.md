---
lecture: L14
title: "Hands-on: Identity Pool with boto3 + moto"
duration: "30:00"
section: 3
prereqs:
  - L13
---

# L14 — Hands-on: Identity Pool with boto3 + moto

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 3 — Cognito Identity Pools
> **Duration:** 30:00

## Prereqs

- Watched **L11–L13** (the entire section 3 theory).
- L10 — you've already created a User Pool with
  `create_user_pool.py`. Export `USER_POOL_ID` and `APP_CLIENT_ID`.
- `pip install -r requirements.txt` from the course root.

## Key terms

- **`cognito-identity:CreateIdentityPool`** — the boto3 call that
  creates the pool. Returns an `IdentityPoolId` like
  `us-east-1:12345678-90ab-cdef-...`.
- **`iam:CreateRole`** — creates the IAM role. Requires
  `iam:PassRole` for the role to be assumable.
- **`iam:PutRolePolicy`** — attaches an inline policy to the role.
  We use this so the role's full policy lives in a single place.
- **`cognito-identity:SetIdentityPoolRoles`** — attaches the IAM
  role to the pool. **Not implemented in moto 5.x**; tested in
  production.
- **`mock_aws`** — the moto decorator that intercepts every boto3
  call in a test. Replaces the older `@mock_cognito-identity`.

## Lecture

In L10 we created a User Pool and got back three tokens. Today we
take the User Pool as input, create an Identity Pool that trusts it,
mint an IAM role with a least-privilege S3 policy, and attach the
role to the pool. By the end of this lecture you should be able to
read `03_identity_pools/code/identity_pool_demo.py` top-to-bottom
and understand every line.

### What the script does

```
identity_pool_demo.py
├── Defaults
├── IdentityPoolStack              dataclass returned by bootstrap()
├── _env()                         env-var helper
├── _cognito_provider()            formats the Cognito provider name
├── _build_trust_policy()          trust policy with aud condition
├── _build_inline_policy()         per-user S3 prefix policy
├── _find_existing_identity_pool() lookup helper (paginated)
├── _find_existing_role()          lookup helper (iam.get_role)
├── _create_identity_pool()        create the pool
├── _create_auth_role()            create role + put_role_policy
├── _attach_roles_to_pool()        set_identity_pool_roles (skipped in moto)
├── bootstrap()                    the main function
├── _print_dry_run()               pretty-prints the plan
└── main() / __main__              argparse + sys.exit
```

The script is intentionally a single-file, 140-line module. Each
helper is one function and is independently testable.

### Walkthrough

**The trust policy** (`_build_trust_policy()`):

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Federated": "cognito-identity.amazonaws.com"},
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "cognito-identity.amazonaws.com:aud": "<IDENTITY_POOL_ID>"
      }
    }
  }]
}
```

The `<IDENTITY_POOL_ID>` placeholder is filled in at role-creation
time. In production you'd construct the trust policy with the actual
pool id. In the course, we leave the placeholder so the policy is
self-documenting (you can see what's going to be substituted in).

**The inline policy** (`_build_inline_policy()`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowUserToListTheirOwnBucketPrefix",
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": ["arn:aws:s3:::demo-cognito-course-bucket"],
      "Condition": {
        "StringLike": {
          "s3:prefix": ["${cognito-identity.amazonaws.com:sub}/*"]
        }
      }
    },
    {
      "Sid": "AllowUserReadWriteTheirOwnObjects",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
      "Resource": [
        "arn:aws:s3:::demo-cognito-course-bucket/${cognito-identity.amazonaws.com:sub}/*"
      ]
    }
  ]
}
```

This is the "dropbox" pattern from L13. Each user can only see,
read, and write objects under their own `sub` prefix. They cannot
list the bucket (the `s3:ListBucket` permission is also scoped to
their prefix via the `Condition` block).

**The pool creation** (`_create_identity_pool()`):

```python
identity.create_identity_pool(
    IdentityPoolName=name,
    AllowUnauthenticatedIdentities=False,    # no guest access
    CognitoIdentityProviders=[
        {
            "ProviderName": _cognito_provider(user_pool_id),
            "ClientId": app_client_id,
            "ServerSideTokenCheck": True,    # ← verify the JWT server-side
        },
    ],
)
```

`ServerSideTokenCheck=True` is the production default. It tells
Cognito to re-validate the token against the User Pool's JWKS
before issuing credentials. Without it, a client could forge the
issuer claim.

**The role creation** (`_create_auth_role()`):

```python
trust = _build_trust_policy()
role = iam.create_role(
    RoleName=role_name,
    AssumeRolePolicyDocument=json.dumps(trust),
    Description="Cognito Identity Pool authenticated role ...",
)
iam.put_role_policy(
    RoleName=role_name,
    PolicyName="cognito-idpool-auth-policy",
    PolicyDocument=_build_inline_policy(),
)
return role["Role"]["Arn"]
```

We use `put_role_policy` (inline) rather than `attach_role_policy`
(managed) because the policy is specific to this one role and we
want it self-contained.

**The role attachment** (`_attach_roles_to_pool()`):

```python
identity.set_identity_pool_roles(
    IdentityPoolId=pool_id,
    Roles={"authenticated": auth_role_arn},
)
```

This is the call that wires the role into the pool. It is
**not** implemented in `moto` 5.x (raises `NotImplementedError`).
We catch the error explicitly in `bootstrap()` and print a clear
message, then continue. In production this is the call that
actually makes the pool work.

### The 5 moto tests

`test_identity_pool_demo.py` has 5 tests:

| Test | What it asserts |
|---|---|
| `test_creates_identity_pool` | A pool with the expected name exists after `bootstrap()` |
| `test_sets_cognito_user_pool_as_provider` | The pool's `CognitoIdentityProviders` list contains our User Pool with the right `ClientId` |
| `test_role_has_correct_trust_policy` | The IAM role's trust policy allows `cognito-identity.amazonaws.com` to `AssumeRoleWithWebIdentity` |
| `test_idempotent` | Two `bootstrap()` calls yield the same IDs |
| `test_dry_run` | `main(["--dry-run"])` prints the plan and creates nothing |

The tests that **would** require real AWS:

- `GetCredentialsForIdentity` returning STS credentials
- The trust policy's `Condition` actually being applied to an
  attempted `AssumeRoleWithWebIdentity`
- The IAM policy's `Condition` actually scoping S3 calls per-user

These are documented in the `NotImplementedError` skip in
`bootstrap()` and the docstring at the top of the test file.

### Running the tests

```bash
cd aws_cognito_authorizers_course
python3 -m pytest 03_identity_pools/code/test_identity_pool_demo.py -v
```

Expected output:

```
03_identity_pools/code/test_identity_pool_demo.py::test_creates_identity_pool PASSED
03_identity_pools/code/test_identity_pool_demo.py::test_sets_cognito_user_pool_as_provider PASSED
03_identity_pools/code/test_identity_pool_demo.py::test_role_has_correct_trust_policy PASSED
03_identity_pools/code/test_identity_pool_demo.py::test_dry_run PASSED
03_identity_pools/code/test_identity_pool_demo.py::test_idempotent PASSED
============================== 5 passed in 1.32s ===============================
```

### Running against real AWS

If you have an AWS account and a User Pool from L10:

```bash
export USER_POOL_ID=us-east-1_aBcDeFgHi
export APP_CLIENT_ID=7a1b2c3d4e5f6g7h
export AWS_REGION=us-east-1
python3 03_identity_pools/code/identity_pool_demo.py
# → creates the identity pool + IAM role
# → prints env-var lines you can copy-paste
```

Then verify with the AWS CLI:

```bash
aws cognito-identity describe-identity-pool \
    --identity-pool-id us-east-1:12345678-90ab-cdef-...
aws iam get-role --role-name Cognito_IdentityPool_Auth_Role
```

The full end-to-end test (mint credentials, call S3) requires
either real AWS or LocalStack.

### Diagram

See `diagrams/identity_pool_federation.mmd` for the full
end-to-end flow.

## Hands-on

You have two tasks:

1. **Run the tests.** From the course root:

```bash
python3 -m pytest 03_identity_pools/code/test_identity_pool_demo.py -v
```

Confirm all 5 pass.

2. **Modify the script.** Pick **one** of the following and apply
   it:

   - Add a `GuestRole` to the bootstrap. Create a second IAM role
     with read-only S3 access to a public bucket, and attach both
     roles to the pool. (You'll need to handle the moto
     `NotImplementedError` gracefully in tests.)
   - Add a second Cognito User Pool as a provider. This requires
     accepting a `cognito_providers: list[dict]` argument to
     `bootstrap()`.
   - Change the inline policy to grant DynamoDB access scoped by
     `cognito-identity.amazonaws.com:sub`. (Hint: use
     `dynamodb:leadingKeys` in a `ForAllValues:StringEquals`
     condition.)

   Re-run the tests; they should still pass. Add at least one new
   test to assert your new behavior.

## Quiz prep

For this lecture, focus on:

- The 4 resources the script creates (pool, role, policy, attachment)
- Why `ServerSideTokenCheck=True` matters
- What the 3 `cognito-identity.amazonaws.com:*` substitution
  variables do
- Which parts of the flow you can test with moto and which you
  cannot

## Further reading

- `03_identity_pools/code/identity_pool_demo.py` (read it
  top-to-bottom)
- `diagrams/identity_pool_federation.mmd` (the full flow)
- AWS docs — IAM roles for Identity Pools: <https://docs.aws.amazon.com/cognito/latest/developerguide/iam-roles.html>
- moto's Identity support: <https://github.com/getmoto/moto/blob/master/moto/cognitoidentity/models.py>

## What's next

Section 3 is done. Next stop: **Section 4 — API Gateway + Cognito
Authorizer**, where we wire the User Pool tokens into HTTP APIs.