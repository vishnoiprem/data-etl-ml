---
lecture: L17
title: "AppSync data sources and resolvers — Lambda, DynamoDB"
duration: "12:00"
section: 4
prereqs: ["L16"]
---

# L17 — AppSync Data Sources and Resolvers

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 4 — AppSync + Step Functions + EventBridge
> **Duration:** 12:00

## Prereqs

L16 — AppSync schema-as-code

## Key terms

- **Data source** — the backing compute/data store for a resolver
  (Lambda, DynamoDB table, RDS, OpenSearch, HTTP endpoint, none).
- **Resolver** — the per-field mapping that turns a GraphQL request
  into a data source call and back.
- **Request/response mapping templates** — Apache Velocity templates
  (VTL) for non-Lambda data sources. Lambda data sources skip them.
- **Pipes vs Lambda** — Lambda data sources carry their own auth via
  the function's role; non-Lambda data sources use IAM + VTL.

## Lecture

Resolvers are what makes AppSync "do" anything. There is one
resolver per field; without one, AppSync returns `null`.

```ts
const lambdaDs = api.addLambdaDataSource('LambdaDS', fn);

// Query.getOrder → lambdaDs
lambdaDs.createResolver('GetOrderResolver', {
  typeName: 'Query',
  fieldName: 'getOrder',
});

// Mutation.startOrder → lambdaDs
lambdaDs.createResolver('StartOrderResolver', {
  typeName: 'Mutation',
  fieldName: 'startOrder',
});
```

That's it for Lambda data sources — your Lambda receives a standard
event:

```jsonc
{
  "arguments": { "id": "o-1" },
  "identity": { "...": "..." },
  "source": null,
  "info": { "fieldName": "getOrder", "parentTypeName": "Query", "...": "..." }
}
```

For DynamoDB, use the built-in `addDynamoDbDataSource` and provide a
VTL request mapping template:

```ts
const ddb = api.addDynamoDbDataSource('OrdersTable', ordersTable);

ddb.createResolver('GetOrderResolver', {
  typeName: 'Query',
  fieldName: 'getOrder',
  requestMappingTemplate: appsync.MappingTemplate.dynamoDbGetItem(
    'Orders',    // table name
    'id',        // primary key
  ),
  responseMappingTemplate: appsync.MappingTemplate.dynamoDbResultItem(),
});
```

**Lambda data sources skip VTL** because the Lambda receives the
full context and returns the full JSON. **DynamoDB data sources use
VTL** because there's no Lambda in between — the templates execute
inside AppSync itself.

For EventBridge, SFN, SQS, SNS — use `addHttpDataSource` and target
the AWS service API directly.

## Hands-on

`code/app-sync-sfn/` has two resolvers. The CDK test asserts both:
`template.resourceCountIs('AWS::AppSync::Resolver', 2)`. Re-run the
test after deleting one resolver to see the count drop.

## Quiz prep

- Which data source type skips VTL? (Lambda)
- Which data source type requires request + response mapping templates?
  (DynamoDB, OpenSearch, HTTP)
- What's the per-field unit of work in AppSync? (a Resolver)

## Further reading

- [AppSync resolvers](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_appsync-readme.html)
- Next up: **L18 — Step Functions**
