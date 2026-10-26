---
lecture: L20
title: "Wiring AppSync → SFN → EventBridge — full serverless flow"
duration: "12:00"
section: 4
prereqs: ["L19"]
---

# L20 — Wiring AppSync → SFN → EventBridge

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 4 — AppSync + Step Functions + EventBridge
> **Duration:** 12:00

## Prereqs

L19 — EventBridge

## Key terms

- **End-to-end (e2e) flow** — every layer talks to the layer below
  (AppSync → Resolver Lambda / SFN → EventBridge → Lambda) and the
  data flows all the way through.
- **Fan-out** — one event source, many targets.

## Lecture

Let's connect the dots. Here's the full serverless flow:

```text
                 ┌───────────────────────────────┐
   HTTP POST     │   AppSync GraphQL API         │
   ─────────▶    │   (orders-api)                 │
                 └────────────┬──────────────────┘
                              │ Mutation.startOrder
                              ▼
                 ┌───────────────────────────────┐
                 │   Lambda (startOrderResolver) │
                 │   StartExecution API call     │
                 └────────────┬──────────────────┘
                              │
                              ▼
                 ┌───────────────────────────────┐
                 │   Step Functions state machine │
                 │   InvokeOrder → Done           │
                 └────────────┬──────────────────┘
                              │ sends event to default bus
                              ▼
                 ┌───────────────────────────────┐
                 │   EventBridge (default bus)   │
                 │   Rule: source=com.myapp.*    │
                 └─────┬───────────────┬─────────┘
                       ▼               ▼
              ┌──────────────┐   ┌────────────────┐
              │  Lambda (a)  │   │  Lambda (b)     │
              │  audit-log    │   │  send-email     │
              └──────────────┘   └────────────────┘
```

In CDK:

```ts
// 1. AppSync + resolver Lambda (from L16–L17)
this.api = new appsync.GraphqlApi(/* ... */);
const lambdaDs = this.api.addLambdaDataSource(/* ... */);
lambdaDs.createResolver('StartOrderResolver', { /* ... */ });

// 2. State machine (from L18)
this.stateMachine = new sfn.StateMachine(/* ... */);

// 3. EventBridge rule to start the SM on schedule (from L19)
new events.Rule(this, 'ScheduleOrders', {
  schedule: events.Schedule.rate(cdk.Duration.minutes(5)),
  targets: [new targets.SfnStateMachine(this.stateMachine)],
});

// 4. EventBridge rule to react to SM-completed events
new events.Rule(this, 'OnOrderCompleted', {
  eventPattern: {
    source: ['aws.states'],
    detailType: ['Step Functions Execution Status Change'],
    detail: { stateMachineArn: [this.stateMachine.stateMachineArn],
              status: ['SUCCEEDED'] },
  },
  targets: [new targets.LambdaFunction(auditFn)],
});
```

You'd typically also wire AppSync `getOrder` to a Lambda that
fetches state-machine execution history. The lesson: **the four
CDK patterns from sections 2–4 (S3 + IAM, Lambda, AppSync, SFN,
EventBridge) compose into a complete asynchronous API** without
writing any CloudFormation by hand.

## Hands-on

Add the schedule rule from L19 to `code/app-sync-sfn/`. Add one
extra Jest assertion:

```ts
template.resourceCountIs('AWS::Events::Rule', 1);
```

Re-run `npm test`. It should pass.

## Quiz prep

- Name the 5 services in the canonical e2e flow.
  (AppSync, Lambda, Step Functions, EventBridge, Lambda again as the consumer)
- Why does CDK need no extra IAM for the rule → targets? (the
  grant* methods auto-wire `events:PutEvents`)

## Further reading

- Working code: `../code/app-sync-sfn/`
- Next up: **Section 5 — Testing & CI/CD (L21+)**
