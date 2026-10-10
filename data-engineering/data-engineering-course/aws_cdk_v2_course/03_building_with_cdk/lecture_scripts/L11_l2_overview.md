---
lecture: L11
title: "L2 constructs for Lambda, API Gateway, S3, IAM"
duration: "12:00"
section: 3
prereqs: ["L10"]
---

# L11 — L2 Constructs for Lambda, API Gateway, S3, IAM

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 3 — Building with CDK
> **Duration:** 12:00

## Prereqs

L10 — `cdk deploy` + `cdk destroy` + outputs

## Key terms

- **`aws-cdk-lib/aws-lambda`** — L2 Lambda constructs
  (`lambda.Function`, `lambda.Code`, `lambda.Runtime`).
- **`aws-cdk-lib/aws-apigateway`** — L2 API Gateway constructs
  (`apigateway.RestApi`, `apigateway.LambdaRestApi`).
- **`aws-cdk-lib/aws-s3`** — L2 S3 constructs (`s3.Bucket`,
  `s3deploy.BucketDeployment`).
- **`aws-cdk-lib/aws-iam`** — L2 IAM constructs (`iam.Role`,
  `iam.Policy`, `iam.Grant`).

## Lecture

The four modules we use in this section all live under
`aws-cdk-lib/`:

```ts
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigw  from 'aws-cdk-lib/aws-apigateway';
import * as s3     from 'aws-cdk-lib/aws-s3';
import * as iam    from 'aws-cdk-lib/aws-iam';
```

The L2 pattern for each is the same — give it a `scope`, an `id`,
and a props object:

```ts
// S3
new s3.Bucket(this, 'Bucket', { versioned: true });

// Lambda
new lambda.Function(this, 'Fn', {
  runtime: lambda.Runtime.NODEJS_20_X,
  handler: 'index.handler',
  code: lambda.Code.fromInline('...'),
});

// API Gateway
new apigw.RestApi(this, 'Api', {
  restApiName: 'orders',
  description: '...',
});
// or the L3 pattern (proxy integration):
new apigw.LambdaRestApi(this, 'Api', { handler: fn });

// IAM role
new iam.Role(this, 'Role', {
  assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
});
```

**L2 vs L3 trade-offs:**

- `apigw.RestApi` gives you full control but you wire up resources,
  methods, integrations, deployments, and stages by hand.
- `apigw.LambdaRestApi` is L3 — it gives you a `/{proxy+}` resource
  with an `ANY` method and an `AWS_PROXY` integration in one line.
- For 80% of CRUD APIs, `LambdaRestApi` is the right answer. For
  complex APIs with custom integrations, fall back to `RestApi`.

The L2 IAM construct deserves a special callout: **most L2
constructs auto-create roles for you.** `lambda.Function` creates a
role, attaches the basic `AWSLambdaBasicExecutionRole` managed
policy, and exposes `fn.grantInvoke(other)` so you can extend it
without writing JSON policy. We'll see that in L14.

## Hands-on

Open `code/lambda-api/lib/lambda-api-stack.ts` and identify each
`new X(...)` call. Confirm you can name the L2 module it came from.

```bash
cd 03_building_with_cdk/code/lambda-api
grep -E "new (s3|lambda|apigw|iam)\." lib/lambda-api-stack.ts
```

## Quiz prep

- Which L2 module holds the `Function` construct? (`aws-cdk-lib/aws-lambda`)
- What's the difference between `RestApi` and `LambdaRestApi`?
  (LambdaRestApi is L3, sets up proxy integration for you)

## Further reading

- [Lambda L2 reference](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_lambda-readme.html)
- Next up: **L12 — Lambda functions with `Code.fromAsset`**
