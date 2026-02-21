# E-Commerce End-to-End Data Platform

**Production-grade data platform for Shopee/Lazada-style marketplace.**
Full stack: Azure + Databricks + Kafka + Flink + ClickHouse + Power BI + ML.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                                  │
│  MySQL 8.0 (ecommerce_db) — Orders, Users, Products, Inventory      │
└────────────────────┬──────────────────────────────────────────────┘
                     │
         ┌───────────┴────────────────────────────────┐
         │  BATCH (ADF hourly)                         │  CDC REAL-TIME
         │                                              │  (MySQL Binlog)
         ▼                                              ▼
┌─────────────────────────┐              ┌──────────────────────────┐
│  Azure Data Lake Gen2   │              │   Kafka (6 partitions)   │
│  (Delta Lake format)    │              │   ecomm.cdc.orders       │
│                         │              │   ecomm.cdc.inventory    │
│  ┌──── ODS Layer ─────┐ │              │   ecomm.cdc.user_events  │
│  │ Raw ingestion      │ │              └────────────┬─────────────┘
│  │ + CDC watermark    │ │                           │
│  └────────┬───────────┘ │                           ▼
│           │             │              ┌──────────────────────────┐
│  ┌──── CDM Layer ─────┐ │              │   Apache Flink           │
│  │ dim_user           │ │              │   - Windowed GMV agg     │
│  │ dim_product        │ │              │   - Funnel metrics       │
│  │ dim_seller         │ │              │   - Stuck order alerts   │
│  │ fact_orders        │ │              └────────────┬─────────────┘
│  │ fact_order_items   │ │                           │
│  │ fact_inventory     │ │                           ▼
│  │ fact_user_events   │ │              ┌──────────────────────────┐
│  └────────┬───────────┘ │              │   ClickHouse (OLAP)      │
│           │             │              │   rt_order_metrics       │
│  ┌──── ADS Layer ─────┐ │              │   rt_funnel_metrics      │
│  │ ads_daily_gmv      │ │              │   mv_hourly_gmv (MV)     │
│  │ ads_product_perf   │ │              │   v_live_kpi (View)      │
│  │ ads_seller_score   │ │              └────────────┬─────────────┘
│  │ ads_customer_rfm   │ │                           │
│  │ ads_category_trends│ │                           │
│  │ ads_warehouse_eff  │ │              ┌─────────────┴────────────┐
│  └────────┬───────────┘ │              │                          │
└───────────┼─────────────┘              │                          │
            │                            │                          │
    ┌───────┴──────┐         ┌───────────┴──────┐      ┌───────────┴──────┐
    │  Power BI    │         │  In-House BI      │      │  Real-Time       │
    │  Dashboard   │         │  (FastAPI+React)  │      │  Dashboard       │
    │  (batch KPIs)│         │  - REST API       │      │  (Grafana)       │
    └──────────────┘         │  - WebSocket live │      └──────────────────┘
                             └─────────┬─────────┘
                                       │
                             ┌─────────┴─────────┐
                             │  ML Module         │
                             │  - Demand Forecast │
                             │  - Reorder Optim.  │
                             │  - Transfer Optim. │
                             └───────────────────┘
```

---

## Project Structure

```
e-commerce-end-2end/
│
├── source_mysql/                    # SOURCE LAYER
│   ├── schemas/
│   │   └── 01_create_database.sql   # Full MySQL schema (16 tables)
│   ├── dummy_data/
│   │   └── 02_seed_data.py          # Generates 500 users, 2000 orders, 10K events
│   └── stored_procedures/
│
├── databricks/                      # BATCH PROCESSING (Delta Lake)
│   ├── ods/
│   │   └── 01_ingest_mysql_to_ods.py  # Incremental MySQL → Delta (MERGE)
│   ├── cdm/
│   │   └── 02_ods_to_cdm.py           # Dimensional model (dims + facts)
│   ├── ads/
│   │   └── 03_cdm_to_ads.py           # Pre-aggregated business tables
│   └── utils/
│
├── realtime_pipeline/               # REAL-TIME PROCESSING
│   ├── kafka/
│   │   ├── producers/
│   │   │   └── mysql_cdc_producer.py  # Binlog → Kafka CDC producer
│   │   ├── consumers/
│   │   └── configs/
│   ├── flink/
│   │   └── jobs/
│   │       └── realtime_order_analytics.py  # Flink streaming jobs
│   └── clickhouse/
│       ├── schemas/
│       │   └── 01_clickhouse_schema.sql     # RT tables + MV + Views
│       └── queries/
│
├── azure/                           # AZURE INFRASTRUCTURE
│   ├── adf_pipelines/
│   │   └── pipeline_mysql_to_databricks.json  # ADF pipeline definition
│   ├── event_hubs/
│   ├── azure_functions/
│   └── arm_templates/
│
├── powerbi/                         # POWER BI
│   ├── measures/
│   │   └── ecommerce_measures.dax   # All DAX measures
│   ├── datasets/
│   └── reports/
│
├── ml/                              # MACHINE LEARNING
│   ├── warehouse_optimization/
│   │   └── models/
│   │       └── warehouse_optimizer.py  # XGBoost + EOQ + LP optimizer
│   └── demand_forecasting/
│
├── bi_product/                      # IN-HOUSE BI PRODUCT
│   ├── backend/
│   │   ├── api/
│   │   │   └── main.py              # FastAPI (REST + WebSocket)
│   │   └── Dockerfile
│   └── frontend/
│       ├── src/pages/
│       │   └── Dashboard.jsx        # React dashboard (Recharts + Tailwind)
│       ├── package.json
│       └── Dockerfile
│
├── docker/
│   └── docker-compose.yml           # Full local stack (10 services)
│
├── monitoring/
│   ├── prometheus/prometheus.yml
│   └── grafana/
│
├── scripts/
│   └── setup/01_local_setup.sh      # One-command local setup
│
├── tests/
│   ├── unit/
│   └── integration/
│
└── requirements.txt
```

---

## Data Model

### MySQL Source (16 tables)

| Table | Description | Key Columns |
|---|---|---|
| `users` | Buyers & sellers | user_id, user_type, status |
| `sellers` | Shop profiles | seller_id, rating, tier |
| `products` | Product catalog (SPU) | product_id, category_id, min_price |
| `product_skus` | Variants (SKU) | sku_id, attributes, price, stock |
| `categories` | 3-level hierarchy | category_id, parent_id, level |
| `warehouses` | 5 fulfillment centers | warehouse_id, city, capacity |
| `inventory` | Stock per SKU/warehouse | quantity, reorder_point |
| `orders` | Purchase orders | order_id, status, total_amount |
| `order_items` | Line items | item_id, quantity, unit_price |
| `payments` | Payment records | payment_id, gateway, status |
| `shipments` | Logistics tracking | tracking_no, carrier, status |
| `reviews` | Product ratings | rating, content, helpful_count |
| `user_events` | Clickstream | event_type, session_id, device |
| `cart_items` | Shopping cart | user_id, sku_id, quantity |
| `vouchers` | Promo codes | code, type, value, usage_limit |
| `flash_sales` | Time-limited sales | quota, sold_count |

### Databricks Layers

**ODS** — Raw Delta tables, full schema, watermark-based incremental load.

**CDM** — Business entities:

| Table | Type | Description |
|---|---|---|
| `dim_date` | Dimension | Calendar (2022–2027) |
| `dim_user` | Dimension | + RFM metrics, segment |
| `dim_product` | Dimension | + category hierarchy, price tier |
| `dim_seller` | Dimension | + tier (Platinum/Gold/Silver) |
| `fact_orders` | Fact | + commission, fulfillment_days |
| `fact_order_items` | Fact | + gross_margin, margin_pct |
| `fact_inventory_snapshot` | Fact | Daily snapshot, needs_reorder |
| `fact_user_events` | Fact | Session sequence, hour |

**ADS** — Pre-aggregated for dashboards:

| Table | Use Case |
|---|---|
| `ads_daily_gmv` | Executive KPI dashboard |
| `ads_product_performance` | Product management |
| `ads_seller_scorecard` | Seller ops |
| `ads_customer_rfm` | CRM / marketing |
| `ads_category_trends` | Merchandising |
| `ads_warehouse_efficiency` | Operations / ML input |

---

## Real-Time Pipeline

```
MySQL Binlog → python-mysql-replication → Kafka → Flink → ClickHouse
```

| Component | Config |
|---|---|
| MySQL | binlog_format=ROW, binlog_row_image=FULL, GTID enabled |
| Kafka | 6 partitions per topic, Snappy compression, 7-day retention |
| Flink | 4 slots, RocksDB state backend, 60s checkpoints |
| ClickHouse | ReplacingMergeTree + Materialized Views + 90-day TTL |

**Topics:**
- `ecomm.cdc.orders` — order create/update (key=order_id)
- `ecomm.cdc.inventory` — stock changes (key=sku_id)
- `ecomm.cdc.user_events` — clickstream (key=session_id)
- `ecomm.cdc.payments` — payment events (key=order_id)
- `ecomm.cdc.shipments` — logistics updates (key=order_id)

**Flink Jobs:**
- **GMV window (1 min):** order count, GMV, unique buyers by city
- **Funnel window (5 min):** view→cart→purchase rates by platform
- **Alert (stateful):** orders stuck in `pending` > 30 minutes

---

## Machine Learning

### Warehouse Optimizer (`ml/warehouse_optimization/`)

| Model | Algorithm | Output |
|---|---|---|
| Demand Forecasting | XGBoost + lag/calendar features | 30-day demand forecast per SKU/warehouse |
| Reorder Optimizer | EOQ + Safety Stock formula | Optimal ROP, EOQ, priority (Critical→None) |
| Transfer Optimizer | Linear Programming (scipy) | Min-cost allocation: warehouse → city |

**Demand features:** lag-1/3/7/14/28, rolling mean/std/max (7/14/30 days), day-of-week, is_weekend, month, quarter, SKU encoding.

---

## BI Product (In-House Dashboard)

**Backend:** FastAPI + WebSocket
**Frontend:** React + Recharts + Tailwind CSS

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/kpi/summary` | Overall KPIs |
| GET | `/api/v1/gmv/daily` | GMV trend (batch) |
| GET | `/api/v1/gmv/realtime` | Live GMV from ClickHouse |
| GET | `/api/v1/products/top` | Top products |
| GET | `/api/v1/sellers/scorecard` | Seller ranking |
| GET | `/api/v1/customers/rfm` | RFM segments |
| GET | `/api/v1/categories/trends` | Category trends |
| GET | `/api/v1/warehouse/status` | Warehouse health |
| GET | `/api/v1/funnel` | Conversion funnel |
| WS | `/ws/live-orders` | Real-time order stream |

### Dashboard Tabs
- **Overview** — KPI cards, 30-day GMV trend, live order ticker
- **Products** — Top 10 revenue, conversion funnel
- **Customers** — RFM pie chart, segment table
- **Operations** — Warehouse cards (utilization, stockouts, delivery)

---

## Power BI

Connect Power BI Desktop to **Databricks SQL** or **Azure Synapse** pointing at the ADS layer.

**Pre-built measures** (`powerbi/measures/ecommerce_measures.dax`):
- GMV Total / MTD / YTD / WoW% / MoM%
- Completion Rate, Cancellation Rate, AOV
- Platform Revenue, Gross Margin %
- Unique Buyers, Repeat Purchase Rate, Customer LTV
- Stockout Rate, Reorder SKU count
- Seller GMV concentration (top-5)

---

## Azure Stack

| Service | Purpose |
|---|---|
| Azure Data Lake Storage Gen2 | Delta Lake storage (ODS/CDM/ADS) |
| Azure Data Factory | Hourly orchestration pipeline |
| Azure Databricks | Spark compute for ODS→CDM→ADS |
| Azure Event Hubs (Kafka API) | Managed Kafka for CDC events |
| Azure Key Vault | Secrets management |
| Azure Monitor | Alerts + logging |

---

## Quick Start

### Prerequisites
- Docker Desktop
- Python 3.11+
- Node.js 20+

### Run locally

```bash
# Clone & navigate
cd e-commerce-end-2end

# One-command setup (MySQL + Kafka + ClickHouse + seed data)
chmod +x scripts/setup/01_local_setup.sh
./scripts/setup/01_local_setup.sh

# Start all services
docker compose -f docker/docker-compose.yml up -d

# Start CDC producer (in new terminal)
source .venv/bin/activate
python realtime_pipeline/kafka/producers/mysql_cdc_producer.py

# Start BI API (in new terminal)
uvicorn bi_product.backend.api.main:app --host 0.0.0.0 --port 8000 --reload

# Start frontend (in new terminal)
cd bi_product/frontend
npm install && npm start
```

### Run ML demo

```bash
source .venv/bin/activate
python ml/warehouse_optimization/models/warehouse_optimizer.py
```

### Service URLs

| Service | URL | Credentials |
|---|---|---|
| BI Dashboard | http://localhost:3000 | — |
| BI API Docs | http://localhost:8000/api/docs | — |
| Kafka UI | http://localhost:8080 | — |
| Flink UI | http://localhost:8081 | — |
| ClickHouse | http://localhost:8123 | default / clickhouse123 |
| Grafana | http://localhost:3001 | admin / admin123 |
| MySQL | localhost:3306 | root / ecommerce123 |

---

## Data Flow Summary

```
[MySQL] ──(ADF hourly)──► [ADLS ODS Delta] ──► [CDM Delta] ──► [ADS Delta]
                                                                      │
                                                        ┌─────────────┼──────────────┐
                                                        ▼             ▼              ▼
                                                   [Power BI]   [BI Product]   [Databricks ML]
                                                  (batch KPIs)  (REST+WS API)  (forecasting)

[MySQL Binlog] ──► [Kafka CDC] ──► [Flink jobs] ──► [ClickHouse] ──► [Grafana RT]
                                                                  └──► [BI API /realtime]
```

---

## Dummy Data Summary

| Entity | Count |
|---|---|
| Users | 500 |
| Sellers / Shops | 50 |
| Products | 200 |
| SKUs | ~600 |
| Warehouses | 5 (Bangkok ×2, Chiang Mai, Phuket, Khon Kaen) |
| Inventory records | ~3,000 |
| Orders | 2,000 |
| Order items | ~6,000 |
| Payments | ~1,400 |
| Shipments | ~1,200 |
| Reviews | ~800 |
| User events (clickstream) | 10,000 |
| Vouchers | 7 |
