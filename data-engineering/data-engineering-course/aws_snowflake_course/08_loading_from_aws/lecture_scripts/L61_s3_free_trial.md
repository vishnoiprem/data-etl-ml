---
l_id: L61
title: "Sign up for free trial (S3)"
duration: "5:00"
prereqs:
  - L60 (Clustering - Practice)
---

# L61 — Sign up for free trial (S3)

> **Section:** 8 — Loading from AWS
> **Duration:** 5:00

## Prereqs

- L60 — Clustering — Practice

## Key terms

- **AWS account** — a billing entity in AWS. The free tier
  gives 12 months of access to many services including S3.
- **Root user** — the email address that owns the account. Has
  unrestricted access; should be MFA-protected.
- **IAM user** — a non-root identity with scoped permissions.
  Always use IAM users, never the root, for day-to-day work.
- **S3 free tier** — 5 GB of standard storage, 20 000 GET
  requests, 2 000 PUT requests per month, for 12 months.

## Lecture

For section 8 we move from **internal stages** (Snowflake's
own storage) to **S3** (AWS's object storage). To do that you
need an AWS account. The free tier is enough for every demo
in this section; you will not be charged.

### Step 1 — sign up at aws.amazon.com

1. Go to **https://aws.amazon.com**.
2. Click **Create an AWS Account**.
3. Enter a **root user email** — use a personal email, not
   a work email. This is the address that owns the account.
4. Set the **account name** (e.g. `snowflake-course-2026`).
5. **Contact information** — fill in real info. AWS validates
   the phone number.
6. **Payment** — credit card. The free tier doesn't charge
   it for the first 12 months, but the card is required for
   verification.
7. **Identity verification** — phone call or SMS.
8. **Support plan** — pick **Basic (Free)**. The other plans
   are $29+/month and unnecessary for this course.

### Step 2 — turn on MFA for the root user

**This is non-negotiable.** The root user has full access to
your account. Without MFA, a leaked password can drain your
bank account in an hour.

1. **IAM → Dashboard → Activate MFA on your root user**.
2. Use a virtual MFA app (Google Authenticator, Authy, 1Password).
3. Save the recovery codes somewhere safe.

### Step 3 — create an IAM user for day-to-day work

Don't use the root user for anything except account-level
admin. Create an IAM user with the permissions you need.

1. **IAM → Users → Add user**.
2. **User name**: `snowflake-demo`.
3. **Access type**: **Programmatic access** + **AWS Management
   Console access**.
4. **Permissions**: attach `AdministratorAccess` for the
   course (you can scope it down later). For a production
   account, never grant `AdministratorAccess`; use least
   privilege.
5. **Tags**: add `Project = snowflake-course` so this user
   is easy to find later.
6. **Review + create**. **Save the access key ID and secret
   access key** — the secret is shown only once.

### Step 4 — set up the AWS CLI

```bash
pip install awscli
aws configure
# AWS Access Key ID: AKIA…
# AWS Secret Access Key: …
# Default region: us-east-1
# Default output format: json
```

`aws configure` writes the credentials to `~/.aws/credentials`.
You can now use `aws s3 ls` to verify.

### Step 5 — verify the free tier

1. **AWS → Billing → Free tier** — you should see a usage
   dashboard.
2. **AWS → Budgets → Create budget** — set a $1 budget with
   an email alert at 50% / 80% / 100%. This is your safety
   net; AWS does not warn before charging your card.

### Why S3 is the right place for "data we share with
Snowflake"

Three reasons:

- **Persistent and replicated.** S3 stores 11 9s of
  durability.
- **Cheap.** Standard storage is ~$0.023/GB/month; the
  infrequent-access tier is even less.
- **Snowflake integrates natively.** Storage integrations
  (covered in L65) let Snowflake read from S3 without
  embedding AWS keys in SQL.

The rest of section 8 is building that integration.

### Common sign-up mistakes

- **Picking a paid support plan.** Always **Basic (Free)**.
- **Forgetting to enable MFA.** A leaked root password
  can run up a five-figure bill in hours.
- **Skipping the budget alert.** A misconfigured S3
  lifecycle policy can balloon storage costs silently.
- **Reusing a work email** as the root user. If you leave
  the company, you lose the account. Use a personal email.

## Hands-on

Sign up, enable MFA, create the IAM user, run
`aws configure`, run `aws s3 ls` to confirm. The output
should be an empty list (no buckets yet) — that's correct,
you haven't created one.

## Quiz prep

- What is the difference between the AWS root user and an IAM
  user?
- What is the S3 free tier allowance for the first 12 months?
- Why is the **Basic** support plan the right choice for this
  course?

## Key takeaways

- Always **enable MFA** on the root user.
- Use an **IAM user** for day-to-day work, never the root.
- The S3 free tier is 5 GB / month for 12 months — more than
  enough for this course.
- **Set a budget alert** before you create any resources.

## What's next

In **L62 — Creating S3 bucket** we create the bucket that
will hold our orders data and configure it for Snowflake
access.