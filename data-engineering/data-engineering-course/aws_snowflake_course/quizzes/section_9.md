# Section 9 Quiz — Loading from Azure

> 10 questions, multi-choice, single answer. Answers are hidden
> in collapsible blocks; expand only after you've attempted the
> question.

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

---

**Q1.** What is the URL scheme for an Azure external stage in
Snowflake?

- A. `https://`
- B. `s3://`
- C. `azure://`
- D. `gs://`

<details><summary>Show answer</summary>

**C — `azure://`.** Snowflake parses the URL scheme to identify
the storage provider. `azure://<account>.blob.core.windows.net/<container>/<path>`
is the canonical form. The `https://` form works in the
browser but not in Snowflake.

</details>

---

**Q2.** Which Azure RBAC role is the least-privilege choice
for a Snowflake storage integration?

- A. `Owner`
- B. `Contributor`
- C. `Storage Blob Data Reader`
- D. `Storage Account Contributor`

<details><summary>Show answer</summary>

**C — `Storage Blob Data Reader`.** It grants read access to
blobs and the ability to list containers — exactly what
Snowflake needs. `Owner` and `Contributor` are over-privileged
and a security risk. `Storage Account Contributor` can
manage the storage account itself, which is far more than
load-time access.

</details>

---

**Q3.** What is the purpose of the `AZURE_CONSENT_URL`
returned by `DESC INTEGRATION`?

- A. To download the storage account's access keys
- B. To grant tenant-level approval for the service principal
  to act on behalf of users
- C. To delete the storage account
- D. To enable TLS on the storage account

<details><summary>Show answer</summary>

**B — Tenant-level approval.** Without consent, the service
principal has **no** permission to read blobs even if
granted `Storage Blob Data Reader`. The consent URL is a
one-time admin approval that the principal is allowed to
act in the tenant at all.

</details>

---

**Q4.** What is the Azure equivalent of an S3 bucket?

- A. Storage account
- B. Container
- C. Resource group
- D. Subscription

<details><summary>Show answer</summary>

**B — Container.** A container is a flat namespace inside a
storage account. The storage account is the billing unit
(more like the AWS account itself), and the container is
where the blobs (objects) live.

</details>

---

**Q5.** What is the cheapest storage SKU for an Azure
storage account used for analytics?

- A. `Premium_LRS`
- B. `Standard_LRS`
- C. `Standard_GZRS`
- D. `Standard_RAGZRS`

<details><summary>Show answer</summary>

**B — `Standard_LRS`.** `LRS` (locally redundant storage)
keeps 3 copies in one region. `Premium` is for high-IOPS
workloads. `GZRS` and `RAGZRS` add cross-region or
read-access geo-redundancy at significant cost. For
analytics with a free-tier budget, `Standard_LRS` is the
right choice.

</details>

---

**Q6.** What is the fastest smoke test for a new storage
integration?

- A. `SELECT * FROM @stage`
- B. `LIST @stage`
- C. `DESC INTEGRATION <name>`
- D. `SHOW TABLES`

<details><summary>Show answer</summary>

**B — `LIST @stage`.** It calls the storage provider's
list-objects API and returns immediately. If `LIST`
returns the expected files, the integration, the IAM
permissions, and the network path are all working. If it
errors, you have a precise error code (`403`, `404`,
`Integration not found`) to debug.

</details>

---

**Q7.** Why is the downstream `COPY INTO` SQL identical
between an S3 stage and an Azure stage?

- A. They are not — Azure requires different SQL
- B. Snowflake's storage layer is cloud-agnostic; the same
  `COPY INTO … FROM @stage` works against any provider
- C. Azure and S3 use the same URL scheme
- D. S3 only supports CSV

<details><summary>Show answer</summary>

**B — Snowflake's storage layer is cloud-agnostic.** The
`COPY INTO … FROM (SELECT $1, METADATA$FILENAME FROM
@stage)` syntax works for S3, Azure, and GCS. The stage's
storage integration handles the credentials and the
protocol. This is the magic of the storage integration:
**storage-agnostic pipelines**.

</details>

---

**Q8.** What is the difference between an Azure AD
**application** and a **service principal**?

- A. They are the same thing
- B. The application is the global identity; the service
  principal is the instance of that identity in a specific
  tenant
- C. Service principals are for users; applications are for
  services
- D. Applications are paid; service principals are free

<details><summary>Show answer</summary>

**B — Application is global; service principal is
per-tenant.** An Azure AD application is the global
identity (like an AWS IAM role definition). A service
principal is the instance of that application in a
specific tenant, with its own role assignments. The
service principal is what gets the `Storage Blob Data
Reader` role.

</details>

---

**Q9.** What is the right Azure Blob access tier for
frequently-read analytics data?

- A. `Archive`
- B. `Cool`
- C. `Cold`
- D. `Hot`

<details><summary>Show answer</summary>

**D — `Hot`.** `Hot` is for frequently-read data with
cheap retrieval. `Cool` and `Cold` are cheaper for
storage but charge per retrieval. `Archive` is the
cheapest storage but takes hours to retrieve. For an
analytics pipeline that loads hourly, `Hot` is the right
choice.

</details>

---

**Q10.** What is the Azure equivalent of an S3 IAM policy
that grants `s3:GetObject`?

- A. `Storage Blob Data Contributor`
- B. `Storage Blob Data Reader`
- C. `Owner`
- D. `Reader`

<details><summary>Show answer</summary>

**B — `Storage Blob Data Reader`.** It grants the
equivalent of `s3:GetObject` plus `s3:ListBucket` —
exactly the read access Snowflake needs. `Contributor`
adds write access; `Owner` and `Reader` are subscription-
or resource-level roles, not data-plane roles.

</details>