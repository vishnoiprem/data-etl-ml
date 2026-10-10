# Section 7 — Glue Pipeline Debug (Lectures L52-L59)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
>
> This file bundles 8 lecture scripts (L52-L59) for Section 7.

---

## L52 — Section Overview (1:21)

> "Section 7 covers the 5 most common Glue pipeline failures and how to fix each one. The failures are: 1) script retrieval, 2) launch + argument, 3) resource policy, 4) identity policy, 5) workflow trigger. For each, I'll show you the symptom, the root cause, and the fix."

---

## L53 — Section Prerequisite (1:59)

> "Before we start debugging, you should have the pipeline from Section 6 deployed and the Glue Job running. If not, go back and run that section first. The debugging section assumes you have a working baseline."

---

## L54 — Fix Error Retrieving The Script (5:40)

> "Symptom: the Glue Job fails immediately with `Error retrieving the script: s3:GetObject access denied`. Root cause: the script is in `s3://<source-bucket>/scripts/`, but the IAM role cannot read it. Two sub-causes: a) the IAM role's identity policy is missing `s3:GetObject` on the source bucket; b) the source bucket's *bucket policy* denies `s3:GetObject` from the role. The fix: check the IAM role's policy (it should have `s3:GetObject` on `arn:aws:s3:::<source-bucket>/*`), and check the bucket policy (it should not deny the role's principal). In `downloads/glue_pipeline_stack.yaml`, the inline policy `GlueJobS3Access` has a `ReadScript` statement that grants `s3:GetObject` on the script's exact key."

Lab: introduce the bug (deny the bucket policy on `s3:GetObject`), watch the Job fail, fix it.

---

## L55 — Fix Launch Error And Glue Argument Error (5:40)

> "Symptom 1: `Launch error: resource limits exceeded`. Root cause: the account's concurrent Glue Job run limit is 1 (the default). A previous run is still in STARTING or RUNNING. Fix: wait for the previous run to complete, or request a quota increase. Symptom 2: `Argument error: --source-bucket is required`. Root cause: the script's `if arg.startswith('--source-bucket=')` is looking for the argument with the dash, but the Job's `DefaultArguments` has the argument with the underscore (`--source_bucket`). Fix: make the key consistent. AWS Glue convention is to use dashes for default arguments (`--source-bucket`); the script must match."

Lab: introduce the underscore-vs-dash typo, watch it fail, fix it.

---

## L56 — Fix Resource Policy Error - Error Reading From Source Bucket (3:33)

> "Symptom: `AccessDenied: s3:GetObject on s3://<source-bucket>/input/city_temperature.csv`. The IAM role's identity policy is correct, the trust policy is correct, the Job is starting — but the read fails. Root cause: the *source bucket's bucket policy* denies `s3:GetObject` from the role's principal. The bucket policy is the second policy that's evaluated (after the IAM identity policy). It can independently deny access. Common causes: a) the bucket policy has a `Deny` statement that includes the role's ARN, b) the bucket policy requires a specific source IP (e.g., a VPC endpoint) and the Job is not running from that VPC. Fix: edit the bucket policy to allow the role, or remove the source IP constraint."

Lab: introduce a `Deny` statement in the bucket policy, watch the Job fail, fix it.

---

## L57 — Fix Identity Policy Error - Error Reading The Key (3:00)

> "Symptom: same as L56, but the bucket policy is fine. Root cause: the IAM role's identity policy is missing the right `s3:GetObject` permission. Specifically, the policy might grant `s3:GetObject` on `arn:aws:s3:::<source-bucket>` (the bucket itself) but not on `arn:aws:s3:::<source-bucket>/*` (the objects). Or it might grant `s3:GetObject` on the bucket but not `s3:ListBucket` (which is needed for `s3:GetObject` to work on a prefix). Fix: ensure the policy has both `s3:GetObject` on `arn:aws:s3:::<source-bucket>/*` AND `s3:ListBucket` on `arn:aws:s3:::<source-bucket>`."

Lab: remove the `s3:GetObject` from the identity policy, watch it fail, add it back.

---

## L58 — Workflow Running GlueJob2 (1:34)

> "Now run the Glue Job as part of a Workflow. A Workflow is a named collection of Triggers, Jobs, and Crawlers. Create the Workflow in the console: Glue → Workflows → Add workflow. Name: `glue-course-workflow`. Add the GlueJob2 trigger. Run the workflow. The workflow run takes 5-7 minutes (Job run + DPU provisioning + post-run cleanup). The run history shows each step's start/end time and success/failure."

---

## L59 — Recap (4:26)

> "Five failure modes, five fixes. 1) `Error retrieving the script` — check both the IAM identity policy AND the bucket policy for `s3:GetObject` on the script's key. 2) `Launch error: resource limits` — wait for the previous run, or increase the quota. 3) `Argument error` — check the script's argument key matches the Job's `DefaultArguments` (dashes vs underscores). 4) `Resource policy error` — check the *bucket* policy, not just the IAM policy. 5) `Identity policy error` — check both `s3:GetObject` AND `s3:ListBucket`. The pattern: read the error message; the message tells you which layer (script, launch, resource policy, identity policy) is wrong."

---

## Section 7 Quiz

5 questions, see `quizzes/section_7.md`.
