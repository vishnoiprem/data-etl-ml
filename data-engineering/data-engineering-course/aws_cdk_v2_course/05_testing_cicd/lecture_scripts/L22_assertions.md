---
lecture: L22
title: "aws-cdk-lib/assertions — Template.fromStack"
duration: "12:00"
section: 5
prereqs: ["L21"]
---

# L22 — `aws-cdk-lib/assertions` — `Template.fromStack`

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 5 — Testing, Snapshots, Assertions, CI/CD
> **Duration:** 12:00

## Prereqs

L21 — Why test CDK stacks

## Key terms

- **`Template.fromStack(stack)`** — synthesize the stack and capture
  its CloudFormation template in memory.
- **`Template.fromStack(stack, { skipValidation: true })`** — skip
  the optional structural validation when synthesizing.
- **`resourceCountIs(type, n)`** — assert the count of a CFN type.
- **`hasResourceProperties(type, props)`** — assert a resource of
  that type has these properties (subset match).
- **`hasOutput(name, props)`** — assert an output exists.
- **`hasResource(type, props)`** — assert a resource exists with
  certain *attribute* properties (Type, DependsOn, etc).

## Lecture

`aws-cdk-lib/assertions` is the official testing library for CDK.
The first thing you do with it is `Template.fromStack`:

```ts
import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { HelloCdkStack } from '../lib/hello-cdk-stack';

const app = new cdk.App();
const stack = new HelloCdkStack(app, 'TestStack');
const template = Template.fromStack(stack);
```

The returned `Template` object exposes assertion methods. The most
common ones:

```ts
// Counts
template.resourceCountIs('AWS::S3::Bucket', 1);
template.resourceCountIs('AWS::IAM::Role', 0);   // not present

// Existence + property check (subset match)
template.hasResourceProperties('AWS::S3::Bucket', {
  VersioningConfiguration: { Status: 'Enabled' },
});

// Outputs
template.hasOutput('BucketName', { /* subset of {Value, ExportName, Description} */ });

// Direct inspection
const buckets = template.findResources('AWS::S3::Bucket');
// { 'MyBucket1234': { Type: '...', Properties: {...} } }
```

Three nuances:

1. **Property match is a *subset* match.** You assert the *parts you
   care about*; everything else is wildcard.
2. **Resource IDs are opaque.** You never reference a CFN logical ID
   directly; you use `hasResourceProperties(type, props)` and CDK
   figures out which resource to look at.
3. **`Template.fromStack` is synchronous.** It calls synth and parses
   the template in memory. No I/O.

## Hands-on

Open `02_app_stack_construct/code/hello-cdk/test/hello-cdk.test.ts`
and read the 5 tests. Run them:

```bash
cd 02_app_stack_construct/code/hello-cdk
npm test
```

## Quiz prep

- What does `Template.fromStack` return? (a `Template` object)
- Is `hasResourceProperties` an exact match or a subset match?
  (subset)
- Does `Template.fromStack` make AWS API calls? (no)

## Further reading

- [Assertions module](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.assertions-readme.html)
- Next up: **L23 — Snapshot tests**
