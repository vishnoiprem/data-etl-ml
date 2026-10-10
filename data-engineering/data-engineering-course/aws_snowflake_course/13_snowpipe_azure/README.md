# Section 13 — Snowpipe for Azure

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Lectures:** L100–L103
> **Duration:** ~30 min

The Snowpipe story we built in section 11 used **GCS** as the
event source. In this section we repeat the same pattern on
**Azure Blob Storage**, where the event surface is
**Event Grid** instead of Pub/Sub.

The shape is identical:

1. Confirm the cloud side (Azure storage account, container,
   service principal).
2. Create the storage integration + stage.
3. Create the notification integration (Event Grid topic).
4. Create the pipe and let Snowflake wire the event-grid
   subscription.

What changes is the cloud-side vocabulary: storage integration
is "service principal + tenant", the notification is "Event Grid
+ Azure Storage queue", and the channel you paste back is an
Azure resource ID, not a `gcs://` URI.

By the end of this section you will have a working Azure Snowpipe
and the same `ALTER PIPE ... REFRESH` / `PIPE_USAGE_HISTORY`
operational tools you have on GCS.

| L# | Title | Min |
|---|---|---|
| L100 | Hands-on: Clean Up | 4:00 |
| L101 | High-level steps (Snowpipe Azure) | 6:00 |
| L102 | Create stage & storage integration | 9:00 |
| L103 | Create notification integration | 11:00 |

## Key concepts you'll need later

- **Storage integration (Azure)** — wraps an Azure service
  principal + tenant + allowed storage account list.
- **Notification integration (Azure)** — wires Snowflake to an
  Event Grid topic so the pipe can subscribe to blob events.
- **`AZURE_EVENT_GRID`** vs `AZURE_QUEUE` — two flavors of
  notification integration; Event Grid is the modern, recommended
  one.
- **Event types** — `Microsoft.Storage.BlobCreated` is the one
  you filter on (matches the `OBJECT_FINALIZE` we used on GCS).

## What comes next

Section 14 is **Time Travel** — the killer Snowflake recovery
feature. We use `AT | BEFORE` offsets, `UNDROP`, and the
`DATA_RETENTION_TIME_IN_DAYS` parameter to round out the
data-protection story.
