---
l_id: L179
title: Connect Tableau & Snowflake
duration: "5:00"
prereqs: ["L178"]
---

# L179 — Connect Tableau & Snowflake

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 6. BI Tools
> **Duration:** 5:00

## Prereqs

L178 — Download & install Tableau. Tableau Desktop should
be running.

## Key terms

- **Connect → Snowflake** — the connection entry in
  Tableau.
- **Server** — `your_locator.snowflakecomputing.com`.
- **Authentication** — username + password, or SSO via
  OAuth.
- **Live vs Extract** — Tableau's analogue of
  DirectQuery vs Import.

## Lecture

Welcome back. Today's lecture is the Tableau-to-Snowflake
connection, mirroring L176 for Power BI. By the end, you
should have a Tableau data source pointing at Snowflake.

### The connection steps

1. Open Tableau Desktop. In the left "Connect" panel,
   click **Snowflake**.
2. A dialog opens. Enter:
   - **Server**: `your_locator.snowflakecomputing.com`
   - **Authentication**: Username and Password (or OAuth)
   - **Username** / **Password**
3. Click **Sign In**. Tableau asks which warehouse to
   use.
4. Pick the warehouse (e.g. `compute_wh`).
5. Tableau shows the schema browser. Drill into the
   schema, drag the table you want into the canvas.

### Live vs Extract

After dragging a table, Tableau prompts you to choose
**Live** or **Extract**:

- **Live** — every visual issues a fresh `SELECT` to
  Snowflake. (Tableau's equivalent of DirectQuery.)
- **Extract** — Tableau materializes the data into its
  in-memory engine; refreshes on a schedule. (Equivalent
  of Power BI's Import.)

For Snowflake, **Live** is the recommended default.

### A small dashboard

Tableau's pattern for visuals:

- Drag a dimension to **Columns** (becomes the X axis).
- Drag a measure to **Rows** (becomes the Y axis).
- Drag a measure to **Color** for color-coding.
- Drag a measure to **Size** for sizing marks.

A simple bar chart:

1. Drag `O_ORDERSTATUS` to **Columns**.
2. Drag `SUM(O_TOTALPRICE)` to **Rows**.
3. Drag `SUM(O_TOTALPRICE)` to **Color** (optional).

A line chart:

1. Drag `O_ORDERDATE` to **Columns** (Tableau
   auto-aggregates by year).
2. Drag `SUM(O_TOTALPRICE)` to **Rows**.

### Publishing

Tableau Desktop saves `.twb` files locally. To share:

- **Tableau Public** — File → Save to Tableau Public.
  The workbook is now on the public web. Only for
  public data.
- **Tableau Server / Cloud** — File → Publish. Requires
  a paid license.

For company data, the workbook lives on Tableau Server
(or Cloud) and is shared via permissions.

### A common error: warehouse

If you don't have a default warehouse, Tableau's
connection may hang. Pick `compute_wh` (or your
workhorse warehouse) explicitly during the connection.

## Hands-on

1. Open Tableau Desktop.
2. Connect → Snowflake.
3. Server: `<your_locator>.snowflakecomputing.com`.
4. Username + password authentication.
5. Pick `compute_wh` as the warehouse.
6. Drag `SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS` to the
   canvas.
7. Choose **Live** connection.
8. Build a bar chart of `SUM(O_TOTALPRICE)` by
   `O_ORDERSTATUS`.

## Key takeaways

- Connect → Snowflake in Tableau is the entry point.
- Use Live connection for Snowflake (Tableau's
  DirectQuery equivalent).
- Dimensions to Columns; measures to Rows; that's the
  default.
- Tableau Public is free for public workbooks; Server
  / Cloud is paid.

## What's next

L180 — Partner Connect. Snowflake's one-click install for
BI tools and other integrations.