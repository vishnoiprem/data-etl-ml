# Section 1 Quiz — Foundations

> 10 questions, multi-choice. Answers hidden in collapsible blocks.
> Expand only after you've attempted the question.

---

**Q1.** What is the central promise of Infrastructure as Code (IaC)?

- A. IaC is always cheaper than clicking the console
- B. IaC makes infrastructure reproducible, reviewable, and recoverable
- C. IaC requires you to learn a new programming language
- D. IaC only works for serverless workloads

<details><summary>Show answer</summary>

**B — IaC makes infrastructure reproducible, reviewable, and recoverable.** These are the 3 promises from L01: the same template produces the same environment; a change is a PR; a rollback is a `git revert`.

</details>

---

**Q2.** Which of the following is a **declarative** IaC tool?

- A. AWS CDK
- B. A `boto3` script that creates an S3 bucket
- C. AWS CloudFormation
- D. Pulumi

<details><summary>Show answer</summary>

**C — AWS CloudFormation.** Declarative tools describe the *desired end state*; CFN is the canonical example. CDK and Pulumi are *imperative* (you write the steps in a real language), even though they compile to declarative CloudFormation.

</details>

---

**Q3.** Which AWS service does AWS CDK v2 compile to behind the scenes?

- A. Terraform
- B. AWS CloudFormation
- C. AWS Proton
- D. AWS Service Catalog

<details><summary>Show answer</summary>

**B — AWS CloudFormation.** `cdk synth` emits a CloudFormation template; `cdk deploy` submits it as a CFN change set.

</details>

---

**Q4.** Which npm package ships the L2 constructs in CDK v2?

- A. `@aws-cdk/aws-s3`
- B. `aws-cdk-lib`
- C. `constructs`
- D. `cdk-runtime`

<details><summary>Show answer</summary>

**B — `aws-cdk-lib`.** In v1 each AWS service had its own package (`@aws-cdk/aws-s3`, etc.). v2 unified them into one package; you import sub-paths like `import * as s3 from 'aws-cdk-lib/aws-s3'`.

</details>

---

**Q5.** What's the role of the `constructs` package?

- A. It's a CloudFormation schema validator
- B. It provides the `Construct` base class that CDK is built on
- C. It's a CLI for `cdk synth`
- D. It's the package that holds your Lambda code

<details><summary>Show answer</summary>

**B — It provides the `Construct` base class.** The construct pattern is generic; `constructs` is a separate package so it can be used without CDK.

</details>

---

**Q6.** Which command confirms your AWS CLI credentials are working?

- A. `aws whoami`
- B. `aws sts get-caller-identity`
- C. `aws s3 ls`
- D. `aws configure list`

<details><summary>Show answer</summary>

**B — `aws sts get-caller-identity`.** It returns a JSON blob with your account, userId, and ARN. If it errors with "Unable to locate credentials," re-run `aws configure`.

</details>

---

**Q7.** What does `cdk bootstrap` create in your AWS account?

- A. The CDK CLI
- B. A CloudFormation stack called `CDKToolkit` with an S3 bucket + IAM role
- C. A new AWS account
- D. A new VPC

<details><summary>Show answer</summary>

**B — A CloudFormation stack called `CDKToolkit` with an S3 bucket + IAM role.** CDK uses these to upload assets and run the deploy Lambda. It runs **once per account/region** and is idempotent.

</details>

---

**Q8.** Which command checks your CDK install for common misconfigurations?

- A. `cdk init`
- B. `cdk synth`
- C. `cdk doctor`
- D. `cdk verify`

<details><summary>Show answer</summary>

**C — `cdk doctor`.** It flags common issues like the wrong Node version or missing AWS credentials.

</details>

---

**Q9.** Which Node version does CDK v2 recommend?

- A. Node 14
- B. Node 16
- C. Node 20+
- D. Node 24

<details><summary>Show answer</summary>

**C — Node 20+.** CDK v2 is built and tested against Node 20; older versions may work but are not the canonical target.

</details>

---

**Q10.** What is **drift** in IaC terms?

- A. A bug in the CDK CLI
- B. The actual state of a resource diverging from its declared template
- C. A failed `cdk deploy`
- D. A version mismatch between the CLI and the library

<details><summary>Show answer</summary>

**B — The actual state of a resource diverging from its declared template.** It happens when someone changes a resource in the console after it was deployed via IaC. `cdk drift` (or CloudFormation's drift detection) can find it.

</details>
