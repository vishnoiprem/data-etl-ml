# Section 18 Quiz — Data Sharing

> 12 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the question.

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

---

**Q1.** What is the producer/consumer model in Snowflake data sharing?

- A. The producer pays for everything
- B. The producer owns the data; the consumer pays for compute
- C. The consumer owns the data
- D. Both parties pay equally for storage and compute

<details><summary>Show answer</summary>

**B — The producer owns the data; the consumer pays for compute.**
Storage stays with the producer (and is billed to the producer);
compute is paid by the consumer account running the queries.

</details>

---

**Q2.** Which statement creates a share?

- A. `CREATE SHARE my_share;`
- B. `CREATE SHARE FROM my_table;`
- C. `GRANT SHARE TO ...;`
- D. `ALTER SHARE ... CREATE;`

<details><summary>Show answer</summary>

**A — `CREATE SHARE my_share;`** An empty share is created, then
you `GRANT` objects to it.

</details>

---

**Q3.** A complete share requires grants on which of these?

- A. Database only
- B. Schema only
- C. Database, schema, and table
- D. Just the table

<details><summary>Show answer</summary>

**C — Database, schema, and table.** All three grants are
required. Forgetting the schema grant is the most common mistake.

</details>

---

**Q4.** Which command publishes a share to a consumer account?

- A. `GRANT SHARE TO ACCOUNT ...;`
- B. `ALTER SHARE ... ADD ACCOUNTS = ...;`
- C. `CREATE SHARE FROM ACCOUNT ...;`
- D. `PUBLISH SHARE TO ...;`

<details><summary>Show answer</summary>

**B — `ALTER SHARE ... ADD ACCOUNTS = ...;`**

</details>

---

**Q5.** Can you share with a company that does not have a Snowflake
account?

- A. No, they must sign up first
- B. Yes, by creating a reader account for them
- C. Yes, by sharing the password of your account
- D. Yes, via S3 export

<details><summary>Show answer</summary>

**B — Yes, by creating a reader account for them.** Reader accounts
are Snowflake-managed accounts you own and provision for
non-Snowflake consumers.

</details>

---

**Q6.** Which edition is required to create reader accounts?

- A. Standard
- B. Enterprise
- C. Business Critical (or above)
- D. Free trial

<details><summary>Show answer</summary>

**C — Business Critical (or above).** Reader accounts are a
managed-account feature that requires elevated edition.

</details>

---

**Q7.** On the consumer side, which statement mounts a share?

- A. `CREATE DATABASE x FROM SHARE locator.share_name;`
- B. `IMPORT SHARE share_name;`
- C. `MOUNT SHARE share_name AS x;`
- D. `ATTACH SHARE share_name;`

<details><summary>Show answer</summary>

**A — `CREATE DATABASE x FROM SHARE locator.share_name;`** The
single statement that turns a share into a local database.

</details>

---

**Q8.** Can a consumer `INSERT` into a shared table?

- A. Yes, if they have the privilege
- B. Yes, only for a limited time
- C. No, sharing is read-only
- D. Only on temporary tables

<details><summary>Show answer</summary>

**C — No.** Shares are read-only by design. The mounted database
is *strictly* queryable; no `INSERT`, `UPDATE`, or `DELETE` is
allowed.

</details>

---

**Q9.** Which type of view can be shared?

- A. Normal view
- B. Secure view
- C. Both
- D. Neither; views can't be shared

<details><summary>Show answer</summary>

**B — Secure view.** Only `CREATE SECURE VIEW` views are eligible
for sharing. Snowflake refuses to include normal views in a share.

</details>

---

**Q10.** Why does Snowflake distinguish normal from secure views for
sharing?

- A. Performance
- B. The optimizer can inline normal views, exposing the
  definition (and possibly hidden columns or predicates) to the
  consumer
- C. Secure views are free; normal views cost extra
- D. It's a UI convention only

<details><summary>Show answer</summary>

**B — A secure view's definition is hidden from the consumer;
a normal view may be inlined by the optimizer, exposing
underlying tables, columns, and predicates.**

</details>

---

**Q11.** A consumer wants a user to query a shared table. In what
order should the consumer's account admin grant?

- A. SELECT on table, USAGE on schema, USAGE on database
- B. USAGE on database, USAGE on schema, SELECT on table
- C. USAGE on schema, USAGE on database, SELECT on table
- D. Order does not matter

<details><summary>Show answer</summary>

**B — USAGE on database, USAGE on schema, SELECT on table.** The
order matters; each grant enables the next level.

</details>

---

**Q12.** Can a single share expose tables from two different
producer databases?

- A. Yes
- B. No, each share is bound to one database
- C. Only if both databases are transient
- D. Only via secure views

<details><summary>Show answer</summary>

**A — Yes.** A single share can include objects from multiple
databases in the same account. The consumer sees them all under
one mounted database.

</details>