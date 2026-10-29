---
l_id: L06
title: Getting to know the interface
duration: "8:00"
prereqs: ["L05"]
downloads: []
---

# L06 — Getting to Know the Interface

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 2 — Getting Started
> **Duration:** ~8:00

## Prereqs

L05 — Sign up for free trial. You should have a working account
URL and be able to log in.

## Key terms

- **Snowsight** — Snowflake's modern web UI (default since
  2023). Replaced the older "Classic Console".
- **Worksheet** — a SQL scratchpad. Persists across sessions;
  supports version history.
- **Dashboards** — visual result panels pinned to a worksheet.
- **Database objects browser** — left sidebar for navigating
  databases, schemas, tables, stages, file formats, sequences,
  tasks, pipes, and streams.
- **Activity / Query History** — top nav. Every query you or
  anyone with your role has run, with warehouse, bytes scanned,
  and duration.

## Lecture

In this lecture we tour the Snowflake UI end to end. Snowflake's
web interface has more moving parts than most data tools, so
spending 8 minutes here saves hours of confusion later.

### Snowsight layout

The Snowsight UI has four main areas:

1. **Left sidebar** — navigation: Worksheets, Dashboards, Data
   (Databases), Marketplace, Activity, Admin.
2. **Top nav** — account selector, role selector, help, user
   menu.
3. **Main pane** — context-sensitive: a worksheet editor, a
   query history list, an admin panel, etc.
4. **Bottom panel** — result set preview, query profile link,
   error messages.

### The role selector — the most important UI element

Snowflake's role-based access control is enforced at the UI
level. The top-right role selector controls which role your
next query runs as. **Always check this before running DDL.**

```sql
-- See your current role and the roles granted to you
SELECT CURRENT_ROLE();
SHOW GRANTS TO USER <your_username>;
```

Most day-to-day work runs as a non-admin role (e.g.
`ANALYST`, `DEVELOPER`). The `ACCOUNTADMIN` role should be
reserved for account-level operations.

### Worksheets

Click **Worksheets** → **+ Worksheet** to open a new SQL
scratchpad. Useful features:

- **Auto-complete** — type `CRE` and hit Tab; it suggests
  `CREATE`, `CREDENTIAL`, etc.
- **Multi-statement** — separate statements with `;`. Run one
  at a time with `Ctrl+Enter`, or run all with `Ctrl+Shift+Enter`.
- **Result panel** — appears below the editor. Click a column
  header to sort, click the **Chart** icon to switch to a
  bar/line/pie chart.
- **History** — every worksheet run is captured in the
  **Worksheet History** panel. Re-run yesterday's query
  without retyping it.
- **Sharing** — share a worksheet with another user in your
  account; they get a read-only view.

### Data (databases) browser

The **Data** section in the left sidebar is your object tree:

```text
📁 Databases
 └─ 📁 SNOWFLAKE               ← system database (read-only)
     └─ 📁 ACCOUNT_USAGE         ← query history, storage, etc.
 └─ 📁 SNOWFLAKE_SAMPLE_DATA   ← sample TPC-H, TPC-DS, weather
 └─ 📁 <your_database>          ← databases you create
     └─ 📁 PUBLIC
         └─ 📄 <your_tables>
```

Click the **+** to create a database, schema, table, stage,
file format, pipe, task, sequence, or stream — all with
wizards that generate the SQL for you.

### Activity / Query History

**Activity** → **Query History** lists every query run by
your user (and by all users if you have the right role).
For each query you see:

- **Query ID** — click to open the **Query Profile**, a
  visual execution plan.
- **Warehouse** — which warehouse ran it.
- **Status** — success, fail, running, queued.
- **Duration** — total + compile + execute.
- **Bytes scanned** — the single most useful number for
  performance debugging.

The Query History view is filterable by date range, user,
warehouse, and status. Save your common filters.

### Admin

**Admin** → **Warehouses**, **Roles**, **Users**, **Resource
Monitors** are where you manage account-level objects.
We'll use these in the next several lectures.

### Keyboard shortcuts

- `Ctrl+Enter` — run statement at cursor
- `Ctrl+Shift+Enter` — run all
- `Ctrl+/` — comment/uncomment
- `Ctrl+Space` — manual auto-complete
- `Ctrl+S` — save worksheet

## Hands-on

```sql
-- Take a look at the sample data Snowflake provides
USE DATABASE SNOWFLAKE_SAMPLE_DATA;
USE SCHEMA TPCH_SF1;

SELECT N_NAME, COUNT(*) AS nation_count
FROM NATION
GROUP BY N_NAME
ORDER BY nation_count DESC;
```

You should see 25 rows — the 25 nations of the TPC-H
sample schema. If this works, your account is fully
operational.

## Quiz prep

- Which UI replaced the older "Classic Console"? (Snowsight)
- What does the **role selector** in the top-right control?
  (The role your next query runs as)
- Where in the UI do you find query history and query
  profile? (Activity → Query History)

## What's next

Next up is **L07 — Understanding Workspaces & Querying Data**,
where we use Snowflake's worksheet workspaces to organize
multi-project SQL development.
