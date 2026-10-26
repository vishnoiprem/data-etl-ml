---
l_id: L18
title: Cloud computing
duration: "5:00"
prereqs: ["L17"]
downloads: []
---

# L18 — Cloud Computing

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 3 — Snowflake Architecture
> **Duration:** ~5:00

## Prereqs

L17 — What is a data warehouse? This is a short context
lecture.

## Key terms

- **IaaS** — Infrastructure as a Service. You rent raw VMs and
  storage (EC2, S3, Azure VMs, GCE). Snowflake runs on top of
  IaaS.
- **PaaS** — Platform as a Service. You rent a managed platform
  (RDS, BigQuery, Snowflake). Less control, less work.
- **SaaS** — Software as a Service. You rent a finished
  application (Salesforce, Slack, Snowflake's web UI).
- **Region** — a geographic area where a cloud provider has
  one or more data centers. Pick a region close to your data
  source.
- **Cross-region** — Snowflake supports cross-region
  replication and replication groups for DR.

## Lecture

Snowflake is fundamentally a **PaaS** offering on top of
**IaaS**. This lecture explains the layering so the
multi-cloud deployment story makes sense.

### The cloud computing stack

```text
┌──────────────────────────────────────┐
│  SaaS         (apps you use)         │
│  ─ Salesforce, Slack, Snowflake UI   │
├──────────────────────────────────────┤
│  PaaS         (managed platforms)    │
│  ─ Snowflake, BigQuery, RDS, Redshift│
├──────────────────────────────────────┤
│  IaaS         (raw infrastructure)   │
│  ─ EC2, S3, Azure VMs, GCE           │
├──────────────────────────────────────┤
│  Hardware     (data centers)         │
└──────────────────────────────────────┘
```

Snowflake sits in the **PaaS** layer but is built on top of
**IaaS**. That's why Snowflake can run on AWS, Azure, or GCP
— it uses whatever IaaS is underneath.

### Snowflake on three clouds

| Cloud | Storage | Compute | Notes |
|---|---|---|---|
| AWS | S3 | EC2 | Original; most features first |
| Azure | ADLS Gen2 | Azure VMs | Tight ADLS integration |
| GCP | GCS | GCE | Newest; BigQuery Omni is the competing service |

A Snowflake **account** is created on a single cloud/region
at signup. You can't have one account spanning multiple
clouds — you'd need separate accounts and Snowflake's data
sharing to move data between them.

### Region selection

Pick the region **closest to your data source**. Cross-region
data transfer is billed and adds latency. If your data lives
in `us-east-1`, run Snowflake in `us-east-1`.

### Multi-cloud strategies

Two common patterns:

1. **Single-cloud.** All your data is in S3, all your
   compute is in AWS. Simplest.
2. **Multi-cloud via sharing.** You have accounts in AWS
   (production) and Azure (for a partner who uses Azure
   tools). Share data cross-cloud via Snowflake's data
   sharing — no actual data movement.

### What Snowflake manages for you

When you use Snowflake, the things you **don't** worry about:

- OS patching on the warehouse nodes
- Disk failures (S3 has 11 nines of durability)
- Database software upgrades
- Query planner bug fixes
- Backup/restore (Time Travel + Fail-safe)
- Index maintenance (Snowflake's pruning is automatic)
- Statistics collection (automatic on every load)

What you **do** worry about:

- Warehouse sizing
- Query design
- Data model
- Cost controls (resource monitors)
- Access control (RBAC)

## Hands-on

No lab. This is a context lecture.

## Quiz prep

- What is the difference between IaaS, PaaS, and SaaS? (IaaS
  = raw infra; PaaS = managed platform; SaaS = finished app)
- Which three clouds does Snowflake run on? (AWS, Azure, GCP)
- What does Snowflake manage for you? (Patching, backups,
  upgrades, indexing, statistics)

## What's next

Next up is **L19 — Snowflake editions**, where we cover the
five edition tiers (Standard through VPS) and the features
each unlocks.
