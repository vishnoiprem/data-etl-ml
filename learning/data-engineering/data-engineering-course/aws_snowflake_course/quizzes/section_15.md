# Section 15 Quiz — Fail Safe

> 5 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the question.

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

---

**Q1.** How long is Fail Safe, and is it configurable?

- A. 1 day, configurable up to 7
- B. 7 days, non-configurable
- C. 14 days, configurable
- D. 30 days, non-configurable

<details><summary>Show answer</summary>

**B — 7 days, non-configurable.** It is automatic and applies
only to permanent tables. You cannot turn it off or change
its length.

</details>

---

**Q2.** Which table types have Fail Safe?

- A. Permanent only
- B. Permanent and transient
- C. Permanent, transient, and temporary
- D. None — only the schema/database

<details><summary>Show answer</summary>

**A — Permanent tables only.** Transient and temporary tables
have neither Fail Safe nor any Time Travel beyond the default
1 day.

</details>

---

**Q3.** Who can read Fail Safe data?

- A. Any Snowflake user with `OWNERSHIP` on the table
- B. The table's owner via `SELECT ... FAIL_SAFE`
- C. Only Snowflake Support
- D. Anyone with the `FAILSAFE_READER` role

<details><summary>Show answer</summary>

**C — Only Snowflake Support.** There is no `SELECT ... FAIL_SAFE`
syntax; no user-facing role grants Fail Safe access. You open
a support case.

</details>

---

**Q4.** Which column in `TABLE_STORAGE_METRICS` represents
the storage cost of historical versions past the Time Travel
window?

- A. `active_bytes`
- B. `time_travel_bytes`
- C. `failsafe_bytes`
- D. `archived_bytes`

<details><summary>Show answer</summary>

**C — `failsafe_bytes`.** `active_bytes` is the live state,
`time_travel_bytes` is the in-retention history, and
`failsafe_bytes` is the 7-day non-configurable tail.

</details>

---

**Q5.** Which statement about Fail Safe is **most accurate**?

- A. Plan your recovery around Fail Safe — it is your
  primary safety net
- B. Fail Safe is a non-configurable last-resort safety net;
  don't plan your recovery around it
- C. Fail Safe is queryable via `SELECT ... AT (FAIL_SAFE => TRUE)`
- D. Fail Safe applies to all Snowflake objects, including
  streams and tasks

<details><summary>Show answer</summary>

**B — Don't plan your recovery around it.** Treat Fail Safe as
"if everything else failed, call Snowflake Support." Build
your own backups and tune `DATA_RETENTION_TIME_IN_DAYS` to
match your SLA. Fail Safe is not queryable via SQL and does
not apply to non-table objects.

</details>
