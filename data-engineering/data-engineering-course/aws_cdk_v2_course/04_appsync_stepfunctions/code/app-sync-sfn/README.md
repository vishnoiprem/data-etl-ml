# app-sync-sfn — AppSync + Step Functions in CDK v2

> Working artifact for **Section 4 — AppSync + Step Functions +
> EventBridge (L16–L20)** of the AWS CDK v2 Crash Course.

## What it does

Provisions a serverless orchestrator:

- **AppSync GraphQL API** — schema-as-code (inline), API_KEY
  authorization, two operations:
  - `Query.getOrder(id)` — reads an order
  - `Mutation.startOrder(id)` — kicks off the Step Functions machine
- **Lambda function** — the GraphQL resolver (Node 20, inline)
- **Step Functions state machine** — `LambdaInvoke` → `Pass` (Done)
- **Resolvers** — one per GraphQL field

## Run it

```bash
npm install
npm test                       # run the Jest assertions
npx cdk synth                  # produce cdk.out/AppSyncSfnStack.template.json
npx cdk deploy                 # create the resources
# query:
API_URL=$(npx cdk output AppSyncSfnStack.GraphqlUrl)
API_KEY=$(npx cdk output AppSyncSfnStack.ApiKey)
curl -X POST "$API_URL" \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ getOrder(id: \"o-1\") { id status } }"}'
npx cdk destroy
```

## Files

| File | Purpose |
|---|---|
| `bin/app-sync-sfn.ts` | CDK App entry point |
| `lib/app-sync-sfn-stack.ts` | The stack — AppSync + Lambda + SFN |
| `test/app-sync-sfn.test.ts` | Jest tests using `Template.fromStack` |
| `cdk.json` | Tells the CDK CLI how to run the app |
| `tsconfig.json` | TypeScript compiler options |
| `package.json` | npm deps (`aws-cdk-lib`, `constructs`, `jest`, ...) |

## Notes

- The schema is declared **inline** with `Schema.fromString` for
  brevity. In production, move it to a `schema.graphql` file and use
  `SchemaFile.fromAsset`.
- The state machine uses a single Lambda task + a Pass state to keep
  the example self-contained. In real apps the Pass state would be
  replaced with `DynamoUpdateItem`, `SnsPublish`, or another
  `LambdaInvoke`.
- For EventBridge wiring (L19), see the lecture script — it adds a
  `Rule` that targets the state machine on a schedule.
