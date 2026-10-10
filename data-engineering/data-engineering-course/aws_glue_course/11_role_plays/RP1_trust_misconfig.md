# Role Play 1 — Diagnose Glue Job Failure: Role/Trust Misconfig (Glue Can't Assume Role)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
>
> **Pacing:** 8-10 minutes total
> **Audience:** Section 8 of *AWS Glue - The Complete Masterclass* (the in-course role play; this script is the full version with worked answers)
> **Personas:**
> - **Priya** (learner) — junior DevOps engineer, 6 months on the job
> - **Prem** (instructor playing the part of the senior DE) — the user is the senior DE

## Scenario

Priya: *"I deployed the `glue_pipeline_stack.yaml` CloudFormation template. Stack went CREATE_COMPLETE. The S3 buckets exist. The IAM role exists. But when I run the Glue Job from the console, it fails in 3 seconds with `Service: AWSGlue; Status Code: 400; Error Code: AccessDeniedException`. Can you take a look?"*

You (the senior DE) have 8 minutes to walk Priya through the diagnosis, identify the root cause, and fix it.

## Learning objectives

By the end of the role play, the learner should be able to:

1. Distinguish **trust policy** from **identity policy** in IAM.
2. Read the Glue Job error message and identify whether the failure is in the role's *trust* boundary or its *permission* boundary.
3. Attach the right `AssumeRole` trust policy to the `GlueJobRole` so that `glue.amazonaws.com` can assume it.
4. Verify the fix by re-running the job.

## Opening (60 seconds)

> **Prem:** "OK, walk me through what you did. Stack deployed cleanly?"
> **Priya:** "Yeah, CREATE_COMPLETE. I see `SourceBucket`, `TargetBucket`, `GlueJobRole`, and `GlueJob` in the resources."
> **Prem:** "Good. When you ran the job, what was the exact error?"
> **Priya:** "It says `AccessDeniedException` and the message is something about `glue.amazonaws.com is not authorized to perform sts:AssumeRole on the role`. I think the role is broken."

## Diagnosis (3-4 minutes)

The senior move: **do not start by editing anything**. Read the error message with the learner.

> **Prem:** "OK, the error message is your best friend. It says `is not authorized to perform sts:AssumeRole`. The action is `sts:AssumeRole`. That tells us this is a *trust policy* problem, not an *identity policy* problem. IAM has two halves: the *trust policy* says *who* can use the role. The *identity policy* says *what* the role can do once it's been assumed. We need to check the trust policy first."
> **Priya:** "How do I see the trust policy?"
> **Prem:** "In the console, IAM → Roles → GlueJobRole → Trust relationships tab. Or in the CLI: `aws iam get-role --role-name GlueJobRole` then read the `AssumeRolePolicyDocument`."

The fix: attach the right trust policy. There are 3 common mistakes:

1. The trust policy is empty.
2. The trust policy lists `ec2.amazonaws.com` (typo, copy-pasted from a different lab).
3. The trust policy uses the wrong account ID (cross-account confusion).

> **Prem:** "The CloudFormation template I gave you in `downloads/glue_pipeline_stack.yaml` has the right trust policy inline. Let me show you." [Read lines 87-94 of the YAML — the `AssumeRolePolicyDocument` block under `GlueJobRole`.]

## Fix (2 minutes)

Three options, ordered by preference:

1. **Re-deploy the stack with the corrected inline `AssumeRolePolicyDocument`.** Best — keeps IaC.
2. **Attach the standalone trust policy from `downloads/glue_service_trust_policy.json`.** Good — minimal blast radius.
3. **Hand-edit in the console.** Worst — drifts from IaC.

> **Prem:** "The fastest fix that doesn't drift is option 2: `aws iam update-assume-role-policy --role-name GlueJobRole --policy-document file://glue_service_trust_policy.json`. But the *right* fix is to update the CFN template, run `cfn update-stack`, and never hand-edit a role in prod again."

## Verification (1 minute)

Re-run the job from the console. Expected: the job starts, runs the Python shell, writes Parquet to the target bucket.

> **Prem:** "Now run it again. Watch for `AccessDeniedException` — if it's gone, we know the trust boundary is fixed. If you see a *different* `AccessDenied` saying `s3:GetObject` failed, that's the *identity* policy. That's a separate problem."

## Closing (30 seconds)

> **Prem:** "Two takeaways. One: every `AccessDenied` you ever see in AWS is either a trust problem or a permission problem. The error message tells you which — read it. Two: keep trust policies and identity policies in different files, and check them into git. The 3-minute debug you just did should not exist in 2026 — IaC should have caught it."

## Worked answer (for the instructor / grading)

- **Root cause:** the `AssumeRolePolicyDocument` either has no `glue.amazonaws.com` principal, or has the wrong one.
- **Fix:** attach the trust policy from `downloads/glue_service_trust_policy.json`, or update the CFN template.
- **Verification:** re-run the job, confirm CREATE_COMPLETE in the Glue Job run history, confirm Parquet files appear in the target bucket under `output/by_country_year_month/`.
- **Senior follow-up:** the *next* failure mode is the identity policy. If the trust fix doesn't help, check `GlueJobS3Access` is attached to the role.
- **Stretch:** "How would you catch this in CI?" Answer: a CFN-lint / `cfn_nag` rule that flags any IAM role without a service principal in its trust policy.

## What the role play tests

- **Diagnostic skill** — read the error message, identify trust vs identity.
- **Communication** — explain the difference to a junior who's never seen it before.
- **IaC discipline** — the fix should be in the template, not in the console.
- **Senior instinct** — the "next failure mode" question tests whether the learner can predict, not just react.

## Common mistakes learners make in this role play

- **Jumping to S3 bucket policies** before reading the error. The error says `AssumeRole` — that's the trust policy. Stop and look there first.
- **Editing the role in the console** and forgetting to update the CFN template. Next `cfn update-stack` clobbers their fix.
- **Not reading the error message at all** and googling "Glue AccessDenied". The first 3 Google results are about S3, not trust policies.
