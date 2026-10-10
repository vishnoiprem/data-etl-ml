# L11 — Recap + Create GlueJobRole

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 2 — IAM / KMS / SNS
> **Duration target:** 1:13 (recap) + 3:00 (lab) = ~4:00

## Part 1 — Recap (1:13)

> "Five things to remember from Section 2. One: IAM has 2 halves — the trust policy says *who* can use a role; the identity policy says *what* the role can do. Two: KMS has a *key policy* in addition to IAM identity policies; both are evaluated. Three: SNS fans out independently to each subscriber; one subscriber's failure does not affect the others. Four: every Glue Job needs an IAM role with the `AWSGlueServiceRole` managed policy plus an inline policy for S3 access. Five: the trust policy of `GlueJobRole` must allow `glue.amazonaws.com` to call `sts:AssumeRole`. That's the most common cause of `AccessDenied` on a Glue Job."

## Part 2 — Create GlueJobRole (3:00 lab)

This is the culminating lab: create the `GlueJobRole` that every Glue Job in the course will use.

### Prerequisites

- Lectures L07 + L08 completed. `GlueJobRole` exists with the `AWSGlueServiceRole` managed policy.
- (Optional) KMS key from L09 if you want to enable SSE-KMS encryption on the buckets.

### Lab steps

1. **Open the role in the IAM console.** IAM → Roles → `GlueJobRole`.
2. **Verify the trust policy.** Click the 'Trust relationships' tab. The principal must be `glue.amazonaws.com`. If it's wrong, fix it (see role play L57 for the diagnosis).
3. **Add the inline S3 access policy.** Click 'Add inline policy' → JSON tab. Paste the `GlueJobS3Access` policy (see `downloads/glue_pipeline_stack.yaml`, the `GlueJobS3Access` block under `GlueJobRole.Policies`). The policy grants:
   - `s3:GetObject` + `s3:ListBucket` on the source bucket (`arn:aws:s3:::<source-bucket>` + `/*`)
   - `s3:PutObject` + `s3:GetObject` + `s3:ListBucket` + `s3:DeleteObject` on the target bucket
   - `s3:GetObject` on the script's exact key
   - `logs:CreateLogGroup` + `logs:CreateLogStream` + `logs:PutLogEvents` on `*` (for CloudWatch)
4. **Review the policy.** Click 'Review policy'. Name it `GlueJobS3Access`. Click 'Create'.
5. **Verify.** The role summary now shows 2 attached policies: `AWSGlueServiceRole` (managed) and `GlueJobS3Access` (inline). The trust policy lists `glue.amazonaws.com`.

### Acceptance criteria

- `GlueJobRole` has 2 attached policies: `AWSGlueServiceRole` + `GlueJobS3Access`.
- The role's trust policy allows `glue.amazonaws.com` to assume it.
- The role can be selected as the `Role` for a new Glue Job (test in Section 7).

### What's next

- In Section 3, you'll learn the AWS CLI to deploy this role + the S3 buckets + the Glue Job in one CloudFormation stack.
- In Section 5, you'll use this role in the first Glue Job.
- In Section 8 / L57, you'll debug a trust-policy failure on this role.

## On-screen

- The role's summary page showing 2 attached policies.
- The 4 statements of the `GlueJobS3Access` policy, each highlighted.