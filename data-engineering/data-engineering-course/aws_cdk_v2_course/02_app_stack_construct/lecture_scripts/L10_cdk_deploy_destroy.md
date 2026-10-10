---
lecture: L10
title: "cdk deploy + cdk destroy + stack outputs"
duration: "10:00"
section: 2
prereqs: ["L09"]
---

# L10 — `cdk deploy` + `cdk destroy` + Stack Outputs

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 2 — App, Stack, Construct
> **Duration:** 10:00

## Prereqs

L09 — Escape hatches

## Key terms

- **`cdk deploy`** — synthesize, upload assets, and submit a
  CloudFormation change set.
- **`--hotswap`** — try to apply changes by mutating existing
  resources instead of replacing them (faster but riskier).
- **`cdk destroy`** — delete the stack and all its resources.
- **`CfnOutput`** — a value exposed in the CloudFormation console
  (`Outputs` tab) and via `cdk output`.

## Lecture

`cdk deploy` is the command that actually puts your code into AWS.
It runs `synth`, uploads assets (Lambda zips, Docker images, file
bundles) to S3, generates a change set, shows you the diff, asks for
approval (unless you pass `--require-approval never`), then executes
the change set.

```bash
cd 02_app_stack_construct/code/hello-cdk

npx cdk deploy                             # synth + upload + deploy
npx cdk deploy --require-approval never    # auto-approve (CI only!)

# read outputs after deploy:
npx cdk output HelloCdkStack -c key=HelloBucket

# or in code:
BUCKET=$(npx cdk output HelloCdkStack --json | jq -r '.HelloBucket')
echo "$BUCKET"
```

`CfnOutput` is how you expose values from a stack. Each output is
listed in the CloudFormation console and saved so other tooling can
discover them later.

```ts
new cdk.CfnOutput(this, 'BucketName', {
  value: this.bucket.bucketName,
  exportName: 'HelloBucketName',  // makes it importable in another stack
});
```

`cdk destroy` is the reverse:

```bash
npx cdk destroy               # confirm "y"
npx cdk destroy --force        # skip confirmation
```

**Caution:** `cdk destroy` deletes resources with `removalPolicy:
RETAIN` (the default) only if you explicitly set it to `DESTROY`.
Most resources use `RETAIN` by default (good — your data survives).

## Hands-on

If you have an AWS account configured:

```bash
cd 02_app_stack_construct/code/hello-cdk
npx cdk deploy
aws s3 ls | grep hellocdk         # confirm the bucket exists
npx cdk output HelloCdkStack -c key=HelloBucket
npx cdk destroy                   # tear it down
```

If you **don't** have an AWS account, you can still finish the
course — sections 1–4 are testable offline. Section 6's multi-stack
assignment assumes an account.

## Quiz prep

- What's the difference between `cdk synth` and `cdk deploy`?
  (synth = emit template; deploy = also push to AWS)
- What does `cdk destroy` do? (deletes the stack + resources with
  DESTROY removal policy)
- What's the purpose of `CfnOutput`? (expose a value to console +
  cross-stack import)

## Further reading

- [`cdk deploy` reference](https://docs.aws.amazon.com/cdk/v2/guide/cli.html#cli-deploy)
- Next up: **Section 3 — Building with CDK (L11+)**
