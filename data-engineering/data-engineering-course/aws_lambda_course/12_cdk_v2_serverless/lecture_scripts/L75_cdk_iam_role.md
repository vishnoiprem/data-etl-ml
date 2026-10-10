---
title: L75 — AWS CDK — Create IAM Role using AWS CDK v2
author: Prem Vishnoi <prem.vishnoi@example.com>
section: 12
duration: 6:56
---

# L75 — AWS CDK — Create IAM Role using AWS CDK v2

> **Section:** 12 — AWS CDK v2
> **Duration target:** 6:56
> **Author:** Prem Vishnoi <prem.vishnoi@example.com>

## Prereqs

- L74 — the S3 bucket is in `serverless-stack.ts` and the
  `objectsBucket` variable is in scope.
- Familiarity with the Lambda execution role from section 2 (L07).

## Key terms

- **`iam.Role`** — the L2 construct that creates an `AWS::IAM::Role`.
- **Trust policy** — the JSON document that says *which* principals
  (here: `lambda.amazonaws.com`) are allowed to assume the role.
- **Permissions (inline policy)** — what the role can do *after* it is
  assumed. We attach a least-privilege inline policy rather than a
  managed policy so the permissions are co-located with the role
  definition.
- **`PolicyStatement`** — a single `{ Effect, Action, Resource, Condition }`
  block. A role can carry many `PolicyStatement`s via `addStatements`.
- **Least privilege** — grant only the actions the workload needs
  (`s3:GetObject` and `s3:PutObject` on the specific bucket ARN). Do
  not use `s3:*` and do not use `Resource: '*'`.

## Lecture

In L74 we created the bucket. In this lecture we create the **IAM
execution role** that both Lambdas will assume. We use a single shared
role for both functions because they need the exact same set of
permissions (read + write on the same bucket) and there is no
operational reason to split it.

### The full role construct

Append this to `lib/serverless-stack.ts`, right after the bucket block:

```ts
import * as iam from 'aws-cdk-lib/aws-iam';
// (no other new imports — we already have Stack, Construct, etc.)

// ------------------------------------------------------------
// IAM role — assumed by both Lambdas
// ------------------------------------------------------------
const lambdaExecutionRole = new iam.Role(this, 'LambdaExecutionRole', {
  // Human-readable name in the IAM console.
  roleName: 'ServerlessStack-LambdaExecutionRole',

  // The service that is allowed to assume this role.
  // For Lambda, this is always `lambda.amazonaws.com`.
  assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),

  description: 'Execution role for the get-object and put-object Lambdas.',

  // Inline policy = least privilege, co-located with the role.
  inlinePolicies: {
    S3ObjectsAccess: new iam.PolicyDocument({
      statements: [
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          actions: ['s3:GetObject', 's3:PutObject'],
          // Scope to the bucket we just created. Never use '*' here.
          resources: [objectsBucket.arnForObjects('*')],
        }),
      ],
    }),
  },
});
```

> **Why `arnForObjects('*')`?** The S3 ARN for a bucket is
> `arn:aws:s3:::my-bucket`. The ARN for any object inside it is
> `arn:aws:s3:::my-bucket/*`. Calling `bucket.arnForObjects('*')` is
> the L2 way to compute the second one — it is the right pattern for
> "any object in this bucket" without resorting to string templates.

### Anatomy of the role

#### `assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com')`

The **trust policy**. Without this, nothing can assume the role, and
the Lambda service will refuse to invoke it. The L2 also auto-derives
the trust policy from the principal: when we pass this role to
`lambda.Function` in L76, CDK does not need to mutate the trust policy
again — it is already correct.

#### `inlinePolicies`

We use an **inline** policy (attached directly to the role) rather than
a managed policy for two reasons:

1. **Co-location.** The role and the permissions it grants live in the
   same file, so a code reviewer sees the full picture in one place.
2. **No orphaned managed policies.** If we delete the stack, the
   managed policy would stick around as an unmanaged resource.

The `inlinePolicies` key is a `{ policyName: PolicyDocument }` map. The
key is the name that will appear in the IAM console.

#### The `PolicyStatement`

```ts
new iam.PolicyStatement({
  effect: iam.Effect.ALLOW,
  actions: ['s3:GetObject', 's3:PutObject'],
  resources: [objectsBucket.arnForObjects('*')],
})
```

- `actions: ['s3:GetObject', 's3:PutObject']` — only the two actions we
  actually use. We **do not** add `s3:ListBucket`, `s3:DeleteObject`,
  or anything else.
- `resources: [objectsBucket.arnForObjects('*')]` — scoped to *this*
  bucket, on *every* key inside it. If we ever had two buckets in the
  same stack, the role would still not be able to touch the second
  one.

This is what "least privilege" looks like in code.

### Logs permissions

Lambda always writes to CloudWatch Logs. The role therefore also needs
permissions on its own log group and log streams. CDK handles this
**automatically** when you pass the role into `lambda.Function` *and*
`logRetention` is set, but in our stack we let CDK create the log
group with the default retention and it auto-grants
`logs:CreateLogGroup`, `logs:CreateLogStream`, and
`logs:PutLogEvents` to the role.

If you ever need to write the role yourself (e.g. you bring your own
log retention Lambda), the pattern is:

```ts
lambdaExecutionRole.addToPolicy(
  new iam.PolicyStatement({
    effect: iam.Effect.ALLOW,
    actions: [
      'logs:CreateLogGroup',
      'logs:CreateLogStream',
      'logs:PutLogEvents',
    ],
    resources: [
      `arn:aws:logs:${this.region}:${this.account}:log-group:/aws/lambda/*`,
    ],
  }),
);
```

For our stack, **do not add this manually**. CDK will add the
necessary permissions when we wire the role into `lambda.Function` in
L76.

### Synthesize to verify

```bash
npx cdk synth ServerlessStack | grep -A 10 "LambdaExecutionRole"
```

You should see the `AWS::IAM::Role` resource with:

- An `AssumeRolePolicyDocument` that allows `lambda.amazonaws.com`.
- An inline policy named `S3ObjectsAccess` with the two `s3:Get*` /
  `s3:Put*` actions and the bucket ARN.

If those three pieces are present, the role is correctly defined.

## Hands-on

1. Add the role block to `lib/serverless-stack.ts`.
2. Run `npx cdk synth` and verify the `AWS::IAM::Role` resource has
   exactly the two S3 actions and no more.
3. Do **not** `cdk deploy` yet — the role is unused until L76 wires it
   into a Lambda.

## Quiz prep

- What is the difference between a trust policy and a permissions
  policy on an IAM role?
- Why do we use `arnForObjects('*')` instead of `bucket.bucketArn` in
  the resource scope?
- Why do we prefer an inline policy here over a managed policy?
- Which service principal must be in the trust policy for a Lambda
  execution role?

## Further reading

- [aws-cdk-lib `iam.Role` API reference](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_iam.Role.html)
- [aws-cdk-lib `iam.PolicyDocument` and `PolicyStatement`](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_iam.PolicyDocument.html)
- [IAM — Lambda execution role](https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html)
- [IAM — Least privilege](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#grant-least-privilege)
