---
lecture: L18
title: "Step Functions state machines in CDK — Choice, LambdaInvoke"
duration: "12:00"
section: 4
prereqs: ["L17"]
---

# L18 — Step Functions State Machines in CDK

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 4 — AppSync + Step Functions + EventBridge
> **Duration:** 12:00

## Prereqs

L17 — AppSync resolvers

## Key terms

- **State machine** — a JSON definition of states and transitions.
  Two flavors: Standard (1 yr duration, exactly-once) and Express
  (5 min, at-least-once).
- **`sfn.Pass`** — a no-op state. Useful for testing or labeling.
- **`tasks.LambdaInvoke`** — a Task state that calls a Lambda.
- **`sfn.Choice`** — conditional branching on JSONPath.
- **`DefinitionBody.fromChainable(startAt)`** — modern API; pass a
  chain you built with `.next()`, `.branch()`, etc.

## Lecture

Step Functions is durable workflow orchestration. Each state is a
unit of work; transitions between states are stored durably so the
workflow can resume after a crash.

The CDK v2 API is fluent: you build a `Chain` and pass it to
`DefinitionBody.fromChainable(...)`.

```ts
import * as sfn     from 'aws-cdk-lib/aws-stepfunctions';
import * as tasks   from 'aws-cdk-lib/aws-stepfunctions-tasks';

const orderWork = new tasks.LambdaInvoke(this, 'OrderWork', {
  lambdaFunction: workFn,
  payload: sfn.TaskInput.fromObject({ 'id.$': '$.id' }),
});

const validate = new tasks.LambdaInvoke(this, 'Validate', {
  lambdaFunction: validateFn,
});

// Branch by amount
const isLarge  = sfn.Condition.numberGreaterThanJsonPath(
  '$.amount',  '$.threshold',
);
const choice   = new sfn.Choice(this, 'IsLarge')
  .when(isLarge, orderWork)
  .otherwise(validate);

const machine = new sfn.StateMachine(this, 'OrderMachine', {
  definitionBody: sfn.DefinitionBody.fromChainable(choice),
  timeout: cdk.Duration.minutes(5),
});
```

The state machine **starts automatically with the right IAM** —
no extra permission wiring needed for Lambda tasks.

Two flavors:

| Flavor | Duration | Pricing model | Use |
|---|---|---|---|
| **Standard** | up to 1 year | per state transition | Long-running, exactly-once semantics |
| **Express** | up to 5 min | per execution + duration | High-volume, at-least-once |

`StateMachineType.EXPRESS` or `.STANDARD` selects which to deploy.

## Hands-on

`code/app-sync-sfn/` has a 2-state machine: `InvokeOrder` (a Lambda
task) → `Done` (a Pass state). The CDK test inspects the
`DefinitionString` JSON to confirm both states exist:

```bash
cd 04_appsync_stepfunctions/code/app-sync-sfn
npm test
```

## Quiz prep

- Which modern API is used to pass a CDK chain to the state machine?
  (`DefinitionBody.fromChainable`)
- Standard vs Express duration limits? (1 yr vs 5 min)
- What's the no-op state called? (`Pass`)

## Further reading

- [Step Functions L2 reference](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_stepfunctions-readme.html)
- Next up: **L19 — EventBridge**
