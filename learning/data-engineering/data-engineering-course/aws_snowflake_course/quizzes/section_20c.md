# Section 20c Quiz — Roles deep-dive + BI Tools (L166–L181)

> 10 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the question.

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Scope:** L166–L181 (Roles deep-dive + BI Tools)

---

**Q1.** RBAC in Snowflake means:

- A. Users get privileges directly
- B. Privileges are attached to roles; users are made members
  of roles
- C. Roles are auto-generated from user names
- D. Roles are only for `ACCOUNTADMIN`

<details><summary>Show answer</summary>

**B — Privileges are attached to roles; users are made
members of roles.** Roles can also be granted to other
roles, forming a hierarchy.

</details>

---

**Q2.** Which system-defined role is the recommended home for
day-to-day work?

- A. `ACCOUNTADMIN`
- B. `SECURITYADMIN`
- C. `SYSADMIN`
- D. `PUBLIC`

<details><summary>Show answer</summary>

**C — `SYSADMIN`.** It can do almost everything a data
engineer needs, with a smaller blast radius than
`ACCOUNTADMIN`.

</details>

---

**Q3.** A custom role should typically be granted to which
parent role?

- A. `ACCOUNTADMIN`
- B. `SECURITYADMIN`
- C. `SYSADMIN`
- D. `PUBLIC`

<details><summary>Show answer</summary>

**C — `SYSADMIN`.** Custom roles inherit `SYSADMIN`'s
basic privileges, which every role needs.

</details>

---

**Q4.** `USERADMIN` differs from `SECURITYADMIN` in that:

- A. `USERADMIN` can grant any object privilege
- B. `USERADMIN` cannot grant object privileges — only
  manage users and role membership
- C. `USERADMIN` is the top role
- D. They are identical

<details><summary>Show answer</summary>

**B — `USERADMIN` can manage users and role membership
but not grant object privileges.** That's the safety
mechanism: the helpdesk can't escalate.

</details>

---

**Q5.** `PUBLIC` is a role that:

- A. Every user is automatically a member of
- B. Has all privileges
- C. Is restricted to `ACCOUNTADMIN`
- D. Doesn't exist

<details><summary>Show answer</summary>

**A — Every user is automatically a member of `PUBLIC`.**
By default, it has no privileges; only the implicit
`USAGE` on `PUBLIC` schema in every database.

</details>

---

**Q6.** DirectQuery (Power BI) and Live (Tableau) modes are
analogues in that they both:

- A. Load data into the BI tool's engine
- B. Push every visual's query to Snowflake
- C. Are slower than Import mode
- D. Are deprecated

<details><summary>Show answer</summary>

**B — Push every visual's query to Snowflake.** The BI
tool has no in-memory copy; the data is always live.

</details>

---

**Q7.** Snowflake Partner Connect is used to:

- A. Connect two Snowflake accounts
- B. One-click install of third-party tools (Power BI,
  Tableau, etc.)
- C. Share data with non-Snowflake consumers
- D. Create a resource monitor

<details><summary>Show answer</summary>

**B — One-click install of third-party tools.** It creates
a service account, sets up the warehouse, and starts a
30-day trial.

</details>

---

**Q8.** Snowflake Marketplace listings are essentially:

- A. Stored procedures
- B. Shares from third-party providers to your account
- C. External functions
- D. Tasks

<details><summary>Show answer</summary>

**B — Shares from third-party providers to your account.**
You mount them with `CREATE DATABASE ... FROM SHARE`; the
bytes stay with the provider.

</details>

---

**Q9.** Most Marketplace listings are:

- A. Paid only
- B. Free; you pay only for the compute to query
- C. Restricted to `ACCOUNTADMIN`
- D. Time-limited to 7 days

<details><summary>Show answer</summary>

**B — Free; you pay only for the compute.** Some listings
are paid; the provider charges through Snowflake's billing.

</details>

---

**Q10.** The "personalized data" feature of the Marketplace
allows:

- A. A provider to read your raw data
- B. Joins between provider data and your data inside
  Snowflake, with neither side seeing the other's raw data
- C. Free compute for both sides
- D. Public exposure of your data

<details><summary>Show answer</summary>

**B — Joins between provider and your data inside
Snowflake, with neither side seeing the other's raw
data.** It's the most powerful Marketplace feature for
privacy-preserving analytics.

</details>