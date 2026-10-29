# Section 2 Quiz — S3 / CLI / CloudFormation

> 5 questions, multi-choice, single answer. The answer key is at the bottom.

---

**Q1.** Which S3 storage class is the cheapest for data you expect to read less than once per quarter and that you can wait hours to retrieve?

- A. S3 Standard
- B. S3 Standard-IA
- C. S3 Glacier Deep Archive
- D. S3 One Zone-IA

---

**Q2.** You run `aws s3 cp city.csv s3://my-bucket/`. The CLI returns `upload failed: ... An error occurred (403) when calling the PutObject operation: Forbidden`. You have IAM permission `s3:PutObject` on `arn:aws:s3:::my-bucket/*`. What is the most likely cause?

- A. The bucket does not exist
- B. The bucket policy denies `s3:PutObject` from your IP
- C. The IAM role's trust policy is wrong
- D. You forgot `aws configure`

---

**Q3.** You run `aws s3 sync ./local s3://my-bucket/prefix/`. The local directory has 1,000 files; the S3 prefix already has 800 of them. How many files does the CLI upload?

- A. 1,000
- B. 800
- C. 200
- D. 0 if all timestamps match

---

**Q4.** You write a CloudFormation template that creates an S3 bucket. You re-run the same template with the same parameters. What happens?

- A. The bucket is replaced
- B. CloudFormation returns `No updates are to be performed` because the resource is unchanged
- C. The bucket is created a second time with a new name
- D. CloudFormation returns an error because the bucket already exists

---

**Q5.** Which CloudFormation section is *required* to reference the value of one resource from another?

- A. Parameters
- B. Mappings
- C. Outputs
- D. Ref intrinsic function

---

# Answer Key

1. **C** — S3 Glacier Deep Archive. The cheapest storage class; retrieval times of 12 hours are acceptable.
2. **B** — Bucket policy denial. The IAM permission is fine; the *bucket policy* is the second policy that AWS evaluates, and it can independently deny access (e.g., by source IP, by VPC endpoint, by encryption requirement).
3. **C** — 200. `aws s3 sync` uploads only the files that don't exist or have a newer modification time on the local side.
4. **B** — `No updates are to be performed`. CloudFormation is idempotent: re-running with no changes is a no-op. (The bucket is not "replaced" because S3 bucket names are globally unique and the resource already exists.)
5. **D** — `Ref` intrinsic function. `!Ref GlueJobRole.Arn` returns the ARN of the role. (Outputs expose values; Ref references them within the template.)
