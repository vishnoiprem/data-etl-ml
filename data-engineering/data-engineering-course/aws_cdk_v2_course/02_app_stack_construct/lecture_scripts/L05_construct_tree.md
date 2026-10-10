---
lecture: L05
title: "The CDK construct tree — App → Stack → Construct"
duration: "11:00"
section: 2
prereqs: ["L04"]
---

# L05 — The CDK Construct Tree

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 2 — App, Stack, Construct
> **Duration:** 11:00

## Prereqs

L04 — Installing and bootstrapping CDK

## Key terms

- **Construct** — a class that extends `constructs.Construct`. The
  smallest unit of CDK code.
- **App** — the root of the tree (`cdk.App`). Holds Stacks.
- **Stack** — a CloudFormation stack, the unit of deployment.
  Contains Constructs.
- **Construct tree** — the parent → child ownership graph that CDK
  synthesizes into a CloudFormation template.

## Lecture

Every CDK app is a **tree of constructs**. There are three layers:

```text
App (cdk.App)
├── Stack (cdk.Stack) ──────── a CloudFormation stack
│   ├── Construct (s3.Bucket) ── an AWS resource (L2)
│   ├── Construct (lambda.Function)
│   └── Construct (apigw.RestApi)
└── Stack (cdk.Stack)
    └── Construct (…)
```

The **App** is the root — created in `bin/app.ts`. It is **not**
deployed; it's just a logical container. Each **Stack** under the app
becomes one CloudFormation stack. Each **Construct** under a stack
becomes one or more resources inside that stack.

```ts
// bin/hello-cdk.ts
import * as cdk from 'aws-cdk-lib';
import { HelloCdkStack } from '../lib/hello-cdk-stack';

const app = new cdk.App();
new HelloCdkStack(app, 'HelloCdkStack');   // 1 stack
// ...could add another stack here in a multi-stack app
```

```ts
// lib/hello-cdk-stack.ts
import { Construct } from 'constructs';
import * as s3 from 'aws-cdk-lib/aws-s3';

export class HelloCdkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    new s3.Bucket(this, 'HelloBucket');    // 1 construct under the stack
  }
}
```

**Why this matters:** CDK uses the tree to compute logical IDs. The
construct path (`HelloCdkStack/HelloBucket/Resource`) is hashed to
produce a stable CloudFormation logical ID (`HelloCdkStackHelloBucket
D7BD8086`). If you reorder the tree, the IDs change, and CDK will
**replace** (delete + recreate) the resource.

## Hands-on

Nothing yet — read the `hello-cdk` stack file
(`02_app_stack_construct/code/hello-cdk/lib/hello-cdk-stack.ts`) and
trace the tree on a sheet of paper.

## Quiz prep

- What is the parent of a `cdk.Stack`? (the `cdk.App`)
- Why do construct IDs matter? (they become CloudFormation logical IDs)

## Further reading

- Diagram: `../../diagrams/cdk_construct_tree.mmd`
- Next up: **L06 — L1 / L2 / L3 constructs**
