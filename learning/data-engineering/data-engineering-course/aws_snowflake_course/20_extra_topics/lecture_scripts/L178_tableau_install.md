---
l_id: L178
title: Download & install Tableau
duration: "4:30"
prereqs: ["L177"]
---

# L178 — Download & install Tableau

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 6. BI Tools
> **Duration:** 4:30

## Prereqs

L177 — Working in Power BI. Power BI concepts are
transferable; today is the Tableau equivalent.

## Key terms

- **Tableau Desktop** — the authoring tool. Free trial;
  paid license.
- **Tableau Public** — the free version with public
  publishing only.
- **Tableau Server / Cloud** — the platform for sharing
  dashboards across a team.
- **Tableau workbook** — the `.twb` or `.twbx` file that
  contains a Tableau report.

## Lecture

Welcome back. Today's lecture is the Tableau install. By
the end, you should have Tableau Desktop running and
ready to connect to Snowflake.

### The download

1. Go to `https://www.tableau.com/products/desktop`.
2. Click **Try Tableau Desktop for free** (14-day trial).
3. Or click **Tableau Public** for the free, public-only
   version.
4. Run the installer.

Tableau Desktop is available on Windows and macOS. Tableau
Public is also cross-platform.

### The license modes

- **Tableau Public** — free; all workbooks are publicly
  published on the Tableau Public website. Cannot connect
  to private data sources.
- **Tableau Desktop (trial)** — 14-day free trial with
  full features.
- **Tableau Desktop (paid)** — full features, paid
  annually.
- **Tableau Cloud / Server** — sharing platform, paid.

For this course, Tableau Public is enough for personal
work. For company data, you need a paid Desktop or Server
license.

### The interface

Tableau's interface is two main areas:

- **Data Source** page (left tab) — where you connect to
  the database and pick tables.
- **Sheet** pages (right tabs) — where you build visuals.

A Tableau "workbook" is a collection of sheets. The
`.twb` file is the XML; `.twbx` is the packaged form
(including data, for offline sharing).

### Verifying the install

Launch Tableau. You should see the start screen with
"Connect" options on the left. **Snowflake** is in the
"To a Server" list.

If Snowflake is not in the list, your version is old.
Update to a recent version (Tableau 2020+).

### The Snowflake driver

Recent Tableau versions ship the Snowflake connector
natively; no ODBC install needed. If you see "Driver
not found", install the Snowflake ODBC driver from
`https://sfc-repo.snowflakecomputing.com/odbc/`.

## Hands-on

1. Download Tableau Desktop (or Tableau Public) from
   `https://www.tableau.com/products/desktop`.
2. Install with default options.
3. Launch and confirm "Snowflake" is in the Connect list.

## Key takeaways

- Tableau Desktop has a 14-day free trial; Tableau Public
  is free for public workbooks.
- Cross-platform — Windows and macOS.
- Snowflake connector is built into recent versions.
- A workbook is a `.twb` or `.twbx` file.

## What's next

L179 — Connect Tableau & Snowflake. The connection walk-
through, mirroring L176.