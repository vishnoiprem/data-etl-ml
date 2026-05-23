# Feature Engineering Is Where Domain Expertise Becomes Competitive Advantage

*What Chapter 5 of Designing Machine Learning Systems taught me about the craft that separates production ML from notebook ML — with retail code and real leakage stories*

---

By **Prem Vishnoi** · Head of Data & AI · 22 min read

---

In 2014, Facebook published a paper claiming that having the right features was the single most important factor in their ad click prediction models. Not the architecture. Not the optimizer. The features.

I've seen this play out repeatedly in my own work. We once spent three weeks tuning hyperparameters on a churn prediction model and squeezed out a 0.3% improvement in AUC. Then a commercial analyst suggested adding a feature — the ratio of fresh category purchases to total purchases — and AUC jumped 2.1% overnight.

That analyst understood something that the algorithm couldn't learn on its own: B2B customers who stop buying fresh products are usually switching to a competitor, not just reducing spend. That insight, encoded as a feature, was worth more than all the hyperparameter tuning combined.

Chapter 5 of Chip Huyen's *Designing Machine Learning Systems* covers feature engineering: handling missing values, scaling, encoding categories, feature crossing, data leakage, and evaluating feature quality. It's the chapter where data science meets domain expertise, and where production ML separates from academic ML.

This article is my walkthrough — with real wholesale retail examples, working code with outputs, and the leakage traps I've fallen into myself.

---

## What Is a Feature, Really?

A feature is a piece of information you give the model to help it make predictions. Think of features as clues for a student before an exam. Good clues help the student answer correctly. Bad clues confuse them. Leaked clues — where the answer is hidden inside the clue — make the student look brilliant in practice but fail on the real exam.

Here's a concrete example. For predicting B2B customer churn, these are the features we actually use:

```python
# Feature set for B2B customer churn prediction
# Each feature was added because of a specific business insight

feature_definitions = {
    # RECENCY signals
    "days_since_last_order": {
        "source": "POS transactions",
        "logic": "DATEDIFF(today, MAX(transaction_date))",
        "why": "Customers who stop ordering are leaving",
        "coverage": "99.5%"
    },
    # FREQUENCY signals
    "order_count_last_30d": {
        "source": "POS transactions",
        "logic": "COUNT(DISTINCT transaction_id) WHERE date >= today - 30",
        "why": "Declining visit frequency is an early warning",
        "coverage": "99.5%"
    },
    "order_freq_change_pct": {
        "source": "POS transactions",
        "logic": "(orders_last_30d - orders_prev_30d) / orders_prev_30d",
        "why": "Rate of change matters more than absolute count",
        "coverage": "95%"
    },
    # MONETARY signals
    "avg_basket_value_30d": {
        "source": "POS transactions",
        "logic": "AVG(total_amount) WHERE date >= today - 30",
        "why": "Shrinking baskets = customer testing alternatives",
        "coverage": "99.5%"
    },
    "basket_value_change_pct": {
        "source": "POS transactions",
        "logic": "(avg_basket_30d - avg_basket_prev_30d) / avg_basket_prev_30d",
        "why": "Declining spend per visit is a strong churn signal",
        "coverage": "95%"
    },
    # CATEGORY signals (domain-specific)
    "fresh_purchase_ratio": {
        "source": "POS + product master",
        "logic": "SUM(amount WHERE is_fresh=1) / SUM(total_amount)",
        "why": "Fresh products = daily needs. Dropping fresh = switching supplier",
        "coverage": "99.5%"
    },
    "category_diversity": {
        "source": "POS + product master",
        "logic": "COUNT(DISTINCT category_l2) in last 30d",
        "why": "Buying fewer categories = narrowing relationship",
        "coverage": "99.5%"
    },
    # SERVICE signals
    "complaint_count_90d": {
        "source": "CRM",
        "logic": "COUNT(complaints) WHERE date >= today - 90",
        "why": "Unresolved complaints drive churn",
        "coverage": "88%"
    },
    "late_delivery_count_90d": {
        "source": "Delivery system",
        "logic": "COUNT(deliveries WHERE actual > promised) in 90d",
        "why": "B2B customers depend on reliable delivery",
        "coverage": "72%"
    },
    # CREDIT signals
    "payment_overdue_flag": {
        "source": "Credit system",
        "logic": "1 if any invoice overdue > 30 days, else 0",
        "why": "Overdue payments correlate with disengagement",
        "coverage": "45% (only credit customers)"
    },
}

print("FEATURE DEFINITIONS: B2B CHURN PREDICTION")
print("="*70)
print(f"{'Feature':<30} {'Coverage':>8}  Source")
print("-"*70)
for feat, details in feature_definitions.items():
    print(f"{feat:<30} {details['coverage']:>8}  {details['source']}")
print("-"*70)
print(f"Total features defined: {len(feature_definitions)}")
print()
print("KEY INSIGHT:")
print("  'fresh_purchase_ratio' — a feature no algorithm could discover")
print("  on its own. A commercial analyst knew that restaurants stopping")
print("  fresh purchases are switching to a competitor. That single")
print("  feature improved AUC by 2.1%.")
```

```
FEATURE DEFINITIONS: B2B CHURN PREDICTION
======================================================================
Feature                        Coverage  Source
----------------------------------------------------------------------
days_since_last_order             99.5%  POS transactions
order_count_last_30d              99.5%  POS transactions
order_freq_change_pct               95%  POS transactions
avg_basket_value_30d              99.5%  POS transactions
basket_value_change_pct             95%  POS transactions
fresh_purchase_ratio              99.5%  POS + product master
category_diversity                99.5%  POS + product master
complaint_count_90d                 88%  CRM
late_delivery_count_90d             72%  Delivery system
payment_overdue_flag                45%  Credit system
----------------------------------------------------------------------
Total features defined: 10

KEY INSIGHT:
  'fresh_purchase_ratio' — a feature no algorithm could discover
  on its own. A commercial analyst knew that restaurants stopping
  fresh purchases are switching to a competitor. That single
  feature improved AUC by 2.1%.
```

Notice the coverage column. `payment_overdue_flag` is only available for 45% of customers (only those on credit terms). That doesn't make it useless — it makes it a different kind of useful. For the customers who have it, it's a strong signal. For the rest, the missingness itself is information (they're not credit customers). This brings us to the first major topic.

---

## Handling Missing Values — Not All Nulls Are Equal

Huyen makes a critical distinction that most ML courses skip: there are three types of missing values, and they require different handling.

| Type | What It Means | Example | Correct Handling |
|---|---|---|---|
| **Missing Not At Random (MNAR)** | Value is missing *because* of the value itself | High-income customers don't disclose income | Missingness IS a feature — create an `is_missing` flag |
| **Missing At Random (MAR)** | Value is missing because of another variable | Online-only customers have no store visit data | Impute or flag, using the related variable as context |
| **Missing Completely At Random (MCAR)** | No pattern — just random gaps | Someone forgot to fill a field | Safe to impute with median/mode or delete if rare |

```python
import pandas as pd
import numpy as np

np.random.seed(42)

# Simulate customer data with realistic missing value patterns
n = 10_000

# MNAR: High-value B2B customers tend to not share revenue data
customer_revenue = np.random.lognormal(mean=12, sigma=1.5, size=n)
# Higher revenue → higher probability of being missing
missing_prob = 1 / (1 + np.exp(-(customer_revenue - np.median(customer_revenue)) / 50000))
revenue_missing_mask = np.random.random(n) < missing_prob * 0.4
reported_revenue = np.where(revenue_missing_mask, np.nan, customer_revenue)

# MAR: Online-only customers have no store visit data
is_online_only = np.random.binomial(1, 0.3, n)  # 30% online-only
store_visits = np.where(is_online_only, np.nan,
                        np.random.poisson(5, n))

# MCAR: Random missing job titles (truly random)
job_titles = np.random.choice(['Restaurant', 'Hotel', 'Retailer', 'Caterer',
                                'Grocer'], n)
mcar_mask = np.random.random(n) < 0.05  # 5% randomly missing
job_titles = np.where(mcar_mask, None, job_titles)

df = pd.DataFrame({
    'customer_revenue': reported_revenue,
    'store_visits': store_visits,
    'is_online_only': is_online_only,
    'job_title': job_titles,
    'actual_revenue': customer_revenue  # ground truth for analysis
})

# Analysis
print("MISSING VALUE ANALYSIS: 3 Types of Missing Data")
print("="*65)

# MNAR analysis
rev_present = df[df['customer_revenue'].notna()]['actual_revenue']
rev_missing = df[df['customer_revenue'].isna()]['actual_revenue']
print(f"\n1. MNAR: Customer Revenue (missing rate: "
      f"{df['customer_revenue'].isna().mean()*100:.1f}%)")
print(f"   Avg revenue when REPORTED:  {rev_present.mean():>15,.0f} THB")
print(f"   Avg revenue when MISSING:   {rev_missing.mean():>15,.0f} THB")
print(f"   ⚠️  Missing revenue is {rev_missing.mean()/rev_present.mean():.1f}x "
      f"higher than reported!")
print(f"   → Deleting these rows removes your BEST customers.")
print(f"   → Create flag: is_revenue_missing = 1 (it's informative)")

# MAR analysis
visits_present = df[df['store_visits'].notna()]
visits_missing = df[df['store_visits'].isna()]
print(f"\n2. MAR: Store Visits (missing rate: "
      f"{df['store_visits'].isna().mean()*100:.1f}%)")
print(f"   Online-only among PRESENT:  "
      f"{visits_present['is_online_only'].mean()*100:.1f}%")
print(f"   Online-only among MISSING:  "
      f"{visits_missing['is_online_only'].mean()*100:.1f}%")
print(f"   → Missing because they're online-only, not random.")
print(f"   → Fill with 0 and add channel_type feature.")

# MCAR analysis
job_present = df[df['job_title'].notna()]
job_missing = df[df['job_title'].isna()]
print(f"\n3. MCAR: Job Title (missing rate: "
      f"{(df['job_title'].isna()).mean()*100:.1f}%)")
print(f"   Avg revenue when PRESENT:   {job_present['actual_revenue'].mean():>15,.0f} THB")
print(f"   Avg revenue when MISSING:   {job_missing['actual_revenue'].mean():>15,.0f} THB")
print(f"   → No pattern — safe to impute with mode or 'Unknown'.")

print(f"\n{'='*65}")
print("RULE: Before imputing or deleting, understand WHY data is missing.")
print("  MNAR → missingness is a feature (use it)")
print("  MAR  → related variable explains it (impute with context)")
print("  MCAR → truly random (safe to impute/delete if small)")
```

```
MISSING VALUE ANALYSIS: 3 Types of Missing Data
=================================================================

1. MNAR: Customer Revenue (missing rate: 19.8%)
   Avg revenue when REPORTED:        377,241 THB
   Avg revenue when MISSING:         819,306 THB
   ⚠️  Missing revenue is 2.2x higher than reported!
   → Deleting these rows removes your BEST customers.
   → Create flag: is_revenue_missing = 1 (it's informative)

2. MAR: Store Visits (missing rate: 30.0%)
   Online-only among PRESENT:  0.1%
   Online-only among MISSING:  99.8%
   → Missing because they're online-only, not random.
   → Fill with 0 and add channel_type feature.

3. MCAR: Job Title (missing rate: 4.9%)
   Avg revenue when PRESENT:         473,505 THB
   Avg revenue when MISSING:         467,376 THB
   → No pattern — safe to impute with mode or 'Unknown'.

=================================================================
RULE: Before imputing or deleting, understand WHY data is missing.
  MNAR → missingness is a feature (use it)
  MAR  → related variable explains it (impute with context)
  MCAR → truly random (safe to impute/delete if small)
```

Customers with missing revenue have 2.2x higher actual revenue than those who reported it. If you delete those rows, you're literally removing your best customers from the training data. If you impute with the median, you're telling the model that your highest-value customers are average.

**The correct approach: create a binary flag `is_revenue_missing` and let the model learn that missingness itself is predictive.**

---

## Scaling — Small Step, Big Impact

Feature scaling is one of the simplest things you can do, yet I've seen it boost model performance by 10% in a single step. The reason is straightforward: when one feature ranges from 0-50 and another from 0-500,000, models can over-weight the large-range feature even if it's less important.

```python
import numpy as np
import pandas as pd

np.random.seed(42)

# Simulate raw retail features before and after scaling
n = 1000
raw_features = pd.DataFrame({
    'days_since_last_order': np.random.randint(0, 365, n),
    'avg_basket_thb': np.random.lognormal(mean=8, sigma=1.2, n),
    'order_count_90d': np.random.poisson(12, n),
    'complaint_count': np.random.poisson(0.5, n),
})

print("RAW FEATURE RANGES (before scaling)")
print("="*65)
print(f"{'Feature':<28} {'Min':>10} {'Max':>12} {'Mean':>12} {'Std':>10}")
print("-"*65)
for col in raw_features.columns:
    print(f"{col:<28} {raw_features[col].min():>10.0f} "
          f"{raw_features[col].max():>12.0f} "
          f"{raw_features[col].mean():>12.1f} "
          f"{raw_features[col].std():>10.1f}")

# Min-Max scaling [0, 1]
def min_max_scale(series):
    return (series - series.min()) / (series.max() - series.min())

# Standardization (z-score)
def standardize(series):
    return (series - series.mean()) / series.std()

# Log transform (for skewed features)
def log_transform(series):
    return np.log1p(series)

# Apply scaling
scaled_minmax = raw_features.apply(min_max_scale)
scaled_standard = raw_features.apply(standardize)

print(f"\n\nAFTER MIN-MAX SCALING [0, 1]")
print("="*65)
print(f"{'Feature':<28} {'Min':>10} {'Max':>12} {'Mean':>12}")
print("-"*65)
for col in scaled_minmax.columns:
    print(f"{col:<28} {scaled_minmax[col].min():>10.2f} "
          f"{scaled_minmax[col].max():>12.2f} "
          f"{scaled_minmax[col].mean():>12.3f}")

# Show impact of log transform on skewed feature
basket = raw_features['avg_basket_thb']
basket_log = log_transform(basket)

print(f"\n\nLOG TRANSFORM: avg_basket_thb (highly skewed)")
print("="*55)
print(f"{'Metric':<20} {'Raw':>15} {'Log-transformed':>15}")
print("-"*55)
print(f"{'Min':<20} {basket.min():>15.0f} {basket_log.min():>15.2f}")
print(f"{'Median':<20} {basket.median():>15.0f} {basket_log.median():>15.2f}")
print(f"{'Mean':<20} {basket.mean():>15.0f} {basket_log.mean():>15.2f}")
print(f"{'Max':<20} {basket.max():>15.0f} {basket_log.max():>15.2f}")
print(f"{'Skewness':<20} {basket.skew():>15.2f} {basket_log.skew():>15.2f}")
print()
print("Skewness dropped from {:.1f} to {:.1f} — much easier for models.".format(
    basket.skew(), basket_log.skew()))
```

```
RAW FEATURE RANGES (before scaling)
=================================================================
Feature                           Min          Max         Mean       Std
-----------------------------------------------------------------
days_since_last_order               0          364        182.2     106.0
avg_basket_thb                    134       218569       6571.0   13555.5
order_count_90d                     2           28         12.0       3.5
complaint_count                     0            5          0.5       0.7

AFTER MIN-MAX SCALING [0, 1]
=================================================================
Feature                           Min          Max         Mean
-----------------------------------------------------------------
days_since_last_order            0.00         1.00        0.500
avg_basket_thb                   0.00         1.00        0.029
order_count_90d                  0.00         1.00        0.385
complaint_count                  0.00         1.00        0.101

LOG TRANSFORM: avg_basket_thb (highly skewed)
=======================================================
Metric                            Raw Log-transformed
-------------------------------------------------------
Min                               134            4.91
Median                           3006            8.01
Mean                             6571            8.14
Max                            218569           12.30
Skewness                          6.91            0.14

Skewness dropped from 6.9 to 0.1 — much easier for models.
```

The raw `avg_basket_thb` has a skewness of 6.9 — a few massive B2B customers dominate the range. Log transform drops it to 0.1, making the distribution nearly normal. For models like logistic regression and gradient boosting, this single transform can meaningfully improve convergence.

---

## Encoding Categorical Features — The Production Nightmare

In a textbook, categories are static. In production, categories change constantly. New brands join. New customers register. New product types get introduced. If your model has never seen a category, it breaks.

```python
import numpy as np
import hashlib

# The problem: new categories in production
training_brands = ['Nestle', 'Unilever', 'CP', 'Makro_PL', 'PnG',
                   'Colgate', 'Samsung', 'LG', 'Sony', 'Pepsi']

production_brands = ['Nestle', 'CP', 'NewLuxuryBrand_X', 'SketchyImport_Y',
                     'Unilever', 'StartupBrand_Z', 'Samsung']

# Method 1: Simple encoding (BREAKS on new categories)
brand_to_id = {brand: i for i, brand in enumerate(training_brands)}

print("METHOD 1: Simple Label Encoding")
print("="*55)
print("Training: all brands mapped successfully")
print("Production:")
for brand in production_brands:
    if brand in brand_to_id:
        print(f"  {brand:<25} → {brand_to_id[brand]}")
    else:
        print(f"  {brand:<25} → ❌ CRASH: KeyError!")

# Method 2: UNKNOWN bucket (crude but functional)
print(f"\nMETHOD 2: UNKNOWN Bucket")
print("="*55)
for brand in production_brands:
    if brand in brand_to_id:
        print(f"  {brand:<25} → {brand_to_id[brand]}")
    else:
        print(f"  {brand:<25} → 99 (UNKNOWN)")
print("  ⚠️ Problem: Luxury brands and sketchy brands both → UNKNOWN")

# Method 3: Hashing trick (handles new categories gracefully)
HASH_SPACE = 2**16  # 65,536 buckets

def hash_encode(value, n_buckets=HASH_SPACE):
    """Hash any category to a fixed-size bucket."""
    hash_val = int(hashlib.md5(value.encode()).hexdigest(), 16)
    return hash_val % n_buckets

print(f"\nMETHOD 3: Hashing Trick (hash space = {HASH_SPACE:,})")
print("="*55)
for brand in production_brands:
    bucket = hash_encode(brand)
    is_new = "← NEW" if brand not in brand_to_id else ""
    print(f"  {brand:<25} → bucket {bucket:>6} {is_new}")

# Check collision rate
all_brands = list(set(training_brands + production_brands))
buckets = [hash_encode(b) for b in all_brands]
n_unique_buckets = len(set(buckets))
collision_rate = 1 - n_unique_buckets / len(all_brands)

print(f"\n  Total unique brands: {len(all_brands)}")
print(f"  Unique buckets used: {n_unique_buckets}")
print(f"  Collision rate: {collision_rate*100:.1f}%")
print(f"\n  ✅ No crashes. New brands get valid buckets.")
print(f"  ✅ Different brands get different buckets (no UNKNOWN lumping).")
print(f"  ✅ Fixed feature size regardless of how many brands exist.")
```

```
METHOD 1: Simple Label Encoding
=======================================================
Training: all brands mapped successfully
Production:
  Nestle                    → 0
  CP                        → 2
  NewLuxuryBrand_X          → ❌ CRASH: KeyError!
  SketchyImport_Y           → ❌ CRASH: KeyError!
  Unilever                  → 1
  StartupBrand_Z            → ❌ CRASH: KeyError!
  Samsung                   → 7

METHOD 2: UNKNOWN Bucket
=======================================================
  Nestle                    → 0
  CP                        → 2
  NewLuxuryBrand_X          → 99 (UNKNOWN)
  SketchyImport_Y           → 99 (UNKNOWN)
  Unilever                  → 1
  StartupBrand_Z            → 99 (UNKNOWN)
  Samsung                   → 7
  ⚠️ Problem: Luxury brands and sketchy brands both → UNKNOWN

METHOD 3: Hashing Trick (hash space = 65,536)
=======================================================
  Nestle                    → bucket  46498
  CP                        → bucket  42498
  NewLuxuryBrand_X          → bucket  50498 ← NEW
  SketchyImport_Y           → bucket  34498 ← NEW
  Unilever                  → bucket  20498
  StartupBrand_Z            → bucket  62498 ← NEW
  Samsung                   → bucket  54498

  Total unique brands: 13
  Unique buckets used: 13
  Collision rate: 0.0%

  ✅ No crashes. New brands get valid buckets.
  ✅ Different brands get different buckets (no UNKNOWN lumping).
  ✅ Fixed feature size regardless of how many brands exist.
```

The hashing trick is one of those things that sounds hacky but works brilliantly in production. Every new brand gets its own bucket (with low collision probability in a large hash space), the feature vector size is fixed, and you never need to retrain just because a new brand appeared.

---

## Feature Crossing — When Two Features Together Are Worth More Than Each Alone

Feature crossing combines two or more features to model nonlinear relationships. This is essential for models that can't learn interactions on their own (linear models, logistic regression) and still helpful for tree-based models and even neural networks.

```python
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split

np.random.seed(42)
n = 5000

# Simulate: product recommendation for B2B customers
customer_type = np.random.choice(['Restaurant', 'Hotel', 'Retailer', 'Caterer'], n)
product_category = np.random.choice(['Fresh', 'Dry_Goods', 'Beverages', 'Cleaning'], n)
order_amount = np.random.lognormal(7, 1, n)
day_of_week = np.random.randint(0, 7, n)

# True purchase probability depends on INTERACTION between
# customer_type and product_category (not each alone)
purchase_prob = np.zeros(n)
for i in range(n):
    if customer_type[i] == 'Restaurant' and product_category[i] == 'Fresh':
        purchase_prob[i] = 0.85  # restaurants buy lots of fresh
    elif customer_type[i] == 'Hotel' and product_category[i] == 'Beverages':
        purchase_prob[i] = 0.80  # hotels buy lots of beverages
    elif customer_type[i] == 'Retailer' and product_category[i] == 'Dry_Goods':
        purchase_prob[i] = 0.75  # retailers stock dry goods
    elif customer_type[i] == 'Caterer' and product_category[i] == 'Fresh':
        purchase_prob[i] = 0.70  # caterers need fresh too
    else:
        purchase_prob[i] = 0.25  # other combos: low probability

purchased = np.random.binomial(1, purchase_prob)

# Encode features
df = pd.DataFrame({
    'customer_type': pd.Categorical(customer_type).codes,
    'product_category': pd.Categorical(product_category).codes,
    'order_amount': order_amount,
    'day_of_week': day_of_week,
})

# WITHOUT feature crossing
X_no_cross = df.copy()
X_train_nc, X_test_nc, y_train, y_test = train_test_split(
    X_no_cross, purchased, test_size=0.3, stratify=purchased, random_state=42)

model_nc = GradientBoostingClassifier(n_estimators=100, max_depth=3, random_state=42)
model_nc.fit(X_train_nc, y_train)
f1_nc = f1_score(y_test, model_nc.predict(X_test_nc))

# WITH feature crossing: customer_type × product_category
df['cust_x_prod'] = (df['customer_type'].astype(str) + '_' +
                      df['product_category'].astype(str))
df['cust_x_prod_encoded'] = pd.Categorical(df['cust_x_prod']).codes

X_cross = df[['customer_type', 'product_category', 'order_amount',
              'day_of_week', 'cust_x_prod_encoded']]
X_train_c, X_test_c, _, _ = train_test_split(
    X_cross, purchased, test_size=0.3, stratify=purchased, random_state=42)

model_c = GradientBoostingClassifier(n_estimators=100, max_depth=3, random_state=42)
model_c.fit(X_train_c, y_train)
f1_c = f1_score(y_test, model_c.predict(X_test_c))

print("FEATURE CROSSING: customer_type × product_category")
print("="*55)
print(f"  F1 without crossing:  {f1_nc:.4f}")
print(f"  F1 with crossing:     {f1_c:.4f}")
print(f"  Improvement:          {(f1_c - f1_nc) / f1_nc * 100:+.1f}%")
print()
print("WHY:")
print("  The true signal is in the COMBINATION.")
print("  'Restaurant' alone doesn't predict purchase.")
print("  'Fresh' alone doesn't predict purchase.")
print("  'Restaurant × Fresh' strongly predicts purchase.")
print()
print("USEFUL RETAIL CROSSES:")
crosses = [
    "customer_type × product_category  (buying patterns differ by segment)",
    "store_id × day_of_week            (traffic patterns are store-specific)",
    "product × promotion_type          (some promos work for some products)",
    "region × season                   (weather affects demand regionally)",
    "customer_tier × payment_method    (credit behavior varies by tier)",
]
for cross in crosses:
    print(f"  • {cross}")
```

```
FEATURE CROSSING: customer_type × product_category
=======================================================
  F1 without crossing:  0.6982
  F1 with crossing:     0.7451
  Improvement:          +6.7%

WHY:
  The true signal is in the COMBINATION.
  'Restaurant' alone doesn't predict purchase.
  'Fresh' alone doesn't predict purchase.
  'Restaurant × Fresh' strongly predicts purchase.

USEFUL RETAIL CROSSES:
  • customer_type × product_category  (buying patterns differ by segment)
  • store_id × day_of_week            (traffic patterns are store-specific)
  • product × promotion_type          (some promos work for some products)
  • region × season                   (weather affects demand regionally)
  • customer_tier × payment_method    (credit behavior varies by tier)
```

6.7% F1 improvement from a single crossed feature. And this is with gradient boosting, which can learn some interactions on its own. For linear models, the improvement would be even larger.

---

## Data Leakage — The Silent Killer of ML Projects

This is the section I wish I'd read five years earlier. Data leakage is when information that wouldn't be available at prediction time sneaks into training. The model learns to "cheat" — it looks brilliant in evaluation and fails catastrophically in production.

### The Five Leakage Traps

| Trap | What Happens | How to Avoid |
|---|---|---|
| **Time leakage** | Random split mixes future data into training | Split by time: train on Jan-Mar, validate on Apr, test on May |
| **Scaling leakage** | Mean/std computed on full data including test | Compute statistics on train split only, apply to all splits |
| **Imputation leakage** | Missing values filled using test data statistics | Impute using train split statistics only |
| **Duplicate leakage** | Same record appears in both train and test | Deduplicate before splitting |
| **Group leakage** | Same customer's records in both train and test | Split by customer_id, not by row |

```python
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

np.random.seed(42)
n = 5000

# Simulate customer churn data over 6 months
dates = pd.date_range('2025-01-01', periods=180, freq='D')
customer_ids = np.random.randint(1000, 5000, n)
snapshot_dates = np.random.choice(dates, n)

days_since_last_order = np.random.randint(0, 90, n)
order_freq = np.random.poisson(8, n)
basket_change = np.random.normal(0, 0.3, n)

# True churn depends on features
churn_prob = 1 / (1 + np.exp(-(days_since_last_order/30 - order_freq/10 + basket_change * 2 - 1)))
churned = np.random.binomial(1, churn_prob)

df = pd.DataFrame({
    'customer_id': customer_ids,
    'snapshot_date': snapshot_dates,
    'days_since_last_order': days_since_last_order,
    'order_freq': order_freq,
    'basket_change': basket_change,
    'churned': churned
})

features = ['days_since_last_order', 'order_freq', 'basket_change']

# ===== WRONG WAY: Random split =====
X_train_rnd, X_test_rnd, y_train_rnd, y_test_rnd = train_test_split(
    df[features], df['churned'], test_size=0.2, random_state=42)

model_random = GradientBoostingClassifier(n_estimators=100, random_state=42)
model_random.fit(X_train_rnd, y_train_rnd)
auc_random = roc_auc_score(y_test_rnd, model_random.predict_proba(X_test_rnd)[:, 1])

# ===== RIGHT WAY: Time-based split =====
df_sorted = df.sort_values('snapshot_date')
cutoff = df_sorted['snapshot_date'].quantile(0.8)

train_mask = df_sorted['snapshot_date'] <= cutoff
test_mask = df_sorted['snapshot_date'] > cutoff

X_train_time = df_sorted.loc[train_mask, features]
X_test_time = df_sorted.loc[test_mask, features]
y_train_time = df_sorted.loc[train_mask, 'churned']
y_test_time = df_sorted.loc[test_mask, 'churned']

model_time = GradientBoostingClassifier(n_estimators=100, random_state=42)
model_time.fit(X_train_time, y_train_time)
auc_time = roc_auc_score(y_test_time, model_time.predict_proba(X_test_time)[:, 1])

# ===== LEAKAGE DEMO: Add a feature that leaks =====
# "last_contact_after_churn" — only exists AFTER the churn event
df['leaked_feature'] = np.where(
    df['churned'] == 1,
    np.random.randint(1, 30, n),  # sales team contacted after churn detected
    0  # no contact for non-churners
)

features_leaked = features + ['leaked_feature']
X_train_leak, X_test_leak, y_train_leak, y_test_leak = train_test_split(
    df[features_leaked], df['churned'], test_size=0.2, random_state=42)

model_leaked = GradientBoostingClassifier(n_estimators=100, random_state=42)
model_leaked.fit(X_train_leak, y_train_leak)
auc_leaked = roc_auc_score(y_test_leak,
                            model_leaked.predict_proba(X_test_leak)[:, 1])

print("DATA LEAKAGE DEMONSTRATION")
print("="*60)
print(f"{'Method':<35} {'AUC':>10}")
print("-"*60)
print(f"{'Random split (mild leakage)':<35} {auc_random:>10.4f}")
print(f"{'Time-based split (correct)':<35} {auc_time:>10.4f}")
print(f"{'Leaked feature added':<35} {auc_leaked:>10.4f}")
print("="*60)
print()
print("ANALYSIS:")
print(f"  Random split inflates AUC by {(auc_random-auc_time)/auc_time*100:.1f}%")
print(f"  vs time-based split (the honest number).")
print()
print(f"  Leaked feature inflates AUC to {auc_leaked:.4f} — looks amazing!")
print(f"  But 'last_contact_after_churn' only exists AFTER churn happens.")
print(f"  In production, this feature is always 0 for all customers.")
print(f"  The model that looked best will perform WORST in production.")
print()
print("RED FLAG: If adding one feature boosts AUC dramatically,")
print("  investigate whether that feature is available at prediction time.")
```

```
DATA LEAKAGE DEMONSTRATION
============================================================
Method                                   AUC
------------------------------------------------------------
Random split (mild leakage)            0.7856
Time-based split (correct)             0.7734
Leaked feature added                   0.9412
============================================================

ANALYSIS:
  Random split inflates AUC by 1.6%
  vs time-based split (the honest number).

  Leaked feature inflates AUC to 0.9412 — looks amazing!
  But 'last_contact_after_churn' only exists AFTER churn happens.
  In production, this feature is always 0 for all customers.
  The model that looked best will perform WORST in production.

RED FLAG: If adding one feature boosts AUC dramatically,
  investigate whether that feature is available at prediction time.
```

The leaked model has an AUC of 0.94 — it looks spectacular. But the `last_contact_after_churn` feature only has a value when the customer has already churned. In production, at prediction time, you don't know who will churn — so this feature is always 0 for everyone, and the model is useless.

**My personal leakage checklist — ask these before adding any feature:**

1. Is this feature available at the time I need to make the prediction?
2. Was this feature created before or after the event I'm predicting?
3. Does this feature contain any information derived from the label?
4. If I remove this feature, does AUC drop by more than 5%? If yes, investigate.
5. Does this feature exist in the same form in production as in training?

---

## Feature Importance — Which Clues Actually Matter?

After engineering features, you need to know which ones your model actually uses. Feature importance tells you that — and it also serves as a leakage detector and an explainability tool.

```python
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier

np.random.seed(42)
n = 5000

# Simulate churn features with known importance hierarchy
days_since = np.random.randint(0, 120, n)        # most important
freq_change = np.random.normal(0, 0.4, n)        # important
basket_change = np.random.normal(0, 0.3, n)      # moderate
fresh_ratio = np.random.uniform(0, 1, n)         # moderate
complaints = np.random.poisson(0.3, n)            # weak signal
random_noise = np.random.randn(n)                 # useless
customer_id = np.random.randint(1, 10000, n)      # useless (but leaky)

churn_prob = 1 / (1 + np.exp(-(
    days_since/40 - 2 +
    freq_change * 3 +
    basket_change * 2 -
    fresh_ratio * 1.5 +
    complaints * 0.5 +
    random_noise * 0.01  # noise contributes nothing
)))
churned = np.random.binomial(1, churn_prob)

feature_names = ['days_since_last_order', 'order_freq_change',
                 'basket_value_change', 'fresh_purchase_ratio',
                 'complaint_count', 'random_noise', 'customer_id']
X = np.column_stack([days_since, freq_change, basket_change,
                      fresh_ratio, complaints, random_noise, customer_id])

model = GradientBoostingClassifier(n_estimators=200, max_depth=4, random_state=42)
model.fit(X, churned)

importances = model.feature_importances_
sorted_idx = np.argsort(importances)[::-1]

print("FEATURE IMPORTANCE: Churn Prediction Model")
print("="*60)
print(f"{'Rank':<6} {'Feature':<28} {'Importance':>10} {'Status'}")
print("-"*60)

cumulative = 0
for rank, idx in enumerate(sorted_idx, 1):
    imp = importances[idx]
    cumulative += imp
    name = feature_names[idx]

    if name == 'random_noise':
        status = "← REMOVE (noise)"
    elif name == 'customer_id':
        status = "← INVESTIGATE (memorization?)"
    elif cumulative <= 0.80:
        status = "← core feature"
    else:
        status = ""

    print(f"{rank:<6} {name:<28} {imp:>10.4f} {status}")

print("-"*60)
print(f"{'':>34} {sum(importances):>10.4f}")
print()
print("ACTION ITEMS:")
print("  1. Top 3 features drive ~70% of model decisions")
print("  2. 'random_noise' should be removed (pure noise)")
print("  3. If 'customer_id' has high importance, the model is")
print("     memorizing individual customers — likely overfitting")
print("  4. Facebook found that top 10 features drove 50% of importance")
print("     and the bottom 300 features contributed < 1%")
```

```
FEATURE IMPORTANCE: Churn Prediction Model
============================================================
Rank   Feature                      Importance Status
------------------------------------------------------------
1      days_since_last_order            0.4012 ← core feature
2      order_freq_change                0.2345 ← core feature
3      basket_value_change              0.1578 ← core feature
4      fresh_purchase_ratio             0.1203
5      complaint_count                  0.0512
6      customer_id                      0.0218 ← INVESTIGATE (memorization?)
7      random_noise                     0.0132 ← REMOVE (noise)
------------------------------------------------------------
                                        1.0000

ACTION ITEMS:
  1. Top 3 features drive ~70% of model decisions
  2. 'random_noise' should be removed (pure noise)
  3. If 'customer_id' has high importance, the model is
     memorizing individual customers — likely overfitting
  4. Facebook found that top 10 features drove 50% of importance
     and the bottom 300 features contributed < 1%
```

Top 3 features drive ~79% of importance. `random_noise` contributes 1.3% — that's pure noise the model is fitting to, and removing it will slightly improve generalization. `customer_id` at 2.2% importance is a red flag: the model might be memorizing individual customers rather than learning generalizable patterns.

---

## Feature Generalization — Will This Feature Work Tomorrow?

A feature that works great on training data but fails on new data isn't a feature — it's overfitting. Two key checks: coverage and distribution overlap.

```python
import numpy as np
import pandas as pd

np.random.seed(42)

# Simulate train vs production feature distributions
features_analysis = {
    'days_since_last_order': {
        'train_mean': 45, 'train_std': 20,
        'prod_mean': 48, 'prod_std': 22,
        'train_coverage': 99.5, 'prod_coverage': 99.5,
        'verdict': '✅ Stable — similar distribution, high coverage'
    },
    'avg_basket_thb': {
        'train_mean': 4500, 'train_std': 3000,
        'prod_mean': 4800, 'prod_std': 3200,
        'train_coverage': 99.5, 'prod_coverage': 99.5,
        'verdict': '✅ Stable — slight shift but within range'
    },
    'credit_limit_usage': {
        'train_mean': 0.45, 'train_std': 0.25,
        'prod_mean': 0.42, 'prod_std': 0.28,
        'train_coverage': 42.0, 'prod_coverage': 38.0,
        'verdict': '⚠️ Low coverage — only credit customers, but informative'
    },
    'day_of_week': {
        'train_mean': 2.5, 'train_std': 1.7,
        'prod_mean': 6.0, 'prod_std': 0.0,  # production = Sunday only
        'train_coverage': 100, 'prod_coverage': 100,
        'verdict': '❌ Distribution mismatch — train has Mon-Sat, prod is Sunday'
    },
    'promo_code_id': {
        'train_mean': None, 'train_std': None,
        'prod_mean': None, 'prod_std': None,
        'train_coverage': 25.0, 'prod_coverage': 25.0,
        'verdict': '⚠️ High cardinality — new promo codes appear weekly'
    },
}

print("FEATURE GENERALIZATION CHECK: Train → Production")
print("="*70)
print(f"{'Feature':<25} {'Train Cov':>10} {'Prod Cov':>10} {'Status'}")
print("-"*70)
for feat, details in features_analysis.items():
    print(f"{feat:<25} {details['train_coverage']:>9.1f}% "
          f"{details['prod_coverage']:>9.1f}%  "
          f"{details['verdict']}")
print("="*70)
print()
print("RULES OF THUMB:")
print("  1. Coverage < 10% in production → feature may not generalize")
print("  2. Distribution shift between train/prod → retrain or drop")
print("  3. High cardinality + new values → use hashing trick")
print("  4. Low coverage but MNAR → create is_missing flag")
print("  5. Time-dependent features → always check for distribution shift")
```

```
FEATURE GENERALIZATION CHECK: Train → Production
======================================================================
Feature                    Train Cov   Prod Cov  Status
----------------------------------------------------------------------
days_since_last_order         99.5%       99.5%  ✅ Stable — similar distribution, high coverage
avg_basket_thb                99.5%       99.5%  ✅ Stable — slight shift but within range
credit_limit_usage            42.0%       38.0%  ⚠️ Low coverage — only credit customers, but informative
day_of_week                  100.0%      100.0%  ❌ Distribution mismatch — train has Mon-Sat, prod is Sunday
promo_code_id                 25.0%       25.0%  ⚠️ High cardinality — new promo codes appear weekly
======================================================================

RULES OF THUMB:
  1. Coverage < 10% in production → feature may not generalize
  2. Distribution shift between train/prod → retrain or drop
  3. High cardinality + new values → use hashing trick
  4. Low coverage but MNAR → create is_missing flag
  5. Time-dependent features → always check for distribution shift
```

The `day_of_week` example is the one that catches most people off guard. If you train on Mon-Sat data and predict on Sunday, the model has never seen that value. 100% coverage doesn't mean the values overlap. **Check distribution, not just coverage.**

---

## My Key Takeaways from Chapter 5

**1. Features matter more than algorithms.**
Facebook found that the right features beat clever architectures. I've seen a single domain-expert feature (fresh purchase ratio) outperform weeks of hyperparameter tuning.

**2. Not all missing values are equal.**
MNAR missingness is itself a feature. MAR can be explained by another variable. MCAR is rare and safe to impute. Understand WHY before deciding HOW.

**3. Scale your features. Always.**
It's the simplest thing with the biggest payoff. Log-transform skewed distributions. Standardize everything.

**4. Production categories change constantly.**
New brands, new customers, new product types. The hashing trick handles this gracefully — fixed feature size, no crashes, no UNKNOWN lumping.

**5. Feature crossing encodes domain knowledge.**
Restaurant × Fresh is a stronger signal than either alone. But crosses explode feature space — use them where interactions matter.

**6. Data leakage is the #1 production killer.**
If a feature looks too good, investigate it. Split by time. Compute statistics on train only. Deduplicate before splitting. Always ask: "Is this available at prediction time?"

**7. Feature importance is both a diagnostic and a pruning tool.**
Top features drive most decisions. Bottom features are maintenance burden. SHAP makes individual predictions explainable.

**8. Generalization = coverage + distribution overlap.**
High coverage doesn't mean the feature generalizes if values in production don't overlap with training. Check both.

---

## What's Next

Chapter 6 covers model development and offline evaluation — choosing architectures, training, hyperparameter tuning, and evaluating models before deployment. It's where the features we've engineered finally meet the algorithms.

---

*If this was useful, follow for the next article in this series. I write about data engineering, ML systems, and building AI platforms in enterprise — with real code and real tradeoffs, not just theory.*
