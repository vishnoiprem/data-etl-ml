---
title: L76 — AWS CDK — Create Lambda using AWS CDK v2
author: Prem Vishnoi <pvishnoi@avilx.com>
section: 12
duration: 8:57
---

# L76 — AWS CDK — Create Lambda using AWS CDK v2

> **Section:** 12 — AWS CDK v2
> **Duration target:** 8:57
> **Author:** Prem Vishnoi <pvishnoi@avilx.com>

## Prereqs

- L74 — `objectsBucket` exists in `serverless-stack.ts`.
- L75 — `lambdaExecutionRole` exists with the right trust + permissions.
- Familiarity with Node.js 20 Lambda handlers and the AWS SDK v3
  `@aws-sdk/client-s3` package.

## Key terms

- **`lambda.Function`** — L2 construct that produces the function, the
  IAM role (if you do not supply one), the log group, and the
  CloudFormation output.
- **`runtime: lambda.Runtime.NODEJS_20_X`** — pins the function to the
  Node 20 managed runtime.
- **`code: lambda.Code.fromAsset('lambda')`** — tells CDK to package
  the local `lambda/` directory as a zip and upload it to the
  bootstrapped S3 bucket at synth time.
- **`handler: 'get-object.handler'`** — the file name + exported
  function name (no `.js` extension) that Lambda invokes.
- **`environment`** — map of env vars baked into the function. We pass
  the bucket name so the handlers do not need to compile-time-import the
  stack file.
- **`memorySize` and `timeout`** — 256 MB / 30 s. Matches the section 8
  CFN version.

## Lecture

In L75 we built the role. Now we wire it into **two Lambda functions**
backed by handlers we write in TypeScript under `code/lambda/`. The
constructs themselves are short; the interesting part is what CDK does
behind the scenes when you call `lambda.Code.fromAsset`.

### The two handler files

`code/lambda/get-object.ts`:

```ts
import { S3Client, GetObjectCommand, NoSuchKey } from '@aws-sdk/client-s3';
import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';

// Reuse the client across invocations — Lambda freezes the module
// graph after the first call, so this client is reused for the
// lifetime of the execution environment.
const s3 = new S3Client({});
const BUCKET = process.env.BUCKET_NAME ?? '';

export const handler = async (
  event: APIGatewayProxyEvent,
): Promise<APIGatewayProxyResult> => {
  const key = event.pathParameters?.key;
  if (!key) {
    return {
      statusCode: 400,
      body: JSON.stringify({ message: 'Missing path parameter: key' }),
    };
  }

  try {
    const out = await s3.send(
      new GetObjectCommand({ Bucket: BUCKET, Key: key }),
    );
    const body = await out.Body!.transformToString('utf-8');
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body,
    };
  } catch (err) {
    if (err instanceof NoSuchKey || (err as { name?: string }).name === 'NoSuchKey') {
      return {
        statusCode: 404,
        body: JSON.stringify({ message: `Object ${key} not found` }),
      };
    }
    console.error('get-object error', err);
    return {
      statusCode: 500,
      body: JSON.stringify({ message: 'Internal server error' }),
    };
  }
};
```

`code/lambda/put-object.ts`:

```ts
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';
import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';

const s3 = new S3Client({});
const BUCKET = process.env.BUCKET_NAME ?? '';

export const handler = async (
  event: APIGatewayProxyEvent,
): Promise<APIGatewayProxyResult> => {
  const key = event.pathParameters?.key;
  if (!key || event.body === null || event.body === undefined) {
    return {
      statusCode: 400,
      body: JSON.stringify({ message: 'Missing path parameter: key or body' }),
    };
  }

  try {
    await s3.send(
      new PutObjectCommand({
        Bucket: BUCKET,
        Key: key,
        Body: event.body,
        ContentType: event.headers['content-type'] ?? 'application/octet-stream',
      }),
    );
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key, bucket: BUCKET, message: 'Stored' }),
    };
  } catch (err) {
    console.error('put-object error', err);
    return {
      statusCode: 500,
      body: JSON.stringify({ message: 'Internal server error' }),
    };
  }
};
```

Two important things to notice:

1. **No `any` types.** Both handlers are typed against
   `APIGatewayProxyEvent` / `APIGatewayProxyResult` from the
   `aws-lambda` package. The `(err as { name?: string })` cast in
   `get-object.ts` is needed because S3 SDK v3's error union does not
   always narrow to `NoSuchKey` from a plain `try/catch`.
2. **The S3 client is constructed once, outside the handler.** This
   is the [official AWS Lambda best practice](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html):
   reusing clients avoids re-creating TLS connections on every
   invocation.

### The two Lambda constructs

Append the following to `lib/serverless-stack.ts`:

```ts
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { join } from 'path';

// ------------------------------------------------------------
// Lambda functions — get-object and put-object
// ------------------------------------------------------------
const commonLambdaProps = {
  runtime: lambda.Runtime.NODEJS_20_X,
  handler: 'index.handler',          // overridden per-function below
  role: lambdaExecutionRole,
  memorySize: 256,
  timeout: Duration.seconds(30),
  environment: {
    BUCKET_NAME: objectsBucket.bucketName,
  },
  // Bundle from the local `lambda/` directory. esbuild is the default
  // bundler in CDK v2 and produces a tiny zip with only the deps we
  // actually import.
  code: lambda.Code.fromAsset(join(__dirname, '..', 'lambda')),
  logRetention: logs.RetentionDays.ONE_WEEK,
};

const getObjectFn = new lambda.Function(this, 'GetObjectFn', {
  ...commonLambdaProps,
  handler: 'get-object.handler',
  description: 'GET /objects/{key} — reads an S3 object and returns its body',
});

const putObjectFn = new lambda.Function(this, 'PutObjectFn', {
  ...commonLambdaProps,
  handler: 'put-object.handler',
  description: 'PUT /objects/{key} — stores the request body as an S3 object',
});
```

### What CDK does at synth time

When you call `lambda.Code.fromAsset('lambda')`, CDK:

1. Spawns `esbuild` to bundle each entry point.
2. Produces a single zip per entry point (or per construct, depending
   on the configuration).
3. Uploads the zip to the bootstrapped assets bucket.
4. Replaces the `code` value in the synthesized CFN template with an
   `S3Bucket` + `S3Key` reference.

You will see the upload happen in your terminal the first time you run
`cdk synth` after adding a new function. Subsequent runs reuse the
already-uploaded asset.

### Why we use `fromAsset` instead of inline code

CDK also supports `Code.fromInline('exports.handler = ...')`, which is
the same approach section 13 takes with `ZipFile` in the CloudFormation
template. We avoid it because:

- Inline code is limited to **4 KB** by CloudFormation. Our handlers
  are well under that, but real handlers usually are not.
- Inline code cannot import npm dependencies. We use
  `@aws-sdk/client-s3` and `aws-lambda`, so we need a real bundle.

### Synthesize to verify

```bash
npx cdk synth ServerlessStack | grep -E "(AWS::Lambda::Function|GetObject|PutObject)"
```

You should see two `AWS::Lambda::Function` resources, each with a
`Code.S3Bucket` and `Code.S3Key`, a `Role` pointing at the
`LambdaExecutionRole` ARN, and the environment variable `BUCKET_NAME`
populated.

## Hands-on

1. Create `code/lambda/get-object.ts` and `code/lambda/put-object.ts`
   with the contents above.
2. Add the two `lambda.Function` constructs to `serverless-stack.ts`.
3. `npm install` to pull `aws-lambda` types and `@aws-sdk/client-s3`
   (CDK v2 does not bundle these by default).
4. Run `npx cdk synth` and confirm two `AWS::Lambda::Function`
   resources appear.
5. `npm run build` to confirm the TypeScript in `serverless-stack.ts`
   still compiles.
6. Do **not** `cdk deploy` yet — the API Gateway wiring is in L77.

## Quiz prep

- What is the difference between `lambda.Code.fromAsset` and
  `lambda.Code.fromInline`?
- Why do we construct the `S3Client` *outside* the handler function?
- What does CDK do behind the scenes when you call `fromAsset`?
- Which `lambda.Runtime` value pins a function to Node 20?
- What is the maximum size of inline code in a CloudFormation
  `AWS::Lambda::Function`?

## Further reading

- [aws-cdk-lib `lambda.Function` API reference](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_lambda.Function.html)
- [AWS Lambda — Node.js best practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [@aws-sdk/client-s3 README](https://github.com/aws/aws-sdk-js-v3/tree/main/clients/client-s3)
- [esbuild bundler in CDK](https://docs.aws.amazon.com/cdk/v2/guide/assets.html)
