# Prem Vishnoi — Data, ETL, ML & AI Engineering Portfolio

> A working monorepo of production-style projects, hands-on labs, course notes,
> interview playbooks, and writing on the data → ML → GenAI stack.
> **Apache Spark · Apache Flink · Kafka · Airflow · AWS Bedrock · LangChain · LangGraph · RAG · Multi-Agent AI**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Made with Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Apache Spark](https://img.shields.io/badge/Apache%20Spark-3.x-E25A1C?logo=apachespark&logoColor=white)](https://spark.apache.org/)
[![Apache Flink](https://img.shields.io/badge/Apache%20Flink-Streaming-E6526F?logo=apacheflink&logoColor=white)](https://flink.apache.org/)
[![Kafka](https://img.shields.io/badge/Apache%20Kafka-Streaming-231F20?logo=apachekafka&logoColor=white)](https://kafka.apache.org/)
[![AWS](https://img.shields.io/badge/AWS-Bedrock%20%7C%20S3-FF9900?logo=amazonaws&logoColor=white)](https://aws.amazon.com/)
[![LangChain](https://img.shields.io/badge/LangChain-RAG-1C3C3C)](https://www.langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-1C3C3C)](https://langchain-ai.github.io/langgraph/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Maintained](https://img.shields.io/badge/Maintained-yes-brightgreen.svg)](.)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

<p align="left">
  <a href="#at-a-glance--headline-projects"><b>Headline projects</b></a> ·
  <a href="#skills-matrix"><b>Skills</b></a> ·
  <a href="#featured-project--scb-aml-platform-deep-dive"><b>Featured: SCB AML</b></a> ·
  <a href="#featured-project--realtime-stock-pipeline"><b>Streaming</b></a> ·
  <a href="#featured-project--enterprise-rag-platform"><b>RAG / Agents</b></a> ·
  <a href="#writing--interview-prep"><b>Writing</b></a> ·
  <a href="#how-to-run-a-project-generic"><b>Run</b></a>
</p>

**Role target:** Senior / Lead Data Engineer · ML Engineer · AI Engineer · Solutions Architect
**Coverage:** Batch ETL · Lakehouse · Streaming · ML · LLM Apps · Agentic AI · Cloud (AWS)
**Status:** Living repo, ~10+ years of work consolidated in one tree for review.

> Looking for a quick tour? Open [At a Glance](#at-a-glance--headline-projects).
> If a link is broken, every project folder has its own `README.md` — start there.

---

## Table of Contents

1. [At a Glance — Headline Projects](#at-a-glance--headline-projects)
2. [Skills Matrix](#skills-matrix)
3. [Repository Layout (Recommended)](#repository-layout-recommended)
4. [How to Navigate This Repo](#how-to-navigate-this-repo)
5. [How to Run a Project (Generic)](#how-to-run-a-project-generic)
6. [Featured Project — SCB AML Platform](#featured-project--scb-aml-platform-deep-dive)
7. [Featured Project — Realtime Stock Pipeline](#featured-project--realtime-stock-pipeline)
8. [Featured Project — Enterprise RAG Platform](#featured-project--enterprise-rag-platform)
9. [Writing & Interview Prep](#writing--interview-prep)
10. [Conventions Used Across Projects](#conventions-used-across-projects)
11. [Tech Highlights — Numbers & Outcomes](#tech-highlights--numbers--outcomes)
12. [FAQ](#faq)
13. [Contact](#contact)

---

## At a Glance — Headline Projects

| Project | What it shows | Stack | Folder |
|---|---|---|---|
| **SCB AML Platform** | End-to-end AML pipeline for 15 countries, 50M+ txns/day, T+1 SLA | Sqoop · Kafka · Hive · Spark · Elasticsearch · FastAPI | [`data-engineering/scb_aml_platform/`](data-engineering/scb_aml_platform/) |
| **Realtime Stock Pipeline** | Sub-second market-data pipeline + Flink jobs + CDC | Kafka · Flink · Postgres · Grafana · Docker | [`realtime-stock-pipeline/`](realtime-stock-pipeline/) |
| **Flink CDC Dashboard** | CDC pipeline with Flink SQL + live dashboard | Flink · Postgres · Docker | [`flink-cdc-dashboard/`](flink-cdc-dashboard/) |
| **Enterprise RAG Platform** | Production RAG: ingestion, retrieval, serving, evals | LangChain · Weaviate · Bedrock · S3 | [`ai-engineering/01-enterprise-rag-platform/`](ai-engineering/01-enterprise-rag-platform/) |
| **Multi-Agent Platform** | Orchestrated agents with shared memory + tool use | LangGraph · Bedrock · OpenAI | [`ai-engineering/03-multi-agent-platform/`](ai-engineering/03-multi-agent-platform/) |
| **Distributed Inference** | Low-latency LLM serving at scale | vLLM · Triton · Ray | [`ai-engineering/05-distributed-inference/`](ai-engineering/05-distributed-inference/) |
| **Regulated Industry AI** | Governed AI for banking/financial-crime compliance | Bedrock · Guardrails · PII | [`ai-engineering/06-regulated-industry/`](ai-engineering/06-regulated-industry/) |
| **LLMOps Platform** | Eval, monitoring, cost, drift for LLM workloads | LangSmith · Prometheus | [`ai-engineering/08-llmops-platform/`](ai-engineering/08-llmops-platform/) |
| **Enterprise Search Agent** | Agentic enterprise search over docs + DBs + APIs | MCP · Bedrock · LangGraph | [`agentic-ai/2-enterprise-search-agent-full/`](agentic-ai/2-enterprise-search-agent-full/) |
| **Logistics Route Optimisation** | ML-driven route optimization | OR-Tools · ML | [`ai-engineering/9-Logistics-Route-Optimisation/`](ai-engineering/9-Logistics-Route-Optimisation/) |
| **Banking AML Data** | AML data modeling + feature engineering | PySpark · Feature Store | [`data-engineering/Banking-AML-Data/`](data-engineering/Banking-AML-Data/) |
| **Financial Reporting Platform** | Reporting layer on a lakehouse | dbt · Snowflake/BQ · Airflow | [`data-engineering/financial-reporting-platform/`](data-engineering/financial-reporting-platform/) |
| **Lazada + Superset** | BI platform, Superset on warehouse | Superset · Druid/Starburst | [`data-engineering/lazada-superset/`](data-engineering/lazada-superset/) |
| **E-commerce End-to-End** | Full e-comm data platform (ingest → marts) | Spark · Airflow · dbt | [`data-engineering/e-commerce-end-2end/`](data-engineering/e-commerce-end-2end/) |
| **Order ETL (Go)** | Order ETL pipeline in Go | Go · Postgres | [`golang/order-etl-pipeline/`](golang/order-etl-pipeline/) |
| **AWS SAM Hello-World** | Serverless reference app on AWS Lambda | SAM · Lambda · API GW | [`app/`](sam-installation/aws-sam-cli-src/) |

> Each project has its own `README.md` with architecture, run instructions, and tests.

---

## Skills Matrix

```
DATA & ETL               STORAGE / LAKEHOUSE        STREAMING                CLOUD & PLATFORM
─────────────────       ────────────────────       ────────────            ────────────────
Apache Spark           Hive / Glue Catalog         Apache Flink            AWS (S3, Glue,
PySpark                Delta Lake                   Kafka (+Connect, KSQL)   Lambda, ECS,
Airflow / DAGs         Iceberg                      Flink CDC                EKS, Bedrock)
dbt                    Snowflake / BigQuery         Pulsar                   Docker / Compose
Sqoop                  Postgres / Druid             Windowing /              Terraform
Schema & Data          Parquet/Avro/ORC              Watermarks              CI/CD (GitHub)
  Modeling              Feature Store

ML / GENAI              LLM OPS                     AGENTIC                 LANGUAGES
─────────────────       ────────────────            ─────────               ─────────
Classical ML            LangSmith / Langfuse        MCP, A2A                Python
(sklearn, XGBoost)      RAG evaluation              ReAct, Plan-Execute     SQL
Deep Learning           Vector DBs                  Tool-use /              Go
(PyTorch, TF)           (Weaviate, pgvector,        Function-calling        Bash
LLM Apps                Pinecone)                   Multi-agent             YAML / JSON
(LangChain, LlamaIndex) Guardrails                  orchestration          HCL/Terraform
RAG / Fine-tuning       Cost & latency              (LangGraph,             Scala (Spark)
Prompt Engineering      observability               CrewAI, Bedrock         Java (Spark)
Distillation            Eval harnesses              Agents)
```

---

## Repository Layout (Recommended)

The repo is currently organized chronologically / by source. Below is the
**proposed target layout** that groups work by purpose so it reads cleanly
top-down for a reviewer. No files have been moved — this is a recommendation.

```
data-etl-ml/
├── 01-projects/                   # Production-style buildables (recruiter first stop)
│   ├── data-engineering/
│   │   ├── scb_aml_platform/         # AML pipeline, 15 countries, 50M txns/day
│   │   ├── Banking-AML-Data/         # AML feature/data modeling
│   │   ├── financial-reporting-platform/
│   │   ├── e-commerce-end-2end/
│   │   ├── lazada-superset/
│   │   ├── clp_projects/
│   │   └── data-enginnering-cloudvala/
│   ├── streaming/
│   │   ├── realtime-stock-pipeline/   # Kafka + Flink + CDC + Grafana
│   │   └── flink-cdc-dashboard/
│   ├── ai-engineering/
│   │   ├── 01-enterprise-rag-platform/
│   │   ├── 03-multi-agent-platform/
│   │   ├── 04-fm-evaluation/
│   │   ├── 05-distributed-inference/
│   │   ├── 06-regulated-industry/
│   │   ├── 07-prompt-engineering/
│   │   ├── 08-llmops-platform/
│   │   ├── 9-Logistics-Route-Optimisation/
│   │   └── 15-code-fix-agent/
│   ├── agentic-ai/
│   │   ├── 2-enterprise-search-agent-full/
│   │   ├── 3-aws-bedrock-aurora-s3/
│   │   ├── 6_wiki_rag_react_project/
│   │   └── 7_Bedrock_course/
│   └── aws/
│       └── ecs-data-ingestion/
│
├── 02-labs/                      # Hands-on exercises, course work
│   ├── Spark/
│   ├── Python/
│   ├── ml/
│   │   ├── deep_Learning/
│   │   ├── GenAI-Pinnacle-Master/
│   │   ├── LLM/
│   │   ├── ai-agent/
│   │   ├── vector-ebedding/
│   │   └── …
│   ├── ai-engineering/            # course sub-folders
│   ├── golang/order-etl-pipeline/
│   └── postgress_cdc_kafka/
│
├── 03-content/                    # Writing & teaching
│   └── medium/                    # Medium articles + interview guides
│
├── 04-career/                     # Resume assets
│   └── Resume/
│
├── 05-reference/                  # Reference / scratch / templates
│   ├── app/                       # SAM hello-world template
│   ├── doc/
│   ├── path/
│   ├── pincel-ai-program/
│   ├── sam-installation/
│   └── Senior Delivery Consultant - Data Engineering/
│
├── infra/                         # Docker, env, scripts
│   ├── docker-compose.yml
│   ├── .env/
│   ├── requirements.txt
│   └── clean_repo.sh
│
└── README.md                      # ← you are here
```

### Suggested migration steps

1. Move buildable projects into `01-projects/<domain>/…`.
2. Move course / tutorial folders into `02-labs/`.
3. Consolidate Medium articles into `03-content/medium/`.
5. Leave `04-career/Resume/` for resume PDFs/DOCX.
6. Keep `.gitignore`, `.env/`, `docker-compose.yml`, `clean_repo.sh` at repo root.
7. Add a short `README.md` to each top-level `0X-…` folder describing what's inside.

---

## How to Navigate This Repo

- **Recruiter / 60-second scan** → read [At a Glance](#at-a-glance--headline-projects) and [Skills Matrix](#skills-matrix).
- **Interview prep (technical)** → jump into a buildable (`01-projects/...`) and follow the **Architecture → Tests → Run** path in its inner README.
- **Course / learning path** → browse `02-labs/` or `ai-engineering/13-ai-engineering-course/`.
- **Writing / articles** → browse `medium/` (search by filename; `*.md` is readable on GitHub).
- **Resume assets** → `Resume/`.

---

## How to Run a Project (Generic)

Most projects follow the same bootstrap:

```bash
# 1. Clone
git clone <this-repo>
cd <project-folder>

# 2. Python venv + install
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Configure
cp .env.example .env  # if present
# edit .env (AWS keys, DB URLs, model names, …)

# 4. Run
# - Python pipelines:    python <entrypoint>.py
# - Docker compose:      docker compose up -d
# - Spark jobs:          spark-submit <job>.py
# - Airflow:             airflow dags/ webserver / scheduler
# - FastAPI:             uvicorn app:app --reload

# 5. Test
pytest -v
```

> Each project's own README has the exact commands.

---

## Featured Project — SCB AML Platform (Deep Dive)

> Standard Chartered Bank | Group Financial Crime Compliance | Feb 2016 – Jul 2018
> 15 countries · 50M+ daily transactions · T+1 SLA · MAS 7-year retention

```
SOURCE SYSTEMS     INGESTION          PROCESSING              AML ENGINE         OUTPUT
──────────────     ─────────          ──────────              ──────────         ──────
Core Banking  ──► Sqoop (batch)  ──► Hive ODS (750+ tables)
Retail        ──► Kafka Connect  ──► Hive CDM (unified)   ──► Rules Engine  ──► STR/SAR/CTR
CIB (SWIFT)   ──► Flat File      ──► Spark Jobs:          ──► Risk Scoring  ──► Case Mgmt
External      ──►               ──►   Job1: Entity Res    ──► Alert Gen     ──► Lucid Search
                                      Job2: Txn Agg
                                      Job3: Features(200+)
                                      Job4: Screening
```

| Metric | Value |
|--------|-------|
| Countries | 15 |
| Hive ODS tables | 750+ |
| Daily transactions | 50M+ |
| AML features | 200+ per customer |
| Processing SLA | T+1 (ready by 08:00) |
| Data retention | 7 years (MAS) |
| Search latency | <200ms |

Folder: [`data-engineering/scb_aml_platform/`](data-engineering/scb_aml_platform/)

---

## Featured Project — Realtime Stock Pipeline

Streaming market-data pipeline: producers → Kafka → Flink (joins, windows, CDC) → Postgres → Grafana.
One-command bring-up with `docker compose`.

Folder: [`realtime-stock-pipeline/`](realtime-stock-pipeline/)

---

## Featured Project — Enterprise RAG Platform

Production RAG covering ingestion (chunking, embedding), retrieval (hybrid + rerank),
serving (FastAPI + Bedrock), eval (LangSmith), and ops (cost/latency dashboards).

Folder: [`ai-engineering/01-enterprise-rag-platform/`](ai-engineering/01-enterprise-rag-platform/)

---

## Writing & Interview Prep

The `medium/` folder holds long-form articles and interview playbooks. A selection:

- **Interview Guides** — Standard Chartered (Director, Data Science) · JPMC (Head, Data & AI Compliance) · Visa (Director, Data Eng) · ST Logistics · APAC Solution Architect
- **AI Engineering Deep-Dives** — RAG Production · Weaviate · Bedrock · DistilBERT
- **Foundational Notes** — Prompt Engineering · ReAct · Tree/Graph-of-Thoughts · Skeleton/Algorithm-of-Thoughts · Metadata & Lineage

See `medium/README.md` for the full index.

---

## Conventions Used Across Projects

- Python 3.10+; Spark 3.x; Java 11 for Spark
- Project layout: `config/`, `ingestion/`, `processing/`, `serving/`, `tests/`
- Tests: `pytest`, fixtures under `tests/`, sample data under `data/dummy/`
- Config: env-driven via `.env`; never hard-code secrets
- Logging: structured JSON via `logging` + `python-json-logger`
- Code style: `black` + `ruff`; type hints; docstrings on public APIs

---

## Tech Highlights — Numbers & Outcomes

- **50M+** transactions/day processed at T+1 SLA across 15 countries
- **750+** Hive ODS tables modeled and maintained
- **200+** AML features engineered per customer
- **Sub-200ms** search latency on Elasticsearch
- **7-year** retention per MAS regulatory requirement
- Multiple **production-style** RAG and agentic-AI builds with cost/eval harnesses

---

## Contact

- **Author:** Prem Vishnoi — Big Data / AI Consultant
- **Resume:** see `Resume/`
- **Articles:** see `medium/`
- **Issues & PRs:** see [CONTRIBUTING.md](CONTRIBUTING.md)
- **Code of Conduct:** see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- **License:** [MIT](LICENSE)

---

## FAQ

**Q: Is this production code or course work?**
Both. Look for the badge at the top of each inner README:
`production-style` projects are built end-to-end and runnable.
`lab` folders are exercises or course work.

**Q: Where do I start?**
Recruiters: read the [At a Glance table](#at-a-glance--headline-projects).
Engineers: pick a headline project, then follow its inner `README.md` to run it.

**Q: Can I use this code?**
Yes — [MIT](LICENSE). Please keep attribution and don't commit secrets or real data.

**Q: How do I cite a project in an article / CV?**
The repo, the folder name, and the inner README. Most projects have a one-line
"summary" block at the top of their README you can quote directly.

**Q: Where's the streaming demo GIF / RAG screen-cast?**
See `.github/REPO_ABOUT.md` for media checklist (you'll need to record & drop
files in `docs/assets/` — the README has placeholder hooks for them).

---

*All data shown in any demo is synthetic. No real customer or transactional data is included in this repo.*

<!--
README SEO keywords (informational; doesn't change what the rendered page shows):
apache spark, pyspark, spark structured streaming, kafka, flink, flink cdc,
etl pipeline example, data engineering portfolio, aws bedrock, amazon bedrock,
rag retrieval augmented generation, langchain, langgraph, multi-agent,
weaviate, pinecone, vector database, llmops, prompt engineering,
hive, delta lake, iceberg, dbt, airflow, docker, terraform, mlops.
-->