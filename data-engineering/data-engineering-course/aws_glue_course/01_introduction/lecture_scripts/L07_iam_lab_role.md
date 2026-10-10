# L07 — IAM Lab: Setting Up an IAM Role

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 1 — Introduction
> **Duration target:** 3:13

## What this lecture covers

- The second IAM hands-on: create an IAM role that an AWS service (Glue) can assume. This is the lab where you build the `GlueJobRole` for the first time.

## Narration

> "Now let's create an IAM role. Roles are different from users: a user has long-term credentials; a role is *assumed* by a trusted principal. The most common use case is the service role — an AWS service like Glue assumes the role to make API calls on your behalf. Open IAM, click 'Roles', click 'Create role'. For the trusted entity type, select 'AWS service'. For the use case, choose 'Glue'. This sets the trust policy to allow `glue.amazonaws.com` to call `sts:AssumeRole` on this role. Click 'Next'. Attach the `AWSGlueServiceRole` managed policy — this gives the role the permissions Glue needs to manage its own resources (Job runs, Crawlers, the Data Catalog). Add an inline policy for S3 access — we'll write that policy in the next lecture. Click 'Next: Tags' (skip), 'Next: Review'. Name the role `GlueJobRole`. Click 'Create role'."

## Lab steps

1. IAM → Roles → Create role.
2. Trusted entity: AWS service. Use case: Glue.
3. Permissions: attach `AWSGlueServiceRole`.
4. Tags: optional.
5. Review: name = `GlueJobRole`. Create.

## Acceptance criteria

- The role `GlueJobRole` exists.
- The trust policy lists `glue.amazonaws.com` as a principal that can assume it.
- The role has the `AWSGlueServiceRole` managed policy attached.

## On-screen

- The 4-step wizard: Select trusted entity → Add permissions → Add tags → Review.