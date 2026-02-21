# SCB AML Platform

**Standard Chartered Bank — Group Financial Crime Compliance (GFCC)**

| Field | Detail |
|-------|--------|
| **Author** | Prem Vishnoi, Big Data Consultant |
| **Period** | February 2016 – July 2018 |
| **Location** | Singapore HQ |
| **Coverage** | 15 Countries — SG, HK, MY, TH, IN, KR, TW, UK, US, AE, KE, NG, PK, BD, CN |
| **Tech Stack** | Hadoop · HDFS · Hive · Apache Spark · Sqoop · Kafka · Elasticsearch · Oozie/Airflow |
| **Banking Lines** | Core Banking · Retail Banking · Corporate & Institutional Banking (CIB) |
| **Regulatory** | MAS (SG) · FCA (UK) · FinCEN (US) · HKMA · RBI + 10 local regulators |

---

## Architecture Diagrams

| Diagram | File |
|---------|------|
| End-to-End Platform Architecture | `doc/SCB_AML_Architecture_Diagram.png` |
| Hive & Spark Pipeline Detail | `doc/SCB_AML_Pipeline_Diagram.png` |
| Lucid Search Application | `doc/SCB_Lucid_Search_Diagram.png` |
| Full Technical Document | `doc/SCB_AML_Project_Prem_Vishnoi.docx` |

### End-to-End Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     SOURCE SYSTEMS                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │ Core Banking │  │Retail Banking│  │     CIB      │  │  External   │ │
│  │Customer/KYC  │  │Deposits/Cards│  │SWIFT/Trade   │  │OFAC/UN/PEP  │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘ │
└─────────┼─────────────────┼─────────────────┼─────────────────┼────────┘
          │   Sqoop(batch)  │  Kafka Connect  │   Flat File     │ Daily
          ▼                 ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              HADOOP HDFS — Raw Data Landing Zone                        │
│     /raw/{country_code}/{source}/{YYYY}/{MM}/{DD}/                      │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │
          ┌───────────────────┴──────────────────┐
          ▼                                      ▼
┌─────────────────────┐              ┌──────────────────────────┐
│  Apache Hive        │              │  Apache Spark            │
│  Data Warehouse     │◄────────────►│  Transformation Engine   │
│                     │              │                          │
│  ODS Layer          │              │  Job1: Entity Resolution │
│  (750+ raw tables)  │              │  Job2: Txn Aggregation   │
│  CDM Layer          │              │  Job3: Feature Eng(200+) │
│  (unified schema)   │              │  Job4: Sanctions Screen  │
│  ADS Layer          │              │                          │
│  (AML-ready)        │              └──────────────────────────┘
└─────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     AML DETECTION ENGINE                                 │
│  ┌──────────────┐  ┌──────────────────┐  ┌───────────────────────────┐  │
│  │ Rules-Based  │  │  Risk Scoring    │  │    Alert Generation       │  │
│  │ Detection    │  │  CRS / TRS / NRS │  │  STR · SAR · CTR          │  │
│  │ CTR          │  │  Composite 0-100 │  │  Regulatory Filing Queue  │  │
│  │ Structuring  │  │  LOW/MED/HIGH    │  │                           │  │
│  │ Sanctions    │  │  /CRITICAL       │  │                           │  │
│  └──────────────┘  └──────────────────┘  └───────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
          │                                          │
          ▼                                          ▼
┌─────────────────────┐              ┌──────────────────────────────────┐
│  Case Management    │              │  Lucid Search (Elasticsearch)    │
│  Investigation →    │              │  entity_master index             │
│  Analyst Review →   │              │  transaction_summary index       │
│  Disposition        │              │  screening_results index         │
│                     │              │  relationship_graph index        │
└─────────────────────┘              └──────────────────────────────────┘
```

---

## Project Structure

```
scb_aml_platform/
│
├── config/
│   └── settings.py                      # All platform config: countries, thresholds,
│                                        # ES connection, Kafka, regulatory SLAs
│
├── data/                                # Auto-created at runtime
│   ├── dummy/
│   │   └── generate_dummy_data.py       # Generates realistic banking data for 15 countries
│   │                                    # Includes high-risk entities (Mohammed Al-Rahman,
│   │                                    # Dragon Trading Ltd, Viktor Petrov)
│   ├── processed/                       # Spark job outputs (parquet files)
│   ├── hdfs_sim/                        # Local HDFS simulation
│   └── es_simulation/                   # Elasticsearch JSON fallback
│
├── ingestion/
│   ├── sqoop_ingest.py                  # Sqoop batch: Oracle/DB2 → HDFS partitions
│   │                                    # Pattern: /raw/{country}/{source}/{YYYY}/{MM}/{DD}/
│   └── kafka_producer.py               # Kafka Connect: high-value wires + large cash
│                                        # Topics: scb.transactions.raw, scb.wire_transfers.raw
│
├── hive/
│   ├── ddl/
│   │   ├── ods_tables.sql               # ODS: per-country raw staging
│   │   │                                # ods_sg.customer_raw, ods_hk.transaction_raw, ...
│   │   │                                # PARTITIONED BY (country_code, dt), ORC+Snappy
│   │   ├── cdm_tables.sql               # CDM: unified cross-country models
│   │   │                                # cdm.dim_customer_unified, cdm.fact_transaction_unified
│   │   └── ads_tables.sql               # ADS: AML-ready analytical tables
│   │                                    # ads.customer_risk_profile, ads.aml_alert_master
│   └── scripts/
│       └── hive_simulator.py            # SQLite-backed Hive for local development
│                                        # (no Hadoop cluster required)
│
├── spark/
│   ├── entity_resolution/
│   │   └── job1_entity_resolution.py    # PASS 1: Exact passport/ID match across countries
│   │                                    # PASS 2: Jaro-Winkler fuzzy (threshold ≥ 0.85)
│   │                                    # PASS 3: Double Metaphone phonetic match
│   │                                    # OUTPUT: golden_entity_id linking all representations
│   │
│   ├── aggregation/
│   │   └── job2_transaction_aggregation.py  # Daily/weekly/monthly txn aggregations
│   │                                        # Cross-border flow analysis by country pair
│   │                                        # Volume velocity (week-over-week change %)
│   │
│   ├── feature_engineering/
│   │   └── job3_feature_engineering.py  # 200+ behavioural features per customer:
│   │                                    # Velocity: txn_count_1d/7d/30d/90d
│   │                                    # Structuring: count_just_below_threshold
│   │                                    # Cross-border: unique_countries_30d, high_risk_vol
│   │                                    # Network: degree_centrality, betweenness
│   │                                    # Behavioural: dormancy_days, channel_diversity
│   │                                    # KYC: kyc_age_days, risk_rating_changes
│   │
│   └── screening/
│       └── job4_sanctions_pep_screening.py  # Fuzzy match vs OFAC SDN, UN, EU + 10 local lists
│                                            # PEP relationship inference (spouse/child/associate)
│                                            # Match confidence scoring 0-100
│
├── aml_engine/
│   ├── rules/
│   │   └── rules_engine.py              # R01 CTR: single txn ≥ USD 10,000
│   │                                    # R02 Structuring: multiple txns just below threshold
│   │                                    # R03 Sanctions: confirmed hit score ≥ 80
│   │                                    # R04 PEP Wire: PEP customer wire ≥ USD 50,000
│   │                                    # R05 Velocity: txn spike > 3× 30d average
│   │                                    # R06 High-Risk Jurisdiction: FATF-listed countries
│   │
│   ├── risk_scoring/
│   │   └── risk_scoring_engine.py       # CRS (Customer Risk Score):  KYC + PEP + demographics
│   │                                    # TRS (Transaction Risk Score): velocity + structuring
│   │                                    # NRS (Network Risk Score): graph + cross-border
│   │                                    # Composite = 0.35*CRS + 0.40*TRS + 0.25*NRS
│   │                                    # Bands: LOW(0-30) MEDIUM(31-60) HIGH(61-80) CRITICAL(81+)
│   │
│   └── alert_generation/
│       └── alert_generator.py           # Merges rules + risk scores
│                                        # Assigns STR/SAR/CTR report type
│                                        # Per-country regulatory SLA due dates
│                                        # OUTPUT: aml_alert_master.parquet
│                                        #         regulatory_filing_queue.csv
│
├── elasticsearch/
│   ├── mappings/
│   │   ├── entity_master_mapping.json   # 5 shards × 2 replicas
│   │   │                                # Custom analyzers: Double Metaphone + n-gram (3-5)
│   │   └── transaction_summary_mapping.json
│   └── scripts/
│       └── es_index_manager.py          # Creates 4 indices + bulk indexes all data
│                                        # Falls back to JSON files if ES unavailable
│
├── lucid_search/
│   ├── api/
│   │   ├── search_engine.py             # Core engine: ES when available, Pandas fallback
│   │   │                                # Fuzzy (Jaro-Winkler), phonetic (Metaphone),
│   │   │                                # cross-script (Arabic↔Latin), wildcard, multi-country
│   │   └── app.py                       # FastAPI REST application
│   │                                    # GET /search, /entity/{id}, /entity/{id}/network
│   │                                    # GET /demo/use-case-1, /demo/use-case-2
│   │                                    # Swagger UI at /docs
│   └── tests/
│       ├── test_search.py               # Search engine integration tests
│       └── test_aml_engine.py           # Rules + scoring unit tests
│
├── orchestration/
│   ├── pipeline_orchestrator.py         # Runs all 9 steps in sequence
│   │                                    # 00:00 Sqoop → 02:00 ODS → 03:00 CDM
│   │                                    # 05:00 Spark → 06:00 AML → 07:00 Lucid → 08:00 Ready
│   └── airflow_dag.py                   # Airflow DAG (schedule: daily 00:00 SGT)
│                                        # Copy to $AIRFLOW_HOME/dags/ for production
│
├── utils/
│   └── logger.py                        # Loguru logger setup (file + stderr)
│
├── doc/                                 # Architecture diagrams
│   ├── SCB_AML_Architecture_Diagram.png
│   ├── SCB_AML_Pipeline_Diagram.png
│   └── SCB_Lucid_Search_Diagram.png
│
├── run_demo.py                          # Interactive demo with rich terminal output
├── requirements.txt                     # All Python dependencies
└── README.md                            # This file
```

---

## Daily Pipeline Schedule

```
00:00  ──► Sqoop Extract Starts       (Oracle/DB2 incremental pulls, 15 countries)
02:00  ──► ODS Load Complete          (750+ Hive tables partitioned by country+date)
03:00  ──► CDM Transform Complete     (unified customer/account/transaction models)
05:00  ──► Spark Jobs Complete        (entity resolution + aggregation + features + screening)
06:00  ──► AML Screening + Alert Gen  (rules engine + risk scoring + STR/SAR/CTR filing)
07:00  ──► Lucid Search Index Refresh (Elasticsearch bulk index update)
08:00  ──► Analysts Start Work        ✓ T+1 SLA MET
```

All 15 country pipelines run in parallel with country-level dependency management.

---

## Key Platform Metrics

| Metric | Value | Context |
|--------|-------|---------|
| Countries | 15 | SG, HK, MY, TH, IN, KR, TW, UK, US, AE, KE, NG, PK, BD, CN |
| Hive ODS Tables | 750+ | 15 countries × ~50 tables each |
| Daily Transactions | 50M+ | All banking lines combined |
| Entities Indexed | 10M+ | Elasticsearch entity_master |
| AML Features | 200+ | Behavioural features per customer |
| Analysts | 200+ | Using Lucid Search daily |
| Search Latency | <200ms | Lucid Search avg response (10M entity index) |
| Processing SLA | T+1 | Yesterday's data ready by 08:00 |
| Data Retention | 7 years | MAS regulatory requirement |
| Pipeline Uptime | 99.9% | Zero missed regulatory SLAs |
| Entity Match Recall | 95%+ | Cross-country entity resolution |
| False Positive Rate | <5% | Entity resolution matching |

---

## Lucid Search — High-Risk Entity Identification

The `Lucid Search` application was built on Elasticsearch to allow AML analysts
to search 10M+ entities across all 15 countries in under 200ms.

### Elasticsearch Indices

| Index | Purpose | Key Fields |
|-------|---------|-----------|
| `entity_master` | Golden entity profiles | name, name_variants[], DOB, risk_score, pep_flag |
| `transaction_summary` | Aggregated txn metrics | txn_count, total_volume, cross_border_vol |
| `screening_results` | Sanctions/PEP matches | matched_list, match_score, match_type |
| `relationship_graph` | Entity network edges | entity_id, related_entities[], relationship_type |

### Search Modes

| Mode | How It Works | Example |
|------|-------------|---------|
| Fuzzy | Jaro-Winkler + edit distance | "Mohamad" finds "Mohammed" |
| Phonetic | Double Metaphone encoding | "Chen" finds "Chan" |
| Cross-Script | Transliterated + original script | Arabic ↔ Latin, Chinese ↔ Pinyin |
| Wildcard | N-gram partial matching | "Al-Rah\*" finds all variants |
| Multi-Country | Federated across all 15 indices | One search = all jurisdictions |
| Filtered | Name + risk_band + country + PEP | "Mohammed" + HIGH + AE |

### Real-World Use Cases

**Use Case 1 — Cross-Border Money Laundering:**
```
Analyst searches "Mohammed Al-Rahman"
  → Finds 15 name variants across SG, HK, AE
  → Transaction summary: USD 5M cross-border wires in 90 days
  → Network graph: linked shell companies in 3 jurisdictions
  → PEP match: Grade B (associate of foreign official)
  → STR filed with MAS within 24 hours
```

**Use Case 2 — Trade-Based Money Laundering:**
```
RM searches "Dragon Trading Ltd" (pre-onboarding CDD)
  → Finds 3 related companies across HK, SG, BVI
  → Relationship graph: circular fund flows
  → Risk score: 87/100 (HIGH)
  → Onboarding rejected, referral to GFCC
```

---

## AML Rules Reference

| Rule | Trigger | Report | Score |
|------|---------|--------|-------|
| R01 CTR | Single transaction ≥ USD 10,000 | CTR | 60 |
| R02 Structuring | 3+ txns 85–100% of CTR threshold in 3 days | STR | 75 |
| R03 Sanctions | Match score ≥ 80 vs OFAC/UN/EU | STR | 90 |
| R04 PEP Wire | PEP customer wire ≥ USD 50,000 | STR | 80 |
| R05 Velocity | Daily txn rate > 3× 30-day average | STR | 65 |
| R06 High-Risk | Wire to FATF high-risk jurisdiction | STR | 70 |

---

## Risk Scoring Model

```
CRS (Customer Risk Score) — 35% weight
  Base rating:       low=10, medium=40, high=80
  PEP modifier:      +20 (Grade A), +15 (B), +10 (C)
  KYC staleness:     +20 if >730 days, +10 if >365 days
  KYC status:        +10 expired, +5 pending, -5 verified

TRS (Transaction Risk Score) — 40% weight
  Volume spike:      +20 if >200% change, +10 if >100%
  Structuring:       up to +40 based on structuring_score
  Dormancy+spike:    +15 if dormant >180d then reactivated
  High volume:       +15 if 30d vol >USD 1M

NRS (Network Risk Score) — 25% weight
  Degree centrality: up to +30 (hub in suspicious network)
  Cross-border:      +15 if >50% volume to high-risk countries
  Unique countries:  +3 per country (max +15)
  Sanctions hit:     +25 if confirmed match ≥ 80

Composite AML Score = 0.35×CRS + 0.40×TRS + 0.25×NRS
  0–30   → LOW
  31–60  → MEDIUM
  61–80  → HIGH
  81–100 → CRITICAL
```

---

## PyCharm Setup

### 1. Open Project
```
File → Open → /data-etl-ml/data-engineering/scb_aml_platform
```

### 2. Create Virtual Environment
```
File → Settings → Project → Python Interpreter
  → Add Interpreter → Virtualenv Environment
  → Base interpreter: Python 3.10+
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Mark Source Root
```
Right-click scb_aml_platform/ → Mark Directory As → Sources Root
```

### 5. Run Configurations (Edit Configurations → + → Python)

| Config Name | Script | Description |
|-------------|--------|-------------|
| Generate Data | `data/dummy/generate_dummy_data.py` | First run — creates all dummy data |
| Full Pipeline | `orchestration/pipeline_orchestrator.py` | All 9 steps end-to-end |
| Interactive Demo | `run_demo.py` | Rich terminal demo with tables |
| Lucid Search API | `lucid_search/api/app.py` | FastAPI server on port 8000 |

### 6. Step-by-Step Commands

```bash
# Step 0: Generate dummy data (required on first run)
python data/dummy/generate_dummy_data.py

# Step 1-2: Ingestion + Hive load
python ingestion/sqoop_ingest.py
python hive/scripts/hive_simulator.py

# Step 3-6: Spark jobs
python spark/entity_resolution/job1_entity_resolution.py
python spark/aggregation/job2_transaction_aggregation.py
python spark/feature_engineering/job3_feature_engineering.py
python spark/screening/job4_sanctions_pep_screening.py

# Step 7-9: AML detection
python aml_engine/risk_scoring/risk_scoring_engine.py
python aml_engine/rules/rules_engine.py
python aml_engine/alert_generation/alert_generator.py

# Step 10: Elasticsearch index refresh
python elasticsearch/scripts/es_index_manager.py

# OR: Run everything in one command
python orchestration/pipeline_orchestrator.py

# Start Lucid Search API
uvicorn lucid_search.api.app:app --host 0.0.0.0 --port 8000 --reload

# Run tests
pytest lucid_search/tests/ -v
```

---

## Lucid Search API Reference

Start: `uvicorn lucid_search.api.app:app --port 8000 --reload`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/docs` | Swagger UI (interactive) |
| GET | `/health` | Health + backend status |
| GET | `/stats` | Platform statistics |
| GET | `/search?q={name}` | Search by entity name |
| GET | `/search?q={name}&countries=SG,HK&risk_band=HIGH` | Filtered search |
| GET | `/search?q={name}&pep_only=true` | PEP entities only |
| GET | `/entity/{entity_id}` | Full entity profile |
| GET | `/entity/{entity_id}/network` | Relationship network graph |
| GET | `/entity/{entity_id}/transactions` | Transaction summary |
| GET | `/screening/{entity_id}` | Sanctions/PEP screening results |
| GET | `/demo/use-case-1` | Cross-border ML detection demo |
| GET | `/demo/use-case-2` | Trade-based ML detection demo |

**Example queries:**
```bash
curl "http://localhost:8000/search?q=Mohammed+Al-Rahman"
curl "http://localhost:8000/search?q=Mohammed&countries=SG,HK,AE&risk_band=HIGH"
curl "http://localhost:8000/demo/use-case-1"
curl "http://localhost:8000/stats"
```

---

## Elasticsearch Setup (Optional)

The platform runs fully without Elasticsearch — the search engine automatically
falls back to Pandas in-memory mode with the same API interface.

To enable real Elasticsearch:

```bash
# macOS (Homebrew)
brew install elastic/tap/elasticsearch-full
brew services start elastic/tap/elasticsearch-full

# Docker
docker run -p 9200:9200 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  docker.elastic.co/elasticsearch/elasticsearch:8.9.0

# Verify
curl http://localhost:9200/_cat/health

# Load indices
python elasticsearch/scripts/es_index_manager.py
```

---

## Regulatory Compliance

| Requirement | Implementation |
|-------------|----------------|
| 7-year data retention | ORC tables with `retention.period=7years` TBLPROPERTY |
| Data sovereignty | Separate HDFS namespaces + Hive schemas per country |
| T+1 processing SLA | Full pipeline completes by 08:00 (monitored via Oozie/Airflow) |
| Audit trails | Every query logged with analyst ID, timestamp, entity accessed |
| STR < 24hr SLA | Automated STR generation with regulatory filing queue |
| Daily sanctions refresh | OFAC/UN/EU/local lists updated every run cycle |

| Regulator | Country | Report Type |
|-----------|---------|-------------|
| MAS | SG | STR (Suspicious Transaction Report) |
| FCA | UK | SAR (Suspicious Activity Report) |
| FinCEN | US | SAR + CTR |
| HKMA | HK | STR |
| RBI | IN | STR |
| BNM | MY | STR |
| CBUAE | AE | STR |
| + 8 more | KR, TW, TH, KE, NG, PK, BD, CN | Local equivalents |

---

## Data Flow Summary

```
Dummy Data → Sqoop Ingest → HDFS Raw Zone
                              │
                              ▼
                         Hive ODS (raw staging, 750+ tables)
                              │
                              ▼
                         Hive CDM (unified schema, all 15 countries)
                              │
                    ┌─────────┴──────────┐
                    ▼                    ▼
             Spark Job 1          Spark Job 2
          Entity Resolution    Txn Aggregation
                    │                    │
                    └─────────┬──────────┘
                              ▼
                         Spark Job 3
                      Feature Engineering
                         (200+ features)
                              │
                              ▼
                         Spark Job 4
                      Sanctions Screening
                              │
                    ┌─────────┴──────────┐
                    ▼                    ▼
              Risk Scoring          Rules Engine
           CRS / TRS / NRS      CTR / STR / SAR
                    │                    │
                    └─────────┬──────────┘
                              ▼
                       Alert Generation
                   regulatory_filing_queue.csv
                              │
                    ┌─────────┴──────────┐
                    ▼                    ▼
            Case Management      Lucid Search
             (analyst queue)   (Elasticsearch API)
```

---

*All data used in this implementation is synthetic.*
*No real customer, transaction, or personally identifiable information is included.*
*Built as a portfolio demonstration of the SCB AML platform architecture.*
