# Section 3 — Snowflake Architecture

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Lectures:** L15–L23
> **Duration:** ~57 min

This section goes deeper into Snowflake's architectural
decisions and the **operational** side of running a Snowflake
account. We cover the **table/database/schema hierarchy**, the
**three loading patterns** (bulk, Snowpipe, manual), the
**data warehouse** context, **cloud computing** basics, the
**five editions** (Standard → VPS), the **pricing model**
(compute credits + storage), **storage and transfer costs**,
**monitoring with `ACCOUNT_USAGE`**, and **resource monitors**
(credit caps).

By the end of this section you should understand the
cost model, be able to estimate a monthly bill, and have set
up resource monitors to prevent runaway charges.

| L# | Title | Min |
|---|---|---|
| L15 | Exploring tables & databases | 8:00 |
| L16 | Loading data in Snowflake (intro) | 6:00 |
| L17 | What is a data warehouse? | 5:00 |
| L18 | Cloud computing | 5:00 |
| L19 | Snowflake editions | 7:00 |
| L20 | Snowflake pricing | 9:00 |
| L21 | Data Storage & Transfer Cost | 7:00 |
| L22 | Monitor Usage | 8:00 |
| L23 | Resource Monitors + Setting up | 8:00 |

## Key concepts you'll need later

- **Three loading patterns** — `COPY INTO` (batch), Snowpipe
  (auto-ingest), manual UI wizard.
- **Editions ladder** — Standard < Enterprise < Business Critical < VPS.
- **Two main cost drivers** — compute credits (per second) +
  storage (per compressed TB per month).
- **Cloud services billing** — only when services usage > 10%
  of warehouse compute (usually free).
- **Resource monitors** — credit caps with NOTIFY / SUSPEND
  triggers at thresholds.
- **`ACCOUNT_USAGE` views** — historical metadata, 1-year
  retention, 3-hour latency.

## What comes next

Section 4 is **Loading Data** — we cover **roles in
Snowflake** (RBAC), the loading methods (`COPY INTO`,
Snowpipe), **stages**, **file formats**, and the
**transformations** you can apply during load. By L32 you'll
have loaded CSV and JSON files end-to-end.