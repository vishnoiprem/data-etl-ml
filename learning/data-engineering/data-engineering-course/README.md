# data-engineering-cloudvala

> **Note (2026-10-13):** This directory was previously named
> `data-enginnering-cloudvala` (a typo: "enginnering" instead of
> "engineering"). It has been renamed to fix the typo. The
> contents are unchanged.

Data Engineering interview-prep and study-path reference material.
Owner: cloudvala / avilex.

All content is reproduced verbatim from articles and course outlines published
on [Data Vidhya](https://datavidhya.com/) by **Darshil Parmar (Founder)**.

## Layout

```
data-enginnering-cloudvala/
├── README.md                                  ← this file
│
├── spark-de-interview-qa/
│   └── spark_top50.md                         ← Top 50 Spark DE interview Q&A
│
├── snowflake-de-interview-qa/
│   └── snowflake_top50.md                     ← Top 50 Snowflake DE interview Q&A
│
├── python-de-interview-qa/
│   └── python_top50.md                        ← Top 50 Python DE interview Q&A
│
└── course-curricula/                          ← Verbatim course outlines
    ├── 01_de_foundations_track.md             ← DE Foundations (6 modules, 49 lessons)
    ├── 02_python_track.md                     ← Python for DE (5 modules, 54 lessons)
    ├── 03_snowflake_hands_on.md               ← Snowflake Hands-On (5 modules, 39 lessons)
    ├── 04_airflow_track.md                    ← Airflow Fundamentals + Intermediate (6 modules, 45 lessons)
    ├── 05_de_interview_prep.md                ← DE Interview Prep: The Complete Course (10 modules, 98 lessons)
    ├── 06_azure_de.md                         ← Azure DE Stack + Batch + Streaming + Production (4 modules, 22 lessons)
    ├── 07_kafka_fundamentals.md               ← Apache Kafka Fundamentals (4 modules, 32 lessons)
    ├── 08_dbt_course.md                       ← dbt (Data Build Tool) Course (5 modules, 37 lessons)
    ├── 09_aws_de.md                           ← AWS for Data Engineering (5 modules, 36 lessons)
    ├── de_foundations_full_detail.md          ← DE Foundations with 4 verbatim deep-dive articles
    ├── aws_de_full_detail.md                  ← AWS for DE with 9 verbatim deep-dive articles
    ├── aws_de_cto_learning_plan.md            ← CTO/Principal plan: theory + example + AI + motivation for all 36 lessons
    ├── azure_de_cto_learning_plan.md          ← CTO/Principal plan for all 22 Azure DE lessons
    ├── de_system_design_cto_learning_plan.md  ← CTO/Principal plan for all 65 DE System Design lessons
    ├── kafka_stream_processing_cto_learning_plan.md  ← CTO/Principal plan for all 16 Kafka Stream Processing lessons
    ├── kafka_python_pipelines_cto_learning_plan.md   ← CTO/Principal plan for all 20 Building Data Pipelines with Kafka lessons
    ├── advanced_pyspark_cto_learning_plan.md  ← CTO/Principal plan for all 19 Advanced PySpark lessons
    ├── data_warehousing_cto_learning_plan.md  ← CTO/Principal plan for all 24 Data Warehousing lessons
    ├── delta_lake_full_detail.md              ← Delta Lake Deep Dive (article body — stub, body to be pasted)
    └── snowflake_full_detail.md               ← Snowflake Hands-On with verbatim Stages/Performance/Types/Streams deep-dives
```

## Counts

| Category | Articles / courses | Lessons / Q&As |
|---|---:|---:|
| Interview Q&A articles | 3 | 150 |
| Course curricula (outline-only) | 9 | 411 |
| Full-detail courses (with verbatim article bodies) | 3 | 124 (49 DE Found. + 36 AWS DE + 39 Snowflake) — 15 article bodies included |
| Single-article deep-dive stubs | 1 | 1 (Delta Lake Deep Dive — body placeholder; to be pasted) |
| CTO/Principal learning plans | 7 | 202 (36 AWS DE + 22 Azure DE + 65 DE System Design + 16 Kafka Stream Processing + 20 Kafka Python Pipelines + 19 Advanced PySpark + 24 Data Warehousing lessons) |
| **Total** | **23** | **764** |

## Use

These files are intended as a study path and interview reference:

- **Interview Q&A** (spark / snowflake / python) — full Q&A bodies, suitable for
  drilling or spaced-repetition. Each article ends with an FAQ section.
- **Course curricula** (course-curricula/*) — verbatim lesson outlines with
  format tags (Video / Article / Exercise / Quiz) so you can plan your study
  path or check coverage against a job description.

## Source attribution

Every file carries a header noting the source author (Darshil Parmar, Data Vidhya),
the article title, and the publication date. Content is reproduced without
editorial wrapping per the user's "Authored Q&A only" instruction.

---

## What this is NOT

- **Not an original work.** Every article body in
  this directory is reproduced verbatim from
  Darshil Parmar's [Data Vidhya](https://datavidhya.com/).
  The value here is the *curation* (which articles
  go together, in what order, with what Q&A drill),
  not the authorship.
- **Not a substitute for hands-on practice.** Q&A
  drilling builds recognition; building a real
  pipeline from scratch builds the engineering
  judgment. Use this for the interview; use the
  project directories in the parent `data-engineering/`
  for the engineering.
- **Not vendor-neutral.** The Azure, AWS, Snowflake,
  dbt, and Kafka tracks are vendor-specific by
  design. The DE Foundations track is the most
  portable; the rest are reference patterns for
  *that* cloud or tool.
- **Not the latest syllabus.** Darshil's content
  evolves; this directory is a snapshot as of
  2026-10. For current outlines, the
  [Data Vidhya](https://datavidhya.com/) site is
  the source of truth.

---

## Related directories

- [`../`](../) — the parent `data-engineering/`
  directory. The 18 production-shaped projects
  here are the *engineering* counterpart to the
  *interview prep* in this directory.
- [`../postgres_cdc_kafka/`](../../../projects/postgres_cdc_kafka/) —
  the Kafka reference that pairs with the
  `kafka_fundamentals` curriculum.
- [`../keystone-iceberg-ops/`](../keystone-iceberg-ops/) —
  the data-warehouse ops reference that pairs
  with the `data_warehousing` learning plan.
- [`../scb_aml_platform/`](../scb_aml_platform/) —
  the production-shaped AML build; the
  `de_system_design` curriculum's "real system"
  case study.

---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
