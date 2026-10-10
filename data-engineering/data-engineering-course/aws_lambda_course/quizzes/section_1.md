# Section 1 Quiz — Introduction

> 10 questions, multi-choice, single answer. Answers are hidden in collapsible
> blocks; expand only after you've attempted the question.

---

**Q1.** How many hands-on enterprise use cases anchor this course?

- A. 1
- B. 2
- C. 3
- D. 5

<details><summary>Show answer</summary>

**C — 3.** They are: (1) the S3 → Lambda → DynamoDB banking JSON pipeline, (2) the API Gateway + Lambda + S3 serverless CRUD API, and (3) the AWS Bedrock (Cohere) Generative AI use case.

</details>

---

**Q2.** Which of the following is **not** one of the 4 downloadable resources for the course?

- A. `lambda_cheat_sheet.pdf`
- B. `boto3_patterns_cheat_sheet.pdf`
- C. `cfn_serverless_template_pack.zip`
- D. `glue_job_python_script.zip`

<details><summary>Show answer</summary>

**D — `glue_job_python_script.zip`.** That belongs to the AWS Glue course. The 4 Lambda course downloads are `lambda_cheat_sheet.pdf`, `boto3_patterns_cheat_sheet.pdf`, `cfn_serverless_template_pack.zip`, and `cdk_serverless_project_pack.zip`.

</details>

---

**Q3.** Which AWS region is recommended as the default for the entire course?

- A. `eu-west-1`
- B. `ap-southeast-1`
- C. `us-west-2`
- D. `us-east-1`

<details><summary>Show answer</summary>

**D — `us-east-1`.** Two reasons: AWS Bedrock (and the Cohere foundational model) is most reliably available in `us-east-1`, and the CloudFormation and CDK templates in sections 12 and 13 assume `us-east-1` for cross-service consistency.

</details>

---

**Q4.** Which Python version is used in the course's code samples?

- A. Python 2.7
- B. Python 3.8
- C. Python 3.11+
- D. Python 3.13 only

<details><summary>Show answer</summary>

**C — Python 3.11+.** The course targets Python 3.11 or newer with `boto3` 1.34+. Earlier 3.x versions mostly work, but 3.11+ is the canonical target.

</details>

---

**Q5.** Which command confirms that the AWS CLI is correctly configured with valid credentials?

- A. `aws whoami`
- B. `aws sts get-caller-identity`
- C. `aws s3 ls`
- D. `aws iam list-users`

<details><summary>Show answer</summary>

**B — `aws sts get-caller-identity`.** It returns a JSON blob with your AWS `Account`, `UserId`, and `Arn`. If it errors with `Unable to locate credentials`, you need to re-run `aws configure`.

</details>

---

**Q6.** Which GenAI service and model are used in the Generative AI use case (section 10)?

- A. Amazon SageMaker JumpStart with Llama
- B. AWS Bedrock with the Cohere foundational model
- C. Amazon Q with Titan
- D. OpenAI via a public API

<details><summary>Show answer</summary>

**B — AWS Bedrock with the Cohere foundational model.** Section 10 builds an end-to-end manufacturing-industry use case where API Gateway invokes Lambda, Lambda calls Bedrock (Cohere), and the response flows back through the API.

</details>

---

**Q7.** Which of the following is the **least** likely to be a hard prerequisite for this course?

- A. An AWS account (free tier is enough)
- B. Python 3.11+ installed
- C. Prior production Lambda experience
- D. AWS CLI v2 installed

<details><summary>Show answer</summary>

**C — Prior production Lambda experience.** Section 2 explicitly starts with "evolution from physical servers to Lambda" before opening the console. Beginners are the target audience.

</details>

---

**Q8.** According to the course, why should you use an IAM user (with `AdministratorAccess`) instead of the AWS account root user for day-to-day work?

- A. Because IAM users are free and root users cost $1/month
- B. Because the AWS console blocks root logins
- C. Because best practice is to lock down root, enable MFA, and use scoped IAM identities for development
- D. Because Lambda functions cannot assume the root user

<details><summary>Show answer</summary>

**C — Best practice is to lock down root, enable MFA, and use scoped IAM identities for development.** Using `AdministratorAccess` on a non-root IAM user is the simplest safe setup; we'll refine role scope (e.g. the Lambda execution role) in section 2.

</details>

---

**Q9.** Which two Infrastructure-as-Code tools are taught later in the course to implement the same serverless CRUD stack?

- A. Terraform and Pulumi
- B. AWS CDK v2 and AWS CloudFormation
- C. Ansible and Chef
- D. Serverless Framework and SAM only

<details><summary>Show answer</summary>

**B — AWS CDK v2 (section 12) and AWS CloudFormation (section 13).** We implement the same API Gateway + Lambda + S3 use case twice — once in TypeScript with CDK and once in YAML/JSON with CloudFormation — so you can pick the tool you prefer.

</details>

---

**Q10.** Section 2 (Lambda Basic Concepts Part 1) is best described as:

- A. An optional appendix for advanced students
- B. A hands-on GenAI deep dive
- C. A conceptual and console-walkthrough foundation that everything later depends on
- D. A CloudFormation-only module

<details><summary>Show answer</summary>

**C — A conceptual and console-walkthrough foundation that everything later depends on.** Section 2 covers Lambda's history, what Lambda is, the console tour, and the execution role; sections 4, 6, 8, 10, 11, 12, and 13 all build on these fundamentals.

</details>
