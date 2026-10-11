# hello-cdk — minimal CDK v2 stack

> The simplest possible useful AWS CDK v2 stack: 1 S3 bucket + 1
> `CfnOutput`. Built as the working artifact for **Section 2 — App,
> Stack, Construct (L05–L10)** of the AWS CDK v2 Crash Course.

## What it does

Provisions a private, versioned, encrypted S3 bucket and exports the
bucket name as a CloudFormation output.

## Run it

```bash
# from this directory
npm install
npm test                  # run the Jest assertions (no AWS account needed)
npx cdk synth              # produce cdk.out/HelloCdkStack.template.json
npx cdk deploy             # actually create the bucket (requires AWS creds)
npx cdk destroy            # tear it down
```

## Files

| File | Purpose |
|---|---|
| `bin/hello-cdk.ts` | CDK App entry point — instantiates the stack |
| `lib/hello-cdk-stack.ts` | The stack — bucket + output |
| `test/hello-cdk.test.ts` | Jest tests using `Template.fromStack` |
| `cdk.json` | Tells the CDK CLI how to run the app (`ts-node bin/hello-cdk.ts`) |
| `tsconfig.json` | TypeScript compiler options |
| `package.json` | npm deps (`aws-cdk-lib`, `constructs`, `jest`, `ts-jest`, ...) |
