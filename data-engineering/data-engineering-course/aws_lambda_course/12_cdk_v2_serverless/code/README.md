# code/ — AWS CDK v2 Serverless Use Case 2

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Companion to:** section 12 (L71–L77)
> **Architecture:** API Gateway + 2 Lambdas + S3, all declared in
> AWS CDK v2 (TypeScript).

This folder is a complete, runnable AWS CDK v2 project. It rebuilds the
serverless CRUD use case from section 8 in TypeScript instead of
CloudFormation YAML.

## What the project deploys

```
                    +-------------------------+
   HTTP client ---->| API Gateway (REST, prod)|
                    +-----------+-------------+
                                |
                +---------------+---------------+
                |                               |
                v                               v
   +--------------------+          +--------------------+
   | Lambda: get-object |          | Lambda: put-object |
   | Node 20 / 256MB    |          | Node 20 / 256MB    |
   +---------+----------+          +---------+----------+
             |                               |
             v                               v
            (+ shared IAM role with s3:GetObject + s3:PutObject)
             |                               |
             +---------------+---------------+
                             |
                             v
                +---------------------------+
                | S3 bucket (versioned +    |
                | SSE-S3, public blocked)   |
                +---------------------------+
```

## Prerequisites

- Node.js 20 LTS and npm 10+ (`node --version`, `npm --version`)
- AWS CLI v2 configured (`aws sts get-caller-identity` returns your account)
- AWS CDK v2 CLI (`npm install -g aws-cdk` and `cdk --version`)

If any of these are missing, complete L72 first.

## Quick start (1, 2, 3, deploy)

```bash
# 1. install dependencies
npm install

# 2. compile TypeScript -> JavaScript
npm run build

# 3. ONE-TIME per account/region: create the CDK assets bucket + roles
npx cdk bootstrap

# 4. preview the synthesized CloudFormation template
npx cdk synth

# 5. deploy the stack (~60s the first time)
npx cdk deploy
```

`cdk deploy` will print the API URL at the end. Save it for the smoke
tests below.

## Smoke tests

```bash
API=$(aws cloudformation describe-stacks \
  --stack-name ServerlessStack \
  --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
  --output text)

# PUT a JSON object
curl -X PUT "$API/objects/hello.json" \
  -H "Content-Type: application/json" \
  -d '{"hello":"world"}'

# GET it back
curl "$API/objects/hello.json"

# GET a missing object (expect 404)
curl -i "$API/objects/does-not-exist.json"
```

Expected output for the first PUT:

```json
{"key":"hello.json","bucket":"serverless-objects-...","message":"Stored"}
```

Expected output for the GET:

```json
{"hello":"world"}
```

## Cleanup

```bash
npx cdk destroy
```

The S3 bucket will be emptied (because of `autoDeleteObjects: true`) and
then deleted. The CDK bootstrap resources (assets bucket, file-publishing
role) are **not** destroyed — they are reused by future stacks.

## File map

| File | Purpose |
|---|---|
| `bin/serverless-app.ts` | CDK app entry point. Instantiates the stack. |
| `lib/serverless-stack.ts` | The stack itself: S3 + IAM + Lambda x2 + API GW. |
| `lambda/get-object.ts` | Handler for `GET /objects/{key}`. |
| `lambda/put-object.ts` | Handler for `PUT /objects/{key}`. |
| `package.json` | Dependencies and npm scripts. |
| `tsconfig.json` | TypeScript compiler options. |
| `cdk.json` | Tells the CDK CLI where the app entry is. |
| `cdk.context.json` | Cached AWS environment lookups (region, account). |
| `.gitignore` | Standard Node + CDK ignores. |

## Why these specific choices

- **One stack, one app.** Mirrors the section 13 CloudFormation template
  exactly so a learner can diff the two side-by-side.
- **Two Lambda functions, one role.** Both functions need the same
  `s3:GetObject` + `s3:PutObject` permission on the same bucket, so a
  single role is simpler and matches the principle of least privilege.
- **AWS SDK v3 (`@aws-sdk/client-s3`)**. The current AWS recommendation
  and what CDK v2 itself uses internally.
- **`lambda.Code.fromAsset('lambda/')`**. CDK bundles the directory
  with `esbuild` and uploads the zip to the bootstrapped assets bucket.
- **`apigateway.RestApi` (not `LambdaRestApi`)**. We have two functions,
  so the higher-level "everything goes to one Lambda" helper is the
  wrong fit.
- **REST API (not HTTP API)**. REST APIs have first-class CDK support
  for CORS preflight, request validation, and API keys. The HTTP API
  L2 is more limited.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `cdk: command not found` | The CDK CLI is not installed | `npm install -g aws-cdk` |
| `Error: Need to perform AWS calls for account ... but no credentials found` | AWS CLI not configured | `aws configure` (or `aws configure sso`) |
| `Error: This stack uses assets, so the toolkit stack must be deployed` | `cdk bootstrap` not run for this account/region | `npx cdk bootstrap aws://<account>/<region>` |
| `Bucket name already exists` | The auto-generated name collides | Edit `bucketName` in `serverless-stack.ts` to add a suffix |
| `AccessDenied` on PUT/GET | Role does not have S3 permissions | Confirm the `inlinePolicies` block in L75 is present in the stack |
| Type errors on `npm run build` | `@aws-sdk/client-s3` not installed | `npm install` (the dev deps include it) |

## License

MIT.
