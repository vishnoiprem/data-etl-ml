---
l_id: L68
title: "Sign up for free trial (Azure)"
duration: "5:00"
prereqs:
  - L67 (Handle JSON (S3))
---

# L68 — Sign up for free trial (Azure)

> **Section:** 9 — Loading from Azure
> **Duration:** 5:00

## Prereqs

- L67 — Handle JSON (S3)

## Key terms

- **Azure account** — a billing entity in Azure, scoped to
  an Azure AD tenant.
- **Azure AD tenant** — the directory that holds users,
  groups, and applications. Every Azure subscription lives
  in exactly one tenant.
- **Free trial** — $200 credit for 30 days, plus 12 months
  of select free services.
- **Owner role** — the highest-privilege role on a
  subscription. Use a less-privileged role for day-to-day
  work.
- **Azure CLI** — `az`, the equivalent of AWS CLI.

## Lecture

For section 9 we move from S3 to **Azure Blob Storage**.
To do that you need an Azure account. The free trial
includes $200 of credit for 30 days — more than enough
for every demo in this section.

### Step 1 — sign up at azure.microsoft.com

1. Go to **https://azure.microsoft.com/free**.
2. Click **Start free**.
3. Sign in with a Microsoft account (or create one).
4. Enter your **profile** — name, email, phone.
5. **Identity verification** by phone or card.
6. **Payment** — credit card required. The card is **not
   charged** during the trial; Azure asks for it to prevent
   fraud.
7. **Agreement** — accept the subscription agreement.
8. **Portal** — you'll land in the Azure Portal at
   portal.azure.com.

### Step 2 — turn on MFA

The free trial account uses your Microsoft account
credentials. Enable MFA on the Microsoft account:

1. **https://account.microsoft.com/security**.
2. **Advanced security options → Two-step verification**.
3. Use an authenticator app.

### Step 3 — set up a budget

1. **Cost Management + Billing → Budgets → Add**.
2. **Budget amount**: $1 (you have $200 of credit; $1 is a
   safety net for misconfigurations).
3. **Alert conditions**: 50%, 80%, 100% of the budget.
4. **Email recipients**: your address.

### Step 4 — install the Azure CLI

```bash
# macOS
brew install azure-cli

# or via the installer
curl -L https://aka.ms/InstallAzureCli | bash

# verify
az --version
```

```bash
az login
# A browser window opens; sign in.
az account show
# { "name": "Free Trial", "id": "..." }
```

### Step 5 — pick a region

For the rest of section 9 we'll use **`eastus`** (US East,
Virginia). Pick the **same** region as your Snowflake
account. If your Snowflake account is on AWS, the cross-cloud
egress is a small cost — for the free trial it's negligible.

If your Snowflake account is hosted on Azure (Snowflake
supports AWS, Azure, and GCP deployments), pick the **same
region** as the account for free cross-region access.

### What the free trial includes

| Service | Free tier |
|---|---|
| Azure Blob Storage (LRS, hot) | 5 GB / month for 12 months |
| Azure Functions | 1 M executions / month |
| Azure AD | unlimited users |

The 5 GB of Blob Storage is enough for the entire section.

### Why we use Azure Blob Storage (and not Data Lake Gen2)

Two storage options in Azure:

- **Blob Storage** — flat object store, like S3.
- **Data Lake Gen2** — Blob Storage with a hierarchical
  namespace (folders are first-class, not just key
  prefixes).

For Snowflake's storage integration, **Blob Storage** is the
supported path. Data Lake Gen2 has a different access model
and isn't directly compatible.

### Common sign-up mistakes

- **Picking the wrong tenant.** If you have a work account,
  Azure might create a new tenant under it. Use a personal
  Microsoft account.
- **Forgetting the budget alert.** Same as AWS: a
  misconfigured storage account can bill you silently.
- **Using the wrong region.** The region you pick at sign-up
  is the **default** for new resources, but you can create
  resources in any region.

## Hands-on

Sign up, install `az`, run `az login`, run `az account show`.
Confirm the output shows your subscription name and ID.

## Quiz prep

- What is the difference between an Azure subscription and
  an Azure AD tenant?
- How much free credit does the Azure free trial give?
- Why pick the same Azure region as your Snowflake account?

## Key takeaways

- The Azure free trial is **$200 for 30 days** + 5 GB
  Blob Storage for 12 months.
- Always **enable MFA** and **set a budget alert** before
  creating resources.
- Pick the **same region** as your Snowflake account.
- Use **Blob Storage** (not Data Lake Gen2) for the
  Snowflake integration.

## What's next

In **L69 — Create a storage account** we create the
storage account that will hold our Azure-side orders data.