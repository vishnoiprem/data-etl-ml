# Data Engineering — Production Pipelines for Banks, Fintechs, AI

> **Twenty working data platforms built the way T+1 SLAs, MAS 7-year retention,
> GDPR right-to-erasure, and trillion-row CDC actually require.**
> Spark · Flink · Kafka · Iceberg · DuckDB · Airflow · dbt · Delta Lake · CDC.

This directory is the data half of the portfolio. Every project below is a real,
runnable pipeline — not a slide, not a tutorial trace. If you've ever had to
defend "how would you build the ledger at Stripe, the data lake at Netflix, or
the AML platform at a global bank," the answers live here.

> 🧭 **Looking for a curated tour by audience?** See
> [DIRECTORY.md](./DIRECTORY.md) — three pre-built paths (bank-audit
> client, senior-DE hiring manager, course student) that walk the
> directory in 5–7 clicks each.

---

## What's in this directory

| # | Project | The job-to-be-done | Stack |
|---|---------|--------------------|-------|
| 1 | [**SCB AML Platform**](./scb_aml_platform/) | Standard Chartered–style AML: 15 countries, 50M+ txns/day, T+1 SLA, MAS 7-year retention | Hive, Spark, Sqoop, Kafka |
| 2 | [**Banking-AML-Data**](./Banking-AML-Data/) | A second reference AML build, smaller, designed to be readable end-to-end | Spark, Postgres, dbt |
| 3 | [**CQRS / Double-entry ledger**](./cqrs-ledger/) | Stripe-style immutable postings, append-only, recon jobs that prove the books close | Postgres, Kafka, dbt |
| 4 | [**Event-sourced audit**](./event-sourced-audit/) | Audit log you can replay and prove in court. Hash-chained events | Postgres, Kafka |
| 5 | [**Multi-tenant isolation**](./multi-tenant-isolation/) | The boring-but-required layer that keeps one noisy tenant from melting another | Postgres RLS, Iceberg |
| 6 | [**Financial-reporting platform**](./financial-reporting-platform/) | IFRS-style reporting layer on top of the ledger, dbt-tested | dbt, DuckDB, Postgres |
| 7 | [**Activity-volume OLAP**](./activity-volume-olap/) | ClickHouse-style wide-table analytics on top of CDC'd events | ClickHouse, Kafka, dbt |
| 8 | [**Bloomberg symbology**](./bloomberg-symbology/) | The mapping problem every multi-asset shop hits on day one | DuckDB, PyArrow |
| 9 | [**CLP projects**](./clp_projects/) | A bank-scale case-lifecycle pipeline: alert → case → STR/SAR → regulator | Spark, Airflow, Hive |
| 10 | [**e-commerce end-to-end**](./e-commerce-end-2end/) | Order → payment → fulfillment → analytics, one full pipeline | Spark, Airflow, dbt |
| 11 | [**Edge analytics workers**](./edge-analytics-workers/) | Lambda@Cloudflare-style analytics at the edge, not in the warehouse | DuckDB-WASM, R2 |
| 12 | [**Keystone + Iceberg ops**](./keystone-iceberg-ops/) | Netflix-style table ops: snapshot expiry, compaction, orphan cleanup, schema-evolution tests | Iceberg, PyIceberg |
| 13 | [**Lazada Superset**](./lazada-superset/) | Marketplace analytics: GMV, search conversion, supply, returns | Superset, Postgres, dbt |
| 14 | [**Ontology data fabric**](./ontology-data-fabric/) | One semantic layer across the lakehouse; queryable, governable | Neo4j, Iceberg, OpenLineage |
| 15 | [**Data-engineering course**](./data-engineering-course/) | 14-week curriculum + dbt project, the way I would teach it | dbt, Snowflake, Airflow |
| 16 | [**Cloudvala**](./data-enginnering-cloudvala/) | Streaming ETL on Cloudvala reference architecture | Spark, Kafka, S3 |
| 17 | [**data-engineering**](./data-engineering/) | The "kitchen sink" reference build: ingestion → lake → warehouse → serving | Spark, Iceberg, dbt |
| 18 | [**activity-volume-olap**](./activity-volume-olap/) | Distinct from #7: focus on wide-table column-store design | ClickHouse, Kafka |

> 18 projects. ~2,600 source files. 1 design philosophy: **ship the boring bits**.

---

## Design philosophy

Every project in this directory follows five rules. If I had to defend a Staff
data-engineering interview, these are the rules I'd quote.

### 1. Idempotent ingestion, always

Every loader writes by partition + primary key, never by append-with-rename.
Re-running yesterday's batch must produce the same output byte-for-byte.
The proof is in the test suite — every project has at least one
"re-run on the same partition twice, expect zero diff" test.

### 2. Schema is a contract, not a comment

Schema changes go through migrations. Breaking changes go through a deprecation
window with a versioned reader. `dbt` + `pytest` + a contract test per table
that every downstream consumer must pass.

### 3. Cost is a first-class SLO

Every job has a per-query, per-GB cost estimate in the README. A job that
costs $X today must say "$X" in its README and explain how it stays at $X
as data grows. If the cost model is "we'll figure it out at 10× scale,"
the job isn't done.

### 4. Observability, not monitoring

Three dashboards per pipeline: data quality (freshness, nulls, distribution),
operational (lag, retries, queue depth), and business (the one KPI the
pipeline is paid to move). Alerts only on the business KPI. Everything else
is a graph, not a page.

### 5. The boring 80% is the product

Recon jobs. Backfills. Compaction. Orphan cleanup. Schema-evolution tests.
Right-to-erasure pipelines. These are the projects that look uninteresting
on a resume and ship in three weeks of quiet work. They are the reason
the platform stays up at year three.

---

## How to navigate

- **For a Staff-interview take-home:** start with `scb_aml_platform/` (the
  AML build) and `cqrs-ledger/` (the ledger). They are the two projects
  that show range — analytics-heavy AML + transactional ledger.
- **For a Fintech / Stripe-style interview:** `cqrs-ledger/`,
  `event-sourced-audit/`, `financial-reporting-platform/`. The boring
  trio.
- **For an AI / data-platform-for-ML interview:** `keystone-iceberg-ops/`,
  `ontology-data-fabric/`, `data-engineering-course/` (curriculum
  angle). The "data platform for AI" view.
- **For a marketplace / e-commerce interview:** `e-commerce-end-2end/`,
  `lazada-superset/`. The order/fulfillment/analytics chain.
- **For a regulated-industry interview:** `scb_aml_platform/`,
  `Banking-AML-Data/`, `multi-tenant-isolation/`. The "we take audits
  seriously" view.

---

## The meta-story for hiring managers

These projects were not built in a vacuum. Each one represents a problem
I shipped or helped ship at scale. The 18 here are the ones I can defend
in detail under a 4-hour system-design loop:

- **Defensibility:** every project includes a problem statement, the
  constraints (T+1 SLA, MAS retention, tenant isolation, etc.), the
  architecture, the cost model, and the failure modes I expect.
- **Breadth:** from the trillion-row CDC pipeline at a global bank
  (`scb_aml_platform/`) to a 14-week curriculum (`data-engineering-course/`)
  to a Stripe-style ledger (`cqrs-ledger/`) — the breadth is deliberate.
- **What I am NOT in this directory:** the actual proprietary code. The
  shape, the contracts, the failure modes, the costs — those are mine.
  The proprietary logic is the bank's.

If you want to talk about any of these, the door is open:
**vishnoiprem@gmail.com** — I reply in < 24 hours.

---

## Related directories

- [`../ai-engineering/`](../ai-engineering/) — the LLM / agent / eval half
  of the portfolio (40 projects, AWS best practices).
- [`../leads-pipeline/`](../../projects/leads-pipeline/) — the side hustle that funded
  a chunk of this work (cold-email + AI tailoring).
- [`../realtime-stock-pipeline/`](../../projects/realtime-stock-pipeline/) — the
  Kafka/Flink/Postgres/Grafana reference build that ties streaming to
  the OLAP store.
- [`../medium/`](../medium/) — long-form articles on every section here,
  if you want the prose version of the design notes.
