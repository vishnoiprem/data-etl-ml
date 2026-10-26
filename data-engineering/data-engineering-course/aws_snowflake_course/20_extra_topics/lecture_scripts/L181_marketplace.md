---
l_id: L181
title: Snowflake Marketplace
duration: "4:30"
prereqs: ["L180"]
---

# L181 — Snowflake Marketplace

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 6. BI Tools
> **Duration:** 4:30

## Prereqs

L180 — Partner Connect.

## Key terms

- **Marketplace** — Snowflake's catalog of data products
  offered by providers and third parties.
- **Free listing** — most listings are free; you only pay
  for the compute to query them.
- **Paid listing** — providers can charge for access.
- **Personalized data** — some listings are "personalized
  for your account" — the provider's data is enriched
  with your Snowflake data without either side copying
  the data.

## Lecture

Welcome to the last lecture in the BI Tools sub-group.
Today's lecture is the **Snowflake Marketplace** — a
catalog of data products you can mount as a database in
your account with a few clicks. By the end, you should
be able to find, consume, and use a Marketplace dataset.

### What the Marketplace is

The Marketplace is a curated catalog of data listings from
third-party providers — weather data, demographics, stock
prices, financial reference data, anonymized behavioral
data, and more. Each listing is a Snowflake share from the
provider to subscribers.

```text
Snowflake Marketplace
├── weather (NOAA-like, free)
├── demographics (US Census, free)
├── finance (stock prices, free tier)
├── marketing (anonymized panel data, paid)
└── ...
```

A listing is essentially a share from the provider's
account to yours. You mount it the same way you mount a
share (L127):

```sql
CREATE DATABASE <db_name> FROM SHARE <provider_locator>.<share_name>;
```

The Marketplace handles the locator lookup for you.

### The trial model

Most listings are free. The provider covers storage; you
cover the compute. Some listings are paid; the provider
charges a subscription fee through Snowflake's billing.

### The personalized data mode

The most powerful feature of the Marketplace: **personalized
data**. The provider's data is joined with your data
*inside Snowflake*, without either side copying the data
or seeing the other side's data.

A typical example: a marketing panel with anonymized
customer behavior. The provider has a "join with your
first-party data" mode; you provide a hashed email
column; the join happens inside Snowflake, and the
provider never sees your raw data.

### How to consume a listing

1. Open Snowsight → **Data** → **Marketplace**.
2. Browse or search for a listing.
3. Click **Get** (for free listings) or **Subscribe**
   (for paid).
4. Snowflake creates the share in your account. You see
   the new database in your **Data** page.
5. `USE <database>.public;` and start querying.

### A real listing: the TPC-H sample

The `SNOWFLAKE_SAMPLE_DATA.TPCH_SF1` database we've been
using throughout the course is, in fact, a Marketplace
listing. You can mount it from a different account
identifier to see how the mechanism works.

### When to use the Marketplace

- **Reference data.** Currency rates, country codes, US
  zip → lat/lon.
- **Demographics and weather.** Common enrichments for
  analytics.
- **Anonymized panel data.** Audience analytics without
  PII.
- **Industry benchmarks.** Anonymized financial ratios,
  retail comps, etc.

When NOT to use it:

- **Sensitive data.** Don't consume free listings that
  include your customers' PII.
- **Real-time data.** Most listings are daily or
  hourly. For real-time, use an API.

## Hands-on

```sql
-- Confirm the TPC-H sample is a Marketplace listing
SHOW DATABASES;
-- The SNOWFLAKE_SAMPLE_DATA database is provisioned automatically;
-- it's effectively a Marketplace share that Snowflake itself publishes.

SELECT * FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.NATION LIMIT 5;
```

For a real Marketplace exercise: Snowsight → Data →
Marketplace → search "weather" → get the NOAA listing →
query the result.

## Key takeaways

- The Marketplace is a catalog of shares from third-party
  providers.
- Most listings are free; you pay for compute.
- Personalized data joins happen inside Snowflake without
  exposing either side's raw data.
- The `SNOWFLAKE_SAMPLE_DATA` you've been using is itself
  a Marketplace listing.

## What's next

We close the BI Tools sub-group and move on to **Best
Practices & Bonus** (L182–L187), the final 6 lectures of
the course.