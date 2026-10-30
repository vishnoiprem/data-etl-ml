# Practice interview: data and AI platform PM (2026-10-28)

Saved outside the data-etl-ml repo on purpose (the repo is public).

## 1. Opener: how's your day going?
Short and positive: a couple of stand-ups to align and unblock, then good progress. Ask them back.

## 2. Tell me about yourself
PM with 15 years in data and AI. Owns the CP AXTRA (Makro and Lotus) data, AI and analytics platform, building end-to-end solutions. Before that, Lazada: lakehouse, data products, data solutions. Earlier, a couple of years in banking (governance, data quality, regulated environment). TODO: add one number (users, cost saved, revenue impact).

## 3. From scratch: first three architectural decisions
1. Storage and compute: lakehouse on object storage with an open table format (Delta or Iceberg), storage separated from compute.
2. Data modeling and layering: medallion (raw, cleaned, curated), curated data as products with owner, SLA and contract.
3. Governance and security from day one: catalog, lineage, access control, data quality checks.
Everything else (orchestration, BI) is cheaper to change later.

## 4. Delta vs Iceberg criteria
Engine compatibility, catalog (Iceberg REST vs Unity Catalog), streaming and write/CDC patterns (merge, deletion vectors, compaction), schema and partition evolution (Iceberg hidden partitioning), multi-region and cost. Decision rule: already on Databricks, so Delta by default with UniForm for Iceberg readers. Multi-vendor from day one means Iceberg with a REST catalog. Team skills count too.

## 5. Silver vs gold, and business rules vs data quality rules
- Silver: reusable, neutral, conformed entities with technical quality gates.
- Gold: purpose-built, business-interpreted data products with agreed metric logic.
- Test: reusable and neutral is silver; encodes a business interpretation is gold.
- Data quality rules (not null, types, uniqueness, RI, freshness) go in bronze to silver, owned by engineering, failures quarantined.
- Business rules (net sales, completed orders, loyalty tier) go in silver to gold, owned by the business domain and versioned in code.

## 6. Idempotency, late-arriving data, backfills in silver
- Stable business keys, MERGE (upsert), dedupe the batch by latest version (source timestamp or sequence, not arrival time).
- Only update when the incoming version is newer; soft deletes or tombstones.
- High-water mark plus lookback window; event-time watermarks for streaming; late-late data goes to reconciliation.
- Backfill: immutable bronze, replay by date or key range with the same merge, then reconcile counts, keys and checksums.
- Refresh affected gold partitions via change data feed; monitor the late-arrival rate.

## 7. Guardrails for an AI agent that edits merge logic
Agent proposes, platform enforces. Least-privilege sandbox with PR-only access; CI tests (merge fixtures, idempotency, contracts, dry run on a clone) and protected tests; policy-as-code checks; risk-tiered human approval; staged rollout with Delta time travel and git revert for rollback; full audit log.

## 8. Semantic layer for an AI agent answering business questions
Agent never writes free-form SQL on raw tables. Metrics defined once (owner, formula, grain, allowed dimensions), versioned and tested. Row-level security and column masks enforced in the catalog, queries run as the end user. Audit log of user, question, metric choice, SQL, latency, cost. Golden question set for accuracy. NOTE: be honest about which parts were actually built.

## 9. Evolving metric definitions without breaking consumers
Treat metrics like an API. Non-breaking changes ship directly; breaking changes get a new version (net_sales_v2) alongside v1. Shadow-run and compare, find impact via lineage, migrate in waves, deprecate with a sunset date, regression-test with golden queries, roll back by repointing. Ownership: business domain owns the meaning, data and platform team owns implementation, governance group (PM, data owners, platform lead) owns standards and breaking-change sign-off. Last question was cut off at "who owns...".

## Follow-ups to prepare
- Concrete numbers for CP AXTRA and Lazada.
- Real examples of the semantic layer and agent work.
- Policy for restating historical metrics.
