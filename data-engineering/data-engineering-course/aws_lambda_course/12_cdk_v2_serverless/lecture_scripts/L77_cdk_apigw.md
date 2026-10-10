---
title: L77 — AWS CDK — Create API Gateway using AWS CDK v2
author: Prem Vishnoi <prem.vishnoi@example.com>
section: 12
duration: 7:53
---

# L77 — AWS CDK — Create API Gateway using AWS CDK v2

> **Section:** 12 — AWS CDK v2
> **Duration target:** 7:53
> **Author:** Prem Vishnoi <prem.vishnoi@example.com>

## Prereqs

- L74 — `objectsBucket` exists.
- L75 — `lambdaExecutionRole` exists.
- L76 — `getObjectFn` and `putObjectFn` exist with the correct
  handler code and environment.
- Section 7 — API Gateway concepts (resources, methods, integrations,
  CORS).

## Key terms

- **`apigateway.RestApi`** — L2 construct for a REST API (as opposed
  to HTTP API). REST APIs are the older, more featureful option.
- **`LambdaIntegration`** — proxy integration that forwards the
  entire HTTP request to Lambda and returns the entire Lambda response.
- **`apigateway.Resource`** — a path part. The pattern
  `api.root.addResource('objects').addResource('{key}')` creates
  `/objects/{key}`.
- **`CorsOptions`** — the L2 way to enable CORS. With `allowOrigins: ['*']`
  and `allowMethods: ['GET', 'PUT']`, API Gateway handles the
  preflight `OPTIONS` for you.
- **`LambdaRestApi`** — a higher-level helper that creates a single
  proxy resource `/{proxy+}` and forwards everything to a single
  Lambda. We use the lower-level `RestApi` + `Resource` API because
  the stack has *two* functions, not one.
- **Deploy + Stage** — the `RestApi` L2 auto-creates a `dev` deployment
  stage. We override the stage name to `prod` for clarity.

## Lecture

This is the last construct to add. With the API Gateway in place,
`npx cdk deploy` will produce the full architecture from the L73
diagram.

### The full API Gateway construct

Append this block to `lib/serverless-stack.ts`:

```ts
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as logs from 'aws-cdk-lib/aws-logs';

// ------------------------------------------------------------
// REST API — exposes the two Lambdas as /objects/{key}
// ------------------------------------------------------------
const api = new apigateway.RestApi(this, 'ObjectsApi', {
  restApiName: 'Serverless Objects API',
  description: 'API Gateway in front of the get-object and put-object Lambdas.',

  // Auto-deploy a `prod` stage on every change. Setting `stageName`
  // overrides the default 'prod' so the URL is predictable.
  deployOptions: {
    stageName: 'prod',
    description: 'Production stage',
  },

  // Default CORS for the whole API. Per-method OPTIONS handlers are
  // also created automatically by the integration when we use
  // `defaultCorsPreflightOptions`.
  defaultCorsPreflightOptions: {
    allowOrigins: apigateway.Cors.ALL_ORIGINS,
    allowMethods: ['GET', 'PUT', 'OPTIONS'],
    allowHeaders: ['Content-Type', 'Authorization'],
  },
});

// /objects
const objectsResource = api.root.addResource('objects');

// /objects/{key}
const keyResource = objectsResource.addResource('{key}');

// GET /objects/{key}  -> getObjectFn
keyResource.addMethod(
  'GET',
  new apigateway.LambdaIntegration(getObjectFn, {
    proxy: true,
  }),
);

// PUT /objects/{key}  -> putObjectFn
keyResource.addMethod(
  'PUT',
  new apigateway.LambdaIntegration(putObjectFn, {
    proxy: true,
  }),
);

// ------------------------------------------------------------
// Outputs
// ------------------------------------------------------------
new CfnOutput(this, 'ApiUrl', {
  value: api.url,
  description: 'Invoke URL of the REST API (prod stage)',
  exportName: 'ServerlessApiUrl',
});
```

### What each piece does

#### `apigateway.RestApi`

The top-level L2 construct. We pass:

- `restApiName` — what shows up in the API Gateway console.
- `deployOptions.stageName` — controls the URL path. With
  `stageName: 'prod'`, the URL is `https://<id>.execute-api.<region>.amazonaws.com/prod/...`.
- `defaultCorsPreflightOptions` — the L2 automatically responds to
  `OPTIONS` requests on every method with the CORS headers you list
  here. Without this, a browser preflight would 403 and the API would
  only work from `curl`.

#### `LambdaIntegration`

`LambdaIntegration` with `proxy: true` is the **Lambda proxy
integration** — the entire HTTP request (path, headers, body,
query string) is passed to the Lambda as an `APIGatewayProxyEvent`,
and the Lambda's `APIGatewayProxyResult` is returned to the client
verbatim. This is the only integration style you should use for
modern serverless APIs.

#### Resources and methods

```ts
const objectsResource = api.root.addResource('objects');
const keyResource = objectsResource.addResource('{key}');
keyResource.addMethod('GET', new apigateway.LambdaIntegration(getObjectFn, { proxy: true }));
keyResource.addMethod('PUT', new apigateway.LambdaIntegration(putObjectFn, { proxy: true }));
```

This is the **L2 fluent API** for resources and methods. Under the
hood, CDK creates:

- An `AWS::ApiGateway::Resource` for `objects`.
- An `AWS::ApiGateway::Resource` for `{key}` (with `PathPart: '{key}'`).
- An `AWS::ApiGateway::Method` for `GET` with an `AWS::ApiGateway::Integration`
  of type `AWS_PROXY` pointing at `getObjectFn`.
- An `AWS::ApiGateway::Method` for `PUT` pointing at `putObjectFn`.
- An `AWS::Lambda::Permission` for each function so API Gateway can
  invoke it.

You do **not** need to write the lambda invoke permission by hand —
CDK adds it automatically when you wire the function into an
integration.

### Outputs

We export two CloudFormation outputs:

- `ApiUrl` — the invoke URL of the `prod` stage.
- `ObjectsBucketName` (from L74) — the bucket name.

After the first deploy, fetch them with:

```bash
aws cloudformation describe-stacks \
  --stack-name ServerlessStack \
  --query "Stacks[0].Outputs"
```

### The final deploy

From `code/`:

```bash
npx cdk synth          # preview the template (~150 lines)
npx cdk deploy         # create / update the stack (~60s the first time)
```

The `cdk deploy` output will include the invoke URL. Copy it.

### Smoke test

```bash
API=$(aws cloudformation describe-stacks \
  --stack-name ServerlessStack \
  --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
  --output text)

# PUT a small JSON document
curl -X PUT "$API/objects/hello.json" \
  -H "Content-Type: application/json" \
  -d '{"hello":"world"}'
# -> 200, {"key":"hello.json","bucket":"serverless-objects-...","message":"Stored"}

# GET it back
curl "$API/objects/hello.json"
# -> 200, {"hello":"world"}

# GET a missing key
curl -i "$API/objects/does-not-exist.json"
# -> 404, {"message":"Object does-not-exist.json not found"}
```

### Cleanup

When you are done, destroy the stack with a single command. The S3
bucket will be emptied (because of `autoDeleteObjects`) and then
deleted:

```bash
npx cdk destroy
```

The bootstrap resources (assets bucket, file-publishing role) are
**not** destroyed — they are reused by future stacks.

## Hands-on

1. Add the API Gateway block to `serverless-stack.ts`.
2. `npm run build` to compile the TypeScript.
3. `npx cdk synth` and confirm the output template contains one
   `AWS::ApiGateway::RestApi`, two `AWS::ApiGateway::Method`
   resources, and one `AWS::ApiGateway::Stage`.
4. `npx cdk deploy` and watch the event stream.
5. Copy the `ApiUrl` output and run the three `curl` smoke tests
   above.
6. `npx cdk destroy` to clean up.

## Quiz prep

- What is the difference between `apigateway.RestApi` and
  `apigateway.LambdaRestApi`?
- What does `proxy: true` on a `LambdaIntegration` mean?
- Why do we not need to write the Lambda invoke permission by hand?
- Which CORS option in the L2 construct auto-creates the `OPTIONS`
  methods?
- What does `cdk destroy` clean up, and what does it leave behind?

## Further reading

- [aws-cdk-lib `apigateway.RestApi`](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_apigateway.RestApi.html)
- [aws-cdk-lib `apigateway.LambdaIntegration`](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_apigateway.LambdaIntegration.html)
- [API Gateway — Lambda proxy integration](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html)
- [Section 7 — API Gateway concepts (L25–L29)](../07_apigw_overview/lecture_scripts/L25_apigw_overview.md)
