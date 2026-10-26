# Section 7 Quiz — Glue Job Debug

> 5 questions, multi-choice, single answer. The answer key is at the bottom.

---

**Q1.** A Glue Job fails at launch with `Error retrieving the script: s3:GetObject access denied`. The IAM role attached to the Job has an identity policy that grants `s3:GetObject` on the script's bucket. Which of the following is the most likely root cause?

- A. The script file does not exist in S3 — the S3 key was typed wrong.
- B. The script file is encrypted with a KMS key the role cannot use, so S3 returns AccessDenied on GetObject.
- C. The bucket policy on the script's bucket contains an explicit `Deny` (e.g. restricting access to a specific VPC endpoint or source IP) that overrides the role's identity policy.
- D. The script's `.py` extension is wrong — Glue 4.0 only loads `.scala` scripts from S3.

---

**Q2.** A Glue Job fails immediately with `Launch error: resource limits exceeded`. The account has not been throttled and the IAM role is valid. What is the most likely cause, and what is the correct fix?

- A. The Job's worker type (e.g. `G.2X`) is too large for the account's vCPU quota — request a quota increase.
- B. Another Glue Job in the same account is in `STARTING` or `RUNNING` state; the default concurrent run limit is 1, so the second Job is rejected. Fix: wait for the other Job to finish, or raise the concurrent-run limit in the account settings.
- C. The S3 source bucket has a `Deny` on `s3:ListBucket` — switch to a different bucket.
- D. The script imports a library not in Glue 4.0's default set — install it via a Job parameter.

---

**Q3.** A Glue Job fails with `Argument error: --source_bucket is required`. The Job's `DefaultArguments` are configured as `--source-bucket my-bucket` (with a dash) and the script calls `getResolvedOptions(sys.argv, ["source_bucket"])`. Which statement is correct?

- A. Glue 4.0 automatically converts dashes to underscores in argument keys, so this should work — it is a bug in the script.
- B. Glue passes arguments through as written. The keys must match exactly; `--source-bucket` and `--source_bucket` are different keys, so the script must ask for `["source-bucket"]` (or the Job must define `--source_bucket`).
- C. The script must use `getResolvedOptions(sys.argv, ["--source_bucket"])` including the leading dashes.
- D. `getResolvedOptions` only reads from `--extra-py-files`, not from `DefaultArguments`.

---

**Q4.** A Glue Job runs to `SUCCEEDED` but writes 0 rows to the target. The script reads 1,000 rows from S3, applies a `filter(...)` on a country column, and writes the result. The most likely root cause is:

- A. The target S3 path is wrong — Glue wrote the 1,000 rows to a different prefix and reports 0 because the target folder is empty.
- B. The filter clause is dropping all rows — e.g. `filter(col("country").isin(["US"]))` when the CSV actually contains `USA`, `U.S.`, or a different case. The Job succeeds because there is no error, just an empty DataFrame.
- C. The IAM role is missing `s3:PutObject` on the target bucket, but Glue still reports `SUCCEEDED` and writes 0 rows.
- D. Glue's DynamicFrame always drops rows that do not match the schema, so 1,000 rows are dropped during cast.

---

**Q5.** A Glue Workflow runs Job A → Job B → Job C. Job A succeeds, Job B fails, and Job C does not run. What is the default Trigger behavior, and how do you make Job C run regardless of Job B's result?

- A. The default is `Continue` — Job C should have run. The failure is caused by a misconfigured predicate; check the trigger's `Logical` condition.
- B. The default is `Skip on failure` (or the equivalent `CONDITIONAL` predicate). To make C run regardless of B's outcome, the B→C Trigger must be reconfigured to `Continue` (an `ON_DEMAND` style or unconditional predicate that fires on any terminal state of B).
- C. Glue Workflows always run all jobs in the chain — Job C should have run. The cause is a permissions issue on Job C's IAM role.
- D. Job C is blocked because the Workflow entered a `STOPPED` state. Restart the Workflow manually; there is no trigger setting that changes this.

---

# Answer Key

1. **C** — A bucket policy `Deny` overrides the role's identity policy. When S3 evaluates an `s3:GetObject` request, an explicit `Deny` in the resource policy wins over any `Allow` in the identity policy. This is an **S3 bucket policy** issue, not a missing-identity-grant, missing-script, or KMS issue. (B is plausible-looking but KMS failures typically surface as `AccessDenied` on `kms:Decrypt`, not on `s3:GetObject` for the object itself.)

2. **B** — Glue enforces a per-account concurrent run limit (default 1) on Jobs. If another Job is `STARTING` or `RUNNING`, new Job launches fail with `resource limits exceeded`. The fix is to wait, or raise the limit under **Settings → Job runs (concurrent runs per account)** in the Glue console. This is a **Glue service quota**, not an IAM or vCPU/EC2 issue.

3. **B** — Glue 4.0 does **not** convert dashes to underscores. `getResolvedOptions` requires the key as Glue sees it: `--source-bucket` and `--source_bucket` are distinct keys. The fix is to align them — either change the script to `["source-bucket"]` or change the Job's DefaultArguments to `--source_bucket`. The script is asking for the **wrong key name**, not the wrong format, and the bug is in the script's argument list, not in `DefaultArguments`.

4. **B** — A filter that drops every row (because the value doesn't match what's actually in the data) produces a successful Job run with 0 output rows. The fix is to inspect a sample of the source data, normalize the values (case, whitespace, country code scheme), and re-run. This is a **script/filter-logic** issue, not an IAM or schema-cast issue. (C is incorrect: an `s3:PutObject` denial would surface as an `AccessDenied` error, not a `SUCCEEDED` with 0 rows.)

5. **B** — Workflow Triggers default to a `CONDITIONAL` / "skip on failure" predicate: downstream Jobs only fire when upstream Jobs succeed. To run Job C regardless of Job B's outcome, edit the B→C Trigger and change its action from conditional to `Continue` (an unconditional trigger that fires on any terminal state of B — `SUCCEEDED`, `FAILED`, or `TIMEOUT`). This is a **Trigger configuration** issue, not an IAM or Workflow-state issue.
