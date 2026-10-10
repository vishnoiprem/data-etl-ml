---
lecture: L12
title: "Building a Lambda function with lambda.Code.fromAsset"
duration: "12:00"
section: 3
prereqs: ["L11"]
---

# L12 — Building a Lambda Function

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 3 — Building with CDK
> **Duration:** 12:00

## Prereqs

L11 — L2 constructs overview

## Key terms

- **`lambda.Runtime`** — the enum of supported runtimes
  (`NODEJS_20_X`, `PYTHON_3_12`, `JAVA_21`, ...).
- **`lambda.Code.fromInline(code)`** — embed code as a string.
  Useful for demos; never use in production.
- **`lambda.Code.fromAsset(path)`** — bundle a local directory as
  the deployment package. CDK zips it for you.
- **`lambda.Code.fromEcrImage(repo)`** — pull a Docker image from
  ECR. Use for container-image Lambdas.

## Lecture

`lambda.Code` has three flavors you'll use in practice:

```ts
// 1. Inline — only for tiny demos. Hard to read past 20 lines.
lambda.Code.fromInline(`
  exports.handler = async () => ({ statusCode: 200, body: 'ok' });
`);

// 2. From a local directory — the production default.
lambda.Code.fromAsset(path.join(__dirname, '../lambda'));

// 3. From an ECR image — for container-image Lambdas.
lambda.Code.fromEcrImage(repo, { tag: 'v1.2.3' });
```

`fromAsset` is the workhorse. CDK bundles the directory, uploads it
to the bootstrap S3 bucket, and configures the Lambda to pull from
there. The bundling step also supports **esbuild** for transpilation:

```ts
lambda.Code.fromAsset(path, {
  bundling: {
    image: lambda.Runtime.NODEJS_20_X.bundlingImage,
    command: ['bash', '-c', 'npm install && npm run build'],
  },
});
```

```ts
new lambda.Function(this, 'Fn', {
  runtime: lambda.Runtime.NODEJS_20_X,
  handler: 'index.handler',          // file.function
  code: lambda.Code.fromAsset(path.join(__dirname, '../lambda')),
  memorySize: 256,                   // MB
  timeout: cdk.Duration.seconds(10),
  environment: {
    TABLE_NAME: table.tableName,
  },
});
```

**Conventions:**

- Handler is always `file.function` — the file without `.js`, then
  the exported function.
- For Node, your `index.js` exports `handler` as the function name.
- For Python, your `index.py` defines `def handler(event, context):`.

## Hands-on

The `lambda-api/` project uses `Code.fromInline` to keep it
self-contained. Replace it with `fromAsset` and a real
`lambda/index.js` file to see the difference:

```bash
cd 03_building_with_cdk/code/lambda-api
mkdir lambda
cat > lambda/index.js <<'EOF'
exports.handler = async () => ({ statusCode: 200, body: 'ok' });
EOF
```

Then change the stack to:

```ts
code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda')),
```

`npm test` should still pass.

## Quiz prep

- Which `Code` flavor do you use in production? (`fromAsset`)
- What does `cdk synth` do with `fromAsset`? (uploads to S3, references from Lambda)
- What's the format of `handler`? (`file.function`)

## Further reading

- [Lambda Code reference](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_lambda.Code.html)
- Next up: **L13 — API Gateway with `LambdaRestApi`**
