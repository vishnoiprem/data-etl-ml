---
lecture: L27
title: "Cross-region stacks — DR, global APIs, regional resources"
duration: "12:00"
section: 6
prereqs: ["L26"]
---

# L27 — Cross-Region Stacks

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 6 — Real-World Patterns
> **Duration:** 12:00

## Prereqs

L26 — Multi-stack

## Key terms

- **Global services** — IAM, CloudFront, Route 53, WAF. Always
  deployed in `us-east-1` (the API endpoint is global; the control
  plane is in us-east-1).
- **Regional services** — EC2, Lambda, DynamoDB, S3. Deployed in
  the region of your choice.
- **Disaster recovery (DR)** — the plan for what happens when a
  region goes down. CDK lets you mirror a stack into a second
  region.
- **`Stack.of(this).region`** — the region the current stack is
  deployed in (set by the `env` in `bin/app.ts`).

## Lecture

The first rule of cross-region CDK: **one stack = one region.** If
you need resources in two regions, you need two stacks.

```ts
// global IAM role in us-east-1
const globalStack = new GlobalStack(app, 'Global', {
  env: { region: 'us-east-1' },
});

// regional API in eu-west-1
const regionalStack = new RegionalStack(app, 'Regional', {
  env: { region: 'eu-west-1' },
});
```

Cross-region references are explicit. **You cannot use
`someBucket.bucketArn` directly across regions** — ARN is
region-specific. Instead, you pass values via context or
`CfnOutput` + lookup:

```ts
// in us-east-1 stack
new cdk.CfnOutput(this, 'BucketArn', { value: bucket.bucketArn });

// in eu-west-1 stack — read it at synth time
const bucketArn = cdk.Fn.importValue('BucketArn-from-us-east-1');
// or, in dev, hardcode and pass via -c
```

**A clean pattern: one App per region, one stack per concern.**

```ts
// bin/app.ts
const env = { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION };
new NetworkStack(app, 'Network', { env });
new AppStack(app, 'App',     { env });
```

Set `CDK_DEFAULT_REGION` per pipeline run to deploy a different
region:

```bash
CDK_DEFAULT_REGION=us-east-1 cdk deploy --all
CDK_DEFAULT_REGION=eu-west-1 cdk deploy --all
```

For DR, the cleanest pattern is **two separate Apps** (one per
region) that you keep in sync via CI. Don't try to do cross-region
in a single App; the indirection is not worth it.

## Hands-on

Add a second stack to a project you have:

```ts
const primary = new AppStack(app, 'App-primary', { env: { region: 'us-east-1' } });
new AppStack(app, 'App-secondary', { env: { region: 'us-west-2' } });
```

`synth --all` should produce two templates.

## Quiz prep

- How many regions can a single CDK Stack deploy to? (one)
- Which AWS services are always global / always in us-east-1? (IAM,
  CloudFront, Route 53, WAF)
- What's the recommended pattern for DR with CDK?
  (two separate Apps, one per region, kept in sync via CI)

## Further reading

- [Passing data between stacks](https://docs.aws.amazon.com/cdk/v2/guide/resources.html#resource_stack)
- Next up: **L28 — `cdk.context`**
