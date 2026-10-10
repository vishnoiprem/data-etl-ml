# Section 3 — Building with CDK (L11–L15)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **L-IDs:** L11–L15 | **Duration:** ~60 min | **Quizzes:** `quizzes/section_3.md`
> **Working artifact:** `code/lambda-api/` — Lambda + API Gateway + S3 + IAM.

Section 3 is where we stop drawing diagrams and start building real
stacks. The `lambda-api/` project is the canonical "API Gateway +
Lambda + S3 + IAM" stack that you can extend to almost any
serverless CRUD API.

## Lectures

| L# | Title | Min | File |
|---|---|---|---|
| L11 | L2 constructs for Lambda, API Gateway, S3, IAM | 12 | `lecture_scripts/L11_l2_overview.md` |
| L12 | Building a Lambda function with `lambda.Code.fromAsset` | 12 | `lecture_scripts/L12_lambda_function.md` |
| L13 | Building a REST API with `apigateway.LambdaRestApi` | 12 | `lecture_scripts/L13_apigw_lambda.md` |
| L14 | IAM roles, policies, and `grantInvoke` patterns | 12 | `lecture_scripts/L14_iam_grants.md` |
| L15 | Putting it together — end-to-end serverless stack | 12 | `lecture_scripts/L15_end_to_end_stack.md` |

## Working code

| Project | Stack summary | Tests |
|---|---|---|
| `code/lambda-api/` | Lambda (Node 20) + API GW REST + S3 asset bucket + IAM role | 8 Jest assertions on the synthesized template |
