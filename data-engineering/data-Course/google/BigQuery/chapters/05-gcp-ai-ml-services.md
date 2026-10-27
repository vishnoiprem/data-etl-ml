# 1.5 — AI & ML Services in GCP

> **Section 1 · Introduction to Google Cloud Platform · Lecture 1.5 · 8:27**

## 🎯 What you will learn

- GCP's AI/ML portfolio and where each service sits
- Vertex AI: training, deployment, and model registry
- Gemini and the Generative AI API
- The data-engineer's role in making AI work: BigQuery as the training-data engine

---

## 🧠 Concept

For a data engineer, AI matters in two ways: **(1)** it is a workload your warehouse must serve, and
**(2)** it is a tool that changes how you prepare data. Both angles run through BigQuery.

### The service map

| Service | What it does | Data engineer relevance |
|---------|--------------|------------------------|
| **Vertex AI** | Unified platform for ML: training, tuning, deployment, registry | Manage training datasets, deploy inference endpoints |
| **Vertex AI Workbench** | Managed Jupyter, feature store, model monitoring | Feature engineering at scale |
| **Vertex AI Model Registry** | Versioned model lifecycle, approvals, aliases | Promotion gates, rollback |
| **Vertex AI Model Garden** | Pre-trained and third-party models | Fine-tune foundation models |
| **Vertex AI Vector Search** | Approximate nearest-neighbour retrieval | RAG over BigQuery data |
| **BigQuery ML** | `CREATE MODEL` — train ML models with SQL | Training inside the warehouse, no pipeline |
| **BigQuery Gemini extensions** | Ask questions of your data in natural language | SQL generation, data discovery |
| **AutoML** | Train without writing model code | Quick baselines |
| **Vision / Speech / NLP / Translation** | Pre-trained media APIs | Enrichment pipelines |
| **Gemma / Gemini APIs** | Foundation models via API | Extraction, summarization, classification |

### The three integration patterns

**Pattern 1 — BigQuery ML.** Train a model with a single SQL statement. No Python, no pipeline, no
model server.

```sql
CREATE OR REPLACE MODEL `YOUR_PROJECT_ID.ml.customer_churn`
OPTIONS (
  MODEL_TYPE = 'LOGISTIC_REGRESSION',
  INPUT_LABEL_COLS = ['churned'],
  DATA_SPLIT_METHOD = 'CUSTOM',
  DATA_SPLIT_EVAL_FRACTION = 0.2,
  INPUT_FEATURE_COLS = ['tenure_months', 'monthly_charge', 'support_tickets'],
  L1_REG = 0.1,
  L2_REG = 0.1
) AS
SELECT
    customer_id,
    tenure_months,
    monthly_charge,
    support_tickets,
    churned
FROM `YOUR_PROJECT_ID.analytics.customers`;
```

💡 **BigQuery ML's real advantage is the `TRANSFORM` clause** — feature engineering happens *inside*
the training query, on the same engine that will serve the data. No extract, no transform, no load.

```sql
CREATE OR REPLACE MODEL `YOUR_PROJECT_ID.ml.churn_advanced`
OPTIONS (
  MODEL_TYPE = 'LOGISTIC_REGRESSION',
  INPUT_LABEL_COLS = ['churned']
) AS
SELECT
    churned,
    tenure_months,
    monthly_charge,
    -- Feature transformation inside BigQuery
    LOG(1 + monthly_charge)                 AS log_charge,
    IF(monthly_charge > AVG(monthly_charge) OVER (), 1, 0) AS above_avg_charge,
    COUNT(*) OVER (PARTITION BY plan_type)  AS plan_cohort_size
FROM `YOUR_PROJECT_ID.analytics.customers`;
```

**Pattern 2 — Vertex AI training on BigQuery tables.** Export the training set, train, register.

```sql
-- Materialize a clean, leakage-free training set
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.ml.training_set`
PARTITION BY DATE(feature_date)
AS
WITH labels AS (
    SELECT customer_id, churned, churn_date
    FROM `YOUR_PROJECT_ID.analytics.churn_events`
),
features AS (
    SELECT
        customer_id,
        feature_date,
        tenure_months,
        monthly_charge,
        support_tickets,
        nps_score
    FROM `YOUR_PROJECT_ID.analytics.customer_features`
)
SELECT
    f.customer_id,
    f.tenure_months,
    f.monthly_charge,
    f.support_tickets,
    f.nps_score,
    IF(l.churned IS NOT NULL, 1, 0) AS churned
FROM features f
LEFT JOIN labels l
    ON f.customer_id = l.customer_id
   AND f.feature_date < l.churn_date   -- prevent label leakage
WHERE f.feature_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 180 DAY);
```

```bash
# Train a custom Vertex AI model with the training set in BigQuery
gcloud ai custom-jobs create \
    --region=us-central1 \
    --display-name=churn-model \
    --worker-pool-spec=machine-type=g2-standard-4,replica-count=1,container-image=us-docker.pkg.dev/vertex-ai/prediction/... \
    --input-data-uri=bigquery://YOUR_PROJECT_ID.ml.training_set
```

**Pattern 3 — Gemini over BigQuery data.** Natural-language data exploration and transformation.

```python
from google.cloud import bigquery
from google import genai

client = bigquery.Client()
gemini = genai.Client()

sql = """
    SELECT plan_type, COUNT(*) AS customers,
           ROUND(AVG(monthly_charge), 2) AS avg_charge
    FROM `YOUR_PROJECT_ID.analytics.customers`
    GROUP BY plan_type
    ORDER BY avg_charge DESC
"""

df = client.query(sql).to_dataframe()

prompt = f"""
Summarize this customer plan summary in three bullets and flag any anomaly
that would concern a data engineer.

{df.to_markdown()}
"""

response = gemini.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
)
print(response.text)
```

---

## 🧠 AI and the Warehouse: Cost Reality

| Workload | Cost profile | Warning |
|----------|--------------|---------|
| BigQuery ML training | Query cost + slot time | Training queries scan data like any other query |
| Vertex AI custom training | GPU/TPU per hour | $100s–$1000s/day if misconfigured |
| Gemini API calls | Per token | Output tokens cost ~5–10× input |
| Vector Search | Storage + query | Index build on large corpora is slow |
| Gemini in BigQuery | Query cost | Free-form SQL can scan entire tables — always dry-run |

⚠️ **The biggest cost risk with AI-generated SQL is unbounded scanning.** A prompt like "show me
all customer trends" can produce a full-table scan of a 50 TB table. Mitigate by:

1. Setting `maximum_bytes_billed` on every AI-assisted query
2. Restricting the AI's view to a materialized view or a partitioned date range
3. Reviewing generated SQL before execution
4. Using `CREATE OR REPLACE VIEW` staging so AI only ever touches a small surface

```python
# Guardrail: hard cap on bytes processed
job_config = bigquery.QueryJobConfig()
job_config.maximum_bytes_billed = 10 * 1024**4   # 10 GB

job = client.query(sql, job_config=job_config)
```

---

## 💡 Production Notes

- **BigQuery ML supports:** `LOGISTIC_REGRESSION`, `LINEAR_REGRESSION`, `KMEANS`, `MATRIX_FACTORIZATION`,
  `KNN`, `TENSORFLOW`, `XGBOOST`, `R_FOREST`, `ARIMA`, `DENSE_FOREST`, `DNN_CLASSIFIER`,
  `DNN_REGRESSOR`. Not every algorithm, but far more than you would guess.
- **Vertex AI Model Registry** gives you versioning, aliases (`production`, `champion`), and approval
  workflows — use it before serving anything.
- **Feature Store** (Vertex AI Feature Store) solves train/serve skew. If features are computed in
  BigQuery for training but by a different path at serving time, you have a skew bug waiting.
- **Gemini via Vertex AI** (not the AI Studio key) if you need VPC-SC, data residency, or audit logs.

---

## 🔑 Key Takeaways

- Vertex AI is the platform; BigQuery ML is the SQL-native shortcut; Gemini is the interface layer.
- **BigQuery ML's `TRANSFORM` clause** is its most underrated feature — feature engineering without
  a separate pipeline.
- Label leakage is the #1 model bug — enforce the label-date boundary in SQL, as shown above.
- AI-generated SQL is a **cost risk**; always cap `maximum_bytes_billed`.
- The data engineer owns the training-data correctness. Models fail on data far more often than
  on architecture.

---

## 📚 Practice Exercises

1. **BigQuery ML.** Write a `CREATE MODEL` statement for a `KMEANS` model that segments customers
   by `tenure_months`, `monthly_charge`, and `avg_session_minutes`. Then write the inference query
   that assigns each customer to a segment.

2. **Leakage audit.** You are building a churn model. Identify the leakage risk in this query and
   rewrite it:

   ```sql
   SELECT c.customer_id, c.monthly_charge, c.tenure, e.churned
   FROM `proj.customers` c
   JOIN `proj.churn_events` e ON c.customer_id = e.customer_id
   ```

3. **Cost guardrail.** A colleague wants to run "find interesting correlations in the events table"
   with Gemini over a 30 TB table. Design the safe version. What would you change?

4. **Model lifecycle.** Outline a promotion process using Vertex AI Model Registry: which stages,
   what metrics, who signs off, how do you roll back?

---

## 📖 Further Reading

- BigQuery ML — https://cloud.google.com/bigquery/docs/introduction-ml
- Vertex AI overview — https://cloud.google.com/vertex-ai/docs/start/introduction-unified-platform
- BigQuery Gemini extensions — https://cloud.google.com/bigquery/docs/gemini-inference
