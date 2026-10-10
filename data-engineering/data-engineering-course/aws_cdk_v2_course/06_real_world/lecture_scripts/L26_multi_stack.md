---
lecture: L26
title: "Multi-stack applications — shared VPC, network + app stacks"
duration: "12:00"
section: 6
prereqs: ["L25"]
---

# L26 — Multi-Stack Applications

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 6 — Real-World Patterns
> **Duration:** 12:00

## Prereqs

L25 — CI/CD

## Key terms

- **Multi-stack** — one CDK App that produces 2+ CloudFormation
  stacks.
- **Network stack** — VPC, subnets, IGW, NAT. Changes rarely.
- **App stack** — compute, data, API. Changes often.
- **Stage** — a class that wraps the per-env stack set
  (`DevStage`, `ProdStage`).

## Lecture

The single-stack pattern works until your network team and your app
team want to deploy on different cadences. Then you split:

```ts
// bin/app.ts
import { App } from 'aws-cdk-lib';
import { NetworkStack } from '../lib/network-stack';
import { AppStack }     from '../lib/app-stack';

const app = new App();

const dev = new NetworkStack(app, 'NetworkStack-dev', { env: DEV });
new AppStack(app, 'AppStack-dev', { env: DEV, vpc: dev.vpc });

const prod = new NetworkStack(app, 'NetworkStack-prod', { env: PROD });
new AppStack(app, 'AppStack-prod', { env: PROD, vpc: prod.vpc });
```

The **consumer** takes a `vpc: ec2.IVpc` (the *interface*), not a
`vpc: ec2.Vpc` (the *class*). The interface decouples the consumer
from how the VPC was built — you could swap in a different VPC L2
without breaking the consumer.

```ts
import * as ec2 from 'aws-cdk-lib/aws-ec2';

export class AppStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: AppStackProps) {
    super(scope, id, props);
    new lambda.Function(this, 'Fn', {
      vpc: props.vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
    });
  }
}
```

The **Stage** pattern is the next step up — a class that bundles
multiple stacks for a single environment:

```ts
export class ServiceStage extends cdk.Stage {
  constructor(scope: Construct, id: string, props: cdk.StageProps) {
    super(scope, id, props);
    const net = new NetworkStack(this, 'Network', props);
    new AppStack(this, 'App', { vpc: net.vpc });
  }
}

// bin/app.ts
new ServiceStage(app, 'Dev',  { env: DEV });
new ServiceStage(app, 'Prod', { env: PROD });
```

Now `cdk deploy --all` deploys 4 stacks in dependency order.

## Hands-on

The assignment in `../assignments/assignment_1_multi_stack.md` walks
you through building this end to end. There's no code in `06_real_world/code/`
yet — the assignment is the working artifact.

## Quiz prep

- What's the difference between a `Stack` and a `Stage`? (Stage
  bundles multiple stacks; Stack is one CFN stack)
- Why pass `ec2.IVpc` and not `ec2.Vpc` to consumers? (decouples
  the consumer from the VPC L2)

## Further reading

- Diagram: `../../diagrams/multi_stack_pattern.mmd`
- Assignment: `../../assignments/assignment_1_multi_stack.md`
- Next up: **L27 — Cross-region stacks**
