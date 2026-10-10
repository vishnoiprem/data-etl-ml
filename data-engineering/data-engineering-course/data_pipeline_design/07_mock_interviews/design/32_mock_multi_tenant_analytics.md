# 32 — Mock Interview: Design a Multi-Tenant SaaS Analytics Platform

> **Lesson 32 of 32 — Mock Interviews**

A full 30-minute mock interview with a candidate designing a
multi-tenant analytics platform with row-level security. The
candidate is a Staff Data Engineer (L6 level). The scenario covers
tenant isolation, query routing, cost attribution, and the
"noisy neighbor" problem.

---

## Setup

**Company:** B2B SaaS in the data / analytics space (hypothetical).
**Role:** Staff Data Engineer.
**Level:** L6.
**Format:** 30-minute system design round, on-site whiteboard.
**Question:** *"Design a multi-tenant analytics platform for 500
customers. Each customer must only see their own data. We have
10B events per day. Queries must complete in under 5 seconds."*

---

## Transcript (30 minutes)

### 0:00 — Opening framing

> **Candidate:** Multi-tenant analytics has three load-bearing
> questions. Let me make sure I have the requirements right
> before I draw.
>
> First, what's the *shape* of a tenant? Are they all similar
> size (a few thousand events per day each), or do we have power
> tenants (one tenant is 50% of the volume)? That changes the
> architecture dramatically.
>
> Second, the latency target — "under 5 seconds" — is that p50,
> p95, or p99? And is that for a single dashboard load with
> 10 widgets, or for one query at a time?
>
> Third, the isolation guarantee — "each customer must only see
> their own data." Is that a contractual guarantee (SLA), a
> regulatory one (SOC2, HIPAA, GDPR), or just a product
> requirement? Because the architecture changes if a leak is a
> breach report vs a customer complaint.

> **Interviewer:** Assume one tenant is 10x the average. So top
> 10 tenants are 50% of the volume. p95 is the latency target;
> one query at a time (the dashboard does a few separate
> queries). The isolation is contractual + SOC2 — a leak is a
> breach.

> **Candidate:** Three big decisions then:
>
> 1. **Tenant skew.** 10x skew is real but not extreme. Most
>    B2B SaaS sees 50-100x. We can handle 10x with query routing
>    + dedicated resources for the top tenants.
> 2. **p95 = 5s.** That's tight. It rules out full table scans on
>    the whole dataset. We need aggressive indexing and per-tenant
>    partitions.
> 3. **SOC2-level isolation.** Row-level security is the right
>    level; we don't need separate databases per tenant (that's
>    overkill at 500 tenants).

### 3:00 — High-level architecture

> **Candidate:** Six boxes. **[DRAWING 1]**

```
┌────────────┐   ┌──────────────┐   ┌──────────────┐   ┌────────────┐
│ Customer   │──►│ API gateway  │──►│ Query        │──►│ Warehouse  │
│ (browser)  │   │ (auth,       │   │ router       │   │ (Snowflake │
└────────────┘   │  rate limit) │   │ (Python /    │   │  per-tenant│
                 └──────────────┘   │  GraphQL)    │   │  schema)   │
                                   └──────┬───────┘   └─────┬──────┘
                                          │                 │
                                          ▼                 ▼
                                   ┌──────────────┐   ┌────────────┐
                                   │ Cache        │   │ Tenant     │
                                   │ (Redis)      │   │ metadata   │
                                   │              │   │ + RLS      │
                                   └──────────────┘   └────────────┘
                                          ▲
                                          │
                                   ┌──────────────┐
                                   │ Ingest path: │
                                   │ Kafka → Spark│
                                   │ → Iceberg    │
                                   │ per tenant   │
                                   └──────────────┘
```

> **Candidate:** Five components:
>
> 1. **Ingest.** Kafka → Spark → Iceberg on S3, partitioned by
>    `tenant_id` *and* `event_date`. Per-tenant partitioning is
>    the key to fast queries.
> 2. **Warehouse.** Snowflake (or BigQuery) with a per-tenant
>    schema and row-level security policies.
> 3. **Query router.** A stateless Python / GraphQL service that
>    authenticates the user, looks up their tenant, and rewrites
>    queries to include the `tenant_id` predicate.
> 4. **Cache.** Redis with a per-tenant, per-query-hash key. p95
>    for the top dashboards drops from 5s to 50ms after a warm
>    cache.
> 5. **Tenant metadata.** A Postgres table of tenants, owners,
>    quotas, RLS roles.

### 6:00 — Back-of-envelope estimation

> **Candidate:** 10B events / day, average event size 1 KB
> compressed = 10 TB / day raw. At 4x compression in Parquet,
> that's 2.5 TB / day on S3, 900 TB / year of growth.
>
> At 500 tenants, average 20M events / day per tenant. Top
> tenant = 200M events / day, top-10 = 1B events / day, the rest
> average ~ 18M / tenant.
>
> Cost:
> - S3 + Iceberg: $20K / month
> - Snowflake: $30K-60K / month (depends on warehouse size +
>   query volume)
> - Cache (Redis): $2K / month
> - Query router: $1K / month
>
> Total: ~$60K-80K / month. Charge customers $500-50K / month
> based on volume. Healthy margin at the top tier.

### 8:00 — Deep dive #1: tenant isolation strategies

> **Interviewer:** Walk me through the tenant isolation choices.
> Separate DB per tenant vs shared with row-level security.

> **Candidate:** Three patterns. **[DRAWING 2]**

```
Pattern A: separate database per tenant
  tenant_42_db (Postgres / Snowflake)
  tenant_77_db
  ...
  Pros: perfect isolation. Simple mental model.
  Cons: 500 DBs = 500 connection pools, 500 cost reports, 500
        migration pipelines. Doesn't scale past ~50 tenants.

Pattern B: shared schema + row-level security (RLS)
  one database, one schema, every row has tenant_id.
  query: SELECT * FROM events WHERE tenant_id = current_tenant()
  Pros: operational simplicity. Single migration, single pool.
  Cons: noisy neighbor. One tenant's slow query can starve others.
        Risk: a query without the tenant_id predicate leaks data.

Pattern C: shared schema + per-tenant partition
  one database, but each tenant's data is in its own partition.
  query pushdown: WHERE tenant_id = 42 → only partition 42 is scanned.
  Pros: fast (no full scan). Cheap (per-tenant cost reporting).
  Cons: 500 partitions = 500 partition operations on ingest.
        Schema changes are 500x.
```

> **Candidate:** The right answer in 2026 is **B (shared + RLS)
> with C-style partition pruning**. Every row has `tenant_id`;
> every table is partitioned on `tenant_id`; the partition
> pruner kicks in for every query. The query router does two
> things: **[DRAWING 3]**
>
> ```python
> # What the query router does on every request:
> def route_query(user, sql):
>     tenant_id = user.tenant_id
>     rewritten = sql.replace(
>         "FROM events",
>         f"FROM events PARTITION (tenant_id = {tenant_id})"
>     )
>     # ... or inject RLS predicate:
>     rewritten = inject_rls_predicate(rewritten, tenant_id)
>     result = warehouse.execute(rewritten)
>     return result
> ```
>
> The router **never trusts user input**. It's the only component
> that's allowed to talk to the warehouse without RLS — and even
> then, it uses the customer's Snowflake role, not a super-admin
> role, so the warehouse itself enforces the policy.
>
> Belt-and-suspenders: even if the router is buggy, the warehouse
> role's RLS policy rejects the query.

### 13:00 — Deep dive #2: query routing and the noisy neighbor

> **Interviewer:** A 10x tenant runs a query that takes 30
> seconds. What happens to the other 499 tenants?

> **Candidate:** Three problems. **[DRAWING 4]**
>
> **First, query latency.** A 30-second query holds a warehouse
> slot. The other tenants queued behind it see their p95 spike.
> Mitigation: per-tenant concurrency limits. Each tenant gets
> at most 2 concurrent queries. The 10x tenant's third query
> gets queued.
>
> **Second, query cost.** A 30-second query on a 100 GB partition
> costs $5 in Snowflake. The other 499 tenants don't directly pay
> for that — but the *platform* does. We attribute the cost to
> the tenant that ran it. The cost-attribution report shows
> the top 10 tenants by Snowflake-credit consumption.
>
> **Third, fairness at the platform level.** If the 10x tenant
> does this repeatedly, they're effectively getting a
> bigger-than-paid-for warehouse. Mitigation: tier-based
> concurrency. The platform tier gets 2 concurrent queries;
> the enterprise tier gets 10; a custom tier gets negotiated
> concurrency. The contract is the throttle.
>
> The query router has a `ConcurrencyGuard`:
>
> ```python
> if get_active_queries(tenant_id) >= tenant.concurrency_limit:
>     return reject_with_429()
> ```
>
> And the warehouse runs as a *multi-cluster* warehouse — at peak
> we scale to 5 clusters, each tenant pinned to at most 2. The
> noisy neighbor gets queued, not starved.

### 18:00 — Deep dive #3: cost attribution

> **Interviewer:** How do you bill customers for what they
> actually use?

> **Candidate:** Three layers of metering. **[DRAWING 5]**
>
> **Layer 1: storage.** Each tenant's Parquet partition has a
> known size (we record it on ingest). Cost = `$0.023 / GB / month`.
> We sum across all of a tenant's partitions.
>
> **Layer 2: ingest.** Each event is 1 KB; we count them at
> ingest time. Cost = `$0.10 / million events`. This is the
> volume tax.
>
> **Layer 3: query.** Every query is logged with `tenant_id`,
> query duration, bytes scanned. Cost = `$5 / TB scanned`. We
> aggregate per tenant per month.
>
> The dashboard shows the customer their live spend and a
> projection. Most customers don't care; the top 5 customers
> care a lot. The CFO of a 10x tenant wants a monthly invoice
> that matches. The platform CFO wants the same data, broken
> down by tenant, to make sure the platform is profitable.
>
> A monthly reconciliation job: `SUM(customer_invoices) ==
> SUM(warehouse_costs) + SUM(s3_costs) + SUM(kafka_costs)`. Drift
> > 5% pages the on-call. The reconciliation is *the* financial
> system of record.

### 23:00 — Failure modes

> **Interviewer:** Five failure modes.

> **Candidate:** Five. **[DRAWING 6]**
>
> One, **tenant leakage.** A query without `tenant_id` returns
> rows from other tenants. Mitigation: test suite that asserts
> every API endpoint injects the predicate; the warehouse RLS
> policy rejects queries without it. A leak is a breach.
>
> Two, **noisy neighbor.** The 10x tenant runs a 60-second
> query. Other tenants wait. Mitigation: per-tenant concurrency
> limits + multi-cluster warehouse.
>
> Three, **ingest lag.** A Kafka broker is overloaded; ingest
> is 30 minutes behind. Mitigation: per-tenant ingest lag
> monitored; alert at 5 minutes; on-call pages at 30 minutes.
> Backfill is a separate batch job.
>
> Four, **cost bomb.** A customer leaves a dashboard open that
> runs an expensive query every 10 seconds. Mitigation: query
> rate limit per tenant; cost dashboard for the customer;
> the customer gets a friendly email at 80% of their quota.
>
> Five, **schema break.** A tenant sends a new event type we
> didn't expect. Mitigation: schema enforcement at ingest;
> new event types are explicitly registered by the tenant;
> unknown events go to a quarantine bucket + alert.

### 28:00 — Wrap-up

> **Candidate:** The architecture is: Kafka → Spark → Iceberg
> per-tenant partition → Snowflake with RLS → Redis cache →
> query router → API. The three hard problems are isolation
> (RLS + per-tenant partition, with the query router as the
> gatekeeper), noisy neighbors (per-tenant concurrency +
> multi-cluster warehouse), and cost attribution (storage + ingest
> + query metering with a monthly reconciliation). The cost
> driver is the warehouse; the latency driver is the partition
> pruning + cache.

---

## Post-interview analysis

**What was good:**

- Three clarifying questions before drawing. The "is this SOC2
  / regulatory?" question is the senior move.
- Three isolation patterns compared; chose the hybrid clearly.
- Belt-and-suspenders isolation (router + warehouse RLS) is
  named explicitly.
- Cost attribution in three layers with the monthly reconciliation.
- Five failure modes named unprompted.
- Cost estimate at the right order of magnitude.

**What was missing:**

- **Multi-region** — 500 customers, some in EU, the data
  residency story (GDPR) wasn't addressed. The right answer
  is per-region warehouse instances, with EU customer data
  staying in EU.
- **Data deletion** (GDPR right to be forgotten) — when a
  customer churns, we have to delete their data. The Iceberg
  partition story makes this tractable (drop a partition), but
  not free (backups, audit logs).
- **Per-tenant encryption keys** — for the SOC2-priority tenants,
  bring-your-own-key (BYOK) encryption is increasingly common.
- **Per-tenant data egress prevention** — a customer who
  downloads their full dataset via the API shouldn't be able to
  exfiltrate a competitor's data via the same API.

**Score against the rubric:**

| Bucket | Score |
|---|---|
| Problem framing (15%) | 5/5 — three drivers named, SOC2 framed |
| Estimation (10%) | 5/5 — math shown, cost driver derived |
| High-level architecture (20%) | 5/5 — six boxes, all the right pieces |
| Hot-path deep dive (35%) | 5/5 — isolation, noisy neighbor, cost attribution |
| Tradeoff articulation (20%) | 4/5 — missing multi-region, GDPR deletion, BYOK |

**Overall: senior+ answer.** Would pass at L6 for a multi-tenant
SaaS analytics platform.

---

## Try it

Re-do this mock out loud. The heart of the answer is the
isolation belt-and-suspenders — router + warehouse RLS — and the
noisy-neighbor concurrency story. If you can describe those in
two sentences each, you have the framework.

---

*Author: Prem Vishnoi <prem.vishnoi@example.com>*
