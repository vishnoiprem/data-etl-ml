---
l_id: L174
title: Data Visualization (Power BI/Tableau)
duration: "4:30"
prereqs: ["L173"]
---

# L174 — Data Visualization (Power BI/Tableau)

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 6. BI Tools
> **Duration:** 4:30

## Prereqs

L173 — PUBLIC role. By now your Snowflake account is
well-structured; today we connect it to a BI tool.

## Key terms

- **ODBC / JDBC** — the two main database drivers; both
  Power BI and Tableau use them.
- **Snowflake ODBC driver** — the official Snowflake driver,
  installed by `Partner Connect` or manually.
- **DirectQuery vs Import** — the two ways a BI tool can
  connect. DirectQuery pushes each query to Snowflake;
  Import loads the data into the BI tool's own engine.
- **Snowflake connector** — Power BI's "Get Data" ships a
  Snowflake-specific connector; Tableau's too.

## Lecture

Welcome to the BI Tools sub-group. By the end of these 8
lectures you will have a working dashboard powered by
Snowflake, in either Power BI or Tableau. Today's lecture
is the high-level concepts: the two main BI tools, the two
modes (DirectQuery vs Import), and the drivers you need.

### The two big players

- **Microsoft Power BI** — Excel-friendly, strong for
  Microsoft-stack companies. Free desktop version.
- **Tableau** — analytical depth, strong for data teams.
  Tableau Public is free; Tableau Desktop requires a paid
  license.

Both connect to Snowflake via a native connector (no ODBC
configuration needed in most cases).

### The two modes: DirectQuery vs Import

- **Import mode.** The BI tool loads the data into its own
  in-memory engine. Fast dashboards; data is stale until
  the next refresh.
- **DirectQuery mode.** Every visual on the dashboard
  issues a fresh `SELECT` against Snowflake. Always
  current; the BI tool has no in-memory copy.

```text
Import mode:
   Snowflake → (periodic refresh) → Power BI engine → dashboard

DirectQuery mode:
   Snowflake ←─ (each query) ─→ Power BI ←→ dashboard
```

For Snowflake, DirectQuery is usually the right choice:
the BI tool's in-memory engine is a poor substitute for
Snowflake's columnar storage. Use Import only when the
dashboard is a self-contained "data island".

### The drivers

- **Power BI** ships a Snowflake connector in the
  "Get Data" picker. No driver install needed in most
  cases.
- **Tableau** ships a Snowflake connector as well.
  Older versions may need the Snowflake ODBC driver
  installed; current versions don't.
- **Snowflake Partner Connect** (L180) installs the
  driver and pre-configures the connection for you
  with one click.

### Authentication

Both tools support:

- **Username + password** — simplest; works for everyone.
- **OAuth / SSO** — required for production; integrates
  with your IdP (Okta, Azure AD, etc.).
- **Key-pair** — strongest; used for service accounts and
  automation.

For BI dashboards, OAuth is the standard. For scheduled
refreshes (Power BI Service, Tableau Server), use OAuth
with a service account or key-pair.

### What you'll build

By L177 (Power BI) and L179 (Tableau), you'll have:

- A Snowflake view that aggregates the data.
- A connection from the BI tool using OAuth.
- A dashboard with three visuals.
- A scheduled refresh (or, for DirectQuery, no refresh
  needed).

## Hands-on

This lecture is conceptual. The hands-on walks are in
L175–L179.

## Key takeaways

- Power BI and Tableau are the two dominant BI tools;
  both connect natively to Snowflake.
- DirectQuery vs Import: DirectQuery for live data,
  Import for self-contained dashboards.
- OAuth is the production authentication method.
- Snowflake Partner Connect simplifies setup.

## What's next

L175 — Download & install Power BI. We get the desktop tool
set up.