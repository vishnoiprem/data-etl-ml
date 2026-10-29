---
lecture: L14
title: "IAM roles, policies, and grantInvoke patterns"
duration: "12:00"
section: 3
prereqs: ["L13"]
---

# L14 — IAM Roles, Policies, and `grantInvoke` Patterns

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 3 — Building with CDK
> **Duration:** 12:00

## Prereqs

L13 — API Gateway + Lambda

## Key terms

- **`iam.Role`** — an IAM role. Required for any service that needs
  to assume credentials.
- **`ServicePrincipal`** — the special principal that lets AWS
  services (like `lambda.amazonaws.com`) assume a role.
- **`grantX(other)`** — the family of helper methods on L2
  constructs that produce **least-privilege** IAM policies for you.
- **`Permissions Boundary`** — an upper bound on what a role can do,
  often used in org-wide guardrails.

## Lecture

The wrong way to do IAM in CDK:

```ts
// DON'T: hand-rolled policy JSON, easy to get wrong
fn.addToRolePolicy(new iam.PolicyStatement({
  actions: ['s3:*',            // too broad!
             'dynamodb:*',       // too broad!
             'logs:*'],
  resources: ['*'],
}));
```

The right way: use the **`grant*` methods** on L2 constructs. They
know the minimum set of permissions and resources that are actually
needed.

```ts
// Read access to the bucket — adds a single s3:GetObject statement
// scoped to this specific bucket's ARN.
bucket.grantRead(fn);

// Invoke permission — lets API Gateway call this Lambda.
api.grantInvoke(/* nothing — the integration is automatic */);

// Or, from the Lambda side, let API Gateway invoke it explicitly:
fn.grantInvoke(new iam.ServicePrincipal('apigateway.amazonaws.com'));
```

Common `grant*` methods:

| Method | Effect |
|---|---|
| `bucket.grantRead(fn)` | `s3:GetObject` + `s3:ListBucket` (scoped to bucket) |
| `bucket.grantWrite(fn)` | `s3:PutObject` + `s3:DeleteObject` |
| `bucket.grantReadWrite(fn)` | both |
| `table.grantReadWriteData(fn)` | DynamoDB read+write on the table |
| `topic.grantPublish(fn)` | `sns:Publish` on the topic |
| `queue.grantConsume(fn)` | `sqs:ReceiveMessage` + `sqs:DeleteMessage` |
| `api.grantInvoke(...)` | `execute-api:Invoke` on the stage |

The Lambda's role is **created for you** by `lambda.Function` (it
attaches `AWSLambdaBasicExecutionRole` for CloudWatch logs). You
extend it via `fn.addToRolePolicy(...)` or by being the target of
another construct's `grant*` call.

```ts
fn.addToRolePolicy(new iam.PolicyStatement({
  actions: ['secretsmanager:GetSecretValue'],
  resources: [`arn:aws:secretsmanager:${this.region}:${this.account}:secret:my-secret-*`],
}));
```

## Hands-on

Open `code/lambda-api/lib/lambda-api-stack.ts`. Find the
`this.assetsBucket.grantRead(this.handler)` line. Run
`npx cdk synth --quiet | jq` and observe that the synthesized
template contains a `BucketPolicy` with an `s3:GetObject` statement
scoped to `arn:aws:s3:::hello-api-assetsbucket-…/*`.

## Quiz prep

- What's the recommended way to grant an L2 resource access to
  another L2? (`grantX(other)`)
- Does `lambda.Function` create its own role? (yes)
- What managed policy does it auto-attach? (`AWSLambdaBasicExecutionRole`)

## Further reading

- [Grant methods in CDK](https://docs.aws.amazon.com/cdk/v2/guide/permissions.html)
- Next up: **L15 — End-to-end stack**
