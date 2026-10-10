# Section 2 — IAM / KMS / SNS (Lectures L13-L19)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
>
> This file bundles 7 lecture scripts (L13-L19) for Section 2. The Udemy-upload version of each will be split into its own file before launch.

---

## L13 — Section Overview (0:47)

> "Section 2 covers the AWS S3 and the AWS CLI — the storage layer for every Glue pipeline. S3 is where your source data lives, where your Glue Job script lives, and where your output Parquet lives. The CLI is how you'll upload, download, and inspect S3 from your terminal. By the end of this section, you'll have 2 S3 buckets created and the `city_temperature.csv` uploaded to the source bucket."

Deliverables: 2 buckets, 1 uploaded file, CLI configured.

---

## L14 — AWS S3 101 (3:43)

> "S3 is object storage. The 3 concepts you need: buckets (top-level container, globally unique name), objects (the files), and keys (the path within the bucket, e.g., `input/city_temperature.csv`). S3 is *eventually consistent* for overwrite and delete — there's a small window where a newly-uploaded object might not be visible to a read in a different region. S3 storage classes: Standard (frequent access), Standard-IA (infrequent, 30-day minimum), Glacier (archive, minutes-to-hours retrieval), Glacier Deep Archive (cheapest, 12-hour retrieval). S3 security: bucket policies (resource-based), IAM policies (identity-based), ACLs (legacy, avoid), Block Public Access (the safety net). S3 encryption: SSE-S3 (AES-256, default, no cost), SSE-KMS (uses KMS, costs per request), SSE-C (customer-provided keys, rare)."

Key bullets: buckets / objects / keys; storage classes; security model; encryption options.

---

## L15 — AWS CLI 101 (3:15)

> "The AWS CLI is the command-line tool for AWS. Install with `pip install awscli` or download the installer. The 2 commands you'll use most: `aws s3` (file operations) and `aws cloudformation` (stack operations). The 3 subcommands of `aws s3` you need: `cp` (copy), `ls` (list), `sync` (mirror a directory). The 3 subcommands of `aws cloudformation`: `create-stack`, `update-stack`, `delete-stack`. Always use `--region us-east-1` explicitly — the CLI's default region is set in `~/.aws/config` but it's a common source of bugs."

Key bullets: install; `aws s3 cp/ls/sync`; `aws cloudformation create/update/delete`; always specify region.

---

## L16 — Configuring AWS CLI using IAM User Credentials (3:22)

> "To use the CLI, you need to configure credentials. Run `aws configure`. You'll be prompted for: AWS Access Key ID, AWS Secret Access Key, Default region name, Default output format. The access key + secret come from the IAM user you created in Lecture L6. The region should be the region where your AWS resources live (us-east-1 for this course). The output format: `json` (default, machine-readable), `text`, or `table` (human-readable). The credentials are stored in `~/.aws/credentials`; the config (region, output) is stored in `~/.aws/config`. **Never check these files into git** — add `~/.aws/` to `.gitignore`."

Lab: `aws configure`, then `aws sts get-caller-identity` to verify.

---

## L17 — AWS CloudFormation 101 (4:41)

> "CloudFormation is the AWS service for infrastructure-as-code. You write a template (YAML or JSON) that declares the AWS resources you want. CloudFormation reads the template and creates the resources in the right order, with the right dependencies, and tears them down cleanly when you delete the stack. The 4 sections of a template: Parameters (user inputs), Mappings (static lookup tables), Resources (the actual AWS resources to create, the only required section), Outputs (values to export). The 4 key intrinsic functions: `!Ref` (reference a parameter or resource), `!Sub` (string substitution), `!GetAtt` (get an attribute of a resource), `!Join` (join strings). CloudFormation is *idempotent* — re-running with no changes is a no-op. CloudFormation is *declarative* — you describe the end state, not the steps."

Key bullets: 4 sections; 4 functions; idempotent; declarative.

---

## L18 — Create S3 Bucket (3:00 lab)

Lab: create the source bucket `awsglueudemycourse-datasoup-gluejob2-source` in the AWS console. Steps: S3 → Create bucket → name (must be globally unique) → region (us-east-1) → Block all public access → enable versioning → enable default encryption (SSE-S3) → Create.

---

## L19 — Optional Assignment: Create S3 Bucket for GlueJob1 Target (3:00 assignment)

> "Repeat the same steps for the target bucket. Name it `awsglueudemycourse-datasoup-gluejob1-target`. Same settings: block public access, versioning enabled, SSE-S3 encryption. This is the bucket that the Glue Job will write Parquet output to."

Deliverable: a screenshot of both buckets in the console.

---

## Section 2 Quiz

5 questions, see `quizzes/section_2.md`.
