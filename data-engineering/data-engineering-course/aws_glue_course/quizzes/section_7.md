# Section 7 Quiz — Glue Pipeline Debug

> 5 questions, multi-choice, single answer. The answer key is at the bottom.

---

**Q1.** A Glue Job fails with `Error retrieving the script: s3:GetObject access denied`. The job's IAM role has `s3:GetObject` on the source bucket. The script is in the source bucket. What is the most likely cause?

- A. The IAM role's identity policy is wrong
- B. The bucket policy on the source bucket denies `s3:GetObject` from the role's principal
- C. The script does not exist
- D. The KMS key policy is wrong

---

**Q2.** A Glue Job fails with `Launch error: resource limits exceeded`. You have 1 concurrent job run allowed (the default). What is the most likely cause?

- A. A previous job run is still in the STARTING or RUNNING state
- B. The IAM role is wrong
- C. The script is too large
- D. The S3 bucket does not exist

---

**Q3.** A Glue Job fails with `Argument error: --source-bucket is required`. The script reads `arg.startswith("--source-bucket=")`. The Job's `DefaultArguments` includes `--source_bucket my-bucket`. What is the most likely cause?

- A. The script is wrong
- B. The argument key uses underscore (`--source_bucket`) but the script expects a dash (`--source-bucket`)
- C. The argument value is missing
- D. The IAM role is wrong

---

**Q4.** A Glue Job succeeds but writes 0 rows to the target. The script reads from `s3://source-bucket/input/` and writes to `s3://target-bucket/output/`. The job run log shows the read step returned 1,000 rows. What is the most likely cause?

- A. The read returned 1,000 rows but the filter dropped all of them
- B. The write step failed silently
- C. The IAM role is wrong
- D. The S3 bucket does not exist

---

**Q5.** A Glue Workflow runs Job A, then Job B, then Job C. Job A succeeds. Job B fails. Job C does *not* run. Why?

- A. Job C's IAM role is wrong
- B. The Workflow's default behavior on failure is to stop (unless the Trigger is configured to continue)
- C. Job C is not in the workflow
- D. The Workflow is paused

---

# Answer Key

1. **B** — Bucket policy. S3 evaluates *both* the IAM identity policy and the bucket policy. If the bucket policy denies access (e.g., to a specific VPC endpoint or source IP), the request fails even if the identity policy allows it.
2. **A** — Concurrency limit. The default Glue concurrent job run limit per account is 1. A second job run will fail with `Launch error: resource limits exceeded` until the first run completes.
3. **B** — Underscore vs dash. AWS Glue uses dashes in default arguments (`--source-bucket`), but custom arguments can use underscores. The mismatch is a common typo.
4. **A** — Filter. The most common cause: a `filter` or `where` clause in the script that drops all rows. Check the script's filter logic; in the lab, it's often `filter(F.col("country").isin(["US"]))` when the CSV has different country codes.
5. **B** — Default stop-on-failure. Workflow Triggers default to "skip on failure" (not "continue"). To make C run after B fails, configure the B→C Trigger with `Trigger.Conditions.OnDemand` or `Continue`.
