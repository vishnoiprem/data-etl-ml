# Section 12 — AWS CDK v2 — Quiz

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 12 — AWS CDK v2 (Infrastructure as Code)
> **Lectures covered:** L71–L77
> **Pass bar:** 7 / 10

Ten multiple-choice / short-answer questions. Answers are in the
`<details>` blocks at the bottom of each question — click to reveal.

---

## Q1 — What is the AWS CDK?

- A. A replacement for CloudFormation that deploys directly without a CFN stack.
- B. An open-source framework that lets you define AWS infrastructure in a
     programming language and synthesizes to a CloudFormation template.
- C. A GUI drag-and-drop tool for designing VPC diagrams.
- D. A managed service that runs CloudFormation templates for you.

<details>
<summary>Answer</summary>
**B.** CDK is an IaC framework authored in TypeScript, Python, Java,
Go, or .NET. It compiles your code to a CloudFormation template that
AWS then deploys exactly as if you had hand-written it.
</details>

---

## Q2 — Which command-line tool produces a CloudFormation template from your CDK code?

- A. `cdk build`
- B. `cdk synth`
- C. `cdk compile`
- D. `cdk render`

<details>
<summary>Answer</summary>
**B. `cdk synth`.** It walks the construct tree, evaluates your code,
and writes a CFN template (and any asset zips) to `cdk.out/`.
</details>

---

## Q3 — Which two resources does `cdk bootstrap` create in your account?

- A. An EC2 instance and an SSH key pair.
- B. An S3 assets bucket and IAM roles for file/image publishing.
- C. A CloudWatch Logs Group and an SNS topic.
- D. A VPC with public and private subnets.

<details>
<summary>Answer</summary>
**B.** `cdk bootstrap` creates the `cdk-<acct>-<region>-assets-...`
S3 bucket and the file-publishing / image-publishing IAM roles. Without
it, `cdk deploy` fails the first time.
</details>

---

## Q4 — Match each L2 construct to the AWS resource it creates.

| CDK construct | AWS resource |
|---|---|
| 1. `s3.Bucket` | A. IAM role |
| 2. `iam.Role` | B. S3 bucket |
| 3. `lambda.Function` | C. REST API |
| 4. `apigateway.RestApi` | D. Lambda function |

<details>
<summary>Answer</summary>
1 → B, 2 → A, 3 → D, 4 → C.
</details>

---

## Q5 — Which `BucketEncryption` value gives you server-side encryption with S3-managed keys at no extra cost?

- A. `BucketEncryption.S3_MANAGED`
- B. `BucketEncryption.KMS_MANAGED`
- C. `BucketEncryption.KMS`
- D. `BucketEncryption.NONE`

<details>
<summary>Answer</summary>
**A. `S3_MANAGED`** (SSE-S3 with AES-256 and S3-managed keys). Free, no
KMS permissions, meets most compliance baselines.
</details>

---

## Q6 — Why do we construct the `S3Client` *outside* the handler function?

- A. Because AWS Lambda will throw a runtime error if you construct it inside.
- B. Because the SDK requires module-scope initialization to send requests.
- C. Because the execution environment is reused across invocations and
     module-scope clients reuse the underlying TLS connection.
- D. Because the SDK package only exports a singleton instance.

<details>
<summary>Answer</summary>
**C.** Lambda freezes the module graph after the first call, so a
client constructed at module scope is reused for the lifetime of the
execution environment. Re-creating it per invocation adds latency and
wastes TLS handshakes.
</details>

---

## Q7 — Which option makes the L2 `apigateway.RestApi` construct automatically respond to CORS preflight `OPTIONS` requests?

- A. `corsPreflight: true`
- B. `enableCors: true`
- C. `defaultCorsPreflightOptions: { allowOrigins: Cors.ALL_ORIGINS, ... }`
- D. Setting `Access-Control-Allow-Origin` on each method.

<details>
<summary>Answer</summary>
**C. `defaultCorsPreflightOptions`.** The L2 walks every method on the
API and adds the preflight handlers for you.
</details>

---

## Q8 — Which statement about `cdk destroy` is correct?

- A. It removes every resource in the stack including the bootstrap assets bucket.
- B. It removes the stack's resources; the bootstrap assets bucket and
     roles are kept for reuse.
- C. It only removes the IAM roles.
- D. It archives the stack but does not delete the resources.

<details>
<summary>Answer</summary>
**B.** `cdk destroy` deletes the stack and every resource the stack
owns (the S3 bucket, Lambdas, API, etc.). The bootstrap resources are
account-level and are reused by future stacks.
</details>

---

## Q9 — In the stack we built, what does the Lambda execution role's inline policy allow?

- A. `s3:*` on every bucket in the account.
- B. `s3:GetObject` and `s3:PutObject` on the specific bucket created by the stack.
- C. Administrator access (`*:*` on `*`).
- D. No permissions — Lambdas always have implicit permissions from the runtime.

<details>
<summary>Answer</summary>
**B.** The inline policy grants only `s3:GetObject` and `s3:PutObject`,
scoped to `arn:aws:s3:::<bucket>/*`. This is least privilege.
</details>

---

## Q10 — Short answer.

You are migrating a CDK v1 project (`@aws-cdk/core`) to CDK v2. Which two
package changes are required?

<details>
<summary>Answer</summary>
1. Replace `aws-cdk` (CDK v1) imports of `@aws-cdk/aws-s3`,
   `@aws-cdk/aws-lambda`, etc. with the single monolithic
   `aws-cdk-lib/aws-s3`, `aws-cdk-lib/aws-lambda`, etc.
2. Install `aws-cdk-lib` as a dependency (instead of individual
   `@aws-cdk/*` packages) and bump the `aws-cdk` CLI to `2.x`.

The CDK v2 CLI (`aws-cdk`) is still the entry point; only the
construct library imports changed.
</details>

---

## Score yourself

- 9–10 correct: ready for section 13 (CloudFormation) — or skip straight
  to the Bedrock GenAI use case in section 10.
- 7–8 correct: solid foundation. Re-read the lectures you missed before
  moving on.
- < 7 correct: redo L71–L77 with the `code/` project open in another
  tab. The hands-on muscle memory matters more than the quiz score.