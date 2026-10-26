# Data Engineer Interview Canonical Questions & Sample Answers

> Reference material pulled from a real interview-prep service. Use these as
> the canonical problem set and sample answers for the corresponding tracks
> of this course. Every problem here should appear as a working lesson +
> test in the relevant track.

Source: Aggregated by community-sourced DE candidates / 500+ interview
experiences, 2026 vintage. Attribute the questions; the sample-answer
phrasing is paraphrased.

---

## SQL & Coding Questions

These become the spine of `sql_interviews/` practice modules.

| # | Question | Difficulty | Module |
|---|---|---|---|
| 1 | Top Earning Employees — highest-paid per department | Easy | `05_sql_easy_practice/` |
| 2 | Employee Earnings — running totals + rankings (window functions) | Easy-Med | `05_sql_easy_practice/` |
| 3 | Remove Duplicate Emails — keep first; delete rest | Easy | `05_sql_easy_practice/` |
| 4 | Top Salaries by Department — top N per group, DENSE_RANK | Medium | `06_sql_medium_practice/` |
| 5 | Instagram Likes — GROUP BY + HAVING engagement | Easy | `05_sql_easy_practice/` |
| 6 | Monthly Post Success — month-over-month success rate | Medium | `06_sql_medium_practice/` |
| 7 | Calculate Test Scores — NULL handling + conditional agg | Medium | `06_sql_medium_practice/` |
| 8 | Customer LTV — transactions × users + business metrics | Medium | `06_sql_medium_practice/` |

### Sample answer: Top Earning Employees

```sql
WITH ranked AS (
  SELECT
    e.name, e.salary, e.department_id,
    DENSE_RANK() OVER (
      PARTITION BY department_id
      ORDER BY salary DESC
    ) AS rk
  FROM Employee e
)
SELECT name, salary, department_id
FROM ranked
WHERE rk = 1;
```

Why this works: `DENSE_RANK` ties correctly (if two employees share the
highest salary, both appear — unlike `MAX()` + self-join). Interviewers
watch whether you reach for window functions vs nested subqueries.

### Sample answer: Employee Earnings (running totals)

```sql
SELECT
  emp_id, salary_month,
  SUM(salary) OVER (
    PARTITION BY emp_id
    ORDER BY salary_month
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) AS running_total
FROM earnings
ORDER BY emp_id, salary_month;
```

Cumulative window — common in finance/comp dashboards.

---

## Data Pipeline Design Questions

These become lessons in `data_pipeline_design/`.

| # | Question | Lesson |
|---|---|---|
| 1 | Design a document processing pipeline | `03_extraction/` or `06_perf_scalability/` |
| 2 | Data lakehouse vs data warehouse | `02_storage/` or `01_overview/` |
| 3 | Medallion Architecture (bronze/silver/gold) | `02_storage/` |
| 4 | Delta Lake — what it adds on top of Parquet | `02_storage/` |
| 5 | Hadoop vs PySpark — when each is right | `03_extraction/` |
| 6 | Scheduling dependencies between two nightly jobs | `06_perf_scalability/` |
| 7 | Task that fails 10% of runs — how to handle | `06_perf_scalability/` |
| 8 | Design Netflix's Clickstream Data Pipeline | `07_mock_interviews/` |

### Sample answer: Lakehouse vs Warehouse

A **warehouse** (Snowflake, Redshift, BigQuery) stores structured, cleaned
data optimized for SQL analytics. Schema-on-write: define schema before load.
Fast queries, limited flexibility.

A **lakehouse** (Delta Lake, Apache Iceberg) combines the cheap, flexible
storage of a lake (raw files on S3 in any format) with ACID transactions,
schema enforcement, and warehouse-grade query performance.

Practical difference: warehouse requires ETL before load; lakehouse lets
you load raw and transform in place while keeping reliable, repeatable
queries. Most modern stacks converge on lakehouse because it eliminates
the duplicated lake + warehouse architecture.

### Sample answer: Document processing pipeline

1. Ingest: S3 / GCS upload triggers event → SQS / Kafka.
2. OCR + parse: workers pull, run OCR + extract structured fields (PDFs,
   DOCX, images). Use Amazon Textract or open-source alternatives.
3. Enrich: NLP for entities, classification, language detection.
4. Persist: write JSON + thumbnails to S3, index metadata in OpenSearch.
5. Serve: API returns signed URL + extracted fields.
6. Monitor: failure DLQ, retry with exponential backoff, ingestion
   latency metric.

Add: exactly-once semantics via idempotency keys on document_id, schema
validation at every stage, dead-letter queue for OCR failures.

---

## Data Modeling Questions

These become lessons in `data_modeling/04_high_level_diagrams/` and
`07_mock_interviews/`.

| # | Question | Lesson |
|---|---|---|
| 1 | Design a fitness app schema | `04_high_level_diagrams/` |
| 2 | Data warehouse schema for a ride-sharing service | `04_high_level_diagrams/` |
| 3 | Data warehouse schema for Instagram | `04_high_level_diagrams/` |
| 4 | Data warehouse schema for customer support | `04_high_level_diagrams/` |
| 5 | Design a Spotify data warehouse | `04_high_level_diagrams/` |
| 6 | Design an Amazon data warehouse | `04_high_level_diagrams/` |

### Sample answer: Fitness app schema

Start by clarifying the analytics use case. Assuming engagement reporting:

- `fact_workouts` — grain: one row per workout session
  - measures: duration_minutes, calories_burned, sets_completed
- `dim_users` — SCD Type 2 (fitness level changes over time)
  - effective_date, expiry_date for accurate historical attribution
- `dim_exercises`, `dim_workout_types`, `dim_dates`

Pattern to apply everywhere: clarify the grain, identify facts vs.
dimensions, address how things change over time (SCD1/2/3).

---

## System Design & Architecture Questions

These become lessons in `system_design/` (already built) and review
references in `data_pipeline_design/`.

| # | Question | Tracks |
|---|---|---|
| 1 | NoSQL vs SQL | `system_design/99_appendix/` cross-ref |
| 2 | Parquet vs Avro | `data_pipeline_design/02_storage/` |
| 3 | OLTP vs OLAP | `system_design/99_appendix/` |
| 4 | Spark wide vs narrow dependencies | `data_pipeline_design/03_extraction/` |
| 5 | Connecting SQL databases — best way | `data_pipeline_design/03_extraction/` |
| 6 | Multithreading vs multiprocessing | `coding_interviews/02_complexity/` |
| 7 | PySpark — what it is | `data_pipeline_design/03_extraction/` |

### Sample answer: NoSQL vs SQL

SQL (PostgreSQL, MySQL): relational, fixed schema, ACID, complex joins,
right when relationships matter more than write speed.

NoSQL is 4 categories:
- **Key-value** (Redis) — caching, sessions
- **Document** (MongoDB) — flexible nested JSON
- **Wide-column** (Cassandra) — high-throughput time-series writes
- **Graph** (Neo4j) — relationship-heavy queries

In a DE context: PostgreSQL as OLTP source → CDC → Kafka → Cassandra or
Delta Lake for analytics. Both coexist in a real pipeline.

### Sample answer: Parquet vs Avro

| | Parquet | Avro |
|---|---|---|
| Layout | Columnar | Row-based |
| Best for | Read-heavy analytics | Write-heavy ingest |
| Schema | Embedded (schema-on-read with stats) | JSON schema + evolution |
| Compression | Excellent (same column = similar values) | OK |
| Use | Snowflake/BigQuery/Datalake | Kafka events, log streams |

---

## Behavioral Questions

These become lessons in `behavioral_interviews/03_story_bank/` and
`behavioral_interviews/04_practice/`.

| # | Question | Asked at |
|---|---|---|
| 1 | Tell me about yourself | 36+ companies |
| 2 | Tell me about a time you made a mistake | Amazon, Google, Meta, 12+ |
| 3 | Tell me about a time you disagreed and resolved it | Amazon, Apple, Google, 5+ |
| 4 | Project you are most proud of | 25+ companies |
| 5 | Tell me about a time you improved a complex process | Amazon, Google |
| 6 | Encourage cross-team collaboration | Amazon, Anthropic, Discord |

### Sample answer: Tell me about a time you made a mistake

> I deployed a pipeline change that modified the deduplication logic
> for our event stream. I tested it against a sample dataset but didn't
> validate against the full production volume. The change introduced
> duplicate records into our analytics warehouse, inflating DAU by ~12%
> for two days before a data analyst flagged the discrepancy.
>
> I immediately rolled back, ran a backfill to correct the affected
> partitions, and set up a reconciliation check that compares source and
> destination row counts after every pipeline run. The broader lesson
> was that sample-based testing isn't sufficient for deduplication; edge
> cases only surface at scale. I now require full-volume staging
> validation for any pipeline change that touches dedup or aggregation
> logic.

Why it works:
- Specific to data engineering (not generic teamwork)
- Names a concrete metric (12% DAU inflation, 2 days)
- Ends with a systemic fix (reconciliation check + SOP change)

---

## Frameworks (use across all tracks)

### STAR Method (behavioral)

| Step | What to do |
|---|---|
| Situation | Set the scene in 1-2 sentences. What team, what system, what was at stake? |
| Task | What was your specific responsibility? What outcome were you accountable for? |
| Action | Walk through what you did. Be specific: tools, queries, decisions. |
| Result | Quantify. Pipeline uptime, cost savings, latency reduction, stakeholder impact. |

### Pipeline Design Framework (system design)

| Step | What to do |
|---|---|
| Clarify | Data volume, velocity, format, downstream consumer? |
| Source | APIs, DBs (CDC), event streams, file drops |
| Ingest | Batch (Airflow + S3) or streaming (Kafka + Flink). State trade-off. |
| Transform | dbt for SQL, Spark for large-scale. Schema evolution. |
| Serve | Warehouse / lakehouse / serving layer. |
| Monitor | Quality checks, SLA alerting, lineage. Always mention this unprompted. |

---

## DE Interview FAQ (highlights)

- **Topics covered**: SQL/coding, pipeline design, data modeling, system
  design, behavioral. Mix varies. Databricks leans pipeline; Meta leans
  SQL/coding.
- **Round count**: 4-6. Recruiter screen, 1-2 technical SQL/coding,
  system/pipeline design, behavioral. Senior adds a "deep dive"
  walking through a past project. 2-4 weeks total end to end.
- **DE vs DS**: DE = infrastructure (SQL, pipelines, modeling, Spark,
  Kafka). DS = usage (stats, ML, A/B testing). Overlap in SQL.
- **Required SQL**: window functions (RANK, DENSE_RANK, ROW_NUMBER,
  LAG/LEAD), CTEs, complex joins (self, anti), GROUP BY + HAVING, CASE,
  query optimization basics. Senior adds recursive CTEs.

---

*Use these as the spine of the SQL, modeling, pipeline, and behavioral
tracks when you build them. Don't fabricate questions — use this list.*
