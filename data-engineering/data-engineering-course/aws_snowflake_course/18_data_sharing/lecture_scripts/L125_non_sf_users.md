---
l_id: L125
title: Sharing with non-snowflake users
duration: "5:00"
prereqs: ["L124"]
---

# L125 — Sharing with non-snowflake users

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 18 — Data Sharing
> **Duration:** 5:00

## Prereqs

L124 — Create share through the interface.

## Key terms

- **Reader account** — a Snowflake-managed account, owned by you,
  that a non-Snowflake consumer uses to query your shares.
- **Business edition minimum** — reader accounts require the
  producer account to be on Business Critical (or above) edition.
- **Non-Snowflake consumer** — a partner or customer who has not
  signed a Snowflake contract themselves.

## Lecture

Welcome back. So far our consumer has been *another Snowflake
account*. That's the easy case — they already have an account
locator, Snowflake handles auth and billing for them. Today we cover
the harder case: **the consumer doesn't have a Snowflake account**.

### Two options

There are exactly two ways to share data with a company that does
not have a Snowflake account:

1. **They sign up.** You wait for them to provision an account,
   then share with them using their account locator.
2. **You provision them a *reader account*.** You create a managed
   Snowflake account on their behalf, hand them login credentials,
   and share your data into it.

Option 2 is what most B2B data vendors use. The reader account is
**owned by your organization** — you control its lifecycle, you can
shut it down, and Snowflake bills *you* for its compute and storage.

### What a reader account can do

A reader account can:

- query the shares you give it
- run warehouses to power those queries
- create users, databases-from-shares, and basic objects

A reader account **cannot**:

- load data
- create new shares outward
- run `CREATE DATABASE` for non-share objects
- use most edition-only features (depends on edition)

### When to use a reader account

Reader accounts shine when:

- you sell a *data product* and your customers just want to query
- you need to give a regulatory body read-only access
- you're prototyping a partnership and the partner isn't ready to
  commit to a Snowflake contract

They are **not** appropriate when the consumer has any serious data
ingestion needs; in that case, push them toward getting their own
account.

### A typical reader-account lifecycle

1. Producer creates reader account (L126).
2. Producer shares data with the reader account using its locator.
3. Consumer logs in with credentials the producer created.
4. Consumer creates databases from shares, runs queries.
5. Producer can suspend / resume the reader account's warehouses
   at will.
6. Producer can drop the reader account when the relationship ends.

The lifecycle is fully under the producer's control.

### Limits

- Reader accounts are limited to a subset of editions.
- Reader account compute is billed to the producer at the
  Snowflake credit rate for the producer's edition.
- Reader accounts cannot be used to share *out* to other accounts.

## Hands-on

A reader account is a privileged action; we walk through the SQL
in the next lecture. For now, confirm your account edition:

```sql
SELECT CURRENT_ACCOUNT() AS acct,
       CURRENT_REGION()   AS region;
SHOW PARAMETERS LIKE 'ACCOUNT_EDITION';
-- "VALUE" should be at least BUSINESS_CRITICAL to create reader accounts.
```

## Key takeaways

- Reader accounts let you share data with non-Snowflake consumers.
- The reader account is owned by *you*; you bill the consumer
  yourself.
- Reader accounts are read-mostly: query, no loading.
- They require Business Critical edition or higher.

## What's next

L126 walks through `CREATE MANAGED ACCOUNT` — the one-liner that
provisions a new reader account.