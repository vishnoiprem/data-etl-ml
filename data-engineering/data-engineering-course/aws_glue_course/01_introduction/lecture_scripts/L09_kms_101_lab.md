# L09 — KMS 101 and KMS Lab: Setting Up a KMS Key

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 1 — Introduction
> **Duration target:** 3:03

## What this lecture covers

- KMS = Key Management Service. The 2 key concepts: the KMS key (the master encryption key) and the key policy (the IAM policy that controls who can use the key).

## Narration

> "KMS is the AWS service for encryption keys. Every KMS key has a key policy — it's a *resource-based policy* (like an S3 bucket policy) attached to the key itself. The key policy is *required*: every KMS key must have one, and the default key policy allows only the root user of the account to use the key. To let other IAM principals use the key, you must add them to the key policy. The 3 most common operations on a KMS key are `kms:Encrypt`, `kms:Decrypt`, and `kms:GenerateDataKey`. For S3, you typically use SSE-KMS encryption on a bucket, and the bucket uses a KMS key to encrypt every object. When the Glue Job reads from the bucket, the Job's IAM role needs `kms:Decrypt` on the key — AND the key policy must also grant the role's principal `kms:Decrypt`. Both policies are evaluated. Let me show you how to create a KMS key and edit the key policy to grant the Glue Job's role access."

## Lab steps

1. KMS → Customer managed keys → Create key.
2. Key type: symmetric. Use case: Encrypt and decrypt. Key alias: `glue-course-key`.
3. Key administrators: your IAM user.
4. Key usage permissions: add `GlueJobRole` to the list of principals that can use the key.
5. Review and create.

## Acceptance criteria

- The KMS key `glue-course-key` exists.
- The key policy grants `kms:Encrypt`, `kms:Decrypt`, `kms:GenerateDataKey` to `GlueJobRole`.

## On-screen

- The 4-step wizard: key type → key details → key administrators → key usage permissions → review.