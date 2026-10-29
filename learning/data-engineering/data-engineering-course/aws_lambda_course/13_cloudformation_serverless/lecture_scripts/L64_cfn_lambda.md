# L64 — AWS CloudFormation — AWS Lambda

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 13
> **Duration target:** 14:02
> **Lecture ID:** L64

## Prereqs

- L62 (S3) and L63 (IAM role) complete.
- Familiarity with Lambda handler signatures and `boto3`.

## Key terms

- **`AWS::Lambda::Function`** — the CFN resource type for a Lambda.
- **`Runtime`** — the language runtime (`python3.11`,
  `nodejs20.x`, `java21`, etc.). Lambda reads this to pick the right
  micro-container.
- **`Handler`** — the import path of the entry point:
  `<filename>.<function_name>` for Python (we use
  `get_object.lambda_handler`).
- **`Code`** — either a `ZipFile` (inline, 4 KiB cap), an inline
  `S3Bucket`/`S3Key` reference, or — most commonly in production —
  a `S3Bucket`/`S3Key` produced by `aws cloudformation package`.
- **`Environment.Variables`** — key/value pairs injected into the
  Lambda runtime. Use these for non-secret config (bucket name,
  feature flags). For secrets use AWS Secrets Manager / SSM.
- **`!Ref` vs `!GetAtt`** — `!Ref` on a Lambda returns the function
  ARN; `!GetAtt` lets you pull individual attributes like
  `Arn`, `Role`, `CodeSha256`.

## Lecture

L64 declares the actual Lambda function. This is the core of the
stack — the compute that API Gateway will invoke.

### Anatomy of `AWS::Lambda::Function`

```yaml
GetObjectFunction:
  Type: AWS::Lambda::Function
  Properties:
    FunctionName: l64-get-object
    Runtime: python3.11
    Handler: get_object.lambda_handler
    Role: !Ref RoleArn
    Timeout: 15
    MemorySize: 256
    Environment:
      Variables:
        BUCKET_NAME: !Ref BucketName
    Code:
      S3Bucket: !Ref CodeAssetsBucket
      S3Key: lambdas/get_object.zip
```

Let's walk through each property.

#### Runtime

`Runtime: python3.11` picks the Python 3.11 micro-container. AWS
publishes a long list of supported runtimes; check
[the runtimes list](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html)
because Lambda deprecates them on a regular schedule. For this
course we standardize on `python3.11`.

#### Handler

`Handler: get_object.lambda_handler` means "import the file
`get_object.py` and call the function `lambda_handler`."

The handler signature is:

```python
def lambda_handler(event, context):
    ...
```

`event` is whatever API Gateway (or your other trigger source)
delivers. For our API Gateway proxy integration this is the
`AWS_PROXY` JSON shape. `context` carries runtime metadata
(request ID, deadline, log group name).

#### Role

`Role: !Ref RoleArn` — the function assumes this role when it
runs. In the full-stack template (L68) we will use
`!GetAtt LambdaExecutionRole.Arn`; here in the standalone template
we accept the role ARN as a parameter so the lecture stays
focused on the function itself.

#### Timeout and MemorySize

- `Timeout: 15` — the function gets up to 15 seconds per
  invocation before Lambda kills it.
- `MemorySize: 256` — 256 MB. The CPU share scales linearly with
  memory in Lambda. 128 MB is the floor; 256 MB is a sensible
  default for a small boto3 handler. You can dial this up later
  in production if you see CPU pressure.

#### Environment Variables

```yaml
Environment:
  Variables:
    BUCKET_NAME: !Ref BucketName
```

The runtime injects `BUCKET_NAME` into the handler's `os.environ`.
In `get_object.py` and `put_object.py` we read it with
`os.environ["BUCKET_NAME"]`.

**Never** put secrets in environment variables in plain text. Use
AWS Secrets Manager (and reference the secret ARN in an env var)
or — better — load them at runtime via the Secrets Manager SDK.

#### Code

There are three code-source options in CFN for Lambda:

| Source | Shape | When to use |
|---|---|---|
| Inline `ZipFile` | Up to ~4 KiB of source code as a string | Throwaway functions |
| Inline `S3Bucket` + `S3Key` | Hardcoded bucket + key | Small templates, fixed location |
| `CodeUri` processed by `aws cloudformation package` | Refer to a local path; CFN uploads + replaces with the packaged URL | **Production** |

For the full-stack template (template 06) we use option 3 — it is
the standard pattern because:

- The zip lives next to the template in your repo.
- `aws cloudformation package` uploads it to a "CFN assets" bucket
  and rewrites the template with the real S3 URL.
- It works for files of any size (up to the Lambda deployment
  package limit of 250 MB unzipped).

The standalone template `03_lambda_function.yaml` is laid out as
option 3, but pointed at an explicit bucket/key for clarity in the
lecture. In production the `package` command rewrites those
properties before deploy.

### Handler code: `get_object.py` and `put_object.py`

Both handlers live in `code/lambdas/`.

- `get_object.py` reads `event.pathParameters.proxy` to get the
  object key, calls `s3.get_object`, decodes the body as text
  for `.txt`/`.json`/`.md`/`.csv` extensions and base64 otherwise,
  and returns a JSON envelope `{"key","data"}`.
- `put_object.py` reads the same path parameter, decodes the
  request body (honoring `isBase64Encoded`), and writes the bytes
  to S3 with `s3.put_object`. Returns `{"key","etag","size"}`.
- Both return `400` when the key is missing, `404` when GET misses
  in S3, `500` for any other failure.

These are deliberately small functions — the goal is to read them
top-to-bottom in one sitting.

### Packaging the code

```bash
cd 13_cloudformation_serverless/code
mkdir -p lambdas_pkg
zip -j lambdas_pkg/get_object.zip lambdas/get_object.py
zip -j lambdas_pkg/put_object.zip lambdas/put_object.py
```

Then upload to a CFN assets bucket (any bucket you own):

```bash
ASSET_BUCKET=l64-code-assets-${AWS::AccountId}-${AWS::Region}
aws s3 mb s3://${ASSET_BUCKET} || true
aws s3 cp lambdas_pkg/ s3://${ASSET_BUCKET}/lambdas/ --recursive
```

In L68 you will see `aws cloudformation package` do the packaging
and upload in one step.

### Deploy

```bash
aws cloudformation package \
  --template-file templates/03_lambda_function.yaml \
  --s3-bucket ${ASSET_BUCKET} \
  --output-template-file /tmp/03.pkg.yaml

aws cloudformation deploy \
  --stack-name l64-sandbox \
  --template-file /tmp/03.pkg.yaml \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
      RoleArn=<paste from L63> \
      BucketName=<your bucket>
```

Tear down with `aws cloudformation delete-stack --stack-name l64-sandbox`.

### Invoke it for a smoke test

```bash
aws lambda invoke \
  --function-name l64-get-object \
  --payload '{"pathParameters":{"proxy":"hello.txt"}}' \
  /tmp/l64-out.json
cat /tmp/l64-out.json
```

You will see a 404 because the object does not exist yet. Use
`l64-put-object` to drop something in the bucket and try again.

## Hands-on

1. Zip both handlers with `zip -j lambdas_pkg/<name>.zip lambdas/<name>.py`.
2. Upload to an asset bucket.
3. Run `aws cloudformation package` against `03_lambda_function.yaml`.
4. Deploy the packaged template, passing the role ARN and bucket
   name as parameter overrides.
5. Invoke both functions with the AWS CLI and read the responses.
6. Tear the stack down.

## Quiz prep

- The three code-source options for `AWS::Lambda::Function`.
- The handler naming convention (`<filename>.<function_name>`).
- Why we never put secrets in `Environment.Variables`.
- Why `MemorySize` is a tuning knob (CPU scaling).
- Why `aws cloudformation package` uploads your local zip and
  rewrites the template.

## Further reading

- [`AWS::Lambda::Function` reference](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-lambda-function.html)
- [Lambda runtimes](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html)
- [AWS::Lambda::LayerVersion reference](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-lambda-layerversion.html)
- [AWS::Lambda::Permission reference](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-lambda-permission.html)
