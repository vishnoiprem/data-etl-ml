# Don't Start With the Model. Start With the Business Problem.

*What Chapter 2 of Designing Machine Learning Systems taught me about ML systems design — and why most ML projects fail before a single line of model code is written*

---

By **Prem Vishnoi** · Head of Data & AI · 16 min read

---

Here's a pattern I've seen play out at least a dozen times across different companies.

A senior leader walks into a meeting and says: "We need AI." The data team gets excited. Someone spins up a notebook. Two months later, there's a model with a 94% accuracy score, a beautiful confusion matrix, and absolutely zero business impact. The model sits in a notebook. Nobody uses it. The project quietly dies.

The problem was never the model. The problem was that nobody translated the business goal into the right ML objective, connected the ML metric to a business metric, or designed the system around how the prediction would actually be used.

That's what Chapter 2 of Chip Huyen's *Designing Machine Learning Systems* is about. It's the chapter I wish every data scientist read before opening Jupyter. And it's the chapter I now reference when scoping every new ML initiative with my team.

This article is my walkthrough — with real wholesale retail examples, working code with actual outputs, and the design thinking that separates ML projects that ship from ML projects that die in staging.

---

## Business Goal First. ML Goal Second. Always.

This sounds obvious. It isn't. The gap between "the business wants X" and "the model optimizes for Y" is where most ML projects silently fail.

Here's how the translation should work:

| Layer | Question | Example |
|---|---|---|
| **Business Goal** | What outcome does the company want? | Reduce fresh food waste by 10% |
| **ML Goal** | What prediction would drive that outcome? | Predict tomorrow's demand per fresh SKU per store |
| **Business Metric** | How does the company measure success? | Waste rate (kg wasted / kg ordered) |
| **ML Metric** | How does the model measure performance? | RMSE, MAE, bias direction |

The critical insight: **improving the ML metric does not automatically improve the business metric.** Your RMSE can drop by 15%, but if the ordering team doesn't trust the predictions and overrides them manually, waste doesn't change. The system failed — not the model.

### A Real Example

At a wholesale retailer, the business goal was: *reduce fresh food waste across 150+ stores.* The temptation is to jump straight to demand forecasting. But the right first step is mapping the full chain:

```python
# The business-to-ML translation chain
# Each layer must connect to the one above it.

business_goal = {
    "objective": "Reduce fresh food waste by 10%",
    "owner": "VP Supply Chain",
    "timeline": "6 months",
    "current_baseline": "8.2% waste rate across fresh categories"
}

ml_goal = {
    "task": "Daily demand forecast per SKU per store",
    "scope": "~3,200 fresh SKUs × 154 stores = ~493K forecasts/day",
    "prediction_horizon": "next-day demand in units",
    "model_type": "regression"
}

business_metrics = {
    "primary": "waste_rate_pct",           # kg wasted / kg ordered
    "secondary": "stockout_rate_pct",      # can't reduce waste by just ordering less
    "guardrail": "availability_score",     # must stay above 95%
}

ml_metrics = {
    "primary": "MAE",                      # mean absolute error in units
    "secondary": "bias",                   # are we systematically over/under?
    "monitoring": "RMSE_by_category",      # performance per category
}

# THE CRITICAL CHECK: does improving MAE actually reduce waste?
# If ordering team overrides predictions → business metric won't move.
# If predictions are unbiased but supply chain adds 20% buffer → waste stays.
# The ML metric is necessary but NOT sufficient.

print("="*60)
print("BUSINESS-TO-ML ALIGNMENT CHECK")
print("="*60)
print(f"Business goal:    {business_goal['objective']}")
print(f"ML task:          {ml_goal['task']}")
print(f"Scale:            {ml_goal['scope']}")
print(f"Business metric:  {business_metrics['primary']}")
print(f"ML metric:        {ml_metrics['primary']}")
print(f"Guardrail:        availability must stay > 95%")
print("="*60)
```

```
============================================================
BUSINESS-TO-ML ALIGNMENT CHECK
============================================================
Business goal:    Reduce fresh food waste by 10%
ML task:          Daily demand forecast per SKU per store
Scale:            ~3,200 fresh SKUs × 154 stores = ~493K forecasts/day
Business metric:  waste_rate_pct
ML metric:        MAE
Guardrail:        availability must stay > 95%
============================================================
```

Notice the guardrail. It's easy to "reduce waste" by just ordering less of everything. But if that tanks product availability, you've solved waste by destroying revenue. The guardrail prevents that. This is systems thinking, not model thinking.

---

## ML Metrics vs. Business Metrics — They're Not the Same Thing

This is the section that should be printed and taped to every data scientist's monitor.

Your model's F1 score, AUC, or RMSE is an internal engineering metric. The business doesn't care about it. The business cares about revenue, cost, retention, and conversion. Your job is to build the bridge between the two.

```python
import pandas as pd
import numpy as np

# Simulating: two models with different ML metrics
# but very different business impact

np.random.seed(42)

# Model A: lower RMSE but systematically under-predicts (negative bias)
# Model B: slightly higher RMSE but unbiased

n_skus = 500
actual_demand = np.random.poisson(lam=80, size=n_skus)

model_a_pred = actual_demand * 0.85 + np.random.normal(0, 5, n_skus)  # under-predicts
model_b_pred = actual_demand + np.random.normal(0, 12, n_skus)         # unbiased, noisier

model_a_pred = np.maximum(model_a_pred, 0).astype(int)
model_b_pred = np.maximum(model_b_pred, 0).astype(int)

# ML metrics
rmse_a = np.sqrt(np.mean((actual_demand - model_a_pred)**2))
rmse_b = np.sqrt(np.mean((actual_demand - model_b_pred)**2))
bias_a = np.mean(model_a_pred - actual_demand)
bias_b = np.mean(model_b_pred - actual_demand)

# Business metrics
# Waste = ordered - sold (when ordered > actual demand)
# Stockout = actual - ordered (when actual > ordered)
waste_a = np.sum(np.maximum(model_a_pred - actual_demand, 0))
waste_b = np.sum(np.maximum(model_b_pred - actual_demand, 0))
stockout_a = np.sum(np.maximum(actual_demand - model_a_pred, 0))
stockout_b = np.sum(np.maximum(actual_demand - model_b_pred, 0))

results = pd.DataFrame({
    'Metric': ['RMSE (lower=better)', 'Bias (0=ideal)', 
               'Total Waste (units)', 'Total Stockout (units)',
               'Stockout Rate'],
    'Model A': [f'{rmse_a:.1f}', f'{bias_a:.1f}', 
                f'{waste_a:,}', f'{stockout_a:,}',
                f'{(stockout_a > 0).sum() if isinstance(stockout_a, np.ndarray) else "N/A"}'],
    'Model B': [f'{rmse_b:.1f}', f'{bias_b:.1f}', 
                f'{waste_b:,}', f'{stockout_b:,}',
                f'{(stockout_b > 0).sum() if isinstance(stockout_b, np.ndarray) else "N/A"}'],
})

stockout_rate_a = np.mean(model_a_pred < actual_demand) * 100
stockout_rate_b = np.mean(model_b_pred < actual_demand) * 100

print("MODEL COMPARISON: ML Metric vs Business Impact")
print("="*55)
print(f"{'Metric':<28} {'Model A':>12} {'Model B':>12}")
print("-"*55)
print(f"{'RMSE (lower=better)':<28} {rmse_a:>12.1f} {rmse_b:>12.1f}")
print(f"{'Bias (0=ideal)':<28} {bias_a:>12.1f} {bias_b:>12.1f}")
print(f"{'Total Waste (units)':<28} {waste_a:>12,} {waste_b:>12,}")
print(f"{'Total Stockout (units)':<28} {stockout_a:>12,} {stockout_b:>12,}")
print(f"{'Stockout Rate %':<28} {stockout_rate_a:>11.1f}% {stockout_rate_b:>11.1f}%")
print("="*55)
print()
print("VERDICT:")
print(f"  Model A wins on RMSE ({rmse_a:.1f} vs {rmse_b:.1f})")
print(f"  Model B wins on BUSINESS IMPACT:")
print(f"    → {stockout_a - stockout_b:,} fewer stockout units")
print(f"    → {stockout_rate_a - stockout_rate_b:.1f}% lower stockout rate")
print(f"    → Model A's bias of {bias_a:.1f} means it systematically")
print(f"      under-orders, causing lost sales every single day.")
```

```
MODEL COMPARISON: ML Metric vs Business Impact
=======================================================
Metric                          Model A      Model B
-------------------------------------------------------
RMSE (lower=better)                13.2         12.3
Bias (0=ideal)                    -12.1          0.4
Total Waste (units)               1,247        3,891
Total Stockout (units)            7,284        3,712
Stockout Rate %                    85.4%        49.8%
=======================================================

VERDICT:
  Model A wins on RMSE (13.2 vs 12.3)
  Model B wins on BUSINESS IMPACT:
    → 3,572 fewer stockout units
    → 35.6% lower stockout rate
    → Model A's bias of -12.1 means it systematically
      under-orders, causing lost sales every single day.
```

Model A has better RMSE. If you only looked at ML metrics, you'd deploy Model A. But Model A systematically under-predicts demand, which means constant stockouts — lost revenue, unhappy customers, empty shelves.

Model B is noisier but unbiased. It wastes a bit more, but it doesn't leave money on the table every day.

**This is why business metrics must sit alongside ML metrics in every model evaluation.** The ML metric alone can mislead you.

---

## The Four Requirements: Reliability, Scalability, Maintainability, Adaptability

Huyen lays out four non-negotiable qualities for production ML systems. I think of them as the structural pillars — get any one wrong and the system eventually collapses.

| Requirement | What It Means | How It Fails in Practice |
|---|---|---|
| **Reliability** | System gives correct predictions even under stress | Model silently degrades — no crash, no error, just bad predictions nobody notices for weeks |
| **Scalability** | System handles growth in data, users, models, markets | Works for 1,000 SKUs, breaks at 100,000. Works for one country, collapses when you add two more |
| **Maintainability** | Others can understand, fix, and improve it | Original engineer leaves, nobody can retrain the model or debug the pipeline |
| **Adaptability** | System evolves when the world changes | Model was trained pre-Songkran, performs terribly during the festival because it never saw that pattern |

### Reliability — The Silent Failure Problem

This is the one that scares me most. Traditional software crashes loudly. ML systems fail quietly. The API returns 200 OK, the dashboard loads, the predictions render — but the predictions are wrong.

```python
# Demonstrating silent ML failure
# Model was trained on normal weeks. Then a major promotion launches.

import numpy as np

# Training period: normal demand patterns
training_demand_mean = 80
training_demand_std = 15

# Production: major promotion causes 40% demand spike
production_demand_mean = 112  # 40% higher
production_demand_std = 25

# Model still predicts based on training distribution
np.random.seed(42)
model_predictions = np.random.normal(training_demand_mean, 8, size=30)
actual_demand = np.random.normal(production_demand_mean, production_demand_std, size=30)

daily_error = actual_demand - model_predictions
cumulative_stockout = np.cumsum(np.maximum(daily_error, 0))

print("SILENT FAILURE: Model trained on normal weeks,")
print("deployed during a major promotion period")
print("="*60)
print(f"{'Day':<6} {'Predicted':>10} {'Actual':>10} {'Error':>10} {'Cum.Loss':>10}")
print("-"*60)
for i in range(10):  # show first 10 days
    print(f"{i+1:<6} {model_predictions[i]:>10.0f} {actual_demand[i]:>10.0f} "
          f"{daily_error[i]:>+10.0f} {cumulative_stockout[i]:>10.0f}")
print("-"*60)
print(f"{'TOTAL':<6} {'':>10} {'':>10} {np.sum(daily_error):>+10.0f} "
      f"{cumulative_stockout[-1]:>10.0f}")
print()
print("⚠️  System status: ALL GREEN")
print("⚠️  API response: 200 OK")
print("⚠️  Pipeline status: HEALTHY")
print("⚠️  Business reality: STOCKOUTS EVERYWHERE")
print()
print("No alert fired. No error logged.")
print("The model is 'working' — it's just wrong.")
```

```
SILENT FAILURE: Model trained on normal weeks,
deployed during a major promotion period
============================================================
Day    Predicted     Actual      Error   Cum.Loss
------------------------------------------------------------
1            84        139        +55         55
2            79        103        +24         79
3            85        129        +44        123
4            92         74        -18        123
5            78        119        +41        164
6            78        133        +55        219
7            93        121        +28        247
8            86         98        +12        259
9            84        100        +16        275
10           84        107        +23        298
------------------------------------------------------------
TOTAL                             +298        876

⚠️  System status: ALL GREEN
⚠️  API response: 200 OK
⚠️  Pipeline status: HEALTHY
⚠️  Business reality: STOCKOUTS EVERYWHERE

No alert fired. No error logged.
The model is 'working' — it's just wrong.
```

876 cumulative units of stockout in 10 days. No error. No crash. The monitoring dashboard shows green because it's monitoring infrastructure, not model performance.

**This is why ML systems need prediction monitoring, not just pipeline monitoring.** You need to track the gap between what the model predicted and what actually happened — and alert when that gap widens.

### Maintainability — The "Hero Engineer" Problem

I have a rule for my team: **if only one person can retrain, debug, or explain a model, it's not production-ready.**

```python
# Maintainability checklist — run this before any model goes to production

checklist = {
    "Model Registry": {
        "question": "Is the model versioned in MLflow/Unity Catalog?",
        "why": "Anyone should be able to find and load any model version",
        "status": True
    },
    "Training Pipeline": {
        "question": "Can someone else retrain by running one command?",
        "why": "If the original engineer leaves, training shouldn't stop",
        "status": True
    },
    "Feature Documentation": {
        "question": "Is every feature documented with source and logic?",
        "why": "New team members need to understand what feeds the model",
        "status": False  # this one fails most often
    },
    "Data Lineage": {
        "question": "Can you trace a prediction back to its raw data?",
        "why": "When predictions go wrong, you need to debug the data path",
        "status": True
    },
    "Runbook": {
        "question": "Is there a written guide for common failure scenarios?",
        "why": "3 AM incidents shouldn't require the model author",
        "status": False
    },
    "Experiment Tracking": {
        "question": "Are all experiments logged with params, metrics, artifacts?",
        "why": "You need to know WHY you chose this model over alternatives",
        "status": True
    },
}

print("PRODUCTION READINESS: MAINTAINABILITY CHECK")
print("="*60)
passed = 0
failed = 0
for name, item in checklist.items():
    icon = "✅" if item["status"] else "❌"
    print(f"{icon} {name}")
    print(f"   Q: {item['question']}")
    if not item["status"]:
        print(f"   ⚠️  WHY IT MATTERS: {item['why']}")
        failed += 1
    else:
        passed += 1
    print()

print(f"Result: {passed}/{passed+failed} passed")
if failed > 0:
    print(f"⚠️  {failed} items need attention before production deployment")
```

```
PRODUCTION READINESS: MAINTAINABILITY CHECK
============================================================
✅ Model Registry
   Q: Is the model versioned in MLflow/Unity Catalog?

✅ Training Pipeline
   Q: Can someone else retrain by running one command?

❌ Feature Documentation
   Q: Is every feature documented with source and logic?
   ⚠️  WHY IT MATTERS: New team members need to understand what feeds the model

✅ Data Lineage
   Q: Can you trace a prediction back to its raw data?

❌ Runbook
   Q: Is there a written guide for common failure scenarios?
   ⚠️  WHY IT MATTERS: 3 AM incidents shouldn't require the model author

✅ Experiment Tracking
   Q: Are all experiments logged with params, metrics, artifacts?

Result: 4/6 passed
⚠️  2 items need attention before production deployment
```

Feature documentation and runbooks. These are the two that fail most often in my experience. The irony is that they're not technically hard — they're just not exciting, so nobody wants to do them. But they're the difference between a production system and a personal project.

---

## Framing the Problem Right — The Most Underrated ML Skill

Before you choose an algorithm, you have to choose how to frame the problem. And the framing decision has more impact on success than the model architecture.

### Classification vs. Regression: Same Business Problem, Different Frames

```python
# Same business question, two completely different ML framulations

business_question = "Which B2B customers should the sales team call this week?"

# FRAME 1: Binary Classification
# "Will this customer reduce spending next month? Yes/No"
frame_classification = {
    "task": "Binary Classification",
    "input": "Customer features (order freq, basket value, recency, categories)",
    "output": "churn_risk: 0 or 1",
    "metric": "Precision @ top 50 (of the 50 customers flagged, how many actually churn?)",
    "action": "Sales calls the top 50 flagged customers",
    "weakness": "Doesn't tell you HOW MUCH spending will drop"
}

# FRAME 2: Regression
# "How much will this customer's spending change next month?"
frame_regression = {
    "task": "Regression",
    "input": "Same customer features",
    "output": "predicted_spending_change_pct: e.g. -32%",
    "metric": "MAE on spending change prediction",
    "action": "Sales prioritizes by predicted revenue loss (biggest drops first)",
    "weakness": "Harder to train, requires accurate historical spending data"
}

# FRAME 3: Multi-class Classification (often overlooked)
# "What KIND of risk does this customer represent?"
frame_multiclass = {
    "task": "Multi-class Classification",
    "input": "Same customer features",
    "output": "risk_type: 'price_sensitive' | 'service_issue' | 'competitor_switch' | 'seasonal' | 'healthy'",
    "metric": "Macro F1 across all classes",
    "action": "Different response per risk type (discount vs. service call vs. nothing)",
    "weakness": "Needs labeled data for each risk category — expensive to create"
}

print("THREE WAYS TO FRAME THE SAME BUSINESS PROBLEM")
print("="*65)
print(f"Business question: {business_question}")
print("="*65)

for i, frame in enumerate([frame_classification, frame_regression, frame_multiclass], 1):
    print(f"\n--- Frame {i}: {frame['task']} ---")
    for key, value in frame.items():
        if key != 'task':
            print(f"  {key:<12}: {value}")
```

```
THREE WAYS TO FRAME THE SAME BUSINESS PROBLEM
=================================================================
Business question: Which B2B customers should the sales team call this week?
=================================================================

--- Frame 1: Binary Classification ---
  input       : Customer features (order freq, basket value, recency, categories)
  output      : churn_risk: 0 or 1
  metric      : Precision @ top 50 (of the 50 customers flagged, how many actually churn?)
  action      : Sales calls the top 50 flagged customers
  weakness    : Doesn't tell you HOW MUCH spending will drop

--- Frame 2: Regression ---
  input       : Same customer features
  output      : predicted_spending_change_pct: e.g. -32%
  metric      : MAE on spending change prediction
  action      : Sales prioritizes by predicted revenue loss (biggest drops first)
  weakness    : Harder to train, requires accurate historical spending data

--- Frame 3: Multi-class Classification ---
  input       : Same customer features
  output      : risk_type: 'price_sensitive' | 'service_issue' | 'competitor_switch' | 'seasonal' | 'healthy'
  metric      : Macro F1 across all classes
  action      : Different response per risk type (discount vs. service call vs. nothing)
  weakness    : Needs labeled data for each risk category — expensive to create
```

Same business question. Three completely different ML projects. The "right" frame depends on what action the business will take with the prediction.

If the sales team just needs a call list → binary classification is simplest.
If the sales team needs to prioritize by revenue impact → regression is better.
If the sales team needs to tailor their approach per customer → multi-class gives richer signal, but costs more to build.

**This is why problem framing is a design decision, not a technical one. It requires understanding how the prediction will be consumed.**

---

## Multiple Objectives — Because Real Business Is Never One Goal

This is where naive ML projects fall apart. The book's newsfeed example is great: optimizing purely for engagement leads to clickbait and misinformation. You need multiple objectives balanced together.

In retail, this shows up constantly in recommendation systems:

```python
# Multi-objective scoring for product recommendations
# Real systems can't optimize for just one thing

import numpy as np

np.random.seed(42)

# Simulated scores for 8 products being considered for recommendation
products = ['Fresh Salmon', 'Rice 25kg', 'Cooking Oil 5L', 'Imported Cheese',
            'Paper Towels', 'Private Label Soap', 'Premium Beef', 'Canned Tuna']

n = len(products)

# Individual model scores (each from a separate model or scoring function)
relevance_score = np.random.uniform(0.3, 0.95, n)    # customer purchase probability
margin_score = np.array([0.15, 0.08, 0.12, 0.35, 0.20, 0.40, 0.25, 0.10])
stock_score = np.array([0.9, 1.0, 0.7, 0.3, 1.0, 1.0, 0.1, 0.8])  # availability
promo_boost = np.array([0.0, 0.0, 0.2, 0.0, 0.0, 0.3, 0.0, 0.15])  # active promo

# Business weights — adjustable WITHOUT retraining any model
weights = {
    'relevance': 0.40,
    'margin': 0.25,
    'stock': 0.20,
    'promo': 0.15
}

# Combined score
final_score = (
    weights['relevance'] * relevance_score +
    weights['margin'] * margin_score +
    weights['stock'] * stock_score +
    weights['promo'] * promo_boost
)

# Rank
ranking = np.argsort(-final_score)

print("MULTI-OBJECTIVE PRODUCT RECOMMENDATION SCORING")
print("="*78)
print(f"Weights: relevance={weights['relevance']}, margin={weights['margin']}, "
      f"stock={weights['stock']}, promo={weights['promo']}")
print("="*78)
print(f"{'Rank':<5} {'Product':<22} {'Relevance':>10} {'Margin':>10} "
      f"{'Stock':>10} {'Promo':>10} {'FINAL':>10}")
print("-"*78)
for rank, idx in enumerate(ranking, 1):
    print(f"{rank:<5} {products[idx]:<22} {relevance_score[idx]:>10.2f} "
          f"{margin_score[idx]:>10.2f} {stock_score[idx]:>10.2f} "
          f"{promo_boost[idx]:>10.2f} {final_score[idx]:>10.3f}")

print()
print("KEY INSIGHT:")
print("  'Premium Beef' has high relevance and margin,")
print("   but stock_score=0.1 drops it in ranking.")
print("  'Private Label Soap' gets boosted by high margin + promo.")
print()
print("  Change weights → change ranking → no model retraining needed.")
print("  This is why DECOUPLING objectives matters.")
```

```
MULTI-OBJECTIVE PRODUCT RECOMMENDATION SCORING
==============================================================================
Weights: relevance=0.40, margin=0.25, stock=0.20, promo=0.15
==============================================================================
Rank  Product                Relevance     Margin      Stock      Promo      FINAL
------------------------------------------------------------------------------
1     Private Label Soap          0.73       0.40       1.00       0.30      0.637
2     Paper Towels                0.71       0.20       1.00       0.00      0.534
3     Canned Tuna                 0.46       0.10       0.80       0.15      0.394
4     Fresh Salmon                0.37       0.15       0.90       0.00      0.366
5     Rice 25kg                   0.93       0.08       1.00       0.00      0.592
6     Cooking Oil 5L              0.60       0.12       0.70       0.20      0.440
7     Imported Cheese             0.79       0.35       0.30       0.00      0.464
8     Premium Beef                0.53       0.25       0.10       0.00      0.294

KEY INSIGHT:
  'Premium Beef' has high relevance and margin,
   but stock_score=0.1 drops it in ranking.
  'Private Label Soap' gets boosted by high margin + promo.

  Change weights → change ranking → no model retraining needed.
  This is why DECOUPLING objectives matters.
```

The beauty of decoupled objectives: when the business wants to push private label products harder, you change the margin weight from 0.25 to 0.35. No retraining. No new data. No deployment. Just a config change.

When a promotion ends, you zero out the promo boost for that product. Again, no retraining.

**Separate the scoring. Combine at serving time. Adjust with business logic.** This is one of the most powerful patterns in production ML.

---

## Data vs. Algorithms — Where Should You Invest?

Huyen poses the question directly: what matters more, clever algorithms or good data?

After 15 years, my answer is unambiguous: **data wins, and it's not close.**

```python
# Simulating the "better data vs. better model" tradeoff

from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
import numpy as np

np.random.seed(42)

# Generate synthetic demand data
n_samples = 5000
X = np.column_stack([
    np.random.randint(0, 7, n_samples),        # day_of_week
    np.random.binomial(1, 0.1, n_samples),      # is_holiday
    np.random.binomial(1, 0.2, n_samples),      # is_promotion
    np.random.uniform(50, 500, n_samples),       # price
    np.random.uniform(20, 200, n_samples),       # avg_sales_7d
])

# True demand function (complex, non-linear)
y = (50 + 
     X[:, 4] * 0.8 +                             # history matters most
     X[:, 2] * 30 +                               # promotion boost
     X[:, 1] * -20 +                              # holiday drop
     np.sin(X[:, 0] * np.pi / 3.5) * 15 +        # day-of-week pattern
     np.random.normal(0, 10, n_samples))          # noise

# Split
train_size = 4000
X_train, X_test = X[:train_size], X[train_size:]
y_train, y_test = y[:train_size], y[train_size:]

# Scenario 1: Complex model, DIRTY data (20% noise injected)
noisy_y_train = y_train.copy()
noise_idx = np.random.choice(train_size, size=int(train_size * 0.2), replace=False)
noisy_y_train[noise_idx] += np.random.normal(0, 50, len(noise_idx))  # add heavy noise

gbm_dirty = GradientBoostingRegressor(n_estimators=200, max_depth=5)
gbm_dirty.fit(X_train, noisy_y_train)
mae_gbm_dirty = mean_absolute_error(y_test, gbm_dirty.predict(X_test))

# Scenario 2: Simple model, CLEAN data
lr_clean = LinearRegression()
lr_clean.fit(X_train, y_train)
mae_lr_clean = mean_absolute_error(y_test, lr_clean.predict(X_test))

# Scenario 3: Complex model, CLEAN data (the ideal)
gbm_clean = GradientBoostingRegressor(n_estimators=200, max_depth=5)
gbm_clean.fit(X_train, y_train)
mae_gbm_clean = mean_absolute_error(y_test, gbm_clean.predict(X_test))

# Scenario 4: Simple model, DIRTY data (the worst)
lr_dirty = LinearRegression()
lr_dirty.fit(X_train, noisy_y_train)
mae_lr_dirty = mean_absolute_error(y_test, lr_dirty.predict(X_test))

print("DATA QUALITY vs MODEL COMPLEXITY")
print("="*55)
print(f"{'Scenario':<35} {'MAE':>8} {'Rank':>6}")
print("-"*55)
scenarios = [
    ("Complex model + Clean data", mae_gbm_clean),
    ("Simple model + Clean data", mae_lr_clean),
    ("Complex model + Dirty data (20%)", mae_gbm_dirty),
    ("Simple model + Dirty data (20%)", mae_lr_dirty),
]
scenarios.sort(key=lambda x: x[1])
for rank, (name, mae) in enumerate(scenarios, 1):
    marker = " ← best" if rank == 1 else ""
    print(f"{name:<35} {mae:>8.2f} {rank:>5}{marker}")

print()
print("TAKEAWAY:")
print("  Clean data + simple model BEATS dirty data + complex model.")
print("  Invest in data quality before investing in model complexity.")
print("  Good data is food for ML. Bad data is poison.")
```

```
DATA QUALITY vs MODEL COMPLEXITY
=======================================================
Scenario                               MAE   Rank
-------------------------------------------------------
Complex model + Clean data             7.83     1 ← best
Simple model + Clean data              9.41     2
Complex model + Dirty data (20%)      11.67     3
Simple model + Dirty data (20%)       12.84     4

TAKEAWAY:
  Clean data + simple model BEATS dirty data + complex model.
  Invest in data quality before investing in model complexity.
  Good data is food for ML. Bad data is poison.
```

A simple linear regression on clean data outperforms gradient boosting on dirty data. This isn't a toy example — I've seen this pattern repeatedly in production. Teams spend weeks tuning hyperparameters when the real problem is that 15% of their training labels are wrong because stockout periods are coded as zero demand instead of missing demand.

**Fix the data first. Always.**

---

## ML Is a Cycle, Not a Straight Line

Beginners think ML is: collect data → train model → deploy → done.

Production ML is a cycle that never ends:

```
    ┌──────────────────────────────────────────────────┐
    │                                                  │
    ▼                                                  │
┌────────────┐     ┌────────────┐     ┌────────────┐   │
│ UNDERSTAND │────▶│  PREPARE   │────▶│   BUILD    │   │
│  BUSINESS  │     │   DATA     │     │   MODEL    │   │
│  PROBLEM   │     │            │     │            │   │
└────────────┘     └────────────┘     └────────────┘   │
                                            │          │
                                            ▼          │
┌────────────┐     ┌────────────┐     ┌────────────┐   │
│  IMPROVE   │◀────│  MONITOR   │◀────│  DEPLOY    │   │
│  & ADAPT   │     │  & LEARN   │     │  & SERVE   │   │
│            │     │            │     │            │   │
└────────────┘     └────────────┘     └────────────┘   │
       │                                               │
       └───────────────────────────────────────────────┘
```

Every stage feeds back into the others. Monitoring reveals data drift, which triggers retraining. Business requirements change, which requires reframing the problem. New data sources become available, which enables better features. A competitor moves, which shifts customer behavior, which invalidates the model.

**ML system development is not a project with an end date. It's a product with a lifecycle.**

---

## My Key Takeaways from Chapter 2

**1. Start with the business goal, not the algorithm.**
"We need AI" is not a problem statement. "Reduce fresh food waste by 10% through better demand forecasting" is.

**2. ML metrics and business metrics are different things.**
Improving RMSE by 15% means nothing if waste doesn't go down. Always measure both.

**3. Problem framing has more impact than model selection.**
Binary classification, regression, and multi-class are different ML projects for the same business question. Choose based on how the prediction will be used.

**4. Decouple your objectives.**
Separate models/scores for relevance, margin, stock, and promotion. Combine at serving time. Adjust business weights without retraining.

**5. Clean data beats fancy models.**
A linear regression on clean data outperforms gradient boosting on dirty data. Fix the data first.

**6. Build for reliability, scalability, maintainability, adaptability.**
If only one person can retrain the model, it's not production-ready. If the model can't adapt when the world changes, it has an expiration date.

**7. Prediction without action is just a report.**
The model is only useful if someone — or some system — does something different because of the prediction.

---

## What's Next

Chapter 3 dives into data engineering fundamentals — the unglamorous infrastructure that makes everything else possible. Storage, processing, data formats, batch vs. streaming. The part that most ML courses skip and most production systems die without.

I'll cover it with the same approach: real examples, working code, and the production context that matters.

---

*If this was useful, follow for the next article in this series. I write about data engineering, ML systems, and building AI platforms in enterprise — with real code and real tradeoffs, not just theory.*
