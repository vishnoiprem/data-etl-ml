---
title: L74 — AWS CDK — Create S3 bucket using AWS CDK v2
author: Prem Vishnoi <pvishnoi@avilx.com>
section: 12
duration: 11:22
---

# L74 — AWS CDK — Create S3 bucket using AWS CDK v2

> **Section:** 12 — AWS CDK v2
> **Duration target:** 11:22
> **Author:** Prem Vishnoi <pvishnoi@avilx.com>

## Prereqs

- L71, L72, L73 — CDK toolchain installed and bootstrapped; target
  architecture understood.
- Section 4 — S3 with Lambda (boto3 patterns) for context.

## Key terms

- **`s3.Bucket`** — the L2 construct that creates a CloudFormation
  `AWS::S3::Bucket` resource. The L2 is *curated* — its constructor
  arguments map to AWS best practices.
- **`BucketEncryption.S3_MANAGED`** — server-side encryption with
  S3-managed keys (SSE-S3). Free, no KMS permissions, and meets almost
  every compliance baseline.
- **`versioned: true`** — turns on S3 object versioning. With versioning
  on, "delete" creates a delete marker and "overwrite" preserves the
  prior version.
- **`blockPublicAccess`** — L2 defaults `BlockPublicAccess.BLOCK_ALL`.
  You have to opt-in to make a bucket public. (We do not.)
- **`autoDeleteObjects`** — when the stack is destroyed, CDK empties the
  bucket automatically. Convenient for dev; do not enable in production
  with real data.
- **`removalPolicy`** — what CDK does to the resource when the stack is
  deleted. `DESTROY` deletes the bucket; `RETAIN` keeps it. We use
  `DESTROY` for the dev stack and pair it with `autoDeleteObjects`.

## Lecture

We start building the stack by adding the **S3 bucket**. This is the
right ordering because every later resource (IAM role, Lambda functions)
needs to reference the bucket by ARN, and CDK resolves those references
at synth time. The bucket itself only needs the stack scope.

### The full S3 construct

Open `code/lib/serverless-stack.ts`. The first thing we add is the
bucket. Here is the full version of the bucket portion:

```ts
import { Stack, StackProps, RemovalPolicy, Duration } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as s3 from 'aws-cdk-lib/aws-s3';
// (more imports added in L75, L76, L77)

export class ServerlessStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    // ------------------------------------------------------------
    // S3 bucket — versioned + encrypted, public access blocked
    // ------------------------------------------------------------
    const objectsBucket = new s3.Bucket(this, 'ObjectsBucket', {
      // A globally-unique name keeps the resource easy to find in the console.
      // CDK falls back to a CDK-generated name if you omit this.
      bucketName: `serverless-objects-${this.account}-${this.region}`,

      // Versioning keeps every prior copy of an object. Required for the
      // "read old version" patterns in section 8.
      versioned: true,

      // SSE-S3 (AES-256) — no KMS permissions, no extra cost.
      encryption: s3.BucketEncryption.S3_MANAGED,

      // Defense in depth: refuse any public ACL or public policy.
      // This is the L2 default, but we set it explicitly for clarity.
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,

      // Enforce TLS on every request — no plain-HTTP GETs allowed.
      enforceSSL: true,

      // When the stack is destroyed, also delete every object.
      // Convenient in dev; dangerous in prod with real data.
      autoDeleteObjects: true,

      // Delete the bucket itself on stack destroy.
      removalPolicy: RemovalPolicy.DESTROY,
    });

    // Expose the bucket name as a CloudFormation output so we can
    // find it from the CLI without logging into the console.
    new CfnOutput(this, 'ObjectsBucketName', {
      value: objectsBucket.bucketName,
      description: 'Name of the S3 bucket that holds objects',
      exportName: 'ServerlessObjectsBucketName',
    });
  }
}
```

### What each option does

#### `bucketName`

CDK will auto-generate a unique name if you omit this. We supply an
explicit name so the bucket is easy to find in the console and so
the name encodes the account and region (helpful when you have multiple
workspaces deploying to the same account).

If you do supply a name, it must be globally unique across **all** AWS
accounts. Using `${this.account}` and `${this.region}` guarantees that.

#### `versioned: true`

Equivalent to setting `VersioningConfiguration.Status: Enabled` on the
underlying `AWS::S3::Bucket`. Every `PUT` of an existing key now stores
a new version; `DELETE` creates a delete marker. The bucket's storage
cost will be higher, so version only what you need.

#### `encryption: s3.BucketEncryption.S3_MANAGED`

There are three L2 options:

| Enum value | Underlying | Cost | Use when |
|---|---|---|---|
| `S3_MANAGED` (SSE-S3) | AES-256 with S3-managed keys | Free | Default. Meets most compliance baselines. |
| `KMS_MANAGED` (SSE-KMS) | AES-256 with AWS-managed KMS key | KMS API charges | You need to audit key usage in CloudTrail. |
| `KMS` (SSE-KMS with CMK) | Customer-managed KMS key | KMS API + CMK charges | You need to grant per-key access or rotate. |

For a dev / learning stack, `S3_MANAGED` is correct. If your team needs
KMS-key-rotation audit trails, swap in `KMS_MANAGED` or `KMS` later.

#### `blockPublicAccess`

The L2 default is already `BLOCK_ALL`, but we set it explicitly to make
the intent obvious in code review. There is no good reason to make a
bucket public when you have API Gateway in front of it.

#### `enforceSSL: true`

Adds an explicit `Deny` for any request where `aws:SecureTransport = false`.
Equivalent to the bucket policy you would write by hand. Costs nothing
and blocks a class of accidental plaintext leaks.

#### `autoDeleteObjects: true` + `removalPolicy: RemovalPolicy.DESTROY`

These two go together. `autoDeleteObjects` makes CDK add a custom
resource (a tiny Lambda) that empties the bucket before it is destroyed.
`removalPolicy: DESTROY` lets CDK delete the bucket at all. If you leave
`removalPolicy` as `RETAIN` (the default for stateful resources in
production stacks), `cdk destroy` keeps the bucket around and warns you
about it.

> **Production tip:** in real stacks, leave `removalPolicy: RETAIN` and
> do **not** use `autoDeleteObjects`. You do not want a one-line config
> change in a PR to nuke a bucket of customer data.

### Outputs

We add a `CfnOutput` so the bucket name is queryable from the CLI:

```bash
aws cloudformation describe-stacks \
  --stack-name ServerlessStack \
  --query "Stacks[0].Outputs[?OutputKey=='ObjectsBucketName'].OutputValue" \
  --output text
```

This avoids clicking through the console when you need the name for the
next lecture.

### Synthesize to verify

```bash
cd code
npx cdk synth ServerlessStack | grep -A 5 "AWS::S3::Bucket"
```

You should see a `Resources.ObjectsBucket...` block in the synthesized
CloudFormation template. The presence of this block (and only this
block — we have not added the role or functions yet) confirms the
construct is wired up correctly.

## Hands-on

1. Replace the body of `lib/serverless-stack.ts` with the snippet above.
2. Run `npm install` if you have not already.
3. Run `npx cdk synth` and confirm a single `AWS::S3::Bucket` resource
   is in the output.
4. **Do not `cdk deploy` yet** — the bucket is not wired to anything,
   so a deploy right now would just create an empty bucket. We will
   deploy the whole stack at the end of L77.

## Quiz prep

- What is the L2 construct that creates an S3 bucket in CDK?
- What are the three `BucketEncryption` options and which one is free?
- Why do we set `blockPublicAccess: BLOCK_ALL` even though it is the
  default?
- What does `autoDeleteObjects: true` add to the template, and what is
  the gotcha with using it in production?

## Further reading

- [aws-cdk-lib `s3.Bucket` API reference](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_s3.Bucket.html)
- [aws-cdk-lib `BucketEncryption` enum](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_s3.BucketEncryption.html)
- [S3 — Using versioning](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html)
- [S3 — Blocking public access](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html)
