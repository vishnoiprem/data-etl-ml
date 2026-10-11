# lambda-api — Lambda + API Gateway + S3 + IAM in CDK v2

> Working artifact for **Section 3 — Building with CDK (L11–L15)** of
> the AWS CDK v2 Crash Course.

## What it does

Provisions a serverless CRUD-ready stack:

- **S3 bucket** — holds the function's code asset
- **Lambda function** — Node 20, inline hello-world handler
- **IAM role** — auto-created by the L2 `lambda.Function` construct;
  least-privilege (only `s3:GetObject` on the assets bucket)
- **API Gateway REST API** — proxy integration to the Lambda, deployed
  to a `prod` stage with permissive CORS

## Run it

```bash
npm install
npm test                  # run the Jest assertions
npx cdk synth              # produce cdk.out/LambdaApiStack.template.json
npx cdk deploy             # create the resources (requires AWS creds)
curl $(npx cdk output -c stage=prod LambdaApiStack.ApiUrl)   # smoke test
npx cdk destroy
```

## Files

| File | Purpose |
|---|---|
| `bin/lambda-api.ts` | CDK App entry point |
| `lib/lambda-api-stack.ts` | The stack — bucket, Lambda, IAM, API GW |
| `test/lambda-api.test.ts` | Jest tests using `Template.fromStack` |
| `cdk.json` | Tells the CDK CLI how to run the app |
| `tsconfig.json` | TypeScript compiler options |
| `package.json` | npm deps (`aws-cdk-lib`, `constructs`, `jest`, ...) |
