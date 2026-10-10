# L11 — Recap (Section 1)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 1 — Introduction
> **Duration target:** 1:13

## What this lecture covers

- A 60-second recap of the 5 things you should remember from Section 1.

## Narration

> "Five things to remember. One: IAM has 2 halves — the trust policy says *who* can use a role; the identity policy says *what* the role can do. Two: KMS has a *key policy* in addition to IAM identity policies; both are evaluated. Three: SNS fans out independently to each subscriber; one subscriber's failure does not affect the others. Four: every Glue Job needs an IAM role with the `AWSGlueServiceRole` managed policy plus an inline policy for S3 access. Five: the trust policy of `GlueJobRole` must allow `glue.amazonaws.com` to call `sts:AssumeRole`. That's the most common cause of `AccessDenied` on a Glue Job. In the next lecture, we'll create that role."

## 5 things to remember

1. IAM has trust + identity policies.
2. KMS has a key policy that's evaluated in addition to IAM policies.
3. SNS fans out independently.
4. Every Glue Job needs `GlueJobRole` with `AWSGlueServiceRole`.
5. The trust policy must allow `glue.amazonaws.com`.

## On-screen

- The 5 items in a checklist.