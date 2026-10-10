---
l_id: L05
title: Sign up for free trial
duration: "6:00"
prereqs: ["L04"]
downloads:
  - "../../downloads/snowflake_cheat_sheet.pdf"
---

# L05 — Sign Up for the Free Trial

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 2 — Getting Started
> **Duration:** ~6:00

## Prereqs

L01–L04. This is the first hands-on lecture — you'll need a web
browser and an email address you can verify.

## Key terms

- **Free trial** — Snowflake's 30-day trial with **$400 of
  credits**, available on AWS, Azure, or GCP.
- **Account admin** — the first user you create; automatically
  granted the `ACCOUNTADMIN` system role. This is the only
  identity that can perform account-level operations.
- **Org** — your company's tenant in Snowflake. A free trial
  creates a single-account org; production deployments typically
  have multiple accounts (prod, dev, test) under one org.
- **Edition** — Standard, Enterprise, Business Critical, VPS,
  or higher. The free trial starts on **Enterprise** edition, which
  unlocks most features including Multi-cluster Warehouses, up to
  90-day Time Travel, and materialized views.

## Lecture

In this lecture we sign up for the Snowflake free trial. By the
end of the lecture you should have a working account URL, a
verified email, and a successful first login.

### Step 1 — Pick a cloud and region

Go to <https://signup.snowflake.com/>. The first thing the wizard
asks is your preferred cloud and region:

- **AWS** — most regions; most third-party integrations; most
  Marketplace data.
- **Azure** — if your data lives in Azure Blob / Data Lake / ADLS.
- **GCP** — if your data lives in GCS or BigQuery.

If you don't have a strong preference, **AWS / us-west-2
(Oregon)** is the safest default — most features land there
first, and the labs in this course are tested against it.

### Step 2 — Account details

Pick a unique account name. It becomes part of your Snowflake
URL:

```text
https://<account_name>.<region>.snowflakecomputing.com
```

For example, `https://abc12345.us-west-2.snowflakecomputing.com`.

> **Account names are immutable.** If you pick
> `pvishnoi-trial`, that's the URL your collaborators and BI
> tools will use forever. Choose something you'll still be
> happy with in 12 months.

### Step 3 — User details

Snowflake asks for an email, a username, and a password. The
**first user becomes the account admin** with the
`ACCOUNTADMIN` role — treat those credentials like root
credentials on any cloud.

### Step 4 — Verify and log in

You'll receive a verification email. Click the link, set a
password, and you'll land in the Snowflake UI at
`snowflakecomputing.com`.

### Step 5 — First query

In the UI, click **Worksheets** → **+ Worksheet** and run:

```sql
SELECT CURRENT_VERSION(),
       CURRENT_ACCOUNT(),
       CURRENT_USER(),
       CURRENT_ROLE();
```

You should see a single row with your Snowflake version
(7.x or higher in late 2024+), your account name, your
username, and `ACCOUNTADMIN` as the role.

### Trial gotchas

- **Auto-suspend default is 60s** — warehouses will spin down
  automatically; you are not billed when they are paused.
- **Auto-resume** — running a query against a suspended
  warehouse automatically resumes it. First query may take
  1–2 seconds longer while compute spins up.
- **Credit budget** — $400 buys roughly 200 hours of an
  X-Small warehouse running flat-out, or ~20 hours of a
  Large. Section 3 covers sizing.

## Hands-on

```sql
-- After signing up, run this in a worksheet:
USE ROLE ACCOUNTADMIN;
SELECT CURRENT_REGION(), CURRENT_ACCOUNT_NAME();
SHOW WAREHOUSES;
```

You should see one auto-created warehouse named
`COMPUTE_WH` (X-Small, auto-suspend 60s).

## Quiz prep

For this lecture, focus on the **setup** questions:

- How long is the free trial and what is the credit budget?
  (30 days, $400)
- What edition does the trial start on? (Enterprise)
- What role does the first user get? (ACCOUNTADMIN)

## What's next

Next up is **L06 — Getting to know the interface**, where we
tour the Snowflake UI: worksheets, databases, warehouses, and
the new Snowsight interface.
