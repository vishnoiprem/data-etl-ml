# SCB AML Platform — End-to-End Implementation

**Standard Chartered Bank | Group Financial Crime Compliance**
**Author:** Prem Vishnoi, Big Data Consultant
**Period:** February 2016 – July 2018
**Coverage:** 15 Countries | 50M+ Daily Transactions | T+1 SLA

---

## Architecture Overview

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

---

## Project Structure

```
scb_aml_platform/
├── config/settings.py               # All configuration
├── data/dummy/generate_dummy_data.py # Dummy data for 15 countries
├── ingestion/
│   ├── sqoop_ingest.py              # Batch ingestion simulator
│   └── kafka_producer.py            # Near-real-time stream simulator
├── hive/
│   ├── ddl/{ods,cdm,ads}_tables.sql # Hive DDL (ODS→CDM→ADS)
│   └── scripts/hive_simulator.py    # SQLite-backed local Hive
├── spark/
│   ├── entity_resolution/job1_*.py  # 3-pass entity resolution
│   ├── aggregation/job2_*.py        # Txn aggregations
│   ├── feature_engineering/job3_*.py # 200+ AML features
│   └── screening/job4_*.py          # OFAC/UN/EU + PEP screening
├── aml_engine/
│   ├── rules/rules_engine.py        # 6 AML detection rules
│   ├── risk_scoring/risk_scoring_engine.py  # CRS/TRS/NRS scores
│   └── alert_generation/alert_generator.py # STR/SAR/CTR alerts
├── elasticsearch/
│   ├── mappings/                    # ES index mappings + analyzers
│   └── scripts/es_index_manager.py  # Index builder
├── lucid_search/
│   ├── api/search_engine.py         # Core search (ES + Pandas fallback)
│   ├── api/app.py                   # FastAPI REST application
│   └── tests/                       # Unit + integration tests
├── orchestration/
│   ├── pipeline_orchestrator.py     # Full 9-step pipeline runner
│   └── airflow_dag.py               # Airflow DAG definition
├── run_demo.py                      # Interactive demo
└── requirements.txt
```

---

## PyCharm Setup

### 1. Open Project
`File → Open → select project folder`

### 2. Create Virtual Environment
`File → Settings → Project → Python Interpreter → Add → Virtualenv → Python 3.10+`

### 3. Install Dependencies
```bash
pip install -r scb_aml_platform/requirements.txt
```

### 4. Mark Source Root
Right-click project root → `Mark Directory As → Sources Root`

### 5. Run Full Pipeline
```bash
python scb_aml_platform/orchestration/pipeline_orchestrator.py
```

### 6. Run Interactive Demo
```bash
python scb_aml_platform/run_demo.py
```

### 7. Start Lucid Search API
```bash
cd scb_aml_platform/lucid_search/api
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
# Open: http://localhost:8000/docs
```

### 8. Run Tests
```bash
pytest scb_aml_platform/lucid_search/tests/ -v
```

---

## Lucid Search API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /docs` | Swagger UI |
| `GET /health` | Health check |
| `GET /stats` | Platform statistics |
| `GET /search?q=Mohammed+Al-Rahman` | Fuzzy name search |
| `GET /search?q=Mohammed&countries=SG,HK&risk_band=HIGH` | Filtered search |
| `GET /entity/{id}` | Full entity profile |
| `GET /entity/{id}/network` | Relationship network graph |
| `GET /demo/use-case-1` | Cross-border ML detection demo |
| `GET /demo/use-case-2` | Trade-based ML detection demo |

---

## Key Metrics

| Metric | Value |
|--------|-------|
| Countries | 15 |
| Hive ODS Tables | 750+ |
| Daily Transactions | 50M+ |
| AML Features | 200+ per customer |
| Processing SLA | T+1 (ready by 08:00) |
| Data Retention | 7 years (MAS) |
| Search Latency | <200ms (ES) |

*All data is synthetic. No real customer data included.*
