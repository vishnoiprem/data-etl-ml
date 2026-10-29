# Section 13 Quiz — AWS CloudFormation (L60–L70)

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Format:** 10 multiple-choice / short-answer questions. Click
> "Show answer" to reveal the answer and a one-line explanation.

## Instructions

- Each question has a single best answer unless explicitly stated.
- Try to answer without scrolling to the answer block.
- Use the question number when posting in the course Q&A.

---

### Q1

Which top-level CloudFormation section is **required** in every
template?

- A. `Parameters`
- B. `Resources`
- C. `Outputs`
- D. `Metadata`

<details><summary>Show answer</summary>

**B. `Resources`.** `Parameters`, `Outputs`, `Metadata`, `Mappings`,
and `Conditions` are all optional. `Resources` is the only
required top-level section because it declares what AWS should
actually create.

</details>

---

### Q2

In the L66 template the API Gateway method is declared as
`HttpMethod: GET`, but the integration to Lambda uses
`IntegrationHttpMethod: POST`. Why?

- A. API Gateway always uses POST, regardless of the public method.
- B. The `IntegrationHttpMethod` must be POST because the Lambda
  service invoke URL only accepts POST.
- C. POST is faster than GET.
- D. It is a CFN template bug; both should be GET.

<details><summary>Show answer</summary>

**B.** API Gateway calls the Lambda service's
`/invocations` endpoint, which only accepts POST. The public
method on the resource can be any HTTP verb; the integration
to Lambda is always POST.

</details>

---

### Q3

You deployed the full-stack template but `curl` to the API URL
returns `{"message":"User: ... is not authorized to perform:
lambda:InvokeFunction ..."}`. What is missing?

- A. The Lambda execution role
- B. The API Gateway deployment
- C. The `AWS::Lambda::Permission` resource
- D. The `AWS::IAM::Policy` resource

<details><summary>Show answer</summary>

**C.** API Gateway invokes Lambda via a service-to-service call
that is authorized by a **resource-based policy** on the Lambda
(`AWS::Lambda::Permission`). The execution role grants the
Lambda permissions to call *other* AWS services; it does not
control who can call the Lambda.

</details>

---

### Q4

In the full-stack template, which property of
`AWS::ApiGateway::Method.Integration` is a **constant** for any
Lambda proxy integration?

- A. `IntegrationHttpMethod: POST`
- B. `Type: AWS_PROXY`
- C. `Uri` shape
- D. Both A and B and C

<details><summary>Show answer</summary>

**D. All three are constant.** `AWS_PROXY` integration with a
Lambda is always:

- `Type: AWS_PROXY`
- `IntegrationHttpMethod: POST`
- `Uri: arn:aws:apigateway:<region>:lambda:path/2015-03-31/functions/<arn>/invocations`

Only the region and the function ARN change.

</details>

---

### Q5

You want to make the bucket name configurable per environment
without forking the template. Which section do you add?

- A. `Mappings`
- B. `Conditions`
- C. `Parameters`
- D. `Metadata`

<details><summary>Show answer</summary>

**C. `Parameters`.** The `Parameters` section declares inputs the
user supplies at deploy time — perfect for environment-specific
values like `BucketName`, `StageName`, etc.

`Mappings` are static lookup tables, `Conditions` are boolean
expressions, and `Metadata` is for tooling/console display.

</details>

---

### Q6

In the L70 template, the `Metadata` block contains
`AWS::CloudFormation::Interface`. What does it do?

- A. Declares a CFN macro for transforming the template at deploy time.
- B. Tells the CloudFormation console how to group and label
  parameters in the wizard.
- C. Adds a default value to a parameter.
- D. Marks a parameter as sensitive.

<details><summary>Show answer</summary>

**B.** `AWS::CloudFormation::Interface` is a UI directive only —
it groups parameters into collapsible sections in the console
wizard and lets you override the per-parameter label. It does
not change what the stack creates.

</details>

---

### Q7

You are deploying a template that creates a `AWS::IAM::Role` with
an explicit `RoleName`. Which capability flag do you need?

- A. `CAPABILITY_IAM`
- B. `CAPABILITY_NAMED_IAM`
- C. `CAPABILITY_AUTO_EXPAND`
- D. `CAPABILITY_NAMED_IAM` is not a real flag — only `CAPABILITY_IAM`

<details><summary>Show answer</summary>

**B. `CAPABILITY_NAMED_IAM`.** When a template creates IAM
resources with explicit names, you need both `CAPABILITY_IAM`
(to acknowledge IAM creation) and `CAPABILITY_NAMED_IAM` (to
acknowledge that you are *naming* them, which can collide with
existing resources).

`CAPABILITY_AUTO_EXPAND` is for templates that use macros.

</details>

---

### Q8

The full-stack template uses `aws cloudformation package` before
`aws cloudformation deploy`. What does `package` do?

- A. Validates the template syntax.
- B. Uploads local assets (Lambda zips, nested templates) to S3
  and rewrites the template so `Code.S3Bucket/S3Key` point at
  them.
- C. Compresses the template for faster deploys.
- D. Computes the cost of the stack.

<details><summary>Show answer</summary>

**B.** `aws cloudformation package` walks the template, finds
references to local files, uploads them to the asset bucket you
specify, and rewrites the template so the resource properties
point at the S3 URLs of the uploaded artifacts.

</details>

---

### Q9

In the API Gateway resource tree, what is the difference between
`{proxy}` and `{proxy+}` in a `PathPart`?

- A. There is no difference.
- B. `{proxy+}` is a "greedy" path parameter that matches any
  character including slashes; `{proxy}` matches a single segment.
- C. `{proxy+}` is used for POST; `{proxy}` is for GET.
- D. `{proxy+}` requires the request body to be base64 encoded.

<details><summary>Show answer</summary>

**B.** The `+` makes the path parameter greedy — it captures
across slashes. `{proxy+}` matches `/objects/a/b/c` as
`proxy = a/b/c`; `{proxy}` would only match `/objects/a` (one
segment).

</details>

---

### Q10

You want to confirm an API Gateway deployment captured the
methods correctly. What is the simplest command?

- A. `aws apigateway get-rest-api --rest-api-id <id>`
- B. `aws cloudformation describe-stack-resources --stack-name <name>`
  and look for `AWS::ApiGateway::Deployment`.
- C. `curl <api-url>/<stage>/<path>` and look at the response.
- D. Both B and C are useful (B is the IaC-friendly check, C is
  the runtime check).

<details><summary>Show answer</summary>

**D.** `describe-stack-resources` confirms the deployment
resource exists in the stack (IaC check), and a `curl` confirms
the deployment was wired to a stage and is actually invokable
(runtime check). Use both — if B succeeds but C fails, the
deployment captured an empty API (forgot `DependsOn`).

</details>
