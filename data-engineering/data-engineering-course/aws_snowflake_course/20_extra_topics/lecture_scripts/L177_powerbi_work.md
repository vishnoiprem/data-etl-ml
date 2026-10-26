---
l_id: L177
title: Working in Power BI
duration: "5:00"
prereqs: ["L176"]
---

# L177 — Working in Power BI

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 6. BI Tools
> **Duration:** 5:00

## Prereqs

L176 — Connect Power BI & Snowflake. Power BI Desktop should
have the ORDERS table loaded.

## Key terms

- **Visual** — a chart, table, or KPI in a Power BI report.
- **Field** — a column from a table, dragged into a visual.
- **Measure** — a calculated value (`SUM(amount)`, etc.).
- **DAX** — the formula language for measures.

## Lecture

Welcome back. Today's lecture is a small working dashboard
in Power BI, sourced from Snowflake. By the end, you'll
have a report with three visuals: a card, a bar chart, and
a line chart.

### The data model

We connected to `ORDERS` from the TPC-H sample dataset in
L176. The table has these columns (among others):

- `O_ORDERDATE` — date
- `O_TOTALPRICE` — order total
- `O_ORDERSTATUS` — status
- `O_ORDERPRIORITY` — priority

Power BI imports the table as-is. No need to flatten.

### Visual 1: a card showing total revenue

1. In the **Visualizations** pane, click the **Card** icon.
2. From the **Data** pane, drag `O_TOTALPRICE` into the
   "Fields" well.
3. Power BI auto-creates a `SUM(O_TOTALPRICE)` measure.
4. The card shows the grand total.

A "card" is a single big number. It's the most common way
to surface a KPI.

### Visual 2: a bar chart by order status

1. Click the **Clustered column chart** icon.
2. Axis: drag `O_ORDERSTATUS`.
3. Value: drag `O_TOTALPRICE`.

You should see a bar chart with one bar per order status,
the height being the total revenue for that status.

### Visual 3: a line chart over time

1. Click the **Line chart** icon.
2. Axis: drag `O_ORDERDATE`.
3. Value: drag `O_TOTALPRICE`.

A line chart over time is the second most common BI
pattern. Adjust the date hierarchy to "Year" or "Month" if
the daily view is too granular.

### A simple measure with DAX

```dax
Total Revenue = SUM(ORDERS[O_TOTALPRICE])
Avg Order Value = AVERAGE(ORDERS[O_TOTALPRICE])
```

In the data pane, click **New measure** and type the
formula. The measure is now available in any visual.

### DirectQuery behavior

Because we connected in DirectQuery mode, every visual
issues a fresh `SELECT` to Snowflake. You can verify:

1. Go to Snowflake's **Query History** in Snowsight.
2. Each visual in your Power BI report corresponds to one
   or more `SELECT` queries.

This is the live-data property. The trade-off: the dashboard
is only as fast as Snowflake's response time.

### Save and publish

1. **File → Save** to save the `.pbix` file locally.
2. **Publish → Publish to Power BI** to upload to the
   Power BI Service.
3. Sign in if prompted.
4. The dashboard is now in "My workspace" in Power BI
   Service.

To share with the team, you need a Pro license. The free
license is enough for personal use.

## Hands-on

Build the three visuals above using the TPC-H ORDERS
table. Save the `.pbix` file. Publish to Power BI
Service.

## Key takeaways

- Power BI visuals: drag fields into the visual's wells.
- Cards, bar charts, and line charts are the workhorse
  three.
- DAX is the formula language for measures.
- DirectQuery means every visual issues a live query to
  Snowflake.

## What's next

L178 — Download & install Tableau. The Tableau half of the
BI sub-group.