---
lecture: L13
title: "IAM Roles for Authenticated & Guest Users"
duration: "15:00"
section: 3
prereqs:
  - L12
---

# L13 — IAM Roles for Authenticated & Guest Users

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 3 — Cognito Identity Pools
> **Duration:** 15:00

## Prereqs

- Watched **L12 — Authentication Providers**.

## Key terms

- **Trust policy** — the `AssumeRolePolicyDocument` on an IAM role. It
  says *who* can assume the role. For Identity Pools, it's
  `cognito-identity.amazonaws.com`.
- **Permissions policy** — the `PolicyDocument` you attach to the
  role. It says *what* the role can do once assumed.
- **Inline policy** — a policy embedded in the role itself, not in a
  separate `AWS::IAM::Policy` resource. Convenient for small
  per-role policies.
- **`Condition` block** — an IAM policy key that scopes a statement
  based on request context. For Identity Pools, the relevant keys
  are `cognito-identity.amazonaws.com:sub`, `:aud`, and `:amr`.
- **`sts:AssumeRoleWithWebIdentity`** — the STS action Cognito
  Identity Pools call to assume the role. The trust policy must
  `Allow` this.
- **Federated principal** — the placeholder for "the user, not a
  specific user". In the trust policy, you write
  `{"Federated": "cognito-identity.amazonaws.com"}` and Cognito
  resolves it to the actual `sub` at assume-time.

## Lecture

In L12 we wired providers. Today we wire **the actual IAM policies
that scope what the federated user can do**. By the end of this
lecture you'll be able to write a least-privilege policy that gives
a user access to **only their own objects** in S3, with no other
permissions.

### The two policies on every role

Every IAM role has:

| Policy | Attached to | Says |
|---|---|---|
| Trust policy | The role itself (mandatory) | Who can assume this role |
| Permissions policy | The role, or as a separate `Policy` resource | What the assumed role can do |

For Identity Pools:

- **Trust policy**: allow `cognito-identity.amazonaws.com` to
  `sts:AssumeRoleWithWebIdentity`, conditioned on the source being
  *your* identity pool.
- **Permissions policy**: scope AWS actions to a specific
  `Resource`, optionally using `cognito-identity.amazonaws.com:sub`
  in a `Condition` to scope per-user.

### The trust policy (least-privilege)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"Federated": "cognito-identity.amazonaws.com"},
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "cognito-identity.amazonaws.com:aud": "us-east-1:12345678-90ab-cdef-1234-567890abcdef"
        }
      }
    }
  ]
}
```

The `Condition.StringEquals.cognito-identity.amazonaws.com:aud` is
the **identity pool ID**. The pool ID is filled in by your bootstrap
script. Without the condition, **any Cognito Identity Pool** could
assume your role — a serious cross-tenant risk.

### The permissions policy — three common shapes

#### Shape 1: Shared read-only bucket (least privilege)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": ["arn:aws:s3:::public-assets/*"]
    }
  ]
}
```

Every authenticated user can read the same `public-assets/*` prefix.
This is what you want for marketing assets, product images, etc.

#### Shape 2: Per-user S3 prefix (the classic Identity Pool pattern)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowUserToListTheirOwnPrefix",
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": ["arn:aws:s3:::user-uploads"],
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
        "arn:aws:s3:::user-uploads/${cognito-identity.amazonaws.com:sub}/*"
      ]
    }
  ]
}
```

This is the "dropbox" pattern: every user gets a sub-prefix named
after their `sub` (e.g. `s3://user-uploads/12345678-90ab-cdef-.../`).
The `Condition` block ensures user A cannot see or modify user B's
files. **This is the policy we use in `identity_pool_demo.py`.**

#### Shape 3: Per-user DynamoDB row (less common, more complex)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["dynamodb:GetItem", "dynamodb:Query"],
      "Resource": ["arn:aws:dynamodb:us-east-1:123456789012:table/Users"],
      "Condition": {
        "ForAllValues:StringEquals": {
          "dynamodb:leadingKeys": ["${cognito-identity.amazonaws.com:sub}"]
        }
      }
    }
  ]
}
```

DynamoDB IAM policies can use `dynamodb:leadingKeys` to enforce that
the partition key matches the `sub`. This is the row-level-security
pattern for DynamoDB. **It's complex and hard to test** — most apps
proxy through Lambda + API Gateway (section 4) for DynamoDB access
and use Identity Pools only for S3.

### The guest role (unauthenticated)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": ["arn:aws:s3:::public-landing-page/*"]
    }
  ]
}
```

That's it. One statement. Read-only on a single prefix. **Never**
give the guest role write access. **Never** give the guest role
access to anything in your `user-uploads` bucket.

### The `${...}` substitution variables

Cognito Identity Pools substitute four variables in policy documents
at assume-time:

| Variable | Meaning |
|---|---|
| `${cognito-identity.amazonaws.com:aud}` | The identity pool ID |
| `${cognito-identity.amazonaws.com:sub}` | The user's identity ID (UUID) |
| `${cognito-identity.amazonaws.com:amr}` | The auth method (e.g. `["cognito-idp"]`) |
| `${cognito-identity.amazonaws.com:email}` | The user's email (only if `email` is a verified attribute) |

The first three are always available. The fourth requires the user
to have a verified email.

### The credentials lifecycle

When Identity Pools assume the role, the resulting STS credentials
have a TTL of 1 hour by default. Your client SDK should refresh at
~75% of the TTL (e.g. after 45 minutes). The `Expiration` field in
the `GetCredentialsForIdentity` response tells you exactly when.

If you want a longer or shorter TTL, set it on the Identity Pool:

```python
identity.set_identity_pool_roles(
    IdentityPoolId=pool_id,
    RoleMappings={...},
    Roles={"authenticated": role_arn},
)
# Or use UpdateIdentityPool with the new Cognito credential duration
# (this is in the pool's AuthFlows settings, not on the role).
```

Actually: as of 2024, the credential TTL is set on the **Cognito
Credential** settings via `UpdateIdentityPool` with
`CognitoIdentityProviders` adjustments, or via the console. The
role's `MaxSessionDuration` is a separate cap (1 hour by default,
12 hours max).

### Testing your policies

The hard part. The only definitive way to test is:

1. Bootstrap the pool + role.
2. Mint a real Identity ID.
3. Call STS `AssumeRoleWithWebIdentity` with the role.
4. Use the resulting credentials to call S3, DynamoDB, etc.
5. Assert what was allowed and what was denied.

`moto` does not implement `SetIdentityPoolRoles` or
`GetCredentialsForIdentity`, so this is the part of the course
you'll need to test against a real AWS account or a local
**LocalStack** instance. The `identity_pool_demo.py` script
documents this gap explicitly in the docstring.

In production, IAM Access Analyzer is your best friend — it can
flag overly-permissive policies and unused permissions.

## Hands-on

No code yet. Write the **trust policy** and **permissions policy**
for a fictional "user-uploads" S3 bucket where every user can
read/write their own prefix. Compare your answer to Shape 2 above.

Then go to the IAM console and create the role by hand:

- IAM → Roles → Create role → "Web identity" → Identity provider =
  `cognito-identity.amazonaws.com`
- Paste your trust policy
- Add the permissions policy (start with Shape 2)
- Save the role ARN

You'll use this role in L14.

## Quiz prep

For this lecture, focus on:

- The two parts of a role (trust policy + permissions policy)
- The 3 substitution variables and when to use each
- Why the guest role should be much smaller than the auth role
- Why you should always include the `cognito-identity.amazonaws.com:aud`
  condition

## Further reading

- AWS docs — Identity Pools and IAM: <https://docs.aws.amazon.com/cognito/latest/developerguide/iam-roles.html>
- IAM policy variables: <https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_variables.html>
- Cognito condition keys: <https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-cognito-identity>

## What's next

Next is **L14 — Hands-on: Identity Pool with boto3 + moto**, the
climax of section 3: a 140-line boto3 script that creates a real
Identity Pool, plus 5 moto tests.