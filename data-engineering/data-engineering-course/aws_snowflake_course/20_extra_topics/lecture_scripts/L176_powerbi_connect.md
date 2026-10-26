---
l_id: L176
title: Connect Power BI & Snowflake
duration: "5:00"
prereqs: ["L175"]
---

# L176 — Connect Power BI & Snowflake

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 6. BI Tools
> **Duration** 5:00

## Prereqs

L175 — Download & install Power BI. Power BI Desktop should
be installed and signed in.

## Key terms

- **Get Data** — the Power BI button for adding a data
  source.
- **Snowflake connector** — Power BI's native connector for
  Snowflake; listed under "Database" in the Get Data picker.
- **DirectQuery** — mode that pushes every query to
  Snowflake.
- **Import** — mode that loads the data into Power BI's
  in-memory engine.

## Lecture

Welcome back. Today's lecture is the actual connection from
Power BI Desktop to Snowflake. By the end, you should see
your Snowflake tables in Power BI's data pane.

### The connection steps

1. Open Power BI Desktop. Click **Get Data** in the
   ribbon.
2. In the picker, type `Snowflake`. The Snowflake
   connector appears in the "Database" list.
3. Click **Connect**. A dialog opens asking for:
   - **Server**: `your_account_locator.snowflakecomputing.com`
   - **Warehouse**: the warehouse to use (e.g. `compute_wh`)
4. Click **OK**. Power BI prompts for credentials.

### The credentials dialog

Power BI offers three authentication modes:

- **Username + password** — type your Snowflake username
  and password.
- **Microsoft account (OAuth)** — sign in with your IdP.
  This is the production recommendation.
- **Key-pair** — provide the private key file. Used for
  service accounts.

For this walkthrough, use username + password. The OAuth
flow is the same after the initial sign-in.

### Import mode vs DirectQuery

After the credentials dialog, Power BI asks which mode:

- **Import** — data is loaded into Power BI's engine. Use
  for self-contained dashboards.
- **DirectQuery** — every visual issues a fresh `SELECT`
  against Snowflake. Use for live data.

**DirectQuery is the recommended default** for Snowflake
because the BI tool's engine is a poor substitute for
Snowflake's columnar engine.

### The Navigator

After the mode selection, Power BI shows the **Navigator**:
a list of databases and tables. Expand the database you
want, tick the tables or views you need, click **Load**
(or **Transform Data** if you want to clean first).

```text
Navigator
└── FINANCE
    ├── PUBLIC
    │   ├── BALANCES       (tick)
    │   ├── TRANSACTIONS   (tick)
    │   └── DIM_CUSTOMER   (tick)
    └── RAW
        └── ...
```

After clicking **Load**, the data is in Power BI's data
pane and ready to use in visuals.

### A common error: warehouse name

The "Server" field expects the full account URL, e.g.
`xy12345.us-east-1.snowflakecomputing.com`. A common newbie
mistake is to put only `xy12345`, which gives a
"Connection failed" error.

If you're unsure of your account URL, run
`SELECT CURRENT_ACCOUNT() || '.' || CURRENT_REGION() ||
'.snowflakecomputing.com';` in a Snowflake worksheet.

## Hands-on

1. Open Power BI Desktop.
2. Get Data → Snowflake → Connect.
3. Server: `<your_locator>.snowflakecomputing.com`
4. Warehouse: `compute_wh`
5. Authentication: username + password.
6. Mode: DirectQuery.
7. Navigator: pick `SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS`.
8. Click Load.

You should see the ORDERS table in Power BI's data pane.

## Key takeaways

- Get Data → Snowflake is the connection path.
- Use the full account URL as the server.
- DirectQuery is the recommended mode for Snowflake.
- The Navigator lets you pick tables and views.

## What's next

L177 — Working in Power BI. We build a small dashboard.