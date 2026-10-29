---
l_id: L71
title: "Create integration object (Azure)"
duration: "8:00"
prereqs:
  - L70 (Create a container)
---

# L71 — Create integration object (Azure)

> **Section:** 9 — Loading from Azure
> **Duration:** 8:00

## Prereqs

- L70 — Create a container

## Key terms

- **Azure AD application** — an identity in Azure AD that
  can be granted permissions to storage accounts.
- **Service principal** — the "instance" of an application
  in a specific tenant. Has a client ID and a client
  secret.
- **Storage Blob Data Reader** — the Azure RBAC role that
  grants read access to blobs.
- **`AZURE_TENANT_ID`** — the Azure AD tenant ID. Snowflake
  uses it to look up the service principal.

## Lecture

For Azure, the storage integration is a Snowflake object
that references an **Azure AD service principal** with
**Storage Blob Data Reader** on the storage account. The
service principal authenticates to Azure AD; Snowflake
uses the credentials transparently.

### Step 1 — register an Azure AD application

```bash
az ad app create \
    --display-name snowflake-sf-course \
    --sign-in-audience AzureADMyOrg
```

Returns JSON with the `appId` (this is the **client ID**).
Save it as `AZURE_CLIENT_ID`.

### Step 2 — create a service principal for the app

```bash
az ad sp create \
    --id <appId from step 1>
```

Returns JSON with the `objectId` (the service principal's
ID). Save it as `AZURE_PRINCIPAL_ID`.

### Step 3 — create a client secret

```bash
az ad app credential reset \
    --id <appId from step 1> \
    --append \
    --display-name snowflake-secret
```

Returns JSON with the `password` field. **Save it now** —
this is the only time it will be visible. Save it as
`AZURE_CLIENT_SECRET`.

### Step 4 — grant Storage Blob Data Reader

```bash
STORAGE_PRINCIPAL_ID=$(az storage account show \
    --name pvsfcourse2026 \
    --resource-group snowflake-course-rg \
    --query identity.principalId \
    --output tsv)

# If the storage account has no managed identity, skip and use the storage account's resource ID:
STORAGE_RESOURCE_ID=$(az storage account show \
    --name pvsfcourse2026 \
    --resource-group snowflake-course-rg \
    --query id \
    --output tsv)

az role assignment create \
    --assignee <AZURE_PRINCIPAL_ID> \
    --role "Storage Blob Data Reader" \
    --scope $STORAGE_RESOURCE_ID
```

`Storage Blob Data Reader` is the least-privilege role:
read blobs and list containers, nothing more.

### Step 5 — retrieve the tenant ID

```bash
az account show --query tenantId --output tsv
```

Save as `AZURE_TENANT_ID`.

### Step 6 — create the Snowflake storage integration

```sql
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE STORAGE INTEGRATION azure_orders_int
    TYPE = EXTERNAL_STAGE
    STORAGE_PROVIDER = 'AZURE'
    ENABLED = TRUE
    AZURE_TENANT_ID = '<AZURE_TENANT_ID>'
    STORAGE_ALLOWED_LOCATIONS = (
        'azure://pvsfcourse2026.blob.core.windows.net/orders/raw/'
    );
```

Note: the URL uses `azure://` (not `https://`). Snowflake
parses the URL to extract the account, container, and path.

### Step 7 — retrieve the consent URL

```sql
DESC INTEGRATION azure_orders_int;
```

Output (truncated):

| property | property_value |
|---|---|
| `AZURE_CONSENT_URL` | `https://login.microsoftonline.com/...` |
| `AZURE_MULTI_TENANT_APP_NAME` | `snowflake-sf-course` |

The `AZURE_CONSENT_URL` must be opened by an Azure AD
admin and approved. Until approval, the integration
**cannot** read from the storage account.

### Step 8 — approve the consent

Open the `AZURE_CONSENT_URL` in a browser. Sign in as the
Azure AD admin. Click **Accept**. The consent grants the
service principal the right to act on behalf of users in
the tenant.

### Step 9 — verify the integration

```sql
LIST @<stage> -- not yet, the stage is in L72
```

Or check that the integration is enabled:

```sql
SHOW INTEGRATIONS LIKE 'azure_orders_int';
```

Look for `enabled = true` and `type = EXTERNAL_STAGE`.

### Why consent matters

Without the admin consent, the service principal has
**no** actual permission to read blobs, even if you
granted it `Storage Blob Data Reader`. Consent is a
**tenant-level** approval that the service principal is
allowed to act in this tenant at all. It's a one-time
step.

### Comparison: AWS vs Azure integration

| Step | AWS | Azure |
|---|---|---|
| Identity | IAM role | Azure AD app + service principal |
| Permission grant | IAM policy | Azure RBAC role (`Storage Blob Data Reader`) |
| Cross-tenant | External ID | Tenant consent URL |
| URL scheme | `s3://` | `azure://` |
| Bridge object | `STORAGE INTEGRATION` | `STORAGE INTEGRATION` (same!) |

The Snowflake object is the same; the underlying
identity and permission model is different.

## Hands-on

Run steps 1–7. Visit the consent URL and approve. Run
`SHOW INTEGRATIONS LIKE 'azure_orders_int';` to confirm
the integration is enabled.

## Quiz prep

- What is the difference between an Azure AD app and a
  service principal?
- Why do you need to approve the consent URL?
- What is the equivalent Azure RBAC role of the IAM
  `s3:GetObject` action?

## Key takeaways

- An Azure AD **app** + **service principal** is the
  identity Snowflake assumes.
- Grant **`Storage Blob Data Reader`** on the storage
  account (least privilege).
- The **consent URL** must be approved once by an
  Azure AD admin.
- The `STORAGE INTEGRATION` is otherwise identical in
  shape to the S3 one.

## What's next

In **L72 — Create stage & test connection (Azure)** we
create the external stage pointing at the Azure
container and run a test `LIST`.