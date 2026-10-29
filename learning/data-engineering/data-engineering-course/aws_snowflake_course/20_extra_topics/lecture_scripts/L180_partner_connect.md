---
l_id: L180
title: Partner Connect
duration: "4:30"
prereqs: ["L179"]
---

# L180 — Partner Connect

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 6. BI Tools
> **Duration:** 4:30

## Prereqs

L179 — Connect Tableau & Snowflake.

## Key terms

- **Partner Connect** — Snowflake's in-Snowsight "one
  click" installer for third-party tools.
- **Trial account** — the partner offers a 30-day trial
  account, billed through Snowflake.
- **Pre-configured connection** — the partner tool
  already has your warehouse, role, and credentials set
  up by the time you log in.

## Lecture

Welcome back. Today's lecture is **Partner Connect** —
Snowflake's one-click installer for BI tools, notebooks,
and other integrations. If you skipped the manual
Power BI and Tableau setups in L175–L179, Partner Connect
gets you connected in two minutes.

### What Partner Connect does

Partner Connect is a directory of pre-integrated tools
inside Snowsight. For each tool (Power BI, Tableau,
Looker, Hex, Sigma, Mode, ...), Snowflake offers:

- A 30-day free trial of the tool, billed through your
  Snowflake account.
- A pre-configured connection to your Snowflake
  warehouse.
- A pre-created `SYSADMIN` service account dedicated to
  the tool.

The user flow:

1. Open Snowsight → **Data** → **Partner Connect**.
2. Pick a tool (e.g. Power BI).
3. Click **Connect**. Snowflake:
   - Creates a service account (e.g. `POWERBI_SVC_USER`).
   - Sets the warehouse, role, and credentials.
   - Spins up the partner's trial.
4. You get a URL and credentials for the partner tool.
5. Log in, and the partner is already connected to your
   Snowflake data.

### The trial model

The first 30 days are free. After that:

- The partner tool starts billing your Snowflake account
  (via Snowflake's billing system).
- Or the trial ends and the connection breaks until you
  upgrade.

For personal learning, the 30-day trial is enough. For
production, you migrate to a paid plan with the partner.

### The pre-configured service account

Partner Connect creates a user like `POWERBI_SVC_USER` or
`TABLEAU_SVC_USER`. The user:

- Has `SYSADMIN` privileges (so it can read everything).
- Is dedicated to the tool — no human uses these
  credentials.
- Should be rotated quarterly in production.

To see what Partner Connect created:

```sql
SHOW USERS LIKE '%SVC%';
-- Or specifically:
SHOW USERS LIKE 'POWERBI_SVC_USER';
```

### Removing a Partner Connect integration

```sql
-- Drop the service user
DROP USER POWERBI_SVC_USER;
```

After this, the partner tool's connection breaks on its
next refresh. The 30-day trial is also cancelled; you'll
get a confirmation email.

### When to use Partner Connect

- **First-time setup.** Get connected in 2 minutes
  instead of 20.
- **Evaluating tools.** If you're choosing between Power
  BI, Tableau, and Looker, Partner Connect lets you try
  each without commitment.
- **Demo accounts.** For sales demos and training.

When NOT to use it:

- **Production.** The pre-configured service account
  has `SYSADMIN`, which is too broad. Production should
  use a custom role.
- **Cost control.** Partner Connect auto-bills through
  Snowflake; in a tight cost-control environment, you
  may want to manage the partner relationship directly.

## Hands-on

```sql
-- Inspect what Partner Connect created
SHOW USERS;
-- Look for: POWERBI_SVC_USER, TABLEAU_SVC_USER, etc.

-- Show their grants
SHOW GRANTS TO USER POWERBI_SVC_USER;

-- Clean up (after the trial)
DROP USER POWERBI_SVC_USER;
```

The actual "click in Snowsight" walkthrough is part of
the lesson material; see the lecture video.

## Key takeaways

- Partner Connect is the one-click install for BI tools
  and integrations.
- It creates a service account, sets up the warehouse,
  and starts a 30-day trial.
- Use it for evaluation; for production, replace the
  service account with a custom role.
- Drop the service user to disconnect.

## What's next

L181 — Snowflake Marketplace. The data-product catalog and
a free way to consume real shares.