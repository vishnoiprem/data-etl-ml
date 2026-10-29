---
l_id: L75
title: "Sign up for free trial (GCP)"
duration: "5:00"
prereqs:
  - L74 (Load JSON file (Azure))
---

# L75 — Sign up for free trial (GCP)

> **Section:** 10 — Loading from GCP
> **Duration:** 5:00

## Prereqs

- L74 — Load JSON file (Azure)

## Key terms

- **GCP project** — the unit of billing, permissions, and
  resource grouping. Every resource lives in exactly one
  project.
- **GCP free trial** — $300 credit for 90 days. The
  most generous of the three cloud providers.
- **Service account** — a non-human identity used by
  services (and Snowflake) to authenticate to GCP APIs.
- **IAM role (GCP)** — a named set of permissions. The
  least-privilege read-only role is `Storage Object
  Viewer`.
- **GCP region** — e.g. `us-central1` (Iowa). Pick the
  same region as your Snowflake account.

## Lecture

Final cloud provider in our multi-cloud pipeline. The
GCP free trial is the most generous of the three —
$300 of credit for 90 days, more than enough for every
demo in this section.

### Step 1 — sign up at cloud.google.com

1. Go to **https://cloud.google.com/free**.
2. Click **Get started for free** (or **Start free**).
3. Sign in with a Google account.
4. **Profile** — name, address, phone.
5. **Identity verification** — credit card required. The
   card is **not** charged; Google requires it for
   fraud prevention.
6. **Account type** — Individual for personal use.
7. **Tax info** — required for US accounts.
8. **Start free trial** — the $300 credit appears in the
   billing dashboard.

### Step 2 — enable MFA

GCP uses your Google account credentials. Enable MFA at
**https://myaccount.google.com/security**:

1. **2-Step Verification → Turn on**.
2. Use an authenticator app (Google Authenticator,
   Authy, 1Password).

### Step 3 — set up a budget alert

1. **Billing → Budgets & alerts → Create budget**.
2. **Amount**: $1 (you have $300; $1 is a safety net for
   misconfigurations).
3. **Alert thresholds**: 50%, 80%, 100%.
4. **Email recipients**: your address.

### Step 4 — install the gcloud CLI

```bash
# macOS
brew install --cask google-cloud-sdk

# or via the installer
curl https://sdk.cloud.google.com | bash

# initialize
gcloud init
gcloud auth login
gcloud config set project <project-id>
```

`gcloud init` opens a browser for OAuth. After login,
pick the project you created in step 1.

### Step 5 — pick a region

For the rest of section 10 we use **`us-central1`**
(Iowa). Pick the **same region** as your Snowflake
account. If your Snowflake account is on GCP, the
in-region access is free. If your Snowflake account is
on AWS or Azure, there's a small cross-cloud egress
cost — negligible on the free trial.

### What the GCP free trial includes

| Service | Free tier |
|---|---|
| Cloud Storage (Standard) | 5 GB / month |
| Compute Engine | 1 f1-micro instance / month |
| BigQuery | 1 TB of queries / month |
| Cloud Functions | 2 M invocations / month |

The 5 GB of Cloud Storage is enough for the entire
section.

### Why GCS is the right place for "data we share with
Snowflake"

Three reasons:

- **Cheap.** Standard storage is ~$0.020/GB/month;
  Nearline is ~$0.010/GB/month.
- **Snowflake integrates natively.** Storage integrations
  (L77) let Snowflake read from GCS without service
  account keys in SQL.
- **Multi-regional replication.** GCS can automatically
  replicate data across regions for redundancy.

### Common sign-up mistakes

- **Picking the wrong project.** GCP lets you create
  many projects; use a dedicated one for this course.
- **Forgetting the budget alert.** A misconfigured GCS
  lifecycle policy can balloon storage costs silently.
- **Reusing a work email.** If you leave the company,
  you lose the GCP project. Use a personal Google
  account.

## Hands-on

Sign up, install `gcloud`, run `gcloud init`, run
`gcloud config list`. The output should show your
project ID and the active account.

## Quiz prep

- What is a GCP project?
- How much free credit does the GCP free trial give?
- Why pick the same GCP region as your Snowflake account?

## Key takeaways

- The GCP free trial is **$300 for 90 days** + 5 GB
  Cloud Storage.
- Always **enable MFA** and **set a budget alert** before
  creating resources.
- Pick the **same region** as your Snowflake account.
- Use a dedicated GCP project for the course so cleanup
  is one command.

## What's next

In **L76 — Create a bucket (GCS)** we create the GCS
bucket that will hold our GCP-side orders data.