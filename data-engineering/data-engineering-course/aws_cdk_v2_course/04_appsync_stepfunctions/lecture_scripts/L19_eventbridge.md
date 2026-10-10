---
lecture: L19
title: "EventBridge buses, rules, and CDK Rule construct"
duration: "12:00"
section: 4
prereqs: ["L18"]
---

# L19 — EventBridge Buses, Rules, and the `Rule` Construct

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 4 — AppSync + Step Functions + EventBridge
> **Duration:** 12:00

## Prereqs

L18 — Step Functions

## Key terms

- **Event bus** — the router. There is a default bus per account
  (`aws.events`); you can create custom buses too.
- **Rule** — a pattern that matches incoming events and sends them
  to one or more targets (Lambda, SQS, SNS, Step Functions, ...).
- **`eventPattern`** — a JSON-like object in CDK land that becomes
  an EventBridge event pattern.
- **Schedule** — a special "rate" expression (`rate(5 minutes)`) or
  cron expression.

## Lecture

EventBridge is the event router that ties everything together.
Services publish events to the bus; you write Rules that match on
event patterns and fan out to targets.

```ts
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';

const bus = events.EventBus.fromEventBusName(this, 'Bus', 'default');

const rule = new events.Rule(this, 'OrderPlaced', {
  eventBus: bus,
  eventPattern: {
    source: ['com.myapp.orders'],
    detailType: ['OrderPlaced'],
    detail: { amount: [{ numeric: [ '>', 1000 ] }] },
  },
});

rule.addTarget(new targets.LambdaFunction(processFn));
rule.addTarget(new targets.SfnStateMachine(stateMachine));
rule.addTarget(new targets.SqsQueue(queue));          // fan-out

// Scheduled (cron / rate)
const every5min = new events.Rule(this, 'Every5Min', {
  schedule: events.Schedule.rate(cdk.Duration.minutes(5)),
});
every5min.addTarget(new targets.LambdaFunction(scheduledFn));
```

Common target types live under `aws-cdk-lib/aws-events-targets`:

- `LambdaFunction(fn)`
- `SqsQueue(queue)`
- `SnsTopic(topic)`
- `SfnStateMachine(sm)`
- `EcsTask(...)`
- `KinesisStream(stream)`

CDK auto-wires the IAM permission for the target — the Lambda's
role, the queue's policy, and the state machine's role all
**receive the bus's `events:PutEvents` permission automatically**.

## Hands-on

There is no EventBridge resource in the `app-sync-sfn` project yet.
Add one as practice:

```ts
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import { SfnStateMachine } from 'aws-cdk-lib/aws-events-targets';

new events.Rule(this, 'TriggerOrderMachine', {
  schedule: events.Schedule.rate(cdk.Duration.minutes(10)),
  targets: [new targets.SfnStateMachine(this.stateMachine)],
});
```

Re-run `npm test` — the test will still pass (we assert state
machine count, which is unchanged), but you can add a new assertion
for `AWS::Events::Rule`.

## Quiz prep

- What's the default event bus name? (`default`)
- Which CDK construct schedules a Lambda every 5 min?
  (`events.Rule` with `Schedule.rate`)
- Where do target classes live? (`aws-cdk-lib/aws-events-targets`)

## Further reading

- [EventBridge CDK reference](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_events-readme.html)
- Next up: **L20 — Wire them all together**
