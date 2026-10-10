---
l_id: L103
title: Create notification integration
duration: "11:00"
prereqs: ["L102 - Create stage & storage integration"]
---

# L103 — Create notification integration

> **Author:** Prem Vishnoi &lt;pvishnoi&commat;avilx.com&gt;
> **Section:** 13 — Snowpipe for Azure
> **Duration:** 11:00

## Prereqs

Stage works (`LIST @raw.azure_stage` returns rows). Snowflake has
an Azure storage queue you can use as the event sink (Snowflake
will create it for you, but the resource provider must allow it).

## Lecture

The notification integration is what makes the pipe *automatic*.
On Azure, the event source is Event Grid, and the target Snowflake
uses to receive events is an **Azure Storage queue**. This lecture
walks through wiring that up.

### Step 1 — Create the notification integration

```sql
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE NOTIFICATION INTEGRATION azure_eventgrid_int
  TYPE = QUEUE
  NOTIFICATION_PROVIDER = AZURE_EVENT_GRID
  ENABLED = TRUE
  AZURE_STORAGE_QUEUE_PRIMARY_URI = 'https://snowflakedemostorage.queue.core.windows.net/snowpipe-events'
  AZURE_TENANT_ID = '<your-tenant-id>';
```

Two notes:

- The storage queue is created by Snowflake the first time you
  use it. The URI you provide must point at a *valid* Azure
  storage account you own; Snowflake creates the queue inside
  that account.
- The queue account doesn't have to be the same as the blob
  account, but it's simpler if it is.

### Step 2 — Get the Event Grid topic details

```sql
DESC NOTIFICATION INTEGRATION azure_eventgrid_int;
```

You will see:

- `AZURE_EVENT_GRID_TOPIC_ENDPOINT` — the Event Grid topic URL.
- `AZURE_EVENT_GRID_TOPEL_ID` — the Event Grid topic resource ID.

These are the values you paste into the Azure event subscription.

### Step 3 — Create an event subscription in Azure

In the Azure portal (or via `az`):

```bash
az eventgrid event-subscription create \
  --name snowflake-snowpipe-sub \
  --source-resource-id "/subscriptions/<sub>/resourceGroups/$RG/providers/Microsoft.Storage/storageAccounts/$ACCT" \
  --endpoint-type webhook \
  --endpoint "<AZURE_EVENT_GRID_TOPIC_ENDPOINT from DESC>" \
  --included-event-types Microsoft.Storage.BlobCreated \
  --subject-begins-with /blobServices/default/containers/orders/blobs/
```

The `--subject-begins-with` filter scopes the events to the
`orders` container so unrelated blobs don't trigger the pipe.

### Step 4 — Create the pipe

```sql
USE SCHEMA raw;

CREATE OR REPLACE TABLE orders_azure (
  order_id    NUMBER,
  customer_id NUMBER,
  order_date  DATE,
  amount      NUMBER(10,2)
);

CREATE OR REPLACE PIPE orders_azure_pipe
  AUTO_INGEST = TRUE
AS
COPY INTO orders_azure
FROM @azure_stage
FILE_FORMAT = (FORMAT_NAME = 'ff_csv_gcs')
ON_ERROR = 'CONTINUE';
```

### Step 5 — Confirm the wire-up

```sql
DESC PIPE orders_azure_pipe;
-- Look for notification_channel_name and pattern
-- It should match the event-subscription name you created

SELECT SYSTEM$PIPE_STATUS('orders_azure_pipe');
```

`PIPE_STATUS` returns a JSON with a `lastForwardedEventTime`,
`lastReceivedEventTime`, and `lastError`. If `lastReceived` is
`null`, the bucket subscription isn't firing yet — re-check the
event subscription in Azure.

### Step 6 — Smoke test

```bash
# Upload a file to the container
az storage blob upload \
  --account-name $ACCT \
  --container-name orders \
  --name orders_2024_04.csv \
  --file ./orders_2024_04.csv
```

Then in Snowflake:

```sql
SELECT file_name, status, row_count, last_loaded_time
FROM TABLE(INFORMATION_SCHEMA.PIPE_USAGE_HISTORY(
  DATE_RANGE_START => DATEADD('minute', -10, CURRENT_TIMESTAMP())
))
WHERE pipe_name = 'ORDERS_AZURE_PIPE'
ORDER BY last_loaded_time DESC;
```

If you see a row with `status = 'LOADED'`, the pipe is healthy.

### Common gotchas

- **Event subscription in `Pending` state.** It takes ~30s to
  move to `Provisioned`. You cannot load until it does.
- **Wrong event type.** `Microsoft.Storage.BlobCreated` is the
  one. Other event types won't fire the pipe.
- **Storage queue region.** If the queue is in a different
  region from the storage account, Event Grid adds latency and
  may fail delivery; keep them in the same region.

## Key takeaways

- Notification integration is `AZURE_EVENT_GRID` with an Azure
  storage queue URI.
- `DESC NOTIFICATION INTEGRATION` returns the topic endpoint
  you paste into the Azure event subscription.
- `SYSTEM$PIPE_STATUS('<pipe>')` is the one-liner for "is the
  pipe healthy?"

## What's next

In **L104 — Create pipe and load data (Azure)** we exercise the
pipe end-to-end and verify rows in the table.
