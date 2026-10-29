# Section 8 Quiz — Loading from AWS

> 10 questions, multi-choice, single answer. Answers are hidden
> in collapsible blocks; expand only after you've attempted the
> question.

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

---

**Q1.** What is a Snowflake **micro-partition**?

- A. A logical partition defined by `PARTITION BY`
- B. A 50–500 MB columnar file holding table data plus min/max
  metadata
- C. A type of stage
- D. A role-based access control unit

<details><summary>Show answer</summary>

**B — A 50–500 MB columnar file.** Snowflake stores every
table as a set of micro-partitions. Each partition has
columnar data plus metadata for every column (min, max,
distinct count, null count). The metadata powers the
query history cache's pruning.

</details>

---

**Q2.** Which tables benefit most from clustering?

- A. Small tables (< 1 GB)
- B. Large tables (> 1 TB) with selective queries on a specific
  column
- C. Tables with no `WHERE` clauses
- D. All tables benefit equally

<details><summary>Show answer</summary>

**B — Large tables with selective queries.** Small tables
fit in cache anyway; full-scan queries don't prune. The
sweet spot is a multi-TB table where most queries filter
on a specific column. Append-only tables loaded in time
order are often **already clustered** on the load
timestamp.

</details>

---

**Q3.** What does `ALTER TABLE … CLUSTER BY (col)` do?

- A. Immediately re-sorts the table
- B. Sets the clustering key; re-clustering happens in the
  background via the auto-clustering service
- C. Creates a new index
- D. Drops the table

<details><summary>Show answer</summary>

**B — Declarative; the actual re-clustering is
background.** `CLUSTER BY` tells the auto-clustering
service the desired sort order. The service re-clusters
micro-partitions as needed and bills you per second for
the work.

</details>

---

**Q4.** What is the difference between the AWS root user and
an IAM user?

- A. The root user owns the account and has unrestricted access;
  IAM users are scoped identities
- B. They are the same thing
- C. IAM users have more permissions than the root
- D. Root is for AWS support; IAM is for everything else

<details><summary>Show answer</summary>

**A — Root owns the account; IAM users are scoped.** The
root user is the email that signed up for AWS. It cannot
be restricted. IAM users are created under the account and
can be granted least-privilege permissions. **Always enable
MFA on the root user and use an IAM user for day-to-day
work.**

</details>

---

**Q5.** What is the safest default for "Block all public
access" on a new S3 bucket?

- A. On (we use IAM roles, not public URLs)
- B. Off
- C. It doesn't matter
- D. Only enable for non-production buckets

<details><summary>Show answer</summary>

**A — On.** Snowflake reads via an IAM role, not via a
public URL. Public buckets are a common source of data
breaches. Leave the block on unless you have a specific
reason to disable it.

</details>

---

**Q6.** Which three S3 actions must the IAM policy grant for
a Snowflake storage integration?

- A. `s3:GetObject`, `s3:GetObjectVersion`, `s3:ListBucket`
- B. `s3:PutObject`, `s3:DeleteObject`, `s3:ListAllMyBuckets`
- C. `s3:*` (full access)
- D. `s3:ReadOnly`, `s3:WriteOnly`

<details><summary>Show answer</summary>

**A — `GetObject`, `GetObjectVersion`, `ListBucket`.** These
are the minimum read-only actions Snowflake needs. Granting
`s3:*` is over-privileged and a security risk. The
`GetObjectVersion` is only required if bucket versioning is
on, but it's harmless to include.

</details>

---

**Q7.** What does an IAM role's **trust policy** specify?

- A. The actions the role can perform
- B. Who can assume the role
- C. The bucket name
- D. The Snowflake account name

<details><summary>Show answer</summary>

**B — Who can assume the role.** A role has two policies: a
**permission** policy (what the role can do) and a
**trust** policy (who can become the role). For
Snowflake, the trust policy is locked to the Snowflake
AWS principal and an external ID.

</details>

---

**Q8.** What does `DESC INTEGRATION s3_orders_int` return
that you need for the IAM role's trust policy?

- A. The bucket name
- B. The Snowflake AWS user ARN and external ID
- C. The Snowflake account password
- D. The S3 access key

<details><summary>Show answer</summary>

**B — `STORAGE_AWS_IAM_USER_ARN` and `STORAGE_AWS_EXTERNAL_ID`.**
These are the values you put in the IAM role's trust
policy. The user ARN is the principal; the external ID is
the condition. Without the external ID, anyone with the
Snowflake AWS principal could assume the role.

</details>

---

**Q9.** What is the role of `STORAGE_ALLOWED_LOCATIONS` in a
storage integration?

- A. It lists the bucket regions
- B. It is a whitelist of S3 prefixes the integration is
  allowed to read
- C. It sets the encryption key
- D. It controls the file format

<details><summary>Show answer</summary>

**B — A whitelist of S3 prefixes.** Anything outside this
list cannot be loaded through the integration, even if the
IAM role has broader permissions. This is **defence in
depth** — the AWS layer and the Snowflake layer both
restrict access.

</details>

---

**Q10.** Why is a `STORAGE INTEGRATION` preferred over
embedding AWS keys in a stage definition?

- A. It's faster
- B. No AWS keys in SQL; credentials are rotatable in AWS
  without changing Snowflake objects
- C. It supports more file formats
- D. It's the only way to load Parquet

<details><summary>Show answer</summary>

**B — No keys in SQL; rotatable.** Embedding AWS keys in a
stage is a security anti-pattern (they show up in
`SHOW STAGES`, query history, error logs). A storage
integration encapsulates the credentials; you can rotate
the IAM role in AWS without touching any Snowflake
objects.

</details>