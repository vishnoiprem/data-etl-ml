# L62 — AWS CloudFormation — S3 Bucket

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 13
> **Duration target:** 6:25
> **Lecture ID:** L62

## Prereqs

- L60 (CFN basics).
- AWS CLI configured for a single region (we use `us-east-1` in
  examples; substitute your region).

## Key terms

- **`AWS::S3::Bucket`** — the CFN resource type for an S3 bucket.
- **`BucketName`** — optional property. If omitted, CFN generates a
  globally-unique name (suitable for production). If supplied, the
  value must be globally unique across all of AWS.
- **`VersioningConfiguration`** — enables or suspends object
  versioning on the bucket.
- **`BucketEncryption`** — sets the default SSE algorithm (AES256 or
  `aws:kms`).
- **`PublicAccessBlockConfiguration`** — the four boolean knobs
  (account + bucket level) that shut off accidental public access.
- **`UpdateReplacePolicy` / `DeletionPolicy`** — control what happens
  to objects when you update or delete the stack.

## Lecture

L62 covers the only S3 resource type we use in this section:
`AWS::S3::Bucket`. The full-stack template (L68) uses the exact
same property block — what we build here is what we will re-use
later.

### The minimal-but-correct shape

A "we will use this for real" S3 bucket in CloudFormation has four
property blocks:

1. `BucketName` — explicit name so your application code can
   reference it. Optional but very common in IaC.
2. `VersioningConfiguration` — turn on versioning so a bad
   `PutObject` cannot destroy a previous good version.
3. `BucketEncryption` — default SSE-S3 (`AES256`) at minimum.
   Choose SSE-KMS if you need a customer-managed CMK.
4. `PublicAccessBlockConfiguration` — flip all four booleans to
   `true` and you have effectively closed the door to public
   access. This is **always** a default for any new bucket.

### Reading the template

The standalone template for this lecture is
`code/templates/01_minimal_s3_bucket.yaml`. Let's walk through it.

```yaml
Resources:
  MinimalBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: l62-minimal-bucket-example
      VersioningConfiguration:
        Status: Enabled
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      Tags:
        - Key: lecture
          Value: L62
        - Key: course
          Value: aws-lambda-serverless
```

#### A note on `BucketName`

`BucketName` must be globally unique across all AWS customers. The
name `l62-minimal-bucket-example` will fail to deploy if anyone
else has used it. For real stacks either:

- omit `BucketName` and let CFN generate one, then read the output
  with `!GetAtt MyBucket` and pass it to downstream resources; or
- include an environment prefix (`prod-`, `staging-`, etc.) plus
  the account ID.

In L69 we turn `BucketName` into a `Parameter` so each environment
gets its own bucket.

#### Public access block

The four booleans together effectively close all public pathways:

- `BlockPublicAcls` — refuses `public-read` / `public-read-write`
  ACLs on new objects.
- `IgnorePublicAcls` — ignores existing public ACLs.
- `BlockPublicPolicy` — refuses bucket policies that grant public
  access.
- `RestrictPublicBuckets` — refuses cross-account public access.

If you genuinely need a static website bucket, you flip these to
`false` plus add a bucket policy granting `s3:GetObject` to
`Principal: "*"`. We do not need to do that for this use case.

### Outputs

The template exposes three outputs:

```yaml
Outputs:
  BucketName:
    Value: !Ref MinimalBucket
  BucketArn:
    Value: !GetAtt MinimalBucket.Arn
  BucketDomainName:
    Value: !GetAtt MinimalBucket.DomainName
```

`!Ref` on a bucket returns the **bucket name** (this is the
historical quirk; for most resource types `!Ref` returns the
resource ID, but for S3 it returns the bucket name). For the ARN
you use `!GetAtt`.

### Validate and deploy

```bash
cd 13_cloudformation_serverless/code

# Sanity-check the template syntax.
aws cloudformation validate-template \
  --template-body file://templates/01_minimal_s3_bucket.yaml

# Deploy it. CAPABILITY_IAM is not strictly needed here (no IAM
# resources) but we add it in 02+.
aws cloudformation deploy \
  --stack-name l62-sandbox \
  --template-file templates/01_minimal_s3_bucket.yaml

# Read the bucket name back.
aws cloudformation describe-stacks \
  --stack-name l62-sandbox \
  --query "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue" \
  --output text
```

When you are done:

```bash
aws cloudformation delete-stack --stack-name l62-sandbox
```

### Upgrade hooks you should know

- `UpdateReplacePolicy: Retain` — keep the bucket (and any objects
  in it) if the stack is deleted or replaced. Use this for buckets
  that hold production data.
- `DeletionPolicy: Delete` — default. CloudFormation deletes the
  bucket. If the bucket is non-empty the delete fails unless you
  also set `Delete` policies on every object version.

## Hands-on

1. Edit `templates/01_minimal_s3_bucket.yaml` and change
   `BucketName` to something with your initials in it
   (e.g. `pv-l62-test`).
2. `aws cloudformation validate-template ...` — must say
   `Parameters: []`.
3. `aws cloudformation deploy ...` — must say
   `Successfully created/updated stack`.
4. `aws s3 ls` — confirm your bucket exists.
5. `aws cloudformation delete-stack --stack-name l62-sandbox`.

## Quiz prep

- The four property blocks of a "production-shaped" S3 bucket in CFN.
- The four `PublicAccessBlockConfiguration` booleans and what they
  each do.
- Why `!Ref` on a bucket returns the bucket name, not the bucket
  ARN.
- The difference between `UpdateReplacePolicy` and `DeletionPolicy`.

## Further reading

- [`AWS::S3::Bucket` reference](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-s3-bucket.html)
- [S3 Block Public Access documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html)
