# Section 4 — AppSync + Step Functions + EventBridge (L16–L20)

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **L-IDs:** L16–L20 | **Duration:** ~60 min | **Quizzes:** `quizzes/section_4.md`
> **Working artifact:** `code/app-sync-sfn/` — AppSync + SFN + Lambda.

Section 4 stitches together the three serverless orchestration
patterns you reach for when a single Lambda isn't enough: GraphQL
front door (AppSync), durable workflow (Step Functions), and
event-driven rules (EventBridge).

## Lectures

| L# | Title | Min | File |
|---|---|---|---|
| L16 | AppSync GraphQL API with CDK — schema-as-code | 12 | `lecture_scripts/L16_appsync_schema.md` |
| L17 | AppSync data sources and resolvers — Lambda, DynamoDB | 12 | `lecture_scripts/L17_appsync_resolvers.md` |
| L18 | Step Functions state machines in CDK — `Choice`, `LambdaInvoke` | 12 | `lecture_scripts/L18_sfn_states.md` |
| L19 | EventBridge buses, rules, and CDK `Rule` construct | 12 | `lecture_scripts/L19_eventbridge.md` |
| L20 | Wiring AppSync → SFN → EventBridge — full serverless flow | 12 | `lecture_scripts/L20_full_flow.md` |

## Working code

| Project | Stack summary | Tests |
|---|---|---|
| `code/app-sync-sfn/` | AppSync GraphQL API + 1 resolver Lambda + Step Functions state machine | 7 Jest assertions on schema + state machine |
