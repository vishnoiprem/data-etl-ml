# How to Crack the ST Logistics Senior Manager — Data, Analytics & AI Interview

*A brutally practical guide. 15 real questions, working code, flow diagrams, memory cheat-sheets, and a 30-day study plan. If someone reads this end-to-end, they pass.*

---

## Decode the Job First

Before we touch a single question, let's X-ray what ST Logistics actually wants. Every sentence in that JD maps to a specific interview signal.

**The Hidden Profile:** They don't want a pure data scientist. They don't want a pure engineer. They want a **unicorn** — someone who can build a data pipeline at 9 AM, train a computer vision model at noon, present ROI to the C-suite at 3 PM, and debug a Databricks cluster at 5 PM. In a logistics company. In Singapore.

**The "T-Shape" Decoded:**

```
BROAD (the horizontal bar)
├── Full-stack engineering (APIs, frontend awareness)
├── Cloud architecture (Azure, Databricks, Fabric)
├── CI/CD, containerization, version control
├── Stakeholder communication & data storytelling
├── Leadership, team management, hiring
└── Data governance & ethics

DEEP (the vertical bar)
└── Data Analytics & AI/ML
    ├── Computer vision models
    ├── Forecasting models
    ├── Route optimisation algorithms
    ├── Real-time + batch data pipelines
    └── Model deployment & scaling
```

---

## Which Tech to Focus First — The Priority Stack

This is critical. You can't master everything in the JD. Here's the **80/20 priority order** based on what will come up in interviews and what you'll use on day one:

```
PRIORITY STACK — Study in This Order
═════════════════════════════════════

🔴 TIER 1: "Ask about these in every round" (Study first, 60% of prep time)
──────────────────────────────────────────────────────────────────────────────
 1. SQL (Advanced)         — Window functions, CTEs, query optimization
                             They WILL give you a live SQL test.
 2. Python + Pandas        — Data manipulation, feature engineering, scripting
 3. PySpark / Spark        — Distributed data processing. ST Logistics = big data.
 4. Azure Ecosystem        — ADF, ADLS Gen2, Synapse, Azure ML, Key Vault
 5. Databricks + Fabric    — Unity Catalog, Delta Lake, Medallion architecture

🟡 TIER 2: "Deep-dive in Round 2-3" (Study second, 25% of prep time)
──────────────────────────────────────────────────────────────────────
 6. ML/AI Frameworks       — PyTorch > TensorFlow (for this role)
                             Computer vision (YOLO, ResNet)
                             Time series forecasting (Prophet, ARIMA, LSTM)
 7. MLOps & Deployment     — Docker, CI/CD (Azure DevOps), MLflow
 8. API Development        — FastAPI / Flask for model serving
 9. Data Governance        — Lineage, PII handling, PDPA compliance (Singapore!)

🟢 TIER 3: "Mention to impress, don't need to demo" (15% of prep time)
──────────────────────────────────────────────────────────────────────
10. Hugging Face & OpenAI  — Transformers, RAG patterns, prompt engineering
11. Route Optimisation     — OR-Tools, genetic algorithms, VRP solvers
12. Full-stack basics      — React awareness, REST conventions
13. Real-time streaming    — Kafka, Event Hubs, Structured Streaming
```

**Memory trick:** Think of it as **"SQL → Python → Spark → Cloud → ML → Deploy"** — the data lifecycle itself.

---

## Interview Structure (Expected)

| Round | Panel | Focus | Duration |
|-------|-------|-------|----------|
| **R1** | HR + Hiring Manager | Culture fit, leadership, motivation | 45 min |
| **R2** | Technical Lead / Data Team | Hands-on coding, SQL, architecture | 90 min |
| **R3** | VP / Director Level | System design, business value, strategy | 60 min |
| **R4** | C-suite (CTO/COO) | Vision, ROI storytelling, transformation | 45 min |

---

## ROUND 1: Leadership & Culture Fit

---

### Q1: "ST Logistics is a supply chain company, not a tech company. Why do you want to work here?"

**Why they ask:** They've been burned by data people who join, find it "not sexy enough," and leave in 6 months. They want commitment signals.

**The Answer:**

> "That's exactly why I'm interested. The biggest AI impact today isn't happening at tech companies — it's happening when you bring AI into industries that have real physical constraints. Logistics is a **constraint-rich, data-rich** environment, which means every model you build has an immediate, measurable impact on real operations."

> "At a tech company, improving a recommendation engine by 2% might be a nice metric. At ST Logistics, optimizing delivery routes by 2% could mean **hundreds of thousands of dollars saved per year** and lower carbon emissions. I want my work to have that kind of tangible impact."

> "Also — and I'll be direct — transforming a traditional company's data capabilities is the hardest thing you can do in data. If I can build a data culture here and prove ROI with AI, that's a career-defining achievement."

**Flow of a great answer:**

```
┌───────────────────────────────────┐
│  1. FLIP THE NARRATIVE            │
│  "Not a tech company" = feature,  │
│   not a bug                       │
└───────────────┬───────────────────┘
                │
                ▼
┌───────────────────────────────────┐
│  2. SHOW DOMAIN AWARENESS         │
│  Mention logistics-specific       │
│  use cases (route opt, CV for     │
│  warehouse, demand forecasting)   │
└───────────────┬───────────────────┘
                │
                ▼
┌───────────────────────────────────┐
│  3. CONNECT TO CAREER AMBITION    │
│  "Building data culture from      │
│   scratch = leadership story"     │
└───────────────────────────────────┘
```

---

### Q2: "Tell me about a time you had to convince the C-suite to invest in a data/AI initiative they were skeptical about."

**Why they ask:** The JD says "comfortable interfacing with C-suite" and "facilitate stakeholder buy-in." This is your proof.

**The Answer (STAR Framework):**

```
SITUATION
─────────
"At my previous company, the operations team was manually
 forecasting inventory demand using spreadsheets. Accuracy
 was ~60%. Leadership didn't see why they needed ML — the
 current process 'worked fine.'"

TASK
────
"I needed to secure $150K budget for a forecasting platform
 on Azure + Databricks, plus one additional data engineer hire."

ACTION — The 3-Meeting Strategy
────────────────────────────────
Meeting 1: "The Pain"
  └─ Showed the cost of bad forecasts:
     $2.3M in excess inventory last year
     12% stockout rate → lost revenue

Meeting 2: "The Proof"
  └─ Built a quick 2-week POC:
     - Pulled 6 months of historical data
     - Trained Prophet + XGBoost ensemble
     - Showed 82% accuracy vs 60% baseline
     - Translated: "This saves $800K/year"

Meeting 3: "The Roadmap"
  └─ Presented phased plan:
     Phase 1 (3mo): Core forecasting model
     Phase 2 (6mo): Real-time dashboard
     Phase 3 (12mo): Auto-replenishment integration

RESULT
──────
"Secured full budget. Model deployed in 4 months. First-year
 savings were $920K — above the original $800K estimate.
 That project became the template for every subsequent AI
 initiative in the company."
```

**Key signals to hit:** Quantify everything. Use dollar amounts. Show a phased approach (they know you won't burn budget).

---

### Q3: "How do you manage team morale when you're under-resourced and the C-suite expects results yesterday?"

**Why they ask:** The JD literally says "managing team morale" and "serve as data engineer, software engineer, cloud engineer, and AI scientist all-in-one." This team is probably small and overworked.

**The Answer:**

> "Three principles I follow:"

```
MORALE MANAGEMENT FRAMEWORK
════════════════════════════

1. PROTECT THE TEAM'S TIME
   ┌─────────────────────────────────────────┐
   │ I am the shield between the C-suite     │
   │ and my team. Every ad-hoc request goes  │
   │ through me. I negotiate scope & timeline │
   │ before it hits my engineers.             │
   └─────────────────────────────────────────┘

2. MAKE WINS VISIBLE
   ┌─────────────────────────────────────────┐
   │ Weekly "Demo Friday" — 15 minutes where │
   │ someone shows what they built. I invite  │
   │ stakeholders. My team gets the credit,   │
   │ not me. Recognition > pizza parties.     │
   └─────────────────────────────────────────┘

3. INVEST IN GROWTH
   ┌─────────────────────────────────────────┐
   │ Each team member gets 4 hrs/week for    │
   │ learning (certification prep, side      │
   │ projects). It's not optional — I protect│
   │ that time like production uptime.        │
   └─────────────────────────────────────────┘
```

> "When we're truly under-resourced, I'm not too proud to roll up my sleeves. If I need to write a Spark job at midnight to hit a deadline so my team can go home, I do it. But I also document why it happened and present a staffing case with data — 'We shipped X projects with Y people; here's what we'll need for next quarter.'"

---

## ROUND 2: Technical Deep-Dive

---

### Q4: "Write a SQL query to find the top 3 warehouses by average delivery delay, excluding weekends, for the last 90 days."

**Why they ask:** SQL is the #1 skill in this JD. They will 100% give you a live SQL problem. This tests window functions, date logic, and filtering.

**The Answer:**

```sql
-- ST Logistics: Warehouse delivery performance analysis
-- Assumes tables: deliveries(id, warehouse_id, scheduled_date, actual_date, status)
--                 warehouses(id, name, region)

WITH delivery_delays AS (
    SELECT
        d.warehouse_id,
        w.name AS warehouse_name,
        d.id AS delivery_id,
        d.scheduled_date,
        d.actual_date,
        -- Calculate delay in business days (exclude weekends)
        (
            DATEDIFF(day, d.scheduled_date, d.actual_date)
            - 2 * DATEDIFF(week, d.scheduled_date, d.actual_date)
            - CASE WHEN DATEPART(weekday, d.scheduled_date) = 1 THEN 1 ELSE 0 END
            - CASE WHEN DATEPART(weekday, d.actual_date) = 7 THEN 1 ELSE 0 END
        ) AS business_day_delay
    FROM deliveries d
    JOIN warehouses w ON d.warehouse_id = w.id
    WHERE d.actual_date >= DATEADD(day, -90, GETDATE())
      AND d.status = 'COMPLETED'
      AND d.actual_date > d.scheduled_date  -- only late deliveries
),

warehouse_stats AS (
    SELECT
        warehouse_id,
        warehouse_name,
        COUNT(*) AS late_deliveries,
        AVG(CAST(business_day_delay AS FLOAT)) AS avg_delay_days,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY business_day_delay)
            OVER (PARTITION BY warehouse_id) AS p95_delay,
        RANK() OVER (ORDER BY AVG(CAST(business_day_delay AS FLOAT)) DESC) AS delay_rank
    FROM delivery_delays
    GROUP BY warehouse_id, warehouse_name
)

SELECT
    warehouse_name,
    late_deliveries,
    ROUND(avg_delay_days, 2) AS avg_delay_days,
    ROUND(p95_delay, 2) AS p95_delay_days
FROM warehouse_stats
WHERE delay_rank <= 3
ORDER BY avg_delay_days DESC;
```

**What to explain while writing:**

```
YOUR NARRATION FLOW
═══════════════════

Step 1: "I'll use CTEs for readability — production code should be self-documenting."
Step 2: "Business days matter in logistics — I'm excluding weekends from the delay calc."
Step 3: "I'm adding P95 alongside average — averages hide outliers, and in logistics,
         outliers are where the real problems are."
Step 4: "RANK() not ROW_NUMBER() — if two warehouses tie, I want both in my top 3."
```

---

### Q5: "Design a data pipeline that ingests shipment tracking events in real-time and updates a dashboard within 5 minutes."

**Why they ask:** "Develop and maintain robust data pipelines that support both real-time and batch processing" — this is a core daily task.

**Architecture Flow:**

```
REAL-TIME SHIPMENT TRACKING PIPELINE
═════════════════════════════════════

┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│  IoT Devices │     │  Partner     │     │  Manual Scans    │
│  (GPS,       │     │  APIs        │     │  (Warehouse      │
│   sensors)   │     │  (carriers)  │     │   barcode)       │
└──────┬───────┘     └──────┬───────┘     └────────┬─────────┘
       │                    │                      │
       └────────────┬───────┘──────────────────────┘
                    │
                    ▼
       ┌────────────────────────┐
       │   Azure Event Hubs     │   ← Ingestion layer
       │   (Kafka-compatible)   │     Partitioned by region
       │   Throughput: 1M       │
       │   events/min           │
       └────────────┬───────────┘
                    │
          ┌─────────┴─────────┐
          │                   │
          ▼                   ▼
  ┌───────────────┐   ┌───────────────────┐
  │  HOT PATH     │   │  COLD PATH        │
  │  (Real-time)  │   │  (Batch)          │
  │               │   │                   │
  │  Spark        │   │  ADF Pipeline     │
  │  Structured   │   │  → ADLS Gen2      │
  │  Streaming    │   │  → Delta Lake     │
  │  (Databricks) │   │  (Bronze/Silver/  │
  │               │   │   Gold layers)    │
  │  Micro-batch: │   │                   │
  │  30-second    │   │  Daily aggregates │
  │  windows      │   │  for reporting    │
  └───────┬───────┘   └───────┬───────────┘
          │                   │
          ▼                   ▼
  ┌───────────────┐   ┌───────────────────┐
  │  Gold Layer   │   │  Gold Layer       │
  │  (Streaming)  │   │  (Batch)          │
  │               │   │                   │
  │  Live status  │   │  Historical KPIs  │
  │  per shipment │   │  Trend analysis   │
  └───────┬───────┘   └───────┬───────────┘
          │                   │
          └─────────┬─────────┘
                    │
                    ▼
       ┌────────────────────────┐
       │   Power BI / Fabric    │   ← Dashboard layer
       │   DirectLake mode      │     Auto-refresh < 5 min
       │                        │
       │   • Live shipment map  │
       │   • Delay alerts       │
       │   • Warehouse KPIs     │
       └────────────────────────┘
```

**Code Prototype — Spark Structured Streaming Job:**

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, window, count, avg, max as spark_max,
    current_timestamp, expr, when
)
from pyspark.sql.types import (
    StructType, StructField, StringType, TimestampType,
    DoubleType, IntegerType
)

# Schema for incoming shipment events
shipment_schema = StructType([
    StructField("shipment_id", StringType()),
    StructField("event_type", StringType()),       # PICKED_UP, IN_TRANSIT, DELIVERED, DELAYED
    StructField("warehouse_id", StringType()),
    StructField("timestamp", TimestampType()),
    StructField("latitude", DoubleType()),
    StructField("longitude", DoubleType()),
    StructField("carrier_id", StringType()),
])

spark = SparkSession.builder \
    .appName("STLogistics_ShipmentTracking") \
    .config("spark.sql.streaming.checkpointLocation", "/mnt/checkpoints/shipments") \
    .getOrCreate()

# Read from Event Hubs (Kafka-compatible)
raw_stream = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "st-logistics-eh.servicebus.windows.net:9093")
    .option("subscribe", "shipment-events")
    .option("startingOffsets", "latest")
    .option("kafka.security.protocol", "SASL_SSL")
    .load()
)

# Parse and transform
parsed = (
    raw_stream
    .select(from_json(col("value").cast("string"), shipment_schema).alias("data"))
    .select("data.*")
    .withColumn("ingestion_time", current_timestamp())
    .withColumn("is_delayed", when(col("event_type") == "DELAYED", 1).otherwise(0))
)

# Aggregate: 5-minute tumbling windows per warehouse
warehouse_metrics = (
    parsed
    .withWatermark("timestamp", "10 minutes")
    .groupBy(
        window(col("timestamp"), "5 minutes"),
        col("warehouse_id")
    )
    .agg(
        count("*").alias("total_events"),
        count(when(col("event_type") == "DELIVERED", 1)).alias("deliveries"),
        count(when(col("event_type") == "DELAYED", 1)).alias("delays"),
        avg("is_delayed").alias("delay_rate"),
    )
)

# Write to Delta Lake Gold layer
(
    warehouse_metrics.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", "/mnt/checkpoints/warehouse_metrics")
    .toTable("gold.shipment_warehouse_metrics")
)
```

**Key talking points:**
- **Medallion architecture** (Bronze → Silver → Gold) because that's what Databricks/Fabric teams expect
- **Watermark of 10 minutes** handles late-arriving events from unreliable IoT/GPS devices
- **Delta Lake** for ACID transactions — logistics data cannot have duplicates
- **DirectLake mode** in Power BI for sub-5-minute dashboard refresh without import scheduling

---

### Q6: "Explain how you'd build a computer vision model for warehouse package damage detection."

**Why they ask:** "Computer vision models" is explicitly listed. At ST Logistics, this is a real use case — they handle physical goods.

**The Answer:**

```
PACKAGE DAMAGE DETECTION — End-to-End Pipeline
═══════════════════════════════════════════════

PHASE 1: DATA COLLECTION (Weeks 1-3)
─────────────────────────────────────
  Warehouse cameras    ──►  Image capture at:
  (fixed mount)              • Receiving dock
                             • Sorting belt
                             • Loading bay
       │
       ▼
  Label Studio (annotation)
  Classes: [INTACT, DENTED, TORN, CRUSHED, WET_DAMAGE]
  Target: 5,000+ labeled images (1,000 per class minimum)
       │
       ▼
PHASE 2: MODEL DEVELOPMENT (Weeks 4-6)
──────────────────────────────────────
  Approach: Transfer learning
  Base model: YOLOv8 (object detection + classification)
  Why YOLO: Real-time inference needed on conveyor belt
       │
       ├── Data augmentation: rotation, brightness, blur
       │   (simulate warehouse lighting conditions)
       │
       ├── Train/Val/Test split: 70/15/15
       │   Stratified by damage class
       │
       └── Metrics: mAP@0.5, Precision, Recall per class
            Target: mAP > 0.85
       │
       ▼
PHASE 3: DEPLOYMENT (Weeks 7-9)
───────────────────────────────
  Option A: Edge (NVIDIA Jetson at each dock)
    ├── Pros: Low latency (<100ms), works offline
    └── Cons: Hardware cost, model update complexity

  Option B: Cloud (Azure ML endpoint)
    ├── Pros: Centralized, easy to update
    └── Cons: Requires stable network, higher latency

  Recommended: Edge with cloud sync
    Camera → Jetson (real-time inference) → Alert
                 │
                 └──► Azure Blob (batch upload images)
                       └──► Retrain pipeline (monthly)
       │
       ▼
PHASE 4: BUSINESS INTEGRATION
─────────────────────────────
  Damage detected → Auto-flag in WMS (Warehouse Management System)
                  → Photo evidence attached to shipment record
                  → Carrier liability report generated
                  → Dashboard: Damage rate per carrier, dock, shift
```

**Code Prototype — Model Training with PyTorch:**

```python
import torch
import torch.nn as nn
from torchvision import models, transforms
from torch.utils.data import DataLoader, Dataset
from pathlib import Path
from PIL import Image

# Custom dataset for warehouse damage images
class DamageDataset(Dataset):
    CLASSES = ["INTACT", "DENTED", "TORN", "CRUSHED", "WET_DAMAGE"]

    def __init__(self, root_dir: str, split: str = "train"):
        self.root = Path(root_dir) / split
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip() if split == "train" else transforms.Lambda(lambda x: x),
            transforms.ColorJitter(brightness=0.3, contrast=0.3),  # warehouse lighting variation
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])
        self.samples = []
        for cls_idx, cls_name in enumerate(self.CLASSES):
            cls_dir = self.root / cls_name
            if cls_dir.exists():
                for img_path in cls_dir.glob("*.jpg"):
                    self.samples.append((img_path, cls_idx))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        image = Image.open(img_path).convert("RGB")
        return self.transform(image), label


# Model: ResNet50 with custom head for damage classification
def build_damage_classifier(num_classes: int = 5, pretrained: bool = True):
    model = models.resnet50(pretrained=pretrained)
    # Freeze early layers (transfer learning)
    for param in list(model.parameters())[:-20]:
        param.requires_grad = False
    # Replace final layer
    model.fc = nn.Sequential(
        nn.Dropout(0.3),
        nn.Linear(model.fc.in_features, 256),
        nn.ReLU(),
        nn.Dropout(0.2),
        nn.Linear(256, num_classes),
    )
    return model


# Training loop
def train_model(model, train_loader, val_loader, epochs=15, lr=1e-4):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_val_acc = 0.0
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        # Validation
        model.eval()
        correct, total = 0, 0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                _, predicted = torch.max(outputs, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()

        val_acc = correct / total
        scheduler.step()

        print(f"Epoch {epoch+1}/{epochs} | Loss: {train_loss/len(train_loader):.4f} | Val Acc: {val_acc:.4f}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), "best_damage_model.pth")

    return model

# Usage
model = build_damage_classifier()
train_ds = DamageDataset("/data/warehouse_damage", split="train")
val_ds = DamageDataset("/data/warehouse_damage", split="val")
train_loader = DataLoader(train_ds, batch_size=32, shuffle=True, num_workers=4)
val_loader = DataLoader(val_ds, batch_size=32, shuffle=False, num_workers=4)
trained_model = train_model(model, train_loader, val_loader)
```

---

### Q7: "How would you build a demand forecasting model for a logistics company?"

**Why they ask:** "Forecasting models" is in the JD. This is the highest-ROI AI use case in logistics.

**The Answer:**

```
DEMAND FORECASTING — Architecture
═════════════════════════════════

DATA SOURCES
────────────
  Historical orders (3+ years)
  Seasonal patterns (holidays, monsoons, Chinese New Year)
  Macroeconomic indicators (GDP, PMI)
  Promotional calendars
  Weather data (Singapore + APAC)
        │
        ▼
FEATURE ENGINEERING
───────────────────
  ┌──────────────────────────────────────────────┐
  │  Lag features:    demand_t-1, t-7, t-30      │
  │  Rolling stats:   7-day avg, 30-day std      │
  │  Calendar:        day_of_week, is_holiday,   │
  │                   days_to_chinese_new_year    │
  │  External:        weather_temp, rainfall_mm  │
  │  Categorical:     product_category, region,  │
  │                   warehouse_id (encoded)      │
  └──────────────────────────────────────────────┘
        │
        ▼
MODEL ENSEMBLE
──────────────
  ┌─────────────────────────────────────────────┐
  │                                             │
  │   Model 1: Prophet (captures seasonality)   │
  │   Model 2: XGBoost (captures non-linear)    │
  │   Model 3: LSTM    (captures sequences)     │
  │                                             │
  │   Ensemble: Weighted average                │
  │   Weights tuned on validation set           │
  │   Prophet: 0.3 | XGBoost: 0.5 | LSTM: 0.2  │
  │                                             │
  └─────────────────┬───────────────────────────┘
                    │
                    ▼
  EVALUATION & DEPLOYMENT
  ───────────────────────
  Metrics: MAPE, RMSE, Bias (over/under-forecast)
  Target: MAPE < 15%
  Deploy: Databricks scheduled job (daily reforecast)
  Monitor: Drift detection on prediction error distribution
```

**Code Prototype — Quick Forecasting Pipeline:**

```python
import pandas as pd
import numpy as np
from prophet import Prophet
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_percentage_error
from sklearn.model_selection import TimeSeriesSplit

def build_forecast_pipeline(df: pd.DataFrame, target_col: str = "demand",
                            date_col: str = "date", horizon: int = 30):
    """
    Ensemble forecasting: Prophet + XGBoost
    df must have columns: date, demand, + any features
    """
    df = df.sort_values(date_col).copy()
    df[date_col] = pd.to_datetime(df[date_col])

    # Feature engineering
    df["day_of_week"] = df[date_col].dt.dayofweek
    df["month"] = df[date_col].dt.month
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["lag_7"] = df[target_col].shift(7)
    df["lag_30"] = df[target_col].shift(30)
    df["rolling_7_mean"] = df[target_col].rolling(7).mean()
    df["rolling_30_std"] = df[target_col].rolling(30).std()
    df = df.dropna()

    # Train/test split (last 'horizon' days = test)
    train = df.iloc[:-horizon]
    test = df.iloc[-horizon:]

    # Model 1: Prophet
    prophet_df = train[[date_col, target_col]].rename(columns={date_col: "ds", target_col: "y"})
    prophet_model = Prophet(yearly_seasonality=True, weekly_seasonality=True)
    prophet_model.fit(prophet_df)
    future = prophet_model.make_future_dataframe(periods=horizon)
    prophet_pred = prophet_model.predict(future).tail(horizon)["yhat"].values

    # Model 2: XGBoost
    feature_cols = ["day_of_week", "month", "is_weekend", "lag_7", "lag_30",
                    "rolling_7_mean", "rolling_30_std"]
    xgb_model = XGBRegressor(n_estimators=200, max_depth=6, learning_rate=0.05)
    xgb_model.fit(train[feature_cols], train[target_col])
    xgb_pred = xgb_model.predict(test[feature_cols])

    # Ensemble (weighted average)
    ensemble_pred = 0.4 * prophet_pred + 0.6 * xgb_pred

    # Evaluate
    actual = test[target_col].values
    results = {
        "prophet_mape": mean_absolute_percentage_error(actual, prophet_pred),
        "xgboost_mape": mean_absolute_percentage_error(actual, xgb_pred),
        "ensemble_mape": mean_absolute_percentage_error(actual, ensemble_pred),
        "predictions": pd.DataFrame({
            "date": test[date_col].values,
            "actual": actual,
            "prophet": prophet_pred,
            "xgboost": xgb_pred,
            "ensemble": ensemble_pred,
        })
    }
    return results

# Usage
# results = build_forecast_pipeline(shipment_data, target_col="daily_volume")
# print(f"Ensemble MAPE: {results['ensemble_mape']:.2%}")
```

---

### Q8: "You discover the data feeding your production model has a PII leak — customer phone numbers are in a field that should be anonymized. What do you do?"

**Why they ask:** "Data ethics and governance" and "data quality champion" are explicit requirements. Singapore's PDPA makes this a legal issue, not just a best-practice issue.

**The Answer:**

```
INCIDENT RESPONSE FLOW — PII LEAK
══════════════════════════════════

HOUR 0: CONTAIN
───────────────
  ┌──────────────────────────────────────────────────┐
  │  1. STOP the pipeline feeding that field          │
  │     (pause ADF trigger / Databricks job)          │
  │                                                  │
  │  2. IDENTIFY blast radius:                        │
  │     - Which tables have this field?               │
  │     - Which dashboards/reports expose it?          │
  │     - Which downstream systems consumed it?        │
  │     - How long has the leak been active?           │
  │                                                  │
  │  3. REVOKE access to affected tables temporarily  │
  └──────────────────────────────────────────────────┘
        │
        ▼
HOUR 1-4: NOTIFY
────────────────
  ┌──────────────────────────────────────────────────┐
  │  4. Notify DPO (Data Protection Officer)          │
  │  5. Notify IT Security                            │
  │  6. Under PDPA: If breach is "significant",       │
  │     must notify PDPC within 3 days                │
  │  7. Document everything in incident log           │
  └──────────────────────────────────────────────────┘
        │
        ▼
DAY 1-3: REMEDIATE
──────────────────
  ┌──────────────────────────────────────────────────┐
  │  8. MASK the PII in all affected locations:       │
  │     - Hash phone numbers (SHA-256 + salt)         │
  │     - Overwrite raw data in Bronze layer          │
  │     - Purge from downstream Gold tables           │
  │                                                  │
  │  9. ADD automated PII scanner to pipeline:        │
  │     - Regex patterns for phone, NRIC, email       │
  │     - Run on every ingestion batch                │
  │     - Alert + block if PII detected               │
  │                                                  │
  │ 10. UPDATE data catalog with sensitivity tags     │
  └──────────────────────────────────────────────────┘
        │
        ▼
WEEK 1-2: PREVENT
─────────────────
  ┌──────────────────────────────────────────────────┐
  │ 11. Implement column-level access control         │
  │     (Unity Catalog / Purview)                     │
  │ 12. Add data quality checks to CI/CD pipeline     │
  │ 13. Conduct team training on PII handling          │
  │ 14. Schedule quarterly data governance audits      │
  └──────────────────────────────────────────────────┘
```

**Code Prototype — Automated PII Scanner:**

```python
import re
from dataclasses import dataclass

@dataclass
class PIIDetector:
    """
    Scan DataFrame columns for PII patterns.
    Singapore-specific: NRIC, phone numbers, postal codes.
    """
    patterns = {
        "sg_phone": r"(\+65|65)?[\s-]?[689]\d{7}",
        "sg_nric": r"[STFGM]\d{7}[A-Z]",
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
        "sg_postal": r"\b\d{6}\b",  # May have false positives — validate context
    }

    def scan_dataframe(self, df, sample_size: int = 1000) -> dict:
        """Scan a pandas DataFrame for PII. Returns dict of {column: [pii_types]}."""
        findings = {}
        sample = df.sample(min(sample_size, len(df)))

        for col in sample.select_dtypes(include=["object"]).columns:
            col_findings = []
            col_text = " ".join(sample[col].dropna().astype(str))

            for pii_type, pattern in self.patterns.items():
                matches = re.findall(pattern, col_text)
                if len(matches) > 2:  # threshold: >2 matches = likely PII column
                    col_findings.append({
                        "type": pii_type,
                        "match_count": len(matches),
                        "severity": "HIGH" if pii_type in ["sg_nric", "credit_card"] else "MEDIUM",
                    })

            if col_findings:
                findings[col] = col_findings

        return findings

    def generate_alert(self, findings: dict, table_name: str) -> str:
        if not findings:
            return f"CLEAR: No PII detected in {table_name}"

        alert_lines = [f"PII ALERT: {table_name}"]
        for col, detections in findings.items():
            for d in detections:
                alert_lines.append(
                    f"  [{d['severity']}] Column '{col}': {d['type']} ({d['match_count']} matches)"
                )
        return "\n".join(alert_lines)

# Usage in pipeline
# detector = PIIDetector()
# findings = detector.scan_dataframe(incoming_df)
# if findings:
#     raise PipelineError(detector.generate_alert(findings, "raw_shipments"))
```

---

## ROUND 3: System Design & Business Value

---

### Q9: "Design the end-to-end data architecture for ST Logistics on Azure."

**Why they ask:** This is THE question. They want to see your Medallion architecture, Azure fluency, and how you connect data to business value.

**The Answer:**

```
ST LOGISTICS — DATA PLATFORM ARCHITECTURE
══════════════════════════════════════════

DATA SOURCES
────────────
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│   WMS    │ │   TMS    │ │   ERP    │ │   IoT    │
│(Warehouse│ │(Transport│ │  (SAP/   │ │  (GPS,   │
│ Mgmt)    │ │  Mgmt)   │ │  Oracle) │ │ sensors) │
└────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
     │            │            │             │
     └────────────┼────────────┼─────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│              INGESTION LAYER                         │
│                                                     │
│  Batch: Azure Data Factory (ADF)                    │
│    • Scheduled pulls from WMS, TMS, ERP             │
│    • Incremental loads via watermark columns         │
│                                                     │
│  Streaming: Azure Event Hubs                         │
│    • Real-time GPS, sensor, scan events              │
│    • Partitioned by warehouse_region                 │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│              STORAGE — MEDALLION ARCHITECTURE         │
│              (ADLS Gen2 + Delta Lake)                │
│                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │   BRONZE    │  │   SILVER    │  │    GOLD     │ │
│  │             │  │             │  │             │ │
│  │ Raw data    │──▶ Cleaned     │──▶ Business    │ │
│  │ as-is       │  │ Deduplicated│  │ aggregates  │ │
│  │ Append-only │  │ Typed       │  │ Star schema │ │
│  │             │  │ Validated   │  │ KPI-ready   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
│                                                     │
│  Governance: Unity Catalog (Databricks)              │
│  + Microsoft Purview for lineage & classification    │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│              COMPUTE LAYER                           │
│                                                     │
│  Databricks Workspace                                │
│  ├── Data Engineering: Spark jobs (Bronze → Gold)    │
│  ├── Data Science: ML model training (PyTorch)       │
│  ├── MLflow: Experiment tracking + model registry    │
│  └── Serving: Model endpoints for inference          │
│                                                     │
│  Azure ML (backup for managed endpoints)             │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│              CONSUMPTION LAYER                       │
│                                                     │
│  Power BI / Fabric                                   │
│  ├── Executive dashboard (daily KPIs)                │
│  ├── Operational dashboard (real-time tracking)      │
│  └── Self-service analytics (managed datasets)       │
│                                                     │
│  APIs (FastAPI on Azure App Service)                 │
│  ├── /predict/demand → Demand forecast endpoint      │
│  ├── /detect/damage → CV model endpoint              │
│  └── /optimize/route → Route optimization endpoint   │
└─────────────────────────────────────────────────────┘
```

**Key design decisions to explain:**
- **Delta Lake everywhere** — ACID transactions prevent data corruption when pipelines fail mid-write (critical for logistics where you can't afford duplicate shipments)
- **Unity Catalog** — centralized governance. Every table has an owner, every column has a sensitivity tag
- **Separate streaming and batch paths** — GPS data needs real-time; ERP/SAP data is daily batch. Don't force both through the same pipeline.
- **FastAPI for model serving** — lightweight, async, easy to containerize. The ops team can call `/predict/demand?warehouse_id=SG-01&horizon=30` from any system.

---

### Q10: "The COO asks you: 'We spent $500K on the data platform. Show me the ROI.' How do you answer?"

**Why they ask:** "Translate model performance into clear business value (ROI, cost, efficiency, revenue)" — this is literally in the JD.

**The Answer:**

```
ROI FRAMEWORK — DATA PLATFORM VALUE
════════════════════════════════════

COST SIDE: $500K Investment Breakdown
─────────────────────────────────────
  Azure infrastructure     $180K/yr
  Databricks licenses      $120K/yr
  Team (3 FTEs)            $150K/yr (incremental)
  Training & tooling       $ 50K

VALUE SIDE: Measured Impact
───────────────────────────

┌──────────────────────────┬──────────┬──────────────────────────────┐
│ USE CASE                 │ ANNUAL   │ HOW MEASURED                  │
│                          │ VALUE    │                              │
├──────────────────────────┼──────────┼──────────────────────────────┤
│ Demand forecasting       │ $320K    │ 40% reduction in excess      │
│ (inventory optimization) │          │ inventory carrying costs      │
├──────────────────────────┼──────────┼──────────────────────────────┤
│ Route optimization       │ $180K    │ 12% reduction in fuel &      │
│                          │          │ driver overtime costs         │
├──────────────────────────┼──────────┼──────────────────────────────┤
│ Damage detection (CV)    │ $95K     │ 60% faster claims processing │
│                          │          │ + reduced carrier disputes   │
├──────────────────────────┼──────────┼──────────────────────────────┤
│ Automated reporting      │ $75K     │ 200 analyst-hours/month      │
│ (replaced manual Excel)  │          │ freed for strategic work     │
├──────────────────────────┼──────────┼──────────────────────────────┤
│ Real-time visibility     │ $60K     │ 25% fewer escalation calls   │
│ dashboard                │          │ from clients                 │
├──────────────────────────┼──────────┼──────────────────────────────┤
│ TOTAL ANNUAL VALUE       │ $730K    │                              │
├──────────────────────────┼──────────┼──────────────────────────────┤
│ NET ROI (YEAR 1)         │ $230K    │ 46% return                   │
│ NET ROI (YEAR 2+)        │ $730K+   │ Incremental use cases added  │
└──────────────────────────┴──────────┴──────────────────────────────┘
```

> "I'd present this to the COO as: 'We invested $500K and returned $730K in year one — a 46% ROI. But the real story is that we built the platform. Every additional use case now costs 70% less to deploy because the infrastructure, pipelines, and governance are already in place. Year two ROI will be north of 100%.'"

---

### Q11: "Write an API endpoint that serves a demand forecast and explain your deployment strategy."

**Why they ask:** "Interfacing (via API) between the data layer and application layer" is in the JD. They want to see full-stack awareness.

**Code Prototype — FastAPI Model Serving:**

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import date, timedelta
import joblib
import pandas as pd
from functools import lru_cache

app = FastAPI(title="ST Logistics - Demand Forecast API", version="1.0.0")

# Pydantic models for request/response
class ForecastRequest(BaseModel):
    warehouse_id: str = Field(..., example="SG-JURONG-01")
    product_category: str = Field(..., example="electronics")
    horizon_days: int = Field(default=14, ge=1, le=90)

class ForecastPoint(BaseModel):
    date: date
    predicted_demand: float
    lower_bound: float  # 95% CI
    upper_bound: float

class ForecastResponse(BaseModel):
    warehouse_id: str
    product_category: str
    model_version: str
    forecast: list[ForecastPoint]

# Load model at startup (cached)
@lru_cache(maxsize=1)
def load_model():
    return joblib.load("/models/demand_forecast_v2.pkl")

@app.get("/health")
def health_check():
    return {"status": "healthy", "model_loaded": load_model() is not None}

@app.post("/predict/demand", response_model=ForecastResponse)
def predict_demand(request: ForecastRequest):
    try:
        model = load_model()
        # Generate future dates
        today = date.today()
        future_dates = [today + timedelta(days=i) for i in range(1, request.horizon_days + 1)]

        # Build feature DataFrame
        features = pd.DataFrame({
            "date": future_dates,
            "warehouse_id": request.warehouse_id,
            "product_category": request.product_category,
            "day_of_week": [d.weekday() for d in future_dates],
            "month": [d.month for d in future_dates],
            "is_weekend": [1 if d.weekday() >= 5 else 0 for d in future_dates],
        })

        # Predict
        predictions = model.predict(features)
        std_dev = predictions * 0.15  # Estimated uncertainty

        forecast = [
            ForecastPoint(
                date=d,
                predicted_demand=round(pred, 1),
                lower_bound=round(pred - 1.96 * std, 1),
                upper_bound=round(pred + 1.96 * std, 1),
            )
            for d, pred, std in zip(future_dates, predictions, std_dev)
        ]

        return ForecastResponse(
            warehouse_id=request.warehouse_id,
            product_category=request.product_category,
            model_version="v2.3.1-20250301",
            forecast=forecast,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

# Deployment: Dockerfile
# FROM python:3.11-slim
# COPY requirements.txt .
# RUN pip install -r requirements.txt
# COPY . /app
# WORKDIR /app
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
#
# Deploy to: Azure App Service (Container) or Azure Kubernetes Service
# CI/CD: Azure DevOps pipeline triggers on model registry update
```

---

## ROUND 4: Vision & Transformation

---

### Q12: "How would you implement a data governance framework from scratch at ST Logistics?"

```
DATA GOVERNANCE — Implementation Roadmap
═════════════════════════════════════════

MONTH 1: FOUNDATIONS
────────────────────
  ┌──────────────────────────────────────────────┐
  │  Define Data Ownership                        │
  │  • Every table gets an OWNER (person, not team)│
  │  • Every column gets SENSITIVITY tag:          │
  │    PUBLIC | INTERNAL | CONFIDENTIAL | PII      │
  │                                                │
  │  Register in Unity Catalog + Purview           │
  └──────────────────────────────────────────────┘

MONTH 2-3: AUTOMATION
─────────────────────
  ┌──────────────────────────────────────────────┐
  │  Data Quality Gates (run in every pipeline):   │
  │  • Schema validation (no surprise columns)     │
  │  • Null rate thresholds (<5% for critical)     │
  │  • PII scan (regex + ML-based detection)       │
  │  • Freshness checks (data not stale)           │
  │                                                │
  │  Lineage Tracking:                             │
  │  ADF/Databricks → Purview auto-lineage         │
  │  "Where did this number come from?" = 1 click  │
  └──────────────────────────────────────────────┘

MONTH 4-6: CULTURE
──────────────────
  ┌──────────────────────────────────────────────┐
  │  PDPA Compliance Training (mandatory, all)     │
  │  Data Quality Scorecard (per team, monthly)    │
  │  "Data Office Hours" (weekly, I answer Qs)     │
  │  Self-service data catalog (searchable)        │
  └──────────────────────────────────────────────┘
```

---

### Q13: "Walk me through how you'd integrate an LLM (OpenAI / Hugging Face) into logistics operations."

**Why they ask:** "Hugging Face, OpenAI APIs" are in the requirements. They want to see you apply GenAI to logistics, not just chatbots.

```
LLM USE CASES IN LOGISTICS — Practical Applications
════════════════════════════════════════════════════

USE CASE 1: Intelligent Document Processing
────────────────────────────────────────────
  Incoming: Bills of Lading, Customs forms, PODs (Proof of Delivery)
  Problem: Manual data entry → errors, delays

  Solution:
  ┌──────────┐     ┌──────────────┐     ┌────────────────┐
  │  Scanned │──►  │  Azure Doc   │──►  │  GPT-4 / LLM   │
  │  PDF     │     │  Intelligence│     │  (structured    │
  │          │     │  (OCR)       │     │   extraction)   │
  └──────────┘     └──────────────┘     └───────┬────────┘
                                                │
                   Extract: shipper, consignee, │
                   weight, HS codes, dates      │
                                                ▼
                                        ┌────────────────┐
                                        │  Validate vs   │
                                        │  WMS records   │
                                        │  Auto-populate │
                                        │  system fields │
                                        └────────────────┘

USE CASE 2: Natural Language Data Queries
─────────────────────────────────────────
  Problem: Only 3 people can write SQL. 50 people need data answers.

  Solution: Text-to-SQL agent
  ┌──────────────────────────────────────────────┐
  │  User: "What was our on-time delivery rate    │
  │         for electronics in March?"            │
  │                                               │
  │  LLM Agent:                                   │
  │  1. Maps question → relevant Gold tables      │
  │  2. Generates SQL (with guardrails)           │
  │  3. Runs query on Databricks                  │
  │  4. Returns: "92.3% — up from 88.1% in Feb"  │
  │  5. (Optional) Auto-generates chart           │
  └──────────────────────────────────────────────┘

USE CASE 3: Anomaly Explanation
───────────────────────────────
  Problem: Dashboard shows a spike. No one knows why.

  Solution: LLM-powered root cause analysis
  ┌──────────────────────────────────────────────┐
  │  Alert: "Delay rate at Jurong warehouse       │
  │          spiked to 34% (normally 8%)"         │
  │                                               │
  │  LLM Agent:                                   │
  │  1. Pulls correlated data (weather, volume,   │
  │     staffing, carrier performance)            │
  │  2. Generates narrative explanation:           │
  │     "Delay spike correlates with Carrier X's  │
  │      vehicle shortage (3 trucks unavailable)  │
  │      combined with 15% volume surge from      │
  │      client Y's flash sale."                  │
  └──────────────────────────────────────────────┘
```

**Code Prototype — RAG-based Document Processor:**

```python
from openai import AzureOpenAI
import json

client = AzureOpenAI(
    azure_endpoint="https://st-logistics-openai.openai.azure.com/",
    api_version="2024-06-01",
)

def extract_shipping_document(ocr_text: str) -> dict:
    """
    Extract structured data from shipping documents using GPT-4.
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": """You are a logistics document parser.
Extract the following fields from shipping documents. Return ONLY valid JSON.
Fields: shipper_name, consignee_name, origin, destination, weight_kg,
        number_of_packages, hs_code, shipping_date, carrier_name, 
        special_instructions, document_type (BOL/POD/INVOICE/CUSTOMS)"""},
            {"role": "user", "content": f"Extract data from this document:\n\n{ocr_text}"}
        ],
        temperature=0.1,  # Low temp for factual extraction
        response_format={"type": "json_object"},
    )

    extracted = json.loads(response.choices[0].message.content)

    # Validate critical fields
    required = ["shipper_name", "destination", "weight_kg"]
    missing = [f for f in required if not extracted.get(f)]
    if missing:
        extracted["_validation_warnings"] = f"Missing fields: {missing}"
        extracted["_needs_human_review"] = True
    else:
        extracted["_needs_human_review"] = False

    return extracted
```

---

## ROUND 5: Curveball Questions

---

### Q14: "You join ST Logistics on Day 1. What do you do in your first 90 days?"

```
90-DAY PLAN
═══════════

DAYS 1-30: LISTEN & AUDIT
──────────────────────────
  Week 1:
    • Meet every team member 1-on-1
    • Meet every stakeholder who touches data
    • Map the current tech stack (what's real vs. what's on paper)

  Week 2-3:
    • Audit existing pipelines: What runs? What breaks? What's manual?
    • Assess data quality: Sample 10 key tables, measure completeness
    • Review cloud spend: Are we overpaying? Right-sized clusters?

  Week 4:
    • Document findings in "State of Data" report
    • Identify 3 quick wins (things fixable in <2 weeks)
    • Present findings to leadership (no blame, just facts)

DAYS 31-60: QUICK WINS + FOUNDATION
────────────────────────────────────
    • Execute 3 quick wins (e.g., fix broken pipeline, automate
      a manual report, clean a critical dataset)
    • Set up proper CI/CD for data pipelines (if missing)
    • Implement basic data quality monitoring
    • Start weekly "Data Office Hours" for stakeholders
    • Hire/backfill if team gaps identified

DAYS 61-90: FIRST BIG PROJECT
──────────────────────────────
    • Launch highest-impact AI project (likely demand forecasting)
    • Establish data governance v1 (ownership, catalog, PII rules)
    • Present roadmap to C-suite with ROI projections
    • Set quarterly OKRs for the data team
```

---

### Q15: "What questions do you have for us?"

**Always ask these:**

> 1. "What does the current data stack look like today — and what's the gap between where you are and where you want to be?"

> 2. "How does the C-suite currently consume data? Dashboards, reports, ad-hoc requests?"

> 3. "What's the team composition today, and what's the hiring plan for the next 12 months?"

> 4. "What does success look like for this role in the first year?"

> 5. "Is there an existing data governance policy, or would I be building that from scratch?"

---

## How to Remember All of This — Memory System

This is the section most guides skip. Here's how to actually retain this material.

### The "PALACE" Method — Memory Architecture

Map each interview round to a room in a place you know well (your home):

```
YOUR MEMORY PALACE
══════════════════

🚪 FRONT DOOR = Round 1 (Culture & Leadership)
   Visualize: Your door has the ST Logistics logo as a doorbell
   Trigger: "Why logistics?" → door opens to a warehouse
   Stories: 3 leadership stories pinned to the wall

🍳 KITCHEN = Round 2 (Technical / Coding)
   Visualize: Ingredients = technologies
   Counter: SQL queries written on the cutting board
   Stove: PySpark jobs "cooking" data (Bronze → Silver → Gold)
   Fridge: Cold storage = ADLS Gen2
   Oven: Model training = GPU heating up

🛋️ LIVING ROOM = Round 3 (System Design)
   Visualize: TV showing the architecture diagram
   Bookshelf: Each shelf = a layer (Ingestion, Storage, Compute, Serve)
   Coffee table: ROI calculations spread out like a newspaper

🛏️ BEDROOM = Round 4 (Vision & Strategy)
   Visualize: Dreaming about the future
   Pillow: 90-day plan tucked underneath
   Alarm clock: "Day 1 — what do you do?"
```

### The "5-4-3-2-1" Daily Drill

Every day for 2 weeks before the interview, practice:

```
5 — Write the Medallion architecture from memory (Bronze/Silver/Gold)
4 — Recite 4 logistics AI use cases (forecast, CV, route opt, NLP)
3 — Write 3 SQL patterns (window functions, CTEs, aggregation)
2 — Explain 2 models end-to-end (Prophet + XGBoost, or YOLO + ResNet)
1 — Tell 1 leadership story with numbers
```

### Acronym Cheat Sheets

**DELTA** — What to remember about the data platform:
```
D - Databricks (compute engine)
E - Event Hubs (streaming ingestion)
L - Lake (ADLS Gen2, Delta Lake format)
T - Transformation (Spark, PySpark)
A - APIs (FastAPI for serving)
```

**CRISP** — How to answer any technical question:
```
C - Context: "In a logistics environment..."
R - Requirements: "The key constraints are..."
I - Implementation: "Here's how I'd build it..."
S - Scale: "This handles X volume because..."
P - Production: "To deploy this, I'd..."
```

**PDPA** — Data governance (and the literal law):
```
P - Purpose limitation (collect only what you need)
D - Data protection officer (must have one)
P - Personal data (NRIC, phone = PII in Singapore)
A - Accountability (you must prove compliance)
```

### Flashcard Prompts (Make Anki cards for these)

| Front | Back |
|-------|------|
| What is Medallion architecture? | Bronze (raw) → Silver (cleaned) → Gold (business-ready), stored in Delta Lake on ADLS Gen2 |
| What GPU metric matters most for training? | GPU utilization % — if below 80%, the bottleneck is data I/O, not compute |
| What's the PDPA breach notification window? | 3 calendar days to notify PDPC if "significant" breach |
| What's Unity Catalog? | Databricks centralized governance: table ownership, column-level access, lineage tracking |
| Prophet vs XGBoost for forecasting? | Prophet: captures seasonality automatically. XGBoost: captures non-linear feature relationships. Ensemble both. |
| What's MAPE? | Mean Absolute Percentage Error. Target for demand forecasting: <15% |
| DirectLake mode in Fabric? | Power BI reads directly from Delta Lake — no import/schedule needed, near-real-time |
| Why Delta Lake over Parquet? | ACID transactions, schema enforcement, time travel, merge/upsert support |

---

## The Night Before — Final Checklist

```
□ Laptop charged, demo code ready to screen-share
□ Architecture diagrams printed (or iPad ready)
□ 3 leadership stories rehearsed with numbers
□ 90-day plan on one page
□ ST Logistics annual report skimmed (know their clients, revenue, challenges)
□ Questions for them written down
□ Good night's sleep
```

---

*This role is hard. They want a unicorn. But unicorns are just people who prepared more than everyone else. You've got the guide. Now go earn that offer.*
