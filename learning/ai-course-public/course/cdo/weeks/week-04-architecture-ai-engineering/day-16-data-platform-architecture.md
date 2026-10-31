# Lesson 16: Data platform architecture

> **Week 4 · Day 16 · 90 min**
> **Deliverable:** The 5 layers of a modern data platform, with the build-vs-buy decision per layer.

## 🎯 Architect Level
Staff.

## 🧠 Concept

A modern data platform has 5 layers. Every vendor maps to a layer; every architecture debate happens at a layer.

| Layer | What it does | Key choices | Build vs. buy |
|---|---|---|---|
| **1. Ingestion** | Move data from source to platform | Batch (Airflow, Dagster), streaming (Kafka, Flink), CDC (Debezium), SaaS connectors (Fivetran, Airbyte) | Buy (connectors); build (custom CDC if needed) |
| **2. Storage** | Persist data at rest | Lakehouse (Iceberg, Delta, Hudi), warehouse (Snowflake, BigQuery, Redshift), lake (S3, GCS) | Buy (object storage); build (table format / open table) |
| **3. Transformation** | Shape data into usable form | dbt, Spark, Flink, Dataform | Build (in-house data eng); standardize on dbt for SQL |
| **4. Semantic** | Define the metrics and entities the business uses | LookML, dbt semantic layer, Cube, MetricFlow | Build (own the metrics) |
| **5. Consumption** | Serve data to humans and machines | BI (Looker, Tableau, PowerBI), notebooks, APIs, reverse-ETL, AI | Buy (BI); build (data products) |

Above these 5 sits the **cross-cutting platform**:
- **Observability** (Monte Carlo, Bigeye, Datafold, Great Expectations)
- **Lineage** (DataHub, Atlan, Unity Catalog, OpenLineage)
- **Orchestration** (Airflow, Dagster, Prefect)
- **FinOps** (custom or vendor)
- **Security** (IAM, encryption, masking, audit, key mgmt)
- **Governance** (catalog, access, retention, contracts)

The single biggest mistake is to **pick a vendor before picking a layer**. The decision is "what does each layer do and who owns it," not "which vendor." The vendor comes after the layer choice.

The second biggest mistake is to **collapse the semantic layer into the warehouse**. The warehouse stores data; the semantic layer defines what the data means. Without the semantic layer, the business has 4 definitions of "active customer" (per Week 2's case study).

The third biggest mistake is to **under-invest in observability and lineage**. They are not "nice to have" — they are the only way to debug, govern, and trust the platform. Plan 10-15% of the data team for platform + reliability.

## 🛠️ Build It

**Spec:** For a 10M-customer retailer, design the 5 layers + cross-cutting platform. Name the choices and the build-vs-buy.

**Acceptance:**
- 5 layers, each with 1-2 named technologies
- Cross-cutting platform with 4-6 named capabilities
- Build-vs-buy per layer
- 1 paragraph on the "why" for the most-debated choice (e.g., lakehouse vs. warehouse)

**Starter:** Use the Makro / Lazada / Xendit evidence from your resume.

**Solution (5 layers, abridged):**

| Layer | Choice | Why | Build vs. buy |
|---|---|---|---|
| Ingestion | Fivetran + Airbyte (SaaS), Kafka (streaming) | SaaS connectors for SaaS sources; Kafka for events | Buy |
| Storage | Lakehouse (Iceberg on S3) + warehouse (Snowflake) | Open table format + proven SQL engine | Buy + build (table format) |
| Transformation | dbt (SQL) + Spark/Flink (heavy) | dbt for the 80%, Spark for the 20% | Build (data eng) + buy (dbt) |
| Semantic | dbt semantic layer + Cube | Single source of metric truth | Build (own the metrics) |
| Consumption | Looker (BI), notebooks, APIs, AI | Looker for the 90%, APIs for product | Buy (BI) + build (data products) |

**Cross-cutting:** DataHub (lineage), Monte Carlo (observability), Dagster (orchestration), custom FinOps, IAM + Unity Catalog (security), contracts (in-house framework).

## 🏛️ Architect Notes

- **Trade-off:** Lakehouse vs. warehouse. Default: lakehouse for the open table format, warehouse for the SQL engine. Don't pick a single vendor for both.
- **Capacity / cost:** A 5-layer platform with cross-cutting capabilities is 12-18 months of build for a 15-20 person platform team. Below that, the platform becomes the bottleneck.
- **When NOT to use:** Don't use a single mega-vendor (e.g., "all-Snowflake" or "all-Databricks") unless the company is <500 people. At 1,200 stores, the seams show.
- **Production checklist:**
  - [ ] 5 layers named
  - [ ] 1-2 technologies per layer
  - [ ] Cross-cutting platform with 4-6 capabilities
  - [ ] Build-vs-buy per layer
  - [ ] "Why" for the most-debated choice

## 🌙 Reflect

- Which layer is the most-debated choice for the role you're interviewing for? Pre-write the answer.
- Which layer would you build first? Why?
- Write 3 sentences you'll say out loud tomorrow.

---

**Next:** Day 17 — Cloud migration and multi-cloud.