# Section 7 Quiz — Glue Job Debug

> 5 questions, multi-choice, single answer. The answer key is at the bottom.

---

**Q1.** A CloudFormation stack deploys a Glue Job, an IAM role, and 2 S3 buckets. The stack goes CREATE_FAILED. The event log shows the IAM role failed to create with `EntityAlreadyExists: Role with name GlueJobRole already exists`. What is the most likely cause?

- A. The role was created in a different account
- B. A previous deployment left the role behind (stack was deleted but the role was retained)
- C. CloudFormation bug
- D. The role name is too long

---

**Q2.** You deploy the pipeline stack and the Glue Job runs successfully. You then go to the target S3 bucket. The expected Parquet output is missing. What is the first thing you check?

- A. The job run history in Glue
- B. The CloudFormation stack events
- C. The S3 bucket policy
- D. The IAM role's identity policy

---

**Q3.** The Glue Job's script reads `s3://source-bucket/input/`. The script writes to `s3://target-bucket/output/`. The job fails with `AccessDenied` on the read. The IAM role's identity policy grants `s3:GetObject` on `arn:aws:s3:::source-bucket/*` and `s3:ListBucket` on `arn:aws:s3:::source-bucket`. What is missing?

- A. Nothing — the policy is complete
- B. The policy must also grant `s3:ListBucket` on the source bucket
- C. The policy must also grant `s3:GetObject` on the target bucket
- D. The IAM role is missing the `AWSGlueServiceRole` managed policy

---

**Q4.** The Glue Job's script uses `sys.argv` to read `--source-bucket` and `--target-bucket`. The job runs but reads from a hardcoded `s3://wrong-bucket/`. What is the most likely cause?

- A. The arguments are not configured in the Job's `DefaultArguments`
- B. The script is buggy
- C. The IAM role is wrong
- D. The Glue version is too old

---

**Q5.** You want to inspect the logs of a Glue Job run. Where do you go?

- A. CloudWatch Logs, in the log group `/aws-glue/jobs/logs-v2/`
- B. S3, in the `spark-logs/` prefix
- C. The Glue console, in the Job run history → "Logs" tab
- D. All of the above

---

# Answer Key

1. **B** — Retained role. The role was not deleted when a previous stack was deleted. CloudFormation does not delete IAM roles by default (to prevent accidental lockout). Delete the role manually or use `Retain` + `Delete` policy.
2. **A** — Job run history. The first check is always: did the job actually run? Did it succeed? Did it write to the right place? The job run history in Glue shows the start/end time, error message (if any), and DPU seconds consumed.
3. **A** — Nothing. The policy is complete. (If the answer is wrong, the diagnosis is that the trust policy is missing — but the question is about the identity policy, which is fine.)
4. **B** — Script bug. The arguments are probably configured correctly in the Job; the script is just not reading them. Common bug: the script's `if arg.startswith(...)` checks look for `--source-bucket` but the Job passes `--source_bucket` (typo or version difference).
5. **D** — All of the above. Glue Jobs write logs to CloudWatch Logs (driver output), S3 (`spark-logs/` for the Spark UI), and the Glue console aggregates both.
