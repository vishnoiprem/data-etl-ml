# Prem Vishnoi — Data, ETL, ML & AI Engineering Portfolio

> **One repo. ~2,600 source files. 1,000+ docs. Real pipelines, not toy examples.**
> A working monorepo of production-style projects, hands-on labs, course notes,
> interview playbooks, and writing on the data → ML → GenAI stack.
> **Apache Spark · Apache Flink · Kafka · Airflow · AWS Bedrock · LangChain · LangGraph · RAG · Multi-Agent AI**

<div align="left">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Made with Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Apache Spark](https://img.shields.io/badge/Apache%20Spark-3.x-E25A1C?logo=apachespark&logoColor=white)](https://spark.apache.org/)
[![Apache Flink](https://img.shields.io/badge/Apache%20Flink-Streaming-E6526F?logo=apacheflink&logoColor=white)](https://flink.apache.org/)
[![Kafka](https://img.shields.io/badge/Apache%20Kafka-Streaming-231F20?logo=apachekafka&logoColor=white)](https://kafka.apache.org/)
[![AWS](https://img.shields.io/badge/AWS-Bedrock%20%7C%20S3-FF9900?logo=amazonaws&logoColor=white)](https://aws.amazon.com/)
[![LangChain](https://img.shields.io/badge/LangChain-RAG-1C3C3C)](https://www.langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-1C3C3C)](https://langchain-ai.github.io/langgraph/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Maintained](https://img.shields.io/badge/Maintained-yes-brightgreen.svg)](.)
[![Visitors](https://visitor-badge.laobi.icu/badge?page_id=prem-vishnoi.data-etl-ml)](https://github.com/pvishnoi)

</div>

<p align="left">
  <a href="#-by-the-numbers"><b>By the numbers</b></a> ·
  <a href="#-at-a-glance--headline-projects"><b>Headline projects</b></a> ·
  <a href="#-skills-matrix"><b>Skills</b></a> ·
  <a href="#-featured-deep-dives"><b>Deep dives</b></a> ·
  <a href="#-lessons-learned"><b>Lessons learned</b></a> ·
  <a href="#-writing--interview-prep"><b>Writing</b></a> ·
  <a href="#-how-to-run-a-project-generic"><b>Run</b></a> ·
  <a href="#-interview-qa"><b>Interview Q&amp;A</b></a>
</p>

---

## By the Numbers

> Counts are taken directly from the working tree (auto-refresh: re-run
> `bash scripts/repo_stats.sh`). Last refresh: see top of this README.

| Metric | Value | Source |
|---|---|---|
| Production-style projects | **15+** | `01-projects/` (recommended) |
| Total source files (`.py`, `.sql`, `.yml`, `.yaml`, `Dockerfile`, `.json`) | **2,600+** | `bash scripts/repo_stats.sh` |
| Total docs / notebooks (`.md`, `.ipynb`) | **1,000+** | `bash scripts/repo_stats.sh` |
| Country coverage in AML pipeline | **15** | `data-engineering/scb_aml_platform/` |
| Hive ODS tables modeled | **750+** | `data-engineering/scb_aml_platform/hive/ddl/` |
| Daily transactions at T+1 SLA | **50M+** | `data-engineering/scb_aml_platform/` |
| AML features engineered per customer | **200+** | `data-engineering/scb_aml_platform/spark/feature_engineering/` |
| Search latency p95 (Elasticsearch) | **< 200 ms** | `data-engineering/scb_aml_platform/elasticsearch/` |
| Spark jobs in AML pipeline | **4** | `entity_resolution → aggregation → features → screening` |
| AML rules engine rule types | **6** | `data-engineering/scb_aml_platform/aml_engine/rules/` |
| Risk-scoring components | **3** | CRS · TRS · NRS |
| RAG sub-systems (RAG platform) | **5** | `ingestion · embedding · retrieval · generation · eval` |
| Vector retrieval techniques (RAG) | **4** | `vector · bm25 · hybrid · reranker` |
| Course tracks completed | **5** | `ai-engineering/13-ai-engineering-course/`, etc. |
| Long-form articles | **40+** | `medium/` |
| `README.md` files across the repo | **149** | `bash scripts/repo_stats.sh` |

---

## At a Glance — Headline Projects

> Click any project name to jump to its folder. Each project has its own
> `README.md` with architecture, run instructions, and tests.

### 🏦 Data Engineering & Streaming

| # | Project | What it actually does | Stack | Folder |
|---|---|---|---|---|
| 1 | **SCB AML Platform** | 15-country AML pipeline at Standard Chartered. 750+ Hive ODS tables, 4 Spark jobs (entity resolution, aggregations, 200+ features, sanctions screening), 6-rule engine, CRS/TRS/NRS risk scoring, STR/SAR/CTR alerts, Lucid Search over Elasticsearch. | Sqoop · Kafka · Hive · Spark · Elasticsearch · FastAPI · Airflow | [`data-engineering/scb_aml_platform/`](data-engineering/scb_aml_platform/) |
| 2 | **Realtime Stock Pipeline** | Streaming market data: producers → Kafka → Flink jobs (windows, joins, CDC) → Postgres → Grafana. One-command bring-up with `docker compose`. | Kafka · Flink · Postgres · Grafana · Docker | [`realtime-stock-pipeline/`](realtime-stock-pipeline/) |
| 3 | **Flink CDC Dashboard** | End-to-end CDC: Postgres → Flink SQL → live dashboard. Self-contained with `0_setup_project.sh` → `5_run_dashboard.sh`. | Flink SQL · Postgres · Docker | [`flink-cdc-dashboard/`](flink-cdc-dashboard/) |
| 4 | **Banking AML Data** | AML data modeling + feature engineering on PySpark. | PySpark · Feature Store | [`data-engineering/Banking-AML-Data/`](data-engineering/Banking-AML-Data/) |
| 5 | **Financial Reporting Platform** | Reporting layer on a lakehouse with dbt + Airflow. | dbt · Snowflake/BQ · Airflow | [`data-engineering/financial-reporting-platform/`](data-engineering/financial-reporting-platform/) |
| 6 | **E-commerce End-to-End** | Full e-comm data platform: ingest → marts → serving. | Spark · Airflow · dbt | [`data-engineering/e-commerce-end-2end/`](data-engineering/e-commerce-end-2end/) |
| 7 | **Lazada + Superset** | BI platform with Superset on a warehouse. | Superset · Druid/Starburst | [`data-engineering/lazada-superset/`](data-engineering/lazada-superset/) |
| 8 | **Order ETL (Go)** | Order ETL pipeline written in Go against Postgres. | Go · Postgres | [`golang/order-etl-pipeline/`](golang/order-etl-pipeline/) |
| 9 | **AWS ECS Data Ingestion** | Containerized data ingestion on AWS ECS. | ECS · Docker · AWS | [`aws/ecs-data-ingestion/`](aws/ecs-data-ingestion/) |

### 🤖 AI Engineering (LLM, RAG, Agents)

| # | Project | What it actually does | Stack | Folder |
|---|---|---|---|---|
| 10 | **Enterprise RAG Platform** | Production RAG with 5 sub-systems: `ingestion/loader.py + chunker.py`, `embedding/`, `retrieval/{vector, bm25, hybrid, reranker}.py`, `generation/`, `eval/ragas_eval.py`. Hybrid retrieval + rerank + RAGAS eval. | LangChain · Weaviate · Bedrock · FastAPI | [`ai-engineering/01-enterprise-rag-platform/`](ai-engineering/01-enterprise-rag-platform/) |
| 11 | **Multi-Agent Platform** | Orchestrated agents with shared memory and tool use. Makefile-driven dev workflow. | LangGraph · Bedrock · OpenAI | [`ai-engineering/03-multi-agent-platform/`](ai-engineering/03-multi-agent-platform/) |
| 12 | **Distributed Inference** | Low-latency LLM serving at scale. | vLLM · Triton · Ray | [`ai-engineering/05-distributed-inference/`](ai-engineering/05-distributed-inference/) |
| 13 | **Regulated Industry AI** | Governed AI for banking / financial-crime compliance. | Bedrock · Guardrails · PII | [`ai-engineering/06-regulated-industry/`](ai-engineering/06-regulated-industry/) |
| 14 | **LLMOps Platform** | Eval, monitoring, cost, drift for LLM workloads. | LangSmith · Prometheus | [`ai-engineering/08-llmops-platform/`](ai-engineering/08-llmops-platform/) |
| 15 | **Code-Fix Agent** | Agent that reads broken code, plans a fix, and opens a patch. | LangGraph · Tools | [`ai-engineering/15-code-fix-agent/`](ai-engineering/15-code-fix-agent/) |
| 16 | **Enterprise Search Agent** | Agentic enterprise search over docs + DBs + APIs via MCP. | MCP · Bedrock · LangGraph | [`agentic-ai/2-enterprise-search-agent-full/`](agentic-ai/2-enterprise-search-agent-full/) |
| 17 | **Bedrock + Aurora + S3** | Reference agent stack on AWS Bedrock + Aurora + S3. | Bedrock · Aurora · S3 | [`agentic-ai/3-aws-bedrock-aurora-s3/`](agentic-ai/3-aws-bedrock-aurora-s3/) |
| 18 | **Wiki RAG ReAct** | Wikipedia-grounded ReAct agent. | ReAct · RAG | [`agentic-ai/6_wiki_rag_react_project/`](agentic-ai/6_wiki_rag_react_project/) |
| 19 | **Logistics Route Optimisation** | ML-driven route optimization with OR-Tools. | OR-Tools · ML | [`ai-engineering/9-Logistics-Route-Optimisation/`](ai-engineering/9-Logistics-Route-Optimisation/) |
| 20 | **FM Evaluation Harness** | Reproducible evaluation harness for foundation models. | RAGAS · LangSmith | [`ai-engineering/04-fm-evaluation/`](ai-engineering/04-fm-evaluation/) |
| 21 | **LLM Fine-Tuning** | Fine-tuning experiments, eval, and recipes. | PEFT · LoRA · HF | [`ai-engineering/02-llm-fine-tuning/`](ai-engineering/02-llm-fine-tuning/) |
| 22 | **Prompt Engineering** | Prompt patterns, regression tests, scoring. | LangChain · pytest | [`ai-engineering/07-prompt-engineering/`](ai-engineering/07-prompt-engineering/) |

### 🧪 Labs & Learning Tracks

| # | Track | What's inside | Folder |
|---|---|---|---|
| 23 | AI Engineering Course (DeepLearning.AI-style) | 18 modules: ML foundations → transformers → LLMs → RAG → agents → evals → safety → infra → infra/deployment → frontier ideas. 18 sub-READMEs. | [`ai-engineering/13-ai-engineering-course/`](ai-engineering/13-ai-engineering-course/) |
| 24 | LLM Application Track | 6 sub-courses: LLM fundamentals · evaluation · prompt engineering · RAG · tool-use · agentic systems. | [`ai-engineering/12-llm-application-track/`](ai-engineering/12-llm-application-track/) |
| 25 | Deep Learning Specialization | DL modules with notebooks. | [`ai-engineering/14-deep-learning-specialization/`](ai-engineering/14-deep-learning-specialization/) |
| 26 | Spark Labs | `basic/`, `agg/`, `document-processing/`, `tunning/`, `realtime/`, `windwow/`, `salting/`, `scripts/`. | [`Spark/`](Spark/) |
| 27 | Python (interview + utilities) | Concurrency, Dask, NVIDIA helpers, contracts cycle, linked lists, etc. | [`Python/`](Python/) |
| 28 | Classic ML | GenAI Pinnacle, diffusion, neural networks, vector embeddings, system design. | [`ml/`](ml/) |

---

## Skills Matrix

```
DATA & ETL                  STORAGE / LAKEHOUSE           STREAMING                  CLOUD & PLATFORM
──────────────────         ────────────────────          ────────────              ────────────────
Apache Spark (PySpark)     Hive / Glue Catalog           Apache Flink               AWS (S3, Glue,
Spark Structured Streaming Delta Lake                    Kafka (+Connect, KSQL)      Lambda, ECS,
Airflow / DAGs             Apache Iceberg                Flink CDC                   EKS, Bedrock)
dbt                        Snowflake / BigQuery          Pulsar                     Docker / Compose
Sqoop                      Postgres / Druid              Windowing /                Terraform
Schema & Data              Parquet / Avro / ORC            Watermarks                CI/CD (GitHub
  Modeling                 Feature Store                 Event-time                   Actions)
dbt tests                  LakeFS (data branching)       Exactly-once              Linux / Networking

ML / GENAI                  LLM OPS                       AGENTIC                    LANGUAGES
──────────────────         ────────────                  ─────────                  ─────────
Classical ML               LangSmith / Langfuse          MCP, A2A                   Python (3.10+)
(sklearn, XGBoost)         RAG evaluation                ReAct, Plan-Execute       SQL (advanced)
Deep Learning              Vector DBs                    Tool-use /                 Go
(PyTorch, TF)              (Weaviate, pgvector,           Function-calling         Bash
LLM Apps                    Pinecone)                    Multi-agent               YAML / JSON
(LangChain, LlamaIndex)    Guardrails                    orchestration             HCL/Terraform
RAG / Fine-tuning          Cost & latency                (LangGraph,               Scala (Spark)
Prompt Engineering          observability                CrewAI, Bedrock           Java (Spark)
Distillation                Eval harnesses               Agents)
RAGAS
```

---

## Featured Deep Dives

### 🏦 1. SCB AML Platform

> Standard Chartered Bank | Group Financial Crime Compliance | Feb 2016 – Jul 2018
> 15 countries · 50M+ daily transactions · T+1 SLA · MAS 7-year retention

**What it does, end-to-end:**

```
SOURCE SYSTEMS          INGESTION              PROCESSING                       AML ENGINE              OUTPUT
──────────────          ─────────              ──────────                       ──────────              ──────
Core Banking       ──► Sqoop (batch)      ──► Hive ODS (750+ tables)
Retail             ──► Kafka Connect      ──► Hive CDM (unified)        ──► Rules Engine    ──► STR / SAR / CTR
CIB (SWIFT)        ──► Flat File          ──► Spark Jobs:               ──► Risk Scoring    ──► Case Mgmt
External           ──►                   ──►   Job1: Entity Resolution  ──► Alert Gen        ──► Lucid Search
                                           ──►   Job2: Txn Aggregations        (6 rule types)
                                           ──►   Job3: 200+ Features     ──► 3 risk components
                                           ──►   Job4: Sanctions Screen       CRS · TRS · NRS
```

**Components you can actually open:**

- `aml_engine/rules/` — 6 detection rules
- `aml_engine/risk_scoring/` — CRS / TRS / NRS components
- `aml_engine/alert_generation/` — STR / SAR / CTR generator
- `spark/entity_resolution/` — 3-pass entity resolution
- `spark/aggregation/` — transaction aggregations
- `spark/feature_engineering/` — 200+ AML features
- `spark/screening/` — OFAC / UN / EU + PEP screening
- `elasticsearch/scripts/es_index_manager.py` — index builder
- `lucid_search/api/app.py` — FastAPI search app (Swagger at `/docs`)
- `lucid_search/api/search_engine.py` — search core with Pandas fallback
- `orchestration/pipeline_orchestrator.py` — 9-step end-to-end runner
- `orchestration/airflow_dag.py` — Airflow DAG
- `run_demo.py` — interactive demo

**Key outcomes / metrics:**

| Metric | Value |
|---|---|
| Countries | 15 |
| Hive ODS tables | 750+ |
| Daily transactions | 50M+ |
| AML features per customer | 200+ |
| Processing SLA | T+1 (ready by 08:00) |
| Data retention | 7 years (MAS) |
| Search latency p95 | < 200 ms |
| Spark job count | 4 (entity, agg, features, screening) |
| Risk components | 3 (CRS, TRS, NRS) |
| Rule types | 6 |

**Why it matters:** A regulated, multi-country AML pipeline that satisfies T+1 SLA
and 7-year retention, on a stack that maps 1:1 to modern lakehouse + streaming
architectures. Real data engineers, real compliance, real trade-offs.

Folder: [`data-engineering/scb_aml_platform/`](data-engineering/scb_aml_platform/)

---

### 🌊 2. Realtime Stock Pipeline

Streaming market-data pipeline: producers → Kafka → Flink (joins, windows, CDC)
→ Postgres → Grafana. One-command bring-up with `docker compose`. Sub-second
end-to-end latency for visualization.

**Stack highlight:** Flink is configurable via `flink/flink-conf.yaml`, jobs live
in `flink/jobs/`, the whole thing is wired with `docker-compose.yml`.

Folder: [`realtime-stock-pipeline/`](realtime-stock-pipeline/)

---

### 🤖 3. Enterprise RAG Platform

Production RAG with **5 sub-systems** that match the architecture you'd see in
a real RAG team:

```
Documents
   │  (loader.py)
   ▼
Chunks
   │  (chunker.py)
   ▼
Embeddings ──────► Vector Store
   │                  │
   │                  │   (vector_store.py)
   ▼                  ▼
User Query ──► Hybrid Retriever (hybrid.py) ──► Reranker (reranker.py) ──► Generation
                                                          │
                                                          ▼
                                                   RAGAS Eval (ragas_eval.py)
                                                          │
                                                          ▼
                                                   LangSmith / Reports
```

**What you can actually open:**

- `src/ingestion/loader.py` + `chunker.py`
- `src/embedding/` — embedding model adapters
- `src/retrieval/vector_store.py` — vector DB integration
- `src/retrieval/bm25.py` — lexical retrieval
- `src/retrieval/hybrid.py` — hybrid combiner
- `src/retrieval/reranker.py` — cross-encoder rerank
- `src/generation/` — LLM-backed answer generation
- `src/eval/ragas_eval.py` — RAGAS-based offline evaluation
- `src/api/` — FastAPI service
- `tests/` — unit + integration tests
- `Makefile` — reproducible commands
- `ARCHITECTURE.md` — deeper write-up

**Why it matters:** Real RAG is not "stuff chunks in a vector DB". The
retrieval-only sub-system here has **4** techniques: vector, BM25, hybrid,
reranker. Adding a new retrieval method is a one-file change. Eval is built
in, not bolted on.

Folder: [`ai-engineering/01-enterprise-rag-platform/`](ai-engineering/01-enterprise-rag-platform/)

---

### 🧩 4. Multi-Agent Platform

Orchestrated agents with shared memory, tool-use, and a planner/executor split.
Has its own `Makefile`, `src/`, `tests/`, and `sample_data/`. Modeled on real
LangGraph + Bedrock patterns.

Folder: [`ai-engineering/03-multi-agent-platform/`](ai-engineering/03-multi-agent-platform/)

---

## Lessons Learned (Tattoo These)

> Things I learned the hard way on these projects. Skim them — they're the
> short version of hundreds of pages of course notes.

### Data engineering
1. **SLA is a pipeline property, not a job property.** T+1 only works when
   *every* hop has a budget and a fallback.
2. **Schema drift is the #1 silent killer.** Build schema-validation into
   ingestion, not as a "later" project.
3. **Lakehouse formats (Delta / Iceberg) buy you time-travel and ACID for
   nearly free.** Worth the migration cost from plain Parquet.
4. **Streaming ≠ real-time.** Pick windowing semantics deliberately
   (event-time + watermarks); document them in the job's README.
5. **CDC is a contract.** Postgres WAL → Kafka is straightforward, but
   *the schema you publish* is what every consumer has to live with.

### ML / GenAI
6. **Eval before tuning.** You cannot improve what you cannot measure.
   RAGAS / DeepEval before LoRA, always.
7. **Hybrid retrieval + rerank > bigger embeddings.** Across the projects
   here, hybrid (vector + BM25) with a cross-encoder rerank beat every
   pure-vector variant on groundedness and recall.
8. **Prompt versioning is non-negotiable.** Treat prompts like code: PRs,
   tests, eval-driven merge gates.
9. **Cost is a feature.** LLM cost-per-query should be on the same dashboard
   as p95 latency. Without it, you ship a money leak.
10. **Agent loops must be bounded.** Without a step / time / cost budget, an
    agent will burn budget and never return.

### Engineering hygiene
11. **`requirements.txt` + lockfile. Always.** Pin major, hash at install.
12. **Synthetic data only in a public repo.** Test data should *not* be
    generated from production samples.
13. **Document the failure modes.** Every pipeline's inner README has a
    "What breaks and how to recover" section — you'll thank yourself.

---

## How to Navigate This Repo

- **Recruiter / 60-second scan** → read [At a Glance](#-at-a-glance--headline-projects) and [By the Numbers](#-by-the-numbers).
- **Interview prep (technical)** → pick a project from [Featured Deep Dives](#-featured-deep-dives) and follow its inner README end-to-end.
- **Course / learning path** → browse [Labs & Learning Tracks](#-at-a-glance--headline-projects) or `ai-engineering/13-ai-engineering-course/`.
- **Writing / articles** → see [Writing & Interview Prep](#-writing--interview-prep) and `medium/`.
- **Resume assets** → `Resume/`.

---

## Repository Layout (Recommended)

The repo is currently organized chronologically / by source. Below is the
**proposed target layout** that groups work by purpose so it reads cleanly
top-down for a reviewer. No files have been moved — this is a recommendation
(see migration steps below).

```
data-etl-ml/
├── 01-projects/                 # Production-style buildables (recruiter first stop)
│   ├── data-engineering/
│   │   ├── scb_aml_platform/         # AML pipeline, 15 countries, 50M txns/day
│   │   ├── Banking-AML-Data/
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
├── 02-labs/                    # Hands-on exercises, course work
│   ├── Spark/
│   ├── Python/
│   ├── ml/   (deep_Learning, GenAI-Pinnacle, LLM, ai-agent, vector-ebedding, …)
│   ├── ai-engineering/   (course sub-folders)
│   ├── golang/order-etl-pipeline/
│   └── postgress_cdc_kafka/
├── 03-content/                 # Writing & teaching
│   └── medium/                 # Medium articles + interview guides
├── 04-career/                  # Resume assets
│   └── Resume/
├── 05-reference/               # Reference / scratch / templates
│   ├── app/                    # SAM hello-world template
│   ├── doc/
│   ├── path/
│   ├── pincel-ai-program/
│   ├── sam-installation/
│   └── Senior Delivery Consultant - Data Engineering/
├── infra/                      # Docker, env, scripts
│   ├── docker-compose.yml
│   ├── .env/
│   ├── requirements.txt
│   └── clean_repo.sh
├── docs/                       # Screenshots, demo GIFs, social preview HTML
│   └── assets/
├── scripts/                    # repo_stats.sh and similar
├── .github/                    # REPO_ABOUT, SOCIAL_PREVIEW, issue/PR templates
├── LICENSE
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── DEMOS.md
└── README.md                   # ← you are here
```

### Migration steps

1. Create `01-projects/`, `02-labs/`, `03-content/`, `04-career/`, `05-reference/`, `docs/`, `scripts/`.
2. Move buildable projects into `01-projects/<domain>/…`.
3. Move course / tutorial folders into `02-labs/`.
4. Move `medium/` into `03-content/medium/`.
5. Move `Resume/` into `04-career/Resume/`.
6. Move scratch / template folders into `05-reference/`.
7. Move `docker-compose.yml`, `clean_repo.sh`, `requirements.txt` to `infra/`.
8. Add a short `README.md` to each top-level `0X-…` folder.

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

# 4. Run — pick the right entrypoint for the project
python <entrypoint>.py            # Python pipelines
docker compose up -d              # containerized pipelines
spark-submit <job>.py             # Spark jobs
airflow dags/ webserver / scheduler   # Airflow
uvicorn app:app --reload          # FastAPI

# 5. Test
pytest -v
```

> Each project's inner README has the exact commands.

### Per-stack quick links

- **SCB AML** → `python data-engineering/scb_aml_platform/run_demo.py`
- **Realtime Stock** → `cd realtime-stock-pipeline && docker compose up -d`
- **Flink CDC** → `cd flink-cdc-dashboard && bash 0_setup_project.sh && bash 1_start_containers.sh && bash 2_setup_cdc.sh && bash 3_run_flink_sql.sh && bash 4_run_data_generator.sh && bash "5_run_dashboard.sh"`
- **RAG Platform** → `cd ai-engineering/01-enterprise-rag-platform && make up && make eval`
- **Multi-Agent** → `cd ai-engineering/03-multi-agent-platform && make demo`

---

## Writing & Interview Prep

The `medium/` folder holds long-form articles and interview playbooks.

**Featured interview guides:**

- [Standard Chartered — Director, Data Science](medium/Standard_Chartered_Director_Data_Science_Interview_Guide.md)
- [JPMC — Head, Data & AI Compliance](medium/JPMC_Head_Data_AI_Compliance_Interview_Guide.md)
- [Visa — Director, Data Engineering](medium/Visa_Director_Data_Engineering_Interview_Guide.md)
- [ST Logistics](medium/ST_Logistics_Interview_Guide.md)
- [APAC Solution Architect Playbook](medium/APAC_Solution_Architect_Interview_Playbook.pptx)

**Featured deep-dives:**

- [RAG Production on Databricks](medium/RAG_Production_Databricks.ipynb)
- [RAG Reference Guide](medium/RAG_Reference_Guide.docx)
- [Weaviate for Banking AI](medium/Weaviate_Banking_AI_Complete_Guide.md)
- [DistilBERT](medium/DistilBERT_Medium_Article.md)
- [CLP Data Engineer Interview Prep](medium/CLP_Data_Engineer_Interview_Preparation.md)
- [Metadata Management & Lineage](medium/Metadata-Management-Lineage-Guide.docx)
- [Building Data-Driven Apps in Go](medium/building-data-driven-apps-golang.md)

**Prompting / reasoning techniques:**

- [ReAct — Complete Guide](medium/ReAct-Prompting-Complete-Guide.docx)
- [Tree of Thoughts](medium/Tree-of-Thoughts-Prompting-Complete-Guide.docx)
- [Graph of Thoughts](medium/Graph-of-Thoughts-Prompting-Complete-Guide.docx)
- [Algorithm of Thoughts](medium/algorithm-of-thoughts-prompting-complete-guide.md)
- [Skeleton of Thoughts](medium/Skeleton-of-Thought-Guide.docx)
- [Advanced Prompt Engineering](medium/advanced-prompt-engineering-complete-guide.md)

> 🎬 Looking for live demos? See [DEMOS.md](DEMOS.md).

---

## Interview Q&A (use as talking points)

**Q1. Walk me through the SCB AML pipeline.**
*Ingest from Core Banking (Sqoop batch), Retail (Kafka Connect), CIB/SWIFT (flat file) into a 750+ table Hive ODS. Normalize into a Hive CDM. Run 4 Spark jobs: entity resolution (3-pass), transaction aggregation, 200+ feature engineering, sanctions screening (OFAC/UN/EU + PEP). A 6-rule engine generates alerts; CRS/TRS/NRS scoring ranks them. STR/SAR/CTR feed the case-management system. Lucid Search over Elasticsearch gives compliance officers a sub-200ms search UI. Airflow orchestrates the 9-step pipeline for T+1 SLA.*

**Q2. How do you keep a multi-country pipeline within T+1 SLA?**
*Per-stage budgets (ingest → CDM → features → score → serve), a single Airflow DAG with explicit SLA misses alerting, fallback paths (Pandas search-engine fallback in the AML Lucid Search component), and CDC for late-arriving data instead of waiting for the next batch.*

**Q3. What does your production RAG look like?**
*Five sub-systems: ingestion (loaders + chunkers), embedding, retrieval (vector + BM25 + hybrid + reranker), generation (Bedrock), eval (RAGAS, persisted to LangSmith). Hybrid retrieval with cross-encoder rerank has consistently beaten pure-vector. Eval is part of the merge gate, not a post-hoc check.*

**Q4. How do you decide between RAG and fine-tuning?**
*Default to RAG when the answer is in docs and changes often. Fine-tune when behavior / style is the bottleneck and data is stable. LoRA for parameter-efficient experiments. Always eval both on the same harness before deciding.*

**Q5. How do you keep LLM cost in check?**
*Per-query cost on the same dashboard as p95 latency. Smaller models by default (Claude Haiku / Llama-3-8B), escalate to larger only on hard queries. Cache embeddings. Batch retrieval. Bounded agent loops.*

**Q6. CDC vs batch — when?**
*CDC when a downstream system needs changes within seconds (fraud, inventory, AML triggers) and the upstream is OLTP. Batch when you can wait hours, when you need full-history recompute, or when CDC overhead isn't worth it. The Flink CDC Dashboard project shows the pattern end-to-end.*

**Q7. How do you version data?**
*LakeFS or Delta time-travel. Track schema changes (Glue Catalog / Hive Metastore). Every feature group has a `git_sha` of the producing code as a column. Every model output has the prompt version, model version, and eval run id.*

**Q8. Most interesting bug you debugged here?**
*Event-time vs ingestion-time skew in a Flink job caused late windows to silently drop — fixed with explicit watermarks, allowed lateness, and a reconciliation job that re-derives from the source of truth.*

---

## Conventions Used Across Projects

- **Python** 3.10+; **Spark** 3.x; **Java** 11 for Spark
- Project layout: `config/`, `ingestion/`, `processing/`, `serving/`, `tests/`
- **Tests:** `pytest`, fixtures under `tests/`, sample data under `data/dummy/`
- **Config:** env-driven via `.env`; never hard-code secrets
- **Logging:** structured JSON via `logging` + `python-json-logger`
- **Code style:** `black` + `ruff`; type hints; docstrings on public APIs
- **Reproducibility:** `Makefile` per AI project; `docker-compose.yml` per stream project

---

## Tech Highlights — Numbers & Outcomes

- **50M+** transactions/day processed at T+1 SLA across 15 countries
- **750+** Hive ODS tables modeled and maintained
- **200+** AML features engineered per customer
- **Sub-200ms** search latency on Elasticsearch
- **7-year** retention per MAS regulatory requirement
- **2,600+** source files; **1,000+** docs / notebooks across **149** READMEs
- Multiple **production-style** RAG and agentic-AI builds with cost/eval harnesses

---

## FAQ

**Q: Is this production code or course work?**
Both. Look for the badge at the top of each inner README:
`production-style` projects are built end-to-end and runnable.
`lab` folders are exercises or course work.

**Q: Where do I start?**
Recruiters: [By the Numbers](#-by-the-numbers) and [At a Glance](#-at-a-glance--headline-projects).
Engineers: pick a [Featured Deep Dive](#-featured-deep-dives) and follow its inner README to run it.

**Q: Can I use this code?**
Yes — [MIT](LICENSE). Please keep attribution and don't commit secrets or real data.

**Q: How do I cite a project in an article / CV?**
The repo, the folder name, and the inner README. Most projects have a one-line
"summary" block at the top of their README you can quote directly.

**Q: Where's the streaming demo GIF / RAG screen-cast?**
See [DEMOS.md](DEMOS.md) for the checklist; the assets folder
[`docs/assets/`](docs/assets/) is ready to receive them.

**Q: What does "production-style" mean here?**
It runs end-to-end on synthetic data, has a README with run commands, has
tests, has at least one observability hook (logging, metrics, or eval), and
has a clear extension point (not a sealed demo).

---

## Contact

- **Author:** Prem Vishnoi — Big Data / AI Consultant
- **Resume:** see `Resume/`
- **Articles:** see `medium/`
- **Issues & PRs:** [CONTRIBUTING.md](CONTRIBUTING.md)
- **Code of Conduct:** [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- **License:** [MIT](LICENSE)

---

*All data shown in any demo is synthetic. No real customer or transactional data is included in this repo.*

<!--
README SEO keywords (informational; doesn't change what the rendered page shows):
apache spark, pyspark, spark structured streaming, kafka, flink, flink cdc,
etl pipeline example, data engineering portfolio, aws bedrock, amazon bedrock,
rag retrieval augmented generation, langchain, langgraph, multi-agent,
weaviate, pinecone, vector database, llmops, prompt engineering,
hive, delta lake, iceberg, dbt, airflow, docker, terraform, mlops,
anti money laundering, aml, sanctions screening, ofac, fincrime.
-->