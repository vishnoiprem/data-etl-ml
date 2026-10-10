---
lecture: L15
title: "Putting it together — end-to-end serverless stack"
duration: "12:00"
section: 3
prereqs: ["L14"]
---

# L15 — End-to-End Serverless Stack

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 3 — Building with CDK
> **Duration:** 12:00

## Prereqs

L14 — IAM roles + grants

## Key terms

- **Asset bucket** — the S3 bucket CDK uses to store function zips
  + Docker layers. Created automatically by `lambda.Function` /
  `s3deploy.BucketDeployment`.
- **`CfnOutput`** — exposes a value to the CloudFormation console
  and to other tools.
- **`stageName`** — the URL prefix for your deployed API.

## Lecture

Let's walk through the `lambda-api` stack end-to-end and label what
each line does:

```ts
// 1. An S3 bucket to hold future assets (e.g., static frontend).
this.assetsBucket = new s3.Bucket(this, 'AssetsBucket', {
  encryption: s3.BucketEncryption.S3_MANAGED,
  blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
  enforceSSL: true,
  removalPolicy: cdk.RemovalPolicy.DESTROY,  // demo only
  autoDeleteObjects: true,                    // demo only
});

// 2. A Lambda function with inline code (replace with fromAsset in prod).
this.handler = new lambda.Function(this, 'HelloHandler', {
  runtime: lambda.Runtime.NODEJS_20_X,
  handler: 'index.handler',
  code: lambda.Code.fromInline(/* ... */),
  memorySize: 256,
  timeout: cdk.Duration.seconds(10),
  environment: { BUCKET_NAME: this.assetsBucket.bucketName },
});

// 3. Least-privilege IAM: the function can read the asset bucket.
this.assetsBucket.grantRead(this.handler);

// 4. The REST API (L3 — proxy integration).
this.api = new apigw.LambdaRestApi(this, 'HelloApi', {
  handler: this.handler,
  restApiName: 'hello-api',
  deployOptions: { stageName: 'prod' },
  defaultCorsPreflightOptions: { /* CORS */ },
});

// 5. Outputs.
new cdk.CfnOutput(this, 'ApiUrl', { value: this.api.url });
new cdk.CfnOutput(this, 'FunctionName', { value: this.handler.functionName });
new cdk.CfnOutput(this, 'AssetsBucketName', { value: this.assetsBucket.bucketName });
```

The synthesized template is ~6 CloudFormation resources:

```text
AWS::ApiGateway::RestApi
AWS::ApiGateway::Deployment
AWS::ApiGateway::Stage
AWS::IAM::Role
AWS::Lambda::Function
AWS::Lambda::Permission
AWS::S3::Bucket
AWS::S3::BucketPolicy
```

After `npx cdk deploy` you can immediately hit the API:

```bash
API=$(npx cdk output LambdaApiStack.ApiUrl)
curl "$API/hello"
# {"message":"Hello from CDK v2!","path":"/hello","method":"GET"}
```

## Hands-on

```bash
cd 03_building_with_cdk/code/lambda-api
npm install
npm test
# If you have AWS creds:
npx cdk deploy
curl "$(npx cdk output LambdaApiStack.ApiUrl)/hello"
npx cdk destroy
```

## Quiz prep

- What 4 things does `lambda.Function` create for you? (role, policy,
  log group, function)
- How do you get the API URL after deploy?
  (`npx cdk output <StackName>.ApiUrl`)

## Further reading

- Code: `../code/lambda-api/`
- Next up: **Section 4 — AppSync + Step Functions (L16+)**
