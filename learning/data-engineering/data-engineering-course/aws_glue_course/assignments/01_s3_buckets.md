# Assignment 01 — S3 Buckets Hands-on

> **Section:** 3 (S3 + CLI)
> **Due:** End of week 1
> **Deliverable:** Screenshot of the 2 S3 buckets in the AWS console + the contents of each.

## Objective

Practice creating and using S3 buckets from both the AWS console and the AWS CLI. The deliverable proves you can:
- Create an S3 bucket with versioning + encryption + public-access-blocked.
- Configure the AWS CLI with IAM user credentials.
- Upload a file (the `city_temperature.csv` from the course downloads).

## Steps

1. **Create the source bucket** named `awsglueudemycourse-datasoup-gluejob2-source` (or your-own-name-source) in the AWS console.
   - Enable versioning.
   - Enable default encryption (SSE-S3, AES-256).
   - Block all public access.
2. **Create the target bucket** named `awsglueudemycourse-datasoup-gluejob1-target` (or your-own-name-target).
   - Same settings.
3. **Configure the AWS CLI** with an IAM user's access key + secret:
   ```
   aws configure
   # AWS Access Key ID: <paste>
   # AWS Secret Access Key: <paste>
   # Default region name: us-east-1
   # Default output format: json
   ```
4. **Upload the CSV**:
   ```
   aws s3 cp city_temperature.csv s3://<your-source-bucket>/input/
   ```
5. **Verify**:
   ```
   aws s3 ls s3://<your-source-bucket>/input/
   aws s3api get-bucket-versioning --bucket <your-source-bucket>
   aws s3api get-bucket-encryption --bucket <your-source-bucket>
   ```

## Acceptance criteria

- Both buckets exist in the AWS console.
- Versioning is `Enabled` on both.
- Encryption is `AES256` on both.
- Public access is `Blocked` on both.
- `city_temperature.csv` is in the `input/` prefix of the source bucket.
- You can run `aws s3 ls` against both buckets without errors.

## Stretch (optional, 30 min)

- Enable S3 server access logging on the source bucket, pointing to a third `logs/` bucket.
- Set up a lifecycle rule: transition objects older than 30 days to `STANDARD_IA`, and older than 90 days to `GLACIER`.
