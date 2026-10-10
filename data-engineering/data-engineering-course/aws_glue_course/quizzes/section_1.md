# Section 1 Quiz — Introduction / IAM / KMS / SNS

> 5 questions, multi-choice, single answer. The answer key is at the bottom — try the questions first.

---

**Q1.** Which IAM concept answers the question *"Who can use this resource?"*?

- A. Identity policy
- B. Trust policy
- C. Permission boundary
- D. Session policy

---

**Q2.** A Glue Job fails with `AccessDeniedException` and the message mentions `sts:AssumeRole`. What is the most likely root cause?

- A. The S3 bucket policy denies `s3:GetObject`
- B. The IAM role's trust policy does not allow `glue.amazonaws.com` to assume it
- C. The KMS key policy denies `kms:Decrypt`
- D. The Glue Job's worker count is too low

---

**Q3.** Which of the following is *not* a valid IAM principal?

- A. `arn:aws:iam::123456789012:user/Bob`
- B. `glue.amazonaws.com`
- C. `s3:GetObject`
- D. `arn:aws:iam::123456789012:role/GlueJobRole`

---

**Q4.** You create a KMS key with no policy modifications. The root user of the AWS account can use it. The Glue Job's IAM role has `kms:Decrypt` and `kms:Encrypt` on the key ARN. The Glue Job fails with `AccessDenied` when trying to decrypt an S3 object encrypted with the key. What is the most likely cause?

- A. The IAM role is missing `s3:GetObject` permission
- B. The KMS key policy does not grant the IAM role's principal `kms:Decrypt`
- C. The S3 bucket is in a different region
- D. KMS keys cannot be used with Glue Jobs

---

**Q5.** You publish a message to an SNS topic. The topic has 3 subscribers: an SQS queue, a Lambda function, and an email address. The Lambda function is misconfigured and throws an exception on every message. What happens to the SQS queue and the email?

- A. Both also fail, because SNS topics fan out and fail atomically
- B. Both receive the message, because SNS fans out independently to each subscriber
- C. The SQS queue receives the message but the email does not
- D. The email receives the message but the SQS queue does not

---

# Answer Key

1. **B** — Trust policy. The trust policy is the half of an IAM role that says *who* (which principal) can call `sts:AssumeRole` on it. The identity policy is the half that says *what* the role can do once assumed.
2. **B** — Trust policy. The error explicitly says `sts:AssumeRole` was denied, which is a trust-policy problem (not an identity-policy problem).
3. **C** — `s3:GetObject` is an *action*, not a principal. The other three are valid IAM principals (user ARN, service principal, role ARN).
4. **B** — KMS key policy. Even when the IAM role's identity policy allows `kms:Decrypt`, the KMS *key policy* is evaluated independently and must also grant the role access. KMS uses key-policy + identity-policy intersection.
5. **B** — SNS fans out independently. Each subscriber gets a copy of the message; one subscriber's failure does not affect the others.
