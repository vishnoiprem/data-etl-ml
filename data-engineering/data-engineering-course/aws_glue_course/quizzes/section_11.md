# Section 11 Quiz — Role Plays & Capstone

> 5 questions, multi-choice, single answer. The answer key is at the bottom. This quiz is a *synthesis* quiz: every question tests the ability to apply Sections 1–10 to the 3 role plays in the course (RP1: Diagnose Glue Job Failure — Role/Trust Misconfig; RP2: Glue Streaming Job is Falling Behind; RP3: Pitch Glue Data Quality to a Skeptic Manager).

---

**Q1.** RP1 — A Glue Job fails on its first run with `AccessDeniedException: User: arn:aws:sts::111122223333:assumed-role/GlueJobRole/... is not authorized to perform: sts:AssumeRole on resource: arn:aws:iam::444455556666:role/SourceBucketRole`. What is the **first** thing you do?

- A. Re-deploy the CloudFormation stack so the role is recreated
- B. Read the error message carefully and identify that the *target* role's trust policy does not allow the *calling* role/principal
- C. Click into the role in the IAM console and edit its permissions by hand
- D. Open the S3 bucket policy on the source bucket and add a wider `Principal`

---

**Q2.** RP2 — Your streaming Glue Job is falling behind (Kinesis `IteratorAge` is climbing). Your manager pings you: *"What's going on? Should we just add more workers?"* What is your **first** response?

- A. "I need ~30 minutes to look at the CloudWatch metrics (IteratorAge, CPU, GC, batch sizes, Kinesis throttling) before I give you a plan"
- B. "Yes, bump the worker count from 2 to 10 right now"
- C. "It's probably schema drift on the producer side; let me check"
- D. "Open a Sev-1 ticket and page the on-call"

---

**Q3.** RP3 — You're pitching a new Glue Data Quality pipeline to a skeptical, non-technical manager. What's the **first** thing you say to get buy-in?

- A. "Glue DQ is built on DeeQu and supports 20+ rule types out of the box"
- B. "Last quarter's $100K incident — and the regulatory fine we narrowly avoided — were both caused by bad data getting past our checks; here's what a DQ pipeline would have caught"
- C. "Let me show you a quick demo of the Glue Studio DQ node"
- D. "DQ costs about 0.44 DPU-hours per run, so it's basically free"

---

**Q4.** RP1 — You fix the *trust* policy on the cross-account role (the one that was blocking `sts:AssumeRole`). You re-run the Glue Job. It still fails — this time with `AccessDeniedException: ... is not authorized to perform: s3:GetObject on resource: arn:aws:s3:::source-bucket/...`. What is wrong, and what is the next step?

- A. The role is in the wrong region — re-create it in `us-east-1`
- B. The bucket policy is missing a `Deny` statement — remove it
- C. The *identity* policy on the role (e.g. `GlueJobS3Access`) is missing the `s3:GetObject` permission for the source bucket/prefix; add it
- D. The Glue Job needs `--job-language` set to `python`; switch it from `scala`

---

**Q5.** RP2 — The streaming job is now healthy (IteratorAge is back to ~0, lag is steady). A teammate asks: *"Can I delete the checkpoint directory on S3 to save storage costs?"* What do you say?

- A. Yes — the job is healthy, the checkpoint is no longer needed
- B. No — the checkpoint is what lets the job resume from where it left off after a restart; deleting it forces a full re-read of the entire stream from the beginning (a multi-hour backfill of duplicate data)
- C. Yes — but only after deleting the Kinesis stream
- D. No — Kinesis Streams charges per shard-hour, not per checkpoint

---

# Answer Key

1. **B** — Read the error message first. The error literally says `sts:AssumeRole`, which means the *trust* policy on the target role is the problem (RP1, 1 min setup → 2 min diagnose). Re-deploying (A) won't help if the trust policy in the IaC is wrong; editing the role in the console (C) drifts from CloudFormation/IaC; opening the S3 bucket policy (D) addresses a different error — the stack trace points at `sts:AssumeRole`, not `s3:*`.

2. **A** — Buy yourself 30 minutes to look at the data (RP2, 1 min setup → 2 min diagnose/decide). The metrics tell you *why* the job is falling behind: it could be a small batch size, a skewed partition, a hot key, a producer surge, or GC pressure — each of which has a *different* fix. Bumping workers (B) is premature optimization and may not help (or may cost 5× more). Assuming schema drift (C) without evidence is guessing.

3. **B** — Lead with the *cost of not having* DQ, framed in business terms the manager cares about (dollars lost, regulatory exposure, customer churn). This is RP3, 30 sec opening. A technical pitch (A) or a demo (C) before the budget conversation is secured will get the request deprioritized. DPU-hour cost (D) is true but irrelevant if the manager doesn't yet see the *value*; it answers a question they didn't ask.

4. **C** — The trust fix opened the door (`sts:AssumeRole` now works), but the *identity* policy on the assumed role still doesn't grant the S3 permission the job needs (RP1, 1 min fix). This is the classic "trust vs identity" distinction: trust policy = who can assume this role; identity policy = what this role can do once assumed. Region (A), bucket `Deny` (B), and `--job-language` (D) are red herrings — the stack trace says `s3:GetObject` on the source bucket, which is a missing `Allow` in the role's identity policy.

5. **B** — The checkpoint is the streaming job's resume token; deleting it means the next restart re-reads the entire stream from `TRIM_HORIZON` (RP2, 1 min verification). For a stream that's been running for days, that's hours of duplicate writes downstream, wasted DPU-hours, and a re-do of any windowed aggregations. (A) is wrong because the checkpoint is required for *every* restart, not just failures. (C) is wrong because the checkpoint is independent of the Kinesis stream itself. (D) is true but unrelated to the question.
