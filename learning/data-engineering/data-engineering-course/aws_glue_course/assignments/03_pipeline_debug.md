# Assignment 03 — Glue Pipeline Debugging

> **Section:** 7 (Glue pipeline debug)
> **Due:** End of week 3
> **Deliverable:** A "post-mortem" markdown document (max 1 page) describing the bug you introduced, how you diagnosed it, and the fix.

## Objective

Practice the **5 common Glue pipeline failure modes**:
1. `AccessDenied` on `sts:AssumeRole` — trust policy.
2. `AccessDenied` on `s3:GetObject` — bucket policy or identity policy.
3. `Resource limit exceeded` — concurrent job run limit.
4. `Error retrieving script` — script location or IAM.
5. `Argument error` — argument key mismatch.

The deliverable proves you can:
- Read a Glue Job error message and identify the failure category.
- Diagnose via the console + CloudWatch + IAM policy simulator.
- Apply the right fix (CFN update, not console hand-edit).

## Steps

1. **Start from a working stack** (Assignment 02). Verify the Job runs and the Parquet output is correct.
2. **Introduce a bug** — pick one of the 5 failure modes above. Modify the stack (or the bucket policy, or the IAM role) to break it.
3. **Diagnose** as if you were a junior DE — read the error message, check the trust policy, check the identity policy, check the bucket policy, check the argument keys.
4. **Fix** — apply the right fix. If you broke the CFN template, fix the template and re-run `update-stack`. If you broke the bucket policy in the console, fix the policy in the console.
5. **Document** the post-mortem.

## Acceptance criteria

- The post-mortem has 4 sections: **Bug** (what you broke), **Symptom** (the error message), **Diagnosis** (what you checked and in what order), **Fix** (the change you made, and why).
- The diagnosis section shows that you used the error message to identify the failure category *before* making any changes.
- The fix section shows that you used `cfn update-stack` (or equivalent) rather than a console hand-edit. (Exception: if the bug was in a resource that CFN does not own, like a manually-added bucket policy.)

## Stretch (optional, 1 hour)

- Introduce 3 bugs, not 1, and diagnose all 3. Use the **trust/identity/argument** mnemonic to triage.
- Write a `cfn_nag` rule (or a `cfn-lint` rule) that would have caught the bug at template-validation time. The rule should be a single regex or a single Python function.
