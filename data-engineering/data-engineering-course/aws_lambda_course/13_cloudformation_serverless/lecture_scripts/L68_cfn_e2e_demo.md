# L68 — AWS CloudFormation — End to End Demo

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 13
> **Duration target:** 1:10
> **Lecture ID:** L68

## Prereqs

- L62–L67 complete (you understand every resource in the full
  stack).
- An asset bucket for `aws cloudformation package` to upload
  Lambda zips to. (Any bucket you own works.)

## Key terms

- **`aws cloudformation package`** — uploads local assets
  (Lambda zips, nested templates) to S3 and rewrites the template
  in place so `Code.S3Bucket`/`S3Key` point at the uploaded
  artifacts.
- **`aws cloudformation deploy`** — convenience command for
  create-or-update. Generates a change set, shows it, and (if you
  pass `--no-fail-on-empty-changeset`) auto-executes it.
- **`--capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM`** —
  opt-in to creating IAM resources and naming them explicitly.
  Required for the full-stack template because we use
  `RoleName:` and `PolicyName:`.

## Lecture

This lecture is the payoff. We collapse everything from L62–L67
into one template — `templates/06_serverless_full_stack.yaml` —
and ship it in two CLI calls.

### The full stack

The full-stack template declares 15 resources, in dependency
order:

1. `ServerlessBucket` — the S3 bucket (L62).
2. `LambdaExecutionRole` + `LambdaS3Policy` — IAM (L63).
3. `GetObjectFunction` + `PutObjectFunction` — Lambda (L64).
4. `CodeAssetsBucket` — a private S3 bucket for CFN to upload the
   Lambda zips to. Only present so the template is
   self-bootstrapping.
5. `ServerlessApi` + `ObjectsResource` + `ObjectKeyResource` — API
   Gateway container + resource tree (L65).
6. `GetObjectMethod` + `PutObjectMethod` — methods with
   `AWS_PROXY` integration (L66).
7. `GetInvokePermission` + `PutInvokePermission` — Lambda
   resource policies (L67).
8. `ApiDeployment` + `ApiStage` — snapshot + named stage (L66).
9. `Outputs.ApiUrl` — the surface URL.

The `!Ref`, `!GetAtt`, and `!Sub` glue chains everything
together:

```text
BucketName parameter → BucketName property of ServerlessBucket
                     → arn:aws:s3:::${BucketName} in LambdaS3Policy
                     → BUCKET_NAME env var in both Lambdas
```

```text
ServerlessApi  ──►  ObjectsResource  ──►  ObjectKeyResource
   │                                                  │
   └────► GetObjectMethod  ◄──────────────────────────┘
   └────► PutObjectMethod
```

### Two CLI calls

```bash
cd 13_cloudformation_serverless/code

# 1. Package: upload local zips to S3 and rewrite the template
#    so Code.S3Bucket/S3Key point at the uploaded artifacts.
aws cloudformation package \
  --template-file templates/06_serverless_full_stack.yaml \
  --s3-bucket serverless-cfn-assets-<your-account-id> \
  --output-template-file /tmp/06.pkg.yaml

# 2. Deploy: create or update the stack. CAPABILITY_NAMED_IAM is
#    required because the template sets RoleName: and PolicyName:.
aws cloudformation deploy \
  --stack-name serverless-full-stack \
  --template-file /tmp/06.pkg.yaml \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --parameter-overrides \
      BucketName=serverless-use-case-2-<your-initials> \
      StageName=prod
```

The `deploy.sh` script in `code/` does the same with a couple of
defaults baked in (region, stack name) so you only have to supply
the unique parts.

### Read the URL and exercise the API

```bash
API_URL=$(aws cloudformation describe-stacks \
  --stack-name serverless-full-stack \
  --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
  --output text)

echo "$API_URL"

# PUT an object
curl -X PUT --data "hello from section 13" \
     "$API_URL/objects/hello.txt"

# GET it back
curl "$API_URL/objects/hello.txt"
```

Expected: PUT returns
`{"key":"hello.txt","etag":"...","size":22}` and GET returns
`{"key":"hello.txt","data":"hello from section 13"}`.

### Teardown

```bash
aws cloudformation delete-stack --stack-name serverless-full-stack
aws s3 rb s3://serverless-cfn-assets-<your-account-id> --force
```

The S3 bucket for assets is declared inside the stack but with
`DeletionPolicy: Retain` so that it survives a `delete-stack`. If
you want to remove it, do it explicitly:

```bash
aws s3 rb s3://serverless-cfn-assets-<your-account-id> --force
```

### What just happened

You created 15 AWS resources — S3 bucket, IAM role + policy, two
Lambdas, a CFN-assets bucket, REST API, two resources, two
methods, two resource-based policies, a deployment, and a stage
— with a single CLI invocation. The whole stack is now in your CloudFormation
"stacks" list, deletable in one click, and reproducible across
regions/accounts.

L69 makes the bucket name + stage name parameter-driven so the
same template works in `dev`, `staging`, and `prod`. L70 adds
`Metadata` to group those parameters in the console wizard.

## Hands-on

Run `code/deploy.sh` end-to-end. It will:

1. `validate-template` on the full-stack template.
2. `package` to upload the zips.
3. `deploy` with a unique bucket name + `prod` stage.
4. Print the `ApiUrl`.
5. Smoke-test with `curl` (PUT then GET).

Then `delete-stack` and re-deploy with a different stage name to
see how easy it is to spin up a parallel environment.

## Quiz prep

- The two CLI commands and what each one does.
- Why `CAPABILITY_NAMED_IAM` is required for the full-stack
  template.
- The dependency order CloudFormation picks for the full stack.
- The three ways to supply parameter values at deploy time
  (default, `--parameter-overrides`, `--parameters-file`).

## Further reading

- [`aws cloudformation package`](https://docs.aws.amazon.com/cli/latest/reference/cloudformation/package.html)
- [`aws cloudformation deploy`](https://docs.aws.amazon.com/cli/latest/reference/cloudformation/deploy.html)
- [Capabilities](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-iam-template.html#capabilities)
