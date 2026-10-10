# Assignment 1 — Multi-Stack CDK Application

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 6 — Real-World Patterns
> **Time budget:** 4–6 hours
> **Deliverable:** a working `multi-stack-app/` TypeScript CDK project
> with 2 stacks, 1 VPC, and 1 Jest test asserting the cross-stack
> resources.

## Goal

Build a multi-stack CDK application that mirrors the pattern discussed
in L26. The app deploys **two stacks** that share a VPC:

1. **`NetworkStack`** — creates a `VPC` with 2 public subnets and 2
   private subnets, exports the VPC ID via `CfnOutput`.
2. **`AppStack`** — accepts a `VPC` via props, deploys a Lambda in a
   private subnet, and outputs the Lambda function name.

Both stacks are instantiated from the same `bin/app.ts` and run in a
single AWS account but in two different stages (`dev` and `prod`).

## Why this exercise

Single-stack apps are easy. Real production systems are **always**
multi-stack: networking changes rarely and must be reviewed slowly;
application stacks change often and must be reviewed quickly. The
standard CDK pattern is to split them.

## What to build

```
multi-stack-app/
├── bin/
│   └── app.ts                ← instantiates NetworkStack + AppStack
├── lib/
│   ├── network-stack.ts      ← VPC, subnets, IGW
│   └── app-stack.ts          ← Lambda in private subnet
├── package.json
├── tsconfig.json
├── cdk.json
└── test/
    └── multi-stack.test.ts   ← Jest: Template.fromStack on each
```

## Acceptance criteria

- [ ] `NetworkStack` produces a `VPC`, 2 public + 2 private subnets,
      and an Internet Gateway.
- [ ] `AppStack` takes a `vpc: ec2.IVpc` prop and places the Lambda
      in a private subnet via `vpc.selectSubnets({ subnetType: PRIVATE })`.
- [ ] Both stacks export a `CfnOutput` (`VpcId` and `LambdaName`).
- [ ] The Jest test uses `Template.fromStack(networkStack)` and
      `Template.fromStack(appStack)` and asserts:
  - `networkStack` has 1 `AWS::EC2::VPC`.
  - `appStack` has 1 `AWS::Lambda::Function`.
  - The Lambda's `VpcConfig.SubnetIds` is non-empty.
- [ ] `cdk synth` succeeds against both stacks without warnings.

## Hints

```ts
// bin/app.ts
const network = new NetworkStack(app, 'NetworkStack', { env: DEV_ENV });
const appStack = new AppStack(app, 'AppStack', {
  env: DEV_ENV,
  vpc: network.vpc,    // pass by reference, not by attribute lookup
});
```

Use `vpc: ec2.IVpc` (the **interface**) in the consuming stack, not
`ec2.Vpc` (the **class**). It keeps the consumer decoupled from how
the VPC was built.

## Stretch goals

- Add a `Stage` class that wraps both stacks so you can deploy
  `dev` and `prod` with one CLI command:
  ```bash
  cdk deploy --all Dev/NetworkStack Dev/AppStack
  ```
- Add a `Tag` Aspect (L29) that forces every resource to carry
  `Project=multi-stack-assignment` and `Stage=<env>`.

## Submission

Zip the `multi-stack-app/` directory (without `node_modules/`) and
include the Jest test output:

```bash
cd multi-stack-app
npm install
npm test
```

Email a link or the zip to **pvishnoi@avilx.com**.

## Further reading

- `../06_real_world/lecture_scripts/L26_multi_stack.md`
- `../06_real_world/lecture_scripts/L28_cdk_context.md`
- `../05_testing_cicd/lecture_scripts/L22_assertions.md`
