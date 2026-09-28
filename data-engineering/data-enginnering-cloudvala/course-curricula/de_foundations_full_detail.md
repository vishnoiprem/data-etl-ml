# Data Engineering Fundamentals — Full-Detail Course Content

**Source attribution:** Course content from Data Vidhya (https://datavidhya.com/)
by **Darshil Parmar (Founder & Lead Instructor, Data Vidhya)**.
Course URL: https://datavidhya.com/learn/de-fundamentals/

**Coverage:** 6 modules • 49 lessons
**Last updated on Data Vidhya:** Jun 30, 2026
**Reproduced in `data-enginnering-cloudvala/course-curricula/`** as a
study-path reference. Full-detail versions of the deep-dive articles are
included where the full body was extractable from the public page.

> **Note on coverage:** This file contains the complete 49-lesson curriculum
> (titles, formats, descriptions) plus the full article bodies for the deep-dive
> lessons that were extractable from the public pages (`What is DE (Deep Dive)`
> and `Lake vs Warehouse (Deep Dive)`). The remaining deep-dive articles
> (Lifecycle, Data Modeling, OLTP vs OLAP, Data Quality, Observability &
> Lineage, Governance & Compliance, Idempotency, Schema Evolution, File
> Formats, Partitioning & Clustering, Modern Data Stack, Tools for DE, dbt,
> Apache Airflow) are JS-rendered and require a logged-in browser session to
> extract. Their descriptions are included below as abstracts.

---

## Module 1: Start Here — 1 lesson

### 1. How This Course Works — Article
An introductory article explaining how to navigate the course structure,
use the modules, and get the most out of the lessons.

---

## Module 2: Data Engineering Foundations — 14 lessons

### 2. What is Data Engineering? — Video
An introductory video defining data engineering, its purpose, and how it
differs from related roles.

### 3. What is DE (Deep Dive) — Article  *(full body included below)*

### 4. The Data Engineering Lifecycle — Video
A video walkthrough of the end-to-end stages that data passes through in an
engineering pipeline.

### 5. The Lifecycle (Deep Dive) — Article
A detailed article expanding on lifecycle stages with examples and context.
*Abstract only — JS-rendered, full body not extractable from public page.*

### 6. Data Generation vs Storage — Video
A video comparing how data is produced versus how it is persisted across
systems.

### 7. Introduction to Data Modeling — Video
A video overview of data modeling concepts and why they matter in
engineering work.

### 8. Data Modeling (Deep Dive) — Article
An in-depth article covering modeling approaches, schemas, and trade-offs.
*Abstract only — JS-rendered, full body not extractable from public page.*

### 9. OLAP vs OLTP — Video
A video contrasting online analytical processing with online transaction
processing systems.

### 10. OLTP vs OLAP (Deep Dive) — Article
An article exploring architectural and use-case differences between the two
system types. *Abstract only — JS-rendered, full body not extractable.*

### 11. Introduction to ETL — Video
A video introducing Extract, Transform, Load patterns and their role in
pipelines.

### 12. ETL vs ELT (Deep Dive) — Article
An article comparing traditional ETL with the more modern ELT approach.
*Abstract only — JS-rendered, full body not extractable.*

### 13. DE vs DS vs Analyst vs MLE — Article
An article clarifying how data engineering differs from data science,
analytics, and machine learning engineering.

### 14. Batch vs Streaming — Article
An article explaining the trade-offs between batch and stream processing
paradigms.

### 15. Quiz: Data Engineering Foundations — Quiz
An assessment testing understanding of the foundational module's concepts.

---

## Module 3: Architecture, Warehousing & Undercurrents — 12 lessons

### 16. Data Engineering Undercurrents — Video
A video introducing cross-cutting concerns like security, lineage, and data
quality.

### 17. Data Quality — Article
An article on measuring, monitoring, and improving data quality in pipelines.
*Abstract only — JS-rendered, full body not extractable.*

### 18. Data Architecture 101 — Video
A video overview of architectural patterns used in data platforms.

### 19. Introduction to Data Warehouse — Video
A video explaining the purpose, structure, and benefits of data warehouses.

### 20. Introduction to Dimensional Modeling — Video
A video introducing star schemas and dimensional modeling techniques.

### 21. Slowly Changing Dimensions — Video
A video covering SCD types and how to handle changing dimensional data
over time.

### 22. Data Marts — Video
A video explaining how data marts serve focused analytical use cases.

### 23. Observability & Lineage — Article
An article on tracking data flow and monitoring pipeline health.
*Abstract only — JS-rendered, full body not extractable.*

### 24. Governance & Compliance — Article
An article covering governance frameworks, policies, and regulatory
considerations. *Abstract only — JS-rendered, full body not extractable.*

### 25. Idempotency — Article
An article on designing pipelines that produce the same result on repeated
runs. *Abstract only — JS-rendered, full body not extractable.*

### 26. Schema Evolution — Article
An article addressing how to manage changes to data schemas over time.
*Abstract only — JS-rendered, full body not extractable.*

### 27. Quiz: Architecture, Warehousing & Undercurrents — Quiz
An assessment covering the architecture and warehousing module.

---

## Module 4: Data Lakes & File Formats — 6 lessons

### 28. Introduction to Data Lakes — Video
A video explaining the concept, structure, and use cases of data lakes.

### 29. Data Lake vs Data Warehouse — Video
A video comparing lake and warehouse approaches side by side.

### 30. Lake vs Warehouse (Deep Dive) — Article  *(full body included below)*

### 31. File Formats — Article
An article covering common data serialization formats like Parquet, ORC,
and Avro. *Abstract only — JS-rendered, full body not extractable.*

### 32. Partitioning & Clustering — Article
An article on organizing data for performance using partitioning and
clustering strategies. *Abstract only — JS-rendered, full body not
extractable.*

### 33. Quiz: Data Lakes & File Formats — Quiz
An assessment covering the data lakes module.

---

## Module 5: The Landscape & Cloud — 8 lessons

### 34. The Big Data & Data Engineering Landscape — Video
A video survey of the modern data engineering tooling ecosystem.

### 35. The Landscape (Deep Dive) — Article
An article expanding on ecosystem tools, trends, and categories.

### 36. Introduction to Cloud Computing — Video
A video covering core cloud concepts relevant to data engineers.

### 37. AWS for Data Engineering — Video
A video introducing key AWS services used in data pipelines.

### 38. Dream11 Architecture Case Study — Video
A video case study examining a real-world data architecture at scale.

### 39. GCP for Data Engineers — Video
A video tour of Google Cloud Platform services for data work.

### 40. Azure for Data Engineering — Video
A video tour of Microsoft Azure services for data work.

### 41. Quiz: The Landscape & Cloud — Quiz
An assessment covering cloud platforms and the broader landscape.

---

## Module 6: Modern Stack, Tools & Security — 8 lessons

### 42. The Modern Data Stack — Video
A video introducing the components and philosophy of the modern data stack.

### 43. Modern Data Stack (Deep Dive) — Article
An article expanding on modern stack tools, integrations, and trade-offs.
*Abstract only — JS-rendered, full body not extractable.*

### 44. Tools for Data Engineering — Video
A video overview of commonly used data engineering tools.

### 45. Tools for DE (Deep Dive) — Article
An article comparing popular tools and their ideal use cases.
*Abstract only — JS-rendered, full body not extractable.*

### 46. Data Security & Masking — Video
A video on securing data and applying masking techniques to protect
sensitive information.

### 47. dbt — Article
An article on dbt (data build tool) for transformation workflows in the
warehouse. *Abstract only — JS-rendered, full body not extractable.*

### 48. Apache Airflow — Article
An article introducing Apache Airflow for orchestrating data pipelines.
*Abstract only — JS-rendered, full body not extractable.*

### 49. Quiz: Modern Stack, Tools & Security — Quiz
A final assessment covering modern tooling and security concepts.

---

# Full Article Bodies

## Lesson 3: What is DE (Deep Dive)

*A comprehensive overview of what data engineering is, what data engineers
build, and why this role is critical in every data-driven organization.*
*6 min read · Beginner · Published Jun 30, 2026*

### Introduction

The article opens by noting that data engineering is in-demand yet commonly
misunderstood. It states: *"Data engineering is not about data itself. It is
about building the systems that make data usable."* The introduction frames
the lesson as covering what data engineering is, why it is needed, and how
it fits into the broader data ecosystem.

### Core Explanation

**What is Data Engineering?**

Quoted: *"Data engineering is the discipline of designing, building, and
maintaining the systems and infrastructure that collect, store, transform,
and deliver data."* The article uses a plumbing analogy — data engineers
build the pipes while analysts decide what to do with the water. Typical
responsibilities listed:

- Build data pipelines from sources into warehouses or lakes
- Transform raw data into structured datasets
- Design data models for efficient querying
- Ensure data quality via validation and monitoring
- Manage infrastructure (databases, storage, orchestration)
- Optimize performance and cost

**Try It Yourself** — interactive canvas for building a pipeline using sources
(PostgreSQL, REST API, CSV, Kafka), transforms (Filter, Join, Aggregate,
Clean), and destinations (Snowflake, Dashboard, ML Model, S3).

**Why Does Data Engineering Exist?**

Three drivers: data volume exploded, data sources multiplied across SaaS
tools, and data-driven decisions became competitive advantages. A context
callout notes the term became common around 2015–2016.

**How Uber uses this** — Uber's "Michelangelo" system processes 100M+ events/sec
to power real-time ETAs.

**Sample explanation:** *"At my previous role, I built a pipeline that
processed 50 million events daily..."*

**The Data Engineering Lifecycle**

Five stages:

1. **Generation** — source systems create data
2. **Ingestion** — CDC, Kafka, REST APIs, Fivetran/Airbyte
3. **Storage** — warehouses (Snowflake, BigQuery, Redshift), lakes (S3, GCS), lakehouses
4. **Transformation** — dbt, Spark, SQL; deduplication, joins, metrics
5. **Serving** — BI tools, ML pipelines, reverse ETL, APIs

A callout warns: *"The most dangerous pipeline bugs are silent."* Row counts,
freshness, and metric checks matter more than job status.

**Software Engineering vs Data Engineering** — comparison table:

| Dimension    | SWE                | DE                              |
|--------------|--------------------|---------------------------------|
| Output       | Apps/services      | Pipelines, datasets             |
| Control      | Own code           | External data                   |
| Failures     | Crashes            | Silent quality issues           |
| Testing      | Unit/integration   | Data validation                 |
| State        | Mostly stateless   | Deeply stateful                 |
| Users        | End users          | Analysts, DS, MLE, business     |

**The Skills a Data Engineer Needs**

*Must-have:* SQL, Python, data modeling (star/snowflake schemas, SCDs), ETL/ELT
patterns, cloud platforms (AWS, GCP, Azure).

*Important:* orchestration (Airflow, Prefect, Dagster), distributed processing
(Spark), streaming (Kafka, Flink), Git/CI/CD, data quality/observability.

*Nice-to-have:* Terraform, Docker/Kubernetes, governance (GDPR, CCPA, HIPAA).

### Real-World Examples

**Example 1 — Food Delivery:** Ingestion → Storage → Transformation → Serving.
Fact tables for orders, dimensions for restaurants and drivers. ML models
predict delivery times.

**Example 2 — Spotify:** Billions of daily events ingested from mobile/desktop,
stored in GCS + BigQuery, transformed into user profiles and metric tables,
then served to ML powering Discover Weekly and Release Radar.

### Common Misconceptions

1. DEs and DSs do the same thing — No, DEs build the kitchen; DSs are the chefs.
2. DE is just SQL — Also includes Python, infrastructure, monitoring, and schema migrations.
3. CS degree required — No; fundamentals can be self-taught.
4. DE is a stepping stone to DS — No, it's a distinct, well-compensated career path.

### Interview Relevance

Three common questions and how to answer them:

- *"What is data engineering?"* — Cover lifecycle, reliability, scale, downstream consumers.
- *"Why DE not DS?"* — Show interest in systems and infrastructure.
- *"Day-to-day?"* — Real activities: build/monitor pipelines, debug quality, define requirements.

### Key Takeaways

- DE designs, builds, and maintains data systems reliably at scale
- The role exists due to volume, source diversity, and business reliance on data
- Lifecycle: Generation → Ingestion → Storage → Transformation → Serving
- DEs enable DS, analytics, and ML
- Core skills: SQL, Python, modeling, cloud, pipeline design
- A standalone career path, not a stepping stone

The takeaway box states: *"Data engineering is not about tools, it's about
building reliable systems that make data usable."*

### What Comes Next

Next: **The Data Engineering Lifecycle** lesson.

---

## Lesson 30: Lake vs Warehouse (Deep Dive)

*Imagine you're organizing a massive library...* — *Published Jun 30, 2026*

### Introduction

Imagine you're organizing a massive library. Would you throw every book,
magazine, newspaper, and random scrap of paper into one giant room? Or would
you carefully catalog everything, create a card system, and arrange books by
topic? What if you could have both — the flexibility to store everything
*and* the organization to find what you need instantly?

This is exactly the challenge data engineers face when choosing between a
**data warehouse**, a **data lake**, and a **lakehouse**. These three
architectures represent different philosophies for storing and managing
data, and picking the wrong one can cost your company millions in wasted
storage, slow queries, or missed insights.

In this article, you'll learn what each system does, when to use it, and how
companies like Netflix, Uber, and Airbnb make these decisions.

### What is a Data Warehouse?

A **data warehouse** is a centralized repository designed for **structured,
cleaned, and organized data** that's ready for analysis.

**Key Characteristics:**

- **Schema-on-write**: You define the structure *before* loading data
- **Structured data only**: Typically works with tables, not raw files
- **Optimized for SQL queries**: Fast aggregations, joins, and reporting
- **Expensive storage**: Because data is cleaned and structured
- **High performance**: Designed for business intelligence and dashboards

> **Context:** Popular data warehouses include **Snowflake**, **Google
> BigQuery**, **Amazon Redshift**, and **Azure Synapse Analytics**.

**Real-World Example: Airbnb**

Airbnb uses a data warehouse (built on top of Amazon Redshift and later
migrated to a custom solution) to power their business intelligence dashboards.

Sample SQL query:

```sql
SELECT
  date_trunc('month', booking_date) AS month,
  listing_city,
  COUNT(*) AS total_bookings,
  SUM(total_price) AS revenue
FROM bookings
WHERE booking_date >= '2025-01-01'
GROUP BY 1, 2
ORDER BY revenue DESC;
```

### What is a Data Lake?

A **data lake** is a massive storage system that holds **raw, unprocessed
data** in its native format — structured tables, semi-structured JSON files,
unstructured text documents, images, videos, or logs.

**Key Characteristics:**

- **Schema-on-read**: You define the structure *when* you read the data
- **Stores any data type**: CSV, JSON, Parquet, images, videos, logs
- **Cheap storage**: Especially on cloud object storage like S3
- **Flexible but chaotic**: Great for data scientists and ML engineers
- **Slower queries**: Without structure, querying can be slow

> **Common Mistake:** Without proper governance, a data lake becomes a
> **data swamp** — terabytes of data nobody understands.

**Real-World Example: Netflix**

Netflix stores petabytes of raw data on Amazon S3, including streaming logs,
user interaction events, A/B test results, ML training data, and encoded
video files.

Sample PySpark code:

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("NetflixAnalysis").getOrCreate()

events = spark.read.json("s3://netflix-data-lake/raw/streaming-events/2026-03-01/")

play_events = events.filter(events.event_type == "play")
popular_shows = play_events.groupBy("show_id").count().orderBy("count", ascending=False)

popular_shows.show()
```

### What is a Lakehouse?

A **lakehouse** is a hybrid architecture that combines the **flexibility of
a data lake** with the **structure and performance of a data warehouse**.

The key innovation is adding a **metadata layer** on top of cheap object
storage that provides ACID transactions, schema enforcement, and indexing.

**Key Characteristics:**

- **Unified storage**: One place for raw and structured data
- **ACID transactions**: Reliable updates and deletes
- **Schema enforcement**: Optional structure when needed
- **Open formats**: Delta Lake, Apache Iceberg, or Apache Hudi
- **Cost-effective**: Cheap storage with warehouse-like performance

> **Key Insight:** Lakehouses eliminate the need to maintain two separate
> systems (a lake and a warehouse).

**Real-World Example: Uber**

Uber built a lakehouse using **Apache Hudi** on S3. Sample code:

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("UberLakehouse").getOrCreate()

trips = spark.read.format("hudi").load("s3://uber-lakehouse/trips/")

updated_trips = trips.filter(trips.trip_id == "12345").withColumn("status", lit("completed"))

updated_trips.write.format("hudi") \
  .option("hoodie.table.name", "trips") \
  .mode("append") \
  .save("s3://uber-lakehouse/trips/")
```

### Side-by-Side Comparison

| Feature             | Data Warehouse                | Data Lake                  | Lakehouse                        |
|---------------------|-------------------------------|----------------------------|----------------------------------|
| **Data Type**       | Structured                    | Any                        | Any (optional structure)         |
| **Schema**          | Schema-on-write               | Schema-on-read             | Flexible                         |
| **Storage Cost**    | High                          | Low                        | Low                              |
| **Query Performance** | Very fast                   | Slow                       | Fast                             |
| **ACID Transactions** | Yes                         | No                         | Yes                              |
| **Use Case**        | BI, dashboards                | Data science, ML           | Unified analytics                |
| **Examples**        | Snowflake, BigQuery           | S3 + Athena                | Delta Lake, Iceberg, Hudi        |

> **Pro Tip:** If starting a new project in 2026, **default to a lakehouse
> architecture** unless you have a specific reason not to.

### When to Use Each Architecture

**Use a Data Warehouse When:**

- Data is mostly **structured**
- You need **fast, reliable SQL queries**
- Users are primarily **business analysts**
- Schema doesn't change often

**Use a Data Lake When:**

- You need to store **raw, unprocessed data**
- Users are **data scientists** needing flexibility
- Collecting **diverse data types**
- Need **cheap storage**

**Use a Lakehouse When:**

- Want **one unified system** for analytics and data science
- Need **ACID transactions** on a data lake
- Want **warehouse-like performance** without warehouse costs
- Building a **modern data platform** from scratch

### Common Misconceptions

**Misconception #1:** "Data lakes are always cheaper than data warehouses"
**Reality:** Total cost of ownership can be higher due to compute, engineering
time, and data quality issues.

**Misconception #2:** "You have to choose one — warehouse OR lake"
**Reality:** Most large companies use both — raw data lands in the lake,
cleaned data goes to the warehouse. Lakehouses aim to eliminate this
dual-system approach.

### Real-World Example: LinkedIn's Evolution

- **2010-2015:** Data warehouse (Oracle, later Teradata)
- **2015-2018:** Data lake on HDFS for raw logs
- **2018-Present:** Lakehouse using Apache Iceberg on HDFS and S3

### Key Takeaways

- **Data Warehouses**: Fast SQL on structured data, expensive, schema-on-write
- **Data Lakes**: Cheap raw storage, flexible, risk of data swamps
- **Lakehouses**: Best of both worlds using Delta Lake, Iceberg, Hudi
- Modern lakehouses aim to unify warehouses and lakes into one system
- Always discuss trade-offs (cost vs performance, flexibility vs structure)

---

*Written by Darshil Parmar, Founder & Lead Instructor, Data Vidhya.
Published Jun 30, 2026.*
