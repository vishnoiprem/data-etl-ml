# L08 — IAM 101: Policies

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 1 — Introduction
> **Duration target:** 4:45

## What this lecture covers

- The structure of an IAM policy document. The 5 elements: `Version`, `Statement` (array), `Effect`, `Action`, `Resource`. Plus optional `Sid`, `Condition`, `Principal`.

## Narration

> "Every IAM policy is a JSON document. The structure is fixed: a `Version`, a `Statement` (which is an array of one or more statements), and each statement has at minimum an `Effect` ('Allow' or 'Deny'), an `Action` (e.g., 's3:GetObject'), and a `Resource` (an ARN or '*'). Optional fields: `Sid` (a statement ID for readability), `Principal` (only for resource-based policies; not needed for identity policies). Let's look at a real example — the inline policy we'll attach to `GlueJobRole` to give it S3 access. The policy says: Allow s3:GetObject and s3:ListBucket on the source bucket; allow s3:PutObject on the target bucket; allow logs:CreateLogGroup, logs:CreateLogStream, and logs:PutLogEvents on any resource. The policy is in `downloads/glue_pipeline_stack.yaml` — look at the `GlueJobS3Access` policy. Notice how the `Resource` field uses `!Sub` to inject the bucket names — this is how CloudFormation lets you parameterize policies."

## Key concepts

- **Identity policy**: attached to an IAM user, group, or role. Says what the *identity* can do.
- **Resource-based policy**: attached to a resource (e.g., S3 bucket, KMS key, SNS topic). Says who can access *that resource*. Often used in addition to (not instead of) identity policies.
- **Permission boundary**: a maximum-permissions wrapper around a role or user. The effective permissions are the *intersection* of the identity policy and the boundary.
- **Session policy**: passed at `sts:AssumeRole` time. Further restricts what the assumed session can do.
- **The evaluation logic**: by default, everything is *denied*. An explicit `Allow` grants access. An explicit `Deny` always wins (overrides any `Allow`).

## On-screen

- A side-by-side of a JSON policy and the YAML rendering in the CFN template.