---
lecture: L13
title: "Building a REST API with apigateway.LambdaRestApi"
duration: "12:00"
section: 3
prereqs: ["L12"]
---

# L13 — Building a REST API with `apigateway.LambdaRestApi`

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 3 — Building with CDK
> **Duration:** 12:00

## Prereqs

L12 — Lambda functions

## Key terms

- **`apigw.LambdaRestApi`** — L3 construct: an API Gateway REST API
  with a `{proxy+}` resource + `ANY` method + `AWS_PROXY` integration
  to a single Lambda.
- **`AWS_PROXY` integration** — API Gateway forwards the entire
  request (path, body, headers) to the Lambda as a single event
  payload; the Lambda's response is passed straight back.
- **`defaultCorsPreflightOptions`** — pre-wired CORS handler. Saves
  you from writing `OPTIONS` methods by hand.
- **`deployOptions.stageName`** — the URL path prefix for the
  deployment (e.g., `prod`, `v1`).

## Lecture

`apigw.LambdaRestApi` is the right answer for 80% of serverless
CRUD APIs. One line wires up the API, the deployment, the stage,
and the `ANY /{proxy+}` resource with `AWS_PROXY` integration.

```ts
const fn = new lambda.Function(this, 'Fn', { /* ... */ });

const api = new apigw.LambdaRestApi(this, 'Api', {
  handler: fn,
  restApiName: 'orders-api',
  description: 'CRUD API for the orders service',
  deployOptions: { stageName: 'prod' },
  defaultCorsPreflightOptions: {
    allowOrigins: apigw.Cors.ALL_ORIGINS,
    allowMethods: apigw.Cors.ALL_METHODS,
  },
});
```

After deploy, every path under the stage goes to your Lambda:

```text
POST   https://abc123.execute-api.us-east-1.amazonaws.com/prod/orders
GET    https://abc123.execute-api.us-east-1.amazonaws.com/prod/orders/123
DELETE https://abc123.execute-api.us-east-1.amazonaws.com/prod/orders/123
```

Your Lambda receives the standard API Gateway proxy event:

```jsonc
{
  "resource": "/orders/{id}",
  "path": "/orders/123",
  "httpMethod": "GET",
  "headers": { "...": "..." },
  "queryStringParameters": { "...": "..." },
  "pathParameters": { "id": "123" },
  "body": "...",
  "isBase64Encoded": false
}
```

For more complex APIs (multi-resource, custom integrations, request
validation) fall back to `apigw.RestApi` and wire up the resources
yourself:

```ts
const api = new apigw.RestApi(this, 'Api', { /* ... */ });
const orders = api.root.addResource('orders');
const order  = orders.addResource('{id}');
order.addMethod('GET', new apigw.LambdaIntegration(getOrderFn));
order.addMethod('DELETE', new apigw.LambdaIntegration(deleteOrderFn));
```

## Hands-on

`code/lambda-api/` uses `LambdaRestApi`. The test asserts the
`AWS::ApiGateway::Method` has `Integration.Type: AWS_PROXY`. Run
the tests:

```bash
cd 03_building_with_cdk/code/lambda-api
npm install
npm test
```

## Quiz prep

- What integration type does `LambdaRestApi` use? (`AWS_PROXY`)
- What's the URL path pattern after deploy?
  (`https://<id>.execute-api.<region>.amazonaws.com/<stage>/<path>`)
- When would you reach for `apigw.RestApi` instead?
  (custom integrations, request validation, complex auth)

## Further reading

- [API Gateway L2 reference](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_apigateway-readme.html)
- Next up: **L14 — IAM roles + `grantInvoke`**
