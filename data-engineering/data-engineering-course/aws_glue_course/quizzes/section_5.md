# Section 5 Quiz — CloudFormation Templates for Glue

> 5 questions, multi-choice, single answer. The answer key is at the bottom.

---

**Q1.** In a CloudFormation template, where do you define user-overridable inputs that can be passed in at stack-create time (e.g., `EnvironmentName`, `BucketName`)? What does `!Ref MyParameter` return inside the `Resources` section?

- A. In the `Mappings` section; `!Ref` returns the parameter's default value
- B. In the `Parameters` section; `!Ref` returns the value supplied at stack creation (or the default)
- C. In the `Outputs` section; `!Ref` returns the exported value
- D. In the `Metadata` section; `!Ref` returns the resource's logical ID

---

**Q2.** A CloudFormation stack fails to create a Glue Job with the error: `Role ... is not authorized to assume the role / cannot be assumed by AWS Glue`. What is the **most common** cause of this failure?

- A. The IAM role is missing the `AWSGlueServiceRole` managed policy
- B. The role's `AssumeRolePolicyDocument` does **not** list `glue.amazonaws.com` as a principal (or lists the wrong service, e.g., `ec2.amazonaws.com`)
- C. The role's `Path` is set to `/service-role/`
- D. The role's `MaxSessionDuration` is too short

---

**Q3.** In a CFN template you need to embed a Glue Job's bucket name into a script argument string, like `--source-bucket my-glue-bucket-2024`. The bucket name is created in the same template as a resource. Which intrinsic function is the cleanest way to build this string?

- A. `!Ref` alone, because it always returns the full string
- B. `!Sub`, which substitutes `${MyBucket}` placeholders inside a template string
- C. `!Join`, which is the only way to concatenate strings in CFN
- D. `!GetAtt`, because it returns the bucket's name attribute

---

**Q4.** A team updates their stack and changes the `BucketName` property of an `AWS::S3::Bucket` resource from `glue-bucket-prod` to `glue-bucket-prod-v2`. CloudFormation returns an error on update. Why, and what is the standard workaround?

- A. S3 bucket names must be globally unique across all AWS accounts, so the new name is rejected
- B. CloudFormation cannot update `AWS::S3::Bucket` resources at all and always requires replacement
- C. S3 bucket names are **immutable** in CloudFormation; changing `BucketName` returns an error. The standard workaround is to put the bucket in a **separate stack** so the rest of the resources can be updated
- D. S3 bucket names can only contain lowercase letters, so `v2` is rejected

---

**Q5.** You run `aws cloudformation deploy` for a stack containing an `AWS::IAM::Role` and an `AWS::Glue::Job` that references that role. CloudFormation reports `CREATE_COMPLETE` for the role but `CREATE_FAILED` for the Glue Job with a transient IAM/consistency error. You immediately retry the stack update and it succeeds. What is the most likely explanation?

- A. CloudFormation does not wait for IAM resources to propagate before creating the Glue Job, and the role was not yet visible to Glue at the moment the Job was created
- B. The Glue Job's script had a syntax error
- C. The role's trust policy was malformed
- D. S3 buckets in the same stack were still being created

---

# Answer Key

1. **B** — `Parameters` section; `!Ref` returns the supplied value. Per the AWS CloudFormation docs, the `Parameters` section declares inputs you can pass at stack creation (or accept defaults for), and `!Ref` on a parameter returns the value the user supplied (or the `Default`). `Mappings` are static lookup tables (not user input), `Outputs` are values exported *after* creation, and `Metadata` is arbitrary template metadata. See: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/parameters-section-structure.html

2. **B** — Wrong trust policy. For a Glue Job to assume a role, the role's `AssumeRolePolicyDocument` must list `glue.amazonaws.com` as a `Principal` with the `sts:AssumeRole` action. A common misconfiguration is pointing the trust at `ec2.amazonaws.com` (which is for EC2 instance profiles) or omitting the trust policy entirely. The `AWSGlueServiceRole` managed policy (option A) grants Glue service permissions but does not control *who* can assume the role — that is the trust policy. See: https://docs.aws.amazon.com/glue/latest/dg/create-an-iam-role.html

3. **B** — `!Sub` for string interpolation. `!Sub "string with ${ResourceName}"` substitutes references inline, which is ideal for building script argument strings. `!Ref` (A) returns the logical ID or value but is not a string-interpolation helper; `!Join` (C) works for concatenation but is more verbose; `!GetAtt` (D) returns an attribute (e.g., `Arn`) of a resource, not its name unless the attribute happens to be `BucketName`. See: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-sub.html

4. **C** — S3 bucket names are immutable in CloudFormation. Per the AWS docs, you cannot update the `BucketName` property of an existing `AWS::S3::Bucket` — CloudFormation returns an error because S3 bucket names cannot be changed after creation. The standard pattern is to put the bucket in its own dedicated stack (or use a generated name) so that updates to the application stack don't trip on this immutability. Option A is wrong because uniqueness is checked at bucket creation, not at update; option B is wrong because most S3 properties *are* updatable. See: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-s3-bucket.html

5. **A** — IAM eventual consistency / propagation delay. CloudFormation typically waits for resources to reach a steady state, but IAM role propagation to AWS Glue is eventually consistent. On the first attempt the role may not yet be visible to the Glue service when the Job's `Role` reference is resolved; on the retry, propagation has completed and the Job creates successfully. Options B and C would fail deterministically on every retry, and D is unrelated — buckets and IAM roles are independent resources. See: https://docs.aws.amazon.com/IAM/latest/UserGuide/troubleshoot_general.html
