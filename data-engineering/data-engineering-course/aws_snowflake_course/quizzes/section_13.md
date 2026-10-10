# Section 13 Quiz — Snowpipe for Azure

> 8 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the question.

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

---

**Q1.** On Azure, which cloud event source does Snowpipe
auto-ingest subscribe to?

- A. Azure Service Bus
- B. Event Grid
- C. Azure Functions
- D. Azure Monitor

<details><summary>Show answer</summary>

**B — Event Grid.** The notification integration is
`NOTIFICATION_PROVIDER = AZURE_EVENT_GRID` and the event
subscription targets a webhook endpoint Snowflake exposes.

</details>

---

**Q2.** What Azure role does the Snowflake service principal
need on the storage container to read blobs for a pipe?

- A. Storage Blob Data Reader (or Contributor) on the container
- B. Storage Account Contributor on the storage account
- C. Owner on the resource group
- D. Reader on the subscription

<details><summary>Show answer</summary>

**A — Storage Blob Data Reader (or Contributor).** The other
options are over-scoped. The integration's
`STORAGE_ALLOWED_LOCATIONS` lists the exact containers/prefixes
Snowflake is allowed to read from.

</details>

---

**Q3.** Which event type do you filter on in the Azure event
subscription for a Snowpipe?

- A. `Microsoft.Storage.BlobDeleted`
- B. `Microsoft.Storage.BlobRenamed`
- C. `Microsoft.Storage.BlobCreated`
- D. `Microsoft.Storage.BlobTierChanged`

<details><summary>Show answer</summary>

**C — `Microsoft.Storage.BlobCreated`.** This is the Azure
equivalent of GCS's `OBJECT_FINALIZE` and AWS S3's
`ObjectCreated:*`.

</details>

---

**Q4.** What is the purpose of the
`AZURE_CONSENT_URL` returned by `DESC STORAGE INTEGRATION`?

- A. It's the URL the Snowflake service principal will use to
  call Azure
- B. It's the URL the Azure admin must click to grant
  Snowflake's app registration access in the tenant
- C. It's the bucket (container) URL
- D. It's a read-only API endpoint for listing blobs

<details><summary>Show answer</summary>

**B — It's a one-time consent URL.** The Azure tenant admin
clicks it to grant Snowflake's multi-tenant app the
`Storage Blob Data Reader` role on the tenant. After consent,
the storage integration is usable.

</details>

---

**Q5.** Which command gives you a one-liner JSON snapshot of
the health of a Snowpipe (last received event, last error,
etc.)?

- A. `SHOW PIPES;`
- B. `SELECT SYSTEM$PIPE_STATUS('<pipe_name>');`
- C. `DESC PIPE <pipe_name>;`
- D. `SELECT SYSTEM$PING_PIPE('<pipe_name>');`

<details><summary>Show answer</summary>

**B — `SELECT SYSTEM$PIPE_STATUS('<pipe_name>');`.** Returns a
JSON object with `lastReceivedEventTime`,
`lastForwardedEventTime`, and `lastError` — the three things
you check first when a pipe is unhealthy.

</details>

---

**Q6.** In the Azure event subscription, what does
`--subject-begins-with /blobServices/default/containers/orders/blobs/`
do?

- A. Restricts events to those whose subject starts with that
  path (i.e. only the `orders` container)
- B. Filters on the event ID prefix
- C. Tags the event with a metadata key
- D. Sets the destination queue name

<details><summary>Show answer</summary>

**A — Restricts events to a subject prefix.** Without it, the
event subscription would fire on *any* container in the storage
account, including ones the pipe doesn't load from.

</details>

---

**Q7.** What is the difference between an Azure
**storage** integration and an Azure **notification**
integration?

- A. Storage integration = read blobs; notification integration
  = receive Event Grid events
- B. Storage integration = receive events; notification
  integration = write blobs
- C. Both are the same; the names are aliases
- D. Storage integration is for GCS only; notification is for
  Azure only

<details><summary>Show answer</summary>

**A — Storage integration handles the data path (read blobs);
notification integration handles the event path (receive Event
Grid events).** You need both for a working Azure Snowpipe.

</details>

---

**Q8.** Why is it useful to keep the storage account, the
storage queue, and the Snowflake account all in the same Azure
region?

- A. It's required; cross-region Snowflake is not allowed
- B. Cross-region adds latency and potential egress fees; same
  region keeps the pipe fast and cheap
- C. Cross-region is cheaper
- D. It is irrelevant to the pipe

<details><summary>Show answer</summary>

**B — Same region is faster and cheaper.** Event Grid delivery
across regions adds latency, and any cross-region data
transfer incurs Azure egress fees. Same region also makes
permissions and consent simpler.

</details>
