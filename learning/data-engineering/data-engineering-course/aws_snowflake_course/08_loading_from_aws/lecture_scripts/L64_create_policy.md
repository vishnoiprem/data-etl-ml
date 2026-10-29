---
l_id: L64
title: "Creating policy"
duration: "7:00"
prereqs:
  - L63 (Upload files in S3)
---

# L64 — Creating policy

> **Section:** 8 — Loading from AWS
> **Duration:** 7:00

## Prereqs

- L63 — Upload files in S3

## Key terms

- **IAM policy** — a JSON document that grants permissions.
  Attached to a user, role, or group.
- **IAM role** — an identity with a permission policy that
  AWS services (EC2, Lambda) or external accounts (Snowflake)
  can **assume**.
- **`s3:GetObject`** — the action to read an object.
- **`s3:ListBucket`** — the action to list the bucket's
  contents.
- **Trust policy** — a separate JSON document that says
  *who* can assume the role.

## Lecture

For Snowflake to read from S3, we need an IAM role with the
right permissions. This lecture writes the **permission
policy**; L65 ties it to a Snowflake **storage integration**.

### The minimum permission set

Snowflake's S3 integration needs three actions:

- `s3:GetObject` — read an object.
- `s3:GetObjectVersion` — read a specific version (only if
  you have versioning on).
- `s3:ListBucket` — list the bucket's contents.

Save this as `policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:GetObjectVersion"
      ],
      "Resource": "arn:aws:s3:::pv-snowflake-course-2026/*"
    },
    {
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::pv-snowflake-course-2026"
    }
  ]
}
```

Two things to notice:

- The `GetObject` actions are scoped to the bucket's **objects**
  (`/*` suffix). The `ListBucket` action is scoped to the
  **bucket** itself (no suffix).
- The `Effect: Allow` and `Resource` ARN together form the
  "least privilege" rule. We grant exactly the actions
  Snowflake needs, on exactly the bucket we control.

### Apply the policy

```bash
aws iam create-policy \
    --policy-name SnowflakeS3ReadOnly \
    --policy-document file://policy.json
```

Expected output: an ARN like
`arn:aws:iam::123456789012:policy/SnowflakeS3ReadOnly`.

### Create the role Snowflake will assume

A **role** is an identity with a permission policy **and** a
trust policy. The trust policy says *who* can assume the role.
For Snowflake, the trust policy is special — it grants
`sts:AssumeRole` to the Snowflake AWS account.

First, retrieve the trust policy template Snowflake expects.
The exact ARN differs by region, so we look it up. For
`us-east-1`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:user/snowflake-demo"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

Wait — for **storage integrations**, the trust policy grants
the role to the **Snowflake account**, not to a user. The
right value comes from L65 (we'll get it from the
`STORAGE_AWS_IAM_USER_ARN` returned by the integration
object).

For now, save the policy as `trust.json` with a placeholder:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "AWS": "PLACEHOLDER" },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

```bash
aws iam create-role \
    --role-name SnowflakeS3IntegrationRole \
    --assume-role-policy-document file://trust.json
```

Then attach the permission policy to the role:

```bash
aws iam attach-role-policy \
    --role-name SnowflakeS3IntegrationRole \
    --policy-arn arn:aws:iam::123456789012:policy/SnowflakeS3ReadOnly
```

### The two-policy pattern

To summarise:

| Policy | Attached to | Says what |
|---|---|---|
| `SnowflakeS3ReadOnly` | The role | "This role can read S3" |
| `SnowflakeS3IntegrationRole` trust | The role | "Snowflake can assume me" |

A role is the **join** of a permission policy and a trust
policy. Without either, the role is useless.

### Why the trust policy matters

The trust policy is what makes the integration **secure**.
Without it, *any* AWS account could `sts:AssumeRole` and read
your bucket. With the trust policy locked to the Snowflake
account ARN, only Snowflake can assume the role — and only
Snowflake can read the bucket.

The placeholder above will be replaced by the actual Snowflake
ARN in L65.

### Permissions diagnostic

If the load fails with "AccessDenied", the most common causes:

1. The role's permission policy is missing one of the three
   actions.
2. The trust policy is wrong (no Snowflake principal).
3. The bucket policy (separate from the IAM policy) is
   blocking the access.

Use `aws sts assume-role` to manually test:

```bash
aws sts assume-role \
    --role-arn arn:aws:iam::123456789012:role/SnowflakeS3IntegrationRole \
    --role-session-name test
```

If this returns credentials, the role is configured correctly.
If it returns `AccessDenied`, the trust policy is the culprit.

## Hands-on

Save `policy.json`, run `aws iam create-policy`, then create
the role and attach the policy. Verify with
`aws iam get-role --role-name SnowflakeS3IntegrationRole`.

## Quiz prep

- What is the difference between an IAM policy and an IAM
  role?
- Why does a role need a trust policy?
- Which three S3 actions must the policy grant?

## Key takeaways

- Snowflake's S3 read-only policy needs `s3:GetObject`,
  `s3:GetObjectVersion`, and `s3:ListBucket`.
- A role = permission policy + trust policy.
- The trust policy locks the role to a specific principal
  (Snowflake's AWS account).
- If the integration fails with `AccessDenied`, the trust
  policy is the first thing to check.

## What's next

In **L65 — Creating integration object** we create the
`STORAGE INTEGRATION` in Snowflake, which ties S3, the IAM
role, and the storage location together.