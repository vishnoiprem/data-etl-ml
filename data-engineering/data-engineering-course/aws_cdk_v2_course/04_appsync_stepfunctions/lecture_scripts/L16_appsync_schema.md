---
lecture: L16
title: "AppSync GraphQL API with CDK — schema-as-code"
duration: "12:00"
section: 4
prereqs: ["L15"]
---

# L16 — AppSync GraphQL API with CDK — Schema-as-Code

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 4 — AppSync + Step Functions + EventBridge
> **Duration:** 12:00

## Prereqs

L15 — End-to-end serverless stack

## Key terms

- **GraphQL** — a query language where the client asks for exactly
  the fields it wants. One endpoint, many shapes of response.
- **Schema-first** — you write the schema first (SDL), then attach
  resolvers per field.
- **AppSync** — AWS's managed GraphQL service.
- **Authorization types** — `API_KEY`, `AWS_IAM`, `AMAZON_COGNITO_USER_POOLS`,
  `OPENID_CONNECT`, `AWS_LAMBDA`.

## Lecture

AppSync is the modern answer to "API Gateway but with GraphQL." You
write a schema, you attach resolvers per field, and AppSync manages
the deployment, the throttling, the subscriptions, the caching.

```ts
import * as appsync from 'aws-cdk-lib/aws-appsync';

const api = new appsync.GraphqlApi(this, 'Api', {
  name: 'orders-api',
  definition: appsync.Schema.fromString(`
    type Order { id: String!  status: String! }

    type Query {
      getOrder(id: String!): Order
    }

    type Mutation {
      startOrder(id: String!): Order
    }

    schema {
      query: Query
      mutation: Mutation
    }
  `),
  authorizationConfig: {
    defaultAuthorization: {
      authorizationType: appsync.AuthorizationType.API_KEY,
    },
  },
});
```

In production, move the schema into a `schema.graphql` file and use
`SchemaFile.fromAsset(path.join(__dirname, 'schema.graphql'))` so it
gets nice IDE syntax highlighting.

There are five authorization types. Pick by audience:

| Audience | Authorization |
|---|---|
| Public, low-trust clients (e.g., a marketing form) | `API_KEY` |
| Internal AWS callers | `AWS_IAM` |
| End users via your own auth | `AMAZON_COGNITO_USER_POOLS` |
| Federated SSO (Auth0, Okta, etc.) | `OPENID_CONNECT` |
| Custom resolver (extreme cases) | `AWS_LAMBDA` (advanced) |

## Hands-on

The `code/app-sync-sfn/` project uses `Schema.fromString`. After
deploying, you can query the API with `curl`:

```bash
API=$(npx cdk output AppSyncSfnStack.GraphqlUrl)
KEY=$(npx cdk output AppSyncSfnStack.ApiKey)

curl -X POST "$API" \
  -H "x-api-key: $KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ getOrder(id: \"o-1\") { id status } }"}'
```

## Quiz prep

- Name two ways to declare an AppSync schema in CDK. (`Schema.fromString`, `SchemaFile.fromAsset`)
- Which authorization type is the simplest for public clients? (`API_KEY`)
- What's the difference between `Query` and `Mutation`? (Query reads,
  Mutation writes — both run server-side in AppSync)

## Further reading

- [AppSync GraphQL schema](https://docs.aws.amazon.com/appsync/latest/devguide/design-graphql.html)
- Next up: **L17 — Data sources and resolvers**
