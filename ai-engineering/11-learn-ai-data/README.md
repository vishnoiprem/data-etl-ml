# AI for Data Engineering — Complete Course Notes

> Source: [Data Vidhya — AI for Data Engineering](https://datavidhya.com/learn/ai-for-data-engineering/)
> Author: Darshil Parmar | Level: Intermediate | 57 lessons across 8 modules
> Tech: Python, LLMs | Prereqs: DE Fundamentals + Python Fundamentals

---

## Course Promise

> "Use AI to ship pipelines faster **and** build the data infra AI runs on — vector DBs, RAG, and feature stores."

This is the **two-sided** AI-for-DE curriculum:
1. **AI as a tool** — accelerate your daily DE work (SQL, pipelines, docs, testing).
2. **AI as a workload** — engineer the storage, retrieval, and serving systems that production LLM/ML applications depend on.

---

## Module Map

| # | Module | Lessons | Theme |
|---|--------|--------:|-------|
| 1 | [AI-Powered DE Foundations](./01-ai-powered-de-foundations/) | 8 | Mental models, prompt craft, trust/verify, ethics |
| 2 | [AI for SQL & Analytics](./02-ai-for-sql-analytics/) | 7 | Text-to-SQL, query tuning, profiling, NL interfaces |
| 3 | [AI for Pipeline Development](./03-ai-for-pipeline-development/) | 8 | Spark, dbt, Airflow, testing, self-healing pipelines |
| 4 | [Vector Databases & Embeddings](./04-vector-databases-embeddings/) | 7 | Embeddings, ANN indexes, hybrid search, scale |
| 5 | [RAG & LLM Data Infrastructure](./05-rag-llm-llm-data-infrastructure/) | 7 | Ingestion, chunking, prod RAG, eval, frameworks |
| 6 | [Feature Stores & ML Data Infra](./06-feature-stores-ml-data-infra/) | 7 | Online/offline serving, training-data versioning, LLMOps |
| 7 | [AI on Cloud Platforms](./07-ai-on-cloud-platforms/) | 6 | AWS / GCP / Azure / Databricks / Snowflake Cortex |
| 8 | [AI DE System Design](./08-ai-de-system-design/) | 7 | Recsys, Enterprise RAG, Feature Platform, Fraud, Multi-Modal |

**Total: 57 lessons · 8 modules · Hands-on systems-design capstone**

---

## How to Use These Notes

Each module folder contains:
```
NN-module-name/
├── README.md                  # Module overview + lesson index
├── 01-lesson-slug.md          # Article-style notes per lesson
├── 02-lesson-slug.md
├── ...
└── examples/                  # (where applicable) runnable code snippets
```

Premium lessons on Data Vidhya are marked *(premium)* in the source; the notes here are **complete and self-contained** — they are not a substitute for the videos, but they are everything you need to review, interview-prep from, or build the projects.

---

## Shared Resources

See [`resources/`](./resources/) for:
- `prompt-library.md` — Reusable prompt templates (text-to-SQL, code-gen, doc-gen, eval).
- `tooling-cheatsheet.md` — Cursor / Copilot / Claude Code / Aider / Continue.dev setup.
- `vector-db-comparison.md` — Pinecone vs Weaviate vs Qdrant vs pgvector vs Milvus.
- `feature-store-comparison.md` — Feast vs Tecton vs Databricks Feature Store vs SageMaker.
- `evaluation-playbook.md` — How to evaluate RAG, classification, and extraction pipelines.

---

## Learning Tracks

This course is part of the **Data Engineer** career track on Data Vidhya:
DE Fundamentals → Python → SQL → dbt → PySpark → Databricks → Airflow → Kafka → AWS/GCP/Azure → Projects → **AI for DE** → DE System Design.

After this course, the suggested next step is:
**Data Engineering Interview Prep: The Complete Course** (98 lessons).

---

## Capstone / Project Ideas

The Data Vidhya hub lists "Projects for this course are on the way." Until then, the System Design lessons in Module 8 double as project briefs:

1. **Recommendation Pipeline** — batch embeddings + ANN retrieval + LLM reranker.
2. **Enterprise RAG** — multi-tenant, ACL-filtered, hybrid search, eval harness.
3. **Feature Platform** — online + offline parity, point-in-time joins, drift monitoring.
4. **Fraud Detection** — streaming feature engineering + low-latency model serving.
5. **Multi-Modal Platform** — text + image + audio ingestion → unified embeddings store.

Pick one. Implement it. You have the module notes.
