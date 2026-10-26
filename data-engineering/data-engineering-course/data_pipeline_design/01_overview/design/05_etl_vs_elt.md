# 05 — ETL vs ELT (when to use each)

> **Lesson 5 of 5 — Overview**

The acronym changed by one letter and the entire architecture shifted.
ETL — Extract, Transform, Load — is the 2000s pattern: do all the
work before you land the data. ELT — Extract, Load, Transform — is
the 2020s pattern: land the data raw, transform inside the warehouse.
This lesson is the *when to use which* decision tree.

---

## 1. The two patterns

```
ETL (2000s):
  Source ──► Extract ──► Transform ──► Load ──► Warehouse
                              │
                              └─► Filter, dedup, enrich, aggregate
                                  on a separate compute cluster
                                  (Informatica, Talend, Spark)

ELT (2020s):
  Source ──► Extract ──► Load ──► Transform ──► Warehouse
                              │                  │
                              │                  └─► dbt runs SQL
                              │                     inside the warehouse
                              │
                              └─► Land raw in Delta / Iceberg
                                  (lakehouse) or in Snowflake raw schema
```

The difference is *where* the transform happens. In ETL the
transform happens on a separate cluster (often the bottleneck). In
ELT the transform happens inside the warehouse, using the warehouse's
compute, against the just-loaded data.

---

## 2. Why ELT won

Five things changed:

1. **Warehouse compute got fast.** Snowflake / BigQuery can scan
   billions of rows in seconds. The "transform on a separate cluster"
   overhead is gone.
2. **Storage got cheap.** S3 standard is $23/TB-month. Landing raw
   data is no longer a budget concern.
3. **dbt made SQL transformations a product.** Versioned, tested,
   documented SQL models are the analytics engineering workflow.
4. **Schema-on-read is OK again.** With Delta / Iceberg, the lake
   has ACID. The "raw is a swamp" problem went away.
5. **Iteration speed.** With ELT you can re-transform without
   re-extracting. A bad dbt model is fixed in minutes, not days.

These five forces collapsed into the 2020s consensus: **ELT is the
default for analytics. ETL is the exception.**

---

## 3. When ETL is still right

ETL is not dead. There are four scenarios where ETL is still the
right call:

1. **Regulated data.** PII / PHI that must be scrubbed before
   landing. HIPAA, GDPR, PCI-DSS all push you to scrub at the edge.
2. **Cost-sensitive ingestion.** Landing 100 TB/day raw into a
   warehouse is expensive even at 2026 prices. If the cost of
   landing raw > the cost of filtering, ETL wins.
3. **Real-time with strict schema.** When you know the consumer
   wants exactly column X, Y, Z and nothing else, transforming
   before load reduces downstream surface area.
4. **Legacy stack.** Some regulated industries (banking, healthcare)
   have 20-year-old ETL tools. The cost to migrate is often higher
   than the cost to maintain.

The senior framing: "ETL is the right call when there's a
*constraint* that prevents raw landing. ELT is the default when
there isn't."

---

## 4. The Medallion Architecture

The most common ELT pattern is the Medallion Architecture (also
called multi-hop). It has three layers:

```
Bronze (raw)
  └─► Landed as-is from source. JSON, CSV, Parquet.
      Schema is whatever the source sent. No transforms.
      Use case: replay, audit, lineage.

Silver (cleaned)
  └─► Schema enforced. Nulls handled. Types coerced.
      Deduplicated. Joined to dimensions.
      Use case: feature engineering, ad-hoc analytics.

Gold (curated)
  └─► Business-specific aggregates. Star schema.
      SCD2 dimensions. Pre-computed KPIs.
      Use case: dashboards, ML features, product.
```

The Medallion pattern is *the* answer to "design a data warehouse"
and to "what's your data architecture." It's a 30-second answer that
scores a 5/5 on the rubric.

---

## 5. The interview answer

> "I'd default to ELT with the Medallion pattern. Bronze in Delta
> on S3, silver in Delta, gold in Snowflake. dbt for the silver →
> gold transforms because that's where the business logic lives.
> Airflow orchestrates the dbt runs. The deep dive would be the
> CDC ingestion into bronze — that's where the reliability work
> lives."

That single paragraph covers: pattern (ELT), architecture
(Medallion), tools (Delta + Snowflake + dbt + Airflow), and deep
dive (CDC). It's a 5/5 answer in 30 seconds.

---

## 6. The failure mode of ELT

ELT isn't free. The failure modes:

| Failure mode | Mitigation |
|---|---|
| **Raw data is dirty** | Quality checks at the bronze → silver boundary. |
| **Compute cost explodes** | dbt model pruning, partition pruning, incremental models. |
| **Schema evolution breaks silver** | Schema registry, contract tests, dbt source freshness. |
| **Lineage is invisible** | dbt docs, OpenLineage, DataHub. |

The senior move: name one failure mode unprompted. "ELT trades
upfront transformation cost for downstream flexibility. The cost
is that you have to be very disciplined about quality at the
silver boundary, because the raw bronze layer is intentionally
dirty."

---

## 7. The decision tree

```
Is the data regulated (PII / PHI / PCI)?
  └─ Yes → ETL (scrub before land)
  └─ No  → Is the raw volume < 10 TB/day?
              └─ Yes → ELT (default)
              └─ No  → Is the latency SLA < 1 min?
                         └─ Yes → Streaming + lightweight ETL
                         └─ No  → ELT with raw landing in lake
```

This isn't a perfect decision tree, but it's the *frame* a senior
candidate uses to answer "ELT or ETL?" in 15 seconds. The
interviewer will fill in the rest.

---

## Try it

Pick the most recent data pipeline you've worked on. Is it ETL or
ELT? Which layer of the Medallion does each table live in? Sketch
the bronze/silver/gold split on paper. If you can't, your pipeline
is one of two things: (a) too small to need the discipline, or
(b) too under-documented to survive without you.
