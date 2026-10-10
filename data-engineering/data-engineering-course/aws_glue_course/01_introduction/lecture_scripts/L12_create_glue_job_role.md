# L12 — Create GlueJobRole

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 1 — Introduction
> **Duration target:** N/A (lab, no video)

## What this lecture covers

- The culminating lab: create the `GlueJobRole` that we'll use for the rest of the course. This is the artifact that ties Sections 1-2 together.

## Narration

> "This is the lab where you build the role that every Glue Job in the course will use. We already created `GlueJobRole` in Lecture L7 — that was the basic version with just `AWSGlueServiceRole`. Now we add the inline policy for S3 access. From the IAM console, open `GlueJobRole`, click 'Add inline policy', click the JSON tab, and paste the `GlueJobS3Access` policy from `downloads/glue_pipeline_stack.yaml`. Review and save. The role is now ready for use. You'll reuse this role in every Glue Job we create in Sections 3-9."

## Lab steps

1. IAM → Roles → GlueJobRole → Add inline policy.
2. JSON tab.
3. Paste the `GlueJobS3Access` policy (see `downloads/glue_pipeline_stack.yaml`).
4. Review policy.
5. Save.

## Acceptance criteria

- `GlueJobRole` has 2 attached policies: `AWSGlueServiceRole` (managed) + `GlueJobS3Access` (inline).
- The role's trust policy allows `glue.amazonaws.com` to assume it.
- The role can be selected as the `Role` for a new Glue Job.

## On-screen

- The role's summary page showing 2 attached policies.