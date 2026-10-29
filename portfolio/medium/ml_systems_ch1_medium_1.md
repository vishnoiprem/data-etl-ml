# Machine Learning in Production Is a System, Not a Model. Here's What That Actually Means.

*What I learned re-reading Chapter 1 of Chip Huyen's Designing Machine Learning Systems — and why it matters more than any algorithm*

---

By **Prem Vishnoi** · Head of Data & AI · 14 min read

---

I've been building data platforms and ML pipelines for over 15 years. I've shipped models on AWS, Azure, Alibaba Cloud. I've debugged Spark jobs at 3 AM during month-end close. I've watched beautifully trained models die in production because nobody thought about the data pipeline feeding them.

And yet, when I picked up Chip Huyen's *Designing Machine Learning Systems* and read Chapter 1, I found myself nodding at almost every page. Not because it taught me new algorithms — it doesn't cover any. But because it finally put into words something I've been telling my team for years:

**The model is the easy part. The system around it is where you win or lose.**

This article is my take on Chapter 1. I'm not going to just summarize it — I'm going to interleave it with real examples from wholesale retail, working code snippets, and the kind of production headaches that textbooks usually skip. If you're a data engineer, ML engineer, or data leader trying to move from notebooks to production, this is for you.

---

## First — What Is a Machine Learning System, Really?

Most people hear "machine learning" and think about algorithms. Logistic regression. XGBoost. Transformers. That's like hearing "restaurant" and thinking only about the chef. The chef matters, but without the kitchen, the supply chain, the waitstaff, the reservation system, and the health inspector — you don't have a restaurant. You have someone who can cook.

An ML system in production includes:

- The **business problem** that justified the project
- The **data pipelines** that feed it
- The **feature engineering** that transforms raw data into model inputs
- The **model** itself (finally)
- The **serving infrastructure** that delivers predictions
- The **monitoring** that tells you when things break
- The **retraining loop** that keeps it current
- The **people** — data engineers, ML engineers, product managers, business users — who operate and depend on it

If you only focus on the model, you're optimizing maybe 10% of the system.

---

## When Should You Use ML? (And When Should You Not?)

This is the most underrated question in the field. Huyen gives a clean framework, and I'm going to map each criterion to real examples.

### The Checklist

| # | Criterion | Retail Example (Use ML) | Retail Example (Don't Use ML) |
|---|---|---|---|
| 1 | **Patterns exist** | Customer purchasing behavior has seasonality, trends, and basket correlations | A fair dice roll has no pattern — nothing to learn |
| 2 | **Patterns are complex** | Demand depends on day-of-week, weather, promotions, price, competitor activity, holidays — too many variables for a simple rule | Mapping a zip code to a province — just use a lookup table |
| 3 | **Data is available** | 3 years of POS transactions, 10M+ rows per month | A brand-new product category with zero sales history |
| 4 | **Problem is predictive** | "How many units of SKU X will store Y sell tomorrow?" | "What is 7% VAT on this invoice?" — that's arithmetic |
| 5 | **Future resembles the past** | Normal weeks follow similar patterns year-over-year | A once-in-a-decade pandemic changes everything overnight |
| 6 | **Task is repetitive** | Predict demand for 50,000 SKUs across 150 stores daily | One-time decision on whether to enter a new market |
| 7 | **Wrong predictions are tolerable** | Ordering 10% too many bananas = some waste, not a disaster | Wrong dosage in a pharmaceutical recommendation = dangerous |
| 8 | **Problem is at scale** | Millions of transactions per day | One quarterly board presentation |

### A Rule I Give My Team

Before you open a notebook, answer this: **"Can I solve this with a SQL query or a business rule?"**

If the answer is yes, do that. ML adds complexity, cost, and maintenance burden. It should earn its place.

```sql
-- This does NOT need ML.
-- Simple business rule: flag orders above threshold for approval.
SELECT
    order_id,
    customer_id,
    total_amount_thb,
    CASE
        WHEN total_amount_thb > 1000000 THEN 'REQUIRES_APPROVAL'
        ELSE 'AUTO_APPROVED'
    END AS approval_status
FROM orders
WHERE order_date = CURRENT_DATE;
```

But this? This needs ML:

```python
# Demand forecasting: too many interacting variables for a rule.
# Simplified feature set for a single SKU forecast.

import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import TimeSeriesSplit

features = [
    'day_of_week',        # 0=Mon, 6=Sun
    'is_holiday',         # binary
    'is_promotion',       # binary
    'price_thb',          # current selling price
    'avg_sales_last_7d',  # rolling 7-day average
    'avg_sales_last_28d', # rolling 28-day average
    'month',              # seasonality
    'store_tier',         # A/B/C store classification
]

# Target: units sold next day
target = 'units_sold_next_day'

model = GradientBoostingRegressor(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.8
)

# Time-series aware split — never leak future data into training
tscv = TimeSeriesSplit(n_splits=5)
for train_idx, val_idx in tscv.split(df):
    X_train, X_val = df[features].iloc[train_idx], df[features].iloc[val_idx]
    y_train, y_val = df[target].iloc[train_idx], df[target].iloc[val_idx]
    model.fit(X_train, y_train)
    score = model.score(X_val, y_val)
    print(f"Fold R²: {score:.3f}")
```

The difference is clear. One is a lookup. The other is a complex, multi-variable pattern that shifts over time. ML earns its place in the second case.

---

## Research ML vs. Production ML — The Gap Nobody Warns You About

If you learned ML in school or through Kaggle, production will feel like a different discipline. Huyen nails this with five dimensions:

| Dimension | Research | Production |
|---|---|---|
| **Objective** | Beat the benchmark (single metric) | Satisfy 5+ stakeholders with competing goals |
| **Compute** | Fast training, high throughput | Fast inference, low latency (p95 < 200ms) |
| **Data** | Clean, static, labeled, documented | Messy, shifting, biased, partially labeled |
| **Fairness** | "We'll handle it later" | Legal and ethical requirement from day one |
| **Interpretability** | Optional | Business teams won't use what they can't explain |

### The Stakeholder Problem

Here's a scenario I've lived through. We built a customer segmentation model for our B2B wholesale business. Five different teams had five different definitions of success:

- **Data Science** wanted clean, well-separated clusters with high silhouette scores
- **Marketing** wanted segments that mapped to existing campaign logic
- **Commercial** wanted segments tied to margin contribution, not just purchase frequency
- **IT/Platform** wanted something that didn't overload the serving layer during peak hours
- **Management** wanted a dashboard they could show the board

The "best" model from a pure ML perspective — the one with the highest silhouette score — was completely useless to marketing because the segments didn't align with how they plan campaigns. We ended up redesigning the feature set three times before we found something everyone could work with.

That's not an ML problem. That's a systems design problem.

### Latency — Think in Percentiles, Not Averages

Huyen makes a subtle but critical point: latency is a distribution, not a single number.

```python
import numpy as np

# Simulated latencies for 1000 API requests (in milliseconds)
latencies = np.concatenate([
    np.random.normal(loc=95, scale=15, size=970),   # normal requests
    np.random.normal(loc=800, scale=200, size=25),   # slow requests (cold starts)
    np.random.normal(loc=3000, scale=500, size=5),   # timeouts / network issues
])

print(f"Mean latency:   {np.mean(latencies):.0f} ms")  # misleading
print(f"Median (p50):   {np.percentile(latencies, 50):.0f} ms")
print(f"p90:            {np.percentile(latencies, 90):.0f} ms")
print(f"p95:            {np.percentile(latencies, 95):.0f} ms")
print(f"p99:            {np.percentile(latencies, 99):.0f} ms")

# Output (approximate):
# Mean latency:   130 ms    <-- looks fine, hides the tail
# Median (p50):   95 ms     <-- most users are happy
# p90:            115 ms    <-- still OK
# p95:            750 ms    <-- cold starts are hurting
# p99:            2800 ms   <-- something is very wrong for 1% of users
```

That p99 at 2,800ms? In an e-commerce context, that's your highest-value customers — the ones with the biggest carts, the most history, the most data to process. If your system is slowest for your best customers, you have a revenue problem disguised as an infrastructure problem.

In our Databricks Model Serving endpoints, we monitor p95 and p99 specifically. The mean tells you almost nothing useful when debugging production issues.

---

## Production Data Will Humble You

I cannot overstate this. If you've only worked with Kaggle datasets or UCI repositories, production data will be a shock.

### What Clean Data Looks Like (Research)

```python
# Kaggle-style: clean, labeled, ready to go
import pandas as pd
df = pd.read_csv('titanic.csv')
print(df.shape)           # (891, 12)
print(df.isnull().sum())  # maybe 177 nulls in 'Age', that's it
print(df['Survived'].value_counts())  # balanced enough
# You can start modeling in 10 minutes.
```

### What Real Data Looks Like (Production)

```python
# Real wholesale retail data: a typical Monday morning
import pandas as pd

df = pd.read_parquet('daily_sales_raw.parquet')

# Data quality check
print(f"Total rows: {len(df):,}")
print(f"Null customer_id: {df['customer_id'].isnull().sum():,}")
print(f"Negative quantities: {(df['quantity'] < 0).sum():,}")
print(f"Future dates: {(df['transaction_date'] > pd.Timestamp.now()).sum():,}")
print(f"Duplicate order_ids: {df['order_id'].duplicated().sum():,}")

# Typical output:
# Total rows: 12,847,293
# Null customer_id: 34,891        <-- walk-in cash customers, no ID
# Negative quantities: 8,412      <-- returns mixed into sales data
# Future dates: 23                <-- timezone bugs
# Duplicate order_ids: 1,847      <-- retry logic in POS system

# And that's BEFORE you check:
# - Product names that don't match across systems
# - Promotion data that arrived 2 days late
# - Stock levels that are negative (physical count mismatch)
# - Delivery timestamps with gaps and nulls
# - Return reasons that aren't standardized
```

This is real. I deal with variants of this every week. And this is just the raw data layer — before you even think about feature engineering.

Huyen's point is sharp: **if you're spending 80% of your time on data quality and 20% on modeling, you're doing production ML correctly.** Most teams get this ratio inverted.

### A Data Validation Pattern I Use

Before any model training job runs, we validate the input data. If it fails, the pipeline stops — no silent failures, no training on garbage.

```python
# Simple data validation before model training
def validate_training_data(df: pd.DataFrame) -> dict:
    """Run quality checks before training. Fail loud, not silent."""

    checks = {}

    # Row count check — did the pipeline actually load data?
    checks['row_count'] = len(df) > 10000
    
    # Null rate per critical column
    critical_cols = ['customer_id', 'sku_id', 'quantity', 'transaction_date']
    for col in critical_cols:
        null_rate = df[col].isnull().mean()
        checks[f'null_rate_{col}'] = null_rate < 0.05  # max 5% nulls
    
    # No future dates
    checks['no_future_dates'] = (
        df['transaction_date'] <= pd.Timestamp.now()
    ).all()
    
    # Target variable distribution hasn't collapsed
    checks['target_variance'] = df['units_sold'].std() > 0
    
    # Date range is complete (no missing days)
    date_range = pd.date_range(
        df['transaction_date'].min(),
        df['transaction_date'].max()
    )
    actual_dates = df['transaction_date'].dt.date.nunique()
    checks['date_completeness'] = actual_dates / len(date_range) > 0.95

    failed = {k: v for k, v in checks.items() if not v}
    if failed:
        raise ValueError(f"Data validation FAILED: {failed}")
    
    return checks
```

This isn't fancy. It's not a complex ML technique. But it has saved us from training on corrupt data more times than I can count.

---

## Fairness and Interpretability — Not Optional, Not an Afterthought

Huyen doesn't soft-pedal this, and neither will I.

### Fairness

ML models encode the past. If your historical data contains bias — and it almost certainly does — the model will learn it and amplify it at scale. A biased human loan officer might affect a few applicants per day. A biased ML model can reject thousands in seconds.

In a retail context, consider a product recommendation model trained on historical purchase data. If certain customer segments were historically underserved (smaller stores, rural areas, new customers with little history), the model will learn to deprioritize them — not because they're less valuable, but because the training data has less signal for them.

### Interpretability

This is where enterprise ML lives or dies. When a model flags a B2B customer as "high churn risk," the sales team's first question is always: **"Why?"**

If the model can't answer that, no one will act on the prediction.

```python
# Feature importance: making predictions actionable
import shap

explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_val)

# For a single customer flagged as high churn risk
customer_idx = 42
print("Top churn risk drivers for this customer:")
feature_impacts = pd.Series(
    shap_values[customer_idx],
    index=features
).sort_values(key=abs, ascending=False)

print(feature_impacts.head(5))

# Output (example):
# order_frequency_trend_8w    -0.34   ← orders dropping fast
# avg_basket_value_change     -0.22   ← spending less per visit
# days_since_last_order        0.19   ← gap is growing
# category_diversity_change   -0.15   ← buying fewer categories
# payment_delay_trend          0.11   ← paying later than usual
```

Now the sales rep knows: *this customer's order frequency dropped, they're spending less, they haven't ordered in a while, they've narrowed their categories, and they're paying slower.* That's an actionable conversation, not a black-box score.

**The model says "this customer may churn." The explanation says "here's why, and here's what to talk about when you call them."** That second part is what makes ML useful in an enterprise.

---

## ML Systems vs. Traditional Software

Traditional software separates code and data cleanly. You version the code, test the code, deploy the code. Data flows through it, but the code defines the behavior.

ML breaks this model. The system's behavior is defined by code AND data AND learned artifacts (model weights). Change the data, and the behavior changes — even if you didn't touch a single line of code.

| Aspect | Traditional Software | ML System |
|---|---|---|
| **Behavior defined by** | Code (deterministic) | Code + Data + Model weights |
| **What you version** | Source code | Code, data, features, model artifacts, config |
| **What breaks things** | Code bugs | Code bugs + data drift + feature drift + concept drift |
| **Testing** | Unit tests, integration tests | All of the above + data validation + model performance on slices + fairness checks |
| **Debugging** | Stack traces, logs | Logs + feature distributions + prediction distributions + data lineage |
| **Monitoring** | Uptime, error rates, latency | All of the above + model accuracy decay + input drift + output drift |

### The Silent Killer: Data Drift

This is the scenario that catches most teams off guard. Your model is running fine. No errors. No alerts. Latency is normal. But performance is slowly degrading because the input data distribution has shifted.

```python
# Monitoring for data drift — compare training vs. production distributions
from scipy import stats

def detect_drift(
    training_data: pd.Series,
    production_data: pd.Series,
    threshold: float = 0.05
) -> dict:
    """
    KS test: are these two distributions significantly different?
    If p-value < threshold, the distribution has shifted.
    """
    statistic, p_value = stats.ks_2samp(training_data, production_data)
    
    return {
        'feature': training_data.name,
        'ks_statistic': round(statistic, 4),
        'p_value': round(p_value, 4),
        'drift_detected': p_value < threshold,
        'training_mean': round(training_data.mean(), 2),
        'production_mean': round(production_data.mean(), 2),
    }

# Check each feature
for feature in features:
    result = detect_drift(
        X_train[feature],
        X_production[feature]
    )
    if result['drift_detected']:
        print(f"⚠️  DRIFT: {result}")

# Example output:
# ⚠️  DRIFT: {'feature': 'avg_basket_value', 'ks_statistic': 0.1823,
#             'p_value': 0.0012, 'drift_detected': True,
#             'training_mean': 4520.0, 'production_mean': 3870.0}
#
# Translation: average basket value has dropped significantly since
# the model was trained. The model's predictions may be stale.
# Trigger retraining or investigate why.
```

In retail, this happens all the time. A new competitor opens nearby. A key supplier changes pricing. A holiday period ends. Government policy changes. The code didn't change, the pipeline didn't break, but the world moved and the model didn't.

**This is why production ML needs monitoring. Not just infrastructure monitoring — model performance monitoring.**

---

## Putting It All Together: The Full ML System

Here's how I think about the end-to-end system for a production ML use case like customer churn prediction:

```
┌─────────────────────────────────────────────────────────────────┐
│                     ML SYSTEM — CHURN PREDICTION                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    ┌──────────────┐    ┌─────────────────┐        │
│  │ RAW DATA │───▶│ FEATURE STORE│───▶│  MODEL TRAINING │        │
│  │          │    │              │    │                 │        │
│  │ • POS    │    │ • order_freq │    │ • GBM / XGB     │        │
│  │ • CRM    │    │ • basket_val │    │ • time-series   │        │
│  │ • Promo  │    │ • recency    │    │   cross-val     │        │
│  │ • Returns│    │ • category   │    │ • hyperparams   │        │
│  │ • Credit │    │   diversity  │    │                 │        │
│  └──────────┘    └──────────────┘    └────────┬────────┘        │
│                                               │                 │
│                                               ▼                 │
│  ┌──────────────┐    ┌──────────┐    ┌────────────────┐         │
│  │  MONITORING  │◀───│ SERVING  │◀───│ MODEL REGISTRY │         │
│  │              │    │          │    │                │         │
│  │ • data drift │    │ • REST   │    │ • versioned    │         │
│  │ • perf decay │    │   API    │    │ • staged       │         │
│  │ • latency    │    │ • batch  │    │ • approved     │         │
│  │ • fairness   │    │ • p95    │    │                │         │
│  └──────┬───────┘    └────┬─────┘    └────────────────┘         │
│         │                 │                                     │
│         │                 ▼                                     │
│         │        ┌────────────────┐                             │
│         │        │ BUSINESS ACTION│                             │
│         │        │                │                             │
│         │        │ • Dashboard    │                             │
│         │        │ • Sales alert  │                             │
│         │        │ • Auto-email   │                             │
│         │        │ • SHAP report  │                             │
│         │        └────────────────┘                             │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────┐                                               │
│  │  RETRAIN     │  ← triggered by drift detection               │
│  │  PIPELINE    │     or scheduled (e.g., monthly)              │
│  └──────────────┘                                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

The model — the part most people think of when they say "machine learning" — is one box in this diagram. Everything else is the system.

---

## My Key Takeaways from Chapter 1

After 15+ years in data and AI, here's how I'd distill this chapter into principles I actually use:

**1. Ask "does this need ML?" before you open a notebook.**
If a SQL query, a business rule, or a lookup table solves the problem — use that. ML adds complexity, cost, and maintenance burden that needs to be justified.

**2. Treat ML as a system, not a model.**
The algorithm is one component. Data pipelines, feature stores, serving infrastructure, monitoring, retraining, and stakeholder alignment are the rest. The system is the product.

**3. Budget 80% of your time for data, 20% for modeling.**
If you're spending more time on model architecture than on data quality, you're optimizing the wrong thing.

**4. Design for latency, not just accuracy.**
A model that's 2% more accurate but 5x slower might be worse for the business. Think in percentiles (p50, p95, p99), not averages.

**5. Build in fairness and explainability from day one.**
Retrofitting these after deployment is expensive and risky. Every prediction should come with a "why."

**6. Monitor for drift, not just uptime.**
Your model can be "up" and still be wrong. Data distributions shift silently. If you're not checking, you won't know until the business impact shows up in revenue.

**7. Align stakeholders before you train.**
The best model is not the most accurate one — it's the one that balances accuracy, speed, cost, and business value across all the teams that depend on it.

---

## What's Next

Chapter 1 sets the frame. The rest of the book goes deep into each component — training data, feature engineering, model development, deployment, monitoring, continual learning, and infrastructure.

I'll be writing about each chapter, with the same approach: real examples, working code, and the production context that textbooks usually skip.

If you're building ML systems in production — or thinking about starting — this book is probably the most practical guide available right now. Not because it teaches you a new algorithm, but because it teaches you everything *around* the algorithm that actually determines whether your ML project succeeds or fails.

---

*If this was useful, follow me for more articles in this series. I write about data engineering, ML systems, and building AI platforms in enterprise — with real code, not just theory.*

## Final Thought

Machine learning in production isn’t about chasing the highest accuracy score. It’s about building a reliable, observable system that delivers consistent business value — even when the data gets messy, the world changes, and stakeholders disagree on what “success” looks like.

The model is just the engine. The system is the car. And in production, nobody cares how fast the engine spins if the brakes don’t work.

---

### 💬 Let’s Talk Production
I’d love to hear from you: **What’s the one ML system failure that taught you the most?** Was it silent data drift? A pipeline that broke at month-end? A model that was “95% accurate” but completely useless in practice? Drop your story in the comments — I read every single one.

---

### 📚 Next in This Series
This was my breakdown of **Chapter 1: Introduction to ML Systems**. Next up:
▶️ **Chapter 2: Training Data & Feature Engineering** — How to build datasets that don’t lie, manage feature stores in production, and avoid the silent killers of data leakage, label inconsistency, and training-serving skew.

[Follow me](your-link) to get notified when it drops. I’m publishing one chapter breakdown per week, complete with real code, wholesale/B2B examples, and production war stories.

---

**Tags:** `Machine Learning` `MLOps` `Data Engineering` `Production ML` `AI Systems`

*Prem Vishnoi is Head of Data & AI, building production ML systems for wholesale retail and B2B commerce. Follow for practical, code-first breakdowns of ML engineering, data platforms, and AI strategy. Connect on [LinkedIn](vishnoiprem) | [GitHub](vishnoiprem)*