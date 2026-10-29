# Section 3 Quiz — Building with CDK

> 10 questions, multi-choice. Answers hidden in collapsible blocks.

---

**Q1.** Which `aws-cdk-lib` sub-path holds Lambda constructs?

- A. `aws-cdk-lib/aws-functions`
- B. `aws-cdk-lib/aws-lambda`
- C. `aws-cdk-lib/lambda`
- D. `aws-cdk-lib/aws.compute`

<details><summary>Show answer</summary>

**B — `aws-cdk-lib/aws-lambda`.** All L2 modules follow the `aws-cdk-lib/aws-<service>` pattern.

</details>

---

**Q2.** What's the difference between `apigw.RestApi` and `apigw.LambdaRestApi`?

- A. `LambdaRestApi` is the L3 pattern that wires up a `{proxy+}` resource with `AWS_PROXY` integration
- B. `RestApi` is for HTTP APIs, `LambdaRestApi` is for REST APIs
- C. `LambdaRestApi` doesn't exist — it's `apigatewayv2`
- D. `LambdaRestApi` is the same as `RestApi` but in a different module

<details><summary>Show answer</summary>

**A — `LambdaRestApi` is the L3 pattern that wires up a `{proxy+}` resource with `AWS_PROXY` integration.** For 80% of CRUD APIs, this is the right answer. Reach for `RestApi` when you need custom integrations, request validation, or multi-resource graphs.

</details>

---

**Q3.** Which `lambda.Code` flavor is the production default?

- A. `fromInline`
- B. `fromAsset`
- C. `fromEcrImage`
- D. `fromS3`

<details><summary>Show answer</summary>

**B — `fromAsset`.** CDK bundles a local directory, uploads it to the bootstrap S3 bucket, and configures the Lambda to pull from there. `fromInline` is for tiny demos; `fromEcrImage` is for container-image Lambdas.

</details>

---

**Q4.** What does `bucket.grantRead(fn)` add to the Lambda's role?

- A. `s3:*` on `*`
- B. A single `s3:GetObject` statement scoped to the bucket's ARN
- C. Nothing — `grantRead` is for humans
- D. A managed policy `AmazonS3FullAccess`

<details><summary>Show answer</summary>

**B — A single `s3:GetObject` statement scoped to the bucket's ARN.** The grant methods produce **least-privilege** policies scoped to the specific resource. This is why they're preferred over hand-rolled `addToRolePolicy` calls.

</details>

---

**Q5.** Which managed policy is auto-attached to a Lambda's execution role by the L2 `lambda.Function` construct?

- A. `AdministratorAccess`
- B. `AWSLambdaBasicExecutionRole`
- C. `AWSLambdaVPCAccessExecutionRole`
- D. None — the L2 doesn't attach any policy

<details><summary>Show answer</summary>

**B — `AWSLambdaBasicExecutionRole`.** It grants permission to write CloudWatch Logs. You extend it via `fn.addToRolePolicy(...)` or by being the target of another construct's `grant*` call.

</details>

---

**Q6.** Which API Gateway integration type does `LambdaRestApi` use?

- A. `HTTP`
- B. `MOCK`
- C. `AWS_PROXY`
- D. `LAMBDA_PROXY`

<details><summary>Show answer</summary>

**C — `AWS_PROXY`.** API Gateway forwards the entire request to the Lambda as a single event payload; the Lambda's response is passed straight back. (There is no `LAMBDA_PROXY` — `AWS_PROXY` is the canonical name for Lambda integrations.)

</details>

---

**Q7.** Which CDK construct creates an asset bucket for a Lambda function automatically?

- A. The user has to create it manually with `s3.Bucket`
- B. `lambda.Function`
- C. `apigw.LambdaRestApi`
- D. `cdk.App`

<details><summary>Show answer</summary>

**B — `lambda.Function`.** When you use `lambda.Code.fromAsset(path)`, CDK creates (or reuses) a bucket in the bootstrap account to hold the zipped deployment package.

</details>

---

**Q8.** How do you read a `CfnOutput` value after `cdk deploy`?

- A. `cdk output <StackName> -c key=<OutputName>`
- B. The console only — there's no CLI for it
- C. `aws cloudformation describe-stacks` only
- D. By reading `cdk.out/`

<details><summary>Show answer</summary>

**A — `cdk output <StackName> -c key=<OutputName>`.** Or read it from the CloudFormation console under **Outputs**.

</details>

---

**Q9.** Which L2 module holds the IAM constructs?

- A. `aws-cdk-lib/aws-iam`
- B. `aws-cdk-lib/aws-roles`
- C. `aws-cdk-lib/aws-access`
- D. `aws-cdk-lib/aws-policies`

<details><summary>Show answer</summary>

**A — `aws-cdk-lib/aws-iam`.** It ships `Role`, `Policy`, `PolicyStatement`, `ServicePrincipal`, etc.

</details>

---

**Q10.** In a `LambdaRestApi`, what does `defaultCorsPreflightOptions` do?

- A. Enables CORS by pre-wiring an `OPTIONS` method on every resource
- B. Sets the API's default content type
- C. Sets a CloudWatch alarm on 4xx errors
- D. Configures JWT auth

<details><summary>Show answer</summary>

**A — Enables CORS by pre-wiring an `OPTIONS` method on every resource.** It saves you from writing the preflight handler yourself.

</details>
