# CLP AI/Data Engineering Interview
## End-to-End Project Portfolio with Full Code

---

**Interview Date:** Monday, 9th March 2026, 5:00 PM
**Focus:** Demonstrate hands-on AI/ML capabilities with production-ready code

---

# TABLE OF CONTENTS

1. [Project 1: Supplier Document LLM (RAG System)](#project-1-supplier-document-llm)
2. [Project 2: Energy Demand Forecasting](#project-2-energy-demand-forecasting)
3. [Project 3: Conversational Data Analytics (Text-to-SQL)](#project-3-conversational-data-analytics)
4. [Interview Q&A for Each Project](#interview-questions-and-answers)

---

# PROJECT 1: SUPPLIER DOCUMENT LLM

## Business Context (CLP Relevant)

CLP manages thousands of suppliers for power generation equipment, maintenance services, and materials. Supplier contracts, compliance documents, and performance reports are scattered across multiple systems. A RAG-based system allows operations teams to ask questions like:
- "What are the warranty terms for Siemens turbines?"
- "Which suppliers are certified for high-voltage work?"
- "What's the lead time for transformer replacement parts?"

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SUPPLIER DOCUMENT LLM ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐    │
│  │   Supplier   │     │   Document   │     │   Text Chunking      │    │
│  │  Documents   │────►│   Loader     │────►│   (Semantic/Fixed)   │    │
│  │  (PDF/DOCX)  │     │  (LangChain) │     │                      │    │
│  └──────────────┘     └──────────────┘     └──────────┬───────────┘    │
│                                                        │                 │
│                                                        ▼                 │
│                                            ┌──────────────────────┐     │
│                                            │   Embedding Model    │     │
│                                            │  (OpenAI/Azure)      │     │
│                                            └──────────┬───────────┘     │
│                                                        │                 │
│                                                        ▼                 │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐    │
│  │    User      │     │   Retriever  │     │    Vector Store      │    │
│  │   Query      │────►│   (Top-K)    │◄───►│   (ChromaDB/FAISS)   │    │
│  └──────────────┘     └──────┬───────┘     └──────────────────────┘    │
│                              │                                          │
│                              ▼                                          │
│                    ┌──────────────────────┐                            │
│                    │   LLM with Context   │                            │
│                    │   (GPT-4/Claude)     │                            │
│                    └──────────┬───────────┘                            │
│                              │                                          │
│                              ▼                                          │
│                    ┌──────────────────────┐                            │
│                    │  Response + Sources  │                            │
│                    └──────────────────────┘                            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Tech Stack
- **Framework:** LangChain
- **Vector Store:** ChromaDB (local) / Pinecone (production)
- **Embeddings:** OpenAI text-embedding-3-small
- **LLM:** GPT-4 / Azure OpenAI
- **Document Processing:** PyPDF, python-docx

---

# PROJECT 2: ENERGY DEMAND FORECASTING

## Business Context (CLP Relevant)

CLP needs to forecast electricity demand to:
- Optimize power generation scheduling
- Plan maintenance windows
- Manage peak load pricing
- Support renewable energy integration

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   ENERGY DEMAND FORECASTING ARCHITECTURE                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐    │
│  │ Smart Meter  │     │   Weather    │     │   Calendar/Holiday   │    │
│  │    Data      │     │     API      │     │       Data           │    │
│  └──────┬───────┘     └──────┬───────┘     └──────────┬───────────┘    │
│         │                    │                        │                 │
│         └────────────────────┼────────────────────────┘                 │
│                              │                                          │
│                              ▼                                          │
│                    ┌──────────────────────┐                            │
│                    │   Feature Pipeline   │                            │
│                    │   (Databricks/Spark) │                            │
│                    └──────────┬───────────┘                            │
│                              │                                          │
│         ┌────────────────────┼────────────────────┐                    │
│         │                    │                    │                    │
│         ▼                    ▼                    ▼                    │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐            │
│  │   Prophet   │    │    LSTM     │    │   XGBoost       │            │
│  │  (Seasonal) │    │ (Deep Learning) │ │  (Gradient Boost) │          │
│  └──────┬──────┘    └──────┬──────┘    └────────┬────────┘            │
│         │                  │                    │                      │
│         └──────────────────┼────────────────────┘                      │
│                            │                                           │
│                            ▼                                           │
│                  ┌──────────────────────┐                             │
│                  │   Ensemble Model     │                             │
│                  │   (Weighted Average) │                             │
│                  └──────────┬───────────┘                             │
│                            │                                           │
│                            ▼                                           │
│                  ┌──────────────────────┐                             │
│                  │  MLflow Model Registry│                            │
│                  │  + Serving Endpoint   │                            │
│                  └──────────────────────┘                             │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

## Tech Stack
- **ML Framework:** scikit-learn, Prophet, TensorFlow/Keras
- **Feature Store:** Databricks Feature Store
- **Experiment Tracking:** MLflow
- **Serving:** FastAPI / Databricks Model Serving

---

# PROJECT 3: CONVERSATIONAL DATA ANALYTICS

## Business Context (CLP Relevant)

Enable business users to ask questions in natural language:
- "What was the total energy consumption last month by district?"
- "Show me the top 10 customers by usage"
- "Compare Q1 vs Q2 revenue"

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                 CONVERSATIONAL DATA ANALYTICS (Text-to-SQL)             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐                                                       │
│  │  User Query  │  "What's the average consumption by district?"        │
│  │  (Natural    │                                                       │
│  │   Language)  │                                                       │
│  └──────┬───────┘                                                       │
│         │                                                               │
│         ▼                                                               │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │                    SCHEMA CONTEXT                             │      │
│  │  • Table definitions (CREATE TABLE statements)                │      │
│  │  • Column descriptions and business meaning                   │      │
│  │  • Sample values for categorical columns                      │      │
│  │  • Relationships between tables                               │      │
│  └──────────────────────────┬───────────────────────────────────┘      │
│                              │                                          │
│                              ▼                                          │
│                    ┌──────────────────────┐                            │
│                    │   LLM (GPT-4/Claude) │                            │
│                    │   SQL Generation     │                            │
│                    └──────────┬───────────┘                            │
│                              │                                          │
│                              ▼                                          │
│                    ┌──────────────────────┐                            │
│                    │   SQL Validation     │                            │
│                    │   & Safety Check     │                            │
│                    └──────────┬───────────┘                            │
│                              │                                          │
│                              ▼                                          │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐   │
│  │   Execute    │────►│   Database   │────►│  Format Results      │   │
│  │    Query     │     │  (Databricks)│     │  + Visualization     │   │
│  └──────────────┘     └──────────────┘     └──────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

# COMPLETE CODE IMPLEMENTATION

Below is the full working code for all three projects. Each can be demonstrated in an interview setting.

---
