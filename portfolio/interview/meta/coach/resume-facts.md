# Resume Facts — Prem Vishnoi (for interview coaching only)

> Extracted from `Resume/Prem_Resume_2026.pdf` on 2026-09-26.
> LOCAL ONLY — this directory is gitignored. Do not commit.
> Purpose: lets the Leadership Screen coach interrogate *real* claims instead of generic prompts.

## Positioning

- **Current title on resume:** Head of Data | Enterprise AI Architecture | Data Strategy
- **Experience:** 15+ years
- **Marquee employers:** Alibaba (Lazada), CP Group (Makro), PayPal, SCB, DBS, Apple (via Exilant)
- **Geography:** Singapore, Thailand; residency Vietnam TRC
- **Education:** M.S. Data Science, Northwestern (in progress, Sep 2025 – Jan 2027); PGP AI/ML, UT Austin; B.E. ECE, Univ. of Rajasthan
- **Certs:** AWS SA Associate (Dec 2023), Delta Lake Essentials, Generative AI (Educative), Agentic AI (CMKL)

## ⚠️ The level problem — highest-risk question in the loop

The target role is **IC Data Engineer, Product Analytics**. The resume sells **Head of Data**: team of 25, $2M budget, C-level stakeholders, $8B business.

An interviewer will ask some form of: *"You're running a data org — why do you want an IC role at Meta?"*
There is no way to avoid this question. A weak answer ("I'm flexible", "I need a change") reads as either
a flight risk or someone who will resent the scope. Prepare a specific, positive, non-defensive answer.
This is story #0 in the drill rotation and must be airtight.

## Claims an interviewer will stress-test

Each of these is a number with no baseline stated on the resume. Expect "compared to what?", "how was it
measured?", "who else could have caused it?" The coach must attack these by name.

| Claim | Where | The obvious attack |
|---|---|---|
| "$8B+ revenue impact" managed | Summary / Makro | Owning the platform under an $8B business ≠ driving $8B. Do not let this sound like credit-taking. |
| Team scaled **8 → 25** | Makro | Who did you hire vs. inherit? Attrition? Did quality hold? |
| **$2M** annual cloud/vendor budget | Makro | What did you cut, what did you defend, what did you get wrong? |
| Incidents **−60%** | Makro | Baseline count? Definition of incident? Did severity mix shift? |
| **10B+ daily rows**, 99.99% uptime, 500+ daily jobs | Makro Lakehouse | How was uptime measured — jobs, API, or freshness SLA? |
| Month-end close **5 days → 2 hours** | Makro | That's a 60x claim. What specifically was the bottleneck? Who verified? |
| Delivery time **−40%** (O2O / real-time fulfillment) | Makro | Attribution — routing algo vs. data platform vs. ops changes? |
| AWS/Databricks cost **−40%** | Makro *and* Xendit | Same 40% at two employers. Expect skepticism; differentiate the mechanisms. |
| DBT/Spark runtime **−60%** | Xendit | What was slow, what did you change, how measured? |
| FX pipeline manual effort **−80%** | Xendit | Hours saved per month in absolute terms? |
| **100M+ daily events**, 10x growth | Lazada | Your scope vs. the team's? |
| **20M+ insights/day** (Flink + ClickHouse) | Lazada | What is an "insight"? Soft metric — define or drop it. |
| **600+ production tables** owned | Lazada | Ownership breadth is good; be ready on governance/quality at that count. |
| AML for **15+ countries** (Hadoop/Hive) | SCB | Regulatory specifics, MAS compliance. |

## Role history (for "walk me through your background")

| Period | Role | Company |
|---|---|---|
| Jul 2024 – present | Data Engineering (platform owner) | Makro / CP Group |
| Jan 2024 – Jun 2024 | Principal Data Engineer | Xendit.co, SG |
| Jul 2018 – Jan 2024 | VP Data Engineer | Lazada Group (Alibaba) |
| Feb 2016 – Jul 2018 | Big Data Consultant | SCB Bank, Singapore |
| Sep 2015 – Mar 2016 | Big Data Developer | DBS |
| Apr 2014 – Sep 2015 | ETL Data Engineer | PayPal |
| Jan 2011 – Apr 2014 | DWH & Software Engineer | Exilant Tech (Apple) |

**Tenure flag:** Xendit was ~6 months (Jan–Jun 2024). Expect a direct question on why. Have a clean,
non-bitter answer ready.

**Strength to lean on:** Lazada 2018–2024 is 5.5 years at an Alibaba-scale e-commerce platform — the
closest thing on this resume to Meta's scale and product-analytics context. Most technical depth
stories should come from here or Makro.

## Technical surface claimed

- **Engines:** Spark, Kafka, Flink, Airflow, dbt, Hive, Hadoop, ClickHouse
- **Platforms:** Databricks (Unity Catalog, Delta Lake, MLflow), AWS, Azure, Alibaba Cloud
- **Languages:** Python, SQL, Scala, Java, PySpark
- **Modeling:** ODS/CDM/ADS layering, SCD2 framework (DBS), star schema, data contracts, lineage
- **Governance:** GDPR / PDPA / MAS compliance
- **AI:** GenAI, LLM, RAG, NLP, MLOps

**Gap vs. Meta's stack:** no Presto/Trino, Hive-at-Meta-scale, or Meta-internal-equivalent experience
named; no experiment/A-B analytics platform work. Product Analytics DE at Meta leans on retention,
funnels, sessionization, and experiment metrics — practice those explicitly (`medium/meta/datavidhya/`).