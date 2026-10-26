# Section 3 Quiz — S3 Buckets Hands-on

> 5 questions, multi-choice, single answer. The answer key is at the bottom.

---

**Q1.** You are creating a new S3 bucket named `glue-source-data-2026` in the `eu-west-1` region using the AWS CLI. Which command is correct?

- A. `aws s3 mb s3://glue-source-data-2026`
- B. `aws s3api create-bucket --bucket glue-source-data-2026 --region eu-west-1 --create-bucket-configuration LocationConstraint=eu-west-1`
- C. `aws s3api create-bucket --bucket glue-source-data-2026 --region eu-west-1`
- D. `aws s3 mb s3://glue-source-data-2026 --region eu-west-1`

---

**Q2.** Versioning has been enabled on your source bucket. A teammate runs `aws s3 rm s3://glue-source-data-2026/city_temperature.csv` and the command succeeds. What actually happened, and how do you restore the file?

- A. The object is permanently deleted and cannot be recovered because versioning only protects against accidental overwrite, not deletion.
- B. A delete marker was placed on the object, hiding the current version. To restore it, delete the delete marker with `aws s3api delete-object --bucket glue-source-data-2026 --key city_temperature.csv --version-id <delete-marker-id>`.
- C. The current object version was removed and a new empty version was created. Run `aws s3 cp s3://glue-source-data-2026/city_temperature.csv ./` to re-download the empty version.
- D. S3 automatically moved the object to a `deleted/` prefix. Run `aws s3 cp s3://glue-source-data-2026/deleted/city_temperature.csv ./` to recover it.

---

**Q3.** The CloudFormation template for this course sets `BlockPublicAccess: true` on every bucket it creates. Why does AWS recommend leaving Block Public Access (BPA) enabled by default?

- A. Because BPA reduces S3 storage costs by compressing public objects.
- B. Because BPA forces all data to be encrypted with SSE-KMS, which is required for compliance.
- C. Because BPA overrides any bucket policy or ACL that would grant public access, preventing accidental data exposure even if a permissive policy is attached.
- D. Because BPA disables versioning on the bucket, which is required when data is publicly accessible.

---

**Q4.** The CFN template configures buckets with `SSEAlgorithm: AES256` (SSE-S3). Compared to SSE-KMS (`aws/kms`), what is the main trade-off?

- A. SSE-S3 provides stronger encryption than SSE-KMS and is therefore always preferred for regulated workloads.
- B. SSE-S3 is free and has no per-request cost, while SSE-KMS incurs charges per object uploaded/downloaded plus KMS key costs, but offers per-key audit trails in CloudTrail.
- C. SSE-S3 only encrypts objects larger than 1 MB; smaller objects are stored unencrypted.
- D. SSE-KMS uses AES-128, while SSE-S3 uses AES-256, so SSE-S3 is twice as strong.

---

**Q5.** You add a lifecycle rule to the source bucket that transitions objects to Glacier Flexible Retrieval after 90 days and expires (deletes) them after 365 days. A large multipart upload of `city_temperature_full.csv` is in progress and abandoned before completion. What does S3 do with the orphaned parts?

- A. They are kept indefinitely and continue to accrue storage charges until the bucket itself is deleted.
- B. They are automatically deleted by the `AbortIncompleteMultipartUpload` action when configured in the lifecycle rule (typically after a set number of days), stopping the storage charges.
- C. They are moved to Glacier along with completed objects on day 90.
- D. They block the lifecycle rule from running until the upload either completes or is manually aborted.

---

# Answer Key

1. **B** — `aws s3api create-bucket` with both `--region` and `--create-bucket-configuration LocationConstraint=<region>` is required for any region other than `us-east-1`. Option A (`s3 mb`) is incomplete because it omits the location constraint, and option C omits the location constraint. Option D uses `s3 mb` which does not accept a `--region` flag in the way shown.

2. **B** — With versioning enabled, a normal `s3 rm` creates a delete marker rather than removing the object permanently. Deleting the delete marker (by its specific version ID) restores the previous current version. Option A is wrong because versioning protects against deletion too. Option C misdescribes the behavior. Option D is not how S3 works.

3. **C** — Block Public Access is an account/bucket-level guardrail that overrides any bucket policy or ACL attempting to grant public access. This is the exact failure mode that caused major public S3 data leaks in the past. BPA does not affect encryption, versioning, or storage cost (eliminating A, B, and D).

4. **B** — SSE-S3 is free and has no per-request charges; SSE-KMS costs per request plus KMS key charges but provides per-key CloudTrail audit trails and customer-managed key control, which is often required for compliance (HIPAA, PCI, FedRAMP). Options A, C, and D are factually wrong — both use AES-256, and SSE-S3 does not skip small objects.

5. **B** — The `AbortIncompleteMultipartUpload` lifecycle action (configured in days, e.g. 7) deletes parts from multipart uploads that were never completed, preventing them from accruing storage charges forever. Option A is the problem this feature exists to solve. Options C and D are incorrect — lifecycle rules do not move incomplete parts, and a stalled upload does not block other lifecycle actions.
