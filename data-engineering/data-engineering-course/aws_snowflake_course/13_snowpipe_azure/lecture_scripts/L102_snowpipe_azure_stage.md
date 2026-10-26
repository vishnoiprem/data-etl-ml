---
l_id: L102
title: Create stage & storage integration
duration: "9:00"
prereqs: ["L101 - High-level steps (Snowpipe Azure)"]
---

# L102 — Create stage & storage integration

> **Author:** Prem Vishnoi &lt;pvishnoi&commat;avilx.com&gt;
> **Section:** 13 — Snowpipe for Azure
> **Duration:** 9:00

## Prereqs

An Azure storage account, a container, and a service principal
(app registration) with `Storage Blob Data Contributor` on the
container.

## Lecture

This lecture covers steps 1–3 of the Azure Snowpipe plan: cloud
side, storage integration, and the stage.

### Step 1 — Azure side

```bash
# Variables
RG=snowflake-demo-rg
ACCT=snowflakedemostorage
CONTAINER=orders
LOCATION=eastus2

# Create the resource group
az group create -n $RG -l $LOCATION

# Create the storage account
az storage account create \
  -n $ACCT \
  -g $RG \
  -l $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2

# Create the container
az storage container create \
  -n $CONTAINER \
  --account-name $ACCT
```

The container URI is `https://<ACCT>.blob.core.windows.net/<CONTAINER>/`.

### Step 2 — Service principal

```bash
# Create the app registration
APP_ID=$(az ad app create --display-name snowflake-snowpipe-demo \
  --sign-in-audience AzureADMyOrg --query appId -o tsv)

# Create the service principal
SP_ID=$(az ad sp create --id $APP_ID --query id -o tsv)

# Grant Storage Blob Data Contributor on the container
az role assignment create \
  --assignee $SP_ID \
  --role "Storage Blob Data Contributor" \
  --scope "/subscriptions/<sub-id>/resourceGroups/$RG/providers/Microsoft.Storage/storageAccounts/$ACCT/blobServices/default/containers/$CONTAINER"
```

Note the **object ID** and the **tenant ID**:

```bash
TENANT_ID=$(az account show --query tenantId -o tsv)
echo "APP_ID=$APP_ID"
echo "TENANT_ID=$TENANT_ID"
```

### Step 3 — Storage integration in Snowflake

```sql
USE ROLE ACCOUNTADMIN;

CREATE STORAGE INTEGRATION azure_snowpipe_int
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'AZURE'
  ENABLED = TRUE
  AZURE_TENANT_ID = '<tenant-id>'
  STORAGE_ALLOWED_LOCATIONS = (
    'azure://snowflakedemostorage.blob.core.windows.net/orders/'
  );

-- Get the consent URL the Azure admin must click
DESC STORAGE INTEGRATION azure_snowpipe_int;
```

The output has two columns you need:

- `AZURE_CONSENT_URL` — a `login.microsoftonline.com` URL.
- `AZURE_MULTI_TENANT_APP_NAME` — the display name Snowflake
  uses for its app in your tenant.

### Step 4 — Grant consent

Send the consent URL to the Azure admin (or open it yourself if
you have the rights). Click "Accept". This grants Snowflake's
service principal the `Storage Blob Data Reader` role on the
tenant.

### Step 5 — Create the stage

```sql
USE SCHEMA raw;

CREATE OR REPLACE STAGE azure_stage
  STORAGE_INTEGRATION = azure_snowpipe_int
  URL = 'azure://snowflakedemostorage.blob.core.windows.net/orders/'
  FILE_FORMAT = (TYPE = CSV FIELD_DELIMITER = ',' SKIP_HEADER = 1);

-- Test
LIST @raw.azure_stage;
```

You should see the files you uploaded to the container. If
`LIST` returns zero rows, the consent grant didn't propagate
yet — wait 30–60 seconds and retry.

### Common gotchas

- **Wrong region.** Snowflake on `eastus2` cannot use a storage
  account in `westus2` *unless* you whitelist it via
  `AZURE_CONSENT_URL` and cross-tenant consent. Easier: keep
  storage and Snowflake in the same region.
- **Wrong role on the container.** The Snowflake service
  principal needs `Storage Blob Data Reader` *and* `Storage Blob
  Delegator` to enumerate blobs in some subscription tiers.
- **Container path case-sensitivity.** `azure://acct/...` and
  `azure://Acct/...` are different objects in some Azure
  configs. Use lowercase everywhere.

## Key takeaways

- Storage integration wraps an Azure app registration + tenant
  + allowed locations.
- The admin must click the consent URL once to grant Snowflake
  blob-reader rights.
- The stage's `URL` is `azure://<account>.blob.core.windows.net/<container>/<prefix>/`.

## What's next

In **L103 — Create notification integration** we wire the
Event Grid topic and finish the pipe.
