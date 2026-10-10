# Section 10 Quiz — Loading from GCP

> 10 questions, multi-choice, single answer. Answers are hidden
> in collapsible blocks; expand only after you've attempted the
> question.

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

---

**Q1.** What is the URL scheme for a GCS external stage in
Snowflake?

- A. `gs://`
- B. `https://`
- C. `gcs://`
- D. `s3://`

<details><summary>Show answer</summary>

**C — `gcs://`.** Snowflake parses the URL scheme to identify
the storage provider. `gcs://<bucket>/<path>` is the
canonical form. The `gs://` form is the `gcloud` CLI's
URL scheme and won't work in Snowflake.

</details>

---

**Q2.** Which GCP IAM role is the least-privilege choice for
a Snowflake storage integration?

- A. `Owner`
- B. `Storage Admin`
- C. `Storage Object Viewer`
- D. `Storage Object Admin`

<details><summary>Show answer</summary>

**C — `Storage Object Viewer`.** It grants read access to
objects and the ability to list them. `Storage Admin` and
`Owner` are over-privileged. `Storage Object Admin` can
delete objects — never what a load-time integration needs.

</details>

---

**Q3.** Why does the GCS storage integration **not** require
a service account key file?

- A. GCP service accounts can't have keys
- B. The IAM binding on the bucket is the trust; Snowflake
  authenticates to GCP and inherits the binding — no key
  file is exchanged
- C. Snowflake impersonates the bucket owner
- D. The integration is broken without a key

<details><summary>Show answer</summary>

**B — IAM is the trust layer.** The service account email
is granted `Storage Object Viewer` on the bucket. When
Snowflake's GCP SA authenticates, GCP checks the IAM
binding and grants access — no key file is exchanged.
This is the most secure pattern: no long-lived secret to
rotate or leak.

</details>

---

**Q4.** What is the GCP equivalent of an S3 bucket?

- A. Project
- B. Service account
- C. Bucket (GCS)
- D. Folder

<details><summary>Show answer</summary>

**C — GCS bucket.** A GCS bucket is the global namespace
that holds objects. It's the direct equivalent of an S3
bucket or an Azure container. (The Azure storage account
is more like a GCP *project* — both are billing units.)

</details>

---

**Q5.** What is the cheapest active storage class in GCS?

- A. `Standard`
- B. `Nearline`
- C. `Coldline`
- D. `Archive`

<details><summary>Show answer</summary>

**A — `Standard`.** Standard is the default and the right
choice for active analytics. `Nearline` is for 30-day
backups (~$0.010/GB/mo), `Coldline` for 90-day backups
(~$0.004/GB/mo), and `Archive` for long-term archives
(~$0.0012/GB/mo) — but each has a per-retrieval cost
that makes them unsuitable for active workloads.

</details>

---

**Q6.** Why do we enable `--uniform-bucket-level-access`
when creating a GCS bucket?

- A. It's required by the GCP free trial
- B. It disables per-object ACLs and forces all permission
  decisions through IAM — recommended for new buckets
- C. It enables encryption at rest
- D. It makes the bucket faster

<details><summary>Show answer</summary>

**B — Modern access model.** Per-object ACLs are legacy
and cause integration issues. Uniform bucket-level access
disables them; all permission decisions go through IAM.
This is the recommended setting for new buckets and
required for clean Snowflake integration.

</details>

---

**Q7.** What is the fastest smoke test for a new GCS
storage integration?

- A. `SELECT * FROM @stage`
- B. `LIST @stage`
- C. `DESC INTEGRATION <name>`
- D. `SHOW BUCKETS`

<details><summary>Show answer</summary>

**B — `LIST @stage`.** It calls GCS's list-objects API
and returns immediately. If `LIST` returns the expected
files, the integration, the IAM role, and the network
path are all working. If it errors, you have a precise
error code (`403`, `404`) to debug.

</details>

---

**Q8.** What is the role of the **Snowflake service account
email** in the GCS integration?

- A. It is the email that authenticates the human user
- B. It is a per-region GCP service account that Snowflake
  uses; the bucket's IAM binding must grant it
  `Storage Object Viewer`
- C. It is the email that receives alerts
- D. It is the GCP project ID

<details><summary>Show answer</summary>

**B — A per-region GCP service account that Snowflake
assumes.** Snowflake publishes one email per region.
The bucket's IAM binding must grant it `Storage Object
Viewer` so the integration can list and read objects.
The exact email depends on the Snowflake account's
region.

</details>

---

**Q9.** Why is the downstream `COPY INTO` SQL identical
between S3, Azure, and GCS stages?

- A. The SQL is provider-specific in practice
- B. Snowflake's storage layer is cloud-agnostic; the
  same `COPY INTO … FROM @stage` works against any
  provider
- C. S3 only supports CSV
- D. Snowflake only supports Parquet

<details><summary>Show answer</summary>

**B — Cloud-agnostic storage layer.** The `COPY INTO
… FROM (SELECT $1, METADATA$FILENAME FROM @stage)`
syntax works for S3, Azure, and GCS. The stage's
storage integration handles the credentials and the
protocol. This is the magic of the storage
integration: **storage-agnostic pipelines**.

</details>

---

**Q10.** How much free credit does the GCP free trial
give?

- A. $200 for 30 days
- B. 12 months of free tier (no credit)
- C. $300 for 90 days
- D. $100 for 60 days

<details><summary>Show answer</summary>

**C — $300 for 90 days.** The GCP free trial is the most
generous of the three cloud providers. Plus 5 GB of Cloud
Storage for 12 months, which is enough for the entire
section. Always set a budget alert before creating
resources.

</details>