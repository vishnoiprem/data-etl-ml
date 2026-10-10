# Section 5 Quiz — CloudFormation Templates for Glue

> 5 questions, multi-choice, single answer. The answer key is at the bottom.

---

**Q1.** In a CloudFormation template, which section declares a value the user can override at stack-create time?

- A. Resources
- B. Parameters
- C. Mappings
- D. Outputs

---

**Q2.** You reference a parameter in a Resources section: `BucketName: !Ref SourceBucketName`. What does `!Ref` return?

- A. The bucket's ARN
- B. The bucket's name (the parameter's value)
- C. The bucket's region
- D. The bucket's IAM role

---

**Q3.** You write a CloudFormation template that creates a Glue Job. The stack goes CREATE_FAILED at the Glue Job. The Glue Job's IAM role is created successfully. What is the most likely cause?

- A. The IAM role is not attached to the Glue Job
- B. The Glue Job's `Role` property uses `!GetAtt GlueJobRole.Arn` but the role is not yet propagated
- C. The IAM role's trust policy is missing `glue.amazonaws.com`
- D. The S3 bucket does not exist yet

---

**Q4.** Which CloudFormation intrinsic function would you use to inject a string from a parameter into a script URL like `s3://bucket/scripts/glue_job.py`?

- A. `!Ref`
- B. `!Sub`
- C. `!Join`
- D. `!GetAtt`

---

**Q5.** You update a CloudFormation stack that contains an S3 bucket. You change the `BucketName` property to a new (globally unique) name. What happens?

- A. The bucket is replaced (the old one is deleted, the new one is created)
- B. The bucket's name is updated in place
- C. CloudFormation returns an error because bucket names are immutable
- D. The stack update is rejected

---

# Answer Key

1. **B** — Parameters. Parameters are the user-overridable inputs to a stack.
2. **B** — The parameter's value. `!Ref` on a parameter returns the parameter's value; `!Ref` on a resource returns the resource's logical ID (or its `Name` if the resource has one).
3. **C** — Trust policy. Same root cause as the role-play: the IAM role's trust policy must allow `glue.amazonaws.com` to assume it. If the role is created but the Glue Job cannot assume it, the stack fails at the Glue Job resource.
4. **B** — `!Sub`. `!Sub "s3://${BucketName}/scripts/glue_job.py"` substitutes the `BucketName` parameter (or resource) into the string. `!Join` would also work but is more verbose.
5. **C** — CloudFormation returns an error because S3 bucket names are immutable. The bucket must be deleted and re-created. (The standard workaround is to use a separate stack for the bucket so the rest of the stack can be updated.)
