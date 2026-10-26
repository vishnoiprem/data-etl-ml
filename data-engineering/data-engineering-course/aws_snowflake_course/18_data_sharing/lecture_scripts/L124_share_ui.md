---
l_id: L124
title: Create share through the interface
duration: "4:30"
prereqs: ["L123"]
---

# L124 — Create share through the interface

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 18 — Data Sharing
> **Duration:** 4:30

## Prereqs

L123 — Using data sharing. You should already know the SQL surface;
this lecture is the equivalent UI walkthrough.

## Key terms

- **Snowsight** — the current Snowflake web UI. Shares are managed
  from `Data → Databases → <db> → Sharing` or `Data → Private
  Sharing`.
- **Provider Studio** — the legacy UI for managing shares.
  Most accounts have migrated to Snowsight, but the steps are
  similar.

## Lecture

Welcome back. Most of this course is SQL — that's the most
reproducible way to work with Snowflake. But shares have a lot of
state to manage (consumer accounts, granted objects, optional
parameters), and the Snowsight UI is sometimes the better place to
audit who has access to what. Today we walk through the clicks.

### The Snowsight walkthrough

1. **Open Snowsight.** Navigate to `Data → Databases`.
2. **Pick a database.** Click on the database you want to share —
   in this example, `DEMO_SHARE`.
3. **Sharing tab.** On the database page, click the **Sharing** tab.
4. **Share with specific accounts.** Click *Share with Specific
   Accounts*.
5. **Add the locator.** Paste the consumer account locator (e.g.
   `abc12345.us-east-1`). You can add multiple locators here.
6. **Pick the objects.** Snowsight asks which schemas and tables
   to include. Tick the boxes; preview the result.
7. **Name the share.** Auto-generated names are usually fine; you
   can override.
8. **Enable.** Click *Enable*. The share is now visible to the
   consumer on their next refresh.

The UI shows you the equivalent statements under the hood. You can
hover over any enabled object and see the
`GRANT USAGE`/`GRANT SELECT` it issued.

### Reading the share state

Once a share exists, the **Sharing** tab shows:

- share name
- list of consumer accounts
- list of granted objects
- the option to *Add consumers* or *Remove consumers*

This is also where you can confirm a particular share is currently
empty (no objects) — useful when triaging access issues.

### When to use the UI vs SQL

| Use UI when... | Use SQL when... |
|---|---|
| Auditing who has access | Building repeatable pipelines |
| Ad-hoc one-time share creation | Programmatically rotating shares |
| Showing non-SQL teammates | Scripted infrastructure as code |

For the rest of this course we will use SQL, because it is
reproducible and scriptable. The UI is here whenever you need to
look under the hood.

### Auditing with SQL

After creating the share through the UI, you can confirm it with
SQL:

```sql
SHOW SHARES;
SHOW GRANTS TO SHARE demo_share;
```

These two commands together give you a complete view of share
membership — what objects it exposes, who the consumers are, and
when it was last modified.

## Hands-on

```sql
-- Pre-flight check: confirm what we created in L123 is still there
SHOW SHARES LIKE 'demo_share';

SHOW GRANTS TO SHARE demo_share;
-- Should list: USAGE on database, USAGE on schema, SELECT on orders.
```

## Key takeaways

- Snowsight's `Data → Databases → Sharing` tab is the UI for share
  management.
- The UI writes the same `GRANT`/`ALTER SHARE` statements you would.
- Use the UI for auditing and ad-hoc work; use SQL for repeatable
  pipelines.
- `SHOW GRANTS TO SHARE` is the canonical audit command.

## What's next

L125 covers sharing with **non-Snowflake users** — a totally
different audience that requires a *reader account*.